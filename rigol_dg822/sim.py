"""
RIGOL DG822 Waveform Generator - Simulated Instrument

A DG822 that lives in this process. It presents the same duck-typed surface a
pyvisa resource presents to :mod:`rigol_dg822.connection` -- ``write``,
``query``, ``write_raw``, ``close``, ``clear`` and the three settable
attributes ``timeout`` / ``read_termination`` / ``write_termination`` -- so the
connection layer drops onto it without a second code path.

It exists because the DAQ box has no NI-VISA and no pyvisa-py: without this,
``pyvisa.ResourceManager()`` raises "Could not locate a VISA implementation"
and nothing above the driver can be exercised at all. The CLI, the web page and
the tests run against this backend.

It is a SCPI parser, not a stub. Every command the driver sends is parsed and
folded into per-channel state, including the DAC16 binary block, so state
written is state read back. A command it does not recognise is pushed onto the
error queue and reported by ``:SYSTem:ERRor?`` rather than silently accepted --
that turns the sim into a way of catching a malformed SCPI string before it
reaches a real instrument.

``*IDN?`` answers with SIMULATED in the serial field, so a simulated run can
never be mistaken for hardware in a log.

Use it by resource name::

    from rigol_dg822 import DG822Controller, SIM_RESOURCE
    dg = DG822Controller(SIM_RESOURCE)      # or DG822Controller(simulate=True)
    dg.connect()
"""

from __future__ import annotations

import fnmatch
import re
import struct
from typing import Dict, List, Optional, Tuple

# The resource name that routes a connection here instead of to pyvisa.
SIM_RESOURCE = "SIM::DG822::INSTR"

# Serial field says SIMULATED so no log can be misread as a hardware run. The
# vendor and model fields stay realistic because discover_devices() filters on
# "RIGOL" (case-insensitive) and on "DG822" (case-sensitive).
SIM_IDN = "Rigol Technologies,DG822,SIMULATED-NO-HARDWARE,SIM 00.02.05"

SIM_VERSION = "SIMULATED,1.0"

# Firmware 00.02.x limits, mirrored so the sim rejects what the hardware rejects.
MIN_ARB_POINTS = 8
MAX_ARB_POINTS = 8192
DAC_FULL_SCALE = 16383  # 14-bit codes stored in 16-bit words

# High-Z reads back as 9.9E+37 on the real device; output.get_impedance maps
# anything above 1e30 to inf, so this value is load-bearing.
HIGH_Z_REPLY = 9.9e37


# ---------------------------------------------------------------------------
# SCPI mnemonic canonicalisation
# ---------------------------------------------------------------------------
# The driver sends the long mixed-case forms (":SOURce1:FUNCtion:SQUare:DCYCle")
# but a human at the CLI will send short or all-caps forms. Both are legal SCPI,
# so every mnemonic is folded to its short form before dispatch. The table is
# written in the mixed-case spelling: the capitals ARE the short form.
_SPECS = [
    "SOURce", "OUTPut", "MMEMory", "SYSTem",
    "APPLy", "FUNCtion", "FREQuency", "VOLTage", "OFFSet", "HIGH", "LOW",
    "PHASe", "SYNChronize", "TRACe", "DATA", "DAC16", "CATalog", "DELete",
    "SINusoid", "SQUare", "RAMP", "PULSe", "NOISe", "DC", "USER", "SEQuence",
    "ARBitrary", "HARMonic", "DCYCle", "WIDTh", "TRANsition", "LEADing",
    "TRAiling", "SYMMetry", "SRATe",
    "STATe", "LOAD", "INFinity", "POLarity", "NORMal", "INVerted", "SYNC",
    "MODE", "CARRier", "MARKer", "POSitive", "NEGative", "TRIGger", "SLOPe",
    "IDLE",
    "CDIRectory", "STORe", "ERRor", "VERSion", "BEEPer", "IMMediate",
    "VOLATILE", "END", "CONtinue", "DEFault", "MINimum", "MAXimum",
]


def _build_aliases() -> Dict[str, str]:
    aliases: Dict[str, str] = {}
    for spec in _SPECS:
        short = "".join(c for c in spec if not c.islower())
        aliases[spec.upper()] = short
        aliases[short] = short
    return aliases


_ALIASES = _build_aliases()
_TOKEN = re.compile(r"^([A-Za-z_][A-Za-z_0-9]*?)(\d*)$")


def _canon(token: str) -> str:
    """Fold one SCPI mnemonic to its short form, keeping any channel suffix."""
    m = _TOKEN.match(token.strip())
    if not m:
        return token.strip().upper()
    word, digits = m.group(1), m.group(2)
    return _ALIASES.get(word.upper(), word.upper()) + digits


def _split_channel(token: str) -> Tuple[str, int]:
    """Split "SOUR2" into ("SOUR", 2). Bare mnemonics default to channel 1."""
    m = re.match(r"^([A-Z_]+)(\d*)$", token)
    if not m:
        return token, 1
    return m.group(1), int(m.group(2) or 1)


def _nr3(value: float) -> str:
    """Format a reply the way the instrument does; the driver parses with float()."""
    if value == float("inf"):
        value = HIGH_Z_REPLY
    return f"{value:.6E}"


def _num(text: str, default: float = 0.0) -> Optional[float]:
    """Parse one SCPI parameter. Returns None if it is not a number at all."""
    t = text.strip().upper()
    if not t:
        return None
    if t.startswith(("DEF", "MIN", "MAX")):
        # APPLy:NOISe / APPLy:DC use DEFault as a positional placeholder.
        return default
    if t.startswith("INF"):
        return float("inf")
    try:
        return float(t)
    except ValueError:
        return None


def _is_on(text: str) -> Optional[bool]:
    t = text.strip().upper()
    if t in ("ON", "1", "TRUE"):
        return True
    if t in ("OFF", "0", "FALSE"):
        return False
    return None


class _Channel:
    """One DG822 output channel. Defaults match the instrument after *RST."""

    def __init__(self) -> None:
        self.function = "SIN"
        self.frequency = 1000.0      # Hz
        self.amplitude = 5.0         # Vpp
        self.offset = 0.0            # V
        self.phase = 0.0             # degrees
        self.square_duty = 50.0      # percent
        self.pulse_duty = 50.0       # percent
        self.pulse_width = 2e-4      # seconds
        self.pulse_lead = 8.4e-9     # seconds
        self.pulse_trail = 8.4e-9    # seconds
        self.ramp_symmetry = 50.0    # percent
        self.sequence_srate = 2000.0  # Sa/s
        self.output = False
        self.impedance = float("inf")  # DG822 powers up High-Z
        self.polarity = "NORM"
        self.sync = False
        self.sync_mode = "NORM"
        self.sync_polarity = "POS"
        self.trigger_out = False
        self.trigger_slope = "POS"
        self.idle = "FPT"
        self.arb_name = "VOLATILE"
        self.arb_data: List[float] = []   # normalised [-1, +1], one period

    def snapshot(self) -> dict:
        d = dict(self.__dict__)
        d["arb_points"] = len(self.arb_data)
        d.pop("arb_data")
        return d


class SimulatedDG822:
    """A DG822 with the interface of a pyvisa resource.

    Only the members the connection layer actually touches are implemented; the
    driver never calls read(), read_raw() or query_binary_values() on the
    instrument object, so those are deliberately absent -- if a future change
    starts using one, the sim should fail loudly rather than fake it.
    """

    def __init__(self, resource_name: str = SIM_RESOURCE) -> None:
        self.resource_name = resource_name
        self.timeout = 5000
        self.read_termination = "\n"
        self.write_termination = "\n"

        self.channels: Dict[int, _Channel] = {1: _Channel(), 2: _Channel()}
        self._errors: List[Tuple[int, str]] = []
        self._closed = False

        # Instrument-internal volume, not a host path: :MMEMory:CDIRectory "C:\"
        self._cwd = "C:\\"
        self._files: Dict[str, List[float]] = {}
        self._last_arb_channel = 1

    # -- pyvisa resource surface -------------------------------------------

    def clear(self) -> None:
        """Discard buffered I/O. connect() calls this inside a try/except."""
        self._errors.clear()

    def close(self) -> None:
        self._closed = True

    def write(self, command: str) -> int:
        self._check_open()
        self._dispatch(str(command))
        return len(command)

    def write_raw(self, data: bytes) -> int:
        self._check_open()
        self._dispatch_raw(bytes(data))
        return len(data)

    def query(self, command: str) -> str:
        self._check_open()
        reply = self._dispatch(str(command))
        # The connection layer calls .strip() on whatever comes back, so this
        # must always be a str -- an unanswerable query returns empty, which the
        # float getters turn into None, exactly as a real timeout would.
        return "" if reply is None else str(reply)

    # -- inspection (sim-only; the driver never calls these) ----------------

    @property
    def errors(self) -> List[Tuple[int, str]]:
        """Pending error queue, oldest first."""
        return list(self._errors)

    def snapshot(self) -> dict:
        """Full instrument state, for tests and the web page's sim banner."""
        return {
            "idn": SIM_IDN,
            "simulated": True,
            "cwd": self._cwd,
            "files": sorted(self._files),
            "errors": list(self._errors),
            "channels": {ch: c.snapshot() for ch, c in self.channels.items()},
        }

    # -- internals ----------------------------------------------------------

    def _check_open(self) -> None:
        if self._closed:
            raise RuntimeError("Simulated instrument session is closed")

    def _error(self, code: int, message: str) -> None:
        # Bounded like a real error queue; the instrument drops the oldest.
        self._errors.append((code, message))
        del self._errors[:-32]

    def _channel(self, index: int) -> Optional[_Channel]:
        ch = self.channels.get(index)
        if ch is None:
            self._error(-222, f"Data out of range; channel {index}")
        return ch

    def _dispatch_raw(self, data: bytes) -> None:
        """Parse the one binary frame the driver sends: DAC16 VOLATILE,END."""
        if b" " not in data:
            self._error(-101, "Invalid character in raw block")
            return
        head, rest = data.split(b" ", 1)
        parts = [_canon(t) for t in head.decode("ascii", "replace").lstrip(":").split(":")]
        root, index = _split_channel(parts[0]) if parts else ("", 1)
        if root != "SOUR" or parts[1:] != ["TRAC", "DATA", "DAC16"]:
            self._error(-113, f"Undefined header; {head.decode('ascii', 'replace')}")
            return

        fields = rest.split(b",", 2)
        if len(fields) != 3:
            self._error(-109, "Missing parameter; DAC16 needs VOLATILE,<mode>,<block>")
            return
        mode = _canon(fields[1].decode("ascii", "replace"))
        block = fields[2].strip()

        if not block.startswith(b"#"):
            self._error(-161, "Invalid block data; missing # header")
            return
        try:
            digits = int(block[1:2])
            byte_count = int(block[2:2 + digits])
        except ValueError:
            self._error(-161, "Invalid block data; bad length header")
            return
        payload = block[2 + digits:2 + digits + byte_count]
        if len(payload) != byte_count:
            self._error(-161,
                        f"Invalid block data; declared {byte_count} bytes, got {len(payload)}")
            return

        codes = struct.unpack(f"<{byte_count // 2}H", payload)
        if any(c > 0x3FFF for c in codes):
            self._error(-222, "Data out of range; DAC16 code above 0x3FFF")

        ch = self._channel(index)
        if ch is None:
            return
        # Inverse of the driver's quantisation: 0 -> -1, 0x2000 -> 0, 0x3FFF -> +1.
        values = [(c / DAC_FULL_SCALE) * 2.0 - 1.0 for c in codes]
        if mode == "CON" and ch.arb_data:
            ch.arb_data.extend(values)
        else:
            ch.arb_data = values
        self._last_arb_channel = index

        # Uploading DAC16 VOLATILE,END auto-switches the instrument into an
        # arbitrary mode -- USER on firmware >= 00.02.x, SEQUENCE on <= 00.01.x.
        # The driver DEPENDS on this (waveform.py apply_arbitrary reads the
        # function back and picks :FREQuency for USER vs :FUNCtion:SEQuence:SRATe
        # for SEQUENCE), and it deliberately does NOT send :FUNCtion USER itself
        # because that resets the buffer to the built-in SINC on some firmware.
        # Without this line the sim leaves the channel reporting SIN, the driver
        # falls through to its "Unexpected arb mode" branch on every upload, and
        # a test suite that only ever ran against the sim would never exercise
        # the USER path the real 00.02.x instrument takes. *IDN? here advertises
        # 00.02.05, so USER is the self-consistent choice.
        ch.function = "USER"

        # The hardware rejects a single-packet DAC16 outside 8..8192 points; the
        # driver gates on this too, but a tool that bypasses it should still see
        # the refusal here rather than on the bench.
        if not (MIN_ARB_POINTS <= len(ch.arb_data) <= MAX_ARB_POINTS):
            self._error(-222,
                        f"Data out of range; {len(ch.arb_data)} points outside "
                        f"{MIN_ARB_POINTS}..{MAX_ARB_POINTS}")

    def _dispatch(self, command: str) -> Optional[str]:
        text = command.strip()
        if not text:
            return None

        header, _, params_text = text.partition(" ")
        is_query = header.endswith("?")
        if is_query:
            header = header[:-1]
        args = [a for a in params_text.split(",")] if params_text.strip() else []

        if header.startswith("*"):
            return self._common(header.upper(), is_query, command)

        parts = [_canon(t) for t in header.lstrip(":").split(":")]
        root, index = _split_channel(parts[0])
        tail = parts[1:]

        if root == "SOUR":
            return self._source(index, tail, args, is_query, command)
        if root == "OUTP":
            return self._output(index, tail, args, is_query, command)
        if root == "MMEM":
            return self._mmemory(tail, args, is_query, command)
        if root == "SYST":
            return self._system(tail, is_query, command)

        self._error(-113, f"Undefined header; {command.strip()}")
        return "" if is_query else None

    def _common(self, header: str, is_query: bool, command: str) -> Optional[str]:
        if header == "*IDN":
            return SIM_IDN
        if header == "*OPC":
            # Every command here completes synchronously, so OPC is always true.
            return "1" if is_query else None
        if header == "*RST":
            self.channels = {1: _Channel(), 2: _Channel()}
            self._errors.clear()
            return None
        if header == "*CLS":
            self._errors.clear()
            return None
        self._error(-113, f"Undefined header; {command.strip()}")
        return "" if is_query else None

    def _system(self, tail: List[str], is_query: bool, command: str) -> Optional[str]:
        if tail == ["ERR"] and is_query:
            if self._errors:
                code, message = self._errors.pop(0)
                return f'{code},"{message}"'
            return '0,"No error"'
        if tail == ["VERS"] and is_query:
            return SIM_VERSION
        if tail[:2] == ["BEEP", "IMM"]:
            return None
        self._error(-113, f"Undefined header; {command.strip()}")
        return "" if is_query else None

    def _apply(self, ch: _Channel, shape: str, args: List[str]) -> None:
        """APPLy sets shape and up to four parameters in one command."""
        # NOISe and DC pass DEFault placeholders in the leading positions, which
        # _num() folds to the current value.
        defaults = [ch.frequency, ch.amplitude, ch.offset, ch.phase]
        values = list(defaults)
        for i, arg in enumerate(args[:4]):
            parsed = _num(arg, defaults[i])
            if parsed is None:
                self._error(-104, f"Data type error; {arg.strip()!r}")
                return
            values[i] = parsed
        ch.function = shape
        ch.frequency, ch.amplitude, ch.offset, ch.phase = values
        if shape == "SQU":
            ch.square_duty = 50.0
        elif shape == "RAMP":
            ch.ramp_symmetry = 50.0

    def _source(self, index: int, tail: List[str], args: List[str],
                is_query: bool, command: str) -> Optional[str]:
        ch = self._channel(index)
        if ch is None:
            return "" if is_query else None

        def arg(i: int = 0, default: float = 0.0) -> Optional[float]:
            if i >= len(args):
                self._error(-109, f"Missing parameter; {command.strip()}")
                return None
            value = _num(args[i], default)
            if value is None:
                self._error(-104, f"Data type error; {args[i].strip()!r}")
            return value

        key = tuple(tail)

        if key[:1] == ("APPL",):
            if is_query:
                return (f"{ch.function},{_nr3(ch.frequency)},{_nr3(ch.amplitude)},"
                        f"{_nr3(ch.offset)},{_nr3(ch.phase)}")
            if len(key) == 2:
                self._apply(ch, key[1], args)
                return None

        elif key == ("FUNC",):
            if is_query:
                return ch.function
            if args:
                ch.function = _canon(args[0])
                return None
            self._error(-109, f"Missing parameter; {command.strip()}")
            return None

        elif key == ("FUNC", "ARB"):
            if is_query:
                return ch.arb_name
            ch.arb_name = args[0].strip() if args else ch.arb_name
            return None

        elif key == ("FUNC", "SEQ", "SRAT"):
            if is_query:
                return _nr3(ch.sequence_srate)
            v = arg(0, ch.sequence_srate)
            if v is not None:
                ch.sequence_srate = v
            return None

        elif key == ("FUNC", "SQU", "DCYC"):
            if is_query:
                return _nr3(ch.square_duty)
            v = arg(0, ch.square_duty)
            if v is not None:
                ch.square_duty = v
            return None

        elif key == ("FUNC", "PULS", "DCYC"):
            if is_query:
                return _nr3(ch.pulse_duty)
            v = arg(0, ch.pulse_duty)
            if v is not None:
                ch.pulse_duty = v
            return None

        elif key == ("FUNC", "PULS", "WIDT"):
            if is_query:
                return _nr3(ch.pulse_width)
            v = arg(0, ch.pulse_width)
            if v is not None:
                ch.pulse_width = v
            return None

        elif key == ("FUNC", "PULS", "TRAN", "LEAD"):
            if is_query:
                return _nr3(ch.pulse_lead)
            v = arg(0, ch.pulse_lead)
            if v is not None:
                ch.pulse_lead = v
            return None

        elif key == ("FUNC", "PULS", "TRAN", "TRA"):
            if is_query:
                return _nr3(ch.pulse_trail)
            v = arg(0, ch.pulse_trail)
            if v is not None:
                ch.pulse_trail = v
            return None

        elif key == ("FUNC", "RAMP", "SYMM"):
            if is_query:
                return _nr3(ch.ramp_symmetry)
            v = arg(0, ch.ramp_symmetry)
            if v is not None:
                ch.ramp_symmetry = v
            return None

        elif key == ("FREQ",):
            if is_query:
                return _nr3(ch.frequency)
            v = arg(0, ch.frequency)
            if v is not None:
                ch.frequency = v
            return None

        elif key == ("VOLT",):
            if is_query:
                return _nr3(ch.amplitude)
            v = arg(0, ch.amplitude)
            if v is not None:
                ch.amplitude = v
            return None

        elif key == ("VOLT", "OFFS"):
            if is_query:
                return _nr3(ch.offset)
            v = arg(0, ch.offset)
            if v is not None:
                ch.offset = v
            return None

        elif key in (("VOLT", "HIGH"), ("VOLT", "LOW")):
            # High/low levels are the same degree of freedom as amplitude and
            # offset; keep the pair consistent so a read-back agrees with a write.
            high = ch.offset + ch.amplitude / 2.0
            low = ch.offset - ch.amplitude / 2.0
            if is_query:
                return _nr3(high if key[1] == "HIGH" else low)
            v = arg(0, high if key[1] == "HIGH" else low)
            if v is None:
                return None
            if key[1] == "HIGH":
                high = v
            else:
                low = v
            ch.amplitude = abs(high - low)
            ch.offset = (high + low) / 2.0
            return None

        elif key == ("PHAS",):
            if is_query:
                return _nr3(ch.phase)
            v = arg(0, ch.phase)
            if v is not None:
                ch.phase = v
            return None

        elif key == ("PHAS", "SYNC"):
            self.channels[2].phase = self.channels[1].phase
            return None

        elif key == ("DATA", "CAT"):
            if is_query:
                return '"VOLATILE"' if ch.arb_data else '""'

        elif key == ("DATA", "DEL"):
            ch.arb_data = []
            return None

        elif key == ("TRAC", "DATA", "DAC16"):
            # The driver only ever sends this through write_raw; arriving here
            # means someone built the frame as text and lost the binary block.
            self._error(-161, "Invalid block data; DAC16 requires a binary block")
            return None

        self._error(-113, f"Undefined header; {command.strip()}")
        return "" if is_query else None

    def _output(self, index: int, tail: List[str], args: List[str],
                is_query: bool, command: str) -> Optional[str]:
        ch = self._channel(index)
        if ch is None:
            return "" if is_query else None
        key = tuple(tail)
        first = args[0] if args else ""

        if key in ((), ("STAT",)):
            # get_state accepts "1" or "ON"; get_sync_state below accepts only
            # "1". Each reply is given in the vocabulary its getter parses, so
            # every state written reads back.
            if is_query:
                return "ON" if ch.output else "OFF"
            state = _is_on(first)
            if state is None:
                self._error(-104, f"Data type error; {first.strip()!r}")
            else:
                ch.output = state
            return None

        if key == ("LOAD",):
            if is_query:
                return _nr3(ch.impedance)
            v = _num(first, ch.impedance)
            if v is None:
                self._error(-104, f"Data type error; {first.strip()!r}")
            else:
                ch.impedance = v
            return None

        if key == ("POL",):
            if is_query:
                return ch.polarity
            token = _canon(first)
            if token in ("NORM", "INV"):
                ch.polarity = token
            else:
                self._error(-224, f"Illegal parameter value; {first.strip()!r}")
            return None

        if key == ("SYNC",):
            if is_query:
                # ON/OFF, not 1/0. The programming guide's Return Format for
                # :OUTPut[<n>]:SYNC[:STATe]? reads "The query returns ON or
                # OFF", same as :OUTPut[<n>][:STATe]?. This used to answer
                # "1"/"0" to match a driver that compared `response == "1"` --
                # which meant the sim was modelling the bug instead of the
                # instrument, and get_sync_state() returned False for every
                # enabled sync on real hardware while the sim went green.
                # The driver now accepts both forms; the sim answers what the
                # DG822 answers.
                return "ON" if ch.sync else "OFF"
            state = _is_on(first)
            if state is None:
                self._error(-104, f"Data type error; {first.strip()!r}")
            else:
                ch.sync = state
            return None

        if key == ("SYNC", "MODE"):
            if is_query:
                return ch.sync_mode
            token = _canon(first)
            if token in ("NORM", "CARR", "MARK"):
                ch.sync_mode = token
            else:
                self._error(-224, f"Illegal parameter value; {first.strip()!r}")
            return None

        if key == ("SYNC", "POL"):
            if is_query:
                return ch.sync_polarity
            token = _canon(first)
            if token in ("POS", "NEG"):
                ch.sync_polarity = token
            else:
                self._error(-224, f"Illegal parameter value; {first.strip()!r}")
            return None

        if key == ("TRIG",):
            if is_query:
                return "1" if ch.trigger_out else "0"
            state = _is_on(first)
            if state is None:
                self._error(-104, f"Data type error; {first.strip()!r}")
            else:
                ch.trigger_out = state
            return None

        if key == ("TRIG", "SLOP"):
            if is_query:
                return ch.trigger_slope
            token = _canon(first)
            if token in ("POS", "NEG"):
                ch.trigger_slope = token
            else:
                self._error(-224, f"Illegal parameter value; {first.strip()!r}")
            return None

        if key == ("IDLE",):
            if is_query:
                return ch.idle
            ch.idle = first.strip().upper() or ch.idle
            return None

        self._error(-113, f"Undefined header; {command.strip()}")
        return "" if is_query else None

    def _mmemory(self, tail: List[str], args: List[str],
                 is_query: bool, command: str) -> Optional[str]:
        key = tuple(tail)
        name = args[0].strip().strip('"') if args else ""

        if key == ("CDIR",):
            if is_query:
                return f'"{self._cwd}"'
            self._cwd = name or self._cwd
            return None

        if key == ("STOR", "DATA"):
            source = self.channels[self._last_arb_channel].arb_data
            if not source:
                self._error(-256, f"File name not found; no arb data to store as {name}")
                return None
            self._files[self._cwd + name] = list(source)
            return None

        if key == ("LOAD", "DATA"):
            path = self._cwd + name
            if path not in self._files:
                self._error(-256, f"File name not found; {path}")
                return None
            ch = self.channels[self._last_arb_channel]
            ch.arb_data = list(self._files[path])
            ch.function = "USER"
            return None

        if key == ("CAT", "DATA", "ARB") and is_query:
            here = [p[len(self._cwd):] for p in sorted(self._files)
                    if p.startswith(self._cwd)]
            return ",".join(f'"{n}"' for n in here)

        self._error(-113, f"Undefined header; {command.strip()}")
        return "" if is_query else None


# Sessions are cached per resource name so instrument state survives a
# disconnect/reconnect the way hardware does -- otherwise every reconnect from
# the panel would look like a factory reset.
_SESSIONS: Dict[str, SimulatedDG822] = {}


class SimulatedResourceManager:
    """Stands in for pyvisa.ResourceManager when the sim backend is selected."""

    # Only ever f-string-interpolated by the connection layer's backend banner.
    visalib = "rigol_dg822.sim (simulated, no VISA implementation needed)"

    def list_resources(self, query: str = "?*::INSTR") -> Tuple[str, ...]:
        # VISA globs are close enough to fnmatch for the two patterns the driver
        # uses ("?*::INSTR" matches, "USB?*::INSTR" does not).
        return (SIM_RESOURCE,) if fnmatch.fnmatch(SIM_RESOURCE, query) else ()

    def open_resource(self, resource_name: str, **kwargs) -> SimulatedDG822:
        if resource_name != SIM_RESOURCE:
            raise ValueError(
                f"Simulated backend has no resource {resource_name!r} "
                f"(it serves {SIM_RESOURCE} only)")
        session = _SESSIONS.get(resource_name)
        if session is None:
            session = SimulatedDG822(resource_name)
            _SESSIONS[resource_name] = session
        session._closed = False
        return session

    def close(self) -> None:
        return None


def reset_simulated_instrument() -> None:
    """Drop the cached session so the next connect() gets a factory-fresh sim.

    Tests that need a known starting state call this; nothing in the driver does.
    """
    _SESSIONS.clear()
