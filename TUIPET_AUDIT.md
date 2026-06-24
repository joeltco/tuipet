# tuipet — Audit & Tightening Plan

Status: tuipet is now a complete, standalone game (DVPet-derived but its own
thing). **All DVPet data files are ported and used.** This phase is a
systematic quality pass — correctness, robustness, consistency, and
regression safety — not new features.

## How we work (resume context)

- Code lives on **um700** at `~/projects/tuipet`; public repo
  `github.com/joeltco/tuipet` (push via SSH on um700; `gh` is authed only on
  the local/Termux side, not um700). Branch `main`.
- Edits are made by **Python patch scripts piped/scp'd over ssh** that assert
  the old string matches exactly once, then `py_compile`. Keeps edits precise
  on the remote box.
- **No test runner / no `tests/` dir yet** — verification has been ad-hoc
  `/tmp/*.py` scripts run with `PYTHONPATH=src python3`. Establishing a real
  `tests/` suite is itself an audit deliverable (see Workstream F).
- Headless UI checks: Textual `app.run_test()` pilots; render a panel via
  `rich.Console(record=True)` then read `.export_text()`. Color needs a PNG
  (text export renders on/off cells identically as `▀`).
- **Persistence tests must isolate** `persistence.SETTINGS_PATH` /
  `SAVE_PATH` (now resolved at call-time, so reassignment works) — a leaked
  real save/settings has broken Joel's game before. Never leave a test save
  at `~/.local/share/tuipet/`.
- Assets (sprites/CSVs) are **gitignored** (Bandai IP); regenerate via
  `tools/setup_assets.sh <DVPet.jar>`. New CSVs must be copied to
  `src/tuipet/data/` AND added to that script's `for f in` list.

## Architecture invariants (don't break these)

- Two clocks: `on_frame` @ 10 Hz (0.1s) drives animation/fx + sub-screen
  panels; `on_tick` @ 1 Hz drives the life-sim and returns early when a
  `mode` (sub-screen) is open. `autosave` @ 10 s. During a care fx
  (`screen_w.fx`), `on_frame` owns painting — `on_tick` must not repaint
  (would flash the status box).
- Single-screen UI: **no pop-up modals**. Every screen is an in-display
  `XPanel` with `text()`/`key()`/`anim()`; `app.mode` swaps the #lcd content.
- Status box (`Stats`) caps at **16 inner lines** / 26 inner cols — adding a
  line clips the bottom. Surface transient state via the `deco` list, not new
  lines. `menu.footer` caps ~38 cols.
- `pet.tick(1.0)` == one real second. `DAY_LENGTH` is a cosmetic 24-min
  day/night cycle, NOT tied to aging (`lifespan` ~3-5 days).
- Combat (verified Workstream A): per-round damage is
  `base_attack(stage) + calc_attack_power(attr)`, floored at 0, where
  calc_attack_power is **-1/0/+1** from comparing this side's attribute COUNT
  vs the opponent's (battle.py). Field/element affinity adds 0 (CSVs all zero) —
  do not re-pitch. NB: the "+32 attribute triangle" is a real-*hardware* concept,
  NOT tuipet's modifier; tuipet uses the count comparison above.
- ZERO hand-drawn sprites (Joel's hard rule). Only weather FX may be
  procedural. Everything else is extracted from real DVPet sheets.

## Workstreams

### A. Correctness vs DVPet data
- [x] Evolution gates: **VERIFIED no soft-lock.** All 93 Fresh starters have a
      pure-timed-care path to a Mega; no climbable below-Mega form can be *forced*
      toward a dead-end. The 8 below-Mega care-terminals (Liamon, Darcmon,
      Targetmon, BaoHackmon, RaptorSparrowmon, Baboongamon, Petaldramon, Sagomon)
      are jogress/spirit/X-only by design and always opt-in (a Mega-bound sibling
      exists at every parent). Pinned by tests/test_evolution.py (graph invariant,
      no magic allowlist). No code change needed.
- [ ] Egg unlock: all 49 eggs reach a non-locked state through real play;
      buyable/temp/owned transitions; the Carimon password path.
- [x] Battle resolution: **VERIFIED.** Per-round damage = base(stage) + (-1/0/+1 count delta), floored at 0; per-stage HP (R10/C15/U20/M25, enemy min 2); win iff own HP>0 (double-KO = loss); first-strike KO blocks retaliation; AI win-ramp thresholds. Pinned by tests/test_battle.py (11 tests). Found+fixed a doc error: combat is the count comparison, not a '+32 triangle' (that's real hardware).
- [ ] Care effects (Futon), care-mistake / death triggers, training gain.
- [ ] Tournament eligibility, season reset, trophy persistence.

### B. Edge cases & robustness
- [ ] Save/load migration: old saves missing new fields (effect_id,
      progress keys) load with defaults — add a guard test.
- [ ] Bounds: empty album/roster, gen 1 with no prev-gen snapshot, 0 bits,
      dead pet interactions, None returns from panels (cancel paths).
- [ ] Offline catch-up math at extremes (36h cap, mid-evolution, mid-effect).
- [ ] Multiplayer/lobby: disconnect, name-taken, partner leaves mid-jogress.

### C. UI / UX consistency
- [ ] Theme propagation across ALL screens (the `_SCREEN_MODULES` set).
- [ ] No status-box clipping anywhere (16-line cap); footer width fits.
- [ ] Status box content correct next to every action (the per-action HUD).
- [ ] Animation gating: every fx completes before re-trigger (feed/clean/etc).

### D. Performance
- [ ] 10 Hz loop does no avoidable work (caches hot, no per-frame CSV reads).
- [ ] `lru_cache` coverage on all data loaders; no repeated parses.

### E. Code health
- [ ] Dead code / unused params / stale comments.
- [ ] Duplication (STAGE_ORDER defined in 4 files — consolidate?).
- [ ] Consistent naming/idiom with surrounding code.

### F. Regression safety (deliverable)
- [x] Stand up a `tests/` dir + pytest runner. **DONE** (26 tests): an autouse
      `isolate_save` fixture sandboxes all persistence I/O into tmp (so a test can
      never touch the real save). Covers: CSV loaders (care/digicore/eggUnlock),
      egg-unlock reachability + password path, save/load round-trip + old-save
      migration, bounded offline catch-up (36h cap), and the Futon care-effect
      lifecycle. Run with `python3 -m pytest -q`.
- [ ] Still to add: evolution no-soft-lock, battle/DP math, jogress outcome,
      tournament eligibility. (Wire these in as those systems are audited.)

## Method

Audit **system by system** (as in prior passes): read the real code +
DVPet source/CSV, find real bugs, fix + verify each individually, commit
per fix. Verify before asserting — most prior "findings" were false
positives. Ground every behavioral claim in decompiled source or the CSVs,
never memory of the hardware.
