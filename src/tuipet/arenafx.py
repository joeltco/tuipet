"""The LCD fx ENGINE (tier-2 split, 2026-07-17): the care-action
animations — start_fx's beat/sound tables, advance_fx's chain rules, the
per-kind _fxk_* painters — plus the filth/status overlays and the geometry
constants they share with the Screen widget.  arena.py keeps the widget
(paint, crossfade, the roamer) and imports every old name back, so
`tuipet.arena.X` and `tuipet.app.X` keep resolving.

The fx-painter status-UI law (2026-07): idle-family poses play in place
with the status actors up; care anims anchor centre with the canon
resetScreen() blackout.  Classify any NEW fx against the decompile before
wiring it.
"""
from __future__ import annotations


from . import data
from . import egg as egg_mod
from . import grid
from . import theme  # noqa: F401  (theme.apply propagation)
from .pet import POOP_MAX_PILES
from .render import blit as _blit
from .theme import LCD_BG, LCD_ON, SIL_SCENE, SIL_LIGHTSOFF, VOID, FLASH  # noqa: F401


SCREEN_COLS, SCREEN_ROWS = 40, 12


SPRITE_W = 16                                   # native creature sprite width


PET_BASE_X = (SCREEN_COLS - SPRITE_W) // 2      # the fx painter's centred-pet origin


class _FxCtx:
    """Mutable per-frame paint context shared by the _fxk_* painters."""
    __slots__ = ("rows", "overlay", "free", "xshift", "yshift", "bg", "bgimg", "px_h", "mirror")


# The filth block is ONE CREATURE CELL: 8x8 slots in a 2x2 grid, so the max 4
# piles span exactly 16x16 -- the same footprint as a 16x16 creature, filling
# the band (y6..22) with no clamp.  (DVPet's raw 30x27+pad slots would scale to
# a 22x18 block -- wider than a cell, taller than the band, and with 3-4 piles
# it left no room for the pet to stand clear inside the 32 grid.  Joel's rule:
# 4 poops == 16x16, and the mon NEVER walks over them.)  The extracted pile
# sizes 1-3 (7x7 / 8x7 / 8x8 -- all _poop_size produces) fit the slot natively.
POOP_W = 8


POOP_PAD = 0


def _evol_strobe(c):
    """DVPet's 50% 'evol' dither tiled over the whole LCD in ink -- the evolve
    burst and the inherit collide strobe carried two copies (refactor 2026-07-05)."""
    ev = (data.load_effects().get("evol") or [None])[0]
    if not ev:
        return
    mh, mw = len(ev), len(ev[0])
    c.overlay += [(x, y) for y in range(c.px_h) for x in range(SCREEN_COLS)
                  if ev[y % mh][x % mw] == "1"]


def _filth_right(count):
    """Right edge x of the filth block: fixed POOP_W columns like DVPet's 30px slots."""
    n = min(count or 0, POOP_MAX_PILES)
    if n <= 0:
        return grid.X0
    return grid.X0 + ((n + 1) // 2 - 1) * (POOP_W + POOP_PAD) + POOP_W


def _filth_pts(pet, tick, count=None, sizes=None, push=0, px_h=None):
    """DVPet drawFilthLevel + animFilth: per-pile SIZED sprites (the real filth.png
    sizes 1-4, two anim frames each, from pet.poop_sizes) laid in fixed 2-high
    columns stepping right from the grid's left edge; the frame swaps every
    7 ticks awake / 10 asleep."""
    E = data.load_effects()
    n = min((pet.poop if count is None else count) or 0, POOP_MAX_PILES)
    if n <= 0:
        return []
    if px_h is None:
        px_h = SCREEN_ROWS * 2
    sz = list(pet.poop_sizes if sizes is None else (sizes or []))
    fi = (tick // (10 if getattr(pet, "asleep", False) else 7)) % 2
    pts = []
    for i in range(n):
        s = max(1, min(4, sz[i] if i < len(sz) else 2))
        frames = E.get("poop_s%d" % s) or E.get("poop") or []
        if not frames:
            continue
        pm = frames[fi % len(frames)]
        if len(pm[0]) > POOP_W:                     # safety: only the unused size-4 art exceeds the slot
            pm = grid.fit_w(pm, POOP_W)
        if len(pm) > POOP_W:
            pm = grid.fit_band(pm, (POOP_W + 2) * 2)
        ph_ = len(pm)
        col, up = i // 2, i % 2
        x = grid.X0 + col * (POOP_W + POOP_PAD) - push
        if up:      # top slot sits on the 8-tall bottom slot -> the 2x2 block tops out at the band (y6)
            y = px_h - 2 - POOP_W - ph_
        else:       # bottom slot grounds 2px above the border
            y = px_h - 2 - ph_
        pts += _blit(pm, x, y)
    return pts


COND_W = COND_H = 7                                # state.png cell size (DVPet 7x7 cells)


PLAY_HOP = 14                                      # DVPet jumping(): 6 up + 6 down + 2 rest per hop


PLAY_LEAD = 6                                      # the grounded lead-in before hop one (canon 0..5)


PLAY_HOP_H = 6                                     # apex px: the FULL body stays on the 24px arena


#                                                    (grounded top row = 24-16-2 = 6, so 6 is the max
#                                                    before a 16px mon clips the ceiling; the old 12
#                                                    launched half the body off-screen -- Joel
#                                                    2026-07-06 "jumping way too high").  1px per rise
#                                                    beat == canon's one moveUp per beat rhythm.
# DVPet gifting(): amble off LEFT until half off-screen (firstGoal -20/104), amble
# back RIGHT to just past centre (secondGoal 39/104 ~ x15/40), gift pops in beside
# the pet (it rides hidden until arrival in DVPet too), pose 5 hold -> giftEnd.
# 3 logical px per 2-interval beat scales to ~1px/beat here (same ~4s legs).
GIFT_OUT = 40                                      # beats*2 ticks: centre x12 -> x-8 (20px)


GIFT_BACK = 46                                     # x-8 -> x15 (23px)


GIFT_HOLD = 18                                     # the % (interval*45) settle before giftEnd


# BANDAI GRAMMAR (2026-07-11, Joel: "how did Bandai fit it all in a 32x16
# screen?" -- they didn't; the matrix is a STAGE, not a dashboard).  The LCD
# carries SCENE ACTORS only, and the pet keeps its full locked 32x16 play area:
#   - the filth block (bottom-left, a walk wall -- settled)
#   - the sleep Zzz, floating in the sky corner above the world
#   - the sick SKULL, standing beside the pet like the real device draws it --
#     a grounded scene object with its own walk wall ("icons can limit walking
#     space"); with 3-4 piles there is no 16px corridor left, so poop wins and
#     the skull yields to the HUD (which always says +sick anyway)
# Everything that is a BADGE, not an actor -- medicine/bandage/vitamin/fatigue/
# injury, the teach bulb, the care-call '!', the idle-state emotes -- lives on
# the status side of the game (STATUS panel deco, digicore pages, the msg-box
# alarm: tuipet's silkscreen chrome).  The care-fx scenes keep their own
# in-scene emotes (cheer/jeer/dying) -- those are full-screen animations,
# exactly how the hardware spends its pixels.
SICK_ZONE = COND_W + 1                             # skull slot + 1px gap off the grid's right edge


_WINDOW = grid.WINDOW                              # the locked 32x16 play window (LAW 2026-07-11:


def _clip_win(pts):
    """Canon overlay ink stays inside the 32x16 window (the matrix edge)."""
    x0, x1, y0, y1 = _WINDOW
    return [(x, y) for x, y in pts if x0 <= x < x1 and y0 <= y < y1]


def _sick_mark_up(pet):
    """The skull stands in the scene: sick, visible (lights on), and only when
    the piles leave the pet a 16px corridor beside it (poop always wins).
    advance()'s roamer wall and paint()'s clamp both key off this ONE
    predicate, so the skull and the pet can never share floor."""
    if not pet.sick or pet.dead or pet.num == -1 or not pet.lights:
        return False
    return _filth_right(pet.poop) <= grid.X1 - SICK_ZONE - SPRITE_W


_HIDDEN_STATUS_ICONS: set[str] = set()             # add keys here to hide a scene mark

# ---------------------------------------------------------------------------
# HOLIDAY DECORATIONS (2026-07-24, Joel: "wire it up").  A small festival
# prop tucks into the arena's top-left corner on a holiday -- ambient, over
# the same festival bonuses (double bits, sales, festival eggs) that were
# already live.  Three ride REAL ripped icons already aboard (candy, cake, a
# Digi-crest for the Odaiba anniversary); the present is the one DRAWN prop,
# design "A" (Joel approved it) -- an outline box with a centre ribbon and a
# bow, which reads as a gift at 8x8 where a solid blob would not.  Drawing is
# a deliberate exception to real-rips-only, made for a generic prop (not
# creature art) at Joel's call.
_PRESENT = ["01000010",
            "00100100",
            "11111111",
            "10011001",
            "10011001",
            "10011001",
            "10011001",
            "11111111"]

# holiday name (tournament.HOLIDAYS) -> its decoration.  "present" is the
# drawn prop; every other value is a load_icons() key (frame 0 is used).
HOLIDAY_DECOR = {
    "Halloween Festival": "f:7",     # candy
    "Christmas Festival": "present",
    "Odaiba Memorial Day": "i:15",   # the Crest of Courage -- the '01 flagship
    "New Year Festival": "f:6",      # cake
}


def _holiday_decor(today=None):
    """TODAY's festival decoration sprite (cropped rows), or None.

    Food icons are stored at 3x (24px cells over an 8px native sprite -- a
    clean integer upscale), so a food-keyed decoration is downsampled back
    to its true 8x8 to fit the corner.  That is REVERSING a known upscale,
    lossless, not a lossy shrink.  Item icons (the crest) are already
    native-size, and the present is the drawn 8x8 prop."""
    from . import tournament
    key = HOLIDAY_DECOR.get(tournament.holiday(today))
    if key is None:
        return None
    if key == "present":
        return _PRESENT
    frames = data.load_icons().get(key)
    if not frames:
        return None
    sprite = frames[0]
    if key.startswith("f:"):                 # 3x food cell -> native 8x8
        sprite = [r[::3] for r in sprite[::3]]
    return grid._crop(sprite)


def _effect_overlay(pet, frame_i, cols, px_h, tick=0):
    """The scene's overlay actors: filth piles, the sleep Zzz, the sick skull.
    Nothing else -- badges belong to the HUD, not the play field."""
    E = data.load_effects()
    pts = []
    if pet.dead:
        return pts
    # a festival prop in the TOP-LEFT corner (2026-07-24): ambient, shown for
    # a live pet OR an egg.  It sits where a resting pet (centred, x~12..28)
    # does not reach; a roamer may briefly pass in front, exactly like poop.
    deco = _holiday_decor()
    if deco:
        pts += _blit(deco, grid.X0, grid.TOP)
    if pet.poop:                                          # sized piles in the slot grid
        pts += _filth_pts(pet, tick, px_h=px_h)
    if pet.num == -1:
        return pts
    asleep = bool(getattr(pet, "asleep", False))
    # sleep Zzz: floats in the sky corner, above the 32x16 world (the 6px
    # glyph fills the sky strip exactly; a nap's own glyph is 7px and dips
    # onto the band's top row -- sleeping poses lie low, sweep-verified).
    # It shows lights-off too: the dark room keeps its Zzz (DVPet
    # sleepLightsOff), our one mark on a black field.
    zkey = "zzz_nap" if (getattr(pet, "nap", False) and E.get("zzz_nap")) else "zzz"
    # the Zzz belongs to the SLEEP SCENE, INSIDE the window (LAW: nothing
    # above the band).  It hangs at the band's top-right; a sleeper with <=2
    # piles is clamped to CENTRE (x12..27), so the corner columns are its own.
    # 3-4 piles push the sleeper right under the corner -- the Zzz yields to
    # the HUD (whose status word already says asleep), poop always wins.
    # It rides the sleep pose: an asleep pet still wearing another anim (a
    # disturbed sleeper's startle beat) skips a beat; a dark room keeps its
    # Zzz over the black field.
    in_sleep_scene = asleep and (pet.anim == "sleep" or not pet.lights)
    z_bot = 0
    if (in_sleep_scene and pet.poop < 3 and E.get(zkey)
            and zkey not in _HIDDEN_STATUS_ICONS):
        z = grid._crop(E[zkey][(tick // 10) % len(E[zkey])])
        pts += _blit(z, grid.X1 - len(z[0]), grid.TOP)
        z_bot = grid.TOP + len(z)
    # sick skull: HIGH at the band's top-right, floating at head height the
    # way the device marks status (Joel 2026-07-12 -- the grounded floor
    # placement was tuipet's own miss), blinking its 2-frame pair on the
    # stateNumTic beat (7 ticks awake / 10 asleep).  A sick SLEEPER's skull
    # tucks in under the Zzz -- the corner belongs to the sleep mark.
    if _sick_mark_up(pet) and E.get("st_sick") and "st_sick" not in _HIDDEN_STATUS_ICONS:
        sf = (tick // (10 if asleep else 7)) % 2
        sk = grid._crop(E["st_sick"][sf])       # crop: the cell pads its INK
        pts += _blit(sk, grid.X1 - len(sk[0]),
                     (z_bot + 1) if z_bot else grid.TOP)
    return pts



class FxMixin:
    """The fx half of the Screen widget (state contract: self.fx, self.update,
    self.roamer, self.frame_i -- arena.Screen composes this in)."""

    # ---- care-action animations (DVPet SpriteAnim eat/clean/cheer) -----------
    def start_fx(self, kind, icon=None, poop=0, old_num=None, pet=None, starving=False, good=True, script=None):
        steps = {"eat": 35, "cheer": 31, "jeer": 31, "clean": 22, "spit": 25, "evolve": 41, "dying": 50, "dna_charge": 44, "play": 48, "poop": 25, "poopdance": 21, "yawn": 22, "losing": 50,
                 "gift": GIFT_OUT + GIFT_BACK + GIFT_HOLD, "assist": 28, "inherit": 50}.get(kind, 12)
        self.fx = {"kind": kind, "step": 0, "steps": steps, "icon": icon, "poop": poop,
                   "old_num": old_num, "good": good}
        if kind == "item":
            # a scripted item-use (itemfx: the per-AnimationType canon tables)
            from . import itemfx
            sc = itemfx.SCRIPTS[script]
            self.fx["script"] = script
            self.fx["steps"] = sc["steps"]
            self.fx["snds"] = dict(sc["snds"])
            self.fx["end"] = sc["end"]
        if kind == "eat":
            # DVPet eat(): each chew beat is scaled by pow(N, mod) -- a starving pet or
            # a glutton wolfs food down (mod 0.9, ends ~beat 23), a picky eater dawdles
            # (mod 1.1, ~48); food descent (beats 0/2/4/6) is NOT scaled.  Disliked
            # food -> +9 grimace.  A heavy species (baseWeight>=40) skips a chew cycle
            # (DVPet's frame jump 18->26): two bites instead of three, ends ~beat 26.
            glut = getattr(pet, "glutton", 0) if pet else 0
            mod = 0.9 if (glut > 0 or starving) else (1.1 if glut < 0 else 1.0)
            # eat(): the grimace bite (+9) fires on DISLIKED food OR an overeating
            # stomach -- canon re-audit 2026-07 (the pill rides this same eat
            # fx on its own bite strip; pill-anim fix 2026-07-18)
            from .pet import OVEREAT_LIMIT as _OVL
            bite = 9 if (pet is not None and (getattr(pet, "_last_meal_disliked", False)
                                              or pet.hunger >= _OVL)) else 7
            heavy = pet is not None and pet.num != -1 and pet._base_weight() >= 40
            leftover = pet is not None and getattr(pet, "_last_meal_leftover", False)
            if leftover:
                # applyFood: modifier <= DisposeLeftoversMinModifier(0.5) -> the
                # STUFFED pet's meal is State.Munching -- two beats of chewing,
                # then disposeFood: it turns away and DROPS the rest off-screen
                beats = [int(b ** mod) for b in (10, 14, 18)]
                self.fx["chew"] = {beats[0]: 8, beats[1]: bite, beats[2]: 8}
                fb = (beats[1], 999, 999)                        # only bite one lands
                self.fx["bite_snds"] = {beats[1]: "eat"}
                self.fx["munch_at"] = beats[2]
                self.fx["steps"] = beats[2] + 22                 # the dispose tail
            elif heavy:
                beats = [int(b ** mod) for b in (10, 14, 18, 22)]
                self.fx["chew"] = {beats[0]: 8, beats[1]: bite, beats[2]: 8, beats[3]: bite}
                fb = (beats[1], beats[3], beats[3])         # food frames 0 -> 1 -> 3 (skips 2)
                self.fx["bite_snds"] = {beats[1]: "eat", beats[3]: "lastBite"}
                self.fx["steps"] = int(26 ** mod) + 1
            else:
                beats = [int(b ** mod) for b in (10, 14, 18, 22, 26, 30)]
                self.fx["chew"] = {b: (8 if i % 2 == 0 else bite) for i, b in enumerate(beats)}
                fb = (beats[1], beats[3], beats[5])
                # DVPet eat(): _eat on the first two bites, _lastBite on the third.
                self.fx["bite_snds"] = {fb[0]: "eat", fb[1]: "eat", fb[2]: "lastBite"}
                self.fx["steps"] = int(34 ** mod) + 1
            self.fx["food_beats"] = fb
        elif kind == "spit":
            # DVPet refuse(): _refuse fires on EVERY head-shake flip (t0/6/12/18).
            # (t0 sounds key as 1 -- the drain runs after the first advance.)
            self.fx["snds"] = {1: "refuse", 6: "refuse", 12: "refuse", 18: "refuse"}
        elif kind == "cheer":
            # DVPet cheer(): its sound (praise/_happy) plays at the anim's t0 --
            # keyed here so chained cheers (wash/evolve/heal tails) sound too.
            self.fx["snds"] = {1: "happy"}
        elif kind == "losing":
            # DVPet losing(): jeer(disposition, _lose) -- the sound at the
            # first UP beat, like every jeer
            self.fx["snds"] = {6: "lose"}
        elif kind == "jeer":
            # DVPet jeer(): the sound fires at the first UP beat (t6).  Canon
            # routes Bad_Scold through the _unhappy cue, but soundConfig.csv
            # maps unhappy -> angry.wav -- the same bark either way, so only
            # the POSES distinguish the variants here.
            self.fx["snds"] = {6: "angry"}
        elif kind == "evolve":
            # DVPet evolveAnim(): _evolve sounds at the first burst beat (t5);
            # digivolve() runs the strobe to evolFinish at 41 (was cut at 37).
            # An ITEM evolution (Digimental) prepends canon itemEvolve's first
            # act: the pet parades with the item cycling its own anim frames
            # (itemEvolveLoop -> jogress.wav), THEN the strobe fires.
            # Pre-ritual (anim hardening 2026-07-14): every reference fronts
            # the strobe with a first act -- the old form HOLDS, then its
            # SILHOUETTE blinks -- so the change reads as a ritual, not a cut.
            # An ITEM evolution keeps canon itemEvolve's parade as that act.
            off = 14 if icon else 12
            self.fx["off"] = off
            self.fx["steps"] = 41 + off
            self.fx["snds"] = {5 + off: "evolve"}
            if icon:                      # the parade opens on the jogress sting
                self.fx["snds"][1] = "jogress"
        elif kind == "inherit":
            # DVPet inheriting(): chip-shrink t11 / parent-grow t17 / parent-shrink
            # t37 all key the attackHit cue; the flight home pips inheritMove
            # (=alarm) every 4; the collide lands inheritCollide (=strongHit).
            # The t-values above are CANON's 65-beat timeline; these keys are
            # the same beats on _fxk_inherit's remapped 50-step timeline
            # (shrink 10 / grow 14 / visit-end 32 / collide 46) -- aligned
            # with the painter, do NOT "fix" them to the canon numbers
            # (sound/fx audit 2026-07-18).
            self.fx["snds"] = {10: "attackHit", 14: "attackHit", 32: "attackHit",
                               36: "alarm", 40: "alarm", 44: "alarm", 46: "strongHit"}
        elif kind == "dna_charge":
            # dnaCharge(): _dnaWash as the sweep enters (t21).
            self.fx["snds"] = {21: "wash"}

    def advance_fx(self):
        if not self.fx:
            return False
        self.frame_i += 1        # filth keeps animating through an fx (audit 2026-07)
        self.fx["step"] += 1
        if self.fx["step"] < self.fx["steps"]:
            return True
        kind = self.fx["kind"]
        had_filth = self.fx.get("poop", 0) > 0
        chain_eat = self.fx.get("chain_eat")
        pet_ref = self.fx.get("pet_ref")
        item_end = self.fx.get("end")
        self.fx = None
        if kind == "item" and item_end:
            # canon: playing()/interact/study/... resolve into Cheering;
            # angrySurprise resolves into Jeering (itemfx script tables)
            self.start_fx(item_end, good=True)
        elif kind == "clean" and had_filth:
            # DVPet clean(): the cheer chains ONLY when filth was actually washed
            # (an empty-room wash just ends -- no celebration).
            self.start_fx("cheer")
        elif kind in ("evolve", "gift", "play", "inherit"):
            # every canon flow that resolves into State.Cheering: evolFinish(true),
            # giftEnd, jumping() frame 48, inheriting()'s strobe tail (branches
            # collapsed 2026-07-05; poopToilet left with the staple props,
            # strict-DSprite items 2026-07-17; the heal/bandage fx left with
            # the pill-anim fix 2026-07-18 -- the pill is eaten, meal-style)
            self.start_fx("cheer")
        elif kind == "assist" and chain_eat:
            # assistantFeed runs the STANDARD eat underneath (canon
            # eat(Assistant_Feed)); the meal is already on the floor, so the
            # chained eat skips its own descent stages
            self.start_fx("eat", chain_eat, pet=pet_ref,
                          starving=getattr(pet_ref, "_last_meal_starving", False))
            self.fx["step"] = 6
        return self.fx is not None

    def _pose_rows(self, pet, role, phase):
        if pet.num == -1:
            rec = egg_mod.record(pet.egg_type)
            roles = egg_mod.ROLES
        else:
            rec = data.record_for(pet.num)   # never KeyError: a cross-version
            #                                  save wears the placeholder
            roles = data.ROLES
        frames = roles.get(role, [0])
        first = next((f for f in rec["frames"] if f), rec["frames"][0])
        return rec["frames"][frames[phase % len(frames)]] or first

    def _pose_rows_idx(self, pet, i):
        """A single creature frame by raw sprite index (for beat-scripted fx poses)."""
        if pet.num == -1:
            rec = egg_mod.record(pet.egg_type)
        else:
            rec = data.record_for(pet.num)   # never KeyError: a cross-version
            #                                  save wears the placeholder
        fr = rec["frames"]
        first = next((f for f in fr if f), fr[0])
        return (fr[i] if i < len(fr) and fr[i] else None) or first

    def _food_frames(self, key, px=8):
        if key and key.startswith("sym:"):
            # 8px LCD symbols eat through their OWN glyph, no DVPet food sheet
            # and no downsample (DSprite: the pill eats PILL -> HALF_PILL ->
            # gone, so the picked icon IS the eaten one).
            from .feedscreen import PILL_FRAMES
            return {"sym:pill": PILL_FRAMES}.get(key)
        raw = data.load_icons().get(key)
        if not raw:
            return None
        from .render import downsample
        f = max(1, 24 // px)
        return [downsample(fr, f) for fr in raw]           # 24px source -> ~px tall on the LCD

    def _fx_filth(self, pet, tick, count=None):
        """DVPet checkFilth: the care anims (eat/cheer/jeer/refuse/poop) keep the
        filth piles on screen and stand the pet clear of them
        (adjustCharacterForFilth).  Returns (overlay_pts, clear_xshift)."""
        n = min((getattr(pet, "poop", 0) or 0) if count is None else count, POOP_MAX_PILES)
        if not n:
            return [], 0
        pts = _filth_pts(pet, tick, count=n)
        base = PET_BASE_X
        cap = max(0, grid.X1 - SPRITE_W - base)             # stay inside the grid's right edge
        return pts, min(max(0, _filth_right(n) - base), cap)

    def _paint_fx(self, pet):
        """The care-fx painter, decomposed (audit 2026-07): a shared context is
        pre-loaded (default pose, the cross-kind FILTH prelude),
        then the kind's own painter (_fxk_<kind>) mutates it.  Bodies verbatim
        from the old 210-line chain; behavior pinned by the fx golden."""
        fx = self.fx
        on, bg = LCD_ON, LCD_BG
        bgimg = self._background(pet)
        if bgimg:
            on = SIL_SCENE   # dark silhouette day OR night, same rule as paint() --
            #                the pet is never white (the old SIL_LIGHTSOFF branch washed
            #                every night-time care fx white)
        step = fx["step"]
        # an Assistant_Lights visit is the one anim that CAUSES the darkness --
        # and DVPet toggles the room at the anim's FINAL beat, so the whole
        # visit (switch AND the helper's exit) plays lit; the old cut at beat
        # 18 left the exit playing white in the dark (bug report 2026-07-13)
        lit_visit = fx["kind"] == "assist" and fx.get("act") == "lights"
        dark = not pet.lights and fx["kind"] != "evolve" and not lit_visit
        if dark:
            # the dark room stays dark through a care fx -- and DVPet's care
            # anims KEEP the fully-opaque lightsOff cover up (SpriteAnim sets
            # lightsOff inside the anims), so a dark-room fx shows NOTHING:
            # no pet, no props, no white poses (bug report 2026-07-13, "mon in
            # white poses during lights out sequence"); the sprite blank-out
            # happens just before update() once the kind painter has run
            bgimg, bg, on = None, VOID, SIL_LIGHTSOFF
        c = _FxCtx()
        c.px_h = SCREEN_ROWS * 2
        c.bg, c.bgimg = bg, bgimg
        # only clean/dying rely on this default pose; the kind painters override
        # `rows` unconditionally otherwise
        pose = {"clean": "idle", "dying": "exhausted"}.get(fx["kind"], "idle")
        c.rows = self._pose_rows(pet, pose, step // 2)
        c.overlay = []
        c.free = []          # (the weather plane left with the weather system)
        c.xshift = 0
        c.yshift = 0
        c.mirror = False
        if fx["kind"] in ("eat", "cheer", "jeer", "spit"):
            # DVPet checkFilth runs inside these anims: piles stay visible and the
            # pet (and its food) stands clear of them.
            filth_pts, filth_clear = self._fx_filth(pet, self.frame_i)
            c.overlay += filth_pts
            c.xshift = filth_clear
        elif fx["kind"] == "poop":
            # DVPet poop(): squat (+4, MIRRORED) clear of the old piles, net-zero
            # sway every 3 ticks; the new pile lands at t18 with the size-keyed
            # sound (fx snds) and the relieved pose (+5); ends 24.
            new = fx["step"] >= 18
            filth_pts, filth_clear = self._fx_filth(pet, self.frame_i,
                                                    count=fx.get("poop", 0) + (1 if new else 0))
            c.overlay += filth_pts
            sway = -1 if (3 <= step < 18 and (step // 3) % 2 == 1) else 0
            c.xshift = filth_clear + sway
            c.rows = self._pose_rows_idx(pet, 5 if new else 4)
        elif fx["kind"] in ("yawn", "poopdance"):
            # canon idle(): the tells are IDLE-family specials -- yawning()/
            # poopDance() move RELATIVE to the pet's LocX with its current
            # facing; only care anims resetScreen() to the anchor.  Seed the
            # roamer so the pose plays where the pet stands (walk-pose audit
            # 2026-07-08: it teleported to centre for every tell).
            c.xshift = self.roamer.xshift
            c.mirror = self.roamer.mirror
        painter = getattr(self, "_fxk_" + fx["kind"], None)
        if painter is not None:
            painter(pet, fx, step, c)
        if fx["kind"] in ("yawn", "poopdance"):
            # canon idle() keeps running stateAnims (checkStates/checkFilth/
            # stateNumTic) while a special idle plays: the scene actors (piles,
            # skull, Zzz) stay up and blinking through the pose.  Care anims
            # keep their resetScreen() blackout -- canon hides those labels.
            # The pose sways around the roamer's spot, so it gets the same
            # zone clamp as paint() (sickness striking MID-yawn would
            # otherwise stand the skull on the pet for the pose's last beats).
            lo = (_filth_right(pet.poop) if pet.poop else grid.X0) - PET_BASE_X
            cap = ((grid.X1 - SICK_ZONE if _sick_mark_up(pet) else grid.X1)
                   - SPRITE_W) - PET_BASE_X
            c.xshift = min(max(c.xshift, lo), max(cap, lo))
            c.overlay += _effect_overlay(pet, self.frame_i // 4, SCREEN_COLS, c.px_h,
                                         tick=self.frame_i)
        if dark:                     # the opaque cover: black over everything
            c.rows, c.overlay, c.free, c.xshift, c.yshift = [], [], [], 0, 0
        mirror = (c.mirror or fx["kind"] in ("dying", "poop")
                  or (fx["kind"] == "gift" and GIFT_OUT <= step < GIFT_OUT + GIFT_BACK)  # facing right, ambling back
                  or (fx["kind"] == "spit" and (step // 6) % 2 == 0))   # refuse(): head-shake flips
        if c.yshift and c.rows:
            # a hop may lift the sprite only as far as ITS clearance under the
            # band top -- nothing exits the window upward (LAW: off-screen is
            # left/right only).  A full-16px mon has no headroom, exactly like
            # the real 16px matrix: its excitement is the pose, not the air.
            ink = grid._crop(c.rows)
            c.yshift = max(0, min(c.yshift, grid.BAND - len(ink)))
        from . import arena as _arena
        # render_screen resolves in ARENA's namespace: tuipet.arena.render_screen
        # is the documented spy/patch point, and it must catch fx frames too
        self.update(_arena.render_screen(c.rows, SCREEN_COLS, SCREEN_ROWS, on, c.bg,
                                  xshift=c.xshift, yshift=c.yshift,
                                  overlay=_clip_win(c.overlay),
                                  bgimg=c.bgimg, mirror=mirror, clip=_WINDOW))

    def _fxk_eat(self, pet, fx, step, c):
        # DVPet eat(): 24px food descends in 4 stages (beats 0/2/4/6) toward the
        # mouth, then a chew triad alternates open-mouth(+8)/chew(+7) at beats
        # 10/14/18/22/26/30 while the food is consumed frame-by-frame; ends ~34.
        food0 = self._food_frames(fx.get("icon") or "f:0")
        fw0 = len(food0[0][0]) if (food0 and food0[0] and food0[0][0]) else 8
        if getattr(pet, "poop", 0):
            # canon eat(): pad = _filthLabel.getSizeX() -- BOTH the food
            # (x31+pad) and the char (x55+pad) slide right by the FULL filth
            # width whenever piles exist, however narrow the block.  The old
            # clear-shift was 0 for 1-2 piles (their edge == the anchor), so
            # the food descended ONTO the slots (feeding audit 2026-07-08).
            # Piles stay visible: checkFilth runs inside eat().
            n = min(pet.poop, POOP_MAX_PILES)
            c.xshift = (_filth_right(n) - PET_BASE_X) + fw0
        elif c.xshift == 0:
            c.xshift = -1                                  # no filth: DVPet char x29 of 104 (~28%)
        # the food is BORN inside the window (Joel 2026-07-12: the descent's
        # left columns were getting cut at the matrix edge): slide the whole
        # canon-abutted pair (food right edge == char left edge) right until
        # the food's left edge sits at the window's -- x4 -- never past it
        c.xshift = max(c.xshift, (grid.X0 + fw0) - PET_BASE_X)
        ma = fx.get("munch_at")
        if ma is not None and step >= ma:
            # disposeFood: the pet turns away (pose 1, flipping at beat 5) and
            # the half-eaten food FALLS off the bottom of the screen
            d = step - ma
            c.rows = self._pose_rows_idx(pet, 1)
            c.mirror = d >= 5
            food = self._food_frames(fx.get("icon") or "f:0")
            if food:
                fr = food[min(1, len(food) - 1)]
                if fr:
                    fw = len(fr[0])
                    fy = 13 + max(0, d - 10)
                    if fy < grid.FLOOR:                    # crumbs stop AT the floor (no bottom exit)
                        c.overlay += _blit(fr, max(grid.X0, PET_BASE_X + c.xshift - fw), fy)
            return
        chew = fx.get("chew") or {10: 8, 14: 7, 18: 8, 22: 7, 26: 8, 30: 7}
        pose_i = 0
        for b in sorted(chew):
            if step >= b:
                pose_i = chew[b]
        c.rows = self._pose_rows_idx(pet, pose_i)
        food = food0
        if food:
            fw = fw0
            # DVPet: the food's RIGHT edge meets the pet's LEFT edge (foodLabel x31+24 == char x55),
            # so it descends right into the mouth -- abut it instead of stranding it on the far left.
            # (The filth pad above already moved BOTH food and char clear of the piles.)
            fx_x = max(grid.X0, PET_BASE_X + c.xshift - fw)
            stage = 0 if step < 2 else 1 if step < 4 else 2 if step < 6 else 3
            fy = (grid.TOP, 8, 11, 13)[stage]              # DVPet descent, mapped INTO the window: the
            #                                                  food drops from the band top to the mouth
            #                                                  (it used to enter from over the matrix --
            #                                                  LAW 2026-07-11: nothing crosses the top edge)
            fb = fx.get("food_beats") or (14, 22, 30)
            fi = 0 if step < fb[0] else 1 if step < fb[1] else 2 if step < fb[2] else 3
            c.overlay += _blit(food[min(fi, len(food) - 1)], fx_x, fy)

    def _fxk_clean(self, pet, fx, step, c):
        # DVPet clean(): the wash enters from the right and, once it reaches the pet,
        # shoves the pet AND the filth left together until they slide off-screen (pet
        # in its clean pose, frame 4); the chained cheer then brings the pet back.
        E = data.load_effects()
        wash = E.get("wash", [None])[0]
        wx = SCREEN_COLS - step * 3                        # wash front: enters right, exits left
        base = PET_BASE_X
        clear = (_filth_right(fx.get("poop", 0)) - base) if fx.get("poop") else 0
        push = max(0, base + clear + SPRITE_W - wx)        # wash shove, measured from the pet's RIGHT edge
        c.xshift = clear - push                            # pet starts cleared of the filth, then both
        if push > 0:                                       # slide left in lockstep (gap preserved, no mash)
            c.rows = self._pose_rows_idx(pet, 4)           # DVPet drawNum(4) while being washed
        if fx.get("poop"):                                 # the sized piles slide off with the pet
            c.overlay += _filth_pts(pet, self.frame_i, count=fx["poop"],
                                    sizes=fx.get("sizes"), push=push, px_h=c.px_h)
        if wash:
            wash = grid.fit_band(wash)                     # the 21px shower fits the 16px band
            c.overlay += _blit(wash, wx, grid.TOP + (grid.BAND - len(wash)) // 2)

    def _fxk_assist(self, pet, fx, step, c):
        # DVPet assistantClean/assistantFeed/assistantLights: the hired helper
        # descends from the top on the LEFT (locX 6, icon flipped to face the
        # pet), does its round, and rises away (moveUp beats 18/19).  Mapped to
        # 28 steps: descend 0-7, act 8-19 (with the wiggle), leave 20+.  During
        # a clean the piles sweep RIGHT off-screen (filthLabel.moveRight(4) each
        # descent beat) -- the OPPOSITE of your wash, which shoves them left.
        act = fx.get("act")
        feed = act in ("feed", "strength")
        cleaning = act == "clean" and fx.get("poop")
        if cleaning:
            # canon assistantClean: filthLabel.moveRight(4) sweeps the mess RIGHT
            # while adjustCharacterForFilth() clamps the pet to the filth's right
            # edge every beat -- so the pet is shoved right AHEAD of the piles and
            # both slide off together (SpriteAnim.assistantClean).  The old
            # give-ground xshift (max 8) ignored the filth entirely, so a full
            # 4-pile block (16px) sat UNDER a sleeping pet auto-care was cleaning
            # -- the poop-overlap glitch (audit 2026-07-08).
            push = -step * 3                                   # filth marches right
            c.xshift = _filth_right(fx["poop"]) - push - PET_BASE_X   # stay clear of its right edge
            c.overlay += _filth_pts(pet, self.frame_i, count=fx["poop"],
                                    sizes=fx.get("sizes"), push=push, px_h=c.px_h)
        elif not feed:
            # assistantLights: the pet gives ground as the helper arrives (DVPet
            # moveRight(2) per descent beat) and drifts back as it leaves --
            # 4+16 | 20+16 fills the grid band x[4,36) with both sprites abutted
            if step < 8:
                c.xshift = min(8, step * 2)
            elif step < 20:
                c.xshift = 8
            else:
                c.xshift = max(0, 8 - (step - 19) * 2)
        if pet.asleep:
            c.rows = self._pose_rows(pet, "sleep", step // 2)
        _, by_num = data.load_sprites()
        rec = by_num.get(fx.get("helper", -1))
        fr = rec["frames"] if rec else None
        hf = (fr[0] if fr and fr[0] else next((f for f in fr if f), None)) if fr else None
        hh = len(hf) if hf else 16
        ground = c.px_h - hh - 2
        if feed:
            # canon assistantFeed: the helper walks the MEAL in -- descends
            # WITH the food, sets it down at the eat spot, and EXITS LEFT by
            # beat 10 (moveLeft 24 x2); the standard eat anim (chained) takes
            # it from there
            food = self._food_frames(fx.get("icon") or "f:44")
            f0 = food[0] if (food and food[0]) else None
            fw = len(f0[0]) if f0 else 8
            fx_x = max(0, PET_BASE_X - 1 - fw)             # the eat anim's food spot
            hff = [row[::-1] for row in hf] if hf else None   # faces the pet
            if step < 7:                                   # the walk-in
                hy = -hh + (step + 1) * (ground + hh) // 7
                hx = 2
                if hff and hy > -hh:
                    c.overlay += _blit(hff, hx, hy)
                if f0:
                    c.overlay += _blit(f0, hx + 10, max(0, hy + hh // 2))
            else:                                          # set down + exit left
                hx = 2 - (step - 6) * 8
                if hf and hx > -20:                        # native facing: walking LEFT out
                    c.overlay += _blit(hf, hx, ground)
                if f0:
                    c.overlay += _blit(f0, fx_x, c.px_h - 2 - len(f0))
            return
        if hf:
            hf = [row[::-1] for row in hf]                 # flipped to face the pet
            if step < 8:
                hy = -hh + (step + 1) * (ground + hh) // 8   # moveDown beats
            elif step < 20:
                hy = ground
            else:
                hy = ground - (step - 19) * 6              # moveUp(24) x2: off the top
            hx = 4 + (0 if not (16 <= step < 20) else (-1 if step % 2 == 0 else 1))   # the wiggle
            if hy > -hh:
                c.overlay += _blit(hf, hx, hy)

    def _fxk_cheer(self, pet, fx, step, c):
        # DVPet cheer(): pose alternates up(+5)/down(+7) every 6 intervals with a
        # "happy" emote bubble pulsing on the up-beats; ends ~beat 30.  A
        # spoiling Bad_Praise (cheer(false)) bounces on 6/4 instead of 5/7.
        up = (step // 6) % 2 == 0
        if fx.get("good", True):
            c.rows = self._pose_rows_idx(pet, 5 if up else 7)
        else:
            c.rows = self._pose_rows_idx(pet, 6 if up else 4)
        if up:
            hap = data.load_effects().get("happy")
            if hap:
                hf = hap[(step // 6) % len(hap)]
                # DVPet cheer(): the pet stays CENTRED and the emote rides its right
                # edge (adjustEmotionLabel) -- not pinned to the far corner.
                # Head height (grid.TOP), IN the window: y=1 was the pre-law
                # bezel spot and the clip beheaded the sun (2026-07-12).
                c.overlay += _blit(hf, PET_BASE_X + c.xshift + SPRITE_W, grid.TOP)

    def _fxk_gift(self, pet, fx, step, c):
        # DVPet gifting(): walk-toggle poses (spriteNum/spriteNum+1) per beat;
        # facing follows the leg (drawNumMirror false left / true right).  The
        # present is only revealed on arrival, beside the pet (locX gap 4/104
        # ~ 1px), vertically centred -- then pose 5 faces it for the hold.
        base = PET_BASE_X
        if step < GIFT_OUT:
            c.xshift = -(step // 2)                        # off to fetch it
            c.rows = self._pose_rows(pet, "walk", step // 2)
        elif step < GIFT_OUT + GIFT_BACK:
            c.xshift = -(GIFT_OUT // 2) + (step - GIFT_OUT) // 2   # ambling back
            c.rows = self._pose_rows(pet, "walk", step // 2)
        else:
            c.xshift = -(GIFT_OUT // 2) + (GIFT_BACK - 1) // 2   # exactly where the walk ended
            c.rows = self._pose_rows_idx(pet, 5)           # ta-dah beside the present
        if step >= GIFT_OUT:
            # the pet pushes home a WRAPPED PRESENT, not the bare item (2026-
            # 07-24, Joel: "presents should be just that, a surprise") -- the
            # contents stay hidden until the reveal message opens it at the
            # end of the amble.  The box rides the whole return leg (canon
            # meatButton moveRight(3) in lockstep).
            g0 = _PRESENT
            gw, gh = 8, 8
            gx = base + c.xshift - gw - 1
            if gx > -gw:
                c.overlay += _blit(g0, gx, grid.TOP + max(0, (grid.BAND - gh) // 2))

    def _fxk_play(self, pet, fx, step, c):
        # DVPet jumping() (SpriteAnim 17308): the pet bounces with joy -- hops UP on
        # the excited pose (5) and lands on the neutral pose (1), a happy chirp at the
        # top of each hop.  Distinct from cheer (which bounces in place on 5/7 with an
        # emote bubble) -- here the body actually leaves the ground.
        # canon shape: a 6-beat grounded lead-in, then rise(6)/fall(6)/rest(2)
        # per hop -- rises land on canon's 6/20/34 with the sting at each launch
        if step < PLAY_LEAD:
            rise, air, y = False, False, 0
        else:
            ph = (step - PLAY_LEAD) % PLAY_HOP
            rise = ph < 6
            air = ph < 12
            y = (PLAY_HOP_H * (ph + 1) // 6 if rise
                 else PLAY_HOP_H * (12 - ph) // 6 if air else 0)
        c.rows = self._pose_rows_idx(pet, 5 if rise else 1)
        c.yshift = y
        # a toy USED from the bag sits on the floor beneath the hop, animating
        # its own frames (canon jumping(): _itemLabel at the pet's feet, 2->1
        # per hop -- the long-flagged unported piece; play audit 2026-07-05)
        if fx.get("icon"):
            frames = data.load_icons().get(fx["icon"]) or []
            frames = [f for f in frames if f]
            if frames:
                # canon _itemLabel: frame 1 while the pet is AIRBORNE (rise
                # start -> landing), frame 2 while it rests between hops.
                # RAW frames -- the /3 downsample crushed the toy to 2px
                # (item-anim audit 2026-07-07)
                toy = frames[(0 if air else 1) % len(frames)]
                if toy:
                    # BESIDE the feet (the eat fx's item-side convention):
                    # canon keeps the pet elevated over the toy for the whole
                    # anim, but our hop grounds out each cycle and would land
                    # ON it -- next to the pet it stays readable every beat
                    tw, th = max(len(r) for r in toy), len(toy)
                    tx = max(0, PET_BASE_X + c.xshift - tw - 1)
                    c.overlay += _blit(toy, tx, c.px_h - 2 - th)

    def _fxk_item(self, pet, fx, step, c):
        # a scripted item-use (item-anim audit 2026-07-07): the item's OWN
        # icon frames animate on the canon stage -- item left/beside/feet,
        # pet right -- per the itemfx table for its AnimationType
        from . import itemfx
        # icons are extracted at native size (~8x5): draw them RAW -- the /3
        # downsample crushed toys to 2px specks (the "broken animations")
        frames = [f for f in (data.load_icons().get(fx["icon"]) or []) if f]
        iw = max((max(len(r) for r in f) for f in frames), default=8)
        ih = max((len(f) for f in frames), default=8)   # tallest frame owns the floor
        fr, pose, ix, iy, pdx, pdy = itemfx.state(fx["script"], step, iw, ih, c.px_h)
        c.rows = self._pose_rows_idx(pet, pose)
        c.xshift = itemfx.PET_X - PET_BASE_X + pdx
        c.yshift = -pdy
        if frames:
            bm = frames[fr % len(frames)]
            # bottom-anchor: shorter frames sit ON the floor line, not above it
            c.overlay += _blit(bm, ix, iy + ih - len(bm))   # _stamp clips

    def _fxk_jeer(self, pet, fx, step, c):
        # DVPet jeer(goodScold): the SCOLD reaction -- pose alternates down(+4)/up(+6)
        # every 6 intervals, leading DOWN, with the "unhappy" emote riding the pet;
        # ends ~beat 30.  (Poses 9/10 belong to badHealthJeer, the dying variant.)
        down = (step // 6) % 2 == 0
        if fx.get("good", True):                # Jeering: the deserved 4/6 pair
            c.rows = self._pose_rows_idx(pet, 4 if down else 6)
        else:                                   # Bad_Scold/Sad_Jeering: the slump (10/9)
            c.rows = self._pose_rows_idx(pet, 10 if down else 9)
        un = data.load_effects().get("unhappy")
        if un:
            uf = un[(step // 6) % len(un)]
            # DVPet jeer(): centred pet, emote at its right edge (not the corner),
            # head height in the window (y=1 predated the law's clip).
            c.overlay += _blit(uf, PET_BASE_X + c.xshift + SPRITE_W, grid.TOP)

    def _fxk_spit(self, pet, fx, step, c):
        # DVPet refuse(): pose 4 held the whole beat while the head SHAKES via
        # mirror flips T/F/T/F at 0/6/12/18 (_refuse on each flip, wired in
        # start_fx); ends at 24.  No food drops -- the meal never appears.
        # (the Depressed pose-9 variant left with the mood system)
        c.rows = self._pose_rows_idx(pet, 4)

    def _fxk_evolve(self, pet, fx, step, c):
        # DVPet evolveAnim(): the room plunges DARK (lightsOff, fully opaque -- the
        # pet vanishes) and the bright "evol" burst strobes over it at beats
        # 5/12/19/25/29/34 (each icon holds until the next beat); changeSprite()
        # swaps in the evolved form at beat 21 UNDER darkness, so it emerges on the
        # next burst.  _evolve sounds at the first burst (start_fx snds).  The
        # chained cheer(true) afterwards is DVPet evolFinish.
        old = fx.get("old_num")
        off = fx.get("off", 0)
        if step < off and fx.get("icon"):                  # itemEvolve's first act: the
            pose = 1 if (step // 4) % 2 == 0 else 4        # pet parades (canon poses
            rec = data.load_sprites()[1].get(old) if old not in (None, -1) else None
            if rec:                                        # animValue+1 <-> +4)...
                fr = rec["frames"]
                pf = (fr[pose] if pose < len(fr) and fr[pose] else fr[0]) or c.rows
                c.rows = pf
            raw = data.load_icons().get(fx.get("icon"))    # ...with the Digimental
            ic = [f for f in (raw or []) if f]             # cycling its OWN frames
            if ic:
                f = ic[(step // 2) % len(ic)]
                c.overlay += _blit(f, 2, c.px_h - len(f) - 4)
            return
        if step < off:                                     # natural evolve's first act
            # (anim hardening 2026-07-14): the old form HOLDS (beats 0-5),
            # then its flood-filled SILHOUETTE blinks 0.2s on / 0.2s off
            # (beats 6-11) -- the "something is happening to me" tell every
            # reference fronts the strobe with.
            rec = data.load_sprites()[1].get(old) if old not in (None, -1) else None
            fr0 = rec["frames"][0] if rec and rec["frames"] and rec["frames"][0] else None
            if fr0:
                if step < 6:
                    c.rows = fr0
                elif (step // 2) % 2 == 1:
                    from .digicorescreen import silhouette
                    c.rows = silhouette(fr0)
                else:
                    c.rows = fr0
            return
        step -= off                                        # the strobe below runs on canon beats
        if step < 21 and old not in (None, -1):            # old form until the covered swap
            rec = data.load_sprites()[1].get(old)
            if rec and rec["frames"][0]:
                c.rows = rec["frames"][0]
        burst = any(a <= step < b for a, b in
                    ((5, 10), (12, 14), (19, 21), (25, 27), (29, 32), (34, 99)))
        if burst:
            # "evol" burst: the room shows through DVPet's 50% dither mask
            _evol_strobe(c)
        else:                                              # lightsOff beats: the void, pet hidden
            c.rows, c.bgimg, c.bg = [], None, VOID

    def _fxk_inherit(self, pet, fx, step, c):
        # DVPet inheriting(): the pet stands RIGHT (locX width-3-size); the chip
        # descends on its left (t1-10), shrinks to a point (t11, chipShrink), the
        # DEPARTED ancestor rises from it (t17, parentGrow) and greets on poses
        # 6/1 (t24-33), fades (t37, parentShrink), then the chip reappears and
        # wobbles home into the pet (t42-64, inheritMove pips) and collides
        # (t65) into an evol-dither strobe.  Mapped to 50 steps; the sprite
        # scaling beats become appear/disappear (16px art does not scale).
        c.xshift = 8                                       # the pet gives the seance room
        chip = data.load_icons().get("i:32")               # raw: the 8x7 chip art is already
        cf = chip[0] if chip and chip[0] else None         # LCD-scale (_food_frames' /3 is for 24px food)
        cw = len(cf[0]) if cf and cf[0] else 8
        cx = 8
        _, by_num = data.load_sprites()
        anc = by_num.get(fx.get("ancestor", -1))
        if step < 10:                                      # the chip descends
            if cf:
                c.overlay += _blit(cf, cx, -8 + step * 2)
        elif step < 14:                                    # ...and shrinks to a point
            cy = c.px_h // 2 + 4
            c.overlay += [(cx + cw // 2 + dx, cy + dy) for dx in (0, 1) for dy in (0, 1)]
        elif step < 32 and anc:                            # the ancestor's visit
            fr = anc["frames"]
            pose = 6 if ((step - 14) // 4) % 2 == 0 else 1
            af = (fr[pose] if pose < len(fr) and fr[pose] else fr[0]) or next((f for f in fr if f), None)
            if af:
                c.overlay += _blit(af, cx - 2, c.px_h - len(af) - 2)
        elif step < 46:                                    # the chip flies home
            if cf:
                wob = -1 if (step % 4) < 2 else 1
                c.overlay += _blit(cf, cx + (step - 34) * 2, c.px_h // 2 + wob)
        else:                                              # the collide strobe
            if step % 2 == 0:
                _evol_strobe(c)

    def _fxk_dna_charge(self, pet, fx, step, c):
        # DVPet dnaCharge() (SpriteAnim 12860): the FIELD badge drops in beside the
        # pet (t1-7), wobbles (9/11/13), inserts (t16), then the full-screen dnaWash
        # wave sweeps DOWN over everything (t21+, ~9px/tick of 120) while the pet
        # strains (pose 9 from the collide at t27); the badge sinks away at the tail
        # (t37+).  Pet nudged 1 right (setLocX 3+x), pose 0 until the collide.
        E = data.load_effects()
        c.rows = self._pose_rows_idx(pet, 9 if step >= 27 else 0)
        c.xshift = 1
        badge = (E.get("field_" + str(fx.get("icon") or "")) or E.get("field_None") or [None])[0]
        if badge:
            # the badge art is 14x14 -- a small chip on the source's 60px
            # stage, but NEAR PET-SIZE on our 24px window (Joel 2026-07-22:
            # "enlarged dna item sprites during eating animation").  Halve it
            # like the eat fx halves its 24px food: a 7px chip feeds in at
            # the source's proportion
            from .render import downsample
            badge = downsample(badge, 2)
            bw, bh = len(badge[0]), len(badge)
            base = PET_BASE_X + c.xshift
            bx = max(0, base - 2 - bw) + ({9: -1, 10: -1, 11: 1, 12: 1}.get(step, 0))
            rest = 8                                       # DVPet rest y21 of 60 -> ~8 of 24
            if step < 8:
                by = -bh + int((rest + bh) * step / 7)     # moveDown 6/tick descent
            else:
                # sink at 2px/tick: the half-scale chip (7px since the fx
                # audit 2026-07-22) never cleared the window bottom at
                # 1px/tick -- it sat at the floor and BLINKED OUT with the
                # fx's last frame instead of sinking away
                by = rest + (1 if step >= 16 else 0) + max(0, step - 36) * 2
            c.overlay += _blit(badge, bx, by)
        wash = (E.get("dna_wash") or [None])[0]
        if wash and step >= 21:
            wy = -len(wash) + (step - 21) * 4              # 9px/tick of 120 -> ~4px/tick of 48
            c.overlay += _blit(wash, max(0, (SCREEN_COLS - len(wash[0])) // 2), wy)

    # (_fxk_heal -- the DVPet bandage() port -- left with the pill-anim fix
    # 2026-07-18: the source has no heal anim at all; its pill is EATEN, and
    # the pill was this painter's only rider.  It also drew the medicine strip
    # at y0-4, above the window top (y6) -- a clipped sliver either way.)

    def _fxk_losing(self, pet, fx, step, c):
        # DVPet losing() (the home-battle defeat): the sore loser jeers for 30
        # beats -- disposition-shaded pose pair (sour 4/6, mild slumps 10/9)
        # with the "dying" emote strobing on the jeer cadence -- then the WASH
        # rolls in from the right and sweeps it clean off the screen.
        E = data.load_effects()
        if step < 30:
            down = (step // 6) % 2 == 0
            sour = pet._disposition() < 0
            if sour:
                c.rows = self._pose_rows_idx(pet, 4 if down else 6)
            else:
                c.rows = self._pose_rows_idx(pet, 10 if down else 9)
            dye = E.get("dying")
            if dye and (step // 6) % 2 == 0:
                c.overlay += _blit(dye[0], PET_BASE_X + c.xshift + SPRITE_W + 1,
                                   grid.TOP)
        else:
            t = step - 30
            wash = E.get("wash", [None])[0]
            wx = SCREEN_COLS - t * 3
            push = max(0, PET_BASE_X + SPRITE_W - wx)
            c.xshift = -push
            c.rows = self._pose_rows_idx(pet, 4)   # shoved in the washed pose
            if PET_BASE_X + SPRITE_W - push < 0:
                c.rows = []                        # swept clean off
            if wash:
                c.overlay += _blit(wash, wx, max(0, (c.px_h - len(wash)) // 2))

    # (_fxk_toilet -- DVPet poopToilet -- left with the staple props:
    # strict-DSprite items, 2026-07-17)

    def _fxk_yawn(self, pet, fx, step, c):
        # DVPet yawning() (SpriteAnim 15742): idle -> the yawn (+8 at beat 4)
        # -> a side-sway (x-3/+3 pairs, beats 10..28) -> the stretch tail
        # (+3/+1 alternating, 33..53).  The special-idle tell that bedtime
        # nears; the doze-off keeps its simple two-pose yawn anim.
        if step < 4:
            c.rows = self._pose_rows_idx(pet, 0)
        elif step <= 9:
            c.rows = self._pose_rows_idx(pet, 8)
        elif step <= 14:
            c.rows = self._pose_rows_idx(pet, 8)
            c.xshift += -1 if ((step - 10) // 3) % 2 == 0 else 1
        else:
            c.rows = self._pose_rows_idx(pet, 3 if ((step - 15) // 2) % 2 == 0 else 1)

    def _fxk_poopdance(self, pet, fx, step, c):
        # DVPet poopDance (a special-idle roll while the gauge is full): a
        # nervous wiggle (+-1 every other beat, 2..10) then pose 4 flipping its
        # mirror every 2 beats (12..18) -- the tell that a poop is coming.
        # tuipet's gauge fires the poop the moment it fills, so the dance rolls
        # while the need APPROACHES instead (>=80%% of the interval).
        if step <= 10:
            c.rows = self._pose_rows_idx(pet, 0)
            c.xshift += -1 if (step // 2) % 2 == 1 else 0
        else:
            c.rows = self._pose_rows_idx(pet, 4)
            # canon drawNumMirror(4, !getIsMirror()): the flip alternates
            # RELATIVE to the pet's current facing (seeded from the roamer)
            if ((step - 12) // 2) % 2 == 1:
                c.mirror = not c.mirror

    def _fxk_dying(self, pet, fx, step, c):
        # DVPet dying() (SpriteAnim 13179): the collapsed pet (pose 10, mirrored)
        # sways +/-1 as the 'dying' emote (dying/dying2) swaps at its right edge,
        # BOTH on a 10-tick beat (frame % (10*interval)), just before the memorial.
        c.xshift = 1 if (step // 10) % 2 == 0 else -1
        dye = data.load_effects().get("dying")
        if dye:
            df = dye[(step // 10) % len(dye)]
            c.overlay += _blit(df, PET_BASE_X + SPRITE_W + c.xshift, grid.TOP)

