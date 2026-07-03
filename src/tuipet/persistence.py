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


def load_settings(path=None):
    """App-level prefs that outlive any single pet (e.g. the tamer name)."""
    path = path or SETTINGS_PATH
    try:
        return json.load(open(path))
    except (OSError, ValueError):
        return {}


def save_settings(d, path=None):
    path = path or SETTINGS_PATH
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


_ALBUM_SEEN = set()          # in-memory mirror: the 10s autosave was re-reading
                             # settings.json on every save just to no-op (audit 2026-07)


def album_add(num):
    if num is None or num < 0 or num in _ALBUM_SEEN:
        return
    _ALBUM_SEEN.add(num)
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


# --- cross-generation egg-unlock progress (DVPet eggUnlock.csv signals) -----------
# These outlive any single pet and feed egg.evaluate(): permanent milestones (album,
# wins, max generation/stage, maps cleared, tournament trophies, X-Antibody ever) plus
# a snapshot of the pet that just freed the slot, for the "previous generation" gates.

def _prog():
    return load_settings().get("progress", {})


def get_eggs_owned():
    """Egg indices permanently licensed (bought, or a met price-0 permanent unlock)."""
    return set(_prog().get("eggs_owned", []))


def egg_own(idx):
    if idx is None:
        return
    d = load_settings()
    prog = d.setdefault("progress", {})
    owned = set(prog.get("eggs_owned", []))
    if idx in owned:
        return
    owned.add(idx)
    prog["eggs_owned"] = sorted(owned)
    save_settings(d)


def _note_max(key, value):
    d = load_settings()
    prog = d.setdefault("progress", {})
    if int(value) > int(prog.get(key, 0)):
        prog[key] = int(value)
        save_settings(d)


def note_generation(g):
    _note_max("max_gen", g)


def note_stage_index(i):
    _note_max("max_stage", i)


def note_xanti():
    d = load_settings()
    prog = d.setdefault("progress", {})
    if not prog.get("xanti_ever"):
        prog["xanti_ever"] = True
        save_settings(d)


def _note_set(key, value):
    d = load_settings()
    prog = d.setdefault("progress", {})
    cur = set(prog.get(key, []))
    if value in cur:
        return
    cur.add(value)
    prog[key] = sorted(cur)
    save_settings(d)


def map_complete_add(map_index):
    _note_set("maps", int(map_index))


def tourney_add(trophy_id):
    _note_set("tourneys", int(trophy_id))


def snapshot_prev_gen(pet):
    """Record the just-ended pet's traits for the 'previous generation' egg gates."""
    if pet is None or getattr(pet, "stage", "Egg") == "Egg":
        return
    d = load_settings()
    prog = d.setdefault("progress", {})
    prog["last_gen"] = {
        "field": getattr(pet, "field", "") or "None",
        "attribute": getattr(pet, "attribute", "") or "None",
        "element": getattr(pet, "element", "") or "None",
        "mood": int(getattr(pet, "mood", 0)),
        "obedience": int(getattr(pet, "obedience", 0)),
        "xanti": getattr(pet, "x_antibody", "None") != "None",
    }
    save_settings(d)


def bank_digimemory(mem):
    """Park the departed's inheritance data in the generational channel (DVPet
    keeps items across resetToEgg; tuipet's per-save channel is progress, the
    same place the last_gen egg gates live).  One slot, like the device."""
    d = load_settings()
    d.setdefault("progress", {})["digimemory"] = dict(mem)
    save_settings(d)


def peek_digimemory():
    return _prog().get("digimemory") or None


def take_digimemory():
    """Pop the banked memory (the heir now carries it on its own save)."""
    d = load_settings()
    mem = (d.get("progress") or {}).pop("digimemory", None)
    if mem:
        save_settings(d)
    return mem or None


def get_progress():
    """Assemble the full progress view egg.evaluate() consumes."""
    prog = _prog()
    last = prog.get("last_gen", {}) or {}
    return {
        "album": set(prog.get("album", [])),
        "wins": int(prog.get("wins", 0)),
        "max_gen": int(prog.get("max_gen", 1)),
        "max_stage": int(prog.get("max_stage", 0)),
        "xanti_ever": bool(prog.get("xanti_ever", False)),
        "maps": set(prog.get("maps", [])),
        "tourneys": set(prog.get("tourneys", [])),
        "last_field": last.get("field", "None"),
        "last_attr": last.get("attribute", "None"),
        "last_elem": last.get("element", "None"),
        "last_mood": int(last.get("mood", 0)),
        "last_obed": int(last.get("obedience", 0)),
        "last_xanti": bool(last.get("xanti", False)),
    }


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


def to_save_dict(pet):
    """The on-disk/cloud save payload: the flat pet plus a wall-clock stamp used
    for offline catch-up AND last-write-wins cloud merge."""
    data = asdict(pet)
    data["_saved_at"] = time.time()
    return data


def save(pet, path=None):
    path = path or SAVE_PATH
    os.makedirs(os.path.dirname(path), exist_ok=True)
    data = to_save_dict(pet)
    tmp = path + ".tmp"
    with open(tmp, "w") as fh:
        json.dump(data, fh)
    os.replace(tmp, path)  # atomic
    if getattr(pet, "num", -1) >= 0 and pet.stage != "Egg":
        album_add(pet.num)            # grow the cross-pet album (gates egg unlocks)


def write_save_dict(data, path=None):
    """Atomically write a raw save dict (e.g. one pulled from the cloud) to disk."""
    path = path or SAVE_PATH
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w") as fh:
        json.dump(data, fh)
    os.replace(tmp, path)


def local_saved_at(path=None):
    """The _saved_at of the on-disk save, or 0.0 if there's no readable save."""
    path = path or SAVE_PATH
    try:
        return float(json.load(open(path)).get("_saved_at") or 0.0)
    except (ValueError, OSError, TypeError):
        return 0.0


def pet_from_save(data, catch_up=True):
    """Build (pet, message) from a save dict (disk or cloud). Returns (None, '')
    on malformed data. Applies the bounded offline decay when catch_up is set."""
    if not isinstance(data, dict):
        return None, ""
    data = dict(data)                            # don't mutate the caller's dict
    saved_at = data.pop("_saved_at", None)
    # JSON stringifies int dict keys: habitat_record / trophies_won come back
    # str-keyed, silently breaking habitat-gated evolutions and cup prelim
    # chains (audit 2026-07).  Coerce them back on every load.
    for k in ("habitat_record", "trophies_won"):
        v = data.get(k)
        if isinstance(v, dict):
            data[k] = {int(kk) if str(kk).lstrip("-").isdigit() else kk: vv
                       for kk, vv in v.items()}
    # _lights_t serializes float("-inf") as Infinity -- json emits it fine, but
    # guard against a stringified copy from older tooling
    if isinstance(data.get("_lights_t"), str):
        data["_lights_t"] = float("-inf")
    valid = {f.name for f in fields(Pet)}
    kwargs = {k: v for k, v in data.items() if k in valid}
    if "full_health" not in data and (data.get("stage") or "Egg") != "Egg":
        # pre-trained-HP save: grandfather the old flat stage HP so a grown pet
        # isn't nerfed to a hatchling's 5 (new pets start at StartingHealthPoints)
        from .battle import MAX_HEALTH, MAX_HEALTH_DEFAULT
        kwargs["full_health"] = MAX_HEALTH.get(data.get("stage"), MAX_HEALTH_DEFAULT)
    try:
        pet = Pet(**kwargs)
    except TypeError:
        return None, ""
    msg = ""
    if catch_up and saved_at:
        elapsed = min(max(0.0, time.time() - saved_at), MAX_OFFLINE)
        msg = _offline(pet, elapsed)
    return pet, msg


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
    new_poop = min(4, pet.poop + int(mins // 8))
    while len(pet.poop_sizes) < new_poop:            # keep poop == len(poop_sizes)
        pet.poop_sizes.append(pet._poop_size() if hasattr(pet, "_poop_size") else 2)
    pet.poop = new_poop
    if mins < 1:
        return ""
    if mins < 60:
        return f"Welcome back! ({int(mins)}m away) Your pet missed you."
    return f"Welcome back! ({int(mins / 60)}h away) Your pet needs care!"


def load(path=None, catch_up=True):
    """Return (pet, message) or (None, '') if no valid save exists."""
    path = path or SAVE_PATH
    if not os.path.exists(path):
        return None, ""
    try:
        data = json.load(open(path))
    except (ValueError, OSError):
        return None, ""
    return pet_from_save(data, catch_up=catch_up)


def delete(path=None):
    path = path or SAVE_PATH
    try:
        os.remove(path)
    except OSError:
        pass


def exists(path=None):
    return os.path.exists(path or SAVE_PATH)
