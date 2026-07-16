"""DigiCore — DVPet's EvolutionState page + tuipet's paged data book.

The CORE page is the canon Digicore (SpriteAnim setupDigicore): the field-
flavoured core backdrop (ViewUtil.getDigicoreBackground picks it by the pet's
HIGHEST DNA field, falling back to its own), the core badge (a special core
from digicoreMenuConfig.csv, else the X-antibody state badge), and the core
NUMBER — with a pending evolution it counts DOWN from DigicoreBaseRate 14 as
the growth period elapses; past growth (or a final form) it counts UP through
the lifespan.  Pressing the core plays the silhouette teaser
(EvolSilhouetteTransition): the next natural evolution as a blacked-out shape.
The data-book pages after it are tuipet's own readout (kept adaptation).
"""
from __future__ import annotations
from . import data
from . import grid, evolution, lines  # noqa: F401  (pet methods drive the data)
from .render import render_scene

from .theme import LCD_ON, LCD_BG, INK, INK_B, DIM, SIL_DAY, SIL_NIGHT, VOID  # noqa: F401  (theme.apply propagation)
from . import menu

DIGICORE_BASE_RATE = 14            # DigicoreBaseRate (config.csv col 1)
SCENE_ROWS = 12                    # the core/teaser pages own the WHOLE arena now --
#                                    Joel 2026-07-05: the 8-row band crammed a 16px mon
#                                    against the chrome; scene-only + strip() instead
EXPAND_T = 8                       # digicoreExpand: the badge zooms in (canon beats 6-14)
MON_T = 10                         # the gaze opens ON the current mon before the core turns
BACK_T = 6                         # evolSilhouetteBack: the dark blink on the way out
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
    if x == "Temporary":
        return "core_xtemp"
    if x != "None":
        return "core_xreq"                      # Permanent / X-Program
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
    """The trophy room: this life's cups (label + the season they fell) topped
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
    # map conquest was tracked but shown NOWHERE (sweep 2026-07-14): it gated
    # continents silently while Album and cups got a shelf
    try:
        cleared = len(_p.get_progress().get("maps", ()) or ())
    except Exception:
        cleared = 0
    rows.append(("Maps", f"{cleared}/{len(data.load_maps())} regions cleared"))
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
    h = pet.habitat_obj()
    aff = pet._affinity()
    fit = "thrives" if aff > 0 else ("suffers" if aff < 0 else "neutral")
    rem = pet.lifespan - pet.age_seconds
    appetite = ["picky", "normal", "greedy"][pet._glutton() + 1]
    temperament = ["mellow", "steady", "restless"][pet._restless() + 1]
    disp = ["sour", "even", "sunny"][pet._disposition() + 1]
    fav, dis = pet.favorite_time(), pet.disliked_time()
    status = [
        ("Name", pet.name),
        # an egg has no dex number yet -- "#-1" leaked the internal sentinel
        # (egg-stage audit 2026-07-05)
        ("No.", "—" if pet.num < 0 else f"#{pet.num}"), ("Stage", pet.stage),
        ("Attrib", pet.attribute), ("Field", data.pretty_field(pet.field) or "-"),
        ("Element", pet.element or "-"), ("Gen", str(pet.generation)),
        ("Age", _mins(pet.age_seconds)), ("Life", f"{_mins(rem)} left"),
    ]
    power = [
        ("Vaccine", str(pet.vaccine)), ("Data", str(pet.data_power)),
        ("Virus", str(pet.virus)), ("Effort", f"{pet.strength}/4"),
        ("Weight", f"{pet.weight}g"), ("Battles", f"{pet.wins}W / {pet.battles}"),
        ("Trophy", str(pet.trophies)), ("Bits", str(pet.bits)),
    ]
    if pet.x_antibody != "None":
        power.append(("X-Anti", pet.x_antibody))   # keep STATUS at its 9-row max (no overflow)
    person = [
        ("Type", pet.personality()), ("Spirit", disp),
        ("Appetite", appetite), ("Pace", temperament),
        ("Likes", fav or "-"), ("Dislikes", dis or "-"),
    ]
    core = data.load_digicore_icons().get(pet.num)
    if core:
        person.append(("Core", f"{chr(0x25C6)} {core}"))   # DVPet digicore badge
    return [
        ("STATUS", status),
        ("POWER", power),
        ("CONDITION", [
            ("Hunger", f"{pet.hunger}/4"), ("Energy", f"{int(pet.energy)}/{pet.max_energy}"),
            ("Spirit", f"{pet.enthusiasm:+d}"),
            ("Ailing", (("sick " if pet.sick else "") + (f"{pet.injuries} inj" if pet.injuries else "")).strip() or "no"),
            # the nutrition tracks (audit 2026-07-05): browsable at last -- they
            # only ever flashed by in the eat readout.  ♥ = good nutrition
            # (all >= 16: faster recovery, fewer fatigues, slower life burn)
            ("Nutrit.", f"P{pet.nutr_protein} M{pet.nutr_mineral} V{pet.nutr_vitamin}"
                        + (" ♥" if pet.good_nutrition() else "")),
            ("Poop", str(pet.poop)),
            ("Care x", str(pet.care_mistakes)), ("Disturb", str(pet.disturb)),
        ]),
        ("HABITAT", [
            ("Home", h["name"]), ("Fit", f"{fit} ({aff:+d})"),
            ("Season", pet.season),
        ]),
        ("PERSON", person),
        ("TROPHIES", _trophy_rows(pet)),
        ("LEGACY", _legacy_rows()),
        ("EVOLVES", _evo_rows(pet)),
    ]


class DigiCorePanel:
    def __init__(self, pet):
        self.pet = pet
        self.pages = [("CORE", None)] + build_pages(pet)
        self.i = 0
        self.teaser = False       # EvolSilhouette view (SPACE on the core)
        self.teaser_t = 0         # ticks into the digicoreExpand zoom
        self._back_t = 0          # evolSilhouetteBack dark-blink ticks left
        self.frame_i = 0
        self.note = "the core stirs…"
        self.evo_sel = 0          # EVOLVES page: the highlighted candidate
        self.detail = None        # (num, name): the open requirement checklist
        self.det_off = 0          # ...and its scroll offset

    def anim(self):
        self.frame_i += 1
        if self.teaser:
            self.teaser_t += 1
        if self._back_t:
            self._back_t -= 1

    def key(self, k):
        if self.teaser:
            if k in ("escape", "space", "enter", "d"):
                self.teaser = False           # EvolSilhouetteBack: dark blink out
                self._back_t = BACK_T
                self.sfx = "wash"             # _silhouetteFade has no rip; wash substitutes
            return None
        if k in ("space", "enter") and self.i == 0:
            # onDigicore -> EvolSilhouetteTransition (the fade sound has no rip;
            # the dna-wash sweep substitutes, like heal's click/confirm cues)
            self.teaser = True
            self.teaser_t = 0                 # the badge zooms in first (digicoreExpand)
            self.sfx = "wash"
            return None
        if k == "m" and self.i == 0:
            # the tModeChange button on the EvolutionState page
            if not self.pet.can_mode_change():
                return None
            old_num, msg = self.pet.mode_change()
            if old_num is not None:
                return ("done", ("evolve", old_num, msg))
            self.note = msg
            self.sfx = "error"
            return None
        if self.detail is not None:                    # the requirement checklist
            if k in ("up", "k"):
                self.det_off = max(0, self.det_off - 1)
            elif k in ("down", "j"):
                self.det_off += 1                      # text() clamps to the list
            elif k in ("escape", "enter", "space", "d"):
                self.detail = None
                self.det_off = 0
            return None
        on_evo = self.pages[self.i][0] == "EVOLVES"
        rows = self.pages[self.i][1] if on_evo else None
        if on_evo and isinstance(rows, list) and rows:
            if k in ("up", "k"):
                self.evo_sel = (self.evo_sel - 1) % len(rows)
                return None
            if k in ("down", "j"):
                self.evo_sel = (self.evo_sel + 1) % len(rows)
                return None
            if k == "enter":
                num, name = rows[self.evo_sel][0], rows[self.evo_sel][1]
                self.detail = (num, name)
                self.det_off = 0
                return None
        if k in ("right", "l") or (k == "space" and self.i > 0):
            self.i = (self.i + 1) % len(self.pages)
        elif k in ("left", "h"):
            self.i = (self.i - 1) % len(self.pages)
        elif k in ("escape", "d"):
            return ("done", None)
        return None

    def _pet_rows(self, num, idx=None):
        if idx is None or num == -1:
            # WALK_BEAT bob; bob_frame owns the egg's shell art (num -1 has
            # no roster sheet -- the gaze rendered an empty LCD, audit 2026-07-05)
            return data.bob_frame(num, self.frame_i,
                                  egg_type=getattr(self.pet, "egg_type", 0))
        rec = data.load_sprites()[1].get(num)
        if not rec:
            return None
        return rec["frames"][idx] or next((f for f in rec["frames"] if f), None)

    @staticmethod
    def _core_place(rows, cell=None):
        """Centre the FULL sprite on the core scene (cell 0/1 = that 16px cell,
        None = whole grid).  grid.center(ph=16) rides the grounded-2px floor
        rule (band_h = 14) and box-mushes every 16px-tall mon -- Joel's Devimon
        read as a broken blob (2026-07-04).  The core has no floor; native
        pixels, bottom on the scene edge."""
        s = grid._crop(rows)
        span, x0 = (grid.W, grid.X0) if cell is None else (grid.CELL, grid.X0 + cell * grid.CELL)
        return (s, x0 + (span - grid.width(s)) // 2, False)

    def _dots(self):
        return " ".join((chr(0x25CF) if j == self.i else chr(0x25CB))
                        for j in range(len(self.pages)))

    def _core_scene(self):
        """The CORE landing page -- a data-menu page like every other digicore
        page (Joel 2026-07-05: one layout language for the whole data book;
        the scene experiment read as inconsistent).  SPACE opens the core
        gaze, where the visuals live."""
        p = self.pet
        n = core_number(p)
        growth = p.STAGE_DURATION.get(p.stage)
        has_next = (bool(lines.evo_rows(p)) if lines.active(p)
                    else bool(data.load_evolutions().get(p.num)))
        pending = growth is not None and p.stage_seconds < growth and has_next
        x = getattr(p, "x_antibody", "None")
        rows = [
            ("Core", f"{chr(0x25C6)} {n}"),
            ("Meter", "evolution nears at 1" if pending else "life meter"),
            ("Field", data.pretty_field(getattr(p, "field", "") or "None")),
            ("X-State", "none" if x == "None" else x.lower()),
            ("Mode", ("ready — press M" if p.can_mode_change() else chr(0x2014))),
        ]
        out = menu.header("DIGICORE  CORE", self._dots())
        for label, val in rows:
            out.append(f" {label:<9}", style=DIM)
            out.append(f"{val}\n", style=INK_B)
        out.append_text(menu.blanks(9 - len(rows) - 3))
        out.append(" gaze into the core to glimpse\n", style=DIM)
        out.append(" what stirs within…\n", style=DIM)
        out.append_text(menu.note(self.note if self.note != "the core stirs…" else "",
                                  tick=self.frame_i))
        out.append_text(menu.footer("SPACE gaze  ←→ page  ESC close"))
        return out

    def _teaser_scene(self):
        """EvolSilhouetteTransition: the core badge ZOOMS IN (digicoreExpand,
        canon beats 6-14 grow it 1.5x each), then the next natural evolution
        holds as a STATIC blacked-out shape (canon draws frame 0 -- the old
        pose-flicker here was the 10Hz flutter class)."""
        """The gaze (Joel 2026-07-05 round 3): the WHOLE LCD, nothing else --
        background, the current mon, the circle animation, the silhouette.
        Boom boom boom.  The narration rides the message box (it IS a
        message); no key hints anywhere."""
        p = self.pet
        bgimg = core_background(p)
        on = menu.scene_ink(bgimg)
        t = self.teaser_t
        if t < MON_T:                                     # beat one: the mon itself
            rows = self._pet_rows(p.num)
            placements = [self._core_place(rows)] if rows else []
            return render_scene(placements, 40, SCENE_ROWS, on, LCD_BG, bgimg=bgimg, clip=grid.WINDOW)
        if t < MON_T + EXPAND_T:                          # beat two: the core turns
            badge = data.load_effects().get(core_badge_key(p) or "core_xnone", [None])[0]
            overlay = []
            if badge:
                k = 1 + (t - MON_T) // (EXPAND_T // 2)    # 1x -> 2x zoom
                k = min(k, 2)
                big = ["".join(ch * k for ch in r) for r in badge for _ in range(k)]
                bw, bh = max(len(r) for r in big), len(big)
                ox, oy = (40 - bw) // 2, (SCENE_ROWS * 2 - bh) // 2
                overlay = [(ox + x, oy + y) for y, row in enumerate(big)
                           for x, c in enumerate(row) if c == "1" and oy + y >= 0]
            return render_scene([], 40, SCENE_ROWS, on, LCD_BG,
                                overlay=overlay, bgimg=bgimg)
        nxt = next_evolution(p)                           # beat three: what stirs
        if nxt is None:
            rows = self._pet_rows(p.num, idx=0)
            placements = [self._core_place(rows)] if rows else []
            return render_scene(placements, 40, SCENE_ROWS, on, LCD_BG, bgimg=bgimg, clip=grid.WINDOW)
        sil = ghost(silhouette(self._pet_rows(nxt, idx=0) or []),
                    phase=(self.frame_i // 5) % 2)
        placements = [self._core_place(sil)] if sil else []
        return render_scene(placements, 40, SCENE_ROWS, on, LCD_BG, bgimg=bgimg, clip=grid.WINDOW)

    def strip(self):
        """Narration only -- the gaze speaks through the message box; every
        other digicore state leaves it alone."""
        if not self.teaser:
            return menu.hints(("SPACE", "gaze"), ("\u2190\u2192", "page"),
                              ("ESC", "close"))
        t = self.teaser_t
        if t < MON_T:
            return "the core stirs…"
        if t < MON_T + EXPAND_T:
            return "the core opens…"
        return ("Nothing stirs — this is its final form."
                if next_evolution(self.pet) is None
                else "A shape looms in the core…")

    def _detail_scene(self):
        """One candidate's requirement checklist (evolution.requirement_report):
        met gates dim out of the way, the unmet ones are the raising guide."""
        from rich.text import Text
        num, name = self.detail
        report = (lines.requirement_report(self.pet, num) if lines.active(self.pet)
                  else evolution.requirement_report(self.pet, num))
        vis = 8
        out = menu.header(f"DIGICORE  {name[:16].upper()}", "req")

        def fmt(r, i):
            met, txt = r
            mark = {True: " " + chr(0x2713) + " ", False: " " + chr(0x2717) + " ",
                    None: "   "}[met]
            t = Text()
            t.append(mark, style=DIM if met else INK_B)
            t.append(txt[:35] + "\n", style=DIM if met is not False else INK_B)
            return t

        self.det_off = menu.scroll_window(out, report, self.det_off, vis, fmt)
        more = "" if len(report) <= vis else f"  ({self.det_off + 1}-{min(len(report), self.det_off + vis)}/{len(report)})"
        out.append_text(menu.footer(f"↑↓ scroll{more}   ESC back"))
        return out

    def _evolves_scene(self, rows, dots):
        from rich.text import Text
        out = menu.header("DIGICORE  EVOLVES", dots)
        if isinstance(rows, str):                      # "(final form)"
            out.append(f" {rows}\n", style=DIM)
            out.append_text(menu.blanks(8))
            out.append_text(menu.footer("←→ page    ESC close"))
            return out

        def fmt(r, j):
            num, name, ready, unmet = r
            cur = j == self.evo_sel
            tag = chr(0x2713) + " ready" if ready else f"{unmet} to go"
            t = Text()
            t.append(("▸" if cur else " ") + f" {name[:20]:<21}", style=INK_B if cur else INK)
            t.append(f"{tag:>10}\n", style=INK_B if ready else DIM)
            return t

        self.evo_sel = menu.list_window(out, rows, self.evo_sel, 8, fmt)
        out.append_text(menu.note("ENTER: what it takes"))
        out.append_text(menu.footer("↑↓ pick  ENTER req  ←→ page  ESC"))
        return out

    def text(self):
        if self.teaser:
            return self._teaser_scene()
        if self._back_t:                              # evolSilhouetteBack: dark blink
            return render_scene([], 40, SCENE_ROWS, SIL_NIGHT, VOID, clip=grid.WINDOW)
        if self.detail is not None:
            return self._detail_scene()
        if self.i == 0:
            return self._core_scene()
        title, rows = self.pages[self.i]
        dots = self._dots()
        if title == "EVOLVES":
            return self._evolves_scene(rows, dots)
        out = menu.header(f"DIGICORE  {title}", dots)
        for label, val in rows:
            out.append(f" {label:<9}", style=DIM)
            out.append(f"{val}\n", style=INK_B)
        out.append_text(menu.blanks(9 - len(rows)))
        out.append_text(menu.footer("←→ page    ESC close"))
        return out
