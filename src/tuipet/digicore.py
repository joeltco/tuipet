"""The DigiCore DATA MODEL -- every page, row and core computation
(Joel 2026-07-17: "can we modularize digicore now. polish it up").

digicorescreen.py renders and routes keys; THIS module decides what the
core says.  The statusbox law applies here too: a row may only show LIVE
data. Disposition wears its own name, and Ailing reads live sickness/injury
(DigiCore audit 2026-10-14).
"""
from __future__ import annotations
from . import data
from . import petbase as _petbase
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


def has_next(pet):
    """Is ANY onward evolution waiting?  Line pets read their line chart;
    corpus/legacy pets read the corpus graph.  (Digicore audit 2026-07-18:
    core_number checked the corpus alone, so 22 line parents whose onward
    rows are line-only — the jogress/X-road Megas — showed the LIFE meter
    while the same page's Meter row said an evolution neared.)"""
    if lines.active(pet):
        return bool(lines.evo_rows(pet))
    return bool(data.load_evolutions().get(pet.num))


def has_timed_next(pet):
    """Can the growth TIMER evolve this pet?  Line pets: their chart rows.
    Off-chart pets: a corpus target the timer may select -- not an item door,
    not a Mode/Death/Xros/Fusion special, not an Induced X-form without the
    antibody.  (VB audit 2026-10-14: Blitzmon/Ranamon/Arbormon/Mercuremon
    evolve only by their Beast Spirit and antibody-less Bolgmon only by Mode
    or X; the core counted a growth window that never comes.)"""
    if lines.active(pet):
        return bool(lines.evo_rows(pet))
    reqs = data.load_requirements()
    _, by_num = data.load_sprites()
    for t in data.load_evolutions().get(pet.num, []):
        rec, req = by_num.get(t), reqs.get(t, {})
        if rec is None or t == pet.num or rec["stage"] == pet.stage:
            continue
        if req.get("evol_item", -1) != -1:
            continue
        if req.get("special", "None") in ("Mode", "Death", "Xros", "Fusion"):
            continue
        if req.get("xantibody", "None") == "Induced" \
                and getattr(pet, "x_antibody", "None") == "None":
            continue
        return True
    return False


def growth_clock(pet):
    """The existing hatch/growth window, or None for an untimed final form."""
    # DigiCore audit 2026-10-14: Godzilla has a finite Mega window; other
    # Megas' sentinel is not a timer. Read the game's clock, never change it.
    if pet.num == -1:
        return pet.EGG_DURATION
    growth = pet._evolve_after()
    onward = has_timed_next(pet) or bool(evolution.divergence_options(pet))
    return growth if growth < 9e8 and onward else None


def growth_pending(pet):
    # DigiCore audit 2026-10-14: cracking is still a hatch, not elderhood.
    if pet.num == -1:
        return True
    growth = growth_clock(pet)
    return growth is not None and pet.stage_seconds < growth


def core_number(pet):
    """setupDigicore's meter: an evolution countdown while a normal evolution is
    pending, otherwise an AGE meter counting up toward the elder line (the
    lifespan denominator left with the clock -- DSprite mortality 2026-07-22:
    age is what kills now, so age is what the core counts).  Floors at 1."""
    base = DIGICORE_BASE_RATE
    growth = growth_clock(pet)
    if growth_pending(pet):
        denom = round(growth / base) or 1
        n = int(base - pet.stage_seconds / denom)
    else:
        from .petbase import AGE_DAY, GERIATRIC_AGE_DAYS
        denom = round(GERIATRIC_AGE_DAYS * AGE_DAY / base) or 1
        n = int(pet.age_seconds / denom)
    return max(1, n)


def evolution_name(num, name):
    """Use the album's existing reveal rule for every book route."""
    from . import persistence
    # DigiCore audit 2026-10-14: line rows must conceal the same hidden forms.
    if data.load_requirements().get(num, {}).get("hidden_evo") and not persistence.album_seen(num):
        return "???"
    return name


def route_tag(pet, num):
    """External doors are not zero unmet care gates."""
    # DigiCore audit 2026-10-14: retain the routes, describe their trigger.
    if pet.num == -1:
        return "hatch"
    if lines.active(pet):
        line = lines.load_lines()[pet.line_id]
        row = next((r for r in line["children"].get(pet.num, []) if r["num"] == num), None)
        if row and row["jogress"] is not None:
            return "lobby"
    return None


def hatch_report(pet):
    left = max(0, pet.EGG_DURATION - pet.stage_seconds)
    return [(None, f"incubation: {_mins(left)} remaining"),
            (None, "hatches when incubation ends")]


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
    options = evolution.divergence_options(pet)
    if options:
        # DNA audit 2026-10-14: a stable example, not a rolled promise.
        return options[0]
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


def _divergence_row(pet):
    """The first stable armed option, or None; retained for readout callers."""
    options = evolution.divergence_options(pet)
    if not options:
        return None
    return _divergence_rows(pet)[0]


def _divergence_rows(pet):
    """All armed road options, in stable order with the album's name mask."""
    _, by = data.load_sprites()
    from tuipet import persistence as _p
    reqs = data.load_requirements()
    rows = []
    for num in evolution.divergence_options(pet):
        name = by.get(num, {}).get("name", "?")
        if reqs.get(num, {}).get("hidden_evo") and not _p.album_seen(num):
            name = "???"
        rows.append((num, name, True, 0))
    return rows


def divergence_report(pet):
    """The armed steer's checklist (met, text) rows -- the EVOLVES detail
    for the divergence row.  lines.requirement_report would answer "not in
    this line" (true, and exactly the point): what fires this jump is the
    charge, so the sheet reports the charge."""
    field = pet.highest_dna()
    need = evolution.DIVERGE_NEED.get(pet.stage, 0)
    have = pet.dna_applied.get(field, 0)
    # DNA audit 2026-10-14: the Field is armed, not a particular random form.
    return [(True, f"{data.pretty_field(field)} {have}/{need} — ARMED"),
            (None, "the steer overrides the chart"),
            (None, "charges clear at every evolution"),
            (None, "road option; final pick at growth")]


def _evo_rows(pet):
    """The evolution line for the data book: (num, name, ready, unmet) per
    candidate, closest-first -- with all armed road options at the top.
    DNA audit 2026-10-14: growth picks the final destination, not this page.
    unmet counts the failing checklist gates (evolution.requirement_report)
    -- the page shows it as distance-to-go.

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
    armed = _divergence_rows(pet)
    armed_nums = {r[0] for r in armed}
    if lines.active(pet):
        # line pets: the line's own chart rows, in first-match order (the order
        # IS the information -- earlier rows win ties), with live unmet counts
        rows = [(n, evolution_name(n, name), ready, unmet)
                for n, name, ready, unmet in lines.evo_rows(pet)]
        if armed:
            # the steer tops the chart; the line rows stay below -- they
            # come BACK if another Field catches up and breaks the strict max
            return armed + [r for r in (rows or []) if r[0] not in armed_nums]
        return rows or "(final form)"
    try:
        # ready first, then HIGHEST fulfilled -- ascending put the form the
        # engine is LEAST likely to pick in the top "closest" row, against
        # the silhouette on the same screen (gameplay audit 2026-07-19)
        cands = sorted(evolution.candidates(pet), key=lambda c: (not c[2], -c[3]))
    except Exception:
        cands = []
    if not cands:
        return armed if armed else "(final form)"
    rows = []
    from tuipet import persistence as _p
    reqs = data.load_requirements()
    # DigiCore audit 2026-10-14: the renderer windows eight, not the data.
    for num, name, ready, dev in cands:
        unmet = sum(1 for met, _ in evolution.requirement_report(pet, num) if met is False)
        # HiddenEvolution (digicore audit 2026-07-06): canon's tree conceals
        # 130 flagged forms until FIRST reached -- the cross-generation album
        # is the reveal state (Evolution.setUnlocked).  The slot still shows
        # (position + distance-to-go intact), only the name is masked.
        if reqs.get(num, {}).get("hidden_evo") and not _p.album_seen(num):
            name = "???"
        rows.append((num, name, ready, unmet))
    if armed:
        rows = armed + [r for r in rows if r[0] not in armed_nums]
    return rows


def _trophy_rows(pet):
    """Inherited championships and distinct career cups, with their win days."""
    from tuipet import tournament as _t
    from tuipet import persistence as _p
    # DigiCore audit 2026-10-14: wins are inherited; twelve stars hid totals.
    rows = [("Wins", f"{pet.trophies} across generations")]
    try:
        career = len(_p.get_progress().get("tourneys", ()) or ())
    except Exception:
        career = 0
    rows.append(("Career", f"{career} distinct cups"))
    # the collection long game ("ultimate v-pet" arc 2026-07-07): every raised
    # form lands in the cross-generation album; divergence/jogress/eggs are
    # the roads to the rest of the corpus
    try:
        seen = len(_p.get_progress().get("album", ()) or ())
    except Exception:
        seen = 0
    # the denominator must count what the numerator can actually REACH: the dex
    # carries 329 duplicate rows (one species can sit on several device pages --
    # five Petitmon, seven Omnimon MM), and album_add stores the CANONICAL num,
    # so `seen` tops out at the canonical count.  Comparing it to the raw row
    # count showed 1218/1547: an album that could never be completed, however
    # perfectly you played (roster audit 2026-07-14, Joel: "we have duplicate
    # mons??").  album_roster() = that canonical set, shared with the album
    # screen's pages (the book this count fronts for).
    total = len(data.album_roster())
    rows.append(("Album", f"{seen}/{total} discovered"))
    # DigiCore audit 2026-10-14: raids share map gates with live adventure.
    try:
        felled = int(_p.get_progress().get("raids", 0) or 0)
    except Exception:
        felled = 0
    rows.append(("Raids", f"{felled} raid bosses felled"))
    won = sorted((getattr(pet, "trophies_won", None) or {}).items())
    for tid, season in won[:4]:                     # keep the page at 9 rows max
        # trophy_name speaks every id space -- town cups included
        # the stored label is the WORLD day (the fast clock, not real days --
        # DigiCore call #10 = A, 2026-10-15); saves keep "day N", shown as such
        shown = str(season)
        if shown.startswith("day "):
            shown = "world " + shown
        rows.append((_t.trophy_name(tid)[:12], shown))   # (was 5: Maps row joined)
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
        # _mins: the book's own REAL-time formatter, same unit as the STATUS
        # Age row and the memorial epitaph (age_seconds is real seconds;
        # petbase.AGE_DAY).  A 1440-based reading inflates every headstone 60x.
        age = _mins(float(r.get("age", 0)))
        fate = "†" if r.get("dead") else ""         # fell vs retired to the next egg
        val = f"{str(r.get('name', '?'))[:12]} {r.get('stage', '?')} {age}{fate}"
        rows.append((f"gen {r.get('gen', '?')}", val[:30]))
    if len(elders) > 8:
        rows.append(("…", f"+{len(elders) - 8} more remembered"))
    return rows


def build_pages(pet):
    appetite = ["picky", "normal", "greedy"][pet._glutton() + 1]
    temperament = ["mellow", "steady", "restless"][pet._restless() + 1]
    disp = ["sour", "even", "sunny"][pet._disposition() + 1]
    status = [
        ("Name", pet.name or "—"),
        # an egg has no dex number yet -- "#-1" leaked the internal sentinel
        # (egg-stage audit 2026-07-05)
        ("No.", "—" if pet.num < 0 else f"#{pet.num}"), ("Stage", pet.stage),
        # an untyped Digimon is "Free", the franchise's word (call #8 = A)
        ("Attrib", "Free" if pet.attribute in ("", "None") else pet.attribute), ("Field", data.pretty_field(pet.field) or "—"),
        ("Gen", str(pet.generation)),
        # (the "Life Xd left" row left with the lifespan clock -- DSprite
        # mortality 2026-07-22: nothing counts down anymore, Age counts up)
        ("Age", _mins(pet.age_seconds)),
        ("Battles", f"{pet.wins}W / {pet.battles} · {pet.bits}b"),
    ]
    if getattr(pet, "line_id", "") == "godzilla":
        # the device's G-Cell meter (Godzilla line): filled cells per colour
        # -- blue 14, yellow 10, red 20 -- the units the evolution routes
        # count in.  Only this line reads it, so only this line shows it.
        b, y, r = _petbase.gcell_cells(getattr(pet, "gcell", 0))
        # + the raw points the cells fold from (DigiCore call #8 = A, 2026-10-15)
        status.append(("G-Cell", f"B{b}/14 Y{y}/10 R{r}/20 {int(getattr(pet, 'gcell', 0) or 0)}pt"
                                 + (" · frag" if getattr(pet, "gcell_fragment", False) else "")))
    # the POWER page is the BATTLE ledger (framing fixed, gameplay polish
    # #17 2026-07-22): the Va/D/Vi attribute powers stopped gating growth
    # when those checks left evolution.check() -- lines never read them
    # either.  What still feeds evolution here is Level (LV gates), KO6 and
    # Effort; the attribute trio also ranks corpus candidates (DigiCore
    # audit 2026-10-14), while Form and Training feed the FIGHT
    # (hit_chance / roll_damage).  The weight/bits/battles bookkeeping
    # moved beside its kin (weight -> CONDITION; battles/bits -> STATUS;
    # trophies have their own page).
    power = [
        ("Vaccine", str(pet.vaccine)), ("Data", str(pet.data_power)),
        ("Virus", str(pet.virus)), ("Effort", f"{pet.strength}/4"),
        # labels say what they mean (DigiCore call #8 = A, 2026-10-15): the
        # hit FORM is the attack style; Level shows the cap this stage allows
        ("Attack", getattr(pet, "saved_hit_type", "normal") + " form"),
        ("Level", f"{lines._pet_level(pet)}/{lines.DMX_LEVEL_CAP.get(pet.stage, 10)}"
                  f" ({getattr(pet, 'exp', 0)} exp)"),
        # both training terms of the hit formula on one row (Joel
        # 2026-07-23 "is there a stat somewhere i can see that shows
        # this?"): lifetime (the +20% term, never resets) · this stage
        # (the +10% term AND the TR evolution gate; resets on evolve) --
        # stage_trainings was live everywhere but visible nowhere.
        # Named TRAINING, not "Drills", since 2026-07-25: a bout feeds
        # both counters now (+2), so a row that says drills would be
        # naming one of its two sources (the liveness law).
        ("Training", f"{getattr(pet, 'total_trainings', 0)}"
                     f" · {getattr(pet, 'stage_trainings', 0)} this stage"),
        ("KO6", f"{pet.mega_kills} Mega felled"),
    ]
    # (the X-Anti row left: CORE's X-State already shows it -- call #10 = A)
    # (the Likes/Dislikes clock rows left with the timeRanks system --
    # BASIC VPET 2026-07-17)
    person = [
        # ("Spirit" was the dead spirit system's word -- the row shows the
        # DISPOSITION trait, which is alive; label polish 2026-07-17)
        ("Type", pet.personality()), ("Nature", disp),
        ("Appetite", appetite), ("Pace", temperament),
        # the manners gauge, LIVE again (canon restoration B, 2026-07-23)
        ("Manners", f"{getattr(pet, 'obedience', 0)}/{_petbase.MAX_OBEDIENCE}"),
    ]
    if getattr(pet, "rival_name", ""):
        # the named rival's head-to-head (Joel 2026-07-26) — appears once
        # the first challenge mints the tamer, dies with the generation
        person.append(("Rival",
                       f"{pet.rival_name} · {pet.rival_wins}W-{pet.rival_losses}L"))
    core = data.load_digicore_icons().get(pet.num)
    if core:
        person.append(("Badge", f"{chr(0x25C6)} {core}"))   # art-catalog badge name: flavor, no mechanic (call #9 = A)
    return [
        ("STATUS", status),
        ("POWER", power),
        ("CONDITION", [
            ("Fullness", f"{pet.hunger}/4"), ("Energy", f"{int(pet.energy)}/{pet.max_energy}"),
            ("Weight", f"{pet.weight}g"),
            # two ailments, two words: INJURY returned with the canon
            # restoration (2026-07-23) but this row kept the removal-era
            # sick-only read -- the data book could never say "hurt".
            # Sick outranks hurt, same as the feed cursor (audit 2026-07-25)
            ("Ailing", "sick" if pet.sick else
             ("hurt" if pet.is_injured() else "no")),
            # (no nutrition row: the macro system was REMOVED 2026-07-16 --
            # its fields are frozen starter values; cards only show LIVE data)
            ("Poop", str(pet.poop)),
            ("Care", f"{pet.care_mistakes} this stage"),
            ("Disturb", f"{pet.disturb} this stage"),
        ]),
        ("HOME", [
            # the household page (data-page polish 2026-07-17): the scene
            # honors the E pick.  (The staple-fixture stock rows left with
            # the props: strict-DSprite items, 2026-07-17.)
            ("Scene", _bgs.name(getattr(pet, "bg_pick", "")
                                or _bgs.scene_for_egg(getattr(pet, "egg_type", 0)))),
            ("Egg", _egg.hatch_name(getattr(pet, "egg_type", 0))),
            ("Helper", "hired" if getattr(pet, "auto_care", False) else "off"),
        ]),
        ("PERSON", person),
        ("TROPHIES", _trophy_rows(pet)),
        ("LEGACY", _legacy_rows()),
        ("EVOLVES", _evo_rows(pet)),
    ]


