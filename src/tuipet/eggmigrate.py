"""The egg-bank index migration (tier-4 split, 2026-07-17): every
shipped bank order and the (name, occurrence) translation between them.
Self-contained on purpose — the tables ARE the history; see the v5 notes
for the fake-egg cut."""
from __future__ import annotations


# --- egg-bank index migration (2026-07-10 egg saga) ---------------------------
# .400/.401 shipped an 84-egg bank; .402 cut/reordered to 78; .403 restored
# Nature Spirits (79); .404's dominance audit cut 11 duplicate eggs -- FIVE of
# them classics, so the classic block moves too.  v5 (the humulos provenance
# audit, 2026-07-17) cut the 22 fake eggs -- the no-covered-device babies and
# the two invented "???" eggs -- leaving the 46 device-verified eggs.  Saved
# egg INDICES translate by (name, occurrence) through the FULL bank order of
# whichever build wrote them (occurrence handles v4's twin "???" eggs).
EGG_ORDER_V = 5

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

_V404_FULL = [
    "Botamon", "Punimon", "Poyomon", "Yuramon", "Zurumon", "Babumon",
    "Kuramon", "Chibickmon", "Tsubumon", "Pururumon", "Jyarimon", "Dodomon",
    "Puttimon", "Kiimon", "Dokimon", "Chibomon", "Datirimon", "ChibiKiwimon",
    "Ketomon", "Leafmon", "Pafumon", "Paomon", "Petitmon", "Popomon",
    "Pupumon", "Bommon", "Pusumon", "Puwamon", "Relemon", "Sakumon",
    "Zerimon", "Cocomon", "Fufumon", "Cotsucomon", "Algomon I", "Bombmon",
    "Carimon", "Sunamon", "Curimon", "Pyonmon", "Puyomon", "???", "???",
    "Fusamon", "Nature Spirits Egg", "Deep Savers Egg",
    "Nightmare Soldiers Egg", "Wind Guardians Egg", "Metal Empire Egg",
    "Virus Busters Egg", "Corona Egg", "Luna Egg", "Zuba Egg", "Hack Egg",
    "Meicoo Egg", "DORU Egg", "Slayerdra Egg", "Breakdra Egg", "Ryuda Egg",
    "Draco Egg", "Lalamon Egg", "Meicoomon Egg", "Terrier Egg", "Lop Egg",
    "V Egg", "Virus Busters Ver. 20th Egg", "Digitama X3", "Kera Digitama"]

# a CUT egg MID-INCUBATION falls back to the surviving egg of the same baby
# (name -> name; resolved against the live bank).  Fallbacks are for egg_type
# ONLY -- never for eggs_owned, or a cut egg would "translate" into permanent
# ownership of an unearned egg (the .403 Puttimon-as-starter bug).
_CUT_FALLBACK = {
    "Digitama X": "Puttimon", "Digitama X2": "Kiimon",
    # the v5 fake-egg cut (humulos provenance audit 2026-07-17): a fake egg
    # mid-incubation becomes a device egg of roughly its temperament
    "Babumon": "Botamon", "Jyarimon": "Botamon", "Datirimon": "Dokimon",
    "ChibiKiwimon": "Punimon", "Pafumon": "Yuramon", "Paomon": "Yuramon",
    "Popomon": "Botamon", "Pupumon": "Poyomon", "Bommon": "Punimon",
    "Pusumon": "Poyomon", "Puwamon": "Punimon", "Relemon": "Yuramon",
    "Bombmon": "Punimon", "Carimon": "Zurumon", "Sunamon": "Zurumon",
    "Curimon": "Yuramon", "Pyonmon": "Punimon", "Puyomon": "Poyomon",
    "Fusamon": "Punimon", "???": "Botamon",
    "Meicoomon Egg": "Virus Busters Egg",
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
    return {2: _V402_FULL, 3: _V403_FULL, 4: _V404_FULL}.get(save_v, _V401_FULL)

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
