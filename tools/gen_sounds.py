#!/usr/bin/env python3
"""Synthesize the tuipet sound set as clean chiptune SQUARE-WAVE beeps.

Authentic v-pets make sound through a piezo buzzer — single-voice square-wave tones,
not samples. This replaces the ripped DVPet WAVs with generated ones: pure stdlib
(wave + struct + math), bundled as small 16-bit mono WAVs and played by the existing
simple player (Termux termux-media-player / aplay / paplay). No runtime synth, no deps.

Run: python3 tools/gen_sounds.py   ->   src/tuipet/data/sounds/<name>.wav
"""
import math
import os
import struct
import wave

SR = 22050
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   "src", "tuipet", "data", "sounds")

# note frequencies (Hz)
N = {"C5": 523, "D5": 587, "E5": 659, "F5": 698, "G5": 784, "A5": 880, "B5": 988,
     "C6": 1046, "D6": 1175, "E6": 1318, "G6": 1568, "A6": 1760, "C7": 2093,
     "G4": 392, "A4": 440, "C4": 262, "E4": 330, "REST": 0}


def tone(freq, ms, vol=0.32, duty=0.5):
    """One square-wave note with a tiny attack/release ramp to kill clicks."""
    n = max(1, int(SR * ms / 1000))
    out = []
    period = SR / freq if freq > 0 else 1e9
    ramp = min(60, n // 4)
    for i in range(n):
        s = (vol if (i % period) / period < duty else -vol) if freq > 0 else 0.0
        env = 1.0
        if ramp:
            env = min(1.0, i / ramp, (n - i) / ramp)
        out.append(s * env)
    return out


def noise(ms, vol=0.28):
    """Pseudo-random square noise (impacts) — a deterministic LFSR so builds are stable."""
    n = int(SR * ms / 1000)
    out, lfsr = [], 0xACE1
    ramp = min(60, n // 3)
    for i in range(n):
        lfsr = ((lfsr >> 1) ^ (-(lfsr & 1) & 0xB400)) & 0xFFFF
        s = vol if (lfsr & 1) else -vol
        env = min(1.0, i / ramp, (n - i) / ramp) if ramp else 1.0
        out.append(s * env)
    return out


def seq(*parts):
    out = []
    for p in parts:
        out.extend(p)
    return out


def slide(f0, f1, ms, vol=0.3, steps=10):
    """A pitch glide built from short stepped tones (a chiptune portamento)."""
    return seq(*[tone(f0 + (f1 - f0) * k / (steps - 1), ms / steps, vol) for k in range(steps)])


# --- the sound set: each name -> a sample list (authentic short v-pet phrases) ---
def build():
    n = N
    S = {}
    # UI blips
    S["scroll"] = tone(n["E6"], 22, 0.22)
    S["select"] = tone(n["G6"], 26, 0.24)
    S["menu"] = tone(n["C6"], 30)
    S["confirm"] = seq(tone(n["A5"], 36), tone(n["E6"], 70))
    S["cancel"] = seq(tone(n["E5"], 36), tone(n["C5"], 70))
    S["error"] = seq(tone(n["E5"], 60, duty=0.25), tone(n["E5"], 0, 0), tone(n["C5"], 90, duty=0.25))
    S["result"] = seq(tone(n["G5"], 40), tone(n["C6"], 60))
    # care
    S["feed"] = seq(tone(n["C6"], 45), tone(n["REST"], 25), tone(n["C6"], 45), tone(n["REST"], 25), tone(n["E6"], 60))
    S["eat"] = S["feed"]
    S["clean"] = slide(n["C5"], n["C6"], 240)
    S["wash"] = S["clean"]
    S["heal"] = seq(tone(n["G5"], 50), tone(n["C6"], 50), tone(n["E6"], 110))
    # moods
    S["happy"] = seq(tone(n["C6"], 50), tone(n["E6"], 50), tone(n["G6"], 110))
    S["cheer"] = S["happy"]
    S["angry"] = seq(tone(n["E4"], 70, duty=0.2), tone(n["C4"], 90, duty=0.2))
    S["jeer"] = S["angry"]
    S["refuse"] = seq(tone(n["D5"], 50, duty=0.25), tone(n["C5"], 50, duty=0.25), tone(n["G4"], 90, duty=0.25))
    S["spit"] = S["refuse"]
    S["alarm"] = seq(*([tone(n["C6"], 80), tone(n["REST"], 60)] * 3))     # the care-call: urgent triple beep
    # lifecycle
    S["hatch"] = seq(tone(n["C6"], 50), tone(n["E6"], 50), tone(n["G6"], 50), tone(n["C7"], 130))
    S["evolve"] = seq(tone(n["C6"], 70), tone(n["E6"], 70), tone(n["G6"], 70),
                      tone(n["C7"], 70), tone(n["REST"], 40), tone(n["G6"], 60), tone(n["C7"], 220))
    S["jogress"] = seq(tone(n["G5"], 60), tone(n["B5"], 60), tone(n["D6"], 60),
                       tone(n["G6"], 60), tone(n["B5"], 60), tone(n["D6"], 200))
    S["dna"] = slide(n["C5"], n["C7"], 360, 0.26, steps=18)               # the DNA charge sweep
    S["death"] = seq(tone(n["C5"], 120), tone(n["G4"], 120), tone(n["E4"], 120), tone(n["C4"], 320))
    S["over"] = S["death"]
    # battle
    S["attack"] = slide(n["C7"], n["C5"], 90, 0.3, steps=8)               # a quick descending zap
    S["strongAttack"] = slide(n["C7"], n["C4"], 130, 0.34, steps=12)
    S["attackHit"] = noise(70)
    S["strongHit"] = noise(120, 0.34)
    S["battle"] = seq(tone(n["G5"], 60), tone(n["C6"], 60), tone(n["E6"], 60), tone(n["G6"], 140))
    S["win"] = seq(tone(n["C6"], 60), tone(n["E6"], 60), tone(n["G6"], 60), tone(n["C7"], 200))
    S["lose"] = seq(tone(n["E5"], 80), tone(n["D5"], 80), tone(n["C5"], 260))
    S["compatible"] = seq(tone(n["E6"], 45), tone(n["G6"], 45), tone(n["C7"], 110))
    S["reward"] = seq(tone(n["G5"], 50), tone(n["C6"], 50), tone(n["E6"], 50), tone(n["G6"], 160))
    S["champion"] = seq(tone(n["C6"], 55), tone(n["E6"], 55), tone(n["G6"], 55), tone(n["C7"], 60),
                        tone(n["REST"], 45), tone(n["G6"], 55), tone(n["C7"], 240))   # colosseum victory fanfare
    S["trainhit"] = seq(noise(45, 0.3), tone(n["G4"], 55, 0.3, duty=0.4))            # a punchy training-bag thud
    # eating / pooping
    S["lastBite"] = seq(tone(n["C6"], 45), tone(n["G5"], 70))             # the final swallow
    S["poop"] = slide(n["G5"], n["C5"], 120, 0.26, steps=6)              # a little plop
    S["smallPoop"] = slide(n["A5"], n["E5"], 100, 0.24, steps=6)
    S["largePoop"] = slide(n["E5"], n["C4"], 180, 0.3, steps=8)          # a bigger plop
    return S


def write_wav(name, samples):
    path = os.path.join(OUT, name + ".wav")
    with wave.open(path, "w") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        frames = b"".join(struct.pack("<h", int(max(-1.0, min(1.0, s)) * 32767)) for s in samples)
        w.writeframes(frames)
    return len(samples) / SR


def main():
    os.makedirs(OUT, exist_ok=True)
    sounds = build()
    # Only regenerate cues the clone already bundles -- this replaces the SFX with clean
    # synth chiptune while leaving the weather ambience (rain/thunder/wind, not defined here)
    # as their recordings, and never adds spurious unused files.
    written, skipped = [], []
    for name, samples in sorted(sounds.items()):
        if os.path.exists(os.path.join(OUT, name + ".wav")):
            write_wav(name, samples)
            written.append(name)
        else:
            skipped.append(name)
    print(f"regenerated {len(written)} clone SFX as chiptune:", " ".join(written))
    if skipped:
        print("(gen-only cues not in the clone, skipped:", " ".join(skipped) + ")")


if __name__ == "__main__":
    main()
