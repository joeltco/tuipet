"""Shared chrome for the in-display menu panels: a consistent titled header
bar, selectable rows with a cursor, and a footer hint. Keeps every menu
looking the same and themed (colours come from theme via the INK/SEL names)."""
from __future__ import annotations
from rich.text import Text
from .theme import INK, INK_B, DIM, SEL

W = 38  # content width inside the 40-wide LCD


def header(title, right=""):
    """Title (left, bold) + optional right-aligned info, then a divider rule."""
    title = title[:W]
    t = Text()
    if right:
        gap = max(1, W - len(title) - len(right))
        t.append(title + " " * gap, style=INK_B)
        t.append(right, style=DIM)
    else:
        t.append(title, style=INK_B)
    t.append("\n")
    t.append("─" * W, style=DIM)
    t.append("\n")
    return t


def bar(title, right=""):
    """Compact 1-line title (bold) + optional right-aligned info, no divider -
    for the scene-heavy activity screens that can't spare a line."""
    t = Text()
    title = title[:W]
    if right:
        gap = max(1, W - len(title) - len(right))
        t.append(title + " " * gap, style=INK_B)
        t.append(right, style=DIM)
    else:
        t.append(title, style=INK_B)
    t.append("\n")
    return t


def row(label, selected=False):
    """A selectable list row with a ▸ cursor; selected rows render inverted."""
    line = (("▸ " if selected else "  ") + label)[:W].ljust(W)
    return Text(line + "\n", style=SEL if selected else INK)


NOTE_HOLD = 16   # marquee ticks held on the head each pass (~1.6s at the 10Hz clock)
NOTE_STEP = 2    # advance one character every N ticks (~5 chars/s, the HUD cadence)
NOTE_GAP = "      "


def note(msg, tick=None):
    """A status line (bold).  A message wider than the LCD used to CLIP silently
    (the battle menu's 'It IGNORED you!' vanished off the end -- audit 2026-07-04).
    Animated panels pass their frame counter as `tick` and long messages marquee
    with the HUD's proven cadence; without a tick they clip on an ellipsis."""
    if len(msg) <= W:
        return Text(msg + "\n", style=INK_B)
    if tick is None:
        return Text(msg[:W - 1] + "…\n", style=INK_B)
    loop = msg + NOTE_GAP
    cycle = len(loop) + NOTE_HOLD                 # hold on the head again each wrap
    pos = (tick // NOTE_STEP) % cycle
    off = max(0, pos - NOTE_HOLD)
    return Text((loop + loop)[off:off + W] + "\n", style=INK_B)


def footer(hint):
    """Control hints (dim), no trailing newline."""
    return Text(hint[:W], style=DIM)


def blanks(n):
    return Text("\n" * max(0, n), style=INK)

def list_window(out, rows, cursor, vis, fmt, empty=None):
    """The shared scrolling list body: a vis-row window centred on the cursor,
    each row through fmt(item, index) -> (label, selected_ok), padded with
    blanks.  Retires seven hand-rolled copies (audit 2026-07).  Returns the
    clamped cursor so callers can keep theirs in range."""
    n = len(rows)
    cursor = min(cursor, max(0, n - 1))
    if not n:
        if empty:
            out.append_text(row(empty))
        out.append_text(blanks(vis - (1 if empty else 0)))
        return cursor
    lo = max(0, min(cursor - vis // 2, n - vis))
    shown = 0
    for i in range(lo, min(lo + vis, n)):
        out.append_text(row(fmt(rows[i], i), i == cursor))
        shown += 1
    out.append_text(blanks(vis - shown))
    return cursor


class SubHost:
    """Mixin for panels that host a child panel in `self.sub` (battle inside
    adventure, town inside adventure, battle inside town/cup).  One home for
    the anim-delegate + sfx-bubble seam that was hand-rolled three ways --
    the flee-boss bug lived in exactly this kind of drift (audit 2026-07)."""

    sub = None

    def sub_anim(self):
        """Delegate a frame to the child; bubble its sfx up.  True if handled."""
        if self.sub is None:
            return False
        self.sub.anim()
        self.sfx = getattr(self.sub, "sfx", None)
        self.sub.sfx = None
        return True

    def sub_key(self, k, on_done):
        """Route a key to the child.  When the child finishes (('done', r)),
        clear it and hand r to on_done.  Returns True if the child had the key."""
        if self.sub is None:
            return False
        r = self.sub.key(k)
        if r is not None and r[0] == "done":
            self.sub = None
            on_done(r[1])
        return True
