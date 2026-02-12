"""
Verify that CON/END upload only keeps the END chunk.
Upload an asymmetric 16384-pt ramp via CON/END,
then upload an 8192-pt single-END matching just the second half.
Compare instrument output frequency readback to infer which data is used.

Also test: does a single 8192-pt upload produce correct trapezoid output?
"""
import pyvisa, time, struct, numpy as np

VISA = "USB0::0x1AB1::0x0643::DG8A252001971::0::INSTR"
rm = pyvisa.ResourceManager()
inst = rm.open_resource(VISA)
inst.timeout = 15000

def upload_single(data_uint16, flag="END"):
    """Upload data as a single DAC16 packet."""
    binary = struct.pack(f'<{len(data_uint16)}H', *data_uint16)
    bc = str(len(binary))
    hdr = f':SOURce1:TRACe:DATA:DAC16 VOLATILE,{flag},#{len(bc)}{bc}'
    cmd = hdr.encode('ascii') + binary + b'\n'
    inst.write_raw(cmd)
    time.sleep(0.5)
    return inst.query('*OPC?').strip()

def upload_chunked(data_uint16, chunk_size=8192):
    """Upload data in CON/END chunks."""
    binary = struct.pack(f'<{len(data_uint16)}H', *data_uint16)
    n = len(data_uint16)
    n_chunks = (n + chunk_size - 1) // chunk_size
    for i in range(n_chunks):
        s = i * chunk_size
        e = min(s + chunk_size, n)
        chunk = binary[s*2:e*2]
        flag = "END" if i == n_chunks - 1 else "CON"
        bc = str(len(chunk))
        hdr = f':SOURce1:TRACe:DATA:DAC16 VOLATILE,{flag},#{len(bc)}{bc}'
        cmd = hdr.encode('ascii') + chunk + b'\n'
        inst.write_raw(cmd)
        time.sleep(0.3)
    time.sleep(0.5)
    return inst.query('*OPC?').strip()

def reset():
    inst.write('*CLS')
    inst.write(':SOURce1:FUNCtion SIN')
    time.sleep(0.3)
    inst.write('*CLS')
    time.sleep(0.2)

print(f"IDN: {inst.query('*IDN?').strip()}")

# === Test: Upload 8192-pt trapezoid (single END, no chunking) ===
print("\n=== TEST: 8192-pt trapezoid (single END) ===")
reset()

n = 8192
rise = int(round(n * 0.2))
pulse = int(round(n * 0.6))
fall = n - rise - pulse

data = np.concatenate([
    np.linspace(-1, 1, rise, endpoint=False),   # rise
    np.ones(pulse),                                # high
    np.linspace(1, -1, fall + 1)[1:],             # fall
])
if len(data) < n:
    data = np.concatenate([data, -np.ones(n - len(data))])
data = data[:n]

dac = np.round((data + 1) / 2 * 16383).astype(np.uint16)
dac = np.clip(dac, 0, 0x3FFF)

upload_single(dac)
mode = inst.query(':SOURce1:FUNCtion?').strip()
err = inst.query(':SYSTem:ERRor?').strip()
print(f"  Mode: {mode}, Error: {err}")

inst.write(':SOURce1:FREQuency 1000')
inst.write(':SOURce1:VOLTage 5')
inst.write(':OUTPut1 ON')
time.sleep(0.5)
freq = inst.query(':SOURce1:FREQuency?').strip()
print(f"  Freq: {freq}")
print(f"  OUTPUT IS ON - Check scope for correct trapezoid (both rise AND fall should be gradual)")
input("  Press Enter after checking scope...")

# === Test: Upload what SECOND chunk would look like (single 8192) ===
print("\n=== TEST: Upload just second-chunk data (8192 pts, single END) ===")
reset()
inst.write(':OUTPut1 OFF')
time.sleep(0.2)

# The second chunk of a 16384-pt trapezoid would be:
# Original 16384 pts: rise=3277, pulse=9830, fall=3277
# Chunk 2 (indices 8192-16383): pulse_tail(4915) + fall(3277)
n2 = 8192
pulse_tail = 4915
fall2 = 3277
data2 = np.concatenate([
    np.ones(pulse_tail),                          # remaining pulse
    np.linspace(1, -1, fall2 + 1)[1:],           # fall
])
if len(data2) < n2:
    data2 = np.concatenate([data2, -np.ones(n2 - len(data2))])
data2 = data2[:n2]

dac2 = np.round((data2 + 1) / 2 * 16383).astype(np.uint16)
dac2 = np.clip(dac2, 0, 0x3FFF)

upload_single(dac2)
mode = inst.query(':SOURce1:FUNCtion?').strip()
print(f"  Mode: {mode}")

inst.write(':SOURce1:FREQuency 1000')
inst.write(':SOURce1:VOLTage 5')
inst.write(':OUTPut1 ON')
time.sleep(0.5)
print(f"  OUTPUT IS ON - This should look like: flat high, then fall, then sharp jump up")
print(f"  If this looks IDENTICAL to what you saw before (sharp rise, gradual fall), theory confirmed")
input("  Press Enter after checking scope...")

inst.write(':OUTPut1 OFF')
inst.close()
print("\nDone.")
