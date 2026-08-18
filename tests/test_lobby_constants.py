"""The lobby's layout budget is defined ONCE.

The 2026-07-17 module split cut lobbyscreen into three files and COPIED the
constants block into each instead of importing it, so lobbychat, lobbybout and
lobbyscreen each carried their own CHATW/ROSTW/BODY/CHAT_MAX.  They agreed at
25/12/8/400 only by luck: Python takes the LAST definition silently, so
widening the chat column in the module you happened to open would have left
the other two narrow, and the divider would tear exactly the way the
CELL-WIDTH LAW exists to prevent.

Equality is NOT the pin -- three duplicate 25s are equal too.  The pin is that
the package contains exactly one module-level assignment of each name, which is
false the moment someone pastes the block back into a sibling.
"""
import ast
import os

import tuipet
from tuipet import lobbybout, lobbychat, lobbyscreen

_SRC = os.path.dirname(os.path.abspath(tuipet.__file__))

# the budget every lobby surface spends, and the module that owns it
OWNER = "lobbychat"
NAMES = ("CHATW", "ROSTW", "BODY", "CHAT_MAX")

# every lobby constant that must have exactly one home, budget or not.
# OFFLINE_ID (2026-08-18) is a SENTINEL id -- a second copy that drifted to a
# different value would silently stop matching, and the offline roster rows it
# marks would start offering ghost actions that address a player who isn't there
SINGLE_SOURCE = NAMES + ("OFFLINE_ID",)


def _module_level_assignments(name):
    """Every module in the package that ASSIGNS `name` at top level.

    Imports don't count -- re-exporting the owner's value is the fix, not the
    bug.  Only a fresh binding of its own is a second source of truth."""
    out = []
    for root, _dirs, files in os.walk(_SRC):
        if "__pycache__" in root:
            continue
        for fn in sorted(files):
            if not fn.endswith(".py"):
                continue
            path = os.path.join(root, fn)
            with open(path, encoding="utf-8") as fh:
                tree = ast.parse(fh.read(), path)
            for node in tree.body:                      # top level only
                targets = (node.targets if isinstance(node, ast.Assign)
                           else [node.target] if isinstance(node, ast.AnnAssign)
                           else [])
                for t in targets:
                    if isinstance(t, ast.Name) and t.id == name:
                        out.append(fn[:-3])
    return out


def test_each_constant_is_assigned_in_exactly_one_module():
    for name in SINGLE_SOURCE:
        where = _module_level_assignments(name)
        assert where == [OWNER], (
            f"{name} is assigned in {where}; it must be defined only in "
            f"{OWNER}.py and imported everywhere else")


def test_the_siblings_see_the_owners_object():
    """Not just an equal value -- the SAME object, i.e. a real import.

    ⚠ Weaker than it looks, and deliberately kept anyway: CPython interns small
    ints, so `is` cannot tell a duplicated 25 from an imported one and only
    CHAT_MAX (400, past the intern cache) actually trips here.  The test above
    is the real pin -- this one just fails louder when it does fire."""
    for name in NAMES:
        src = getattr(lobbychat, name)
        for mod in (lobbybout, lobbyscreen):
            assert getattr(mod, name) is src, f"{mod.__name__}.{name} is a copy"


def test_the_old_names_stay_importable():
    """lobbyscreen's header promises 'the old names stay importable' -- tests
    and tools import CHATW/CHAT_MAX from it by name, so the re-export is part
    of the contract, not incidental."""
    from tuipet.lobbyscreen import CHATW, CHAT_MAX, ROSTW  # noqa: F401
    assert (CHATW, ROSTW, CHAT_MAX) == (25, 12, 400)


def test_the_widths_still_add_up_to_the_lcd_box():
    """The chat column, the divider and the player box tile the 38-cell box."""
    assert lobbychat.CHATW + lobbychat.ROSTW + 1 == 38
