"""Tournament — pick an hourly cup, then fight its bracket, in the display box."""
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
FIGHT_ROWS = 12   # the ONE locked arena (was a squat 8-row band that
#                   cropped the scenery, then the fight itself jumped to 12)


class TournamentPanel(menu.SubHost):
    def __init__(self, pet):
        self.pet = pet
        self.frame_i = 0
        self.sub = None
        self.tourney = None
        self.sched = tournament.schedule(pet)      # today's 24 hourly cups
        self.cursor = tournament._hour(pet)        # start the list on NOW
        fest = tournament.holiday()
        self.msg = (f"{fest} — every cup runs today!" if fest
                    else "One cup per hour — F fights today's featured.")
        self.phase = "select"
        self.tree_view = False       # the bracket page (B toggles; shown between rounds)

    def anim(self):
        if self.sub_anim():          # SubHost: delegate + sfx bubble
            return
        self.frame_i += 1

    def strip(self):
        """The message-box hint line (hint overhaul 2026-07-10)."""
        if self.sub is not None:
            return ""                          # the bout's own panel owns the box
        if self.phase == "select":
            return menu.hints(("↑↓", "pick"), ("ENTER", "go"),
                              ("F", "feat."), ("A", "alarm"))
        return menu.hints(("SPACE", "fight on"), ("B", "bracket"),
                          ("ESC", "leave"))

    def key(self, k):
        if self.sub is not None:
            r = self.sub.key(k)
            if r is not None and r[0] == "done":
                self.tourney.record(bool(r[1] and r[1].won))
                self.sub = None
                self.tree_view = True                   # show the field advancing
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
                # checkTourneyClosed: only the current hour's cup takes
                # entries -- except on a FESTIVAL day, when every un-run
                # slot is open (cadence layer 2026-07-17)
                tid = self.sched[self.cursor] if 0 <= self.cursor < n else -1
                tr = tournament.trophy_by_id(tid) if tid >= 0 else None
                if tr is None:
                    self.msg = "No cup in that slot."
                    self.sfx = "error"
                    return None
                err = tournament.eligibility_at(self.pet, tr, self.cursor)
                if err:
                    self.msg = err
                    self.sfx = "error"
                    return None
                self.tourney = Tournament(self.pet, tr, slot=self.cursor)
                self.phase = "bracket"
                self.tree_view = True          # the event opens on the field of eight
                self.sfx = "mischief"          # soundConfig tourneyStart -> mischief.wav
            elif k == "f":
                # today's FEATURED cup: any hour, once per real day
                tr = tournament.featured_now(self.pet)
                if tr is None:
                    self.msg = "No featured cup today."
                    self.sfx = "error"
                    return None
                err = tournament.eligibility_featured(self.pet, tr)
                if err:
                    self.msg = err
                    self.sfx = "error"
                    return None
                self.tourney = Tournament(self.pet, tr, featured=True)
                self.phase = "bracket"
                self.tree_view = True
                self.sfx = "mischief"
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
        if k == "b":
            self.tree_view = not self.tree_view
            return None
        if k in ("space", "enter") and self.tree_view and not t.over:
            self.tree_view = False             # from the field to the faceoff
            return None
        if k in ("space", "enter") and t.over and self.tree_view:
            self.tree_view = False             # from the final tree to the result
            return None
        if k in ("space", "enter") and not (t.over or self.sub):
            self.sub = BattlePanel(self.pet, t.current_opponent())
        elif k in ("escape", "u"):          # u (the opening key) also closes
            if not t.over:
                t.record(False)             # walking out forfeits: the elimination is real
            # carry the VERDICT home: the winner's cheer / loser's sulk plays
            # on the house screen, like the devices (anim hardening 2026-07-14)
            return ("done", (t.last, t.champion))
        return None

    def _render_tree(self):
        """The bracket page: the field of eight and the tree filling in round
        by round (the entrants always existed in the engine; the player just
        never SAW the tournament)."""
        t = self.tourney
        tree = t.tree

        def nm(e, w):
            s = (self.pet.name or "YOU") if e == "YOU" else e["name"]
            return s[:w]

        out = menu.bar(t.name, "BRACKET")
        champ = tree[3][0] if len(tree) > 3 else None
        for i in range(8):
            c1 = nm(tree[0][i], 10)
            c2 = c3 = ""
            if i % 2 == 0 and len(tree) > 1:
                c2 = nm(tree[1][i // 2], 10)
            if i in (0, 4) and len(tree) > 2:
                c3 = nm(tree[2][i // 4], 10)
                if champ is not None and tree[2][i // 4] == champ:
                    c3 += " ★"
            you = (tree[0][i] == "YOU" or c2 and tree[1][i // 2] == "YOU"
                   or c3 and tree[2][i // 4] == "YOU")
            style = INK_B if you else INK
            out.append(" %-11s%-11s%s\n" % (c1, c2, c3),
                       style=style if you else (INK if c1 else DIM))
        out.append_text(menu.note(t.last, tick=self.frame_i))
        if t.over:
            out.append_text(menu.footer("SPACE result   ESC leave"))
        else:
            out.append_text(menu.footer("SPACE to the %s   ESC forfeit" % t.round_name.lower()))
        return out

    def _frames(self, num, role="idle"):
        # the standard ~2Hz WALK_BEAT bob -- this screen alone flipped poses
        # every 0.1s tick (a 10Hz flutter, accidental drift; calmed to match
        # the rest, Joel 2026-07-05)
        return data.bob_frame(num, self.frame_i, role)

    def text(self):
        if self.sub is not None:
            return self.sub.text()
        if self.phase == "select":
            self.sched = tournament.schedule(self.pet)   # live: a day rollover re-rolls
            hour = tournament._hour(self.pet)
            out = menu.header("CUP", "%02d:00" % hour)

            def fmt(tid, i):
                tr = tournament.trophy_by_id(tid) if tid >= 0 else None
                name = tournament.trophy_label(tr)[:22] if tr else "\u2014"
                extra = " +item" if (tr and tr["item"] >= 0) else ""
                mark = "\u00bb OPEN" if i == hour else ""
                if tr and self.pet.tourney_alarm == tr["id"]:
                    mark = (mark + " \u2666alarm").strip()
                return "%02dh %-22s%s %s" % (i, name, extra, mark)

            self.cursor = menu.list_window(out, self.sched, self.cursor, 5, fmt)
            from . import lines as _lines
            wg = _lines.win_gate_progress(self.pet)
            if wg:
                now, need, window = wg
                mark = " \u2713 ready" if now >= need else ""
                out.append("  evolution: %d/%d wins (last %d)%s\n" % (now, need, window, mark),
                           style=INK_B if now >= need else DIM)
            # the stake/purse line describes the cup you'd ACTUALLY enter:
            # on a festival that's the slot under the cursor, not the hour's
            # -- and the shown purse carries the weekend x1.5 the payout
            # does (cup review 2026-07-18)
            tr_line = tournament.open_now(self.pet)
            if tournament.holiday() and 0 <= self.cursor < len(self.sched) \
                    and self.sched[self.cursor] >= 0:
                tr_line = tournament.trophy_by_id(self.sched[self.cursor]) or tr_line
            if tr_line:
                from .pet import weekend_bonus
                fee = tournament.entry_fee(self.pet, tr_line)
                purse = int(fee * tournament.ENTRY_FEE_DIV * weekend_bonus())
                wk = " \u00b7 wknd x1.5" if weekend_bonus() > 1 else ""
                out.append("  stake %db \u00b7 purse ~%db%s\n" % (fee, purse, wk),
                           style=DIM)
            ftr = tournament.featured_now(self.pet)
            if ftr is not None:
                done = tournament.featured_done(self.pet)
                tag = "run today" if done else "F to fight \u00b7 any hour"
                out.append("  \u2605 %s \u00b7 %s\n"
                           % (tournament.trophy_label(ftr)[:20], tag),
                           style=DIM if done else INK_B)
            nw = tournament.next_winnable(self.pet)
            if nw and nw[0] == hour:
                out.append("  \u2713 %s is open NOW\n" % tournament.trophy_label(nw[1])[:24],
                           style=INK_B)
            elif nw:
                out.append("  next winnable %02d:00 %s\n"
                           % (nw[0], tournament.trophy_label(nw[1])[:16]), style=DIM)
            else:
                out.append("  no cup left you can enter today\n", style=DIM)
            out.append_text(menu.note(self.msg, tick=self.frame_i))
            out.append_text(menu.footer("↑↓ browse  ENTER go  A alarm  ESC out"))
            return out
        # bracket
        t = self.tourney
        if self.tree_view:
            return self._render_tree()
        # BackgroundAnim checkBack: while the tournament is active every scene
        # plays in the ARENA (tourneyBack.png), not the home habitat
        bgimg = self.pet.background(file="tourneyBack")
        on = menu.scene_ink(bgimg)
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
            out.append_text(menu.note(t.last, tick=self.frame_i))
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
        out.append_text(menu.note(t.last, tick=self.frame_i))
        out.append_text(menu.footer("SPACE fight   ESC leave"))
        return out
