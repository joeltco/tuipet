"""Bake data/sounds/boot.wav — the power-on jingle (Joel 2026-07-20:
"make a tiny jingle using the beeps we already use").

Every sample is lifted from the shipped device rips; nothing is
synthesized.  The device speaks three tones (trainhit ~1632Hz low,
click ~2736Hz mid, menu ~4084Hz high) in 40ms beep units — the jingle
is a rising da-di-dii-dii: low, mid, high, high, 40ms of silence
between notes.  The low note is cut from trainhit's sustained tone, so
it gets a 3ms fade-out to land without a pop; the mid beep and high
blip already end on silence/zero-adjacent samples and are used whole.

Run from the repo root: python3 tools/make_boot_jingle.py
"""
import os
import wave

import numpy as np

DIR = os.path.join(os.path.dirname(__file__), "..", "src", "tuipet", "data", "sounds")
RATE = 44100
NOTE = int(0.04 * RATE)          # the device's 40ms beep unit
GAP = np.zeros(NOTE, dtype=np.int16)


def _samples(name):
    with wave.open(os.path.join(DIR, name + ".wav")) as w:
        assert (w.getframerate(), w.getnchannels(), w.getsampwidth()) == (RATE, 1, 2)
        return np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16)


def main():
    low = _samples("trainhit")[:NOTE].astype(np.float64)
    ramp = int(0.003 * RATE)     # 3ms fade so the cut sustained tone doesn't pop
    low[-ramp:] *= np.linspace(1.0, 0.0, ramp)
    low = low.astype(np.int16)
    mid = _samples("click")[:NOTE]          # click = two 40ms beeps; take the first
    hi = _samples("menu")                    # the 40ms high blip, whole
    jingle = np.concatenate([low, GAP, mid, GAP, hi, GAP, hi])
    out = os.path.join(DIR, "boot.wav")
    with wave.open(out, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(RATE)
        w.writeframes(jingle.tobytes())
    print(f"wrote {out}: {len(jingle) / RATE:.2f}s, peak {np.abs(jingle).max()}")


if __name__ == "__main__":
    main()
