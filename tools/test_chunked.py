"""Test CON/END chunked upload for 16384 points."""
import pyvisa, time, struct, numpy as np

VISA = "USB0::0x1AB1::0x0643::DG8A252001971::0::INSTR"
rm = pyvisa.ResourceManager()
inst = rm.open_resource(VISA)
inst.timeout = 15000

print(f"IDN: {inst.query('*IDN?').strip()}")

# Generate 16384-pt square wave
n = 16384
d = np.zeros(n); d[:n//2] = 1.0; d[n//2:] = -1.0
dac = np.round((d + 1.0) / 2.0 * 16383).astype(np.uint16)
dac = np.clip(dac, 0, 0x3FFF)
binary = struct.pack(f'<{n}H', *dac)

# Reset to SIN
inst.write('*CLS')
inst.write(':SOURce1:FUNCtion SIN')
time.sleep(0.5)
inst.write('*CLS')
time.sleep(0.2)
print(f"Mode before: {inst.query(':SOURce1:FUNCtion?').strip()}")

# ---- Method 1: Two chunks of 8192 pts (CON then END) ----
print("\n=== Method 1: CON(8192) + END(8192) ===")
half = n // 2  # 8192 points
chunk1 = binary[:half * 2]  # first 8192 pts = 16384 bytes
chunk2 = binary[half * 2:]  # last 8192 pts = 16384 bytes

# Chunk 1 with CON flag
bc1 = str(len(chunk1))
hdr1 = f':SOURce1:TRACe:DATA:DAC16 VOLATILE,CON,#{len(bc1)}{bc1}'
cmd1 = hdr1.encode('ascii') + chunk1 + b'\n'
print(f"  Sending CON chunk: {len(cmd1)} bytes ({half} pts)...")
nw1 = inst.write_raw(cmd1)
print(f"  write_raw returned: {nw1}")
time.sleep(0.5)
err1 = inst.query(':SYSTem:ERRor?').strip()
print(f"  Error: {err1}")

if '0,"No error"' in err1:
    # Chunk 2 with END flag
    bc2 = str(len(chunk2))
    hdr2 = f':SOURce1:TRACe:DATA:DAC16 VOLATILE,END,#{len(bc2)}{bc2}'
    cmd2 = hdr2.encode('ascii') + chunk2 + b'\n'
    print(f"  Sending END chunk: {len(cmd2)} bytes ({half} pts)...")
    nw2 = inst.write_raw(cmd2)
    print(f"  write_raw returned: {nw2}")
    time.sleep(1)
    try: inst.query('*OPC?')
    except: pass
    err2 = inst.query(':SYSTem:ERRor?').strip()
    mode = inst.query(':SOURce1:FUNCtion?').strip()
    print(f"  Error: {err2}")
    print(f"  Mode: {mode}")
    print(f"  Result: {'PASS' if 'SIN' not in mode.upper() else 'FAIL'}")
else:
    print(f"  CON chunk failed, skipping END")

# ---- Method 2: Four chunks of 4096 pts ----
print("\n=== Method 2: CON(4096) x3 + END(4096) ===")
inst.write('*CLS'); time.sleep(0.2)
inst.write(':SOURce1:FUNCtion SIN'); time.sleep(0.3)
inst.write('*CLS'); time.sleep(0.2)

qtr = n // 4  # 4096 points per chunk
chunks = [binary[i * qtr * 2:(i + 1) * qtr * 2] for i in range(4)]

for i, chunk in enumerate(chunks):
    flag = 'END' if i == 3 else 'CON'
    bc = str(len(chunk))
    hdr = f':SOURce1:TRACe:DATA:DAC16 VOLATILE,{flag},#{len(bc)}{bc}'
    cmd = hdr.encode('ascii') + chunk + b'\n'
    print(f"  Chunk {i+1}/4 ({flag}): {len(cmd)} bytes ({qtr} pts)...")
    inst.write_raw(cmd)
    time.sleep(0.3)
    err = inst.query(':SYSTem:ERRor?').strip()
    print(f"    Error: {err}")
    if '0,"No error"' not in err:
        print(f"  FAILED at chunk {i+1}")
        break

time.sleep(0.5)
try: inst.query('*OPC?')
except: pass
mode = inst.query(':SOURce1:FUNCtion?').strip()
print(f"  Final Mode: {mode}")
print(f"  Result: {'PASS' if 'SIN' not in mode.upper() else 'FAIL'}")

if 'SIN' not in mode.upper():
    # Verify we can set frequency
    inst.write(':SOURce1:FREQuency 1000')
    time.sleep(0.3)
    freq = inst.query(':SOURce1:FREQuency?').strip()
    print(f"  Freq: {freq} Hz")
    inst.write(':OUTPut1 ON')
    print("  Output ON - CHECK FRONT PANEL")

inst.close()
print("\nDone.")
