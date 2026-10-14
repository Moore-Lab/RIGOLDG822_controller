"""DG822 control page — the web surface for the RIGOL DG822 function generator.

A FastAPI app that drives one DG822 through :class:`rigol_dg822.DG822Controller`
and serves the browser page that operates it. This is the standalone control
surface; the xsphere-daq panel mounts the same app under ``/rigol``, exactly as
it mounts the camera dock under ``/cameras``.

Run it standalone::

    C:/Users/xbox/anaconda3/python.exe -m rigol_dg822.webapp --sim --port 8010
    C:/Users/xbox/anaconda3/python.exe -m rigol_dg822.webapp --resource USB0::0x1AB1::...

``--sim`` drives rigol_dg822.sim and needs neither hardware nor a VISA
implementation; with neither flag the app discovers USB hardware and takes the
first DG800-series unit it finds.

Mount it from the panel::

    from rigol_dg822 import webapp as rigol
    session = rigol.make_session()                    # or make_session(simulate=True)
    app.mount("/rigol", rigol.create_app(session, manage_lifecycle=False))

``manage_lifecycle=False`` omits the startup/shutdown lifespan, because Starlette
does not run a mounted sub-app's lifespan: the panel calls ``session.start()``
and ``session.stop()`` from its own, so there is exactly one top-level place
that brings the rig up and down. ``stop()`` turns both outputs off *before* it
closes the VISA session — a signal generator left driving a coil or a piezo
after the process exits is a physical hazard, not just an untidy state.

The page derives its API base from ``window.location`` and never hardcodes a
prefix, which is what makes an arbitrary mount point work with no server-side
base-URL configuration (the dock's pages do the same).

HTTP API, all JSON unless stated::

    GET  /                        the page
    GET  /static/{fname}          page assets, Cache-Control: no-cache
    GET  /api/state               whole-instrument state + both channels
    GET  /api/devices             discovered instruments (the simulator last)
    POST /api/connect             {resource?, sim?}          -> state
    POST /api/disconnect                                     -> state
    POST /api/reset               *RST                       -> state
    POST /api/beep                                           -> {ok}
    POST /api/sync-phases         :SOURce1:PHASe:SYNChronize -> {ok}
    POST /api/ch/{n}/apply        one APPLy + its shape parameter   -> CH
    POST /api/ch/{n}/set          any subset of the scalar params   -> CH
    POST /api/ch/{n}/output       {on, seconds?, cycles?}           -> CH
    POST /api/ch/{n}/load         {impedance: "high-z" | ohms}      -> CH
    POST /api/ch/{n}/polarity     {inverted}                        -> CH
    POST /api/ch/{n}/sync         {on}                              -> CH
    GET  /api/ch/{n}/preview      pure-numpy trace for the canvas
    GET  /api/arb/shapes          self-describing generator catalogue
    POST /api/arb/generate        synthesise a normalised buffer
    POST /api/arb/upload          DAC16 upload + apply, to one channel
    GET  /api/arb/files           local waveforms/ + the instrument's C:\\
    POST /api/arb/save-csv        write .csv (and the .raf sibling)
    POST /api/arb/load-csv        read a local .csv back
    POST /api/arb/store-raf       :MMEMory:STORe:DATA
    POST /api/arb/load-raf        :MMEMory:LOAD:DATA          -> CH
    GET  /api/presets             the quick-preset table
    POST /api/presets/apply       {id, channel}               -> CH

CH, the per-channel object every write returns and ``/api/state`` carries two
of: function, frequency, amplitude, offset, phase, duty_cycle, pulse_width,
symmetry, output, impedance, polarity, sync, arb_name, sample_rate, points,
run_mode, off_at (a unix timestamp while a timed run is in flight, else null),
plus ``function_raw`` and ``arb_loaded`` — see ``DG822Session._blank_channel``
for why those two exist. ``impedance`` is a number of ohms or the string
``"high-z"``, because JSON has no Infinity and the /load endpoint takes the same
two forms back.

Error convention, matching the dock: 404 for a thing that does not exist (a
channel other than 1 or 2, an unknown preset, a missing file) · 422 for a value
the instrument cannot accept · 503 when the instrument is not connected or a
SCPI call fails. The body key is always ``detail``. Nothing escapes as a 500
with a traceback: the session layer never raises, and a catch-all handler turns
anything that slips through into a readable 503.

Never-raise, all the way down: this module imports and the app starts with no
VISA implementation present, no instrument attached, and no static assets on
disk. The simulated instrument (``rigol_dg822.sim``) is always offered, so every
endpoint here is exercisable on a machine that has never seen a DG822.

Concurrency: a VISA session is single-owner and NOT thread-safe — two overlapping
writes interleave on the wire and the replies come back to the wrong caller. So
every instrument access goes through ``session.lock``. The path operations are
plain ``def`` rather than ``async def`` on purpose: FastAPI runs those in a
worker thread, so a SCPI call that sits on the driver's 5 s timeout blocks one
pool worker instead of the event loop, and the rest of the page (and the panel
around it) keeps answering.
"""

from __future__ import annotations

import argparse
import math
import os
import re
import threading
import time
import uuid
from collections import OrderedDict
from contextlib import asynccontextmanager
from typing import Dict, List, Optional

import numpy as np
from fastapi import Body, FastAPI, HTTPException
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse

from . import arbitrary as arb
from .arbitrary import ArbitraryWaveform, WaveformGenerator
from .controller import DG822Controller
from .plot import WaveformPlotter
from .sim import SIM_RESOURCE
from .waveform import WaveformType

_STATIC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")

# Host-side waveform library, beside the package (the same directory the tkinter
# GUI's file dialogs default to). The instrument's own store is a different
# thing entirely: ':MMEMory:CDIRectory "C:\"' addresses a volume inside the
# DG822, not a path on this machine.
_WAVEFORMS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                          "waveforms")

CHANNELS = (1, 2)

# The longest timed run the host can actually guarantee. threading.Timer waits
# on a condition variable whose timeout is capped at _thread.TIMEOUT_MAX
# (4294967 s ~ 49.7 days on Windows -- the DWORD-milliseconds ceiling); past it
# t.start() returns normally but the timer thread dies with OverflowError, so
# the output is enabled with NOTHING left to switch it off. That is the exact
# hazard the timed run exists to prevent, so an unschedulable duration is
# refused up front rather than accepted and silently dropped. 24 h is well under
# the ceiling and longer than any run this rig has reason to make; a genuinely
# longer one wants a continuous output the operator ends deliberately, not a
# host timer that a process restart would forget anyway.
MAX_RUN_SECONDS = 24 * 60 * 60

# Instrument limits, mirrored from DG822Waveform (and the same numbers the CLI
# carries). Used for WARNINGS, not refusals -- the policy the CLI states at its
# own limit block and the tkinter GUI follows: the DG822 clamps silently rather
# than erroring, a bench user occasionally means an odd value, and refusing one
# would make the web page stricter than the two front ends beside it. What the
# page must never do is stay SILENT, which is what it did before: an out-of-range
# request returned 200 echoing the value back, so the operator's driven device
# saw a level that was neither what they asked for nor reported as wrong.
MIN_FREQUENCY_HZ, MAX_FREQUENCY_HZ = 1e-6, 25e6
MIN_AMPLITUDE_VPP, MAX_AMPLITUDE_VPP = 1e-3, 20.0

# |offset| + Vpp/2 must stay inside the rail, and the rail halves into 50 ohm.
# The user guide: "The DC offset setting range is limited by the 'Impedance' and
# 'Amplitude/High Level' settings ... the instrument would display a prompt
# message and set the offset to the offset upper limit of the new configuration
# automatically" -- i.e. it substitutes its own value and the host is never told.
MAX_RAIL_HIGH_Z_V, MAX_RAIL_50_OHM_V = 10.0, 5.0

# A generated buffer is up to 8192 float64 samples plus its metadata, and the
# page can generate on every parameter tweak. The cache exists so an upload does
# not have to round-trip the whole buffer back through the browser; it is bounded
# because without a bound a long session pins one buffer per click for the life
# of the process. Eight is far more than the page needs (it uploads the newest)
# and holds the ceiling to well under a megabyte.
_TOKEN_LIMIT = 8

# Monte Carlo phase search cost is iterations x tones x points. The GUI's 1000
# is fine; an unbounded value from a URL would let one request spin for minutes
# inside the lock-free generate path and starve the worker pool.
_MC_MAX = 20000

# Preview sample count. The page draws these on a canvas a few hundred pixels
# wide, so more than this is bytes on the wire nobody can see.
_PREVIEW_DEFAULT = 1000
_PREVIEW_MAX = 4096

# Full buffers stay server-side under a token; only a decimated copy is shipped
# for the preview.
_ARB_PREVIEW_MAX = 4096

_TIME_UNIT_SCALE = {"ns": 1e9, "µs": 1e6, "ms": 1e3, "s": 1.0}

# GUI parity: the raw SCPI reply is matched on its first four characters, which
# is how the instrument's short and long forms (SIN/SINusoid, SEQ/SEQuence) both
# land on one name. USER and SEQ are both "an arbitrary waveform is loaded".
_FUNCTION_NAMES = {"SIN": "sine", "SQU": "square", "PULS": "pulse", "RAMP": "ramp",
                   "NOIS": "noise", "DC": "dc", "ARB": "arbitrary",
                   "SEQU": "arbitrary", "USER": "arbitrary"}

WAVEFORMS = ("sine", "square", "pulse", "ramp", "noise", "dc", "arbitrary")


class _Unavailable(Exception):
    """The instrument could not be reached, or refused a command (-> 503)."""


# --------------------------------------------------------------------------- #
# small coercions — every one of these raises ValueError, which the HTTP layer
# turns into a 422 with the message intact
# --------------------------------------------------------------------------- #

def _num(payload: dict, key: str, default: Optional[float] = None, *,
         required: bool = False) -> Optional[float]:
    if key not in payload or payload[key] is None:
        if required:
            raise ValueError(f"'{key}' is required")
        return default
    try:
        v = float(payload[key])
    except (TypeError, ValueError):
        raise ValueError(f"'{key}' must be a number, got {payload[key]!r}")
    if not math.isfinite(v):
        raise ValueError(f"'{key}' must be finite, got {payload[key]!r}")
    return v


def _int(payload: dict, key: str, default: Optional[int] = None, *,
         required: bool = False) -> Optional[int]:
    v = _num(payload, key, None, required=required)
    if v is None:
        return default
    return int(v)


def _bool(payload: dict, key: str, default: bool = False) -> bool:
    v = payload.get(key, default)
    if isinstance(v, bool):
        return v
    if isinstance(v, str):
        return v.strip().lower() in ("1", "true", "yes", "on")
    return bool(v)


def _text(payload: dict, key: str, default: str = "") -> str:
    v = payload.get(key, default)
    return "" if v is None else str(v)


def _canon_waveform(name: str) -> str:
    w = (name or "").strip().lower()
    if w in ("arb", "user", "seq", "sequence"):
        w = "arbitrary"
    if w not in WAVEFORMS:
        raise ValueError(f"waveform must be one of {', '.join(WAVEFORMS)}, got {name!r}")
    return w


def _canon_function(raw: Optional[str]) -> Optional[str]:
    """Map a ':FUNCtion?' reply onto the page's waveform vocabulary."""
    if not raw:
        return None
    return _FUNCTION_NAMES.get(raw.strip().upper()[:4], raw.strip().lower())


def _jsonable(values, digits: int = 6) -> List[float]:
    """numpy -> JSON. NaN/Inf are not valid JSON and would make the whole
    response unparseable in the browser, so they are folded to finite values."""
    a = np.nan_to_num(np.asarray(values, dtype=float),
                      nan=0.0, posinf=0.0, neginf=0.0)
    return [float(x) for x in np.round(a, digits)]


def _decimate(data: np.ndarray, limit: int) -> np.ndarray:
    """Even sub-sample that keeps both endpoints (so a preview of a ramp still
    reaches its corners)."""
    n = len(data)
    if n <= limit:
        return np.asarray(data, dtype=float)
    idx = np.unique(np.round(np.linspace(0, n - 1, limit)).astype(int))
    return np.asarray(data, dtype=float)[idx]


def _pulse_duty(width_s: float, period_s: float) -> float:
    """GUI parity: pulse width is expressed to the instrument as a duty cycle,
    hard-clamped to 1..99 % because the DG822 refuses the endpoints."""
    if period_s <= 0:
        return 50.0
    return max(1.0, min(99.0, width_s / period_s * 100.0))


def _square_v(freq: float, amp: float, offset: float, phase: float,
              duty: float, points: int, cycles: int):
    """Square/pulse-train preview. scipy is not in this repo's requirements, so
    the numpy identity is the fallback rather than an ImportError in a request."""
    try:
        return WaveformPlotter.generate_square(freq, amp, offset, phase, duty,
                                               points, cycles)
    except Exception:
        t = np.linspace(0, cycles / freq, points)
        ph = np.deg2rad(phase) / (2 * np.pi)
        frac = np.mod(freq * t + ph, 1.0)
        v = np.where(frac < duty / 100.0, 1.0, -1.0) * (amp / 2) + offset
        return t, v


def _ramp_v(freq: float, amp: float, offset: float, phase: float,
            symmetry: float, points: int, cycles: int):
    """Ramp preview, with the same scipy fallback as ``_square_v``."""
    try:
        return WaveformPlotter.generate_ramp(freq, amp, offset, phase, symmetry,
                                             points, cycles)
    except Exception:
        t = np.linspace(0, cycles / freq, points)
        w = min(max(symmetry / 100.0, 0.0), 1.0)
        p = np.mod(freq * t + np.deg2rad(phase) / (2 * np.pi), 1.0)
        if w <= 0:
            v = 1.0 - 2.0 * p
        elif w >= 1:
            v = 2.0 * p - 1.0
        else:
            v = np.where(p < w, 2.0 * p / w - 1.0, 2.0 * (1.0 - p) / (1.0 - w) - 1.0)
        return t, v * (amp / 2) + offset


# --------------------------------------------------------------------------- #
# generator catalogue and presets — both are data the page renders generically,
# so adding a shape or a preset needs no page change
# --------------------------------------------------------------------------- #

def _p(name, label, default, unit, lo, hi):
    return {"name": name, "label": label, "default": default,
            "unit": unit, "min": lo, "max": hi}


# Shape parameters are percentages OF THE SHAPE PERIOD, which is what the
# generators in rigol_dg822.arbitrary actually consume. The tkinter dialog asks
# for seconds and converts; here the conversion belongs to the page, which is
# given ``period`` and ``shape_period`` in every generate response so it can show
# either. Under bipolar drive the shape occupies half the output period, so a
# percentage means percent of that half — same rule as the dialog.
ARB_SHAPES = [
    {"name": "square", "label": "Square",
     "params": [_p("on_time", "On time", 50.0, "% of shape period", 0.0, 100.0)]},
    {"name": "sine", "label": "Sine",
     "params": [_p("phase", "Phase", 0.0, "deg", -360.0, 360.0)]},
    {"name": "ramp", "label": "Ramp",
     "params": [_p("rise_time", "Rise time", 100.0, "% of shape period", 0.0, 100.0)]},
    {"name": "trapezoid", "label": "Trapezoid",
     "params": [_p("rise_time", "Rise time", 20.0, "% of shape period", 0.0, 100.0),
                _p("pulse_time", "Pulse time", 60.0, "% of shape period", 0.0, 100.0),
                _p("fall_time", "Fall time", 20.0, "% of shape period", 0.0, 100.0)]},
    {"name": "pulse", "label": "Pulse",
     "params": [_p("on_time", "On time", 10.0, "% of shape period", 0.0, 100.0),
                _p("rise_time", "Rise time", 5.0, "% of shape period", 0.0, 100.0),
                _p("fall_time", "Fall time", 5.0, "% of shape period", 0.0, 100.0)]},
    {"name": "sinc", "label": "Sinc",
     "params": [_p("lobes", "Lobes", 5, "count", 1, 64)]},
    {"name": "exponential", "label": "Exponential decay",
     "params": [_p("tau", "Time constant", 20.0, "% of shape period", 0.1, 1000.0)]},
    {"name": "gaussian", "label": "Gaussian",
     "params": [_p("sigma", "Std deviation", 30.0, "% of shape period", 0.1, 200.0)]},
    # No shape params: the tone list in ``comb`` defines it, and the point count
    # and fundamental fall out of the frequencies themselves.
    {"name": "frequency_comb", "label": "Frequency comb", "params": []},
]

_SHAPE_BY_NAME = {s["name"]: s for s in ARB_SHAPES}

PRESETS = [
    {"id": "sine-1k-1v", "label": "1 kHz sine 1 Vpp",
     "description": "Small-signal reference tone.",
     "channel_defaults": {"waveform": "sine", "frequency": 1000.0,
                          "amplitude": 1.0, "offset": 0.0, "phase": 0.0}},
    {"id": "sine-1k-5v", "label": "1 kHz sine 5 Vpp",
     "description": "Full-scale reference tone.",
     "channel_defaults": {"waveform": "sine", "frequency": 1000.0,
                          "amplitude": 5.0, "offset": 0.0, "phase": 0.0}},
    {"id": "square-10k-3v3", "label": "10 kHz square 3.3 V",
     "description": "Unipolar 0-3.3 V logic clock (3.3 Vpp on a 1.65 V offset).",
     "channel_defaults": {"waveform": "square", "frequency": 10000.0,
                          "amplitude": 3.3, "offset": 1.65, "phase": 0.0,
                          "duty_cycle": 50.0}},
    {"id": "sine-1m-1v", "label": "1 MHz sine 1 Vpp",
     "description": "High-frequency reference tone.",
     "channel_defaults": {"waveform": "sine", "frequency": 1000000.0,
                          "amplitude": 1.0, "offset": 0.0, "phase": 0.0}},
    {"id": "ramp-100-5v", "label": "100 Hz ramp 5 Vpp",
     "description": "Rising sawtooth (symmetry 100 %).",
     "channel_defaults": {"waveform": "ramp", "frequency": 100.0,
                          "amplitude": 5.0, "offset": 0.0, "phase": 0.0,
                          "symmetry": 100.0}},
    {"id": "dc-3v3", "label": "DC 3.3 V",
     "description": "Constant level; the DC path takes the offset field only.",
     "channel_defaults": {"waveform": "dc", "frequency": 1000.0,
                          "amplitude": 5.0, "offset": 3.3, "phase": 0.0}},
]

_PRESET_BY_ID = {p["id"]: p for p in PRESETS}


# --------------------------------------------------------------------------- #
# token cache
# --------------------------------------------------------------------------- #

class _TokenCache:
    """Bounded LRU of generated buffers, keyed by an opaque token.

    Holds the FULL buffer so ``/api/arb/upload`` does not have to receive 8192
    floats back from the browser it just sent a decimated copy to. Bounded for
    the reason in ``_TOKEN_LIMIT``.
    """

    def __init__(self, limit: int = _TOKEN_LIMIT) -> None:
        self._limit = limit
        self._items: "OrderedDict[str, dict]" = OrderedDict()
        self._lock = threading.Lock()

    def put(self, entry: dict) -> str:
        token = uuid.uuid4().hex[:16]
        with self._lock:
            self._items[token] = entry
            while len(self._items) > self._limit:
                self._items.popitem(last=False)
        return token

    def get(self, token: str) -> dict:
        with self._lock:
            entry = self._items.get(token)
            if entry is None:
                # LookupError, not _Unavailable: the buffer is gone, which is a
                # 404 under this app's convention, not an instrument fault.
                raise LookupError(
                    f"generated waveform {token!r} is no longer cached "
                    f"(only the last {self._limit} are kept) - generate it again")
            self._items.move_to_end(token)
            return entry

    def clear(self) -> None:
        with self._lock:
            self._items.clear()


# --------------------------------------------------------------------------- #
# the session — the DG822 equivalent of camera_dock.webapp.CameraSession
# --------------------------------------------------------------------------- #

def _limit_warnings(c: dict) -> List[str]:
    """Everything about this channel the DG822 cannot actually honour.

    Derived on every read rather than stored at write time, so the list stays
    true after any route that changes a value -- /apply, /set, a preset, an arb
    upload, or a load change that halves the rail under a setting that was legal
    a moment ago. Nothing here refuses anything; see the limit constants for why
    warn-not-refuse is the policy the three front ends share.
    """
    w: List[str] = []
    f = c.get("frequency")
    fn = (c.get("function") or "")
    # Noise and DC have no frequency, and an arbitrary buffer is clocked by its
    # own sample rate -- warning about 25 MHz there would be noise, not signal.
    if f is not None and fn not in ("noise", "dc"):
        if not (MIN_FREQUENCY_HZ <= f <= MAX_FREQUENCY_HZ):
            w.append(f"frequency {f:.6g} Hz is outside the DG822 range "
                     f"{MIN_FREQUENCY_HZ:g}-{MAX_FREQUENCY_HZ:g} Hz; the "
                     f"instrument will use its own limit instead")
    a, o = c.get("amplitude"), c.get("offset")
    if a is not None and fn != "dc":
        if not (MIN_AMPLITUDE_VPP <= a <= MAX_AMPLITUDE_VPP):
            w.append(f"amplitude {a:.6g} Vpp is outside the DG822 range "
                     f"{MIN_AMPLITUDE_VPP:g}-{MAX_AMPLITUDE_VPP:g} Vpp into "
                     f"High-Z; the instrument will use its own limit instead")
    imp = c.get("impedance")
    rail = MAX_RAIL_50_OHM_V if isinstance(imp, (int, float)) and imp <= 100         else MAX_RAIL_HIGH_Z_V
    load = "50 ohm" if rail == MAX_RAIL_50_OHM_V else "High-Z"
    if a is not None and o is not None:
        peak = abs(o) + (0.0 if fn == "dc" else a / 2.0)
        if peak > rail:
            w.append(f"offset {o:.6g} V with {a:.6g} Vpp reaches {peak:.6g} V "
                     f"peak, past the {rail:g} V rail into {load}. The DG822 "
                     f"clamps to its own limit WITHOUT reporting it, so the "
                     f"output will not be what is shown here")
    d = c.get("duty_cycle")
    if d is not None and fn in ("square", "pulse") and not (0.01 <= d <= 99.99):
        w.append(f"duty cycle {d:.6g} % is outside 0.01-99.99 %")
    sym = c.get("symmetry")
    if sym is not None and fn == "ramp" and not (0.0 <= sym <= 100.0):
        w.append(f"ramp symmetry {sym:.6g} % is outside 0-100 %")
    return w


class DG822Session:
    """One DG822 + its lock + its last-known state, behind the web API.

    Owns the controller, serialises every instrument access, remembers the
    values the instrument cannot be asked for, and runs the timed-output timers.
    Nothing here raises out of an ordinary failure: a missing VISA backend, an
    absent instrument or a SCPI timeout all land in ``ok``/``error``, and the
    page says so.
    """

    def __init__(self, resource: Optional[str] = None, *,
                 simulate: bool = False, timeout: int = 5000) -> None:
        self.resource = SIM_RESOURCE if simulate else resource
        self.sim = bool(simulate) or (resource == SIM_RESOURCE)
        self.controller = DG822Controller(self.resource, timeout, simulate=self.sim)
        # Re-entrant: the write endpoints take the lock and then call state(),
        # which takes it again to read back.
        self.lock = threading.RLock()
        self.ok = False
        self.error = ""
        self.tokens = _TokenCache()

        # Everything the instrument cannot be asked for. The DG822 has no getter
        # for pulse width, for the arbitrary point count, or for what the host
        # scheduled — losing these on a page reload is exactly the "server-owned
        # state means a reload rediscovers a running operation" property the
        # dock's pages rely on.
        self._ch: Dict[int, dict] = {n: self._blank_channel() for n in CHANNELS}
        self._timers: Dict[int, threading.Timer] = {}
        self._run_gen: Dict[int, int] = {n: 0 for n in CHANNELS}

        self._state_cache: Optional[dict] = None
        self._state_at = 0.0
        # A full read is 9 SCPI round trips per channel. Several browser tabs
        # polling at 1 s would multiply that straight onto the wire, so a read
        # this fresh is served from the cache instead. Writes invalidate it, so
        # the operator never sees their own change lag.
        self.refresh_interval = 0.5

    # -- construction helpers ------------------------------------------------
    @staticmethod
    def _blank_channel() -> dict:
        return {"function": None, "frequency": None, "amplitude": None,
                "offset": None, "phase": None, "duty_cycle": None,
                "pulse_width": None, "symmetry": None, "output": False,
                "impedance": None, "polarity": None, "sync": None,
                "arb_name": None, "sample_rate": None, "points": None,
                "run_mode": "continuous", "off_at": None,
                # Two additions to the wire contract, both because the page
                # cannot work them out for itself: `function_raw` is the
                # instrument's untranslated ':FUNCtion?' reply, and `arb_loaded`
                # says a buffer is sitting on this channel even on firmware that
                # keeps reporting the previous built-in shape.
                "function_raw": None, "arb_loaded": False,
                "arb_data": None}

    # -- lifecycle -----------------------------------------------------------
    def start(self) -> None:
        """Connect. Idempotent; never raises (it sets ok/error instead).

        With no resource configured this discovers hardware and takes the first
        real instrument. It deliberately does NOT fall through to the simulator:
        an operator who thinks they are driving a coil must never be quietly
        handed a simulation. The simulator is offered by /api/devices and chosen
        on purpose.
        """
        with self.lock:
            if self.ok:
                return
            try:
                if self.resource:
                    connected = self.controller.connect(self.resource)
                else:
                    connected = self._connect_first_hardware()
                if connected:
                    self.resource = self.controller.connection.resource_name
                    self.sim = self.controller.is_simulated
                    self.ok = True
                    self.error = ""
                    self._prime()
                else:
                    self.ok = False
                    self.error = self.error or self._why_not()
            except Exception as exc:              # a bad instrument never sinks the panel
                self.ok, self.error = False, f"{type(exc).__name__}: {exc}"

    def _connect_first_hardware(self) -> bool:
        devices = [d for d in self.controller.discover_devices() if d[0] != SIM_RESOURCE]
        if not devices:
            self.error = self._why_not()
            return False
        return self.controller.connect(devices[0][0])

    def _why_not(self) -> str:
        reason = self.controller.connection.backend_error
        if reason:
            return (f"no DG822 found - {reason}. Connect the simulator to work "
                    f"without hardware.")
        if self.resource:
            return f"could not open {self.resource}"
        return ("no DG822 found on USB. Connect the simulator to work without "
                "hardware.")

    def stop(self) -> None:
        """Outputs OFF, then release the VISA session. Never raises.

        Order matters and is the whole point: an output left driving after the
        process exits is a physical hazard, and closing the session first would
        leave it driving with nothing able to stop it.
        """
        with self.lock:
            self._cancel_all_timers()
            try:
                out = self.controller.output
                if out is not None:
                    for n in CHANNELS:
                        try:
                            out.disable(n)
                        except Exception:
                            pass
            except Exception:
                pass
            try:
                self.controller.disconnect()
            except Exception:
                pass
            try:
                # disconnect() leaves the resource manager loaded so the object
                # stays reconnectable; on the way out we want the VISA library
                # released too.
                self.controller.connection.close()
            except Exception:
                pass
            self.ok = False
            self._state_cache = None
            self.tokens.clear()

    def connect(self, resource: Optional[str] = None, simulate: bool = False) -> None:
        """Switch to a named instrument (or the simulator). Never raises.

        Releases the current instrument through ``disconnect()`` rather than
        dropping the session outright, because switching instruments has the
        same consequence for a TIMED run that releasing one does, only worse:
        after this call the previous instrument is not merely unowned, it is
        unreachable -- the session is rebound, ``_ch`` describes the new box,
        and ``stop()`` will thereafter disable channels on the new instrument
        while the old one keeps driving. A timed run whose deadline nothing can
        honour is exactly what disconnect() switches off, so the policy is
        shared rather than duplicated (and a continuous run is still left alone,
        for the reason given there).

        This used to call ``_cancel_all_timers()`` and then
        ``controller.disconnect()`` directly, which cancelled the shutoff timer
        of a timed run without switching its output off -- permanently orphaning
        a driving channel.
        """
        with self.lock:
            self.disconnect()                 # outputs handled, timers cancelled
            self.resource = SIM_RESOURCE if simulate else (resource or None)
            self.sim = simulate or (self.resource == SIM_RESOURCE)
            self.error = ""
            self.start()

    def disconnect(self) -> None:
        """Release the instrument but leave the session reusable. Never raises.

        A continuous output is left running: this is an operator handing the box
        to something else, not a shutdown, and killing a running experiment
        because someone released the VISA session would be the worse surprise.
        A TIMED run is not, though — the operator asked for it to stop at a
        fixed moment, and after this call nothing here can make that happen. So
        those channels go off now, while there is still a session to do it with.
        """
        with self.lock:
            timed = [n for n in CHANNELS if self._ch[n].get("off_at") is not None]
            for n in timed:
                try:
                    _, out = self.require()
                    out.disable(n)
                    self._ch[n]["output"] = False
                except Exception:
                    pass
            self._cancel_all_timers()
            try:
                self.controller.disconnect()
            except Exception:
                pass
            self.ok = False
            self._state_cache = None

    # -- guards --------------------------------------------------------------
    def require(self):
        """The controller's waveform/output pair, or a readable 503 reason."""
        if not self.ok or not self.controller.is_connected:
            raise _Unavailable(f"DG822 not connected: {self.error or 'no instrument'}")
        wf, out = self.controller.waveform, self.controller.output
        if wf is None or out is None:
            raise _Unavailable("DG822 connection is up but the control layer is not")
        return wf, out

    @staticmethod
    def _ok(result: bool, what: str) -> None:
        """The driver reports a failed SCPI write as False, not an exception."""
        if not result:
            raise _Unavailable(f"instrument refused {what}")

    # -- state ---------------------------------------------------------------
    def state(self, *, refresh: bool = True) -> dict:
        with self.lock:
            if refresh and self.ok:
                fresh = (time.time() - self._state_at) < self.refresh_interval
                if not fresh or self._state_cache is None:
                    self._read_all()
            return self._snapshot()

    def _invalidate(self) -> None:
        self._state_at = 0.0

    def _snapshot(self) -> dict:
        return {
            "connected": bool(self.ok and self.controller.is_connected),
            "resource": self.resource,
            "idn": self.controller.idn,
            "sim": bool(self.sim),
            "error": self.error or "",
            "backend_reason": self.controller.connection.backend_error or "",
            "channels": {str(n): self.channel(n) for n in CHANNELS},
        }

    def channel(self, n: int) -> dict:
        """One channel's public view (the internal arb buffer stays server-side)."""
        with self.lock:
            d = dict(self._ch[n])
            d.pop("arb_data", None)
            d["warnings"] = _limit_warnings(d)
            return d

    def arb_buffer(self, n: int) -> Optional[np.ndarray]:
        """The samples last uploaded to this channel, for the preview to draw.
        None once a .RAF was loaded instrument-side, where the host never saw
        them."""
        with self.lock:
            return self._ch[n].get("arb_data")

    def read_channel(self, n: int) -> dict:
        """Force a fresh read of one channel, then return it."""
        with self.lock:
            if self.ok:
                try:
                    self._read_channel(n)
                except Exception as exc:
                    self.error = f"{type(exc).__name__}: {exc}"
                self._invalidate()
            return self.channel(n)

    def _prime(self) -> None:
        """Seed the cache from the instrument on connect, so the page opens
        showing what the box is actually doing rather than page defaults."""
        try:
            self._read_all()
        except Exception as exc:
            self.error = f"connected, but could not read state: {exc}"

    def _read_all(self) -> None:
        # /api/state is the page's heartbeat: it must answer even when a query
        # times out mid-poll, or one dropped reply blanks the whole page instead
        # of one stale field.
        for n in CHANNELS:
            try:
                self._read_channel(n)
            except Exception as exc:
                self.error = f"CH{n} read failed: {exc}"
        self._state_at = time.time()

    def _read_channel(self, n: int) -> None:
        wf, out = self.require()
        c = self._ch[n]

        # One ':SOURceN:APPLy?' instead of five separate getters: the reply
        # carries function, frequency, amplitude, offset and phase together, so
        # a full page refresh costs 9 round trips per channel rather than 13.
        parsed = _parse_apply(wf.get_apply_settings(n))
        if parsed is not None:
            raw, freq, amp, off, ph = parsed
            c["function_raw"] = raw
            c["function"] = _canon_function(raw)
            c["frequency"], c["amplitude"], c["offset"], c["phase"] = freq, amp, off, ph
        else:
            # A firmware that answers APPLy? differently must not blank the page.
            raw = wf.get_function(n)
            if raw:
                c["function_raw"] = raw
                c["function"] = _canon_function(raw)
            for key, getter in (("frequency", wf.get_frequency),
                                ("amplitude", wf.get_amplitude),
                                ("offset", wf.get_offset),
                                ("phase", wf.get_phase)):
                v = getter(n)
                if v is not None:
                    c[key] = v

        for key, getter in (("duty_cycle", wf.get_square_duty_cycle),
                            ("symmetry", wf.get_ramp_symmetry)):
            v = getter(n)
            if v is not None:
                c[key] = v

        # arb_name is host-tracked (upload and load_raf set it), never queried.
        # This read used to send :SOURce<n>:FUNCtion:ARBitrary?, which is not in
        # the DG800 command set: the instrument never replies, so every channel
        # read sat out the full 5 s VISA timeout while holding the session lock.
        # Measured on the bench (fw 00.02.06): every /api/state took 10.0 s, and
        # an output-on request queued behind that poll for up to the same again.

        # What an arbitrary buffer is actually clocking out at -- but WHICH
        # number that is depends on the arb mode, and there is no driver getter
        # for either.
        #
        # SEQUENCE mode (firmware <= 00.01.x): the instrument is clocked by
        #   :FUNCtion:SEQuence:SRATe, and the output frequency falls out of it
        #   as SRATe/points. Query it.
        # USER mode (firmware >= 00.02.x, what this driver targets): the buffer
        #   plays once per output period, so the true rate is frequency x points
        #   and SRATe is NOT used. Querying it returns whatever it was last left
        #   at -- 2000 on a fresh instrument -- so trusting the query here
        #   reported 2 kSa/s for a 4096-point buffer at 2 kHz whose real rate is
        #   8.192 MSa/s: wrong by the point count, and wrong downwards, which
        #   reads as a far gentler waveform than is actually being emitted.
        #   upload() computes the right value; this poll used to clobber it
        #   half a second later.
        mode = (c.get("function_raw") or "").upper()
        pts = c.get("points")
        if "USER" in mode and pts:
            c["sample_rate"] = (c.get("frequency") or 0.0) * pts
        else:
            srate = self.controller.connection.query(
                f":SOURce{n}:FUNCtion:SEQuence:SRATe?")
            if srate:
                try:
                    c["sample_rate"] = float(srate)
                except ValueError:
                    pass

        st = out.get_state(n)
        if st is not None:
            c["output"] = bool(st)
            if not st:
                # The instrument's output went off (front panel, *RST, a timer
                # that already fired) — a run is not in progress any more.
                c["run_mode"] = "continuous"
                c["off_at"] = None

        imp = out.get_impedance(n)
        if imp is not None:
            # JSON has no Infinity. High-Z travels as the same string the /load
            # endpoint accepts, so the page round-trips it without a special case.
            c["impedance"] = "high-z" if math.isinf(imp) else float(imp)

        pol = out.get_polarity(n)
        if pol:
            c["polarity"] = "inverted" if pol.strip().upper().startswith("INV") else "normal"

        sync = out.get_sync_state(n)
        if sync is not None:
            c["sync"] = bool(sync)

    # -- timed runs ----------------------------------------------------------
    def _cancel_timer(self, n: int) -> None:
        t = self._timers.pop(n, None)
        if t is not None:
            t.cancel()
        # Bump the generation so a timer already past cancel() — fired, waiting
        # on the lock we are holding — cannot switch off the run that replaced it.
        self._run_gen[n] += 1
        self._ch[n]["off_at"] = None
        self._ch[n]["run_mode"] = "continuous"

    def _cancel_all_timers(self) -> None:
        for n in CHANNELS:
            self._cancel_timer(n)

    def _schedule_off(self, n: int, seconds: float, mode: str) -> None:
        self._cancel_timer(n)
        gen = self._run_gen[n]
        # Daemon so a ten-hour run cannot keep the process alive after uvicorn
        # exits; stop() cancels every timer and drops the outputs, which is the
        # path that actually ends a run at shutdown.
        t = threading.Timer(seconds, self._timed_off, args=(n, gen))
        t.daemon = True
        t.name = f"dg822-ch{n}-off"
        self._timers[n] = t
        self._ch[n]["off_at"] = time.time() + seconds
        self._ch[n]["run_mode"] = mode
        try:
            t.start()
        except Exception:
            # The caller bounds the duration so this should be unreachable, but
            # the consequence of an unarmed timer is an output driving with
            # nothing left to stop it -- the one failure this class exists to
            # prevent. If the timer cannot be armed, the run does not start:
            # drop the output and re-raise so the request fails loudly instead
            # of returning 200 with an off_at that will never arrive.
            self._timers.pop(n, None)
            self._ch[n]["off_at"] = None
            self._ch[n]["run_mode"] = "continuous"
            try:
                _, out = self.require()
                out.disable(n)
            except Exception:
                pass
            self._ch[n]["output"] = False
            self._invalidate()
            raise

    def _timed_off(self, n: int, gen: int) -> None:
        with self.lock:
            if self._run_gen[n] != gen:
                return                        # superseded by a newer output command
            self._timers.pop(n, None)
            self._ch[n]["off_at"] = None
            self._ch[n]["run_mode"] = "continuous"
            self._ch[n]["output"] = False
            self._invalidate()
            try:
                _, out = self.require()
                out.disable(n)
            except Exception as exc:
                self.error = f"timed run on CH{n} could not switch the output off: {exc}"

    # -- writes --------------------------------------------------------------
    def apply(self, n: int, payload: dict) -> dict:
        wave = _canon_waveform(_text(payload, "waveform", "sine"))
        freq = _num(payload, "frequency", 1000.0)
        amp = _num(payload, "amplitude", 5.0)
        off = _num(payload, "offset", 0.0)
        phase = _num(payload, "phase", 0.0)
        duty = _num(payload, "duty_cycle")
        width = _num(payload, "pulse_width")
        symm = _num(payload, "symmetry")
        if wave not in ("noise", "dc") and freq <= 0:
            raise ValueError("frequency must be positive")

        with self.lock:
            self.require()
            ctl = self.controller
            c = self._ch[n]
            if wave == "sine":
                self._ok(ctl.setup_sine(n, freq, amp, off, phase), "APPLy:SINusoid")
            elif wave == "square":
                self._ok(ctl.setup_square(n, freq, amp, off, phase,
                                          duty if duty is not None else 50.0),
                         "APPLy:SQUare")
                c["duty_cycle"] = duty if duty is not None else 50.0
            elif wave == "pulse":
                # GUI parity: the operator sets a width, the instrument takes a
                # duty cycle, and the controller adds the centring phase shift.
                period = 1.0 / freq
                d = duty if duty is not None else _pulse_duty(
                    width if width is not None else period * 0.1, period)
                self._ok(ctl.setup_pulse(n, freq, amp, off, phase, duty_cycle=d),
                         "APPLy:PULSe")
                c["duty_cycle"] = d
                c["pulse_width"] = (width if width is not None
                                    else period * d / 100.0)
            elif wave == "ramp":
                self._ok(ctl.setup_ramp(n, freq, amp, off, phase,
                                        symm if symm is not None else 50.0),
                         "APPLy:RAMP")
                c["symmetry"] = symm if symm is not None else 50.0
            elif wave == "noise":
                # The instrument's NOISe path takes amplitude and offset only.
                self._ok(ctl.setup_noise(n, amp, off), "APPLy:NOISe")
            elif wave == "dc":
                # DC takes the offset field as the level; frequency, amplitude
                # and phase are discarded by the instrument.
                self._ok(ctl.setup_dc(n, off), "APPLy:DC")
            else:                                     # arbitrary
                data = c.get("arb_data")
                if data is None:
                    raise ValueError(
                        "no arbitrary waveform on this channel - generate or "
                        "load one and POST /api/arb/upload first")
                # GUI parity: Apply on an arbitrary channel re-uploads and
                # re-applies, WITHOUT the SIN pre-clear that the explicit Upload
                # button does.
                self._upload_locked(n, np.asarray(data, dtype=float),
                                    name=c.get("arb_name") or "CUSTOM",
                                    frequency=freq, amplitude=amp, offset=off,
                                    phase=phase, save_raf=True, pre_clear=False)
            self._invalidate()
            return self.read_channel(n)

    def set_params(self, n: int, payload: dict) -> dict:
        known = ("frequency", "amplitude", "offset", "phase", "duty_cycle",
                 "pulse_width", "symmetry")
        given = [k for k in known if k in payload and payload[k] is not None]
        if not given:
            raise ValueError(f"nothing to set - expected any of {', '.join(known)}")

        with self.lock:
            wf, _ = self.require()
            c = self._ch[n]
            for key in given:
                v = _num(payload, key)
                if key == "frequency":
                    if v <= 0:
                        raise ValueError("frequency must be positive")
                    self._ok(wf.set_frequency(n, v), ":FREQuency")
                elif key == "amplitude":
                    self._ok(wf.set_amplitude(n, v), ":VOLTage")
                elif key == "offset":
                    self._ok(wf.set_offset(n, v), ":VOLTage:OFFSet")
                elif key == "phase":
                    self._ok(wf.set_phase(n, v), ":PHASe")
                elif key == "duty_cycle":
                    # Square and pulse duty are different SCPI nodes; pick by
                    # what the channel is currently generating.
                    if (c.get("function") or "") == "pulse":
                        self._ok(wf.set_pulse_duty_cycle(n, v), ":PULSe:DCYCle")
                    else:
                        self._ok(wf.set_square_duty_cycle(n, v), ":SQUare:DCYCle")
                    c["duty_cycle"] = v
                elif key == "pulse_width":
                    if v <= 0:
                        raise ValueError("pulse_width must be positive (seconds)")
                    self._ok(wf.set_pulse_width(n, v), ":PULSe:WIDTh")
                    c["pulse_width"] = v
                elif key == "symmetry":
                    self._ok(wf.set_ramp_symmetry(n, v), ":RAMP:SYMMetry")
                    c["symmetry"] = v
            self._invalidate()
            return self.read_channel(n)

    def set_output(self, n: int, on: bool, seconds: Optional[float] = None,
                   cycles: Optional[int] = None) -> dict:
        with self.lock:
            _, out = self.require()
            # Any new output command supersedes a run in progress, so its timer
            # goes first — otherwise the old one would switch off the new run.
            self._cancel_timer(n)
            if not on:
                self._ok(out.disable(n), f"OUTPut{n} OFF")
                self._ch[n]["output"] = False
                self._invalidate()
                return self.read_channel(n)

            mode, duration = "continuous", None
            if seconds is not None and cycles is not None:
                raise ValueError("give either 'seconds' or 'cycles', not both")
            if seconds is not None:
                if seconds <= 0:
                    raise ValueError("seconds must be positive")
                if seconds > MAX_RUN_SECONDS:
                    raise ValueError(
                        f"seconds must be at most {MAX_RUN_SECONDS:g} "
                        f"({MAX_RUN_SECONDS / 3600:g} h): a longer run cannot be "
                        f"scheduled, and enabling the output for one that cannot "
                        f"be scheduled would leave it driving with no timer to "
                        f"switch it off. Use a continuous run instead.")
                mode, duration = "timed", float(seconds)
            elif cycles is not None:
                if cycles <= 0:
                    raise ValueError("cycles must be a positive whole number")
                freq = self._ch[n].get("frequency") or 0.0
                if freq <= 0:
                    raise ValueError(
                        "cannot time an N-cycle burst: this channel has no "
                        "positive frequency (noise and DC have none)")
                # GUI parity, and worth being plain about: an N-cycle run is a
                # HOST timer of cycles/frequency, not the instrument's :BURSt
                # mode. The count is nominal — accurate to the scheduler, not to
                # the waveform — and the last cycle is not gated.
                mode, duration = "cycles", float(cycles) / freq
                # Same ceiling, reached the indirect way: the guide allows a
                # frequency down to 1 uHz, so a few cycles at the bottom of the
                # range is already days of runtime.
                if duration > MAX_RUN_SECONDS:
                    raise ValueError(
                        f"{cycles:g} cycles at {freq:g} Hz is {duration:g} s, "
                        f"over the {MAX_RUN_SECONDS:g} s ceiling for a timed "
                        f"run. Lower the cycle count, raise the frequency, or "
                        f"use a continuous run.")
            self._ok(out.enable(n), f"OUTPut{n} ON")
            self._ch[n]["output"] = True
            if duration is not None:
                self._schedule_off(n, duration, mode)
            self._invalidate()
            return self.read_channel(n)

    def set_load(self, n: int, impedance) -> dict:
        with self.lock:
            _, out = self.require()
            if isinstance(impedance, str) and impedance.strip().lower() in (
                    "high-z", "highz", "high z", "inf", "infinity"):
                self._ok(out.set_impedance_high_z(n), f"OUTPut{n}:LOAD INFinity")
            else:
                try:
                    ohms = float(impedance)
                except (TypeError, ValueError):
                    raise ValueError(
                        f"impedance must be a number of ohms or \"high-z\", "
                        f"got {impedance!r}")
                # The driver only warns outside 1..10000 and sends the value
                # anyway; refuse here so a typo cannot reach the instrument.
                if not (out.MIN_IMPEDANCE <= ohms <= out.MAX_IMPEDANCE):
                    raise ValueError(
                        f"impedance must be {out.MIN_IMPEDANCE}..{out.MAX_IMPEDANCE} "
                        f"ohms or \"high-z\", got {ohms}")
                self._ok(out.set_impedance(n, ohms), f"OUTPut{n}:LOAD")
            self._invalidate()
            return self.read_channel(n)

    def set_polarity(self, n: int, inverted: bool) -> dict:
        with self.lock:
            _, out = self.require()
            self._ok(out.set_polarity_inverted(n) if inverted
                     else out.set_polarity_normal(n), f"OUTPut{n}:POLarity")
            self._invalidate()
            return self.read_channel(n)

    def set_sync(self, n: int, on: bool) -> dict:
        with self.lock:
            _, out = self.require()
            self._ok(out.enable_sync(n) if on else out.disable_sync(n),
                     f"OUTPut{n}:SYNC")
            self._invalidate()
            return self.read_channel(n)

    def reset(self) -> dict:
        with self.lock:
            self.require()
            # *RST drops both outputs, so the host timers are meaningless now.
            self._cancel_all_timers()
            self._ok(self.controller.reset(), "*RST")
            for n in CHANNELS:
                self._ch[n] = self._blank_channel()
            self._invalidate()
            return self.state()

    def beep(self) -> None:
        with self.lock:
            self.require()
            self._ok(self.controller.beep(), ":SYSTem:BEEPer:IMMediate")

    def sync_phases(self) -> None:
        with self.lock:
            wf, _ = self.require()
            # Instrument-wide, addressed at :SOURce1 — there is no per-channel form.
            self._ok(wf.sync_phases(), ":SOURce1:PHASe:SYNChronize")
            self._invalidate()

    def devices(self) -> dict:
        with self.lock:
            try:
                found = self.controller.discover_devices()
            except Exception as exc:          # discovery must never raise here
                return {"devices": [{"resource": SIM_RESOURCE, "idn": "simulated DG822",
                                     "sim": True}],
                        "reason": f"{type(exc).__name__}: {exc}"}
            devices = [{"resource": r, "idn": i, "sim": r == SIM_RESOURCE}
                       for r, i in found]
            return {"devices": devices,
                    "reason": self.controller.connection.backend_error or ""}

    # -- arbitrary waveforms -------------------------------------------------
    def upload_arb(self, n: int, data: np.ndarray, *, name: str,
                   frequency: Optional[float], amplitude: float, offset: float,
                   phase: Optional[float] = None, save_raf: bool = True) -> dict:
        with self.lock:
            self.require()
            self._upload_locked(n, data, name=name, frequency=frequency,
                                amplitude=amplitude, offset=offset, phase=phase,
                                save_raf=save_raf, pre_clear=True)
            self._invalidate()
            return self.read_channel(n)

    def _upload_locked(self, n: int, data: np.ndarray, *, name: str,
                       frequency: Optional[float], amplitude: float, offset: float,
                       phase: Optional[float], save_raf: bool,
                       pre_clear: bool) -> None:
        wf, _ = self.require()
        points = len(data)
        if not (arb.DG822_MIN_POINTS <= points <= arb.DG822_MAX_POINTS):
            raise ValueError(
                f"arbitrary waveforms must be "
                f"{arb.DG822_MIN_POINTS}..{arb.DG822_MAX_POINTS} points, got {points}")

        raf_name = (name or "CUSTOM")[:7].upper()
        buf = ArbitraryWaveform(name or "CUSTOM")
        buf.set_data_normalized(np.asarray(data, dtype=float))

        if pre_clear:
            # Firmware 00.02.x keeps the previous buffer in DDRIII memory and a
            # fresh DAC16 upload can composite with it. Switching the channel to
            # SIN first is the GUI's workaround and the difference between a
            # clean upload and a corrupted one.
            mode_before = (wf.get_function(n) or "").upper()
            if "USER" in mode_before or "SEQ" in mode_before:
                wf.set_function(n, WaveformType.SINE)
                time.sleep(0.3)

        self._ok(wf.upload_arbitrary_waveform_from_object(n, buf),
                 f"DAC16 upload of {points} points to CH{n}")
        time.sleep(0.2)

        # The END flag on the DAC16 packet is what makes the instrument switch
        # itself to arbitrary output; nothing sends :FUNCtion USER, because on
        # some firmware that resets the buffer to a built-in SINC. If the switch
        # did not happen, the channel is still generating its old shape and the
        # upload achieved nothing visible - say so rather than reporting success.
        mode_after = (wf.get_function(n) or "?").strip()
        if "USER" not in mode_after.upper() and "SEQ" not in mode_after.upper():
            print(f"[dg822] CH{n}: uploaded {points} points but the instrument "
                  f"is still in {mode_after} mode, not arbitrary", flush=True)

        if save_raf:
            # Names longer than 7 characters are truncated by the driver; the
            # instrument's own store allows no more.
            self._ok(wf.store_arb_file(raf_name), f'MMEMory:STORe "{raf_name}.RAF"')

        freq = frequency if frequency and frequency > 0 else (
            self._ch[n].get("frequency") or 1000.0)
        ph = phase if phase is not None else (self._ch[n].get("phase") or 0.0)
        self._ok(wf.apply_arbitrary(n, freq, amplitude, offset, ph, num_points=points),
                 "arbitrary parameter set")

        c = self._ch[n]
        c["arb_data"] = np.asarray(data, dtype=float)
        c["points"] = points
        c["arb_loaded"] = True
        c["arb_name"] = raf_name if save_raf else (name or "CUSTOM")
        c["sample_rate"] = freq * points

    def load_raf(self, n: int, name: str) -> dict:
        with self.lock:
            wf, _ = self.require()
            self._ok(wf.load_arb_file(name), f'MMEMory:LOAD "{name}"')
            self._ch[n]["arb_name"] = name
            self._ch[n]["arb_loaded"] = True
            # The host never saw the samples - they went instrument-internal
            # store to channel - so there is nothing to preview from here.
            self._ch[n]["arb_data"] = None
            self._ch[n]["points"] = None
            self._invalidate()
            return self.read_channel(n)

    def store_raf(self, name: str) -> None:
        with self.lock:
            wf, _ = self.require()
            self._ok(wf.store_arb_file(name), f'MMEMory:STORe "{name}"')

    def instrument_files(self) -> List[str]:
        """The instrument's arbitrary-file catalogue, or [] when it is not
        reachable — the page must still be able to browse local files offline."""
        with self.lock:
            if not self.ok:
                return []
            try:
                wf, _ = self.require()
                raw = wf.list_arb_files()
            except Exception:
                return []
            return _parse_catalog(raw)

    def apply_preset(self, preset: dict, n: int) -> dict:
        return self.apply(n, dict(preset["channel_defaults"]))


def _parse_apply(reply: Optional[str]):
    """Split a ':SOURceN:APPLy?' reply into (function, freq, amp, offset, phase).

    Returns None if the reply is missing or does not have the five fields, which
    puts the caller back on the individual getters.
    """
    if not reply:
        return None
    parts = [p.strip() for p in reply.strip().strip('"').split(",")]
    if len(parts) < 5:
        return None
    try:
        return (parts[0].strip('"'), float(parts[1]), float(parts[2]),
                float(parts[3]), float(parts[4]))
    except ValueError:
        return None


def _parse_catalog(reply: Optional[str]) -> List[str]:
    """':MMEMory:CATalog:DATA:ARBitrary?' -> plain names."""
    if not reply:
        return []
    names = []
    for tok in reply.split(","):
        name = tok.strip().strip('"').strip()
        # Real firmware prefixes the catalogue with size fields; keep the entries
        # that look like file names.
        if name and not re.fullmatch(r"[0-9]+", name):
            names.append(name)
    return names


# --------------------------------------------------------------------------- #
# preview and generation — pure numpy, no matplotlib anywhere in a request path
# --------------------------------------------------------------------------- #

def build_preview(channel: int, params: dict, arb_data: Optional[np.ndarray]) -> dict:
    """The trace the page draws on its canvas.

    Deliberately server-side and deliberately array-only: the maths is the same
    code the desktop GUI plots (rigol_dg822.plot's static generators), so the
    preview cannot drift from it, and NO figure is ever rendered — matplotlib is
    never imported on this path.
    """
    wave = _canon_waveform(_text(params, "waveform", "sine"))
    freq = _num(params, "frequency", 1000.0)
    amp = _num(params, "amplitude", 5.0)
    off = _num(params, "offset", 0.0)
    phase = _num(params, "phase", 0.0)
    duty = _num(params, "duty_cycle", 50.0)
    width = _num(params, "pulse_width")
    symm = _num(params, "symmetry", 50.0)
    points = int(_num(params, "points", _PREVIEW_DEFAULT))
    points = max(16, min(points, _PREVIEW_MAX))
    cycles = 3

    warnings: List[str] = []
    if wave not in ("noise", "dc") and freq <= 0:
        raise ValueError("frequency must be positive")

    period = (1.0 / freq) if (wave not in ("noise", "dc") and freq > 0) else None
    title = f"CH{channel} - {wave}"

    if wave == "sine":
        t, v = WaveformPlotter.generate_sine(freq, amp, off, phase, points, cycles)
    elif wave == "square":
        t, v = _square_v(freq, amp, off, phase, duty, points, cycles)
    elif wave == "pulse":
        d = _pulse_duty(width, period) if width is not None else duty
        if width is not None:
            raw = width / period * 100.0
            if raw > 100.0:
                warnings.append(
                    f"pulse width {width:.6g} s is longer than the {period:.6g} s "
                    f"period ({raw:.1f} % duty) - clamped to 99 %")
            elif abs(raw - d) > 1e-9:
                warnings.append(f"duty cycle clamped from {raw:.2f} % to {d:.2f} %")
        t, v = WaveformPlotter.generate_pulse(freq, amp, off, phase, d,
                                              num_points=points, num_cycles=cycles,
                                              centered=True)
        # The GUI names the pulse geometry in its plot title; the numbers are
        # what an operator checks a width against.
        start = (period - period * d / 100.0) / 2.0
        title = (f"CH{channel} - pulse (period={period:.6g} s, "
                 f"width={period * d / 100.0:.6g} s, start={start:.6g} s)")
    elif wave == "ramp":
        t, v = _ramp_v(freq, amp, off, phase, symm, points, cycles)
    elif wave == "noise":
        # Noise and DC have no period, so the GUI shows a fixed 10 ms window.
        t, v = WaveformPlotter.generate_noise(amp, off, points, duration=0.01)
        warnings.append("noise ignores frequency and phase")
    elif wave == "dc":
        t, v = WaveformPlotter.generate_dc(off, points, duration=0.01)
        warnings.append("DC takes the offset as its level; "
                        "frequency, amplitude and phase are ignored")
    else:                                             # arbitrary
        if arb_data is None or not len(arb_data):
            t, v = WaveformPlotter.generate_dc(0.0, points, duration=0.01)
            warnings.append("no arbitrary waveform loaded on this channel")
            period = None
        else:
            t, v = WaveformPlotter.generate_arbitrary(np.asarray(arb_data, dtype=float),
                                                      freq, amp, off, cycles)
            if len(v) > _PREVIEW_MAX:
                keep = np.unique(np.round(
                    np.linspace(0, len(v) - 1, _PREVIEW_MAX)).astype(int))
                t, v = t[keep], v[keep]

    scaled, unit = WaveformPlotter.format_time_axis(np.asarray(t, dtype=float))
    return {"t": _jsonable(scaled), "v": _jsonable(v), "t_unit": unit,
            "t_scale": _TIME_UNIT_SCALE.get(unit, 1.0), "title": title,
            "period": period, "warnings": warnings}


def generate_arb(body: dict) -> dict:
    """Synthesise a normalised buffer from the shape catalogue.

    Feasibility warnings are returned, not enforced: the tkinter dialog stops
    and asks "continue anyway?", and the equivalent here is handing the page the
    warning and letting the operator decide. The one exception is a shape or a
    frequency the maths cannot express at all, which is a 422.
    """
    shape = _text(body, "shape", "square").strip().lower()
    if shape not in _SHAPE_BY_NAME:
        raise ValueError(f"unknown shape {shape!r} - see GET /api/arb/shapes")

    polarity = _text(body, "polarity", "unipolar").strip().lower()
    if polarity not in ("unipolar", "bipolar"):
        raise ValueError("polarity must be 'unipolar' or 'bipolar'")
    bipolar = polarity == "bipolar"

    drive = _text(body, "drive_mode", "frequency").strip().lower()
    if drive not in ("frequency", "time"):
        raise ValueError("drive_mode must be 'frequency' or 'time'")

    params = body.get("params") or {}
    if not isinstance(params, dict):
        raise ValueError("'params' must be an object")

    if shape == "frequency_comb":
        return _generate_comb(body, params)

    if drive == "frequency":
        output_freq = _num(body, "frequency", None, required=True)
    else:
        # Under bipolar drive the entered period is the HALF period: the buffer
        # holds the shape followed by its mirror, so the emitted period is twice
        # the shape's. Same rule as the desktop dialog.
        period_s = _num(body, "period", None, required=True)
        if period_s <= 0:
            raise ValueError("period must be positive")
        output_freq = 1.0 / (2.0 * period_s) if bipolar else 1.0 / period_s
    if output_freq <= 0:
        raise ValueError("frequency must be positive")

    points = _int(body, "points") or arb.compute_optimal_points(output_freq)
    points = max(arb.DG822_MIN_POINTS, min(int(points), arb.DG822_MAX_POINTS))

    warnings: List[str] = []
    feas = arb.check_frequency_feasibility(output_freq, points)
    if feas.get("warning"):
        warnings.append(feas["warning"])

    period = 1.0 / output_freq
    shape_period = period / 2.0 if bipolar else period
    # Bipolar spends half the point budget on the base shape and interpolates
    # the doubled array back to the full count.
    gen_points = max(points // 2, arb.DG822_MIN_POINTS) if bipolar else points

    # Echoed back as info.params, so it records what was USED, not what was
    # asked for: the trapezoid's auto pulse time and any default that filled in
    # for an omitted key both belong in the record of what was generated.
    used: Dict[str, float] = {}

    def pct(name: str) -> float:
        spec = next(p for p in _SHAPE_BY_NAME[shape]["params"] if p["name"] == name)
        used[name] = float(_num(params, name, spec["default"]))
        return used[name]

    if shape == "square":
        wf = WaveformGenerator.square(gen_points, pct("on_time"))
    elif shape == "sine":
        wf = WaveformGenerator.sine(gen_points, pct("phase"))
    elif shape == "ramp":
        wf = WaveformGenerator.ramp(gen_points, pct("rise_time"))
    elif shape == "trapezoid":
        rise, fall = pct("rise_time"), pct("fall_time")
        # The dialog's "specify pulse time" checkbox, inverted: leave it out and
        # the flat top fills whatever the edges do not use.
        pulse = (_num(params, "pulse_time") if params.get("pulse_time") is not None
                 else max(0.0, 100.0 - rise - fall))
        used["pulse_time"] = pulse
        if rise + pulse + fall > 100.001:
            warnings.append(
                f"rise + pulse + fall = {rise + pulse + fall:.4g} % exceeds the "
                f"shape period; the generator rescales all three to fit")
        wf = WaveformGenerator.trapezoid(gen_points, rise, pulse, fall)
    elif shape == "pulse":
        wf = WaveformGenerator.pulse(gen_points, pct("on_time"), pct("rise_time"),
                                     pct("fall_time"))
    elif shape == "sinc":
        wf = WaveformGenerator.sinc(gen_points, int(pct("lobes")))
    elif shape == "exponential":
        # The dialog's "exponential" is the decay only; the rise generator exists
        # but the GUI never reaches it, and parity beats completeness here.
        wf = WaveformGenerator.exponential_decay(gen_points, pct("tau"))
    else:                                             # gaussian
        wf = WaveformGenerator.gaussian(gen_points, pct("sigma"))

    if bipolar:
        wf = WaveformGenerator.make_bipolar(wf, total_points=points)

    data = np.asarray(wf.data, dtype=float)
    info = {"shape": shape, "polarity": polarity, "drive_mode": drive,
            "period": period, "shape_period": shape_period,
            "description": wf.description, "feasible": bool(feas.get("achievable")),
            "params": used}
    return _generated(wf.name, data, output_freq, info, warnings)


def _generate_comb(body: dict, params: dict) -> dict:
    comb = body.get("comb") or {}
    if not isinstance(comb, dict):
        raise ValueError("'comb' must be an object")
    mode = _text(comb, "mode", "range").strip().lower()
    if mode == "list":
        raw = comb.get("list") or []
        if isinstance(raw, str):
            raw = [tok for tok in raw.replace(";", ",").split(",") if tok.strip()]
        try:
            freqs = [float(f) for f in raw]
        except (TypeError, ValueError):
            raise ValueError("comb.list must be a list of frequencies in Hz")
    elif mode == "range":
        start = _num(comb, "start", None, required=True)
        stop = _num(comb, "stop", None, required=True)
        step = _num(comb, "step", None, required=True)
        if step <= 0:
            raise ValueError("comb.step must be positive")
        if stop < start:
            raise ValueError("comb.stop must not be below comb.start")
        # The half-step guard is what makes the stop value inclusive.
        freqs = [float(f) for f in np.arange(start, stop + step / 2.0, step)]
    else:
        raise ValueError("comb.mode must be 'range' or 'list'")

    if not freqs:
        raise ValueError("no frequencies specified")
    if any(f <= 0 for f in freqs):
        raise ValueError("all comb frequencies must be positive")

    num_pts, info = arb.compute_optimal_points_for_comb(freqs)
    warnings = [info["warning"]] if info.get("warning") else []

    requested = _int(body, "points")
    if requested:
        num_pts = max(arb.DG822_MIN_POINTS, min(int(requested), arb.DG822_MAX_POINTS))
        warnings.append(
            f"point count overridden to {num_pts}; the computed optimum was "
            f"{info['num_points']}")

    phases = _text(comb, "phases", "random").strip().lower()
    if phases not in ("random", "zero"):
        raise ValueError("comb.phases must be 'random' or 'zero'")
    random_phases = phases == "random"
    # 0 iterations leaves the search with no best signal at all (a TypeError out
    # of the generator), and an unbounded count is a request that never returns.
    iterations = max(1, min(int(_num(comb, "iterations", 1000)), _MC_MAX))

    wf = WaveformGenerator.frequency_comb(
        frequencies=freqs, num_points=num_pts, random_phases=random_phases,
        monte_carlo_iterations=iterations if random_phases else 1)

    fundamental = float(wf.comb_info["fundamental"])
    # _approximate_gcd falls back to min(freqs) when the tones are near
    # incommensurate. Detect the fallback by its consequence rather than by
    # comparing to min(freqs) - for 1,2,..,10 Hz the true GCD *is* min(freqs).
    # If a tone is not a whole number of cycles per period, the loop steps at
    # the wrap and the operator should know why.
    ratios = np.asarray(freqs, dtype=float) / fundamental
    if np.any(np.abs(ratios - np.round(ratios)) > 1e-6):
        warnings.append(
            "these tones share no usable common divisor, so the period was "
            "taken as 1/f_min; the looped waveform will step at the wrap")

    out_info = {"shape": "frequency_comb", "polarity": "bipolar",
                "drive_mode": "frequency", "tones": len(freqs),
                "frequencies": [float(f) for f in freqs],
                "phases": [float(p) for p in wf.comb_phases],
                "phase_mode": phases, "iterations": iterations if random_phases else 0,
                "fundamental": fundamental,
                "f_max": float(wf.comb_info["f_max"]),
                "harmonics": float(wf.comb_info["harmonics"]),
                "min_points_needed": int(wf.comb_info["min_points_needed"]),
                "period": 1.0 / fundamental,
                "description": wf.description}
    return _generated(wf.name, np.asarray(wf.data, dtype=float), fundamental,
                      out_info, warnings)


def _generated(name: str, data: np.ndarray, output_frequency: float,
               info: dict, warnings: List[str]) -> dict:
    """Package a synthesised buffer for the page (the caller adds the token)."""
    points = len(data)
    preview = _decimate(data, _ARB_PREVIEW_MAX)
    info = dict(info)
    info["full_points"] = points
    info["decimated"] = len(preview) < points
    return {"name": name, "points": points,
            "sample_rate": output_frequency * points,
            "output_frequency": output_frequency,
            "data": _jsonable(preview), "info": info,
            "warnings": list(warnings), "_full": data}


# --------------------------------------------------------------------------- #
# local waveform library
# --------------------------------------------------------------------------- #

def _waveform_dir() -> str:
    try:
        os.makedirs(_WAVEFORMS, exist_ok=True)
    except OSError:
        pass
    return _WAVEFORMS


def _local_path(name: str, ext: str = ".csv") -> str:
    """Resolve a library file name. basename() is the traversal guard — the name
    comes straight off the wire."""
    base = os.path.basename((name or "").strip())
    if not base:
        raise ValueError("a file name is required")
    if not base.lower().endswith(ext):
        base += ext
    return os.path.join(_waveform_dir(), base)


def _local_files() -> List[str]:
    try:
        return sorted(f for f in os.listdir(_waveform_dir())
                      if f.lower().endswith(".csv"))
    except OSError:
        return []


# --------------------------------------------------------------------------- #
# app assembly
# --------------------------------------------------------------------------- #

def make_session(resource: Optional[str] = None, *, simulate: bool = False,
                 timeout: int = 5000) -> DG822Session:
    """Build the session the panel (or ``serve``) hands to ``create_app``."""
    return DG822Session(resource, simulate=simulate, timeout=timeout)


def start(session: DG822Session) -> None:
    """Bring the generator up. Never raises — mirrors webapp.start_all."""
    try:
        session.start()
    except Exception as exc:                  # belt and braces; start() shouldn't
        session.ok, session.error = False, f"{type(exc).__name__}: {exc}"


def stop(session: DG822Session) -> None:
    """Outputs off, then release the instrument. Never raises."""
    try:
        session.stop()
    except Exception as exc:
        print(f"[dg822] error during stop: {exc}", flush=True)


def create_app(session: DG822Session, *, manage_lifecycle: bool = True):
    """Build the FastAPI app for one :class:`DG822Session`.

    ``manage_lifecycle=False`` omits the startup/shutdown lifespan so a parent
    app (xsphere_daq.panel) owns start/stop itself — Starlette does not run a
    mounted sub-app's lifespan, so passing True while mounted would be silently
    inert and the instrument would never be opened or released. The page derives
    its API base from window.location, so mounting under any prefix works.
    """
    @asynccontextmanager
    async def lifespan(app):
        start(session)
        try:
            yield
        finally:
            stop(session)

    app = FastAPI(lifespan=lifespan,
                  title="RIGOL DG822") if manage_lifecycle else FastAPI(title="RIGOL DG822")
    app.state.session = session
    # The dock idiom: publish the teardown so a parent that prefers hooks to
    # direct calls still gets outputs-off on the way down.
    app.state.shutdown_hooks = [lambda: stop(session)]

    @app.exception_handler(Exception)
    async def _never_500(request, exc):       # noqa: ANN001 - starlette signature
        """Backstop for the never-raise policy.

        Every path below maps its own failures, so reaching here means a bug —
        but the operator gets a readable line instead of a traceback page, and
        Starlette still re-raises afterwards so the server log keeps the stack.
        """
        return JSONResponse(status_code=503,
                            content={"detail": f"{type(exc).__name__}: {exc}"})

    # --- guards -------------------------------------------------------------
    def chan(n: int) -> int:
        if n not in CHANNELS:
            raise HTTPException(404, f"no channel {n} - the DG822 has 1 and 2")
        return n

    def call(fn, *args, **kwargs):
        """Run an instrument operation, mapping failures onto the contract.

        404 the thing does not exist · 422 the value cannot be accepted ·
        503 not connected, or the instrument refused. One funnel rather than a
        try/except in every endpoint, so the mapping cannot drift between them.
        """
        try:
            return fn(*args, **kwargs)
        except HTTPException:
            raise
        except _Unavailable as exc:
            raise HTTPException(503, str(exc))
        except ValueError as exc:
            raise HTTPException(422, str(exc))
        except (FileNotFoundError, LookupError) as exc:
            raise HTTPException(404, str(exc))
        except Exception as exc:
            raise HTTPException(503, f"{type(exc).__name__}: {exc}")

    # --- page / static ------------------------------------------------------
    # Read from disk per request and edited constantly, so never let a browser
    # cache them: a stale rigol.css/js silently reverts a fix and costs an hour
    # of debugging something that is already correct on disk. Matches the dock's
    # own policy (camera_dock/webapp.py `_page`).
    def _page(fname: str) -> FileResponse:
        return FileResponse(os.path.join(_STATIC, fname),
                            headers={"Cache-Control": "no-cache"})

    @app.get("/")
    def index():
        path = os.path.join(_STATIC, "index.html")
        if not os.path.isfile(path):
            # Never-raise, extended to the page itself: the API is fully usable
            # without the assets, so say what is missing rather than 500.
            return HTMLResponse(
                "<!doctype html><meta charset='utf-8'>"
                "<body style=\"margin:0;background:#111;color:#ddd;"
                "font-family:system-ui,sans-serif;padding:24px\">"
                "<h2 style='color:#c77'>DG822 page assets are missing</h2>"
                f"<pre style='white-space:pre-wrap;color:#bbb'>{_STATIC}"
                "\\index.html not found</pre>"
                "<p style='color:#888'>The HTTP API under /api is unaffected.</p>"
                "</body>", status_code=503)
        return _page("index.html")

    @app.get("/static/{fname}")
    def static_file(fname: str):
        # basename() is the traversal guard; there is no StaticFiles mount here
        # precisely so the no-cache header above always applies.
        base = os.path.basename(fname)
        if not os.path.isfile(os.path.join(_STATIC, base)):
            raise HTTPException(404, f"no asset '{base}'")
        return _page(base)

    # --- instrument ---------------------------------------------------------
    @app.get("/api/state")
    def get_state():
        # need_ok=False in spirit: a disconnected generator still has a state,
        # and the page needs it to render the "not connected" case.
        return call(session.state)

    @app.get("/api/devices")
    def get_devices():
        return call(session.devices)

    @app.post("/api/connect")
    def post_connect(payload: dict = Body(default_factory=dict)):
        resource = _text(payload, "resource").strip() or None
        sim = _bool(payload, "sim", resource == SIM_RESOURCE)
        call(session.connect, resource, sim)
        if not session.ok:
            raise HTTPException(503, session.error or "could not connect")
        return call(session.state)

    @app.post("/api/disconnect")
    def post_disconnect():
        call(session.disconnect)
        return call(session.state)

    @app.post("/api/reset")
    def post_reset():
        return call(session.reset)

    @app.post("/api/beep")
    def post_beep():
        call(session.beep)
        return {"ok": True}

    @app.post("/api/sync-phases")
    def post_sync_phases():
        call(session.sync_phases)
        return {"ok": True}

    # --- per channel --------------------------------------------------------
    @app.post("/api/ch/{n}/apply")
    def ch_apply(n: int, payload: dict = Body(default_factory=dict)):
        return call(session.apply, chan(n), payload)

    @app.post("/api/ch/{n}/set")
    def ch_set(n: int, payload: dict = Body(default_factory=dict)):
        return call(session.set_params, chan(n), payload)

    @app.post("/api/ch/{n}/output")
    def ch_output(n: int, payload: dict = Body(default_factory=dict)):
        chan(n)
        on = _bool(payload, "on", True)
        seconds = call(_num, payload, "seconds")
        cycles = call(_int, payload, "cycles")
        return call(session.set_output, n, on, seconds, cycles)

    @app.post("/api/ch/{n}/load")
    def ch_load(n: int, payload: dict = Body(default_factory=dict)):
        chan(n)
        if "impedance" not in payload:
            raise HTTPException(422, "'impedance' is required")
        return call(session.set_load, n, payload["impedance"])

    @app.post("/api/ch/{n}/polarity")
    def ch_polarity(n: int, payload: dict = Body(default_factory=dict)):
        return call(session.set_polarity, chan(n), _bool(payload, "inverted"))

    @app.post("/api/ch/{n}/sync")
    def ch_sync(n: int, payload: dict = Body(default_factory=dict)):
        return call(session.set_sync, chan(n), _bool(payload, "on"))

    @app.get("/api/ch/{n}/preview")
    def ch_preview(n: int, waveform: str = "sine", frequency: float = 1000.0,
                   amplitude: float = 5.0, offset: float = 0.0, phase: float = 0.0,
                   duty_cycle: float = 50.0, pulse_width: Optional[float] = None,
                   symmetry: float = 50.0, points: int = _PREVIEW_DEFAULT,
                   token: Optional[str] = None):
        """Pure-numpy trace for the page's canvas. No instrument access at all —
        it previews what an Apply *would* do, so it works while disconnected."""
        chan(n)
        params = {"waveform": waveform, "frequency": frequency, "amplitude": amplitude,
                  "offset": offset, "phase": phase, "duty_cycle": duty_cycle,
                  "pulse_width": pulse_width, "symmetry": symmetry, "points": points}
        data = None
        if token:
            data = call(session.tokens.get, token)["data"]
        elif call(_canon_waveform, waveform) == "arbitrary":
            data = session.arb_buffer(n)
        return call(build_preview, n, params, data)

    # --- arbitrary waveforms ------------------------------------------------
    @app.get("/api/arb/shapes")
    def arb_shapes():
        return ARB_SHAPES

    @app.post("/api/arb/generate")
    def arb_generate(payload: dict = Body(default_factory=dict)):
        result = call(generate_arb, payload)
        full = result.pop("_full")
        result["info"]["token"] = session.tokens.put({
            "data": full, "name": result["name"],
            "output_frequency": result["output_frequency"],
            "points": result["points"]})
        return result

    @app.post("/api/arb/upload")
    def arb_upload(payload: dict = Body(default_factory=dict)):
        n = chan(call(_int, payload, "channel", 1))
        data, freq, default_name = call(_resolve_buffer, session, payload)
        name = _text(payload, "name").strip() or default_name
        return call(session.upload_arb, n, data, name=name,
                    frequency=_num(payload, "frequency", freq),
                    amplitude=_num(payload, "amplitude", 5.0),
                    offset=_num(payload, "offset", 0.0),
                    phase=_num(payload, "phase"),
                    save_raf=_bool(payload, "save_raf", True))

    @app.get("/api/arb/files")
    def arb_files():
        return {"local": _local_files(), "instrument": session.instrument_files(),
                "dir": _waveform_dir()}

    @app.post("/api/arb/save-csv")
    def arb_save_csv(payload: dict = Body(default_factory=dict)):
        data, _freq, default_name = call(_resolve_buffer, session, payload)
        name = _text(payload, "name").strip() or default_name
        amplitude = _num(payload, "amplitude", 10.0)
        path = call(_local_path, name, ".csv")
        buf = ArbitraryWaveform(os.path.splitext(os.path.basename(path))[0])
        buf.set_data_normalized(np.asarray(data, dtype=float))
        raf = os.path.splitext(path)[0] + ".raf"
        # GUI parity: the .raf sibling is written alongside, so the file can be
        # dropped straight onto the instrument's volume.
        call(buf.save_csv, path, amplitude)
        call(buf.save_binary, raf, amplitude)
        return {"path": path, "raf": raf}

    @app.post("/api/arb/load-csv")
    def arb_load_csv(payload: dict = Body(default_factory=dict)):
        path = call(_local_path, _text(payload, "name"), ".csv")
        if not os.path.isfile(path):
            raise HTTPException(404, f"no local waveform '{os.path.basename(path)}'")
        buf = ArbitraryWaveform.from_csv(path)
        if buf.data is None or not len(buf.data):
            # from_csv ignores its loader's return value, so this is the only
            # place a bad file is caught.
            raise HTTPException(422, f"{os.path.basename(path)} has no readable data")
        data = np.clip(np.asarray(buf.data, dtype=float), -1.0, 1.0)
        # Neither the CSV nor the RAF format stores a frequency or a sample rate,
        # so there is nothing honest to report here — the channel's own frequency
        # is used at upload time.
        result = _generated(buf.name, data, 0.0,
                            {"shape": "file", "source": path,
                             "description": f"loaded from {os.path.basename(path)}"},
                            ["the file format carries no frequency or sample rate; "
                             "the channel's current frequency is used on upload"])
        full = result.pop("_full")
        result["output_frequency"] = None
        result["sample_rate"] = None
        result["info"]["token"] = session.tokens.put({
            "data": full, "name": buf.name, "output_frequency": None,
            "points": len(full)})
        return result

    @app.post("/api/arb/store-raf")
    def arb_store_raf(payload: dict = Body(default_factory=dict)):
        name = _text(payload, "name").strip()
        if not name:
            raise HTTPException(422, "'name' is required")
        call(session.store_raf, name)
        return {"ok": True}

    @app.post("/api/arb/load-raf")
    def arb_load_raf(payload: dict = Body(default_factory=dict)):
        name = _text(payload, "name").strip()
        if not name:
            raise HTTPException(422, "'name' is required")
        return call(session.load_raf, chan(call(_int, payload, "channel", 1)), name)

    # --- presets ------------------------------------------------------------
    @app.get("/api/presets")
    def get_presets():
        return PRESETS

    @app.post("/api/presets/apply")
    def apply_preset(payload: dict = Body(default_factory=dict)):
        pid = _text(payload, "id").strip()
        preset = _PRESET_BY_ID.get(pid)
        if preset is None:
            raise HTTPException(404, f"no preset '{pid}'")
        return call(session.apply_preset, preset,
                    chan(call(_int, payload, "channel", 1)))

    return app


def _resolve_buffer(session: DG822Session, payload: dict):
    """Find the buffer an upload/save refers to: token, local CSV, or inline.

    Returns (data, output_frequency|None, default_name). The token path is the
    normal one — it is why a 8192-point buffer does not have to make the round
    trip back through the browser.
    """
    token = _text(payload, "token").strip()
    if token:
        entry = session.tokens.get(token)
        return (np.asarray(entry["data"], dtype=float), entry.get("output_frequency"),
                entry.get("name") or "CUSTOM")

    csv_name = _text(payload, "csv_name").strip()
    if csv_name:
        path = _local_path(csv_name, ".csv")
        if not os.path.isfile(path):
            raise FileNotFoundError(f"no local waveform '{os.path.basename(path)}'")
        buf = ArbitraryWaveform.from_csv(path)
        if buf.data is None or not len(buf.data):
            raise ValueError(f"{os.path.basename(path)} has no readable data")
        return (np.clip(np.asarray(buf.data, dtype=float), -1.0, 1.0), None, buf.name)

    data = payload.get("data")
    if data is not None:
        try:
            arr = np.asarray(data, dtype=float)
        except (TypeError, ValueError):
            raise ValueError("'data' must be a list of numbers")
        if arr.ndim != 1 or not len(arr):
            raise ValueError("'data' must be a non-empty flat list of numbers")
        if not np.all(np.isfinite(arr)):
            raise ValueError("'data' contains non-finite values")
        return np.clip(arr, -1.0, 1.0), None, "CUSTOM"

    raise ValueError("give one of 'token', 'csv_name' or 'data'")


# --------------------------------------------------------------------------- #
# entry point
# --------------------------------------------------------------------------- #

def serve(session: DG822Session, host: str = "127.0.0.1", port: int = 8010) -> None:
    import uvicorn
    # timeout_graceful_shutdown bounds the drain so Ctrl+C always reaches the
    # lifespan teardown — which is what switches the outputs off.
    app = create_app(session)
    config = uvicorn.Config(app, host=host, port=port, timeout_graceful_shutdown=5)
    server = uvicorn.Server(config)
    app.state.server = server
    server.run()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Control a RIGOL DG822 from the browser.")
    parser.add_argument("--resource", default=None,
                        help="VISA resource string (e.g. USB0::0x1AB1::0x0643::"
                             "DG8A204201757::0::INSTR). Omitted: discover USB "
                             "hardware and take the first DG800-series unit.")
    parser.add_argument("--sim", action="store_true",
                        help="drive the simulated instrument (rigol_dg822.sim); "
                             "needs no VISA implementation and no hardware")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8010)
    args = parser.parse_args()
    serve(make_session(args.resource, simulate=args.sim),
          host=args.host, port=args.port)


if __name__ == "__main__":
    main()
