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

_MENU = (("shop", "Shop"), ("eggs", "Eggs"), ("sell", "Sell"),
         ("cup", "Town Cup"), ("leave", "Leave"))


class TownPanel(menu.SubHost):
    def __init__(self, pet, town_id=None):
        self.pet = pet
        self.town_id = town_id
        self.cursor = 0
        self.sub = None
        self.tourney = None            # a running town-cup bracket (sub is its match)
        self._cup_done = False         # the cup runs ONCE per town visit
        self.frame_i = 0
        self.sfx = None
        # <= 38 cols: the hub body clips hard, no marquee (sheet audit
        # 2026-07-21 caught the old line dying mid-word at "resupply, o")
        self.msg = "A town on the road — rest up, shop."

    def anim(self):
        if self.sub_anim():            # the shop / cup match owns the clock
            return
        self.frame_i += 1

    # -- input ----------------------------------------------------------------
    def key(self, k):
        if self.sub_key(k, self._cup_match_done if self.tourney is not None
                        else self._sub_done):
            return None
        if k in ("up", "k"):
            self.cursor = (self.cursor - 1) % len(_MENU)
        elif k in ("down", "j"):
            self.cursor = (self.cursor + 1) % len(_MENU)
        elif k in ("enter", "space"):
            key = _MENU[self.cursor][0]
            if key == "shop":
                from .shopscreen import ShopPanel
                # the real shop layout, serving THIS town's authored stock,
                # local prices, and the day's deal (shops arc 2026-07-21)
                self.sub = ShopPanel(self.pet, town_id=self.town_id)
            elif key == "eggs":
                from .towneggscreen import TownEggPanel
                # this town's DISTINCT egg stock, as real 8x8 thumbnails
                self.sub = TownEggPanel(self.pet, self.town_id)
            elif key == "sell":
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

    def _sub_done(self, _result):
        self.msg = "Anything else?"              # the shop closed -> back to the menu

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
        cup = tournament.town_cup(self.pet, self.town_id)
        fee = tournament.entry_fee(self.pet, cup)
        if self.pet.bits < fee:
            self.msg = f"Stake {fee}b — you can't cover it."
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
