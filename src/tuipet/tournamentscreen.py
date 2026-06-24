"""Tournament — pick a seasonal cup, then fight its bracket, in the display box."""
from __future__ import annotations
from rich.text import Text
from . import data
from . import tournament
from .tournament import Tournament
from .battlescreen import BattlePanel
from .render import render_scene

from .theme import LCD_ON, LCD_BG, INK, INK_B, DIM, SIL_DAY, SIL_NIGHT
from . import menu
COLS, ROWS = 40, 7


class TournamentPanel:
    def __init__(self, pet):
        self.pet = pet
        self.frame_i = 0
        self.sub = None
        self.tourney = None
        self.trophies = tournament.available(pet)
        self.cursor = 0
        self.phase = "select" if self.trophies else "none"

    def anim(self):
        if self.sub is not None:
            self.sub.anim()
            return
        self.frame_i += 1

    def key(self, k):
        if self.sub is not None:
            r = self.sub.key(k)
            if r is not None and r[0] == "done":
                self.tourney.record(bool(r[1] and r[1].won))
                self.sub = None
            return None
        if self.phase == "none":
            if k in ("escape", "enter", "space", "u"):
                return ("done", None)
            return None
        if self.phase == "select":
            n = len(self.trophies)
            if k in ("up", "k"):
                self.cursor = (self.cursor - 1) % n
            elif k in ("down", "j"):
                self.cursor = (self.cursor + 1) % n
            elif k in ("enter", "space"):
                self.tourney = Tournament(self.pet, self.trophies[self.cursor])
                self.phase = "bracket"
            elif k == "escape":
                return ("done", None)
            return None
        # bracket
        t = self.tourney
        if k in ("space", "enter") and not (t.over or self.sub):
            self.sub = BattlePanel(self.pet, t.current_opponent())
        elif k == "escape":
            return ("done", t.last if t.over else None)
        return None

    def _frames(self, num, role="idle"):
        rec = data.load_sprites()[1][num]
        roles = data.ROLES.get(role, data.ROLES["idle"])
        idx = roles[self.frame_i % len(roles)]
        return rec["frames"][idx] or rec["frames"][0]

    def _prize_bits(self, tr):
        base = tournament.TOURNEY_BITS.get(self.pet.stage, 125)
        return min(tournament.TOURNEY_MAX_BITS, int(base * tr["bit_mod"]))

    def text(self):
        if self.sub is not None:
            return self.sub.text()
        if self.phase == "none":
            out = menu.header("CUP", self.pet.season)
            out.append_text(menu.blanks(1))
            out.append_text(menu.row("No cup open this season."))
            out.append_text(menu.blanks(3))
            out.append_text(menu.note("Cups rotate by season & your field."))
            out.append_text(menu.footer("ESC leave"))
            return out
        if self.phase == "select":
            out = menu.header("CUP", self.pet.season)
            n = len(self.trophies)
            vis = 5
            lo = max(0, min(self.cursor - vis // 2, n - vis))
            shown = 0
            for i in range(lo, min(lo + vis, n)):
                tr = self.trophies[i]
                extra = " +item" if tr["item"] >= 0 else ""
                label = "%-21s %db%s" % (tournament.trophy_label(tr)[:21], self._prize_bits(tr), extra)
                out.append_text(menu.row(label, i == self.cursor))
                shown += 1
            out.append_text(menu.blanks(vis - shown))
            out.append_text(menu.note("Pick a cup to enter (%d open)." % n))
            out.append_text(menu.footer("up/dn pick  ENTER enter  ESC out"))
            return out
        # bracket
        t = self.tourney
        bgimg = self.pet.background()
        on = SIL_NIGHT if self.pet.day_phase == "night" else (SIL_DAY if bgimg else LCD_ON)
        if t.over:
            out = menu.bar(t.name, "RESULT")
            pose = "happy" if t.champion else "tired"
            scene = render_scene([(self._frames(self.pet.num, pose), (COLS - 16) // 2, False)],
                                 COLS, ROWS, on, LCD_BG, bgimg=bgimg)
            out.append_text(scene)
            if t.champion:
                out.append("\n%s\n" % ("★" * min(self.pet.trophies, 14)), style=INK_B)
            else:
                out.append("\n\n")
            out.append_text(menu.note(t.last))
            out.append_text(menu.footer("ESC leave"))
            return out
        opp = t.current_opponent()
        pet_rows = self._frames(self.pet.num)
        opp_rows = self._frames(opp["num"])
        ow = max(len(r) for r in opp_rows)
        scene = render_scene([(pet_rows, 2, True), (opp_rows, COLS - ow - 2, False)],
                             COLS, ROWS, on, LCD_BG, bgimg=bgimg)
        out = menu.bar(t.name, "%s %d/3" % (t.round_name, t.round + 1))
        out.append_text(scene)
        out.append("\nvs %s[%s]   Trophy %d\n" % (opp["name"], opp["attribute"][:2], self.pet.trophies), style=INK)
        out.append_text(menu.note(t.last))
        out.append_text(menu.footer("SPACE fight   ESC leave"))
        return out
