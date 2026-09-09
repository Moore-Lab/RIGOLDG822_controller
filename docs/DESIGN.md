# DG822 signal generation — one controller, three front ends

*v1.0, 2026-09-08. Written when the flat `dg822_*.py` modules became the `rigol_dg822`
package and the repo became a git submodule of `xsphere-daq`. Grounded in the driver as it
stands plus the bench findings in the top-level [README](../README.md) — its
**Key SCPI Notes** section is the authority on what the instrument accepts, and
**Smooth Waveform Generation: Design & Constraints** on the point-budget maths. Neither is
repeated here.*

## 1. Layering

```
rigol_dg822/
  connection.py   resource discovery, USB-TMC session, SCPI write / query / write_raw,
                  IEEE-488.2 (*RST, *IDN?, *OPC?); routes to sim.py on SIM::DG822::INSTR
  waveform.py     :APPLy quick setup, per-parameter read/write, DAC16 binary upload,
                  sequence sample rate, .RAF save / load / list
  output.py       channel on/off, load impedance (1 Ω - 10 kΩ or High-Z), polarity,
                  sync output, trigger edge
  controller.py   the facade: owns one connection, lazily builds waveform + output on a
                  successful connect, adds setup_sine() / setup_pulse() / print_status()
  arbitrary.py    ArbitraryWaveform (normalised +-1 <-> 14-bit DAC) + WaveformGenerator
                  (shapes, frequency combs, Monte Carlo phase optimisation) + the
                  optimal-point calculators
  plot.py         preview arrays for every waveform type, axis auto-scaling, and the
                  matplotlib figure — headless-safe
  sim.py          a DG822 in this process, behind the pyvisa resource surface
dg822_gui.py      the tkinter desktop GUI, deliberately outside the package
```

The arrow points one way. `connection` knows nothing about waveforms; `waveform` and
`output` know nothing about each other; `controller` is the only module that knows all
three. `arbitrary` and `plot` are pure — no VISA, no instrument, no I/O — which is what
lets the arb generator and the preview run on a machine with nothing plugged in. `sim` is
stdlib-only and does not import pyvisa.

Consequences worth stating, because they are the reason for the shape:

- **The package must import on a headless server with no VISA and no matplotlib.** So
  `pyvisa` is a guarded import in `connection.py`; `plot.py` imports tkinter, the Tk canvas
  and pyplot inside the functions that need a display and pins the Agg backend in
  `create_figure()` when pyplot is not already up; and `__init__.py` re-exports the
  controller, the enums and the sim but **not** `arbitrary` or `plot` — a control path that
  only talks SCPI should not fail to import because matplotlib is missing.
- **The GUI is not in the package.** `dg822_gui.py` imports `rigol_dg822`, never the
  reverse. Putting it inside would make `import rigol_dg822` a tkinter dependency.
- **The package name is the submodule contract.** `xsphere-daq` puts this directory on
  `sys.path`, exactly as it does for `xsphere-camera-dock`. Flat modules named
  `dg822_connection` would land in the parent's global module namespace; one package name
  that nothing else in the rig uses is the whole point of the rename.

## 2. Three front ends, one controller

| Front end | Where | For |
|---|---|---|
| tkinter GUI | `dg822_gui.py` | The operator at the bench: live preview while typing, the arb generator dialog with point-budget warnings, presets |
| CLI | `rigol_dg822/cli.py` | Scripts and run procedures: set a channel, upload a comb, read state back, in one non-interactive invocation |
| Web page | `rigol_dg822/webapp.py` + `static/` | The rig from any machine — standalone, and mounted by the parent panel as a subsystem tab beside `/cameras` |

None of the three contains instrument logic. Each is a translation from its own input
vocabulary (widget events, argv, HTTP) into `DG822Controller` calls, and back out again.
A behaviour that belongs to the DG822 — the centred-pulse phase offset, the SINC-reset
traps, the sample-rate clamp — is fixed once, in the layer that owns it, and all three
inherit the fix. The test for whether something is in the right place: if a rule has to be
restated in a second front end to keep them agreeing, it is in the wrong layer.

The web layer follows the dock's parent contract (`camera_dock.webapp`): a
`create_app(...)` that takes `manage_lifecycle=False` so the panel owns startup and
shutdown, pages that derive their API base from `window.location` so they work standalone
and mounted, and an HTTP error convention — **503** instrument unavailable, **409** state
conflict, **422** parameter rejected. The panel mounts subsystems defensively; a DG822 that
is not there must produce a tab that explains itself, never a panel that will not boot.

## 3. One owner: a VISA resource is not shared

A USB-TMC session is a single conversation. There is no request id and no interleaving: a
`query()` writes and then reads whatever comes back next. Two threads inside one process
will read each other's replies; two processes cannot hold the instrument at all, since the
underlying VISA session is exclusive.

**There is no lock anywhere in `rigol_dg822`, and that is deliberate** — a lock in the
driver would imply the driver can make sharing safe, and it cannot. The rule is instead:

- One `DG822Controller` per instrument per process. The controller is the ownership token.
- **Whoever embeds the controller serialises access to it.** For the web app that means one
  lock around every handler that touches the controller, the way `camera_dock.webapp` uses
  a per-session lock: FastAPI runs `def` handlers in a threadpool, so two browser tabs are
  genuinely two threads, and the naive version interleaves a `:SOURce1:FREQuency?` with
  someone else's `:OUTPut1:STATe ON` and mis-parses the reply.
- The GUI on the bench workstation and the panel on the DAQ server are two owners. They
  cannot both be connected. This is the camera connect/disconnect situation exactly: the
  fix is to release the instrument, not to make it shareable.
- The one thread the driver does start is in `discover_devices()`: each candidate `*IDN?`
  runs in a daemon thread joined with a 2 s timeout, because a non-TMC device on the bus
  can block a query indefinitely and discovery must not hang the caller.

**Never-raise, everywhere below the front end.** A missing `pyvisa`, a VISA implementation
that is not installed, an absent instrument, a busy instrument or a SCPI timeout all
degrade to a marked unavailable state carrying the reason. `_init_resource_manager` records
`backend_error` instead of re-raising; `discover_devices()` reports "no devices found" plus
that reason and always offers the simulator, listed **last** so real hardware still wins
`auto_connect()`. The cost of getting this wrong is not an ugly traceback — it is the whole
panel, and therefore the cameras and the running recording, going down because a function
generator was unplugged.

## 4. The simulated instrument

`rigol_dg822/sim.py` is a DG822 that lives in this process, presenting the surface the
connection layer duck-types against (`write`, `query`, `write_raw`, `close`, `clear`,
`timeout`, the two terminations). It is selected by resource name — `SIM::DG822::INSTR`, or
`simulate=True` — so it enters through the one injection point,
`DG822Connection._init_resource_manager`, and every path above it is the real code.

It exists because this DAQ machine has **no VISA implementation at all**:
`pyvisa.ResourceManager()` raises "Could not locate a VISA implementation", so without the
sim nothing above the connection layer could be run even once.

It is a parser, not a stub. Commands are matched and folded into per-channel state —
including the DAC16 binary block, the sequence sample rate and a virtual internal `.RAF`
store — so state written is state read back, and an unrecognised command goes on the error
queue for `:SYSTem:ERRor?` rather than being silently swallowed.

**What a sim run proves:**

- The SCPI the driver emits is well-formed, correctly ordered and correctly framed — the
  binary block header included.
- The driver's readback parsing matches the response *formats* it will see, including the
  asymmetries that are easy to get wrong: `:OUTPut:STATe?` answers `ON`/`OFF` while
  `:OUTPut:SYNC?` answers `1`/`0`, and `:OUTPut:LOAD?` answers `9.9E+37` for High-Z, which
  the getter maps to `inf`.
- The state machine above the wire: connect, configure, upload, read back, output on, and
  the never-raise degradations.
- Front-end wiring end to end. The CLI and the web page are developed and demonstrated
  against it.

**What it does not prove, and must never be quoted as proving:**

- Anything analogue. There is no output, no amplitude accuracy, no timing, no jitter.
- Anything about *this firmware's* acceptance of a command. The sim was built from the
  driver's model of the instrument, so it can only find disagreements with that model — it
  cannot discover that the model itself is wrong. The bench findings in *Key SCPI Notes*
  came from hardware and could not have come from here.
- Transport reality: USB-TMC chunk sizes, the largest upload that survives, `*OPC?` timing,
  timeouts, or a device that stops answering mid-sequence.

`*IDN?` returns `SIMULATED-NO-HARDWARE` in the serial field for exactly this reason: no log
of a simulated run can be misread later as a hardware run.

## 5. Instrument quirks

The behaviours that constrain the driver — the DAC16 upload form, the `:APPLy:USER` /
`:APPLy:ARBitrary` / `:FUNCtion USER` commands that silently reset the waveform to the
built-in SINC, the 2 kSa/s–30 MSa/s sequence sample rate, the 7-character `.RAF` name limit,
and the fact that ASCII `:DATA VOLATILE,{csv}` is rejected outright — are documented once,
in **Key SCPI Notes** in the [README](../README.md). Read that before changing
`waveform.py`. They are firmware-version findings from a specific unit (DG822 non-Pro,
00.01.08.00.01), not general RIGOL behaviour, and the sim encodes the driver's belief about
them rather than independent evidence.

## 6. Graceful failure rules

| Condition | Behaviour |
|---|---|
| `pyvisa` not importable | Recorded as `backend_error`; sim still available; import of the package unaffected |
| No VISA implementation installed | `discover_devices()` returns no hardware plus the reason, and offers the simulator |
| Instrument absent, busy or unplugged | `connect()` returns False with a printed reason; controller stays unconnected |
| A device on the bus that will not answer `*IDN?` | Skipped after a 2 s threaded timeout; discovery continues |
| SCPI timeout mid-session | Degrades to an unavailable state; never propagates out of the driver |
| Parameter out of hardware range | Clamped by the layer that owns the limit (e.g. sample rate to 2 kSa/s–30 MSa/s) |
| Front end asks for a display that is not there | `plot.py` pure helpers work with matplotlib absent; `create_figure()` falls back to Agg |
| Two owners want the instrument | Not resolvable in software — one must disconnect |

## 7. Definition of done

1. `import rigol_dg822` succeeds on a box with no VISA, no instrument and no matplotlib.
2. Every front end is demonstrable end to end against `SIM::DG822::INSTR`, with no VISA
   implementation installed.
3. A DAC16 upload round-trips through the sim to within one 14-bit LSB.
4. Unplugging the instrument (or having never had one) costs the DG822 tab and nothing
   else: the panel boots, the cameras stream, the CLI exits with a reason.
5. Hardware validation is a separate, explicitly labelled event. Until it happens, no
   document in this repo claims a hardware run.
