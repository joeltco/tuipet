"""In-game help — the controls and a quick how-to, so a new player isn't left
staring at single-letter keys (Joel 2026-07-09).  Scrolls in the LCD box; open
with ? from anywhere on the home screen."""
from __future__ import annotations
from . import menu
from .theme import INK, INK_B, DIM  # noqa: F401  (palette names bound for theme.apply propagation)

VIS = 8                                   # lines shown at once in the box

# (text, kind): 2 = section head (bold), 1 = a control line, 0 = prose (dim)
HELP = [
    ("CARE", 2),
    ("f feed - meat fills the belly", 1),
    ("h pill - cures sickness, restores", 1),
    ("  strength and energy", 0),
    ("c clean poop   s lights", 1),
    ("Your mon lives in REAL TIME - it", 0),
    ("sleeps on a clock, gets hungry", 0),
    ("hourly, and calls when it needs", 0),
    ("you. Ignore a call for 20 minutes", 0),
    ("and it counts a care mistake.", 0),
    ("", 0),
    ("ONLINE", 2),
    ("l lobby - go online: chat, and", 1),
    ("  battle / jogress other players;", 0),
    ("  TAB pages the ladder + RAID BOSS", 0),
    ("", 0),
    ("GROW", 2),
    ("Eggs hatch and evolve on a clock:", 0),
    ("good care + training picks the", 0),
    ("BEST branch, neglect the worst.", 0),
    ("t train - drills feed evolution", 1),
    ("  and widen your battle windows", 0),
    ("Battles also count toward growth.", 0),
    ("", 0),
    ("SCENES", 2),
    ("The backdrop is yours to pick:", 0),
    ("e opens the scene gallery.", 1),
    ("", 0),
    ("CREDITS", 2),
    ("Art ripped from multiple fan games", 0),
    ("and the V-pet sprite community.", 0),
    ("The artists, with thanks:", 0),
]


def _full_help():
    """HELP + the sprite-artist credits appended (attribution ships with
    the game; it lives here now instead of its own screen)."""
    rows = list(HELP)
    try:
        from . import creditscreen
        for text, kind in creditscreen._rows()[3:]:
            if text:
                rows.append((text[:38], 0))
    except Exception:
        rows.append(("(credits unavailable)", 0))
    return rows


class HelpPanel:
    def __init__(self, pet):
        self.pet = pet
        self.top = 0
        self.frame_i = 0
        self.msg = "How to play tuipet."

    def anim(self):
        self.frame_i += 1

    def strip(self):
        return menu.hints(("↑↓", "scroll"), ("ESC", "out"))

    def _max_top(self):
        rows = getattr(self, "_rows", None)
        if rows is None:
            rows = self._rows = _full_help()
        return max(0, len(rows) - VIS)

    def key(self, k):
        if k in ("up", "k"):
            self.top = max(0, self.top - 1)
        elif k in ("down", "j"):
            self.top = min(self._max_top(), self.top + 1)
        elif k in ("escape", "q"):
            return ("done", None)
        return None

    def _more_cue(self):
        """A scroll affordance for the footer -- it says THERE IS more (the
        message strip already says HOW to move), so the two never echo."""
        up, dn = self.top > 0, self.top < self._max_top()
        if up and dn:
            return "▲▼ more"
        if dn:
            return "▼ more below"
        if up:
            return "▲ more above"
        return ""

    def text(self):
        rows = getattr(self, "_rows", None)
        if rows is None:
            rows = self._rows = _full_help()
        self.top = max(0, min(self.top, self._max_top()))
        pos = "%d-%d/%d" % (self.top + 1, min(self.top + VIS, len(rows)), len(rows))
        out = menu.header("HELP", pos)
        for text, kind in rows[self.top:self.top + VIS]:
            style = INK_B if kind == 2 else (INK if kind == 1 else DIM)
            out.append((text or " ") + "\n", style=style)
        out.append_text(menu.footer(self._more_cue()))
        return out
