"""The ONE attack-volley animation, shared by the battle screen and every training drill
(single source of truth -- so the pet's fire / orb-flight / impact look identical everywhere).

A volley is the battle player's attack, cloned as an alternating-view sequence (only one
combatant on screen at a time): the attacker rears back and fires its orb off the near grid
edge -> the view switches to the TARGET as the orb arrives -> a fullscreen impact flash ->
the target breaks (hit) or the attacker deflates (miss).  battlescreen owns the beat timings
(WINDUP_T / FIRE_T / ...); this module owns the geometry + orb flight so both stay in lockstep.
"""
from __future__ import annotations
from . import grid

# the orb rides the same 16px creature band every sprite stands in
BAND_TOP = grid.TOP          # 6
BAND_BOT = grid.FLOOR        # 22


from .render import blit    # one blit for app/training/strikefx (refactor 2026-07-05)


def beat_sfx(m, strong):
    """The launch/impact stings every strike timeline shares -- battle and
    training hand-rolled the same two arms (refactor 2026-07-05).  None for
    markers the caller shades itself (reveal, miss, bossdie)."""
    if m == "fire_out":
        return "strongAttack" if strong else "attack"
    if m == "hit":
        return "strongHit" if strong else "attackHit"
    return None


# the source's 3x5 training font (only the glyphs HIT! needs; '!' is absent
# and blanks, exactly like the original)
_FONT_3X5 = {
    "H": [1, 0, 1, 1, 0, 1, 1, 1, 1, 1, 0, 1, 1, 0, 1],
    "I": [1, 1, 1, 0, 1, 0, 0, 1, 0, 0, 1, 0, 1, 1, 1],
    "T": [1, 1, 1, 0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0],
    " ": [0] * 15,
}


LOCK_GRACE = 2   # trailing marker steps forgiven on a bar lock (10Hz: ~200ms)


def grade_lock(hist, mega_lo, mega_hi, veteran=False):
    """ONE grading rule for every bar lock (the drill and the bout ran
    hand-copies).  Reflex honesty (timing rework 2026-07-23, Joel: "i hit
    the center every time, what are you talking about"): the marker steps
    every 100ms and a seen-centered press lands ~200-300ms later (human
    reaction + terminal latency), so the lock grades the BEST of now and
    the last LOCK_GRACE steps -- the same honesty the hazard dodge got.
    The 2px-wide marker counts BOTH its pixels (grading bar's left pixel
    alone failed a visually-inside lock on the low approach).  The
    normal shoulder (window ±5) stays strict on the pressed position.
    veteran: battles >= 999 never whiffs -- VERBATIM v0.4.12 (DSprite
    truth, drill audit 2026-07-19; not a cheat shim, do not "fix" it).
    hist: recent marker positions, the LIVE one last."""
    if veteran:
        return "mega"
    recent = hist[-(LOCK_GRACE + 1):]
    if any(mega_lo - 1 <= b <= mega_hi for b in recent):
        return "mega"
    if mega_lo - 5 <= hist[-1] <= mega_hi + 5:
        return "normal"
    return "miss"


def timing_bar(bar, mega_lo, mega_hi):
    """The canon timing bar, pixel for pixel from the source's
    TRAINING_MINIGAME render (Joel 2026-07-15: 'do it canon style'):
    HIT! in the 3x5 font at (9,0), the 28x5 outlined track at (2,7),
    single-pixel ticks above and below the mega window's edges, and the
    moving 2x3 marker at (3+bar, 8).  Single-sourced here so the drill
    AND the battle/raid ready screen sweep the SAME sprite (Joel
    2026-07-19: 'the slide bar should be the same sprite as the
    training slide bar')."""
    pts = []

    def L(x, y):                              # the source's pixel-set
        pts.append((grid.X0 + x, grid.TOP + y))

    def B(x, y, w, h):                        # the source's rect outline
        for i in range(w):
            L(x + i, y), L(x + i, y + h - 1)
        for i in range(h):
            L(x, y + i), L(x + w - 1, y + i)

    def R(s, x, y):                           # the source's 3x5 font run
        for ci, ch in enumerate(s):
            g = _FONT_3X5.get(ch, _FONT_3X5[" "])
            for gy in range(5):
                for gx in range(3):
                    if g[gy * 3 + gx]:
                        L(x + ci * 4 + gx, y + gy)

    R("HIT!", 9, 0)
    B(2, 7, 28, 5)
    lo, hi = 3 + mega_lo, 3 + mega_hi + 1
    for tx in (lo, hi):                       # the mega window's ticks
        L(tx, 6), L(tx, 12)
    B(3 + bar, 8, 2, 3)                       # the marker (outline == solid at 2 wide)
    return pts


def cbounds(rows):
    """Leftmost / rightmost lit column of a sprite (its real content bounds)."""
    w = max(len(r) for r in rows)
    cols = [x for x in range(w) if any(x < len(r) and r[x] == "1" for r in rows)]
    return (min(cols), max(cols)) if cols else (0, w - 1)


def clamp_grid(x, lo, hi):
    """Clamp x so the sprite's lit content [x+lo, x+hi] stays inside the grid [X0, X1).
    Steady poses hug the grid wall; a rear-back that would push past it compresses against
    the wall instead of escaping (the lunge-forward beat still reads)."""
    return max(grid.X0 - lo, min(x, (grid.X1 - 1) - hi))


def place_combatant(faces_left, rows, xshift=0, mirror=True, turn=False):
    """Place the ONE combatant on screen, grounded in the grid, clamped in-bounds.
    faces_left=True  -> attacker/pet: stands RIGHT, faces left, fires left (content right edge
                        hugs the grid); mouth = its LEFT edge (toward the target).
    faces_left=False -> target/foe: stands LEFT facing right -- mirrored for creatures (they
                        face left natively); mirror=False keeps a PROP's sheet facing (canon
                        setAltIcon never flips the punching bag / cannon).  mouth = its RIGHT edge.
    turn=True flips the combatant to the OPPOSITE of its battle facing -- the
    tuipet turn-away dodge (Joel 2026-07-21): airborne, the dodger shows the
    foe its back.  Bounds anchor on the AS-SHOWN orientation so the ink still
    hugs its own wall mid-turn.
    Returns (placements, mouth_x)."""
    if faces_left:
        m = bool(turn)
        src = [r[::-1] for r in rows] if m else rows
        lo, hi = cbounds(src)
        x = clamp_grid(((grid.X1 - 1) - hi) + xshift, lo, hi)
        return [(rows, x, m)], x + lo
    m = bool(mirror) and not turn
    src = [r[::-1] for r in rows] if m else rows
    lo, hi = cbounds(src)
    x = clamp_grid((grid.X0 - lo) + xshift, lo, hi)
    return [(rows, x, m)], x + hi + 1


def orb_flight(orb, fires_left, m, prog, mouth, double=False):
    """The attacker's real orb, flying between the mouth and the grid edge.
    m 'fire_out' -> leaves the mouth, off the near grid edge.
    m 'fire_in'  -> arrives from the far grid edge, stops at the defender's edge (mouth).
    On a dodge the orb is NOT drawn (canon dodge() hides the attack sprite --
    the defender's unhurt hop + the absent explosion ARE the miss; a 16px
    defender in the 16px band can never visibly clear a passing orb).
    fires_left mirrors battle's `atk == 'pet'` (player fires left, enemy fires right)."""
    if not orb:
        return []
    w, h = len(orb[0]), len(orb)
    if m == "fire_out":
        x0, x1 = (mouth - w, grid.X0 - w) if fires_left else (mouth, grid.X1)
    else:
        x0, x1 = (grid.X1, mouth) if fires_left else (grid.X0 - w, mouth - w)
    src = orb if fires_left else [r[::-1] for r in orb]
    x = int(x0 + (x1 - x0) * prog)
    if double:                                            # doubleAttack: BOTH orbs, top & bottom of band
        return blit(src, x, BAND_TOP) + blit(src, x, BAND_BOT - h)
    return blit(src, x, BAND_TOP + (16 - h) // 2)


def build_volley(success, strong):
    """A single-attacker volley timeline (the battle player's attack, standalone):
    windup -> fire_out -> fire_in -> hit + break (success) / miss (fail).  Beats come from
    battlescreen so the pace matches the real battle exactly."""
    from .battlescreen import WINDUP_T, FIRE_T, EXPLODE_FRAMES, EXPLODE_HOLD, FLINCH_T
    tl = [{"m": "windup", "wu": s} for s in range(WINDUP_T)]
    tl += [{"m": "fire_out", "prog": (s + 1) / FIRE_T, "double": strong} for s in range(FIRE_T)]
    tl += [{"m": "fire_in", "prog": (s + 1) / FIRE_T, "double": strong} for s in range(FIRE_T)]
    if success:                                           # HIT: strobing explosion, then the broken target
        tl += [{"m": "hit", "f": (s // EXPLODE_HOLD) % 2} for s in range(EXPLODE_FRAMES)]
        tl += [{"m": "break"}] * FLINCH_T
    else:                                                 # FAIL: orb fizzles, target intact, pet deflates
        tl += [{"m": "miss"}] * FLINCH_T
    return tl
