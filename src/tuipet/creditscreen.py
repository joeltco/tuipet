"""CREDITS — the sprite artists.

The mon art in tuipet is ripped from multiple fan games and the sprite
community around them; the artists below made those pixels.  Every player
gets this screen one key away ('z').  Data: credits.json (artist -> the
sprites matched to them), plus the lead spriters whose work anchors the
whole set."""
from __future__ import annotations
from . import data, menu
from .theme import INK, INK_B, DIM  # noqa: F401  (theme.apply propagation)

VIS = 8

# the lead spriters credited by the source projects themselves
LEADS = ["Tortoiseshel", "Mirasein"]


def _rows():
    by = data.load_credits().get("authors", {})
    counts = {}
    for a, sprites in by.items():
        if a.lower() == "unknown":
            continue
        for part in a.split(","):            # combined "a,b" entries
            part = part.strip()
            if part:
                counts[part] = counts.get(part, 0) + len(sprites)
    rows = [("SPRITE ARTISTS", 2),
            ("the pixels are theirs — thank them", 0), ("", 0)]
    for a in LEADS:
        rows.append((f"{a} — lead spriter", 1))
        counts.pop(a, None)
    for a, n in sorted(counts.items(), key=lambda kv: -kv[1]):
        rows.append((f"{a} — {n} sprite{'s' if n != 1 else ''}", 1))
    rows += [("", 0), ("...and the wider V-pet sprite", 0),
             ("community. Art ripped from multiple", 0),
             ("fan games; credit where it is due.", 0)]
    return rows


class CreditsPanel:
    def __init__(self, pet):
        self.pet = pet
        self.rows = _rows()
        self.top = 0
        self.frame_i = 0

    def anim(self):
        self.frame_i += 1

    def _max_top(self):
        return max(0, len(self.rows) - VIS)

    def key(self, k):
        if k in ("up", "k"):
            self.top = max(0, self.top - 1)
        elif k in ("down", "j"):
            self.top = min(self._max_top(), self.top + 1)
        elif k in ("escape", "z", "enter", "space", "q"):
            return ("done", "")
        return None

    def strip(self):
        return menu.hints(("↑↓", "scroll"), ("ESC", "back"))

    def text(self):
        self.top = max(0, min(self.top, self._max_top()))
        pos = "%d-%d/%d" % (self.top + 1,
                            min(self.top + VIS, len(self.rows)), len(self.rows))
        out = menu.header("CREDITS", pos)
        for text, kind in self.rows[self.top:self.top + VIS]:
            style = INK_B if kind == 2 else (INK if kind == 1 else DIM)
            out.append((text or " ")[:38] + "\n", style=style)
        more = "▼ more below" if self.top < self._max_top() else ""
        out.append_text(menu.footer(more))
        return out
