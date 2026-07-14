"""Evolution reachability — the anti-soft-lock guarantee (Workstream A).

select() climbs via 'normal stage-up' edges (special=None, evol_item=-1, non-X)
plus 'Failed' forms when nothing else qualifies; the comment there promises a pet
"NEVER gets stuck below Mega". We verify the data backs that up:

  1. Every Fresh starter has a pure-timed-care path to a Mega.
  2. No climbable form below Mega can lose its path to Mega — i.e. you can never
     be *forced* toward a dead-end. (Jogress/fusion/X-only terminals exist by
     design — e.g. Liamon, Petaldramon — but they're always opt-in: reaching one
     means you chose stats for it over a Mega-bound sibling.)

Graph-only; no randomness, so these are stable. Skips if sprite assets are absent.
"""
import pytest

from tuipet import data

STAGE = {s: i for i, s in enumerate(data.STAGE_ORDER)}
MEGA = STAGE["Mega"]


def _graph():
    _, by_num = data.load_sprites()
    if not by_num:
        pytest.skip("sprite assets not installed (run tools/setup_assets.sh)")
    evo = data.load_evolutions()
    req = data.load_requirements()

    def real(n):
        return n in by_num and not data.is_placeholder(n)

    def sidx(n):
        return STAGE.get(by_num[n]["stage"], -1)

    def care_edges(n):
        """Targets select() can reach with only timed care + battles."""
        out = []
        for t in evo.get(n, []):
            if not real(t) or sidx(t) <= sidx(n):
                continue
            r = req.get(t, {})
            # the ENGINE gates "Induced" only (evolution.py: "canon gates
            # Induced only" -- Natural just means the species carries the
            # X-antibody in lore, e.g. the whole DORUmon line, and is reached
            # by ordinary care).  This helper also excluded Natural, so it
            # modelled paths the game does not actually block; it only passed
            # because the device roots were polluted with non-X children
            # (root audit 2026-07-14).
            if r.get("special", "None") in ("None", "Failed") \
                    and r.get("evol_item", -1) == -1 \
                    and r.get("xantibody", "None") != "Induced":
                out.append(t)
        return out

    fresh = [n for n, r in by_num.items() if r["stage"] == "Fresh" and real(n)]
    return by_num, sidx, care_edges, fresh


def _care_reachable(fresh, care_edges):
    seen = set(fresh)
    stack = list(fresh)
    while stack:
        n = stack.pop()
        for t in care_edges(n):
            if t not in seen:
                seen.add(t)
                stack.append(t)
    return seen


def test_every_fresh_starter_reaches_mega():
    by_num, sidx, care_edges, fresh = _graph()
    assert len(fresh) > 0

    from functools import lru_cache

    @lru_cache(maxsize=None)
    def reaches_mega(n):
        if sidx(n) >= MEGA:
            return True
        return any(reaches_mega(t) for t in care_edges(n))

    stranded_starts = [n for n in fresh if not reaches_mega(n)]
    names = [by_num[n]["name"] for n in stranded_starts]
    assert not stranded_starts, f"Fresh starters with no timed-care path to Mega: {names}"


def test_no_forced_softlock_below_mega():
    """Every climbable (>=1 care-edge) form below Mega keeps a path to Mega, so a pet
    is never *forced* down a dead branch. Dead-end terminals are fine — they just
    have no care-edges and are reached only by choosing their stats over a sibling's."""
    by_num, sidx, care_edges, fresh = _graph()
    reachable = _care_reachable(fresh, care_edges)

    from functools import lru_cache

    @lru_cache(maxsize=None)
    def reaches_mega(n):
        if sidx(n) >= MEGA:
            return True
        return any(reaches_mega(t) for t in care_edges(n))

    forced = []
    for n in reachable:
        if sidx(n) < MEGA and care_edges(n) and not reaches_mega(n):
            forced.append((n, by_num[n]["name"], by_num[n]["stage"]))
    assert not forced, f"forms that can evolve but are forced toward a soft-lock: {forced}"


def test_dead_end_terminals_are_optin():
    """The below-Mega care-terminals (jogress/spirit forms) are always opt-in: every
    parent that can evolve into one also offers a non-terminal sibling."""
    by_num, sidx, care_edges, fresh = _graph()
    reachable = _care_reachable(fresh, care_edges)
    dead = {n for n in reachable if sidx(n) < MEGA and not care_edges(n)}

    forced_in = []
    for p in reachable:
        kids = care_edges(p)
        if kids and all(k in dead for k in kids):   # parent's only options are terminals
            forced_in.append((p, by_num[p]["name"]))
    assert not forced_in, f"forms whose only evolutions are dead-end terminals: {forced_in}"
