# DVPet animation spec — canonical timelines + tuipet reconciliation

Reverse-engineered from the decompiled game source `_audit_src/View/SpriteAnim.java`
(full method bodies, CFR 0.152). This is the authoritative reference for sprite
pose order, motion offsets, and timing — replacing eyeballed approximations.

## The master clock identity

`SpriteAnim` sets `_interval = targetFPS / 10`. Every animation event is written
`if (_frame == _interval * N)`, so **N is tenths of a second** (t = N/10 s). The
game is authored in 0.1 s units regardless of frame rate.

**tuipet's `on_frame` runs at 10 Hz → 1 tuipet frame == 1 DVPet `_interval`.**
Timelines port 1:1 with no conversion. (`_stateFrame` is a *separate* counter used
only by the status-badge blinker `stateNumTic`.)

## Pose model

A pose is `getSpriteNum() + OFFSET`, drawn via `drawNumMirror(pose, mirror)`.
Offsets 0–10 map directly onto tuipet's 11-frame per-creature strip:

| off | meaning | off | meaning |
|----|---------|----|---------|
| 0 | idle / neutral base | 6 | attack / strike / cheer-up(small) |
| 1 | idle-B / walk-B / turn | 7 | chew / swallow / **cheer-down(big)** |
| 2 | sleep-A | 8 | mouth-open / eat-swallow |
| 3 | sleep-B / stretch | 9 | hurt / disliked / fail / jeer-up |
| 4 | side / clean / **cheer-down(small)** | 10 | collapse / hurt / jeer-down |
| 5 | excited / **cheer-up(big)** | | |

Legend for verdicts: ✅ faithful · ⚠️ partial/divergent · ❌ missing · 🚩 bug

---

## 1. Idle / walk / run  — tuipet `anim.py`

`idle()` routes by `world.travelSpeed`: 0 = stand-fidget, 1 = walk, 2 = run.

**idleNormal (stand-fidget)** — fires one `stepFrame`, then re-arms
`_frame = -(restless>0?5 : restless<0?7 : 6)*_interval` → a fidget every
0.5 / 0.6 / 0.7 s. `stepFrame` mostly toggles poses 0↔1, takes occasional literal
3 px steps, flips facing, and — gated by mood/energy via `checkMoodFrame` —
substitutes an **expression pose** (happy=5, tired=9/10/2, unhappy=4/6, neutral=8).

**idleWalk (speed 1)**

| t(s) | pose | move |
|----|------|------|
| 0.0 | 0 | ±3 px |
| 0.5 | 1 (or 10 if tired) | ±3 px; re-arm −0.5 s → 1.0 s cycle |

Wraps around screen edges (off one side, on the other).

**idleRun (speed 2)** — draws + moves 6 px **every 0.1 s**, alternating 0 / 1(10),
on a 0.7 s loop (42 px/cycle), same edge-wrap.

verdicts: ✅ fidget cadence 5/6/7 (`idle_hold`) · ✅ walk 3 px / 5-tick (`STEP_PX`,`WALK_BEAT`) ·
⚠️ walk **wraps** in DVPet but tuipet `Roamer` **bounces** + adds a non-canon `TURN_CHANCE`
(and its docstring wrongly claims it wraps) · ❌ **run mode** absent ·
❌ **idle mood-expression poses** absent — tuipet idle is flat 0↔1, so a happy/tired/sad
pet looks identical at rest · ❌ tired-walk variant (pose 10) absent · ✅ idle is silent.

---

## 2. Sleep / sick / poop  — tuipet `anim.py`

**idleSleep** — stationary 2.0 s loop: pose 2 @0.0, pose 3 @1.0, back @2.0.
Z-indicator icon toggles on the same beat; routed to the emotion bubble (lights on,
body hidden) or room overlay (lights off). A napping pet may re-roll to the deeper
"sleep" indicator at the 1.0 s mark.

**idleUnwell (stand, sick)** — clock-jumps to t=2.5, holds pose **+10**, net-zero
shuffle (L1,R1,R1,L1) at 3.0/3.5/4.0/4.5, one **+9** frame at the 5.0 s wrap.
Sick **walk/run** exist too: poses 9↔10, 3 px per toggle, 2.8 s (walk) / 1.4 s (run), wrap.

**poop (in room)** — squat **+4** (mirror true; nudged +30 px right if filth count even),
sway L,R,L,R,L,R @0.3–1.5, drop to relieve **+5** @1.8 with size-keyed sound, end @2.4.
`playPoopSound`: `_smallPoop` (1) / `_largePoop` (>2) / `_poop` (else).
A separate **poop-outside** 3-state machine (walk off → relieve → walk home) runs in
town/tournament. **poopDance**: sway on 0 (0.2–1.0) then 4 horizontal flips on pose 4.

verdicts: ✅ sleep 2↔3 / period-20 exact (`sleep_pose`,`SLEEP_BEAT`) · ✅ poop poses 4→5 ·
⚠️ sick shuffle path differs (tuipet `sick_frame` dx drifts right vs canon net-zero; period 50 & weary@49 right) ·
❌ sick walk/run absent · ❌ poop size-keyed sounds collapsed to one · ❌ poop-outside sequence absent.

---

## 3. Eat / care / refuse  — tuipet `ROLES` + screens

**eat()** — `mod` scales timing (0.9 hungry/glutton+, 1.1 glutton−, else 1.0);
`chew = +9` if disliked/overeat/spriteNum==20 else `+7`.

| t(s) | pose | sound | note |
|----|------|-------|------|
| 0.0 | 0 | | food appears, char repositions |
| 0.2/0.4/0.6 | — | | food drops (y 65/76/87) |
| 1.0 | 8 | | mouth open |
| 1.4 | chew(7/9) | `_eat` | bite 1 (foodLabel→1) |
| 1.8 | 8 | | mouth open (weight≥40 skips to 2.6) |
| 2.2 | chew(7/9) | `_eat` | bite 2 |
| 2.6 | 8 | | mouth open |
| 3.0 | chew(7/9) | `_lastBite` | bite 3 |
| 3.4 | — | | cleanup, endAnim |

**refuse()** — pose 4 (9 if Depressed), mirror T/F/T/F @0.6 s, `_refuse` each flip, end 2.4.
**wakeUp** — 2↔3 drowsy → 1↔2 flutter → settle target (slow, rate 5).
**clean()** — wash sprite sweeps R→L pushing the pet (pose→4); cheers if it was filthy (`_wash`).
**recover() (item)** — descends, alternates 8/7 with `_adventureLifeRecover` (heavy skips one).
**bandage / shower / bathing** — prop label + effort poses → transition into the cheer tail.

verdicts: ✅ refuse exact · ✅ wake 2,3→1 · ✅ wash 0→4 · ✅ recover 8/7 (`ROLES["heal"]`) ·
⚠️ eat keeps poses [8,7] but flattens the **3-bite structure, real timing, `_lastBite`, and disliked-`+9`** ·
⚠️ clean simplified (sweep/push/cheer-tail) · care SFX granularity collapsed.

---

## 4. Cheer / scold  — tuipet `ROLES["happy"]`,`["angry"]`

All four are a 0.6 s two-pose bounce, 3.0 s total (ticks 0/6/12/18/24/30→idle).

| call | up | down | start | sound | bubble |
|------|----|----|-------|-------|--------|
| **cheer(true)** praise / **win** / **evolve-finish** | **5** | **7** | up, t0 | param | happy |
| cheer(false) | 6 | 4 | up, t0 | param | happy |
| jeer(true) scold | 6 | 4 | down, t0.6 | param | unhappy/unhappy2 |
| jeer(false) bad-health | 9 | 10 | down, t0.6 | `_badHealthJeer` | dying/dying2 |
| (Egg, any) | 0 | 1 | | | |

🚩 **BUG:** `ROLES["happy"]=[6,4]` is the `cheer(false)` / scold pair, **not** the
canonical praise poses. The comment even mis-cites "cheer(false) poseA=6 poseB=4".
Canon happy = **[5,7]** — and `battlescreen.py` already uses 5,7 for the win pose
(`CHEER_A,CHEER_B`), so the ROLE contradicts the battle screen. **Fix: `happy = [5,7]`.**
⚠️ `ROLES["angry"]=[9,10]` is bad-health jeer (ok as "dying"); normal scold is [6,4]
— consider splitting `scold=[6,4]` vs `dying=[9,10]`.

---

## 5. Evolve / hatch / jogress

**evolveAnim** — pet on pose 0; `_evolve` @0.5; room strobes `evol`/`lightsOff` at
0.5/1.0/1.2/1.4/1.9/2.1/2.5/2.7/2.9/3.2/3.4; **new form swapped in @2.1 under the flash**
(masked reveal); `digivolve` → `evolFinish(true)` @4.1.
**hatch** — egg wobbles ±3 px ~1 s, `_hatch` @0.6, crack poses 1→2, hatch @2.9.
**jogress** — two pets slide to center, light/dark fade swap, clash, then `evolveAnim`
flash; model mutates @10.8, `evolFinish` @13.0.
**Every** non-egg evolution path ends by jumping into `cheer(true, _happy)` — the
good-praise bounce is the canonical reveal/finish.

verdicts: ⚠️ verify tuipet evolve/jogress screens reproduce the strobe + swap-under-flash@2.1
+ `_evolve` sound + the `cheer(true)` celebratory tail (jogressscreen has a fuse flash; check the rest).

---

## 6. Training / battle  — tuipet `training.py`,`battlescreen.py`

DVPet has **two** training systems:

- **HP-training** (guess the hidden attribute): loops `_trainTimer`; correct → pose **6** + `_attack`;
  wrong/timeout → pose **9** + `_attack`; both resolve through a 3-cycle impact flash.
- **Attribute-training** (Vaccine mash / Data hi-lo shooter / Virus stop-bar): pre-game →
  strike (`attackDefault` pose **6**, projectile −6 px/0.1 s, `_attack`; **success** upgrades to
  `_strongAttack` + doubled 48 px projectile → `_strongHit`) / `attackGreen` (Data, projectile
  +6 px, `_turretShoot`) → `hitAnim` (3-cycle flash) → aftermath (**success = idle 0 + broken bag;
  fail = +10 hurt**), hold 1.6 s → finish.

**Battle attack** — `battlePlayerShootAnim`: wind-up poses 1→0→4, lunge bobble, pull-back,
**strike pose 6** fires the projectile (6 px/5 frames, `_attack`/`_strongAttack` by 24/48 px).
Defender flinch-bobs 4↔0; hit = 3-cycle flash; dodge = 1.2 s hop; aftermath hurt = **+10**,
`_battleHPDecrease` @0.6, `checkBattleEnd` @1.0.

verdicts: ✅ tuipet uses 6=hit/success, 9=miss/fail · ✅ **battlescreen faithful**: wind-up
(1,1,0,0,4,4), `fire_out`=6, defender bob 4↔0, hurt=10, win=5,7 — with deliberately-retuned
readable timing · ✅ tuipet vaccine=mash & virus=stop-bar match DVPet pre-games · ✅ data poses
[1,4] match (cadence 0.5 s vs 0.2 s) · ⚠️ tuipet HP = hit-the-zone slider (canon = guess hidden
attribute); data = slot-match (canon = hi/lo shooter) · ❌ no `_trainTimer` tension loop ·
❌ no strong-vs-normal hit (success doubled projectile + `_strongHit`) · ❌ training has no
strike→projectile→impact→aftermath mini-battle visual (it's an abstract UI minigame).

---

## Fix status (applied 2026-06-27)

APPLIED:
1. ✅ `ROLES["happy"] = [5, 7]` (was `[6,4]`) — celebrations now match canon **and** the
   battle screen's win pose. Stale comments corrected (`data.py`).
2. ✅ Eat per-bite SFX: `eat`/`eat`/`lastBite` fire on the three chew beats in the fx loop
   (`app.py`). The 3-bite cadence, mod-scaling, and disliked-food `+9` chew were already
   present in the eat fx — only the sounds were missing. Unified direct-feed + bag-feed
   (bag-feed previously had no eat sound at all).
3. ✅ Idle mood-expression poses: `anim.mood_pose()` surfaces a weary/sour/bright pose on
   ~30% of idle steps (`IDLE_EXPR_CHANCE`) instead of the flat 0↔1 walk toggle, so a resting
   pet reads its state (`anim.py` + `app.py` step roll + render).
4. ✅ Poop size-keyed sounds (`smallPoop`/`poop`/`largePoop` by new pile count) + net-zero
   sick shuffle (`sick_frame` now holds −1/0/+1/0 across the ranges, summing to zero).
5. ✅ Training strong-hit SFX: a full-success drill (`hits>=3`) plays `strongHit` (`training.py`).
6. ✅ Play action: was rendering the **cheer** fx (poses 5↔7). DVPet has a dedicated play
   animation — `jumping()` (L17308) / `playing()` (L16914), poses **1↔5** = `ROLES["play"]`.
   Added a real "play" hop fx: the pet leaves the ground (pose 5 up / 1 land) on a triangle
   `yshift`, `happy` chirp at each hop's launch (`app.py` + a zero-default `yshift` on
   `render_screen`). `ROLES["play"]=[1,5]` was correct but had been **dead code**.

   Canon `playing()` (toy bounce): char 1↔5 every 0.6s ×3, `_playingInteract` on each up-beat,
   3.6s. Canon `jumping()` (hop): pose 5 up / 1 down, 6px/tick, `_happy` per hop. tuipet uses
   the hop (visually distinct from cheer) with `happy.wav` (the only matching ripped asset).
7. ✅ Battle strong-hit audio: the `dbl` (DVPet doubleAttack) flag was computed and tagged on
   `fire_out`/`fire_in` but the sfx played flat `attack`/`attackHit`.  Propagated `double` to the
   `hit` entry and branched `_emit_sfx`: a strong hit now launches with `strongAttack` and lands
   with `strongHit` (`battlescreen.py`) — the same parity training got in fix #5, using the
   already-ripped `strongAttack.wav`/`strongHit.wav`.

All asset files (`lastBite.wav`, `smallPoop/largePoop.wav`, `strongHit.wav`, …) already
shipped in `data/sounds/` — they were ripped but unwired. Tests: `tests/test_anim_canon.py`.

8. ✅ **Training mini-battle** (the big one — `attackDefault`→`hitAnim`→`aftermathDefault`).
   Training was an abstract UI minigame: pet bobs in place, flashes a hit/miss pose, no opponent.
   Now, after the skill drill, a **strike phase** plays: the pet (right, facing left) winds to
   pose 6 and **fires a projectile** at the **punching bag** (vaccine/virus/hp) or **green target**
   (data) on the left; the impact **flashes**; then the **aftermath** — bag shows **broken**
   (`punchingBagBroken`) on success, pet **recoils to pose 10** on a fail. Launch/impact use the
   strong-vs-normal `attack`/`strongAttack` + `attackHit`/`strongHit` sounds (fix #5/#7).
   Extracted `punching_bag`/`punching_bag_broken`/`train_green`/`train_green_up` into
   `effects.json.gz` (the projectile + flash art was already there); reused `render_scene` +
   battle's composition approach. `training.py` strike phase + `tests/test_training_strike.py`.

DEFERRED (genuine features, not fidelity fixes — would change deliberate tuipet design):
- **Run mode (travelSpeed 2) + sick walk/run** — tuipet has no world-travel-speed model; the
  pet roams (walk) during idle and there is no "running" trigger to hang these on.
- **The looping `_trainTimer` tension sound** — the one-shot `subprocess` audio backend has no
  looping primitive, so the during-drill timer hum can't be reproduced without a loop player.
