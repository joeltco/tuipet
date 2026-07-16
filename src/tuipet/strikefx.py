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


def cbounds(rows):
    """Leftmost / rightmost lit column of a sprite (its real content bounds).
    Matches ANY ink via grid.lit -- the old `== "1"` test saw ZERO lit cells
    in the clone's COLOUR frames (all hex strings), so every combatant fell
    back to full-frame bounds and orbs launched from the frame corner, not the
    sprite's mouth (round-3 audit 2026-07-16)."""
    w = max(len(r) for r in rows)
    cols = [x for x in range(w)
            if any(x < len(r) and grid.lit(r[x]) for r in rows)]
    return (min(cols), max(cols)) if cols else (0, w - 1)


def clamp_grid(x, lo, hi):
    """Clamp x so the sprite's lit content [x+lo, x+hi] stays inside the grid [X0, X1).
    Steady poses hug the grid wall; a rear-back that would push past it compresses against
    the wall instead of escaping (the lunge-forward beat still reads)."""
    return max(grid.X0 - lo, min(x, (grid.X1 - 1) - hi))


def place_combatant(faces_left, rows, xshift=0, mirror=True):
    """Place the ONE combatant on screen, grounded in the grid, clamped in-bounds.
    faces_left=True  -> attacker/pet: stands RIGHT, faces left, fires left (content right edge
                        hugs the grid); mouth = its LEFT edge (toward the target).
    faces_left=False -> target/foe: stands LEFT facing right -- mirrored for creatures (they
                        face left natively); mirror=False keeps a PROP's sheet facing (canon
                        setAltIcon never flips the punching bag / cannon).  mouth = its RIGHT edge.
    Returns (placements, mouth_x)."""
    if faces_left:
        lo, hi = cbounds(rows)
        x = clamp_grid(((grid.X1 - 1) - hi) + xshift, lo, hi)
        return [(rows, x, False)], x + lo
    src = [r[::-1] for r in rows] if mirror else rows
    lo, hi = cbounds(src)
    x = clamp_grid((grid.X0 - lo) + xshift, lo, hi)
    return [(rows, x, mirror)], x + hi + 1


def orb_flight(orb, fires_left, m, prog, mouth, double=False, color=None):
    """The attacker's real orb, flying between the mouth and the grid edge.
    m 'fire_out' -> leaves the mouth, off the near grid edge.
    m 'fire_in'  -> arrives from the far grid edge, stops at the defender's edge (mouth).
    On a dodge the orb is NOT drawn (canon dodge() hides the attack sprite --
    the defender's unhurt hop + the absent explosion ARE the miss; a 16px
    defender in the 16px band can never visibly clear a passing orb).
    fires_left mirrors battle's `atk == 'pet'` (player fires left, enemy fires right).
    `color` tints the shape with the firing mon's own hue (the source LCD
    recolours per digimon; ink-stamped shapes read as dark blobs on the
    clone's colour scenes -- audit 2026-07-15)."""
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
        return blit(src, x, BAND_TOP, color) + blit(src, x, BAND_BOT - h, color)
    return blit(src, x, BAND_TOP + (16 - h) // 2, color)


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
