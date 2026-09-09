"""
Diagnose trapezoid and comb waveform issues.
Dumps the actual data arrays and DAC values to find discrepancies.
"""
import numpy as np
import sys
import os
# Run from anywhere: the rigol_dg822 package lives one level up from tools/.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from rigol_dg822.arbitrary import WaveformGenerator, compute_optimal_points

# ── Trapezoid (unipolar) ──
print("="*60)
print("TRAPEZOID ANALYSIS (unipolar)")
print("="*60)
freq = 1000.0
pts = compute_optimal_points(freq)
print(f"Freq: {freq} Hz, Optimal points: {pts}")

# Standard 20/60/20 trapezoid
wf = WaveformGenerator.trapezoid(pts, rise_percent=20.0, pulse_percent=60.0, fall_percent=20.0)
data = wf.data

n = len(data)
rise_pts = int(round(n * 0.2))
pulse_pts = int(round(n * 0.6))
fall_pts = int(round(n * 0.2))

print(f"\nData shape: {data.shape}")
print(f"Expected segments: rise={rise_pts}, pulse={pulse_pts}, fall={fall_pts}")
print(f"Data range: [{data.min():.4f}, {data.max():.4f}]")

# Show transitions
print(f"\nFirst 10 values (should be rising from -1):   {data[:10]}")
print(f"Values around rise→high: {data[rise_pts-3:rise_pts+3]}")
print(f"Values at high plateau mid: {data[rise_pts+pulse_pts//2-2:rise_pts+pulse_pts//2+2]}")
print(f"Values around high→fall: {data[rise_pts+pulse_pts-3:rise_pts+pulse_pts+3]}")
print(f"Last 10 values (should be low at -1):          {data[-10:]}")

# Check the DAC conversion matches
dac = np.round((data + 1.0) / 2.0 * 16383).astype(np.uint16)
dac = np.clip(dac, 0, 0x3FFF)
print(f"\nDAC first 10:  {dac[:10]}")
print(f"DAC at rise→high: {dac[rise_pts-3:rise_pts+3]}")
print(f"DAC at high→fall: {dac[rise_pts+pulse_pts-3:rise_pts+pulse_pts+3]}")
print(f"DAC last 10:   {dac[-10:]}")

# Check monotonicity of rise segment
rise_data = data[:rise_pts]
diffs = np.diff(rise_data)
non_mono = np.sum(diffs < 0)
print(f"\nRise segment: {rise_pts} pts, monotonically increasing: {non_mono == 0}")
print(f"  start={rise_data[0]:.6f}, end={rise_data[-1]:.6f}")

# Check monotonicity of fall segment
fall_start = rise_pts + pulse_pts
fall_data = data[fall_start:fall_start+fall_pts]
diffs = np.diff(fall_data)
non_mono = np.sum(diffs > 0)
print(f"Fall segment: {fall_pts} pts, monotonically decreasing: {non_mono == 0}")
print(f"  start={fall_data[0]:.6f}, end={fall_data[-1]:.6f}")

# ── Now check byte order: how the binary looks ──
import struct
binary = struct.pack(f'<{len(dac)}H', *dac)
print(f"\nBinary representation (first 20 bytes, little-endian):")
print(f"  {' '.join(f'{b:02X}' for b in binary[:20])}")

print(f"\nSample [0] DAC={dac[0]:04X} -> bytes: {binary[0]:02X} {binary[1]:02X}")
print(f"Sample [1] DAC={dac[1]:04X} -> bytes: {binary[2]:02X} {binary[3]:02X}")
mid = rise_pts // 2
print(f"Sample [{mid}] DAC={dac[mid]:04X} -> bytes: {binary[mid*2]:02X} {binary[mid*2+1]:02X}")
print(f"Sample [{rise_pts}] DAC={dac[rise_pts]:04X} -> bytes: {binary[rise_pts*2]:02X} {binary[rise_pts*2+1]:02X}")

# ── Bipolar trapezoid ──
print("\n" + "="*60)
print("BIPOLAR TRAPEZOID ANALYSIS")
print("="*60)
# For bipolar, gen_points = pts // 2
gen_pts = pts // 2
bpol_base = WaveformGenerator.trapezoid(gen_pts, 20.0, 60.0, 20.0)
bpol = WaveformGenerator.make_bipolar(bpol_base, total_points=pts)
bd = bpol.data

print(f"Unipolar base: {gen_pts} pts, Bipolar result: {len(bd)} pts")
print(f"Bipolar range: [{bd.min():.4f}, {bd.max():.4f}]")

# The positive half should go [0 → +1 → 0] (trapezoid shape)
# The negative half should go [0 → -1 → 0] (inverted trapezoid)
half = len(bd) // 2
print(f"\nPositive half first 5: {bd[:5]}")
print(f"Positive half mid:     {bd[half//2-2:half//2+2]}")
print(f"Positive half last 5:  {bd[half-5:half]}")
print(f"Negative half first 5: {bd[half:half+5]}")
print(f"Negative half mid:     {bd[half+half//2-2:half+half//2+2]}")
print(f"Negative half last 5:  {bd[-5:]}")

# ── Check for the wrap-around discontinuity ──
print(f"\nWrap check: last value={bd[-1]:.6f}, first value={bd[0]:.6f}")
print(f"Difference: {abs(bd[-1] - bd[0]):.6f}")

# ── Frequency comb ──
print("\n" + "="*60)
print("FREQUENCY COMB ANALYSIS")
print("="*60)
freqs = [100, 200, 300, 400, 500]
from rigol_dg822.arbitrary import compute_optimal_points_for_comb
num_pts, info = compute_optimal_points_for_comb(freqs)
print(f"Frequencies: {freqs}")
print(f"Fundamental: {info['fundamental']} Hz")
print(f"Points: {num_pts}")

wf_comb = WaveformGenerator.frequency_comb(frequencies=freqs, num_points=num_pts, 
                                            random_phases=False)
cd = wf_comb.data
print(f"Comb data shape: {cd.shape}")
print(f"Comb range: [{cd.min():.4f}, {cd.max():.4f}]")
print(f"\nWrap check: last value={cd[-1]:.6f}, first value={cd[0]:.6f}")
print(f"Difference: {abs(cd[-1] - cd[0]):.6f}")

# Derivative continuity check
deriv_end = cd[-1] - cd[-2]
deriv_start = cd[1] - cd[0]
# If the waveform repeats, the derivative at the wrap should be continuous
# The "next" slope after the last point would be cd[0] - cd[-1]
wrap_deriv = cd[0] - cd[-1]
print(f"Slope at end (last 2 pts): {deriv_end:.6f}")
print(f"Slope at start (first 2 pts): {deriv_start:.6f}")
print(f"Wrap slope (cd[0]-cd[-1]): {wrap_deriv:.6f}")

# Now with random phases
wf_comb_rand = WaveformGenerator.frequency_comb(frequencies=freqs, num_points=num_pts,
                                                  random_phases=True, monte_carlo_iterations=100)
rd = wf_comb_rand.data
print(f"\nRandom phases wrap: last={rd[-1]:.6f}, first={rd[0]:.6f}, diff={abs(rd[-1]-rd[0]):.6f}")
wrap_deriv_r = rd[0] - rd[-1]
print(f"Wrap slope (rd[0]-rd[-1]): {wrap_deriv_r:.6f}")

print("\nDone.")
