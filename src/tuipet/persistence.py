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

def _can_use(d):
    """True if we could actually WRITE here -- without creating anything yet
    (an import-time mkdir would litter every dev box and test run)."""
    if os.path.isdir(d):
        return os.access(d, os.W_OK)
    parent = os.path.dirname(d)
    while parent and not os.path.isdir(parent):
        parent = os.path.dirname(parent)
    return bool(parent) and os.access(parent, os.W_OK)


def _pick_save_dir():
    """Where the pet lives.  iOS (a-Shell, our official iPhone/iPad target)
    CANNOT write to `~` -- only ~/Documents, ~/Library and ~/tmp are writable.
    tuipet wrote to ~/.local/share/tuipet and _atomic_write_json swallows
    OSError, so on iOS every save failed SILENTLY: the pet never persisted and
    the player was never told (iOS support 2026-07-13).  Pick the first
    location we can actually write, and let TUIPET_SAVE_DIR override."""
    env = os.environ.get("TUIPET_SAVE_DIR")
    if env:
        return os.path.expanduser(env)
    cands = []
    xdg = os.environ.get("XDG_DATA_HOME")
    if xdg:
        cands.append(os.path.join(os.path.expanduser(xdg), "tuipet"))
    cands.append(os.path.expanduser("~/.local/share/tuipet"))   # Linux/Termux/macOS
    cands.append(os.path.expanduser("~/Documents/tuipet"))      # iOS: the writable home
    for d in cands:
        if _can_use(d):
            return d
    return cands[0]              # nothing writable: saves will fail LOUDLY now


SAVE_DIR = _pick_save_dir()
SAVE_PATH = os.path.join(SAVE_DIR, "save.json")
MAX_OFFLINE = 36 * 3600  # cap catch-up at 36h of real time
SETTINGS_PATH = os.path.join(SAVE_DIR, "settings.json")

# set by _atomic_write_json when the disk refuses us -- the app surfaces it once
# so a silently-unsaveable install (iOS's read-only ~) can never eat a pet
save_failed = ""


def _atomic_write_json(path, data, keep_bak=False):
    """Atomic JSON write (tmp + os.replace); keep_bak rotates one generation
    back first.  This dance lived in three hand-rolled copies (settings, save,
    cloud-pull; refactor 2026-07-05)."""
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        tmp = path + ".tmp"
        with open(tmp, "w") as fh:
            json.dump(data, fh)
        if keep_bak and os.path.exists(path):
            os.replace(path, path + ".bak")   # keep one generation back
        os.replace(tmp, path)
    except OSError as e:
        # best-effort, mirroring the read side (load/load_settings both swallow
        # OSError): a full / read-only / quota'd disk must never crash the 10s
        # autosave timer or on_unmount teardown (hardening 2026-07-12).  A
        # non-serializable payload still raises TypeError -- that is a bug, not
        # a disk problem, and must surface.
        #
        # ...but it must not be SILENT either (iOS support 2026-07-13): a
        # read-only save dir meant the pet quietly never persisted and the
        # player only found out by losing it.  Record it; the app warns.
        global save_failed
        save_failed = "%s: %s" % (os.path.dirname(path) or path, e.strerror or e)
        return


def load_settings(path=None):
    """App-level prefs that outlive any single pet (e.g. the lobby account).
    Falls back to the .bak rotated by save_settings -- settings hold the album,
    lifetime wins, owned eggs and the banked Digimemory; one corrupt write must
    not erase a save file's whole history (audit 2026-07)."""
    path = path or SETTINGS_PATH
    for candidate in (path, path + ".bak"):
        try:
            d = json.load(open(candidate))
        except (OSError, ValueError):
            continue
        if _migrate_v401_settings(d):        # .400/.401 egg indices -> .402 bank
            save_settings(d, path)
        return d
    return {}


def get_auto_update():
    """Should the game install a newer release for itself at launch?  On by
    default (Joel 2026-07-14) -- a player can turn it off in g options."""
    return bool(load_settings().get("auto_update", True))


def get_cloud_sync():
    """The player-facing cloud-save switch (settings only; see sync_enabled)."""
    return bool(load_settings().get("cloud_sync", True))


def set_cloud_sync(on):
    d = load_settings()
    d["cloud_sync"] = bool(on)
    save_settings(d)
    return bool(on)


def sync_enabled():
    """Should any cloud traffic run?  False when TUIPET_NO_SYNC is set (dev
    override) or the options toggle is off.  Every sync entry point checks
    THIS -- TUIPET_NO_SYNC used to gate only the startup pull while pushes
    ran anyway (sweep 2026-07-14)."""
    if os.environ.get("TUIPET_NO_SYNC"):
        return False
    return get_cloud_sync()


_LOCK_NAME = "running.pid"


def acquire_instance_lock():
    """Claim the save dir for this process.  Returns the OTHER live pid when a
    second copy already runs (two instances autosave over one file,
    last-write-wins -- sweep 2026-07-14), else records our pid and returns
    None.  Doubt resolves to 'not locked': wrongly blocking a player is worse
    than the old free-for-all."""
    p = os.path.join(SAVE_DIR, _LOCK_NAME)
    try:
        other = int(open(p).read().strip())
    except (OSError, ValueError):
        other = None
    if other and other != os.getpid():
        try:
            os.kill(other, 0)
            return other             # alive: the save is claimed
        except PermissionError:
            return other             # alive, just not ours to signal
        except OSError:
            pass                     # stale lock from a dead run
    try:
        os.makedirs(SAVE_DIR, exist_ok=True)
        with open(p, "w") as f:
            f.write(str(os.getpid()))
    except OSError:
        pass                         # unwritable dir: nothing to fight over either
    return None


def release_instance_lock():
    """Drop the pid file, but only if it is ours (best-effort)."""
    p = os.path.join(SAVE_DIR, _LOCK_NAME)
    try:
        if int(open(p).read().strip()) == os.getpid():
            os.remove(p)
    except (OSError, ValueError):
        pass


def write_crash_log(exc):
    """Write the full traceback to crash.log in the save dir (one file, newest
    crash wins).  Returns the path, or None when the disk refused."""
    import traceback
    try:
        os.makedirs(SAVE_DIR, exist_ok=True)
        p = os.path.join(SAVE_DIR, "crash.log")
        with open(p, "w", encoding="utf-8") as f:
            f.write("tuipet crash — %s\n" % time.strftime("%Y-%m-%d %H:%M:%S"))
            traceback.print_exception(type(exc), exc, exc.__traceback__, file=f)
        return p
    except OSError:
        return None


def set_auto_update(on):
    d = load_settings()
    d["auto_update"] = bool(on)
    save_settings(d)
    return bool(on)


def save_settings(d, path=None):
    # every write stamps the CURRENT egg-bank version -- without it, a
    # settings file created THIS session would look like a pre-migration
    # (.400/.401) file on the next load and get wrongly re-translated
    d["egg_order_v"] = EGG_ORDER_V
    _atomic_write_json(path or SETTINGS_PATH, d, keep_bak=True)


# --- egg-bank index migration (2026-07-10 egg saga) ---------------------------
# .400/.401 shipped an 84-egg bank; .402 cut/reordered to 78; .403 restored
# Nature Spirits (79); .404's dominance audit cut 11 duplicate eggs -- FIVE of
# them classics, so the classic block moves too.  Saved egg INDICES translate
# by (name, occurrence) through the FULL bank order of whichever build wrote
# them (occurrence handles the twin "???" mystery eggs).
EGG_ORDER_V = 4
_CLASSIC49 = [
    "YukimiBotamon", "Botamon", "Punimon", "Poyomon", "Yuramon", "Zurumon",
    "Babumon", "Pichimon", "Mokumon", "Nyokimon", "Choromon", "Kuramon",
    "Chibickmon", "Tsubumon", "Pururumon", "Jyarimon", "Dodomon", "Puttimon",
    "Kiimon", "Dokimon", "Chibomon", "Datirimon", "ChibiKiwimon", "Ketomon",
    "Leafmon", "Pafumon", "Paomon", "Petitmon", "Popomon", "Pupumon",
    "Bommon", "Pusumon", "Puwamon", "Relemon", "Sakumon", "Zerimon",
    "Cocomon", "Fufumon", "Cotsucomon", "Algomon I", "Bombmon", "Carimon",
    "Sunamon", "Curimon", "Pyonmon", "Puyomon", "???", "???", "Fusamon"]
_V401_FULL = _CLASSIC49 + [
    "Breakdra Egg", "Corona Egg", "DORU Egg", "Deep Savers Egg",
    "Digitama X", "Digitama X2", "Digitama X3", "Vorvomon Egg", "Draco Egg",
    "Hack Egg", "Kera Digitama", "Lalamon Egg", "Lop Egg", "Ludo Egg",
    "Luna Egg", "Meicoo Egg", "Meicoomon Egg", "Metal Empire Egg",
    "Nature Spirits Egg", "Nightmare Soldiers Egg",
    "Nightmare Soldiers Ver.20th Egg", "Ryuda Egg", "Slayerdra Egg",
    "Terrier Egg", "V Egg", "Version 1 Egg", "Version 2 Egg",
    "Version 3 Egg", "Version 4 Egg", "Version 5 Egg", "Version 6 Egg",
    "Virus Busters Egg", "Virus Busters Ver. 20th Egg",
    "Wind Guardians Egg", "Zuba Egg"]
_V402_FULL = _CLASSIC49 + [
    "Version 1 Egg", "Version 2 Egg", "Version 3 Egg", "Version 4 Egg",
    "Version 5 Egg", "Deep Savers Egg", "Nightmare Soldiers Egg",
    "Wind Guardians Egg", "Metal Empire Egg", "Virus Busters Egg",
    "Corona Egg", "Luna Egg", "Zuba Egg", "Hack Egg", "Meicoo Egg",
    "DORU Egg", "Slayerdra Egg", "Breakdra Egg", "Ryuda Egg", "Draco Egg",
    "Lalamon Egg", "Ludo Egg", "Meicoomon Egg", "Terrier Egg", "Lop Egg",
    "V Egg", "Virus Busters Ver. 20th Egg", "Digitama X3", "Kera Digitama"]
_V403_FULL = _CLASSIC49 + [
    "Version 1 Egg", "Version 2 Egg", "Version 3 Egg", "Version 4 Egg",
    "Version 5 Egg", "Nature Spirits Egg", "Deep Savers Egg",
    "Nightmare Soldiers Egg", "Wind Guardians Egg", "Metal Empire Egg",
    "Virus Busters Egg", "Corona Egg", "Luna Egg", "Zuba Egg", "Hack Egg",
    "Meicoo Egg", "DORU Egg", "Slayerdra Egg", "Breakdra Egg", "Ryuda Egg",
    "Draco Egg", "Lalamon Egg", "Ludo Egg", "Meicoomon Egg", "Terrier Egg",
    "Lop Egg", "V Egg", "Virus Busters Ver. 20th Egg", "Digitama X3",
    "Kera Digitama"]
# a CUT egg MID-INCUBATION falls back to the surviving egg of the same baby
# (name -> name; resolved against the live bank).  Fallbacks are for egg_type
# ONLY -- never for eggs_owned, or a cut egg would "translate" into permanent
# ownership of an unearned egg (the .403 Puttimon-as-starter bug).
_CUT_FALLBACK = {
    "Digitama X": "Puttimon", "Digitama X2": "Kiimon",
    "Vorvomon Egg": "Nightmare Soldiers Egg",
    "Nightmare Soldiers Ver.20th Egg": "Metal Empire Egg",
    "Version 6 Egg": "Nature Spirits Egg", "Ludo Egg": "Cotsucomon",
    "Version 1 Egg": "Botamon", "Version 2 Egg": "Punimon",
    "Version 3 Egg": "Poyomon", "Version 4 Egg": "Yuramon",
    "Version 5 Egg": "Zurumon", "YukimiBotamon": "Virus Busters Egg",
    "Pichimon": "Deep Savers Egg", "Mokumon": "Nightmare Soldiers Egg",
    "Nyokimon": "Wind Guardians Egg", "Choromon": "Metal Empire Egg"}


def _current_names():
    from . import egg as egg_mod
    return [egg_mod.hatch_name(i) for i in range(egg_mod.count())]


def _find_occurrence(names, name, occ):
    seen = 0
    for i, n in enumerate(names):
        if n == name:
            seen += 1
            if seen == occ:
                return i
    return None


def _migrate_egg_index(old, table=_V401_FULL, fallback=True):
    """Translate an old-bank egg index into the current bank (None = drop)."""
    if not isinstance(old, int) or not (0 <= old < len(table)):
        return None
    name = table[old]
    occ = table[:old + 1].count(name)
    cur = _current_names()
    hit = _find_occurrence(cur, name, occ)
    if hit is not None:
        return hit
    if fallback:
        fb = _CUT_FALLBACK.get(name)
        if fb is not None:
            return _find_occurrence(cur, fb, 1)
    return None


def _table_for(save_v):
    """The FULL bank order a given save version's indices were written
    against; None = indices are already current."""
    return {2: _V402_FULL, 3: _V403_FULL}.get(save_v, _V401_FULL)


def _sane_owned(owned):
    """Drop impossible eggs_owned entries: out-of-range, and TEMP lineage
    eggs (can_perm FALSE) which are never ownable however they snuck in."""
    from . import data, egg as egg_mod
    rules = data.load_egg_unlock()
    out = set()
    for i in owned:
        if not isinstance(i, int) or not (0 <= i < egg_mod.count()):
            continue
        r = rules.get(i)
        if r is not None and not r["can_perm"]:
            continue
        out.add(i)
    return sorted(out)


def _migrate_v401_save(data):
    """In-place pet-save migration across bank versions (egg indices only)."""
    v = data.get("egg_order_v")
    if v == EGG_ORDER_V:
        return
    table = _table_for(v)
    if table is not None and isinstance(data.get("egg_type"), int):
        new = _migrate_egg_index(data["egg_type"], table)
        data["egg_type"] = new if new is not None else 1
    data["egg_order_v"] = EGG_ORDER_V


def _migrate_v401_settings(d):
    """One-time owned-egg index translation + sanity pass for older settings
    files (v4 also REPAIRS v3's fallback leak: temp eggs granted as owned)."""
    if not d or d.get("egg_order_v") == EGG_ORDER_V:
        return False
    prog = d.get("progress") or {}
    owned = prog.get("eggs_owned")
    if owned:
        table = _table_for(d.get("egg_order_v"))
        if table is not None:
            owned = [n for n in (_migrate_egg_index(i, table, fallback=False)
                                 for i in owned) if n is not None]
        prog["eggs_owned"] = _sane_owned(owned)
    d["egg_order_v"] = EGG_ORDER_V
    return True


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


def ladder_award_claimed(season):
    """Has this device already granted the season's ladder award?  The server
    keeps its own claim ledger; this local one stops a double-grant when the
    claim message races a re-query (monthly ladder, 2026-07-14)."""
    return season in load_settings().get("progress", {}).get("ladder_claimed", [])


def note_ladder_award(season):
    d = load_settings()
    lst = d.setdefault("progress", {}).setdefault("ladder_claimed", [])
    if season not in lst:
        lst.append(season)
        save_settings(d)


def album_has(num):
    """Is this species (name-canonical) already in the cross-pet album?  Lets
    the evolve/hatch moment announce a genuine FIRST -- album_add() itself is
    buried in save() and records silently (sweep 2026-07-14)."""
    if num is None or num < 0:
        return True                  # sentinels are never announceable firsts
    from . import data
    num = data.canonical_num(num)
    if num in _ALBUM_SEEN:
        return True
    return num in set(load_settings().get("progress", {}).get("album", []))


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


def record_connection(peer_name):
    """A completed online link (versus bout or jogress) with another tamer --
    the DM20 connection-battle signal behind the Corona/Luna/Meicoo/DORU
    eggs.  Distinct tamers count once, like the device's friend list."""
    if peer_name:
        _note_set("connections", str(peer_name)[:24])


def mega_kills_add(n=1):
    """Lifetime Mega/Ultimate-class foes felled (gates the X egg; LINES_SPEC §7)."""
    return _note_add("mega_kills", n)


def get_blocked():
    """Muted lobby peers (names)."""
    return set(load_settings().get("blocked", []))


def set_blocked(names):
    d = load_settings()
    d["blocked"] = sorted(names)
    save_settings(d)


DM_KEEP = 50           # persisted tail per DM thread (the live cap is net.CHAT_CAP)


def get_dms():
    """Persisted lobby DM threads -> ({peer: [(from, text), ...]}, unread set).
    Conversations survive leaving the thread/lobby (Joel 2026-07-10)."""
    d = load_settings()
    dms = {p: [tuple(m[:2]) for m in v if isinstance(m, (list, tuple)) and len(m) >= 2]
           for p, v in (d.get("dms") or {}).items()}
    return dms, set(d.get("dm_unread") or [])


def save_dms(dms, unread):
    d = load_settings()
    d["dms"] = {p: [list(m) for m in v[-DM_KEEP:]] for p, v in dms.items() if v}
    d["dm_unread"] = sorted(n for n in unread if n in d["dms"])
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
    if idx is not None:
        _note_set("eggs_owned", idx)


def get_titles_owned():
    """Honor titles bought (profile-level, survives generations)."""
    return set(_prog().get("titles_owned", []))


def title_own(tid):
    _note_set("titles_owned", int(tid))


def get_title_worn():
    """The WORN honor title id (-1 = none)."""
    try:
        return int(_prog().get("title_worn", -1))
    except (TypeError, ValueError):
        return -1


def set_title_worn(tid):
    d = load_settings()
    d.setdefault("progress", {})["title_worn"] = int(tid)
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
    # the LEGACY roll (sweep 2026-07-14): every retired generation used to
    # vanish -- only this gate snapshot survived, and it was never SHOWN.
    # Bank a small headstone per life for the DigiCore LEGACY page.
    legacy = prog.setdefault("legacy", [])
    legacy.append({
        "gen": int(getattr(pet, "generation", 1)),
        "name": getattr(pet, "name", "") or "?",
        "stage": getattr(pet, "stage", "?"),
        "age": float(getattr(pet, "age_seconds", 0.0)),
        "cups": int(getattr(pet, "trophies", 0)),
        "dead": bool(getattr(pet, "dead", False)),
    })
    del legacy[:-30]                 # the book keeps the 30 most recent elders
    save_settings(d)


def prev_gen_estate():
    """The device-lifetime estate the next generation inherits (bits, the bag,
    the trophy room -- canon resetToEgg preserves them all)."""
    d = load_settings()
    last = (d.get("progress") or {}).get("last_gen") or {}
    # JSON stringifies int dict keys (the trophies_won load trap): coerce
    # them back so prelim-chain lookups keep matching
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
        "connections": len(prog.get("connections", [])),
    }


def add_pending_bug(rec):
    """Stash a bug that could not be sent (offline) to retry next launch.
    True when it is safely on disk -- the caller PROMISES the player it will
    send later, so a failed stash must not be reported as a save (swallowed-
    failure sweep 2026-07-13)."""
    import os as _os
    import json as _json
    try:
        _os.makedirs(SAVE_DIR, exist_ok=True)
        with open(_os.path.join(SAVE_DIR, "pending_bugs.jsonl"), "a", encoding="utf-8") as f:
            f.write(_json.dumps(rec) + "\n")
        return True
    except OSError:
        return False


def take_pending_bugs():
    """Return and clear the stashed bugs (a best-effort flush)."""
    import os as _os
    import json as _json
    p = _os.path.join(SAVE_DIR, "pending_bugs.jsonl")
    try:
        recs = [_json.loads(l) for l in open(p, encoding="utf-8") if l.strip()]
        _os.remove(p)
        return recs
    except (OSError, ValueError):
        return []


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
    # the album's in-process mirror must die with the files, or every species
    # raised BEFORE the erase silently never re-records in the fresh album
    # (album_add early-returns on the cached num; audit 2026-07-13)
    _ALBUM_SEEN.clear()
    return removed


def to_save_dict(pet):
    """The on-disk/cloud save payload: the flat pet plus a wall-clock stamp used
    for offline catch-up AND last-write-wins cloud merge."""
    data = asdict(pet)
    data["_saved_at"] = time.time()
    data["egg_order_v"] = EGG_ORDER_V   # marks post-.402 egg indices (migration guard)
    return data


def save(pet, path=None):
    # the .bak generation matters: a corrupt main save used to mean a silent
    # new egg -- and the next autosave then DESTROYED the old pet
    _atomic_write_json(path or SAVE_PATH, to_save_dict(pet), keep_bak=True)
    if getattr(pet, "num", -1) >= 0 and pet.stage != "Egg":
        album_add(pet.num)            # grow the cross-pet album (gates egg unlocks)


def write_save_dict(data, path=None):
    """Atomically write a raw save dict (e.g. one pulled from the cloud) to disk.
    keep_bak: a cloud pull is the ONE writer that replaces the save with bytes
    this device never played -- it must not also burn the local backup."""
    _atomic_write_json(path or SAVE_PATH, data, keep_bak=True)


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
    _migrate_v401_save(data)                     # egg-bank reorder + ver6 cut
    saved_at = data.pop("_saved_at", None)
    # JSON stringifies int dict keys: trophies_won comes back str-keyed,
    # silently breaking cup prelim chains (audit 2026-07).  Coerce on load.
    for k in ("trophies_won",):
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
    msg = ""
    # the Great Simplification (2026-07-15): a pre-rebuild save carries the
    # retired habitat economy -- refund every PURCHASED home at full price
    # (the starter pair 0/2 came free) and start on the default scene
    from . import backgrounds as _bgs
    if getattr(pet, "bg_current", None) not in _bgs.CATALOG:
        pet.bg_current = _bgs.DEFAULT      # an off-catalog pick (retired scene) resets
    pet.bg_owned = [k for k in getattr(pet, "bg_owned", []) if k in _bgs.CATALOG]
    if "bg_owned" not in data and isinstance(data.get("habitats"), list):
        from . import data as _data
        habs = _data.load_habitats()
        refund = sum((habs.get(h) or {}).get("price", 0)
                     for h in data["habitats"] if h not in (0, 2))
        if refund:
            pet.bits = int(getattr(pet, "bits", 0)) + refund
            msg = f"(habitats retired — {refund} bits refunded)"
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
        elif not getattr(pet, "line_id", ""):
            # pre-line save: a consistent pet with no line_id would ride the
            # corpus engine forever; re-anchor by membership (truly off-chart
            # forms keep '' as before)
            from . import lines as _lines
            _lines.adopt_line(pet)
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
    mood_drop = min(50, mins * 2)
    pet.mood = _clamp(pet.mood - mood_drop, -300, 300)
    drop = min(pet.hunger, int(mins // 5))
    pet.hunger -= drop
    starved = mins > 10 and pet.hunger == 0
    if starved:
        pet.care_mistakes += 1
    new_poop = min(4, pet.poop + int(mins // 8))
    poops = new_poop - pet.poop
    while len(pet.poop_sizes) < new_poop:            # keep poop == len(poop_sizes)
        pet.poop_sizes.append(pet._poop_size() if hasattr(pet, "_poop_size") else 2)
    pet.poop = new_poop
    if mins < 1:
        return ""
    # ITEMIZE the return (sweep 2026-07-14): this routine knows exactly what
    # happened while you were gone, and used to throw it away for one generic
    # line -- the player just found a changed pet.  Say only what WAS applied.
    away = f"{int(mins)}m" if mins < 60 else f"{int(mins / 60)}h"
    parts = []
    if starved:
        parts.append("went hungry (+1 care mistake)")
    elif drop:
        parts.append("got hungrier")
    if poops:
        parts.append(f"{poops} poop{'s' if poops > 1 else ''} piled up")
    if mood_drop >= 20:
        parts.append("mood slipped")
    name = getattr(pet, "name", "") or "your pet"
    if not parts:
        return f"Welcome back! ({away} away) {name} missed you."
    return f"Welcome back! ({away} away) While you were gone: " + ", ".join(parts) + "."


def quarantine_save(path):
    """Copy an unreadable save aside (save.corrupt.<ts>.json) before a new game
    rotates over it, so the pet stays recoverable by hand.  Returns the
    quarantine path, or None when the disk refused."""
    import shutil
    try:
        dst = os.path.join(os.path.dirname(path) or ".",
                           "save.corrupt.%s.json" % time.strftime("%Y%m%d-%H%M%S"))
        shutil.copyfile(path, dst)
        return dst
    except OSError:
        return None


def load(path=None, catch_up=True):
    """Return (pet, message); pet is None if no valid save exists.  A corrupt
    main save falls back to the .bak rotated by save() -- at most one autosave
    (~10s) behind, instead of a silent new egg.  When BOTH generations are
    unreadable, the damaged file is quarantined and the message SAYS SO -- a
    corrupt save must never be indistinguishable from a first launch
    (professionalism sweep 2026-07-14)."""
    path = path or SAVE_PATH
    broken = None                    # first candidate that existed but wouldn't load
    for candidate in (path, path + ".bak"):
        if not os.path.exists(candidate):
            continue
        try:
            data = json.load(open(candidate))
        except (ValueError, OSError):
            broken = broken or candidate
            continue
        pet, msg = pet_from_save(data, catch_up=catch_up)
        if pet is None:
            broken = broken or candidate
            continue
        if candidate != path:
            msg = (msg + "  " if msg else "") + "(recovered from the backup save)"
        return pet, msg
    if broken is None:
        return None, ""              # a true first launch: nothing on disk
    kept = quarantine_save(broken)
    if kept:
        return None, ("Your old save couldn't be read — the damaged file was kept as "
                      f"{os.path.basename(kept)}. Starting fresh.")
    return None, "Your old save couldn't be read. Starting fresh."


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
