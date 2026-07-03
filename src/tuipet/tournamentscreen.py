"""Tournament — pick a seasonal cup, then fight its bracket, in the display box."""
from __future__ import annotations
from . import data
from . import tournament
from .tournament import Tournament
from .battlescreen import BattlePanel
from .render import render_scene
from . import grid

from .theme import LCD_ON, LCD_BG, INK, INK_B, DIM, SIL_DAY, SIL_NIGHT  # noqa: F401  (palette names bound for theme.apply propagation)
from . import menu
COLS, ROWS = 40, 7
# the bracket/result scenes only carry ONE info line + note + footer below the bar,
# so they afford an 8-row (16px) box -> a 14px band: most creatures render at
# native size (crop-first fit), only full-16px sprites get a gentle 16->14 fit
FIGHT_ROWS = 8


class TournamentPanel:
    def __init__(self, pet):
        self.pet = pet
        self.frame_i = 0
        self.sub = None
        self.tourney = None
        self.sched = tournament.schedule(pet)      # today's 24 hourly cups
        self.cursor = tournament._hour(pet)        # start the list on NOW
        self.msg = "One cup per hour — only NOW is open."
        self.phase = "select"

    def anim(self):
        if self.sub is not None:
            self.sub.anim()
            self.sfx = getattr(self.sub, "sfx", None)   # bubble nested battle sfx up to on_frame's drain
            self.sub.sfx = None
            return
        self.frame_i += 1

    def key(self, k):
        if self.sub is not None:
            r = self.sub.key(k)
            if r is not None and r[0] == "done":
                self.tourney.record(bool(r[1] and r[1].won))
                self.sub = None
                if self.tourney.over:                   # cup finished this match
                    self.sfx = "champion" if self.tourney.champion else "lose"
            return None
        if self.phase == "select":
            n = len(self.sched)
            if k in ("up", "k"):
                self.cursor = (self.cursor - 1) % n
            elif k in ("down", "j"):
                self.cursor = (self.cursor + 1) % n
            elif k in ("enter", "space"):
                # checkTourneyClosed: only the current hour's cup takes entries
                hour = tournament._hour(self.pet)
                tr = tournament.open_now(self.pet)
                if self.cursor != hour or tr is None:
                    self.msg = "That cup is closed — only the %02d:00 one runs now." % hour
                    self.sfx = "error"
                    return None
                err = tournament.eligibility(self.pet, tr)   # isEligible
                if err:
                    self.msg = err
                    self.sfx = "error"
                    return None
                self.tourney = Tournament(self.pet, tr)
                self.phase = "bracket"
            elif k == "a":
                # onTourneyAlarm: toggle the wake-me call on this slot's cup
                tid = self.sched[self.cursor] if 0 <= self.cursor < len(self.sched) else -1
                if tid >= 0:
                    if self.pet.tourney_alarm == tid:
                        self.pet.tourney_alarm = -1
                        self.msg = "Alarm off."
                    else:
                        self.pet.tourney_alarm = tid
                        self.msg = "Alarm set — it will call you at %02d:00." % self.cursor
                    self.sfx = "confirm"
            elif k in ("escape", "u"):          # u (the opening key) also closes
                return ("done", None)
            return None
        # bracket
        t = self.tourney
        if k in ("space", "enter") and not (t.over or self.sub):
            self.sub = BattlePanel(self.pet, t.current_opponent())
        elif k in ("escape", "u"):          # u (the opening key) also closes
            return ("done", t.last if t.over else None)
        return None

    def _frames(self, num, role="idle"):
        rec = data.load_sprites()[1][num]
        roles = data.ROLES.get(role, data.ROLES["idle"])
        idx = roles[self.frame_i % len(roles)]
        return rec["frames"][idx] or rec["frames"][0]

    def text(self):
        if self.sub is not None:
            return self.sub.text()
        if self.phase == "select":
            hour = tournament._hour(self.pet)
            out = menu.header("CUP", "%s %02d:00" % (self.pet.season, hour))
            n = len(self.sched)
            vis = 5
            lo = max(0, min(self.cursor - vis // 2, n - vis))
            shown = 0
            for i in range(lo, min(lo + vis, n)):
                tr = tournament.trophy_by_id(self.sched[i]) if self.sched[i] >= 0 else None
                name = tournament.trophy_label(tr)[:22] if tr else "—"
                extra = " +item" if (tr and tr["item"] >= 0) else ""
                mark = "» OPEN" if i == hour else ""
                if tr and self.pet.tourney_alarm == tr["id"]:
                    mark = (mark + " ♦alarm").strip()
                label = "%02dh %-22s%s %s" % (i, name, extra, mark)
                out.append_text(menu.row(label, i == self.cursor))
                shown += 1
            out.append_text(menu.blanks(vis - shown))
            out.append_text(menu.note(self.msg))
            out.append_text(menu.footer("↑↓ browse ENTER enter A alarm ESC out"))
            return out
        # bracket
        t = self.tourney
        bgimg = self.pet.background()
        on = SIL_NIGHT if self.pet.day_phase == "night" else (SIL_DAY if bgimg else LCD_ON)
        if t.over:
            out = menu.bar(t.name, "RESULT")
            pose = "happy" if t.champion else "tired"
            scene = render_scene([grid.center(self._frames(self.pet.num, pose), ph=FIGHT_ROWS * 2)],
                                 COLS, FIGHT_ROWS, on, LCD_BG, bgimg=bgimg)
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
        scene = render_scene(grid.faceoff(pet_rows, opp_rows, left_mirror=True, right_mirror=False, ph=FIGHT_ROWS * 2),
                             COLS, FIGHT_ROWS, on, LCD_BG, bgimg=bgimg)
        out = menu.bar(t.name, "%s %d/3" % (t.round_name, t.round + 1))
        out.append_text(scene)
        out.append("\nvs %s[%s]   Trophy %d\n" % (opp["name"], opp["attribute"][:2], self.pet.trophies), style=INK)
        out.append_text(menu.note(t.last))
        out.append_text(menu.footer("SPACE fight   ESC leave"))
        return out
