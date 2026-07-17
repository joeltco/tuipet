"""The DigiCore DATA MODEL -- every page, row and core computation
(Joel 2026-07-17: "can we modularize digicore now. polish it up").

digicorescreen.py renders and routes keys; THIS module decides what the
core says.  The statusbox law applies here too: a row may only show LIVE
data -- the move purged the dead "Spirit" label (the disposition trait
wears its own name now) and the Ailing row's injury fragment (the injury
system left 2026-07-16; is_injured() is hard False).
"""
from __future__ import annotations
from . import data
from . import backgrounds as _bgs
from . import egg as _egg
from . import evolution, lines


DIGICORE_BASE_RATE = 14            # DigicoreBaseRate (config.csv col 1)
# ViewUtil.getDigicoreBackground field -> backdrop file suffix
_CORE_BG = {"": "digicoreN", "None": "digicoreN", "DragonsRoar": "digicoreDr",
            "DeepSaver": "digicoreDs", "JungleTrooper": "digicoreJt",
            "MetalEmpire": "digicoreMe", "NatureSpirit": "digicoreNsp",
            "WindGuardian": "digicoreWg", "NightmareSoldier": "digicoreNs",
            "DarkArea": "digicoreDa", "VirusBuster": "digicoreVb"}


def core_number(pet):
    """setupDigicore's meter: an evolution countdown while a normal evolution is
    pending, otherwise a lifespan meter counting up.  Floors at 1."""
    base = DIGICORE_BASE_RATE
    growth = pet.STAGE_DURATION.get(pet.stage)
    pending = (growth is not None and pet.stage_seconds < growth
               and bool(data.load_evolutions().get(pet.num)))
    if pending:
        denom = round(growth / base) or 1
        n = int(base - pet.stage_seconds / denom)
    else:
        denom = round(pet.lifespan / base) or 1
        n = int(pet.age_seconds / denom)
    return max(1, n)


def core_badge_key(pet):
    """setupDigicore's badge: the per-Digimon special core (digicoreMenuConfig,
    IconX while X-antibody; "null" hides it), else the X-state badges."""
    cfg = data.load_digicore_config().get(pet.num, {})
    x = getattr(pet, "x_antibody", "None")
    pick = cfg.get("icon_x") if x != "None" else cfg.get("icon")
    if pick == "hidden":
        return None
    if pick:
        return pick
    if x != "None":
        return "core_xreq"                      # Permanent (binary since the X slim)
    return "core_xnone"


def core_background(pet):
    """The core swirl backdrop by the highest CHARGED DNA field (DNA.getHighestDNA:
    strict max over the charged array, ties yield none) -- else the pet's own field."""
    field = pet.highest_dna() or pet.field
    frames = data.load_backgrounds().get(_CORE_BG.get(field, "digicoreN"))
    return frames[0] if frames else None


def silhouette(rows):
    """ViewUtil.getSilhouetteImage on 1-bit art: black the sprite's OPAQUE
    MASK.  Canon blackens every non-transparent pixel; our 1-bit equivalent is
    an exterior flood fill -- any '0' NOT reachable from outside the sprite is
    enclosed body and goes black, while real gaps (between wings, under arms)
    stay clear.  (The old per-row scanline fill bridged every concavity into
    one melted blob -- Joel: 'the shape is out of resolution', 2026-07-04.)"""
    if not rows:
        return rows
    w = max(len(r) for r in rows)
    g = [list(r.ljust(w, "0")) for r in rows]
    h = len(g)
    # flood the EXTERIOR from every border '0' (4-connected)
    stack = [(x, y) for x in range(w) for y in (0, h - 1) if g[y][x] == "0"]
    stack += [(x, y) for y in range(h) for x in (0, w - 1) if g[y][x] == "0"]
    outside = set(stack)
    while stack:
        x, y = stack.pop()
        for nx, ny in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
            if 0 <= nx < w and 0 <= ny < h and g[ny][nx] == "0" and (nx, ny) not in outside:
                outside.add((nx, ny))
                stack.append((nx, ny))
    return ["".join("0" if (x, y) in outside else "1" for x in range(w))
            for y in range(h)]


def ghost(mask, phase=0):
    """The teaser's unresolved-data look: the mask's CONTOUR stays crisp while
    the interior renders as a 50% dither (the evolve strobe's own idiom),
    shimmering with `phase`.  A solid 16px mask carries no shape information
    -- it read as a broken blob (Joel: 'the shape is out of resolution');
    canon's solid silhouette only works at 48px."""
    if not mask:
        return mask
    w = max(len(r) for r in mask)
    g = [r.ljust(w, "0") for r in mask]
    h = len(g)
    out = []
    for y in range(h):
        row = []
        for x in range(w):
            if g[y][x] != "1":
                row.append("0")
                continue
            edge = (x == 0 or y == 0 or x == w - 1 or y == h - 1
                    or g[y][x - 1] == "0" or g[y][x + 1] == "0"
                    or g[y - 1][x] == "0" or g[y + 1][x] == "0")
            row.append("1" if edge or (x + y + phase) % 2 == 0 else "0")
        out.append("".join(row))
    return out


def next_evolution(pet):
    """The silhouette's subject (getCurrentNaturalEvol first entry): the ready
    candidate first, else the closest one; None past growth / at a final form."""
    if pet.num == -1:
        # canon setupDigicore counts an EGG's hatch as its next evolution
        # (the chart holds Egg -> Fresh), so the gaze teases the hatchling --
        # it said "final form" over an egg (audit 2026-07-05)
        from . import egg as egg_mod
        targets = egg_mod.hatch_targets(getattr(pet, "egg_type", 0))
        return targets[0] if targets else None
    if lines.active(pet):
        rows = lines.evo_rows(pet)      # line chart: ready first, else fewest-unmet
        if not rows:
            return None
        return sorted(rows, key=lambda r: (not r[2], r[3]))[0][0]
    try:
        cands = sorted(evolution.candidates(pet), key=lambda c: (not c[2], -c[3]))
    except Exception:
        cands = []
    return cands[0][0] if cands else None


def _mins(s):
    s = int(max(0, s))
    if s < 3600:
        return f"{s // 60}m{s % 60:02d}s"
    if s < 86400:
        return f"{s // 3600}h{(s % 3600) // 60:02d}m"
    return f"{s // 86400}d{(s % 86400) // 3600:02d}h"


def _evo_rows(pet):
    """The evolution line for the data book: (num, name, ready, unmet) per
    candidate, closest-first.  unmet counts the failing checklist gates
    (evolution.requirement_report) -- the page shows it as distance-to-go.

    Canon shows the chart at EVERY stage -- DVPet's drawEvolutionMenu never
    gates on age, and setupDigicore counts hatching as the egg's own
    evolution (the "(too young)" stonewall was a pre-line-engine tuipet
    invention; Joel caught it 2026-07-10)."""
    if pet.num == -1:
        # an egg's next form is its hatchling; the multi-target mystery
        # digitama keeps its surprise (name masked, like hidden_evo)
        from . import egg as egg_mod
        _, by = data.load_sprites()
        targets = egg_mod.hatch_targets(getattr(pet, "egg_type", 0))
        if not targets:
            return "(final form)"
        if len(targets) > 1:
            return [(targets[0], "???", False, 0)]
        return [(t, by.get(t, {}).get("name", "?"), False, 0) for t in targets]
    if lines.active(pet):
        # line pets: the line's own chart rows, in first-match order (the order
        # IS the information -- earlier rows win ties), with live unmet counts
        rows = lines.evo_rows(pet)
        return rows or "(final form)"
    try:
        cands = sorted(evolution.candidates(pet), key=lambda c: (not c[2], c[3]))
    except Exception:
        cands = []
    if not cands:
        return "(final form)"
    rows = []
    from tuipet import persistence as _p
    reqs = data.load_requirements()
    for num, name, ready, dev in cands[:8]:
        unmet = sum(1 for met, _ in evolution.requirement_report(pet, num) if met is False)
        # HiddenEvolution (digicore audit 2026-07-06): canon's tree conceals
        # 130 flagged forms until FIRST reached -- the cross-generation album
        # is the reveal state (Evolution.setUnlocked).  The slot still shows
        # (position + distance-to-go intact), only the name is masked.
        if reqs.get(num, {}).get("hidden_evo") and not _p.album_seen(num):
            name = "???"
        rows.append((num, name, ready, unmet))
    return rows


def _trophy_rows(pet):
    """The trophy room: this life's cups (label + the day they fell) topped
    by the career totals -- lifetime cups persist across generations."""
    from tuipet import tournament as _t
    from tuipet import persistence as _p
    # "This life" is exactly the 9-char label column -- it rendered flush
    # against its value ("This lifenone yet"; egg-stage audit 2026-07-05)
    rows = [("This pet", "\u2605" * min(pet.trophies, 12) or "none yet")]
    try:
        career = len(_p.get_progress().get("tourneys", ()) or ())
    except Exception:
        career = 0
    rows.append(("Career", f"{career} cup(s), all generations"))
    # the collection long game ("ultimate v-pet" arc 2026-07-07): every raised
    # form lands in the cross-generation album; divergence/jogress/eggs are
    # the roads to the rest of the corpus
    try:
        seen = len(_p.get_progress().get("album", ()) or ())
    except Exception:
        seen = 0
    _, by = data.load_sprites()
    # the denominator must count what the numerator can actually REACH: the dex
    # carries 329 duplicate rows (one species can sit on several device pages --
    # five Petitmon, seven Omnimon MM), and album_add stores the CANONICAL num,
    # so `seen` tops out at the canonical count.  Comparing it to the raw row
    # count showed 1218/1547: an album that could never be completed, however
    # perfectly you played (roster audit 2026-07-14, Joel: "we have duplicate
    # mons??").
    total = len({data.canonical_num(n) for n in by if not data.is_placeholder(n)})
    rows.append(("Album", f"{seen}/{total} discovered"))
    # the Maps row became the Raids row (BASIC VPET 2026-07-16): adventure
    # left, and felled community bosses gate the old MapComplete eggs now
    try:
        felled = int(_p.get_progress().get("raids", 0) or 0)
    except Exception:
        felled = 0
    rows.append(("Raids", f"{felled} raid bosses felled"))
    won = sorted((getattr(pet, "trophies_won", None) or {}).items())
    for tid, season in won[:4]:                     # keep the page at 9 rows max
        tr = _t.trophy_by_id(tid)                   # (was 5: the Maps row joined)
        rows.append((_t.trophy_label(tr)[:12] if tr else f"cup {tid}", season))
    if len(won) > 4:
        rows.append(("…", f"+{len(won) - 4} more"))
    return rows


def _legacy_rows():
    """The LEGACY page: every retired generation's headstone, newest first --
    they were banked by snapshot_prev_gen and never shown (sweep 2026-07-14).
    Value budget is 30 cols (40 - the 9-char label gutter)."""
    from tuipet import persistence as _p
    try:
        elders = list(_p.load_settings().get("progress", {}).get("legacy", []))
    except Exception:
        elders = []
    if not elders:
        return [("—", "no elders yet — this pet"), ("", "is writing generation one")]
    rows = []
    for r in reversed(elders[-8:]):                 # 8 headstones + the more row = 9
        days = int(float(r.get("age", 0)) // 1440)  # 1 game day = 1440 real seconds
        fate = "†" if r.get("dead") else ""         # fell vs retired to the next egg
        val = f"{str(r.get('name', '?'))[:12]} {r.get('stage', '?')} {days}d{fate}"
        rows.append((f"gen {r.get('gen', '?')}", val[:30]))
    if len(elders) > 8:
        rows.append(("…", f"+{len(elders) - 8} more remembered"))
    return rows


def build_pages(pet):
    rem = pet.lifespan - pet.age_seconds
    appetite = ["picky", "normal", "greedy"][pet._glutton() + 1]
    temperament = ["mellow", "steady", "restless"][pet._restless() + 1]
    disp = ["sour", "even", "sunny"][pet._disposition() + 1]
    status = [
        ("Name", pet.name),
        # an egg has no dex number yet -- "#-1" leaked the internal sentinel
        # (egg-stage audit 2026-07-05)
        ("No.", "—" if pet.num < 0 else f"#{pet.num}"), ("Stage", pet.stage),
        ("Attrib", pet.attribute), ("Field", data.pretty_field(pet.field) or "-"),
        ("Gen", str(pet.generation)),
        ("Age", _mins(pet.age_seconds)), ("Life", f"{_mins(rem)} left"),
        ("Battles", f"{pet.wins}W / {pet.battles} · {pet.bits}b"),
    ]
    # the POWER page carries the numbers the evolution gates actually read
    # (data-page polish 2026-07-17): the attribute ledger (setPower), the
    # trained battle Form, the DMX battle level, KO6 Mega kills.  The
    # weight/bits/battles bookkeeping moved beside its kin (weight ->
    # CONDITION; battles/bits -> STATUS; trophies have their own page).
    power = [
        ("Vaccine", str(pet.vaccine)), ("Data", str(pet.data_power)),
        ("Virus", str(pet.virus)), ("Effort", f"{pet.strength}/4"),
        ("Form", getattr(pet, "saved_hit_type", "normal")),
        ("Level", f"{lines._pet_level(pet)} ({getattr(pet, 'exp', 0)} exp)"),
        ("Drills", str(getattr(pet, "total_trainings", 0))),
        ("KO6", f"{pet.mega_kills} Mega felled"),
    ]
    if pet.x_antibody != "None":
        power.append(("X-Anti", pet.x_antibody))   # keep the page at its 9-row max
    # (the Likes/Dislikes clock rows left with the timeRanks system --
    # BASIC VPET 2026-07-17)
    person = [
        # ("Spirit" was the dead spirit system's word -- the row shows the
        # DISPOSITION trait, which is alive; label polish 2026-07-17)
        ("Type", pet.personality()), ("Nature", disp),
        ("Appetite", appetite), ("Pace", temperament),
    ]
    core = data.load_digicore_icons().get(pet.num)
    if core:
        person.append(("Core", f"{chr(0x25C6)} {core}"))   # DVPet digicore badge
    return [
        ("STATUS", status),
        ("POWER", power),
        ("CONDITION", [
            ("Hunger", f"{pet.hunger}/4"), ("Energy", f"{int(pet.energy)}/{pet.max_energy}"),
            ("Weight", f"{pet.weight}g"),
            # (the injury fragment left: is_injured() is hard False since the
            # injury system was removed 2026-07-16 -- sick is the one ailment)
            ("Ailing", "sick" if pet.sick else "no"),
            # (no nutrition row: the macro system was REMOVED 2026-07-16 --
            # its fields are frozen starter values; cards only show LIVE data)
            ("Poop", str(pet.poop)),
            ("Care", f"{pet.care_mistakes} this stage"),
            ("Disturb", str(pet.disturb)),
        ]),
        ("HOME", [
            # the household page (data-page polish 2026-07-17): the scene
            # honors the E pick; the staple fixtures show their stock
            ("Scene", _bgs.name(getattr(pet, "bg_pick", "")
                                or _bgs.scene_for_egg(getattr(pet, "egg_type", 0)))),
            ("Egg", _egg.hatch_name(getattr(pet, "egg_type", 0))),
            ("Toilet", f"{pet.inventory.get('i:82', 0)} flushes"),
            ("Potty", f"{pet.inventory.get('i:83', 0)} uses"),
            ("Futon", f"{pet.inventory.get('i:81', 0)} nights"),
            ("Trained", "yes — goes alone" if pet.is_toilet_trained()
             else f"{pet.toilet_trained}/1 toilet uses"),
            ("Helper", "hired" if getattr(pet, "auto_care", False) else "off"),
        ]),
        ("PERSON", person),
        ("TROPHIES", _trophy_rows(pet)),
        ("LEGACY", _legacy_rows()),
        ("EVOLVES", _evo_rows(pet)),
    ]


