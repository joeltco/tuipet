"""Adventure — tuipet's OWN expedition (rebuild FOUNDATION, 2026-07-20).

This is the skeleton the expedition engine grows into: the menu action, the
can_adventure() gate, and the REAL canon teleport (SpriteAnim.teleportLeave /
teleportArrive / teleportAppear) carried VERBATIM from the pre-0.5.8 build --
leaving home and returning both ride the same striped-curtain wipe.

⛔ OWN-GAME LAW (Joel 2026-07-13, carried forward): DVPet is NOT canon for
adventures.  One biome per run, cross a zone in ~40 interactive travel actions,
victory teleport home.

Built so far: the teleport (verbatim); the MARCH -- the pet walks the run's one
backdrop while the journey rides a ribbon (adventure.Adventure), arrival
teleports it home with the verdict, ESC turns back; and WILD ENCOUNTERS -- a
per-leg roll pulls a real roster enemy that fights through BattlePanel (a
SubHost child), a loss costs an adventure life, and 0 lives fails the run home;
the real 26-ZONE GEOGRAPHY (adventure.ZONES from data.load_maps -- each zone its
own biome + wild table); the zone BOSS FIGHT -- the end opens the gate boss,
felling it is the win, a survivable loss stands the pet at the gate to try again
(SPACE) or turn back (ESC); TRAVEL DRAIN -- marching tires the pet (⚡ energy on
the strip), burns weight and tops effort; TOWNS -- a mid-zone rest that refills
lives + energy; and PROGRESSION -- the ZonePickPanel picks an unlocked zone,
felling a boss unlocks the next (pet.adv_progress); and FINDS -- spot loot on
the road, ENTER digs it into the bag; the home STATUS CARD; and TRANSPORT -- press T
mid-march to spend a town/danger warp item (skip ahead, rest or get ambushed).
Nothing here is faked.
"""
from __future__ import annotations
from . import data, grid, menu
from . import adventure
from .adventure import Adventure, MAX_LIVES, ZONES
from .theme import LCD_ON, LCD_BG, INK, INK_B, DIM, POS, NEG  # noqa: F401  (theme.apply propagation)

COLS, ROWS = 40, 12           # the ONE locked LCD arena, like every other screen

# the zone-change celebration (canon SpriteAnim.zoneChange, restored from the
# old build): four zonePulse beats on the map light at interval*5/15/25/35,
# resolution at interval*54 -- ported as backdrop pulses on the LCD (no map
# screen on the 32-col arena).  A parade_msg boss chains the BossParade after
# the pulse: the map's bosses march across, one at a time (the LCD's one-mon
# rule serialises canon's three-abreast).
PULSE_T = 54
PULSE_ON = ((5, 10), (15, 20), (25, 30), (35, 54))
PARADE_T = 40                 # ticks for one boss to march across (edge to
#                               edge since audit A10: ~48px at ~1.2px/tick)

# the investigateLeft playbook (canon SpriteAnim beats in 0.1s ticks, restored
# from the old build): walk out to the LEFT goal, suspense dots, the reveal --
# then the ReturnItem walk-back so the pet never teleports back to its spot
INV_WALK_T = 12               # walk-left leg
INV_REVEAL_T = 30             # dots done -> the reveal pose fires
INV_HOLD_T = 42               # reveal held (the find shown beside the cheer)
INV_END_T = 54                # walk-back (ReturnItem) complete

# the TIMED DIG (arcade arc, Joel 2026-07-21 "do the timed dig"): reaching
# the dig spot runs the CANON timing bar -- the same sprite and the same
# care-widened mega window as the training drill and the battle bell
# (strikefx.timing_bar / battlescreen.mega_window; one bar everywhere is
# Joel's standing law).  SPACE locks it; mega digs a SECOND copy of the
# find.  The meter is pure upside: a wide miss still scrapes the find out
# -- no loot is ever lost to it, the verdict just says so.
DIG_METER_T = 48              # one full 0..24..0 sweep, then the spade falls
#                               wherever the marker stands (the TIMED part)

# HAZARD DODGES (arcade arc, Joel 2026-07-21 "do the hazard dodges"): an
# ambush telegraphs -- the "!" blinking at the road's right edge -- then one
# of the zone's OWN wilds pounces in; SPACE anywhere inside the window ducks
# it (canon shield pose) and the pouncer sails past out the LEFT edge; eat
# it and the engine takes adventure.HAZARD_ENERGY off the tank.  All real
# art: roster frames for the pouncer, atlas "attention"/"hit" for the fx.
HZ_TELE_T = 8                 # the "!" telegraph window
HZ_LUNGE_T = 8                # the pounce crosses the right half
HZ_END_T = 10                 # the verdict beat (the duck-under / the burst)

# CONDITION WALKS + TRAVEL REFUSALS (restored from the old build's audit
# pass 3 / canTravel port, 2026-07-21): a SICK pet drags the idleUnwell
# trudge at HALF march pace; a GERIATRIC one walks the +9 aged-shuffle
# frames; a sleeping traveller halts the march AND the stride clock (no
# rolls) as the roadside nap; and a pet pushed PAST EMPTY plants its feet
# (petcare.check_stop_travel -- today's calibration, deliberately soft:
# only negative energy refuses.  NEVER revert to chance-based refusals).
REFUSE_T = 24                 # the refusal head-shake (the fx convention)

WALK_BEAT = 5                 # idleWalk pose-flip cadence while marching
MARCH_PX = 0.5                # the march: px per 0.1s tick across the window
#                               (a full crossing ~ 9-10s, ~one per stride)
TRAVEL_TICKS = 8              # auto-march pace: ticks per travel step (~0.8s a leg)
TOWN_HOLD = 14                # ticks the pet rests at a town before marching on
NOTE_HOLD = 30                # ticks a road-item verdict rides the strip

# the habitat transition (canon Enum.State.Teleport_Leave/Teleport_Arrive --
# SpriteAnim.teleportLeave()/teleportArrive()): the striped CURTAIN
# (resources/evol.png: 2-on/1-off black stripes) flashes over the standing pet
# three times, stays down and swallows it (t23), shrinks to a sliver (t26..)
# and zips off the RIGHT (window law: exits are left/right); the world swaps
# under the cut, the sliver zips back in from the LEFT, expands to the full
# window, and teleportAppear flickers it three times -- the pet standing in the
# new world from the third flash.  Beats are canon interval units (0.1s) mapped
# 1:1 onto tuipet's 0.1s tick; sounds are the canon device mapping.  Ported
# verbatim from adventurescreen @ ed22b64 (v0.5.7) -- Joel: "same teleport
# animation."
TELE_LEAVE_T = 50             # flashes 3..22, swallow 23, shrink 26..40 (the
#                               sliver then HOLDS to 43 -- both dims floor
#                               early), depart right 44..
TELE_ARRIVE_T = 46            # sliver zips in from the LEFT 0..5, expand
#                               6..22, appear flicker 23..46
TELE_ON = ((3, 9), (15, 18), (21, 22))        # leave: curtain flash spans
TELE_APPEAR_ON = ((1, 2), (5, 8), (14, 20))   # arrive: flicker spans (t-23)
TELE_LEAVE_SNDS = {3: "strongHit", 15: "strongHit", 21: "strongHit",
                   26: "attackHit", 44: "attack"}
TELE_ARRIVE_SNDS = {1: "attack", 5: "attackHit",
                    24: "strongHit", 28: "strongHit", 37: "strongHit"}

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


def _curtain_pts(x, y, w, h):
    """The evol curtain as overlay pixels: the canon stripe pattern (each 3-px
    band = 1 clear + 2 filled) over an LCD rect.  Rides paint()'s overlay so it
    covers the PET too, like canon's room-effect layer.  Window-law: the ink is
    cut at the window, so the sliver's off-edge travel reads as a lawful exit."""
    return [(px, py) for py in range(y, y + h)
            for px in range(x, x + w)
            if (px - x) % 3
            and grid.X0 <= px < grid.X1 and grid.TOP <= py < grid.FLOOR]


class AdventurePanel(menu.SubHost):
    def __init__(self, pet, zone=None):
        self.pet = pet
        self.adv = Adventure(pet, zone=zone)   # zone chosen by the picker (or the frontier)
        self.frame_i = 0
        self.sfx = None
        self.sub = None
        self.auto_close = None
        self._landed = False
        self.travelling = False       # the march begins once the teleport lands
        self._travel_t = 0            # auto-march pacing counter
        self._home_msg = None         # the verdict flashed home on close
        self._fighting_boss = False   # the current sub is the gate boss, not a wild
        self._fighting_enemy = None   # the enemy dict of the active fight (for the bounty)
        self._at_gate = False         # knocked back: standing before the boss
        self._rest_t = 0              # ticks left resting (transport town-warp beat)
        self._heal_t = 0              # ticks left on the Life Recovery second-wind beat
        self._note = ""               # a transient strip verdict (heal / bare warp)
        self._note_t = 0
        self._town_prompt = False     # standing at a town: visit the hub or walk on
        self._town_sub = False        # the current sub is the TownPanel, not a fight
        self._find = None             # a loot key spotted, awaiting dig/pass
        self._scene = None            # a running investigateLeft playbook
        self._find_msg = None         # the reveal line (sealed until the beat)
        self._hazard = None           # a running ambush: {"t","enemy","dodged","hit"}
        self._refuse_t = 0            # ticks left on the refusal head-shake
        self._refused = False         # planted: SPACE re-issues the walk
        self._transport = None        # open transport menu: the held transport keys
        self._transport_cursor = 0
        self._summary = False         # showing the run-results card before homecoming
        self._summary_shown = False   # ...so _go_home only defers to it once
        self._pulse = None            # a running zoneChange pulse celebration
        self._parade = None           # a running BossParade (map beaten)
        self._wx = float(grid.X0)     # the march x: the pet CROSSES the window
        # leaving home rides the canon teleport (dir "in" == INTO the adventure:
        # leave-phase plays over HOME, arrive-phase materialises on the road)
        self._trans = {"dir": "in", "phase": "leave", "t": 0}

    # -- clock ----------------------------------------------------------------
    def anim(self):
        if self.sub_anim():               # a wild fight owns the clock -- delegate
            return
        self.frame_i += 1
        if self._note_t > 0:              # the transient strip verdict decays
            self._note_t -= 1
        if self._trans is not None:
            # the teleport owns the screen both ways -- canon's state machine
            # holds every input until endAnim()
            tr = self._trans
            tr["t"] += 1
            snds = TELE_LEAVE_SNDS if tr["phase"] == "leave" else TELE_ARRIVE_SNDS
            snd = snds.get(tr["t"])
            if snd:
                self.sfx = snd
            if tr["phase"] == "leave" and tr["t"] >= TELE_LEAVE_T:
                # the sliver left the screen: the world swaps under the cut
                # (canon teleportArrive frame 0 -- background changes, no anim)
                tr["phase"], tr["t"] = "arrive", 0
            elif tr["phase"] == "arrive" and tr["t"] >= TELE_ARRIVE_T:
                self._trans = None
                if tr["dir"] == "out":
                    # home: the flag the body sim gates on (assistant billing,
                    # filth, gift call -- canon _isHome) comes back down.  The
                    # SETTER died with the old adventure and was never rewired
                    # (found 2026-07-21 via Joel's @-line question); the app's
                    # death path already cleared it, waiting for this.
                    self.pet.away = False
                    self.pet.away_where = ""
                    self.auto_close = ("done", self._home_msg)   # home: close + verdict
                else:
                    self._landed = True                # on the road -- the march begins
                    self.travelling = True
                    self.pet.away = True               # canon: the teleport toggles it
                    self.pet.away_where = self.adv.name   # the @-line's live zone
            return
        if self._pulse is not None:
            # zoneChange: four zonePulse beats, then home (or the parade)
            p = self._pulse
            if any(p["t"] == on for on, _off in PULSE_ON):
                self.sfx = "select"           # the zonePulse chirp
            p["t"] += 1
            if p["t"] >= PULSE_T:
                self._pulse = None
                if p.get("parade"):
                    self._parade = {"t": 0, "nums": p["parade"],
                                    "msg": p.get("msg")}
                    self.sfx = "win"          # bossParade cue
                else:
                    self._go_home()           # celebrated -- now the verdict
            return
        if self._parade is not None:
            self._parade["t"] += 1
            if self._parade["t"] >= PARADE_T * len(self._parade["nums"]):
                self._parade = None
                self._go_home()
            return
        if self.travelling:
            if self.pet.asleep:           # the roadside nap: the journey waits
                return                    #   -- no strides, no rolls, no march
            if self._refuse_t > 0:        # the head-shake plays out
                self._refuse_t -= 1
                return
            if self._refused:             # planted: SPACE re-issues the walk
                return
            if self._scene is not None:   # the investigate playbook plays out
                self._scene_tick()
                return
            if self._hazard is not None:  # an ambush owns the beat
                self._hazard_tick()
                return
            if self._transport is not None:   # transport menu open: wait for input
                return
            if self._find is not None:    # a glint spotted: wait for dig/pass
                return
            if self._town_prompt:         # standing at a town: visit or walk on
                return
            if self._rest_t > 0:          # a transport town-warp rest beat
                self._rest_t -= 1
                return
            if self._heal_t > 0:          # the Life Recovery second wind
                self._heal_t -= 1
                return
            # THE MARCH (walking sequence restored from the old build,
            # 8ab28a0 -- Joel 2026-07-13: "mon should walk across the
            # screen"): the journey walk actually CROSSES the window -- off
            # the right edge, back in from the left, the lawful exits --
            # instead of stepping in place at an anchor.  A SICK pet
            # trudges at HALF pace (pass 3).
            self._wx += MARCH_PX * (0.5 if self.pet.sick else 1.0)
            if self._wx >= grid.X1:              # fully out the right side
                # slide back in from JUST off-left of the real sprite (audit
                # C2: the flat 16px offset over-hid narrow sprites for ticks)
                self._wx = float(grid.X0 - grid.width(self._rows(0)))
            # auto-march: the pet walks the road on its own pace; arrival ends
            # the run and rides the same teleport back home (SPACE hurries a leg)
            self._travel_t += 1
            if self._travel_t >= TRAVEL_TICKS:
                self._travel_t = 0
                self._advance()

    # -- input ----------------------------------------------------------------
    def _advance(self):
        """One leg of the march.  A wild encounter opens a battle; the zone's
        end opens the BOSS gate; a bossless crossing rides the teleport home."""
        r = self.adv.travel()
        if isinstance(r, tuple) and r[0] == "encounter":
            self._start_battle(r[1])
        elif isinstance(r, tuple) and r[0] == "boss":
            self._start_boss(r[1])
        elif isinstance(r, tuple) and r[0] == "find":
            self._find = r[1]                 # a glint: wait for the player to choose
        elif isinstance(r, tuple) and r[0] == "hazard":
            self._hazard = {"t": 0, "enemy": r[1], "dodged": False, "hit": False}
            self.sfx = "cancel"               # the rustle: the warning thunk
        elif isinstance(r, tuple) and r[0] == "refused":
            self._refuse_t = REFUSE_T         # the head-shake, then the stand
            self._refused = True
            self.sfx = "refuse"
        elif r == "town":
            self._town_prompt = True          # rested on arrival; now visit or walk on
        elif r == "arrived":
            self._home_msg = f"{self.adv.name} conquered!{self._bits_tail()}"
            self._go_home()

    def _use_transport(self, key):
        """Spend the chosen road item: a town warp rests, a danger warp
        ambushes, a life recovery refills the hearts in place."""
        r = self.adv.use_transport(key)
        self._transport = None
        if r == "town-warp":
            self._rest_t = TOWN_HOLD          # the warp-in rest beat
            self._refused = False             # rested = willing to walk again
        elif isinstance(r, tuple) and r[0] == "encounter":
            self._start_battle(r[1])          # the danger-warp ambush
        elif r == "life-recovery":
            # the second wind is VISIBLE now (anim audit A3, 2026-07-22):
            # the v0.5.164 heal was nothing but the heart glyphs ticking --
            # a happy beat + the verdict on the strip, the rest-beat grammar
            self._heal_t = TOWN_HOLD
            self._note, self._note_t = self.adv.last, NOTE_HOLD
            self.sfx = "confirm"
        elif r == "danger-warp":
            # empty wild pool: the dash still happened -- say so instead of
            # silently eating the ticket (anim audit A12)
            self._note, self._note_t = self.adv.last, NOTE_HOLD

    def _dig(self):
        """ENTER on a glint: the OUTCOME lands now -- the bag gets the loot,
        the tally counts it -- then the investigateLeft playbook plays (the
        discover sequence, restored from the old build): walk out LEFT,
        suspense dig, the reveal, the carry back.  The beats are pure
        presentation, like a battle timeline; the verdict and the reward
        chime stay sealed until the reveal beat."""
        from . import shop
        from .battlescreen import mega_window
        key, self._find = self._find, None
        self.pet.add_item(key)                # a CATALOG key: real, usable loot
        self.adv.finds += 1
        name = (shop.entry(key) or {}).get("name", "loot")
        self._find_msg = f"Dug up {name}!"
        lo, hi = mega_window(self.pet)        # the SHARED care-widened window
        self._scene = {"t": 0, "icon": self._find_icon(key), "key": key,
                       "name": name, "grade": None,
                       "meter": {"bar": 0, "dir": 1, "left": DIG_METER_T,
                                 "lo": lo, "hi": hi}}

    def _find_icon(self, key):
        """The find at HAND size, ~8px beside the 16px mon (old-build rule:
        scale by ceil(dim/8) so every icon reads held -- never crushed to a
        speck, never drawn as big as the pet)."""
        from . import shop
        from .render import downsample
        raw = [f for f in (data.load_icons().get(shop.ICON_KEYS.get(key)) or [])
               if f]
        icon = raw[0] if raw else None
        if icon:
            dim = max(len(icon), max(len(r) for r in icon))
            if dim > 8:
                icon = downsample(icon, -(-dim // 8))
        return icon

    def _scene_tick(self):
        """Advance the playbook.  At the dig spot the TIMED-DIG meter holds
        the clock (the bar sweeps, the countdown burns, timeout locks the
        spade wherever the marker stands); after the lock, the dots and the
        reveal (reward chime) play on; the walk-back's end puts the mon
        back on the road."""
        from .battlescreen import BAR_MAX
        s = self._scene
        if s["t"] >= INV_WALK_T and s["grade"] is None:
            m = s["meter"]                    # the meter owns the beat
            m["bar"] += m["dir"]
            if m["bar"] >= BAR_MAX or m["bar"] <= 0:
                m["dir"] = -m["dir"]
                m["bar"] = max(0, min(BAR_MAX, m["bar"]))
            m["left"] -= 1
            if m["left"] <= 0:
                self._lock_dig()              # time's up: the spade falls
            return
        s["t"] += 1
        if s["t"] == INV_REVEAL_T:
            self.sfx = "reward"               # _discoverConsumable
        if s["t"] >= INV_END_T:               # carried home -> back on the road
            self._scene = None

    def _hazard_tick(self):
        """Advance the ambush.  Impact settles it: a duck already banked
        rings clean, an unducked pounce lands -- the ENGINE takes the toll
        -- and the verdict beat plays either way before the march resumes."""
        h = self._hazard
        h["t"] += 1
        if h["t"] == HZ_TELE_T + HZ_LUNGE_T:      # the pounce lands (or doesn't)
            if h["dodged"]:
                self.sfx = "confirm"              # a clean duck-under
            else:
                h["hit"] = True
                self.adv.hazard_hit()             # the small energy toll
                self.sfx = "attackHit"
        if h["t"] >= HZ_TELE_T + HZ_LUNGE_T + HZ_END_T:
            self._hazard = None                   # back to the march
            self._wx = float(grid.X0)             # ...from the wall the
            #                                       scramble left it at (A1)

    def _lock_dig(self):
        """The spade falls: grade the marker against the shared mega window
        (battles >= 999 never whiffs -- DSprite truth, the verbatim battle/
        drill rule).  Mega banks a SECOND copy of the find on the spot;
        normal keeps the honest single; a wide miss still scrapes the find
        out -- the meter is pure upside, only the verdict changes."""
        s = self._scene
        m = s.pop("meter")
        if self.pet.battles >= 999 or m["lo"] <= m["bar"] <= m["hi"]:
            g = "mega"
        elif m["lo"] - 5 <= m["bar"] <= m["hi"] + 5:
            g = "normal"
        else:
            g = "miss"
        s["grade"] = g
        if g == "mega":
            self.pet.add_item(s["key"])       # the bonus copy, banked at the lock
            self._find_msg = f"Dug up {s['name']} ×2!"
        elif g == "miss":
            self._find_msg = f"Scraped out {s['name']}..."
        self.sfx = "confirm" if g != "miss" else "cancel"

    def _start_battle(self, enemy):
        """A wild fight rides BattlePanel as a child (SubHost): the road's biome
        is the fight's scene, wild=True gives the pre-bell flee."""
        from .battlescreen import BattlePanel
        self.travelling = False               # the march pauses during the fight
        self._fighting_enemy = enemy
        self.sub = BattlePanel(self.pet, enemy=enemy, wild=True, scene=self.adv.scene)

    def _start_boss(self, boss):
        """The gate boss fight -- same road biome, flagged so _battle_done knows
        to settle it as the zone's end, not a wayside wild."""
        from .battlescreen import BattlePanel
        self.travelling = False
        self._at_gate = False
        self._fighting_boss = True
        self._fighting_enemy = boss
        self.sub = BattlePanel(self.pet, enemy=boss, wild=True, scene=self.adv.scene)

    def _battle_done(self, result):
        """Settle a finished fight.  result is the battle object (has .won) or
        None if the pet fled before the bell."""
        won = bool(getattr(result, "won", False)) if result is not None else False
        fled = result is None
        enemy, self._fighting_enemy = self._fighting_enemy, None
        if not fled:                          # a fought bout (not a pre-bell flee)
            self.adv.fights += 1
            if won:
                self.adv.wins += 1
        self.adv.chain(won)                   # the streak: BEFORE the bounty, so
        #                                       this win's own chain pays it
        if won and enemy is not None:
            self.adv.award_bits(enemy)        # the bounty into the purse + run tally
        if self._fighting_boss:
            self._fighting_boss = False
            out = self.adv.resolve_boss(won, fled=fled)
            if out == "won":
                unlocked = adventure.record_win(self.pet, self.adv.zone)   # progression
                from . import persistence              # profile signals: unlocks
                m = self.adv.zone.get("map")
                if m is not None and adventure.is_map_cleared(self.pet, m):
                    persistence.map_complete_add(m - 1)  # shop shelf + eggs (0-based)
                if self.adv.holiday:                   # conquered on a festival day
                    persistence.festival_add(self.adv.holiday)  # gates the festival egg
                tail = " New ground opens!" if unlocked else ""
                self._home_msg = (f"{self.adv.boss_name} felled — "
                                  f"{self.adv.name} conquered!{self._bits_tail()}{tail}")
                # the zoneChange CELEBRATION plays before the homecoming
                # (restored from the old build): the pulse first; a
                # parade_msg boss (each map's final gate) chains the
                # BossParade of the map's own bosses -- canon shows three
                paraders = []
                if (enemy or {}).get("parade_msg"):
                    m = self.adv.zone.get("map")
                    paraders = [b["num"] for z in ZONES if z.get("map") == m
                                for b in z["bosses"]][:3]
                self._pulse = {"t": 0, "parade": paraders,
                               "msg": (enemy or {}).get("parade_msg")}
            elif out == "fled":
                self._home_msg = f"Turned back from {self.adv.boss_name}.{self._bits_tail()}"
                self._go_home()
            elif out == "failed":
                self._home_msg = f"Defeated by {self.adv.boss_name}.{self._bits_tail()}"
                self._go_home()
            else:                             # 'retry' -- stand at the gate, choose
                self._at_gate = True
            return
        # a wayside wild
        out = self.adv.resolve(won, fled=fled)
        if out == "failed":
            self._home_msg = f"Driven back from {self.adv.name}.{self._bits_tail()}"
            self._go_home()
        else:
            self.travelling = True            # resume the march (a grace leg follows)

    def _bits_tail(self):
        """The run's purse for the homecoming verdict (empty if nothing won)."""
        return f" +{self.adv.bits_earned}b" if self.adv.bits_earned else ""

    def _town_done(self, _result):
        """Left the town hub -- back onto the road, the march resumes."""
        self._town_sub = False
        self._town_prompt = False

    def _go_home(self):
        """Conclude the run: show the results card first (a key rides the
        teleport home), unless there's nothing to summarise -- a bare turn-back
        goes straight to the canon teleport."""
        self.travelling = False
        a = self.adv
        if not self._summary_shown and (a.bits_earned or a.fights or a.finds or a.done):
            # a run of substance gets SCORED against the zone's standing
            # best (bare turn-backs skip the card AND the books)
            from . import persistence
            zi = adventure.zone_index(a.zone)
            self._new_best = (persistence.zone_best_set(zi, a.score())
                              if zi is not None else False)
            self._summary = True              # results, then a key teleports
            return
        self._trans = {"dir": "out", "phase": "leave", "t": 0}

    def _outcome_word(self):
        if self.adv.done:
            return "Conquered!"
        if self.adv.failed:
            return "Defeated"
        return "Turned back"

    def key(self, k):
        if self.sub is not None:              # a fight or the town hub owns input
            self.sub_key(k, self._town_done if self._town_sub else self._battle_done)
            return None
        if (self._trans is not None or self._scene is not None
                or self._pulse is not None or self._parade is not None):
            # the teleport / investigate / celebration beats own the screen
            # (no skips: own-game law 2026-07-13 -- the beats play out).
            # ONE exception: SPACE locks a LIVE timed-dig meter -- that's
            # the arcade input, not a skip
            s = self._scene
            if (s is not None and s.get("meter") and s["grade"] is None
                    and s["t"] >= INV_WALK_T and k in ("space", "enter")):
                self._lock_dig()
            return None
        if self._town_prompt:                 # at a town: visit the hub or walk on
            if k in ("enter",):
                from .townscreen import TownPanel
                self.sub = TownPanel(self.pet, self.adv.town_at(self.adv.loc))
                self._town_sub = True
            elif k in ("space", "escape"):
                self._town_prompt = False     # walk on, the march resumes
            return None
        if self._summary:                     # results card up: any key rides home
            self._summary = False
            self._summary_shown = True
            self._go_home()                   # the latch makes this teleport now
            return None
        if self._refuse_t > 0:
            return None                       # the head-shake plays out
        if self._refused and self._transport is None:   # planted on the road
            #                                 (an open warp menu keeps its keys)
            if k == "space":
                self._refused = False         # re-issue the walk: canTravel
                self._advance()               # re-rolls on the very next leg
            elif k == "t":
                held = self.adv.held_transports()
                if held:                      # a town warp is the way out
                    self._transport, self._transport_cursor = held, 0
            elif k == "escape":
                self._home_msg = f"Turned back from {self.adv.name}.{self._bits_tail()}"
                self._go_home()
            return None
        if self._hazard is not None:          # the ambush: SPACE ducks it
            # a REAL reflex window now (dodge rework 2026-07-23, Joel: "the
            # whole space to dodge thing... its sloppy as fuck").  The old
            # rule banked a duck ANYWHERE in the 1.6s beat -- and SPACE is
            # also the hurry-the-march key, so the mash bled in and won the
            # dodge by accident before the ! even registered.  New grammar,
            # ONE press per ambush: during the telegraph it's TOO SOON (the
            # duck is spent -- the anti-mash rule); during the lunge it's
            # the clean duck.  ! ! ! means WAIT FOR IT.
            h = self._hazard
            if (k in ("space",) and not h["dodged"] and not h["hit"]
                    and not h.get("spent")
                    and h["t"] < HZ_TELE_T + HZ_LUNGE_T):
                h["spent"] = True
                if h["t"] >= HZ_TELE_T:       # inside the lunge: the duck
                    h["dodged"] = True
            return None                       # everything else rides the beat
        if self._find is not None:            # a glint spotted: dig or pass
            if k in ("enter",):
                self._dig()
            elif k in ("space", "escape"):
                self._find = None             # walk on, leave it
            return None
        if self._transport is not None:       # transport menu: choose / use / cancel
            n = len(self._transport)
            if k in ("up", "k"):
                self._transport_cursor = (self._transport_cursor - 1) % n
            elif k in ("down", "j"):
                self._transport_cursor = (self._transport_cursor + 1) % n
            elif k in ("enter", "space"):
                self._use_transport(self._transport[self._transport_cursor])
            elif k in ("escape",):
                self._transport = None        # back to the road
            return None
        if self._at_gate:                     # knocked back before the boss
            if k == "space":
                self._start_boss(self.adv.boss)   # face it again
            elif k == "escape":
                self._home_msg = f"Turned back from {self.adv.boss_name}.{self._bits_tail()}"
                self._go_home()
            return None
        if k in ("t",) and self.travelling:
            held = self.adv.held_transports()  # open the transport menu if any held
            if held:
                self._transport, self._transport_cursor = held, 0
        elif k in ("space",) and self.travelling:
            self._advance()                   # hurry the next leg
        elif k in ("escape",):
            # turn back: the SAME teleport the other way; anim() auto-closes
            # the mode once it lands (canon teleportArrive/endAnim)
            self._home_msg = f"Turned back from {self.adv.name}.{self._bits_tail()}"
            self._go_home()
        return None

    def strip(self):
        if self.sub is not None:
            return self.sub.strip()            # the wild fight owns the line
        if self._trans is not None or self._pulse is not None:
            return ""                          # the teleport / pulse plays out
        if self._parade is not None:
            msg = self._parade.get("msg")      # the parade carries the victory line
            return f"[b]★ {msg}[/]" if msg else ""
        if self._summary:
            return menu.hints(("any key", "home"))
        if self._at_gate:                      # knocked back before the boss
            hearts = "♥" * self.adv.lives + "[dim]♡[/]" * (MAX_LIVES - self.adv.lives)
            return f"{self.adv.boss_name} {hearts}  [dim]· SPACE fight  ESC home[/]"
        if self.travelling:
            lost = MAX_LIVES - self.adv.lives
            hearts = "♥" * self.adv.lives + "[dim]♡[/]" * lost
            if self._transport is not None:
                from . import shop
                key = self._transport[self._transport_cursor]
                name = (shop.entry(key) or {}).get("name", "Transport")
                nav = " ↑↓" if len(self._transport) > 1 else ""
                return f"[b]⟿ {name}[/]  [dim]ENTER use{nav} · ESC[/]"
            if self._town_prompt:
                return "[b]⌂ A town[/]  [dim]ENTER visit · SPACE walk on[/]"
            if self.pet.asleep:
                return "[dim]zzZ — a roadside nap[/]"
            if self._refuse_t > 0 or self._refused:
                thint = " T" if self.adv.held_transports() else ""
                return f"[b]Refuses to walk![/]  [dim]SPACE urge{thint} · ESC[/]"
            if self._scene is not None:
                s, t = self._scene, self._scene["t"]
                if s["grade"] is None and t >= INV_WALK_T:
                    return menu.hints(("SPACE", "dig!"))   # the meter is live
                if t >= INV_REVEAL_T:         # the reveal, unsealed
                    return f"[b]✦ {self._find_msg}[/]"
                if t >= INV_WALK_T:           # suspense: . .. ...
                    dots = "." * min(3, 1 + (t - INV_WALK_T) // 6)
                    return f"[dim]{dots}[/]"
                return ""                     # the walk-out plays wordless
            if self._hazard is not None:
                h = self._hazard
                if h["t"] < HZ_TELE_T:        # the warning: DON'T press yet
                    if h.get("spent"):
                        return "[b]Jumped too soon![/]"
                    return "[b]! ! ![/]  [dim]wait for it…[/]"
                if h["t"] < HZ_TELE_T + HZ_LUNGE_T:
                    if h["dodged"]:
                        return "[b]![/]  [dim]ducking...[/]"
                    if h.get("spent"):
                        return "[b]Jumped too soon![/]"
                    return "[b]NOW![/]  [dim]SPACE — duck![/]"
                if h["dodged"]:
                    return "[b]Dodged the ambush![/]"
                return f"[b]Ambushed![/]  ⚡-{adventure.HAZARD_ENERGY}"
            if self._find is not None:
                # <= 40 plain (budget sweep 2026-07-21: the long line ran 45)
                return "[b]✦ A glint![/]  [dim]ENTER dig · SPACE pass[/]"
            if self._rest_t > 0:
                return f"[b]⌂ Town — rested up[/]  ⚡{self.pet.energy} {hearts}"
            if self._heal_t > 0 or self._note_t > 0:
                # the road-item verdict (audit A3/A12): second wind / bare dash
                return f"[b]⚡ {self._note}[/] {hearts}" if self._note else ""
            thint = " T" if self.adv.held_transports() else ""
            chain = f" [b]×{self.adv.streak}[/]" if self.adv.streak >= 2 else ""
            return (f"[dim]{self.adv.ribbon()}[/] ⚡{self.pet.energy} {hearts}"
                    f"{chain}  [dim]· SPACE{thint} ESC[/]")
        return menu.hints(("ESC", "home"))

    # -- render ---------------------------------------------------------------
    def _rows(self, idx):
        fr = data.frames_for(self.pet.num, getattr(self.pet, "egg_type", 0))
        return grid.prep((fr[idx] if idx < len(fr) else None) or fr[0], ph=ROWS * 2)

    def _road_bg(self):
        return self.pet.background(self.adv.scene)   # the run's ONE biome (own-game law)

    def _jx(self, rows, clamp=True):
        """Where the mon stands RIGHT NOW: the march position (it walks
        clear across the window while travelling -- old build 8ab28a0).
        Beats, reveals and stand-stills play at this spot; `clamp` pulls it
        fully inside the walkable band so a beat never plays half-off an
        edge.  Journey progress lives on the ribbon."""
        x = int(self._wx)
        if clamp:
            lo, hi = grid.roam_bounds(grid.width(rows))
            x = min(max(x, lo), hi)
            if x != int(self._wx):
                # a beat that clamps also RE-ANCHORS the march (anim audit
                # A6): the beat still never plays half-off an edge, and the
                # resume now walks on from where the beat played -- one
                # snap instead of a snap-there-and-back
                self._wx = float(x)
        return x

    def _condition_rows(self, wi):
        """The pet's road sprite, CONDITION-aware (pass 3 restored): a SICK
        pet drags the idleUnwell collapse/weary trudge with its canon 1px
        shuffle; a GERIATRIC one walks the +9 aged frames (home stepFrame
        idiom); everyone else walks the frame given.  Returns (rows, dx)."""
        from . import anim
        if self.pet.sick and self.pet.num != -1:
            si, dx = anim.sick_frame(self.frame_i)
            return self._rows(si), dx
        if self.pet.is_geriatric and self.pet.num != -1:
            wi += 9                            # the aged shuffle
        return self._rows(wi), 0

    def _march_frame(self):
        """The pet walking the road: the idleWalk pose-flip, FACING the way
        it's going, at the RAW march x -- partial edge exits ARE the journey
        (window law: exits are left/right, so the crossing clips at the
        play window, not the LCD border)."""
        wi = data.ROLES["walk"][(self.frame_i // WALK_BEAT) % 2]
        rows, dx = self._condition_rows(wi)
        return menu.paint([(rows, self._jx(rows, clamp=False) + dx, True)],
                          self._road_bg(), rows=ROWS, cols=COLS,
                          clip=grid.WINDOW)

    def _standing_frame(self):
        """The pet standing on the road: beats (glint, town, rest, gate)
        play WHERE IT STANDS -- the clamped march x -- not snapped back to
        centre (old build: "beats play wherever it stands")."""
        rows, dx = self._condition_rows(0)     # canon drawNumMirror(0, false)
        lo, hi = grid.roam_bounds(grid.width(rows))
        # re-clamp AFTER the sick shuffle's dx (audit A11: +1 at the right
        # bound poked the sprite a pixel past the window)
        x = min(max(self._jx(rows) + dx, lo), hi)
        return menu.paint([(rows, x, True)],
                          self._road_bg(), rows=ROWS, cols=COLS,
                          clip=grid.WINDOW)

    def _heal_frame(self):
        """The Life Recovery beat (anim audit A3): the happy pose-flip where
        the pet stands -- the glint celebration frames -- while the hearts
        refill on the strip."""
        rows = self._rows((5, 7)[(self.frame_i // 5) % 2])
        return menu.paint([(rows, self._jx(rows), True)], self._road_bg(),
                          rows=ROWS, cols=COLS, clip=grid.WINDOW)

    def _nap_frame(self):
        """The roadside nap (pass 3): the sleep pose-flip where the pet lay
        down, the Zzz hanging at the band's top-right exactly like the home
        sleep scene (arenafx idiom: nothing above the band)."""
        from . import strikefx
        rows = self._rows(data.ROLES["sleep"][(self.frame_i // 10) % 2])
        px = self._jx(rows)
        overlay = []
        zz = data.load_effects().get("zzz")
        if zz:
            z = grid._crop(zz[(self.frame_i // 10) % len(zz)])
            if z:
                zw = len(z[0])
                zx = grid.X1 - zw
                if zx < px + grid.width(rows) + 1:
                    # a right-side sleeper sat UNDER the Zzz -- first-ink-
                    # wins merged them into one silhouette (anim audit A7);
                    # hang it on the free side instead (the glint rule)
                    zx = grid.X0
                overlay = strikefx.blit(z, zx, grid.TOP)
        return menu.paint([(rows, px, True)], self._road_bg(),
                          rows=ROWS, cols=COLS, overlay=overlay,
                          clip=grid.WINDOW)

    def _refuse_frame(self):
        """The travel refusal: the canon head-shake (refuse pose under the
        mirror toggle) while the shake runs, then the WEARY stand -- the
        planted pet is refusing because it's spent past empty."""
        if self._refuse_t > 0:
            rows = self._rows(data.ROLES["refuse"][0])
            shake = ((REFUSE_T - self._refuse_t) // 6) % 2 == 0
            return menu.paint([(rows, self._jx(rows), shake)], self._road_bg(),
                              rows=ROWS, cols=COLS, clip=grid.WINDOW)
        rows = self._rows(data.ROLES["tired"][0])
        return menu.paint([(rows, self._jx(rows), True)], self._road_bg(),
                          rows=ROWS, cols=COLS, clip=grid.WINDOW)

    def _glint_frame(self):
        """A glint spotted: the DiscoverCall attention bounce (happy 5<->7)
        with the atlas "!" riding the up-beats, side-flipped to the free
        side so it never clamps INTO the sprite -- restored from the old
        build (audit passes 1+2)."""
        from . import strikefx
        rows = self._rows(data.ROLES["happy"][(self.frame_i // 6) % 2])
        x = self._jx(rows)
        overlay = []
        att = data.load_effects().get("attention")
        if att:
            ef = att[(self.frame_i // 6) % len(att)]
            ew = max((len(r) for r in ef), default=0)
            ex = x + grid.width(rows) + 1
            if ex + ew > grid.X1:                 # no room on the right
                ex = max(grid.X0, x - ew - 1)
            overlay = strikefx.blit(ef, ex, grid.TOP)
        return menu.paint([(rows, x, True)], self._road_bg(), rows=ROWS,
                          cols=COLS, overlay=overlay, clip=grid.WINDOW)

    def _held_icon(self, icon, x, rows, gap):
        """The find beside the mon, vertically centred in the band: in
        FRONT when the right has room, flipped BEHIND when it doesn't (the
        glint's side-flip rule).  The old right-wall pin (min(.., X1-iw))
        dropped the icon ONTO a pet returning from a right-side dig -- the
        exact clamped-onto-the-sprite bug its docstring claimed the pin
        prevented (anim audit A2, 2026-07-22)."""
        if not icon:
            return []
        from . import strikefx
        iw = max(len(r) for r in icon)
        oy = grid.TOP + max(0, (grid.BAND - len(icon)) // 2)
        ox = x + grid.width(rows) + gap
        if ox + iw > grid.X1:                  # no room in front: carry behind
            ox = max(grid.X0, x - iw - gap)
        return strikefx.blit(icon, ox, oy)

    def _scene_frame(self):
        """One frame of the investigateLeft playbook (the restored discover
        sequence): walk OUT to the left goal (native facing), the suspense
        dig under the pulsing "!", the cheer reveal with the find held up
        beside, then ReturnItem -- the carry back to the journey spot, the
        find riding IN FRONT of the walking mon."""
        from . import strikefx
        s, bg = self._scene, self._road_bg()
        t = s["t"]
        if t < INV_WALK_T:                        # walk out to the LEFT goal
            rows = self._rows((t // 3) % 2)
            x0 = self._jx(rows)
            x = round(x0 + (grid.X0 - x0) * (t / INV_WALK_T))
            return menu.paint([(rows, x, False)], bg, rows=ROWS, cols=COLS,
                              clip=grid.WINDOW)   # faces left (native)
        if s["grade"] is None:                    # the TIMED DIG: the canon bar
            m = s["meter"]                        # owns the window, like the
            return menu.paint([], bg, rows=ROWS,  # drill and the battle bell
                              cols=COLS, clip=grid.WINDOW,
                              overlay=strikefx.timing_bar(m["bar"], m["lo"],
                                                          m["hi"]))
        if t < INV_REVEAL_T:                      # the suspense dig
            rows = self._rows(0)
            overlay = []
            att = data.load_effects().get("attention")
            if att and (t // 4) % 2:              # the "!" pulses, blink 4/4
                ef = att[(t // 8) % len(att)]
                overlay = strikefx.blit(ef, grid.X0 + grid.width(rows) + 1,
                                        grid.TOP)
            return menu.paint([(rows, grid.X0, False)], bg, rows=ROWS,
                              cols=COLS, overlay=overlay, clip=grid.WINDOW)
        if t < INV_HOLD_T:                        # the reveal: cheer, find shown
            rows = self._rows(5)
            overlay = self._held_icon(s["icon"], grid.X0, rows, gap=2)
            return menu.paint([(rows, grid.X0, False)], bg, rows=ROWS,
                              cols=COLS, overlay=overlay, clip=grid.WINDOW)
        rows = self._rows((t // 3) % 2)           # ReturnItem: the carry back
        x0 = self._jx(rows)
        p = min(1.0, (t - INV_HOLD_T) / (INV_END_T - INV_HOLD_T))
        x = round(grid.X0 + (x0 - grid.X0) * p)
        overlay = self._held_icon(s["icon"], x, rows, gap=1)
        return menu.paint([(rows, x, True)], bg, rows=ROWS, cols=COLS,
                          overlay=overlay, clip=grid.WINDOW)

    def _hazard_frame(self):
        """The ambush, frame by frame: the "!" blinking at the road's right
        edge, one of the zone's own wilds pouncing in (attack pose, riding
        the overlay like fx do), then the duck-under -- the pouncer sails
        past and exits LEFT, never sharing the pet's cell (the gap IS the
        leap-over) -- or the eaten hit: the atlas burst over the hurt pose.
        All real art; window-law edges throughout."""
        from . import strikefx
        h, t = self._hazard, self._hazard["t"]
        impact = HZ_TELE_T + HZ_LUNGE_T
        if h["hit"]:
            prows = self._rows(9)                 # eaten: the hurt pose
        elif h["dodged"] and t >= HZ_TELE_T:
            prows = self._rows(4)                 # the duck (canon shield pose)
        else:
            prows = self._rows(1)                 # alert on the road
        # the pet SCRAMBLES to the left wall during the telegraph (anim
        # audit A1, 2026-07-22): the pounce lands at the pet's right edge,
        # and two 16px sprites only fit the 32px window with the pet at X0
        # -- anchored at the march x, the ambusher rendered half-cut on
        # most legs and fully OFF-window with the pet right of centre (the
        # pet reacted to nothing).  The scramble is animated, so it reads
        # as the startle, not a snap; the gate faceoff pins the same wall.
        x0 = h.setdefault("x0", self._jx(prows))
        if t < HZ_TELE_T:
            p = t / max(1, HZ_TELE_T - 1)
            px = round(x0 + (grid.X0 - x0) * min(1.0, p))
        else:
            px = grid.X0
        pw = grid.width(prows)
        overlay = []
        if t < HZ_TELE_T:                         # the telegraph
            att = data.load_effects().get("attention")
            if att and att[0] and (t // 2) % 2:   # urgent blink 2/2
                ew = max((len(r) for r in att[0]), default=0)
                ex = grid.X1 - ew - 1
                if ex < px + pw + 1:              # scrambler still under it:
                    ex = max(grid.X0, px - ew - 1)   # flip (the glint rule,
                    #                                  audit A8 -- it drew
                    #                                  over the pet's head)
                overlay = strikefx.blit(att[0], ex, grid.TOP)
        else:
            e = h["enemy"]
            fr = data.frames_for(e["num"])
            pose = data.ROLES["attack"][0]
            # prepped like every other arena actor (audit A9: the raw frame
            # floated above the y21 floor on bottom-padded rips and measured
            # its PADDED box in the overlap guards)
            bm = grid.prep((fr[pose] if pose < len(fr) else None) or fr[0],
                           ph=ROWS * 2)
            oy = grid.FLOOR - len(bm) if bm else grid.TOP
            if t < impact:                        # charging in from the right
                p = (t - HZ_TELE_T) / max(1, HZ_LUNGE_T - 1)
                x = round(grid.X1 - (grid.X1 - (px + pw)) * min(1.0, p))
                if bm and x >= px + pw:           # never share the pet's cell
                    overlay = strikefx.blit(bm, x, oy)
            elif h["dodged"]:                     # the WHIFF (dodge fix
                # 2026-07-22, Joel: "the space to dodge mechanic was
                # glitchy"): the old sail-past hid the pouncer whenever its
                # box touched the pet's columns -- and with the pet at the
                # wall (audit A1) that was the ENTIRE tail, so a clean duck
                # played as the attacker blinking out of existence.  Two
                # 16px sprites cannot cross a 32px window without one
                # hiding, so the duck now makes the strike WHIFF: the
                # pouncer pulls up short of the crouch and retreats out the
                # RIGHT edge -- the free side of the pet, visible for the
                # whole beat, never a hidden frame.
                p = (t - impact) / max(1, HZ_END_T - 1)
                x = round((px + pw) + (grid.X1 - (px + pw)) * p)
                if bm and x >= px + pw:           # never share the pet's cell
                    overlay = strikefx.blit(bm, x, oy)
            else:                                 # eaten: the burst covers the beat
                hitfx = data.load_effects().get("hit")
                if hitfx and hitfx[0] and (t - impact) < 6:
                    hw = max(len(r) for r in hitfx[0])
                    overlay = strikefx.blit(hitfx[0], min(px + pw, grid.X1 - hw),
                                            grid.TOP + 2)
        return menu.paint([(prows, px, True)], self._road_bg(), rows=ROWS,
                          cols=COLS, overlay=overlay, clip=grid.WINDOW)

    def _pulse_frame(self):
        """The zoneChange pulse: the conqueror stands its ground while the
        world flashes bright on the canon beat spans (restored old build)."""
        rows = self._rows(0)
        bg = self._road_bg()
        if bg and any(on <= self._pulse["t"] < off for on, off in PULSE_ON):
            bg = _brighten(bg, 0.6)            # the zonePulse light, on the LCD
        return menu.paint([(rows, self._jx(rows), True)], bg, rows=ROWS,
                          cols=COLS, clip=grid.WINDOW)

    def _parade_frame(self):
        """BossParade: the map's bosses march across, one at a time (canon
        moveLeft; the one-mon LCD rule serialises canon's three-abreast) --
        over a BRIGHTENED stage, so dark marcher ink pops (old audit pass 2:
        a dim stage read worse)."""
        p = self._parade
        i = min(p["t"] // PARADE_T, len(p["nums"]) - 1)
        t = p["t"] % PARADE_T
        fr = data.frames_for(p["nums"][i])
        wi = data.ROLES["walk"][(t // 3) % 2]
        rows = grid.prep((fr[wi] if wi < len(fr) else None) or fr[0],
                         ph=ROWS * 2)
        # each boss ENTERS off the right edge and EXITS off the left (anim
        # audit A10, 2026-07-22): the old roam-bounds interpolation popped
        # them in at x=20 and vanished them at x=4 mid-window -- the march's
        # own edge-crossing grammar, with the window clip doing the doors
        w = grid.width(rows)
        x = round(grid.X1 + ((grid.X0 - w) - grid.X1)
                  * (t / max(1, PARADE_T - 1)))
        bg = self._road_bg()
        if bg:
            bg = _brighten(bg, 0.45)
        return menu.paint([(rows, x, False)], bg, rows=ROWS, cols=COLS,
                          clip=grid.WINDOW)

    def _gate_frame(self):
        """The GATE FACEOFF (restored from the old build, audit pass 1: a
        knocked-back gate showed the mon alone on empty road): squared up
        at the left, stepping in place, while the boss LOOMS half-emerged
        past the gate's right edge -- flush placement would read as one
        blob (two 16px sprites cannot share the 32px window with a gap)."""
        rows = self._rows((self.frame_i // 8) % 2)
        placements = [(rows, grid.X0, True)]
        boss = self.adv.boss
        bfr = data.frames_for(boss["num"]) if boss else []
        bf = next((f for f in bfr if f), None)
        if bf:
            brows = grid.prep(bf, ph=ROWS * 2)
            placements.append((brows, grid.X1 - grid.width(brows) * 3 // 4,
                               False))
        return menu.paint(placements, self._road_bg(), rows=ROWS, cols=COLS,
                          clip=grid.WINDOW)

    def _teleport_frame(self):
        """One frame of the canon teleport, on the side of the wipe the beat
        script says the world is showing (verbatim port)."""
        tr = self._trans
        t, ph = tr["t"], tr["phase"]
        # which world is under the curtain: leaving-out and arriving-in show the
        # ROAD; leaving-in and arriving-out show HOME
        home_side = (tr["dir"] == "in") == (ph == "leave")
        bgimg = self.pet.background() if home_side else self._road_bg()
        wx0, wy0, ww, wh = grid.X0, grid.TOP, grid.W, grid.BAND
        cx, cy = wx0 + (ww - 4) // 2, wy0 + (wh - 6) // 2
        pet_on, cur = False, None
        if ph == "leave":
            pet_on = t < 23                       # swallowed at t23
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
                # f==0 rides the expand's full curtain (audit C3: it used to
                # render one frame of bare road between expand and flicker)
                if f == 0 or any(on <= f < off for on, off in TELE_APPEAR_ON):
                    cur = (wx0, wy0, ww, wh)
        placements = []
        if pet_on:
            rows = self._rows(0)
            lo, hi = grid.roam_bounds(grid.width(rows))
            if home_side:
                x, mirror = (lo + hi) // 2, False   # the home scene's centre
            else:
                # ROAD side: the pet stands AT ITS MARCH SPOT facing the way
                # it walks (anim audit A4+A5, 2026-07-22): the centred reveal
                # popped ~8px left + flipped facing into the first march
                # frame at every run start, and an ESC turn-back snapped a
                # right-side marcher to centre before the curtain dropped
                x, mirror = self._jx(rows), True
            placements = [(rows, x, mirror)]
        overlay = _curtain_pts(*cur) if cur else []
        # every arena frame clips to the window (audit C1: this was the one
        # unclipped paint -- safe only because the curtain self-clips)
        return menu.paint(placements, bgimg, rows=ROWS, cols=COLS,
                          overlay=overlay, clip=grid.WINDOW)

    def _summary_frame(self):
        """The run-results card, shown on the LCD before the homecoming teleport."""
        a = self.adv
        out = menu.header("ADVENTURE", "results")
        out.append(a.name[:26] + "\n", style=INK_B)
        word = self._outcome_word()
        out.append(word + "\n", style={"Conquered!": POS, "Defeated": NEG}.get(word, DIM))
        out.append(f"Bits    +{a.bits_earned}\n", style=INK)
        out.append(f"Fights  {a.wins}W/{a.fights}\n", style=INK)
        out.append(f"Loot    {a.finds}\n", style=INK)
        hearts = "♥" * a.lives + "♡" * (MAX_LIVES - a.lives)
        out.append(f"Lives   {hearts}\n", style=INK)
        if a.best_streak >= 2:                 # a chain worth bragging about
            out.append(f"Streak  ×{a.best_streak} best\n", style=INK)
        out.append(f"Score   {a.score()}", style=INK_B)
        if getattr(self, "_new_best", False):
            out.append("  ★ new best!", style=POS)
        out.append("\n")
        if a.holiday:
            out.append(f"★ {a.holiday}\n", style=POS)
        # the card is 12 physical rows: pad only while both extras are absent
        if (1 if a.best_streak >= 2 else 0) + (1 if a.holiday else 0) < 2:
            out.append_text(menu.blanks(1))
        out.append_text(menu.footer("press any key — home"))
        return out

    def text(self):
        if self.sub is not None:
            return self.sub.text()             # the fight owns the screen
        if self._trans is not None:
            return self._teleport_frame()
        if self._pulse is not None:
            return self._pulse_frame()         # the zoneChange light
        if self._parade is not None:
            return self._parade_frame()        # the map's bosses march past
        if self._summary:
            return self._summary_frame()       # the run-results card
        if self._at_gate:
            return self._gate_frame()          # the FACEOFF: squared up at the gate
        if self.travelling:
            if self.pet.asleep:
                return self._nap_frame()       # the roadside nap
            if self._refuse_t > 0 or self._refused:
                return self._refuse_frame()    # the head-shake / planted feet
            if self._scene is not None:
                return self._scene_frame()     # the investigate playbook
            if self._hazard is not None:
                return self._hazard_frame()    # the ambush beat
            if self._find is not None:
                return self._glint_frame()     # the attention bounce at the spot
            if self._heal_t > 0:
                return self._heal_frame()      # the second-wind celebration
            if (self._transport is not None or self._rest_t > 0
                    or self._town_prompt):
                return self._standing_frame()  # menu / rest / town: stand still
            return self._march_frame()
        return self._standing_frame()


class ZonePickPanel:
    """The embark screen: pick an UNLOCKED zone to run.  Progression phase --
    zones unlock as their gate boss is felled (pet.adv_progress); a conquered
    zone can be replayed, the frontier is the next challenge.  Returns the
    chosen zone dict on ENTER, or None on ESC (back out of Adventure)."""

    VIS = 8

    def __init__(self, pet):
        from . import persistence
        self.pet = pet
        self.frame_i = 0
        self.indices = adventure.unlocked_indices(pet)   # unlocked zone indices, in order
        self.cursor = len(self.indices) - 1              # default: the frontier (newest)
        self.holiday = adventure.active_holiday()        # festival banner + double rewards
        self.bests = persistence.zone_bests()            # standing run scores per zone

    def anim(self):
        self.frame_i += 1

    def key(self, k):
        n = len(self.indices)
        if k in ("up", "k"):
            self.cursor = (self.cursor - 1) % n
        elif k in ("down", "j"):
            self.cursor = (self.cursor + 1) % n
        elif k in ("pageup", "pagedown"):       # up to 26 zones unlock
            self.cursor = menu.page_step(self.cursor, n, self.VIS, k)
        elif k in ("enter", "space"):
            return ("done", ZONES[self.indices[self.cursor]])   # embark
        elif k in ("escape", "a"):
            return ("done", None)                               # back out
        return None

    def strip(self):
        return menu.hints(("↑↓", "pick"), ("ENTER", "go"), ("ESC", "back"))

    def _fmt(self, zi, _i):
        z = ZONES[zi]
        mark = "✓" if adventure.is_conquered(self.pet, zi) else "★"   # conquered vs the frontier
        best = self.bests.get(zi)
        if best:                               # the standing score: chase it
            return f"{mark} {z['name']}"[:27].ljust(27) + f"{best:>6}"
        return f"{mark} {z['name']}"[:34]

    def text(self):
        right = "★ FESTIVAL" if self.holiday else f"{len(self.indices)}/{len(ZONES)}"
        out = menu.header("ADVENTURE", right)
        self.cursor = menu.list_window(out, self.indices, self.cursor, self.VIS, self._fmt)
        if self.holiday:
            out.append_text(menu.note(f"★ {self.holiday}: 2× bits · more loot!"))
        elif adventure.is_conquered(self.pet, self.indices[self.cursor]):
            # the VETERAN ROAD tease (replay scaling 2026-07-21) -- the
            # festival note owns the slot on the rarer festival days
            out.append_text(menu.note("✓ veteran road: foes fight trained "
                                      "· bounties +50%"))
        out.append_text(menu.footer("↑↓ pick   ENTER go   ESC back"))
        return out
