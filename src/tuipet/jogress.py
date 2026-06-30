"""Jogress (DNA Digivolution) — the authentic DM20 fusion.

A SPECIFIC partner mon fuses your pet into a SPECIFIC super form. The pairs come
straight from the corpus (the "Tag Battle 5x with <partner>" evolution edges), e.g.
Taichi's WarGreymon + Yamato's MetalGarurumon -> Omnimon. No attribute matrix, no
digimon.csv — just the canonical partner->result pairs.
"""
from __future__ import annotations
from . import data
from . import species


def options(pet):
    """The fusions available from the pet's current form: each is a NAMED partner mon
    -> a fusion result (corpus tag_battle_with edges)."""
    _, by = data.load_sprites()
    out, seen = [], set()
    for e in species.evolutions(pet.num):
        partner = (e.get("parsed") or {}).get("tag_battle_with")
        if not partner:
            continue
        tgt = species.by_id(e.get("to_id"))
        if not tgt or tgt["num"] in seen or data.is_placeholder(tgt["num"]):
            continue
        seen.add(tgt["num"])
        prec = species.by_name(partner)
        out.append({
            "num": tgt["num"], "name": tgt["name"], "attribute": tgt["attribute"],
            "stage": tgt["stage"],
            "partner_num": prec["num"] if prec else None,
            "partner_name": partner,
        })
    return out


def can_jogress(pet):
    if pet.stage in ("Egg", "Baby I", "Baby II"):
        return "Too young to jogress."
    if pet.asleep:
        return "zzz... asleep"
    if not options(pet):
        return "No fusion partner resonates now."
    return None


def fuse_targets(pet, partner_num):
    """Online jogress: the fusion(s) reachable when the connected partner's pet is the
    species `partner_num` (the real partner replaces the offline example)."""
    if partner_num is None:
        return []
    return [o for o in options(pet) if o["partner_num"] == partner_num]


def resolve(pet, partner_num):
    """The fusion form for a connected partner of species `partner_num` (or None)."""
    targets = fuse_targets(pet, partner_num)
    return targets[0] if targets else None


def fuse(pet, target_num):
    """Perform the fusion: the pet jogress-evolves into the target form."""
    _, by = data.load_sprites()
    name = by[target_num]["name"]
    pet.evolve_to(target_num)   # special evolution; the partner supplies the DNA
    return f"Jogress! Fused into {name}!"
