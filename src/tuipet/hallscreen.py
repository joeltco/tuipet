"""The HALL OF MEMORY — the lineage's own book (Joel 2026-07-26: "build the
hall of memory").

The album remembers SPECIES; nothing remembered the INDIVIDUALS.  Every
retired generation already banks a headstone (persistence.snapshot_prev_gen,
the LEGACY page's data since the 2026-07-14 sweep) — this is the room those
headstones stand in: every elder newest-first, ENTER raises one for its
portrait (the real 16x16 rip bobbing in the home scenery, exactly the album's
detail language) and its epitaph — generation, form, lifespan, what took it,
cups and fights.  A live retire is remembered too: it didn't fall, it walked
to the next egg.

Headstones banked before 2026-07-26 predate the portrait fields (num/cause/
wins) — those elders stand behind the GRAVE glyph and the epitaph says only
what the record knows; nothing here is guessed (the never-fake law).

↑↓ browse, PgUp/PgDn leap, ENTER view, ←→ page inside the book, ESC out.
Opened from the digicore LEGACY page (where the headstones already lived),
the TROPHIES→ALBUM door's exact grammar."""
from __future__ import annotations
from rich.text import Text
from . import data
from . import menu
from . import persistence
from .digicore import _mins
from .theme import INK, INK_B, DIM, LCD_ON, LCD_BG  # noqa: F401  (theme.apply propagation)

VIS = 9                      # list rows shown at once (the album's window)
IMG_W, IMG_H = 40, 16        # detail pixel area (8 character rows)


def _elders():
    """Newest first, like the LEGACY page reads its own rows."""
    try:
        rows = list(persistence.load_settings()
                    .get("progress", {}).get("legacy", []))
    except Exception:
        rows = []
    return list(reversed(rows))


class HallPanel:
    def __init__(self, pet=None):
        self.pet = pet
        self.elders = _elders()
        self.n = len(self.elders)
        self.i = 0
        self.detail = False
        self.frame_i = 0
        self.sfx = None

    # ---- panel protocol --------------------------------------------------
    def anim(self):
        self.frame_i += 1

    def strip(self):
        if self.detail:
            return menu.hints(("←→", "browse"), ("ESC", "back"))
        return menu.hints(("↑↓", "browse"), ("ENTER", "view"),
                          ("ESC", "out"))

    def key(self, k):
        if not self.n:
            if k in ("escape", "enter", "space"):
                return ("done", None)
            return None
        if self.detail:
            if k in ("left", "h", "up", "k"):
                self.i = (self.i - 1) % self.n
            elif k in ("right", "l", "down", "j"):
                self.i = (self.i + 1) % self.n
            elif k == "pageup":
                self.i = (self.i - (VIS - 1)) % self.n
            elif k == "pagedown":
                self.i = (self.i + (VIS - 1)) % self.n
            elif k == "escape":
                self.detail = False
            return None
        if k in ("up", "k"):                 # the list wraps (the album law)
            self.i = (self.i - 1) % self.n
        elif k in ("down", "j"):
            self.i = (self.i + 1) % self.n
        elif k == "pageup":
            self.i = max(0, self.i - (VIS - 1))
        elif k == "pagedown":
            self.i = min(self.n - 1, self.i + (VIS - 1))
        elif k in ("enter", "space"):
            self.detail = True
        elif k == "escape":
            return ("done", None)
        return None

    # ---- the list ----------------------------------------------------------
    def _epitaph(self, r):
        """One elder's line: lifespan, then its fate — a fallen elder names
        what took it (when the record knows), a retired one walked on."""
        age = _mins(float(r.get("age", 0.0)))
        if r.get("dead"):
            cause = str(r.get("cause", "") or "")
            fate = f"fell of {cause}" if cause else "fell"
        else:
            fate = "walked to the next egg"
        extra = ""
        cups, wins = int(r.get("cups", 0)), int(r.get("wins", -1))
        if cups:
            extra += f" · {cups} cup{'s' if cups != 1 else ''}"
        if wins > 0:
            extra += f" · {wins} wins"
        return f"lived {age} · {fate}{extra}"

    def _list_scene(self):
        # (plural, 2026-08-04: the header read "1 elders" -- caught in the
        #  smoke launch when the new HALL CARD beside it said "1 elder")
        out = menu.header("HALL OF MEMORY",
                          f"{self.n} elder{'' if self.n == 1 else 's'}"
                          if self.n else "")

        def fmt(r, j):
            cur = j == self.i
            body = INK_B if cur else INK
            t = Text()
            t.append(("▸" if cur else " ")
                     + ("†" if r.get("dead") else "·") + " ", style=body)
            t.append(f"{str(r.get('name', '?'))[:20]:<21}", style=body)
            tag = f"g{r.get('gen', '?')} {str(r.get('stage', ''))[:11]}"
            t.append(f"{tag[:15]:>15}\n", style=INK_B if cur else DIM)
            return t

        self.i = menu.list_window(out, self.elders, self.i, VIS, fmt,
                                  empty="no elders rest here yet")
        note = (self._epitaph(self.elders[self.i]) if self.n
                else "this pet is writing generation one")
        out.append_text(menu.note(note, tick=self.frame_i))
        out.right_crop(1)     # keys ride the strip (the egg-guide law)
        return out

    # ---- one elder's page ----------------------------------------------------
    def _portrait_rows(self, r):
        """The elder's form bobbing, when the record knows it — headstones
        from before the portrait fields stand behind the grave instead."""
        num = int(r.get("num", 0) or 0)
        if num and data.load_sprites()[1].get(num):
            return data.bob_frame(num, self.frame_i) or []
        return (data.load_effects().get("grave") or [[]])[0] or []

    def _detail_scene(self):
        r = self.elders[self.i]
        name = str(r.get("name", "?"))
        out = menu.header(f"MEMORY  {name[:20].upper()}",
                          f"g{r.get('gen', '?')}")
        rows = self._portrait_rows(r)
        buf = [[0] * IMG_W for _ in range(IMG_H)]
        w = max((len(row) for row in rows), default=0)
        ox, oy = (IMG_W - w) // 2, (IMG_H - len(rows)) // 2
        for y, line in enumerate(rows):
            for x, ch in enumerate(line):
                if ch == "1" and 0 <= oy + y < IMG_H and 0 <= ox + x < IMG_W:
                    buf[oy + y][ox + x] = 1
        bt = Text()
        for cy in range(IMG_H // 2):
            ty, byy = cy * 2, cy * 2 + 1
            for cx in range(IMG_W):
                tc = LCD_ON if buf[ty][cx] else LCD_BG
                bc = LCD_ON if buf[byy][cx] else LCD_BG
                bt.append("▀", style=f"{tc} on {bc}")
            bt.append("\n")
        out.append_text(bt)
        stage = str(r.get("stage", "") or "")
        info = (f"{stage} · " if stage else "") + self._epitaph(r)
        out.append_text(menu.note(info, tick=self.frame_i))
        out.right_crop(1)     # keys ride the strip (the egg-guide law)
        return out

    def text(self):
        return self._detail_scene() if self.detail and self.n else self._list_scene()
