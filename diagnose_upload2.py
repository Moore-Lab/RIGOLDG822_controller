"""Focused test: reset then upload 16384 points. Does mode change?"""
import pyvisa, time, struct, numpy as np

VISA = "USB0::0x1AB1::0x0643::DG8A252001971::0::INSTR"
rm = pyvisa.ResourceManager()
inst = rm.open_resource(VISA)
inst.timeout = 15000

print(f"IDN: {inst.query('*IDN?').strip()}")
print(f"chunk_size: {inst.chunk_size}")
print(f"send_end: {inst.send_end}")

# Reset
print("\nResetting...")
inst.write('*RST')
time.sleep(3)
print(f"OPC: {inst.query('*OPC?').strip()}")
print(f"Mode: {inst.query(':SOURce1:FUNCtion?').strip()}")

# Upload 16384 points
n = 16384
data = np.zeros(n); data[:n//2] = 1.0; data[n//2:] = -1.0
dac = np.round((data + 1.0) / 2.0 * 16383).astype(np.uint16)
dac = np.clip(dac, 0, 0x3FFF)
binary = struct.pack(f'<{n}H', *dac)
bc = str(len(binary))
header = f':SOURce1:TRACe:DATA:DAC16 VOLATILE,END,#{len(bc)}{bc}'
cmd = header.encode('ascii') + binary + b'\n'

print(f"\nUploading {n} pts ({len(cmd)} bytes total)...")
t0 = time.time()
nw = inst.write_raw(cmd)
dt = time.time() - t0
print(f"write_raw took {dt:.3f}s, returned: {nw}")

time.sleep(1)
print(f"OPC: {inst.query('*OPC?').strip()}")
err = inst.query(':SYSTem:ERRor?').strip()
print(f"Error: {err}")
mode = inst.query(':SOURce1:FUNCtion?').strip()
print(f"Mode: {mode}")

if 'SIN' in mode.upper():
    print("\n--- SIZE STILL SIN. Trying smaller sizes ---")
    for sz in [8192, 4096, 2048, 1024, 512, 256, 128, 64]:
        inst.write('*RST')
        time.sleep(3)
        inst.query('*OPC?')
        d = np.zeros(sz); d[:sz//2] = 1.0; d[sz//2:] = -1.0
        dv = np.round((d + 1.0) / 2.0 * 16383).astype(np.uint16)
        dv = np.clip(dv, 0, 0x3FFF)
        b = struct.pack(f'<{sz}H', *dv)
        bcs = str(len(b))
        h = f':SOURce1:TRACe:DATA:DAC16 VOLATILE,END,#{len(bcs)}{bcs}'
        c = h.encode('ascii') + b + b'\n'
        nw2 = inst.write_raw(c)
        time.sleep(1)
        inst.query('*OPC?')
        m = inst.query(':SOURce1:FUNCtion?').strip()
        print(f"  {sz:>5} pts ({len(c):>6} bytes) -> {m}  {'PASS' if 'SIN' not in m.upper() else 'FAIL'}")
        if 'SIN' not in m.upper():
            print(f"  THRESHOLD: {sz} works, {sz*2} doesn't")
            break
else:
    print("\n16384 pts uploaded OK!")

inst.close()
print("Done.")
