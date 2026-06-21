"""Save/load the pet to disk, with bounded offline catch-up.

The pet is a flat dataclass, so it serialises straight to JSON. On load we apply
a gentle "while you were away" decay (hunger/energy/mood/poop) scaled to the real
elapsed time — but never run evolution or death offline, so reopening is always
safe and predictable.
"""
from __future__ import annotations
import json
import os
import time
from dataclasses import asdict, fields

from .pet import Pet, _clamp

SAVE_DIR = os.path.expanduser("~/.local/share/tuipet")
SAVE_PATH = os.path.join(SAVE_DIR, "save.json")
MAX_OFFLINE = 36 * 3600  # cap catch-up at 36h of real time


def save(pet, path=SAVE_PATH):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    data = asdict(pet)
    data["_saved_at"] = time.time()
    tmp = path + ".tmp"
    with open(tmp, "w") as fh:
        json.dump(data, fh)
    os.replace(tmp, path)  # atomic


def _offline(pet, elapsed):
    pet.world_seconds += elapsed       # keep the day/night clock turning while away
    pet.age_seconds += elapsed         # the pet ages while you're away
    if elapsed < 30 or pet.stage == "Egg":
        return ""
    mins = elapsed / 60.0
    pet.energy = _clamp(pet.energy - min(60, mins * 3), 0, 100)
    pet.mood = _clamp(pet.mood - min(50, mins * 2), 0, 100)
    drop = min(pet.hunger, int(mins // 5))
    pet.hunger -= drop
    if mins > 10 and pet.hunger == 0:
        pet.care_mistakes += 1
    pet.poop = min(4, pet.poop + int(mins // 8))
    if mins < 1:
        return ""
    if mins < 60:
        return f"Welcome back! ({int(mins)}m away) Your pet missed you."
    return f"Welcome back! ({int(mins / 60)}h away) Your pet needs care!"


def load(path=SAVE_PATH, catch_up=True):
    """Return (pet, message) or (None, '') if no valid save exists."""
    if not os.path.exists(path):
        return None, ""
    try:
        data = json.load(open(path))
    except (ValueError, OSError):
        return None, ""
    saved_at = data.pop("_saved_at", None)
    valid = {f.name for f in fields(Pet)}
    kwargs = {k: v for k, v in data.items() if k in valid}
    try:
        pet = Pet(**kwargs)
    except TypeError:
        return None, ""
    msg = ""
    if catch_up and saved_at:
        elapsed = min(max(0.0, time.time() - saved_at), MAX_OFFLINE)
        msg = _offline(pet, elapsed)
    return pet, msg


def delete(path=SAVE_PATH):
    try:
        os.remove(path)
    except OSError:
        pass


def exists(path=SAVE_PATH):
    return os.path.exists(path)
