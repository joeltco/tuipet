"""The world + presentation data (tier-1 split, 2026-07-17):
backgrounds, effects, icons, battle fx, attacks/orbs, enemies, cups, maps."""
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
from .data_core import (  # noqa: F401  (shared plumbing +
    AssetsError, _load_bundled, _open_data,  # cross-domain reads)
    _attack_index, load_requirements, load_sprites)


@lru_cache(maxsize=1)
def load_battle_fx():
    """The 0.5 battle-effect bitmaps (battle_fx.json.gz, ported from the
    clone 2026-07-17: attacks / hit / ready / start / wall / dead -- the
    DSprite rips the HP-race show draws from)."""
    try:
        with gzip.open(os.path.join(_DATA, "battle_fx.json.gz"), "rt", encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, EOFError, ValueError):
        return {}

@lru_cache(maxsize=1)
def load_orbs():
    return _load_bundled("orbs.json.gz")

@lru_cache(maxsize=1)
def load_device_attacks():
    """deviceAttacks.csv: species -> its real-hardware attack in orbs.json.gz
    'device' (ripped from MultiVPet's data.win, the classic V-Pet lineup).
    Keyed by normalized name so every roster row of the species matches."""
    path = os.path.join(_RAW, "deviceAttacks.csv")
    out = {}
    if os.path.exists(path):
        for r in csv.DictReader(_open_data(path)):
            nm = "".join(c for c in (r.get("Name") or "").lower() if c.isalnum())
            if nm and r.get("AttackKey"):
                out[nm] = r["AttackKey"]
    return out

def attack_orb(num, attribute, power, frame_i=0):
    """The attack projectile.  Device-accurate first (Joel 2026-07-14): a species
    in deviceAttacks.csv fires ITS OWN real-hardware attack for EVERY attribute,
    exactly like the original V-Pet -- frame_i animates the 2-frame attacks at
    the caller's 10Hz clock.  Everyone else keeps DVPet checkAttackSprite: the
    per-species special orb (attackSpritesSpecial.png, digimon.csv col 55) if set
    for this attribute, else the generic per-attribute orb at the power tier
    floor(power/25) from attackSprites.png."""
    orbs = load_orbs()
    req = load_requirements().get(num) or {}
    nm = "".join(c for c in (req.get("name") or "").lower() if c.isalnum())
    key = load_device_attacks().get(nm)
    if key:
        frames = orbs.get("device", {}).get(key)
        if frames:
            return frames[frame_i % len(frames)]
    idx = (req.get("attack_index") or {}).get(attribute, -1)
    if idx is not None and idx >= 0:
        sp = orbs["special"].get(str(idx))
        if sp:
            return sp
    tiers = orbs["generic"].get(attribute) or orbs["generic"]["Vaccine"]
    t = max(0, min(int(power) // 25, len(tiers) - 1))
    return tiers[t] or next((x for x in tiers if x), None)

_ATTACKS = None

def _load_attacks():
    global _ATTACKS
    if _ATTACKS is None:
        _ATTACKS = {}
        cols = {"Vaccine": "VaccineName:Effect", "Data": "DataName:Effect", "Virus": "VirusName:Effect"}
        for r in csv.DictReader(_open_data(os.path.join(_DATA, "digimon.csv"))):
            try:
                n = int(r["DigimonNum"])
            except (KeyError, ValueError):
                continue
            info = {}
            for a, c in cols.items():
                parts = [p.strip() for p in (r.get(c, "") or "").split(":")]
                effect = parts[1] if len(parts) > 1 and parts[1] else "None"
                info[a] = {"name": parts[0] if parts else "", "effect": effect,
                           "conditions": [p for p in parts[2:] if p]}
            _ATTACKS[n] = info
    return _ATTACKS

def move_name(num, attribute):
    """The flavour name of a Digimon's attack for an attribute (DVPet
    VaccineName/DataName/VirusName columns), e.g. 'Exhaust Flame'."""
    return (_load_attacks().get(num) or {}).get(attribute, {}).get("name", "")

def attack_info(num, attribute):
    """Full DVPet attack for an attribute: {name, effect, conditions[]} parsed from
    the digimon.csv Name:Effect:Condition(s) cell (AttackEffectProcess input)."""
    return (_load_attacks().get(num) or {}).get(attribute) or {"name": "", "effect": "None", "conditions": []}

# ---------------------------------------------------------------------------
# Adventure maps: ordered maps -> ordered zones, each with its random-encounter
# enemies and zone boss(es), parsed from zones.csv + enemies.csv.
# ---------------------------------------------------------------------------
@lru_cache(maxsize=1)
def load_tournies():
    """Tournament trophies (tournies.csv): per-season cups with field/attribute/age
    restrictions, a BitModifier prize, ItemWon/FoodWon prizes, and enemy overrides."""
    path = os.path.join(_DATA, "tournies.csv")
    rows = list(csv.DictReader(_open_data(path)))
    if not rows:
        return []
    hdr = list(rows[0].keys())
    age_col = next((k for k in hdr if k.startswith("AgeLimit")), "AgeLimit")
    food_col = next((k for k in hdr if k.startswith("FoodWon")), "FoodWonqAmount")

    def na(v):
        v = (v or "NA").strip()
        return "" if v in ("NA", "None", "") else v

    out = []
    for r in rows:
        try:
            tid = int(r["Trophy"])
        except (KeyError, ValueError):
            continue
        fid, famt = -1, 0
        fw = r.get(food_col) or "-1q-1"
        if "q" in fw:
            a, b = fw.split("q", 1)
            try:
                fid, famt = int(a), int(b)
            except ValueError:
                pass
        try:
            item = int(r.get("ItemWon") or -1)
        except ValueError:
            item = -1
        try:
            bm = float(r.get("BitModifier") or 1)
        except ValueError:
            bm = 1.0
        try:
            prelim = int(r.get("Prelim") or 0)
        except ValueError:
            prelim = 0
        out.append({
            "prelim": prelim,
            "id": tid, "sprite": int(r.get("SpriteNum") or 0),
            "season": na(r.get("Season")) or "Spring",
            "field_req": na(r.get("FieldRestriction")),
            "attr_req": na(r.get("AttributeRestriction")),
            "age_limit": na(r.get(age_col)),
            "bit_mod": bm, "item": item, "food_id": fid, "food_amt": famt,
            "reset_season": (r.get("ResetWonOnSeasonChange") or "FALSE").strip().upper() == "TRUE",
            "same_day_retry": (r.get("SameDayRetry") or "FALSE").strip().upper() == "TRUE",
            "enemy_stage": na(r.get("OverrideEnemyStage")),
            "enemy_attr": na(r.get("OverrideEnemyAttribute")),
            "enemy_elem": na(r.get("OverrideEnemyElement")),
            "enemy_field": na(r.get("OverrideEnemyField")),
        })
    return out

@lru_cache(maxsize=1)
def load_backgrounds():
    """Background scene sheets keyed by file name: the DSprite rip set (one
    frame each) plus the arena's 5-frame tourneyBack (BASIC VPET 2026-07-16;
    backgrounds.scene_for_egg wires a scene to every egg)."""
    path = os.path.join(_DATA, "backgrounds.json.gz")
    if not os.path.exists(path):
        return {}
    try:
        with gzip.open(path, "rt", encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return {}

@lru_cache(maxsize=1)
def load_effects():
    """Auxiliary effect overlays (poop/zzz/frozen/wash/emotes) keyed by name."""
    path = os.path.join(_DATA, "effects.json.gz")
    if not os.path.exists(path):
        return {}
    try:
        with gzip.open(path, "rt", encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return {}

@lru_cache(maxsize=1)
def load_icons():
    """Food/item icons (frame 0) keyed f:<id> / i:<id>, or empty if not extracted."""
    path = os.path.join(_DATA, "icons.json.gz")
    if not os.path.exists(path):
        return {}
    try:
        with gzip.open(path, "rt", encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return {}

# (load_armor_eggs -- the armorEggs.png ghost eggs -- REMOVED 2026-07-18:
# fan-authored art, unused even by DVPet, and Joel rejected it.  The shop's
# crest eggs show DVPet's own Digimental item glyphs, canon display.)
