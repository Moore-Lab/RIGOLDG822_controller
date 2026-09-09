"""Find max upload size. No *RST between tests."""
import pyvisa, time, struct, numpy as np

VISA = "USB0::0x1AB1::0x0643::DG8A252001971::0::INSTR"
rm = pyvisa.ResourceManager()
inst = rm.open_resource(VISA)
inst.timeout = 10000

print(f"IDN: {inst.query('*IDN?').strip()}")

# Single reset at start
inst.write('*CLS')
inst.write('*RST')
time.sleep(3)
inst.query('*OPC?')
print(f"Mode after RST: {inst.query(':SOURce1:FUNCtion?').strip()}")

# Test sizes from small to large
for sz in [32, 64, 128, 256, 512, 1024, 2048, 4096, 8192, 16384]:
    # Clear errors and switch back to SIN
    inst.write('*CLS')
    time.sleep(0.2)
    inst.write(':SOURce1:FUNCtion SIN')
    time.sleep(0.3)
    inst.write('*CLS')
    time.sleep(0.2)
    
    # Generate data
    d = np.zeros(sz); d[:sz//2] = 1.0; d[sz//2:] = -1.0
    dac = np.round((d + 1.0) / 2.0 * 16383).astype(np.uint16)
    dac = np.clip(dac, 0, 0x3FFF)
    b = struct.pack(f'<{sz}H', *dac)
    bcs = str(len(b))
    h = f':SOURce1:TRACe:DATA:DAC16 VOLATILE,END,#{len(bcs)}{bcs}'
    cmd = h.encode('ascii') + b + b'\n'
    
    inst.write_raw(cmd)
    time.sleep(0.5)
    try:
        inst.query('*OPC?')
    except:
        time.sleep(1)
        try: inst.query('*OPC?')  
        except: pass
    
    err = inst.query(':SYSTem:ERRor?').strip()
    mode = inst.query(':SOURce1:FUNCtion?').strip()
    ok = 'SIN' not in mode.upper()
    print(f"  {sz:>5} pts  {len(cmd):>6} bytes  ->  {mode:<10}  err={err:<25}  {'OK' if ok else 'FAIL'}")
    
    if not ok and sz > 32:
        prev = sz // 2
        print(f"\n  >> Max working size: {prev} pts ({prev*2} bytes binary)")
        break

inst.close()
print("Done.")
