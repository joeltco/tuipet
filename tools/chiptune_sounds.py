#!/usr/bin/env python3
"""Render tuipet's SFX as raw square-wave CHIPTUNE, transcribed from the authentic
DVPet recordings by CONTINUOUS pitch tracking, analysed under a slow-motion "lens".

Pipeline: authentic DVPet recording (raw_resources/sounds/*.wav)
          -> time-stretch ANALYSIS_STRETCHx slower, pitch preserved (rubberband) --
             a transcription microscope: fast sweeps spread out so each note resolves
             cleanly (halves octave-detection errors). PLAYBACK speed is unaffected.
          -> frame the slowed audio: RMS (amplitude gate) + exact fundamental via
             Harmonic Product Spectrum (FFT), median-smoothed -> a fine pitch contour
          -> render that contour back at the ORIGINAL tempo: one square-wave voice via
             a phase accumulator following it sample-for-sample, gated by the envelope
          -> mono 16-bit 44.1 kHz WAV, native game speed.

Why slow only for analysis: the user wants device-speed SFX, but fast sweeps blur a
real-time pitch tracker. Slowing the AUDIO (not the output) gives fine musical-time
resolution while each FFT window still holds full waveform cycles (good freq res) --
something a shorter real-time window can't do. aubio note-detection was abandoned
earlier (discrete notes -> silent-gap delay; octave-broken, semitone-snapped pitch).

Nothing is invented -- pitch, timing and dynamics are all measured off the recording.
Requires numpy + ffmpeg + rubberband. Run: python3 tools/chiptune_sounds.py
"""
import os
import subprocess  # nosec B404 - ffmpeg/rubberband from PATH, no shell, our own files
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

AMP = 0.6              # uniform square level (~-4.4 dB)
HOP_MS, WIN_MS = 8.0, 40.0
F0_MIN, F0_MAX = 120.0, 2600.0
GATE_FRAC = 0.10       # voiced when frame RMS > 10% of the file's peak RMS
GATE_FLOOR = 0.02
ANALYSIS_STRETCH = 4.0 # slow the audio this much for pitch detection ONLY (output stays native)
SMOOTH = 4             # median window = 2*SMOOTH+1 frames (wider, since slowed frames are short)
STEP_TOL = 0.6         # semitones: pitch wobble within one held note (device steps, doesn't glide)
STEP_MIN_MS = 25.0     # shorter detected notes get merged (no blips)

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
        lo, hi = max(0, j - SMOOTH), min(len(vi), j + SMOOTH + 1)
        sm[i] = np.median(f0[vi[lo:hi]])
    return sm, gate, hop


def stretch_for_analysis(src, tmp):
    """rubberband: a pitch-preserved slow-mo copy of the recording for transcription."""
    base = os.path.basename(src)
    t16 = os.path.join(tmp, base + ".16.wav")
    tsl = os.path.join(tmp, base + ".slow.wav")
    subprocess.run(["ffmpeg", "-y", "-i", src, "-ar", "44100", "-ac", "1",   # nosec B603,B607
                    "-c:a", "pcm_s16le", t16],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    subprocess.run(["rubberband", "-t", str(ANALYSIS_STRETCH), t16, tsl],     # nosec B603,B607
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    return tsl


def quantize_steps(f0, gate, hop, fr):
    """Collapse the continuous contour into discrete HELD notes -- the device sets a
    tone register and holds it (no portamento). Group consecutive voiced frames that
    stay within STEP_TOL of the running note; each note plays its median pitch; merge
    sub-STEP_MIN_MS notes so there are no blips. Output steps cleanly, no glide, no gaps."""
    out = f0.copy()
    vi = np.where(gate)[0]
    if len(vi) == 0:
        return out
    # one slowed-frame spans HOP_MS/STRETCH ms of REAL time -> convert the min note length
    min_frames = max(2, int(STEP_MIN_MS * ANALYSIS_STRETCH / HOP_MS))
    notes, cur, ref = [], [vi[0]], f0[vi[0]]
    for idx in range(1, len(vi)):
        i, prev = vi[idx], vi[idx - 1]
        contiguous = (i - prev) == 1
        close = f0[i] > 0 and ref > 0 and abs(12 * np.log2(f0[i] / ref)) <= STEP_TOL
        if contiguous and close:
            cur.append(i)
            ref = np.median([f0[j] for j in cur])
        else:
            notes.append(cur)
            cur, ref = [i], f0[i]
    notes.append(cur)
    merged = []
    for nt in notes:                                         # absorb too-short notes into the previous
        if merged and len(nt) < min_frames and (nt[0] - merged[-1][-1]) == 1:
            merged[-1].extend(nt)
        else:
            merged.append(nt)
    for nt in merged:
        m = float(np.median([f0[j] for j in nt]))
        for j in nt:
            out[j] = m
    return out


def render(src, tmp):
    n_orig = len(load(src)[0])                               # original length -> output stays native speed
    asl, fr = load(stretch_for_analysis(src, tmp))           # slowed audio, analysed under the lens
    f0, gate, hop = track(asl, fr)
    f0 = quantize_steps(f0, gate, hop, fr)                   # discrete held notes, not a glide
    rep = max(1, int(round(hop / ANALYSIS_STRETCH)))         # map slowed frames back to ORIGINAL tempo
    f0s = np.repeat(f0, rep)[:n_orig]
    g = np.repeat(gate.astype(np.float64), rep)[:n_orig]
    if len(f0s) < n_orig:                                    # pad tail to the native length
        f0s = np.pad(f0s, (0, n_orig - len(f0s)))
        g = np.pad(g, (0, n_orig - len(g)))
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
