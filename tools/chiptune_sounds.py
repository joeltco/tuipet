#!/usr/bin/env python3
"""Render tuipet's SFX as raw square-wave CHIPTUNE, transcribed from the authentic
DVPet recordings by CONTINUOUS pitch tracking.

Pipeline: authentic DVPet recording (raw_resources/sounds/*.wav)
          -> frame the audio every 8 ms (40 ms window)
          -> per frame: RMS (amplitude gate) + exact fundamental via Harmonic
             Product Spectrum (FFT) -> a continuous pitch+gate contour
          -> median-smooth the pitch (kills stray single-frame octave spikes)
          -> one square-wave voice driven by a phase accumulator that follows the
             contour sample-for-sample, gated by the amplitude envelope
          -> mono 16-bit 44.1 kHz WAV.

Why not aubio note-detection (earlier attempts): aubionotes chops the sound into a
few discrete notes with silent gaps between -> dead air = audible delay, and it
under-samples the fast pitch sweeps -> wrong melody. aubionotes' pitch is also
octave-broken and snaps to integer semitones, while the device tones sit ~30-40 c
flat. Continuous HPS tracking follows the REAL contour, timing-aligned, true tuning.

Nothing is invented -- pitch, timing and dynamics are all measured off the recording.
Requires numpy. Run: python3 tools/chiptune_sounds.py
"""
import os
import wave

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_SRC_CANDIDATES = [
    os.path.join(ROOT, "raw_resources", "sounds"),
    os.path.join(ROOT, "_extract", "game", "DVPetTest", "jar", "resources", "sounds"),
]
SRC = next((p for p in _SRC_CANDIDATES if os.path.isdir(p)), _SRC_CANDIDATES[0])
OUT = os.path.join(ROOT, "src", "tuipet", "data", "sounds")

AMP = 0.6              # uniform square level (~-4.4 dB)
HOP_MS, WIN_MS = 8.0, 40.0
F0_MIN, F0_MAX = 120.0, 2600.0
GATE_FRAC = 0.10       # voiced when frame RMS > 10% of the file's peak RMS
GATE_FLOOR = 0.02

# tuipet cue -> authentic DVPet source stem (5 subs have no 1:1 cue; see git history)
MAP = {
    "alarm": "alarm", "angry": "angry", "attack": "attack", "battle": "battle",
    "eat": "eat", "error": "error", "evolve": "evolve", "happy": "happy",
    "hatch": "hatch", "jogress": "jogress", "largePoop": "largePoop",
    "lastBite": "lastBite", "lose": "lose", "poop": "poop", "refuse": "refuse",
    "select": "select", "smallPoop": "smallPoop", "strongAttack": "strongAttack",
    "strongHit": "strongHit", "wash": "wash", "win": "win",
    "cancel": "error", "confirm": "click", "menu": "select", "scroll": "select",
    "death": "lose",
}
SUBS = {"cancel", "confirm", "menu", "scroll", "death"}


def load(src):
    w = wave.open(src, "rb")
    fr, sw = w.getframerate(), w.getsampwidth()
    raw = w.readframes(w.getnframes())
    if sw == 1:                                              # 8-bit unsigned (the DVPet rips)
        a = (np.frombuffer(raw, np.uint8).astype(np.float64) - 128) / 128.0
    else:
        a = np.frombuffer(raw, np.int16).astype(np.float64) / 32768.0
    return a, fr


def hps_f0(seg, fr):
    """Exact fundamental (Hz) of one frame via Harmonic Product Spectrum; 0 if too quiet."""
    if len(seg) < 256:
        return 0.0
    s = seg - seg.mean()
    win = s * np.hanning(len(s))
    n = 1 << int(np.ceil(np.log2(len(win) * 8)))             # zero-pad -> fine freq grid
    spec = np.abs(np.fft.rfft(win, n))
    mx = spec.max()
    if mx <= 1e-9:
        return 0.0
    spec /= mx                                               # normalize -> HPS product can't overflow
    freqs = np.fft.rfftfreq(n, 1.0 / fr)
    hps = spec.copy()
    for h in range(2, 6):                                    # multiply 2nd..5th downsampled spectra
        d = spec[::h]
        hps[:len(d)] *= d
    lo = np.searchsorted(freqs, F0_MIN)
    hi = np.searchsorted(freqs, F0_MAX)
    k = lo + int(np.argmax(hps[lo:hi]))
    if 1 <= k < len(freqs) - 1:                              # parabolic interp for sub-bin precision
        a, b, c = (np.log(hps[k + d] + 1e-12) for d in (-1, 0, 1))
        denom = a - 2 * b + c
        if denom:
            return float(freqs[k] + 0.5 * (a - c) / denom * (freqs[1] - freqs[0]))
    return float(freqs[k])


def track(a, fr):
    """Continuous (f0, gate) per hop across the whole recording."""
    hop = int(fr * HOP_MS / 1000)
    win = int(fr * WIN_MS / 1000)
    nfr = max(1, (len(a) - 1) // hop + 1)
    f0 = np.zeros(nfr)
    rms = np.zeros(nfr)
    for i in range(nfr):
        seg = a[i * hop:i * hop + win]
        if len(seg) < 64:
            continue
        rms[i] = np.sqrt(np.mean(seg * seg))
        f0[i] = hps_f0(seg, fr)
    gate = rms > max(GATE_FLOOR, rms.max() * GATE_FRAC)
    # median-smooth f0 across voiced frames -> drop lone octave spikes
    vi = np.where(gate)[0]
    sm = f0.copy()
    for j, i in enumerate(vi):
        lo, hi = max(0, j - 2), min(len(vi), j + 3)
        sm[i] = np.median(f0[vi[lo:hi]])
    return sm, gate, hop


def render(src):
    a, fr = load(src)
    f0, gate, hop = track(a, fr)
    n = len(a)
    f0s = np.repeat(f0, hop)[:n]
    g = np.repeat(gate.astype(np.float64), hop)[:n]
    if len(f0s) < n:                                         # pad tail
        f0s = np.pad(f0s, (0, n - len(f0s)))
        g = np.pad(g, (0, n - len(g)))
    f0s = np.where(f0s > 0, f0s, 1.0)                        # avoid 0-phase stall (gated off anyway)
    phase = np.cumsum(2.0 * np.pi * f0s / fr)                # phase accumulator -> glitch-free pitch glide
    sig = AMP * np.sign(np.sin(phase))
    ramp = max(1, int(fr * 0.004))                           # 4 ms gate ramp -> no clicks
    g = np.convolve(g, np.ones(ramp) / ramp, "same")
    out = np.clip(sig * g, -1.0, 1.0).astype(np.float32)
    return out, fr, int(gate.sum())


def write_wav(path, buf, fr):
    data = (np.clip(buf, -1.0, 1.0) * 32767.0).astype("<i2").tobytes()
    w = wave.open(path, "wb")
    w.setnchannels(1)
    w.setsampwidth(2)
    w.setframerate(fr)
    w.writeframes(data)
    w.close()


def main():
    for cue, stem in MAP.items():
        src = os.path.join(SRC, stem + ".wav")
        if not os.path.exists(src):
            print("  MISSING SOURCE:", cue, stem)
            continue
        buf, fr, voiced = render(src)
        write_wav(os.path.join(OUT, cue + ".wav"), buf, fr)
        print("  %-14s <- %-13s %.2fs, %d voiced frames%s"
              % (cue, stem + ".wav", len(buf) / fr, voiced, "  [SUB]" if cue in SUBS else ""))


if __name__ == "__main__":
    main()
