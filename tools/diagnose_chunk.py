"""Test if chunk_size is the root cause for 16384-pt failure."""
import pyvisa, time, struct, numpy as np

VISA = "USB0::0x1AB1::0x0643::DG8A252001971::0::INSTR"
rm = pyvisa.ResourceManager()
inst = rm.open_resource(VISA)
inst.timeout = 15000

print(f"Default chunk_size: {inst.chunk_size}")

# Generate 16384-pt square
n = 16384
d = np.zeros(n); d[:n//2] = 1.0; d[n//2:] = -1.0
dac = np.round((d + 1.0) / 2.0 * 16383).astype(np.uint16)
dac = np.clip(dac, 0, 0x3FFF)
binary = struct.pack(f'<{n}H', *dac)
bc = str(len(binary))
hdr = f':SOURce1:TRACe:DATA:DAC16 VOLATILE,END,#{len(bc)}{bc}'
cmd = hdr.encode('ascii') + binary + b'\n'
print(f"Command size: {len(cmd)} bytes")

# --- Test 1: Default chunk_size ---
print("\n--- Test 1: Default chunk_size (20480) ---")
inst.write('*CLS'); time.sleep(0.2)
inst.write(':SOURce1:FUNCtion SIN'); time.sleep(0.3)
inst.write('*CLS'); time.sleep(0.2)
inst.write_raw(cmd)
time.sleep(1)
try: inst.query('*OPC?')
except: pass
err = inst.query(':SYSTem:ERRor?').strip()
mode = inst.query(':SOURce1:FUNCtion?').strip()
print(f"  Mode: {mode}, Error: {err}")

# --- Test 2: Large chunk_size ---
print("\n--- Test 2: chunk_size = 1048576 ---")
inst.write('*CLS'); time.sleep(0.2)
inst.write(':SOURce1:FUNCtion SIN'); time.sleep(0.3)
inst.write('*CLS'); time.sleep(0.2)
inst.chunk_size = 1048576
inst.write_raw(cmd)
time.sleep(1)
try: inst.query('*OPC?')
except: pass
err = inst.query(':SYSTem:ERRor?').strip()
mode = inst.query(':SOURce1:FUNCtion?').strip()
print(f"  Mode: {mode}, Error: {err}")
inst.chunk_size = 20480  # restore

# --- Test 3: write_binary_values ---
print("\n--- Test 3: write_binary_values ---")
inst.write('*CLS'); time.sleep(0.2)
inst.write(':SOURce1:FUNCtion SIN'); time.sleep(0.3)
inst.write('*CLS'); time.sleep(0.2)
try:
    hdr_cmd = ':SOURce1:TRACe:DATA:DAC16 VOLATILE,END,'
    inst.write_binary_values(hdr_cmd, dac, datatype='H', 
                             is_big_endian=False, header_fmt='ieee')
    time.sleep(1)
    try: inst.query('*OPC?')
    except: pass
    err = inst.query(':SYSTem:ERRor?').strip()
    mode = inst.query(':SOURce1:FUNCtion?').strip()
    print(f"  Mode: {mode}, Error: {err}")
except Exception as e:
    print(f"  Exception: {e}")

inst.close()
print("\nDone.")
