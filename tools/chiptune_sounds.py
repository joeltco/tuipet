#!/usr/bin/env python3
"""Render tuipet's SFX as raw 1-bit CHIPTUNE, converted directly from the authentic
DVPet recordings by a square-wave COMPARATOR -- no pitch detection, no transcription.

Pass each recording through a 1-bit comparator (sign of the waveform): a comparator
outputs a square wave at the EXACT instantaneous frequency already present, so the
melody is mathematically the recording's own. That's how a 1-bit/piezo speaker
actually voices a tone. (This is the sound system from the authentic-rebuild branch,
brought back onto the DVPet clone.)

Pipeline per cue: bundled recording (src/tuipet/data/sounds/<cue>.wav)
  -> high-pass (remove DC/drift so zero-crossings track the tone)
  -> RMS-envelope amplitude gate (silence stays silent, not full-volume hiss)
  -> out = AMP * sign(signal) * gate   (the 1-bit square), soft gate edges = no clicks
  -> written back in place, mono 16-bit, native rate.

SKIP the weather-ambience cues: rain/wind/thunder are BROADBAND NOISE, and a 1-bit
comparator turns noise into harsh buzz. The authentic-rebuild chiptune never touched
them (it had stripped weather); the clone keeps them as their recordings.

All bundled sounds are read into memory BEFORE any are written, so the in-place
transform is a clean one-pass over the original set (re-runnable).

Pure numpy, no external tools. Run: python3 tools/chiptune_sounds.py
"""
import glob
import os
import wave

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SND = os.path.join(ROOT, "src", "tuipet", "data", "sounds")

AMP = 0.6              # square level (~-4.4 dB)
HP_MS = 4.0            # DC/drift-removal window
ENV_MS = 20.0         # RMS envelope window for the silence gate
GATE_FRAC, GATE_FLOOR = 0.08, 0.01
RAMP_MS = 4.0         # gate-edge ramp -> no clicks

# weather ambience = broadband noise -> a 1-bit square makes it harsh; keep the recording
SKIP = {"rain", "wind", "thunder", "thunder2", "thunder3"}


def load(path):
    w = wave.open(path, "rb")
    fr, sw = w.getframerate(), w.getsampwidth()
    raw = w.readframes(w.getnframes())
    w.close()
    if sw == 1:                                              # 8-bit unsigned (the DVPet rips)
        a = (np.frombuffer(raw, np.uint8).astype(np.float64) - 128) / 128.0
    else:
        a = np.frombuffer(raw, np.int16).astype(np.float64) / 32768.0
    return a, fr


def render(a, fr):
    if len(a) == 0:
        return np.zeros(1, np.float32), fr
    hp_w = max(1, int(fr * HP_MS / 1000))
    hp = a - np.convolve(a, np.ones(hp_w) / hp_w, "same")    # high-pass: comparator tracks the tone, not DC
    env_w = max(1, int(fr * ENV_MS / 1000))
    env = np.sqrt(np.convolve(hp ** 2, np.ones(env_w) / env_w, "same"))
    gate = (env > max(GATE_FLOOR, env.max() * GATE_FRAC)).astype(np.float64)
    ramp = max(1, int(fr * RAMP_MS / 1000))
    gate = np.convolve(gate, np.ones(ramp) / ramp, "same")   # soft edges -> no clicks
    out = AMP * np.sign(hp) * gate                           # the 1-bit square -- exact source pitch
    return np.clip(out, -1.0, 1.0).astype(np.float32), fr


def write_wav(path, buf, fr):
    data = (np.clip(buf, -1.0, 1.0) * 32767.0).astype("<i2").tobytes()
    w = wave.open(path, "wb")
    w.setnchannels(1)
    w.setsampwidth(2)
    w.setframerate(fr)
    w.writeframes(data)
    w.close()


def main():
    paths = sorted(glob.glob(os.path.join(SND, "*.wav")))
    loaded = {p: load(p) for p in paths}                     # read ALL first (clean one-pass)
    for p in paths:
        cue = os.path.basename(p)[:-4]
        if cue in SKIP:
            print("  %-14s SKIP (weather ambience -> kept as recording)" % cue)
            continue
        a, fr = loaded[p]
        buf, fr = render(a, fr)
        write_wav(p, buf, fr)
        print("  %-14s chiptune  %.2fs" % (cue, len(buf) / fr))


if __name__ == "__main__":
    main()
