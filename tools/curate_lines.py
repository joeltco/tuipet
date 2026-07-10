"""Curate every remaining egg into an evolution line (LINES_SPEC arc 5).

Walks the REAL corpus evolution graph from each egg's hatch root into a
DM20-shaped subtree (1 Baby I -> 1 Baby II -> 2 Child -> ~3 Adult/Child ->
shared Perfects -> Megas) and emits lines.csv rows in the established bracket
grammar. Never invents an edge; never uses a placeholder form.

Canon-name HINTS steer the pick where humulos documents the roster (Ver.2,
Ver.E, the Corona/Luna pair); a hint that names a form the graph cannot reach
simply does not fire.  ver1 and verX (hand-curated) are preserved verbatim.

Run:  PYTHONPATH=src python3 tools/curate_lines.py [--write]
"""
import csv
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from tuipet import data  # noqa: E402

LINES_CSV = os.path.join(os.path.dirname(__file__), "..", "src", "tuipet", "data", "lines.csv")
# hand-maintained lines the curator never rewrites: the device-canon ports +
# canon bonus line (kept against the humulos DM20 charts, canon scan 2026-07-08)
# and tuipet's own authored lines (petitmon/pichimon, Joel 2026-07-09 -- canon
# evolution families, tuipet-authored conditions)
HAND_CURATED = ("ver1", "ver2", "ver3", "ver4", "ver5", "verE", "verX", "sakumon", "petitmon", "pichimon")
STAGE_ORDER = ["Fresh", "InTraining", "Rookie", "Champion", "Ultimate", "Mega"]
# Baby II sleeps at 21:00 on every DM20 chart; Baby I is canon-NA (house 20:00)
BEDTIME = {"Fresh": "20:00", "InTraining": "21:00", "Rookie": "21:00",
           "Champion": "22:00", "Ultimate": "23:00", "Mega": "23:00"}

# canon egg names -> line ids (DM20 versions); everything else gets a name slug
LINE_IDS = {"Botamon": "ver1", "Punimon": "ver2", "Poyomon": "ver3",
            "Yuramon": "ver4", "Zurumon": "ver5", "YukimiBotamon": "verE",
            "Dodomon": "verX"}

# humulos-documented rosters only -- a hint is a PREFERENCE, never an invention
HINTS = {
    "ver2": {"InTraining": ["Tsunomon", "Tunomon"], "Rookie": ["Gabumon", "Elecmon"],
             "Champion": ["Garurumon", "Kabuterimon", "Angemon", "Frigimon",
                          "Yukidarumon", "Birdramon", "Whamon", "Vegiemon", "Vegimon"],
             "Ultimate": ["SkullGreymon", "MetalMamemon", "Vademon"],
             "Mega": ["CresGarurumon", "SkullMammothmon", "SkullMammon"]},
    "verE": {"InTraining": ["Nyaromon"], "Rookie": ["Salamon", "Plotmon"],
             "Champion": ["Meicoomon", "Gatomon", "Tailmon"],
             "Ultimate": ["Meicrackmon", "Angewomon"],
             "Mega": ["Rasielmon", "Ophanimon"]},
    "pichimon": {"Rookie": ["Coronamon", "Lunamon"], "Champion": ["Firamon", "Lekismon"],
                 "Ultimate": ["Flaremon", "Crescemon"], "Mega": ["Apollomon", "Dianamon"]},
    "sakumon": {"InTraining": ["Sakuttomon"], "Rookie": ["Zubamon", "Hackmon"],
                "Champion": ["Zubaeagermon", "BaoHackmon"],
                "Ultimate": ["Duramon", "SaviorHackmon"],
                "Mega": ["Durandamon", "Jesmon"]},
    "petitmon": {"InTraining": ["Babydmon"], "Rookie": ["Dracomon"],
                 "Champion": ["Coredramon"], "Ultimate": ["Wingdramon", "Groundramon"],
                 "Mega": ["Slayerdramon", "Breakdramon"]},
    "ver3": {"InTraining": ["Tokomon"], "Rookie": ["Patamon", "Kunemon"],
             "Champion": ["Unimon", "Centarumon", "Centalmon", "Ogremon", "Orgemon",
                          "Bakemon", "Shellmon", "Drimogemon", "Sukamon", "Scumon"],
             "Ultimate": ["Andromon", "Giromon", "Etemon"],
             "Mega": ["HiAndromon", "KingEtemon"]},
    "ver4": {"InTraining": ["Tanemon"], "Rookie": ["Biyomon", "Piyomon", "Palmon"],
             "Champion": ["Monochromon", "Kokatorimon", "Cockatrimon", "Leomon",
                          "Kuwagamon", "Coelamon", "Mojyamon", "Nanimon"],
             "Ultimate": ["Megadramon", "Piximon", "Piccolomon", "Digitamamon"],
             "Mega": ["Aegisdramon", "Titamon"]},
    "ver5": {"InTraining": ["Pagumon"], "Rookie": ["Gazimon", "Gizamon"],
             "Champion": ["DarkTyrannomon", "Cyclomon", "Devidramon", "Tuskmon",
                          "Flymon", "Deltamon", "Raremon"],
             "Ultimate": ["MetalTyrannomon", "Datamon", "Nanomon", "ExTyrannomon"],
             "Mega": ["Machinedramon", "Mugendramon", "Puppetmon", "Pinochimon"]},
}

# per-form sleep times (humulos DM20 list, full re-fetch 2026-07-08; covers
# every Ver.1-5 + bonus-line form); 0:00 AM -> 24:00 per the ver1 convention.
# Applied by NAME; unlisted forms keep stage defaults.
SLEEP = {}
for _names, _t in (
    (("Koromon", "Agumon", "Numemon", "Tsunomon", "Tunomon", "Gabumon",
      "Vegimon", "Vegiemon", "Tokomon", "Patamon", "Sukamon", "Scumon",
      "Tanemon", "Biyomon", "Piyomon", "Nanimon", "Pagumon", "Raremon",
      "Nyaromon", "Salamon", "Plotmon", "Sakuttomon", "Babydmon", "Pukamon",
      "Coronamon", "Dorimon"), "21:00"),
    (("Betamon", "Meramon", "Mamemon", "Elecmon", "Kabuterimon", "Angemon",
      "Kunemon", "Unimon", "Shellmon", "Drimogemon", "Palmon", "Monochromon",
      "Leomon", "Kokatorimon", "Cockatrimon", "Piximon", "Piccolomon",
      "Puppetmon", "Pinochimon", "Meicoomon", "Meicrackmon", "Zubamon",
      "Hackmon", "Firamon", "Flaremon", "Dorumon"), "22:00"),
    (("Greymon", "Tyrannomon", "Tyranomon", "Airdramon", "Seadramon",
      "MetalGreymon", "Monzaemon", "BlitzGreymon", "Garurumon", "Yukidarumon",
      "Frigimon", "Birdramon", "Whamon", "MetalMamemon", "Vademon",
      "CresGarurumon", "Centarumon", "Centalmon", "Kuwagamon", "Megadramon",
      "Gazimon", "Gizamon", "Zubaeagermon", "BaoHackmon", "Dracomon",
      "Coredramon", "Wingdramon", "Examon", "Apollomon", "Dorugamon",
      "DoruGreymon", "Alphamon", "Omegamon"), "23:00"),
    (("Devimon", "BanchoMamemon", "SkullGreymon", "SkullMammothmon",
      "SkullMammon", "Ogremon", "Orgemon", "Bakemon", "Andromon", "Etemon",
      "Giromon", "HiAndromon", "KingEtemon", "Coelamon", "Mojyamon",
      "Digitamamon", "Titamon", "Aegisdramon", "DarkTyrannomon", "Devidramon",
      "Flymon", "Cyclomon", "Tuskmon", "Deltamon", "MetalTyrannomon",
      "Datamon", "Nanomon", "ExTyrannomon", "Machinedramon", "Mugendramon",
      "Rasielmon", "Duramon", "Durandamon", "SaviorHackmon", "Jesmon",
      "Slayerdramon", "Breakdramon", "Groundramon", "Lunamon", "Lekismon",
      "Crescemon", "Dianamon", "RustTyrannomon"), "24:00"),
):
    for _n in _names:
        SLEEP[_n] = _t


def _slug(name):
    return "".join(c for c in name.lower() if c.isalnum())


def load_corpus():
    _, by_num = data.load_sprites()
    evo = data.load_evolutions()
    reqs = data.load_requirements()
    return by_num, evo, reqs


def curate(by_num, evo, reqs, root, line_id, usage, auto_hints=None):
    """One line: list of row dicts. Deterministic; consults/updates `usage`.

    auto_hints carries the line's PREVIOUS roster (from the CSV being
    rewritten) so a re-run repairs structure without rerolling shipped
    content; explicit HINTS win per stage."""
    hints = {**(auto_hints or {}), **HINTS.get(line_id, {})}
    members = {}          # num -> row
    rows = []

    def add(num, stage, parents, rule):
        if num in members:                      # shared child
            new_parents = [p for p in parents if p not in members[num]["parents"]
                           and all(p not in r["parents"] for r in rows if r["num"] == num)]
            if not new_parents:
                return
            if stage in ("Ultimate", "Mega") and rule == members[num]["rule"]:
                # single-child funnel rows: same gate, no ordering hazard
                members[num]["parents"].extend(new_parents)
                return
            # multi-child stages get ONE ROW PER PARENT so first-match order
            # stays correct per road (the ver1 dual-road idiom).  Merging into
            # the first row parked the shared catch-all BEFORE the second
            # rookie's own rows and shadowed them all dead (canon scan
            # 2026-07-08: 137 unreachable forms).
            rows.append({"num": num, "stage": stage,
                         "parents": new_parents, "rule": rule})
            return
        row = {"num": num, "stage": stage, "parents": list(parents), "rule": rule}
        members[num] = row
        rows.append(row)
        # usage is keyed by NAME so duplicate dexes count as one identity
        nm = by_num[num]["name"]
        usage[nm] = usage.get(nm, 0) + 1

    def candidates(parent, stage):
        out = []
        for t in evo.get(parent, []):
            r = by_num.get(t)
            if not r or r["stage"] != stage or data.is_placeholder(t):
                continue
            if t in members:                    # in-line sharing handled by add()
                out.append(t)
                continue
            if reqs.get(t, {}).get("special", "None") not in ("None", "Failed"):
                continue                        # jogress/fusion/mode stay special paths
            out.append(t)
        hint = {n: i for i, n in enumerate(hints.get(stage, []))}
        root_field = by_num[root].get("field", "")
        line_names = {by_num[m]["name"] for m in members}
        out.sort(key=lambda t: (
            hint.get(by_num[t]["name"], 99),            # canon roster first
            0 if t in members else 1,                    # then in-line sharing
            usage.get(by_num[t]["name"], 0),             # then spread across lines
            0 if by_num[t].get("field", "") == root_field else 1,   # then flavor
            t))
        # de-dupe by NAME: three corpus Gabumons are one Gabumon; a form already
        # in the line under another dex must not reappear as a sibling
        seen, uniq = set(), []
        for t in out:
            nm = by_num[t]["name"]
            if nm in seen or (t not in members and nm in line_names):
                continue
            seen.add(nm)
            uniq.append(t)
        return uniq

    def failed_last(pool):
        """Catch-all slot prefers a Failed-flagged form (the Numemon of the line)."""
        f = [t for t in pool if reqs.get(t, {}).get("special") == "Failed"]
        return f[0] if f else (pool[0] if pool else None)

    def is_failed(t):
        return reqs.get(t, {}).get("special") == "Failed"

    def has_onward(t, next_stage):
        """The corpus graph continues from t: a form we could pick next stage."""
        return any(by_num.get(k, {}).get("stage") == next_stage
                   and not data.is_placeholder(k) for k in evo.get(t, []))

    add(root, "Fresh", ["egg"], "TIME")
    baby2 = candidates(root, "InTraining")[:1]
    for t in baby2:
        add(t, "InTraining", [root], "TIME")
    rookies = []
    for b in baby2:
        picks = candidates(b, "Rookie")[:2]
        rules = ["CM 0-2", "CM 3+"] if len(picks) == 2 else ["TIME"]
        for t, rl in zip(picks, rules):
            add(t, "Rookie", [b], rl)
            rookies.append(t)
    champs = []
    for rk in rookies:
        pool = candidates(rk, "Champion")
        if not pool:
            continue
        flav = 0 if line_id in HINTS else (sum(map(ord, line_id)) % 3)
        T3 = (["CM 0-2, TR 16+", "CM 0-2, TR 0-15", "TIME"],   # care (canon shape)
              ["TR 16+", "TR 5-15", "TIME"],                    # a training line
              ["CM 0-2, BTL 4+", "CM 0-2", "TIME"])[flav]       # a battler line
        T2 = (["CM 0-2", "TIME"], ["TR 8+", "TIME"], ["BTL 4+", "TIME"])[flav]
        # Failed forms take only the catch-all slot (a punishment mon in a
        # good-care slot reads as reward); good slots prefer champions the
        # graph can continue from, so a well-raised pet is never the one
        # that strands (sunamon's Baboongamon, canon scan 2026-07-08)
        good = [t for t in pool if not is_failed(t)]
        good.sort(key=lambda t: 0 if has_onward(t, "Ultimate") else 1)  # stable
        if len(pool) >= 3 and len(good) >= 2:
            picks = good[:2] + [failed_last([t for t in pool if t not in good[:2]])]
            rules = T3
        elif len(good) >= 1 and len(pool) >= 2:
            catch = failed_last([t for t in pool if t != good[0]])
            picks, rules = [good[0], catch], T2
        else:
            picks, rules = pool[:1], ["TIME"]
        for t, rl in zip(picks, rules):
            add(t, "Champion", [rk], rl)
            champs.append(t)
    flav = 0 if line_id in HINTS else (sum(map(ord, line_id)) % 3)
    ult_gate = ("WIN 12/15", "WIN 12/15", "BTL 12+")[flav]      # battlers grind fights
    mega_gate = ("CM 0-2", "CM 0-2, TR 10+", "KO6 2+")[flav]    # trainers drill, battlers hunt
    ults = []
    for ch in dict.fromkeys(champs):
        pool = candidates(ch, "Ultimate")
        pool.sort(key=lambda t: 0 if has_onward(t, "Mega") else 1)  # stable
        for t in pool[:1]:
            add(t, "Ultimate", [ch], ult_gate)
            ults.append(t)
    for ul in dict.fromkeys(ults):
        pick = candidates(ul, "Mega")[:1]
        for t in pick:
            add(t, "Mega", [ul], mega_gate)
    # a member below the line's ceiling with no onward row is a dead end the
    # graph forced on us -- annotate so the invariant tests see it was chosen,
    # not missed (device lines mark their canon dead ends the same way)
    kids = set()
    for r in rows:
        kids.update(r["parents"])
    ceiling = max(STAGE_ORDER.index(r["stage"]) for r in rows)
    for r in rows:
        if STAGE_ORDER.index(r["stage"]) < ceiling and r["num"] not in kids:
            r["note"] = "dead end: no onward corpus edge"
    return rows


def main(write=False):
    from tuipet import egg as egg_mod
    by_num, evo, reqs = load_corpus()

    with open(LINES_CSV, newline="") as fh:
        kept = [r for r in csv.reader(fh)][0:]
    header, kept_rows = kept[0], [r for r in kept[1:] if r and r[0] in HAND_CURATED]

    usage = {}
    for r in kept_rows:
        nm = by_num[int(r[2])]["name"]
        usage[nm] = usage.get(nm, 0) + 1

    # previous rosters become per-line auto-hints: a re-run repairs rule
    # structure (per-parent rows, Failed slotting) without rerolling the
    # shipped content of 40 lines
    prev_hints = {}
    for r in kept[1:]:
        if not r or r[0] in HAND_CURATED:
            continue
        names = prev_hints.setdefault(r[0], {}).setdefault(r[1], [])
        nm = by_num[int(r[2])]["name"]
        if nm not in names:
            names.append(nm)

    out_rows, stats = [], []
    for idx in range(egg_mod.count()):
        targets = egg_mod.hatch_targets(idx)
        if len(targets) != 1:
            continue                            # the "???" pool eggs hatch other lines' roots
        root = targets[0]
        name = egg_mod.hatch_name(idx)
        line_id = LINE_IDS.get(name, _slug(name))
        if line_id in HAND_CURATED:
            continue
        rows = curate(by_num, evo, reqs, root, line_id, usage,
                      auto_hints=prev_hints.get(line_id))
        ceiling = max(rows, key=lambda r: STAGE_ORDER.index(r["stage"]))["stage"]
        stats.append((line_id, len(rows), ceiling))
        for r in rows:
            nm = by_num[r["num"]]["name"]
            bed = SLEEP.get(nm, BEDTIME[r["stage"]])   # canon per-form, else stage default
            note = nm + (f" ({r['note']})" if r.get("note") else "")
            out_rows.append([line_id, r["stage"], str(r["num"]),
                             ";".join(str(p) for p in r["parents"]),
                             r["rule"], bed, note])

    for lid, n, ceil in stats:
        print(f"{lid:16s} {n:3d} forms   ceiling {ceil}")
    print(f"{len(stats)} lines curated, {len(out_rows)} rows"
          f" (+{len(kept_rows)} hand-curated kept)")
    if write:
        import io
        buf = io.StringIO()
        w = csv.writer(buf, lineterminator="\n")
        w.writerow(header)
        w.writerows(kept_rows)
        w.writerows(out_rows)
        open(LINES_CSV, "w").write(buf.getvalue())
        print("lines.csv written")


if __name__ == "__main__":
    main(write="--write" in sys.argv)
