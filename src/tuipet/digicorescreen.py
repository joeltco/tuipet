"""DigiCore — the data book: paged, read-only status on every facet of the pet.

Mirrors DVPet's Data_* menu family (Status / Power / Condition / Habitat /
Person), surfacing everything the model tracks in one flip-through book."""
from __future__ import annotations
from rich.text import Text
from textual.screen import ModalScreen
from textual.widgets import Static

LCD_ON, LCD_BG = "#0b3d0b", "#9bbc0f"
INK = f"{LCD_ON} on {LCD_BG}"
INK_B = f"bold {LCD_ON} on {LCD_BG}"
DIM = f"#5a7a1a on {LCD_BG}"


def _mins(s):
    s = int(max(0, s))
    return f"{s // 60}m{s % 60:02d}s"


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
            ("Hunger", f"{pet.hunger}/4"), ("Energy", f"{int(pet.energy)}/100"),
            ("Mood", f"{int(pet.mood)}/100"), ("Sick", "yes" if pet.sick else "no"),
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
            ("Likes", fav or "—"), ("Dislikes", dis or "—"),
        ]),
    ]


class DigiCoreScreen(ModalScreen):
    CSS = """
    DigiCoreScreen { align: center middle; }
    #dc { border: heavy #5a7a1a; background: #9bbc0f; padding: 0 1; width: 36; height: 16; }
    """
    BINDINGS = [
        ("right", "page(1)", "Next"), ("l", "page(1)", "Next"), ("space", "page(1)", "Next"),
        ("left", "page(-1)", "Prev"), ("h", "page(-1)", "Prev"),
        ("escape", "leave", "Close"), ("d", "leave", "Close"),
    ]

    def __init__(self, pet):
        super().__init__()
        self.pet = pet
        self.pages = build_pages(pet)
        self.i = 0

    def compose(self):
        yield Static(id="dc")

    def on_mount(self):
        self.view = self.query_one("#dc", Static)
        self.render_view()

    def action_page(self, d):
        self.i = (self.i + d) % len(self.pages)
        self.render_view()

    def action_leave(self):
        self.dismiss(None)

    def render_view(self):
        title, rows = self.pages[self.i]
        out = Text()
        out.append(f"DIGICORE  {title}\n", style=INK_B)
        out.append("─" * 32 + "\n", style=DIM)
        for label, val in rows:
            out.append(f" {label:<8}", style=DIM)
            out.append(f"{val}\n", style=INK_B)
        for _ in range(max(0, 9 - len(rows))):
            out.append("\n")
        dots = " ".join((chr(0x25CF) if j == self.i else chr(0x25CB)) for j in range(len(self.pages)))
        out.append(f"{dots}\n", style=INK)
        out.append("←→ page   ESC close", style=DIM)
        self.view.update(out)
