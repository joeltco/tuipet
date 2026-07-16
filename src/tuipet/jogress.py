"""Jogress (DNA) fusion — the pair table (the clone rebuild, 2026-07-15).

Fusion is EXACT-PAIR now: my species + the partner's species look up the
sorted 'pathA|pathB' key in the pair table; a hit is the fusion form, a
miss is 'no resonance'.  Both sides of a lobby jogress run the same lookup
on the same two paths, so the fusion is both-or-neither by construction.
The fusion costs battle-scale energy/weight and banks the stage counters
exactly like a natural evolution.
"""
from __future__ import annotations
from . import data


def can_jogress(pet):
    if getattr(pet, "dead", False):
        return "It rests now — press N for a new egg."
    if pet.stage in ("Egg", "Baby I", "Baby II"):
        return "Too young to jogress."
    if pet.asleep:
        return "zzz… asleep"
    if pet.energy < 5:
        return "Too tired to fuse."
    return None


def partner_options(pet):
    """Every partner path this pet's species can fuse with -> the result."""
    mine = pet.species_path
    if not mine:
        return {}
    out = {}
    for key, result in data.load_jogress_pairs().items():
        a, b = key.split("|", 1)
        if a == mine:
            out[b] = result
        elif b == mine:
            out[a] = result
    return out


def resolve_pair(pet, partner_path):
    """The fusion form (num) for me + this exact partner, or None."""
    mine = pet.species_path
    if not mine or not partner_path:
        return None
    key = f"{min(mine, partner_path)}|{max(mine, partner_path)}"
    result = data.load_jogress_pairs().get(key)
    if not result:
        return None
    return data.num_by_path().get(result)


def resolve_online(pet, payload):
    """A lobby partner's card carries its species num -> its path -> the
    pair lookup.  Symmetric: both devices compute the same key."""
    # the num is UNTRUSTED wire data from the fusion partner: a non-int
    # (num:"evil") crashed the whole client on int() (round-3 audit 2026-07-16)
    try:
        pnum = int(payload.get("num"))
    except (TypeError, ValueError):
        return None
    rec = data.load_sprites()[1].get(pnum)
    if rec is None:
        return None
    target = resolve_pair(pet, rec.get("path"))
    if target is None:
        return None
    _, by = data.load_sprites()
    return {"num": target, "name": by[target]["name"],
            "attribute": by[target]["attribute"],
            "stage": by[target]["stage"]}


def fuse(pet, target_num):
    """Perform the fusion: evolve into the target; the counters bank like a
    natural evolution; the effort costs ride Pet.record-style."""
    _, by = data.load_sprites()
    name = by[target_num]["name"]
    path = by[target_num]["path"]
    pet._evolve_to_path(path)
    pet.energy = max(0, pet.energy - 5)
    pet.weight = max(1, pet.weight - 4)
    return f"Jogress! Fused into {name}!"
