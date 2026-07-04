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
from . import data, evolution, grid, lines  # noqa: F401  (pet methods drive the data)
from .render import render_scene

from .theme import LCD_ON, LCD_BG, INK, INK_B, DIM, SIL_DAY, SIL_NIGHT  # noqa: F401  (theme.apply propagation)
from . import menu

DIGICORE_BASE_RATE = 14            # DigicoreBaseRate (config.csv col 1)
CORE_ROWS = 8                      # 16px scene band, like the tournament fight scenes
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
    """ViewUtil.getSilhouetteImage on 1-bit art: black the whole body out
    (scanline fill between the outline's extremes)."""
    out = []
    for r in rows:
        a, b = r.find("1"), r.rfind("1")
        out.append(r if a < 0 else r[:a] + "1" * (b - a + 1) + r[b + 1:])
    return out


def next_evolution(pet):
    """The silhouette's subject (getCurrentNaturalEvol first entry): the ready
    candidate first, else the closest one; None past growth / at a final form."""
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
    (evolution.requirement_report) -- the page shows it as distance-to-go."""
    if pet.num == -1 or pet.stage in ("Egg", "Fresh"):
        return "(too young)"
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
    for num, name, ready, dev in cands[:8]:
        unmet = sum(1 for met, _ in evolution.requirement_report(pet, num) if met is False)
        rows.append((num, name, ready, unmet))
    return rows


def _trophy_rows(pet):
    """The trophy room: this life's cups (label + the season they fell) topped
    by the career totals -- lifetime cups persist across generations."""
    from tuipet import tournament as _t
    from tuipet import persistence as _p
    rows = [("This life", "\u2605" * min(pet.trophies, 12) or "none yet")]
    try:
        career = len(_p.get_progress().get("tourneys", ()) or ())
    except Exception:
        career = 0
    rows.append(("Career", f"{career} cup(s), all generations"))
    won = sorted((getattr(pet, "trophies_won", None) or {}).items())
    for tid, season in won[:6]:                     # keep the page at 9 rows max
        tr = _t.trophy_by_id(tid)
        rows.append((_t.trophy_label(tr)[:12] if tr else f"cup {tid}", season))
    if len(won) > 6:
        rows.append(("…", f"+{len(won) - 6} more"))
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
        ("Name", pet.name), ("No.", f"#{pet.num}"), ("Stage", pet.stage),
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
            ("Mood", pet.current_mood()), ("Spirit", f"{pet.enthusiasm:+d}"), ("Sick", "yes" if pet.sick else "no"),
            ("Injury", str(pet.injuries)), ("Poop", str(pet.poop)),
            ("Care x", str(pet.care_mistakes)), ("Disturb", str(pet.disturb)),
        ]),
        ("HABITAT", [
            ("Home", h["name"]), ("Fit", f"{fit} ({aff:+d})"),
            ("Season", pet.season), ("Weather", pet.weather),
            ("Temp", f"{int(pet.temp)}°"),
            ("Ideal", f"{pet.ideal_temp[0]}-{pet.ideal_temp[1]}°"),
        ]),
        ("PERSON", person),
        ("TROPHIES", _trophy_rows(pet)),
        ("EVOLVES", _evo_rows(pet)),
    ]


class DigiCorePanel:
    def __init__(self, pet):
        self.pet = pet
        self.pages = [("CORE", None)] + build_pages(pet)
        self.i = 0
        self.teaser = False       # EvolSilhouette view (SPACE on the core)
        self.frame_i = 0
        self.note = "the core stirs..."
        self.evo_sel = 0          # EVOLVES page: the highlighted candidate
        self.detail = None        # (num, name): the open requirement checklist
        self.det_off = 0          # ...and its scroll offset

    def anim(self):
        self.frame_i += 1

    def key(self, k):
        if self.teaser:
            if k in ("escape", "space", "enter", "d"):
                self.teaser = False           # EvolSilhouetteBack
                self.sfx = "wash"
            return None
        if k in ("space", "enter") and self.i == 0:
            # onDigicore -> EvolSilhouetteTransition (the fade sound has no rip;
            # the dna-wash sweep substitutes, like heal's click/confirm cues)
            self.teaser = True
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

    def _pet_rows(self, num):
        rec = data.load_sprites()[1].get(num)
        if not rec:
            return None
        idx = data.ROLES["idle"][self.frame_i % 2]
        return rec["frames"][idx] or next((f for f in rec["frames"] if f), None)

    def _core_scene(self):
        """The canon Digicore page: core backdrop + badge + the meter number."""
        p = self.pet
        bgimg = core_background(p)
        on = SIL_DAY if bgimg else LCD_ON   # never white (paint() rule)
        badge = core_badge_key(p)
        overlay = []
        if badge:
            b = data.load_effects().get(badge, [None])[0]
            if b:
                bw = max(len(r) for r in b)
                overlay = [(20 - bw // 2 + x, 1 + y) for y, row in enumerate(b)
                           for x, c in enumerate(row) if c == "1"]
        rows = self._pet_rows(p.num)
        placements = [grid.center(rows, ph=CORE_ROWS * 2)] if rows else []
        out = menu.bar("DIGICORE", "core")
        out.append_text(render_scene(placements, 40, CORE_ROWS, on, LCD_BG,
                                     overlay=overlay, bgimg=bgimg))
        n = core_number(p)
        growth = p.STAGE_DURATION.get(p.stage)
        has_next = (bool(lines.evo_rows(p)) if lines.active(p)
                    else bool(data.load_evolutions().get(p.num)))
        pending = growth is not None and p.stage_seconds < growth and has_next
        lbl = "evolution nears at 1" if pending else "life meter"
        out.append(f"\n core {chr(0x25C6)} {n}", style=INK_B)
        out.append(f"   {lbl}\n", style=DIM)
        out.append_text(menu.note(self.note, tick=self.frame_i))
        foot = "SPACE core  M mode  → data  ESC" if self.pet.can_mode_change() \
            else "SPACE core  → data  ESC out"
        out.append_text(menu.footer(foot))
        return out

    def _teaser_scene(self):
        """EvolSilhouette: the next natural evolution, blacked out."""
        p = self.pet
        nxt = next_evolution(p)
        out = menu.bar("DIGICORE", "???")
        if nxt is None:
            rows = self._pet_rows(p.num)
            placements = [grid.center(rows, ph=CORE_ROWS * 2)] if rows else []
            out.append_text(render_scene(placements, 40, CORE_ROWS, LCD_ON, LCD_BG))
            out.append("\n")
            out.append_text(menu.note("Nothing stirs — this is its final form."))
        else:
            sil = silhouette(self._pet_rows(nxt) or [])
            placements = [grid.center(sil, ph=CORE_ROWS * 2)] if sil else []
            out.append_text(render_scene(placements, 40, CORE_ROWS, LCD_ON, LCD_BG))
            out.append("\n")
            out.append_text(menu.note("A shape looms in the core..."))
        out.append_text(menu.footer("SPACE back   ESC out"))
        return out

    def _detail_scene(self):
        """One candidate's requirement checklist (evolution.requirement_report):
        met gates dim out of the way, the unmet ones are the raising guide."""
        num, name = self.detail
        report = (lines.requirement_report(self.pet, num) if lines.active(self.pet)
                  else evolution.requirement_report(self.pet, num))
        vis = 8
        self.det_off = max(0, min(self.det_off, max(0, len(report) - vis)))
        out = menu.header(f"DIGICORE  {name[:16].upper()}", "req")
        for met, txt in report[self.det_off:self.det_off + vis]:
            mark = {True: " " + chr(0x2713) + " ", False: " " + chr(0x2717) + " ",
                    None: "   "}[met]
            out.append(mark, style=DIM if met else INK_B)
            out.append(txt[:35] + "\n", style=DIM if met is not False else INK_B)
        out.append_text(menu.blanks(vis - min(vis, len(report) - self.det_off)))
        more = "" if len(report) <= vis else f"  ({self.det_off + 1}-{min(len(report), self.det_off + vis)}/{len(report)})"
        out.append_text(menu.footer(f"↑↓ scroll{more}   ESC back"))
        return out

    def _evolves_scene(self, rows, dots):
        out = menu.header("DIGICORE  EVOLVES", dots)
        if isinstance(rows, str):                      # "(too young)" / "(final form)"
            out.append(f" {rows}\n", style=DIM)
            out.append_text(menu.blanks(8))
            out.append_text(menu.footer("←→ page    ESC close"))
            return out
        self.evo_sel = min(self.evo_sel, len(rows) - 1)
        for j, (num, name, ready, unmet) in enumerate(rows):
            cur = j == self.evo_sel
            tag = chr(0x2713) + " ready" if ready else f"{unmet} to go"
            out.append(("▸" if cur else " ") + f" {name[:20]:<21}", style=INK_B if cur else INK)
            out.append(f"{tag:>10}\n", style=INK_B if ready else DIM)
        out.append_text(menu.blanks(8 - len(rows)))
        out.append_text(menu.note("ENTER: what it takes"))
        out.append_text(menu.footer("↑↓ pick  ENTER req  ←→ page  ESC"))
        return out

    def text(self):
        if self.teaser:
            return self._teaser_scene()
        if self.detail is not None:
            return self._detail_scene()
        if self.i == 0:
            return self._core_scene()
        title, rows = self.pages[self.i]
        dots = " ".join((chr(0x25CF) if j == self.i else chr(0x25CB)) for j in range(len(self.pages)))
        if title == "EVOLVES":
            return self._evolves_scene(rows, dots)
        out = menu.header(f"DIGICORE  {title}", dots)
        for label, val in rows:
            out.append(f" {label:<9}", style=DIM)
            out.append(f"{val}\n", style=INK_B)
        out.append_text(menu.blanks(9 - len(rows)))
        out.append_text(menu.footer("←→ page    ESC close"))
        return out
