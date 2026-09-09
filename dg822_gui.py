"""
RIGOL DG822 Waveform Generator - GUI Application

This module provides a graphical user interface for controlling the RIGOL DG822
waveform generator. It uses tkinter for the GUI and the DG822Controller for
instrument communication.

Author: Auto-generated
Date: 2026-01-09
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
from typing import Optional, List, Tuple
import threading
import time
import numpy as np

from rigol_dg822.controller import DG822Controller
from rigol_dg822.plot import WaveformPlotter
from rigol_dg822.arbitrary import (
    ArbitraryWaveform, WaveformGenerator,
    compute_optimal_points, compute_optimal_points_for_comb,
    check_frequency_feasibility, DG822_MIN_POINTS, DG822_MAX_POINTS,
    DG822_MAX_SAMPLE_RATE, DG822_MIN_SAMPLE_RATE,
)


class ConnectionFrame(ttk.LabelFrame):
    """Frame for connection controls."""
    
    def __init__(self, parent, on_connect_callback, on_disconnect_callback):
        super().__init__(parent, text="Connection", padding=10)
        
        self.on_connect = on_connect_callback
        self.on_disconnect = on_disconnect_callback
        self.devices: List[Tuple[str, str]] = []
        
        self._create_widgets()
    
    def _create_widgets(self):
        # Row 0: Connection mode selection
        self.mode_var = tk.StringVar(value="scan")
        
        ttk.Radiobutton(
            self, text="Scan for devices", variable=self.mode_var,
            value="scan", command=self._on_mode_change
        ).grid(row=0, column=0, sticky="w", padx=5)
        
        ttk.Radiobutton(
            self, text="Manual VISA address", variable=self.mode_var,
            value="manual", command=self._on_mode_change
        ).grid(row=0, column=1, sticky="w", padx=5)
        
        # Row 1: Device selection (for scan mode)
        self.scan_frame = ttk.Frame(self)
        self.scan_frame.grid(row=1, column=0, columnspan=4, sticky="ew", pady=5)
        
        ttk.Label(self.scan_frame, text="Device:").pack(side="left", padx=(0, 5))
        
        self.device_combo = ttk.Combobox(self.scan_frame, width=50, state="readonly")
        self.device_combo.pack(side="left", padx=5)
        
        self.scan_btn = ttk.Button(self.scan_frame, text="Scan", command=self._scan_devices)
        self.scan_btn.pack(side="left", padx=5)
        
        # Row 1 (alternate): Manual VISA entry
        self.manual_frame = ttk.Frame(self)
        
        ttk.Label(self.manual_frame, text="VISA Address:").pack(side="left", padx=(0, 5))
        
        self.visa_entry = ttk.Entry(self.manual_frame, width=55)
        self.visa_entry.pack(side="left", padx=5)
        self.visa_entry.insert(0, "USB0::0x1AB1::0x0643::DG8A204201757::0::INSTR")
        
        # Row 2: Connect/Disconnect buttons and status
        btn_frame = ttk.Frame(self)
        btn_frame.grid(row=2, column=0, columnspan=4, sticky="ew", pady=5)
        
        self.connect_btn = ttk.Button(btn_frame, text="Connect", command=self._connect)
        self.connect_btn.pack(side="left", padx=5)
        
        self.disconnect_btn = ttk.Button(
            btn_frame, text="Disconnect", command=self._disconnect, state="disabled"
        )
        self.disconnect_btn.pack(side="left", padx=5)
        
        self.status_label = ttk.Label(btn_frame, text="Not connected", foreground="red")
        self.status_label.pack(side="left", padx=20)
        
        # Configure column weights
        self.columnconfigure(0, weight=1)
    
    def _on_mode_change(self):
        """Handle connection mode change."""
        if self.mode_var.get() == "scan":
            self.manual_frame.grid_remove()
            self.scan_frame.grid(row=1, column=0, columnspan=4, sticky="ew", pady=5)
        else:
            self.scan_frame.grid_remove()
            self.manual_frame.grid(row=1, column=0, columnspan=4, sticky="ew", pady=5)
    
    def _scan_devices(self):
        """Scan for available devices."""
        self.scan_btn.config(state="disabled")
        self.status_label.config(text="Scanning...", foreground="orange")
        self.update()
        
        # Run scan in a thread to keep UI responsive
        def do_scan():
            controller = DG822Controller()
            self.devices = controller.discover_devices()
            controller.connection.close()
            
            # Update UI in main thread
            self.after(0, self._update_device_list)
        
        thread = threading.Thread(target=do_scan, daemon=True)
        thread.start()
    
    def _update_device_list(self):
        """Update the device combobox with scan results."""
        self.scan_btn.config(state="normal")
        
        if self.devices:
            device_strings = [f"{idn} ({res})" for res, idn in self.devices]
            self.device_combo['values'] = device_strings
            self.device_combo.current(0)
            self.status_label.config(
                text=f"Found {len(self.devices)} device(s)", foreground="green"
            )
        else:
            self.device_combo['values'] = []
            self.device_combo.set("")
            self.status_label.config(text="No devices found", foreground="red")
    
    def _connect(self):
        """Connect to selected device."""
        if self.mode_var.get() == "scan":
            if not self.devices:
                messagebox.showwarning("No Device", "Please scan for devices first.")
                return
            
            idx = self.device_combo.current()
            if idx < 0:
                messagebox.showwarning("No Device", "Please select a device.")
                return
            
            resource = self.devices[idx][0]
        else:
            resource = self.visa_entry.get().strip()
            if not resource:
                messagebox.showwarning("No Address", "Please enter a VISA address.")
                return
        
        self.status_label.config(text="Connecting...", foreground="orange")
        self.update()
        
        if self.on_connect(resource):
            self.connect_btn.config(state="disabled")
            self.disconnect_btn.config(state="normal")
            self.scan_btn.config(state="disabled")
            self.device_combo.config(state="disabled")
            self.visa_entry.config(state="disabled")
            self.status_label.config(text="Connected", foreground="green")
        else:
            self.status_label.config(text="Connection failed", foreground="red")
    
    def _disconnect(self):
        """Disconnect from device."""
        self.on_disconnect()
        self.connect_btn.config(state="normal")
        self.disconnect_btn.config(state="disabled")
        self.scan_btn.config(state="normal")
        self.device_combo.config(state="readonly")
        self.visa_entry.config(state="normal")
        self.status_label.config(text="Disconnected", foreground="red")


class ChannelFrame(ttk.LabelFrame):
    """Frame for controlling a single channel."""
    
    WAVEFORMS = ["Sine", "Square", "Pulse", "Ramp", "Noise", "DC", "Arbitrary"]
    
    def __init__(self, parent, channel: int, controller_getter):
        super().__init__(parent, text=f"Channel {channel}", padding=10)
        
        self.channel = channel
        self.get_controller = controller_getter
        self.arb_waveform: Optional[ArbitraryWaveform] = None
        self.plotter = WaveformPlotter()
        
        self._create_widgets()
        self._set_defaults()
    
    def _create_widgets(self):
        # Create a horizontal paned window for controls and plot
        self.paned = ttk.PanedWindow(self, orient="horizontal")
        self.paned.pack(fill="both", expand=True)
        
        # Left side: Controls
        controls_frame = ttk.Frame(self.paned)
        self.paned.add(controls_frame, weight=1)
        
        # Right side: Plot
        plot_frame = ttk.LabelFrame(self.paned, text="Waveform Preview", padding=5)
        self.paned.add(plot_frame, weight=1)
        
        # === Output Control ===
        output_frame = ttk.Frame(controls_frame)
        output_frame.grid(row=0, column=0, columnspan=4, sticky="ew", pady=5)
        
        self.output_var = tk.BooleanVar(value=False)
        self.output_btn = ttk.Checkbutton(
            output_frame, text="Output ON", variable=self.output_var,
            command=self._toggle_output, style="Toggle.TButton"
        )
        self.output_btn.pack(side="left", padx=5)
        
        self.output_indicator = tk.Canvas(output_frame, width=20, height=20)
        self.output_indicator.pack(side="left", padx=5)
        self._update_output_indicator(False)
        
        # Run mode selector
        ttk.Label(output_frame, text="  Run:").pack(side="left", padx=(15, 5))
        self.run_mode_var = tk.StringVar(value="Continuous")
        self.run_mode_combo = ttk.Combobox(
            output_frame, textvariable=self.run_mode_var,
            values=["Continuous", "N Cycles", "Duration"], width=12, state="readonly"
        )
        self.run_mode_combo.pack(side="left", padx=5)
        self.run_mode_combo.bind("<<ComboboxSelected>>", self._on_run_mode_change)
        
        # N Cycles input (hidden by default)
        self.cycles_frame = ttk.Frame(output_frame)
        self.cycles_frame.pack(side="left", padx=5)
        ttk.Label(self.cycles_frame, text="Cycles:").pack(side="left")
        self.cycles_var = tk.StringVar(value="100")
        ttk.Entry(self.cycles_frame, textvariable=self.cycles_var, width=8).pack(side="left", padx=2)
        self.cycles_frame.pack_forget()  # Hidden by default
        
        # Duration input (hidden by default)
        self.duration_frame = ttk.Frame(output_frame)
        self.duration_frame.pack(side="left", padx=5)
        ttk.Label(self.duration_frame, text="Time:").pack(side="left")
        self.duration_var = tk.StringVar(value="10")
        ttk.Entry(self.duration_frame, textvariable=self.duration_var, width=8).pack(side="left", padx=2)
        self.duration_unit_var = tk.StringVar(value="s")
        ttk.Combobox(
            self.duration_frame, textvariable=self.duration_unit_var,
            values=["s", "min", "hour"], width=5, state="readonly"
        ).pack(side="left", padx=2)
        self.duration_frame.pack_forget()  # Hidden by default
        
        # === Waveform Selection ===
        wave_frame = ttk.LabelFrame(controls_frame, text="Waveform", padding=5)
        wave_frame.grid(row=1, column=0, columnspan=4, sticky="ew", pady=5)
        
        self.waveform_var = tk.StringVar(value="Sine")
        for i, wf in enumerate(self.WAVEFORMS):
            row = i // 4
            col = i % 4
            ttk.Radiobutton(
                wave_frame, text=wf, variable=self.waveform_var,
                value=wf, command=self._on_waveform_change
            ).grid(row=row, column=col, padx=8, pady=3, sticky="w")
        
        # === Parameters Frame ===
        param_frame = ttk.LabelFrame(controls_frame, text="Parameters", padding=5)
        param_frame.grid(row=2, column=0, columnspan=4, sticky="ew", pady=5)
        
        # Frequency (supports equations like 1/0.1 for period-based input)
        ttk.Label(param_frame, text="Frequency:").grid(row=0, column=0, sticky="e", padx=5, pady=3)
        self.freq_var = tk.StringVar(value="1000")
        self.freq_entry = ttk.Entry(param_frame, textvariable=self.freq_var, width=15)
        self.freq_entry.grid(row=0, column=1, padx=5, pady=3)
        self.freq_entry.bind("<FocusOut>", lambda e: self._validate_frequency())
        
        self.freq_unit_var = tk.StringVar(value="Hz")
        self.freq_unit = ttk.Combobox(
            param_frame, textvariable=self.freq_unit_var,
            values=["Hz", "kHz", "MHz"], width=5, state="readonly"
        )
        self.freq_unit.grid(row=0, column=2, padx=5, pady=3)
        
        # Hint about equation support
        self.freq_hint_label = ttk.Label(param_frame, text="(e.g. 1/0.1 = 10)", 
                  font=("TkDefaultFont", 8), foreground="gray")
        self.freq_hint_label.grid(row=0, column=3, sticky="w", padx=5)
        
        # Amplitude
        ttk.Label(param_frame, text="Amplitude:").grid(row=1, column=0, sticky="e", padx=5, pady=3)
        self.amp_var = tk.StringVar(value="5.0")
        self.amp_entry = ttk.Entry(param_frame, textvariable=self.amp_var, width=15)
        self.amp_entry.grid(row=1, column=1, padx=5, pady=3)
        ttk.Label(param_frame, text="Vpp").grid(row=1, column=2, sticky="w", padx=5, pady=3)
        
        # Offset
        ttk.Label(param_frame, text="Offset:").grid(row=2, column=0, sticky="e", padx=5, pady=3)
        self.offset_var = tk.StringVar(value="0.0")
        self.offset_entry = ttk.Entry(param_frame, textvariable=self.offset_var, width=15)
        self.offset_entry.grid(row=2, column=1, padx=5, pady=3)
        ttk.Label(param_frame, text="V").grid(row=2, column=2, sticky="w", padx=5, pady=3)
        
        # Phase
        ttk.Label(param_frame, text="Phase:").grid(row=3, column=0, sticky="e", padx=5, pady=3)
        self.phase_var = tk.StringVar(value="0.0")
        self.phase_entry = ttk.Entry(param_frame, textvariable=self.phase_var, width=15)
        self.phase_entry.grid(row=3, column=1, padx=5, pady=3)
        ttk.Label(param_frame, text="°").grid(row=3, column=2, sticky="w", padx=5, pady=3)
        
        # === Waveform-specific parameters ===
        self.extra_frame = ttk.LabelFrame(controls_frame, text="Waveform Options", padding=5)
        self.extra_frame.grid(row=3, column=0, columnspan=4, sticky="ew", pady=5)
        
        # Duty Cycle (for Square)
        self.duty_label = ttk.Label(self.extra_frame, text="Duty Cycle:")
        self.duty_label.grid(row=0, column=0, sticky="e", padx=5, pady=3)
        self.duty_var = tk.StringVar(value="50")
        self.duty_entry = ttk.Entry(self.extra_frame, textvariable=self.duty_var, width=10)
        self.duty_entry.grid(row=0, column=1, padx=5, pady=3)
        self.duty_unit_label = ttk.Label(self.extra_frame, text="%")
        self.duty_unit_label.grid(row=0, column=2, sticky="w", padx=5, pady=3)
        
        # Pulse Width Frame (for Pulse) - shown instead of duty cycle
        self.pulse_frame = ttk.Frame(self.extra_frame)
        self.pulse_frame.grid(row=1, column=0, columnspan=6, sticky="ew", pady=3)
        
        # Pulse width mode selector
        ttk.Label(self.pulse_frame, text="Pulse Width:").grid(row=0, column=0, sticky="e", padx=5)
        self.pulse_width_var = tk.StringVar(value="100")
        self.pulse_width_entry = ttk.Entry(self.pulse_frame, textvariable=self.pulse_width_var, width=10)
        self.pulse_width_entry.grid(row=0, column=1, padx=5)
        
        self.pulse_width_unit_var = tk.StringVar(value="µs")
        self.pulse_width_unit = ttk.Combobox(
            self.pulse_frame, textvariable=self.pulse_width_unit_var,
            values=["ns", "µs", "ms", "s"], width=5, state="readonly"
        )
        self.pulse_width_unit.grid(row=0, column=2, padx=5)
        
        # Period display (calculated from frequency)
        ttk.Label(self.pulse_frame, text="Period:").grid(row=0, column=3, sticky="e", padx=(15, 5))
        self.period_display_var = tk.StringVar(value="1.000 ms")
        ttk.Label(self.pulse_frame, textvariable=self.period_display_var, width=12).grid(row=0, column=4, padx=5)
        
        # Duty cycle display (calculated)
        ttk.Label(self.pulse_frame, text="Duty:").grid(row=0, column=5, padx=(10, 2))
        self.calc_duty_var = tk.StringVar(value="10.0%")
        ttk.Label(self.pulse_frame, textvariable=self.calc_duty_var, width=8).grid(row=0, column=6, padx=2)
        
        # Info row - 1 pulse per period
        ttk.Label(self.pulse_frame, text="(1 pulse per period — use N Cycles for pulse count)", 
                  font=("TkDefaultFont", 8), foreground="gray").grid(row=1, column=0, columnspan=7, sticky="w", padx=5, pady=(2, 0))
        
        self.pulse_frame.grid_remove()  # Hidden by default
        
        # Symmetry (for Ramp)
        self.symm_label = ttk.Label(self.extra_frame, text="Symmetry:")
        self.symm_label.grid(row=0, column=3, sticky="e", padx=5, pady=3)
        self.symm_var = tk.StringVar(value="50")
        self.symm_entry = ttk.Entry(self.extra_frame, textvariable=self.symm_var, width=10)
        self.symm_entry.grid(row=0, column=4, padx=5, pady=3)
        self.symm_unit_label = ttk.Label(self.extra_frame, text="%")
        self.symm_unit_label.grid(row=0, column=5, sticky="w", padx=5, pady=3)
        
        # === Arbitrary Waveform ===
        self.arb_frame = ttk.LabelFrame(controls_frame, text="Arbitrary Waveform", padding=5)
        self.arb_frame.grid(row=4, column=0, columnspan=4, sticky="ew", pady=5)
        
        self.arb_file_var = tk.StringVar(value="No file loaded")
        ttk.Label(self.arb_frame, textvariable=self.arb_file_var).grid(row=0, column=0, columnspan=2, sticky="w", padx=5)
        
        ttk.Button(self.arb_frame, text="Load CSV...", command=self._load_arb_csv).grid(row=0, column=2, padx=5)
        ttk.Button(self.arb_frame, text="Generate...", command=self._generate_arb).grid(row=0, column=3, padx=5)
        ttk.Button(self.arb_frame, text="Save CSV...", command=self._save_arb_csv).grid(row=0, column=4, padx=5)
        ttk.Button(self.arb_frame, text="Upload", command=self._upload_arb).grid(row=0, column=5, padx=5)
        
        # === Load Impedance ===
        load_frame = ttk.LabelFrame(controls_frame, text="Load", padding=5)
        load_frame.grid(row=5, column=0, columnspan=2, sticky="ew", pady=5)
        
        self.load_var = tk.StringVar(value="HighZ")
        ttk.Radiobutton(
            load_frame, text="High-Z", variable=self.load_var, value="HighZ",
            command=self._on_load_change
        ).pack(side="left", padx=10)
        ttk.Radiobutton(
            load_frame, text="50Ω", variable=self.load_var, value="50",
            command=self._on_load_change
        ).pack(side="left", padx=10)
        
        # === Apply Button ===
        btn_frame = ttk.Frame(controls_frame)
        btn_frame.grid(row=5, column=2, columnspan=2, sticky="e", pady=5)
        
        self.apply_btn = ttk.Button(btn_frame, text="Apply Settings", command=self._apply_settings)
        self.apply_btn.pack(side="right", padx=5)
        
        self.refresh_btn = ttk.Button(btn_frame, text="Refresh", command=self._refresh_status)
        self.refresh_btn.pack(side="right", padx=5)
        
        # === Plot Frame ===
        self.plotter.create_figure(figsize=(4, 3), dpi=80)
        self.canvas = self.plotter.embed_in_tkinter(plot_frame)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)
        
        # Initial plot
        self._update_plot()
    
    def _set_defaults(self):
        """Set default values and configure auto-update for plot."""
        self._on_waveform_change()
        
        # Add traces to auto-update plot when parameters change
        # Use a small delay to avoid too many updates while typing
        self._update_scheduled = False
        
        def schedule_update(*args):
            """Schedule a plot update with debouncing."""
            if not self._update_scheduled:
                self._update_scheduled = True
                self.after(100, self._do_delayed_update)
        
        # Trace all parameter variables
        self.freq_var.trace_add("write", schedule_update)
        self.freq_unit_var.trace_add("write", schedule_update)
        self.amp_var.trace_add("write", schedule_update)
        self.offset_var.trace_add("write", schedule_update)
        self.phase_var.trace_add("write", schedule_update)
        self.duty_var.trace_add("write", schedule_update)
        self.symm_var.trace_add("write", schedule_update)
        self.pulse_width_var.trace_add("write", schedule_update)
        self.pulse_width_unit_var.trace_add("write", schedule_update)
        
        # Also update period/duty display when frequency or pulse width changes
        def update_pulse_display(*args):
            self._update_pulse_display()
        self.freq_var.trace_add("write", update_pulse_display)
        self.freq_unit_var.trace_add("write", update_pulse_display)
        self.pulse_width_var.trace_add("write", update_pulse_display)
        self.pulse_width_unit_var.trace_add("write", update_pulse_display)
    
    def _update_pulse_display(self):
        """Update the period and calculated duty cycle display for pulse mode."""
        try:
            # Get frequency in Hz using equation parser
            freq_hz = self._get_frequency_hz()
            
            if freq_hz <= 0:
                return
            
            # Calculate period
            period_s = 1.0 / freq_hz
            
            # Format period display
            if period_s >= 1:
                self.period_display_var.set(f"{period_s:.3f} s")
            elif period_s >= 1e-3:
                self.period_display_var.set(f"{period_s*1e3:.3f} ms")
            elif period_s >= 1e-6:
                self.period_display_var.set(f"{period_s*1e6:.3f} µs")
            else:
                self.period_display_var.set(f"{period_s*1e9:.3f} ns")
            
            # Get pulse width in seconds
            width = float(self.pulse_width_var.get())
            width_unit = self.pulse_width_unit_var.get()
            width_multipliers = {"ns": 1e-9, "µs": 1e-6, "ms": 1e-3, "s": 1}
            width_s = width * width_multipliers.get(width_unit, 1e-6)
            
            # Calculate duty cycle
            duty = (width_s / period_s) * 100
            
            if duty > 100:
                self.calc_duty_var.set(">100%!")
            else:
                self.calc_duty_var.set(f"{duty:.1f}%")
                
        except (ValueError, ZeroDivisionError):
            pass
    
    def _get_pulse_duty_cycle(self, freq_hz: float) -> float:
        """Calculate duty cycle from pulse width settings."""
        try:
            if freq_hz <= 0:
                return 50.0
            
            period_s = 1.0 / freq_hz
            
            # Get pulse width in seconds
            width = float(self.pulse_width_var.get())
            width_unit = self.pulse_width_unit_var.get()
            width_multipliers = {"ns": 1e-9, "µs": 1e-6, "ms": 1e-3, "s": 1}
            width_s = width * width_multipliers.get(width_unit, 1e-6)
            
            # Calculate duty cycle, capped at 99%
            duty = min(99.0, (width_s / period_s) * 100)
            return max(1.0, duty)  # Also minimum 1%
        except (ValueError, ZeroDivisionError):
            return 50.0
    
    def _do_delayed_update(self):
        """Perform the delayed plot update."""
        self._update_scheduled = False
        self._update_plot()
    
    def _update_output_indicator(self, on: bool):
        """Update the output indicator LED."""
        self.output_indicator.delete("all")
        color = "#00ff00" if on else "#444444"
        self.output_indicator.create_oval(2, 2, 18, 18, fill=color, outline="black")
    
    def _on_waveform_change(self):
        """Handle waveform type change - show/hide relevant parameters."""
        wf = self.waveform_var.get()
        
        # Show/hide frequency (not applicable to Noise, DC, or Arbitrary)
        # For ALL arb waveforms (comb or not), frequency is set by the arb dialog
        is_arb = (wf == "Arbitrary" and self.arb_waveform is not None)
        freq_disabled = wf in ["Noise", "DC"] or is_arb
        self.freq_entry.config(state="disabled" if freq_disabled else "normal")
        self.freq_unit.config(state="disabled" if freq_disabled else "readonly")
        
        # Show/hide phase (not applicable to Noise and DC)
        phase_state = "disabled" if wf in ["Noise", "DC"] else "normal"
        self.phase_entry.config(state=phase_state)
        
        # Show/hide duty cycle (only for Square)
        if wf == "Square":
            self.duty_label.grid()
            self.duty_entry.grid()
            self.duty_entry.config(state="normal")
            self.duty_unit_label.grid()
            self.pulse_frame.grid_remove()
        elif wf == "Pulse":
            # For Pulse, show pulse width controls instead of duty cycle
            self.duty_label.grid_remove()
            self.duty_entry.grid_remove()
            self.duty_unit_label.grid_remove()
            self.pulse_frame.grid()
            self._update_pulse_display()
        else:
            self.duty_label.grid()
            self.duty_entry.grid()
            self.duty_entry.config(state="disabled")
            self.duty_unit_label.grid()
            self.pulse_frame.grid_remove()
        
        # Show/hide symmetry (only for Ramp)
        symm_state = "normal" if wf == "Ramp" else "disabled"
        self.symm_entry.config(state=symm_state)
        
        # Show/hide arbitrary waveform frame
        if wf == "Arbitrary":
            self.arb_frame.grid()
            # Update frequency hint for arb mode
            if (self.arb_waveform is not None 
                    and hasattr(self.arb_waveform, 'comb_info') 
                    and self.arb_waveform.comb_info):
                f0 = self.arb_waveform.comb_info['fundamental']
                self.freq_hint_label.config(
                    text=f"(comb fundamental: {f0:.4g} Hz)",
                    foreground="blue")
            elif self.arb_waveform is not None:
                self.freq_hint_label.config(
                    text=f"(set by arb dialog)",
                    foreground="blue")
            else:
                self.freq_hint_label.config(
                    text="(generate or load an arb waveform first)",
                    foreground="gray")
        else:
            self.arb_frame.grid_remove()
            self.freq_hint_label.config(
                text="(e.g. 1/0.1 = 10)",
                foreground="gray")
        
        # Update the plot preview
        self._update_plot()
    
    def _on_run_mode_change(self, event=None):
        """Handle run mode change - show/hide relevant inputs."""
        mode = self.run_mode_var.get()
        
        if mode == "Continuous":
            self.cycles_frame.pack_forget()
            self.duration_frame.pack_forget()
        elif mode == "N Cycles":
            self.cycles_frame.pack(side="left", padx=5)
            self.duration_frame.pack_forget()
        elif mode == "Duration":
            self.cycles_frame.pack_forget()
            self.duration_frame.pack(side="left", padx=5)
    
    def _toggle_output(self):
        """Toggle output on/off."""
        controller = self.get_controller()
        if not controller or not controller.is_connected:
            self.output_var.set(False)
            self._update_output_indicator(False)
            return
        
        if self.output_var.get():
            # Check run mode
            run_mode = self.run_mode_var.get()
            
            if run_mode == "Continuous":
                success = controller.output_on(self.channel)
                if success:
                    self._update_output_indicator(True)
            elif run_mode == "N Cycles":
                try:
                    cycles = int(self.cycles_var.get())
                    if cycles <= 0:
                        raise ValueError("Cycles must be positive")
                    success = controller.output_on(self.channel)
                    if success:
                        self._update_output_indicator(True)
                        # Schedule output off after N cycles
                        freq = self._get_frequency_hz()
                        duration_s = cycles / freq
                        self._schedule_output_off(duration_s)
                except ValueError as e:
                    messagebox.showerror("Invalid Value", f"Invalid number of cycles: {e}")
                    self.output_var.set(False)
                    return
            elif run_mode == "Duration":
                try:
                    duration = float(self.duration_var.get())
                    unit = self.duration_unit_var.get()
                    if duration <= 0:
                        raise ValueError("Duration must be positive")
                    
                    # Convert to seconds
                    if unit == "min":
                        duration_s = duration * 60
                    elif unit == "hour":
                        duration_s = duration * 3600
                    else:
                        duration_s = duration
                    
                    success = controller.output_on(self.channel)
                    if success:
                        self._update_output_indicator(True)
                        self._schedule_output_off(duration_s)
                except ValueError as e:
                    messagebox.showerror("Invalid Value", f"Invalid duration: {e}")
                    self.output_var.set(False)
                    return
        else:
            # Cancel any scheduled off
            if hasattr(self, '_output_off_job') and self._output_off_job:
                self.after_cancel(self._output_off_job)
                self._output_off_job = None
            success = controller.output_off(self.channel)
            if success:
                self._update_output_indicator(False)
    
    def _schedule_output_off(self, duration_s: float):
        """Schedule output to turn off after duration."""
        # Cancel any existing scheduled off
        if hasattr(self, '_output_off_job') and self._output_off_job:
            self.after_cancel(self._output_off_job)
        
        # Schedule the off (convert to milliseconds)
        delay_ms = int(duration_s * 1000)
        self._output_off_job = self.after(delay_ms, self._auto_output_off)
    
    def _auto_output_off(self):
        """Automatically turn off output after scheduled time."""
        self._output_off_job = None
        controller = self.get_controller()
        if controller and controller.is_connected:
            controller.output_off(self.channel)
        self.output_var.set(False)
        self._update_output_indicator(False)
    
    def _on_load_change(self):
        """Handle load impedance change."""
        controller = self.get_controller()
        if not controller or not controller.is_connected:
            return
        
        if self.load_var.get() == "50":
            controller.set_load_50_ohm(self.channel)
        else:
            controller.set_load_high_z(self.channel)
    
    def _validate_frequency(self):
        """Validate frequency entry and show feedback if invalid."""
        try:
            freq = self._get_frequency_hz()
            if freq <= 0:
                self.freq_entry.configure(style="Error.TEntry")
            else:
                self.freq_entry.configure(style="TEntry")
        except:
            self.freq_entry.configure(style="Error.TEntry")
    
    def _get_frequency_hz(self) -> float:
        """Get frequency in Hz from entry and unit.
        
        Supports simple math expressions like 1/100 for easier period-based thinking.
        """
        try:
            freq_str = self.freq_var.get().strip()
            
            # Try to evaluate as a simple math expression (supports +, -, *, /, parentheses)
            # Only allow safe characters for security
            allowed_chars = set('0123456789.+-*/() eE')
            if all(c in allowed_chars for c in freq_str):
                value = eval(freq_str, {"__builtins__": {}}, {})
            else:
                value = float(freq_str)
            
            unit = self.freq_unit_var.get()
            
            if unit == "kHz":
                value *= 1000
            elif unit == "MHz":
                value *= 1000000
            
            return float(value)
        except (ValueError, SyntaxError, TypeError, ZeroDivisionError):
            return 1000.0
    
    def _apply_settings(self):
        """Apply all settings to the instrument."""
        controller = self.get_controller()
        if not controller or not controller.is_connected:
            messagebox.showwarning("Not Connected", "Please connect to a device first.")
            return
        
        try:
            wf = self.waveform_var.get()
            freq = self._get_frequency_hz()
            amp = float(self.amp_var.get())
            offset = float(self.offset_var.get())
            phase = float(self.phase_var.get())
            
            success = False
            
            if wf == "Sine":
                success = controller.setup_sine(self.channel, freq, amp, offset, phase)
            elif wf == "Square":
                duty = float(self.duty_var.get())
                success = controller.setup_square(self.channel, freq, amp, offset, phase, duty)
            elif wf == "Pulse":
                duty = self._get_pulse_duty_cycle(freq)
                success = controller.setup_pulse(self.channel, freq, amp, offset, phase, duty_cycle=duty)
            elif wf == "Ramp":
                symm = float(self.symm_var.get())
                success = controller.setup_ramp(self.channel, freq, amp, offset, phase, symm)
            elif wf == "Noise":
                success = controller.setup_noise(self.channel, amp, offset)
            elif wf == "DC":
                success = controller.setup_dc(self.channel, offset)
            elif wf == "Arbitrary":
                if self.arb_waveform is not None and controller.waveform:
                    # First, ensure waveform has a name
                    if not self.arb_waveform.name:
                        self.arb_waveform.name = "CUSTOM"
                    
                    num_pts = len(self.arb_waveform.data)
                    print(f"[APPLY ARB] CH{self.channel}: {num_pts} pts, freq={freq}")
                    
                    # Upload arbitrary waveform (binary DAC16 format)
                    # The upload with flag=END auto-switches device to SEQUENCE mode
                    if not controller.waveform.upload_arbitrary_waveform_from_object(self.channel, self.arb_waveform):
                        messagebox.showerror("Error", "Failed to upload arbitrary waveform.")
                        return
                    
                    # Verify instrument switched to SEQUENCE mode
                    import time
                    time.sleep(0.2)
                    mode_after = controller.waveform.get_function(self.channel)
                    print(f"[APPLY ARB] Mode after upload: {mode_after}")
                    
                    # Save to internal memory as .RAF file
                    raf_name = self.arb_waveform.name[:7]  # Max 7 chars
                    controller.waveform.store_arb_file(raf_name)
                    
                    # Determine the output frequency:
                    #  - For frequency combs: use the fundamental (comb repetition rate)
                    #  - For other shapes:    use the frequency from the main controls
                    if hasattr(self.arb_waveform, 'comb_info') and self.arb_waveform.comb_info:
                        arb_freq = self.arb_waveform.comb_info['fundamental']
                    else:
                        arb_freq = freq
                    
                    sample_rate = arb_freq * num_pts
                    print(f"[APPLY ARB] apply_arbitrary: freq={arb_freq}, "
                          f"pts={num_pts}, sample_rate={sample_rate}")
                    
                    # Set parameters (sample rate, amplitude, offset, phase)
                    # Do NOT call :APPLy:USER — that resets to built-in SINC!
                    success = controller.waveform.apply_arbitrary(
                        self.channel, arb_freq, amp, offset, phase, num_points=num_pts
                    )
                    
                    mode_final = controller.waveform.get_function(self.channel)
                    print(f"[APPLY ARB] Mode final: {mode_final}")
                else:
                    messagebox.showwarning("No Waveform", "Please load or generate an arbitrary waveform first.")
                    return
            
            if success:
                self._refresh_status()
            else:
                messagebox.showerror("Error", "Failed to apply settings.")
                
        except ValueError as e:
            messagebox.showerror("Invalid Value", f"Please check your input values: {e}")
    
    def _refresh_status(self):
        """Refresh status from instrument."""
        controller = self.get_controller()
        if not controller or not controller.is_connected:
            return
        
        # Get current values
        freq = controller.get_frequency(self.channel)
        amp = controller.get_amplitude(self.channel)
        offset = controller.get_offset(self.channel)
        wf_type = controller.get_waveform_type(self.channel)
        output_on = controller.is_output_on(self.channel)
        
        # Update UI
        if freq is not None:
            if freq >= 1000000:
                self.freq_var.set(f"{freq/1000000:.6g}")
                self.freq_unit_var.set("MHz")
            elif freq >= 1000:
                self.freq_var.set(f"{freq/1000:.6g}")
                self.freq_unit_var.set("kHz")
            else:
                self.freq_var.set(f"{freq:.6g}")
                self.freq_unit_var.set("Hz")
        
        if amp is not None:
            self.amp_var.set(f"{amp:.6g}")
        
        if offset is not None:
            self.offset_var.set(f"{offset:.6g}")
        
        if wf_type is not None:
            wf_map = {"SIN": "Sine", "SQU": "Square", "PULS": "Pulse", 
                      "RAMP": "Ramp", "NOIS": "Noise", "DC": "DC", "ARB": "Arbitrary",
                      "SEQU": "Arbitrary", "USER": "Arbitrary"}
            mapped = wf_map.get(wf_type.upper()[:4], wf_type)
            # If we're in SEQUENCE mode (arbitrary uploaded), keep showing Arbitrary
            # and don't clobber arb_waveform by re-triggering _on_waveform_change
            if mapped == "Arbitrary" and self.waveform_var.get() == "Arbitrary":
                # Already showing Arbitrary — just refresh non-waveform fields
                pass
            else:
                self.waveform_var.set(mapped)
                self._on_waveform_change()
        
        self.output_var.set(output_on)
        self._update_output_indicator(output_on)
    
    def set_enabled(self, enabled: bool):
        """Enable or disable all controls."""
        state = "normal" if enabled else "disabled"
        for child in self.winfo_children():
            self._set_widget_state(child, state)
        
        if enabled:
            self._on_waveform_change()  # Re-apply waveform-specific states
    
    def _set_widget_state(self, widget, state):
        """Recursively set state for widget and children."""
        try:
            if isinstance(widget, (ttk.Entry, ttk.Button, ttk.Checkbutton, ttk.Radiobutton)):
                widget.config(state=state)
            elif isinstance(widget, ttk.Combobox):
                widget.config(state="readonly" if state == "normal" else "disabled")
        except tk.TclError:
            pass
        
        for child in widget.winfo_children():
            self._set_widget_state(child, state)
    
    def _update_plot(self):
        """Update the waveform preview plot based on current settings."""
        try:
            waveform = self.waveform_var.get()
            
            # Use the equation-aware frequency parser
            freq_hz = self._get_frequency_hz()
            if freq_hz <= 0:
                return
            
            amp = float(self.amp_var.get())
            offset = float(self.offset_var.get())
            
            # Generate waveform data
            if waveform == "Sine":
                phase = float(self.phase_var.get())
                t, y = self.plotter.generate_sine(freq_hz, amp, offset, phase)
            elif waveform == "Square":
                phase = float(self.phase_var.get())
                duty = float(self.duty_var.get())
                t, y = self.plotter.generate_square(freq_hz, amp, offset, phase, duty)
            elif waveform == "Pulse":
                phase = float(self.phase_var.get())
                # Calculate duty cycle from pulse width
                duty = self._get_pulse_duty_cycle(freq_hz)
                t, y = self.plotter.generate_pulse(freq_hz, amp, offset, phase, duty)
                # Debug: show computed values in title
                period = 1.0/freq_hz
                pulse_start = (period - period*duty/100) / 2
                pulse_end = pulse_start + period*duty/100
                title = f"CH{self.channel} - Pulse (Period={period:.2f}s, Width={period*duty/100:.2f}s, Start={pulse_start:.2f}s)"
                self.plotter.plot_data(t, y, title, channel=self.channel)
                self.canvas.draw()
                return
            elif waveform == "Ramp":
                phase = float(self.phase_var.get())
                symm = float(self.symm_var.get())
                t, y = self.plotter.generate_ramp(freq_hz, amp, offset, phase, symm)
            elif waveform == "Noise":
                t, y = self.plotter.generate_noise(amp, offset)
            elif waveform == "DC":
                t, y = self.plotter.generate_dc(offset)
            elif waveform == "Arbitrary":
                if self.arb_waveform is not None:
                    t, y = self.plotter.generate_arbitrary(self.arb_waveform.data, freq_hz, amp, offset)
                else:
                    # No arbitrary waveform loaded, show flat line
                    t, y = self.plotter.generate_dc(0)
            else:
                return
            
            # Update plot
            self.plotter.plot_data(t, y, f"CH{self.channel} - {waveform}", channel=self.channel)
            self.canvas.draw()
            
        except (ValueError, tk.TclError):
            # Invalid values, don't update plot
            pass
    
    def _load_arb_csv(self):
        """Load arbitrary waveform from CSV file."""
        from tkinter import filedialog
        
        filepath = filedialog.askopenfilename(
            title="Load Arbitrary Waveform",
            initialdir="waveforms",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        
        if filepath:
            try:
                self.arb_waveform = ArbitraryWaveform.load_csv(filepath)
                self.arb_file_var.set(f"Loaded: {self.arb_waveform.name}")
                messagebox.showinfo("Success", 
                    f"Loaded arbitrary waveform with {len(self.arb_waveform.data)} points")
                self._update_plot()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load waveform: {e}")
    
    def _save_arb_csv(self):
        """Save arbitrary waveform to CSV file."""
        if self.arb_waveform is None:
            messagebox.showwarning("Warning", "No arbitrary waveform to save. Load or generate one first.")
            return
        
        # Get name for the waveform
        name = simpledialog.askstring("Waveform Name", 
            "Enter name for the waveform:",
            initialvalue=self.arb_waveform.name or "CUSTOM")
        
        if not name:
            return
        
        self.arb_waveform.name = name
        
        # Default to waveforms folder
        import os
        waveforms_dir = os.path.join(os.path.dirname(__file__), "waveforms")
        os.makedirs(waveforms_dir, exist_ok=True)
        
        filepath = filedialog.asksaveasfilename(
            title="Save Arbitrary Waveform",
            initialdir=waveforms_dir,
            initialfile=f"{name}.csv",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        
        if filepath:
            try:
                # Get amplitude from GUI for file headers
                try:
                    amp_vpp = float(self.amp_var.get())
                except (ValueError, AttributeError):
                    amp_vpp = 10.0
                
                self.arb_waveform.save_csv(filepath, amplitude_vpp=amp_vpp)
                # Also save a .raf (Rigol binary) file alongside the CSV
                import os
                raf_path = os.path.splitext(filepath)[0] + '.raf'
                self.arb_waveform.save_binary(raf_path, amplitude_vpp=amp_vpp)
                self.arb_file_var.set(f"Saved: {name}")
                messagebox.showinfo("Success", 
                    f"Saved waveform to:\n{filepath}\n{raf_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save waveform: {e}")
    
    def _generate_arb(self):
        """Open dialog to generate an arbitrary waveform."""
        output_freq = self._get_frequency_hz()
        dialog = ArbGeneratorDialog(self, output_frequency=output_freq)
        self.wait_window(dialog)
        
        if dialog.result is not None:
            self.arb_waveform = dialog.result
            pts = len(self.arb_waveform.data)
            self.arb_file_var.set(f"Generated: {dialog.waveform_type} ({pts} pts)")
            
            # Auto-set the frequency box based on the dialog's output frequency
            if (hasattr(self.arb_waveform, 'comb_info') 
                    and self.arb_waveform.comb_info):
                # Frequency comb: use fundamental
                f0 = self.arb_waveform.comb_info['fundamental']
                self._set_freq_box(f0)
                self.freq_hint_label.config(
                    text=f"(comb fundamental: {f0:.4g} Hz)",
                    foreground="blue")
                # Disable freq entry — comb fundamental is fixed
                self.freq_entry.config(state="disabled")
                self.freq_unit.config(state="disabled")
            else:
                # Non-comb arb: use the dialog's computed output frequency
                f0 = dialog.dialog_output_frequency
                self._set_freq_box(f0)
                self.freq_hint_label.config(
                    text=f"(arb output: {f0:.4g} Hz)",
                    foreground="blue")
                # Disable freq entry — frequency is set by the arb dialog
                self.freq_entry.config(state="disabled")
                self.freq_unit.config(state="disabled")
            
            print(f"[GENERATE ARB] type={dialog.waveform_type}, pts={pts}, "
                  f"freq={f0:.4g} Hz, freq_var='{self.freq_var.get()}' "
                  f"{self.freq_unit_var.get()}")
            
            messagebox.showinfo("Success", 
                f"Generated {dialog.waveform_type} with {pts} points")
            self._update_plot()
    
    def _set_freq_box(self, freq_hz: float):
        """Set the frequency entry box to a given value in Hz, choosing the best unit."""
        if freq_hz >= 1e6:
            self.freq_var.set(f"{freq_hz/1e6:.6g}")
            self.freq_unit_var.set("MHz")
        elif freq_hz >= 1e3:
            self.freq_var.set(f"{freq_hz/1e3:.6g}")
            self.freq_unit_var.set("kHz")
        else:
            self.freq_var.set(f"{freq_hz:.6g}")
            self.freq_unit_var.set("Hz")
    
    def _upload_arb(self):
        """Upload the current arbitrary waveform to the instrument."""
        if self.arb_waveform is None:
            messagebox.showwarning("Warning", "No arbitrary waveform loaded. Load or generate one first.")
            return
        
        controller = self.get_controller()
        if not controller or not controller.is_connected:
            messagebox.showwarning("Not Connected", "Please connect to a device first.")
            return
        
        try:
            # Ask for waveform name
            name = simpledialog.askstring("Waveform Name", 
                "Enter name for the arbitrary waveform (max 7 chars):",
                initialvalue=self.arb_waveform.name or "CUSTOM")
            
            if name:
                self.arb_waveform.name = name[:7]
                
                num_pts = len(self.arb_waveform.data)
                print(f"[ARB UPLOAD] CH{self.channel}: {num_pts} pts, "
                      f"data range [{self.arb_waveform.data.min():.3f}, "
                      f"{self.arb_waveform.data.max():.3f}]")
                
                # Query instrument mode BEFORE upload
                mode_before = controller.waveform.get_function(self.channel)
                print(f"[ARB UPLOAD] Mode BEFORE upload: {mode_before}")
                
                # Switch to SIN first to clear the volatile arb buffer.
                # On firmware 00.02.x the DDRIII memory retains old data
                # and a new DAC16 upload can be composited with stale data.
                import time
                if mode_before and mode_before.upper() in ('USER', 'SEQUENCE'):
                    from rigol_dg822.waveform import WaveformType
                    controller.waveform.set_function(self.channel, WaveformType.SINE)
                    time.sleep(0.3)
                    print(f"[ARB UPLOAD] Cleared arb buffer (switched to SIN)")
                
                # Upload to volatile memory (auto-switches to USER mode)
                upload_ok = controller.waveform.upload_arbitrary_waveform_from_object(
                    self.channel, self.arb_waveform)
                print(f"[ARB UPLOAD] upload_arbitrary_waveform_from_object returned: {upload_ok}")
                
                if upload_ok:
                    # Verify instrument switched to SEQUENCE mode
                    import time
                    time.sleep(0.2)
                    mode_after = controller.waveform.get_function(self.channel)
                    print(f"[ARB UPLOAD] Mode AFTER upload: {mode_after}")
                    
                    if mode_after and 'SEQ' not in mode_after.upper():
                        print(f"[ARB UPLOAD] WARNING: Instrument did NOT switch to "
                              f"SEQUENCE mode! Got: {mode_after}")
                    
                    # Save to internal memory as .RAF file
                    raf_name = self.arb_waveform.name[:7]
                    controller.waveform.store_arb_file(raf_name)
                    
                    # Set parameters individually (do NOT use :APPLy:USER)
                    try:
                        freq = self._get_frequency_hz()
                        amp = float(self.amp_var.get())
                        offset = float(self.offset_var.get())
                        phase = float(self.phase_var.get())
                        
                        # For frequency combs use the fundamental as output freq
                        if hasattr(self.arb_waveform, 'comb_info') and self.arb_waveform.comb_info:
                            freq = self.arb_waveform.comb_info['fundamental']
                        
                        sample_rate = freq * num_pts
                        print(f"[ARB UPLOAD] apply_arbitrary: freq={freq} Hz, "
                              f"pts={num_pts}, sample_rate={sample_rate}, "
                              f"amp={amp}, offset={offset}, phase={phase}")
                        
                        controller.waveform.apply_arbitrary(
                            self.channel, freq, amp, offset, phase, num_points=num_pts
                        )
                    except Exception as e:
                        print(f"Warning: Could not set arb parameters: {e}")
                    
                    # Verify mode is still SEQUENCE after apply
                    mode_final = controller.waveform.get_function(self.channel)
                    print(f"[ARB UPLOAD] Mode FINAL (after apply): {mode_final}")
                    
                    # Keep GUI on Arbitrary view
                    self.waveform_var.set("Arbitrary")
                    self._on_waveform_change()
                    self._update_plot()
                    
                    messagebox.showinfo("Success", 
                        f"Uploaded and saved '{raf_name}.RAF' to CH{self.channel}\n"
                        f"Mode: {mode_final}")
                else:
                    messagebox.showerror("Error", "Failed to upload waveform to instrument.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to upload waveform: {e}")


class ArbGeneratorDialog(tk.Toplevel):
    """Dialog for generating arbitrary waveforms.
    
    The number of waveform points is computed automatically to maximise
    smoothness within the DG822's hardware limits (8–16 384 points,
    sample rate 2 kSa/s – 30 MSa/s).
    
    For basic shapes the dialog provides controls for polarity
    (unipolar / bipolar) and drive mode (frequency-driven / time-driven).
    For frequency combs the fundamental (GCD of comb tones) drives the
    calculation and warnings are shown when the frequency span is too
    wide for the available point budget.
    """
    
    # Shape-specific parameter definitions.
    # 'time' type gets unit dropdown; None default = compute from period.
    # 'plain' type is a raw number (phase, lobes, etc.).
    SHAPE_PARAMS = {
        "square":      [("On Time", "time", None)],
        "sine":        [("Phase (deg)", "plain", "0")],
        "ramp":        [("Rise Time", "time", None)],
        "trapezoid":   [("Rise Time", "time", None), ("Pulse Time", "time", None), ("Fall Time", "time", None)],
        "pulse":       [("On Time", "time", None), ("Rise Time", "time", None), ("Fall Time", "time", None)],
        "sinc":        [("Num Lobes", "plain", "5")],
        "exponential": [("Time Constant", "time", None)],
        "gaussian":    [("Std Dev", "time", None)],
    }
    
    # Unit conversion tables
    FREQ_UNITS = {"Hz": 1.0, "kHz": 1e3, "MHz": 1e6}
    TIME_UNITS = {"s": 1.0, "ms": 1e-3, "µs": 1e-6}
    # Reverse: raw seconds → best display unit
    @staticmethod
    def _best_time_unit(val_s):
        if abs(val_s) < 1e-3:
            return val_s / 1e-6, "µs"
        elif abs(val_s) < 1.0:
            return val_s / 1e-3, "ms"
        return val_s, "s"
    
    @staticmethod
    def _best_freq_unit(val_hz):
        if abs(val_hz) >= 1e6:
            return val_hz / 1e6, "MHz"
        elif abs(val_hz) >= 1e3:
            return val_hz / 1e3, "kHz"
        return val_hz, "Hz"
    
    def __init__(self, parent, output_frequency: float = 1000.0):
        super().__init__(parent)
        self.title("Generate Arbitrary Waveform")
        self.result = None
        self.waveform_type = None
        self.output_frequency = output_frequency
        self.dialog_output_frequency = output_frequency
        
        self._last_drive_mode = "frequency"
        self._last_polarity = "unipolar"
        self._trap_pulse_override = False  # trapezoid: user specifies pulse time
        
        self.transient(parent)
        self.grab_set()
        
        self._create_widgets()
        self._rebuild_shape_params()
        self._update_freq_controls()
        self._update_info()
        
        # Center dialog
        self.update_idletasks()
        x = parent.winfo_rootx() + (parent.winfo_width() - self.winfo_width()) // 2
        y = parent.winfo_rooty() + (parent.winfo_height() - self.winfo_height()) // 2
        self.geometry(f"+{x}+{y}")
    
    def _create_widgets(self):
        main_frame = ttk.Frame(self, padding=10)
        main_frame.pack(fill="both", expand=True)
        
        # Info label
        ttk.Label(main_frame,
                  text="Generate a normalized waveform shape.\n"
                       "Points are auto-calculated for maximum smoothness.\n"
                       "Amplitude and offset are set in the main controls.",
                  justify="center").grid(row=0, column=0, columnspan=3, pady=10)
        
        # Waveform type
        ttk.Label(main_frame, text="Waveform Type:").grid(row=1, column=0, sticky="e", padx=5, pady=5)
        self.type_var = tk.StringVar(value="square")
        type_combo = ttk.Combobox(main_frame, textvariable=self.type_var, state="readonly",
            values=["square", "sine", "ramp", "trapezoid", "pulse", "sinc", "exponential", "gaussian", "frequency_comb"])
        type_combo.grid(row=1, column=1, columnspan=2, sticky="ew", padx=5, pady=5)
        type_combo.bind("<<ComboboxSelected>>", self._on_type_change)
        
        # === Wave Properties Frame (hidden for combs) ===
        self.wave_props_frame = ttk.LabelFrame(main_frame, text="Wave Properties", padding=5)
        self.wave_props_frame.grid(row=2, column=0, columnspan=3, sticky="ew", padx=5, pady=5)
        
        # Polarity
        ttk.Label(self.wave_props_frame, text="Polarity:").grid(row=0, column=0, sticky="e", padx=5, pady=3)
        self.polarity_var = tk.StringVar(value="unipolar")
        ttk.Radiobutton(self.wave_props_frame, text="Unipolar", variable=self.polarity_var,
                        value="unipolar", command=self._on_polarity_change).grid(row=0, column=1, sticky="w", padx=5)
        ttk.Radiobutton(self.wave_props_frame, text="Bipolar", variable=self.polarity_var,
                        value="bipolar", command=self._on_polarity_change).grid(row=0, column=2, sticky="w", padx=5)
        
        # Drive mode
        ttk.Label(self.wave_props_frame, text="Drive Mode:").grid(row=1, column=0, sticky="e", padx=5, pady=3)
        self.drive_mode_var = tk.StringVar(value="frequency")
        ttk.Radiobutton(self.wave_props_frame, text="Frequency", variable=self.drive_mode_var,
                        value="frequency", command=self._on_drive_mode_change).grid(row=1, column=1, sticky="w", padx=5)
        ttk.Radiobutton(self.wave_props_frame, text="Time", variable=self.drive_mode_var,
                        value="time", command=self._on_drive_mode_change).grid(row=1, column=2, sticky="w", padx=5)
        
        # Frequency / Period entry with unit dropdown
        self.freq_time_label = ttk.Label(self.wave_props_frame, text="Frequency:")
        self.freq_time_label.grid(row=2, column=0, sticky="e", padx=5, pady=3)
        ft_frame = ttk.Frame(self.wave_props_frame)
        ft_frame.grid(row=2, column=1, columnspan=2, sticky="w", padx=5, pady=3)
        
        disp_val, disp_unit = self._best_freq_unit(self.output_frequency)
        self.freq_time_var = tk.StringVar(value=f"{disp_val:.6g}")
        self.freq_time_entry = ttk.Entry(ft_frame, textvariable=self.freq_time_var, width=12)
        self.freq_time_entry.pack(side="left")
        self.freq_time_entry.bind("<KeyRelease>", lambda e: self._update_info())
        
        self.freq_time_unit_var = tk.StringVar(value=disp_unit)
        self.freq_time_unit = ttk.Combobox(ft_frame, textvariable=self.freq_time_unit_var,
                                           state="readonly", width=5,
                                           values=["Hz", "kHz", "MHz"])
        self.freq_time_unit.pack(side="left", padx=(3, 0))
        self.freq_time_unit.bind("<<ComboboxSelected>>", lambda e: self._update_info())
        
        # === Shape Parameters Frame (dynamic, hidden for combs) ===
        self.shape_frame = ttk.LabelFrame(main_frame, text="Shape Parameters", padding=5)
        self.shape_frame.grid(row=3, column=0, columnspan=3, sticky="ew", padx=5, pady=5)
        self.shape_param_vars = []
        self.shape_param_widgets = []
        
        # === Frequency Comb Frame ===
        self.comb_frame = ttk.LabelFrame(main_frame, text="Frequency Comb Settings", padding=5)
        self.comb_frame.grid(row=4, column=0, columnspan=3, sticky="ew", padx=5, pady=10)
        
        # Frequency input mode
        ttk.Label(self.comb_frame, text="Frequency Input:").grid(row=0, column=0, sticky="e", padx=5, pady=3)
        self.freq_mode_var = tk.StringVar(value="range")
        ttk.Radiobutton(self.comb_frame, text="Range (start:step:stop)", variable=self.freq_mode_var, 
                       value="range", command=self._on_freq_mode_change).grid(row=0, column=1, sticky="w", padx=5)
        ttk.Radiobutton(self.comb_frame, text="List", variable=self.freq_mode_var,
                       value="list", command=self._on_freq_mode_change).grid(row=0, column=2, sticky="w", padx=5)
        
        # Range inputs
        self.range_frame = ttk.Frame(self.comb_frame)
        self.range_frame.grid(row=1, column=0, columnspan=3, sticky="ew", pady=5)
        
        ttk.Label(self.range_frame, text="Start (Hz):").grid(row=0, column=0, padx=5)
        self.start_freq_var = tk.StringVar(value="1")
        ttk.Entry(self.range_frame, textvariable=self.start_freq_var, width=10).grid(row=0, column=1, padx=5)
        
        ttk.Label(self.range_frame, text="Stop (Hz):").grid(row=0, column=2, padx=5)
        self.stop_freq_var = tk.StringVar(value="10")
        ttk.Entry(self.range_frame, textvariable=self.stop_freq_var, width=10).grid(row=0, column=3, padx=5)
        
        ttk.Label(self.range_frame, text="Step (Hz):").grid(row=0, column=4, padx=5)
        self.step_freq_var = tk.StringVar(value="1")
        ttk.Entry(self.range_frame, textvariable=self.step_freq_var, width=10).grid(row=0, column=5, padx=5)
        
        # List input
        self.list_frame = ttk.Frame(self.comb_frame)
        self.list_frame.grid(row=2, column=0, columnspan=3, sticky="ew", pady=5)
        
        ttk.Label(self.list_frame, text="Frequencies (Hz, comma-separated):").grid(row=0, column=0, padx=5, sticky="w")
        self.freq_list_var = tk.StringVar(value="1, 2, 3, 4, 5, 6, 7, 8, 9, 10")
        ttk.Entry(self.list_frame, textvariable=self.freq_list_var, width=40).grid(row=1, column=0, padx=5, sticky="ew")
        self.list_frame.grid_remove()  # Hidden by default
        
        # Phase options
        ttk.Label(self.comb_frame, text="Phases:").grid(row=3, column=0, sticky="e", padx=5, pady=3)
        self.phase_mode_var = tk.StringVar(value="random")
        ttk.Radiobutton(self.comb_frame, text="Random (Monte Carlo optimized)", 
                       variable=self.phase_mode_var, value="random").grid(row=3, column=1, sticky="w", padx=5)
        ttk.Radiobutton(self.comb_frame, text="Zero (all in phase)", 
                       variable=self.phase_mode_var, value="zero").grid(row=3, column=2, sticky="w", padx=5)
        
        # Monte Carlo iterations
        ttk.Label(self.comb_frame, text="Monte Carlo iterations:").grid(row=4, column=0, sticky="e", padx=5, pady=3)
        self.mc_iter_var = tk.StringVar(value="1000")
        ttk.Entry(self.comb_frame, textvariable=self.mc_iter_var, width=10).grid(row=4, column=1, sticky="w", padx=5)
        
        # Preview/calculate button for comb
        ttk.Button(self.comb_frame, text="Preview Points",
                   command=self._update_info).grid(row=5, column=0, columnspan=3, pady=5)
        
        # Hide comb frame by default
        self.comb_frame.grid_remove()
        
        # === Info / Warning Display ===
        self.info_frame = ttk.LabelFrame(main_frame, text="Waveform Info", padding=5)
        self.info_frame.grid(row=5, column=0, columnspan=3, sticky="ew", padx=5, pady=5)
        
        self.info_var = tk.StringVar(value="")
        self.info_label = ttk.Label(self.info_frame, textvariable=self.info_var,
                                    justify="left", wraplength=500)
        self.info_label.pack(fill="x", padx=5, pady=3)
        
        self.warning_var = tk.StringVar(value="")
        self.warning_label = ttk.Label(self.info_frame, textvariable=self.warning_var,
                                       foreground="red", justify="left", wraplength=500)
        self.warning_label.pack(fill="x", padx=5, pady=3)
        
        # Buttons
        btn_frame = ttk.Frame(main_frame)
        btn_frame.grid(row=6, column=0, columnspan=3, pady=10)
        
        ttk.Button(btn_frame, text="Generate", command=self._generate).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Cancel", command=self.destroy).pack(side="left", padx=5)
    
    def _on_type_change(self, event=None):
        """Handle waveform type change."""
        wf_type = self.type_var.get()
        if wf_type == "frequency_comb":
            self.wave_props_frame.grid_remove()
            self.shape_frame.grid_remove()
            self.comb_frame.grid()
        else:
            self.wave_props_frame.grid()
            self.shape_frame.grid()
            self.comb_frame.grid_remove()
            self._trap_pulse_override = False
            self._rebuild_shape_params()
        self._update_info()
    
    def _on_polarity_change(self):
        """Handle polarity toggle — convert freq/time entry to keep output freq constant."""
        if self.drive_mode_var.get() == "time":
            try:
                val = float(self.freq_time_var.get())
                unit_scale = self.TIME_UNITS[self.freq_time_unit_var.get()]
                old_pol = self._last_polarity
                new_pol = self.polarity_var.get()
                if old_pol == "unipolar" and new_pol == "bipolar":
                    self.freq_time_var.set(f"{val / 2:.6g}")
                elif old_pol == "bipolar" and new_pol == "unipolar":
                    self.freq_time_var.set(f"{val * 2:.6g}")
            except (ValueError, ZeroDivisionError):
                pass
        self._last_polarity = self.polarity_var.get()
        self._update_freq_controls()
        self._rebuild_shape_params()
        self._update_info()
    
    def _on_drive_mode_change(self):
        """Handle drive mode toggle — convert between frequency and period."""
        old_mode = self._last_drive_mode
        new_mode = self.drive_mode_var.get()
        try:
            val = float(self.freq_time_var.get())
            old_unit = self.freq_time_unit_var.get()
            if val > 0:
                if old_mode == "frequency" and new_mode == "time":
                    freq_hz = val * self.FREQ_UNITS[old_unit]
                    pol = self.polarity_var.get()
                    period = 1.0 / freq_hz
                    if pol == "bipolar":
                        period /= 2.0
                    disp, unit = self._best_time_unit(period)
                    self.freq_time_var.set(f"{disp:.6g}")
                    self.freq_time_unit_var.set(unit)
                elif old_mode == "time" and new_mode == "frequency":
                    period_s = val * self.TIME_UNITS[old_unit]
                    pol = self.polarity_var.get()
                    if pol == "bipolar":
                        freq = 1.0 / (2.0 * period_s)
                    else:
                        freq = 1.0 / period_s
                    disp, unit = self._best_freq_unit(freq)
                    self.freq_time_var.set(f"{disp:.6g}")
                    self.freq_time_unit_var.set(unit)
        except (ValueError, ZeroDivisionError):
            pass
        self._last_drive_mode = new_mode
        self._update_freq_controls()
        self._update_info()
    
    def _update_freq_controls(self):
        """Update the frequency/period label and unit dropdown based on drive mode & polarity."""
        mode = self.drive_mode_var.get()
        pol = self.polarity_var.get()
        if mode == "frequency":
            self.freq_time_label.config(text="Frequency:")
            self.freq_time_unit.config(values=["Hz", "kHz", "MHz"])
            if self.freq_time_unit_var.get() not in ("Hz", "kHz", "MHz"):
                self.freq_time_unit_var.set("Hz")
        else:
            if pol == "unipolar":
                self.freq_time_label.config(text="Period:")
            else:
                self.freq_time_label.config(text="Half Period:")
            self.freq_time_unit.config(values=["µs", "ms", "s"])
            if self.freq_time_unit_var.get() not in ("µs", "ms", "s"):
                self.freq_time_unit_var.set("ms")
    
    def _rebuild_shape_params(self):
        """Rebuild the shape parameter widgets for the current waveform type."""
        for widget in self.shape_param_widgets:
            widget.destroy()
        self.shape_param_widgets.clear()
        self.shape_param_vars.clear()
        self._shape_param_unit_vars = []
        
        wf_type = self.type_var.get()
        if wf_type == "frequency_comb":
            return
        
        params = self.SHAPE_PARAMS.get(wf_type, [])
        time_defaults = self._get_time_defaults(wf_type)
        time_idx = 0
        row = 0
        
        # For trapezoid: add "Specify Pulse Time" checkbox before the params
        if wf_type == "trapezoid":
            self._trap_override_var = tk.BooleanVar(value=self._trap_pulse_override)
            chk = ttk.Checkbutton(self.shape_frame, text="Specify Pulse Time",
                                  variable=self._trap_override_var,
                                  command=self._on_trap_override_toggle)
            chk.grid(row=0, column=0, columnspan=3, sticky="w", padx=5, pady=3)
            self.shape_param_widgets.append(chk)
            row = 1
        
        for i, (label_text, ptype, default_val) in enumerate(params):
            lbl = ttk.Label(self.shape_frame, text=f"{label_text}:")
            lbl.grid(row=row + i, column=0, sticky="e", padx=5, pady=3)
            
            param_frame = ttk.Frame(self.shape_frame)
            param_frame.grid(row=row + i, column=1, columnspan=2, sticky="w", padx=5, pady=3)
            
            if ptype == "time":
                if default_val is None:
                    val_s = time_defaults[time_idx] if time_idx < len(time_defaults) else 0
                    disp, unit = self._best_time_unit(val_s)
                    time_idx += 1
                else:
                    disp = float(default_val)
                    unit = "s"
                var = tk.StringVar(value=f"{disp:.6g}")
                ent = ttk.Entry(param_frame, textvariable=var, width=12)
                ent.pack(side="left")
                unit_var = tk.StringVar(value=unit)
                unit_cb = ttk.Combobox(param_frame, textvariable=unit_var,
                                       state="readonly", width=4,
                                       values=["µs", "ms", "s"])
                unit_cb.pack(side="left", padx=(3, 0))
                unit_cb.bind("<<ComboboxSelected>>", lambda e: self._update_info())
                self._shape_param_unit_vars.append(unit_var)
                self.shape_param_widgets.extend([lbl, param_frame])
            else:
                if default_val is None:
                    default_val = "0"
                var = tk.StringVar(value=default_val)
                ent = ttk.Entry(param_frame, textvariable=var, width=12)
                ent.pack(side="left")
                self._shape_param_unit_vars.append(None)  # no unit
                self.shape_param_widgets.extend([lbl, param_frame])
            
            ent.bind("<KeyRelease>", lambda e: self._update_info())
            self.shape_param_vars.append(var)
            
            # Trapezoid: disable pulse time entry when not overridden
            if wf_type == "trapezoid" and label_text == "Pulse Time":
                self._trap_pulse_entry = ent
                self._trap_pulse_idx = len(self.shape_param_vars) - 1
                if not self._trap_pulse_override:
                    ent.config(state="disabled")
    
    def _on_trap_override_toggle(self):
        """Toggle trapezoid pulse time override."""
        self._trap_pulse_override = self._trap_override_var.get()
        if hasattr(self, '_trap_pulse_entry'):
            if self._trap_pulse_override:
                self._trap_pulse_entry.config(state="normal")
            else:
                self._trap_pulse_entry.config(state="disabled")
                # Recompute auto pulse time
                self._update_trap_auto_pulse()
        self._update_info()
    
    def _update_trap_auto_pulse(self):
        """Auto-compute trapezoid pulse time = shape_period - rise - fall."""
        try:
            freq = self._get_output_frequency()
            period = 1.0 / freq
            pol = self.polarity_var.get()
            shape_period = period / 2 if pol == "bipolar" else period
            
            params_s = self._get_shape_params_seconds()
            rise_s = params_s[0]
            fall_s = params_s[2]
            pulse_s = max(0, shape_period - rise_s - fall_s)
            
            disp, unit = self._best_time_unit(pulse_s)
            self.shape_param_vars[self._trap_pulse_idx].set(f"{disp:.6g}")
            self._shape_param_unit_vars[self._trap_pulse_idx].set(unit)
        except (ValueError, ZeroDivisionError, IndexError):
            pass
    
    def _get_time_defaults(self, wf_type):
        """Compute default time-based parameter values from the current period (in seconds)."""
        try:
            freq = self._get_output_frequency()
            period = 1.0 / freq
        except (ValueError, ZeroDivisionError):
            period = 1e-3
        if self.polarity_var.get() == "bipolar":
            period = period / 2
        return {
            "square":      [period / 2],
            "ramp":        [period],
            "trapezoid":   [period * 0.2, period * 0.6, period * 0.2],
            "pulse":       [period * 0.1, period * 0.05, period * 0.05],
            "exponential": [period * 0.2],
            "gaussian":    [period * 0.3],
        }.get(wf_type, [])
    
    def _get_shape_params(self):
        """Get the current shape parameter values as raw display numbers."""
        return [float(var.get()) for var in self.shape_param_vars]
    
    def _get_shape_params_seconds(self):
        """Get all shape params converted to base units (seconds for time, raw for plain)."""
        result = []
        for var, unit_var in zip(self.shape_param_vars, self._shape_param_unit_vars):
            val = float(var.get())
            if unit_var is not None:
                val *= self.TIME_UNITS[unit_var.get()]
            result.append(val)
        return result
    
    def _get_output_frequency(self):
        """Derive the output frequency in Hz from the dialog's frequency/period controls."""
        val = float(self.freq_time_var.get())
        if val <= 0:
            raise ValueError("Frequency/period must be positive")
        if self.drive_mode_var.get() == "frequency":
            return val * self.FREQ_UNITS[self.freq_time_unit_var.get()]
        else:
            period_s = val * self.TIME_UNITS[self.freq_time_unit_var.get()]
            if self.polarity_var.get() == "unipolar":
                return 1.0 / period_s
            else:
                return 1.0 / (2.0 * period_s)
    
    def _on_freq_mode_change(self):
        """Handle frequency input mode change."""
        if self.freq_mode_var.get() == "range":
            self.range_frame.grid()
            self.list_frame.grid_remove()
        else:
            self.range_frame.grid_remove()
            self.list_frame.grid()
    
    def _get_comb_frequencies(self):
        """Parse comb frequency inputs and return list of floats."""
        if self.freq_mode_var.get() == "range":
            start = float(self.start_freq_var.get())
            stop = float(self.stop_freq_var.get())
            step = float(self.step_freq_var.get())
            return list(np.arange(start, stop + step / 2, step))
        else:
            return [float(f.strip()) for f in self.freq_list_var.get().split(",") if f.strip()]
    
    def _update_info(self):
        """Update the info/warning display based on current settings."""
        try:
            wf_type = self.type_var.get()
            if wf_type == "frequency_comb":
                freqs = self._get_comb_frequencies()
                if not freqs:
                    self.info_var.set("No frequencies specified.")
                    self.warning_var.set("")
                    return
                num_pts, info = compute_optimal_points_for_comb(freqs)
                self.info_var.set(
                    f"Fundamental: {info['fundamental']:.4g} Hz | "
                    f"Highest tone: {info['f_max']:.4g} Hz\n"
                    f"Harmonics in period: {info['harmonics']:.1f} cycles | "
                    f"Min points needed: {info['min_points_needed']}\n"
                    f"Optimal points: {num_pts} | "
                    f"Sample rate: {info['sample_rate']/1e3:.1f} kSa/s"
                )
                self.warning_var.set(info.get('warning') or "")
            else:
                freq = self._get_output_frequency()
                num_pts = compute_optimal_points(freq)
                sr = freq * num_pts
                info = check_frequency_feasibility(freq, num_pts)
                pol = self.polarity_var.get()
                mode = self.drive_mode_var.get()
                period = 1.0 / freq
                shape_period = period / 2 if pol == "bipolar" else period
                lines = [
                    f"Polarity: {pol} | Mode: {mode}",
                    f"Output frequency: {freq:.4g} Hz | Period: {period*1e3:.4g} ms",
                ]
                if pol == "bipolar":
                    lines.append(f"Shape half-period: {shape_period*1e3:.4g} ms")
                lines.append(
                    f"Optimal points: {num_pts} | "
                    f"Sample rate: {sr/1e3:.1f} kSa/s"
                )
                # Auto-update trapezoid pulse time when not overridden
                if wf_type == "trapezoid" and not self._trap_pulse_override:
                    self._update_trap_auto_pulse()
                    
                self.info_var.set("\n".join(lines))
                self.warning_var.set(info.get('warning') or "")
        except (ValueError, ZeroDivisionError) as e:
            self.info_var.set(f"Cannot compute: {e}")
            self.warning_var.set("")
    
    def _generate(self):
        """Generate the waveform with auto-optimal points."""
        try:
            wf_type = self.type_var.get()
            
            self.waveform_type = wf_type
            
            if wf_type == "frequency_comb":
                self.result = self._generate_frequency_comb()
            else:
                # Get output frequency from dialog controls
                output_freq = self._get_output_frequency()
                points = compute_optimal_points(output_freq)
                info = check_frequency_feasibility(output_freq, points)
                if info.get('warning'):
                    if not messagebox.askyesno("Warning", 
                            f"{info['warning']}\n\nContinue anyway?"):
                        return
                
                polarity = self.polarity_var.get()
                params = self._get_shape_params_seconds()
                
                # For bipolar: generate unipolar shape at half the points
                gen_points = points // 2 if polarity == "bipolar" else points
                gen_points = max(gen_points, DG822_MIN_POINTS)
                
                # Convert time-based params to percentages for WaveformGenerator
                period = 1.0 / output_freq
                shape_period = period / 2 if polarity == "bipolar" else period
                
                if wf_type == "square":
                    duty = params[0] / shape_period * 100
                    result = WaveformGenerator.square(gen_points, duty)
                elif wf_type == "sine":
                    result = WaveformGenerator.sine(gen_points, params[0])
                elif wf_type == "ramp":
                    symmetry = params[0] / shape_period * 100
                    result = WaveformGenerator.ramp(gen_points, symmetry)
                elif wf_type == "trapezoid":
                    rise_s = params[0]
                    pulse_s = params[1]
                    fall_s = params[2]
                    total_s = rise_s + pulse_s + fall_s
                    
                    # If overriding pulse and sum exceeds period, warn and default
                    if self._trap_pulse_override and total_s > shape_period * 1.001:
                        auto_pulse = max(0, shape_period - rise_s - fall_s)
                        if not messagebox.askyesno("Warning",
                                f"Rise + Pulse + Fall = {total_s*1e3:.4g} ms "
                                f"exceeds shape period = {shape_period*1e3:.4g} ms.\n\n"
                                f"Default pulse time to {auto_pulse*1e3:.4g} ms?"):
                            return
                        pulse_s = auto_pulse
                        total_s = rise_s + pulse_s + fall_s
                    
                    r_pct = rise_s / shape_period * 100
                    p_pct = pulse_s / shape_period * 100
                    f_pct = fall_s / shape_period * 100
                    result = WaveformGenerator.trapezoid(gen_points, r_pct, p_pct, f_pct)
                elif wf_type == "pulse":
                    w_pct = params[0] / shape_period * 100
                    r_pct = params[1] / shape_period * 100
                    f_pct = params[2] / shape_period * 100
                    result = WaveformGenerator.pulse(gen_points, w_pct, r_pct, f_pct)
                elif wf_type == "sinc":
                    result = WaveformGenerator.sinc(gen_points, int(params[0]))
                elif wf_type == "exponential":
                    tau_pct = params[0] / shape_period * 100
                    result = WaveformGenerator.exponential_decay(gen_points, tau_pct)
                elif wf_type == "gaussian":
                    sigma_pct = params[0] / shape_period * 100
                    result = WaveformGenerator.gaussian(gen_points, sigma_pct)
                else:
                    messagebox.showerror("Error", f"Unknown waveform type: {wf_type}")
                    return
                
                # Apply bipolar transform if needed
                if polarity == "bipolar":
                    result = WaveformGenerator.make_bipolar(result, total_points=points)
                
                self.result = result
                self.dialog_output_frequency = output_freq
            
            if self.result is not None:
                self.destroy()
            
        except ValueError as e:
            messagebox.showerror("Error", f"Invalid parameter: {e}")
    
    def _generate_frequency_comb(self):
        """Generate frequency comb with auto-optimal points."""
        freqs = self._get_comb_frequencies()
        if not freqs:
            messagebox.showerror("Error", "No frequencies specified.")
            return None
        
        # Compute optimal points and check feasibility
        num_pts, info = compute_optimal_points_for_comb(freqs)
        
        if info.get('warning'):
            if not messagebox.askyesno("Warning",
                    f"{info['warning']}\n\n"
                    f"Will use {num_pts} points.\nContinue anyway?"):
                return None
        
        # Get phase options
        random_phases = self.phase_mode_var.get() == "random"
        mc_iterations = int(self.mc_iter_var.get()) if random_phases else 1
        
        # Show progress message for Monte Carlo
        if random_phases:
            self.update()
            self.title("Generating... (Monte Carlo optimization)")
        
        return WaveformGenerator.frequency_comb(
            frequencies=freqs,
            num_points=num_pts,
            random_phases=random_phases,
            monte_carlo_iterations=mc_iterations
        )


class PresetsFrame(ttk.LabelFrame):
    """Frame for preset configurations."""
    
    PRESETS = {
        "1kHz Sine 1Vpp": {"waveform": "Sine", "freq": 1000, "amp": 1.0, "offset": 0, "phase": 0},
        "1kHz Sine 5Vpp": {"waveform": "Sine", "freq": 1000, "amp": 5.0, "offset": 0, "phase": 0},
        "10kHz Square 3.3V": {"waveform": "Square", "freq": 10000, "amp": 3.3, "offset": 1.65, "phase": 0, "duty": 50},
        "1MHz Sine 1Vpp": {"waveform": "Sine", "freq": 1000000, "amp": 1.0, "offset": 0, "phase": 0},
        "100Hz Ramp 5Vpp": {"waveform": "Ramp", "freq": 100, "amp": 5.0, "offset": 0, "phase": 0, "symm": 100},
        "DC 3.3V": {"waveform": "DC", "freq": 1000, "amp": 5.0, "offset": 3.3, "phase": 0},
    }
    
    def __init__(self, parent, channel_frames: List[ChannelFrame]):
        super().__init__(parent, text="Quick Presets", padding=10)
        
        self.channel_frames = channel_frames
        self._create_widgets()
    
    def _create_widgets(self):
        # Channel selection for preset
        ttk.Label(self, text="Apply to:").grid(row=0, column=0, padx=5, pady=5)
        
        self.channel_var = tk.StringVar(value="CH1")
        ttk.Radiobutton(self, text="CH1", variable=self.channel_var, value="CH1").grid(row=0, column=1, padx=5)
        ttk.Radiobutton(self, text="CH2", variable=self.channel_var, value="CH2").grid(row=0, column=2, padx=5)
        ttk.Radiobutton(self, text="Both", variable=self.channel_var, value="Both").grid(row=0, column=3, padx=5)
        
        # Preset buttons
        btn_frame = ttk.Frame(self)
        btn_frame.grid(row=1, column=0, columnspan=4, sticky="ew", pady=5)
        
        for i, (name, settings) in enumerate(self.PRESETS.items()):
            btn = ttk.Button(
                btn_frame, text=name, width=18,
                command=lambda s=settings: self._apply_preset(s)
            )
            btn.grid(row=i // 3, column=i % 3, padx=5, pady=3)
    
    def _apply_preset(self, settings: dict):
        """Apply a preset to selected channel(s)."""
        channels = []
        if self.channel_var.get() == "CH1":
            channels = [0]
        elif self.channel_var.get() == "CH2":
            channels = [1]
        else:
            channels = [0, 1]
        
        for ch_idx in channels:
            frame = self.channel_frames[ch_idx]
            
            frame.waveform_var.set(settings["waveform"])
            frame._on_waveform_change()
            
            freq = settings["freq"]
            if freq >= 1000000:
                frame.freq_var.set(f"{freq/1000000:.6g}")
                frame.freq_unit_var.set("MHz")
            elif freq >= 1000:
                frame.freq_var.set(f"{freq/1000:.6g}")
                frame.freq_unit_var.set("kHz")
            else:
                frame.freq_var.set(f"{freq:.6g}")
                frame.freq_unit_var.set("Hz")
            
            frame.amp_var.set(str(settings["amp"]))
            frame.offset_var.set(str(settings["offset"]))
            frame.phase_var.set(str(settings["phase"]))
            
            if "duty" in settings:
                frame.duty_var.set(str(settings["duty"]))
            if "symm" in settings:
                frame.symm_var.set(str(settings["symm"]))
            
            frame._apply_settings()


class StatusBar(ttk.Frame):
    """Status bar at bottom of window."""
    
    def __init__(self, parent):
        super().__init__(parent)
        
        self.status_label = ttk.Label(self, text="Ready", anchor="w")
        self.status_label.pack(side="left", fill="x", expand=True, padx=5)
        
        self.idn_label = ttk.Label(self, text="", anchor="e")
        self.idn_label.pack(side="right", padx=5)
    
    def set_status(self, text: str):
        """Set status message."""
        self.status_label.config(text=text)
    
    def set_idn(self, idn: str):
        """Set instrument identification."""
        self.idn_label.config(text=idn)


class DG822GUI(tk.Tk):
    """Main GUI application for DG822 control."""
    
    def __init__(self):
        super().__init__()
        
        self.title("RIGOL DG822 Controller")
        self.geometry("800x700")
        self.minsize(700, 600)
        
        self.controller: Optional[DG822Controller] = None
        
        self._create_widgets()
        self._setup_bindings()
        
        # Disable channel controls until connected
        for frame in self.channel_frames:
            frame.set_enabled(False)
    
    def _create_widgets(self):
        # Main container with padding
        main_frame = ttk.Frame(self, padding=10)
        main_frame.pack(fill="both", expand=True)
        
        # Connection frame
        self.connection_frame = ConnectionFrame(
            main_frame, self._on_connect, self._on_disconnect
        )
        self.connection_frame.pack(fill="x", pady=(0, 10))
        
        # Channel frames in a notebook (tabs)
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill="both", expand=True, pady=(0, 10))
        
        self.channel_frames = []
        for ch in [1, 2]:
            frame = ChannelFrame(self.notebook, ch, lambda: self.controller)
            self.notebook.add(frame, text=f"Channel {ch}")
            self.channel_frames.append(frame)
        
        # Presets frame
        self.presets_frame = PresetsFrame(main_frame, self.channel_frames)
        self.presets_frame.pack(fill="x", pady=(0, 10))
        
        # Status bar
        self.status_bar = StatusBar(main_frame)
        self.status_bar.pack(fill="x", side="bottom")
    
    def _setup_bindings(self):
        """Setup keyboard bindings."""
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.bind("<Control-q>", lambda e: self._on_close())
    
    def _on_connect(self, resource: str) -> bool:
        """Handle connection request."""
        self.status_bar.set_status("Connecting...")
        self.update()
        
        self.controller = DG822Controller()
        
        if self.controller.connect(resource):
            self.status_bar.set_status("Connected")
            self.status_bar.set_idn(self.controller.idn or "")
            
            # Enable channel controls
            for frame in self.channel_frames:
                frame.set_enabled(True)
                frame._refresh_status()
            
            return True
        else:
            self.controller = None
            self.status_bar.set_status("Connection failed")
            return False
    
    def _on_disconnect(self):
        """Handle disconnection."""
        if self.controller:
            self.controller.disconnect()
            self.controller.connection.close()
            self.controller = None
        
        # Disable channel controls
        for frame in self.channel_frames:
            frame.set_enabled(False)
        
        self.status_bar.set_status("Disconnected")
        self.status_bar.set_idn("")
    
    def _on_close(self):
        """Handle window close."""
        if self.controller:
            self._on_disconnect()
        self.destroy()


def main():
    """Main entry point."""
    app = DG822GUI()
    app.mainloop()


if __name__ == "__main__":
    main()
