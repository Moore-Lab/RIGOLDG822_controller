"""
RIGOL DG822 Waveform Generator - Output Control Module

This module handles output configuration for the RIGOL DG822/DG800 Pro series
waveform generators. It provides methods to enable/disable outputs,
configure impedance, polarity, and sync signal settings.

Author: Auto-generated
Date: 2026-01-08
"""

from typing import Optional, Literal
from enum import Enum


class OutputPolarity(Enum):
    """Output polarity options."""
    NORMAL = "NORMal"
    INVERTED = "INVerted"


class SyncMode(Enum):
    """Sync signal mode options."""
    NORMAL = "NORMal"
    CARRIER = "CARRier"
    MARKER = "MARKer"


class DG822Output:
    """
    Handles output configuration for RIGOL DG822.
    
    This class provides methods to:
    - Enable/disable channel outputs
    - Configure output impedance (load)
    - Set output polarity (normal/inverted)
    - Configure sync signal output
    - Set idle level for burst/sweep modes
    """
    
    # Impedance limits
    MIN_IMPEDANCE = 1  # 1 Ohm
    MAX_IMPEDANCE = 10000  # 10 kOhm
    HIGH_Z = float('inf')  # High impedance
    
    def __init__(self, connection):
        """
        Initialize output controller.
        
        Args:
            connection: DG822Connection instance for communication
        """
        self._conn = connection
    
    # =========================================================================
    # Output Enable/Disable
    # =========================================================================
    
    def enable(self, channel: int = 1) -> bool:
        """
        Enable the output for the specified channel.
        
        Args:
            channel: Output channel (1 or 2)
            
        Returns:
            True if successful
        """
        cmd = f":OUTPut{channel}:STATe ON"
        return self._conn.write(cmd)
    
    def disable(self, channel: int = 1) -> bool:
        """
        Disable the output for the specified channel.
        
        Args:
            channel: Output channel (1 or 2)
            
        Returns:
            True if successful
        """
        cmd = f":OUTPut{channel}:STATe OFF"
        return self._conn.write(cmd)
    
    def set_state(self, channel: int, enabled: bool) -> bool:
        """
        Set the output state for the specified channel.
        
        Args:
            channel: Output channel (1 or 2)
            enabled: True to enable, False to disable
            
        Returns:
            True if successful
        """
        state = "ON" if enabled else "OFF"
        cmd = f":OUTPut{channel}:STATe {state}"
        return self._conn.write(cmd)
    
    def get_state(self, channel: int = 1) -> Optional[bool]:
        """
        Query the output state for the specified channel.
        
        Args:
            channel: Output channel (1 or 2)
            
        Returns:
            True if enabled, False if disabled, None if query failed
        """
        response = self._conn.query(f":OUTPut{channel}:STATe?")
        if response:
            return response == "1" or response.upper() == "ON"
        return None
    
    def is_enabled(self, channel: int = 1) -> bool:
        """
        Check if channel output is enabled.
        
        Args:
            channel: Output channel (1 or 2)
            
        Returns:
            True if enabled
        """
        state = self.get_state(channel)
        return state is True
    
    # =========================================================================
    # Output Impedance (Load)
    # =========================================================================
    
    def set_impedance(self, channel: int, impedance: float) -> bool:
        """
        Set the output load impedance.
        
        Args:
            channel: Output channel (1 or 2)
            impedance: Load impedance in Ohms (1 to 10000)
            
        Returns:
            True if successful
            
        Note:
            The output impedance setting affects displayed amplitude.
            Set this to match your actual load for accurate readings.
        """
        if impedance < self.MIN_IMPEDANCE or impedance > self.MAX_IMPEDANCE:
            print(f"Warning: Impedance should be between {self.MIN_IMPEDANCE} and {self.MAX_IMPEDANCE} Ohms")
        
        cmd = f":OUTPut{channel}:LOAD {impedance}"
        return self._conn.write(cmd)
    
    def set_impedance_high_z(self, channel: int) -> bool:
        """
        Set the output load impedance to High-Z (infinite).
        
        Args:
            channel: Output channel (1 or 2)
            
        Returns:
            True if successful
        """
        cmd = f":OUTPut{channel}:LOAD INFinity"
        return self._conn.write(cmd)
    
    def set_impedance_50_ohm(self, channel: int) -> bool:
        """
        Set the output load impedance to 50 Ohms (common value).
        
        Args:
            channel: Output channel (1 or 2)
            
        Returns:
            True if successful
        """
        return self.set_impedance(channel, 50)
    
    def get_impedance(self, channel: int = 1) -> Optional[float]:
        """
        Query the output load impedance.
        
        Args:
            channel: Output channel (1 or 2)
            
        Returns:
            Impedance in Ohms, or float('inf') for High-Z, None if query failed
        """
        response = self._conn.query(f":OUTPut{channel}:LOAD?")
        if response:
            try:
                value = float(response)
                # High-Z returns a very large value (9.9E+37)
                if value > 1e30:
                    return float('inf')
                return value
            except ValueError:
                return None
        return None
    
    # =========================================================================
    # Output Polarity
    # =========================================================================
    
    def set_polarity(self, channel: int, polarity: OutputPolarity) -> bool:
        """
        Set the output polarity.
        
        Args:
            channel: Output channel (1 or 2)
            polarity: OutputPolarity.NORMAL or OutputPolarity.INVERTED
            
        Returns:
            True if successful
            
        Note:
            Inverted mode inverts the waveform around the DC offset.
            The sync signal is not inverted.
        """
        cmd = f":OUTPut{channel}:POLarity {polarity.value}"
        return self._conn.write(cmd)
    
    def set_polarity_normal(self, channel: int) -> bool:
        """Set output polarity to normal."""
        return self.set_polarity(channel, OutputPolarity.NORMAL)
    
    def set_polarity_inverted(self, channel: int) -> bool:
        """Set output polarity to inverted."""
        return self.set_polarity(channel, OutputPolarity.INVERTED)
    
    def get_polarity(self, channel: int = 1) -> Optional[str]:
        """
        Query the output polarity.
        
        Args:
            channel: Output channel (1 or 2)
            
        Returns:
            "NORM" or "INV"
        """
        return self._conn.query(f":OUTPut{channel}:POLarity?")
    
    # =========================================================================
    # Sync Signal Output
    # =========================================================================
    
    def enable_sync(self, channel: int = 1) -> bool:
        """
        Enable the sync signal output.
        
        Args:
            channel: Output channel (1 or 2)
            
        Returns:
            True if successful
        """
        cmd = f":OUTPut{channel}:SYNC ON"
        return self._conn.write(cmd)
    
    def disable_sync(self, channel: int = 1) -> bool:
        """
        Disable the sync signal output.
        
        Args:
            channel: Output channel (1 or 2)
            
        Returns:
            True if successful
        """
        cmd = f":OUTPut{channel}:SYNC OFF"
        return self._conn.write(cmd)
    
    def get_sync_state(self, channel: int = 1) -> Optional[bool]:
        """
        Query the sync signal state.
        
        Args:
            channel: Output channel (1 or 2)
            
        Returns:
            True if enabled, False if disabled
        """
        response = self._conn.query(f":OUTPut{channel}:SYNC?")
        if response:
            return response == "1"
        return None
    
    def set_sync_mode(self, channel: int, mode: SyncMode) -> bool:
        """
        Set the sync signal mode.
        
        Args:
            channel: Output channel (1 or 2)
            mode: SyncMode.NORMAL, SyncMode.CARRIER, or SyncMode.MARKER
            
        Returns:
            True if successful
        """
        cmd = f":OUTPut{channel}:SYNC:MODE {mode.value}"
        return self._conn.write(cmd)
    
    def set_sync_polarity(self, channel: int, positive: bool = True) -> bool:
        """
        Set the sync signal polarity.
        
        Args:
            channel: Output channel (1 or 2)
            positive: True for positive polarity, False for negative
            
        Returns:
            True if successful
        """
        polarity = "POSitive" if positive else "NEGative"
        cmd = f":OUTPut{channel}:SYNC:POLarity {polarity}"
        return self._conn.write(cmd)
    
    # =========================================================================
    # Trigger Output
    # =========================================================================
    
    def enable_trigger_output(self, channel: int = 1) -> bool:
        """
        Enable the trigger output signal.
        
        Args:
            channel: Output channel (1 or 2)
            
        Returns:
            True if successful
        """
        cmd = f":OUTPut{channel}:TRIGger ON"
        return self._conn.write(cmd)
    
    def disable_trigger_output(self, channel: int = 1) -> bool:
        """
        Disable the trigger output signal.
        
        Args:
            channel: Output channel (1 or 2)
            
        Returns:
            True if successful
        """
        cmd = f":OUTPut{channel}:TRIGger OFF"
        return self._conn.write(cmd)
    
    def set_trigger_slope(self, channel: int, positive: bool = True) -> bool:
        """
        Set the trigger output edge.
        
        Args:
            channel: Output channel (1 or 2)
            positive: True for rising edge, False for falling edge
            
        Returns:
            True if successful
        """
        slope = "POSitive" if positive else "NEGative"
        cmd = f":OUTPut{channel}:TRIGger:SLOPe {slope}"
        return self._conn.write(cmd)
    
    # =========================================================================
    # Idle Level (for Burst/Sweep modes)
    # =========================================================================
    
    def set_idle_level(self, channel: int, level: str) -> bool:
        """
        Set the idle level for burst/sweep modes.
        
        Args:
            channel: Output channel (1 or 2)
            level: "FPT" (first point), "TOP", "CENTER", "BOTTOM"
            
        Returns:
            True if successful
        """
        cmd = f":OUTPut{channel}:IDLE {level}"
        return self._conn.write(cmd)
    
    def get_idle_level(self, channel: int = 1) -> Optional[str]:
        """
        Query the idle level setting.
        
        Args:
            channel: Output channel (1 or 2)
            
        Returns:
            Idle level setting string
        """
        return self._conn.query(f":OUTPut{channel}:IDLE?")
    
    # =========================================================================
    # Convenience Methods
    # =========================================================================
    
    def get_all_states(self) -> dict:
        """
        Get the output states for all channels.
        
        Returns:
            Dictionary with channel states
        """
        return {
            'ch1_enabled': self.get_state(1),
            'ch2_enabled': self.get_state(2),
            'ch1_impedance': self.get_impedance(1),
            'ch2_impedance': self.get_impedance(2),
            'ch1_polarity': self.get_polarity(1),
            'ch2_polarity': self.get_polarity(2),
        }


# =============================================================================
# Module Test / Evaluation Mode
# =============================================================================
if __name__ == "__main__":
    from dg822_connection import DG822Connection
    
    # Known working resource (update this if your device has a different ID)
    KNOWN_RESOURCE = 'USB0::0x1AB1::0x0643::DG8A204201757::0::INSTR'
    
    print("=" * 60)
    print("DG822 Output Module - Evaluation Mode")
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
        # Create output controller
        out = DG822Output(conn)
        
        print("\n" + "-" * 60)
        print("Testing Output Control")
        print("-" * 60)
        
        # Query current states
        print("\n1. Querying current output states...")
        states = out.get_all_states()
        for key, value in states.items():
            print(f"   {key}: {value}")
        
        # Test enable/disable
        print("\n2. Testing output enable/disable...")
        print("   Enabling CH1...")
        out.enable(1)
        print(f"   CH1 Enabled: {out.is_enabled(1)}")
        
        print("   Disabling CH1...")
        out.disable(1)
        print(f"   CH1 Enabled: {out.is_enabled(1)}")
        
        # Test impedance
        print("\n3. Testing impedance settings...")
        print("   Setting CH1 to 50 Ohm...")
        out.set_impedance_50_ohm(1)
        print(f"   CH1 Impedance: {out.get_impedance(1)} Ohm")
        
        print("   Setting CH1 to High-Z...")
        out.set_impedance_high_z(1)
        imp = out.get_impedance(1)
        if imp == float('inf'):
            print("   CH1 Impedance: High-Z")
        else:
            print(f"   CH1 Impedance: {imp} Ohm")
        
        # Test polarity
        print("\n4. Testing polarity settings...")
        print("   Setting CH1 to inverted...")
        out.set_polarity_inverted(1)
        print(f"   CH1 Polarity: {out.get_polarity(1)}")
        
        print("   Setting CH1 to normal...")
        out.set_polarity_normal(1)
        print(f"   CH1 Polarity: {out.get_polarity(1)}")
        
        # Test sync
        print("\n5. Testing sync output...")
        print("   Enabling sync...")
        out.enable_sync(1)
        print(f"   Sync Enabled: {out.get_sync_state(1)}")
        
        print("   Disabling sync...")
        out.disable_sync(1)
        print(f"   Sync Enabled: {out.get_sync_state(1)}")
        
        print("\n" + "-" * 60)
    else:
        print("Connection failed!")
    
    # Clean up connection and resource manager
    conn.close()
    
    print("\n" + "=" * 60)
    print("Evaluation complete.")
    print("=" * 60)
