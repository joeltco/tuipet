"""Generate src/tuipet/data/shadow_ties.json -- the chart rows that can never
win first-match (Joel 2026-10-15, evolution call #18 = A).

For every parent in every line chart, enumerate the bracket boundaries of the
counters its rows read, through the REAL checker (lines.check_rule), and
record each row that matches in some state but is never the FIRST match.
lines.select_line ties those rows with the first match (the stage roll picks),
so every form is reachable while deliberate catch-all rows keep their place.

Adapted from the read-only evolution audit probe (_astra/evo_probe.py,
2026-10-14).  Run:  python3 tools/shadow_ties.py [--check]
"""
import json
import os
import sys
from itertools import product
from types import SimpleNamespace

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from tuipet import adventure, lines, persistence  # noqa: E402
from tuipet.pet import EXP_PER_WIN  # noqa: E402

OUT = os.path.join(os.path.dirname(__file__), "..", "src", "tuipet", "data",
                   "shadow_ties.json")


def compute():
    """{line_id: {parent_dex: [shadowed target dex, ...]}} (JSON-ready)."""
    real_progress, real_cleared = persistence.get_progress, adventure.is_map_cleared
    profile = {"maps": set(), "raids": 0}
    persistence.get_progress = lambda: profile
    adventure.is_map_cleared = lambda pet, n: pet.map_done
    try:
        return _scan(profile)
    finally:
        persistence.get_progress, adventure.is_map_cleared = real_progress, real_cleared


def _scan(profile):
    out = {}
    for lid, chart in lines.load_lines().items():
        for parent, rows in chart["children"].items():
            stage = chart["members"][parent]["stage"]
            atoms = [atom for row in rows for alt in row["rule"] for atom in alt]
            kinds = {kind for kind, _, _ in atoms} - {"jogress"}
            domains = {}
            for kind in sorted(kinds):
                if kind in ("area", "noarea", "frag"):
                    continue
                if kind == "lv":
                    domains[kind] = range(1, lines.DMX_LEVEL_CAP[stage] + 1)
                    continue
                ceiling = {"gc": 472, "rand": 99, "cm": 19, "win": 15}.get(kind)
                values = {0}
                for key, lo, hi in atoms:
                    if key != kind:
                        continue
                    values.add(lo)
                    if hi is not None:
                        values.add(hi if kind == "win" else hi + 1)
                domains[kind] = sorted(v for v in values if ceiling is None or v <= ceiling)
            if kinds & {"area", "noarea"}:
                domains["map_done"] = [False, True]
                # All current AREA atoms fit these two raid endpoints.
                domains["raids"] = [0, 7]
            if "frag" in kinds:
                domains["frag"] = [False, True]
            reachable, met = set(), set()
            keys = list(domains)
            for values in product(*(domains[key] for key in keys)):
                state = dict(zip(keys, values))
                map_done = state.get("map_done", False)
                profile["maps"] = {3, 6} if map_done else set()
                profile["raids"] = state.get("raids", 0)
                battles = state.get("btl", 0)
                trainings = state.get("tr", 2 * battles)
                if trainings < 2 * battles:
                    continue
                # A win window and KO6 cannot exist without their paid experience.
                exp = EXP_PER_WIN * max(state.get("win", 0), state.get("ko6", 0))
                exp_ceiling = None
                if "lv" in state:
                    level = state["lv"]
                    exp = max(exp, lines.DMX_EXP_LEVELS[level - 1])
                    if level < lines.DMX_LEVEL_CAP[stage]:
                        exp_ceiling = lines.DMX_EXP_LEVELS[level] - 1
                exp = ((exp + EXP_PER_WIN - 1) // EXP_PER_WIN) * EXP_PER_WIN
                if exp_ceiling is not None and exp > exp_ceiling:
                    continue
                pet = SimpleNamespace(
                    num=parent, line_id=lid, stage=stage,
                    care_mistakes=state.get("cm", 0), stage_trainings=trainings,
                    overeat=state.get("of", 0), stage_battles=battles, exp=exp,
                    mega_kills=state.get("ko6", 0), gcell=state.get("gc", 0),
                    stage_roll=state.get("rand", 0), gcell_fragment=state.get("frag", False),
                    battle_log=[1] * state.get("win", 0), map_done=map_done,
                )
                matches = [i for i, row in enumerate(rows) if lines.check_rule(pet, row["rule"])]
                met.update(matches)
                if matches:
                    reachable.add(matches[0])       # pure first-match: who WINS
            for index, row in enumerate(rows):
                if row["jogress"] is None and index not in reachable and index in met:
                    out.setdefault(lid, {}).setdefault(str(parent), []).append(row["num"])
    return out


def main():
    data = compute()
    text = json.dumps(data, indent=1, sort_keys=True) + "\n"
    if "--check" in sys.argv:
        with open(OUT, encoding="utf-8") as fh:
            same = fh.read() == text
        print("shadow_ties.json", "up to date" if same else "STALE")
        sys.exit(0 if same else 1)
    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write(text)
    n = sum(len(v) for chart in data.values() for v in chart.values())
    print(f"wrote {n} shadowed rows across {len(data)} charts")


if __name__ == "__main__":
    main()
