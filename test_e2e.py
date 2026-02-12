"""End-to-end test: simulate the GUI upload flow through the real modules."""
import sys
sys.path.insert(0, r'c:\Users\darro\OneDrive - Yale University\Desktop\RIGOLDG822_controller')

import time
from dg822_controller import DG822Controller
from dg822_arbitrarywf import WaveformGenerator, compute_optimal_points

VISA = "USB0::0x1AB1::0x0643::DG8A252001971::0::INSTR"
CH = 1

print("=" * 60)
print("END-TO-END ARB UPLOAD TEST (via DG822Controller)")
print("=" * 60)

controller = DG822Controller()
if not controller.connect(VISA):
    print("Failed to connect!")
    sys.exit(1)

print(f"Connected.")

# Reset to SIN to reproduce the GUI starting condition
controller.reset()
time.sleep(2)
controller.connection.query("*OPC?")
print(f"CH{CH} mode after reset: {controller.get_waveform_type(CH)}")

# Generate a 1kHz square arb waveform (same as GUI would)
freq = 1000.0
pts = compute_optimal_points(freq)
print(f"\nGenerating {pts}-point square wave for {freq} Hz...")
wf = WaveformGenerator.square(pts, 50.0)
wf.name = "TSTSQR"

# Upload (same as _upload_arb)
print("Uploading via upload_arbitrary_waveform_from_object...")
ok = controller.waveform.upload_arbitrary_waveform_from_object(CH, wf)
print(f"Upload result: {ok}")
time.sleep(0.3)
print(f"CH{CH} mode after upload: {controller.get_waveform_type(CH)}")

# Store RAF
print("Storing RAF file...")
controller.waveform.store_arb_file("TSTSQR")

# Apply parameters (same as _upload_arb / _apply_settings)
print(f"\nApplying: freq={freq}, amp=5, offset=0, phase=0, pts={pts}")
ok2 = controller.waveform.apply_arbitrary(CH, freq, 5.0, 0.0, 0.0, num_points=pts)
print(f"Apply result: {ok2}")

print(f"\nCH{CH} mode final: {controller.get_waveform_type(CH)}")
print(f"CH{CH} frequency: {controller.get_frequency(CH)}")
print(f"CH{CH} amplitude: {controller.get_amplitude(CH)}")

# Turn output ON
controller.output_on(CH)
print(f"Output ON: {controller.is_output_on(CH)}")

print("\n" + "=" * 60)
print("CHECK THE FRONT PANEL!")
print(f"You should see a {freq} Hz square arb wave on CH{CH}")
print("=" * 60)

controller.disconnect()
