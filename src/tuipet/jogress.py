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
JOGRESS_SICK_CHANCE = 90       # startJogress checkSick(90): fusing with a SICK partner is a
#                                near-certain catch (a hardcoded canon literal, not config;
#                                jogress audit 2026-07-06)

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
    if getattr(pet, "dead", False):
        # the missing dead leg let a full-DP corpse pass -- this gate also
        # drives the lobby invite auto-decline (dead sweep 2026-07-06)
        return "It rests now — press N for a new egg."
    if pet.stage in ("Egg", "Fresh", "InTraining"):
        return "Too young to jogress."
    if pet.asleep:
        # a PLAYER poke disturbs the sleeper like every other care key (feed/
        # train/battle/dna all grumble-wake; Joel 2026-07-06).  The lobby's
        # REMOTE path never reaches here -- _session_gate short-circuits
        # asleep before this gate, so strangers still can't wake the pet.
        return pet._disturbed()
    # Pen20 (LINES_SPEC §6): a jogress takes FULL DP -- earned with protein
    # feeds (+1 each) or a night's sleep (3 game-hours refills the meter)
    from .pet import DP_MAX
    if getattr(pet, "dp", 0) < DP_MAX:
        return f"DP {getattr(pet, 'dp', 0)}/{DP_MAX} — protein or a night's sleep."
    # canJogress -> checkRefused(energyChange=-0.66): a non-compliant pet may balk,
    # and one that can't afford the fusion's energy auto-refuses
    refused = pet.check_refused(energy_change=-JOGRESS_ENERGY_COST)
    pet.check_compliant()                        # canJogress: checkRefused; checkCompliant
    if refused:
        return f"{pet.name} refuses to fuse!"
    if not options(pet):
        return "No fusion partner resonates now."
    return None


def fuse_targets(pet, partner_attr):
    """Multiplayer jogress: the forms `pet` can fuse into when the partner has
    attribute `partner_attr` (the real partner replaces offline `_partner_for`)."""
    pa = partner_attr or "None"
    return [o for o in options(pet) if pa in o["partners"]]


def _final_pick(pet, targets):
    """getFinalEvolution's pick (canon re-audit 2026-07): highest fulfilled
    score, ties broken by smallest deviation, then at random."""
    best = max(evolution.fulfilled(pet, o["num"]) for o in targets)
    top = [o for o in targets if abs(evolution.fulfilled(pet, o["num"]) - best) < 1e-9]
    if len(top) > 1:
        mind = min(evolution.deviation(pet, o["num"]) for o in top)
        top = [o for o in top if evolution.deviation(pet, o["num"]) == mind]
    return random.choice(top)


def resolve(pet, partner_attr):
    """Choose the fusion form from the partner's attribute alone (the offline
    panel + the LEGACY online path -- see resolve_online)."""
    targets = fuse_targets(pet, partner_attr)
    return _final_pick(pet, targets) if targets else None


def pairable_attrs(pet):
    """The partner attributes that unlock at least one fusion for this pet --
    canon's 'attributes' half of the jogressMatch wire string."""
    return sorted({p for o in options(pet) for p in o["partners"]})


def resolve_online(pet, payload):
    """Canon JogressProtocol.jogressFindFusionsAndAttributes (lobby session
    audit 2026-07-07).  The match runs in canon's two channels:
      1. SHARED FUSION NAMES -- the intersection of both sides' reachable
         fusion-name lists; attribute pairing is not consulted.  Symmetric,
         so both devices fuse (each through its own getFinalEvolution pick,
         canon's own quirk included: the two picks may differ).
      2. The ATTRIBUTE fallback -- canon gates it on the SAME growth stage
         and MUTUAL compatibility (my attr in their pairable list AND their
         attr in mine).  Both checks are symmetric, so a fusion is
         both-or-neither: the one-sided fuse (A spends DP + 66% energy and
         evolves while B reads 'no resonance') cannot happen.
    A LEGACY peer (pre-v0.2.347) ships neither list; fall back to the old
    one-sided attr resolve so mixed-version fusions still work."""
    if "attrs" not in payload and "fusions" not in payload:
        return resolve(pet, payload.get("attr"))
    mine = options(pet)
    named = [o for o in mine if o["name"] in set(payload.get("fusions") or ())]
    if named:
        return _final_pick(pet, named)
    p_stage = payload.get("stage")
    if not p_stage:                       # older new-client: derive from the dex
        _, by = data.load_sprites()
        p_stage = by.get(payload.get("num"), {}).get("stage")
    if p_stage != pet.stage:              # canon: getOppStage().equals(getGrowthStage())
        return None
    p_attr = payload.get("attr") or "None"
    if (pet.attribute not in (payload.get("attrs") or ())
            or p_attr not in {p for o in mine for p in o["partners"]}):
        return None
    return resolve(pet, p_attr)


def fuse(pet, target_num):
    """Perform the fusion: the pet jogress-evolves into the target form.
    A fusion drinks 66% of max energy (JogressEnergyChange -0.66)."""
    _, by = data.load_sprites()
    name = by[target_num]["name"]
    # canon PhysicalState.jogress: energy += Math.ceil(-0.66 x max) -- the ceil
    # rounds TOWARD ZERO on the negative product (max 24 drains 15, not 16)
    import math
    pet._set_energy(pet.energy + math.ceil(-JOGRESS_ENERGY_COST * pet.max_energy))
    pet.dp = 0                  # Pen20: the fusion spends the whole DP meter
    pet.evolve_to(target_num)   # special evolution; partner supplies the DNA
    from . import lines as lines_mod
    lines_mod.adopt_line(pet)   # stay in the line system if any chart claims the fusion
    return f"Jogress! Fused into {name}!"
