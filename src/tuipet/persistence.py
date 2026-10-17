"""Save/load the pet to disk.

The pet is a flat dataclass, so it serialises straight to JSON.

A CLOSED GAME IS A STOPPED CLOCK.  Nothing at all happens while you are away:
no aging, no growth, no incubation, no hunger, no poop, no sleep.  You reopen
to exactly the pet you left.  This replaces the bounded "while you were away"
catch-up that used to run here (Joel 2026-07-22: "do we have an away system?
like, where the mon still grows, even when its shut off? if so, we gotta
remove it" -> total stasis).  It is the same law as the canon menu freeze the
lobby carve-out was removed for the same day: time passes only while you are
actually playing.
"""
from __future__ import annotations
import json
import os
import time
from dataclasses import MISSING, asdict, fields

from .roadmigrate import ROAD_ORDER_V, migrate_road
from .pet import Pet
from .petbase import (FRESH_OBEDIENCE, IN_TRAINING_OBEDIENCE,
                      ROOKIE_OBED_DEFAULT, MAX_DNA_INVENTORY, MAX_DNA_WAGER)

# the IO plumbing + the egg-bank migration live in their own modules
# (tier-4 split 2026-07-17); the old names keep resolving from here
from .eggmigrate import (  # noqa: F401
    EGG_ORDER_V, _CLASSIC49, _CUT_FALLBACK, _V401_FULL, _V402_FULL,
    _V403_FULL, _V404_FULL, _current_names, _find_occurrence,
    _migrate_egg_index, _migrate_v401_save, _migrate_v401_settings,
    _sane_owned, _table_for)
from .persistio import (  # noqa: F401
    SAVE_DIR, SAVE_PATH, SETTINGS_PATH, _LOCK_NAME,
    _atomic_write_json, _can_use, _pick_save_dir, acquire_instance_lock,
    release_instance_lock, write_crash_log)
from . import persistio as _persistio


def __getattr__(name):
    """`save_failed` is MUTABLE state owned by persistio's writer -- a
    static re-export would freeze it at import; delegate reads instead."""
    if name == "save_failed":
        return _persistio.save_failed
    raise AttributeError(name)


def load_settings(path=None):
    """App-level prefs that outlive any single pet (e.g. the lobby account).
    Falls back to the .bak rotated by save_settings -- settings hold the album,
    lifetime wins, owned eggs and the banked Digimemory; one corrupt write must
    not erase a save file's whole history (audit 2026-07)."""
    path = path or SETTINGS_PATH
    for candidate in (path, path + ".bak"):
        try:
            d = json.load(open(candidate, encoding="utf-8"))
        except (OSError, ValueError):
            continue
        # sync audit 2026-10-14: JSON validity alone cannot make a profile usable.
        if not isinstance(d, dict) or any(
                k in d and d[k] is not None and not isinstance(d[k], dict)
                for k in ("progress", "account")):
            continue
        eggs_changed = _migrate_v401_settings(d)
        _bind_progress(d)
        buckets = d["progress_by_account"]
        buckets[d[_OWNER]] = d["progress"]
        changed = any(isinstance(p, dict) and p.get("road_order_v", 0) < ROAD_ORDER_V
                      for p in buckets.values())
        for key, prog in list(buckets.items()):
            if isinstance(prog, dict):
                buckets[key] = migrate_road(prog)
        d["progress"] = buckets[d[_OWNER]]
        if changed or eggs_changed:
            save_settings(d, path)
        return d
    return {}


# ---- PER-ACCOUNT HISTORY (saves call #28 = A, Joel 2026-10-15) --------------
# The earned history ("progress": album, wins, eggs, titles, maps...) used to
# be ONE per device, so every account signed in here merged into it.  It is
# kept per ACCOUNT now: settings hold `progress_by_account` {account: progress}
# and `progress` is the signed-in account's bucket, swapped in on load and
# filed back on save.  A pre-split file's history becomes the signed-in
# account's (nothing is lost or re-sorted); history earned SIGNED OUT goes
# with the first account signed into.
_OWNER = "_progress_owner"


def _account_key(d):
    return ((d.get("account") or {}).get("name") or "").strip().lower()


def _bind_progress(d):
    buckets = d.get("progress_by_account")
    if not isinstance(buckets, dict):
        buckets = {}
    key = _account_key(d)
    if "progress_by_account" not in d:          # a pre-split file: adopt it whole
        buckets[key] = d.get("progress") or {}
    elif key not in buckets and key and buckets.get(""):
        buckets[key] = buckets.pop("")          # signed-out play joins the first account
    d["progress_by_account"] = buckets
    d["progress"] = buckets.get(key) or {}
    d[_OWNER] = key


def _file_progress(d):
    """save_settings: put the live bucket back under the account it was
    LOADED for (set_account may have changed the name since)."""
    if _OWNER not in d and "progress_by_account" not in d:
        _bind_progress(d)                       # a dict built without load_settings
    owner = d.pop(_OWNER, _account_key(d))
    buckets = d.get("progress_by_account")
    if not isinstance(buckets, dict):
        buckets = {}
    buckets[owner] = d.get("progress") or {}
    d["progress_by_account"] = buckets
    # `progress` stays on disk too, the signed-in account's bucket: an
    # older build (a rollback) reads only that key
    d["progress"] = buckets.get(_account_key(d)) or {}


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
    d.setdefault("progress", {}).setdefault("road_order_v", ROAD_ORDER_V)
    out = dict(d)                               # the caller's dict stays bound
    _file_progress(out)
    _atomic_write_json(path or SETTINGS_PATH, out, keep_bak=True)


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


def raid_paid(raid_id):
    """Has this profile already APPLIED raid `raid_id`'s reward?  The server
    re-sends an unacknowledged payout (battle call #23 = A, 2026-10-15);
    this ledger keeps a re-send from paying twice."""
    return str(raid_id) in load_settings().get("progress", {}).get("raids_paid", [])


def note_raid_paid(raid_id):
    d = load_settings()
    lst = d.setdefault("progress", {}).setdefault("raids_paid", [])
    if str(raid_id) not in lst:
        lst.append(str(raid_id))
        del lst[:-50]                        # the newest fifty are plenty
        save_settings(d)


def note_ladder_award(season):
    d = load_settings()
    lst = d.setdefault("progress", {}).setdefault("ladder_claimed", [])
    if season not in lst:
        lst.append(season)
        save_settings(d)


def eggs_announced():
    """Egg indices whose NEW-DIGITAMA flash already fired -- or None when the
    ledger was never seeded (a pre-announce save: the caller seeds silently
    instead of flooding years of old earnings as 'new')."""
    return _prog().get("eggs_announced")


def note_eggs_announced(idxs):
    d = load_settings()
    lst = d.setdefault("progress", {}).setdefault("eggs_announced", [])
    for i in idxs:
        if i not in lst:
            lst.append(int(i))
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


def armor_add(n=1):
    """Lifetime armor (Digimental) evolutions performed -- the crest-wave
    Digimental shop gate (2026-07-17)."""
    return _note_add("armor_evos", n)


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
    """Egg indices permanently earned (a met can_perm unlock, stuck forever)."""
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


def map_cleared_add(map_index):
    """One adventure MAP's boss cleared (0-based index into the 30-map world).
    `maps` holds whole AREAS (6 maps each); a map-specific egg gate needs the
    map itself (Volcanic Beat egg = the Volcano road, 2026-10-14)."""
    _note_set("maps_cleared", int(map_index))


def wild_beaten_add(map_index, num):
    """One species beaten on one adventure map ("MAP:DEX", 0-based map index
    + the foe's dex num) -- the card eggs' "beat the partner as a WILD on
    that road" gate (Joel 2026-10-15).  Bosses land here too; harmless."""
    _note_set("wilds_beaten", f"{int(map_index)}:{int(num)}")


def zone_best_set(zone_index, score):
    """Record an adventure run's SCORE against the zone's standing best
    (arcade arc, 2026-07-21).  Returns True when it's a NEW best -- the
    summary card's brag."""
    d = load_settings()
    prog = d.setdefault("progress", {})
    bests = prog.setdefault("map_bests", {})   # per MAP (the 2026-10-14 world; old zone bests retired)
    k = str(int(zone_index))
    if int(score) > int(bests.get(k, 0)):
        bests[k] = int(score)
        save_settings(d)
        return True
    return False


def zone_bests():
    """zone_index -> best run score (str-keyed in storage, int-keyed here)."""
    return {int(k): int(v)
            for k, v in (_prog().get("map_bests", {}) or {}).items()}


def raid_add():
    """One community raid boss this save contributed to FELL (counted at the
    claim, when the relay confirms defeated=True).  The count re-gates the
    old MapComplete egg rows (BASIC VPET 2026-07-16)."""
    d = load_settings()
    prog = d.setdefault("progress", {})
    prog["raids"] = int(prog.get("raids", 0)) + 1
    save_settings(d)


def tourney_add(trophy_id):
    _note_set("tourneys", int(trophy_id))


def festival_add(name):
    """Celebrated a festival -- conquered an adventure zone on a holiday day.
    A set of the festival NAMES seen (distinct festivals only, so same-day
    conquers count once); gates the seasonal egg (Draco/Examon, the grand
    festival prize -- festivals were reward-hollow before, 2026-07-20)."""
    _note_set("festivals", str(name))


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
        # the BANKED DNA is device-lifetime too (DNA polish 2026-07-17):
        # it is bought with bits + the mash minigame, so wiping it at
        # rollover made late-life banking worthless.  The CHARGED
        # distribution (dna_applied) is the pet's own biology and dies
        # with it, exactly as before.
        "dna_owned": dict(getattr(pet, "dna_owned", {}) or {}),
        # egg audit 2026-10-14: profile daily purchases outlive a partner.
        "town_bought": dict(getattr(pet, "town_bought", {}) or {}),
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
        "cups": int(getattr(pet, "trophies", 0)),        # the lineage total
        # THIS life's own cups (eggs call #31 = A, Joel 2026-10-15)
        "cups_life": max(0, int(getattr(pet, "trophies", 0))
                         - int(getattr(pet, "trophies_at_birth", 0) or 0)),
        "dead": bool(getattr(pet, "dead", False)),
        # the HALL OF MEMORY fields (Joel 2026-07-26 "build the hall of
        # memory"): the individual, not just the count -- its form for the
        # portrait, what took it, and its fight record.  Headstones from
        # before this date miss them; the hall shows the grave and says
        # only what it knows.
        "num": int(getattr(pet, "num", 0)),
        "cause": getattr(pet, "death_cause", "") or "",
        "wins": int(getattr(pet, "wins", 0)),
        "battles": int(getattr(pet, "battles", 0)),
    })
    del legacy[:-30]                 # the book keeps the 30 most recent elders
    save_settings(d)



def _heal_bag(inv):
    """The bag heal, both eras in one pass: shed the dead staple props
    (strict-DSprite 2026-07-17) and map the retired catalog's keys onto
    their TUIPET heirs 1:1 (shop.LEGACY_KEYS; catalog turnover 2026-07-18
    -- nobody loses goods)."""
    from . import shop
    # "bandage" is a dead key AGAIN (Joel 2026-07-26, on seeing the
    # expansion's 10b pocket med: "cut it out, i think its supposed to
    # just be used for the animations for heal") -- the wrap belongs to
    # the H heal's Bandaging show, not to a bag row.  It was live for
    # about an hour of 0.5.283/284, so this heals out at most a couple of
    # 10b purchases (the R3 precedent).  The raw-icon keys are ancient-
    # save cruft; the surviving expansion items wear snake_case keys
    # (futon / toilet / port_potty).
    for dead in ("i:80", "i:81", "i:82", "i:83", "bandage"):
        inv.pop(dead, None)
    # ...and the 2026-07-27 refactor's RETIRED ledger rides the same door:
    # every cut key converts 1:1 to its named heir, same as the 07-18
    # turnover -- nobody loses goods
    for old, new in {**shop.LEGACY_KEYS, **shop.RETIRED}.items():
        n = inv.pop(old, 0)
        if n:
            inv[new] = inv.get(new, 0) + n
    return inv

def _dna_counts(value, bank=False):
    """Normalize legacy missing slots; reject malformed counts without truncation."""
    from . import data
    if value is None:
        value = {}
    if not isinstance(value, dict):
        raise ValueError("invalid DNA dictionary")
    out = {f: 0 for f in data.DNA_FIELDS}
    for field, count in value.items():
        # DNA audit 2026-10-14: shape checks alone let poisoned banks reach UI/cloud.
        if (field not in out or isinstance(count, bool)
                or not isinstance(count, (int, float)) or count < 0
                or (bank and count > MAX_DNA_INVENTORY)):
            raise ValueError("invalid DNA count")
        try:
            whole = int(count)
        except (ValueError, OverflowError):
            raise ValueError("invalid DNA count") from None
        if whole != count:
            raise ValueError("invalid DNA count")
        out[field] = whole
    return out


def _dna_save_fields(value):
    """Validate the DNA portion independently of the rest of a save."""
    out = {key: _dna_counts(value.get(key), bank=key == "dna_owned")
           for key in ("dna_owned", "dna_applied")}
    pending = value.get("dna_wager_pending")
    if pending is None:
        pending = 0
    if (isinstance(pending, bool) or not isinstance(pending, (int, float))
            or not 0 <= pending <= MAX_DNA_WAGER or int(pending) != pending):
        raise ValueError("invalid DNA wager")
    out["dna_wager_pending"] = int(pending)
    return out


def prev_gen_estate():
    """The device-lifetime estate the next generation inherits (bits, the bag,
    the trophy room -- canon resetToEgg preserves them all)."""
    d = load_settings()
    last = (d.get("progress") or {}).get("last_gen") or {}
    # JSON stringifies int dict keys (the trophies_won load trap): coerce
    # them back so prelim-chain lookups keep matching
    tw = {int(k) if str(k).lstrip("-").isdigit() else k: v
          for k, v in (last.get("trophies_won") or {}).items()}
    inv = _heal_bag(dict(last.get("inventory") or {}))
    # digimemory items never ride the estate bag (2026-07-24): the inherited
    # PAYLOAD travels via the bank channel (take_digimemory -> _grant re-adds
    # exactly one chip), and a WILD chip's trace is within-life loot that
    # fades with its finder.  Carrying the item without its payload would
    # deal the heir a dud -- the very thing the no-traps rule forbids.
    inv.pop("digimemory", None)
    try:
        bank = _dna_counts(last.get("dna_owned"), bank=True)
    except ValueError:
        # DNA audit 2026-10-14: archive the malformed estate, keep every valid slot.
        quarantine_save(SETTINGS_PATH)
        bank = _dna_counts(None)
        raw = last.get("dna_owned")
        if isinstance(raw, dict):
            for field, count in raw.items():
                try:
                    slot = _dna_counts({field: count}, bank=True)
                except ValueError:
                    continue
                bank[field] = slot[field]
    return {"bits": int(last.get("bits", 0)),
            "inventory": inv,
            "trophies": int(last.get("trophies", 0)),
            "trophies_won": tw,
            # egg audit 2026-10-14: old estates without a ledger stay compatible.
            "town_bought": dict(last.get("town_bought") or {}),
            "dna_owned": bank}


_FX_SEEN = (None, None)          # (settings path, set) -- keyed by path so a
#                                  redirected HOME never reads a stale cache


def _fx_seen_set():
    global _FX_SEEN
    if _FX_SEEN[0] != SETTINGS_PATH:
        _FX_SEEN = (SETTINGS_PATH,
                    set((load_settings().get("progress") or {}).get("fx_seen") or []))
    return _FX_SEEN[1]


def fx_seen(key):
    """Has this home show played to its end before (any life)?  The
    animation audit's first-time/repeat split (2026-10-14).  Cached: it is
    read at every show start."""
    return key in _fx_seen_set()


def mark_fx_seen(key):
    seen = _fx_seen_set()
    if key in seen:
        return
    seen.add(key)
    d = load_settings()
    d.setdefault("progress", {})["fx_seen"] = sorted(seen)
    save_settings(d)


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


def gcell_fragment_waiting():
    """A G-Cell Fragment left at a G-Erosion kaiju's grave, not yet hatched
    into a Godzilla Egg (app._death_ceremony / app._hatch_new)."""
    return bool(_prog().get("gcell_frag"))


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
        "road_order_v": ROAD_ORDER_V,
        "maps": set(prog.get("maps", [])),
        "maps_cleared": set(prog.get("maps_cleared", [])),
        "wilds_beaten": set(prog.get("wilds_beaten", [])),
        "raids": int(prog.get("raids", 0)),
        "tourneys": set(prog.get("tourneys", [])),
        "last_field": last.get("field", "None"),
        "last_attr": last.get("attribute", "None"),
        "last_obed": int(last.get("obedience", 0)),
        "last_xanti": bool(last.get("xanti", False)),
        "connections": len(prog.get("connections", [])),
        "festivals": set(prog.get("festivals", [])),
        "armor_evos": int(prog.get("armor_evos", 0)),
    }


# --- the profile block that rides WITH the pet across devices ---------------
# GoingUnder, 2026-08-11: "save import device to device dosent import eggs
# progress".  The cartridge moves save.json and nothing else, but EVERY
# cross-generation milestone the egg gates read -- eggs_owned, the album,
# lifetime wins, max gen/stage -- lives in settings.json, which never crossed
# the wire.  A taken pet therefore landed on the new device with its whole
# egg-unlock history back at zero.
#
# Only MONOTONIC earned history travels, and it MERGES rather than replaces:
# union for the earned sets, max for the counters.  That is the one merge rule
# which provably cannot cost a player something they already earned on either
# device -- and a cartridge take must never be a way to LOSE progress.
#
# The one-slot live values (last_gen, digimemory, bonus_seed, title_worn) are
# deliberately NOT here: they are current state, not earned history, and no
# merge of them is lose-nothing.  Deciding those is a design call, not this fix.
_PROG_SETS = ("album", "eggs_owned", "titles_owned", "connections", "maps", "maps_cleared",
              "wilds_beaten", "raids_paid",
              "tourneys", "festivals", "eggs_announced", "ladder_claimed",
              "shop_unlocks", "holiday_notice_seen")
_PROG_MAXES = ("wins", "mega_kills", "armor_evos", "raids",
               "max_gen", "max_stage")


def progress_for_sync():
    """The travelling slice of settings['progress'] (see the block above)."""
    prog = _prog()
    out = {}
    for k in _PROG_SETS:
        v = prog.get(k)
        if v:
            out[k] = sorted(set(v))
    for k in _PROG_MAXES:
        try:
            v = int(prog.get(k, 0))
        except (TypeError, ValueError):
            continue
        if v:
            out[k] = v
    if prog.get("xanti_ever"):
        out["xanti_ever"] = True
    bests = prog.get("map_bests") or {}
    if isinstance(bests, dict) and bests:
        out["map_bests"] = dict(bests)
    if out:
        out["road_order_v"] = ROAD_ORDER_V
    return out


def merge_progress(incoming):
    """Fold a synced progress block into this device's settings, keeping the
    BETTER of the two everywhere.  No-op on junk -- a malformed cloud payload
    must never cost the local profile its history."""
    if not isinstance(incoming, dict) or not incoming:
        return False
    incoming = migrate_road(incoming)
    d = load_settings()
    prog = d.setdefault("progress", {})
    changed = False
    for k in _PROG_SETS:
        v = incoming.get(k)
        if not isinstance(v, list) or not v:
            continue
        # sync audit 2026-10-14: junk in one earned set must not abort the pull.
        try:
            merged = sorted(set(prog.get(k) or []) | set(v))
        except (TypeError, ValueError):
            continue
        if merged != (prog.get(k) or []):
            prog[k] = merged
            changed = True
    for k in _PROG_MAXES:
        try:
            v = int(incoming.get(k, 0))
        except (TypeError, ValueError):
            continue
        try:
            cur = int(prog.get(k, 0))
        except (TypeError, ValueError):
            cur = 0
        if v > cur:
            prog[k] = v
            changed = True
    if incoming.get("xanti_ever") and not prog.get("xanti_ever"):
        prog["xanti_ever"] = True
        changed = True
    # map_bests: the 2026-10-14 world's per-MAP scores (an old cloud's
    # zone_bests named the retired 26 zones and is ignored)
    bests = incoming.get("map_bests")
    if isinstance(bests, dict):
        cur = prog.setdefault("map_bests", {})
        for zk, zv in bests.items():
            try:
                zv = int(zv)
            except (TypeError, ValueError):
                continue
            try:
                have = int(cur.get(str(zk), 0))
            except (TypeError, ValueError):
                have = 0
            if zv > have:
                cur[str(zk)] = zv
                changed = True
    if changed:
        save_settings(d)
    return changed


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


def peek_pending_bugs():
    """Read the stashed bugs WITHOUT deleting them (bug audit 2026-07-19:
    the old take-then-send cleared the stash up front, so quitting mid-
    flush lost every unsent report -- the round-5 PM-flush lesson).  The
    flush rewrites the survivors when it is done."""
    import os as _os
    import json as _json
    p = _os.path.join(SAVE_DIR, "pending_bugs.jsonl")
    try:
        return [_json.loads(l) for l in open(p, encoding="utf-8") if l.strip()]
    except (OSError, ValueError):
        return []


def write_pending_bugs(recs):
    """Atomically rewrite the stash to exactly `recs` ([] removes the file).
    True when it landed on disk."""
    import os as _os
    import json as _json
    p = _os.path.join(SAVE_DIR, "pending_bugs.jsonl")
    try:
        if not recs:
            if _os.path.exists(p):
                _os.remove(p)
            return True
        tmp = p + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            for r in recs:
                f.write(_json.dumps(r) + "\n")
        _os.replace(tmp, p)
        return True
    except OSError:
        return False


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


# ---- the cloud CARTRIDGE (2026-07-29) ---------------------------------------
# One pet, checked out to ONE device at a time.  The GPD incident: two
# devices both held playable copies, "newest save wins" let the stale fork
# out-stamp the real pet, and the cloud regressed twice in one night.  The
# server now tracks a HOLDER per account; these are the client's identity
# and its cached answer to "am I the holder?".

RESCUE_KEEP = 5


def device_id():
    """This install's stable identity, minted once into settings.  The
    cartridge's holder is a DEVICE, not a login -- the same account on two
    machines must be tellable apart."""
    d = load_settings()
    did = d.get("device_id")
    if not did:
        import uuid
        did = uuid.uuid4().hex[:16]
        d["device_id"] = did
        save_settings(d)
    return did


def device_label():
    """A human name for this device, for the other device's take-question
    ('Your pet is on phone.')."""
    from . import hostinfo
    import platform as _plat
    if hostinfo.is_termux():
        return "phone"
    if hostinfo.is_ios():
        return "iPhone"
    return ((_plat.node() or "").split(".")[0] or "PC")[:16]


def holder_cache():
    """The last successful cloud contact's verdict: True = we hold the pet,
    False = another device does, None = never learned (pre-cartridge saves,
    or no contact yet).  Read OFFLINE to decide whether this device may
    play: a cached non-holder stays a spectator until it can take."""
    return load_settings().get("cloud_holder")


def set_holder_cache(val):
    d = load_settings()
    if d.get("cloud_holder") is not bool(val):
        d["cloud_holder"] = bool(val)
        save_settings(d)


def rescue_copy(path=None):
    """Snapshot the CURRENT local save somewhere the autosave can never roll
    over, and return its filename ('' if there was nothing to copy).

    save.json.bak is ONE generation deep and every write rotates it, so a
    cloud pull that replaces the pet is undoable for about ten seconds --
    the next autosave turns the rescued pet into the pulled one (the gen-10
    BlitzGreymon incident, 2026-07-27).  A pull (or a cartridge take) is
    the one write that replaces bytes this device never played; it gets a
    copy that STAYS.  (Shipped 0.5.290, cut by 0.5.294's plain-and-simple
    revert, restored 2026-07-29 after the GPD fork stomped the cloud.)"""
    import glob as _glob
    src = path or SAVE_PATH
    try:
        with open(src, encoding="utf-8") as fh:
            data = json.load(fh)
    except (ValueError, OSError):
        return ""                        # no readable save: nothing to rescue
    stamp = time.strftime("%Y%m%d-%H%M%S", time.gmtime())
    name = f"save.rescue.{stamp}.json"
    _atomic_write_json(os.path.join(SAVE_DIR, name), data)
    old = sorted(_glob.glob(os.path.join(SAVE_DIR, "save.rescue.*.json")))
    for p in old[:-RESCUE_KEEP]:         # keep the newest few, drop the rest
        try:
            os.remove(p)
        except OSError:
            pass
    return name


def erase_all():
    """Erase the WHOLE local state: pet save (+bak), settings (progress,
    account, digimemory, +bak), sound + theme prefs -- and every other file
    carrying the erased pet's data: quarantined save.corrupt.* copies, the
    crash log and the stashed bug reports (persistence audit 2026-07-18:
    'for keeps' left the old pet recoverable on disk).  The cloud copy stays
    with the account server-side; with the login gone, nothing pulls it.
    Options-menu 'Erase all data' (Joel 2026-07-04)."""
    import glob as _glob
    removed = []
    names = ["save.json", "save.json.bak", "settings.json", "settings.json.bak",
             "sound.txt", "theme.txt", "crash.log", "pending_bugs.jsonl",
             "volume.txt"]   # never in this list before the 2026-07-19 shape sweep
    names += [os.path.basename(p) for p in
              _glob.glob(os.path.join(SAVE_DIR, "save.corrupt.*.json"))]
    # sync audit 2026-10-14: rescue copies and interrupted writes contain the pet too.
    names += ["save.json.tmp", "settings.json.tmp", "pending_bugs.jsonl.tmp"]
    names += [os.path.basename(p) for p in
              _glob.glob(os.path.join(SAVE_DIR, "save.rescue.*.json"))]
    for fn in names:
        p = os.path.join(SAVE_DIR, fn)
        try:
            os.remove(p)
            removed.append(fn)
        except OSError:
            pass
    import shutil as _sh
    try:
        _sh.rmtree(os.path.join(SAVE_DIR, "sndcache"))   # the scaled-wav cache:
        removed.append("sndcache/")                      # rebuildable, but "for
    except OSError:                                      # keeps" is for keeps
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
    data["road_order_v"] = ROAD_ORDER_V
    data["egg_order_v"] = EGG_ORDER_V   # marks post-.402 egg indices (migration guard)
    # the account's earned history rides along, or a cartridge take lands the
    # pet on a device with no egg progress at all (GoingUnder 2026-08-11).
    # pet_from_save drops every key that isn't a Pet field, so an older client
    # pulling this save simply ignores it -- no server change, no format break.
    prog = progress_for_sync()
    # Trophy history repairs old split writes and retains credit if projecting
    # the committed cup journal into settings is temporarily unavailable.
    won = getattr(pet, "trophies_won", None) or {}
    if won:
        prog["tourneys"] = sorted(set(prog.get("tourneys", [])) | {
            int(tid) for tid in won if str(tid).isdigit()})
    if prog:
        data["progress"] = prog
    return data


def cup_checkpoint(pet, trophy_id=None):
    """Commit purse, locks and egg credit in one replace before projecting settings.

    The travelling save is the journal: load/sync already set-merges its progress,
    so interruption before the settings projection is repaired on reload.
    """
    payload = to_save_dict(pet)
    if trophy_id is not None:
        prog = payload.setdefault("progress", {})
        prog["tourneys"] = sorted(set(prog.get("tourneys", [])) | {int(trophy_id)})
    _atomic_write_json(SAVE_PATH, payload, keep_bak=True, strict=True)
    if trophy_id is not None:
        merge_progress(payload.get("progress"))


def save(pet, path=None):
    # the .bak generation matters: a corrupt main save used to mean a silent
    # new egg -- and the next autosave then DESTROYED the old pet
    _atomic_write_json(path or SAVE_PATH, to_save_dict(pet), keep_bak=True)
    if getattr(pet, "num", -1) >= 0 and pet.stage != "Egg":
        album_add(pet.num)            # grow the cross-pet album (gates egg unlocks)


def write_save_dict(data, path=None):
    """Atomically write a raw save dict (e.g. one pulled from the cloud) to disk.
    keep_bak: a cloud pull is the ONE writer that replaces the save with bytes
    this device never played -- it must not also burn the local backup.

    This is the ONE funnel every cloud install goes through (the boot pull,
    the take, and both account-switch paths), so the profile merge lives HERE
    rather than at four call sites one of them would eventually forget."""
    if isinstance(data, dict):
        merge_progress(data.get("progress"))
    _atomic_write_json(path or SAVE_PATH, data, keep_bak=True)


def local_saved_at(path=None):
    """The _saved_at of the on-disk save, or 0.0 if there's no readable save."""
    path = path or SAVE_PATH
    try:
        return float(json.load(open(path, encoding="utf-8")).get("_saved_at") or 0.0)
    # sync audit 2026-10-14: a JSON array is unreadable save data, not a boot crash.
    except (ValueError, OSError, TypeError, AttributeError):
        return 0.0


def pet_from_save(data, strict=False):
    """Build (pet, message) from a save dict (disk or cloud). Returns (None, '')
    on malformed data.

    NOTHING is applied for time spent away: a closed game is a STOPPED clock
    (Joel 2026-07-22, "we gotta remove it").  The bounded offline catch-up
    that used to run here -- age, growth, hunger, poop, sleep -- is gone with
    the `catch_up` flag that gated it; see the module header.

    strict=True (the cloud probe) REJECTS foreign-format saves outright --
    a save whose name/stage disagree with its dex was written by a different
    tuipet (the 2026-07-04 incident: an outdated client pushed a rebuild-era
    save with stage 'Child' and an empty name; the probe let it clobber the
    local pet).  strict=False (the local load) REPAIRS instead: the pet is
    re-derived from its dex and re-bound to its line, so a corrupted file
    becomes a playable pet rather than a silent fresh-egg wipe."""
    if not isinstance(data, dict):
        return None, ""
    data = migrate_road(data)                    # daily ledgers follow their scenes
    try:
        data.update(_dna_save_fields(data))
    except (ValueError, OverflowError):
        return None, ""
    _migrate_v401_save(data)                     # egg-bank reorder + ver6 cut
    # egg_type must be an INT: the 2026-07-18 'guide' incident wrote the
    # carousel's sentinel string into a save (the crash handler then saved
    # the poisoned pet, and every launch died in the egg renderer).  A
    # non-int heals to egg 0 -- a classic Botamon egg beats a dead app.
    if not isinstance(data.get("egg_type"), int):
        try:
            data["egg_type"] = int(data.get("egg_type"))
        except (TypeError, ValueError):
            data["egg_type"] = 0
    # still POPPED (it is not a Pet field), but no longer READ: the elapsed
    # time it stamped drove the offline catch-up, removed 2026-07-22.  The
    # stamp itself stays on disk -- cloudsync's local_saved_at() reads it to
    # decide which SAVE is newer, which is a sync question, not a sim one.
    data.pop("_saved_at", None)
    # JSON stringifies int dict keys: trophies_won comes back str-keyed,
    # silently breaking cup prelim chains (audit 2026-07; habitat_record
    # left with the habitat system).  Coerce them back on every load.
    for k in ("trophies_won",):
        v = data.get(k)
        if isinstance(v, dict):
            data[k] = {int(kk) if str(kk).lstrip("-").isdigit() else kk: vv
                       for kk, vv in v.items()}
    # _lights_t serializes float("-inf") as Infinity -- json emits it fine, but
    # guard against a stringified copy from older tooling
    if isinstance(data.get("_lights_t"), str):
        data["_lights_t"] = float("-inf")
    # the bag heal: dead staple props shed + retired catalog keys mapped to
    # their TUIPET heirs (catalog turnover 2026-07-18)
    if isinstance(data.get("inventory"), dict):
        _heal_bag(data["inventory"])
    # THE TYPE GATE, whole-roster edition (live-play audit 2026-07-25): the
    # 13-field wrong-type list missed ~20 fields that crashed tick() or the
    # first render, and two pre-construction migrations (the manners heal's
    # float(), the wager settle's compare) raised on strings BEFORE any
    # check ran -- so load()'s promised .bak/quarantine fallback never got
    # the chance.  Every save value must match its dataclass default's
    # shape (numbers for numbers, dict for dict, ...); one generic sweep
    # over fields(Pet), no list to forget -- a defense is only as good as
    # its worst consumer (visual audit 2026-07-25).  Values a heal above
    # already coerced (egg_type, _lights_t, trophies_won keys) arrive here
    # healed; anything else malformed rejects into the fallback chain.
    for f in fields(Pet):
        if f.name not in data or data[f.name] is None:
            # None is TOLERATED, not rejected: the foreign-save repair
            # contract (the 2026-07-04 'Child' incident) loads real saves
            # carrying line_id: None and heals them downstream -- the gate
            # judges wrong TYPES, absence-shaped values pass through
            continue
        proto = (f.default if f.default is not MISSING
                 else f.default_factory() if f.default_factory is not MISSING
                 else 0)                    # `num` is the one default-less field
        if isinstance(proto, bool):
            want = (bool, int)
        elif isinstance(proto, (int, float)):
            want = (int, float)
        else:
            want = type(proto)
        if not isinstance(data[f.name], want):
            return None, ""
    # THE MANNERS HEAL, once per save (D1/P3, 2026-07-23).  _set_obedience
    # was a NO-OP for the whole BASIC VPET era, so every pet on disk sits
    # at the dataclass default 0 -- "worst-raised pet alive" through no
    # fault of its tamer.  Seed those saves to the stage's canon starting
    # manners the first time they load under the live meter.  The marker
    # makes it ONCE: without it, a genuinely neglected pet could reset its
    # gauge by restarting.  (Same shape as the egg_order_v migration.)
    if not data.get("obed_v") and not data.get("dead"):
        seed = {"Fresh": FRESH_OBEDIENCE, "InTraining": IN_TRAINING_OBEDIENCE}
        if float(data.get("obedience") or 0) <= 0:
            data["obedience"] = seed.get(data.get("stage"), ROOKIE_OBED_DEFAULT)
        data["obed_v"] = 1
    valid = {f.name for f in fields(Pet)}
    kwargs = {k: v for k, v in data.items() if k in valid}
    # (the full_health backfill left with the classic battle -- the 0.5 HP
    # race fights from a flat 5, so trained HP has no consumer; 0.5 BATTLE
    # 2026-07-17)
    try:
        pet = Pet(**kwargs)
    except TypeError:
        return None, ""
    # (the 13-field wrong-type list that stood here was superseded by THE
    # TYPE GATE above: same rejection, every field, checked BEFORE the
    # migrations that used to crash on the poison -- live-play audit
    # 2026-07-25.  It still guards sync_down_at_startup's probe.)
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
        elif not getattr(pet, "line_id", ""):
            # pre-line save: a consistent pet with no line_id would ride the
            # corpus engine forever; re-anchor by membership (truly off-chart
            # forms keep '' as before)
            from . import lines as _lines
            _lines.adopt_line(pet)
    if (getattr(pet, "dna_owned", None) or {}).get("None"):
        paid = pet.settle_dud_dna()           # DNA call #4 = A (2026-10-15)
        msg = (msg + f"  (old dud DNA cashed in: +{paid}b)").strip()
    if getattr(pet, "dna_wager_pending", 0) > 0 and not pet.dead:
        # a paid mash was in flight at quit/crash: SETTLE it as the spoiled
        # mash it was (rate 0 -- the stabilizer band still honors a >=500
        # stake).  The stake stays spent, like the tournament's documented
        # forfeit; the charge now always buys its outcome
        # (SUSPECT S2 ruling 2026-07-20)
        amt = int(pet.dna_wager_pending)
        field = pet.dna_minigame_award(amt, 0)
        note = (f"(the interrupted DNA wager settled: {amt} on a spoiled mash"
                + (f" → {field} banked" if field != "None"
                   else f" → {amt // 2}b back") + ")")
        msg = (msg + "  " + note).strip()
    return pet, msg


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


def load(path=None):
    """Return (pet, message); pet is None if no valid save exists.  A corrupt
    main save falls back to the .bak rotated by save() -- at most one autosave
    (~10s) behind, instead of a silent new egg.  When BOTH generations are
    unreadable, the damaged file is quarantined and the message SAYS SO -- a
    corrupt save must never be indistinguishable from a first launch
    (professionalism sweep 2026-07-14)."""
    path = path or SAVE_PATH
    broken = None                    # first candidate that existed but wouldn't load
    broken_dna = False
    for candidate in (path, path + ".bak"):
        if not os.path.exists(candidate):
            continue
        try:
            data = json.load(open(candidate, encoding="utf-8"))
        except (ValueError, OSError):
            broken = broken or candidate
            continue
        try:
            pet, msg = pet_from_save(data)
        except Exception:
            # the BELT under the type gate (live-play audit 2026-07-25): this
            # function's contract is fallback/quarantine, NEVER a raise -- a
            # poisoned save that slips any future gate must land in the same
            # .bak -> quarantine chain, not crash the boot in app.py
            pet, msg = None, ""
        if pet is None:
            if broken is None and isinstance(data, dict):
                try:
                    _dna_save_fields(data)
                except (ValueError, OverflowError):
                    broken_dna = True
            broken = broken or candidate
            continue
        if candidate != path:
            # DNA audit 2026-10-14: keep the poisoned original even if backup recovers.
            if broken_dna:
                quarantine_save(broken)
            msg = (msg + "  " if msg else "") + "(recovered from the backup save)"
        # Replay the committed progress rider after an interrupted projection.
        prog = data.get("progress") or {}
        if pet.trophies_won:
            prog = dict(prog, tourneys=sorted(set(prog.get("tourneys", [])) | {
                int(tid) for tid in pet.trophies_won if str(tid).isdigit()}))
        merge_progress(prog)
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
