"""
RIGOL DG822 Waveform Generator - Connection Module

This module handles VISA communication with the RIGOL DG822/DG800 Pro series
waveform generators. It provides device discovery, connection management,
and low-level SCPI command communication.

Author: Auto-generated
Date: 2026-01-08
"""

import pyvisa
from typing import Optional, List, Tuple
import threading
import time


class DG822Connection:
    """
    Manages VISA connection to RIGOL DG822 waveform generator.
    
    This class handles:
    - Device discovery and listing
    - Connection establishment and teardown
    - Low-level SCPI command sending and querying
    - Error checking and status queries
    """
    
    # RIGOL manufacturer ID string for identification
    RIGOL_ID = "Rigol"
    DG800_MODELS = ["DG821", "DG822", "DG852", "DG902", "DG912", "DG922"]
    
    def __init__(self, resource_name: Optional[str] = None, timeout: int = 5000):
        """
        Initialize the connection object.
        
        Args:
            resource_name: VISA resource string (e.g., 'USB0::0x1AB1::0x0643::DG8...::INSTR')
                          If None, use discover_devices() and connect() later.
            timeout: Communication timeout in milliseconds (default: 5000ms)
        """
        self._rm: Optional[pyvisa.ResourceManager] = None
        self._instrument: Optional[pyvisa.resources.Resource] = None
        self._resource_name: Optional[str] = resource_name
        self._timeout = timeout
        self._connected = False
        self._idn_string: Optional[str] = None
        
    @property
    def is_connected(self) -> bool:
        """Return True if connected to instrument."""
        return self._connected
    
    @property
    def idn(self) -> Optional[str]:
        """Return the instrument identification string."""
        return self._idn_string
    
    @property
    def resource_name(self) -> Optional[str]:
        """Return the current VISA resource name."""
        return self._resource_name
    
    def _init_resource_manager(self, backend: str = '') -> None:
        """
        Initialize the VISA resource manager if not already initialized.
        
        Args:
            backend: VISA backend to use. Options:
                     '' = auto-detect (tries NI-VISA first, then pyvisa-py)
                     '@py' = force pyvisa-py backend
                     '@ni' = force NI-VISA backend
        """
        if self._rm is None:
            try:
                self._rm = pyvisa.ResourceManager(backend)
                print(f"Using VISA backend: {self._rm.visalib}")
            except Exception as e:
                print(f"Error initializing ResourceManager with '{backend}': {e}")
                # Try fallback to pyvisa-py
                if backend != '@py':
                    try:
                        self._rm = pyvisa.ResourceManager('@py')
                        print(f"Fallback to pyvisa-py backend: {self._rm.visalib}")
                    except Exception as e2:
                        print(f"Fallback also failed: {e2}")
                        raise
    
    def list_resources(self, query: str = '?*::INSTR') -> List[str]:
        """
        List available VISA resources without querying them.
        
        Args:
            query: VISA resource query pattern (default: all instruments)
                   '?*::INSTR' = all instruments
                   'USB?*::INSTR' = USB instruments only
                   'TCPIP?*::INSTR' = LAN instruments only
            
        Returns:
            List of resource strings
        """
        self._init_resource_manager()
        try:
            resources = list(self._rm.list_resources(query))
            print(f"Found {len(resources)} VISA resource(s): {resources}")
            return resources
        except Exception as e:
            print(f"Error listing resources: {e}")
            return []
    
    def discover_devices(self, filter_rigol: bool = True, query: str = 'USB?*::INSTR') -> List[Tuple[str, str]]:
        """
        Discover available VISA instruments by querying each one.
        
        Args:
            filter_rigol: If True, only return RIGOL DG800/DG900 series devices
            query: VISA resource query pattern (default: USB instruments only)
            
        Returns:
            List of tuples: (resource_name, idn_string)
        """
        self._init_resource_manager()
        devices = []
        
        try:
            resources = self._rm.list_resources(query)
            # Filter out serial ports (ASRL) which can cause hangs
            resources = [r for r in resources if not r.startswith('ASRL')]
            print(f"Scanning {len(resources)} USB resource(s)...")
        except Exception as e:
            print(f"Error listing resources: {e}")
            return devices
        
        for resource in resources:
            print(f"  Trying: {resource}...", end=" ")
            
            # Use a thread with timeout to avoid hanging
            result = {"idn": None, "error": None, "instr": None}
            
            def query_device():
                try:
                    instr = self._rm.open_resource(resource)
                    result["instr"] = instr  # Store for cleanup
                    instr.timeout = 2000  # Short timeout for discovery
                    instr.read_termination = '\n'
                    instr.write_termination = '\n'
                    result["idn"] = instr.query("*IDN?").strip()
                except Exception as e:
                    result["error"] = e
                finally:
                    # Always try to close the resource
                    if result["instr"] is not None:
                        try:
                            result["instr"].close()
                        except Exception:
                            pass
                    result["instr"] = None
            
            thread = threading.Thread(target=query_device)
            thread.daemon = True
            thread.start()
            thread.join(timeout=2)  # Wait max 2 seconds
            
            if thread.is_alive():
                print("TIMEOUT (>2s) - skipping")
                # Try to close any dangling resource
                if result["instr"] is not None:
                    try:
                        result["instr"].close()
                    except Exception:
                        pass
                continue
            
            # Skip devices that caused errors (busy, not responding, etc.)
            if result["error"] is not None:
                print(f"ERROR: {result['error']} - skipping")
                continue
            
            idn = result["idn"]
            if idn is None:
                print("No response - skipping")
                continue
                
            print(f"OK - {idn[:40]}...")
            
            # Filter for RIGOL DG800/DG900 series if requested
            if filter_rigol:
                # Case-insensitive check for RIGOL
                if self.RIGOL_ID.upper() in idn.upper():
                    # Check if it's a DG800/DG900 series
                    for model in self.DG800_MODELS:
                        if model in idn:
                            devices.append((resource, idn))
                            print("   -> RIGOL DG800/DG900 series found.")
                            break
            else:
                devices.append((resource, idn))
                
        return devices
    
    def connect(self, resource_name: Optional[str] = None) -> bool:
        """
        Connect to the instrument.
        
        Args:
            resource_name: VISA resource string. If None, uses the one from __init__
            
        Returns:
            True if connection successful, False otherwise
        """
        if resource_name:
            self._resource_name = resource_name
            
        if not self._resource_name:
            print("Error: No resource name specified")
            return False
        
        self._init_resource_manager()
        
        try:
            self._instrument = self._rm.open_resource(self._resource_name)
            self._instrument.timeout = self._timeout
            
            # Configure for proper line termination
            self._instrument.read_termination = '\n'
            self._instrument.write_termination = '\n'
            
            # Clear any pending data in the buffer
            try:
                self._instrument.clear()
            except Exception:
                pass  # Some backends don't support clear
            
            # Query identification to verify connection
            self._idn_string = self.query("*IDN?")
            
            if self._idn_string:
                self._connected = True
                print(f"Connected to: {self._idn_string}")
                return True
            else:
                print("Error: No response from instrument")
                return False
                
        except Exception as e:
            print(f"Connection error: {e}")
            self._connected = False
            return False
    
    def disconnect(self) -> None:
        """Disconnect from the instrument."""
        if self._instrument:
            try:
                self._instrument.close()
            except Exception:
                pass
            self._instrument = None
        self._connected = False
        self._idn_string = None
        print("Disconnected from instrument")
    
    def write(self, command: str) -> bool:
        """
        Send a SCPI command to the instrument (no response expected).
        
        Args:
            command: SCPI command string
            
        Returns:
            True if successful, False otherwise
        """
        if not self._connected or not self._instrument:
            print("Error: Not connected to instrument")
            return False
        
        try:
            self._instrument.write(command)
            return True
        except Exception as e:
            print(f"Write error: {e}")
            return False
    
    def query(self, command: str) -> Optional[str]:
        """
        Send a SCPI query and return the response.
        
        Args:
            command: SCPI query string (should end with '?')
            
        Returns:
            Response string, or None if error
        """
        if not self._connected or not self._instrument:
            # Allow query during connection phase
            if self._instrument is None:
                print("Error: Not connected to instrument")
                return None
        
        try:
            response = self._instrument.query(command).strip()
            return response
        except Exception as e:
            print(f"Query error: {e}")
            return None
    
    def reset(self) -> bool:
        """
        Reset the instrument to default settings.
        
        Returns:
            True if successful
        """
        return self.write("*RST")
    
    def clear_status(self) -> bool:
        """
        Clear the instrument status registers.
        
        Returns:
            True if successful
        """
        return self.write("*CLS")
    
    def get_error(self) -> Optional[str]:
        """
        Query the instrument error queue.
        
        Returns:
            Error string, or None if no error or query failed
        """
        return self.query(":SYSTem:ERRor?")
    
    def get_version(self) -> Optional[str]:
        """
        Query the instrument firmware version.
        
        Returns:
            Version string
        """
        return self.query(":SYSTem:VERSion?")
    
    def beep(self) -> bool:
        """
        Make the instrument beep (useful for testing connection).
        
        Returns:
            True if successful
        """
        return self.write(":SYSTem:BEEPer:IMMediate")
    
    def wait_for_operation_complete(self) -> bool:
        """
        Wait for all pending operations to complete.
        
        Returns:
            True when operations complete
        """
        response = self.query("*OPC?")
        return response == "1"
    
    def __enter__(self):
        """Context manager entry."""
        if self._resource_name and not self._connected:
            self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()
        return False
    
    def close(self) -> None:
        """
        Close the connection and resource manager.
        Call this when completely done with the connection object.
        """
        self.disconnect()
        if self._rm:
            try:
                self._rm.close()
            except Exception:
                pass
            self._rm = None
    
    def __del__(self):
        """Destructor - ensure clean disconnect (silent)."""
        # Only clean up if not already closed
        if self._rm is not None:
            try:
                self.close()
            except Exception:
                pass


# =============================================================================
# Module Test / Evaluation Mode
# =============================================================================
if __name__ == "__main__":
    import time
    
    # Known working resource (update this if your device has a different ID)
    KNOWN_RESOURCE = 'USB0::0x1AB1::0x0643::DG8A204201757::0::INSTR'
    
    print("=" * 60)
    print("DG822 Connection Module - Evaluation Mode")
    print("=" * 60)
    
    # Create connection object
    conn = DG822Connection()
    
    # Step 1: Show available backends
    print("\n--- VISA Backend Information ---")
    try:
        rm_default = pyvisa.ResourceManager()
        print(f"Default backend: {rm_default.visalib}")
        rm_default.close()
    except Exception as e:
        print(f"Default backend failed: {e}")
    
    # Step 2: List raw resources (no query)
    print("\n--- Listing VISA Resources ---")
    resources = conn.list_resources()
    
    # Step 3: Connect directly to known resource
    print("\n--- Connecting to Device ---")
    print(f"Using resource: {KNOWN_RESOURCE}")
    
    if conn.connect(KNOWN_RESOURCE):
        print(f"\nConnection successful!")
        print(f"IDN: {conn.idn}")
        
        # Give device time to settle
        time.sleep(0.2)
        
        # Test some basic queries
        print("\n--- Testing Basic Queries ---")
        
        # Try *OPC? which is standard IEEE 488.2
        time.sleep(0.1)
        opc = conn.query("*OPC?")
        print(f"Operation Complete (*OPC?): {opc}")
        
        # Try to get current waveform settings on CH1
        time.sleep(0.1)
        apply = conn.query(":SOURce1:APPLy?")
        print(f"CH1 Waveform Settings: {apply}")
        
        # Check for errors
        time.sleep(0.1)
        error = conn.get_error()
        print(f"Error Status: {error}")
        
        # Test beep
        print("\n--- Testing Beep ---")
        print("Sending beep command...")
        if conn.beep():
            print("Beep command sent!")
        
        # Give beep time to sound
        time.sleep(0.5)
        
        # Test reset
        print("\n--- Testing Reset ---")
        if conn.reset():
            print("Reset command sent!")
    else:
        print("Connection failed!")
        print("\nTrying device discovery...")
        devices = conn.discover_devices()
        if devices:
            print(f"Found: {devices[0][1]}")
            print(f"Resource: {devices[0][0]}")
            print("Update KNOWN_RESOURCE with this resource string.")
    
    # Clean up connection and resource manager
    conn.close()
    
    print("\n" + "=" * 60)
    print("Evaluation complete.")
    print("=" * 60)
