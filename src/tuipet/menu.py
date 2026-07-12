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


def hints(*pairs):
    """The MESSAGE-BOX hint line (hint overhaul, Joel 2026-07-10): keys bright,
    labels dim, dot-separated -- '[b]KEY[/][dim] label[/] [dim]·[/] ...'.  One
    convention for every screen's strip(); keep the PLAIN text <= 40 cols so
    the line holds still (live hints never marquee)."""
    return " [dim]·[/] ".join(f"[b]{k}[/][dim] {lbl}[/]" for k, lbl in pairs)


def blanks(n):
    return Text("\n" * max(0, n), style=INK)


def scene_ink(bgimg):
    """The paint() rule: sprites over a background image render as dark
    silhouettes (SIL_DAY), plain LCD ink otherwise -- NEVER white over a bg.
    This one-line invariant lived in 13 hand-rolled copies across the scene
    screens (refactor 2026-07-05)."""
    from .theme import SIL_DAY, LCD_ON           # read late: theme.apply retints
    return SIL_DAY if bgimg else LCD_ON


def paint(placements, bgimg, rows=12, cols=40, overlay=None, clip=None, overlay_free=None):
    """render_scene under the paint() rule -- the whole-LCD scene call the
    scene screens share (screens that reuse one ink across several render
    calls take scene_ink directly).  `clip` forwards the window-law rect --
    pass grid.WINDOW ONLY from callers whose canvas is a verified full-LCD
    12-row scene; screens that stage their own cinematics leave it None."""
    from .render import render_scene
    from .theme import LCD_BG
    return render_scene(placements, cols, rows, scene_ink(bgimg), LCD_BG,
                        overlay=overlay, bgimg=bgimg, clip=clip,
                        overlay_free=overlay_free)


IC_W, IC_ROWS = 10, 4   # the selected-item icon cell every icon view shares


def icon_cell(src):
    """Rasterise one sprite bitmap into the IC_W x IC_ROWS icon cell,
    auto-downsampled to fit both dimensions so it never clips."""
    blank = [" " * IC_W] * IC_ROWS
    sh = len(src) if src else 0
    sw = max((len(r) for r in src), default=0) if src else 0
    if not sw:
        return blank
    from .render import downsample, bitmap_text
    from .theme import LCD_ON, LCD_BG           # read late: theme.apply retints
    factor = max(1, -(-sw // IC_W), -(-sh // (2 * IC_ROWS)))
    bm = downsample(src, factor)
    if not max((len(r) for r in bm), default=0):
        return blank
    lines = [t.plain.ljust(IC_W)                # w <= IC_W (factor guarantees it)
             for t in bitmap_text(bm, LCD_ON, LCD_BG)]
    return (lines + blank)[:IC_ROWS]


def item_icon(e):
    """A consumable/egg entry's icon as IC_ROWS cell lines.  ONE lookup for
    every icon view -- the shop, the bag, the feed menu and the town shops
    (refactor 2026-07-05); shop eggs ride their real egg frames."""
    fr = None
    if e and e.get("egg_idx") is not None:
        from . import egg as egg_mod
        fr = egg_mod.frames(e["egg_idx"])
    elif e:
        from . import data
        fr = data.load_icons().get(e.get("key"))
    if not fr:
        return [" " * IC_W] * IC_ROWS
    return icon_cell(fr[0])


def icon_info(out, icon, info):
    """The selected-item block: icon column + info column, first line bold --
    the ONE layout shared by every icon view."""
    tw = W - IC_W - 2
    for r in range(IC_ROWS):
        tx = info[r] if r < len(info) else ""
        out.append(icon[r] + "  ", style=INK)
        out.append(tx[:tw] + "\n", style=INK_B if r == 0 else INK)

def list_window(out, rows, cursor, vis, fmt, empty=None):
    """The shared scrolling list body: a vis-row window centred on the cursor,
    each row through fmt(item, index), padded with blanks.  Retires seven
    hand-rolled copies (audit 2026-07).  fmt returns a plain label (rendered
    via row() with the ▸ cursor) OR a styled Text owning its whole line incl.
    the newline -- for lists with their own row grammar (digicore EVOLVES).
    Returns the clamped cursor so callers can keep theirs in range."""
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
        lbl = fmt(rows[i], i)
        out.append_text(lbl if isinstance(lbl, Text) else row(lbl, i == cursor))
        shown += 1
    out.append_text(blanks(vis - shown))
    return cursor


def scroll_window(out, rows, off, vis, fmt):
    """list_window's cursor-less cousin: a vis-row window at a raw scroll
    OFFSET (requirement checklists, logs) -- no selection, no centring.  Same
    fmt contract (plain label or a styled whole-line Text).  Returns the
    clamped offset."""
    off = max(0, min(off, max(0, len(rows) - vis)))
    shown = 0
    for i in range(off, min(off + vis, len(rows))):
        lbl = fmt(rows[i], i)
        out.append_text(lbl if isinstance(lbl, Text) else row(lbl))
        shown += 1
    out.append_text(blanks(vis - shown))
    return off


class SubHost:
    """Mixin for panels that host a child panel in `self.sub` (battle inside
    adventure, town inside adventure, battle inside town/cup).  One home for
    the anim-delegate + sfx-bubble seam that was hand-rolled three ways --
    the flee-boss bug lived in exactly this kind of drift (audit 2026-07)."""

    sub = None

    def sub_anim(self):
        """Delegate a frame to the child; bubble its sfx up.  True if handled.
        A child with no anim() (ShopPanel) is simply held -- the host's own
        clock pauses either way (adventure road-keys 2026-07-07)."""
        if self.sub is None:
            return False
        if hasattr(self.sub, "anim"):
            self.sub.anim()
        self.sfx = getattr(self.sub, "sfx", None) or getattr(self, "sfx", None)
        if getattr(self.sub, "sfx", None):
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
