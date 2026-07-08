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


def _atomic_write_json(path, data, keep_bak=False):
    """Atomic JSON write (tmp + os.replace); keep_bak rotates one generation
    back first.  This dance lived in three hand-rolled copies (settings, save,
    cloud-pull; refactor 2026-07-05)."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w") as fh:
        json.dump(data, fh)
    if keep_bak and os.path.exists(path):
        os.replace(path, path + ".bak")   # keep one generation back
    os.replace(tmp, path)


def load_settings(path=None):
    """App-level prefs that outlive any single pet (e.g. the lobby account).
    Falls back to the .bak rotated by save_settings -- settings hold the album,
    lifetime wins, owned eggs and the banked Digimemory; one corrupt write must
    not erase a save file's whole history (audit 2026-07)."""
    path = path or SETTINGS_PATH
    for candidate in (path, path + ".bak"):
        try:
            return json.load(open(candidate))
        except (OSError, ValueError):
            continue
    return {}


def save_settings(d, path=None):
    _atomic_write_json(path or SETTINGS_PATH, d, keep_bak=True)


def get_album():
    """Set of distinct Digimon species ever raised, NAME-CANONICAL (the
    DM20-style zukan).  DVPet's dex sync is by name (checkNaturalUnlocked):
    the 1410+ egg-hatch duplicate rows and their chart twins reveal together
    -- old saves may hold either num, so entries canonicalize on read
    (album/dex audit 2026-07-06)."""
    from . import data
    return {data.canonical_num(n)
            for n in load_settings().get("progress", {}).get("album", [])}


def get_wins():
    """Lifetime battle wins across all pets/generations."""
    return int(load_settings().get("progress", {}).get("wins", 0))


_ALBUM_SEEN: set[int] = set()   # in-memory mirror: the 10s autosave was re-reading
                             # settings.json on every save just to no-op (audit 2026-07)


def album_seen(num):
    """Has ANY generation been this form -- under EITHER of its name-twin nums?
    (canon Evolution.setUnlocked + checkNaturalUnlocked: the dex reveal state
    the hidden-evolution mask keys on, synced across same-name rows)."""
    from . import data
    num = data.canonical_num(num)
    if num in _ALBUM_SEEN:
        return True
    return num in get_album()


def album_add(num):
    if num is None or num < 0:
        return
    from . import data
    num = data.canonical_num(num)    # store the name-canonical identity
    if num in _ALBUM_SEEN:
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


def _note_add(key, n):
    """Bump a lifetime progress counter (the generic behind wins/mega_kills --
    the load-modify-save dance was copied per counter; refactor 2026-07-05)."""
    d = load_settings()
    prog = d.setdefault("progress", {})
    prog[key] = int(prog.get(key, 0)) + int(n)
    save_settings(d)
    return prog[key]


def wins_add(n=1):
    return _note_add("wins", n)


def mega_kills_add(n=1):
    """Lifetime Mega/Ultimate-class foes felled (gates the X egg; LINES_SPEC §7)."""
    return _note_add("mega_kills", n)


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
    if idx is not None:
        _note_set("eggs_owned", idx)


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
    """Record the just-ended pet's traits for the 'previous generation' egg
    gates -- and the careBonusOnReset math (death/rebirth audit 2026-07-06):
    the ended life's care ADJUSTS the bonus the next generation inherits.
    Canon never zeroes _bonus on resetToEgg; tuipet carries it through this
    channel instead."""
    if pet is None or getattr(pet, "stage", "Egg") == "Egg":
        return
    # (the careBonusOnReset math moved to Pet.final_care_grade -> the
    # bonus_seed channel -- this copy was a second, PARTIAL grading of the
    # same life that the seed always stomped; digimemory audit 2026-07-06)
    d = load_settings()
    prog = d.setdefault("progress", {})
    prog["last_gen"] = {
        "field": getattr(pet, "field", "") or "None",
        "attribute": getattr(pet, "attribute", "") or "None",
        "element": getattr(pet, "element", "") or "None",
        "mood": int(getattr(pet, "mood", 0)),
        "obedience": int(getattr(pet, "obedience", 0)),
        "xanti": getattr(pet, "x_antibody", "None") != "None",
        # the DEVICE BAG (item/inventory audit 2026-07-06): canon's resetToEgg
        # never touches bits, the bag, or the beaten-qualifier trophies --
        # they are device-lifetime; the heir inherits them all
        "bits": int(getattr(pet, "bits", 0)),
        "inventory": dict(getattr(pet, "inventory", {}) or {}),
        "trophies": int(getattr(pet, "trophies", 0)),
        "trophies_won": dict(getattr(pet, "trophies_won", {}) or {}),
    }
    save_settings(d)


def prev_gen_estate():
    """The device-lifetime estate the next generation inherits (bits, the bag,
    the trophy room -- canon resetToEgg preserves them all)."""
    d = load_settings()
    last = (d.get("progress") or {}).get("last_gen") or {}
    # JSON stringifies int dict keys (the habitat_record/trophies_won load
    # trap): coerce them back so prelim-chain lookups keep matching
    tw = {int(k) if str(k).lstrip("-").isdigit() else k: v
          for k, v in (last.get("trophies_won") or {}).items()}
    return {"bits": int(last.get("bits", 0)),
            "inventory": dict(last.get("inventory") or {}),
            "trophies": int(last.get("trophies", 0)),
            "trophies_won": tw}


def _note_put(key, value):
    """Park a one-slot value in the generational progress channel."""
    d = load_settings()
    d.setdefault("progress", {})[key] = value
    save_settings(d)


def _note_take(key):
    """Pop a one-slot progress value (None when the slot is empty)."""
    d = load_settings()
    v = (d.get("progress") or {}).pop(key, None)
    if v is not None:
        save_settings(d)
    return v


def shop_unlock_add(key):
    """Canon unlockItem/unlockFood (shop/economy audit 2026-07-06): finding a
    consumable in the wild UNLOCKS its home-shop listing for good -- device-
    lifetime in canon (the bag survives resetToEgg), so the per-save progress
    channel here.  The nine Digimentals are the payload: found once, buyable
    (4000b) forever after."""
    d = load_settings()
    got = d.setdefault("progress", {}).setdefault("shop_unlocks", [])
    if key not in got:
        got.append(key)
        save_settings(d)


def shop_unlocks():
    d = load_settings()
    return set((d.get("progress") or {}).get("shop_unlocks") or [])


def bank_digimemory(mem):
    """Park the departed's inheritance data in the generational channel (DVPet
    keeps items across resetToEgg; tuipet's per-save channel is progress, the
    same place the last_gen egg gates live).  One slot, like the device."""
    _note_put("digimemory", dict(mem))


def bank_bonus_seed(n):
    """Park the departed's care grade (careBonusOnReset) for the next egg."""
    _note_put("bonus_seed", int(n))


def take_bonus_seed():
    return int(_note_take("bonus_seed") or 0)


def peek_digimemory():
    return _prog().get("digimemory") or None


def take_digimemory():
    """Pop the banked memory (the heir now carries it on its own save)."""
    return _note_take("digimemory") or None


def get_progress():
    """Assemble the full progress view egg.evaluate() consumes."""
    prog = _prog()
    last = prog.get("last_gen", {}) or {}
    return {
        "album": get_album(),        # name-canonical (the egg gates match on it)
        "wins": int(prog.get("wins", 0)),
        "mega_kills": int(prog.get("mega_kills", 0)),
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


def get_account():
    """The cached lobby account: (name, password). (None, "") if unset."""
    a = load_settings().get("account") or {}
    name = (a.get("name") or "").strip()
    return (name or None, a.get("pw") or "")


def set_account(name, pw):
    d = load_settings()
    name = (name or "").strip()[:24]
    d["account"] = {"name": name, "pw": pw or ""}
    save_settings(d)


def erase_all():
    """Erase the WHOLE local state: pet save (+bak), settings (progress,
    account, digimemory, +bak), sound + theme prefs.  The cloud copy stays
    with the account server-side; with the login gone, nothing pulls it.
    Options-menu 'Erase all data' (Joel 2026-07-04)."""
    removed = []
    for fn in ("save.json", "save.json.bak", "settings.json", "settings.json.bak",
               "sound.txt", "theme.txt"):
        p = os.path.join(SAVE_DIR, fn)
        try:
            os.remove(p)
            removed.append(fn)
        except OSError:
            pass
    return removed


def to_save_dict(pet):
    """The on-disk/cloud save payload: the flat pet plus a wall-clock stamp used
    for offline catch-up AND last-write-wins cloud merge."""
    data = asdict(pet)
    data["_saved_at"] = time.time()
    return data


def save(pet, path=None):
    # the .bak generation matters: a corrupt main save used to mean a silent
    # new egg -- and the next autosave then DESTROYED the old pet
    _atomic_write_json(path or SAVE_PATH, to_save_dict(pet), keep_bak=True)
    if getattr(pet, "num", -1) >= 0 and pet.stage != "Egg":
        album_add(pet.num)            # grow the cross-pet album (gates egg unlocks)


def write_save_dict(data, path=None):
    """Atomically write a raw save dict (e.g. one pulled from the cloud) to disk."""
    _atomic_write_json(path or SAVE_PATH, data)


def local_saved_at(path=None):
    """The _saved_at of the on-disk save, or 0.0 if there's no readable save."""
    path = path or SAVE_PATH
    try:
        return float(json.load(open(path)).get("_saved_at") or 0.0)
    except (ValueError, OSError, TypeError):
        return 0.0


def pet_from_save(data, catch_up=True, strict=False):
    """Build (pet, message) from a save dict (disk or cloud). Returns (None, '')
    on malformed data. Applies the bounded offline decay when catch_up is set.

    strict=True (the cloud probe) REJECTS foreign-format saves outright --
    a save whose name/stage disagree with its dex was written by a different
    tuipet (the 2026-07-04 incident: an outdated client pushed a rebuild-era
    save with stage 'Child' and an empty name; the probe let it clobber the
    local pet).  strict=False (the local load) REPAIRS instead: the pet is
    re-derived from its dex and re-bound to its line, so a corrupted file
    becomes a playable pet rather than a silent fresh-egg wipe."""
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
    # a dataclass constructor validates NOTHING: a save with the right keys but
    # wrong-typed values (hand-edited file, corrupt cloud payload) builds a pet
    # that crashes minutes later in tick().  Reject it here instead -- this also
    # guards sync_down_at_startup's probe (audit 2026-07).
    for fname, want in (("hunger", (int, float)), ("energy", (int, float)),
                        ("mood", (int, float)), ("weight", (int, float)),
                        ("bits", (int, float)), ("poop", (int, float)),
                        ("world_seconds", (int, float)), ("age_seconds", (int, float)),
                        ("lifespan", (int, float)), ("sleep_lapse", (int, float)),
                        ("stage", str), ("attribute", str),
                        ("inventory", dict), ("poop_sizes", list)):
        if not isinstance(getattr(pet, fname), want):
            return None, ""
    # a save written mid-adventure carries the ROAD's habitat; the pet comes
    # home while you're away (habitat audit 2026-07-06 -- adventures are
    # per-session, so the current habitat always loads as the home)
    if getattr(pet, "home_habitat", -1) >= 0 and pet.habitat != pet.home_habitat:
        pet.habitat = pet.home_habitat
    msg = ""
    if pet.num >= 0 and pet.stage != "Egg":
        from . import data as _data
        _, by_num = _data.load_sprites()
        rec = by_num.get(pet.num)
        if rec is None:
            # a dex this build has never heard of: the cloud must not push it,
            # but a LOCAL save survives a data refresh untouched (robustness
            # contract -- test_load_unknown_num)
            if strict:
                return None, ""
        elif pet.stage != rec["stage"] or pet.name != rec["name"]:
            if strict:
                return None, ""              # foreign format: never accept from the cloud
            # local repair: identity comes from the dex; the line re-binds by name
            from . import lines as _lines
            croot, lid = _lines.canonical_root(pet.num)
            pet._become(croot if croot is not None else pet.num)
            pet.line_id = lid
            pet.stage_seconds = 0.0
            msg = "(save repaired — the pet's records were from another version)"
    if catch_up and saved_at:
        elapsed = min(max(0.0, time.time() - saved_at), MAX_OFFLINE)
        off = _offline(pet, elapsed)
        msg = (msg + "  " + off).strip() if off else msg
    return pet, msg


def _offline(pet, elapsed):
    """The BOUNDED offline decay -- a deliberate design divergence from canon
    (completeness sweep 2026-07-06): DVPet's processSkippedSeconds replays
    EVERY skipped second through the full lapse machinery (auto-care feeding
    mid-replay, mistakes, death while away).  On tuipet's compressed clock a
    full replay of 8h away = ~20 pet-days = a guaranteed grave; the capped
    approximation below is the humane terminal-app adaptation."""
    if getattr(pet, "dead", False):
        # the departed do not decay: the catch-up starved/soiled a corpse and
        # greeted 'Your pet needs care!' over the grave (dead sweep 2026-07-06);
        # even the clocks stay still -- its age is part of the epitaph
        return ""
    pet.world_seconds += elapsed       # keep the day/night clock turning while away
    pet.age_seconds += elapsed         # the pet ages while you're away (canon: the age
    #                                    clock timeToAgeMin has NO egg gate -- age runs
    #                                    from egg creation, so a hatchling carries it)
    if pet.stage == "Egg":
        # canon's replay advances incubation too: an egg left alone hatches while
        # you're away.  Advance the growth clock so the return greets a hatch --
        # aging WITHOUT incubating was the one incoherent half-state (2026-07-06).
        pet.stage_seconds += elapsed
        return ""
    if elapsed < 30:
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
    """Return (pet, message) or (None, '') if no valid save exists.  A corrupt
    main save falls back to the .bak rotated by save() -- at most one autosave
    (~10s) behind, instead of a silent new egg."""
    path = path or SAVE_PATH
    for candidate in (path, path + ".bak"):
        if not os.path.exists(candidate):
            continue
        try:
            data = json.load(open(candidate))
        except (ValueError, OSError):
            continue
        pet, msg = pet_from_save(data, catch_up=catch_up)
        if pet is not None:
            if candidate != path:
                msg = (msg + "  " if msg else "") + "(recovered from the backup save)"
            return pet, msg
    return None, ""


def delete(path=None):
    """Remove the save AND its .bak -- a deliberate delete must not come back
    from the backup on the next launch."""
    path = path or SAVE_PATH
    for candidate in (path, path + ".bak"):
        try:
            os.remove(candidate)
        except OSError:
            pass


def exists(path=None):
    return os.path.exists(path or SAVE_PATH)
