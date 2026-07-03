"""Jogress (DNA) fusion — combine your pet with a partner of a matching attribute
to evolve into a special fusion form. The attribute pairing is DVPet's
attributeJogress matrix; jogress targets are flagged SpecialEvolution=Jogress in
the evolution graph and bypass the normal care requirements (the partner provides
the "DNA"), so it's a deliberate fusion the player triggers."""
from __future__ import annotations
import random
from . import data
from . import evolution

JOGRESS_ENERGY_COST = 0.66     # JogressEnergyChange -0.66: a fusion drinks 66% of max energy

# attributeJogress.csv as (result, digimon, partner) attribute triples. BOTH matrix blocks
# are included (DVPet Affinity.readAttributeInfo reads all rows), so None/Free-attribute
# fusions are covered -- not just the Vaccine/Data/Virus 3x3. 308 mons are Free-attribute and
# 23 jogress targets (Apocalymon, Mastemon, ...) are Free, all unreachable without block 2.
JOGRESS_PAIRS = [
    # block 1 -- partner None yields None
    ("None", "None", "None"), ("None", "Vaccine", "None"), ("None", "Data", "None"), ("None", "Virus", "None"),
    # block 1 -- partner Vaccine / Data / Virus (the classic 3x3, plus the None-digimon column)
    ("None", "None", "Vaccine"), ("Vaccine", "Vaccine", "Vaccine"), ("Data", "Data", "Vaccine"), ("Vaccine", "Virus", "Vaccine"),
    ("None", "None", "Data"), ("Data", "Vaccine", "Data"), ("Data", "Data", "Data"), ("Virus", "Virus", "Data"),
    ("None", "None", "Virus"), ("Vaccine", "Vaccine", "Virus"), ("Virus", "Data", "Virus"), ("Virus", "Virus", "Virus"),
    # block 2 -- Free-attribute combinations (a None partner or None digimon yields a real result)
    ("Virus", "Vaccine", "None"), ("Vaccine", "Data", "None"), ("Data", "Virus", "None"),
    ("Virus", "None", "Vaccine"), ("Vaccine", "None", "Data"), ("Data", "None", "Virus"),
]
ATTRS = ("Vaccine", "Data", "Virus")


def required_partners(player_attr, target_attr):
    """Partner attributes that fuse a `player_attr` digimon into a `target_attr` form
    (attributeJogress.csv, both blocks -- handles None/Free combinations natively)."""
    return [par for (evol, dig, par) in JOGRESS_PAIRS
            if dig == player_attr and evol == target_attr]


def _partner_for(pet, attrs):
    _, by = data.load_sprites()
    same = [n for n, r in by.items() if r["stage"] == pet.stage and r["attribute"] in attrs
            and not data.is_placeholder(n) and n != pet.num]
    pool = same or [n for n, r in by.items() if r["attribute"] in attrs and not data.is_placeholder(n)]
    n = min(pool) if pool else None        # stable example partner (was random -> re-rolled each visit)
    return n, (by[n]["name"] if n else "?")


def options(pet):
    """Available fusions from the pet's current form."""
    _, by = data.load_sprites()
    reqs = data.load_requirements()
    evo = data.load_evolutions()
    out = []
    seen = set()
    for t in evo.get(pet.num, []):
        if t not in by or t in seen:
            continue
        r = reqs.get(t)
        if not r or r.get("special") not in ("Jogress", "Fusion", "Mode"):   # Fusion+Mode share the Jogress DNA matrix
            continue
        partners = required_partners(pet.attribute, by[t]["attribute"])
        if not partners:
            continue
        # DVPet getValidEvolutions(connecting=true): the fusion form's FULL
        # requirement list (or its DNA bypass) still gates the jogress -- the
        # handshake only waives the special-type check.  Evaluated once per
        # menu open (the probability roll rides inside, like checkEvolReq).
        if not evolution.check(pet, t, connecting=True):
            continue
        seen.add(t)
        pnum, pname = _partner_for(pet, partners)
        out.append({
            "num": t, "name": by[t]["name"], "attribute": by[t]["attribute"],
            "stage": by[t]["stage"], "partners": partners,
            "partner_num": pnum, "partner_name": pname,
        })
    return out


def can_jogress(pet):
    if pet.stage in ("Egg", "Fresh", "InTraining"):
        return "Too young to jogress."
    if pet.asleep:
        return "zzz... asleep"
    if not options(pet):
        return "No fusion partner resonates now."
    return None


def fuse_targets(pet, partner_attr):
    """Multiplayer jogress: the forms `pet` can fuse into when the partner has
    attribute `partner_attr` (the real partner replaces offline `_partner_for`)."""
    pa = partner_attr or "None"
    return [o for o in options(pet) if pa in o["partners"]]


def resolve(pet, partner_attr):
    """Choose the fusion form for a partner of `partner_attr` the way DVPet's
    pairJogressMatch does: the highest-priority valid target, ties broken at random."""
    targets = fuse_targets(pet, partner_attr)
    if not targets:
        return None
    reqs = data.load_requirements()
    best = max(reqs.get(o["num"], {}).get("priority", 0.0) for o in targets)
    top = [o for o in targets if reqs.get(o["num"], {}).get("priority", 0.0) == best]
    return random.choice(top)


def fuse(pet, target_num):
    """Perform the fusion: the pet jogress-evolves into the target form.
    A fusion drinks 66% of max energy (JogressEnergyChange -0.66)."""
    _, by = data.load_sprites()
    name = by[target_num]["name"]
    pet._set_energy(pet.energy - int(round(pet.max_energy * JOGRESS_ENERGY_COST)))
    pet.evolve_to(target_num)   # special evolution; partner supplies the DNA
    return f"Jogress! Fused into {name}!"
