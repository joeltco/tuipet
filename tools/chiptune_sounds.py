#!/usr/bin/env python3
"""Render tuipet's SFX as raw 1-bit CHIPTUNE, converted directly from the authentic
DVPet recordings by a square-wave COMPARATOR -- no pitch detection, no transcription.

Every earlier attempt detected pitch and re-synthesized, and pitch detection kept
getting notes wrong. This drops transcription entirely: pass the recording through a
1-bit comparator (sign of the waveform). A comparator outputs a square wave at the
EXACT instantaneous frequency already present, so the melody is mathematically the
recording's own -- verified within ~1 cent of the source. That's how a 1-bit/piezo
speaker actually voices a tone.

Pipeline: authentic DVPet recording (raw_resources/sounds/*.wav)
          -> remove DC / slow drift (so the comparator's zero-crossings track the tone,
             not any offset)
          -> amplitude gate from the RMS envelope (silence stays silent instead of
             becoming full-volume square hiss)
          -> out = AMP * sign(signal) * gate   (the 1-bit square)
          -> mono 16-bit, native rate + speed.

Pure numpy, no external tools. Run: python3 tools/chiptune_sounds.py
"""
import os
import wave

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "src", "tuipet", "data", "sounds")
# resolve each source stem across candidates, in order: the pristine DVPet rips first,
# then the bundled recordings (the last resort for clone-only cues -- champion/reward/
# trainhit -- that aren't in the base DVPet sound set).
_SRC_DIRS = [
    os.path.join(ROOT, "raw_resources", "sounds"),
    os.path.join(ROOT, "_extract", "game", "DVPetTest", "jar", "resources", "sounds"),
    OUT,
]


def find_src(stem):
    for d in _SRC_DIRS:
        p = os.path.join(d, stem + ".wav")
        if os.path.exists(p):
            return p
    return None

AMP = 0.6              # square level (~-4.4 dB)
HP_MS = 4.0            # DC/drift-removal window
ENV_MS = 20.0          # RMS envelope window for the silence gate
GATE_FRAC, GATE_FLOOR = 0.08, 0.01
RAMP_MS = 4.0          # gate-edge ramp -> no clicks

# tuipet cue -> authentic DVPet source stem (5 subs have no 1:1 cue; see git history)
MAP = {
    "alarm": "alarm", "attack": "attack", "battle": "battle",
    "eat": "eat", "evolve": "evolve", "happy": "happy",
    "hatch": "hatch", "jogress": "jogress", "largePoop": "largePoop",
    "lastBite": "lastBite", "lose": "lose", "poop": "poop", "refuse": "refuse",
    "smallPoop": "smallPoop", "strongAttack": "strongAttack",
    "strongHit": "strongHit", "wash": "wash", "win": "win",
    "compatible": "compatible",   # DVPet pairing-handshake beep (battle/jogress match)
    "cancel": "error", "confirm": "click", "menu": "select", "scroll": "select",
    "death": "lose",
    "angry": "angry", "error": "error", "select": "select", "attackHit": "attackHit",
    "champion": "champion", "reward": "reward", "trainhit": "trainhit",
    # bundled-but-currently-unused DVPet cues -- convert them too so the whole non-weather
    # set is consistent chiptune (ready if a feature ever wires them up)
    "click": "click", "mischief": "mischief", "startBattle": "startBattle",
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


def render(src):
    a, fr = load(src)
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
    # read every source first, so a cue that sources from OUT (bundled) is read before we
    # start overwriting OUT -- a clean one-pass transform.
    loaded = {}
    for cue, stem in MAP.items():
        src = find_src(stem)
        if not src:
            print("  MISSING SOURCE:", cue, stem)
            continue
        loaded[cue] = render(src)
    for cue, (buf, fr) in loaded.items():
        write_wav(os.path.join(OUT, cue + ".wav"), buf, fr)
        print("  %-14s %.2fs%s" % (cue, len(buf) / fr, "  [SUB]" if cue in SUBS else ""))


if __name__ == "__main__":
    main()
