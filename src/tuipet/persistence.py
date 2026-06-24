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
SETTINGS_PATH = os.path.join(SAVE_DIR, "settings.json")


def load_settings(path=SETTINGS_PATH):
    """App-level prefs that outlive any single pet (e.g. the tamer name)."""
    try:
        return json.load(open(path))
    except (OSError, ValueError):
        return {}


def save_settings(d, path=SETTINGS_PATH):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w") as fh:
        json.dump(d, fh)
    os.replace(tmp, path)


def get_album():
    """Set of distinct Digimon species nums ever raised (the DM20-style zukan)."""
    return set(load_settings().get("progress", {}).get("album", []))


def get_wins():
    """Lifetime battle wins across all pets/generations."""
    return int(load_settings().get("progress", {}).get("wins", 0))


def album_add(num):
    if num is None or num < 0:
        return
    d = load_settings()
    prog = d.setdefault("progress", {})
    album = set(prog.get("album", []))
    if num in album:
        return                       # already registered -> no write
    album.add(num)
    prog["album"] = sorted(album)
    save_settings(d)


def wins_add(n=1):
    d = load_settings()
    prog = d.setdefault("progress", {})
    prog["wins"] = int(prog.get("wins", 0)) + int(n)
    save_settings(d)


def get_tamer():
    return (load_settings().get("tamer") or "").strip()


def set_tamer(name):
    d = load_settings()
    d["tamer"] = (name or "").strip()[:24]
    save_settings(d)


def get_account():
    """The cached lobby account: (name, password). (None, "") if unset."""
    a = load_settings().get("account") or {}
    name = (a.get("name") or "").strip()
    return (name or None, a.get("pw") or "")


def set_account(name, pw):
    d = load_settings()
    name = (name or "").strip()[:24]
    d["account"] = {"name": name, "pw": pw or ""}
    d["tamer"] = name
    save_settings(d)


def save(pet, path=SAVE_PATH):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    data = asdict(pet)
    data["_saved_at"] = time.time()
    tmp = path + ".tmp"
    with open(tmp, "w") as fh:
        json.dump(data, fh)
    os.replace(tmp, path)  # atomic
    if getattr(pet, "num", -1) >= 0 and pet.stage != "Egg":
        album_add(pet.num)            # grow the cross-pet album (gates egg unlocks)


def _offline(pet, elapsed):
    pet.world_seconds += elapsed       # keep the day/night clock turning while away
    pet.age_seconds += elapsed         # the pet ages while you're away
    if elapsed < 30 or pet.stage == "Egg":
        return ""
    mins = elapsed / 60.0
    # DVPet has no passive energy decay; just re-clamp to the (per-pet) range.
    pet.energy = _clamp(pet.energy, -pet.max_energy, pet.max_energy)
    pet.mood = _clamp(pet.mood - min(50, mins * 2), -300, 300)
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
