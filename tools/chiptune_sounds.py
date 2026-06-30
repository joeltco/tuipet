#!/usr/bin/env python3
"""Render tuipet's SFX as raw square-wave CHIPTUNE, transcribed from the authentic
DVPet recordings.

Pipeline: authentic DVPet recording (raw_resources/sounds/*.wav)
          -> time-stretch ANALYSIS_STRETCHx slower, pitch preserved (rubberband) -- a
             transcription microscope so fast notes resolve cleanly. PLAYBACK is native.
          -> pitch via aubio YIN (aubiopitch -p yinfft): far more octave-stable than a
             plain spectral peak, so the actual melody is recovered, not an octave-
             scrambled approximation. Amplitude gate from the native RMS envelope.
          -> median-smooth, then QUANTIZE into discrete held notes (the device sets a
             tone register and holds it -- it steps, it doesn't glide/portamento).
          -> synthesize each note as a BAND-LIMITED square (additive odd harmonics up
             to Nyquist): the device's bright square timbre WITHOUT the aliasing grit a
             naive hard square produces (that grit is the "recorded onto an Atari" buzz).
          -> mono 16-bit 44.1 kHz WAV, native game speed.

Nothing is invented -- pitch, timing, dynamics measured off the recording.
Requires numpy + ffmpeg + rubberband + aubio. Run: python3 tools/chiptune_sounds.py
"""
import os
import subprocess  # nosec B404 - ffmpeg/rubberband/aubiopitch from PATH, no shell, our own files
import tempfile
import wave

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_SRC_CANDIDATES = [
    os.path.join(ROOT, "raw_resources", "sounds"),
    os.path.join(ROOT, "_extract", "game", "DVPetTest", "jar", "resources", "sounds"),
]
SRC = next((p for p in _SRC_CANDIDATES if os.path.isdir(p)), _SRC_CANDIDATES[0])
OUT = os.path.join(ROOT, "src", "tuipet", "data", "sounds")

AMP = 0.6              # per-note square peak (~-4.4 dB)
HOP_MS, WIN_MS = 8.0, 40.0
F0_MIN, F0_MAX = 120.0, 2600.0
GATE_FRAC, GATE_FLOOR = 0.10, 0.02
ANALYSIS_STRETCH = 4.0 # slow the audio this much for pitch detection ONLY (output stays native)
YIN_TOL = 0.5          # aubio yin pitch tolerance (0.1..0.7; higher = steadier on these tones)
SMOOTH = 2             # median window = 2*SMOOTH+1 frames
STEP_TOL = 0.6         # semitones: pitch wobble kept within one held note (device steps)
STEP_MIN_MS = 30.0     # shorter detected notes get merged (no blips)

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


def stretch_for_analysis(src, tmp):
    """rubberband: a 16-bit pitch-preserved slow-mo copy for transcription."""
    base = os.path.basename(src)
    t16 = os.path.join(tmp, base + ".16.wav")
    tsl = os.path.join(tmp, base + ".slow.wav")
    subprocess.run(["ffmpeg", "-y", "-i", src, "-ar", "44100", "-ac", "1",   # nosec B603,B607
                    "-c:a", "pcm_s16le", t16],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    subprocess.run(["rubberband", "-t", str(ANALYSIS_STRETCH), t16, tsl],     # nosec B603,B607
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    return tsl


def yin_pitch(wav):
    """aubio YIN pitch track of `wav` -> (times_s, freqs_hz)."""
    out = subprocess.run(["aubiopitch", "-i", wav, "-p", "yinfft",            # nosec B603,B607
                          "-l", str(YIN_TOL)], capture_output=True, text=True).stdout
    t, f = [], []
    for line in out.splitlines():
        p = line.split()
        if len(p) == 2:
            t.append(float(p[0]))
            f.append(float(p[1]))
    return np.array(t), np.array(f)


def analyze(src, tmp):
    """-> (native_audio, fr, f0_per_hop, gate_per_hop, hop_samples) on the NATIVE timeline."""
    native, fr = load(src)
    ts, fs = yin_pitch(stretch_for_analysis(src, tmp))
    ts = ts / ANALYSIS_STRETCH                              # slowed seconds -> real seconds
    hop = max(1, int(HOP_MS / 1000 * fr))
    win = int(WIN_MS / 1000 * fr)
    nfr = max(1, (len(native) - 1) // hop + 1)
    grid = np.arange(nfr) * hop / fr
    f0 = np.interp(grid, ts, fs, left=0.0, right=0.0) if len(ts) else np.zeros(nfr)
    f0 = np.where((f0 >= F0_MIN) & (f0 <= F0_MAX), f0, 0.0)
    rms = np.array([np.sqrt(np.mean(native[i * hop:i * hop + win] ** 2))
                    if i * hop < len(native) else 0.0 for i in range(nfr)])
    gate = rms > max(GATE_FLOOR, rms.max() * GATE_FRAC)
    vi = np.where(gate & (f0 > 0))[0]                       # median-smooth pitch over voiced frames
    sm = f0.copy()
    for j, i in enumerate(vi):
        lo, hi = max(0, j - SMOOTH), min(len(vi), j + SMOOTH + 1)
        sm[i] = np.median(f0[vi[lo:hi]])
    return native, fr, sm, gate, hop


def quantize_steps(f0, gate, hop, fr):
    """Collapse the contour into discrete HELD notes -- group voiced frames within
    STEP_TOL of the running note (median pitch), merge sub-STEP_MIN_MS blips."""
    out = f0.copy()
    vi = np.where(gate & (f0 > 0))[0]
    if len(vi) == 0:
        return out
    min_frames = max(2, int(STEP_MIN_MS / 1000 * fr / hop))
    notes, cur, ref = [], [vi[0]], f0[vi[0]]
    for idx in range(1, len(vi)):
        i, prev = vi[idx], vi[idx - 1]
        close = abs(12 * np.log2(f0[i] / ref)) <= STEP_TOL if ref > 0 else False
        if (i - prev) == 1 and close:
            cur.append(i)
            ref = np.median([f0[j] for j in cur])
        else:
            notes.append(cur)
            cur, ref = [i], f0[i]
    notes.append(cur)
    merged = []
    for nt in notes:
        if merged and len(nt) < min_frames and (nt[0] - merged[-1][-1]) == 1:
            merged[-1].extend(nt)
        else:
            merged.append(nt)
    for nt in merged:
        m = float(np.median([f0[j] for j in nt]))
        for j in nt:
            out[j] = m
    return out


def synth(f0, gate, hop, fr, total):
    """Band-limited square per held note (additive odd harmonics up to Nyquist)."""
    out = np.zeros(total)
    i, nfr = 0, len(f0)
    while i < nfr:
        if gate[i] and f0[i] > 0:
            j = i
            while j + 1 < nfr and gate[j + 1] and abs(f0[j + 1] - f0[i]) < 1e-6:
                j += 1
            freq = f0[i]
            s0, s1 = i * hop, min(total, (j + 1) * hop)
            n = s1 - s0
            if n > 0:
                t = np.arange(n) / fr
                sig = np.zeros(n)
                k = 1
                while k * freq < 0.45 * fr:                 # odd harmonics, 1/k -> band-limited square
                    sig += np.sin(2 * np.pi * k * freq * t) / k
                    k += 2
                mx = np.max(np.abs(sig))
                if mx > 0:
                    sig *= AMP / mx
                r = min(n // 2, int(0.003 * fr))            # 3 ms edges -> no clicks
                if r > 0:
                    env = np.ones(n)
                    env[:r] = np.linspace(0, 1, r)
                    env[-r:] = np.linspace(1, 0, r)
                    sig *= env
                out[s0:s1] += sig
            i = j + 1
        else:
            i += 1
    return np.clip(out, -1.0, 1.0)


def render(src, tmp):
    native, fr, f0, gate, hop = analyze(src, tmp)
    f0 = quantize_steps(f0, gate, hop, fr)
    out = synth(f0, gate, hop, fr, len(native)).astype(np.float32)
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
    with tempfile.TemporaryDirectory(prefix="tuipet_sfx_") as tmp:
        for cue, stem in MAP.items():
            src = os.path.join(SRC, stem + ".wav")
            if not os.path.exists(src):
                print("  MISSING SOURCE:", cue, stem)
                continue
            buf, fr, voiced = render(src, tmp)
            write_wav(os.path.join(OUT, cue + ".wav"), buf, fr)
            print("  %-14s <- %-13s %.2fs, %d voiced frames%s"
                  % (cue, stem + ".wav", len(buf) / fr, voiced, "  [SUB]" if cue in SUBS else ""))


if __name__ == "__main__":
    main()
