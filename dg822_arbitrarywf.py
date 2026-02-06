"""
RIGOL DG822 Waveform Generator - Arbitrary Waveform Module

This module provides tools for creating and managing arbitrary waveforms
for the RIGOL DG822 waveform generator. It can generate waveform data,
save/load waveform files, and upload waveforms to the instrument.

Author: Auto-generated
Date: 2026-01-09
"""

import numpy as np
from math import gcd
from functools import reduce
from typing import Optional, List, Tuple, Union
from pathlib import Path
import struct


# =============================================================================
# DG822 Hardware Constants
# =============================================================================
DG822_MIN_POINTS = 8
DG822_MAX_POINTS = 16384
DG822_MIN_SAMPLE_RATE = 2e3      # 2 kSa/s
DG822_MAX_SAMPLE_RATE = 30e6     # 30 MSa/s
# Minimum points per cycle of highest frequency for smooth waveform
MIN_POINTS_PER_CYCLE = 10


def compute_optimal_points(frequency: float) -> int:
    """
    Compute the optimal (maximum) number of waveform points for a given
    output frequency, maximizing smoothness within hardware limits.

    output_frequency = sample_rate / num_points
    => sample_rate = frequency * num_points
    => max num_points = DG822_MAX_SAMPLE_RATE / frequency  (capped at 16384)

    Args:
        frequency: Desired output frequency in Hz

    Returns:
        Optimal number of points (8–16384)
    """
    if frequency <= 0:
        return DG822_MAX_POINTS
    max_pts = int(DG822_MAX_SAMPLE_RATE / frequency)
    return max(DG822_MIN_POINTS, min(max_pts, DG822_MAX_POINTS))


def compute_optimal_points_for_comb(frequencies: List[float]) -> Tuple[int, dict]:
    """
    Compute the optimal number of waveform points for a frequency comb,
    ensuring the highest-frequency component is smoothly represented.

    The waveform period = 1 / fundamental, where fundamental ≈ GCD of all
    frequencies.  Within that period the highest comb tone completes
    f_max / f_fundamental cycles, each needing ≥ MIN_POINTS_PER_CYCLE
    points for smooth rendering.

    Args:
        frequencies: List of comb frequencies in Hz

    Returns:
        (num_points, info_dict) where info_dict contains:
            - 'fundamental': the fundamental frequency (Hz)
            - 'f_max': highest comb frequency (Hz)
            - 'harmonics': f_max / fundamental (cycles in one period)
            - 'min_points_needed': minimum points for smooth highest harmonic
            - 'max_points_available': max points before exceeding sample rate
            - 'sample_rate': resulting sample rate
            - 'warning': string warning or None
    """
    freqs = np.array(frequencies, dtype=float)
    if len(freqs) == 0:
        raise ValueError("No frequencies specified")
    if np.any(freqs <= 0):
        raise ValueError("All frequencies must be positive")

    fundamental = _approximate_gcd(freqs)
    f_max = np.max(freqs)
    harmonics = f_max / fundamental  # cycles of f_max per waveform period

    # Minimum points to represent highest harmonic smoothly
    min_points_needed = int(np.ceil(harmonics * MIN_POINTS_PER_CYCLE))

    # Maximum points before sample rate exceeds 30 MSa/s
    max_points_available = int(DG822_MAX_SAMPLE_RATE / fundamental)

    # Choose: as many points as possible, but capped at 16384
    optimal = min(max_points_available, DG822_MAX_POINTS)
    optimal = max(optimal, DG822_MIN_POINTS)

    warning = None
    if min_points_needed > DG822_MAX_POINTS:
        warning = (
            f"Frequency span too wide for smooth output.\n"
            f"The highest tone ({f_max:.4g} Hz) needs ~{min_points_needed} points "
            f"within a {fundamental:.4g} Hz fundamental period,\n"
            f"but the DG822 maximum is {DG822_MAX_POINTS}.\n"
            f"The highest harmonics will appear coarse/aliased.\n"
            f"Consider narrowing the frequency range or increasing the step size."
        )
    elif optimal < min_points_needed:
        warning = (
            f"Sample-rate limited: only {optimal} points achievable "
            f"(need {min_points_needed} for smooth output).\n"
            f"Highest harmonics may appear coarse."
        )

    # Also check if fundamental is too low for minimum sample rate
    if optimal * fundamental < DG822_MIN_SAMPLE_RATE:
        # Need to raise optimal so sample rate ≥ 2 kSa/s
        min_pts_for_sr = int(np.ceil(DG822_MIN_SAMPLE_RATE / fundamental))
        if min_pts_for_sr > DG822_MAX_POINTS:
            warning = (
                f"Fundamental frequency {fundamental:.4g} Hz is too low.\n"
                f"Cannot achieve minimum sample rate of {DG822_MIN_SAMPLE_RATE/1e3:.0f} kSa/s "
                f"within {DG822_MAX_POINTS} points."
            )
        else:
            optimal = max(optimal, min_pts_for_sr)

    sample_rate = optimal * fundamental

    info = {
        'fundamental': fundamental,
        'f_max': f_max,
        'harmonics': harmonics,
        'min_points_needed': min_points_needed,
        'max_points_available': min(max_points_available, DG822_MAX_POINTS),
        'num_points': optimal,
        'sample_rate': sample_rate,
        'warning': warning,
    }
    return optimal, info


def check_frequency_feasibility(frequency: float, num_points: int = None) -> dict:
    """
    Check whether a given output frequency is achievable and return info.

    Args:
        frequency: Desired output frequency in Hz
        num_points: Number of points (if None, uses optimal)

    Returns:
        dict with 'achievable', 'sample_rate', 'num_points', 'warning', etc.
    """
    if num_points is None:
        num_points = compute_optimal_points(frequency)

    sample_rate = frequency * num_points
    achievable = DG822_MIN_SAMPLE_RATE <= sample_rate <= DG822_MAX_SAMPLE_RATE
    warning = None

    if sample_rate < DG822_MIN_SAMPLE_RATE:
        min_freq = DG822_MIN_SAMPLE_RATE / num_points
        warning = (
            f"Frequency too low for {num_points} points.\n"
            f"Minimum achievable: {min_freq:.4g} Hz"
        )
    elif sample_rate > DG822_MAX_SAMPLE_RATE:
        max_freq = DG822_MAX_SAMPLE_RATE / num_points
        warning = (
            f"Frequency too high for {num_points} points.\n"
            f"Maximum achievable: {max_freq:.4g} Hz"
        )

    return {
        'achievable': achievable,
        'sample_rate': sample_rate,
        'num_points': num_points,
        'frequency': frequency,
        'warning': warning,
    }


def _approximate_gcd(values: np.ndarray, tolerance: float = 1e-6) -> float:
    """
    Compute an approximate GCD of a list of float frequencies.

    Uses integer-scaled GCD: multiply all values to make them integers,
    compute GCD, scale back.  Falls back to the minimum value if the
    result is unreasonably small (< tolerance * min).
    """
    if len(values) == 1:
        return float(values[0])

    # Scale to integers (handle decimals by multiplying up)
    # Find smallest decimal precision needed
    scale = 1.0
    for v in values:
        s = f"{v:.10g}"
        if '.' in s:
            decimals = len(s.split('.')[1])
            scale = max(scale, 10 ** decimals)

    int_values = np.round(values * scale).astype(int)
    g = reduce(gcd, int_values)
    result = g / scale

    # Sanity check: if GCD is unreasonably small, use min frequency
    if result < float(np.min(values)) * tolerance:
        result = float(np.min(values))

    return float(result)


class ArbitraryWaveform:
    """
    Represents an arbitrary waveform that can be uploaded to the DG822.
    
    The DG822 supports arbitrary waveforms with:
    - 8-16384 points per waveform
    - 14-bit vertical resolution (-8192 to +8191 DAC values)
    - Voltage range determined by amplitude/offset settings
    """
    
    # DG822 arbitrary waveform specifications
    MIN_POINTS = 8
    MAX_POINTS = 16384
    DAC_MIN = -8192
    DAC_MAX = 8191
    DAC_RANGE = 16384
    
    def __init__(self, name: str = "CUSTOM"):
        """
        Initialize an arbitrary waveform.
        
        Args:
            name: Name for the waveform (max 12 characters)
        """
        self.name = name[:12]  # DG822 limits names to 12 chars
        self.data: Optional[np.ndarray] = None  # Normalized data (-1 to +1)
        self.sample_rate: float = 1.0  # For reference only
        self.description: str = ""
    
    @property
    def num_points(self) -> int:
        """Get number of points in the waveform."""
        return len(self.data) if self.data is not None else 0
    
    @property
    def is_valid(self) -> bool:
        """Check if waveform is valid for upload."""
        if self.data is None:
            return False
        n = len(self.data)
        return self.MIN_POINTS <= n <= self.MAX_POINTS
    
    def set_data_normalized(self, data: np.ndarray) -> None:
        """
        Set waveform data from normalized values (-1 to +1).
        
        Args:
            data: Array of values in range [-1, +1]
        """
        self.data = np.clip(data, -1.0, 1.0)
    
    def set_data_voltage(self, data: np.ndarray, vpp: float, offset: float = 0.0) -> None:
        """
        Set waveform data from voltage values.
        
        Args:
            data: Array of voltage values
            vpp: Expected peak-to-peak voltage
            offset: DC offset voltage
        """
        # Normalize to -1 to +1 range
        data_centered = data - offset
        if vpp > 0:
            normalized = data_centered / (vpp / 2)
        else:
            normalized = data_centered
        self.data = np.clip(normalized, -1.0, 1.0)
    
    def get_dac_values(self) -> np.ndarray:
        """
        Get waveform data as DAC values for upload.
        
        Returns:
            Array of 14-bit DAC values (-8192 to +8191)
        """
        if self.data is None:
            return np.array([])
        
        # Scale from [-1, +1] to [-8192, +8191]
        dac = np.round(self.data * self.DAC_MAX).astype(np.int16)
        return np.clip(dac, self.DAC_MIN, self.DAC_MAX)
    
    def get_voltage_preview(self, vpp: float = 2.0, offset: float = 0.0) -> np.ndarray:
        """
        Get waveform as voltage values for preview.
        
        Args:
            vpp: Peak-to-peak voltage
            offset: DC offset
            
        Returns:
            Array of voltage values
        """
        if self.data is None:
            return np.array([])
        
        return self.data * (vpp / 2) + offset
    
    def resample(self, num_points: int) -> None:
        """
        Resample the waveform to a different number of points.
        
        Args:
            num_points: Target number of points
        """
        if self.data is None:
            return
        
        num_points = max(self.MIN_POINTS, min(num_points, self.MAX_POINTS))
        
        if len(self.data) == num_points:
            return
        
        # Use linear interpolation for resampling
        old_x = np.linspace(0, 1, len(self.data))
        new_x = np.linspace(0, 1, num_points)
        self.data = np.interp(new_x, old_x, self.data)
    
    def save_csv(self, filename: str) -> None:
        """
        Save waveform to CSV file.
        
        Args:
            filename: Output filename
        """
        if self.data is None:
            return
        
        with open(filename, 'w') as f:
            f.write(f"# Arbitrary Waveform: {self.name}\n")
            f.write(f"# Points: {len(self.data)}\n")
            f.write(f"# Description: {self.description}\n")
            f.write("# Format: normalized values (-1 to +1)\n")
            for val in self.data:
                f.write(f"{val:.6f}\n")
    
    @classmethod
    def from_csv(cls, filename: str) -> 'ArbitraryWaveform':
        """
        Create an ArbitraryWaveform from a CSV file.
        
        Args:
            filename: Input filename
            
        Returns:
            ArbitraryWaveform object
        """
        wf = cls()
        wf.load_csv_data(filename)
        # Try to get name from filename
        import os
        wf.name = os.path.splitext(os.path.basename(filename))[0][:12]
        return wf
    
    # Keep load_csv as an alias for backwards compatibility
    @classmethod  
    def load_csv(cls, filename: str) -> 'ArbitraryWaveform':
        """Alias for from_csv for backwards compatibility."""
        return cls.from_csv(filename)
    
    def load_csv_data(self, filename: str) -> bool:
        """
        Load waveform from CSV file into this instance.
        
        Args:
            filename: Input filename
            
        Returns:
            True if successful
        """
        try:
            data = []
            with open(filename, 'r') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    try:
                        data.append(float(line))
                    except ValueError:
                        continue
            
            if data:
                self.data = np.array(data)
                return True
            return False
        except Exception as e:
            print(f"Error loading CSV: {e}")
            return False
    
    def save_binary(self, filename: str) -> None:
        """
        Save waveform to binary file (more compact).
        
        Args:
            filename: Output filename
        """
        if self.data is None:
            return
        
        dac_values = self.get_dac_values()
        
        with open(filename, 'wb') as f:
            # Header
            f.write(b'DG82ARB\x00')  # Magic number
            f.write(struct.pack('<I', len(dac_values)))  # Number of points
            f.write(self.name.ljust(12).encode('ascii')[:12])  # Name
            # Data
            for val in dac_values:
                f.write(struct.pack('<h', val))
    
    def load_binary(self, filename: str) -> bool:
        """
        Load waveform from binary file.
        
        Args:
            filename: Input filename
            
        Returns:
            True if successful
        """
        try:
            with open(filename, 'rb') as f:
                magic = f.read(8)
                if magic != b'DG82ARB\x00':
                    return False
                
                num_points = struct.unpack('<I', f.read(4))[0]
                self.name = f.read(12).decode('ascii').strip()
                
                dac_values = []
                for _ in range(num_points):
                    val = struct.unpack('<h', f.read(2))[0]
                    dac_values.append(val)
                
                # Convert DAC values to normalized
                self.data = np.array(dac_values) / self.DAC_MAX
                return True
        except Exception as e:
            print(f"Error loading binary: {e}")
            return False


class WaveformGenerator:
    """
    Factory class for generating common arbitrary waveforms.
    """
    
    @staticmethod
    def square(num_points: int = 1024, duty_cycle: float = 50.0) -> ArbitraryWaveform:
        """
        Generate a square wave.
        
        Args:
            num_points: Number of points
            duty_cycle: Duty cycle in percent
            
        Returns:
            ArbitraryWaveform object
        """
        wf = ArbitraryWaveform("SQUARE")
        
        high_samples = int(num_points * duty_cycle / 100)
        low_samples = num_points - high_samples
        
        data = np.concatenate([
            np.ones(high_samples),
            -np.ones(low_samples)
        ])
        
        wf.set_data_normalized(data)
        wf.description = f"Square wave, {duty_cycle}% duty cycle"
        return wf
    
    @staticmethod
    def sine(num_points: int = 1024, phase: float = 0.0) -> ArbitraryWaveform:
        """
        Generate a sine wave.
        
        Args:
            num_points: Number of points
            phase: Phase in degrees
            
        Returns:
            ArbitraryWaveform object
        """
        wf = ArbitraryWaveform("SINE")
        
        t = np.linspace(0, 2 * np.pi, num_points, endpoint=False)
        phase_rad = np.deg2rad(phase)
        data = np.sin(t + phase_rad)
        
        wf.set_data_normalized(data)
        wf.description = f"Sine wave, {phase}° phase"
        return wf
    
    @staticmethod
    def ramp(num_points: int = 1024, symmetry: float = 100.0) -> ArbitraryWaveform:
        """
        Generate a ramp/sawtooth wave.
        
        Args:
            num_points: Number of points
            symmetry: Symmetry in percent (0=falling, 50=triangle, 100=rising)
            
        Returns:
            ArbitraryWaveform object
        """
        wf = ArbitraryWaveform("RAMP")
        
        rise_samples = int(num_points * symmetry / 100)
        fall_samples = num_points - rise_samples
        
        if rise_samples > 0:
            rise = np.linspace(-1, 1, rise_samples)
        else:
            rise = np.array([])
        
        if fall_samples > 0:
            fall = np.linspace(1, -1, fall_samples)
        else:
            fall = np.array([])
        
        data = np.concatenate([rise, fall])
        
        wf.set_data_normalized(data)
        wf.description = f"Ramp wave, {symmetry}% symmetry"
        return wf
    
    @staticmethod
    def pulse(num_points: int = 1024, width_percent: float = 10.0,
              rise_percent: float = 5.0, fall_percent: float = 5.0) -> ArbitraryWaveform:
        """
        Generate a pulse with adjustable rise/fall times.
        
        Args:
            num_points: Number of points
            width_percent: Pulse width as percent of period
            rise_percent: Rise time as percent of period
            fall_percent: Fall time as percent of period
            
        Returns:
            ArbitraryWaveform object
        """
        wf = ArbitraryWaveform("PULSE")
        
        rise_samples = max(1, int(num_points * rise_percent / 100))
        high_samples = max(1, int(num_points * width_percent / 100))
        fall_samples = max(1, int(num_points * fall_percent / 100))
        low_samples = num_points - rise_samples - high_samples - fall_samples
        
        if low_samples < 0:
            # Adjust if parameters exceed 100%
            total = rise_samples + high_samples + fall_samples
            scale = num_points / total
            rise_samples = int(rise_samples * scale)
            high_samples = int(high_samples * scale)
            fall_samples = int(fall_samples * scale)
            low_samples = num_points - rise_samples - high_samples - fall_samples
        
        rise = np.linspace(-1, 1, rise_samples) if rise_samples > 0 else np.array([])
        high = np.ones(high_samples)
        fall = np.linspace(1, -1, fall_samples) if fall_samples > 0 else np.array([])
        low = -np.ones(max(0, low_samples))
        
        data = np.concatenate([low[:len(low)//2], rise, high, fall, low[len(low)//2:]])
        
        # Ensure correct length
        if len(data) < num_points:
            data = np.concatenate([data, -np.ones(num_points - len(data))])
        elif len(data) > num_points:
            data = data[:num_points]
        
        wf.set_data_normalized(data)
        wf.description = f"Pulse, {width_percent}% width, {rise_percent}% rise, {fall_percent}% fall"
        return wf
    
    @staticmethod
    def sinc(num_points: int = 1024, num_lobes: int = 5) -> ArbitraryWaveform:
        """
        Generate a sinc function.
        
        Args:
            num_points: Number of points
            num_lobes: Number of lobes on each side
            
        Returns:
            ArbitraryWaveform object
        """
        wf = ArbitraryWaveform("SINC")
        
        x = np.linspace(-num_lobes * np.pi, num_lobes * np.pi, num_points)
        # Avoid division by zero
        data = np.where(x == 0, 1.0, np.sin(x) / x)
        
        wf.set_data_normalized(data)
        wf.description = f"Sinc function, {num_lobes} lobes"
        return wf
    
    @staticmethod
    def exponential_rise(num_points: int = 1024, tau_percent: float = 20.0) -> ArbitraryWaveform:
        """
        Generate an exponential rise waveform.
        
        Args:
            num_points: Number of points
            tau_percent: Time constant as percent of period
            
        Returns:
            ArbitraryWaveform object
        """
        wf = ArbitraryWaveform("EXPRISE")
        
        tau = tau_percent / 100.0
        t = np.linspace(0, 1, num_points)
        data = 1 - np.exp(-t / tau)
        
        # Normalize to -1 to +1
        data = 2 * data - 1
        
        wf.set_data_normalized(data)
        wf.description = f"Exponential rise, τ={tau_percent}%"
        return wf
    
    @staticmethod
    def exponential_decay(num_points: int = 1024, tau_percent: float = 20.0) -> ArbitraryWaveform:
        """
        Generate an exponential decay waveform.
        
        Args:
            num_points: Number of points
            tau_percent: Time constant as percent of period
            
        Returns:
            ArbitraryWaveform object
        """
        wf = ArbitraryWaveform("EXPDECAY")
        
        tau = tau_percent / 100.0
        t = np.linspace(0, 1, num_points)
        data = np.exp(-t / tau)
        
        # Normalize to -1 to +1
        data = 2 * data - 1
        
        wf.set_data_normalized(data)
        wf.description = f"Exponential decay, τ={tau_percent}%"
        return wf
    
    @staticmethod
    def gaussian(num_points: int = 1024, width_percent: float = 30.0) -> ArbitraryWaveform:
        """
        Generate a Gaussian pulse.
        
        Args:
            num_points: Number of points
            width_percent: Width (sigma) as percent of period
            
        Returns:
            ArbitraryWaveform object
        """
        wf = ArbitraryWaveform("GAUSSIAN")
        
        sigma = width_percent / 100.0
        t = np.linspace(-0.5, 0.5, num_points)
        data = np.exp(-t**2 / (2 * sigma**2))
        
        # Normalize to -1 to +1 (pulse goes from -1 to +1 at peak)
        data = 2 * data - 1
        
        wf.set_data_normalized(data)
        wf.description = f"Gaussian pulse, σ={width_percent}%"
        return wf
    
    @staticmethod
    def from_function(func, num_points: int = 1024, name: str = "CUSTOM") -> ArbitraryWaveform:
        """
        Generate waveform from a user-defined function.
        
        Args:
            func: Function that takes x in [0, 1] and returns value in [-1, +1]
            num_points: Number of points
            name: Waveform name
            
        Returns:
            ArbitraryWaveform object
        """
        wf = ArbitraryWaveform(name)
        
        t = np.linspace(0, 1, num_points, endpoint=False)
        data = np.array([func(x) for x in t])
        
        wf.set_data_normalized(data)
        wf.description = "Custom function"
        return wf
    
    @staticmethod
    def frequency_comb(frequencies: List[float] = None,
                       start_freq: float = None, stop_freq: float = None, step_freq: float = None,
                       num_points: int = None,
                       random_phases: bool = True,
                       monte_carlo_iterations: int = 1000) -> ArbitraryWaveform:
        """
        Generate a frequency comb waveform (sum of sinusoids).
        
        The waveform represents one period of the fundamental (GCD of all
        frequencies).  If num_points is None, the optimal number is computed
        automatically to maximise smoothness within hardware limits.
        
        Args:
            frequencies: List of frequencies in Hz. If None, use start/stop/step.
            start_freq: Starting frequency for arange-style input
            stop_freq: Stopping frequency for arange-style input  
            step_freq: Step size for arange-style input
            num_points: Number of points (None = auto-optimal)
            random_phases: If True, use random phases (with Monte Carlo optimization)
                          If False, all phases are zero
            monte_carlo_iterations: Number of random phase sets to try (if random_phases=True)
            
        Returns:
            ArbitraryWaveform object with optimized frequency comb.
            The returned object has extra attributes:
              .comb_frequencies, .comb_phases, .comb_info (dict)
        """
        # Determine frequencies
        if frequencies is not None:
            freqs = np.array(frequencies, dtype=float)
        elif start_freq is not None and stop_freq is not None and step_freq is not None:
            freqs = np.arange(start_freq, stop_freq + step_freq/2, step_freq)
        else:
            # Default: 1 to 10 Hz in 1 Hz steps
            freqs = np.arange(1, 11, 1, dtype=float)
        
        if len(freqs) == 0:
            raise ValueError("No frequencies specified")
        if np.any(freqs <= 0):
            raise ValueError("All frequencies must be positive")
        
        # Auto-calculate optimal points if not specified
        optimal_pts, comb_info = compute_optimal_points_for_comb(freqs.tolist())
        if num_points is None:
            num_points = optimal_pts
        else:
            # User specified — just update the info dict
            comb_info['num_points'] = num_points
            comb_info['sample_rate'] = num_points * comb_info['fundamental']

        fundamental = comb_info['fundamental']
        
        # Time array for one period of the fundamental
        t = np.linspace(0, 1/fundamental, num_points, endpoint=False)
        
        def generate_comb(phases):
            """Generate comb waveform with given phases."""
            signal = np.zeros(num_points)
            for i, freq in enumerate(freqs):
                signal += np.sin(2 * np.pi * freq * t + phases[i])
            return signal
        
        def compute_rms(signal):
            """Compute RMS of signal."""
            return np.sqrt(np.mean(signal**2))
        
        if random_phases:
            # Monte Carlo optimization to maximize RMS
            best_rms = 0
            best_phases = np.zeros(len(freqs))
            best_signal = None
            
            for _ in range(monte_carlo_iterations):
                phases = np.random.uniform(0, 2*np.pi, len(freqs))
                signal = generate_comb(phases)
                rms = compute_rms(signal)
                
                if rms > best_rms:
                    best_rms = rms
                    best_phases = phases.copy()
                    best_signal = signal.copy()
            
            data = best_signal
            phase_desc = f"random (optimized, RMS={best_rms:.3f})"
        else:
            # All phases zero
            phases = np.zeros(len(freqs))
            data = generate_comb(phases)
            best_phases = phases
            phase_desc = "zero"
        
        # Normalize to -1 to +1
        max_abs = np.max(np.abs(data))
        if max_abs > 0:
            data = data / max_abs
        
        wf = ArbitraryWaveform("FREQCOMB")
        wf.set_data_normalized(data)
        
        freq_range = f"{freqs[0]:.1f}-{freqs[-1]:.1f} Hz" if len(freqs) > 1 else f"{freqs[0]:.1f} Hz"
        wf.description = (
            f"Frequency comb: {len(freqs)} tones, {freq_range}, {phase_desc}, "
            f"{num_points} pts (f0={fundamental:.4g} Hz)"
        )
        
        # Store metadata for reference
        wf.comb_frequencies = freqs.tolist()
        wf.comb_phases = best_phases.tolist()
        wf.comb_info = comb_info
        
        return wf


# =============================================================================
# Module Test / Evaluation Mode
# =============================================================================
if __name__ == "__main__":
    import matplotlib.pyplot as plt
    
    print("=" * 60)
    print("DG822 Arbitrary Waveform Module - Evaluation Mode")
    print("=" * 60)
    
    # Create a 1V square wave at 1Hz (as requested)
    print("\n--- Creating 1V 1Hz Square Wave ---")
    
    # Generate the waveform
    wf = WaveformGenerator.square(num_points=1024, duty_cycle=50.0)
    wf.name = "SQR_1HZ"
    wf.description = "1V 1Hz Square Wave for testing"
    
    print(f"Name: {wf.name}")
    print(f"Points: {wf.num_points}")
    print(f"Valid: {wf.is_valid}")
    print(f"Description: {wf.description}")
    
    # Save to files
    csv_file = "test_square_1hz.csv"
    bin_file = "test_square_1hz.arb"
    
    print(f"\nSaving to {csv_file}...")
    wf.save_csv(csv_file)
    
    print(f"Saving to {bin_file}...")
    wf.save_binary(bin_file)
    
    # Test loading
    print(f"\nLoading from {csv_file}...")
    wf2 = ArbitraryWaveform("LOADED")
    if wf2.load_csv(csv_file):
        print(f"Loaded {wf2.num_points} points")
    
    # Preview the waveform (simulating 1V amplitude at 1Hz)
    print("\n--- Preview Plot ---")
    print("Showing waveform at 1Vpp, 1Hz...")
    
    voltage_preview = wf.get_voltage_preview(vpp=1.0, offset=0.0)
    t = np.linspace(0, 1, len(voltage_preview))  # 1 second for 1Hz
    
    plt.figure(figsize=(10, 4))
    plt.plot(t, voltage_preview, 'b-', linewidth=2)
    plt.xlabel("Time (s)")
    plt.ylabel("Voltage (V)")
    plt.title(f"Arbitrary Waveform: {wf.name} - 1Vpp @ 1Hz")
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.ylim(-0.7, 0.7)
    
    # Add annotation
    plt.text(0.98, 0.98, f"Points: {wf.num_points}\nVpp: 1.0 V\nf: 1 Hz",
             transform=plt.gca().transAxes,
             verticalalignment='top',
             horizontalalignment='right',
             fontsize=10,
             bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
    
    plt.tight_layout()
    plt.show()
    
    # Demonstrate other waveform types
    print("\n--- Demonstrating Other Waveform Types ---")
    
    fig, axes = plt.subplots(2, 3, figsize=(12, 6))
    fig.suptitle("Arbitrary Waveform Types", fontsize=14)
    
    waveforms = [
        ("Pulse", WaveformGenerator.pulse(1024, 20, 10, 10)),
        ("Sinc", WaveformGenerator.sinc(1024, 5)),
        ("Exp Rise", WaveformGenerator.exponential_rise(1024, 20)),
        ("Exp Decay", WaveformGenerator.exponential_decay(1024, 20)),
        ("Gaussian", WaveformGenerator.gaussian(1024, 15)),
        ("Triangle", WaveformGenerator.ramp(1024, 50)),
    ]
    
    for ax, (name, wf) in zip(axes.flat, waveforms):
        preview = wf.get_voltage_preview(vpp=2.0)
        ax.plot(preview)
        ax.set_title(name)
        ax.set_ylabel("V")
        ax.grid(True, linestyle='--', alpha=0.5)
    
    plt.tight_layout()
    plt.show()
    
    print("\n" + "=" * 60)
    print("Evaluation complete.")
    print("=" * 60)
