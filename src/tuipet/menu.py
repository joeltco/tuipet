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


def row(label, selected=False):
    """A selectable list row with a ▸ cursor; selected rows render inverted."""
    line = (("▸ " if selected else "  ") + label)[:W].ljust(W)
    return Text(line + "\n", style=SEL if selected else INK)


def note(msg):
    """A status line (bold)."""
    return Text(msg[:W] + "\n", style=INK_B)


def footer(hint):
    """Control hints (dim), no trailing newline."""
    return Text(hint[:W], style=DIM)


def blanks(n):
    return Text("\n" * max(0, n), style=INK)
