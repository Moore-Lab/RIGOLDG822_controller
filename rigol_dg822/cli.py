"""Command-line control of the RIGOL DG822 -- everything the tkinter GUI can do.

The GUI (``dg822_gui.py``) is the operator surface; this is the surface for a
script or an AI agent. Feature parity is the contract: every waveform, every
parameter, every quick preset, the whole arbitrary-waveform generator dialog,
the timed and N-cycle run modes, and the instrument's .RAF file memory are all
reachable from here.

VISA is per-process and stateless, so every command connects, acts and
disconnects. There is no session to keep alive and nothing to clean up between
calls. With no ``--resource`` the CLI discovers the instrument itself; with
``--sim`` it drives the in-process simulated DG822 from :mod:`rigol_dg822.sim`,
which is the only backend available on a box with no VISA implementation.

Run it::

    python -m rigol_dg822.cli discover
    python -m rigol_dg822.cli --sim apply sine --channel 1 --freq 1/0.1 --ampl 2.0
    python -m rigol_dg822.cli --sim apply pulse --channel 2 --freq 10k --width 20us
    python -m rigol_dg822.cli --sim output on --channel 1 --for 30s
    python -m rigol_dg822.cli --sim output on --channel 1 --cycles 1000
    python -m rigol_dg822.cli --sim preset apply square-10k-3v3 --channel both
    python -m rigol_dg822.cli --sim arb generate gaussian --freq 5k --sigma 20us -o g.csv
    python -m rigol_dg822.cli --sim arb comb --start 100 --stop 1000 --step 100 -o comb.csv
    python -m rigol_dg822.cli --sim arb preview --file comb.csv
    python -m rigol_dg822.cli --sim arb upload --channel 1 --file comb.csv --save-raf
    python -m rigol_dg822.cli --sim selftest

One caveat that only applies to ``--sim``: the simulated instrument lives in
this process, so it is factory-fresh at the start of every command and forgets
everything at the end. Hardware does not behave that way, and neither does the
panel, which holds one long-lived connection. Use ``selftest`` -- which does its
whole apply/read-back/upload sequence inside one process -- to exercise state
that has to persist across commands.

``--json`` is the agent-facing mode: every command then emits exactly one JSON
object on stdout and nothing else, and the exit code is 0 on success or
non-zero with the reason in ``error``::

    $ python -m rigol_dg822.cli --sim --json status
    {"ok": true, "command": "status", "resource": "SIM::DG822::INSTR", ...}

    $ python -m rigol_dg822.cli --json idn
    {"ok": false, "command": "idn", "error": "no instrument found: ..."}

Nothing here raises out of the process. A missing VISA implementation, an
absent instrument or a SCPI failure is diagnosed in one line and exits
non-zero, matching the driver's never-raise policy -- an agent parsing a
traceback would be parsing noise.

Two deliberate departures from the GUI, both because silence is wrong for a
machine caller: a frequency that will not parse is an error here instead of a
silent fall back to 1000 Hz, and the pulse duty-cycle clamp to [1 %, 99 %] is
reported as a warning instead of being applied invisibly.
"""

from __future__ import annotations

import argparse
import glob
import io
import json
import math
import os
import re
import sys
import time
from contextlib import contextmanager, redirect_stdout
from typing import Any, Dict, List, Optional, Sequence, Tuple

from .connection import DG822Connection
from .controller import DG822Controller
from .output import OutputPolarity
from .sim import SIM_IDN, SIM_RESOURCE
from .waveform import WaveformType

PROG = "python -m rigol_dg822.cli"

EXIT_OK = 0
EXIT_FAIL = 1
EXIT_USAGE = 2
EXIT_INTERRUPTED = 130

# Instrument limits, mirrored from the driver so the CLI can warn about a value
# the driver would happily transmit. Warnings, never refusals: the GUI does not
# enforce them either, and a bench user occasionally means it.
MIN_FREQUENCY_HZ = 1e-6
MAX_FREQUENCY_HZ = 25e6
MIN_AMPLITUDE_VPP = 1e-3
MAX_AMPLITUDE_VPP = 20.0

# Arbitrary-waveform hardware limits (firmware 00.02.x).
MIN_ARB_POINTS = 8
MAX_ARB_POINTS = 8192

# The GUI's per-channel defaults, so an omitted flag lands where the GUI lands.
DEFAULT_FREQUENCY_HZ = 1000.0
DEFAULT_AMPLITUDE_VPP = 5.0
DEFAULT_OFFSET_V = 0.0
DEFAULT_PHASE_DEG = 0.0
DEFAULT_DUTY_PCT = 50.0
DEFAULT_SYMMETRY_PCT = 50.0
DEFAULT_PULSE_WIDTH_S = 100e-6

# Where "Save CSV..." puts files in the GUI: <repo>/waveforms beside the package.
WAVEFORM_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "waveforms")


class CliError(Exception):
    """A diagnosis for the caller. Printed as one line; never a traceback."""


class Result:
    """What a handler returns: the JSON payload, plus lines for a human.

    A handler that half-succeeded -- the timed run that was cut short but still
    switched the output off -- reports through ``error``/``exit_code`` rather
    than raising, so the payload describing what actually happened survives.
    """

    def __init__(self, payload: Dict[str, Any], lines: Optional[List[str]] = None,
                 error: Optional[str] = None, exit_code: int = EXIT_OK):
        self.payload = payload
        self.lines = lines or []
        self.error = error
        self.exit_code = exit_code


class Ctx:
    """Per-invocation state: parsed flags, and warnings collected on the way."""

    def __init__(self, args: argparse.Namespace):
        self.args = args
        self.warnings: List[str] = []
        self.instrument_errors: List[str] = []

    def warn(self, message: str) -> None:
        self.warnings.append(message)


# ---------------------------------------------------------------------------
# Value parsing
# ---------------------------------------------------------------------------

# The GUI's frequency box evaluates arithmetic, which is how an operator writes
# "one pulse every 100 ms" as 1/0.1. Same character whitelist, same stripped
# builtins; the difference is that a failure here is fatal instead of silently
# becoming 1000 Hz.
_EXPR_CHARS = set("0123456789.+-*/() eE")

_FREQ_UNITS = {"hz": 1.0, "khz": 1e3, "mhz": 1e6, "k": 1e3, "m": 1e6}

_TIME_UNITS = {
    "ns": 1e-9,
    "us": 1e-6,
    "\u00b5s": 1e-6,   # MICRO SIGN, what the GUI's unit combobox uses
    "\u03bcs": 1e-6,   # GREEK SMALL LETTER MU, what some shells paste
    "ms": 1e-3,
    "s": 1.0,
    "sec": 1.0,
    "min": 60.0,
    "h": 3600.0,
    "hr": 3600.0,
    "hour": 3600.0,
    "hours": 3600.0,
}


def _eval_number(text: str, what: str) -> float:
    expr = text.strip()
    if not expr:
        raise CliError(f"{what}: no value given")
    try:
        if all(c in _EXPR_CHARS for c in expr):
            value = eval(expr, {"__builtins__": {}}, {})  # noqa: S307 - whitelisted chars only
        else:
            value = float(expr)
        result = float(value)
    except ZeroDivisionError:
        raise CliError(f"{what}: division by zero in {expr!r}")
    except (ValueError, SyntaxError, TypeError, NameError, OverflowError) as e:
        raise CliError(f"{what}: cannot evaluate {expr!r} ({e})")
    if not math.isfinite(result):
        raise CliError(f"{what}: {expr!r} is not a finite number")
    return result


def parse_frequency(text: str, what: str = "--freq") -> float:
    """Parse "1/0.1", "2.5kHz", "1e3" or "25M" into Hz."""
    s = str(text).strip()
    multiplier = 1.0
    m = re.search(r"(?i)(mhz|khz|hz|k|m)\s*$", s)
    if m:
        multiplier = _FREQ_UNITS[m.group(1).lower()]
        s = s[: m.start()].strip()
    hz = _eval_number(s, what) * multiplier
    if hz <= 0:
        raise CliError(f"{what}: frequency must be positive, got {hz:g} Hz")
    return hz


def parse_duration(text: str, what: str, default_unit: str = "s") -> float:
    """Parse "100us", "1/0.1", "5min", "2h" into seconds."""
    s = str(text).strip()
    unit = default_unit
    m = re.search(r"(?i)([a-z\u00b5\u03bc]+)\s*$", s)
    if m:
        token = m.group(1).lower()
        if token not in _TIME_UNITS:
            raise CliError(
                f"{what}: unknown time unit {m.group(1)!r} "
                f"(use ns, us, ms, s, min, hour)")
        unit = token
        s = s[: m.start()].strip()
    seconds = _eval_number(s, what) * _TIME_UNITS[unit]
    if seconds < 0:
        raise CliError(f"{what}: duration must not be negative, got {seconds:g} s")
    return seconds


def _width_arg(text: str) -> float:
    # Bare numbers follow the GUI's pulse-width unit combobox, which defaults to
    # microseconds; an explicit suffix always wins.
    return parse_duration(text, "--width", default_unit="us")


def _percent(value: float, what: str, low: float = 0.0, high: float = 100.0) -> float:
    if not math.isfinite(value):
        raise CliError(f"{what}: not a finite number")
    if not (low <= value <= high):
        raise CliError(f"{what}: {value:g} is outside {low:g}-{high:g} percent")
    return value


def check_frequency_range(ctx: Ctx, hz: float) -> None:
    if hz < MIN_FREQUENCY_HZ or hz > MAX_FREQUENCY_HZ:
        ctx.warn(f"frequency {hz:.6g} Hz is outside the DG822 range "
                 f"{MIN_FREQUENCY_HZ:g}-{MAX_FREQUENCY_HZ:g} Hz")


def check_amplitude_range(ctx: Ctx, vpp: float) -> None:
    if vpp < MIN_AMPLITUDE_VPP or vpp > MAX_AMPLITUDE_VPP:
        ctx.warn(f"amplitude {vpp:.6g} Vpp is outside the DG822 range "
                 f"{MIN_AMPLITUDE_VPP:g}-{MAX_AMPLITUDE_VPP:g} Vpp (High-Z)")


# ---------------------------------------------------------------------------
# Formatting
# ---------------------------------------------------------------------------

def kv(pairs: Sequence[Tuple[str, Any]], indent: str = "") -> List[str]:
    """Aligned "key   value" lines. No banners, no boxes."""
    rows = [(str(k), "" if v is None else str(v)) for k, v in pairs]
    if not rows:
        return []
    width = max(len(k) for k, _ in rows)
    return [f"{indent}{k.ljust(width)}  {v}".rstrip() for k, v in rows]


def fmt_hz(hz: Optional[float]) -> str:
    if hz is None:
        return "unavailable"
    if abs(hz) >= 1e6:
        return f"{hz / 1e6:.6g} MHz"
    if abs(hz) >= 1e3:
        return f"{hz / 1e3:.6g} kHz"
    return f"{hz:.6g} Hz"


def fmt_seconds(s: Optional[float]) -> str:
    if s is None:
        return "unavailable"
    a = abs(s)
    if a >= 1.0 or a == 0.0:
        return f"{s:.6g} s"
    if a >= 1e-3:
        return f"{s * 1e3:.6g} ms"
    if a >= 1e-6:
        return f"{s * 1e6:.6g} us"
    return f"{s * 1e9:.6g} ns"


def fmt_value(v: Optional[float], unit: str) -> str:
    return "unavailable" if v is None else f"{v:.6g} {unit}"


def fmt_sample_rate(sa_per_s: float) -> str:
    if sa_per_s >= 1e6:
        return f"{sa_per_s / 1e6:.3f} MSa/s"
    return f"{sa_per_s / 1e3:.1f} kSa/s"


def _jsonable(obj: Any) -> Any:
    """Make a payload strictly JSON-safe: no numpy scalars, no NaN/Infinity.

    json.dumps would happily emit bare ``Infinity`` for a High-Z impedance, and
    that is not JSON -- an agent's parser rejects it. Non-finite floats become
    null and carry their meaning in a sibling string field instead.
    """
    if isinstance(obj, dict):
        return {str(k): _jsonable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_jsonable(v) for v in obj]
    if isinstance(obj, bool) or obj is None or isinstance(obj, (str, int)):
        return obj
    if isinstance(obj, float):
        return obj if math.isfinite(obj) else None
    for attr in ("tolist", "item"):
        converter = getattr(obj, attr, None)
        if callable(converter):
            try:
                return _jsonable(converter())
            except Exception:
                break
    return str(obj)


def ascii_waveform(values: Sequence[float], width: int = 72, height: int = 17,
                   ) -> List[str]:
    """Render samples as a plain-ASCII plot.

    Plain ASCII on purpose: this has to be readable in a bare cmd.exe window
    with codepage 437, where box-drawing and braille characters come out as
    mojibake.
    """
    n = len(values)
    if n == 0:
        return ["(no samples)"]
    width = max(8, min(int(width), 200))
    height = max(5, min(int(height), 60))

    vmin = float(min(values))
    vmax = float(max(values))
    if vmax - vmin < 1e-12:
        vmin -= 0.5
        vmax += 0.5

    def row_of(v: float) -> int:
        frac = (float(v) - vmin) / (vmax - vmin)
        return max(0, min(height - 1, int(round((1.0 - frac) * (height - 1)))))

    grid = [[" "] * width for _ in range(height)]
    zero_row = row_of(0.0) if vmin <= 0.0 <= vmax else None
    if zero_row is not None:
        grid[zero_row] = ["-"] * width

    for col in range(width):
        lo_i = int(col * n / width)
        hi_i = max(lo_i + 1, int((col + 1) * n / width))
        segment = values[lo_i:hi_i]
        top, bottom = row_of(max(segment)), row_of(min(segment))
        for row in range(top, bottom + 1):
            grid[row][col] = "*"

    label_width = 9
    lines: List[str] = []
    for row in range(height):
        if row == 0:
            label = f"{vmax:+.3f}"
        elif row == height - 1:
            label = f"{vmin:+.3f}"
        elif zero_row is not None and row == zero_row:
            label = f"{0.0:+.3f}"
        else:
            label = ""
        lines.append(f"{label:>{label_width}} |" + "".join(grid[row]))
    lines.append(" " * label_width + " +" + "-" * width)
    return lines


# ---------------------------------------------------------------------------
# Connecting
# ---------------------------------------------------------------------------

def _probe(timeout: int, simulate: bool) -> Tuple[Dict[str, Any], List[Tuple[str, str]]]:
    """Bring a backend up, describe why it did or did not come up, and scan.

    One pass for both answers: the resource manager is built lazily and each
    failed attempt reprints its diagnosis, so probing and then discovering
    separately would double every line in the log.
    """
    from . import connection as connection_module

    conn = DG822Connection(timeout=timeout, simulate=simulate)
    try:
        devices = conn.discover_devices()
        rm = getattr(conn, "_rm", None)
        report = {
            "pyvisa_importable": getattr(connection_module, "pyvisa", None) is not None,
            "pyvisa_error": getattr(connection_module, "_PYVISA_ERROR", None),
            "simulated": simulate,
            "backend_available": rm is not None,
            "backend": str(getattr(rm, "visalib", "")) if rm is not None else None,
            "backend_error": conn.backend_error,
        }
    finally:
        conn.close()
    return report, devices


def resolve_resource(ctx: Ctx) -> Tuple[str, bool]:
    """Work out which instrument to talk to. Returns (resource, simulated)."""
    args = ctx.args
    if args.resource:
        return args.resource, bool(args.sim) or args.resource == SIM_RESOURCE
    if args.sim:
        return SIM_RESOURCE, True

    report, devices = _probe(args.timeout, simulate=False)

    real = [d for d in devices if d[0] != SIM_RESOURCE]
    if real:
        return real[0][0], False

    if not report["backend_available"]:
        reason = ((report["backend_error"] or report["pyvisa_error"]
                   or "no VISA backend")
                  + "; install NI-VISA or pyvisa-py for hardware")
    else:
        reason = "no RIGOL DG800/DG900 device answered *IDN? on USB"
    # Never silently fall through to the simulator: an agent that thinks it
    # drove hardware and did not is the worst failure mode this tool has.
    raise CliError(
        f"no instrument found: {reason}. "
        f"Pass --sim to run against the simulated DG822, "
        f"or -r <VISA address> to name one explicitly.")


def drain_errors(dg: DG822Controller, limit: int = 16) -> List[str]:
    """Pop the instrument's error queue until it says there is nothing left.

    SCPI writes are fire-and-forget: the driver returns True as soon as the
    bytes leave, so ":MMEMory:STORe:DATA" with nothing to store looks like a
    success at every layer above the wire. The queue is the only place the
    instrument gets to disagree, so it is read rather than left to fill up.
    """
    found: List[str] = []
    for _ in range(limit):
        reported = dg.connection.get_error()
        if not reported or reported.startswith("0,"):
            break
        found.append(reported)
    return found


def fail_on_instrument_error(ctx: Ctx, dg: DG822Controller, what: str) -> None:
    """Refuse to report success for a write the instrument rejected."""
    errors = drain_errors(dg)
    if errors:
        ctx.instrument_errors.extend(errors)
        raise CliError(f"{what}: the instrument reported {errors[0]}")


@contextmanager
def instrument(ctx: Ctx):
    """Connect, yield the controller, always disconnect and release the RM."""
    resource, simulate = resolve_resource(ctx)
    dg = DG822Controller(resource, timeout=ctx.args.timeout, simulate=simulate)
    if not dg.connect(resource):
        hint = ("" if simulate else
                " (pass --sim to run against the simulated DG822)")
        raise CliError(f"could not connect to {resource}{hint}")
    # Start from an empty queue so anything found on the way out belongs to this
    # command and not to whatever ran before it.
    dg.connection.clear_status()
    try:
        yield dg
    finally:
        try:
            for reported in drain_errors(dg):
                ctx.instrument_errors.append(reported)
                ctx.warn(f"instrument error queue: {reported}")
        except Exception:
            pass
        try:
            # close() disconnects and then releases the resource manager, which
            # plain disconnect() leaves loaded. Calling both, as the GUI does,
            # only prints the driver's "Disconnected" line twice.
            dg.connection.close()
        except Exception:
            pass


def _channels(args: argparse.Namespace) -> List[int]:
    if getattr(args, "all", False):
        return [1, 2]
    return [int(args.channel)]


def _require(ok: Any, what: str) -> None:
    """Turn a driver's False/None into a diagnosis instead of a silent no-op."""
    if not ok:
        raise CliError(f"{what} failed (the instrument rejected it or the "
                       f"write timed out; check 'status' and the SCPI error queue)")


# ---------------------------------------------------------------------------
# discover / idn / status / reset / beep / sync-phases
# ---------------------------------------------------------------------------

def cmd_discover(ctx: Ctx) -> Result:
    report, devices = _probe(ctx.args.timeout, simulate=bool(ctx.args.sim))

    entries = [{
        "resource": resource,
        "idn": idn,
        "simulated": resource == SIM_RESOURCE,
    } for resource, idn in devices]

    payload = {
        "visa": report,
        "devices": entries,
        "count": len(entries),
        "hardware_count": sum(0 if e["simulated"] else 1 for e in entries),
    }

    lines = kv([
        ("pyvisa", "importable" if report["pyvisa_importable"]
         else f"NOT importable: {report['pyvisa_error']}"),
        ("backend", report["backend"] if report["backend_available"]
         else f"unavailable: {report['backend_error']}"),
        ("devices", len(entries)),
    ])
    lines.append("")
    for e in entries:
        lines.append(f"{e['resource']}{'  [simulated]' if e['simulated'] else ''}")
        lines.append(f"    {e['idn']}")
    if payload["hardware_count"] == 0:
        lines.append("")
        lines.append("No hardware found. Use --sim to drive the simulated DG822.")
    return Result(payload, lines)


def cmd_idn(ctx: Ctx) -> Result:
    with instrument(ctx) as dg:
        payload = {
            "resource": dg.connection.resource_name,
            "idn": dg.idn,
            "simulated": dg.is_simulated,
            "version": dg.connection.get_version(),
        }
    return Result(payload, kv([
        ("resource", payload["resource"]),
        ("idn", payload["idn"]),
        ("version", payload["version"]),
        ("simulated", payload["simulated"]),
    ]))


def _channel_state(dg: DG822Controller, ch: int) -> Dict[str, Any]:
    wf, out = dg.waveform, dg.output
    impedance = out.get_impedance(ch)
    state: Dict[str, Any] = {
        "channel": ch,
        "output": out.get_state(ch),
        "function": wf.get_function(ch),
        "frequency_hz": wf.get_frequency(ch),
        "amplitude_vpp": wf.get_amplitude(ch),
        "offset_v": wf.get_offset(ch),
        "phase_deg": wf.get_phase(ch),
        "square_duty_pct": wf.get_square_duty_cycle(ch),
        "ramp_symmetry_pct": wf.get_ramp_symmetry(ch),
        "polarity": out.get_polarity(ch),
        "sync": out.get_sync_state(ch),
        "idle": out.get_idle_level(ch),
        "apply": wf.get_apply_settings(ch),
    }
    # High-Z reads back as 9.9E+37 and the driver maps it to inf, which has no
    # JSON spelling; the numeric field goes null and the meaning goes in "load".
    if impedance is None:
        state["load"] = None
        state["load_ohms"] = None
    elif impedance == float("inf"):
        state["load"] = "high-z"
        state["load_ohms"] = None
    else:
        state["load"] = f"{impedance:.6g} ohm"
        state["load_ohms"] = impedance
    return state


def cmd_status(ctx: Ctx) -> Result:
    channels = [1, 2] if ctx.args.channel is None else [int(ctx.args.channel)]
    with instrument(ctx) as dg:
        payload = {
            "resource": dg.connection.resource_name,
            "idn": dg.idn,
            "simulated": dg.is_simulated,
            "channels": {str(ch): _channel_state(dg, ch) for ch in channels},
        }
        # Read as data here, so it is reported rather than warned about.
        payload["error_queue"] = drain_errors(dg)

    lines = kv([
        ("resource", payload["resource"]),
        ("idn", payload["idn"]),
        ("simulated", payload["simulated"]),
        ("errors", "; ".join(payload["error_queue"]) or "none"),
    ])
    for ch in channels:
        s = payload["channels"][str(ch)]
        lines.append("")
        lines.append(f"channel {ch}")
        lines.extend(kv([
            ("output", "unavailable" if s["output"] is None
             else ("ON" if s["output"] else "off")),
            ("function", s["function"]),
            ("frequency", fmt_hz(s["frequency_hz"])),
            ("amplitude", fmt_value(s["amplitude_vpp"], "Vpp")),
            ("offset", fmt_value(s["offset_v"], "V")),
            ("phase", fmt_value(s["phase_deg"], "deg")),
            ("square duty", fmt_value(s["square_duty_pct"], "%")),
            ("ramp symmetry", fmt_value(s["ramp_symmetry_pct"], "%")),
            ("load", s["load"]),
            ("polarity", s["polarity"]),
            ("sync", s["sync"]),
        ], indent="  "))
    return Result(payload, lines)


def cmd_reset(ctx: Ctx) -> Result:
    with instrument(ctx) as dg:
        _require(dg.reset(), "*RST")
        payload = {"resource": dg.connection.resource_name, "reset": True}
    return Result(payload, ["instrument reset (*RST)"])


def cmd_beep(ctx: Ctx) -> Result:
    with instrument(ctx) as dg:
        _require(dg.beep(), ":SYSTem:BEEPer:IMMediate")
        payload = {"resource": dg.connection.resource_name, "beep": True}
    return Result(payload, ["beeped"])


def cmd_sync_phases(ctx: Ctx) -> Result:
    with instrument(ctx) as dg:
        # The driver hardcodes :SOURce1 -- there is no per-channel form of this
        # command on the DG822; CH2 is aligned to CH1, not the other way round.
        _require(dg.waveform.sync_phases(), ":SOURce1:PHASe:SYNChronize")
        payload = {"resource": dg.connection.resource_name, "synchronized": True}
    return Result(payload, ["channel phases synchronized to CH1"])


# ---------------------------------------------------------------------------
# apply
# ---------------------------------------------------------------------------

def _pulse_duty(ctx: Ctx, frequency: float, width_s: Optional[float],
                duty_pct: Optional[float]) -> Tuple[float, float]:
    """Resolve a pulse into (duty percent actually sent, width in seconds)."""
    period = 1.0 / frequency
    if width_s is not None and duty_pct is not None:
        raise CliError("give --width or --duty for a pulse, not both "
                       "(they are the same degree of freedom)")
    if width_s is None and duty_pct is None:
        width_s = DEFAULT_PULSE_WIDTH_S      # the GUI's pulse-width default
    if width_s is not None:
        raw = width_s / period * 100.0
    else:
        raw = float(duty_pct)
        width_s = raw / 100.0 * period
    # The GUI clamps to [1, 99] silently and only shows ">100%!" in a readout.
    # Same clamp, but said out loud: a 200 % request that becomes 99 % without
    # a word is a bench mystery waiting to happen.
    duty = max(1.0, min(99.0, raw))
    if abs(duty - raw) > 1e-9:
        ctx.warn(f"pulse duty {raw:.4g}% clamped to {duty:.4g}% "
                 f"(width {fmt_seconds(width_s)} against period {fmt_seconds(period)})")
    return duty, width_s


def cmd_apply(ctx: Ctx) -> Result:
    args = ctx.args
    shape = args.shape
    channel = int(args.channel)

    frequency = (DEFAULT_FREQUENCY_HZ if args.freq is None
                 else parse_frequency(args.freq))
    amplitude = DEFAULT_AMPLITUDE_VPP if args.ampl is None else args.ampl
    offset = DEFAULT_OFFSET_V if args.offset is None else args.offset
    phase = DEFAULT_PHASE_DEG if args.phase is None else args.phase
    duty_arg = getattr(args, "duty", None)
    symmetry_arg = getattr(args, "symmetry", None)
    width_arg = getattr(args, "width", None)
    width_s = None if width_arg is None else _width_arg(width_arg)

    if shape not in ("noise", "dc"):
        check_frequency_range(ctx, frequency)
    if shape != "dc":
        check_amplitude_range(ctx, amplitude)

    # The instrument discards these for noise and DC; say so rather than let a
    # caller believe a value landed.
    if shape == "noise":
        for flag, value in (("--freq", args.freq), ("--phase", args.phase)):
            if value is not None:
                ctx.warn(f"noise ignores {flag}; :APPLy:NOISe takes amplitude and offset only")
    if shape == "dc":
        for flag, value in (("--freq", args.freq), ("--ampl", args.ampl),
                            ("--phase", args.phase)):
            if value is not None:
                ctx.warn(f"DC ignores {flag}; --offset is the DC level")

    payload: Dict[str, Any] = {
        "channel": channel,
        "shape": shape,
    }

    # Everything that can be decided without the instrument is decided before
    # the connection opens, so a bad flag fails immediately instead of after a
    # VISA round trip.
    pulse_duty = pulse_requested_width = None
    if shape == "pulse":
        pulse_duty, pulse_requested_width = _pulse_duty(
            ctx, frequency, width_s, duty_arg)

    with instrument(ctx) as dg:
        if shape == "sine":
            ok = dg.setup_sine(channel, frequency, amplitude, offset, phase)
            payload.update(frequency_hz=frequency, amplitude_vpp=amplitude,
                           offset_v=offset, phase_deg=phase)
        elif shape == "square":
            duty = _percent(DEFAULT_DUTY_PCT if duty_arg is None else duty_arg,
                            "--duty", 0.01, 99.99)
            ok = dg.setup_square(channel, frequency, amplitude, offset, phase, duty)
            payload.update(frequency_hz=frequency, amplitude_vpp=amplitude,
                           offset_v=offset, phase_deg=phase, duty_pct=duty)
        elif shape == "ramp":
            symmetry = _percent(
                DEFAULT_SYMMETRY_PCT if symmetry_arg is None else symmetry_arg,
                "--symmetry", 0.0, 100.0)
            ok = dg.setup_ramp(channel, frequency, amplitude, offset, phase, symmetry)
            payload.update(frequency_hz=frequency, amplitude_vpp=amplitude,
                           offset_v=offset, phase_deg=phase, symmetry_pct=symmetry)
        elif shape == "pulse":
            duty, requested_width_s = pulse_duty, pulse_requested_width
            period = 1.0 / frequency
            # What the instrument will actually produce, which is not the
            # requested width whenever the duty clamp bit.
            width_s = duty / 100.0 * period
            # setup_pulse(centered=True) writes (phase + (1 - duty/100)*180) % 360,
            # which puts the rising edge at (period - width)/2. Same arithmetic as
            # the GUI, and the only reason to go through the controller rather
            # than calling apply_pulse directly.
            effective_phase = (phase + (1.0 - duty / 100.0) * 180.0) % 360.0
            ok = dg.setup_pulse(channel, frequency, amplitude, offset, phase,
                                duty_cycle=duty, centered=True)
            payload.update(frequency_hz=frequency, amplitude_vpp=amplitude,
                           offset_v=offset, phase_deg=phase, duty_pct=duty,
                           width_s=width_s, requested_width_s=requested_width_s,
                           period_s=period,
                           effective_phase_deg=effective_phase,
                           pulse_start_s=(period - width_s) / 2.0,
                           centered=True)
        elif shape == "noise":
            ok = dg.setup_noise(channel, amplitude, offset)
            payload.update(amplitude_vpp=amplitude, offset_v=offset)
        elif shape == "dc":
            ok = dg.setup_dc(channel, offset)
            payload.update(level_v=offset)
        else:
            raise CliError(f"unknown waveform {shape!r}")

        _require(ok, f"apply {shape} on CH{channel}")
        payload["function"] = dg.waveform.get_function(channel)
        payload["resource"] = dg.connection.resource_name

    rows: List[Tuple[str, Any]] = [("channel", channel), ("shape", shape)]
    if "frequency_hz" in payload:
        rows.append(("frequency", fmt_hz(payload["frequency_hz"])))
    if "amplitude_vpp" in payload:
        rows.append(("amplitude", fmt_value(payload["amplitude_vpp"], "Vpp")))
    if "offset_v" in payload:
        rows.append(("offset", fmt_value(payload["offset_v"], "V")))
    if "level_v" in payload:
        rows.append(("DC level", fmt_value(payload["level_v"], "V")))
    if "phase_deg" in payload:
        rows.append(("phase", fmt_value(payload["phase_deg"], "deg")))
    if "duty_pct" in payload:
        rows.append(("duty", fmt_value(payload["duty_pct"], "%")))
    if "symmetry_pct" in payload:
        rows.append(("symmetry", fmt_value(payload["symmetry_pct"], "%")))
    if "width_s" in payload:
        rows.append(("width", fmt_seconds(payload["width_s"])))
        rows.append(("period", fmt_seconds(payload["period_s"])))
        rows.append(("pulse start", fmt_seconds(payload["pulse_start_s"])))
        rows.append(("phase sent", fmt_value(payload["effective_phase_deg"], "deg")))
    rows.append(("function", payload["function"]))
    return Result(payload, kv(rows))


# ---------------------------------------------------------------------------
# set / get
# ---------------------------------------------------------------------------

_SET_PARAMS = {
    "freq": "frequency in Hz; expression and Hz/kHz/MHz suffix accepted",
    "ampl": "amplitude in Vpp",
    "offset": "DC offset in V",
    "phase": "start phase in degrees",
    "duty": "square duty cycle in percent (0.01-99.99)",
    "pulse-duty": "pulse duty cycle in percent (1-99)",
    "width": "pulse width; ns/us/ms/s suffix, bare numbers are us",
    "symmetry": "ramp symmetry in percent (0 falling, 50 triangle, 100 rising)",
    "high": "high level in V",
    "low": "low level in V",
    "function": "shape: sine|square|ramp|pulse|noise|dc|arbitrary|harmonic",
}

_GET_PARAMS = {
    "freq": "frequency in Hz",
    "ampl": "amplitude in Vpp",
    "offset": "DC offset in V",
    "phase": "start phase in degrees",
    "duty": "square duty cycle in percent",
    "symmetry": "ramp symmetry in percent",
    "function": "current waveform shape",
    "output": "output state",
    "load": "load impedance in ohms (high-z reads as infinite)",
    "polarity": "output polarity",
    "sync": "sync output state",
    "idle": "idle level",
    "apply": "the instrument's own :APPLy? summary",
}

_FUNCTIONS = {
    "sine": WaveformType.SINE,
    "square": WaveformType.SQUARE,
    "ramp": WaveformType.RAMP,
    "pulse": WaveformType.PULSE,
    "noise": WaveformType.NOISE,
    "dc": WaveformType.DC,
    "arbitrary": WaveformType.ARBITRARY,
    "harmonic": WaveformType.HARMONIC,
}


def cmd_set(ctx: Ctx) -> Result:
    param = ctx.args.param
    raw = ctx.args.value
    channel = int(ctx.args.channel)

    with instrument(ctx) as dg:
        wf = dg.waveform
        if param == "freq":
            value: Any = parse_frequency(raw, "freq")
            check_frequency_range(ctx, value)
            ok = wf.set_frequency(channel, value)
        elif param == "ampl":
            value = _eval_number(raw, "ampl")
            check_amplitude_range(ctx, value)
            ok = wf.set_amplitude(channel, value)
        elif param == "offset":
            value = _eval_number(raw, "offset")
            ok = wf.set_offset(channel, value)
        elif param == "phase":
            value = _eval_number(raw, "phase")
            ok = wf.set_phase(channel, value)
        elif param == "duty":
            value = _percent(_eval_number(raw, "duty"), "duty", 0.01, 99.99)
            ok = wf.set_square_duty_cycle(channel, value)
        elif param == "pulse-duty":
            value = _percent(_eval_number(raw, "pulse-duty"), "pulse-duty", 1.0, 99.0)
            ok = wf.set_pulse_duty_cycle(channel, value)
        elif param == "width":
            value = _width_arg(raw)
            ok = wf.set_pulse_width(channel, value)
        elif param == "symmetry":
            value = _percent(_eval_number(raw, "symmetry"), "symmetry", 0.0, 100.0)
            ok = wf.set_ramp_symmetry(channel, value)
        elif param == "high":
            value = _eval_number(raw, "high")
            ok = wf.set_high_level(channel, value)
        elif param == "low":
            value = _eval_number(raw, "low")
            ok = wf.set_low_level(channel, value)
        elif param == "function":
            key = str(raw).strip().lower()
            if key not in _FUNCTIONS:
                raise CliError(f"function: {raw!r} is not one of "
                               f"{', '.join(sorted(_FUNCTIONS))}")
            value = _FUNCTIONS[key].value
            ok = wf.set_function(channel, _FUNCTIONS[key])
        else:
            raise CliError(f"unknown parameter {param!r}")

        _require(ok, f"set {param} on CH{channel}")
        payload = {"channel": channel, "param": param, "value": value,
                   "resource": dg.connection.resource_name}

    return Result(payload, kv([("channel", channel), (param, value)]))


def _get_one(dg: DG822Controller, channel: int, param: str) -> Any:
    wf, out = dg.waveform, dg.output
    if param == "freq":
        return wf.get_frequency(channel)
    if param == "ampl":
        return wf.get_amplitude(channel)
    if param == "offset":
        return wf.get_offset(channel)
    if param == "phase":
        return wf.get_phase(channel)
    if param == "duty":
        return wf.get_square_duty_cycle(channel)
    if param == "symmetry":
        return wf.get_ramp_symmetry(channel)
    if param == "function":
        return wf.get_function(channel)
    if param == "output":
        return out.get_state(channel)
    if param == "load":
        impedance = out.get_impedance(channel)
        if impedance == float("inf"):
            return "high-z"
        return impedance
    if param == "polarity":
        return out.get_polarity(channel)
    if param == "sync":
        return out.get_sync_state(channel)
    if param == "idle":
        return out.get_idle_level(channel)
    if param == "apply":
        return wf.get_apply_settings(channel)
    raise CliError(f"unknown parameter {param!r}")


def cmd_get(ctx: Ctx) -> Result:
    channel = int(ctx.args.channel)
    params = list(ctx.args.params)
    values: Dict[str, Any] = {}
    with instrument(ctx) as dg:
        for param in params:
            values[param] = _get_one(dg, channel, param)
        resource = dg.connection.resource_name

    unavailable = [p for p, v in values.items() if v is None]
    for param in unavailable:
        ctx.warn(f"{param}: no reply from the instrument (query failed, "
                 f"empty reply, or unparseable)")
    payload = {"channel": channel, "values": values, "resource": resource}
    return Result(payload, kv([(p, "unavailable" if values[p] is None else values[p])
                               for p in params]))


# ---------------------------------------------------------------------------
# output
# ---------------------------------------------------------------------------

def _sleep_interruptible(seconds: float) -> float:
    """Sleep in slices so Ctrl+C lands promptly. Returns elapsed seconds."""
    started = time.monotonic()
    deadline = started + seconds
    while True:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            break
        time.sleep(min(0.2, remaining))
    return time.monotonic() - started


def cmd_output(ctx: Ctx) -> Result:
    args = ctx.args
    turning_on = args.state == "on"
    channels = _channels(args)

    if not turning_on and (args.duration is not None or args.cycles is not None):
        raise CliError("--for and --cycles only make sense with 'output on'")
    if args.duration is not None and args.cycles is not None:
        raise CliError("give --for or --cycles, not both")

    payload: Dict[str, Any] = {"channels": channels, "requested": args.state}

    with instrument(ctx) as dg:
        if not turning_on:
            for ch in channels:
                _require(dg.output_off(ch), f"output off CH{ch}")
            payload["state"] = "off"
            payload["resource"] = dg.connection.resource_name
            return Result(payload, [f"CH{ch} output off" for ch in channels])

        run_seconds: Optional[float] = None
        if args.duration is not None:
            run_seconds = parse_duration(args.duration, "--for", default_unit="s")
            if run_seconds <= 0:
                raise CliError("--for: duration must be greater than zero")
            payload["mode"] = "duration"
        elif args.cycles is not None:
            if args.cycles <= 0:
                raise CliError("--cycles: must be a positive integer")
            # The GUI derives the run time the same way, from the frequency in
            # its box. Here the instrument is the authority on its own frequency.
            frequency = dg.waveform.get_frequency(channels[0])
            if not frequency or frequency <= 0:
                raise CliError(
                    f"--cycles: CH{channels[0]} did not report a usable frequency; "
                    f"apply a waveform first or use --for")
            run_seconds = args.cycles / frequency
            payload["mode"] = "cycles"
            payload["cycles"] = args.cycles
            payload["frequency_hz"] = frequency
        else:
            payload["mode"] = "continuous"

        if run_seconds is not None:
            payload["run_seconds"] = run_seconds
            # Host wall-clock, not the instrument's burst mode: no :BURSt command
            # is sent, exactly as in the GUI. The cycle count is nominal and the
            # end time carries this process's scheduling jitter.
            payload["timing"] = "host wall-clock timer, not instrument burst"

        for ch in channels:
            _require(dg.output_on(ch), f"output on CH{ch}")
        payload["state"] = "on"

        if run_seconds is None:
            payload["resource"] = dg.connection.resource_name
            return Result(payload, [f"CH{ch} output on (continuous)" for ch in channels])

        if not ctx.args.quiet and not ctx.args.json:
            print(f"CH{','.join(str(c) for c in channels)} on for "
                  f"{run_seconds:.3f} s", file=sys.stderr)

        interrupted = False
        started = time.monotonic()
        try:
            _sleep_interruptible(run_seconds)
        except KeyboardInterrupt:
            interrupted = True
        finally:
            elapsed = time.monotonic() - started
            # The output goes off on the way out whatever happened. The GUI drops
            # its pending after() timer on exit and leaves a channel driving; a
            # CLI that did the same would leave the bench live.
            off_ok = all(dg.output_off(ch) for ch in channels)

        payload["state"] = "off" if off_ok else "unknown"
        payload["elapsed_seconds"] = elapsed
        payload["switched_off"] = bool(off_ok)
        payload["interrupted"] = interrupted
        payload["resource"] = dg.connection.resource_name

    lines = kv([
        ("channels", ", ".join(str(c) for c in channels)),
        ("mode", payload["mode"]),
        ("run", f"{run_seconds:.3f} s"),
        ("elapsed", f"{payload['elapsed_seconds']:.3f} s"),
        ("state", payload["state"]),
    ])
    if not off_ok:
        return Result(payload, lines, exit_code=EXIT_FAIL, error=(
            "the output was switched on but switching it back off failed -- "
            "the channel may still be driving; check 'status'"))
    if interrupted:
        return Result(payload, lines, exit_code=EXIT_INTERRUPTED,
                      error="interrupted by Ctrl+C; the output was switched off")
    return Result(payload, lines)


# ---------------------------------------------------------------------------
# load / polarity / sync
# ---------------------------------------------------------------------------

def cmd_load(ctx: Ctx) -> Result:
    args = ctx.args
    channels = _channels(args)
    if args.ohms is not None and args.setting is not None:
        raise CliError("give a load of high-z or 50, or --ohms R, not both")
    if args.ohms is None and args.setting is None:
        raise CliError("give a load: high-z, 50, or --ohms R")

    with instrument(ctx) as dg:
        results = {}
        for ch in channels:
            if args.setting == "high-z":
                ok = dg.set_load_high_z(ch)
                value: Any = "high-z"
            elif args.setting == "50":
                ok = dg.set_load_50_ohm(ch)
                value = 50.0
            else:
                value = float(args.ohms)
                if not (1 <= value <= 10000):
                    ctx.warn(f"--ohms {value:g} is outside the driver's 1-10000 ohm "
                             f"range; it is transmitted anyway")
                ok = dg.output.set_impedance(ch, value)
            _require(ok, f"set load on CH{ch}")
            results[str(ch)] = value
        payload = {"channels": channels, "load": results,
                   "resource": dg.connection.resource_name}
    return Result(payload, kv([(f"CH{ch} load", results[str(ch)]) for ch in channels]))


def cmd_polarity(ctx: Ctx) -> Result:
    channels = _channels(ctx.args)
    polarity = (OutputPolarity.NORMAL if ctx.args.setting == "normal"
                else OutputPolarity.INVERTED)
    with instrument(ctx) as dg:
        for ch in channels:
            _require(dg.output.set_polarity(ch, polarity), f"set polarity on CH{ch}")
        payload = {"channels": channels, "polarity": ctx.args.setting,
                   "resource": dg.connection.resource_name}
    return Result(payload, [f"CH{ch} polarity {ctx.args.setting}" for ch in channels])


def cmd_sync(ctx: Ctx) -> Result:
    channels = _channels(ctx.args)
    enable = ctx.args.state == "on"
    with instrument(ctx) as dg:
        for ch in channels:
            ok = dg.output.enable_sync(ch) if enable else dg.output.disable_sync(ch)
            _require(ok, f"set sync on CH{ch}")
        payload = {"channels": channels, "sync": ctx.args.state,
                   "resource": dg.connection.resource_name}
    return Result(payload, [f"CH{ch} sync {ctx.args.state}" for ch in channels])


# ---------------------------------------------------------------------------
# presets
# ---------------------------------------------------------------------------

# The GUI's Quick Presets, verbatim -- same waveform, same numbers, same order.
PRESETS: Dict[str, Dict[str, Any]] = {
    "sine-1k-1vpp": {"label": "1kHz Sine 1Vpp", "waveform": "sine",
                     "freq": 1000.0, "ampl": 1.0, "offset": 0.0, "phase": 0.0},
    "sine-1k-5vpp": {"label": "1kHz Sine 5Vpp", "waveform": "sine",
                     "freq": 1000.0, "ampl": 5.0, "offset": 0.0, "phase": 0.0},
    "square-10k-3v3": {"label": "10kHz Square 3.3V", "waveform": "square",
                       "freq": 10000.0, "ampl": 3.3, "offset": 1.65, "phase": 0.0,
                       "duty": 50.0},
    "sine-1m-1vpp": {"label": "1MHz Sine 1Vpp", "waveform": "sine",
                     "freq": 1000000.0, "ampl": 1.0, "offset": 0.0, "phase": 0.0},
    "ramp-100-5vpp": {"label": "100Hz Ramp 5Vpp", "waveform": "ramp",
                      "freq": 100.0, "ampl": 5.0, "offset": 0.0, "phase": 0.0,
                      "symmetry": 100.0},
    "dc-3v3": {"label": "DC 3.3V", "waveform": "dc",
               "freq": 1000.0, "ampl": 5.0, "offset": 3.3, "phase": 0.0},
}


def cmd_preset_list(ctx: Ctx) -> Result:
    entries = []
    lines = []
    for pid, p in PRESETS.items():
        entry = {"id": pid, "label": p["label"], "waveform": p["waveform"],
                 "frequency_hz": p["freq"], "amplitude_vpp": p["ampl"],
                 "offset_v": p["offset"], "phase_deg": p["phase"]}
        if "duty" in p:
            entry["duty_pct"] = p["duty"]
        if "symmetry" in p:
            entry["symmetry_pct"] = p["symmetry"]
        entries.append(entry)
        extra = ""
        if "duty" in p:
            extra = f", duty {p['duty']:g}%"
        if "symmetry" in p:
            extra = f", symmetry {p['symmetry']:g}%"
        if p["waveform"] == "dc":
            detail = f"DC level {p['offset']:g} V"
        else:
            detail = (f"{p['waveform']} {fmt_hz(p['freq'])}, {p['ampl']:g} Vpp, "
                      f"offset {p['offset']:g} V{extra}")
        lines.append(f"{pid:<16} {p['label']:<20} {detail}")
    return Result({"presets": entries, "count": len(entries)}, lines)


def cmd_preset_apply(ctx: Ctx) -> Result:
    pid = ctx.args.preset
    if pid not in PRESETS:
        raise CliError(f"unknown preset {pid!r}; run 'preset list' for the "
                       f"{len(PRESETS)} available ids")
    p = PRESETS[pid]
    channels = [1, 2] if ctx.args.channel == "both" else [int(ctx.args.channel)]

    with instrument(ctx) as dg:
        for ch in channels:
            if p["waveform"] == "sine":
                ok = dg.setup_sine(ch, p["freq"], p["ampl"], p["offset"], p["phase"])
            elif p["waveform"] == "square":
                ok = dg.setup_square(ch, p["freq"], p["ampl"], p["offset"],
                                     p["phase"], p["duty"])
            elif p["waveform"] == "ramp":
                ok = dg.setup_ramp(ch, p["freq"], p["ampl"], p["offset"],
                                   p["phase"], p["symmetry"])
            elif p["waveform"] == "dc":
                # The preset carries a frequency and amplitude the DC path throws
                # away; the offset is the level. Kept in the table so the CLI's
                # preset reads identically to the GUI button.
                ok = dg.setup_dc(ch, p["offset"])
            else:
                raise CliError(f"preset {pid}: unsupported waveform {p['waveform']!r}")
            _require(ok, f"apply preset {pid} on CH{ch}")
        payload = {"preset": pid, "label": p["label"], "channels": channels,
                   "waveform": p["waveform"], "resource": dg.connection.resource_name}
    return Result(payload, [f"applied '{p['label']}' to CH{ch}" for ch in channels])


# ---------------------------------------------------------------------------
# arbitrary waveforms
# ---------------------------------------------------------------------------

# The generator dialog's shapes, their parameters, and where the auto default
# comes from. Time parameters are fractions of the SHAPE period, which is the
# output period for a unipolar shape and half of it for a bipolar one.
ARB_SHAPES: Dict[str, Dict[str, Any]] = {
    "square": {"params": [("--on-time", "time", "50% of the shape period")],
               "generator": "WaveformGenerator.square(points, duty_pct)"},
    "sine": {"params": [("--phase", "degrees", "0")],
             "generator": "WaveformGenerator.sine(points, phase_deg)"},
    "ramp": {"params": [("--rise-time", "time", "100% of the shape period "
                         "(a rising sawtooth)")],
             "generator": "WaveformGenerator.ramp(points, symmetry_pct)"},
    "trapezoid": {"params": [("--rise-time", "time", "20% of the shape period"),
                             ("--pulse-time", "time",
                              "shape period minus rise and fall"),
                             ("--fall-time", "time", "20% of the shape period")],
                  "generator": "WaveformGenerator.trapezoid(points, r%, p%, f%)"},
    "pulse": {"params": [("--on-time", "time", "10% of the shape period"),
                         ("--rise-time", "time", "5% of the shape period"),
                         ("--fall-time", "time", "5% of the shape period")],
              "generator": "WaveformGenerator.pulse(points, w%, r%, f%)"},
    "sinc": {"params": [("--lobes", "count", "5")],
             "generator": "WaveformGenerator.sinc(points, lobes)"},
    "exponential": {"params": [("--tau", "time", "20% of the shape period")],
                    "generator": "WaveformGenerator.exponential_decay(points, tau%)"},
    "gaussian": {"params": [("--sigma", "time", "30% of the shape period")],
                 "generator": "WaveformGenerator.gaussian(points, sigma%)"},
}


def _arb_modules():
    """Import the numpy-backed waveform maths only when a command needs it."""
    try:
        from . import arbitrary as arb
    except Exception as e:  # pragma: no cover - depends on the host
        raise CliError(f"arbitrary-waveform support needs numpy: {e}")
    return arb


def _sidecar_path(csv_path: str) -> str:
    return os.path.splitext(csv_path)[0] + ".comb.json"


def _write_comb_sidecar(csv_path: str, wf,
                        design_frequency: Optional[float] = None) -> Optional[str]:
    """Persist a generated waveform's design metadata beside the CSV.

    Neither the Rigol CSV nor the RAF format has anywhere to put the tone list,
    the phases, the fundamental, or -- for every other shape -- the frequency
    the samples were SHAPED for. The GUI keeps it in memory and locks the
    channel's frequency box to it (dg822_gui.py _generate_arb), so a shape is
    always driven at the frequency it was designed for; a CLI process ends, so
    it goes in a sidecar the upload reads back.

    This used to be written only when the waveform carried ``comb_info``, so the
    eight basic shapes lost their frequency entirely and ``arb upload`` fell
    through to DEFAULT_FREQUENCY_HZ without a word. A gaussian shaped for 5 kHz
    then played at 1 kHz -- a sigma five times wider than asked for, reported as
    "1 kHz (default)" as though that were the intent.
    """
    info = getattr(wf, "comb_info", None)
    if not info and design_frequency is None:
        return None
    path = os.path.abspath(_sidecar_path(csv_path))
    document = {
        "name": wf.name,
        "description": wf.description,
        "num_points": int(wf.num_points),
        "output_frequency_hz": (float(design_frequency)
                                if design_frequency is not None else None),
        "comb_frequencies": [float(f) for f in getattr(wf, "comb_frequencies", [])],
        "comb_phases": [float(p) for p in getattr(wf, "comb_phases", [])],
        "comb_info": _jsonable(dict(info)) if info else None,
    }
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(document, fh, indent=2)
    return path


def _read_comb_sidecar(csv_path: str) -> Optional[Dict[str, Any]]:
    path = _sidecar_path(csv_path)
    if not os.path.isfile(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except Exception:
        return None


def _save_waveform(ctx: Ctx, wf, out_path: str, amplitude_vpp: float,
                   write_raf: bool = True,
                   design_frequency: Optional[float] = None) -> Dict[str, Any]:
    directory = os.path.dirname(os.path.abspath(out_path))
    os.makedirs(directory, exist_ok=True)
    wf.save_csv(out_path, amplitude_vpp=amplitude_vpp)
    written = {"csv": os.path.abspath(out_path)}
    if write_raf:
        # The GUI's "Save CSV..." always writes the .raf sibling; keep the pair
        # together so a file copied to a USB stick is loadable by the instrument.
        raf = os.path.splitext(out_path)[0] + ".raf"
        wf.save_binary(raf, amplitude_vpp=amplitude_vpp)
        written["raf"] = os.path.abspath(raf)
    sidecar = _write_comb_sidecar(out_path, wf, design_frequency)
    if sidecar:
        written["sidecar"] = sidecar
    return written


def cmd_arb_shapes(ctx: Ctx) -> Result:
    arb = _arb_modules()
    shapes = []
    lines = []
    for name, spec in ARB_SHAPES.items():
        entry = {
            "shape": name,
            "generator": spec["generator"],
            "parameters": [{"flag": f, "kind": k, "default": d}
                           for f, k, d in spec["params"]],
        }
        shapes.append(entry)
        lines.append(f"{name}")
        for flag, kind, default in spec["params"]:
            lines.append(f"    {flag:<14} {kind:<8} default: {default}")
    lines.append("frequency-comb  (its own command: 'arb comb')")
    lines.append("    --start/--stop/--step or --list, --phases, --iterations")
    lines.append("")
    lines.extend(kv([
        ("shared flags", "--polarity unipolar|bipolar, --drive frequency|time, "
                         "--freq/--period, --points, --name, -o"),
        ("point budget", f"{MIN_ARB_POINTS}-{MAX_ARB_POINTS} points, auto-chosen as "
                         f"clamp(floor(30e6/f), {MIN_ARB_POINTS}, {MAX_ARB_POINTS})"),
        ("sample rate", f"{arb.DG822_MIN_SAMPLE_RATE:g}-{arb.DG822_MAX_SAMPLE_RATE:g} Sa/s"),
    ]))
    return Result({"shapes": shapes,
                   "min_points": MIN_ARB_POINTS,
                   "max_points": MAX_ARB_POINTS,
                   "min_sample_rate": arb.DG822_MIN_SAMPLE_RATE,
                   "max_sample_rate": arb.DG822_MAX_SAMPLE_RATE}, lines)


def _drive_frequency(ctx: Ctx) -> Tuple[float, str]:
    """Resolve --drive/--freq/--period into an output frequency in Hz."""
    args = ctx.args
    if args.drive == "frequency":
        if args.freq is None:
            raise CliError("--drive frequency needs --freq")
        if args.period is not None:
            ctx.warn("--period ignored under --drive frequency")
        return parse_frequency(args.freq), "frequency"

    if args.period is None:
        raise CliError("--drive time needs --period")
    if args.freq is not None:
        ctx.warn("--freq ignored under --drive time")
    period = parse_duration(args.period, "--period", default_unit="s")
    if period <= 0:
        raise CliError("--period must be greater than zero")
    # In bipolar time mode the entry is the HALF period: the shape itself runs
    # for that long and is then mirrored, so the output period is twice it.
    if args.polarity == "bipolar":
        return 1.0 / (2.0 * period), "time"
    return 1.0 / period, "time"


def cmd_arb_generate(ctx: Ctx) -> Result:
    arb = _arb_modules()
    args = ctx.args
    shape = args.shape
    if shape not in ARB_SHAPES:
        raise CliError(f"unknown shape {shape!r}; run 'arb shapes'")

    frequency, drive = _drive_frequency(ctx)
    check_frequency_range(ctx, frequency)
    bipolar = args.polarity == "bipolar"

    points = (arb.compute_optimal_points(frequency) if args.points is None
              else int(args.points))
    if not (MIN_ARB_POINTS <= points <= MAX_ARB_POINTS):
        raise CliError(f"--points: {points} is outside "
                       f"{MIN_ARB_POINTS}-{MAX_ARB_POINTS}")

    feasibility = arb.check_frequency_feasibility(frequency, points)
    if feasibility.get("warning"):
        ctx.warn(feasibility["warning"].replace("\n", " "))

    period = 1.0 / frequency
    shape_period = period / 2.0 if bipolar else period
    # Bipolar spends half the point budget on the base shape and interpolates the
    # mirrored pair back up to the full count.
    gen_points = max(points // 2, MIN_ARB_POINTS) if bipolar else points

    def time_param(flag: str, value: Optional[str], default_s: float) -> float:
        if value is None:
            return default_s
        return parse_duration(value, flag, default_unit="s")

    def pct(seconds: float) -> float:
        return seconds / shape_period * 100.0

    gen = arb.WaveformGenerator
    resolved: Dict[str, Any] = {}

    if shape == "square":
        on = time_param("--on-time", args.on_time, shape_period * 0.5)
        resolved = {"on_time_s": on, "duty_pct": pct(on)}
        wf = gen.square(gen_points, pct(on))
    elif shape == "sine":
        phase = 0.0 if args.phase is None else float(args.phase)
        resolved = {"phase_deg": phase}
        wf = gen.sine(gen_points, phase)
    elif shape == "ramp":
        rise = time_param("--rise-time", args.rise_time, shape_period)
        resolved = {"rise_time_s": rise, "symmetry_pct": pct(rise)}
        wf = gen.ramp(gen_points, pct(rise))
    elif shape == "trapezoid":
        rise = time_param("--rise-time", args.rise_time, shape_period * 0.2)
        fall = time_param("--fall-time", args.fall_time, shape_period * 0.2)
        auto_pulse = max(0.0, shape_period - rise - fall)
        if args.pulse_time is None:
            pulse = auto_pulse
        else:
            pulse = time_param("--pulse-time", args.pulse_time, auto_pulse)
            if rise + pulse + fall > shape_period * 1.001:
                ctx.warn(
                    f"rise + pulse + fall = {fmt_seconds(rise + pulse + fall)} "
                    f"exceeds the shape period {fmt_seconds(shape_period)}; "
                    f"the generator rescales all three to fit "
                    f"(the fitting pulse time would be {fmt_seconds(auto_pulse)})")
        resolved = {"rise_time_s": rise, "pulse_time_s": pulse, "fall_time_s": fall,
                    "auto_pulse_time_s": auto_pulse,
                    "rise_pct": pct(rise), "pulse_pct": pct(pulse),
                    "fall_pct": pct(fall)}
        wf = gen.trapezoid(gen_points, pct(rise), pct(pulse), pct(fall))
    elif shape == "pulse":
        on = time_param("--on-time", args.on_time, shape_period * 0.1)
        rise = time_param("--rise-time", args.rise_time, shape_period * 0.05)
        fall = time_param("--fall-time", args.fall_time, shape_period * 0.05)
        resolved = {"on_time_s": on, "rise_time_s": rise, "fall_time_s": fall,
                    "on_pct": pct(on), "rise_pct": pct(rise), "fall_pct": pct(fall)}
        wf = gen.pulse(gen_points, pct(on), pct(rise), pct(fall))
    elif shape == "sinc":
        lobes = 5 if args.lobes is None else int(args.lobes)
        if lobes < 1:
            raise CliError("--lobes must be at least 1")
        resolved = {"lobes": lobes}
        wf = gen.sinc(gen_points, lobes)
    elif shape == "exponential":
        tau = time_param("--tau", args.tau, shape_period * 0.2)
        resolved = {"tau_s": tau, "tau_pct": pct(tau)}
        # The dialog's "exponential" is decay only; exponential_rise exists in
        # the generator but no GUI control reaches it.
        wf = gen.exponential_decay(gen_points, pct(tau))
    elif shape == "gaussian":
        sigma = time_param("--sigma", args.sigma, shape_period * 0.3)
        resolved = {"sigma_s": sigma, "sigma_pct": pct(sigma)}
        wf = gen.gaussian(gen_points, pct(sigma))
    else:  # pragma: no cover - guarded by the choices list
        raise CliError(f"unknown shape {shape!r}")

    if bipolar:
        wf = gen.make_bipolar(wf, total_points=points)
    if args.name:
        wf.name = str(args.name)[:12]

    data = wf.data
    payload: Dict[str, Any] = {
        "shape": shape,
        "name": wf.name,
        "description": wf.description,
        "polarity": args.polarity,
        "drive": drive,
        "output_frequency_hz": frequency,
        "period_s": period,
        "shape_period_s": shape_period,
        "points": int(wf.num_points),
        "generator_points": gen_points,
        "sample_rate": frequency * wf.num_points,
        "feasible": bool(feasibility.get("achievable")),
        "min": float(min(data)),
        "max": float(max(data)),
        "params": resolved,
    }

    if args.output:
        payload["files"] = _save_waveform(ctx, wf, args.output, args.ampl,
                                          design_frequency=frequency)

    rows: List[Tuple[str, Any]] = [
        ("shape", shape),
        ("name", wf.name),
        ("polarity", args.polarity),
        ("drive", drive),
        ("output frequency", fmt_hz(frequency)),
        ("period", fmt_seconds(period)),
        ("shape period", fmt_seconds(shape_period)),
        ("points", payload["points"]),
        ("sample rate", fmt_sample_rate(payload['sample_rate'])),
        ("range", f"{payload['min']:+.4f} .. {payload['max']:+.4f}"),
    ]
    for key, value in resolved.items():
        label = key.replace("_", " ")
        if key.endswith("_s"):
            rows.append((label[:-2].strip(), fmt_seconds(value)))
        else:
            rows.append((label, f"{value:g}" if isinstance(value, float) else value))
    if args.output:
        rows.extend(payload["files"].items())
    lines = kv(rows)
    if not args.output and not ctx.args.json:
        lines.append("")
        lines.append("(nothing written; pass -o FILE.csv to save)")
    return Result(payload, lines)


def cmd_arb_comb(ctx: Ctx) -> Result:
    arb = _arb_modules()
    args = ctx.args

    if args.list is not None:
        try:
            freqs = [float(tok) for tok in str(args.list).replace(";", ",").split(",")
                     if tok.strip()]
        except ValueError as e:
            raise CliError(f"--list: {e}")
        source = "list"
    else:
        missing = [flag for flag, value in (("--start", args.start),
                                            ("--stop", args.stop),
                                            ("--step", args.step)) if value is None]
        if missing:
            raise CliError(f"give --list, or all of --start/--stop/--step "
                           f"(missing {', '.join(missing)})")
        if args.step <= 0:
            raise CliError("--step must be greater than zero")
        # The half-step guard is what makes --stop inclusive, matching the dialog.
        import numpy as np
        freqs = [float(f) for f in
                 np.arange(args.start, args.stop + args.step / 2.0, args.step)]
        source = "range"

    if not freqs:
        raise CliError("no frequencies specified")
    if any(f <= 0 for f in freqs):
        raise CliError("all comb frequencies must be positive")

    random_phases = args.phases == "random"
    iterations = int(args.iterations) if random_phases else 1
    if random_phases and iterations < 1:
        # monte_carlo_iterations=0 leaves the generator with no best signal and
        # it fails on the normalisation step; refuse before it gets there.
        raise CliError("--iterations must be at least 1")

    try:
        num_points, info = arb.compute_optimal_points_for_comb(freqs)
    except ValueError as e:
        raise CliError(f"comb: {e}")
    if args.points is not None:
        num_points = int(args.points)
        if not (MIN_ARB_POINTS <= num_points <= MAX_ARB_POINTS):
            raise CliError(f"--points: {num_points} is outside "
                           f"{MIN_ARB_POINTS}-{MAX_ARB_POINTS}")

    if info.get("warning"):
        ctx.warn(info["warning"].replace("\n", " "))
    # _approximate_gcd gives up on near-incommensurate tones and returns
    # min(freqs) instead. The tell is that the other tones then no longer divide
    # into whole harmonics of it, so the waveform is not one whole period of
    # anything and the loop steps at the wrap. The GUI never says so.
    ratios = [f / info["fundamental"] for f in freqs]
    if any(abs(r - round(r)) > 1e-6 for r in ratios):
        ctx.warn(f"the tones are not whole harmonics of the fundamental "
                 f"{info['fundamental']:.6g} Hz, so the GCD search fell back to "
                 f"the lowest tone: this waveform is not one whole period and "
                 f"the output will step at the loop wrap")

    if args.seed is not None:
        # The generator's Monte Carlo draw is unseeded, so two identical
        # invocations give different phases. A caller that needs the same comb
        # twice seeds it here.
        import numpy as np
        np.random.seed(int(args.seed))

    try:
        wf = arb.WaveformGenerator.frequency_comb(
            frequencies=freqs,
            num_points=num_points,
            random_phases=random_phases,
            monte_carlo_iterations=iterations)
    except ValueError as e:
        raise CliError(f"comb: {e}")

    if args.name:
        wf.name = str(args.name)[:12]

    comb_info = dict(wf.comb_info)
    data = wf.data
    payload: Dict[str, Any] = {
        "name": wf.name,
        "description": wf.description,
        "source": source,
        "frequencies": freqs,
        "tones": len(freqs),
        "phases": args.phases,
        "iterations": iterations,
        "seed": args.seed,
        "fundamental_hz": float(comb_info["fundamental"]),
        "f_max_hz": float(comb_info["f_max"]),
        "harmonics": float(comb_info["harmonics"]),
        "min_points_needed": int(comb_info["min_points_needed"]),
        "max_points_available": int(comb_info["max_points_available"]),
        "points": int(wf.num_points),
        "sample_rate": float(comb_info["sample_rate"]),
        "comb_phases_rad": [float(p) for p in wf.comb_phases],
        "min": float(min(data)),
        "max": float(max(data)),
    }

    if args.output:
        payload["files"] = _save_waveform(ctx, wf, args.output, args.ampl,
                                          design_frequency=frequency)

    lines = kv([
        ("tones", f"{len(freqs)} ({freqs[0]:g} .. {freqs[-1]:g} Hz)"),
        ("fundamental", fmt_hz(payload["fundamental_hz"])),
        ("highest tone", fmt_hz(payload["f_max_hz"])),
        ("harmonics in period", f"{payload['harmonics']:.1f} cycles"),
        ("min points needed", payload["min_points_needed"]),
        ("points", payload["points"]),
        ("sample rate", fmt_sample_rate(payload['sample_rate'])),
        ("phases", f"{args.phases} ({iterations} Monte Carlo iteration"
                   f"{'' if iterations == 1 else 's'})"),
        ("range", f"{payload['min']:+.4f} .. {payload['max']:+.4f}"),
    ])
    if args.output:
        lines.extend(kv([(k, v) for k, v in payload["files"].items()]))
    if not args.output and not ctx.args.json:
        lines.append("")
        lines.append("(nothing written; pass -o FILE.csv to save)")
    return Result(payload, lines)


def _load_arb_file(path: str):
    arb = _arb_modules()
    if not os.path.isfile(path):
        raise CliError(f"no such file: {path}")
    wf = arb.ArbitraryWaveform.from_csv(path)
    # from_csv discards the loader's return value, so a file it could not parse
    # comes back as a correctly-named waveform holding nothing.
    if wf.data is None or len(wf.data) == 0:
        raise CliError(f"{path}: no samples parsed (expected a Rigol CSV or one "
                       f"float per line)")
    return wf


def cmd_arb_preview(ctx: Ctx) -> Result:
    args = ctx.args
    wf = _load_arb_file(args.file)
    sidecar = _read_comb_sidecar(args.file)

    frequency = None
    frequency_source = "default"
    if args.freq is not None:
        frequency = parse_frequency(args.freq)
        frequency_source = "--freq"
    elif sidecar and sidecar.get("comb_info"):
        frequency = float(sidecar["comb_info"]["fundamental"])
        frequency_source = "comb sidecar fundamental"
    elif sidecar and sidecar.get("output_frequency_hz"):
        frequency = float(sidecar["output_frequency_hz"])
        frequency_source = "sidecar design frequency"
    if frequency is None:
        frequency = DEFAULT_FREQUENCY_HZ

    from .plot import WaveformPlotter
    t, v = WaveformPlotter.generate_arbitrary(
        wf.data, frequency, amplitude=args.ampl, offset=args.offset,
        num_cycles=args.cycles)

    data = [float(x) for x in wf.data]
    import numpy as np
    payload: Dict[str, Any] = {
        "file": os.path.abspath(args.file),
        "name": wf.name,
        "points": int(wf.num_points),
        "valid_for_upload": bool(wf.is_valid),
        "frequency_hz": frequency,
        "frequency_source": frequency_source,
        "amplitude_vpp": args.ampl,
        "offset_v": args.offset,
        "cycles": args.cycles,
        "min": min(data),
        "max": max(data),
        "rms": float(np.sqrt(np.mean(np.square(wf.data)))),
        "duration_s": float(t[-1]) if len(t) else 0.0,
    }
    if sidecar and sidecar.get("comb_info"):
        payload["comb"] = {
            "frequencies": sidecar.get("comb_frequencies"),
            "fundamental_hz": sidecar["comb_info"].get("fundamental"),
        }
    if not wf.is_valid:
        ctx.warn(f"{wf.num_points} points is outside the uploadable range "
                 f"{MIN_ARB_POINTS}-{MAX_ARB_POINTS}")

    if args.json_samples or ctx.args.json:
        payload["samples"] = data
        payload["voltage_preview"] = [float(x) for x in v]

    lines = kv([
        ("file", payload["file"]),
        ("name", wf.name),
        ("points", payload["points"]),
        ("range", f"{payload['min']:+.4f} .. {payload['max']:+.4f} (normalized)"),
        ("rms", f"{payload['rms']:.4f}"),
        ("frequency", f"{fmt_hz(frequency)} ({frequency_source})"),
        ("shown", f"{args.cycles} cycle(s), {fmt_seconds(payload['duration_s'])}, "
                  f"{args.ampl:g} Vpp, offset {args.offset:g} V"),
    ])

    if args.png:
        plotter = WaveformPlotter()
        plotter.create_figure(figsize=(8, 3), dpi=120)
        plotter.plot_data(t, v, title=f"{wf.name} ({payload['points']} pts)",
                          channel=1)
        directory = os.path.dirname(os.path.abspath(args.png))
        os.makedirs(directory, exist_ok=True)
        plotter.save(args.png)
        payload["png"] = os.path.abspath(args.png)
        lines.extend(kv([("png", payload["png"])]))
    else:
        lines.append("")
        lines.extend(ascii_waveform([float(x) for x in v],
                                    width=args.width, height=args.height))
        lines.append(f"{'':>9}  0 s{' ' * max(0, args.width - 16)}"
                     f"{fmt_seconds(payload['duration_s'])}")
    return Result(payload, lines)


def cmd_arb_upload(ctx: Ctx) -> Result:
    args = ctx.args
    channel = int(args.channel)
    wf = _load_arb_file(args.file)
    points = int(wf.num_points)
    if not (MIN_ARB_POINTS <= points <= MAX_ARB_POINTS):
        raise CliError(f"{args.file}: {points} points is outside the DG822's "
                       f"{MIN_ARB_POINTS}-{MAX_ARB_POINTS} single-packet limit")

    sidecar = _read_comb_sidecar(args.file)
    if args.freq is not None:
        frequency = parse_frequency(args.freq)
        frequency_source = "--freq"
    elif sidecar and sidecar.get("comb_info"):
        # The comb's output frequency IS its fundamental; the GUI reads it off
        # the in-memory comb_info, this reads it off the sidecar.
        frequency = float(sidecar["comb_info"]["fundamental"])
        frequency_source = "comb sidecar fundamental"
    elif sidecar and sidecar.get("output_frequency_hz"):
        # Every other shape: the frequency it was designed for. Without this the
        # shape plays at DEFAULT_FREQUENCY_HZ and every time constant in it
        # (sigma, rise time, on time) is wrong by frequency/1000.
        frequency = float(sidecar["output_frequency_hz"])
        frequency_source = "sidecar design frequency"
    else:
        frequency = DEFAULT_FREQUENCY_HZ
        frequency_source = "default"
    check_frequency_range(ctx, frequency)

    name = (args.name or wf.name or "CUSTOM")
    raf_name = name[:7].upper()
    sample_rate = frequency * points
    if not (2e3 <= sample_rate <= 30e6):
        ctx.warn(f"sample rate {sample_rate:.6g} Sa/s is outside the instrument's "
                 f"2 kSa/s - 30 MSa/s range; apply_arbitrary clamps it, so the "
                 f"real output frequency will not be {fmt_hz(frequency)}")

    payload: Dict[str, Any] = {
        "channel": channel,
        "file": os.path.abspath(args.file),
        "name": name,
        "points": points,
        "frequency_hz": frequency,
        "frequency_source": frequency_source,
        "sample_rate": sample_rate,
        "amplitude_vpp": args.ampl,
        "offset_v": args.offset,
        "phase_deg": args.phase,
        "data_min": float(min(wf.data)),
        "data_max": float(max(wf.data)),
    }

    with instrument(ctx) as dg:
        wave = dg.waveform
        mode_before = wave.get_function(channel)
        payload["mode_before"] = mode_before
        if mode_before and mode_before.upper() in ("USER", "SEQUENCE", "SEQ"):
            # Firmware 00.02.x keeps the previous arb in DDRIII and a fresh DAC16
            # upload can composite with it. Dropping to SIN first clears the
            # buffer. This is the step the GUI's Apply path skips and its Upload
            # button performs.
            wave.set_function(channel, WaveformType.SINE)
            time.sleep(0.3)
            payload["cleared_arb_buffer"] = True
        else:
            payload["cleared_arb_buffer"] = False

        _require(wave.upload_arbitrary_waveform_from_object(channel, wf),
                 f"DAC16 upload of {points} points to CH{channel}")
        fail_on_instrument_error(ctx, dg, f"uploading {points} points")
        time.sleep(0.2)

        mode_after = wave.get_function(channel)
        payload["mode_after"] = mode_after
        # DAC16 VOLATILE,END auto-switches the channel into an arbitrary mode,
        # and WHICH one is firmware-dependent: USER on >= 00.02.x, SEQUENCE on
        # <= 00.01.x (see DG822Waveform.apply_arbitrary, which branches on
        # exactly this to choose :FREQuency vs :FUNCtion:SEQuence:SRATe). This
        # used to demand SEQUENCE and warn on USER -- i.e. warn on the correct
        # answer for the firmware this driver targets.
        arb_mode = (mode_after or "").upper()
        if not any(m in arb_mode for m in ("USER", "SEQ")):
            ctx.warn(f"CH{channel} did not switch to an arbitrary mode after the "
                     f"upload (got {mode_after!r}, expected USER or SEQUENCE); on "
                     f"hardware the END flag switches it, so check the output "
                     f"before trusting it")

        if args.save_raf:
            _require(wave.store_arb_file(raf_name),
                     f'store "{raf_name}.RAF" in instrument memory')
            fail_on_instrument_error(ctx, dg, f'storing "{raf_name}.RAF"')
            payload["stored_raf"] = f"{raf_name}.RAF"
        else:
            payload["stored_raf"] = None

        _require(wave.apply_arbitrary(channel, frequency, args.ampl, args.offset,
                                      args.phase, num_points=points),
                 f"set arbitrary parameters on CH{channel}")
        payload["mode_final"] = wave.get_function(channel)
        payload["resource"] = dg.connection.resource_name

    lines = kv([
        ("channel", channel),
        ("file", payload["file"]),
        ("name", name),
        ("points", points),
        ("frequency", f"{fmt_hz(frequency)} ({frequency_source})"),
        ("sample rate", fmt_sample_rate(sample_rate)),
        ("amplitude", fmt_value(args.ampl, "Vpp")),
        ("offset", fmt_value(args.offset, "V")),
        ("phase", fmt_value(args.phase, "deg")),
        ("mode", f"{payload['mode_before']} -> {payload['mode_after']} "
                 f"-> {payload['mode_final']}"),
        ("stored", payload["stored_raf"] or "not stored (pass --save-raf)"),
    ])
    return Result(payload, lines)


def _parse_catalog(catalog: Optional[str]) -> List[str]:
    if not catalog:
        return []
    return [token.strip().strip('"') for token in catalog.split(",") if token.strip()]


def cmd_arb_files(ctx: Ctx) -> Result:
    args = ctx.args
    directory = os.path.abspath(args.dir or WAVEFORM_DIR)
    local = []
    for path in sorted(glob.glob(os.path.join(directory, "*.csv"))):
        entry = {"path": path, "name": os.path.basename(path),
                 "bytes": os.path.getsize(path)}
        try:
            wf = _arb_modules().ArbitraryWaveform.from_csv(path)
            entry["points"] = int(wf.num_points)
        except Exception:
            entry["points"] = None
        entry["comb_sidecar"] = os.path.isfile(_sidecar_path(path))
        entry["raf"] = os.path.isfile(os.path.splitext(path)[0] + ".raf")
        local.append(entry)

    payload: Dict[str, Any] = {"directory": directory, "local": local,
                               "local_count": len(local)}
    lines = kv([("local directory", directory), ("local CSVs", len(local))])
    for e in local:
        flags = "".join(["+raf" if e["raf"] else "", " +comb" if e["comb_sidecar"] else ""])
        lines.append(f"  {e['name']:<24} {str(e['points'] or '?'):>6} pts  {flags}")

    if args.local_only:
        payload["instrument"] = None
        return Result(payload, lines)

    with instrument(ctx) as dg:
        catalog = dg.waveform.list_arb_files(args.instrument_dir)
        volatile = dg.waveform.list_arbitrary_waveforms(int(args.channel))
        payload["instrument"] = {
            "directory": args.instrument_dir,
            "catalog_raw": catalog,
            "files": _parse_catalog(catalog),
            "volatile_catalog": volatile,
        }
        payload["resource"] = dg.connection.resource_name

    lines.append("")
    lines.extend(kv([("instrument volume", args.instrument_dir),
                     ("RAF files", len(payload["instrument"]["files"]) or "none")]))
    for name in payload["instrument"]["files"]:
        lines.append(f"  {name}")
    return Result(payload, lines)


def cmd_arb_store(ctx: Ctx) -> Result:
    name = str(ctx.args.name)
    raf_name = name[:7].upper()
    if len(name) > 7:
        ctx.warn(f"instrument .RAF names are 7 characters; {name!r} stored as "
                 f"{raf_name!r}")
    with instrument(ctx) as dg:
        _require(dg.waveform.store_arb_file(raf_name, ctx.args.instrument_dir),
                 f'store "{raf_name}.RAF"')
        fail_on_instrument_error(ctx, dg, f'storing "{raf_name}.RAF"')
        payload = {"name": raf_name, "file": f"{raf_name}.RAF",
                   "directory": ctx.args.instrument_dir,
                   "resource": dg.connection.resource_name}
    return Result(payload, [f"stored {ctx.args.instrument_dir}{raf_name}.RAF"])


def cmd_arb_load(ctx: Ctx) -> Result:
    name = str(ctx.args.name)
    with instrument(ctx) as dg:
        _require(dg.waveform.load_arb_file(name, ctx.args.instrument_dir),
                 f"load {name} from instrument memory")
        fail_on_instrument_error(ctx, dg, f"loading {name}")
        payload = {"name": name, "directory": ctx.args.instrument_dir,
                   "function": dg.waveform.get_function(int(ctx.args.channel)),
                   "resource": dg.connection.resource_name}
    return Result(payload, kv([("loaded", name),
                               ("function", payload["function"])]))


def cmd_arb_delete(ctx: Ctx) -> Result:
    name = str(ctx.args.name)
    if ctx.args.local:
        path = name if os.path.isabs(name) else os.path.join(WAVEFORM_DIR, name)
        if not os.path.isfile(path):
            raise CliError(f"no such local file: {path}")
        removed = [path]
        os.remove(path)
        for sibling in (os.path.splitext(path)[0] + ".raf", _sidecar_path(path)):
            if os.path.isfile(sibling):
                os.remove(sibling)
                removed.append(sibling)
        payload = {"local": True, "removed": removed}
        return Result(payload, [f"removed {p}" for p in removed])

    with instrument(ctx) as dg:
        _require(dg.waveform.delete_arbitrary_waveform(int(ctx.args.channel), name),
                 f"delete {name} from the instrument")
        fail_on_instrument_error(ctx, dg, f"deleting {name}")
        payload = {"local": False, "name": name, "channel": int(ctx.args.channel),
                   "resource": dg.connection.resource_name}
    return Result(payload, [f"deleted {name} from CH{ctx.args.channel}"])


# ---------------------------------------------------------------------------
# selftest
# ---------------------------------------------------------------------------

def cmd_selftest(ctx: Ctx) -> Result:
    """Drive every command path against the simulated instrument.

    This is the regression net for a machine with no DG822 on it: the sim parses
    real SCPI and folds it into per-channel state, so a readback that disagrees
    with the write is a genuine driver or CLI fault, not a stub returning what it
    was told.
    """
    import tempfile

    from .sim import reset_simulated_instrument

    steps: List[Dict[str, Any]] = []

    def step(name: str, fn) -> Any:
        try:
            detail = fn()
            steps.append({"step": name, "ok": True, "detail": detail})
            return detail
        except Exception as e:
            steps.append({"step": name, "ok": False, "detail": f"{type(e).__name__}: {e}"})
            return None

    def close(a: Optional[float], b: float, tol: float = 1e-6) -> bool:
        return a is not None and abs(float(a) - b) <= tol * max(1.0, abs(b))

    reset_simulated_instrument()
    workdir = tempfile.mkdtemp(prefix="dg822-selftest-")
    dg = DG822Controller(SIM_RESOURCE, timeout=ctx.args.timeout, simulate=True)

    def _discover():
        found = dg.discover_devices()
        assert any(r == SIM_RESOURCE for r, _ in found), "sim not offered by discovery"
        return f"{len(found)} device(s)"

    step("discover", _discover)

    def _connect():
        assert dg.connect(SIM_RESOURCE), "connect returned False"
        assert dg.idn == SIM_IDN, f"unexpected IDN {dg.idn!r}"
        return dg.idn

    if step("connect", _connect) is None:
        payload = {"simulated": True, "steps": steps, "passed": 0,
                   "failed": len(steps), "workdir": workdir}
        raise CliError("selftest could not connect to the simulated instrument")

    try:
        step("reset", lambda: (dg.reset() and "*RST accepted") or _fail("*RST refused"))
        step("beep", lambda: (dg.beep() and "beeped") or _fail("beep refused"))

        def _sine():
            assert dg.setup_sine(1, 2500.0, 1.5, 0.25, 30.0), "setup_sine refused"
            assert close(dg.get_frequency(1), 2500.0), "frequency did not read back"
            assert close(dg.get_amplitude(1), 1.5), "amplitude did not read back"
            assert close(dg.get_offset(1), 0.25), "offset did not read back"
            assert close(dg.waveform.get_phase(1), 30.0), "phase did not read back"
            return "CH1 sine 2.5 kHz / 1.5 Vpp verified"

        step("apply sine", _sine)

        def _square():
            assert dg.setup_square(2, 10000.0, 3.3, 1.65, 0.0, 25.0), "setup_square refused"
            duty = dg.waveform.get_square_duty_cycle(2)
            assert close(duty, 25.0), f"duty read back as {duty}"
            return "CH2 square duty 25% verified (APPLy resets it to 50, order matters)"

        step("apply square", _square)

        def _pulse():
            frequency, width = 10000.0, 20e-6
            duty = max(1.0, min(99.0, width * frequency * 100.0))
            assert dg.setup_pulse(1, frequency, 2.0, 0.0, 0.0,
                                  duty_cycle=duty, centered=True), "setup_pulse refused"
            expected = (0.0 + (1.0 - duty / 100.0) * 180.0) % 360.0
            phase = dg.waveform.get_phase(1)
            assert close(phase, expected, 1e-4), f"centring phase {phase} != {expected}"
            return f"CH1 pulse duty {duty:g}% centred at phase {expected:.3f} deg"

        step("apply pulse centred", _pulse)

        def _ramp():
            assert dg.setup_ramp(1, 100.0, 5.0, 0.0, 0.0, 100.0), "setup_ramp refused"
            symmetry = dg.waveform.get_ramp_symmetry(1)
            assert close(symmetry, 100.0), f"symmetry read back as {symmetry}"
            return "CH1 ramp symmetry 100% verified"

        step("apply ramp", _ramp)
        step("apply noise", lambda: (dg.setup_noise(1, 4.0, 0.1) and "CH1 noise 4 Vpp")
             or _fail("setup_noise refused"))

        def _dc():
            assert dg.setup_dc(2, 3.3), "setup_dc refused"
            assert close(dg.get_offset(2), 3.3), "DC level did not read back"
            return "CH2 DC 3.3 V verified"

        step("apply dc", _dc)

        def _setget():
            assert dg.waveform.set_frequency(1, 12345.0), "set_frequency refused"
            assert close(dg.get_frequency(1), 12345.0), "frequency did not read back"
            assert dg.waveform.set_high_level(1, 2.0) and dg.waveform.set_low_level(1, -1.0)
            assert close(dg.get_amplitude(1), 3.0), "high/low did not fold into amplitude"
            assert close(dg.get_offset(1), 0.5), "high/low did not fold into offset"
            return "set/get round-trip verified including high/low levels"

        step("set / get", _setget)

        def _output():
            assert dg.output_on(1), "output_on refused"
            assert dg.is_output_on(1) is True, "output did not read back ON"
            assert dg.output_off(1), "output_off refused"
            assert dg.is_output_on(1) is False, "output did not read back off"
            return "CH1 output on/off verified"

        step("output on / off", _output)

        def _load():
            assert dg.set_load_50_ohm(1), "50 ohm refused"
            assert close(dg.output.get_impedance(1), 50.0), "50 ohm did not read back"
            assert dg.set_load_high_z(1), "high-z refused"
            assert dg.output.get_impedance(1) == float("inf"), "high-z did not read back"
            return "load 50 ohm and High-Z verified"

        step("load impedance", _load)

        def _polarity():
            assert dg.output.set_polarity(1, OutputPolarity.INVERTED), "polarity refused"
            assert dg.output.get_polarity(1) == "INV", "polarity did not read back"
            dg.output.set_polarity(1, OutputPolarity.NORMAL)
            return "polarity inverted/normal verified"

        step("polarity", _polarity)

        def _sync():
            assert dg.output.enable_sync(1), "sync on refused"
            assert dg.output.get_sync_state(1) is True, "sync did not read back on"
            assert dg.output.disable_sync(1), "sync off refused"
            return "sync on/off verified"

        step("sync", _sync)
        step("sync-phases", lambda: (dg.waveform.sync_phases() and "phases synchronized")
             or _fail("sync_phases refused"))

        def _preset():
            p = PRESETS["square-10k-3v3"]
            assert dg.setup_square(1, p["freq"], p["ampl"], p["offset"], p["phase"],
                                   p["duty"]), "preset refused"
            assert close(dg.get_frequency(1), 10000.0), "preset frequency wrong"
            return f"preset square-10k-3v3 applied ({len(PRESETS)} presets defined)"

        step("preset apply", _preset)

        arb = _arb_modules()
        generated = {}

        def _generate():
            frequency = 5000.0
            points = arb.compute_optimal_points(frequency)
            wf = arb.WaveformGenerator.gaussian(points, 30.0)
            generated["wf"] = wf
            assert wf.is_valid, f"{wf.num_points} points is not uploadable"
            return f"gaussian {wf.num_points} pts at {fmt_hz(frequency)}"

        step("arb generate", _generate)

        def _bipolar():
            points = arb.compute_optimal_points(1000.0)
            base = arb.WaveformGenerator.square(max(points // 2, 8), 50.0)
            wf = arb.WaveformGenerator.make_bipolar(base, total_points=points)
            assert wf.num_points == points, f"bipolar gave {wf.num_points} not {points}"
            return f"bipolar square resampled to exactly {points} pts"

        step("arb generate bipolar", _bipolar)

        def _comb():
            freqs = [100.0, 200.0, 300.0]
            num_points, info = arb.compute_optimal_points_for_comb(freqs)
            wf = arb.WaveformGenerator.frequency_comb(
                frequencies=freqs, num_points=num_points,
                random_phases=False, monte_carlo_iterations=1)
            assert close(info["fundamental"], 100.0), "fundamental is not 100 Hz"
            generated["comb"] = wf
            return (f"comb f0 {info['fundamental']:g} Hz, {wf.num_points} pts, "
                    f"{info['sample_rate'] / 1e3:.1f} kSa/s")

        step("arb comb", _comb)

        csv_path = os.path.join(workdir, "selftest.csv")

        def _save():
            wf = generated.get("wf")
            assert wf is not None, "no generated waveform to save"
            wf.save_csv(csv_path, amplitude_vpp=2.0)
            wf.save_binary(os.path.splitext(csv_path)[0] + ".raf", amplitude_vpp=2.0)
            assert os.path.isfile(csv_path), "CSV was not written"
            return f"wrote {os.path.basename(csv_path)} and its .raf sibling"

        step("arb save csv + raf", _save)

        def _roundtrip():
            wf = generated.get("wf")
            loaded = arb.ArbitraryWaveform.from_csv(csv_path)
            assert loaded.data is not None, "CSV did not parse back"
            assert loaded.num_points == wf.num_points, "point count changed on reload"
            worst = max(abs(float(a) - float(b)) for a, b in zip(loaded.data, wf.data))
            assert worst < 1e-6, f"worst sample error {worst:g}"
            return f"CSV round-trip exact to {worst:.2e}"

        step("arb csv round-trip", _roundtrip)

        def _preview():
            loaded = arb.ArbitraryWaveform.from_csv(csv_path)
            lines = ascii_waveform([float(x) for x in loaded.data], width=40, height=9)
            assert len(lines) == 10, "ascii preview did not render"
            assert all(all(ord(c) < 128 for c in line) for line in lines), \
                "ascii preview emitted non-ASCII"
            return f"{len(lines)} lines, ASCII only"

        step("arb preview (ascii)", _preview)

        def _upload():
            wf = generated.get("wf")
            assert wf is not None, "no generated waveform to upload"
            before = dg.waveform.get_function(1)
            if before and before.upper() in ("USER", "SEQUENCE", "SEQ"):
                dg.waveform.set_function(1, WaveformType.SINE)
            assert dg.waveform.upload_arbitrary_waveform_from_object(1, wf), \
                "DAC16 upload refused"
            errors = dg.connection.get_error()
            assert errors and errors.startswith("0,"), f"instrument error queue: {errors}"
            return f"{wf.num_points} points uploaded, error queue clean"

        step("arb upload (DAC16)", _upload)

        def _apply_arb():
            wf = generated.get("wf")
            assert dg.waveform.apply_arbitrary(1, 5000.0, 2.0, 0.0, 0.0,
                                               num_points=wf.num_points), \
                "apply_arbitrary refused"
            assert close(dg.get_amplitude(1), 2.0), "arb amplitude did not read back"
            return "arb frequency/amplitude/offset/phase applied"

        step("arb apply parameters", _apply_arb)

        def _store():
            assert dg.waveform.store_arb_file("SELFTST"), "store refused"
            catalog = dg.waveform.list_arb_files()
            assert catalog and "SELFTST" in catalog.upper(), \
                f"stored file not in catalog: {catalog!r}"
            return f"catalog: {catalog}"

        step("arb store / files", _store)

        def _load_raf():
            assert dg.waveform.load_arb_file("SELFTST"), "load refused"
            return "SELFTST.RAF loaded back into the channel"

        step("arb load", _load_raf)
        step("arb delete", lambda: (dg.waveform.delete_arbitrary_waveform(1, "SELFTST")
                                    and "volatile arb data deleted")
             or _fail("delete refused"))

        def _status():
            state = _channel_state(dg, 1)
            assert state["function"], "no function reported"
            document = json.dumps(_jsonable(state))
            assert "Infinity" not in document and "NaN" not in document, \
                "status payload is not strict JSON"
            return f"{len(state)} fields, strictly JSON-safe"

        step("status payload", _status)

        def _errors():
            # A command the instrument does not know must reach the error queue
            # rather than being silently swallowed -- that property is what makes
            # the sim useful for catching a malformed SCPI string before the bench.
            dg.connection.write(":SOURce1:NOSUCH:COMMand 1")
            reported = dg.connection.get_error()
            assert reported and not reported.startswith("0,"), \
                f"bad command was accepted: {reported!r}"
            dg.connection.clear_status()
            return f"rejected as {reported}"

        step("SCPI error reporting", _errors)

    finally:
        dg.connection.close()

    passed = sum(1 for s in steps if s["ok"])
    failed = len(steps) - passed
    payload = {
        "simulated": True,
        "resource": SIM_RESOURCE,
        "idn": SIM_IDN,
        "steps": steps,
        "total": len(steps),
        "passed": passed,
        "failed": failed,
        "workdir": workdir,
    }

    lines = []
    for s in steps:
        lines.append(f"[{'PASS' if s['ok'] else 'FAIL'}] {s['step']:<26} {s['detail']}")
    lines.append("")
    lines.extend(kv([("total", len(steps)), ("passed", passed), ("failed", failed),
                     ("scratch", workdir)]))
    if failed:
        raise CliError(f"selftest: {failed} of {len(steps)} steps failed "
                       f"({', '.join(s['step'] for s in steps if not s['ok'])})")
    return Result(payload, lines)


def _fail(message: str):
    raise AssertionError(message)


# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------

def _add_global_flags(parser: argparse.ArgumentParser, suppress: bool) -> None:
    """Declare the global flags. Also attached to every subparser as a parent.

    argparse only accepts an option where it is declared, so ``--json`` before
    the subcommand and ``--json`` after it are two different declarations. The
    subparser copies default to SUPPRESS so an omitted flag leaves whatever the
    top-level parse produced instead of resetting it.
    """
    def default(value):
        return argparse.SUPPRESS if suppress else value

    group = parser.add_argument_group(
        "global options" if not suppress
        else "global options (accepted before or after the subcommand)")
    group.add_argument("-r", "--resource", metavar="VISA_ADDR", default=default(None),
                       help="VISA resource, e.g. "
                            "USB0::0x1AB1::0x0643::DG8A204201757::0::INSTR. "
                            f"{SIM_RESOURCE} selects the simulator. "
                            "Omit to discover automatically.")
    group.add_argument("--sim", action="store_true", default=default(False),
                       help="drive the in-process simulated DG822 "
                            "(rigol_dg822.sim); needs no VISA implementation. "
                            "The simulated instrument lives in this process, so "
                            "its state does not survive to the next command")
    group.add_argument("--json", action="store_true", default=default(False),
                       help="emit exactly one JSON object on stdout and nothing "
                            "else; this is the mode for a script or an agent")
    group.add_argument("--timeout", type=int, default=default(5000), metavar="MS",
                       help="VISA I/O timeout in milliseconds (default 5000)")
    group.add_argument("-q", "--quiet", action="store_true", default=default(False),
                       help="suppress the driver's progress chatter (it goes to "
                            "stderr in text mode, and to the JSON 'log' key)")


def _add_channel(parser: argparse.ArgumentParser, default: int = 1,
                 allow_all: bool = False) -> None:
    parser.add_argument("-c", "--channel", type=int, choices=(1, 2), default=default,
                        help="output channel (1 or 2; default %(default)s)")
    if allow_all:
        parser.add_argument("--all", action="store_true",
                            help="apply to both channels instead of --channel")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=PROG,
        description="Control a RIGOL DG822 function generator from the command "
                    "line. Feature parity with the tkinter GUI.",
        epilog="Every command connects, acts and disconnects: VISA is per-process "
               "and stateless, so there is no session to manage. With no "
               "--resource the instrument is discovered automatically; the "
               "simulated DG822 is never chosen implicitly, ask for it with --sim.",
        formatter_class=argparse.RawDescriptionHelpFormatter)

    _add_global_flags(parser, suppress=False)

    # One shared parent so every leaf subparser accepts the global flags too.
    common = argparse.ArgumentParser(add_help=False)
    _add_global_flags(common, suppress=True)

    def add_command(group, name: str, **kwargs) -> argparse.ArgumentParser:
        kwargs["parents"] = list(kwargs.get("parents", ())) + [common]
        return group.add_parser(name, **kwargs)

    subparsers = parser.add_subparsers(dest="command", metavar="<command>")
    subparsers.required = True

    # -- discovery and state ------------------------------------------------
    p = add_command(subparsers, "discover", help="list instruments and report why "
                                               "VISA is or is not available")
    p.set_defaults(handler=cmd_discover)

    p = add_command(subparsers, "idn", help="identify the instrument (*IDN?)")
    p.set_defaults(handler=cmd_idn)

    p = add_command(subparsers, 
        "status", help="read back the instrument state",
        description="Query one channel or both. Under --json the whole state is "
                    "dumped: function, frequency, amplitude, offset, phase, "
                    "duties, symmetry, load, polarity, sync and the error queue.")
    p.add_argument("-c", "--channel", type=int, choices=(1, 2), default=None,
                   help="channel to report; omit for both")
    p.set_defaults(handler=cmd_status)

    p = add_command(subparsers, "reset", help="reset the instrument (*RST)")
    p.set_defaults(handler=cmd_reset)

    p = add_command(subparsers, "beep", help="sound the instrument's beeper")
    p.set_defaults(handler=cmd_beep)

    p = add_command(subparsers, 
        "sync-phases", help="align CH2's phase to CH1 (:SOURce1:PHASe:SYNChronize)")
    p.set_defaults(handler=cmd_sync_phases)

    # -- apply --------------------------------------------------------------
    apply_parser = add_command(subparsers, 
        "apply", help="configure a channel's waveform in one command",
        description="One APPLy command per shape, exactly as the GUI's "
                    "'Apply Settings' button issues it.")
    apply_sub = apply_parser.add_subparsers(dest="shape", metavar="<shape>")
    apply_sub.required = True

    # Only the flags a shape actually honours are declared on it. The help is
    # what an agent reads to decide what to send, so offering --symmetry on a
    # pulse would be misinformation. --freq/--phase stay on noise and DC, where
    # the instrument discards them, because a caller sweeping a uniform flag set
    # is better served by a warning than by an argparse rejection.
    shape_spec = {
        "sine": ("sinusoid", ()),
        "square": ("square wave with a settable duty cycle", ("duty",)),
        "ramp": ("ramp/triangle with a settable symmetry", ("symmetry",)),
        "pulse": ("pulse, centred in its period the way the GUI centres it",
                  ("duty", "width")),
        "noise": ("noise; frequency and phase are discarded by the instrument", ()),
        "dc": ("DC level; --offset is the level, everything else is discarded", ()),
    }
    for shape, (help_text, extras) in shape_spec.items():
        sp = add_command(apply_sub, shape, help=help_text, description=help_text)
        _add_channel(sp)
        sp.add_argument("--freq", metavar="EXPR",
                        help="frequency in Hz. Arithmetic is evaluated, so "
                             "'1/0.1' is 10 Hz; a Hz/kHz/MHz suffix is allowed, "
                             f"so '2.5kHz' is 2500. Range "
                             f"{MIN_FREQUENCY_HZ:g}-{MAX_FREQUENCY_HZ:g} Hz. "
                             f"Default {DEFAULT_FREQUENCY_HZ:g} Hz")
        sp.add_argument("--ampl", type=float, metavar="VPP",
                        help=f"amplitude in Vpp, {MIN_AMPLITUDE_VPP:g}-"
                             f"{MAX_AMPLITUDE_VPP:g} into High-Z "
                             f"(default {DEFAULT_AMPLITUDE_VPP:g})")
        sp.add_argument("--offset", type=float, metavar="V",
                        help=("the DC output level in volts (default "
                              f"{DEFAULT_OFFSET_V:g})") if shape == "dc" else
                             f"DC offset in volts (default {DEFAULT_OFFSET_V:g})")
        sp.add_argument("--phase", type=float, metavar="DEG",
                        help=f"start phase in degrees (default {DEFAULT_PHASE_DEG:g})")
        if "duty" in extras and shape == "square":
            sp.add_argument("--duty", type=float, metavar="PCT",
                            help="duty cycle in percent, 0.01-99.99 "
                                 f"(default {DEFAULT_DUTY_PCT:g}). Written after "
                                 "the APPLy, which resets it to 50")
        elif "duty" in extras:
            sp.add_argument("--duty", type=float, metavar="PCT",
                            help="pulse duty cycle in percent, 1-99; an "
                                 "alternative to --width, not a companion to it")
        if "width" in extras:
            sp.add_argument("--width", metavar="TIME",
                            help="pulse width with a ns/us/ms/s suffix, e.g. "
                                 "'20us'. A bare number is microseconds, as in "
                                 f"the GUI (default "
                                 f"{DEFAULT_PULSE_WIDTH_S * 1e6:g}us). The duty "
                                 "is width/period, clamped to 1-99 percent with "
                                 "the clamp reported")
        if "symmetry" in extras:
            sp.add_argument("--symmetry", type=float, metavar="PCT",
                            help="symmetry in percent: 0 falling, 50 triangle, "
                                 "100 rising sawtooth (default "
                                 f"{DEFAULT_SYMMETRY_PCT:g})")
        sp.set_defaults(handler=cmd_apply, shape=shape)

    # -- set / get ----------------------------------------------------------
    p = add_command(subparsers, 
        "set", help="write one parameter",
        description="Write a single parameter without re-issuing an APPLy.\n\n"
                    + "\n".join(f"  {k:<11} {v}" for k, v in _SET_PARAMS.items()),
        formatter_class=argparse.RawDescriptionHelpFormatter)
    _add_channel(p)
    p.add_argument("param", choices=sorted(_SET_PARAMS), help="parameter to write")
    p.add_argument("value", help="new value; expressions and unit suffixes are "
                                 "accepted where the parameter allows them")
    p.set_defaults(handler=cmd_set)

    p = add_command(subparsers, 
        "get", help="read one or more parameters",
        description="Read parameters back from the instrument.\n\n"
                    + "\n".join(f"  {k:<11} {v}" for k, v in _GET_PARAMS.items()),
        formatter_class=argparse.RawDescriptionHelpFormatter)
    _add_channel(p)
    p.add_argument("params", nargs="+", choices=sorted(_GET_PARAMS),
                   metavar="PARAM", help="one or more of: "
                                         + ", ".join(sorted(_GET_PARAMS)))
    p.set_defaults(handler=cmd_get)

    # -- output -------------------------------------------------------------
    p = add_command(subparsers, 
        "output", help="switch an output on or off, optionally for a fixed time",
        description="--for and --cycles are host wall-clock timers, not the "
                    "instrument's burst mode: no :BURSt command is sent, exactly "
                    "as in the GUI, so the cycle count is nominal. Unlike the GUI, "
                    "the output is switched back off even on Ctrl+C.")
    p.add_argument("state", choices=("on", "off"), help="new output state")
    _add_channel(p, allow_all=True)
    p.add_argument("--for", dest="duration", metavar="DURATION",
                   help="run for this long then switch off, blocking until then. "
                        "Suffix ns/us/ms/s/min/hour; a bare number is seconds")
    p.add_argument("--cycles", type=int, metavar="N",
                   help="run for N cycles then switch off. The duration is "
                        "N divided by the channel's current frequency, read from "
                        "the instrument")
    p.set_defaults(handler=cmd_output)

    # -- load / polarity / sync --------------------------------------------
    p = add_command(subparsers, 
        "load", help="set the output load impedance",
        description="Applied immediately, as in the GUI. The DG822 powers up "
                    "High-Z; 50 ohm halves the delivered amplitude into a "
                    "matched load.")
    p.add_argument("setting", nargs="?", choices=("high-z", "50"),
                   help="high-z (:OUTPut:LOAD INFinity) or 50 ohm")
    p.add_argument("--ohms", type=float, metavar="R",
                   help="an arbitrary load in ohms; the driver's range is "
                        "1-10000 and a value outside it is warned about, "
                        "not refused")
    _add_channel(p, allow_all=True)
    p.set_defaults(handler=cmd_load)

    p = add_command(subparsers, "polarity", help="set the output polarity")
    p.add_argument("setting", choices=("normal", "inverted"), help="output polarity")
    _add_channel(p, allow_all=True)
    p.set_defaults(handler=cmd_polarity)

    p = add_command(subparsers, "sync", help="switch the sync output on or off")
    p.add_argument("state", choices=("on", "off"), help="sync output state")
    _add_channel(p, allow_all=True)
    p.set_defaults(handler=cmd_sync)

    # -- presets ------------------------------------------------------------
    preset_parser = add_command(subparsers, 
        "preset", help="the GUI's quick presets",
        description="Every button in the GUI's 'Quick Presets' panel, with the "
                    "same parameters.")
    preset_sub = preset_parser.add_subparsers(dest="preset_command", metavar="<action>")
    preset_sub.required = True

    sp = add_command(preset_sub, "list", help="list the available presets")
    sp.set_defaults(handler=cmd_preset_list)

    sp = add_command(preset_sub, "apply", help="apply a preset to a channel")
    sp.add_argument("preset", choices=sorted(PRESETS), metavar="ID",
                    help="preset id: " + ", ".join(sorted(PRESETS)))
    sp.add_argument("-c", "--channel", choices=("1", "2", "both"), default="1",
                    help="channel to apply to (default %(default)s)")
    sp.set_defaults(handler=cmd_preset_apply)

    # -- arbitrary ----------------------------------------------------------
    arb_parser = add_command(subparsers, 
        "arb", help="arbitrary waveforms: generate, preview, upload, file memory",
        description="The generator dialog, the CSV/RAF file formats and the "
                    "instrument's internal .RAF volume.")
    arb_sub = arb_parser.add_subparsers(dest="arb_command", metavar="<action>")
    arb_sub.required = True

    sp = add_command(arb_sub, "shapes", help="list the generators and their parameters")
    sp.set_defaults(handler=cmd_arb_shapes)

    sp = add_command(arb_sub, 
        "generate", help="synthesise a normalized shape and optionally save it",
        description="Point count is chosen automatically for maximum smoothness: "
                    f"clamp(floor(30e6/f), {MIN_ARB_POINTS}, {MAX_ARB_POINTS}). "
                    "Time parameters are fractions of the SHAPE period, which is "
                    "the output period when unipolar and half of it when bipolar.")
    sp.add_argument("shape", choices=sorted(ARB_SHAPES), metavar="SHAPE",
                    help="one of: " + ", ".join(sorted(ARB_SHAPES))
                         + " (for a frequency comb use 'arb comb')")
    sp.add_argument("--polarity", choices=("unipolar", "bipolar"), default="unipolar",
                    help="bipolar emits the shape then its mirror, so the output "
                         "period is twice the shape period (default %(default)s)")
    sp.add_argument("--drive", choices=("frequency", "time"), default="frequency",
                    help="specify the waveform by --freq or by --period "
                         "(default %(default)s)")
    sp.add_argument("--freq", metavar="EXPR",
                    help="output frequency in Hz under --drive frequency; "
                         "arithmetic and a Hz/kHz/MHz suffix are accepted")
    sp.add_argument("--period", metavar="TIME",
                    help="output period under --drive time (unipolar), or the "
                         "shape's HALF period (bipolar). Suffix ns/us/ms/s")
    sp.add_argument("--on-time", metavar="TIME",
                    help="square/pulse on time; suffix ns/us/ms/s")
    sp.add_argument("--rise-time", metavar="TIME",
                    help="ramp/trapezoid/pulse rise time; suffix ns/us/ms/s")
    sp.add_argument("--pulse-time", metavar="TIME",
                    help="trapezoid flat-top time; defaults to whatever the shape "
                         "period leaves after rise and fall")
    sp.add_argument("--fall-time", metavar="TIME",
                    help="trapezoid/pulse fall time; suffix ns/us/ms/s")
    sp.add_argument("--phase", type=float, metavar="DEG",
                    help="sine phase in degrees (default 0)")
    sp.add_argument("--lobes", type=int, metavar="N",
                    help="sinc lobe count (default 5)")
    sp.add_argument("--tau", metavar="TIME",
                    help="exponential decay time constant; suffix ns/us/ms/s")
    sp.add_argument("--sigma", metavar="TIME",
                    help="gaussian standard deviation; suffix ns/us/ms/s")
    sp.add_argument("--points", type=int, metavar="N",
                    help=f"override the automatic point count "
                         f"({MIN_ARB_POINTS}-{MAX_ARB_POINTS})")
    sp.add_argument("--name", metavar="NAME",
                    help="waveform name, truncated to 12 characters")
    sp.add_argument("--ampl", type=float, default=10.0, metavar="VPP",
                    help="amplitude recorded in the CSV/RAF header only; the "
                         "samples themselves are normalized (default %(default)s)")
    sp.add_argument("-o", "--output", metavar="FILE.csv",
                    help="write a Rigol-compatible CSV, plus a .raf sibling")
    sp.set_defaults(handler=cmd_arb_generate)

    sp = add_command(arb_sub, 
        "comb", help="synthesise a frequency comb (sum of equal-amplitude tones)",
        description="The waveform is one period of the fundamental, which is the "
                    "approximate GCD of the tones. Reports the fundamental, the "
                    "point count, the sample rate and every feasibility warning.")
    sp.add_argument("--start", type=float, metavar="HZ",
                    help="first tone in Hz (with --stop and --step)")
    sp.add_argument("--stop", type=float, metavar="HZ",
                    help="last tone in Hz, inclusive")
    sp.add_argument("--step", type=float, metavar="HZ", help="tone spacing in Hz")
    sp.add_argument("--list", metavar="HZ,HZ,...",
                    help="explicit comma-separated tone list in Hz, instead of "
                         "--start/--stop/--step")
    sp.add_argument("--phases", choices=("random", "zero"), default="random",
                    help="random draws Monte Carlo phase sets and keeps the "
                         "highest-RMS one; zero puts every tone in phase, which "
                         "maximises crest factor (default %(default)s)")
    sp.add_argument("--iterations", type=int, default=1000, metavar="N",
                    help="Monte Carlo iterations when --phases random "
                         "(default %(default)s)")
    sp.add_argument("--seed", type=int, metavar="N",
                    help="seed the phase draw so the same comb comes out twice; "
                         "the generator is otherwise unseeded")
    sp.add_argument("--points", type=int, metavar="N",
                    help=f"override the automatic point count "
                         f"({MIN_ARB_POINTS}-{MAX_ARB_POINTS})")
    sp.add_argument("--name", metavar="NAME", help="waveform name, max 12 characters")
    sp.add_argument("--ampl", type=float, default=10.0, metavar="VPP",
                    help="amplitude recorded in the file header (default %(default)s)")
    sp.add_argument("-o", "--output", metavar="FILE.csv",
                    help="write the CSV, its .raf sibling, and a .comb.json "
                         "sidecar holding the tones and the fundamental (no file "
                         "format has anywhere to put them, and 'arb upload' needs "
                         "the fundamental as the output frequency)")
    sp.set_defaults(handler=cmd_arb_comb)

    sp = add_command(arb_sub, 
        "preview", help="render a CSV waveform without a GUI",
        description="Draws plain ASCII in the terminal by default, which works in "
                    "a bare cmd.exe. --png writes an image instead.")
    sp.add_argument("--file", required=True, metavar="FILE.csv",
                    help="Rigol CSV, or one float per line")
    sp.add_argument("--freq", metavar="EXPR",
                    help="frequency to scale the time axis with; defaults to the "
                         "comb fundamental from a .comb.json sidecar, else "
                         f"{DEFAULT_FREQUENCY_HZ:g} Hz")
    sp.add_argument("--ampl", type=float, default=2.0, metavar="VPP",
                    help="amplitude to scale the preview to (default %(default)s)")
    sp.add_argument("--offset", type=float, default=0.0, metavar="V",
                    help="offset for the preview (default %(default)s)")
    sp.add_argument("--cycles", type=int, default=1, metavar="N",
                    help="cycles to draw (default %(default)s)")
    sp.add_argument("--width", type=int, default=72, metavar="COLS",
                    help="ASCII plot width in columns (default %(default)s)")
    sp.add_argument("--height", type=int, default=17, metavar="ROWS",
                    help="ASCII plot height in rows (default %(default)s)")
    sp.add_argument("--png", metavar="PATH", help="write a PNG instead of ASCII")
    sp.add_argument("--samples", dest="json_samples", action="store_true",
                    help="include the raw samples in the payload (implied by --json)")
    sp.set_defaults(handler=cmd_arb_preview)

    sp = add_command(arb_sub, 
        "upload", help="send a CSV waveform to the instrument",
        description="Clears a stale arbitrary buffer first when the channel is "
                    "already in USER/SEQUENCE mode, uploads via "
                    ":TRACe:DATA:DAC16 VOLATILE,END, then sets frequency, "
                    "amplitude, offset and phase.")
    _add_channel(sp)
    sp.add_argument("--file", required=True, metavar="FILE.csv",
                    help=f"CSV to upload; {MIN_ARB_POINTS}-{MAX_ARB_POINTS} samples")
    sp.add_argument("--name", metavar="NAME",
                    help="name for the instrument's .RAF, truncated to 7 characters")
    sp.add_argument("--save-raf", action="store_true",
                    help="also store the waveform in the instrument's internal "
                         "memory as NAME.RAF, so it survives a power cycle")
    sp.add_argument("--freq", metavar="EXPR",
                    help="output frequency in Hz; defaults to the comb "
                         "fundamental from a .comb.json sidecar, else "
                         f"{DEFAULT_FREQUENCY_HZ:g} Hz. The sample rate is "
                         "frequency x points and must land in 2 kSa/s - 30 MSa/s")
    sp.add_argument("--ampl", type=float, default=DEFAULT_AMPLITUDE_VPP,
                    metavar="VPP", help="amplitude in Vpp (default %(default)s)")
    sp.add_argument("--offset", type=float, default=DEFAULT_OFFSET_V, metavar="V",
                    help="DC offset in volts (default %(default)s)")
    sp.add_argument("--phase", type=float, default=DEFAULT_PHASE_DEG, metavar="DEG",
                    help="start phase in degrees (default %(default)s)")
    sp.set_defaults(handler=cmd_arb_upload)

    sp = add_command(arb_sub, 
        "files", help="list local CSVs and the instrument's .RAF memory")
    sp.add_argument("--dir", metavar="PATH",
                    help=f"local waveform directory (default {WAVEFORM_DIR})")
    sp.add_argument("--local-only", action="store_true",
                    help="skip the instrument, do not connect")
    sp.add_argument("--instrument-dir", default="C:\\", metavar="VOL",
                    help="instrument-internal volume, not a host path "
                         "(default %(default)s)")
    _add_channel(sp)
    sp.set_defaults(handler=cmd_arb_files)

    sp = add_command(arb_sub, 
        "store", help="save the channel's current arbitrary data as NAME.RAF")
    sp.add_argument("name", help="file name, truncated to 7 characters")
    sp.add_argument("--instrument-dir", default="C:\\", metavar="VOL",
                    help="instrument-internal volume (default %(default)s)")
    sp.set_defaults(handler=cmd_arb_store)

    sp = add_command(arb_sub, "load", help="load NAME.RAF from instrument memory")
    sp.add_argument("name", help="file name, with or without the .RAF extension")
    sp.add_argument("--instrument-dir", default="C:\\", metavar="VOL",
                    help="instrument-internal volume (default %(default)s)")
    _add_channel(sp)
    sp.set_defaults(handler=cmd_arb_load)

    sp = add_command(arb_sub, "delete", help="delete a waveform")
    sp.add_argument("name", help="instrument waveform name, or a local file name "
                                 "with --local")
    sp.add_argument("--local", action="store_true",
                    help=f"delete the local CSV (and its .raf and .comb.json "
                         f"siblings) from {WAVEFORM_DIR} instead of the instrument")
    _add_channel(sp)
    sp.set_defaults(handler=cmd_arb_delete)

    # -- selftest -----------------------------------------------------------
    p = add_command(subparsers, 
        "selftest", help="exercise every path against the simulated instrument",
        description="Always runs against rigol_dg822.sim regardless of --sim or "
                    "--resource; it never touches hardware. Exits non-zero if any "
                    "step fails.")
    p.set_defaults(handler=cmd_selftest)

    return parser


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def _emit(args: argparse.Namespace, ok: bool, command: str,
          payload: Dict[str, Any], warnings: List[str], log: List[str],
          error: Optional[str] = None, lines: Optional[List[str]] = None) -> None:
    if args.json:
        document: Dict[str, Any] = {"ok": ok, "command": command}
        if error:
            document["error"] = error
        document.update(payload)
        if warnings:
            document["warnings"] = warnings
        if log and not args.quiet:
            document["log"] = log
        # One object, one line, strict JSON: no NaN, no Infinity, no numpy.
        sys.stdout.write(json.dumps(_jsonable(document)) + "\n")
        return

    if log and not args.quiet:
        # Driver chatter is diagnostic, not the answer -- keep stdout to the
        # answer so a shell pipeline stays usable.
        for line in log:
            print(line, file=sys.stderr)
    if error:
        print(f"error: {error}", file=sys.stderr)
    for line in lines or []:
        print(line)
    for warning in warnings:
        print(f"warning: {warning}", file=sys.stderr)


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    ctx = Ctx(args)

    parts = [args.command]
    for key in ("preset_command", "arb_command", "shape"):
        value = getattr(args, key, None)
        if value:
            parts.append(str(value))
    command = " ".join(parts)

    buffer = io.StringIO()
    result: Optional[Result] = None
    error: Optional[str] = None
    status = EXIT_OK

    try:
        # Every driver module diagnoses itself with print(); capture it so --json
        # keeps its promise of one object on stdout and nothing else.
        with redirect_stdout(buffer):
            result = args.handler(ctx)
    except CliError as e:
        error, status = str(e), EXIT_FAIL
    except KeyboardInterrupt:
        error, status = "interrupted by Ctrl+C", EXIT_INTERRUPTED
    except Exception as e:
        # Nothing reaches the user as a traceback: an agent parsing one is
        # parsing noise, and the driver's own policy is to degrade, not raise.
        error = f"{type(e).__name__}: {e}"
        status = EXIT_FAIL
    else:
        if result is not None and result.error:
            error, status = result.error, result.exit_code

    log = [line for line in buffer.getvalue().splitlines() if line.strip()]
    payload = result.payload if result else {}
    if ctx.instrument_errors:
        payload.setdefault("instrument_errors", ctx.instrument_errors)
    lines = result.lines if result else []
    _emit(args, status == EXIT_OK, command, payload, ctx.warnings, log, error, lines)
    return status


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        sys.exit(EXIT_INTERRUPTED)
