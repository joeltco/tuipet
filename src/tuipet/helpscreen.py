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
    ("f feed - meat fills, pill heals", 1),
    ("p play   c clean poop", 1),
    ("s lights   v assistant", 1),
    ("", 0),
    ("EXPLORE", 2),
    ("a adventure - travel named regions,", 1),
    ("  fight wilds, clear zone bosses,", 0),
    ("  find items, rest in towns", 0),
    ("u cup - hourly tournaments; win", 1),
    ("  trophies to unlock new eggs", 0),
    ("l lobby - go online: chat, and", 1),
    ("  battle / jogress other players", 0),
    ("", 0),
    ("GROW", 2),
    ("Eggs hatch, then evolve by HOW you", 0),
    ("raise them - care, train, battles.", 0),
    ("Each egg has its own line to a Mega.", 0),
    ("t train - drills build battle power", 1),
    ("x DNA   d digicore", 1),
    ("n egg guide - every digitama + what", 1),
    ("  earns it, with live progress", 0),
    ("", 0),
    ("MANAGE", 2),
    ("o shop   i bag   e habitat", 1),
    ("g options   b report a bug   q quit", 1),
    ("", 0),
    ("TIPS", 2),
    ("Feed when hungry, clean the poop,", 0),
    ("and let it sleep at night. Win cups", 0),
    ("and adventures to unlock more eggs.", 0),
    ("Town shops sell eggs themed to their", 0),
    ("biome - explore to find them all.", 0),
]


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
        return max(0, len(HELP) - VIS)

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
        self.top = max(0, min(self.top, self._max_top()))
        pos = "%d-%d/%d" % (self.top + 1, min(self.top + VIS, len(HELP)), len(HELP))
        out = menu.header("HELP", pos)
        for text, kind in HELP[self.top:self.top + VIS]:
            style = INK_B if kind == 2 else (INK if kind == 1 else DIM)
            out.append((text or " ") + "\n", style=style)
        out.append_text(menu.footer(self._more_cue()))
        return out
