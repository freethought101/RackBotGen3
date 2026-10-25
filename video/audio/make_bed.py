"""Synthesise the 90 s music bed (120 BPM, A minor) so cuts land on bar lines (2 s = 60 frames).
Royalty-free by construction. Usage: python audio/make_bed.py public/audio/bed.wav"""

import sys
import wave

import numpy as np
from scipy.signal import butter, lfilter

SR = 48000
DUR = 90.0
BEAT = 0.5
N = int(SR * DUR)
t_all = np.arange(N) / SR
rng = np.random.default_rng(7)

L = np.zeros(N)
R = np.zeros(N)


def hz(note):
    names = {'C': -9, 'D': -7, 'E': -5, 'F': -4, 'G': -2, 'A': 0, 'B': 2}
    n, octv = note[:-1], int(note[-1])
    semis = names[n[0]] + (1 if '#' in n else 0) + 12 * (octv - 4)
    return 440.0 * 2 ** (semis / 12)


def add(sig, start, pan=0.0, gain=1.0):
    i = int(start * SR)
    if i >= N:
        return
    sig = sig[: N - i] * gain
    L[i:i + len(sig)] += sig * np.sqrt(0.5 * (1 - pan))
    R[i:i + len(sig)] += sig * np.sqrt(0.5 * (1 + pan))


def env(n, a, r, hold=0.0):
    t = np.arange(n) / SR
    e = np.minimum(1, t / max(a, 1e-4))
    rel_start = a + hold
    e = np.where(t > rel_start, np.exp(-(t - rel_start) / r), e)
    return e


def lp(x, fc, order=2):
    b, a = butter(order, fc / (SR / 2), 'low')
    return lfilter(b, a, x)


def hp(x, fc, order=2):
    b, a = butter(order, fc / (SR / 2), 'high')
    return lfilter(b, a, x)


def saw(f, n, detune=0.0):
    t = np.arange(n) / SR
    out = np.zeros(n)
    for d in (-detune, 0, detune):
        ph = (t * f * (1 + d)) % 1.0
        out += 2 * ph - 1
    return out / 3


def pad(notes, start, dur, gain=0.12, fc=1400):
    n = int(dur * SR)
    sig = sum(saw(hz(x), n, 0.004) for x in notes) / len(notes)
    sig = lp(sig, fc, 2)
    e = np.minimum(1, np.arange(n) / (0.6 * SR)) * np.minimum(1, (n - np.arange(n)) / (0.6 * SR))
    add(sig * e, start, -0.3, gain)
    add(lp(saw(hz(notes[0]) * 1.002, n, 0.006), fc) * e, start, 0.3, gain * 0.6)


def kick(start, gain=0.9):
    n = int(0.45 * SR)
    t = np.arange(n) / SR
    f = 45 + 110 * np.exp(-t * 28)
    ph = 2 * np.pi * np.cumsum(f) / SR
    add(np.sin(ph) * np.exp(-t * 7.5), start, 0, gain)


def clap(start, gain=0.25):
    n = int(0.25 * SR)
    t = np.arange(n) / SR
    noise = hp(rng.standard_normal(n), 900)
    e = np.exp(-t * 22) + 0.6 * np.exp(-np.maximum(0, t - 0.012) * 30) * (t > 0.012)
    add(noise * e, start, 0.1, gain)


def hat(start, gain=0.08, pan=0.35):
    n = int(0.06 * SR)
    t = np.arange(n) / SR
    add(hp(rng.standard_normal(n), 7000) * np.exp(-t * 70), start, pan, gain)


def pluck(f, start, gain=0.09, pan=0.0, decay=9.0):
    n = int(0.35 * SR)
    t = np.arange(n) / SR
    sig = lp(saw(f, n, 0.002), 3200) * np.exp(-t * decay)
    add(sig, start, pan, gain)


def bass(f, start, dur, gain=0.22):
    n = int(dur * SR)
    t = np.arange(n) / SR
    sig = lp(saw(f, n), 380) + 0.6 * np.sin(2 * np.pi * f * t)
    add(sig * env(n, 0.005, 0.12, dur * 0.5), start, 0, gain)


def riser(start, dur, gain=0.18):
    n = int(dur * SR)
    t = np.arange(n) / SR
    noise = rng.standard_normal(n)
    out = np.zeros(n)
    seg = 2048
    for i in range(0, n, seg):           # sweep a band-pass upward
        fc = 300 + 7000 * (i / n) ** 2
        b, a = butter(2, [fc / (SR / 2), min(0.99, fc * 1.6 / (SR / 2))], 'band')
        out[i:i + seg] = lfilter(b, a, noise[i:i + seg])
    add(out * (t / dur) ** 2, start, 0, gain)


def impact(start, gain=0.9):
    n = int(2.5 * SR)
    t = np.arange(n) / SR
    f = 30 + 70 * np.exp(-t * 6)
    sub = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 2.2)
    noise = lp(rng.standard_normal(n), 2500) * np.exp(-t * 9)
    add(sub * 0.9 + noise * 0.25, start, 0, gain)


def beep(start, f=1760, gain=0.05):
    n = int(0.09 * SR)
    t = np.arange(n) / SR
    add(np.sin(2 * np.pi * f * t) * np.exp(-t * 30), start, -0.2, gain)


PROG = [  # 2 bars (4 s) per chord
    (['A2', 'E3', 'A3', 'C4', 'E4'], 'A1'),
    (['F2', 'C3', 'F3', 'A3', 'C4'], 'F1'),
    (['C3', 'G3', 'C4', 'E4', 'G4'], 'C2'),
    (['G2', 'D3', 'G3', 'B3', 'D4'], 'G1'),
]
ARP = {0: ['A4', 'C5', 'E5', 'A5'], 1: ['F4', 'A4', 'C5', 'F5'], 2: ['C5', 'E5', 'G5', 'C6'], 3: ['G4', 'B4', 'D5', 'G5']}

# 0-16 s: data-hall drone, alarm beeps, ticking tension, riser into the reveal
n = int(16 * SR)
drone = lp(saw(hz('A1'), n, 0.003), 220) * 0.8 + 0.25 * np.sin(2 * np.pi * 120 * np.arange(n) / SR)
add(drone * np.minimum(1, np.arange(n) / (3 * SR)), 0, 0, 0.22)
for b in range(16):
    kick(b * 1.0 + 0.0, 0.35)            # slow heartbeat
for i in range(0, 8):
    beep(0.5 + i * 1.0 + 0.25, 1760, 0.035)
pad(['A2', 'E3', 'C4'], 8, 8, 0.07, 700)
for i in range(16):
    hat(8 + i * 0.5 + 0.25, 0.05)
riser(12, 4, 0.2)

# 16 s reveal impact, 16-42 s: build
impact(16, 0.8)
for k in range(int((42 - 16) / 4)):
    chord, root = PROG[k % 4]
    pad(chord, 16 + k * 4, 4.2, 0.10, 1100 + 150 * k)
start_beat = 22.0
for b in np.arange(16, 40, BEAT):
    if b >= start_beat or (b - 16) % 1.0 == 0:
        kick(b, 0.55 if b < start_beat else 0.75)
    if b >= start_beat:
        hat(b + 0.25, 0.06)
for i, b in enumerate(np.arange(22, 40, 0.25)):
    k = int((b - 16) // 4) % 4
    pluck(hz(ARP[k][i % 4]), b, 0.06, 0.4 if i % 2 else -0.4)
riser(38, 4, 0.22)

# 42 s swap impact, 42-72 s: full groove
impact(42, 0.7)
for k in range(int((72 - 42) / 4) + 1):
    chord, root = PROG[k % 4]
    s0 = 42 + k * 4
    if s0 >= 72:
        break
    pad(chord, s0, min(4.2, 72.2 - s0), 0.10, 1800)
    for e in np.arange(0, 4, 0.5):
        if s0 + e < 72:
            bass(hz(root) * (2 if e % 1.0 else 1), s0 + e, 0.45, 0.2)
for b in np.arange(42, 72, BEAT):
    kick(b, 0.8)
    hat(b + 0.25, 0.07)
    if int((b - 42) / BEAT) % 2 == 1:
        clap(b, 0.22)
for i, b in enumerate(np.arange(42, 72, 0.25)):
    k = int((b - 42) // 4) % 4
    pluck(hz(ARP[k][(i * 3) % 4]), b, 0.065, 0.4 if i % 2 else -0.4)

# 72-82 s: breakdown under the Delta section
for k in range(3):
    chord, root = PROG[(k + 1) % 4]
    pad(chord, 72 + k * 4, 4.2 if k < 2 else 2.2, 0.11, 1500)
for b in np.arange(72, 82, BEAT):
    hat(b + 0.25, 0.05)
    if (b - 72) % 1.0 == 0:
        kick(b, 0.4)
for i, b in enumerate(np.arange(72, 82, 0.5)):
    pluck(hz(ARP[(int((b - 72) // 4) + 1) % 4][i % 4]), b, 0.05, 0.3)
riser(80, 2, 0.2)

# 82-90 s: final impact and a sustained A minor (add 9) to the end card
impact(82, 0.8)
pad(['A2', 'E3', 'A3', 'B3', 'C4', 'E4'], 82, 8, 0.14, 1600)
bass(hz('A1'), 82, 6, 0.25)
for i, b in enumerate(np.arange(82, 86, 0.25)):
    pluck(hz(ARP[0][i % 4]) * (1 if i < 8 else 2), b, 0.05 * (1 - (b - 82) / 4), 0.3 if i % 2 else -0.3)

# simple stereo room: a few damped delays
mix = np.stack([L, R])
wet = np.zeros_like(mix)
for d, g in ((0.031, 0.35), (0.047, 0.3), (0.071, 0.25), (0.113, 0.18), (0.167, 0.12)):
    k = int(d * SR)
    wet[0, k:] += g * mix[1, :-k]
    wet[1, k:] += g * mix[0, :-k]
mix = mix + lp(wet, 4000) * 0.5
mix = np.tanh(mix * 1.2)
mix /= np.max(np.abs(mix)) / 0.89
fade = np.minimum(1, (N - np.arange(N)) / (2.0 * SR))
mix *= fade

out = sys.argv[1]
with wave.open(out, 'wb') as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes((mix.T * 32767).astype('<i2').tobytes())
print('wrote', out)
