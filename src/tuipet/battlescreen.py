"""Battle screen — pet vs enemy, attribute-triangle combat with animation."""
from __future__ import annotations
from rich.text import Text
from textual.screen import ModalScreen
from textual.widgets import Static

from . import data
from .battle import Battle
from .render import render_scene

LCD_ON, LCD_BG = "#0b3d0b", "#9bbc0f"
INK = f"{LCD_ON} on {LCD_BG}"
INK_B = f"bold {LCD_ON} on {LCD_BG}"
DIM = f"#5a7a1a on {LCD_BG}"
COLS, ROWS = 40, 9


class BattleScreen(ModalScreen):
    CSS = """
    BattleScreen { align: center middle; }
    #bt { border: heavy #5a7a1a; background: #9bbc0f; padding: 0 1; width: 44; height: 18; }
    """
    BINDINGS = [("1", "atk('Vaccine')", "Vaccine"), ("2", "atk('Data')", "Data"),
                ("3", "atk('Virus')", "Virus"), ("escape", "leave", "Flee"),
                ("space", "leave", "Close")]

    def __init__(self, pet, enemy=None):
        super().__init__()
        self.pet = pet
        self.battle = Battle(pet, enemy)
        self.frame_i = 0
        self.flash_atk = None
        self.flash_ttl = 0

    def compose(self):
        yield Static(id="bt")

    def on_mount(self):
        self.view = self.query_one("#bt", Static)
        self.set_interval(0.4, self._anim)
        self.render_view()

    def _anim(self):
        self.frame_i += 1
        if self.flash_ttl > 0:
            self.flash_ttl -= 1
            if self.flash_ttl == 0:
                self.flash_atk = None
        self.render_view()

    def action_atk(self, which):
        if self.battle.over:
            return
        before = self.battle.enemy_hp
        self.battle.play_round(which)
        self.flash_atk = "pet" if self.battle.enemy_hp < before else "enemy"
        self.flash_ttl = 1
        self.render_view()

    def action_leave(self):
        self.dismiss(self.battle if self.battle.over else None)

    def _frames(self, num, attacking):
        rec = data.load_sprites()[1][num]
        roles = data.ROLES["attack"] if attacking else data.ROLES["idle"]
        idx = roles[self.frame_i % len(roles)]
        return rec["frames"][idx] or rec["frames"][0]

    def _hp(self, hp, mx):
        hp = max(0, hp)
        if mx <= 12:
            return "●" * hp + "○" * (mx - hp)
        return f"{hp}/{mx}"

    def render_view(self):
        b = self.battle
        pet_rows = self._frames(self.pet.num, self.flash_atk == "pet")
        enemy_rows = self._frames(b.enemy["num"], self.flash_atk == "enemy")
        ew = max(len(r) for r in enemy_rows)
        scene = render_scene(
            [(pet_rows, 1, True), (enemy_rows, COLS - ew - 1, False)],
            COLS, ROWS, LCD_ON, LCD_BG)

        title = f"BATTLE vs {b.enemy['name']}" + (" (BOSS)" if b.enemy["boss"] else "")
        out = Text()
        out.append(title + "\n", style=INK_B)
        out.append_text(scene)
        out.append(f"\nYou {self._hp(b.pet_hp, b.pet_max)}", style=INK)
        out.append(f"    Foe[{b.enemy['attribute'][:2]}] {self._hp(b.enemy_hp, b.enemy_max)}\n", style=INK)
        out.append((b.last or "Choose your attack!") + "\n", style=INK_B)
        if b.over:
            res = "VICTORY!" if b.won else "DEFEAT"
            out.append(f"{res}  {b.reward}   SPACE", style=INK_B)
        else:
            out.append("1 Vaccine  2 Data  3 Virus   ESC flee", style=DIM)
        self.view.update(out)
