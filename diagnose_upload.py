"""
Diagnose why DAC16 upload doesn't switch mode from SIN.
Tests different data sizes and connection states.
"""
import pyvisa
import time
import struct
import numpy as np

VISA = "USB0::0x1AB1::0x0643::DG8A252001971::0::INSTR"
CH = 1

rm = pyvisa.ResourceManager()
inst = rm.open_resource(VISA)
inst.timeout = 10000

def q(cmd):
    try:
        r = inst.query(cmd).strip()
        return r
    except Exception as e:
        try:
            inst.write('*CLS')
            time.sleep(0.3)
        except:
            pass
        return f"ERROR: {e}"

def upload_dac16(n_points):
    """Upload n_points square wave via DAC16. Return (success, mode_after)."""
    data = np.zeros(n_points)
    data[:n_points//2] = 1.0
    data[n_points//2:] = -1.0
    dac = np.round((data + 1.0) / 2.0 * 16383).astype(np.uint16)
    dac = np.clip(dac, 0, 0x3FFF)
    binary = struct.pack(f'<{n_points}H', *dac)
    bc = str(len(binary))
    header = f':SOURce{CH}:TRACe:DATA:DAC16 VOLATILE,END,#{len(bc)}{bc}'
    cmd = header.encode('ascii') + binary + b'\n'
    
    print(f"  Sending {len(cmd)} bytes ({n_points} pts, {len(binary)} binary bytes)...")
    
    # Check bytes actually written
    n_written = inst.write_raw(cmd)
    print(f"  write_raw returned: {n_written} (expected: {len(cmd)})")
    
    time.sleep(0.5)
    opc = q('*OPC?')
    print(f"  *OPC?: {opc}")
    
    # Check for errors
    err = q(':SYSTem:ERRor?')
    print(f"  :SYST:ERR?: {err}")
    
    mode = q(f':SOURce{CH}:FUNCtion?')
    print(f"  Mode: {mode}")
    return mode

# ── Reset to known state ──
print("=== Resetting instrument ===")
inst.write('*CLS')
time.sleep(0.2)
inst.write('*RST')
time.sleep(2)
q('*OPC?')
print(f"Mode after reset: {q(f':SOURce{CH}:FUNCtion?')}")

# ── Test 1: Small upload (32 points) ──
print(f"\n=== Test 1: 32 points ===")
mode = upload_dac16(32)
print(f"  Result: {'PASS' if 'SIN' not in mode.upper() else 'FAIL — still SIN'}")

# Reset
inst.write('*RST'); time.sleep(2); q('*OPC?')

# ── Test 2: Medium upload (1024 points) ──
print(f"\n=== Test 2: 1024 points ===")
mode = upload_dac16(1024)
print(f"  Result: {'PASS' if 'SIN' not in mode.upper() else 'FAIL — still SIN'}")

# Reset
inst.write('*RST'); time.sleep(2); q('*OPC?')

# ── Test 3: Large upload (16384 points) ──
print(f"\n=== Test 3: 16384 points ===")
mode = upload_dac16(16384)
print(f"  Result: {'PASS' if 'SIN' not in mode.upper() else 'FAIL — still SIN'}")

# ── Test 4: Try large upload with explicit chunk_size ──
print(f"\n=== Test 4: 16384 points with chunk_size=1048576 ===")
inst.write('*RST'); time.sleep(2); q('*OPC?')
old_chunk = inst.chunk_size
print(f"  Default chunk_size: {old_chunk}")
inst.chunk_size = 1024 * 1024  # 1 MB
mode = upload_dac16(16384)
inst.chunk_size = old_chunk
print(f"  Result: {'PASS' if 'SIN' not in mode.upper() else 'FAIL — still SIN'}")

# ── Test 5: Try with send_end=True explicitly ──
print(f"\n=== Test 5: 16384 points with send_end check ===")
inst.write('*RST'); time.sleep(2); q('*OPC?')
print(f"  send_end: {inst.send_end}")
print(f"  write_termination: {repr(inst.write_termination)}")
print(f"  read_termination: {repr(inst.read_termination)}")

# Try without the trailing \n and let PyVISA handle termination
data = np.zeros(16384)
data[:8192] = 1.0; data[8192:] = -1.0
dac = np.round((data + 1.0) / 2.0 * 16383).astype(np.uint16)
dac = np.clip(dac, 0, 0x3FFF)
binary = struct.pack(f'<16384H', *dac)
bc = str(len(binary))
header = f':SOURce{CH}:TRACe:DATA:DAC16 VOLATILE,END,#{len(bc)}{bc}'
# No trailing \n this time
cmd_no_nl = header.encode('ascii') + binary
print(f"  Sending {len(cmd_no_nl)} bytes (no trailing newline)...")
n = inst.write_raw(cmd_no_nl)
print(f"  write_raw returned: {n}")
time.sleep(0.5)
print(f"  *OPC?: {q('*OPC?')}")
print(f"  :SYST:ERR?: {q(':SYSTem:ERRor?')}")
mode = q(f':SOURce{CH}:FUNCtion?')
print(f"  Mode: {mode}")
print(f"  Result: {'PASS' if 'SIN' not in mode.upper() else 'FAIL — still SIN'}")

# ── Test 6: Use visa write_binary_values instead ──
print(f"\n=== Test 6: 16384 pts via inst.write_binary_values ===")
inst.write('*RST'); time.sleep(2); q('*OPC?')
try:
    # Construct just the SCPI header without block data
    hdr_cmd = f':SOURce{CH}:TRACe:DATA:DAC16 VOLATILE,END,'
    inst.write_binary_values(hdr_cmd, dac, datatype='H', 
                             is_big_endian=False, header_fmt='ieee')
    time.sleep(0.5)
    print(f"  *OPC?: {q('*OPC?')}")
    mode = q(f':SOURce{CH}:FUNCtion?')
    print(f"  Mode: {mode}")
    print(f"  Result: {'PASS' if 'SIN' not in mode.upper() else 'FAIL — still SIN'}")
except Exception as e:
    print(f"  ERROR: {e}")

inst.close()
print("\nDone.")
