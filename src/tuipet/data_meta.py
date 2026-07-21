"""The progression metadata (tier-1 split, 2026-07-17): egg unlock
rules, care effects, digicore config, honors titles."""
from __future__ import annotations
import csv  # noqa: F401
import gzip  # noqa: F401
import json  # noqa: F401
import os
import re  # noqa: F401
from functools import lru_cache  # noqa: F401

_HERE = os.path.dirname(__file__)
_DATA = os.path.join(_HERE, "data")
_RAW = _DATA  # bundled CSVs (digimon/evolutions/foods) live alongside sprites
from .data_core import (  # noqa: F401  (shared plumbing)
    AssetsError, _load_bundled, _open_data)


# (load_care_effects -- the careEffect.csv runtime, whose only shipped
# effect was the Futon's sleep boost -- left with the staple props:
# strict-DSprite items, 2026-07-17.  The csv stays on disk as dormant
# corpus data.)

@lru_cache(maxsize=1)
def load_digicore_config():
    """DVPet digicoreMenuConfig.csv -> {num: {label, icon, icon_x}}.
    Icon/IconX name the SPECIAL core badge png (setupDigicore info[1]/info[2]);
    a literal "null" HIDES the badge for that Digimon; unlisted Digimon get the
    default X-antibody-state badges."""
    label = {"burstCore.png": "Burst", "twelveCore.png": "Twelve",
             "twoCore.png": "Two", "darkcore.png": "Dark"}
    key = {"burstCore.png": "core_burst", "twelveCore.png": "core_twelve",
           "twoCore.png": "core_two", "darkcore.png": "core_dark"}
    out = {}
    path = os.path.join(_DATA, "digicoreMenuConfig.csv")
    if not os.path.exists(path):
        return out
    for r in csv.reader(open(path)):
        if len(r) < 2 or not r[0].strip().isdigit():
            continue
        icon = (r[1] or "").strip()
        icon_x = (r[2] or "").strip() if len(r) > 2 else ""
        out[int(r[0])] = {
            "label": label.get(icon),
            "icon": "hidden" if icon == "null" else key.get(icon),
            "icon_x": "hidden" if icon_x == "null" else key.get(icon_x),
        }
    return out

@lru_cache(maxsize=1)
def load_digicore_icons():
    """Back-compat: {num: core_label} for the Data Book PERSON page."""
    return {n: c["label"] for n, c in load_digicore_config().items() if c["label"]}

@lru_cache(maxsize=1)
def load_egg_unlock():
    """DVPet eggUnlock.csv -> {egg_index: rule}. Joined to tuipet egg indices by the
    egg's hatch name. Each rule is the parsed set of conditions that gate the egg;
    egg.evaluate() tests them against persistence.get_progress()."""
    from . import egg as egg_mod
    name_to_idx = {}
    for i in range(egg_mod.count()):
        name_to_idx.setdefault(egg_mod.hatch_name(i), i)

    def _int(v):
        v = (v or "").strip()
        return int(v) if v.lstrip("-").isdigit() else None

    def _opt(v):
        v = (v or "").strip()
        return None if v in ("", "-1", "None", "FALSE") else v

    rules = {}
    path = os.path.join(_DATA, "eggUnlock.csv")
    rows = list(csv.reader(open(path)))
    for r in rows[1:]:
        if len(r) < 23:
            continue
        idx = name_to_idx.get(r[0].strip())
        if idx is None:
            continue                      # egg not in this tuipet build
        hist = None
        if _opt(r[12]):
            hist = [int(x) for x in r[12].split(":") if x.strip().isdigit()]
        # (the Price column is dead: the DVPet licence economy was cut
        # 2026-07-17 -- "i never wanted egg licenses" -- real devices unlock
        # eggs by CONDITION, they never sell them.  Every surviving priced
        # row traded its price for a device-story gate.)
        rules[idx] = {
            "idx": idx,
            "name": r[0].strip(),
            "start": r[1].strip() == "TRUE",
            "map": _int(r[3]) if (_int(r[3]) is not None and _int(r[3]) >= 0) else None,
            "stage": _opt(r[4]),
            "xanti": r[5].strip() == "TRUE",
            "tourney": _int(r[6]) if (_int(r[6]) is not None and _int(r[6]) >= 0) else None,
            "zone": _opt(r[7]),
            "gen": _int(r[8]) if (_int(r[8]) is not None and _int(r[8]) >= 0) else None,
            "prev_field": _opt(r[9]),
            "prev_attr": _opt(r[10]),
            "prev_elem": _opt(r[11]),
            "history": hist,
            "food": _int(r[13]) if (_int(r[13]) is not None and _int(r[13]) >= 0) else None,
            "item": _int(r[14]) if (_int(r[14]) is not None and _int(r[14]) >= 0) else None,
            "habitat": _int(r[15]) if (_int(r[15]) is not None and _int(r[15]) >= 0) else None,
            "password": _opt(r[16]),
            # canon re-audit 2026-07: the checker compares these against the
            # PREVIOUS generation's snapshot, so they must source the (Temp)
            # prev-gen columns 18/20 -- the old 17/19 read the CURRENT-pet
            # columns (a latent mis-map; every one of the four is data-empty
            # in the corpus, so nothing observable changed)
            "obedience": _int(r[18]) if (_int(r[18]) is not None and _int(r[18]) >= 0) else None,
            "mood": _int(r[20]) if (_int(r[20]) is not None and _int(r[20]) >= 0) else None,
            "desc": (r[21] or "").strip(),
            "can_perm": r[22].strip() == "TRUE",
            # tuipet achievement columns (LINES_SPEC §7): unlocks that tell the
            # story of the egg -- lifetime wins (Sakumon = the battle egg),
            # album breadth (Petitmon = the collector egg), Mega-class kills
            # (Dodomon = the X egg)
            "wins": _int(r[23]) if (len(r) > 23 and _int(r[23]) is not None and _int(r[23]) >= 0) else None,
            "album_n": _int(r[24]) if (len(r) > 24 and _int(r[24]) is not None and _int(r[24]) >= 0) else None,
            "mega": _int(r[25]) if (len(r) > 25 and _int(r[25]) is not None and _int(r[25]) >= 0) else None,
            # online connections (DM20 connection-battle unlocks: Corona/Luna/
            # Meicoo/DORU) -- distinct tamers linked via a completed lobby
            # bout or jogress; persistence.record_connection() feeds it
            "connections": _int(r[26]) if (len(r) > 26 and _int(r[26]) is not None and _int(r[26]) >= 0) else None,
            # tuipet festival gate (2026-07-20): celebrate N of the 4 festival
            # days (recorded on a holiday-day adventure conquer) -- the seasonal
            # egg (Draco/Examon), so festivals stop being reward-hollow
            "festivals_n": _int(r[28]) if (len(r) > 28 and _int(r[28]) is not None and _int(r[28]) >= 0) else None,
        }
        if rules[idx]["map"] is not None:
            # the raid re-gate (BASIC VPET 2026-07-16): adventure left with
            # the world layer, so the CSV's map-clear stories become felled-
            # raid milestones (a map-N row opens after N+1 broken bosses)
            rules[idx]["desc"] = f"Fell {rules[idx]['map'] + 1} raid " \
                + ("boss" if rules[idx]["map"] == 0 else "bosses")
    return rules

@lru_cache(maxsize=1)
def load_titles():
    """titles.csv: the HONORS ladder -- purely cosmetic tamer titles, priced
    as the late-game prestige sink (bit-sink design 2026-07-14).  A title is
    profile-level (it survives generations) and rides the STATUS panel plus
    the lobby presence card."""
    out = []
    for r in csv.DictReader(_open_data(os.path.join(_DATA, "titles.csv"))):
        try:
            out.append({"id": int(r["TitleID"]), "name": (r["Name"] or "").strip(),
                        "price": int(r["Price"]),
                        "desc": (r.get("Description") or "").strip()})
        except (KeyError, ValueError):
            continue
    return out

def title_name(tid):
    """The honor's display name ('' for -1/unknown -- nothing worn)."""
    for t in load_titles():
        if t["id"] == tid:
            return t["name"]
    return ""
