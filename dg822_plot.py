"""
RIGOL DG822 Waveform Generator - Plot Module

This module provides waveform visualization for the DG822 controller.
It can generate preview plots of waveforms based on parameters or
display arbitrary waveform data.

Author: Auto-generated
Date: 2026-01-09
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from typing import Optional, Tuple, List, Union
import tkinter as tk


class WaveformPlotter:
    """
    Generates and displays waveform plots.
    
    This class can:
    - Generate mathematical waveforms (sine, square, pulse, ramp, noise, DC)
    - Plot arbitrary waveform data
    - Embed plots in tkinter widgets
    - Annotate plots with frequency, amplitude, etc.
    """
    
    # Number of points for plotting
    PLOT_POINTS = 1000
    CYCLES_TO_SHOW = 3  # Number of waveform cycles to display
    
    def __init__(self):
        """Initialize the plotter."""
        self.fig: Optional[Figure] = None
        self.ax = None
        self.canvas = None
    
    @staticmethod
    def generate_sine(frequency: float, amplitude: float, offset: float,
                      phase: float, num_points: int = 1000,
                      num_cycles: int = 3) -> Tuple[np.ndarray, np.ndarray]:
        """
        Generate sine wave data.
        
        Args:
            frequency: Frequency in Hz
            amplitude: Peak-to-peak amplitude in V
            offset: DC offset in V
            phase: Phase in degrees
            num_points: Number of points to generate
            num_cycles: Number of cycles to show
            
        Returns:
            Tuple of (time_array, voltage_array)
        """
        period = 1.0 / frequency
        t = np.linspace(0, num_cycles * period, num_points)
        phase_rad = np.deg2rad(phase)
        v = (amplitude / 2) * np.sin(2 * np.pi * frequency * t + phase_rad) + offset
        return t, v
    
    @staticmethod
    def generate_square(frequency: float, amplitude: float, offset: float,
                        phase: float, duty_cycle: float = 50.0,
                        num_points: int = 1000, num_cycles: int = 3) -> Tuple[np.ndarray, np.ndarray]:
        """
        Generate square wave data.
        
        Args:
            frequency: Frequency in Hz
            amplitude: Peak-to-peak amplitude in V
            offset: DC offset in V
            phase: Phase in degrees
            duty_cycle: Duty cycle in percent (0-100)
            num_points: Number of points to generate
            num_cycles: Number of cycles to show
            
        Returns:
            Tuple of (time_array, voltage_array)
        """
        from scipy import signal
        
        period = 1.0 / frequency
        t = np.linspace(0, num_cycles * period, num_points)
        phase_rad = np.deg2rad(phase)
        
        # Generate square wave using scipy
        duty = duty_cycle / 100.0
        v = (amplitude / 2) * signal.square(2 * np.pi * frequency * t + phase_rad, duty=duty) + offset
        return t, v
    
    @staticmethod
    def generate_pulse(frequency: float, amplitude: float, offset: float,
                       phase: float, duty_cycle: float = 50.0,
                       rise_time: Optional[float] = None,
                       fall_time: Optional[float] = None,
                       num_points: int = 1000, num_cycles: int = 3,
                       centered: bool = True) -> Tuple[np.ndarray, np.ndarray]:
        """
        Generate pulse wave data with optional rise/fall times.
        
        The pulse is centered in each cycle by default.
        
        Args:
            frequency: Frequency in Hz
            amplitude: Peak-to-peak amplitude in V
            offset: DC offset in V
            phase: Phase in degrees
            duty_cycle: Duty cycle in percent
            rise_time: Rise time in seconds (None for ideal)
            fall_time: Fall time in seconds (None for ideal)
            num_points: Number of points to generate
            num_cycles: Number of cycles to show
            centered: If True, center the pulse in each cycle
            
        Returns:
            Tuple of (time_array, voltage_array)
        """
        period = 1.0 / frequency
        t = np.linspace(0, num_cycles * period, num_points)
        
        # Calculate pulse timing
        duty = duty_cycle / 100.0
        pulse_width = period * duty
        
        if centered:
            # Center the pulse: start at (period - pulse_width) / 2
            pulse_start = (period - pulse_width) / 2.0
        else:
            # Phase offset for non-centered pulse
            pulse_start = (phase / 360.0) * period
        
        pulse_end = pulse_start + pulse_width
        
        # Generate centered pulse waveform
        v = np.zeros_like(t)
        high_level = (amplitude / 2) + offset
        low_level = -(amplitude / 2) + offset
        
        for i, time in enumerate(t):
            # Get position within current cycle
            cycle_pos = time % period
            if pulse_start <= cycle_pos < pulse_end:
                v[i] = high_level
            else:
                v[i] = low_level
        
        return t, v
    
    @staticmethod
    def generate_ramp(frequency: float, amplitude: float, offset: float,
                      phase: float, symmetry: float = 50.0,
                      num_points: int = 1000, num_cycles: int = 3) -> Tuple[np.ndarray, np.ndarray]:
        """
        Generate ramp/triangle wave data.
        
        Args:
            frequency: Frequency in Hz
            amplitude: Peak-to-peak amplitude in V
            offset: DC offset in V
            phase: Phase in degrees
            symmetry: Symmetry in percent (0=falling, 50=triangle, 100=rising)
            num_points: Number of points to generate
            num_cycles: Number of cycles to show
            
        Returns:
            Tuple of (time_array, voltage_array)
        """
        from scipy import signal
        
        period = 1.0 / frequency
        t = np.linspace(0, num_cycles * period, num_points)
        phase_rad = np.deg2rad(phase)
        
        # Sawtooth width: 0=falling, 0.5=triangle, 1=rising
        width = symmetry / 100.0
        v = (amplitude / 2) * signal.sawtooth(2 * np.pi * frequency * t + phase_rad, width=width) + offset
        return t, v
    
    @staticmethod
    def generate_noise(amplitude: float, offset: float,
                       num_points: int = 1000, duration: float = 0.01) -> Tuple[np.ndarray, np.ndarray]:
        """
        Generate noise data.
        
        Args:
            amplitude: Peak-to-peak amplitude in V
            offset: DC offset in V
            num_points: Number of points to generate
            duration: Time duration in seconds
            
        Returns:
            Tuple of (time_array, voltage_array)
        """
        t = np.linspace(0, duration, num_points)
        # Generate gaussian noise scaled to approximate Vpp
        v = (amplitude / 6) * np.random.randn(num_points) + offset  # ~99.7% within Vpp
        return t, v
    
    @staticmethod
    def generate_dc(voltage: float, num_points: int = 1000,
                    duration: float = 0.01) -> Tuple[np.ndarray, np.ndarray]:
        """
        Generate DC level data.
        
        Args:
            voltage: DC voltage level
            num_points: Number of points to generate
            duration: Time duration in seconds
            
        Returns:
            Tuple of (time_array, voltage_array)
        """
        t = np.linspace(0, duration, num_points)
        v = np.full(num_points, voltage)
        return t, v
    
    @staticmethod
    def generate_arbitrary(data: np.ndarray, frequency: float,
                           amplitude: float = 2.0, offset: float = 0.0,
                           num_cycles: int = 3) -> Tuple[np.ndarray, np.ndarray]:
        """
        Generate arbitrary waveform data by repeating the pattern.
        
        Args:
            data: Array of normalized values (-1 to +1, one cycle)
            frequency: Frequency in Hz
            amplitude: Peak-to-peak amplitude in V
            offset: DC offset in V
            num_cycles: Number of cycles to show
            
        Returns:
            Tuple of (time_array, voltage_array)
        """
        period = 1.0 / frequency
        # Tile the data for multiple cycles
        v_normalized = np.tile(data, num_cycles)
        # Scale by amplitude and add offset
        v = v_normalized * (amplitude / 2) + offset
        t = np.linspace(0, num_cycles * period, len(v))
        return t, v
    
    @staticmethod
    def format_time_axis(t: np.ndarray) -> Tuple[np.ndarray, str]:
        """
        Format time axis with appropriate units.
        
        Args:
            t: Time array in seconds
            
        Returns:
            Tuple of (scaled_time_array, unit_string)
        """
        max_t = np.max(t)
        
        if max_t < 1e-6:
            return t * 1e9, "ns"
        elif max_t < 1e-3:
            return t * 1e6, "µs"
        elif max_t < 1:
            return t * 1e3, "ms"
        else:
            return t, "s"
    
    @staticmethod
    def format_frequency(frequency: float) -> str:
        """Format frequency with appropriate units."""
        if frequency >= 1e6:
            return f"{frequency/1e6:.6g} MHz"
        elif frequency >= 1e3:
            return f"{frequency/1e3:.6g} kHz"
        else:
            return f"{frequency:.6g} Hz"
    
    def create_figure(self, figsize: Tuple[float, float] = (6, 3),
                      dpi: int = 100) -> Figure:
        """
        Create a matplotlib figure for plotting.
        
        Args:
            figsize: Figure size in inches (width, height)
            dpi: Dots per inch
            
        Returns:
            Matplotlib Figure object
        """
        self.fig = Figure(figsize=figsize, dpi=dpi)
        self.ax = self.fig.add_subplot(111)
        return self.fig
    
    def plot_data(self, t: np.ndarray, v: np.ndarray, title: str = "Waveform",
                  channel: int = 1, show_grid: bool = True) -> None:
        """
        Plot pre-generated waveform data directly.
        
        Args:
            t: Time array in seconds
            v: Voltage array
            title: Plot title
            channel: Channel number for color selection
            show_grid: Whether to show grid
        """
        if self.ax is None:
            self.create_figure()
        
        self.ax.clear()
        
        # Format time axis
        t_scaled, time_unit = self.format_time_axis(t)
        
        # Plot the waveform
        color = "#1f77b4" if channel == 1 else "#ff7f0e"  # Blue for CH1, Orange for CH2
        self.ax.plot(t_scaled, v, color=color, linewidth=1.5)
        
        # Configure axes
        self.ax.set_xlabel(f"Time ({time_unit})")
        self.ax.set_ylabel("Voltage (V)")
        self.ax.set_title(title)
        
        # Set y-axis limits with some margin
        v_min, v_max = np.min(v), np.max(v)
        v_range = v_max - v_min
        if v_range < 0.001:  # DC signal
            margin = 1.0
        else:
            margin = v_range * 0.1
        self.ax.set_ylim(v_min - margin, v_max + margin)
        
        if show_grid:
            self.ax.grid(True, linestyle='--', alpha=0.7)
        
        self.fig.tight_layout()
    
    def plot_waveform(self, waveform_type: str, frequency: float = 1000.0,
                      amplitude: float = 5.0, offset: float = 0.0,
                      phase: float = 0.0, duty_cycle: float = 50.0,
                      symmetry: float = 50.0, arb_data: Optional[np.ndarray] = None,
                      channel: int = 1, show_grid: bool = True,
                      show_annotations: bool = True) -> None:
        """
        Plot a waveform with annotations.
        
        Args:
            waveform_type: Type of waveform ("Sine", "Square", "Pulse", "Ramp", "Noise", "DC", "Arbitrary")
            frequency: Frequency in Hz
            amplitude: Amplitude in Vpp
            offset: DC offset in V
            phase: Phase in degrees
            duty_cycle: Duty cycle for Square/Pulse
            symmetry: Symmetry for Ramp
            arb_data: Arbitrary waveform data (for Arbitrary type)
            channel: Channel number for labeling
            show_grid: Whether to show grid
            show_annotations: Whether to show parameter annotations
        """
        if self.ax is None:
            self.create_figure()
        
        self.ax.clear()
        
        # Generate waveform data based on type
        wf_type = waveform_type.lower()
        
        if wf_type == "sine":
            t, v = self.generate_sine(frequency, amplitude, offset, phase)
        elif wf_type == "square":
            t, v = self.generate_square(frequency, amplitude, offset, phase, duty_cycle)
        elif wf_type == "pulse":
            t, v = self.generate_pulse(frequency, amplitude, offset, phase, duty_cycle)
        elif wf_type == "ramp":
            t, v = self.generate_ramp(frequency, amplitude, offset, phase, symmetry)
        elif wf_type == "noise":
            t, v = self.generate_noise(amplitude, offset)
        elif wf_type == "dc":
            t, v = self.generate_dc(offset)
        elif wf_type == "arbitrary" and arb_data is not None:
            t, v = self.generate_arbitrary(arb_data, frequency)
        else:
            # Default to sine
            t, v = self.generate_sine(frequency, amplitude, offset, phase)
        
        # Format time axis
        t_scaled, time_unit = self.format_time_axis(t)
        
        # Plot the waveform
        color = "#1f77b4" if channel == 1 else "#ff7f0e"  # Blue for CH1, Orange for CH2
        self.ax.plot(t_scaled, v, color=color, linewidth=1.5)
        
        # Configure axes
        self.ax.set_xlabel(f"Time ({time_unit})")
        self.ax.set_ylabel("Voltage (V)")
        self.ax.set_title(f"Channel {channel}: {waveform_type}")
        
        # Set y-axis limits with some margin
        v_min, v_max = np.min(v), np.max(v)
        margin = (v_max - v_min) * 0.1 if v_max != v_min else 0.5
        self.ax.set_ylim(v_min - margin, v_max + margin)
        
        if show_grid:
            self.ax.grid(True, linestyle='--', alpha=0.7)
        
        # Add annotations
        if show_annotations and wf_type not in ["noise", "dc"]:
            annotation_text = f"f = {self.format_frequency(frequency)}\n"
            annotation_text += f"Vpp = {amplitude:.3g} V\n"
            annotation_text += f"Offset = {offset:.3g} V\n"
            annotation_text += f"Phase = {phase:.1f}°"
            
            if wf_type in ["square", "pulse"]:
                annotation_text += f"\nDuty = {duty_cycle:.1f}%"
            elif wf_type == "ramp":
                annotation_text += f"\nSymm = {symmetry:.1f}%"
            
            self.ax.text(0.98, 0.98, annotation_text,
                        transform=self.ax.transAxes,
                        verticalalignment='top',
                        horizontalalignment='right',
                        fontsize=8,
                        bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
        elif show_annotations and wf_type == "dc":
            self.ax.text(0.98, 0.98, f"DC = {offset:.3g} V",
                        transform=self.ax.transAxes,
                        verticalalignment='top',
                        horizontalalignment='right',
                        fontsize=8,
                        bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
        
        self.fig.tight_layout()
    
    def embed_in_tkinter(self, parent: tk.Widget) -> FigureCanvasTkAgg:
        """
        Embed the figure in a tkinter widget.
        
        Args:
            parent: Parent tkinter widget
            
        Returns:
            FigureCanvasTkAgg object
        """
        if self.fig is None:
            self.create_figure()
        
        self.canvas = FigureCanvasTkAgg(self.fig, master=parent)
        self.canvas.draw()
        return self.canvas
    
    def update(self):
        """Update the canvas after changes."""
        if self.canvas:
            self.canvas.draw()
    
    def save(self, filename: str, dpi: int = 150):
        """
        Save the figure to a file.
        
        Args:
            filename: Output filename
            dpi: Resolution in dots per inch
        """
        if self.fig:
            self.fig.savefig(filename, dpi=dpi, bbox_inches='tight')


def plot_waveform_standalone(waveform_type: str, frequency: float = 1000.0,
                             amplitude: float = 5.0, offset: float = 0.0,
                             phase: float = 0.0, duty_cycle: float = 50.0,
                             symmetry: float = 50.0, channel: int = 1,
                             arb_data: Optional[np.ndarray] = None) -> None:
    """
    Convenience function to create and show a standalone waveform plot.
    
    Args:
        waveform_type: Type of waveform
        frequency: Frequency in Hz
        amplitude: Amplitude in Vpp
        offset: DC offset in V
        phase: Phase in degrees
        duty_cycle: Duty cycle for Square/Pulse
        symmetry: Symmetry for Ramp
        channel: Channel number
        arb_data: Arbitrary waveform data
    """
    plotter = WaveformPlotter()
    plotter.create_figure(figsize=(10, 5))
    plotter.plot_waveform(
        waveform_type, frequency, amplitude, offset, phase,
        duty_cycle, symmetry, arb_data, channel
    )
    plt.show()


# =============================================================================
# Module Test / Evaluation Mode
# =============================================================================
if __name__ == "__main__":
    print("=" * 60)
    print("DG822 Plot Module - Evaluation Mode")
    print("=" * 60)
    
    # Create a figure with multiple subplots to demonstrate all waveforms
    fig, axes = plt.subplots(3, 2, figsize=(12, 10))
    fig.suptitle("Waveform Types Demo", fontsize=14)
    
    plotter = WaveformPlotter()
    
    # Sine wave
    t, v = plotter.generate_sine(1000, 2.0, 0.5, 90)
    t_scaled, unit = plotter.format_time_axis(t)
    axes[0, 0].plot(t_scaled, v)
    axes[0, 0].set_title("Sine: 1kHz, 2Vpp, 0.5V offset, 90° phase")
    axes[0, 0].set_xlabel(f"Time ({unit})")
    axes[0, 0].set_ylabel("Voltage (V)")
    axes[0, 0].grid(True, linestyle='--', alpha=0.7)
    
    # Square wave
    t, v = plotter.generate_square(5000, 3.3, 0, 0, 25)
    t_scaled, unit = plotter.format_time_axis(t)
    axes[0, 1].plot(t_scaled, v, color='orange')
    axes[0, 1].set_title("Square: 5kHz, 3.3Vpp, 25% duty")
    axes[0, 1].set_xlabel(f"Time ({unit})")
    axes[0, 1].set_ylabel("Voltage (V)")
    axes[0, 1].grid(True, linestyle='--', alpha=0.7)
    
    # Ramp (sawtooth)
    t, v = plotter.generate_ramp(2000, 4.0, 0, 0, 100)
    t_scaled, unit = plotter.format_time_axis(t)
    axes[1, 0].plot(t_scaled, v, color='green')
    axes[1, 0].set_title("Ramp: 2kHz, 4Vpp, 100% symmetry (rising)")
    axes[1, 0].set_xlabel(f"Time ({unit})")
    axes[1, 0].set_ylabel("Voltage (V)")
    axes[1, 0].grid(True, linestyle='--', alpha=0.7)
    
    # Triangle
    t, v = plotter.generate_ramp(1000, 5.0, 0, 0, 50)
    t_scaled, unit = plotter.format_time_axis(t)
    axes[1, 1].plot(t_scaled, v, color='red')
    axes[1, 1].set_title("Triangle: 1kHz, 5Vpp, 50% symmetry")
    axes[1, 1].set_xlabel(f"Time ({unit})")
    axes[1, 1].set_ylabel("Voltage (V)")
    axes[1, 1].grid(True, linestyle='--', alpha=0.7)
    
    # Noise
    t, v = plotter.generate_noise(2.0, 0)
    t_scaled, unit = plotter.format_time_axis(t)
    axes[2, 0].plot(t_scaled, v, color='purple', linewidth=0.5)
    axes[2, 0].set_title("Noise: 2Vpp")
    axes[2, 0].set_xlabel(f"Time ({unit})")
    axes[2, 0].set_ylabel("Voltage (V)")
    axes[2, 0].grid(True, linestyle='--', alpha=0.7)
    
    # DC
    t, v = plotter.generate_dc(3.3)
    t_scaled, unit = plotter.format_time_axis(t)
    axes[2, 1].plot(t_scaled, v, color='brown')
    axes[2, 1].set_title("DC: 3.3V")
    axes[2, 1].set_xlabel(f"Time ({unit})")
    axes[2, 1].set_ylabel("Voltage (V)")
    axes[2, 1].set_ylim(0, 5)
    axes[2, 1].grid(True, linestyle='--', alpha=0.7)
    
    plt.tight_layout()
    plt.show()
    
    print("\n" + "=" * 60)
    print("Evaluation complete.")
    print("=" * 60)
