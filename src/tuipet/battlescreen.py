"""Battle screen — pet vs enemy, attribute-triangle combat with attack effects."""
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

_E = data.load_effects()
ATTACK = (_E.get("attack") or [None])[0]   # flying projectile orb
HIT = (_E.get("hit") or [None])[0]         # impact burst
FLY = 5                                     # frames the projectile travels


def _blit(bm, ox, oy):
    return [(ox + x, oy + y) for y, row in enumerate(bm)
            for x, c in enumerate(row) if c == "1"]


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
        self.atk = None          # active attack animation, or None

    def compose(self):
        yield Static(id="bt")

    def on_mount(self):
        self.view = self.query_one("#bt", Static)
        self.set_interval(0.22, self._anim)
        self.render_view()

    def _anim(self):
        self.frame_i += 1
        if self.atk:
            self.atk["step"] += 1
            if self.atk["step"] > FLY + 2:      # fly, then 2 frames of impact
                self.atk = None
        self.render_view()

    def action_atk(self, which):
        if self.battle.over or self.atk:
            return
        before = self.battle.enemy_hp
        self.battle.play_round(which)
        attacker = "pet" if self.battle.enemy_hp < before else "enemy"
        self.atk = {"attacker": attacker, "step": 0}
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
        return "●" * hp + "○" * (mx - hp) if mx <= 12 else f"{hp}/{mx}"

    def _attack_overlay(self, pet_x, pw, enemy_x, ew):
        if not (self.atk and ATTACK):
            return []
        a = self.atk
        py = ROWS * 2 - 13                       # mid-height of the scene
        ow, hw = len(ATTACK[0]), (len(HIT[0]) if HIT else 0)
        if a["attacker"] == "pet":               # left -> right, bursts on the foe
            x0, x1, tx = pet_x + pw - 1, enemy_x - ow, enemy_x + ew // 2 - hw // 2
        else:                                    # right -> left, bursts on the pet
            x0, x1, tx = enemy_x - ow, pet_x + pw - 1, pet_x + pw // 2 - hw // 2
        if a["step"] <= FLY:
            x = int(x0 + (x1 - x0) * (a["step"] / FLY))
            return _blit(ATTACK, x, py)
        return _blit(HIT, tx, py - 1) if HIT else []

    def render_view(self):
        b = self.battle
        a = self.atk
        pet_atk = bool(a and a["attacker"] == "pet" and a["step"] <= FLY)
        enemy_atk = bool(a and a["attacker"] == "enemy" and a["step"] <= FLY)
        pet_rows = self._frames(self.pet.num, pet_atk)
        enemy_rows = self._frames(b.enemy["num"], enemy_atk)
        pw = max(len(r) for r in pet_rows)
        ew = max(len(r) for r in enemy_rows)
        pet_x, enemy_x = 1, COLS - ew - 1
        overlay = self._attack_overlay(pet_x, pw, enemy_x, ew)
        scene = render_scene(
            [(pet_rows, pet_x, True), (enemy_rows, enemy_x, False)],
            COLS, ROWS, LCD_ON, LCD_BG, overlay=overlay)

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
