"""Jogress (DNA) fusion — combine your pet with a partner of a matching attribute
to evolve into a special fusion form. The attribute pairing is DVPet's
attributeJogress matrix; jogress targets are flagged SpecialEvolution=Jogress in
the evolution graph and bypass the normal care requirements (the partner provides
the "DNA"), so it's a deliberate fusion the player triggers."""
from __future__ import annotations
import random
from . import data

# result = JOGRESS[player_attribute][partner_attribute]  (from attributeJogress.csv)
JOGRESS = {
    "Vaccine": {"Vaccine": "Vaccine", "Data": "Data", "Virus": "Vaccine"},
    "Data":    {"Vaccine": "Data",    "Data": "Data", "Virus": "Virus"},
    "Virus":   {"Vaccine": "Vaccine", "Data": "Virus", "Virus": "Virus"},
}
ATTRS = ("Vaccine", "Data", "Virus")


def required_partners(player_attr, target_attr):
    if player_attr not in JOGRESS:
        return []
    return [p for p in ATTRS if JOGRESS[player_attr].get(p) == target_attr]


def _partner_for(pet, attrs):
    _, by = data.load_sprites()
    same = [n for n, r in by.items() if r["stage"] == pet.stage and r["attribute"] in attrs
            and not data.is_placeholder(n) and n != pet.num]
    pool = same or [n for n, r in by.items() if r["attribute"] in attrs and not data.is_placeholder(n)]
    n = random.choice(pool) if pool else None
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


def fuse(pet, target_num):
    """Perform the fusion: the pet jogress-evolves into the target form."""
    _, by = data.load_sprites()
    name = by[target_num]["name"]
    pet.evolve_to(target_num)   # special evolution; partner supplies the DNA
    return f"Jogress! Fused into {name}!"
