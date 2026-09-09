# xsphere-rigol-dg822 — Development Session Log

Running, chronological record of development for **this repo only**
(`xsphere-rigol-dg822`). This repo is a git submodule of `xsphere-daq`; changes to the
parent's panel, shell or launcher are logged in *that repo's* `docs/session-log.md` —
write to the log of the repo you're modifying.

Scope of this log: the `rigol_dg822` driver package, the simulated instrument, the three
front ends (tkinter GUI, CLI, web page), the bench scripts in `tools/`, and this repo's
docs.

Newest entries first. Keep entries short and factual; convert relative dates to absolute.
See the [README](../README.md) for the operating manual and [DESIGN.md](DESIGN.md) for why
the code is shaped the way it is.

---

## 2026-09-09 — Adversarial review: six critical defects, and what the simulator was hiding

**Context.** The three front ends landed (entry below) with everything "verified" against
`rigol_dg822.sim`, because this machine has no VISA implementation. That is a real limit,
not a formality: the simulator is the only oracle this code has ever been checked against,
so a simulator that models the *driver's assumptions* rather than the *instrument* produces
a green test suite that means nothing. This session put the integration through a
multi-agent review — six finders over validation, sim fidelity, output safety, CLI/GUI
parity, the page, and repo hygiene, every finding then adversarially refuted through two
independent lenses. 42 findings survived: 6 critical, 14 high, 18 medium, 4 low. All six
criticals are fixed here, along with three defects found by running the code rather than
reading it.

**The one that mattered most: the simulator was modelling a bug.**
`:OUTPut[<n>]:SYNC[:STATe]?` — the programming guide's Return Format is unambiguous ("The
query returns ON or OFF", with an example returning `ON`). `output.py` parsed it as
`response == "1"`, so **`get_sync_state()` returns False for every enabled sync on real
hardware** — the page would show sync off while the rear-panel connector was driving. The
simulator answered `"1"`/`"0"` *to match the broken parser*, and the previous session's log
recorded that inversion as "a quirk the sim has to honour". It was not a quirk; it was the
bug, cemented and then documented. The driver now accepts both forms (as `get_state` always
did for `:OUTPut:STATe?`), and the sim answers what the instrument answers.

**Three more defects the simulator was concealing**, all found by *running* the CLI and the
page rather than reading them:

- **DAC16 upload never switched the channel into arbitrary mode.** `apply_arbitrary`
  branches on USER (fw >= 00.02.x) vs SEQUENCE (fw <= 00.01.x) to choose `:FREQuency` vs
  `:FUNCtion:SEQuence:SRATe`, and deliberately never sends `:FUNCtion USER` because that
  resets the buffer on some firmware. The sim stored the samples and left `function` at
  `SIN`, so every upload fell through to the "Unexpected arb mode" fallback and **the
  USER-mode branch — the path a real 00.02.05 instrument takes — had never once executed.**
  The sim advertises `SIM 00.02.05` in `*IDN?`, so it now switches to USER, as that
  firmware does.
- **The page reported a sample rate wrong by the point count, downwards.** `upload()`
  computes `frequency x points` correctly; the 0.5 s state poll then overwrote it by
  querying `:FUNCtion:SEQuence:SRATe?`, which is meaningful only in SEQUENCE mode and
  returns the stale 2000 default in USER mode. A 4096-point buffer at 2 kHz displayed as
  **2 kSa/s instead of 8.192 MSa/s**. Only visible once the sim reported USER at all.
- **The CLI warned on the correct answer.** Its post-upload check demanded SEQUENCE and
  warned on USER — i.e. warned whenever the firmware this driver targets behaved properly.
  It now accepts either and warns only when the channel switched to neither.

**The six critical findings.**

1. **An output could be left driving with nothing able to switch it off**
   (`webapp.py` `set_output`). `seconds`/`cycles` were checked for positivity but never for
   schedulability. `threading.Timer` silently dies past `_thread.TIMEOUT_MAX`
   (~4294967 s, about 49.7 days — the Windows DWORD-millisecond ceiling): `t.start()`
   returns normally, the endpoint has already sent `OUTPut ON`, and it returns 200 with a
   `run_mode: "timed"` and an `off_at` the page renders as a live countdown — for a shutoff
   that was never armed. Reachable by an ordinary units slip (the page offers an "hour"
   unit) or a few cycles at the guide's 1 uHz minimum. Now bounded by `MAX_RUN_SECONDS`
   (24 h) on both paths with a 422, and `_schedule_off` drops the output and re-raises if
   the timer cannot be armed, so the run never starts rather than starting unbounded.
2. **Amplitude and offset were never checked against each other**, so an over-rail
   combination went to the instrument. The DG822 constrains |offset| + Vpp/2 against the
   load (10 V High-Z, 5 V into 50 ohm) and, per the user guide, "would display a prompt
   message and set the offset to the offset upper limit of the new configuration
   automatically" — it substitutes its own value and never tells the host. See warnings,
   below.
3. **`connect()` orphaned a driving channel.** It cancelled every timed-output timer and
   dropped the VISA session without disabling a single output, then rebound to another
   instrument — after which the old one was not merely unowned but *unreachable*, and
   `stop()` would disable channels on the new box. It now releases through `disconnect()`,
   which already carries the right policy for exactly this case (kill a TIMED run, whose
   deadline nothing can honour; leave a continuous one, which is the operator's setup).
4. **`arb upload` silently played every non-comb shape at 1 kHz.** The sidecar carrying a
   generated waveform's design frequency was written only for combs, so the eight basic
   shapes lost it and the upload fell through to `DEFAULT_FREQUENCY_HZ` with no warning —
   a gaussian shaped for 5 kHz played at 1 kHz has a sigma five times too wide, reported as
   "1 kHz (default)" as though intended. The GUI never had this problem: it copies the
   design frequency into the channel and locks the field. The sidecar now records
   `output_frequency_hz` for every shape.
5. **The SIMULATED badge scrolled off screen** — every simulated-instrument cue lived in a
   `position:static` header on a page about 2.5x the height of its pane (measured: 1821 px
   of content in a 720 px viewport). For most of the scroll range nothing distinguished the
   simulator from a DG822 physically driving the experiment, in *either* direction. The
   header is now `position:sticky`, and `body.sim` additionally paints a `position:fixed`
   amber viewport frame — bound to the viewport, so it has no scroll range to fall out of,
   and independent of the header in case a future layout defeats it.
6. **Duty cycle and ramp symmetry were unvalidated** on `/set` and `/apply` (and amplitude
   on all three write paths). Folded into the warnings below.

**Warnings on the write path, not refusals.** The instrument clamps silently and the two
existing front ends warn rather than refuse — the CLI says so at its own limit block ("the
GUI does not enforce them either, and a bench user occasionally means it"). The web page had
neither: an out-of-range request returned 200 echoing the value back. `channel()` now derives
a `warnings` list on every read — frequency, amplitude, the amplitude+offset rail against the
current load, duty cycle, symmetry — and the page paints it in a per-channel box that is not
behind a dirty flag or a focus guard. Derived on read, not stored at write, so it stays true
when something else changes the picture: 18 Vpp is legal into High-Z and warns the moment the
load becomes 50 ohm. `warnings` is a new key in the channel wire contract.

**Regression tests.** `tools/test_safety.py` — 12 checks over the timer ceiling, the
`connect()` orphan, shutdown, the sync read-back, the arb mode switch and sample rate, and
the limit warnings. Every one of them was a real defect, so they are grouped by consequence
rather than by module: the DG822 keeps driving when the software believes it does not, or
the page shows a level the instrument is not emitting. Needs no VISA implementation.

**Verified after the fixes:** selftest 30/30 · `tools/test_safety.py` 12/12 · headless
import of `webapp`/`cli` pulls in neither tkinter nor matplotlib · shutdown with two outputs
driving and a live timer leaves both off and the timer cancelled · the standalone
`manage_lifecycle=True` lifespan connects and leaves outputs off · arb round trip through
the mounted page reports USER / 4096 points / 8.192 MSa/s · the SIMULATED badge is on screen
at the bottom of the scroll.

**Still not tested against hardware, and now that matters more, not less.** Four of the
defects above existed *because* the simulator was the only oracle, and one of them
(`:OUTPut:SYNC?`) had been written into this log as intended behaviour. The sim is closer to
the instrument than it was, but "the sim agrees" is not evidence — it is the same class of
claim that was wrong here. The next session on this repo should be a bench pass.

**Known issues — 33 confirmed findings not fixed here.** None critical. Recorded rather than
silently carried; each was confirmed by an adversarial pass, so these are defects, not
suspicions.

| sev | where | what |
|---|---|---|
| high | `rigol_dg822/cli.py:1409` | Trapezoid over-budget handling differs: the CLI shrinks the edges, the GUI preserves them |
| high | `rigol_dg822/cli.py:994` | `output on --all --cycles N` times both channels off CH1's frequency |
| high | `xsphere-rigol-dg822/rigol_dg822/static/rigol.js:1530` | Every control ships enabled and no "not connected" notice appears until the first successful /api/state — the page fails open |
| high | `xsphere-rigol-dg822/rigol_dg822/static/rigol.js:699` | c.adopt() clears the dirty flag on every field in the card, so any single successful write silently reverts the operator's unapplied edits |
| high | `rigol_dg822/webapp.py:778` | _timed_off marks the channel off before the write and discards disable()'s False return, so a failed automatic OFF is completely invisible |
| high | `rigol_dg822/webapp.py:523` | stop() discards disable()'s return value, so the one step that clears a physical hazard has no failure detection at all |
| high | `rigol_dg822/sim.py:281` | DAC16 binary block is passed through bytes.strip(), so uploads whose last sample is ~0.0 are silently truncated and rejected |
| high | `rigol_dg822/sim.py:650` | Sim silently accepts seven SCPI headers that do not exist on a DG800, defeating its stated purpose |
| high | `../requirements.txt:7` | Parent requirements.txt -r's a directory that is not in the parent repo (rigol is not a registered submodule), breaking the whole pip install including the cameras |
| high | `rigol_dg822/webapp.py:1280` | /api/arb/generate ignores the min/max its own shape catalogue advertises, letting a NaN sample reach the DAC16 upload |
| high | `rigol_dg822/webapp.py:1683` | /api/arb/upload accepts any frequency, amplitude and offset, and never checks the resulting sample rate against 2 kSa/s-30 MSa/s |
| medium | `rigol_dg822/cli.py:1281` | No CLI equivalent of the GUI's "Save CSV..." for a waveform that was loaded rather than generated |
| medium | `rigol_dg822/cli.py:1283` | Generated waveforms are written to the CWD but `arb files` and `arb delete --local` look in the waveforms directory |
| medium | `rigol_dg822/cli.py:1747` | The comb sidecar records the waveform name but the upload never reads it, so `--name` is lost between generate and upload |
| medium | `xsphere-rigol-dg822/rigol_dg822/static/rigol.js:1526` | Polling never pauses or stops: no visibilitychange/pagehide handler, and the shell keeps the /rigol iframe mounted when the pane is hidden |
| medium | `xsphere-rigol-dg822/rigol_dg822/static/rigol.js:431` | stateSeq is dead code: the documented in-flight-write guard is never read, so a late /api/state response repaints the card with pre-write values |
| medium | `xsphere-rigol-dg822/rigol_dg822/static/rigol.js:1190` | The comb frequency list silently discards every entry it cannot parse, generating a different waveform than the operator typed |
| medium | `rigol_dg822/webapp.py:892` | set_output cancels the timed-off timer before the OFF write is confirmed, converting a bounded run into an unbounded one when the write fails |
| medium | `rigol_dg822/webapp.py:718` | _read_channel clears off_at/run_mode without cancelling the armed timer, leaving a stale timer that later cuts a run the UI reports as continuous |
| medium | `rigol_dg822/sim.py:691` | MMEMory STORe/LOAD:DATA route through a sim-only _last_arb_channel; the instrument defaults to CH1 |
| medium | `rigol_dg822/sim.py:329` | The DAC16 range checks report an error but still commit the data, and the point ceiling is half the documented one |
| medium | `rigol_dg822/sim.py:559` | :PHASe:SYNChronize rewrites CH2's start-phase setting and ignores the channel index |
| medium | `rigol_dg822/sim.py:123` | _num() folds MINimum/MAXimum to the current value, so MIN/MAX parameters and '? MAXimum' queries are silent no-ops |
| medium | `rigol_dg822/sim.py:607` | :OUTPut:LOAD accepts any number and never rescales amplitude, so the sim's displayed drive level diverges from the instrument's |
| medium | `README.md:44` | README's "This installs:" list names two packages requirements.txt does not install and omits the two the panel needs |
| medium | `rigol_dg822/webapp.py:10` | Machine-local absolute paths survive in webapp.py's usage docstring and tools/README.md's run example |
| medium | `dg822_gui.py:951` | GUI's arb-CSV load dialog uses a bare relative "waveforms" initialdir while the save dialog resolves it from __file__ |
| medium | `README.md:319` | README Project Structure tree, dependency graph and module table document only the tkinter GUI, omitting both new front ends |
| medium | `rigol_dg822/webapp.py:1260` | /api/arb/generate silently clamps an out-of-range point count where the CLI returns an error, and emits no warning |
| low | `rigol_dg822/cli.py:1735` | `arb upload --freq` silently overrides a comb's fundamental, which the GUI deliberately locks |
| low | `xsphere-rigol-dg822/rigol_dg822/static/rigol.js:1383` | refreshFiles() swallows every non-OK response, leaving both file dropdowns as empty <select> elements with no explanation |
| low | `xsphere-rigol-dg822/rigol_dg822/static/rigol.js:1247` | A page reload loses the server-held arbitrary buffer: the arb card resets to blank while the channel it was uploaded to still holds it |
| low | `.gitignore:23` | .gitignore's keep-the-folder negations point at two files that do not exist, unlike the dock convention it cites |

**Next.** A hardware validation pass - the only thing that can settle whether the
sim's model of the instrument is right. Then the 11 high findings above, of which the
largest group is the page failing open (controls live before the first `/api/state`,
`adopt()` clearing unapplied edits, no visibility-based polling pause).

## 2026-09-08 — Three front ends over one controller; the repo joins xsphere-daq

**Context.** With the package importable headless and a simulated instrument behind it
(entry below), the driver could be exercised — but only from a desktop with tkinter. The
rig needs the DG822 from a run script and from the DAQ panel, and the panel is a web
surface on a server the operator is not sitting at. Same controller, two more front ends,
and the repo furniture to become a submodule.

- **CLI** (`rigol_dg822/cli.py`) — the scriptable surface: discover, connect, configure a
  channel, upload an arbitrary waveform, read state back, in one non-interactive
  invocation. It is a translation from argv to `DG822Controller` and back; no instrument
  logic lives in it. It inherits the never-raise policy as an operating requirement: an
  absent instrument, an absent VISA implementation or a SCPI timeout is a printed reason
  and a non-zero exit, never a traceback out of a run script.
- **Web page** (`rigol_dg822/webapp.py`, `rigol_dg822/static/`) — FastAPI over the same
  controller, following the dock's parent contract so the panel can mount it as a
  subsystem tab: `create_app(...)` with `manage_lifecycle=False` for the panel to own
  startup and shutdown, pages deriving their API base from `window.location` so the app
  works standalone and mounted, and the error convention 503 unavailable / 409 conflict /
  422 rejected.
- **The web layer owns the lock, because the driver deliberately has none.** A USB-TMC
  session is one conversation with no request ids: `query()` writes and reads whatever
  comes back next. FastAPI runs `def` handlers in a threadpool, so two browser tabs are two
  real threads, and unserialised they interleave a `:SOURce1:FREQuency?` with someone
  else's `:OUTPut1:STATe ON` and mis-parse the reply. A lock inside `rigol_dg822` would
  imply the driver can make an exclusive resource shareable; it cannot. One controller per
  instrument per process, and whoever embeds it serialises — same rule the dock applies
  with its per-session lock. Written up in [DESIGN.md](DESIGN.md) §3.
- **Repo furniture for submodule life**, matching `xsphere-camera-dock` and its own
  submodules: `.gitignore`, a rewritten `requirements.txt`, `docs/DESIGN.md`,
  `docs/session-log.md` (this file) and `tools/README.md`.
  - `requirements.txt` now covers the real set — numpy and scipy for the waveform maths,
    fastapi/uvicorn for the web page, matplotlib for the GUI preview — and is explicit
    that **pyvisa is the API, not the driver**: this machine has it installed and
    `ResourceManager()` still raises "Could not locate a VISA implementation". Hardware
    needs NI-VISA (not a pip package) or `pip install pyvisa-py pyusb`; the simulator needs
    neither, which is why the CLI and the web page could be built at all.
  - `.gitignore` treats `waveforms/` the way the dock treats `recordings/`: keep the
    folder, ignore what lands in it. The CSVs there are 80–170 KB numeric dumps the arb
    generator regenerates from a handful of parameters, half of them bench scratch
    (`TEST_GUI`, `TEST_RAF`), and a `.RAF` is one step further downstream — the 14-bit
    DAC16 image of a CSV in the instrument's internal-memory format. Neither is a source of
    truth.
  - **For the integrator:** seven `__pycache__/*.cpython-312.pyc` files are in `HEAD` from
    before there was a `.gitignore`. Their removal is already staged (they went with the
    flat modules), so the commit that lands this restructure drops them — they stay in
    history, which no ignore rule can change. The nine files in `waveforms/` are still
    tracked and would need `git rm --cached` if the owner agrees they are rig state; a
    `waveforms/.gitkeep` then keeps the folder, as `recordings/.gitkeep` does in the dock.

**Verified** (all through `SIM::DG822::INSTR`, no VISA implementation installed):
`DG822Controller` connect → `setup_sine(1, 2500 Hz, 1.0 V)` → `output_on(1)` round trip;
a 1024-point DAC16 upload read back out of the simulated channel with a max round-trip
error of **6.10e-05**, i.e. half a 14-bit LSB (one LSB = 1.22e-04); the virtual `.RAF`
store (`store_arb_file` → `list_arb_files`) with nothing written to the host disk;
`discover_devices()` on this box printing the real backend failure and degrading to the
simulator rather than raising; `tools/diagnose_waveforms.py` running end to end.

**Not tested against hardware.** The DG822 is not reachable from this machine, and no
document in this repo claims otherwise.

**Next.** Mount the web page in the parent panel as a subsystem tab and bump the submodule
pointer; then a hardware validation pass, which is the only thing that can confirm the
simulator's model of the instrument is right.

## 2026-09-08 — Flat modules become the `rigol_dg822` package, plus a simulated DG822

**Context.** This repo is becoming a git submodule of `xsphere-daq`. The parent puts the
submodule directory on `sys.path` (exactly as it does for `xsphere-camera-dock`), so flat
top-level names like `dg822_connection` would land in the parent's module namespace and
collide. Everything importable now lives under one package name.

**Moves** (all `git mv`, so history follows the files):

| Was | Now |
|---|---|
| `dg822_connection.py` | `rigol_dg822/connection.py` |
| `dg822_waveform.py` | `rigol_dg822/waveform.py` |
| `dg822_output.py` | `rigol_dg822/output.py` |
| `dg822_controller.py` | `rigol_dg822/controller.py` |
| `dg822_arbitrarywf.py` | `rigol_dg822/arbitrary.py` |
| `dg822_plot.py` | `rigol_dg822/plot.py` |
| `diagnose_*.py`, `test_*.py` | `tools/` |

`dg822_gui.py` stays at the top level and imports from the package: the package must remain
importable on a headless server, and the tkinter GUI is not. Cross-module imports inside
the package are now explicit relative imports. The two `tools/` scripts that imported the
driver had a hardcoded `sys.path.insert` pointing at a dead OneDrive path; that is now
derived from `__file__`.

- **Headless plot.** `plot.py` used to hard-import `tkinter` and
  `matplotlib.backends.backend_tkagg` at module level, so a web server could not even reach
  the pure maths. tkinter, the Tk canvas and pyplot are now imported inside the functions
  that need a display, `from __future__ import annotations` keeps the `tk.Widget` /
  `FigureCanvasTkAgg` annotations from being evaluated at `def` time, and `create_figure()`
  pins the Agg backend unless pyplot is already up (the GUI's own doing — leave its choice
  alone). Verified: importing `rigol_dg822.plot` does not even load matplotlib, and
  `create_figure()` does not load tkinter.
- **Simulated instrument.** New `rigol_dg822/sim.py`. There is no NI-VISA and no pyvisa-py
  on this machine, so `pyvisa.ResourceManager()` raises "Could not locate a VISA
  implementation" and nothing above the driver could be exercised at all. The sim presents
  the pyvisa resource interface the connection layer duck-types against (`write`, `query`,
  `write_raw`, `close`, `clear`, `timeout`, the two terminations), parses the real SCPI
  strings the driver sends — including the DAC16 binary block — and models both channels,
  the arbitrary buffers, the sequence sample rate and a virtual internal `.RAF` store.
  Unknown commands go on the error queue and come back from `:SYSTem:ERRor?` rather than
  being silently accepted, which makes the sim a way of catching a malformed SCPI string
  before it reaches the bench. `*IDN?` carries `SIMULATED-NO-HARDWARE` in the serial field
  so no log can be misread as a hardware run.
- **Two quirks the sim has to honour**, both from the driver study: `OUTPut:STATe?` must
  answer `ON`/`OFF` (its getter accepts both `"1"` and `"ON"`) while `OUTPut:SYNC?` must
  answer `1`/`0` (its getter accepts only `"1"`), and `OUTPut:LOAD?` must answer `9.9E+37`
  for High-Z because the getter maps anything above 1e30 to `inf`.
- **Injection point.** `DG822Connection._init_resource_manager` — the single site that used
  to be `self._rm = pyvisa.ResourceManager(backend)`. `list_resources`, `discover_devices`
  and `connect` all funnel through it and thereafter touch only `self._rm`, so one branch
  covers every path in the driver and the real path is otherwise untouched. `import pyvisa`
  is now guarded, because on this box it may not be importable at all.
- **Never-raise policy applied here too:** `_init_resource_manager` used to re-raise when
  both backends failed, which is how `discover_devices()` produced a `ValueError` on a box
  with no VISA. It now records the reason in `backend_error`, and `discover_devices()`
  degrades to "no devices found" plus the reason, always offering the simulator (listed
  last, so real hardware still wins `auto_connect()`).

**Verified.** Package import (`rigol_dg822`, `.plot`, `.arbitrary`, `.controller`), a sim
round trip through `DG822Controller` (connect, `setup_sine`, read frequency/amplitude/offset
back, `output_on`, confirm state), a 1024-point DAC16 upload round trip (max round-trip
error 6.1e-05, i.e. half a 14-bit LSB), the virtual `.RAF` store, the error queue, and
`py_compile` on `dg822_gui.py`, the package and `tools/`.

**Not tested against hardware.** The DG822 is not reachable from this machine.

**Known, pre-existing, not fixed here:** `DG822Controller.print_status()` prints a `Ω` and
raises `UnicodeEncodeError` on a cp1252 Windows console. It would do the same against
hardware. `tools/diagnose_waveforms.py` has the same problem with a `→`
(`set PYTHONIOENCODING=utf-8` is the workaround). Worth folding into the CLI phase, which
owns the output layer.

**Next:** `rigol_dg822/cli.py`, `rigol_dg822/webapp.py` and `rigol_dg822/static/` — the CLI
and the FastAPI control page, both exercised through the simulator.
