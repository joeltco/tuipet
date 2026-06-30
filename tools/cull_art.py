#!/usr/bin/env python3
"""Cull dead art keys from the shipped data files.

The authentic-rebuild stripped several DVPet subsystems (weather, the old training
drills, per-mon special attacks, the variety-food shop). Their art is still extracted
into the data files but is never rendered. This drops the unused keys — keeping every
live authentic sprite untouched — so the wheel doesn't ship dead ripped assets.

Live keys are verified against code references (see the comments below). Run after any
re-extract: python3 tools/cull_art.py
"""
import gzip
import json
import os

DATA = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                    "src", "tuipet", "data")

# effect keys with ZERO live render references (stripped features):
DEAD_EFFECTS = {
    "frozen", "call", "depressed", "flash",                 # weather + unused emotes
    "punching_bag", "punching_bag_broken", "train_green",   # old training drills
    "train_green_up", "train_shield", "train_button",
    "train_hit", "train_bar", "train_bar_empty", "train_cannon",
    "battle_bag", "atk_vaccine", "atk_data", "atk_virus",   # old per-attribute drill orbs
}


def _load_gz(name):
    with gzip.open(os.path.join(DATA, name), "rt", encoding="utf-8") as fh:
        return json.load(fh)


def _save_gz(name, obj):
    with gzip.open(os.path.join(DATA, name), "wt", encoding="utf-8") as fh:
        json.dump(obj, fh, separators=(",", ":"), ensure_ascii=False)


def main():
    # effects: drop the stripped-feature keys
    eff = _load_gz("effects.json.gz")
    kept = {k: v for k, v in eff.items() if k not in DEAD_EFFECTS}
    print("effects: %d -> %d keys (dropped %s)" % (
        len(eff), len(kept), sorted(set(eff) - set(kept))))
    _save_gz("effects.json.gz", kept)

    # orbs: battle uses only the generic attribute orbs; the per-mon `special` set is dead
    orbs = _load_gz("orbs.json.gz")
    if orbs.get("special"):
        print("orbs: dropping %d special per-mon orb sets (generic kept)" % len(orbs["special"]))
    orbs["special"] = {}
    _save_gz("orbs.json.gz", orbs)

    # icons: the variety-food system was stripped; feeding always uses f:0
    icons = _load_gz("icons.json.gz")
    food = {k: v for k, v in icons.items() if k == "f:0"}
    print("icons: %d -> %d keys (feeding uses only f:0)" % (len(icons), len(food)))
    _save_gz("icons.json.gz", food)

    # battle_overlays.json: banner/vs/burst are all authentic + live — left as-is.


if __name__ == "__main__":
    main()
