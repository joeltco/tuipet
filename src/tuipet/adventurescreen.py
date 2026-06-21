"""Adventure screen — travel a zone, fight encounters and the zone boss."""
from __future__ import annotations
from rich.text import Text
from textual.screen import ModalScreen
from textual.widgets import Static

from . import data
from .adventure import Adventure
from .battlescreen import BattleScreen
from .render import render_scene

LCD_ON, LCD_BG = "#0b3d0b", "#9bbc0f"
INK = f"{LCD_ON} on {LCD_BG}"
INK_B = f"bold {LCD_ON} on {LCD_BG}"
DIM = f"#5a7a1a on {LCD_BG}"
COLS, ROWS = 40, 8
BAR_W = 30


class AdventureScreen(ModalScreen):
    CSS = """
    AdventureScreen { align: center middle; }
    #adv { border: heavy #5a7a1a; background: #9bbc0f; padding: 0 1; width: 44; height: 17; }
    """
    BINDINGS = [("space", "toggle", "Go/Stop"), ("escape", "leave", "Leave")]

    def __init__(self, pet):
        super().__init__()
        self.pet = pet
        self.adv = Adventure(pet)
        self.frame_i = 0
        self.travelling = True
        self.in_battle = False

    def compose(self):
        yield Static(id="adv")

    def on_mount(self):
        self.view = self.query_one("#adv", Static)
        self.set_interval(0.4, self._anim)
        self.set_interval(0.6, self._travel)
        self.render_view()

    def _anim(self):
        self.frame_i += 1
        self.render_view()

    def _travel(self):
        if self.in_battle or not self.travelling or self.adv.done:
            return
        ev = self.adv.travel()
        if ev and ev[0] in ("encounter", "boss"):
            self.travelling = False
            self.in_battle = True
            was_boss = ev[0] == "boss"
            enemy = ev[1]
            self.render_view()
            self.app.push_screen(
                BattleScreen(self.pet, enemy),
                lambda b, wb=was_boss, en=enemy: self._after_battle(b, wb, en))
        else:
            self.render_view()

    def _after_battle(self, battle, was_boss, enemy):
        self.in_battle = False
        if battle is None:                     # fled
            self.adv.last = "Fled the battle."
        else:
            self.adv.resolve(battle.won, was_boss, enemy)
        self.travelling = not self.adv.done
        self.render_view()

    def action_toggle(self):
        if not self.adv.done:
            self.travelling = not self.travelling
            self.render_view()

    def action_leave(self):
        self.dismiss(None)

    def _frames(self):
        rec = data.load_sprites()[1][self.pet.num]
        roles = data.ROLES["idle"]
        idx = roles[self.frame_i % len(roles)]
        return rec["frames"][idx] or rec["frames"][0]

    def render_view(self):
        a = self.adv
        pet_rows = self._frames()
        # pet walks rightward; x position tracks progress across the scene
        ew = max(len(r) for r in pet_rows)
        x = 1 + int((COLS - ew - 2) * (a.pct / 100))
        scene = render_scene([(pet_rows, x, True)], COLS, ROWS, LCD_ON, LCD_BG)

        fill = round(a.pct / 100 * BAR_W)
        bar = "[" + "█" * fill + "·" * (BAR_W - fill) + "]"
        lives = "♥" * a.lives + "·" * (3 - a.lives)

        out = Text()
        out.append(f"ADVENTURE  Map {a.mi + 1}-{a.zi + 1}\n", style=INK_B)
        out.append_text(scene)
        out.append(f"\n{bar} {a.pct}%\n", style=INK)
        bag = sum(self.pet.inventory.values())
        out.append(f"Life {lives}   Bits {self.pet.bits}   Bag {bag}\n", style=INK)
        out.append((a.last or "") + "\n", style=INK_B)
        if a.done:
            out.append("Journey complete!   ESC", style=INK_B)
        elif self.travelling:
            out.append("travelling...   SPACE stop   ESC leave", style=DIM)
        else:
            out.append("stopped.   SPACE go   ESC leave", style=DIM)
        self.view.update(out)
