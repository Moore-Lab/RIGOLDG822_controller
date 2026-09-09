# RIGOL DG822 Waveform Generator Controller

A modular Python application for controlling the **RIGOL DG822** dual-channel arbitrary waveform generator over USB. Includes a full tkinter GUI with live waveform preview, arbitrary waveform generation (including frequency combs with Monte Carlo phase optimisation), and persistent storage to the instrument's internal memory.

> **Hardware tested:** RIGOL DG822 (non-Pro), firmware 00.01.08.00.01  
> **Communication:** USB-TMC via PyVISA / NI-VISA

---

## Features

- **Dual-channel control** — independent waveform type, frequency, amplitude, offset, and phase for CH1 and CH2
- **Supported waveforms** — Sine, Square, Pulse, Ramp, Noise, DC, and Arbitrary
- **Arbitrary waveform engine** — generate, upload, save, and load custom waveforms:
  - Basic shapes (square, sine, ramp, pulse, sinc, exponential, Gaussian) with auto-optimal point count
  - **Frequency comb** generator — sum of sinusoids with random-phase Monte Carlo optimisation for maximum RMS
  - Auto-calculates the smoothest waveform (most points) within hardware limits (8–16,384 points, 2 kSa/s – 30 MSa/s)
  - Warnings when frequency span is too wide for available point budget
  - Save/load `.RAF` files to the instrument's internal memory and CSV files locally
- **Live preview** — embedded matplotlib plot updates as you type, with auto-scaled time/voltage axes
- **Frequency expressions** — enter `1/0.1` to get 10 Hz, or any simple math
- **Pulse width control** — set pulse width in ns/µs/ms/s with real-time duty cycle and period display
- **Centered pulses** — pulses are centered in the period via automatic phase offset
- **Run modes** — Continuous, N Cycles, or timed Duration
- **Quick presets** — one-click setup for common configurations (1 kHz Sine, DC 3.3 V, etc.)
- **Load impedance** — toggle between High-Z and 50 Ω per channel

---

## Installation

### Prerequisites

- **Python 3.10+** (tested with 3.12)
- **NI-VISA** runtime (recommended) — download from [ni.com/visa](https://www.ni.com/en/support/downloads/drivers/download.ni-visa.html). Alternatively, the pure-Python `pyvisa-py` backend works for basic USB communication.
- **USB driver** — the RIGOL DG822 should appear as a USB-TMC device when connected. On Windows, NI-VISA typically handles this automatically.

### Install dependencies

```bash
pip install -r requirements.txt
```

This installs:
- `pyvisa` — VISA communication library
- `pyvisa-py` — pure-Python VISA backend (fallback)
- `pyusb` — USB device support

`tkinter`, `numpy`, `matplotlib`, and `scipy` are also required but are typically bundled with standard Python / Anaconda distributions.

---

## Quick Start

### Launch the GUI

```bash
python dg822_gui.py
```

1. **Connect** — click *Scan* to find your instrument, or switch to *Manual VISA address* and enter the resource string (e.g. `USB0::0x1AB1::0x0643::DG8A...::INSTR`). Click *Connect*.
2. **Configure** — select a waveform type, set frequency/amplitude/offset/phase, then click *Apply Settings*.
3. **Toggle output** — use the *Output* checkbox on each channel tab.

### Scripting (no GUI)

Each module can be used independently:

```python
from rigol_dg822 import DG822Controller

with DG822Controller() as gen:
    gen.connect("USB0::0x1AB1::0x0643::DG8A204201757::0::INSTR")

    # 1 kHz sine, 2 Vpp on CH1
    gen.setup_sine(channel=1, frequency=1000, amplitude=2.0)
    gen.output_on(1)

    # 5 kHz square, 3.3 Vpp, 1.65 V offset on CH2
    gen.setup_square(channel=2, frequency=5000, amplitude=3.3, offset=1.65, duty_cycle=50)
    gen.output_on(2)
```

### No instrument? Use the simulator

`rigol_dg822.sim` is a DG822 that lives in the process. It presents the same
interface a pyvisa resource presents, so it drops into the connection layer and
needs **no VISA implementation installed** — reach it by resource name:

```python
from rigol_dg822 import DG822Controller, SIM_RESOURCE   # "SIM::DG822::INSTR"

dg = DG822Controller(SIM_RESOURCE)      # or DG822Controller(simulate=True)
dg.connect()
dg.setup_sine(1, frequency=2500.0, amplitude=1.5)
dg.output_on(1)
print(dg.get_frequency(1))              # 2500.0 — state written is state read back
```

It parses the real SCPI strings the driver sends, including the DAC16 binary
block, and models both channels, the arbitrary buffers, the sequence sample rate
and a virtual internal `.RAF` file store. Commands it does not recognise go onto
the error queue and come back from `:SYSTem:ERRor?`, so a malformed command is
caught here rather than on the bench.

`*IDN?` answers `Rigol Technologies,DG822,SIMULATED-NO-HARDWARE,SIM 00.02.05` —
a simulated run can never be mistaken for hardware in a log. `discover_devices()`
always lists the simulator, marked that way, after any real instruments.

Nothing in the driver raises. With no VISA implementation installed,
`discover_devices()` reports "no devices found" plus the reason and offers the
simulator instead of throwing `Could not locate a VISA implementation`.

---

## Arbitrary Waveforms

### Generating in the GUI

1. Select **Arbitrary** from the waveform type.
2. Click **Generate…** to open the generator dialog.
3. Choose a shape (or *frequency_comb*) and set parameters.
4. Points are **auto-calculated** for maximum smoothness — you don't need to specify them.
5. Click **Generate**, then **Upload** to send to the instrument.

### Internal memory (.RAF files)

Uploaded waveforms are automatically saved as `.RAF` files on the instrument's internal storage (`C:\` Arb File directory). Filenames are limited to 7 characters. These persist across power cycles.

---

## Smooth Waveform Generation: Design & Constraints

This section documents the general framework the software uses to produce the smoothest possible arbitrary waveform output within the DG822's hardware limits. The principles apply to **all** arbitrary waveform types — not just frequency combs — and should be followed when adding new waveform generators.

### The hardware playback model

The DG822 stores one period of the waveform as a buffer of discrete samples and replays it in a loop at a fixed sample rate:

$$f_{\text{out}} = \frac{f_s}{N}$$

where $f_s$ is the sample rate and $N$ is the number of points in the buffer. Rearranging:

$$f_s = f_{\text{out}} \times N$$

The hardware imposes three hard constraints:

| Constraint | Symbol | Value |
|---|---|---|
| Minimum buffer length | $N_{\min}$ | 8 points |
| Maximum buffer length | $N_{\max}$ | 16,384 points |
| Minimum sample rate | $f_{s,\min}$ | 2 kSa/s |
| Maximum sample rate | $f_{s,\max}$ | 30 MSa/s |
| Vertical resolution | — | 14 bits (0x0000–0x3FFF unsigned) |

All three constraints act simultaneously. For a given output frequency $f_{\text{out}}$, the achievable number of points is:

$$N = \min\!\left(N_{\max},\;\left\lfloor \frac{f_{s,\max}}{f_{\text{out}}} \right\rfloor\right)$$

and the resulting sample rate is $f_s = f_{\text{out}} \times N$, which must also satisfy $f_s \geq f_{s,\min}$.

### The smoothness goal

More points = smoother output. A waveform rendered with 16,384 points will look nearly analog; the same shape with 30 points will look like a staircase. The software's job is to **always maximise $N$** within the constraints, so the user only specifies what they care about (frequency, shape, parameters) and the backend decides how many points to use.

### Single-frequency waveforms

For waveforms defined by a single output frequency (square, pulse, ramp, sine, gaussian, etc.), the calculation is straightforward:

| Output frequency | Optimal $N$ | Sample rate | Quality |
|---|---|---|---|
| 0.1 Hz | 16,384 | 1.6 kSa/s | Maximum (but below min $f_s$ — **warning**) |
| 1 Hz | 16,384 | 16.4 kSa/s | Maximum |
| 100 Hz | 16,384 | 1.64 MSa/s | Maximum |
| 1 kHz | 16,384 | 16.4 MSa/s | Maximum |
| 10 kHz | 3,000 | 30 MSa/s | Good (sample-rate limited) |
| 100 kHz | 300 | 30 MSa/s | Acceptable |
| 1 MHz | 30 | 30 MSa/s | Coarse — only 30 steps per period |
| 3.75 MHz | 8 | 30 MSa/s | Minimum allowed — essentially 8 steps |
| > 3.75 MHz | — | — | **Not achievable** ($N < 8$) |

**Key insight:** below ~1.83 kHz the buffer is always 16,384 points (maximum). Above that, points decrease as $30 \times 10^6 / f_{\text{out}}$. The crossover is:

$$f_{\text{crossover}} = \frac{f_{s,\max}}{N_{\max}} = \frac{30\,\text{MSa/s}}{16{,}384} \approx 1{,}831\;\text{Hz}$$

Below this crossover the waveform is always at maximum resolution. Above it, you're trading resolution for frequency.

### Multi-frequency waveforms (the hard case)

When a waveform contains multiple frequency components — such as a frequency comb, or any future waveform defined as a sum/product of different-frequency terms — the point budget problem becomes more nuanced.

#### The waveform period

The DG822 replays the buffer as a single repeating period. For the waveform to tile seamlessly, the buffer must contain **exactly one period of the fundamental**. For a sum of sinusoids at frequencies $f_1, f_2, \ldots, f_k$, the fundamental is their greatest common divisor:

$$f_0 = \gcd(f_1, f_2, \ldots, f_k)$$

The output frequency is $f_0$, and the buffer represents the time interval $[0,\; 1/f_0)$.

> **Example:** A comb with tones at 100, 200, 300, …, 1000 Hz has $f_0 = 100$ Hz. The buffer holds one period of 10 ms.

#### Cycles of each component within the buffer

Within that one buffer period, the $i$-th component completes $f_i / f_0$ full cycles. The highest component $f_{\max}$ completes the most cycles and therefore needs the most points to be rendered smoothly.

$$\text{cycles of } f_{\max} \text{ per buffer} = \frac{f_{\max}}{f_0} = h_{\max}$$

If we require at least $P$ points per cycle for smooth rendering (the software uses $P = 10$), the minimum buffer length for the highest harmonic is:

$$N_{\min,\text{smooth}} = h_{\max} \times P = \frac{f_{\max}}{f_0} \times P$$

This is the **minimum points needed** value shown in the GUI's info display.

#### The three regimes

Depending on the relationship between $N_{\min,\text{smooth}}$, $N_{\max}$, and the sample-rate ceiling $f_{s,\max} / f_0$, the waveform falls into one of three regimes:

| Regime | Condition | Outcome |
|---|---|---|
| **Smooth** | $N_{\min,\text{smooth}} \leq N \leq N_{\max}$ | All harmonics well-represented. No warning. |
| **Sample-rate limited** | $N < N_{\min,\text{smooth}}$ but $N_{\min,\text{smooth}} \leq N_{\max}$ | Highest harmonics are coarse because the sample rate cap limits $N$ below the ideal. |
| **Point-budget exceeded** | $N_{\min,\text{smooth}} > N_{\max}$ | The frequency span is too wide for 16,384 points. Highest harmonics will be visibly aliased/stepped. **Warning shown.** |

#### Worked example: frequency combs

**Case 1 — Comfortable budget (1–10 Hz, step 1 Hz)**

| Parameter | Value |
|---|---|
| Frequencies | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10 Hz |
| Fundamental $f_0$ | $\gcd = 1$ Hz |
| Highest tone $f_{\max}$ | 10 Hz |
| Harmonics $h_{\max}$ | 10 cycles per buffer |
| Min points needed | $10 \times 10 = 100$ |
| Max points (sample-rate cap) | $30\text{M} / 1 = 30{,}000{,}000$ → capped at **16,384** |
| **Optimal $N$** | **16,384** |
| Points per cycle of 10 Hz | $16{,}384 / 10 = 1{,}638$ |
| Regime | **Smooth** — 1,638 points per cycle of the highest tone |

**Case 2 — Moderate span (100–1000 Hz, step 100 Hz)**

| Parameter | Value |
|---|---|
| Frequencies | 100, 200, …, 1000 Hz |
| Fundamental $f_0$ | 100 Hz |
| Highest tone $f_{\max}$ | 1000 Hz |
| Harmonics $h_{\max}$ | 10 |
| Min points needed | 100 |
| Max points | $30\text{M} / 100 = 300{,}000$ → capped at **16,384** |
| **Optimal $N$** | **16,384** |
| Points per cycle of 1 kHz | 1,638 |
| Regime | **Smooth** |

**Case 3 — Wide span with warning (1 Hz + 10,000 Hz)**

| Parameter | Value |
|---|---|
| Frequencies | 1, 10000 Hz |
| Fundamental $f_0$ | 1 Hz |
| Highest tone $f_{\max}$ | 10,000 Hz |
| Harmonics $h_{\max}$ | 10,000 |
| Min points needed | $10{,}000 \times 10 = 100{,}000$ |
| Max points | capped at **16,384** |
| **Optimal $N$** | **16,384** |
| Points per cycle of 10 kHz | $16{,}384 / 10{,}000 \approx 1.6$ |
| Regime | **Point-budget exceeded** — only ~1.6 points per cycle of the highest tone |

The 10 kHz component needs 100,000 points but the hardware maximum is 16,384. The GUI shows a warning:

> *Frequency span too wide for smooth output. The highest tone (1e+04 Hz) needs ~100000 points within a 1 Hz fundamental period, but the DG822 maximum is 16384.*

**Practical rule of thumb:** for a comb spanning $f_{\min}$ to $f_{\max}$ with resolution $\Delta f$, the frequency ratio $f_{\max} / f_0$ should be ≲ 1,638 for full smoothness (16,384 points ÷ 10 points-per-cycle). Within one decade of frequency this is easily satisfied; spanning three decades starts to get tight.

#### Generalising to future waveforms

The same framework applies to **any** waveform that has identifiable frequency content:

| Waveform type | How to determine point budget |
|---|---|
| **Single-frequency shapes** (square, pulse, ramp, gaussian, sinc, …) | Output frequency determines $N$ directly. No harmonic concern within the buffer — the shape is defined in normalised coordinates. |
| **Sum of sinusoids** (frequency comb, multi-tone) | Fundamental = GCD of all tones. Budget driven by $f_{\max} / f_0$. |
| **Modulated waveforms** (AM, FM, chirp, …) | The buffer period is set by the modulation rate. The highest instantaneous frequency within the sweep determines the point requirement, analogous to $f_{\max}$ in the comb case. |
| **Waveforms with sharp edges** (step functions, PWM patterns, …) | Sharp transitions have high-frequency content. Effective bandwidth ≈ $f_s / 2$ (Nyquist). More points = sharper edges. Quantify by the fastest transition time relative to the period. |
| **Mathematically defined shapes** (Lorentzian, Bessel, custom functions, …) | If the shape has no intrinsic frequency structure, use the single-frequency formula. The output frequency is set by the user; $N$ is maximised for that frequency. |

The design contract for any new `WaveformGenerator` method is:

1. **Accept a frequency** (or set of frequencies) rather than a point count.
2. **Call `compute_optimal_points()`** (or `compute_optimal_points_for_comb()` for multi-tone) to determine $N$.
3. **Generate the waveform** at that $N$.
4. **Attach metadata** (`.comb_info` or equivalent) so the GUI and upload code can extract the correct output frequency and show warnings.
5. **Return an `ArbitraryWaveform`** with normalised data in [-1, +1].

The GUI and upload pipeline then handle:
- Displaying the computed $N$, sample rate, and any warnings
- Setting the sample rate on the instrument via `:SOURce:FUNCtion:SEQuence:SRATe`
- Disabling the frequency box if the waveform determines its own repetition rate (as with combs)

### Frequency combs: additional details

The frequency comb generator sums sinusoids at specified frequencies. Phases are optimised via Monte Carlo to maximise RMS (flatten the waveform envelope).

- **Frequency input** — range (`start:step:stop`) or explicit comma-separated list
- **Fundamental** — computed as the GCD of all input frequencies
- **Points** — auto-calculated as described above
- **Frequency box** — auto-set to the fundamental and grayed out (since the comb's repetition rate is fixed by $f_0$)
- **Phase optimisation** — random phases are drawn uniformly from $[0, 2\pi)$; the set with the highest RMS is kept. This tends to produce a flatter envelope with less peak clipping after normalisation. Default: 1,000 Monte Carlo iterations.

---

## Project Structure

The driver is the importable package `rigol_dg822/`. This repo is also a git
submodule of `xsphere-daq`, which puts this directory on `sys.path` — hence the
package, rather than flat top-level modules that would collide in the parent's
namespace.

```
xsphere-rigol-dg822/
├── rigol_dg822/            # the importable package
│   ├── __init__.py         # re-exports the controller, the sim, the enums
│   ├── connection.py       # VISA connection & SCPI I/O (pyvisa or sim)
│   ├── controller.py       # High-level controller façade
│   ├── waveform.py         # Waveform type & parameter configuration
│   ├── output.py           # Output state, impedance, polarity, sync
│   ├── arbitrary.py        # Arbitrary waveform generation & optimisation
│   ├── plot.py             # Waveform preview maths + matplotlib (headless-safe)
│   └── sim.py              # Simulated DG822 — needs no VISA backend
├── dg822_gui.py            # Tkinter GUI application (entry point)
├── tools/                  # diagnose_*.py / test_*.py bench scripts
├── docs/session-log.md
├── requirements.txt
├── README.md
└── waveforms/              # Saved waveform CSV files
    ├── FREQCOMB.csv
    └── SQUARE.csv
```

### Module dependency graph

```
dg822_gui.py
  ├── rigol_dg822.controller
  │     ├── rigol_dg822.connection    (pyvisa, or rigol_dg822.sim)
  │     │     └── rigol_dg822.sim     (stdlib only)
  │     ├── rigol_dg822.waveform
  │     └── rigol_dg822.output
  ├── rigol_dg822.plot                (numpy; matplotlib/scipy/tkinter lazily)
  └── rigol_dg822.arbitrary           (numpy)
```

`rigol_dg822.plot` imports cleanly on a headless server: tkinter, the Tk canvas
and pyplot are imported inside the functions that need a display, and
`create_figure()` pins the Agg backend when pyplot is not already up. The pure
`generate_*` helpers work with matplotlib absent entirely.

### Module roles

| Module | Role |
|---|---|
| `rigol_dg822/connection.py` | VISA resource discovery, USB-TMC connection, SCPI `write` / `query` / `write_raw` (binary), IEEE-488.2 commands (`*RST`, `*IDN?`, `*OPC?`); routes to the simulator on `SIM::DG822::INSTR` |
| `rigol_dg822/waveform.py` | `:APPLy` quick-setup for all standard waveforms, individual parameter R/W, binary DAC16 upload, `.RAF` file save/load/list |
| `rigol_dg822/output.py` | Channel on/off, load impedance (1 Ω–10 kΩ or High-Z), polarity, sync output, trigger edge |
| `rigol_dg822/controller.py` | Unified façade combining connection + waveform + output; convenience methods like `setup_sine()`, `setup_pulse()` (with centering) |
| `rigol_dg822/plot.py` | Generates numpy time/voltage arrays for all waveform types, auto-scales axes, embeds matplotlib in tkinter via `FigureCanvasTkAgg` (imported lazily) |
| `rigol_dg822/arbitrary.py` | `ArbitraryWaveform` data container (normalised ±1 ↔ 14-bit DAC), `WaveformGenerator` factory (shapes, frequency combs), optimal-point calculators |
| `rigol_dg822/sim.py` | Simulated DG822 presenting the pyvisa resource interface: parses the real SCPI (including the DAC16 block), models both channels and a virtual `.RAF` store, and reports unknown commands through the error queue |
| `dg822_gui.py` | Full tkinter GUI: connection panel, dual-channel tabs with live preview, arb generator dialog with auto-optimal points and warnings, presets, status bar |
| `tools/` | Bench diagnostics and hardware scripts, kept out of the import path |

---

## Key SCPI Notes (DG822 non-Pro)

These were discovered during development and are important if extending the code:

- **Arbitrary upload:** `:SOURce{n}:TRACe:DATA:DAC16 VOLATILE,END,#<digits><bytecount><binary>` — unsigned 16-bit little-endian (0x0000–0x3FFF). Auto-switches device to `SEQUENCE` mode.
- **Do NOT use** `:APPLy:USER`, `:APPLy:ARBitrary`, or `:FUNCtion USER` after uploading — they all reset the waveform to the built-in SINC.
- **Sample rate:** `:SOURce{n}:FUNCtion:SEQuence:SRATe {rate}` — range 2 kSa/s to 30 MSa/s.
- **Save to internal memory:** `:MMEMory:STORe:DATA "name.RAF"` (no channel number, max 7-char name).
- **ASCII data commands** (`:DATA VOLATILE,{csv}`) are **not supported** on the DG822 — they return `"Command header error"`.

---

## License

This project is provided as-is for laboratory use. No warranty expressed or implied.
