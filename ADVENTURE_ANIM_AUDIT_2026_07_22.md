# Adventure animation & placement audit — 2026-07-22 (v0.5.171 baseline)

Three-lane audit (journey beats / event beats / placement substrate) of every
adventure sequence, tick-traced with coordinate arithmetic.  Checklist file (ALL SHIPPED v0.5.172 on Joel's "fix all";
B-items kept as deliberate):
`[x]` = shipped, `[J]` = Joel's call, `[ ]` = queued, `[~]` = in progress.

Ground truth verified by hand before this board was written: the window law
HOLDS everywhere — every road frame clips to `grid.WINDOW` and off-window ink
drops gracefully; no wrap, no raise, no escape.  The defects below are pops,
overlaps, invisible actors, and contract drift INSIDE that safe window.

## A — Player-visible defects (fix candidates)

- [x] **A1 — The hazard pouncer is clipped or invisible at the moment of
  impact on most legs.**  `_hazard_frame` charges the raw 16-wide enemy to
  `px+pw` (the pet's right edge, adventurescreen.py:841) with the pet at its
  clamped MARCH x — not pinned to a wall.  At the sheet's own `_wx=14`:
  impact spans 30..45, clipped to 30..35 — 10 of 16 columns cut.  At
  `_wx≥20` (half of all positions): the whole charge renders at x=36 —
  the ambush plays as the pet reacting to NOTHING.
  **Fix shape:** pin the pet to X0 for the hazard beat (the `_gate_frame`
  faceoff idiom) so the pouncer always has the right half.

- [x] **A2 — The dig's carried reward icon smears over the pet on
  right-side finds.**  `_held_icon` pins `ox = min(x+w+gap, X1-iw)`
  (adventurescreen.py:761); with the pet returning to `x0=20` the pin drops
  the icon INTO the sprite (28..35 vs pet 20..35) — the exact "clamped ONTO
  the sprite" bug its own docstring claims can't happen.
  **Fix shape:** side-flip like the glint (icon on the LEFT when the right
  has no room), or carry the icon above the band-center clear of the pet.

- [x] **A3 — Life Recovery heals invisibly** (v0.5.164 gap — mine).
  `use_transport` returns `"life-recovery"` but `_use_transport`
  (adventurescreen.py:289-298) only handles town-warp/encounter: no beat, no
  pose, no message — just the strip's heart count ticking.  `adv.last` is
  set and never rendered (ribbon ignores it).
  **Fix shape:** a happy-pose beat + the "second wind" line on the strip
  (the town-warp rest-beat grammar).

- [x] **A4 — Every run opens with an ~8px pop and a facing flip.**
  Teleport-arrive reveals the pet centered at x=12 facing LEFT
  (adventurescreen.py:942-945); the first march frame renders at `_wx=4`
  facing RIGHT (init at :165, never synced on landing at :200-203).
  **Fix shape:** sync `_wx` to the reveal x on landing (and reveal
  mirror=True), so the march walks out of the materialization.

- [x] **A5 — Turn-back teleport snaps the marcher to center pre-curtain.**
  The leave frame always centers the pet (x=12) regardless of march x; the
  first 3 ticks have no curtain yet, so an ESC at `_wx=30` visibly snaps.
  **Fix shape:** leave-phase pet at the clamped march x instead of center.

- [x] **A6 — Beat interrupts snap the sprite up to 16px.**  March x is
  unclamped (−12..35); every beat frame clamps to [4,20]
  (`_jx`, :657-667).  A glint/refuse/hazard landing while `_wx>20` snaps
  left, then snaps BACK on resume (wx frozen during the beat).  The clamp
  itself is documented intent ("a beat never plays half-off an edge") —
  the polish is syncing `_wx` to the clamped x when a beat fires, so the
  resume walks on from where the beat played (one snap, not two).

- [x] **A7 — Roadside-nap zzZ merges into the pet on the right half.**
  zzz pins to the window top-right (:713-714); a pet asleep at the right
  bound occupies the same columns and first-ink-wins makes the zzZ
  unreadable.  **Fix shape:** side-flip the zzz to the free side (the
  glint rule).

- [x] **A8 — The hazard telegraph `!` can draw over the pet's head.**
  Pinned at `X1-ew-1` (:831) regardless of pet position, unlike the glint's
  side-flip (:743-747).  Same fix shape as A7.

- [x] **A9 — The pouncer is the one arena sprite that skips `grid.prep`.**
  Raw `frames_for` rows (:834-836): baseline off frame-height (floats above
  the y21 floor on bottom-padded rips) and the overlap guards measure its
  PADDED 16-box, not real ink.  **Fix shape:** `grid.prep` it like the gate
  boss (:900) — also fixes half of A1's width math.

- [x] **A10 — Parade marchers pop in/out mid-window.**  `x` interpolates
  `hi=20 → lo=4` (:880-881): each boss materializes at x=20 and vanishes
  at x=4 — never entering/exiting through an edge.  **Fix shape:** run the
  interpolation from `X1` to `X0-w` and let the window clip do the
  entrances (the march's own grammar).

- [x] **A11 — Sick shuffle overshoots the clamp by 1px.**  `_jx(rows)+dx`
  adds the shuffle AFTER clamping (:698): at the right bound the sprite
  pokes 1px past the window (clipped).  Clamp after the dx.

- [x] **A12 — Danger-warp with an empty wild pool is a silent no-op.**
  `use_transport` returns bare `"danger-warp"` (adventure.py:474-475) which
  `_use_transport` ignores — ticket spent, no dash beat, no message.  Rare.
  **Fix shape:** treat it as the dash-arrival beat with the strip line.

## B — Flagged, deliberate — Joel's call, default KEEP

- [J] **B1 — Two 16px mons on screen (gate faceoff, hazard pounce).**  The
  literal one-mon law bends here BY the faceoff grammar; the no-overlap
  guards hold (verified arithmetically).  Keep as theater unless ruled
  otherwise — but see D1 for the missing pixel pin.
- [J] **B2 — The dig meter blanks the mon (~4.8s max).**  Battle-bell
  grammar (`_render_ready` does the same); reads as intended.
- [J] **B3 — Hand-rolled placement instead of grid helpers** (gate faceoff
  hand-computes what `grid.faceoff` exists for; pet/boss/pouncer/parade all
  place by arithmetic on grid constants).  In-bounds today; each site is an
  independent drift risk.  A refactor pass is available on order.
- [J] **B4 — `timing_bar`'s hand-authored font/track pixels** on the dig
  path (strikefx.py:34-76) — canon-ported shared UI widget, not creature
  art; noted for the rips law, no action proposed.

## C — Comment/latent hygiene (cheap, bundled with any A-fix)

- [x] **C1 — Teleport frame omits `clip=grid.WINDOW`** (:947) — the only
  arena render without it; safe today only because the curtain self-clips.
- [x] **C2 — Stale choreography comments:** TELE_ARRIVE "drop 0..5" is
  actually a left zip-in; shrink holds a static sliver its last ~4 ticks;
  anim.py:24 "flash at 50" is `f==49`; `SPRITE_W_MARCH=16` re-entry offset
  ignores real prepped width (extra hidden ticks).
- [x] **C3 — Arrive t=23 renders one frame of bare road** (no curtain, no
  pet) between expand-end and the first flicker span.

## D — Coverage (why none of this ever surfaced)

- [x] **D1 — No pixel-level assertion exists for ANY adventure scene:**
  nothing checks non-overlap or in-window; the two overlap guards
  (:842, :847) are never pixel-tested.  **Fix shape:** a sweep test that
  renders every sheet state at `_wx ∈ {4, 14, 20, 32}` and asserts the
  mon's ink is inside the window and actor ink-sets are disjoint.
- [x] **D2 — The contact sheet fixes `_wx=14`** so every right-half defect
  (A1, A2, A7) is unstageable; it also never stages teleport-ARRIVE, the
  homecoming teleport, transports, the rest beat, or the wrap/re-entry.
  **Fix shape:** parameterize the sheet's `_wx` + add the missing states.
- [x] **D3 — Clipping hides placement bugs from every observer** (the sheet
  prints the post-clip buffer).  The D1 sweep test is the countermeasure —
  it must assert on PRE-clip placements, not the painted buffer.

## Addendum — THE DODGE (the audit's actual instigator, fixed v0.5.173)

- [x] **The successful dodge blinked the attacker out of existence.**  The
  "sails past, exits LEFT" tail hid the pouncer whenever its box touched
  the pet's columns — and with the pet at the wall (A1) that was the
  ENTIRE tail.  Two 16px sprites cannot cross a 32px window without one
  hiding, so the duck now makes the strike WHIFF: the pouncer pulls up
  short of the crouch and retreats out the RIGHT edge — the pet's free
  side, visible at every tick of the beat.  Pinned per-tick at four march
  positions in the placement sweep.

## Clean bills

Encounters (handoff, return, no stale frames), the boss gate faceoff (4px
guaranteed gap), boss-death beat, pulse, summary, the dig walk/suspense/
reveal geometry, the timing bar (fully in-window), pose fallbacks (every
species renders every role via the fr[0] backfill), and the rips law —
no hand-authored creature pixels anywhere in the adventure paths.
