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
from . import data, evolution, grid  # noqa: F401  (pet methods drive the data)
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
    """The core swirl backdrop by the highest banked DNA field (else own field)."""
    owned = getattr(pet, "dna_owned", None) or {}
    field = max(owned, key=owned.get) if any(owned.values()) else pet.field
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
    """The evolution line for the data book: what this Digimon can become,
    closest-first, with the ones whose requirements are already met flagged."""
    if pet.num == -1 or pet.stage in ("Egg", "Fresh"):
        return [("(too young)", "")]
    try:
        cands = sorted(evolution.candidates(pet), key=lambda c: (not c[2], c[3]))
    except Exception:
        cands = []
    if not cands:
        return [("(final form)", "")]
    rows = []
    for num, name, ready, dev in cands[:9]:
        rows.append((name[:14], chr(0x2713) + " ready" if ready else ""))
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
        ("EVOLVES", _evo_rows(pet)),
    ]


class DigiCorePanel:
    def __init__(self, pet):
        self.pet = pet
        self.pages = [("CORE", None)] + build_pages(pet)
        self.i = 0
        self.teaser = False       # EvolSilhouette view (SPACE on the core)
        self.frame_i = 0

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
        on = SIL_NIGHT if p.day_phase == "night" else (SIL_DAY if bgimg else LCD_ON)
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
        pending = (growth is not None and p.stage_seconds < growth
                   and bool(data.load_evolutions().get(p.num)))
        lbl = "evolution nears at 1" if pending else "life meter"
        out.append(f"\n core {chr(0x25C6)} {n}", style=INK_B)
        out.append(f"   {lbl}\n", style=DIM)
        out.append_text(menu.note("the core stirs..."))
        out.append_text(menu.footer("SPACE core  → data  ESC out"))
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

    def text(self):
        if self.teaser:
            return self._teaser_scene()
        if self.i == 0:
            return self._core_scene()
        title, rows = self.pages[self.i]
        dots = " ".join((chr(0x25CF) if j == self.i else chr(0x25CB)) for j in range(len(self.pages)))
        out = menu.header(f"DIGICORE  {title}", dots)
        for label, val in rows:
            out.append(f" {label:<9}", style=DIM)
            out.append(f"{val}\n", style=INK_B)
        out.append_text(menu.blanks(9 - len(rows)))
        out.append_text(menu.footer("←→ page    ESC close"))
        return out
