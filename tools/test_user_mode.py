"""Quick test of USER mode commands on newer firmware."""
import pyvisa
import time

rm = pyvisa.ResourceManager()
inst = rm.open_resource('USB0::0x1AB1::0x0643::DG8A252001971::0::INSTR')
inst.timeout = 5000
ch = 1

# Clear any stuck state
try:
    inst.write('*CLS')
    time.sleep(0.3)
    inst.write('*RST')
    time.sleep(2)
    inst.query('*OPC?')
except:
    pass

def q(cmd):
    try:
        return inst.query(cmd).strip()
    except Exception as e:
        # Try to clear error state
        try:
            inst.write('*CLS')
            time.sleep(0.2)
        except:
            pass
        return f"ERROR: {e}"

def w(cmd):
    try:
        inst.write(cmd)
        return True
    except Exception as e:
        print(f"  Write error: {e}")
        return False

print('=== After *RST ===')
print('Function:', q(f':SOURce{ch}:FUNCtion?'))
print('Frequency:', q(f':SOURce{ch}:FREQuency?'))

# First upload a 32-pt square wave to get into USER/arb mode
import struct, numpy as np
N = 32
data = np.zeros(N); data[:N//2] = 1.0; data[N//2:] = -1.0
dac = np.round((data + 1.0) / 2.0 * 16383).astype(np.uint16)
dac = np.clip(dac, 0, 0x3FFF)
binary = struct.pack(f'<{N}H', *dac)
bc = str(len(binary))
hdr = f':SOURce{ch}:TRACe:DATA:DAC16 VOLATILE,END,#{len(bc)}{bc}'
inst.write_raw(hdr.encode('ascii') + binary + b'\n')
time.sleep(0.5)
print('OPC after upload:', q('*OPC?'))
print('Function after upload:', q(f':SOURce{ch}:FUNCtion?'))

# Test 1: Can we set frequency directly in USER mode?
print()
print('=== Test 1: Set frequency to 1000 Hz in USER mode ===')
w(f':SOURce{ch}:FREQuency 1000')
time.sleep(0.2)
print('Freq after set:', q(f':SOURce{ch}:FREQuency?'))
print('Function:', q(f':SOURce{ch}:FUNCtion?'))

# Test 2: Try setting frequency to 500 Hz
print()
print('=== Test 2: Set frequency to 500 Hz ===')
w(f':SOURce{ch}:FREQuency 500')
time.sleep(0.2)
print('Freq after set:', q(f':SOURce{ch}:FREQuency?'))

# Test 3: Try switching to SEQuence mode explicitly
print()
print('=== Test 3: Switch to SEQUENCE mode via :FUNCtion SEQuence ===')
w(f':SOURce{ch}:FUNCtion SEQuence')
time.sleep(0.3)
func = q(f':SOURce{ch}:FUNCtion?')
print('Function after:', func)

if 'SEQ' in func.upper():
    print('  SUCCESS! Now try SEQ sample rate...')
    w(f':SOURce{ch}:FUNCtion:SEQuence:SRATe 32000')
    time.sleep(0.1)
    print('  SEQ SRate:', q(f':SOURce{ch}:FUNCtion:SEQuence:SRATe?'))
else:
    print('  Did not switch. Trying :FUNCtion:SEQuence:FILTer?...')
    print('  Filter:', q(f':SOURce{ch}:FUNCtion:SEQuence:FILTer?'))

# Test 4: Query current sample rate via different commands
print()
print('=== Test 4: Sample rate queries ===')
print('SEQ SRate:', q(f':SOURce{ch}:FUNCtion:SEQuence:SRATe?'))
print('FREQ:', q(f':SOURce{ch}:FREQuency?'))

# Test 5: Try :APPLy:USER (yes we know it might reset, but let's see)
print()
print('=== Test 5: What does :APPLy:USER do on this firmware? ===')
w(f':SOURce{ch}:APPLy:USER 1000,5,0')
time.sleep(0.3)
func = q(f':SOURce{ch}:FUNCtion?')
print('Function after :APPLy:USER:', func)
print('Freq:', q(f':SOURce{ch}:FREQuency?'))

# Test 6: Check if :APPLy:ARBitrary exists
print()
print('=== Test 6: :APPLy:ARBitrary? ===')
w(f':SOURce{ch}:APPLy:ARBitrary 1000,5,0')
time.sleep(0.3)
func = q(f':SOURce{ch}:FUNCtion?')
print('Function after :APPLy:ARBitrary:', func)

inst.close()
print('\nDone.')
