"""Evolution lines — the LINES_SPEC.md engine (arc 1).

An egg is a line: a curated, DM20-shaped subtree of the corpus. A pet hatched
from a line egg evolves ONLY inside its line, judged by first-match bracket
rules instead of the corpus fulfilled-score engine. Rules read the per-stage
care counters (care_mistakes / stage_trainings / overeat / stage_battles) and
the rolling battle_log, so every evolution is a legible verdict on this
stage's care.

Rule grammar (LINES_SPEC §2) — comma = AND, `|` = OR, first matching row wins:
    CM 0-2 | CM 3+      care mistakes bracket        TR 5-15   trainings
    OF 3+               overfeeds                    BTL 15+   battles this stage
    WIN 12/15           >=12 wins in last 15         LV 5-6    DMX level (battle exp,
                                                     humulos table; fix 2026-07-17)
    KO6 5+              Mega-class foes beaten       AREA <n>  n+1 raid bosses felled
                                                     (was "map n cleared"; the raid
                                                     re-gate, BASIC VPET 2026-07-16)
    TIME                no requirement — the stage timer alone
"""
from __future__ import annotations
import csv
import os
from functools import lru_cache

from . import data

_DATA = os.path.join(os.path.dirname(__file__), "data")

# stages whose corpus rank counts as "Mega-class" for the KO6 gate (DMX: Stage VI)
_KO6_MIN_STAGE = "Ultimate"


def _bracket(arg):
    """'0-2' -> (0, 2); '3+' -> (3, None); '7' -> (7, 7)."""
    arg = arg.strip()
    if arg.endswith("+"):
        return int(arg[:-1]), None
    if "-" in arg:
        lo, hi = arg.split("-", 1)
        return int(lo), int(hi)
    v = int(arg)
    return v, v


def parse_rule(text):
    """Rule text -> list of OR-alternatives, each a list of (kind, a, b) atoms.
    'TIME' (or blank) parses to one unconstrained alternative."""
    text = (text or "").strip()
    alts = []
    for alt in text.split("|"):
        atoms = []
        for part in alt.split(","):
            part = part.strip()
            if not part or part.upper() == "TIME":
                continue
            kind, _, arg = part.partition(" ")
            kind, arg = kind.upper(), arg.strip()
            if kind == "WIN":
                k, n = arg.split("/", 1)
                atoms.append(("win", int(k), int(n)))
            elif kind == "JOGRESS":
                # a jogress DOOR (LINES_SPEC §6): arg = the exact partner dex,
                # or a Pendulum attribute spec ("Data/Virus") -- any same-stage
                # partner with a listed attribute resonates (pen20 manual).
                # Never fires on the stage timer -- the lobby fusion opens it.
                if arg.isdigit():
                    atoms.append(("jogress", int(arg), None))
                else:
                    attrs = tuple(a.strip() for a in arg.split("/") if a.strip())
                    if not attrs or any(a not in ("Vaccine", "Data", "Virus",
                                                  "None") for a in attrs):
                        raise ValueError(f"bad JOGRESS partner: {part!r}")
                    atoms.append(("jogress", attrs, None))
            elif kind == "AREA":
                if not arg:
                    raise ValueError(f"AREA atom needs a map: {part!r}")
                atoms.append(("area", arg, None))
            elif kind in ("CM", "TR", "OF", "BTL", "LV", "KO6"):
                lo, hi = _bracket(arg)
                atoms.append((kind.lower(), lo, hi))
            else:
                raise ValueError(f"unknown rule atom: {part!r}")
        alts.append(atoms)
    return alts


@lru_cache(maxsize=1)
def load_lines():
    """lines.csv -> {line_id: {"root": dex, "members": {dex: row},
    "children": {parent_dex: [row, ...] in CSV (first-match) order}}}.
    A row is {"num", "stage", "parents", "rule" (parsed), "rule_text", "bedtime"}."""
    out = {}
    with open(os.path.join(_DATA, "lines.csv"), newline="") as fh:
        for raw in csv.DictReader(fh):
            lid = raw["LineID"].strip()
            line = out.setdefault(lid, {"root": None, "members": {}, "children": {}})
            num = int(raw["DexNum"])
            parents = [p.strip() for p in raw["Parents"].split(";") if p.strip()]
            rule = parse_rule(raw["Rule"])
            row = {"num": num, "stage": raw["Stage"].strip(),
                   "rule": rule, "rule_text": raw["Rule"].strip(),
                   "bedtime": raw["Bedtime"].strip(),
                   "parents": [int(p) for p in parents if p != "egg"],
                   # jogress door: the exact partner dex, or None for a
                   # normal timed-care row (LINES_SPEC §6)
                   "jogress": next((a for alt in rule for k, a, _ in alt
                                    if k == "jogress"), None)}
            mem = line["members"].get(num)
            if mem is None:
                line["members"][num] = row
            else:
                # a dual-road target (ver1 Devimon: Agumon needs TR 0-15,
                # Betamon TR 16+ -- DM20 canon) keeps ONE row per parent so
                # each road judges by its own rule; members unions the
                # parentage so the curation invariants see every edge
                mem["parents"] = sorted(set(mem["parents"]) | set(row["parents"]))
            if "egg" in parents:
                line["root"] = num
            for p in row["parents"]:
                line["children"].setdefault(p, []).append(row)
    return out


def line_for_hatch(dex):
    """The line whose root Fresh form is `dex` ('' = no line: corpus engine)."""
    for lid, line in load_lines().items():
        if line["root"] == dex:
            return lid
    return ""


def canonical_root(dex):
    """(root_dex, line_id) a hatching `dex` should become.  A dex that IS a
    root maps to itself; a duplicate twin (the corpus keeps 2-3 dexes per Baby
    name; the mystery-egg pools hatch the sub-1410 twins) maps to the root
    sharing its NAME.  16 Baby names root SEVERAL lines (four Petitmon roots:
    the classic petitmon line plus the slayerdra/breakdra/draco device charts),
    so a name-hatched twin always becomes the CLASSIC line -- the lowest root
    dex (141x < 16xx by construction) -- never csv-order luck; the device
    lines are entered only through their own eggs.  (None, '') when no line
    claims the name -- with every egg curated (arc 5) that means legacy data
    only."""
    lid = line_for_hatch(dex)
    if lid:
        return dex, lid
    _, by_num = data.load_sprites()
    rec = by_num.get(dex)
    if rec:
        owners = [(line["root"], lid) for lid, line in load_lines().items()
                  if (by_num.get(line["root"]) or {}).get("name") == rec["name"]]
        if owners:
            return min(owners)
    return None, ""


def active(pet):
    """This pet evolves by line rules: hatched from a line egg AND still inside
    the line (a jogress/fusion that leaves the subtree falls back to the corpus
    engine — defensive until arc 4 formalizes specials for lines)."""
    line = load_lines().get(getattr(pet, "line_id", ""))
    return bool(line) and pet.num in line["members"]


def bedtime(pet):
    """The form's fixed bedtime 'HH:MM' ('' if not a line form)."""
    line = load_lines().get(getattr(pet, "line_id", ""))
    row = line["members"].get(pet.num) if line else None
    return row["bedtime"] if row else ""


def bedtime_minutes(pet):
    """The bedtime as a minute-of-day (0..1439), or None for non-line forms.
    '24:00' wraps to 0 (a midnight sleeper like Devimon)."""
    bt = bedtime(pet)
    if not bt:
        return None
    h, m = bt.split(":", 1)
    return (int(h) % 24) * 60 + int(m)


# DMX levels, humulos canon (the manual's table verbatim, 2026-07-17 --
# the old DVPet getLevel read powers + trained HP, both of which starved
# when the 0.5 battle/training landed, silently walling every LV gate):
# cumulative experience thresholds for levels 1..10, and each stage's cap.
DMX_EXP_LEVELS = (0, 50, 150, 500, 800, 1000, 1500, 2000, 3000, 5000)
DMX_LEVEL_CAP = {"Fresh": 1, "InTraining": 2, "Rookie": 4,
                 "Champion": 6, "Ultimate": 8, "Mega": 10}


def _pet_level(pet):
    """The DMX level: battle experience vs the canon thresholds, capped by
    the CURRENT stage (Rookie 4 / Champion 6 / Ultimate 8 / Mega 10) -- a
    Mega-target row gating LV 8 reads the Ultimate PARENT's cap, and the
    LV 9-10 rows are the Mega X-roads."""
    e = getattr(pet, "exp", 0)
    lvl = sum(1 for t in DMX_EXP_LEVELS if e >= t)
    return min(lvl, DMX_LEVEL_CAP.get(getattr(pet, "stage", "Mega"), 10))


def _actual(pet, kind):
    return {"cm": pet.care_mistakes, "tr": pet.stage_trainings,
            "of": pet.overeat, "btl": pet.stage_battles,
            "lv": _pet_level(pet), "ko6": pet.mega_kills}[kind]


def _felled_raids():
    from . import persistence          # late: persistence imports pet at module top
    try:
        return int(persistence.get_progress().get("raids", 0) or 0)
    except Exception:
        return 0


def _atom_met(pet, atom):
    kind, a, b = atom
    if kind == "jogress":
        return False       # a door, not a timer rule: only the lobby fusion opens it
    if kind == "win":
        return sum(pet.battle_log[-b:]) >= a
    if kind == "area":
        # the raid re-gate (BASIC VPET 2026-07-16): adventure left with the
        # world layer, so an AREA-N atom means N+1 felled community raid
        # bosses now -- the same map->milestone conversion the eggUnlock
        # MapComplete rows took (Alphamon's AREA 3 = 4 broken bosses)
        n = int(a) if str(a).lstrip("-").isdigit() else 0
        return _felled_raids() >= n + 1
    v = _actual(pet, kind)
    return v >= a and (b is None or v <= b)


def check_rule(pet, rule):
    """True if ANY alternative has every atom met (an empty alternative — the
    TIME rule — is always met)."""
    return any(all(_atom_met(pet, atom) for atom in alt) for alt in rule)


def jogress_declared(pet):
    """Line-declared jogress doors from the pet's current form:
    [(target_num, partner_dex)] — the DM20 capstones (Omnimon Alter-S,
    RustTyrannomon).  The partner is EXACT; jogress.options feeds these into
    the lobby's shared-fusion-name channel (LINES_SPEC §6)."""
    line = load_lines().get(getattr(pet, "line_id", ""))
    if not line or pet.num not in line["members"]:
        return []
    return [(row["num"], row["jogress"])
            for row in line["children"].get(pet.num, [])
            if row["jogress"] is not None]


def companion_wanted(num):
    """True when some line's exact-partner jogress door names `num` as the
    REQUIRED companion (canon one-sided doors -- Jesmon GX needs a Jesmon X
    that never evolves itself; jogress canon audit 2026-07-17)."""
    for line in load_lines().values():
        for rows in line["children"].values():
            for row in rows:
                if row["jogress"] == num:
                    return True
    return False


def select_line(pet):
    """First-match evolution: the ordered child rows of the pet's current form,
    first row whose rule passes. None = stay (keep re-checking: counters can
    still earn a later row — the DM20 Perfect battle gate works exactly so)."""
    line = load_lines().get(pet.line_id)
    if not line:
        return None
    for row in line["children"].get(pet.num, []):
        if check_rule(pet, row["rule"]):
            return row["num"]
    return None


@lru_cache(maxsize=1)
def hatchable_roots():
    """Every root dex some egg can hatch today.  The dormant legacy charts
    (the classic 141x lines the family eggs used to borrow, and ver6) still
    LOAD -- a pet mid-journey keeps its tree -- but they aren't hatched
    anymore (test_old_wrong_lines_stay_dormant_for_existing_pets), so a
    re-anchor must never bind a NEW pet into one (consistency audit
    2026-07-21: 37 shared forms tie-broke into unhatchable charts)."""
    from . import egg as egg_mod       # late: egg has no lines dependency
    return {t for i in range(egg_mod.count()) for t in egg_mod.hatch_targets(i)}


def adopt_line(pet, prev=None):
    """Re-anchor the pet to a line whose chart contains its CURRENT form -- a
    jogress/mode fusion keeps the pet in the line system whenever ANY line
    claims the target (its own line preferred).  Shared nodes sit in several
    charts (Babydmon 955 is in slayerdra, breakdra AND draco), so among
    foreign claimants a line containing the road actually travelled -- `prev`,
    the dex worn BEFORE the special evolution, AND the current form -- is the
    pet's true chart; then HATCHABLE lines outrank the dormant legacy charts
    (hatchable_roots: never capture a new pet into a line no egg hatches);
    remaining ties break on the lowest root so the binding is data-stable,
    never csv-order luck.  '' = truly off-chart: the legacy corpus engine
    takes over, as before."""
    cur = load_lines().get(getattr(pet, "line_id", ""))
    if cur and pet.num in cur["members"]:
        return pet.line_id
    owners = [(lid, line) for lid, line in load_lines().items()
              if pet.num in line["members"]]
    if prev is not None:
        travelled = [o for o in owners if prev in o[1]["members"]]
        if travelled:
            owners = travelled
    live = [o for o in owners if o[1]["root"] in hatchable_roots()]
    if live:
        owners = live
    if owners:
        lid = min(owners, key=lambda o: o[1]["root"])[0]
        pet.line_id = lid
        return lid
    pet.line_id = ""
    return ""


def win_gate_progress(pet):
    """(now, need, window) for the pet's nearest WIN gate, or None -- the cup
    screen shows how tournament fights feed the evolution window."""
    line = load_lines().get(getattr(pet, "line_id", ""))
    if not line or pet.num not in line["members"]:
        return None
    for row in line["children"].get(pet.num, []):
        for alt in row["rule"]:
            for kind, a, b in alt:
                if kind == "win":
                    return (sum(pet.battle_log[-b:]), a, b)
    return None


# ---- data-book presentation (digicorescreen) --------------------------------

_TXT = {"cm": "care slips", "tr": "trainings", "of": "overfeeds",
        "btl": "battles this stage", "lv": "level", "ko6": "Mega-class felled"}

# what fills a WIN window (and what doesn't): drills feed TR gates, lobby
# duels feed nothing (L17), and a raid attempt writes NOTHING on the pet
# (RaidBout, clone rule) -- "road" = the adventure's wilds + zone bosses.
# <= 35 chars -- the digicore LCD row clip.
WIN_FEED_NOTE = "fed by cup & road, not pvp/raids"


def _atom_row(pet, atom):
    kind, a, b = atom
    if kind == "win":
        now = sum(pet.battle_log[-b:])
        # "training isnt filling the evo requirements in my metal greymon,
        # unless thats supposed to be battles? is it training or battles,
        # because i dont think its filling either way" (Joel, 2026-07-21).
        # VERDICT MATCHES -- the counters are canon: checkEvolReq has no
        # trainings gate (drills feed TR gates + effort), and the L17
        # ruling keeps lobby duels progression-neutral.  The ROW was the
        # gap: it never said WHICH battles fill the window, right after a
        # stage whose gate WAS trainings (Agumon->Greymon TR 16+).  The
        # answer lives in a WIN_FEED_NOTE sub-row (requirement_report):
        # "local bouts" inlined here overflowed the LCD's 35-char row clip
        # and amputated the (now ...) counter (Joel's screenshot, same day).
        return _atom_met(pet, atom), f"wins {a} of last {b}  (now {now}/{min(len(pet.battle_log), b)})"
    if kind == "jogress":
        if isinstance(a, tuple):                         # Pendulum attribute door
            spec = "/".join("Free" if x == "None" else x for x in a)
            return None, f"jogress with a {spec} partner"
        _, by_num = data.load_sprites()
        pname = (by_num.get(a) or {}).get("name", f"#{a}")
        return None, f"jogress with {pname} (lobby)"     # informational: a door, not a counter
    if kind == "area":
        # speak the raid re-gate, not the departed adventure maps ("clear
        # map N" survived the re-gate; the gate is N+1 felled raid bosses)
        n = int(a) if str(a).lstrip("-").isdigit() else 0
        return _atom_met(pet, atom), (f"{n + 1} raid boss{'es' if n else ''} felled"
                                      f"  (now {_felled_raids()})")
    span = f"{a}+" if b is None else (f"{a}" if a == b else f"{a}-{b}")
    return _atom_met(pet, atom), f"{_TXT[kind]} {span}  (now {_actual(pet, kind)})"


def requirement_report(pet, num):
    """The bracket checklist for one line target, same row shape as
    evolution.requirement_report: (met, text). With OR alternatives, shows the
    closest one (fewest unmet atoms)."""
    line = load_lines().get(pet.line_id)
    row = None
    if line:
        # a dual-road target has one row per parent -- report the rule for
        # THIS pet's road (its child row), not whichever row loaded first
        row = next((r for r in line["children"].get(pet.num, [])
                    if r["num"] == num), None) or line["members"].get(num)
    if row is None:
        return [(False, "not in this line")]
    best, best_alt, best_unmet = None, None, None
    for alt in row["rule"]:
        rows = [_atom_row(pet, atom) for atom in alt]
        unmet = sum(1 for met, _ in rows if not met)
        if best is None or unmet < best_unmet:
            best, best_alt, best_unmet = rows, alt, unmet
    if best and any(kind == "win" for kind, _a, _b in best_alt):
        # the WHICH-battles answer rides under the WIN row as a dim
        # informational line (met=None, the jogress-door shape) -- inlining
        # it in the row clipped the counter off the 35-char LCD (Joel's
        # screenshot 2026-07-21, the "is it training or battles" report)
        best = best + [(None, WIN_FEED_NOTE)]
    return best or [(True, "time alone — the clock decides")]


def evo_rows(pet):
    """(num, name, ready, unmet) per child of the current form, in chart
    (first-match) order — the line data book page."""
    line = load_lines().get(pet.line_id)
    if not line:
        return []
    _, by_num = data.load_sprites()
    out = []
    for row in line["children"].get(pet.num, []):
        rec = by_num.get(row["num"])
        report = requirement_report(pet, row["num"])
        unmet = sum(1 for met, _ in report if met is False)
        out.append((row["num"], rec["name"] if rec else f"#{row['num']}",
                    check_rule(pet, row["rule"]), unmet))
    return out
