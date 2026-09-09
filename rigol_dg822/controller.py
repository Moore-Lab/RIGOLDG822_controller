"""
RIGOL DG822 Waveform Generator - Main Controller Module

This module provides a unified interface to control the RIGOL DG822/DG800 Pro
series waveform generators. It combines connection, waveform, and output
control into a single easy-to-use class.

Author: Auto-generated
Date: 2026-01-08
"""

from typing import Optional, List, Tuple

from .connection import DG822Connection
from .waveform import DG822Waveform, WaveformType
from .output import DG822Output, OutputPolarity, SyncMode


class DG822Controller:
    """
    Unified controller for RIGOL DG822 waveform generator.
    
    This class provides a high-level interface combining:
    - Connection management (connect, disconnect, discover)
    - Waveform configuration (sine, square, pulse, ramp, etc.)
    - Output control (enable, disable, impedance, polarity)
    
    Example usage:
        # Quick start with auto-discovery
        dg = DG822Controller()
        if dg.auto_connect():
            dg.setup_sine(1, frequency=1000, amplitude=2.0)
            dg.output_on(1)
            # ... do work ...
            dg.output_off(1)
            dg.disconnect()
        
        # Or use as context manager
        with DG822Controller() as dg:
            if dg.is_connected:
                dg.setup_sine(1, frequency=1000, amplitude=2.0)
                dg.output_on(1)
    """
    
    def __init__(self, resource_name: Optional[str] = None, timeout: int = 5000,
                 simulate: bool = False):
        """
        Initialize the DG822 controller.
        
        Args:
            resource_name: VISA resource string (optional). Pass
                           rigol_dg822.SIM_RESOURCE for the simulated instrument.
            timeout: Communication timeout in milliseconds
            simulate: Force the simulated backend, no VISA needed
        """
        # Initialize sub-modules
        self._connection = DG822Connection(resource_name, timeout, simulate=simulate)
        self._waveform: Optional[DG822Waveform] = None
        self._output: Optional[DG822Output] = None
    
    # =========================================================================
    # Properties
    # =========================================================================
    
    @property
    def is_connected(self) -> bool:
        """Return True if connected to instrument."""
        return self._connection.is_connected
    
    @property
    def idn(self) -> Optional[str]:
        """Return the instrument identification string."""
        return self._connection.idn
    
    @property
    def is_simulated(self) -> bool:
        """Return True if this controller drives the simulated instrument."""
        return self._connection.is_simulated
    
    @property
    def connection(self) -> DG822Connection:
        """Access the underlying connection object."""
        return self._connection
    
    @property
    def waveform(self) -> Optional[DG822Waveform]:
        """Access the waveform control object."""
        return self._waveform
    
    @property
    def output(self) -> Optional[DG822Output]:
        """Access the output control object."""
        return self._output
    
    # =========================================================================
    # Connection Management
    # =========================================================================
    
    def discover_devices(self) -> List[Tuple[str, str]]:
        """
        Discover available RIGOL DG800/DG900 devices.
        
        Returns:
            List of tuples: (resource_name, idn_string)
        """
        return self._connection.discover_devices()
    
    def connect(self, resource_name: Optional[str] = None) -> bool:
        """
        Connect to a specific instrument.
        
        Args:
            resource_name: VISA resource string
            
        Returns:
            True if connection successful
        """
        if self._connection.connect(resource_name):
            # Initialize sub-modules with active connection
            self._waveform = DG822Waveform(self._connection)
            self._output = DG822Output(self._connection)
            return True
        return False
    
    def auto_connect(self) -> bool:
        """
        Automatically discover and connect to the first available device.
        
        Returns:
            True if connection successful
        """
        devices = self.discover_devices()
        if devices:
            resource = devices[0][0]
            print(f"Auto-connecting to: {devices[0][1]}")
            return self.connect(resource)
        else:
            print("No RIGOL DG800/DG900 devices found.")
            return False
    
    def disconnect(self) -> None:
        """Disconnect from the instrument."""
        self._connection.disconnect()
        self._waveform = None
        self._output = None
    
    def reset(self) -> bool:
        """Reset the instrument to default settings."""
        return self._connection.reset()
    
    def beep(self) -> bool:
        """Make the instrument beep."""
        return self._connection.beep()
    
    # =========================================================================
    # Quick Waveform Setup Methods
    # =========================================================================
    
    def setup_sine(self, channel: int = 1, frequency: float = 1000.0,
                   amplitude: float = 5.0, offset: float = 0.0,
                   phase: float = 0.0) -> bool:
        """
        Configure a sine wave output.
        
        Args:
            channel: Output channel (1 or 2)
            frequency: Frequency in Hz
            amplitude: Amplitude in Vpp
            offset: DC offset in V
            phase: Start phase in degrees
        """
        if self._waveform:
            return self._waveform.apply_sine(channel, frequency, amplitude, offset, phase)
        return False
    
    def setup_square(self, channel: int = 1, frequency: float = 1000.0,
                     amplitude: float = 5.0, offset: float = 0.0,
                     phase: float = 0.0, duty_cycle: Optional[float] = None) -> bool:
        """
        Configure a square wave output.
        
        Args:
            channel: Output channel (1 or 2)
            frequency: Frequency in Hz
            amplitude: Amplitude in Vpp
            offset: DC offset in V
            phase: Start phase in degrees
            duty_cycle: Optional duty cycle in percent (default: 50%)
        """
        if self._waveform:
            result = self._waveform.apply_square(channel, frequency, amplitude, offset, phase)
            if result and duty_cycle is not None:
                self._waveform.set_square_duty_cycle(channel, duty_cycle)
            return result
        return False
    
    def setup_pulse(self, channel: int = 1, frequency: float = 1000.0,
                    amplitude: float = 5.0, offset: float = 0.0,
                    phase: float = 0.0, duty_cycle: Optional[float] = None,
                    width: Optional[float] = None,
                    rise_time: Optional[float] = None,
                    fall_time: Optional[float] = None,
                    centered: bool = True) -> bool:
        """
        Configure a pulse wave output.
        
        Args:
            channel: Output channel (1 or 2)
            frequency: Frequency in Hz
            amplitude: Amplitude in Vpp
            offset: DC offset in V
            phase: Start phase in degrees
            duty_cycle: Optional duty cycle in percent
            width: Optional pulse width in seconds
            rise_time: Optional rise time in seconds
            fall_time: Optional fall time in seconds
            centered: If True, center the pulse in each cycle (adjusts phase)
        """
        if self._waveform:
            # Calculate effective phase for centering
            effective_phase = phase
            if centered and duty_cycle is not None:
                # To center pulse: shift phase by (1 - duty/100) * 180 degrees
                # This moves the pulse start to (period - pulse_width) / 2
                center_offset = (1.0 - duty_cycle / 100.0) * 180.0
                effective_phase = phase + center_offset
                # Keep phase in valid range
                effective_phase = effective_phase % 360.0
            
            result = self._waveform.apply_pulse(channel, frequency, amplitude, offset, effective_phase)
            if result:
                if duty_cycle is not None:
                    self._waveform.set_pulse_duty_cycle(channel, duty_cycle)
                if width is not None:
                    self._waveform.set_pulse_width(channel, width)
                if rise_time is not None:
                    self._waveform.set_pulse_leading_edge(channel, rise_time)
                if fall_time is not None:
                    self._waveform.set_pulse_trailing_edge(channel, fall_time)
            return result
        return False
    
    def setup_ramp(self, channel: int = 1, frequency: float = 1000.0,
                   amplitude: float = 5.0, offset: float = 0.0,
                   phase: float = 0.0, symmetry: Optional[float] = None) -> bool:
        """
        Configure a ramp/triangle wave output.
        
        Args:
            channel: Output channel (1 or 2)
            frequency: Frequency in Hz
            amplitude: Amplitude in Vpp
            offset: DC offset in V
            phase: Start phase in degrees
            symmetry: Optional symmetry in percent (0=falling, 50=triangle, 100=rising)
        """
        if self._waveform:
            result = self._waveform.apply_ramp(channel, frequency, amplitude, offset, phase)
            if result and symmetry is not None:
                self._waveform.set_ramp_symmetry(channel, symmetry)
            return result
        return False
    
    def setup_noise(self, channel: int = 1, amplitude: float = 5.0,
                    offset: float = 0.0) -> bool:
        """
        Configure noise output.
        
        Args:
            channel: Output channel (1 or 2)
            amplitude: Amplitude in Vpp
            offset: DC offset in V
        """
        if self._waveform:
            return self._waveform.apply_noise(channel, amplitude, offset)
        return False
    
    def setup_dc(self, channel: int = 1, voltage: float = 0.0) -> bool:
        """
        Configure DC voltage output.
        
        Args:
            channel: Output channel (1 or 2)
            voltage: DC voltage level in V
        """
        if self._waveform:
            return self._waveform.apply_dc(channel, voltage)
        return False
    
    # =========================================================================
    # Output Control Methods
    # =========================================================================
    
    def output_on(self, channel: int = 1) -> bool:
        """Enable output for the specified channel."""
        if self._output:
            return self._output.enable(channel)
        return False
    
    def output_off(self, channel: int = 1) -> bool:
        """Disable output for the specified channel."""
        if self._output:
            return self._output.disable(channel)
        return False
    
    def all_outputs_on(self) -> bool:
        """Enable outputs for both channels."""
        if self._output:
            ch1 = self._output.enable(1)
            ch2 = self._output.enable(2)
            return ch1 and ch2
        return False
    
    def all_outputs_off(self) -> bool:
        """Disable outputs for both channels."""
        if self._output:
            ch1 = self._output.disable(1)
            ch2 = self._output.disable(2)
            return ch1 and ch2
        return False
    
    def set_load_50_ohm(self, channel: int = 1) -> bool:
        """Set output impedance to 50 Ohm."""
        if self._output:
            return self._output.set_impedance_50_ohm(channel)
        return False
    
    def set_load_high_z(self, channel: int = 1) -> bool:
        """Set output impedance to High-Z."""
        if self._output:
            return self._output.set_impedance_high_z(channel)
        return False
    
    # =========================================================================
    # Parameter Query Methods
    # =========================================================================
    
    def get_frequency(self, channel: int = 1) -> Optional[float]:
        """Get current frequency in Hz."""
        if self._waveform:
            return self._waveform.get_frequency(channel)
        return None
    
    def get_amplitude(self, channel: int = 1) -> Optional[float]:
        """Get current amplitude in Vpp."""
        if self._waveform:
            return self._waveform.get_amplitude(channel)
        return None
    
    def get_offset(self, channel: int = 1) -> Optional[float]:
        """Get current DC offset in V."""
        if self._waveform:
            return self._waveform.get_offset(channel)
        return None
    
    def get_waveform_type(self, channel: int = 1) -> Optional[str]:
        """Get current waveform type."""
        if self._waveform:
            return self._waveform.get_function(channel)
        return None
    
    def is_output_on(self, channel: int = 1) -> bool:
        """Check if output is enabled."""
        if self._output:
            return self._output.is_enabled(channel)
        return False
    
    # =========================================================================
    # Parameter Set Methods
    # =========================================================================
    
    def set_frequency(self, channel: int, frequency: float) -> bool:
        """Set frequency in Hz."""
        if self._waveform:
            return self._waveform.set_frequency(channel, frequency)
        return False
    
    def set_amplitude(self, channel: int, amplitude: float) -> bool:
        """Set amplitude in Vpp."""
        if self._waveform:
            return self._waveform.set_amplitude(channel, amplitude)
        return False
    
    def set_offset(self, channel: int, offset: float) -> bool:
        """Set DC offset in V."""
        if self._waveform:
            return self._waveform.set_offset(channel, offset)
        return False
    
    def set_phase(self, channel: int, phase: float) -> bool:
        """Set phase in degrees."""
        if self._waveform:
            return self._waveform.set_phase(channel, phase)
        return False
    
    # =========================================================================
    # Status Methods
    # =========================================================================
    
    def get_status(self) -> dict:
        """
        Get comprehensive status of the instrument.
        
        Returns:
            Dictionary with all status information
        """
        status = {
            'connected': self.is_connected,
            'idn': self.idn,
        }
        
        if self.is_connected:
            status['channels'] = {}
            for ch in [1, 2]:
                status['channels'][ch] = {
                    'output_enabled': self.is_output_on(ch),
                    'waveform': self.get_waveform_type(ch),
                    'frequency': self.get_frequency(ch),
                    'amplitude': self.get_amplitude(ch),
                    'offset': self.get_offset(ch),
                }
                if self._output:
                    status['channels'][ch]['impedance'] = self._output.get_impedance(ch)
                    status['channels'][ch]['polarity'] = self._output.get_polarity(ch)
        
        return status
    
    def print_status(self) -> None:
        """Print formatted status information."""
        status = self.get_status()
        
        print("\n" + "=" * 50)
        print("DG822 Status")
        print("=" * 50)
        print(f"Connected: {status['connected']}")
        
        if status['connected']:
            print(f"IDN: {status['idn']}")
            
            for ch in [1, 2]:
                ch_status = status['channels'][ch]
                print(f"\n--- Channel {ch} ---")
                print(f"  Output: {'ON' if ch_status['output_enabled'] else 'OFF'}")
                print(f"  Waveform: {ch_status['waveform']}")
                print(f"  Frequency: {ch_status['frequency']} Hz")
                print(f"  Amplitude: {ch_status['amplitude']} Vpp")
                print(f"  Offset: {ch_status['offset']} V")
                if ch_status.get('impedance'):
                    imp = ch_status['impedance']
                    if imp == float('inf'):
                        print("  Load: High-Z")
                    else:
                        print(f"  Load: {imp} Ω")
                if ch_status.get('polarity'):
                    print(f"  Polarity: {ch_status['polarity']}")
        
        print("=" * 50)
    
    # =========================================================================
    # Context Manager Support
    # =========================================================================
    
    def __enter__(self):
        """Context manager entry - auto-connect if not connected."""
        if not self.is_connected:
            self.auto_connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - disconnect."""
        self.disconnect()
        return False


# =============================================================================
# Module Test / Evaluation Mode
# =============================================================================
if __name__ == "__main__":
    # Known working resource (update this if your device has a different ID)
    KNOWN_RESOURCE = 'USB0::0x1AB1::0x0643::DG8A204201757::0::INSTR'
    
    print("=" * 60)
    print("DG822 Controller - Evaluation Mode")
    print("=" * 60)
    
    # Create controller
    dg = DG822Controller()
    
    # Try to discover devices first
    print("\nSearching for devices...")
    devices = dg.discover_devices()
    
    if devices:
        resource = devices[0][0]
        print(f"Found device: {resource}")
    else:
        print("Auto-discovery failed. Using known resource...")
        resource = KNOWN_RESOURCE
    
    print(f"Connecting to: {resource}")
    
    if dg.connect(resource):
        print("\n" + "-" * 60)
        print("Running Integration Tests")
        print("-" * 60)
        
        # Test 1: Status query
        print("\n1. Initial Status:")
        dg.print_status()
        
        # Test 2: Setup sine wave
        print("\n2. Setting up sine wave (1 kHz, 2 Vpp, 0.5V offset)...")
        dg.setup_sine(1, frequency=1000, amplitude=2.0, offset=0.5)
        print(f"   Frequency: {dg.get_frequency(1)} Hz")
        print(f"   Amplitude: {dg.get_amplitude(1)} Vpp")
        print(f"   Offset: {dg.get_offset(1)} V")
        
        # Test 3: Enable output
        print("\n3. Enabling output...")
        dg.output_on(1)
        print(f"   Output enabled: {dg.is_output_on(1)}")
        
        # Test 4: Change frequency
        print("\n4. Changing frequency to 5 kHz...")
        dg.set_frequency(1, 5000)
        print(f"   New frequency: {dg.get_frequency(1)} Hz")
        
        # Test 5: Setup square wave on CH2
        print("\n5. Setting up square wave on CH2 (10 kHz, 3.3 Vpp, 25% duty)...")
        dg.setup_square(2, frequency=10000, amplitude=3.3, duty_cycle=25)
        dg.output_on(2)
        print(f"   CH2 Waveform: {dg.get_waveform_type(2)}")
        print(f"   CH2 Output enabled: {dg.is_output_on(2)}")
        
        # Test 6: Final status
        print("\n6. Final Status:")
        dg.print_status()
        
        # Test 7: Turn off outputs and reset
        print("\n7. Turning off outputs and resetting...")
        dg.all_outputs_off()
        dg.reset()
        print("   Done!")
        
        print("\n" + "-" * 60)
    else:
        print("Connection failed!")
    
    # Clean up connection and resource manager
    dg.connection.close()
    
    print("\n" + "=" * 60)
    print("Evaluation complete.")
    print("=" * 60)
