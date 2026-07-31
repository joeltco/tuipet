"""Adventure town hub (rebuild 2026-07-20): a visitable stop on the road.

The old town was a full hub (Food · Items · Eggs · Sell · Cups) via a web of
helpers that left with the town system.  Rebuilt in phases: T1 = the enterable
hub with a working SHOP (the real ShopPanel, reused).  T4 = a DISTINCT road-only
TOWN CUP -- its own trophy (tournament.town_cup, id 900+), an open bracket run
by the real Tournament engine, one per town visit.  Later: Sell, Eggs.

A SubHost: the shop OR a cup match rides as a child (the old town hosted both);
returns ('done', None) to the adventure when the pet leaves.
"""
from __future__ import annotations
from . import menu, tournament
from .theme import INK, INK_B, DIM, POS  # noqa: F401  (theme.apply propagation)

# ⭐ "Sell" WAS A LIE ABOUT THE MOST IMPORTANT DOOR IN A TOWN (road item audit
# 2026-07-31, Joel: "do 1").  This row opens the REAL BAG -- ENTER uses, R
# sells -- and it is the ONLY place in a whole 40-leg run where a pet can eat,
# take a pill, mend a wound or drink its tank back up (the open road reaches
# exactly five transport tickets; every global key is stopped while a panel
# owns the keyboard).  A tamer walking a starving pet past a town read "Sell"
# and kept walking.  Name what the door does.
_MENU = (("shop", "Shop"), ("eggs", "Eggs"), ("bag", "Bag — eat, mend, sell"),
         ("cup", "Town Cup"), ("leave", "Leave"))


# the session's last hub pick: a multi-town run re-entered every hub on
# "shop" (QOL sweep 2026-07-23).  Session-only, like the shop's memory.
_LAST_CURSOR = [0]


class TownPanel(menu.SubHost):
    def __init__(self, pet, town_id):
        # town_id is REQUIRED (audit 2026-07-25): None silently meant the
        # HOME counter -- full unrationed catalog, Honors tab, and town 0's
        # trophy -- in a constructor whose whole job is "this town"
        self.pet = pet
        self.town_id = town_id
        self.cursor = _LAST_CURSOR[0] % len(_MENU)
        self.sub = None
        self.tourney = None            # a running town-cup bracket (sub is its match)
        self._cup_done = False         # the cup runs ONCE per town visit
        self.frame_i = 0
        self.sfx = None
        # <= 38 cols: the hub body clips hard, no marquee (sheet audit
        # 2026-07-21 caught the old line dying mid-word at "resupply, o")
        self.msg = "A town — rest, eat, mend, shop."

    def anim(self):
        if self.sub_anim():            # the shop / cup match owns the clock
            return
        self.frame_i += 1

    # -- input ----------------------------------------------------------------
    def key(self, k):
        if self.sub_key(k, self._cup_match_done if self.tourney is not None
                        else self._sub_done):
            return None
        if self.pet.dead:
            # a lethal bag item (the poison mushroom is a real road find):
            # the verdict has spoken on the strip; any key closes the hub
            # so the run can end and the memorial take over (audit 2026-07-25)
            return ("done", None)
        if k in ("up", "k"):
            self.cursor = (self.cursor - 1) % len(_MENU)
            _LAST_CURSOR[0] = self.cursor
        elif k in ("down", "j"):
            self.cursor = (self.cursor + 1) % len(_MENU)
            _LAST_CURSOR[0] = self.cursor
        elif k in ("enter", "space"):
            key = _MENU[self.cursor][0]
            if key == "shop":
                from .shopscreen import ShopPanel
                # the real shop layout, serving THIS town's authored stock,
                # local prices, and the day's deal (shops arc 2026-07-21)
                self.sub = ShopPanel(self.pet, town_id=self.town_id)
            elif key == "eggs":
                from .shopscreen import ShopPanel
                # this town's DISTINCT egg band, on the SHOP's own Eggs tab
                # (shops-look-the-same 2026-07-22: the one-off thumbnail
                # grid made the town's egg counter a different UI from
                # every other shelf -- one shop family now, one layout)
                self.sub = ShopPanel(self.pet, town_id=self.town_id,
                                     start_tab="Eggs")
            elif key == "bag":
                from .shopscreen import ShopPanel
                # the real bag (use / sell back), same layout as home --
                # paying THIS town's rates: demand goods fetch 70%, its own
                # stock a pittance (buy-low/sell-high, shops arc 2026-07-21)
                self.sub = ShopPanel(self.pet, start_mode="bag", bag_only=True,
                                     town_id=self.town_id)
            elif key == "cup":
                self._start_cup()
            elif key == "leave":
                return ("done", None)            # back to the road
        elif k in ("escape",):
            return ("done", None)
        return None

    def _sub_done(self, result):
        """The shop/bag closed.  The payloads _after_shop PLAYS at home (eat
        fx, evolution strobe, item scripts) have no LCD here, so the town
        SPEAKS them -- SHOW-FLOW: a show plays or speaks (audit 2026-07-25:
        a road-town poison mushroom killed with the strip reading 'Anything
        else?', and a crest egg swapped the species in silence)."""
        r = result if isinstance(result, tuple) else ()
        kind = r[0] if r else None
        if kind == "eat" and len(r) > 2 and r[2]:
            self.msg = str(r[2])
        elif kind == "item_use" and len(r) > 3 and r[3]:
            self.msg = str(r[3])
        elif kind == "evolve":
            self.msg = f"...evolved into {self.pet.name}!"
        elif kind == "inherit":
            self.msg = "The memory settles in."
        else:
            self.msg = "Anything else?"          # a plain browse -> back to the menu

    # -- the town cup ---------------------------------------------------------
    def _start_cup(self):
        """Enter the distinct town championship (one per visit)."""
        if self._cup_done:
            self.msg = "The Town Cup has run — come back next visit."
            return
        # the SAME pet gates the home board runs (cup audit 2026-07-21: the
        # town cup skipped them -- the exact gap the 2026-07-19 audit closed
        # for home cups; a starving/sick/napping pet could grind three
        # recorded bouts).  can_enter wakes a dozing entrant like every
        # care key; battle_condition is the ONE bout-condition source.
        reason = tournament.can_enter(self.pet) or self.pet.battle_condition()
        if reason:
            self.msg = reason
            return
        # THE SHARED HOURLY CADENCE (live-play audit 2026-07-25): entering
        # ANY cup spends the pet's cup-hour slot -- Tournament.__init__ has
        # always burned it -- but this door never CHECKED it.  Wrong both
        # ways: with the world clock parked on the road, a march-and-flee
        # loop re-entered the town cup every arrival (the exact "~1,500b a
        # minute" farm the hour rule exists to close -- measured: 100 cups,
        # +47,632 bits, 0.0 game-seconds), and each entry silently killed
        # that hour's HOME cup.  One slot, both doors.
        # ROLL THE DAY FIRST (audit 2026-07-25): schedule() is the one
        # place fought_hours resets on a game-day rollover, and only the
        # HOME board called it -- so yesterday's burned hours held this
        # door shut until the player happened to open the home cup screen
        tournament.schedule(self.pet)
        if tournament._hour(self.pet) in (getattr(self.pet, "fought_hours", None) or []):
            self.msg = "The cup hour is spent — the next starts on the hour."
            return
        cup = tournament.town_cup(self.pet, self.town_id)
        if (stake := tournament._stake_check(self.pet, cup)):
            # the ONE stake gate (audit 2026-07-25: this door hand-copied
            # the rule with its own wording -- the drift the 2026-07-18
            # review collapsed at home)
            self.msg = stake
            return
        self._cup_done = True                    # your cup for this visit, win or lose
        # THE FIGHT SCENE (the cups arc's parked item, ruled 2026-07-22):
        # the town cup rides the SAME shipped machinery as the home board --
        # TournamentPanel entered at the bracket (the field of eight), so the
        # faceoff, walk-in introductions, advancing-field parade and the
        # champion's podium all play here too.  The raw BattlePanel jump had
        # the town cup fighting three bare bouts with none of the show.
        from .tournamentscreen import TournamentPanel
        pan = TournamentPanel(self.pet)
        pan.tourney = tournament.Tournament(self.pet, cup)    # stake paid on entry
        pan.phase = "bracket"
        pan.tree_view = True                     # the event opens on the field
        self.sfx = "mischief"                    # tourneyStart, like the home board
        self.tourney = pan.tourney               # the visit flag's live handle
        self.sub = pan

    def _cup_match_done(self, result):
        """The cup panel closed: ('done', (last, champion)) from the bracket,
        or None from its select-phase escape (unreachable here -- the panel
        never enters select)."""
        self.tourney = None
        if isinstance(result, tuple):
            last, champ = result
            self.sfx = "champion" if champ else "lose"
            self.msg = last or ("Town champion!" if champ
                                else "Knocked out of the Town Cup.")
        else:
            self.msg = "You forfeit the Town Cup."

    # -- render ---------------------------------------------------------------
    def strip(self):
        if self.sub is not None:
            return self.sub.strip()
        return menu.hints(("↑↓", "pick"), ("ENTER", "go"), ("ESC", "leave"))

    def text(self):
        if self.sub is not None:
            return self.sub.text()
        out = menu.header("TOWN", "")
        menu.list_window(out, list(_MENU), self.cursor, 6, lambda row, _i: row[1])
        out.append_text(menu.blanks(1))
        out.append_text(menu.note(self.msg, tick=self.frame_i))
        out.append_text(menu.footer("↑↓ pick   ENTER go   ESC leave"))
        return out
