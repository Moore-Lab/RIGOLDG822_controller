"""
DG822 Hardware Diagnostic — Compare two instruments.

Run this against each generator to identify firmware/model differences
that could explain why arb waveform upload works on one but not the other.

Usage:
  python diagnose_hw.py
  python diagnose_hw.py "USB0::0x1AB1::0x0643::SERIAL::0::INSTR"
"""
import sys
import time
import struct
import numpy as np

# ------------------------------------------------------------------
# Connection
# ------------------------------------------------------------------
def connect(resource=None):
    import pyvisa
    rm = pyvisa.ResourceManager()
    if resource is None:
        resources = rm.list_resources()
        print(f"Available VISA resources: {resources}")
        if not resources:
            print("No devices found!")
            sys.exit(1)
        resource = resources[0]
        print(f"Auto-selected: {resource}")
    inst = rm.open_resource(resource)
    inst.timeout = 10000
    return inst

# ------------------------------------------------------------------
# Queries
# ------------------------------------------------------------------
def query_safe(inst, cmd):
    try:
        return inst.query(cmd).strip()
    except Exception as e:
        return f"ERROR: {e}"

def write_safe(inst, cmd):
    try:
        inst.write(cmd)
        return True
    except Exception as e:
        print(f"  Write error ({cmd}): {e}")
        return False

# ------------------------------------------------------------------
# Main diagnostic
# ------------------------------------------------------------------
def diagnose(inst):
    print("=" * 65)
    print("DG822 HARDWARE DIAGNOSTIC")
    print("=" * 65)

    # Identity
    idn = query_safe(inst, "*IDN?")
    print(f"\n*IDN?           : {idn}")

    # Parse model from IDN (typically: RIGOL TECHNOLOGIES,DG822,serial,firmware)
    parts = [p.strip() for p in idn.split(",")]
    if len(parts) >= 4:
        print(f"  Manufacturer  : {parts[0]}")
        print(f"  Model         : {parts[1]}")
        print(f"  Serial        : {parts[2]}")
        print(f"  Firmware      : {parts[3]}")
    
    # System version
    sysver = query_safe(inst, ":SYSTem:VERSion?")
    print(f"\n:SYST:VERS?     : {sysver}")

    # Current function
    for ch in [1, 2]:
        func = query_safe(inst, f":SOURce{ch}:FUNCtion?")
        print(f"\nCH{ch} function    : {func}")
        freq = query_safe(inst, f":SOURce{ch}:FREQuency?")
        print(f"CH{ch} frequency   : {freq}")
        amp = query_safe(inst, f":SOURce{ch}:VOLTage?")
        print(f"CH{ch} amplitude   : {amp}")

    # ------------------------------------------------------------------
    # Arb waveform upload test (small 32-point square wave)
    # ------------------------------------------------------------------
    print("\n" + "-" * 65)
    print("ARBITRARY WAVEFORM UPLOAD TEST (CH1)")
    print("-" * 65)

    ch = 1

    # Generate a simple 32-point square wave: first half high, second half low
    N = 32
    data = np.zeros(N, dtype=np.float64)
    data[:N//2] = 1.0    # first half = +1
    data[N//2:] = -1.0   # second half = -1

    # Convert to unsigned 14-bit DAC: 0x0000–0x3FFF
    dac_14bit = np.round((data + 1.0) / 2.0 * 16383).astype(np.uint16)
    dac_14bit = np.clip(dac_14bit, 0, 0x3FFF)
    print(f"\n  Waveform      : {N}-point square wave")
    print(f"  DAC range     : {dac_14bit.min()} – {dac_14bit.max()}  (expected 0 – 16383)")
    print(f"  First 8 DAC   : {list(dac_14bit[:8])}")
    print(f"  Last 8 DAC    : {list(dac_14bit[-8:])}")

    # Build binary block
    binary_data = struct.pack(f'<{N}H', *dac_14bit)
    byte_count = len(binary_data)
    byte_count_str = str(byte_count)
    num_digits = len(byte_count_str)

    header = f":SOURce{ch}:TRACe:DATA:DAC16 VOLATILE,END,"
    block_header = f"#{num_digits}{byte_count_str}"
    cmd_bytes = header.encode('ascii') + block_header.encode('ascii') + binary_data + b'\n'

    print(f"\n  Command header: {header}{block_header}<{byte_count} bytes binary>")
    print(f"  Total cmd len : {len(cmd_bytes)} bytes")

    # Query mode BEFORE
    mode_before = query_safe(inst, f":SOURce{ch}:FUNCtion?")
    print(f"\n  Mode BEFORE   : {mode_before}")

    # Upload
    print("  Uploading...")
    try:
        inst.write_raw(cmd_bytes)
        time.sleep(0.5)
        opc = query_safe(inst, "*OPC?")
        print(f"  *OPC?         : {opc}")
    except Exception as e:
        print(f"  UPLOAD FAILED : {e}")
        return

    # Query mode AFTER
    mode_after = query_safe(inst, f":SOURce{ch}:FUNCtion?")
    print(f"  Mode AFTER    : {mode_after}")

    if "SEQ" in mode_after.upper():
        print("  ✓ Instrument switched to SEQUENCE mode (arb with interpolation)")
    elif "USER" in mode_after.upper() or "ARB" in mode_after.upper():
        print("  ✓ Instrument switched to USER/ARB mode")
    else:
        print(f"  ✗ WARNING: Instrument did NOT switch to arb mode! Still: {mode_after}")
        print("    This is likely the root cause of the problem.")

    # Try setting sample rate
    target_freq = 1000.0
    sample_rate = target_freq * N  # 32000 Sa/s
    sr_cmd = f":SOURce{ch}:FUNCtion:SEQuence:SRATe {sample_rate}"
    print(f"\n  Setting sample rate: {sr_cmd}")
    write_safe(inst, sr_cmd)
    time.sleep(0.1)

    # Read back sample rate
    sr_read = query_safe(inst, f":SOURce{ch}:FUNCtion:SEQuence:SRATe?")
    print(f"  Sample rate readback: {sr_read}")

    # Query function again
    mode_final = query_safe(inst, f":SOURce{ch}:FUNCtion?")
    print(f"  Mode FINAL    : {mode_final}")

    # ------------------------------------------------------------------
    # Try alternative: full 16-bit range (0x0000-0xFFFF) — Pro format
    # ------------------------------------------------------------------
    print("\n" + "-" * 65)
    print("ALTERNATIVE TEST: 16-BIT FULL RANGE (Pro format)")
    print("-" * 65)
    print("  (If the unit is actually a DG800 Pro, it may expect 16-bit data)")

    dac_16bit = np.round((data + 1.0) / 2.0 * 65535).astype(np.uint16)
    dac_16bit = np.clip(dac_16bit, 0, 0xFFFF)
    print(f"  DAC range     : {dac_16bit.min()} – {dac_16bit.max()}  (0 – 65535)")

    binary_data_16 = struct.pack(f'<{N}H', *dac_16bit)
    byte_count_16 = len(binary_data_16)
    byte_count_str_16 = str(byte_count_16)
    num_digits_16 = len(byte_count_str_16)

    header_16 = f":SOURce{ch}:TRACe:DATA:DAC16 VOLATILE,END,"
    block_header_16 = f"#{num_digits_16}{byte_count_str_16}"
    cmd_bytes_16 = header_16.encode('ascii') + block_header_16.encode('ascii') + binary_data_16 + b'\n'

    print(f"  Uploading with 16-bit full range...")
    try:
        inst.write_raw(cmd_bytes_16)
        time.sleep(0.5)
        opc = query_safe(inst, "*OPC?")
        print(f"  *OPC?         : {opc}")
        mode_16 = query_safe(inst, f":SOURce{ch}:FUNCtion?")
        print(f"  Mode AFTER    : {mode_16}")
    except Exception as e:
        print(f"  UPLOAD FAILED : {e}")

    # ------------------------------------------------------------------
    # Try :DATA:DAC (without the 16)
    # ------------------------------------------------------------------
    print("\n" + "-" * 65)
    print("ALTERNATIVE TEST: :DATA:DAC (non-16 command)")
    print("-" * 65)

    header_dac = f":SOURce{ch}:TRACe:DATA:DAC VOLATILE,END,"
    cmd_bytes_dac = header_dac.encode('ascii') + block_header.encode('ascii') + binary_data + b'\n'
    print(f"  Uploading with :DATA:DAC ...")
    try:
        inst.write_raw(cmd_bytes_dac)
        time.sleep(0.5)
        opc = query_safe(inst, "*OPC?")
        print(f"  *OPC?         : {opc}")
        mode_dac = query_safe(inst, f":SOURce{ch}:FUNCtion?")
        print(f"  Mode AFTER    : {mode_dac}")
    except Exception as e:
        print(f"  UPLOAD FAILED : {e}")

    # ------------------------------------------------------------------
    # Query stored RAF files
    # ------------------------------------------------------------------
    print("\n" + "-" * 65)
    print("STORED ARBITRARY WAVEFORM FILES")
    print("-" * 65)

    write_safe(inst, ':MMEMory:CDIRectory "C:\\"')
    time.sleep(0.2)
    catalog = query_safe(inst, ":MMEMory:CATalog?")
    print(f"  C:\\ catalog   : {catalog[:200]}..." if len(catalog) > 200 else f"  C:\\ catalog   : {catalog}")

    # List arb data catalog
    arb_cat = query_safe(inst, f":SOURce{ch}:DATA:CATalog?")
    print(f"  Arb catalog   : {arb_cat[:200]}..." if len(arb_cat) > 200 else f"  Arb catalog   : {arb_cat}")

    # ------------------------------------------------------------------
    # Try :FUNCtion:ARBitrary? to see what arb is selected
    # ------------------------------------------------------------------
    arb_sel = query_safe(inst, f":SOURce{ch}:FUNCtion:ARBitrary?")
    print(f"  Arb selected  : {arb_sel}")

    # ------------------------------------------------------------------
    # Option / license info
    # ------------------------------------------------------------------
    print("\n" + "-" * 65)
    print("OPTIONS / LICENSE")
    print("-" * 65)
    opt = query_safe(inst, "*OPT?")
    print(f"  *OPT?         : {opt}")
    
    # Check if it's a Pro by trying Pro-specific commands
    # Pro models respond to :SYSTem:OPTion:TYPE?
    opt_type = query_safe(inst, ":SYSTem:OPTion:TYPE?")
    print(f"  :SYST:OPT:TYPE? : {opt_type}")

    print("\n" + "=" * 65)
    print("DIAGNOSTIC COMPLETE")
    print("=" * 65)
    print("\nPlease run this on BOTH generators and compare the output!")
    print("Key things to look for:")
    print("  1. Different firmware versions")
    print("  2. Different *OPT? responses (Pro vs non-Pro)")
    print("  3. Whether the instrument switches to SEQUENCE mode after upload")
    print("  4. Whether :DATA:DAC (without 16) works instead")


if __name__ == "__main__":
    resource = sys.argv[1] if len(sys.argv) > 1 else None
    inst = connect(resource)
    diagnose(inst)
    inst.close()
