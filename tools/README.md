# tools/ — bench diagnostics and scratch tests

These are the scripts that were written while working out how the DG822 actually
behaves. They are kept because the answers they produced are the reason the
driver is shaped the way it is (see *Key SCPI Notes* in the top-level
[README](../README.md)), and because the next firmware surprise will be
diagnosed the same way.

They are **not** a test suite. There is no pytest, no assertions, no exit codes:
each one prints what the instrument said and you read it. Nothing in `tools/` is
imported by `rigol_dg822` or by `dg822_gui.py`, which is why they sit here rather
than in the package.

## Running them

The package moved from flat `dg822_*.py` modules into `rigol_dg822/`, and these
scripts moved down one level into `tools/`. The two that import the driver
(`diagnose_waveforms.py`, `test_e2e.py`) put
the repo root on `sys.path` themselves, derived from `__file__`, so the working
directory does not matter:

```
python "C:/Users/xbox/Desktop/xsphere-daq/xsphere-rigol-dg822/tools/diagnose_waveforms.py"
```

Several print arrows and Greek letters. On a stock Windows console that is a
`UnicodeEncodeError` mid-run (cp1252), not a bug in the instrument or the maths:

```
set PYTHONIOENCODING=utf-8
```

## What needs real hardware

Nine of the eleven talk to **raw pyvisa**, not to the driver, and open a
hardcoded resource string for the bench unit
(`USB0::0x1AB1::0x0643::DG8A252001971::0::INSTR`). They need a DG822 on USB *and*
a VISA implementation (NI-VISA, or `pip install pyvisa-py pyusb` — see
[requirements.txt](../requirements.txt)). This machine has neither, so they stop
at `pyvisa.ResourceManager()` with "Could not locate a VISA implementation", as a
plain traceback: the never-raise policy is a property of `rigol_dg822`, and these
scripts deliberately sit underneath it so that a failure is visible rather than
absorbed.

| Script | Needs | What it answers |
|---|---|---|
| `diagnose_hw.py` | hardware (takes a resource string as argv[1]) | Full identity/firmware/capability dump; written to compare two units when arb upload worked on one and not the other |
| `diagnose_upload.py` | hardware | Why a DAC16 upload does not move the instrument off `SIN` |
| `diagnose_upload2.py` | hardware | `*RST` then a 16384-point upload — does the mode change? |
| `diagnose_upload3.py` | hardware | Largest upload that survives, with no `*RST` between attempts |
| `diagnose_chunk.py` | hardware | Whether pyvisa's `chunk_size` is what breaks 16384 points |
| `test_chunked.py` | hardware | CON/END chunked upload of 16384 points |
| `test_chunk_theory.py` | hardware | Whether CON/END keeps only the END chunk (it does) |
| `test_freq_fix.py` | hardware | DAC16 upload plus a direct frequency write — the sequence the driver now uses |
| `test_user_mode.py` | hardware | `USER`-mode commands on newer firmware (they reset the waveform to SINC) |
| `diagnose_waveforms.py` | nothing | Pure numpy: dumps trapezoid and comb arrays and their DAC values to find wrap discontinuities. Runs anywhere |
| `test_e2e.py` | hardware, or the simulator | The GUI's upload flow through `DG822Controller` |

`test_e2e.py` is the one hardware script that can run without hardware: it goes
through the controller rather than raw pyvisa, so changing its `VISA` constant to
`SIM::DG822::INSTR` (`rigol_dg822.SIM_RESOURCE`) routes the whole flow into the
simulated instrument. That exercises the SCPI the driver emits, not the
instrument's response to it — see [../docs/DESIGN.md](../docs/DESIGN.md) for what
the simulator does and does not prove.
