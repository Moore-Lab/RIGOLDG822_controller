"""
RIGOL DG822 Waveform Generator - Waveform Module

This module handles waveform configuration for the RIGOL DG800 Pro series
waveform generators. It provides methods to set up various waveform types
including sine, square, pulse, ramp, noise, DC, and arbitrary waveforms.

Author: Auto-generated
Date: 2026-01-08
"""

from __future__ import annotations

from typing import Optional, Literal, TYPE_CHECKING
from enum import Enum

if TYPE_CHECKING:
    import numpy
    from dg822_arbitrarywf import ArbitraryWaveform


class WaveformType(Enum):
    """Supported waveform types."""
    SINE = "SINusoid"
    SQUARE = "SQUare"
    RAMP = "RAMP"
    PULSE = "PULSe"
    NOISE = "NOISe"
    DC = "DC"
    ARBITRARY = "ARBitrary"
    HARMONIC = "HARMonic"


class DG822Waveform:
    """
    Handles waveform configuration for RIGOL DG822.
    
    This class provides methods to:
    - Set waveform type and parameters (frequency, amplitude, offset, phase)
    - Configure pulse-specific parameters (duty cycle, rise/fall time, width)
    - Configure square wave duty cycle
    - Configure ramp symmetry
    - Query current waveform settings
    """
    
    # DG822 Pro specifications
    MAX_FREQUENCY_DG822 = 25e6  # 25 MHz
    MIN_FREQUENCY = 1e-6  # 1 µHz
    MAX_AMPLITUDE = 20.0  # 20 Vpp (with HighZ load)
    MIN_AMPLITUDE = 1e-3  # 1 mVpp
    
    def __init__(self, connection):
        """
        Initialize waveform controller.
        
        Args:
            connection: DG822Connection instance for communication
        """
        self._conn = connection
    
    def _channel_prefix(self, channel: int) -> str:
        """Get the SCPI source prefix for a channel."""
        return f":SOURce{channel}"
    
    # =========================================================================
    # Quick Waveform Setup (APPLy commands)
    # =========================================================================
    
    def apply_sine(self, channel: int = 1, frequency: float = 1000.0,
                   amplitude: float = 5.0, offset: float = 0.0,
                   phase: float = 0.0) -> bool:
        """
        Configure channel to output a sine wave.
        
        Args:
            channel: Output channel (1 or 2)
            frequency: Frequency in Hz (default: 1000 Hz)
            amplitude: Amplitude in Vpp (default: 5 Vpp)
            offset: DC offset in V (default: 0 V)
            phase: Start phase in degrees (default: 0°)
            
        Returns:
            True if successful
        """
        cmd = f":SOURce{channel}:APPLy:SINusoid {frequency},{amplitude},{offset},{phase}"
        return self._conn.write(cmd)
    
    def apply_square(self, channel: int = 1, frequency: float = 1000.0,
                     amplitude: float = 5.0, offset: float = 0.0,
                     phase: float = 0.0) -> bool:
        """
        Configure channel to output a square wave (50% duty cycle).
        
        Args:
            channel: Output channel (1 or 2)
            frequency: Frequency in Hz (default: 1000 Hz)
            amplitude: Amplitude in Vpp (default: 5 Vpp)
            offset: DC offset in V (default: 0 V)
            phase: Start phase in degrees (default: 0°)
            
        Returns:
            True if successful
            
        Note:
            This command sets duty cycle to 50%. Use set_square_duty_cycle()
            after this command to change duty cycle.
        """
        cmd = f":SOURce{channel}:APPLy:SQUare {frequency},{amplitude},{offset},{phase}"
        return self._conn.write(cmd)
    
    def apply_ramp(self, channel: int = 1, frequency: float = 1000.0,
                   amplitude: float = 5.0, offset: float = 0.0,
                   phase: float = 0.0) -> bool:
        """
        Configure channel to output a ramp/triangle wave (50% symmetry).
        
        Args:
            channel: Output channel (1 or 2)
            frequency: Frequency in Hz (default: 1000 Hz)
            amplitude: Amplitude in Vpp (default: 5 Vpp)
            offset: DC offset in V (default: 0 V)
            phase: Start phase in degrees (default: 0°)
            
        Returns:
            True if successful
            
        Note:
            This command sets symmetry to 50%. Use set_ramp_symmetry()
            after this command to change symmetry.
        """
        cmd = f":SOURce{channel}:APPLy:RAMP {frequency},{amplitude},{offset},{phase}"
        return self._conn.write(cmd)
    
    def apply_pulse(self, channel: int = 1, frequency: float = 1000.0,
                    amplitude: float = 5.0, offset: float = 0.0,
                    phase: float = 0.0) -> bool:
        """
        Configure channel to output a pulse wave.
        
        Args:
            channel: Output channel (1 or 2)
            frequency: Frequency in Hz (default: 1000 Hz)
            amplitude: Amplitude in Vpp (default: 5 Vpp)
            offset: DC offset in V (default: 0 V)
            phase: Start phase in degrees (default: 0°)
            
        Returns:
            True if successful
        """
        cmd = f":SOURce{channel}:APPLy:PULSe {frequency},{amplitude},{offset},{phase}"
        return self._conn.write(cmd)
    
    def apply_noise(self, channel: int = 1, amplitude: float = 5.0,
                    offset: float = 0.0) -> bool:
        """
        Configure channel to output noise.
        
        Args:
            channel: Output channel (1 or 2)
            amplitude: Amplitude in Vpp (default: 5 Vpp)
            offset: DC offset in V (default: 0 V)
            
        Returns:
            True if successful
        """
        # Noise doesn't have frequency or phase parameters
        cmd = f":SOURce{channel}:APPLy:NOISe DEFault,{amplitude},{offset}"
        return self._conn.write(cmd)
    
    def apply_dc(self, channel: int = 1, offset: float = 0.0) -> bool:
        """
        Configure channel to output DC voltage.
        
        Args:
            channel: Output channel (1 or 2)
            offset: DC voltage level in V (default: 0 V)
            
        Returns:
            True if successful
        """
        cmd = f":SOURce{channel}:APPLy:DC DEFault,DEFault,{offset}"
        return self._conn.write(cmd)
    
    def apply_arbitrary(self, channel: int = 1, frequency: float = 1000.0,
                        amplitude: float = 5.0, offset: float = 0.0,
                        phase: float = 0.0) -> bool:
        """
        Configure channel to output the currently loaded arbitrary waveform.
        
        Args:
            channel: Output channel (1 or 2)
            frequency: Frequency in Hz (default: 1000 Hz)
            amplitude: Amplitude in Vpp (default: 5 Vpp)
            offset: DC offset in V (default: 0 V)
            phase: Start phase in degrees (default: 0°)
            
        Returns:
            True if successful
        """
        cmd = f":SOURce{channel}:APPLy:ARBitrary {frequency},{amplitude},{offset},{phase}"
        return self._conn.write(cmd)
    
    # =========================================================================
    # Individual Parameter Control
    # =========================================================================
    
    def set_function(self, channel: int, waveform: WaveformType) -> bool:
        """
        Set the waveform function type.
        
        Args:
            channel: Output channel (1 or 2)
            waveform: WaveformType enum value
            
        Returns:
            True if successful
        """
        cmd = f":SOURce{channel}:FUNCtion {waveform.value}"
        return self._conn.write(cmd)
    
    def get_function(self, channel: int = 1) -> Optional[str]:
        """
        Query the current waveform function type.
        
        Args:
            channel: Output channel (1 or 2)
            
        Returns:
            Waveform type string
        """
        return self._conn.query(f":SOURce{channel}:FUNCtion?")
    
    def set_frequency(self, channel: int, frequency: float) -> bool:
        """
        Set the waveform frequency.
        
        Args:
            channel: Output channel (1 or 2)
            frequency: Frequency in Hz
            
        Returns:
            True if successful
        """
        cmd = f":SOURce{channel}:FREQuency {frequency}"
        return self._conn.write(cmd)
    
    def get_frequency(self, channel: int = 1) -> Optional[float]:
        """
        Query the current frequency.
        
        Args:
            channel: Output channel (1 or 2)
            
        Returns:
            Frequency in Hz
        """
        response = self._conn.query(f":SOURce{channel}:FREQuency?")
        if response:
            try:
                return float(response)
            except ValueError:
                return None
        return None
    
    def set_amplitude(self, channel: int, amplitude: float) -> bool:
        """
        Set the waveform amplitude.
        
        Args:
            channel: Output channel (1 or 2)
            amplitude: Amplitude in current unit (default: Vpp)
            
        Returns:
            True if successful
        """
        cmd = f":SOURce{channel}:VOLTage {amplitude}"
        return self._conn.write(cmd)
    
    def get_amplitude(self, channel: int = 1) -> Optional[float]:
        """
        Query the current amplitude.
        
        Args:
            channel: Output channel (1 or 2)
            
        Returns:
            Amplitude value
        """
        response = self._conn.query(f":SOURce{channel}:VOLTage?")
        if response:
            try:
                return float(response)
            except ValueError:
                return None
        return None
    
    def set_offset(self, channel: int, offset: float) -> bool:
        """
        Set the DC offset voltage.
        
        Args:
            channel: Output channel (1 or 2)
            offset: Offset in Volts
            
        Returns:
            True if successful
        """
        cmd = f":SOURce{channel}:VOLTage:OFFSet {offset}"
        return self._conn.write(cmd)
    
    def get_offset(self, channel: int = 1) -> Optional[float]:
        """
        Query the current DC offset.
        
        Args:
            channel: Output channel (1 or 2)
            
        Returns:
            Offset in Volts
        """
        response = self._conn.query(f":SOURce{channel}:VOLTage:OFFSet?")
        if response:
            try:
                return float(response)
            except ValueError:
                return None
        return None
    
    def set_phase(self, channel: int, phase: float) -> bool:
        """
        Set the waveform start phase.
        
        Args:
            channel: Output channel (1 or 2)
            phase: Phase in degrees (-360 to 360)
            
        Returns:
            True if successful
        """
        cmd = f":SOURce{channel}:PHASe {phase}"
        return self._conn.write(cmd)
    
    def get_phase(self, channel: int = 1) -> Optional[float]:
        """
        Query the current phase.
        
        Args:
            channel: Output channel (1 or 2)
            
        Returns:
            Phase in degrees
        """
        response = self._conn.query(f":SOURce{channel}:PHASe?")
        if response:
            try:
                return float(response)
            except ValueError:
                return None
        return None
    
    def set_high_level(self, channel: int, high: float) -> bool:
        """
        Set the waveform high level voltage.
        
        Args:
            channel: Output channel (1 or 2)
            high: High level in Volts
            
        Returns:
            True if successful
        """
        cmd = f":SOURce{channel}:VOLTage:HIGH {high}"
        return self._conn.write(cmd)
    
    def set_low_level(self, channel: int, low: float) -> bool:
        """
        Set the waveform low level voltage.
        
        Args:
            channel: Output channel (1 or 2)
            low: Low level in Volts
            
        Returns:
            True if successful
        """
        cmd = f":SOURce{channel}:VOLTage:LOW {low}"
        return self._conn.write(cmd)
    
    # =========================================================================
    # Square Wave Specific
    # =========================================================================
    
    def set_square_duty_cycle(self, channel: int, duty_cycle: float) -> bool:
        """
        Set the square wave duty cycle.
        
        Args:
            channel: Output channel (1 or 2)
            duty_cycle: Duty cycle in percent (0.01% to 99.99%)
            
        Returns:
            True if successful
        """
        cmd = f":SOURce{channel}:FUNCtion:SQUare:DCYCle {duty_cycle}"
        return self._conn.write(cmd)
    
    def get_square_duty_cycle(self, channel: int = 1) -> Optional[float]:
        """
        Query the square wave duty cycle.
        
        Args:
            channel: Output channel (1 or 2)
            
        Returns:
            Duty cycle in percent
        """
        response = self._conn.query(f":SOURce{channel}:FUNCtion:SQUare:DCYCle?")
        if response:
            try:
                return float(response)
            except ValueError:
                return None
        return None
    
    # =========================================================================
    # Pulse Wave Specific
    # =========================================================================
    
    def set_pulse_duty_cycle(self, channel: int, duty_cycle: float) -> bool:
        """
        Set the pulse wave duty cycle.
        
        Args:
            channel: Output channel (1 or 2)
            duty_cycle: Duty cycle in percent
            
        Returns:
            True if successful
        """
        cmd = f":SOURce{channel}:FUNCtion:PULSe:DCYCle {duty_cycle}"
        return self._conn.write(cmd)
    
    def set_pulse_width(self, channel: int, width: float) -> bool:
        """
        Set the pulse width.
        
        Args:
            channel: Output channel (1 or 2)
            width: Pulse width in seconds
            
        Returns:
            True if successful
        """
        cmd = f":SOURce{channel}:FUNCtion:PULSe:WIDTh {width}"
        return self._conn.write(cmd)
    
    def set_pulse_leading_edge(self, channel: int, time: float) -> bool:
        """
        Set the pulse leading edge (rise) time.
        
        Args:
            channel: Output channel (1 or 2)
            time: Rise time in seconds
            
        Returns:
            True if successful
        """
        cmd = f":SOURce{channel}:FUNCtion:PULSe:TRANsition:LEADing {time}"
        return self._conn.write(cmd)
    
    def set_pulse_trailing_edge(self, channel: int, time: float) -> bool:
        """
        Set the pulse trailing edge (fall) time.
        
        Args:
            channel: Output channel (1 or 2)
            time: Fall time in seconds
            
        Returns:
            True if successful
        """
        cmd = f":SOURce{channel}:FUNCtion:PULSe:TRANsition:TRAiling {time}"
        return self._conn.write(cmd)
    
    # =========================================================================
    # Ramp Wave Specific
    # =========================================================================
    
    def set_ramp_symmetry(self, channel: int, symmetry: float) -> bool:
        """
        Set the ramp wave symmetry.
        
        Args:
            channel: Output channel (1 or 2)
            symmetry: Symmetry in percent (0% to 100%)
                      0% = falling ramp, 50% = triangle, 100% = rising ramp
            
        Returns:
            True if successful
        """
        cmd = f":SOURce{channel}:FUNCtion:RAMP:SYMMetry {symmetry}"
        return self._conn.write(cmd)
    
    def get_ramp_symmetry(self, channel: int = 1) -> Optional[float]:
        """
        Query the ramp wave symmetry.
        
        Args:
            channel: Output channel (1 or 2)
            
        Returns:
            Symmetry in percent
        """
        response = self._conn.query(f":SOURce{channel}:FUNCtion:RAMP:SYMMetry?")
        if response:
            try:
                return float(response)
            except ValueError:
                return None
        return None
    
    # =========================================================================
    # Utility Methods
    # =========================================================================
    
    def get_apply_settings(self, channel: int = 1) -> Optional[str]:
        """
        Query the current waveform settings in APPLy format.
        
        Args:
            channel: Output channel (1 or 2)
            
        Returns:
            String with waveform type and parameters
        """
        return self._conn.query(f":SOURce{channel}:APPLy?")
    
    def sync_phases(self) -> bool:
        """
        Synchronize the phases of both channels.
        
        Returns:
            True if successful
        """
        return self._conn.write(":SOURce1:PHASe:SYNChronize")
    
    # =========================================================================
    # Arbitrary Waveform Methods
    # =========================================================================
    
    def upload_arbitrary_waveform(self, channel: int, name: str,
                                   data: 'numpy.ndarray') -> bool:
        """
        Upload an arbitrary waveform to the instrument's volatile memory.
        
        Args:
            channel: Output channel (1 or 2)
            name: Name for the waveform (max 12 characters)
            data: Array of DAC values (-8192 to +8191) or normalized (-1 to +1)
            
        Returns:
            True if successful
        """
        import numpy as np
        
        # Validate data length
        if len(data) < 8 or len(data) > 16384:
            print(f"Error: Data length must be 8-16384 points (got {len(data)})")
            return False
        
        # Check if data is normalized (-1 to +1) or DAC values
        if np.max(np.abs(data)) <= 1.0:
            # Normalized data - convert to DAC values
            dac_data = np.round(data * 8191).astype(np.int16)
        else:
            # Already DAC values
            dac_data = np.clip(data, -8192, 8191).astype(np.int16)
        
        # Build the data string - comma-separated integer values
        data_str = ",".join(str(int(v)) for v in dac_data)
        
        # Upload to volatile memory
        # Command: :SOURce[<n>]:DATA:DAC16 VOLATILE,<name>,<binary_data>
        # For simplicity, we use the ASCII DATA command
        cmd = f":SOURce{channel}:DATA VOLATILE,{data_str}"
        
        if not self._conn.write(cmd):
            print("Error: Failed to upload waveform data")
            return False
        
        # Set the arbitrary waveform name
        # Note: The name might need to be set differently on non-Pro models
        # cmd_name = f":SOURce{channel}:FUNCtion:ARBitrary {name}"
        # self._conn.write(cmd_name)
        
        return True
    
    def upload_arbitrary_waveform_from_object(self, channel: int,
                                               waveform: 'ArbitraryWaveform') -> bool:
        """
        Upload an ArbitraryWaveform object to the instrument.
        
        Args:
            channel: Output channel (1 or 2)
            waveform: ArbitraryWaveform object from dg822_arbitrarywf module
            
        Returns:
            True if successful
        """
        if waveform.data is None:
            print("Error: Waveform has no data")
            return False
        
        return self.upload_arbitrary_waveform(channel, waveform.name, waveform.data)
    
    def set_arbitrary_waveform(self, channel: int, name: str) -> bool:
        """
        Select a stored arbitrary waveform by name.
        
        Args:
            channel: Output channel (1 or 2)
            name: Name of the stored waveform
            
        Returns:
            True if successful
        """
        cmd = f":SOURce{channel}:FUNCtion:ARBitrary {name}"
        return self._conn.write(cmd)
    
    def get_arbitrary_waveform(self, channel: int = 1) -> Optional[str]:
        """
        Query the currently selected arbitrary waveform.
        
        Args:
            channel: Output channel (1 or 2)
            
        Returns:
            Name of the current arbitrary waveform
        """
        return self._conn.query(f":SOURce{channel}:FUNCtion:ARBitrary?")
    
    def list_arbitrary_waveforms(self, channel: int = 1) -> Optional[str]:
        """
        List available arbitrary waveforms.
        
        Args:
            channel: Output channel (1 or 2)
            
        Returns:
            String listing available waveforms
        """
        return self._conn.query(f":SOURce{channel}:DATA:CATalog?")
    
    def delete_arbitrary_waveform(self, channel: int, name: str) -> bool:
        """
        Delete a stored arbitrary waveform.
        
        Args:
            channel: Output channel (1 or 2)
            name: Name of the waveform to delete
            
        Returns:
            True if successful
        """
        cmd = f":SOURce{channel}:DATA:DELete {name}"
        return self._conn.write(cmd)


# =============================================================================
# Module Test / Evaluation Mode
# =============================================================================
if __name__ == "__main__":
    from dg822_connection import DG822Connection
    
    # Known working resource (update this if your device has a different ID)
    KNOWN_RESOURCE = 'USB0::0x1AB1::0x0643::DG8A204201757::0::INSTR'
    
    print("=" * 60)
    print("DG822 Waveform Module - Evaluation Mode")
    print("=" * 60)
    
    # Create connection
    conn = DG822Connection()
    
    # Try to discover devices first
    print("\nSearching for devices...")
    devices = conn.discover_devices()
    
    if devices:
        resource = devices[0][0]
        print(f"Found device: {resource}")
    else:
        print("Auto-discovery failed. Using known resource...")
        resource = KNOWN_RESOURCE
    
    print(f"Connecting to: {resource}")
    
    if conn.connect(resource):
        # Create waveform controller
        wf = DG822Waveform(conn)
        
        print("\n" + "-" * 60)
        print("Testing Waveform Configuration")
        print("-" * 60)
        
        # Query current settings
        print("\n1. Querying current settings...")
        settings = wf.get_apply_settings(1)
        print(f"   CH1 Current: {settings}")
        
        # Apply sine wave
        print("\n2. Applying sine wave (1 kHz, 2 Vpp, 0.5V offset)...")
        if wf.apply_sine(1, 1000, 2.0, 0.5, 0):
            print("   Success!")
            settings = wf.get_apply_settings(1)
            print(f"   CH1 Now: {settings}")
        
        # Query individual parameters
        print("\n3. Querying individual parameters...")
        print(f"   Function: {wf.get_function(1)}")
        print(f"   Frequency: {wf.get_frequency(1)} Hz")
        print(f"   Amplitude: {wf.get_amplitude(1)} Vpp")
        print(f"   Offset: {wf.get_offset(1)} V")
        print(f"   Phase: {wf.get_phase(1)}°")
        
        # Apply square wave
        print("\n4. Applying square wave (5 kHz, 3.3 Vpp)...")
        if wf.apply_square(1, 5000, 3.3, 0, 0):
            print("   Success!")
            # Modify duty cycle
            print("   Setting duty cycle to 25%...")
            wf.set_square_duty_cycle(1, 25)
            dc = wf.get_square_duty_cycle(1)
            print(f"   Duty Cycle: {dc}%")
        
        # Apply ramp wave
        print("\n5. Applying ramp wave (2 kHz, 4 Vpp)...")
        if wf.apply_ramp(1, 2000, 4.0, 0, 0):
            print("   Success!")
            # Modify symmetry (sawtooth)
            print("   Setting symmetry to 100% (rising sawtooth)...")
            wf.set_ramp_symmetry(1, 100)
            sym = wf.get_ramp_symmetry(1)
            print(f"   Symmetry: {sym}%")
        
        # Reset to default
        print("\n6. Resetting to default...")
        conn.reset()
        settings = wf.get_apply_settings(1)
        print(f"   CH1 After Reset: {settings}")
        
        print("\n" + "-" * 60)
    else:
        print("Connection failed!")
    
    # Clean up connection and resource manager
    conn.close()
    
    print("\n" + "=" * 60)
    print("Evaluation complete.")
    print("=" * 60)
