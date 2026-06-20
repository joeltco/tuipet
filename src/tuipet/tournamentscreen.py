"""Tournament screen — fight a bracket of matches for a trophy."""
from __future__ import annotations
from rich.text import Text
from textual.screen import ModalScreen
from textual.widgets import Static

from . import data
from .tournament import Tournament
from .battlescreen import BattleScreen
from .render import render_scene

LCD_ON, LCD_BG = "#0b3d0b", "#9bbc0f"
INK = f"{LCD_ON} on {LCD_BG}"
INK_B = f"bold {LCD_ON} on {LCD_BG}"
DIM = f"#5a7a1a on {LCD_BG}"
COLS, ROWS = 40, 10


class TournamentScreen(ModalScreen):
    CSS = """
    TournamentScreen { align: center middle; }
    #tn { border: heavy #5a7a1a; background: #9bbc0f; padding: 0 1; width: 46; height: 19; }
    """
    BINDINGS = [("space", "fight", "Fight"), ("enter", "fight", "Fight"),
                ("escape", "leave", "Leave")]

    def __init__(self, pet):
        super().__init__()
        self.pet = pet
        self.tourney = Tournament(pet)
        self.frame_i = 0
        self.in_battle = False

    def compose(self):
        yield Static(id="tn")

    def on_mount(self):
        self.view = self.query_one("#tn", Static)
        self.set_interval(0.4, self._anim)
        self.render_view()

    def _anim(self):
        self.frame_i += 1
        self.render_view()

    def action_fight(self):
        t = self.tourney
        if t.over or self.in_battle:
            return
        self.in_battle = True
        opp = t.current_opponent()
        self.app.push_screen(BattleScreen(self.pet, opp), self._after_battle)

    def _after_battle(self, battle_obj):
        self.in_battle = False
        won = bool(battle_obj and battle_obj.won)
        self.tourney.record(won)
        self.render_view()

    def action_leave(self):
        self.dismiss(self.tourney.last if self.tourney.over else None)

    def _frames(self, num, attacking=False):
        rec = data.load_sprites()[1][num]
        roles = data.ROLES["attack"] if attacking else data.ROLES["idle"]
        idx = roles[self.frame_i % len(roles)]
        return rec["frames"][idx] or rec["frames"][0]

    def render_view(self):
        t = self.tourney
        out = Text()
        out.append(f"{t.name}\n", style=INK_B)
        if t.over:
            scene_num = self.pet.num
            scene = render_scene([(self._frames(scene_num), (COLS - 16) // 2, False)],
                                 COLS, ROWS, LCD_ON, LCD_BG)
            out.append_text(scene)
            out.append(f"\n{'●' * min(self.pet.trophies, 14)}\n", style=INK_B)
            out.append(f"{t.last}\n", style=INK_B)
            out.append("ESC leave", style=DIM)
            self.view.update(out)
            return
        opp = t.current_opponent()
        pet_rows = self._frames(self.pet.num)
        opp_rows = self._frames(opp["num"])
        ow = max(len(r) for r in opp_rows)
        scene = render_scene([(pet_rows, 2, True), (opp_rows, COLS - ow - 2, False)],
                             COLS, ROWS, LCD_ON, LCD_BG)
        out.append(f"{t.round_name}  (match {t.round + 1}/3)\n", style=INK_B)
        out.append_text(scene)
        out.append(f"\nYou  vs  {opp['name']}[{opp['attribute'][:2]}]\n", style=INK)
        out.append(f"Trophies {self.pet.trophies}\n", style=INK)
        out.append(f"{t.last}\n", style=INK_B)
        out.append("SPACE fight   ESC leave", style=DIM)
        self.view.update(out)
