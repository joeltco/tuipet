"""The sim soak harness (round 9, 2026-07-18) — run after any sim change.

    PYTHONPATH=src python tools/soak.py                    # all four policies
    PYTHONPATH=src python tools/soak.py perfect,neglect    # a subset

Drives full lifetimes (egg -> death, 3 generations per seed) under four care
policies — perfect / neglect / chaotic / insomniac — checking invariants every
tick, a save round-trip every game-day, and printing FINDING lines for
anything that breaks.  Reads no save file and writes none: every pet is
in-memory (Pet.new_egg / to_save_dict / pet_from_save only).

⚠ THE CLOCK LAW (the round-9 near-miss): the world clock is GAME-MINUTES —
1 tick = 1 world_second = 1 game-minute, DAY_LENGTH = 1440/day, hour =
world_seconds / 60 % 24, and nights last ~10 REAL minutes.  A harness that
computes hours as /3600 lights the pet's true nights at random and every
"perfectly cared" pet dies of neglect — that is the HARNESS's bug, not the
sim's.  The canon-cadence constants (LIGHTS_MISTAKE_SEC=60 et al.) are the
porting law pinned in test_clock_units: never "fix" them to 3600.
"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))
from tuipet.pet import Pet                             # noqa: E402
from tuipet import persistence                         # noqa: E402

STAGE_ORDER = {"Egg": 0, "Fresh": 1, "InTraining": 2, "Rookie": 3,
               "Champion": 4, "Ultimate": 5, "Mega": 6}
FLOAT_FIELDS = ("age_seconds", "stage_seconds", "world_seconds", "lifespan",
                "energy", "weight")

findings = []


def note(policy, seed, tick, msg):
    """Record a finding once per (policy, kind) so a hot loop can't flood."""
    key = (policy, msg.split(":")[0])
    if key not in {(p, m.split(":")[0]) for p, _s, _t, m in findings}:
        findings.append((policy, seed, tick, msg))
        print(f"FINDING [{policy} seed={seed} t={tick}]: {msg}")


def check_invariants(p, policy, seed, t, prev_age, prev_stage):
    for f in FLOAT_FIELDS:
        v = getattr(p, f, 0)
        if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
            note(policy, seed, t, f"NaN/inf: {f}={v}")
    for f in ("hunger", "strength", "poop", "bits", "trophies", "care_mistakes"):
        v = getattr(p, f, 0)
        if not isinstance(v, (int, float)) or v < 0:
            note(policy, seed, t, f"negative/bad {f}: {v!r}")
    if p.energy < 0 or p.energy > 200:
        note(policy, seed, t, f"energy out of range: {p.energy}")
    if p.weight < 0:
        note(policy, seed, t, f"weight negative: {p.weight}")
    if p.age_seconds < prev_age - 1e-6:
        note(policy, seed, t, f"age went backwards: {prev_age} -> {p.age_seconds}")
    so_prev, so_now = STAGE_ORDER.get(prev_stage, -1), STAGE_ORDER.get(p.stage, -1)
    if so_now < 0:
        note(policy, seed, t, f"unknown stage: {p.stage!r}")
    elif so_now < so_prev and not p.dead:
        note(policy, seed, t, f"stage regressed: {prev_stage} -> {p.stage}")
    if len(getattr(p, "poop_sizes", [])) != min(p.poop, 4) and p.poop <= 4:
        note(policy, seed, t,
             f"poop_sizes desync: poop={p.poop} sizes={p.poop_sizes}")


def roundtrip(p, policy, seed, t):
    """to_save_dict -> pet_from_save must reproduce a live pet, no heals."""
    d = persistence.to_save_dict(p)
    p2, msg = persistence.pet_from_save(d, catch_up=False)
    if p2 is None:
        note(policy, seed, t, f"save round-trip REJECTED a live pet: "
                              f"stage={p.stage} name={p.name!r} msg={msg!r}")
        return
    for f in ("num", "stage", "hunger", "bits", "generation", "dead"):
        if getattr(p2, f) != getattr(p, f):
            note(policy, seed, t,
                 f"round-trip drift: {f} {getattr(p, f)!r} -> {getattr(p2, f)!r}")
    if msg:
        note(policy, seed, t, f"round-trip healed a clean save: {msg!r}")


def act(p, policy, rng, t):
    """One policy decision per game-hour (60 ticks)."""
    if p.stage == "Egg" or p.dead:
        return
    if policy == "perfect":
        if p.sick and not p.asleep:
            p.feed_pill()
        if p.hunger <= 1 and not p.asleep:
            p.feed_meat()
        if p.poop and not p.asleep:
            p.clean()
        hour = (p.world_seconds / 60.0) % 24   # THE CLOCK LAW: /60, never /3600
        night = 21 <= hour or hour < 7
        if night and p.lights:
            p.toggle_lights()                  # lights OFF for the night
        elif not night and not p.lights:
            p.toggle_lights()
        if p.strength <= 1 and not p.asleep and not p.can_train():
            p.train_result(rng.random() < 0.8)     # the drill answers the effort call
    elif policy == "neglect":
        pass
    elif policy == "insomniac":
        if p.asleep and rng.random() < 0.05:
            p.feed_meat()                      # poke the sleeper forever
        if p.hunger <= 0 and rng.random() < 0.3:
            p.feed_meat()
    elif policy == "chaotic":
        r = rng.random()
        if r < 0.05:
            p.feed_meat()
        elif r < 0.08:
            p.feed_pill()
        elif r < 0.10:
            p.clean()
        elif r < 0.12:
            p.toggle_lights()
        elif r < 0.13 and not p.can_train():
            p.train_result(rng.random() < 0.5)


def run(policy, seed, max_gens=3, max_ticks=3_000_000):
    rng = random.Random(seed)
    random.seed(seed * 7 + 1)                  # the sim's own module-level rng
    p = Pet.new_egg(egg_type=rng.randrange(0, 46))
    gens, deaths = 0, []
    prev_age, prev_stage = p.age_seconds, p.stage
    t = 0
    day_mark = 0
    while t < max_ticks and gens < max_gens:
        t += 1
        try:
            if p.hatching:
                p.advance_hatch(1.0)
            p.tick(1.0)
            if t % 60 == 0:
                act(p, policy, rng, t)
        except Exception as e:
            note(policy, seed, t, f"EXCEPTION in tick/act: {type(e).__name__}: {e}")
            raise
        check_invariants(p, policy, seed, t, prev_age, prev_stage)
        prev_age, prev_stage = p.age_seconds, p.stage
        if p.world_seconds - day_mark >= 1440:         # one game-day
            day_mark = p.world_seconds
            roundtrip(p, policy, seed, t)
        if p.dead:
            deaths.append((p.stage, p.death_cause,
                           round(p.age_seconds / 86400, 2),      # REAL days
                           round(p.lifespan / 86400, 2)))
            roundtrip(p, policy, seed, t)
            gens += 1
            g = p.generation
            p = Pet.new_egg(egg_type=rng.randrange(0, 46))
            p.generation = g + 1
            prev_age, prev_stage = p.age_seconds, p.stage
    return t, gens, deaths


if __name__ == "__main__":
    policies = sys.argv[1].split(",") if len(sys.argv) > 1 else \
        ["perfect", "neglect", "chaotic", "insomniac"]
    for policy in policies:
        for seed in (1, 2, 3):
            t, gens, deaths = run(policy, seed)
            print(f"{policy} seed={seed}: {t:,} ticks, {gens} lives ended; "
                  f"deaths={deaths}")
    print(f"\n{len(findings)} distinct finding(s)")
