"""DigiCore — paged data book, rendered in the display box."""
from __future__ import annotations
from rich.text import Text
from . import data, evolution  # noqa: F401  (pet methods drive the data)

from .theme import LCD_ON, LCD_BG, INK, INK_B, DIM
from . import menu


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
        ("Attrib", pet.attribute), ("Field", pet.field or "-"),
        ("Element", pet.element or "-"), ("Gen", str(pet.generation)),
        ("Age", _mins(pet.age_seconds)), ("Life", f"{_mins(rem)} left"),
    ]
    if pet.x_antibody != "None":
        status.append(("X-Anti", pet.x_antibody))
    return [
        ("STATUS", status),
        ("POWER", [
            ("Vaccine", str(pet.vaccine)), ("Data", str(pet.data_power)),
            ("Virus", str(pet.virus)), ("Effort", f"{pet.strength}/4"),
            ("Weight", f"{pet.weight}g"), ("Battles", f"{pet.wins}W / {pet.battles}"),
            ("Trophy", str(pet.trophies)), ("Bits", str(pet.bits)),
        ]),
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
        ("PERSON", [
            ("Type", pet.personality()), ("Spirit", disp),
            ("Appetite", appetite), ("Pace", temperament),
            ("Likes", fav or "-"), ("Dislikes", dis or "-"),
        ]),
        ("EVOLVES", _evo_rows(pet)),
    ]


class DigiCorePanel:
    def __init__(self, pet):
        self.pet = pet
        self.pages = build_pages(pet)
        self.i = 0

    def key(self, k):
        if k in ("right", "l", "space"):
            self.i = (self.i + 1) % len(self.pages)
        elif k in ("left", "h"):
            self.i = (self.i - 1) % len(self.pages)
        elif k in ("escape", "d"):
            return ("done", None)
        return None

    def text(self):
        title, rows = self.pages[self.i]
        dots = " ".join((chr(0x25CF) if j == self.i else chr(0x25CB)) for j in range(len(self.pages)))
        out = menu.header(f"DIGICORE  {title}", dots)
        for label, val in rows:
            out.append(f" {label:<9}", style=DIM)
            out.append(f"{val}\n", style=INK_B)
        out.append_text(menu.blanks(9 - len(rows)))
        out.append_text(menu.footer("←/→ page    ESC close"))
        return out
