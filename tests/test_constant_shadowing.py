"""No module-level constant may be defined twice with two different values.

Found by the sickness-system audit (2026-07-30, Joel: "audit the rest of the
sickness system for the same thing").  The P4 injury ruling of 2026-07-23 set

    INJ_LAPSE_MIN = 300      # game-min per lapse -- a wound lasts 5-60 real min

on line 582 of petbase.py, above the module's pre-existing

    INJ_LAPSE_MIN = 29       # InjLapseMin

on line 866.  Python re-bound the name, so the deliberate ruling was DEAD ON
ARRIVAL: every wound since has healed on canon's 29 (0.5-5.8 real minutes),
while the comment above the dead line described a game nobody was playing.
Nothing failed, nothing warned -- the shipped value was simply not the one the
author chose.  Same family as the .313 reason code that no client branch
matched: the change looked shipped because the code was there.

Same-VALUE repeats are noise (a constant restated identically in two blocks
hurts nobody), so this pin only fires on a genuine disagreement.
"""
import ast
import os

import tuipet

_SRC = os.path.dirname(os.path.abspath(tuipet.__file__))


def _module_constants(path):
    """{NAME: [(lineno, source-of-value)]} for module-level UPPER_CASE assigns."""
    with open(path, encoding="utf-8") as fh:
        tree = ast.parse(fh.read(), filename=path)
    out = {}
    for node in tree.body:                       # module level only, not in defs
        if not isinstance(node, ast.Assign):
            continue
        for target in node.targets:
            names = ([target] if isinstance(target, ast.Name)
                     else target.elts if isinstance(target, (ast.Tuple, ast.List))
                     else [])
            for i, n in enumerate(names):
                if not (isinstance(n, ast.Name) and n.id.isupper()):
                    continue
                value = node.value
                if isinstance(target, (ast.Tuple, ast.List)) and isinstance(
                        value, (ast.Tuple, ast.List)) and i < len(value.elts):
                    value = value.elts[i]        # unpack X, Y = 1, 12 elementwise
                out.setdefault(n.id, []).append((n.lineno, ast.unparse(value)))
    return out


def _py_files():
    for root, _dirs, files in os.walk(_SRC):
        if "__pycache__" in root:
            continue
        for f in sorted(files):
            if f.endswith(".py"):
                yield os.path.join(root, f)


def test_no_constant_is_silently_rebound_to_a_different_value():
    offenders = []
    for path in _py_files():
        for name, sites in _module_constants(path).items():
            if len(sites) < 2 or len({v for _, v in sites}) < 2:
                continue
            where = ", ".join(f"line {ln} = {v}" for ln, v in sites)
            offenders.append(f"{os.path.basename(path)}: {name} ({where})")
    assert not offenders, (
        "a later definition silently wins -- the earlier value, and whatever "
        "reasoning sits above it, is dead code:\n  " + "\n  ".join(offenders))


def test_the_injury_lapse_is_the_canon_one_and_says_so():
    """The specific case this pin was born from: one definition, canon's 29,
    so a wound heals in 29-348 game-min.  If the wait is ever meant to be
    longer that is a balance decision -- change it here, and there must still
    be exactly one place to change."""
    from tuipet import petbase
    assert petbase.INJ_LAPSE_MIN == 29
    sites = _module_constants(os.path.join(_SRC, "petbase.py"))["INJ_LAPSE_MIN"]
    assert len(sites) == 1, sites
    span = (petbase.MIN_INJ_LENGTH * petbase.INJ_LAPSE_MIN,
            petbase.MAX_INJ_LENGTH * petbase.INJ_LAPSE_MIN)
    assert span == (29, 348), span
