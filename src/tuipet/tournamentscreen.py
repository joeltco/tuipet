"""Tournament — pick an hourly cup, then fight its bracket, in the display box."""
from __future__ import annotations
from . import data
from . import tournament
from .tournament import Tournament
from .battlescreen import BattlePanel
from .render import render_scene
from . import grid

from .theme import LCD_ON, LCD_BG, INK, INK_B, DIM, SIL_SCENE, SIL_LIGHTSOFF  # noqa: F401  (palette names bound for theme.apply propagation)
from . import menu
COLS, ROWS = 40, 7
# the bracket/result scenes only carry ONE info line + note + footer below the bar,
# so they afford an 8-row (16px) box -> a 14px band: most creatures render at
# native size (crop-first fit), only full-16px sprites get a gentle 16->14 fit
FIGHT_ROWS = 12   # the ONE locked arena (was a squat 8-row band that
#                   cropped the scenery, then the fight itself jumped to 12)

# the CUP THEATER (fun arc 2026-07-21, Joel: "do the award ceremony and npc
# rounds"): the two dead moments between fights come alive -- the field's
# other winners PARADE across the arena after each of your wins (the
# adventure parade's idiom on the cup stage), and the crown gets its
# AWARD CEREMONY: the champion cheering under a pulsing arena light (the
# zoneChange idiom) before the tree and the numbers.  Real art only; the
# shows lock input and play out (own-game law: no skips).
NPC_T = 20        # ticks per advancing winner's crossing
CEREMONY_T = 40   # the podium beat

# MATCH INTRODUCTIONS (fun arc, Joel: "do the match introductions"): SPACE
# on the faceoff page stages the walk-ins before the bell -- the challenger
# strides in from the RIGHT and is announced, your mon answers from the
# LEFT, both hold the faceoff, then the fight opens itself.  The faceoff
# page stays the decision point; the intro is the committed entrance.
INTRO_OPP_T = 14  # the challenger's walk-in
INTRO_PET_T = 14  # your mon's answer
INTRO_HOLD_T = 10 # the held stare-down, then the bell


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
        self._advance = None         # the field-advances parade: {"t","nums"}
        self._ceremony = None        # the champion's podium beat: {"t"}
        self._intro = None           # the match introductions: {"t"}

    def anim(self):
        if self.sub_anim():          # SubHost: delegate + sfx bubble
            return
        self.frame_i += 1
        if self._ceremony is not None:
            self._ceremony["t"] += 1
            if self._ceremony["t"] >= CEREMONY_T:
                self._ceremony = None
                self.tree_view = True          # the crowned tree, then the numbers
            return
        if self._advance is not None:
            self._advance["t"] += 1
            if self._advance["t"] >= NPC_T * max(1, len(self._advance["nums"])):
                self._advance = None
                self.tree_view = True          # the field, freshly advanced
            return
        if self._intro is not None:
            self._intro["t"] += 1
            if self._intro["t"] >= INTRO_OPP_T + INTRO_PET_T + INTRO_HOLD_T:
                self._intro = None             # the bell: the fight opens itself
                self.sub = BattlePanel(self.pet, self.tourney.current_opponent())
            return

    def strip(self):
        """The message-box hint line (hint overhaul 2026-07-10)."""
        if self.sub is not None:
            return ""                          # the bout's own panel owns the box
        if self._ceremony is not None:
            return "[b]★ CHAMPION![/]"
        if self._advance is not None:
            return "[dim]the field advances…[/]"
        if self._intro is not None:
            return "[dim]introductions…[/]"
        if self.phase == "select":
            return menu.hints(("↑↓", "pick"), ("ENTER", "go"),
                              ("F", "feat."), ("A", "alarm"))
        return menu.hints(("SPACE", "fight on"), ("B", "bracket"),
                          ("ESC", "leave"))

    def key(self, k):
        if self.sub is not None:
            r = self.sub.key(k)
            if r is not None and r[0] == "done":
                self.sub = None
                if r[1] is None:
                    # ESC before the bell: no volley rolled -- backing out
                    # returns to the bracket with the match still owed (the
                    # raid's rule for the same signal).  Recording it as a
                    # loss made the "back out" hint a silent stake-losing
                    # forfeit (gameplay audit 2026-07-19); walking out of
                    # the CUP stays the labeled forfeit on the bracket ESC.
                    self.tree_view = True
                    self.tourney.last = "You back out — the match still waits."
                    self.sfx = "refuse"
                    return None
                won = bool(r[1].won)
                opp = self.tourney.current_opponent()   # before the bracket moves
                self.tourney.record(won)
                if won and isinstance(opp, dict) and opp.get("rival"):
                    # REVENGE: the grudge is settled, the slate wiped
                    self.pet.rival_num, self.pet.rival_name = -1, ""
                    self.tourney.last = ("REVENGE on %s! The grudge is settled."
                                         % opp["name"])
                    self.sfx = "happy"
                if self.tourney.over:                   # cup finished this match
                    self.sfx = "champion" if self.tourney.champion else "lose"
                    if self.tourney.champion:
                        self._ceremony = {"t": 0}       # the podium beat first
                    else:
                        self.tree_view = True           # eliminated: the tree...
                        if isinstance(opp, dict):       # ...and the beater becomes
                            self.pet.rival_num = opp.get("num", -1)   # THE RIVAL
                            self.pet.rival_name = opp.get("name", "")
                elif won and getattr(self.tourney, "results_nums", None):
                    # your win advances the FIELD too: parade the other
                    # winners across before the tree
                    self._advance = {"t": 0,
                                     "nums": list(self.tourney.results_nums)}
                else:
                    self.tree_view = True               # backed out: the tree waits
            return None
        if self.phase == "select":
            n = len(self.sched)
            if k in ("up", "k"):
                self.cursor = (self.cursor - 1) % n
            elif k in ("down", "j"):
                self.cursor = (self.cursor + 1) % n
            elif k in ("pageup", "pagedown"):   # 24 hourly slots, 5 on screen
                self.cursor = menu.page_step(self.cursor, n, 5, k)
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
        if (self._ceremony is not None or self._advance is not None
                or self._intro is not None):
            return None                        # the show plays out (no skips)
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
            self._intro = {"t": 0}             # the introductions, then the bell
            self.sfx = "menu"
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
            if e == "YOU":
                s = self.pet.name or "YOU"
            else:                              # the rival wears its grudge mark
                s = ("!" if e.get("rival") else "") + e["name"]
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
            # two-space gap: "quarterfinal" runs the line to exactly 38 --
            # three spaces clipped "ESC forfeit" to "ESC forfei" (menu audit
            # 2026-07-21; menu.footer hard-cuts at W)
            out.append_text(menu.footer("SPACE to the %s  ESC forfeit" % t.round_name.lower()))
        return out

    def _frames(self, num, role="idle"):
        # the standard ~2Hz WALK_BEAT bob -- this screen alone flipped poses
        # every 0.1s tick (a 10Hz flutter, accidental drift; calmed to match
        # the rest, Joel 2026-07-05)
        return data.bob_frame(num, self.frame_i, role)

    def _ceremony_frame(self):
        """THE AWARD CEREMONY: the champion cheers centre-stage while the
        arena light pulses bright (the zoneChange idiom) -- the podium beat
        the crown never had.  Mirrors the result page's shape exactly (one
        layout language per screen family)."""
        from .adventurescreen import _brighten
        t = self._ceremony["t"]
        bgimg = self.pet.background(file="tourneyBack")
        if bgimg and any(a <= t % 20 < b for a, b in ((3, 8), (12, 17))):
            bgimg = _brighten(bgimg, 0.5)      # the podium light, on the beat
        on = menu.scene_ink(bgimg)
        out = menu.bar(self.tourney.name, "CHAMPION")
        scene = render_scene([grid.center(self._frames(self.pet.num, "happy"),
                                          ph=FIGHT_ROWS * 2)],
                             COLS, FIGHT_ROWS, on, LCD_BG, bgimg=bgimg)
        out.append_text(scene)
        out.append("\n%s\n" % ("★" * min(self.pet.trophies, 14)), style=INK_B)
        out.append_text(menu.note("The trophy is yours!", tick=self.frame_i))
        out.append_text(menu.footer("— the crowd roars —"))
        return out

    def _advance_frame(self):
        """THE FIELD ADVANCES: the other winners cross the arena one at a
        time (the parade idiom on the cup stage) before the bracket page
        lands -- the tournament happening AROUND you, visible at last."""
        a = self._advance
        i = min(a["t"] // NPC_T, len(a["nums"]) - 1)
        t = a["t"] % NPC_T
        fr = data.frames_for(a["nums"][i])
        wi = data.ROLES["walk"][(t // 3) % 2]
        rows = grid.prep((fr[wi] if wi < len(fr) else None) or fr[0],
                         ph=FIGHT_ROWS * 2)
        lo, hi = grid.roam_bounds(grid.width(rows))
        x = round(hi + (lo - hi) * (t / max(1, NPC_T - 1)))
        bgimg = self.pet.background(file="tourneyBack")
        scene = render_scene([(rows, x, False)], COLS, FIGHT_ROWS,
                             menu.scene_ink(bgimg), LCD_BG, bgimg=bgimg)
        out = menu.bar(self.tourney.name, "ADVANCING")
        out.append_text(scene)
        nm = (self.tourney.results[i]
              if i < len(self.tourney.results) else "")
        out.append("\n%s advances\n" % nm, style=INK)
        out.append_text(menu.note(self.tourney.last, tick=self.frame_i))
        out.append_text(menu.footer("— the next round forms —"))
        return out

    def _intro_frame(self):
        """MATCH INTRODUCTIONS: the challenger strides in from the RIGHT and
        is announced, your mon answers from the LEFT, both hold the
        stare-down -- then the bell (anim opens the fight).  The corners are
        grid.faceoff's own, so the entrance lands exactly where the fight
        stands."""
        t = self._intro["t"]
        opp = self.tourney.current_opponent()
        pet_rows = self._frames(self.pet.num, "walk" if t >= INTRO_OPP_T else "idle")
        opp_rows = self._frames(opp["num"], "walk" if t < INTRO_OPP_T else "idle")
        left, right = grid.faceoff(pet_rows, opp_rows, left_mirror=True,
                                   right_mirror=False, ph=FIGHT_ROWS * 2)
        lrows, lx, lm = left
        rrows, rx, rm = right
        placements = []
        if t < INTRO_OPP_T:                    # the challenger walks in
            p = t / max(1, INTRO_OPP_T - 1)
            placements = [(rrows, round(grid.X1 + (rx - grid.X1) * p), rm)]
            note = ("%s — your RIVAL!" % opp["name"] if opp.get("rival") else
                    "%s [%s] enters!" % (opp["name"], opp["attribute"][:2]))
        elif t < INTRO_OPP_T + INTRO_PET_T:    # your mon answers
            p = (t - INTRO_OPP_T) / max(1, INTRO_PET_T - 1)
            lw = grid.width(lrows)
            placements = [(lrows, round((grid.X0 - lw) + (lx - (grid.X0 - lw)) * p), lm),
                          (rrows, rx, rm)]
            note = ("%s answers!" % self.pet.name if self.pet.name
                    else "You answer!")           # unnamed: "YOU answers!" was bad grammar
        else:                                  # the held stare-down
            placements = [(lrows, lx, lm), (rrows, rx, rm)]
            note = "%s — FIGHT!" % self.tourney.round_name
        bgimg = self.pet.background(file="tourneyBack")
        scene = render_scene(placements, COLS, FIGHT_ROWS,
                             menu.scene_ink(bgimg), LCD_BG, bgimg=bgimg,
                             clip=grid.WINDOW)
        out = menu.bar(self.tourney.name,
                       "%s %d/3" % (self.tourney.round_name, self.tourney.round + 1))
        out.append_text(scene)
        out.append("\nvs %s[%s]   Trophy %d\n"
                   % (opp["name"], opp["attribute"][:2], self.pet.trophies),
                   style=INK)
        out.append_text(menu.note(note, tick=self.frame_i))
        out.append_text(menu.footer("— introductions —"))
        return out

    def text(self):
        if self.sub is not None:
            return self.sub.text()
        if self._ceremony is not None:
            return self._ceremony_frame()
        if self._advance is not None:
            return self._advance_frame()
        if self._intro is not None:
            return self._intro_frame()
        if self.phase == "select":
            self.sched = tournament.schedule(self.pet)   # live: a day rollover re-rolls
            hour = tournament._hour(self.pet)
            out = menu.header("CUP", "%02d:00" % hour)

            def fmt(tid, i):
                tr = tournament.trophy_by_id(tid) if tid >= 0 else None
                name = tournament.trophy_label(tr)[:22] if tr else "\u2014"
                if tr and tid in (getattr(self.pet, "trophies_won", None) or {}):
                    # a cup you HOLD: entering again is a title defense
                    name = ("\u265b" + name)[:22]
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
                # tag <= 12: "  \u2605 " + 20-char label + " \u00b7 " + tag must fit
                # the 40-col box (cup audit 2026-07-21: the old 21-char tag
                # ran the row to 44 and clipped)
                tag = "run today" if done else "F \u00b7 any hour"
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
