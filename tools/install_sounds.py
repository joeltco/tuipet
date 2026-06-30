#!/usr/bin/env python3
"""Install the AUTHENTIC DVPet sound effects as tuipet's SFX set.

Like the sprites, the sounds are real DVPet rips (jar resources/sounds), NOT
synthesized. The previous gen_sounds.py invented square-wave melodies that don't
match the device -- this replaces them with the genuine DVPet WAVs.

Each tuipet cue maps to a DVPet source file, converted to a uniform mono / 16-bit /
44.1kHz PCM (broad Termux/Android compatibility) while PRESERVING DVPet's own
relative levels (no per-file normalization -- that would un-balance the mix the
device shipped). A handful of cues have no 1:1 DVPet file and reuse the closest
authentic beep; those are flagged [SUB] below.

Run: python3 tools/install_sounds.py
"""
import os
import re
import subprocess  # nosec B404 - ffmpeg from a fixed path, no shell, our own files

TARGET_PEAK_DB = -2.0   # the raw DVPet rips sit ~-20 dB (device boosts at playback);
#                         lift each to a common ceiling so they're audible on a phone,
#                         preserving DVPet's relative mix (all sources peak near-uniform)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# authentic DVPet sound source -- via the raw_resources symlink (setup_assets) or the
# direct extract path (standalone); first that exists wins
_SRC_CANDIDATES = [
    os.path.join(ROOT, "raw_resources", "sounds"),
    os.path.join(ROOT, "_extract", "game", "DVPetTest", "jar", "resources", "sounds"),
]
SRC = next((p for p in _SRC_CANDIDATES if os.path.isdir(p)), _SRC_CANDIDATES[0])
OUT = os.path.join(ROOT, "src", "tuipet", "data", "sounds")

# tuipet cue -> authentic DVPet source stem. Direct unless it's in SUBS.
MAP = {
    "alarm": "alarm", "angry": "angry", "attack": "attack", "battle": "battle",
    "eat": "eat", "error": "error", "evolve": "evolve", "happy": "happy",
    "hatch": "hatch", "jogress": "jogress", "largePoop": "largePoop",
    "lastBite": "lastBite", "lose": "lose", "poop": "poop", "refuse": "refuse",
    "select": "select", "smallPoop": "smallPoop", "strongAttack": "strongAttack",
    "strongHit": "strongHit", "wash": "wash", "win": "win",
    # --- substitutions: no 1:1 DVPet cue, reuse the closest authentic beep ---
    "cancel": "error",    # back / cancel -> the reject buzz
    "confirm": "click",   # A-button confirm -> the button click
    "menu": "select",     # menu open -> the cursor tick
    "scroll": "select",   # list cursor-move blip -> the cursor tick
    "death": "lose",      # authentic death.wav is a 60s BGM track, not a beep -> defeat tone
}
SUBS = {"cancel", "confirm", "menu", "scroll", "death"}


def peak_db(path):
    """Source peak in dBFS (bit-depth conversion doesn't change dB, so measure the src)."""
    out = subprocess.run(                                 # nosec B603,B607 - fixed cmd, no shell
        ["ffmpeg", "-i", path, "-af", "volumedetect", "-f", "null", os.devnull],
        capture_output=True, text=True)
    m = re.search(r"max_volume:\s*(-?[0-9.]+) dB", out.stderr)
    return float(m.group(1)) if m else None


def main():
    keep, missing = set(), []
    for name, stem in MAP.items():
        src = os.path.join(SRC, stem + ".wav")
        if not os.path.exists(src):
            missing.append((name, stem))
            continue
        dst = os.path.join(OUT, name + ".wav")
        pk = peak_db(src)
        gain = (TARGET_PEAK_DB - pk) if pk is not None else 0.0
        af = ["-af", "volume=%.1fdB" % gain] if abs(gain) > 0.1 else []
        subprocess.run(                                   # nosec B603,B607 - fixed cmd, no shell
            ["ffmpeg", "-y", "-i", src, "-ac", "1", "-ar", "44100"] + af
            + ["-c:a", "pcm_s16le", dst],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        keep.add(name + ".wav")
        print("  %-14s <- %-14s peak %+.1f->%.1f dB%s"
              % (name, stem + ".wav", pk or 0, TARGET_PEAK_DB, "  [SUB]" if name in SUBS else ""))
    # drop any leftover synthesized/dead wavs so the wheel ships only live authentic SFX
    orphans = sorted(f for f in os.listdir(OUT) if f.endswith(".wav") and f not in keep)
    for f in orphans:
        os.remove(os.path.join(OUT, f))
    print("\ninstalled %d authentic cues (%d direct, %d sub); removed %d orphan(s): %s"
          % (len(keep), len(MAP) - len(SUBS), len(SUBS), len(orphans), orphans))
    if missing:
        print("MISSING SOURCES:", missing)


if __name__ == "__main__":
    main()
