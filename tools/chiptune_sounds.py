#!/usr/bin/env python3
"""Render tuipet's SFX as raw square-wave CHIPTUNE, transcribed from the authentic
DVPet recordings by aubio.

Pipeline: authentic DVPet recording (raw_resources/sounds/*.wav)
          -> `aubionotes` (real monophonic note detection: midi/onset/offset)
          -> one square-wave voice per detected note (the piezo-buzzer voice)
          -> mono 16-bit 44.1kHz WAV.

The melody/timing is aubio's transcription of the REAL sound -- nothing is invented
and nothing is hand-corrected (rendering aubio's notes verbatim). Requires the
`aubio` package (provides the aubionotes CLI). Run: python3 tools/chiptune_sounds.py
"""
import os
import subprocess  # nosec B404 - aubionotes from PATH, no shell, our own files
import struct
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


def midi_hz(n):
    return 440.0 * 2.0 ** ((n - 69.0) / 12.0)


def aubio_notes(src):
    """[(midi, onset_s, offset_s)] from aubionotes' note-event lines."""
    out = subprocess.run(["aubionotes", "-i", src],         # nosec B603,B607 - fixed cmd, no shell
                         capture_output=True, text=True).stdout
    notes = []
    for line in out.splitlines():
        p = line.split()
        if len(p) == 3:                                      # midi  start  end
            notes.append((float(p[0]), float(p[1]), float(p[2])))
    return notes


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
    notes = aubio_notes(src)
    if not notes:
        return np.zeros(int(SR * 0.04), dtype=np.float32)
    total = max(off for _, _, off in notes)
    buf = np.zeros(int(SR * total) + SR // 100, dtype=np.float32)
    for midi, on, off in notes:                              # mono voice: note in its slot, gaps stay silent
        seg = square(midi_hz(midi), off - on)
        i = int(SR * on)
        buf[i:i + len(seg)] += seg
    return np.clip(buf, -1.0, 1.0)


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
        buf = render(src)
        write_wav(os.path.join(OUT, cue + ".wav"), buf)
        nn = len(aubio_notes(src))
        print("  %-14s <- %-13s %2d notes -> %.2fs chiptune%s"
              % (cue, stem + ".wav", nn, len(buf) / SR, "  [SUB]" if cue in SUBS else ""))


if __name__ == "__main__":
    main()
