"""Verify: upload DAC16 + set frequency directly = working arb output."""
import pyvisa, time, struct
import numpy as np

rm = pyvisa.ResourceManager()
inst = rm.open_resource('USB0::0x1AB1::0x0643::DG8A252001971::0::INSTR')
inst.timeout = 5000
ch = 1

def q(cmd):
    try:
        return inst.query(cmd).strip()
    except Exception as e:
        try: inst.write('*CLS'); time.sleep(0.2)
        except: pass
        return f"ERROR: {e}"

# Reset
inst.write('*CLS'); time.sleep(0.2)

print(f'IDN: {q("*IDN?")}')
print(f'Mode before: {q(f":SOURce{ch}:FUNCtion?")}')

# Upload a 1024-point square wave
N = 1024
data = np.zeros(N); data[:N//2] = 1.0; data[N//2:] = -1.0
dac = np.round((data + 1.0) / 2.0 * 16383).astype(np.uint16)
dac = np.clip(dac, 0, 0x3FFF)
binary = struct.pack(f'<{N}H', *dac)
bc = str(len(binary))
hdr = f':SOURce{ch}:TRACe:DATA:DAC16 VOLATILE,END,#{len(bc)}{bc}'
inst.write_raw(hdr.encode('ascii') + binary + b'\n')
time.sleep(0.5)
print(f'OPC: {q("*OPC?")}')
print(f'Mode after upload: {q(f":SOURce{ch}:FUNCtion?")}')

# Set frequency DIRECTLY (not via sample rate)
target_freq = 1000.0
inst.write(f':SOURce{ch}:FREQuency {target_freq}')
time.sleep(0.2)
print(f'Freq readback: {q(f":SOURce{ch}:FREQuency?")}')

# Set amplitude, offset, phase
inst.write(f':SOURce{ch}:VOLTage 5.0')
inst.write(f':SOURce{ch}:VOLTage:OFFSet 0')
inst.write(f':SOURce{ch}:PHASe 0')
time.sleep(0.2)

print(f'Amp: {q(f":SOURce{ch}:VOLTage?")}')
print(f'Offset: {q(f":SOURce{ch}:VOLTage:OFFSet?")}')
print(f'Mode final: {q(f":SOURce{ch}:FUNCtion?")}')

# Turn output ON
inst.write(f':OUTPut{ch} ON')
time.sleep(0.2)
print(f'Output: {q(f":OUTPut{ch}?")}')

print()
print('CHECK THE FRONT PANEL: You should see a 1kHz square arb wave on CH1.')
print('If you see it, the fix is to use :FREQuency instead of :SEQuence:SRATe!')

inst.close()
