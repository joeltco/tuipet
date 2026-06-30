#!/usr/bin/env python3
"""Render tuipet's SFX as raw square-wave CHIPTUNE, transcribed from the authentic
DVPet recordings.

Pipeline: authentic DVPet recording (raw_resources/sounds/*.wav)
          -> `aubionotes` for note SEGMENTATION (onset/offset timing -- aubio is good
             at this)
          -> per segment, the EXACT fundamental via Harmonic Product Spectrum (NOT
             aubio's pitch: aubionotes is octave-unreliable on these piezo tones and
             snaps to integer semitones, while the device's tones sit ~30-40 cents
             flat of equal temperament -- HPS recovers the true, non-tempered Hz in
             the correct octave)
          -> one square-wave voice per segment at that exact Hz (the piezo voice)
          -> mono 16-bit 44.1kHz WAV.

Nothing is invented or hand-corrected -- both timing and pitch are measured off the
real recording. Requires the `aubio` package + numpy. Run: python3 tools/chiptune_sounds.py
"""
import os
import subprocess  # nosec B404 - aubionotes from PATH, no shell, our own files
import wave

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_SRC_CANDIDATES = [
    os.path.join(ROOT, "raw_resources", "sounds"),
    os.path.join(ROOT, "_extract", "game", "DVPetTest", "jar", "resources", "sounds"),
]
SRC = next((p for p in _SRC_CANDIDATES if os.path.isdir(p)), _SRC_CANDIDATES[0])
OUT = os.path.join(ROOT, "src", "tuipet", "data", "sounds")

SR = 44100
AMP = 0.6           # uniform level across cues (square peak ~-4.4 dB; loud, leaves headroom)
RAMP_MS = 1.5       # tiny per-note attack/release so square edges don't click

# tuipet cue -> authentic DVPet source stem (5 subs have no 1:1 cue, see install_sounds.py)
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


F0_MIN, F0_MAX = 120.0, 2600.0   # piezo fundamental search band


def load(src):
    w = wave.open(src, "rb")
    fr, sw = w.getframerate(), w.getsampwidth()
    raw = w.readframes(w.getnframes())
    if sw == 1:                                              # 8-bit unsigned (the DVPet rips)
        a = (np.frombuffer(raw, np.uint8).astype(np.float64) - 128) / 128.0
    else:
        a = np.frombuffer(raw, np.int16).astype(np.float64) / 32768.0
    return a, fr


def aubio_segments(src):
    """[(onset_s, offset_s)] -- aubionotes' note TIMING only (its pitch is unreliable)."""
    out = subprocess.run(["aubionotes", "-i", src],         # nosec B603,B607 - fixed cmd, no shell
                         capture_output=True, text=True).stdout
    segs = []
    for line in out.splitlines():
        p = line.split()
        if len(p) == 3:                                      # midi  start  end
            segs.append((float(p[1]), float(p[2])))
    return segs


def hps_f0(seg, fr):
    """Exact fundamental (Hz) via Harmonic Product Spectrum; 0 if unpitched/silent."""
    if len(seg) < 256:
        return 0.0
    s = seg - seg.mean()
    if np.sqrt(np.mean(s * s)) < 0.01:
        return 0.0
    win = s * np.hanning(len(s))
    n = 1 << int(np.ceil(np.log2(len(win) * 8)))             # zero-pad -> fine freq grid
    spec = np.abs(np.fft.rfft(win, n))
    spec /= spec.max() + 1e-12                               # normalize -> HPS product can't overflow
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


def square(freq, dur):
    n = int(SR * dur)
    if n <= 0 or freq <= 0:
        return np.zeros(max(0, n), dtype=np.float32)
    t = np.arange(n, dtype=np.float32)
    w = AMP * np.sign(np.sin(2.0 * np.pi * freq * t / SR)).astype(np.float32)
    r = min(n // 2, int(SR * RAMP_MS / 1000))
    if r > 0:
        env = np.ones(n, dtype=np.float32)
        env[:r] = np.linspace(0, 1, r)
        env[-r:] = np.linspace(1, 0, r)
        w *= env
    return w


def render(src):
    a, fr = load(src)
    segs = aubio_segments(src)
    if not segs:
        return np.zeros(int(SR * 0.04), dtype=np.float32), 0
    total = max(off for _, off in segs)
    buf = np.zeros(int(SR * total) + SR // 100, dtype=np.float32)
    voiced = 0
    for on, off in segs:                                     # mono voice: note in its slot, gaps stay silent
        f0 = hps_f0(a[int(on * fr):int(off * fr)], fr)       # EXACT Hz, correct octave, true tuning
        if f0 <= 0:
            continue
        voiced += 1
        seg = square(f0, off - on)
        i = int(SR * on)
        buf[i:i + len(seg)] += seg
    return np.clip(buf, -1.0, 1.0), voiced


def write_wav(path, buf):
    data = (np.clip(buf, -1.0, 1.0) * 32767.0).astype("<i2").tobytes()
    w = wave.open(path, "wb")
    w.setnchannels(1)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes(data)
    w.close()


def main():
    for cue, stem in MAP.items():
        src = os.path.join(SRC, stem + ".wav")
        if not os.path.exists(src):
            print("  MISSING SOURCE:", cue, stem)
            continue
        buf, voiced = render(src)
        write_wav(os.path.join(OUT, cue + ".wav"), buf)
        print("  %-14s <- %-13s %2d notes -> %.2fs chiptune%s"
              % (cue, stem + ".wav", voiced, len(buf) / SR, "  [SUB]" if cue in SUBS else ""))


if __name__ == "__main__":
    main()
