"""Digitama guide — the browsable egg-unlock book (Joel 2026-07-12).

The egg SELECT carousel stays available-only (no silhouettes, no teasers);
THIS is where the rest of the roster lives: every digitama in the game, the
state it is in, and — verbatim from eggUnlock.csv's LockedDescription — what
earns it, with the live 'how close am I' counter (egg.unlock_progress).
Data only: names, conditions and progress all come from egg.py /
data.load_egg_unlock(); nothing here is guessed.  (Prices left with the
licence cut 2026-07-17: every egg is earned, none are sold.)

↑↓ browse the list, ENTER opens one egg's story (←→ pages between eggs
without leaving it), ESC backs out."""
from __future__ import annotations
from . import data
from . import egg as egg_mod
from . import menu
from . import persistence
from .theme import INK, INK_B, DIM  # noqa: F401  (palette names bound for theme.apply propagation)

VIS = 9                                   # list rows shown at once (the old
#                                           in-LCD footer's row -- round 34)
_MARK = {"owned": "✓", "temp": "~", "locked": "✗"}
_VAL_W = 27                               # detail value column (38 - 10 label - cursor pad)


def _wrap(text, width=_VAL_W):
    """Greedy word wrap for the detail page's unlock line."""
    words, lines, cur = text.split(), [], ""
    for w in words:
        if cur and len(cur) + 1 + len(w) > width:
            lines.append(cur)
            cur = w
        else:
            cur = (cur + " " + w) if cur else w
    if cur:
        lines.append(cur)
    return lines


def _short_progress(line):
    """'lifetime wins 37/50' -> '37/50' for the list's right-hand tag."""
    tail = line.rsplit(" ", 1)[-1]
    return tail if "/" in tail else ""


class EggGuidePanel:
    def __init__(self, pet=None):
        self.pet = pet
        self.prog = persistence.get_progress()
        owned = persistence.get_eggs_owned()
        self.states = egg_mod.egg_states(self.prog, owned)
        self.rules = data.load_egg_unlock()
        self.n = egg_mod.count()
        self.i = 0
        self.detail = False
        self.frame_i = 0
        self.msg = "Every digitama, and what earns it."
        self.sfx = None

    # ---- panel protocol --------------------------------------------------
    def anim(self):
        self.frame_i += 1

    def strip(self):
        if self.detail:
            return menu.hints(("←→", "browse"), ("ESC", "back"))
        return menu.hints(("↑↓", "browse"), ("ENTER", "story"),
                          ("ESC", "out"))

    def key(self, k):
        if self.detail:
            if k in ("left", "h", "up", "k"):
                self.i = (self.i - 1) % self.n
            elif k in ("right", "l", "down", "j"):
                self.i = (self.i + 1) % self.n
            elif k == "pageup":                # the list's leap, in the story too
                self.i = (self.i - (VIS - 1)) % self.n
            elif k == "pagedown":
                self.i = (self.i + (VIS - 1)) % self.n
            elif k == "escape":
                self.detail = False
            elif k == "n":                     # n (the opening key) closes the book
                return ("done", None)
            return None
        # the list wraps like every sibling cursor list (and like this
        # screen's own detail view) -- QOL sweep 2026-07-23
        if k in ("up", "k"):
            self.i = (self.i - 1) % self.n
        elif k in ("down", "j"):
            self.i = (self.i + 1) % self.n
        elif k == "pageup":                  # page jumps, lobby-chat style
            self.i = max(0, self.i - (VIS - 1))
        elif k == "pagedown":
            self.i = min(self.n - 1, self.i + (VIS - 1))
        elif k in ("enter", "space"):
            self.detail = True
        elif k in ("escape", "n"):             # n (the opening key) also closes
            return ("done", None)
        return None

    # ---- the list ----------------------------------------------------------
    def _tag(self, idx):
        state = self.states[idx]
        if state == "owned":
            return "yours"
        if state == "temp":
            return "this gen"
        return _short_progress(egg_mod.unlock_progress(idx, self.prog)) or "locked"

    def _note(self, idx):
        """The selected egg's one-line story under the list: the rule's own
        LockedDescription, else the live win-gate counter (mystery eggs)."""
        rule = self.rules.get(idx)
        return (rule["desc"] if rule else "") or egg_mod.unlock_progress(idx, self.prog)

    def _list_scene(self):
        from rich.text import Text
        have = sum(1 for s in self.states.values() if s in ("owned", "temp"))
        out = menu.header("DIGITAMA GUIDE", f"{have}/{self.n}")

        def fmt(idx, j):
            cur = j == self.i
            state = self.states[idx]
            t = Text()
            t.append(("▸" if cur else " ") + _MARK[state] + " ",
                     style=INK_B if cur else (DIM if state == "locked" else INK))
            t.append(f"{egg_mod.hatch_name(idx)[:22]:<23}",
                     style=INK_B if cur else (DIM if state == "locked" else INK))
            t.append(f"{self._tag(idx)[:10]:>10}\n", style=INK_B if cur else DIM)
            return t

        self.i = menu.list_window(out, list(range(self.n)), self.i, VIS, fmt)
        out.append_text(menu.note(self._note(self.i), tick=self.frame_i))
        out.right_crop(1)     # keys ride the strip (round 34: the footer
        #                       doubled them and disagreed on the verb)
        return out

    # ---- one egg's story -----------------------------------------------------
    def _detail_rows(self, idx):
        state = self.states[idx]
        rule = self.rules.get(idx)
        rows = [("State", {"owned": "yours — on the carousel",
                           "temp": "hatchable this gen only",
                           "locked": "locked"}[state])]
        desc = (rule["desc"] if rule else "") or "a mystery egg"
        first = True
        for ln in _wrap(desc):
            rows.append(("Unlock" if first else "", ln))
            first = False
        live = egg_mod.unlock_progress(idx, self.prog)
        if state == "locked" and live and live != desc:
            rows.append(("Goal", live))
        rows.append(("Keeps", "this generation only"
                     if rule is not None and not rule["can_perm"] else "forever"))
        return rows

    def _detail_scene(self):
        name = egg_mod.hatch_name(self.i)
        out = menu.header(f"DIGITAMA  {name[:20].upper()}", f"{self.i + 1}/{self.n}")
        rows = self._detail_rows(self.i)
        for label, val in rows[:10]:
            out.append(f" {label:<9}", style=DIM)
            out.append(val[:_VAL_W + 1] + "\n", style=INK_B)
        out.append_text(menu.blanks(10 - len(rows)))
        out.right_crop(1)     # keys ride the strip (round 34)
        return out

    def text(self):
        return self._detail_scene() if self.detail else self._list_scene()
