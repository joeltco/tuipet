"""Adventure — travel a zone, fight encounters/boss, all in the display box."""
from __future__ import annotations
from . import data
from .adventure import Adventure
from .battlescreen import BattlePanel
from .feedscreen import FeedPanel
from .shopscreen import ShopPanel
from .townscreen import TownPanel
from .render import render_scene, downsample
from . import grid
from . import strikefx

from .theme import LCD_ON, LCD_BG, INK, INK_B, DIM, SIL_DAY
from . import menu
COLS, ROWS = 40, 12           # the ONE locked LCD arena, like every other screen

# the investigateLeft playbook (canon SpriteAnim beats in 0.1s ticks): walk out
# to the LEFT goal, suspense dots at 5/10/15, the reveal at 20, done at 25 --
# then tuipet adds the ReturnItem walk-back so the pet never teleports home
INV_WALK_T = 12               # walk-left leg
INV_REVEAL_T = 30             # dots done -> the reveal pose fires
INV_HOLD_T = 42               # reveal held (item shown / startle / dejection)
INV_END_T = 54                # walk-back (ReturnItem) complete
REFUSE_T = 24                 # Refusing: the 24-tick mirror head-shake (fx convention)
PARADE_T = 26                 # victory parade: ticks for one boss to march across
#                               (canon BossParade shows the map's bosses after the
#                               final ZoneChange; one at a time -- one-mon LCD rule)
WALK_BEAT = 5                 # idleWalk pose cadence (anim.WALK_BEAT -- NOT every tick)
FADE_T = 20                   # habitat cross-fade ticks (canon BackgroundAnim.animateBack:
#                               BackgroundOpacityChange -0.05/frame -> 20 frames old-over-new)


def _blend_bg(old, new, t):
    """Per-pixel RGB lerp between two backdrop buffers (rows of packed 6-hex
    colours) -- the halfblock LCD's honest equivalent of canon's alpha fade."""
    out = []
    for ro, rn in zip(old, new):
        row = []
        for i in range(0, min(len(ro), len(rn)) - 5, 6):
            o, n = int(ro[i:i + 6], 16), int(rn[i:i + 6], 16)
            r = round(((o >> 16) & 255) * (1 - t) + ((n >> 16) & 255) * t)
            g = round(((o >> 8) & 255) * (1 - t) + ((n >> 8) & 255) * t)
            b = round((o & 255) * (1 - t) + (n & 255) * t)
            row.append("%02x%02x%02x" % (r, g, b))
        out.append("".join(row))
    return out


class AdventurePanel(menu.SubHost):
    def __init__(self, pet):
        self.pet = pet
        self.adv = Adventure(pet)
        self.frame_i = 0
        self.travelling = True
        self.sub = None
        self._pending = None
        self._travel_t = 0
        self.discovering = False    # DiscoverCall: pause for the investigate prompt
        self.town_prompt = None     # a reached town's id: visit or walk on
        self._refuse_t = 0          # Refusing head-shake ticks left
        self._scene = None          # a running investigateLeft playbook
        self._parade = None         # a running BossParade (map beaten)

    def anim(self):
        if self.sub_anim():          # SubHost: delegate + sfx bubble
            return
        self.frame_i += 1
        if self._refuse_t:
            self._refuse_t -= 1
        fade = getattr(self, "_bg_fade", None)
        if fade is not None:
            fade["t"] += 1                   # the habitat cross-fade clock
        if self._parade is not None:
            self._parade["t"] += 1
            if self._parade["t"] >= PARADE_T * len(self._parade["nums"]):
                self._parade = None
                self.travelling = not self.adv.done
            return
        if self._scene is not None:
            self._scene_tick()
            return
        self._travel_t += 1
        if self._travel_t >= 3 and self.travelling and not self.adv.done:
            self._travel_t = 0
            ev = self.adv.travel()
            if ev and ev[0] in ("encounter", "boss"):
                self.travelling = False
                self._pending = (ev[0] == "boss", ev[1])
                self.sub = BattlePanel(self.pet, ev[1], wild=True)
            elif ev and ev[0] == "town":
                self.sfx = "reward"          # reached the rest-town: life + energy restored
                self.travelling = False
                self.town_prompt = ev[1]     # its gates are open -- visit?
            elif ev and ev[0] == "refused":
                self.travelling = False      # Refusing: travelSpeed 0 -- SPACE re-issues the walk
                self.sfx = "refuse"
                self._refuse_t = REFUSE_T    # the mirror head-shake plays in the arena
            elif ev and ev[0] == "discover":
                self.travelling = False      # DiscoverCall: stop and ask
                self.discovering = True
                self.sfx = "reward"

    def _scene_tick(self):
        """Advance the investigateLeft playbook.  The OUTCOME was decided when
        the scene began (adv.investigate() already applied its side effects);
        these beats are pure presentation, like a battle timeline."""
        s = self._scene
        s["t"] += 1
        if s["t"] == INV_REVEAL_T:
            self.adv.last = s["msg"]                  # the reveal says what it was
            if s["kind"] == "item":
                self.sfx = "reward"                   # _discoverConsumable
        if s["kind"] == "enemy":
            if s["t"] >= INV_REVEAL_T + 6:            # startle beat, then the ambush
                self._pending = (False, s["thing"])
                self.sub = BattlePanel(self.pet, s["thing"], wild=True)
                self._scene = None
        elif s["t"] >= INV_END_T:                     # carried home -> back on the road
            self._scene = None
            self.travelling = True

    def key(self, k):
        if isinstance(self.sub, TownPanel):
            r = self.sub.key(k)
            if r is not None and r[0] == "done":
                self.sub = None
                self.adv.last = "Back on the road."
                self.travelling = True
            return None
        if isinstance(self.sub, (FeedPanel, ShopPanel)):
            # a road-side care panel (road-keys 2026-07-07): the journey holds
            # while it's open; its outcome lands on the strip, no home fx
            pmsg = getattr(self.sub, "msg", "")
            r = self.sub.key(k)
            if r is not None and r[0] == "done":
                pmsg = getattr(self.sub, "msg", "") or pmsg
                self.sub = None
                res = r[1]
                if isinstance(res, tuple) and res:
                    if res[0] in ("fed", "full", "refused"):
                        self.adv.last = res[2]
                    elif res[0] == "evolve":
                        self.adv.last = f"Evolved into {self.pet.name}!"
                    elif res[0] == "inherit":
                        self.adv.last = f"{res[1].get('name', 'The memory')}'s power lives on!"
                    else:                # eat/toilet/play: effect applied in-panel
                        self.adv.last = pmsg or self.adv.last
                elif isinstance(res, str) and res:
                    self.adv.last = res
            return None
        if self.sub is not None:
            r = self.sub.key(k)
            if r is not None and r[0] == "done":
                was_boss, enemy = self._pending
                self._pending = None
                self.sub = None
                if r[1] is None:
                    self.adv.last = "Fled the battle."
                    self.adv.flee(enemy, was_boss=was_boss)  # canEscape: penalty knockback re-arms the boss
                    if was_boss:
                        self.travelling = False         # knocked back from the gate -- SPACE to approach again
                        return None
                else:
                    paraders = None
                    if r[1].won and was_boss and enemy.get("parade_msg"):
                        # canon ZoneChange tail: the beaten FINAL boss cues the
                        # map's bosses to parade -- capture them before resolve()
                        # advances past this map
                        paraders = [bb["num"] for z in self.adv.maps[self.adv.mi]["zones"]
                                    for bb in z["bosses"]][:3]      # canon shows three
                    self.adv.resolve(r[1].won, was_boss, enemy)
                    if paraders:
                        self._parade = {"t": 0, "nums": paraders}
                        self.adv.last = enemy["parade_msg"]         # "You saved the Digital World!"
                        self.sfx = "win"                            # bossParade cue (the parade
                        self.travelling = False                     # track is music, unbundled)
                        return None
                self.travelling = not self.adv.done
            return None
        if getattr(self, "town_prompt", None) is not None:
            if k in ("enter", "y"):
                self.sub = TownPanel(self.pet, self.town_prompt)
                self.town_prompt = None
            elif k in ("escape", "n", "space"):
                self.town_prompt = None
                self.adv.last = "Passed the town by."
                self.travelling = True
            return None
        if getattr(self, "_parade", None) is not None:
            if k in ("space", "enter", "escape"):     # skip to the next marcher / the end
                self._parade["t"] = ((self._parade["t"] // PARADE_T) + 1) * PARADE_T
                if self._parade["t"] >= PARADE_T * len(self._parade["nums"]):
                    self._parade = None
                    self.travelling = not self.adv.done
            return None
        if getattr(self, "_scene", None) is not None:
            if k in ("space", "enter", "escape") and self._scene["t"] < INV_REVEAL_T:
                self._scene["t"] = INV_REVEAL_T - 1   # skip the suspense to the reveal
            return None
        if getattr(self, "discovering", False):
            # Investigate_Validation: ENTER looks, ESC walks on
            if k in ("enter", "y"):
                self.discovering = False
                kind, thing = self.adv.investigate()
                icon = None
                if kind == "item":                    # the find's REAL icon (meatButton)
                    raw = data.load_icons().get(thing["key"])
                    icon = downsample(raw[0], 3) if raw else None
                # the result message stays sealed until the reveal beat
                self._scene = {"t": 0, "kind": kind or "none", "thing": thing,
                               "msg": self.adv.last, "icon": icon}
                self.adv.last = f"{self.pet.name} goes to look..."
            elif k in ("escape", "n", "space"):
                self.discovering = False
                self.adv.last = "Walked on by."
                self.travelling = True
            return None
        # the CARE keys work on the road (Joel 2026-07-07: "arent i supposed to
        # have access to action keys in adventure?" -- canon's device keeps the
        # full button set live while travel runs).  f/i host their panels (the
        # journey holds); h/r/k/s act directly.  Notably k answers the scold
        # window a travel REFUSAL opens -- it was unreachable mid-adventure.
        if k == "f":
            reason = self.pet.can_feed()
            if reason:
                self.adv.last = reason
                self.sfx = "refuse"
            else:
                self.sub = FeedPanel(self.pet)
            return None
        if k == "i":
            self.sub = ShopPanel(self.pet, start_mode="bag")
            return None
        if k == "h":
            self.adv.last = self.pet.heal()
            self.sfx = "confirm"
            return None
        if k == "r":
            self.adv.last = self.pet.praise()
            self.sfx = "confirm"
            return None
        if k == "k":
            self.adv.last = self.pet.scold()
            self.sfx = "refuse"
            return None
        if k == "s":
            self.adv.last = self.pet.toggle_lights()
            self.sfx = "confirm"
            return None
        if k == "space" and not self.adv.done:
            if not self.travelling:
                # re-issuing the walk = DVPet canTravel: checkRefused; checkCompliant
                refused = self.pet.check_refused()
                self.pet.check_compliant()
                if refused:
                    self.adv.last = f"{self.pet.name} refuses to walk!"
                    self.sfx = "refuse"
                    self._refuse_t = REFUSE_T
                    return None
            self.travelling = not self.travelling
        elif k in ("escape", "a"):          # a (the opening key) also closes, like shop/habitat
            if getattr(self, "pet", None) is not None:
                self.pet.go_home_habitat()  # back from the road: home climate resumes
                self.pet.away = False       # canon teleportArrive: home again -- the
                #                             assistant resumes (auto-care audit 2026-07-06)
            return ("done", None)
        return None

    def _rows(self, idx):
        fr = data.frames_for(self.pet.num, getattr(self.pet, "egg_type", 0))
        return grid.prep((fr[idx] if idx < len(fr) else None) or fr[0], ph=ROWS * 2)

    def _jx(self, rows):
        """The journey spot: progress along the walkable grid."""
        lo, hi = grid.roam_bounds(grid.width(rows))
        return lo + int((hi - lo) * (self.adv.pct / 100))

    def _pet_placement(self):
        """(rows, x, mirror, overlay, note_override) for this frame -- the journey
        walk (WALK_BEAT pose flips, per anim.Roamer/idleWalk), the DiscoverCall
        attention bounce (canon attention(5,7)), the Refusing head-shake, or the
        running investigateLeft playbook."""
        p = self._parade
        if p is not None:
            # BossParade: the map's bosses march across, one at a time (canon
            # moveLeft; the LCD's one-mon rule serialises canon's three-abreast)
            i = min(p["t"] // PARADE_T, len(p["nums"]) - 1)
            t = p["t"] % PARADE_T
            fr = data.frames_for(p["nums"][i])
            wi = data.ROLES["walk"][(t // 3) % 2]
            rows = grid.prep((fr[wi] if wi < len(fr) else None) or fr[0], ph=ROWS * 2)
            lo, hi = grid.roam_bounds(grid.width(rows))
            x = round(hi + (lo - hi) * (t / max(1, PARADE_T - 1)))
            return rows, x, False, [], None       # the strip carries the victory message
        s = self._scene
        if s is not None:
            t = s["t"]
            if t < INV_WALK_T:                        # walk out to the LEFT goal
                rows = self._rows(data.ROLES["walk"][(t // 3) % 2])
                x0 = self._jx(rows)
                x = round(x0 + (grid.X0 - x0) * (t / INV_WALK_T))
                return rows, x, False, [], ""         # faces left (native)
            if t < INV_REVEAL_T:                      # suspense: . .. ...
                rows = self._rows(data.ROLES["walk"][0])
                return rows, grid.X0, False, [], "." * min(3, 1 + (t - INV_WALK_T) // 6)
            if t < INV_HOLD_T or s["kind"] == "enemy":   # the reveal
                pose = {"item": 5, "enemy": 6}.get(s["kind"], 9)   # cheer / startle / dejected
                rows = self._rows(pose)
                overlay = []
                if s["kind"] == "item" and s["icon"]:              # the find, held up beside it
                    oy = grid.TOP + (grid.BAND - len(s["icon"])) // 2
                    overlay = strikefx.blit(s["icon"], grid.X0 + grid.width(rows) + 2, oy)
                return rows, grid.X0, False, overlay, None
            # ReturnItem: carry it back to the journey spot (faces right again)
            rows = self._rows(data.ROLES["walk"][(t // 3) % 2])
            x0 = self._jx(rows)
            p = min(1.0, (t - INV_HOLD_T) / (INV_END_T - INV_HOLD_T))
            x = round(grid.X0 + (x0 - grid.X0) * p)
            overlay = []
            if s["kind"] == "item" and s["icon"]:     # the find rides along (meatButton)
                oy = grid.TOP + (grid.BAND - len(s["icon"])) // 2
                overlay = strikefx.blit(s["icon"], x - len(s["icon"][0]) - 1, oy)
            return rows, x, True, overlay, None
        if self._refuse_t:                            # Refusing: the mirror head-shake
            rows = self._rows(data.ROLES["refuse"][0])
            shake = ((REFUSE_T - self._refuse_t) // 6) % 2 == 0
            return rows, self._jx(rows), shake, [], None
        if self.discovering:                          # DiscoverCall: attention bounce 5<->7
            rows = self._rows(data.ROLES["happy"][(self.frame_i // 6) % 2])
            return rows, self._jx(rows), True, [], None
        beat = WALK_BEAT if self.travelling else 8    # stepping / a calmer stand
        rows = self._rows(data.ROLES["walk"][(self.frame_i // beat) % 2])
        return rows, self._jx(rows), True, [], None

    def text(self):
        if self.sub is not None:
            return self.sub.text()
        a = self.adv
        pet_rows, x, mirror, overlay, note_over = self._pet_placement()
        # the journey's SCENERY (restyle 2026-07-04 -- the old flat 7-row strip
        # "looked nothing like the rest of the game"): the zone's canonical
        # per-step backdrop (zones.csv BackgroundsAndRange), so the world
        # CHANGES as the pet walks -- desert into forest into mountains.
        # Home scenery covers spans the data leaves blank.  Pet over a bg is
        # ALWAYS the dark silhouette (paint() rule, v0.2.197).
        bg_h = next((hid for (blo, bhi, hid) in a.zone.get("bgs", [])
                     if blo <= a.location <= bhi), None)
        # arriving at a town shows the TOWN's scenery (towns.csv TownBackgroundID)
        tspan = next((t for t in a.zone.get("towns", []) if t[0] <= a.location <= t[1]), None)
        if tspan is not None:
            tbg = (data.load_towns().get(tspan[2]) or {}).get("bg_habitat")
            bg_h = tbg if tbg is not None else bg_h
        bgimg = self.pet.background(bg_h) if bg_h is not None else self.pet.background()
        # crossing into a new habitat CROSS-FADES the scenery (canon
        # BackgroundAnim.animateBack: the old backdrop's opacity steps out
        # over the new at -0.05/frame -- the world used to SNAP mid-stride)
        if bg_h != getattr(self, "_bg_id", bg_h):
            self._bg_fade = {"old": getattr(self, "_bg_last", None), "t": 0}
        self._bg_id = bg_h
        fade = getattr(self, "_bg_fade", None)
        if fade and fade["old"] and bgimg and fade["t"] < FADE_T:
            bgimg = _blend_bg(fade["old"], bgimg, fade["t"] / FADE_T)
        else:
            self._bg_fade = None
        self._bg_last = bgimg
        # the scene IS the whole LCD (box-clip audit 2026-07-04: the old
        # bar/progress/note/footer stack ran 16 lines and the physical 12-row
        # box clipped everything below the arena).  The journey's numbers live
        # on the ADVENTURE status card; the note + controls ride the strip.
        return menu.paint([(pet_rows, x, mirror)], bgimg,
                          rows=ROWS, cols=COLS, overlay=overlay)

    def strip(self):
        """One line under the LCD: the journey note + the controls that apply.
        The HINT is fixed chrome and never leaves view; an over-long note
        marquees in what's left (the v0.2.349 field-scroll doctrine -- a long
        species name used to push the whole line past 40 and the display
        marquee slid the keys off-screen, major audit 2026-07-07)."""
        if self.sub is not None:
            return ""
        a = self.adv
        _, _, _, _, note_over = self._pet_placement()
        note = note_over if note_over is not None else (a.last or "")
        if self._parade is not None:
            hint = "SPACE next"
        elif self._scene is not None:
            hint = "SPACE skip"
        elif a.done:
            hint = "ESC out"
        elif self.travelling:
            hint = "SPACE stop · ESC"     # travelling note + hint <= 40 (2026-07-07)
        elif getattr(self, "town_prompt", None) is not None:
            hint = "ENTER visit  ESC walk on"
        elif self.discovering:
            hint = "ENTER look  ESC walk on"
        else:
            hint = "SPACE go  ESC out"
        if not note:
            return f"[dim]{hint}[/]"
        from .render import marquee
        note = marquee(note, 40 - len(hint) - 4, self.frame_i // 2)
        return f"{note}  [dim]· {hint}[/]"
