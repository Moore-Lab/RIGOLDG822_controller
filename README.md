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
from dg822_controller import DG822Controller

with DG822Controller() as gen:
    gen.connect("USB0::0x1AB1::0x0643::DG8A204201757::0::INSTR")

    # 1 kHz sine, 2 Vpp on CH1
    gen.setup_sine(channel=1, frequency=1000, amplitude=2.0)
    gen.output_on(1)

    # 5 kHz square, 3.3 Vpp, 1.65 V offset on CH2
    gen.setup_square(channel=2, frequency=5000, amplitude=3.3, offset=1.65, duty_cycle=50)
    gen.output_on(2)
```

---

## Arbitrary Waveforms

### Generating in the GUI

1. Select **Arbitrary** from the waveform type.
2. Click **Generate…** to open the generator dialog.
3. Choose a shape (or *frequency_comb*) and set parameters.
4. Points are **auto-calculated** for maximum smoothness — you don't need to specify them.
5. Click **Generate**, then **Upload** to send to the instrument.

### Frequency Combs

The frequency comb generator sums sinusoids at specified frequencies. Phases are optimised via Monte Carlo to maximise RMS (flatten the waveform envelope).

- **Frequency input** — range (`start:step:stop`) or explicit list
- **Points** — auto-calculated from the comb's fundamental frequency (GCD of all tones)
- **Frequency box** — auto-set to the fundamental and grayed out (since the comb's repetition rate is fixed)
- **Warnings** — shown if the frequency span is too wide for the 16,384-point limit (e.g. a 1 Hz + 10 kHz comb needs ~100,000 points)

### How frequency relates to points

The DG822 replays the waveform buffer at a configurable sample rate:

$$f_{\text{out}} = \frac{\text{sample rate}}{\text{num points}}$$

The software maximises points for the smoothest output:

$$\text{num points} = \min\!\left(16384,\;\left\lfloor \frac{30\,\text{MSa/s}}{f_{\text{out}}} \right\rfloor\right)$$

| Output frequency | Auto points | Sample rate |
|---|---|---|
| 1 Hz | 16,384 | 16.4 kSa/s |
| 1 kHz | 16,384 | 16.4 MSa/s |
| 10 kHz | 3,000 | 30 MSa/s |
| 100 kHz | 300 | 30 MSa/s |
| 1 MHz | 30 | 30 MSa/s |

### Internal memory (.RAF files)

Uploaded waveforms are automatically saved as `.RAF` files on the instrument's internal storage (`C:\` Arb File directory). Filenames are limited to 7 characters. These persist across power cycles.

---

## Project Structure

```
RIGOLDG822_controller/
├── dg822_gui.py            # Tkinter GUI application (entry point)
├── dg822_controller.py     # High-level controller façade
├── dg822_connection.py     # VISA connection & SCPI I/O
├── dg822_waveform.py       # Waveform type & parameter configuration
├── dg822_output.py         # Output state, impedance, polarity, sync
├── dg822_plot.py           # Matplotlib waveform preview & embedding
├── dg822_arbitrarywf.py    # Arbitrary waveform generation & optimisation
├── requirements.txt
├── README.md
└── waveforms/              # Saved waveform CSV files
    ├── FREQCOMB.csv
    └── SQUARE.csv
```

### Module dependency graph

```
dg822_gui.py
  ├── dg822_controller.py
  │     ├── dg822_connection.py      (pyvisa)
  │     ├── dg822_waveform.py
  │     └── dg822_output.py
  ├── dg822_plot.py                  (matplotlib, scipy)
  └── dg822_arbitrarywf.py           (numpy)
```

### Module roles

| Module | Role |
|---|---|
| `dg822_connection.py` | VISA resource discovery, USB-TMC connection, SCPI `write` / `query` / `write_raw` (binary), IEEE-488.2 commands (`*RST`, `*IDN?`, `*OPC?`) |
| `dg822_waveform.py` | `:APPLy` quick-setup for all standard waveforms, individual parameter R/W, binary DAC16 upload, `.RAF` file save/load/list |
| `dg822_output.py` | Channel on/off, load impedance (1 Ω–10 kΩ or High-Z), polarity, sync output, trigger edge |
| `dg822_controller.py` | Unified façade combining connection + waveform + output; convenience methods like `setup_sine()`, `setup_pulse()` (with centering) |
| `dg822_plot.py` | Generates numpy time/voltage arrays for all waveform types, auto-scales axes, embeds matplotlib in tkinter via `FigureCanvasTkAgg` |
| `dg822_arbitrarywf.py` | `ArbitraryWaveform` data container (normalised ±1 ↔ 14-bit DAC), `WaveformGenerator` factory (shapes, frequency combs), optimal-point calculators |
| `dg822_gui.py` | Full tkinter GUI: connection panel, dual-channel tabs with live preview, arb generator dialog with auto-optimal points and warnings, presets, status bar |

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
