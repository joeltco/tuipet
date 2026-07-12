"""Adventure — travel a zone, fight encounters/boss, all in the display box."""
from __future__ import annotations
from . import data
from .adventure import Adventure
from .battlescreen import BattlePanel
from .feedscreen import FeedPanel
from .shopscreen import ShopPanel
from .townscreen import TownPanel
from .render import downsample
from . import grid
from . import strikefx
from . import arena
from . import anim
from . import weather as wx

from .theme import LCD_ON, LCD_BG, INK, INK_B, DIM, SIL_DAY  # noqa: F401  (palette names bound for theme.apply propagation)
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
TRAVEL_TICKS = 10             # ticks per auto-stride (the INTERACTIVE_STEPS compression's
#                               pacing knob).  Was 3 -- a zone crossed in ~12s and zone 1's
#                               twelve BackgroundsAndRange scenes strobed ~1/s; at 1s/stride
#                               each scene HOLDS like canon's set-piece backdrops and towns
#                               read as interludes (Joel 2026-07-07: "adventure felt
#                               different in dvpet")
# the habitat transition (canon Enum.State.Teleport_Leave/Teleport_Arrive --
# SpriteAnim.teleportLeave()/teleportArrive(), the state ClockTic fires the
# moment the pet leaves for (or returns from) the adventure world): the
# striped CURTAIN (resources/evol.png: 2-on/1-off black stripes over the
# whole LCD) flashes over the standing pet three times (t3/t15/t21), stays
# down and swallows it (t23), shrinks to a sliver (t26..) and departs
# (canon shoots it off the TOP; tuipet zips it off the RIGHT -- window law,
# exits are left/right); the world swaps under the cut (teleportArrive
# frame 0 toggles isHome + checkBackNoAnim), the sliver zips back in from
# the LEFT, expands back to the full window, and teleportAppear flickers it
# three times -- the pet standing in the new world from the third flash.  Beats
# are canon interval units (targetFPS/10 = 0.1s) mapped 1:1 onto tuipet's
# 0.1s tick; sounds are the canon device mapping (soundConfig.csv rows
# 39-44: disappear=strongHit, shrink/expand=attackHit, depart/arrive=attack,
# appear=strongHit).  Battles get NO transition (their intro is the battle
# screen); v0.2.361's fade() port was the WRONG canon animation (fade() is
# the pause/silhouette wipe, not the habitat teleport -- Joel 2026-07-07).
TELE_LEAVE_T = 50             # flashes 3..22, swallow 23, shrink 26..44, depart right
TELE_ARRIVE_T = 46            # drop 0..5, expand 5..23, appear flicker 23..46
TELE_ON = ((3, 9), (15, 18), (21, 22))        # leave: curtain flash spans
TELE_APPEAR_ON = ((1, 2), (5, 8), (14, 20))   # arrive: flicker spans (t-23)
TELE_LEAVE_SNDS = {3: "strongHit", 15: "strongHit", 21: "strongHit",
                   26: "attackHit", 44: "attack"}
TELE_ARRIVE_SNDS = {1: "attack", 5: "attackHit",
                    24: "strongHit", 28: "strongHit", 37: "strongHit"}
# out-of-life retreat (canon Enum.State.Retreat_Town -- SpriteAnim.
# retreatToTown(): the pet holds the dejected pose 9 while a black layer
# steps to opaque at +5 alpha/frame, the world resets to the closest town
# under full black, then it steps back out and adventure life refills)
RETREAT_T = 34                # ~17 ticks down + 17 up (canon 255/5 x2)
# the zone-change transition (canon SpriteAnim.zoneChange): four zonePulse
# beats on the map light at interval*5/15/25/35, resolution at interval*54 --
# ported as backdrop pulses on the LCD (no map screen on the 32-col arena)
PULSE_T = 54
PULSE_ON = ((5, 10), (15, 20), (25, 30), (35, 54))
# road care beats (feel arc 2026-07-07: the direct keys used to act text-only):
# the HOME fx dispatch mirrored onto the arena -- cheer (praise: poses 5/7,
# Bad_Praise 6/4, happy emote on up-beats), jeer (scold: 4/6 leading down,
# Bad_Scold slump 10/9, unhappy emote riding), heal (hurt pose 9 + the i:80
# bandage strip at beats 0/8/13/18, chains into cheer like canon bandage())
CARE_T = 31
HEAL_T = 24
CARE_SNDS = {"cheer": {1: "happy"}, "jeer": {6: "angry"},
             "heal": {8: "click", 13: "click", 18: "confirm"}}


def _brighten(bg, f):
    """Lerp a backdrop toward white -- the LCD's zonePulse flash."""
    out = []
    for r in bg:
        row = []
        for i in range(0, len(r) - 5, 6):
            v = int(r[i:i + 6], 16)
            row.append("%02x%02x%02x" % tuple(
                round(c + (255 - c) * f)
                for c in ((v >> 16) & 255, (v >> 8) & 255, v & 255)))
        out.append("".join(row))
    return out


def _dim(bg, f):
    """Lerp a backdrop toward black -- canon fade()'s alpha layer, honestly."""
    out = []
    for r in bg:
        row = []
        for i in range(0, len(r) - 5, 6):
            v = int(r[i:i + 6], 16)
            row.append("%02x%02x%02x" % tuple(
                round(c * (1 - f))
                for c in ((v >> 16) & 255, (v >> 8) & 255, v & 255)))
        out.append("".join(row))
    return out


def _curtain_pts(x, y, w, h):
    """The evol curtain as overlay pixels: the canon stripe pattern (each
    3-px band = 1 clear + 2 filled, resources/evol.png) over an LCD rect.
    Rides render_scene's overlay so it covers the PET too, exactly like
    canon's room-effect layer sitting over the character sprite.  Window-law
    (audit 2026-07-13, Joel's call): the curtain is a canon SPRITE layer, not
    weather, so its ink is cut at the window -- the sliver's off-edge travel
    reads as the lawful left/right exit."""
    return [(px, py) for py in range(y, y + h)
            for px in range(x, x + w)
            if (px - x) % 3
            and grid.X0 <= px < grid.X1 and grid.TOP <= py < grid.FLOOR]


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
        self.travelling = False     # the walk starts once the teleport lands
        self.sub = None
        self._pending = None
        self._travel_t = 0
        self.discovering = False    # DiscoverCall: pause for the investigate prompt
        self.town_prompt = None     # a reached town's id: visit or walk on
        self._refuse_t = 0          # Refusing head-shake ticks left
        self._scene = None          # a running investigateLeft playbook
        self._parade = None         # a running BossParade (map beaten)
        self._pulse = None          # a running zoneChange pulse transition
        self._care = None           # a running road care beat (cheer/jeer/heal)
        self._retreat = None        # a running Retreat_Town fade (out of life)
        # leaving home rides the real canon transition: Teleport_Leave plays
        # over the HOME habitat, the world swaps, Teleport_Arrive materialises
        # the pet on the road (Joel 2026-07-07: the fade was the wrong anim)
        self._trans = {"dir": "in", "phase": "leave", "t": 0}

    def anim(self):
        if self.sub_anim():          # SubHost: delegate + sfx bubble
            return
        self.frame_i += 1
        self._roll_weather()                     # weather happens on the road
        if self._refuse_t:
            self._refuse_t -= 1
        fade = getattr(self, "_bg_fade", None)
        if fade is not None:
            fade["t"] += 1                   # the habitat cross-fade clock
        if self._trans is not None:
            # the teleport (canon Teleport_Leave -> Teleport_Arrive): the
            # curtain script owns the screen both ways -- canon's state
            # machine holds every input until endAnim()
            tr = self._trans
            tr["t"] += 1
            snds = TELE_LEAVE_SNDS if tr["phase"] == "leave" else TELE_ARRIVE_SNDS
            snd = snds.get(tr["t"])
            if snd:
                self.sfx = snd
            if tr["phase"] == "leave" and tr["t"] >= TELE_LEAVE_T:
                # the sliver left the screen: the world swaps under the cut
                # (canon teleportArrive frame 0: isHome toggles + the
                # background changes with NO anim)
                tr["phase"], tr["t"] = "arrive", 0
                if tr["dir"] == "out":
                    self.pet.go_home_habitat()  # back from the road: home climate
                    self.pet.away = False       # resumes; canon teleportArrive
            elif tr["phase"] == "arrive" and tr["t"] >= TELE_ARRIVE_T:
                self._trans = None
                if tr["dir"] == "out":
                    self.auto_close = ("done", None)
                else:
                    self.travelling = not self.adv.done   # landed: the walk begins
            return
        if self._retreat is not None:
            # Retreat_Town: the black fade plays out while the town reset
            # (already applied by _apply_life_penalty) waits under it
            self._retreat["t"] += 1
            if self._retreat["t"] >= RETREAT_T:
                self._retreat = None
                self.travelling = not self.adv.done
            return
        if self._pulse is not None:
            # zoneChange: four zonePulse beats, then the road (or the parade)
            p = self._pulse
            if any(p["t"] == on for on, _off in PULSE_ON):
                self.sfx = "select"          # the zonePulse chirp
            p["t"] += 1
            if p["t"] >= PULSE_T:
                self._pulse = None
                if p.get("parade"):
                    self._parade = {"t": 0, "nums": p["parade"]}
                    self.sfx = "win"         # bossParade cue
                else:
                    self.travelling = not self.adv.done
            return
        if self._care is not None:
            # a road care beat: canon-scripted stings, travel held while it
            # plays; bandage() chains into cheer(true) exactly like home
            c = self._care
            snd = CARE_SNDS[c["kind"]].get(c["t"])
            if snd:
                self.sfx = snd
            c["t"] += 1
            if c["t"] >= (HEAL_T if c["kind"] == "heal" else CARE_T):
                if c["kind"] == "heal":
                    self._care = {"kind": "cheer", "good": True, "t": 0,
                                  "resume": c["resume"]}
                else:
                    self._care = None
                    self.travelling = c["resume"] and not self.adv.done
            return
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
        if self._travel_t >= TRAVEL_TICKS and self.travelling and not self.adv.done:
            self._travel_t = 0
            ev = self.adv.travel()
            if ev and ev[0] in ("encounter", "boss"):
                self.travelling = False
                self._pending = (ev[0] == "boss", ev[1])
                self.sub = BattlePanel(self.pet, ev[1], wild=True)
            elif ev and ev[0] in ("zone", "map", "all"):
                # walked past a cleared gate: the zoneChange pulse plays
                self.travelling = False
                self._pulse = {"t": 0}
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

    def _road_react(self, fallback):
        """Route a direct care action's reaction onto the arena (the home fx
        dispatch, action_praise/scold/heal): the pet's anim picks the beat --
        cheer (happy/surprise), jeer (angry/sad), heal -- travel holds while it
        plays; a refusal rides the existing head-shake; anything else keeps
        the old button blip."""
        beat = {"happy": ("cheer", True), "surprise": ("cheer", False),
                "angry": ("jeer", True), "sad": ("jeer", False),
                "heal": ("heal", True)}.get(self.pet.anim)
        if beat is not None:
            self._care = {"kind": beat[0], "good": beat[1], "t": 0,
                          "resume": self.travelling}
            self.travelling = False
        elif self.pet.anim == "refuse":       # squirmed away / spat the med
            self.sfx = "refuse"
            self._refuse_t = REFUSE_T
        else:
            self.sfx = fallback

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
                    res = self.adv.resolve(r[1].won, was_boss, enemy)
                    if getattr(self.adv, "retreated", False):
                        # out of life: the Retreat_Town fade plays over the
                        # town reset (canon SpriteAnim.retreatToTown)
                        self.adv.retreated = False
                        self._retreat = {"t": 0}
                        self.travelling = False
                        return None
                    if res:
                        # zone/map/all advanced: the zoneChange pulse plays
                        # first; a parade_msg boss chains the parade after it
                        # (canon zoneChange's interval*54 tail)
                        self._pulse = {"t": 0, "parade": paraders}
                        if paraders:
                            self.adv.last = enemy["parade_msg"]     # "You saved the Digital World!"
                        self.travelling = False
                        return None
                self.travelling = not self.adv.done
            return None
        if getattr(self, "_trans", None) is not None:
            return None                       # the teleport owns the screen (canon
            #                                   holds every input until endAnim)
        if getattr(self, "_retreat", None) is not None:
            return None                       # the Retreat_Town fade plays out
        if getattr(self, "_pulse", None) is not None:
            return None                       # canon zoneChange is not skippable
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
        if getattr(self, "_care", None) is not None and k != "escape":
            # let the current care beat finish before acting again (the home
            # fx guard, action_praise/scold/heal)
            return None
        if k == "f":
            reason = self.pet.can_feed()
            if reason:
                self.adv.last = reason
                self.sfx = "refuse"
            else:
                self.sub = FeedPanel(self.pet)
            return None
        if k == "i":
            # bag only on the road -- buying needs a town shop (Joel 2026-07-12)
            self.sub = ShopPanel(self.pet, start_mode="bag", bag_only=True)
            return None
        if k == "h":
            self.adv.last = self.pet.heal()
            self._road_react("confirm")
            return None
        if k == "r":
            self.adv.last = self.pet.praise()
            self._road_react("confirm")
            return None
        if k == "k":
            self.adv.last = self.pet.scold()
            self._road_react("refuse")
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
            if getattr(self, "adv", None) is None or not hasattr(self, "_trans"):
                return ("done", None)       # a bare/legacy panel: close outright
            # going home plays the SAME teleport the other way: leave on the
            # road, the world swaps to home, arrive in the habitat -- then
            # anim() auto-closes the panel (canon teleportArrive/endAnim)
            self._trans = {"dir": "out", "phase": "leave", "t": 0}
            self.travelling = False
            return None
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
        c = self._care
        if c is not None:                             # a road care beat (home fx port)
            t = c["t"]
            if c["kind"] == "heal":
                # bandage(): hurt pose held, the item strip applies on the left
                rows = self._rows(9)
                x = self._jx(rows)
                overlay = []
                item = data.load_icons().get("i:80")
                if item:
                    fi = 0 if t < 8 else 1 if t < 13 else 2 if t < 18 else 3
                    bm = item[min(fi, len(item) - 1)]
                    if bm:
                        bw = max(len(r) for r in bm)
                        # window-law: the item descends from the BAND top, not
                        # the bezel sky (y0/4 pre-dated the law; audit 2026-07-13)
                        overlay = strikefx.blit(bm, max(grid.X0, x - bw),
                                                grid.TOP if t < 4 else grid.TOP + 4)
                return rows, x, True, overlay, None
            up = (t // 6) % 2 == 0
            if c["kind"] == "cheer":                  # 5/7 (Bad_Praise 6/4)
                pose = (5 if up else 7) if c["good"] else (6 if up else 4)
                emote = "happy" if up else None       # the bubble pulses on up-beats
            else:                                     # jeer 4/6 (Bad_Scold slump 10/9)
                pose = (4 if up else 6) if c["good"] else (10 if up else 9)
                emote = "unhappy"                     # rides the whole jeer
            rows = self._rows(pose)
            x = self._jx(rows)
            overlay = []
            em = data.load_effects().get(emote) if emote else None
            if em:
                ef = em[(t // 6) % len(em)]
                # window-law: emote riders pop at HEAD HEIGHT inside the band
                # (the v0.2.413 arena precedent), clamped off the right wall
                ew = max((len(r) for r in ef), default=0)
                ex = min(x + grid.width(rows) + 1, grid.X1 - ew)
                overlay = strikefx.blit(ef, max(grid.X0, ex), grid.TOP)
            return rows, x, True, overlay, None
        if self._retreat is not None:                 # Retreat_Town: dejected (pose
            rows = self._rows(9)                      # 9) under the stepping black
            return rows, self._jx(rows), False, [], None
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

    def _quiet_standing(self):
        """The pet is simply standing on the road: no walk, no encounter, no
        scripted beat.  This is the state that should read as the home biome."""
        return (not self.travelling and self.sub is None
                and self._trans is None and self._scene is None
                and self._care is None and self._parade is None
                and self._retreat is None and self._pulse is None
                and not self._refuse_t and not self.discovering
                and not self.adv.done
                and getattr(self, "town_prompt", None) is None)

    def _biome_frame(self):
        """Render the standing pet exactly like the home scene: state-driven
        pose, the poop/Zzz/sick-skull actors, and the weather -- the whole
        thing clipped to the play window and laid over the zone backdrop."""
        p = self.pet
        wf = self.frame_i // 4                      # arena's ~0.4s overlay cadence
        px_h = ROWS * 2
        xshift = 0
        if p.sick and p.num != -1:                  # idleUnwell: collapse + sway
            si, dx = anim.sick_frame(self.frame_i)
            rows = self._rows(si)
            xshift = dx
        elif getattr(p, "asleep", False) and (p.anim == "sleep" or not p.lights):
            pose = data.ROLES["sleep"][(self.frame_i // anim.SLEEP_BEAT) % 2]
            rows = self._rows(pose)
        else:                                       # idleWalk toggle (calm beat)
            rows = self._rows(data.ROLES["walk"][(self.frame_i // 8) % 2])
        x = self._jx(rows) + xshift
        # the home floor law: the filth block is a hard left wall, the sick
        # skull a hard right one -- the pet can never share their columns
        lo = arena._filth_right(p.poop) if p.poop else grid.X0
        hi = ((grid.X1 - arena.SICK_ZONE if arena._sick_mark_up(p) else grid.X1)
              - grid.width(rows))
        x = min(max(x, lo), max(hi, lo))
        bgimg = self._road_bg()
        if not p.lights:                            # lights out: dark room + Zzz
            bgimg, rows = None, []
        overlay = arena._clip_win(
            arena._effect_overlay(p, wf, COLS, px_h, tick=self.frame_i))
        weather = arena._weather_overlay(p.weather, wf, COLS, px_h)
        return menu.paint([(rows, x, False)], bgimg, rows=ROWS, cols=COLS,
                          overlay=overlay, overlay_free=weather, clip=grid.WINDOW)

    def _current_hab_id(self):
        """The habitat id of the scenery under the pet right now -- the zone's
        per-step backdrop, or the town's backdrop when standing in one.  None
        means fall back to the home habitat."""
        a = self.adv
        bg_h = next((hid for (blo, bhi, hid) in a.zone.get("bgs", [])
                     if blo <= a.location <= bhi), None)
        tspan = next((t for t in a.zone.get("towns", [])
                      if t[0] <= a.location <= t[1]), None)
        if tspan is not None:
            tbg = (data.load_towns().get(tspan[2]) or {}).get("bg_habitat")
            if tbg is not None:
                bg_h = tbg
        return bg_h

    def _roll_weather(self):
        """Weather keeps happening while travelling (Joel 2026-07-12), off the
        CURRENT zone habitat -- so it shifts as the pet crosses biomes and an
        underwater leg stays clear (weather.next_weather gates no-sky habitats).
        Re-rolls on every biome crossing, plus the canon slow cadence."""
        hid = self._current_hab_id()
        hab = (data.load_habitats().get(hid) if hid is not None else None) \
            or self.pet.habitat_obj()
        self._wx_t = getattr(self, "_wx_t", 0.0) + 0.1
        if hid != getattr(self, "_wx_hab", "unset") or self._wx_t >= wx.WEATHER_CHECK_SEC:
            self._wx_t = 0.0
            self._wx_hab = hid
            self.pet.weather = wx.next_weather(self.pet.weather, self.pet.season,
                                               self.pet.day_temp, hab)

    def _road_bg(self):
        """The journey's SCENERY (restyle 2026-07-04 -- the old flat 7-row
        strip "looked nothing like the rest of the game"): the zone's
        canonical per-step backdrop (zones.csv BackgroundsAndRange), so the
        world CHANGES as the pet walks -- desert into forest into mountains.
        Home scenery covers spans the data leaves blank.  Crossing into a new
        habitat CROSS-FADES (canon BackgroundAnim.animateBack: the old
        backdrop's opacity steps out over the new at -0.05/frame)."""
        bg_h = self._current_hab_id()
        bgimg = self.pet.background(bg_h) if bg_h is not None else self.pet.background()
        if bg_h != getattr(self, "_bg_id", bg_h):
            self._bg_fade = {"old": getattr(self, "_bg_last", None), "t": 0}
        self._bg_id = bg_h
        fade = getattr(self, "_bg_fade", None)
        if fade and fade["old"] and bgimg and fade["t"] < FADE_T:
            bgimg = _blend_bg(fade["old"], bgimg, fade["t"] / FADE_T)
        else:
            self._bg_fade = None
        self._bg_last = bgimg
        return bgimg

    def _teleport_frame(self):
        """One frame of the canon teleport (SpriteAnim.teleportLeave /
        teleportArrive / teleportAppear), on the side of the wipe the beat
        script says the world is showing."""
        tr = self._trans
        t, ph = tr["t"], tr["phase"]
        # which world is under the curtain: leaving-out and arriving-in show
        # the ROAD; leaving-in and arriving-out show the HOME habitat
        home_side = (tr["dir"] == "in") == (ph == "leave")
        if home_side:
            bgimg = (self.pet.background(self.pet.home_habitat)
                     if tr["dir"] == "in" else self.pet.background())
        else:
            bgimg = self._road_bg()
        # the wipe is staged on the 32x16 WINDOW (audit 2026-07-13: the old
        # full-LCD rects + the sliver's upward exit predated the law; the
        # sliver now zips off RIGHT on leave and back in from the LEFT on
        # arrive -- one continuous world direction, like the battle orb)
        wx0, wy0, ww, wh = grid.X0, grid.TOP, grid.W, grid.BAND
        cx, cy = wx0 + (ww - 4) // 2, wy0 + (wh - 6) // 2
        pet_on, cur = False, None
        if ph == "leave":
            pet_on = t < 23                       # swallowed at interval*23
            if any(on <= t < off for on, off in TELE_ON) or t >= 23:
                cur = (wx0, wy0, ww, wh)          # the full-window curtain
            if 26 <= t < 44:                      # shrinking to the sliver
                k = t - 26
                w, h = max(4, ww - 2 * k), max(6, wh - k)
                cur = (wx0 + (ww - w) // 2, wy0 + (wh - h) // 2, w, h)
            elif t >= 44:                         # the sliver departs RIGHT
                cur = (cx + 4 * (t - 44), cy, 4, 6)
        else:                                     # arrive
            if t <= 5:                            # the sliver zips in from the LEFT
                cur = (wx0 - 4 + round((cx - wx0 + 4) * t / 5), cy, 4, 6)
            elif t < 23:                          # expands back to the full window
                k = t - 5
                w, h = min(ww, 4 + 2 * k), min(wh, 6 + k)
                cur = (wx0 + (ww - w) // 2, wy0 + (wh - h) // 2, w, h)
            else:                                 # teleportAppear flicker
                f = t - 23
                pet_on = f >= 14                  # revealed on the third flash
                if any(on <= f < off for on, off in TELE_APPEAR_ON):
                    cur = (wx0, wy0, ww, wh)
        placements = []
        if pet_on:
            rows = self._rows(0)                  # canon drawNumMirror(0, false)
            if home_side and tr["dir"] == "in":
                lo, hi = grid.roam_bounds(grid.width(rows))
                x = (lo + hi) // 2                # standing at home, centre stage
            else:
                x = self._jx(rows)                # at the journey spot
            placements = [(rows, x, False)]
        overlay = _curtain_pts(*cur) if cur else []
        return menu.paint(placements, bgimg, rows=ROWS, cols=COLS,
                          overlay=overlay)

    def text(self):
        if self.sub is not None:
            return self.sub.text()
        if self._trans is not None:
            return self._teleport_frame()
        if self._quiet_standing():
            return self._biome_frame()             # standing = the home biome
        pet_rows, x, mirror, overlay, note_over = self._pet_placement()
        bgimg = self._road_bg()
        if self._pulse is not None and bgimg and \
                any(on <= self._pulse["t"] < off for on, off in PULSE_ON):
            bgimg = _brighten(bgimg, 0.6)     # the zonePulse light, on the LCD
        placements = [(pet_rows, x, mirror)]
        if self._retreat is not None and bgimg:
            # Retreat_Town: the black layer steps down over the dejected pet,
            # the town reset waits under full black, then it steps back out
            t = self._retreat["t"]
            half = RETREAT_T // 2
            d = t / half if t < half else (RETREAT_T - t) / half
            bgimg = _dim(bgimg, min(1.0, d))
            if d > 0.6:                       # near-black: the pet is under it too
                placements, overlay = [], []
        # the scene IS the whole LCD (box-clip audit 2026-07-04: the old
        # bar/progress/note/footer stack ran 16 lines and the physical 12-row
        # box clipped everything below the arena).  The journey's numbers live
        # on the ADVENTURE status card; the note + controls ride the strip.
        return menu.paint(placements, bgimg,
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
        if self._trans is not None or self._pulse is not None \
                or self._care is not None or self._retreat is not None:
            hint = ""                 # the beat plays out (teleport / zoneChange /
            #                           care fx / the Retreat_Town fade)
        elif self._parade is not None:
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
        if not hint:                  # a hint-less beat: the note has the line
            return marquee(note, 40, self.frame_i // 2)
        note = marquee(note, 40 - len(hint) - 4, self.frame_i // 2)
        return f"{note}  [dim]· {hint}[/]"
