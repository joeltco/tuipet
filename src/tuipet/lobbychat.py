"""The lobby's CHAT surface — cell-width helpers, the log, DMs and
slash commands, as a mixin over LobbyPanel's state (modularize
2026-07-17: "the lobby too").  THE CELL-WIDTH LAW lives here: the
lobby is the one place a player types arbitrary text, and emoji/CJK
glyphs are two cells wide — every width decision goes through
cell_len/set_cell_size/chop_cells.
"""
from __future__ import annotations


from rich.cells import cell_len, chop_cells, set_cell_size  # noqa: F401
from rich.text import Text  # noqa: F401

from . import data  # noqa: F401
from . import jogress  # noqa: F401
from . import battle  # noqa: F401
from . import battlescreen  # noqa: F401
from . import jogressscreen  # noqa: F401
from . import menu  # noqa: F401
from . import persistence  # noqa: F401
from .net import ANNOUNCE, CHAT_CAP  # noqa: F401
from .render import marquee  # noqa: F401
from .theme import INK, INK_B, DIM, SEL  # noqa: F401  (theme.apply propagation)

CHATW = 25
ROSTW = 12
BODY = 8
CHAT_MAX = 400          # server MAX_CHAT: the local input buffer stops here too


def _fit(s, w):
    """Pad or truncate to exactly `w` DISPLAY CELLS (never characters)."""
    return set_cell_size(str(s), w)


def _wrap(s, w):
    """Word-wrap `s` into lines of <= w CELLS, hard-splitting any over-long word.
    A wide glyph is never split down the middle -- chop_cells keeps it whole."""
    out, line = [], ""
    for word in str(s).split(" "):
        while cell_len(word) > w:
            if line:
                out.append(line); line = ""
            chunks = chop_cells(word, w)
            out.append(chunks[0])
            word = "".join(chunks[1:])
        if not line:
            line = word
        elif cell_len(line) + 1 + cell_len(word) <= w:
            line += " " + word
        else:
            out.append(line); line = word
    if line:
        out.append(line)
    return out or [""]


def _tail_cells(s, w):
    """The LAST `w` cells of `s` -- the input line scrolls as you type, and a
    character-based slice let a typed emoji run past the frame."""
    while cell_len(s) > w:
        s = s[1:]
    return s


def _hpbar(hp, mx, w=10):
    fill = max(0, min(w, round(hp / mx * w))) if mx else 0
    return "█" * fill + "─" * (w - fill)


class ChatMixin:
    def _save_dms(self):
        """Persist the DM threads + unread badges (leaving must not lose them)."""
        if self.state is not None:
            from . import persistence
            persistence.save_dms(self.state.dms, self.state.unread)
    def _key_dm(self, k):
        """Private thread with one peer: type + Enter sends, Esc back to the
        lobby.  The thread scrolls like the lobby log (grammar sweep
        2026-07-18: 'thread saved' was true but everything above the window
        was unreadable) — ↑↓ a line, PgUp/PgDn a page, sending snaps live."""
        if k == "escape":
            if self.dm_scroll:                 # scrolled thread: snap live first
                self.dm_scroll = 0
                return None
            self.phase, self.buf = "lobby", ""
            self._save_dms()                   # the conversation stays
            return None
        if k == "enter":
            self.dm_scroll = 0                 # speaking snaps the view live
            if self.buf.strip() and self.dm_peer and self.client:
                self.client.pm(self.dm_peer[0], self.buf.strip(), self.dm_peer[1])
            self.buf = ""
            return None
        if k == "up":
            self.dm_scroll += 1                # older; _text_dm clamps
            return None
        if k == "down":
            self.dm_scroll = max(0, self.dm_scroll - 1)
            return None
        if k == "pageup":
            self.dm_scroll += BODY - 1         # older; _text_dm clamps
            return None
        if k == "pagedown":
            self.dm_scroll = max(0, self.dm_scroll - (BODY - 1))
            return None
        return self._edit(k)
    def _text_dm(self):
        s = self.state
        peer = self.dm_peer[1] if self.dm_peer else "?"
        me = (s.me_name or "you") if s else "you"
        w = CHATW + ROSTW + 1
        t = Text()
        t.append(_fit(f"✉ {peer}", w) + "\n", style=INK_B)
        rows = []
        for frm, tx in (s.dms.get(peer, []) if s else []):
            mine = frm == me
            who = "you" if mine else frm
            parts = _wrap(f"{who}: {tx}", w - 1)
            rows.append((parts[0], DIM if mine else INK_B))
            rows.extend((" " + ln, DIM if mine else INK_B) for ln in parts[1:])
        body = BODY + 2      # the old in-LCD key footer's row, given to the
        #                      history (round 30: the strip already carries
        #                      ENTER send / ESC back -- one hint surface)
        # clamp the scrollback to the log, like _text_lobby does for the room
        self.dm_scroll = max(0, min(self.dm_scroll, max(0, len(rows) - body)))
        self._dm_overflow = len(rows) > body         # strip(): advertise PgUp
        end = len(rows) - self.dm_scroll
        view = rows[max(0, end - body):end]
        view = [("", INK)] * (body - len(view)) + view
        if not rows:
            view[body // 2] = ("— no messages yet — say hi —"[:w], DIM)
        for ln, sty in view:
            t.append(_fit(ln, w) + "\n", style=sty)
        label = f"→{peer[:8]}: "
        fw = w - len(label)
        shown = self.buf if len(self.buf) < fw else self.buf[-(fw - 1):]
        caret = "_" if (getattr(self, "_mq", 0) // 5) % 2 == 0 else " "
        t.append(label, style=INK_B)
        t.append(_fit(shown + caret, fw), style=INK)
        return t
    def _slash(self, txt):
        """Chat slash commands (password rooms 2026-07-14): `/room <phrase>`
        joins the private room for that phrase — everyone typing the same
        phrase meets there (the phrase IS the password, DSprite-style 🔒);
        `/leave` returns to the main lobby.  Anything else prints the help."""
        cmd, _, arg = txt.partition(" ")
        cmd, arg = cmd.lower(), arg.strip()
        if cmd == "/room" and arg:
            self.client.room(arg)
            self.status = "Joining the room…"
        elif cmd == "/room":
            room = getattr(self.state, "room", None) if self.state else None
            self.status = f"room: {room} · /leave exits" if room else "main lobby · /room <phrase>"
        elif cmd in ("/leave", "/lobby"):
            self.client.room("")
            self.status = "Back to the main lobby…"
        else:
            self.status = "Commands: /room <phrase> · /leave"
    def _chat_w(self):
        """The chat column's width: the folded player box cedes its columns."""
        return CHATW + ROSTW + 1 if self.rost_hidden else CHATW
    def _chat_rows(self):
        """The wrapped history as (line, style) rows, oldest first -- one
        style per MESSAGE (chat polish 2026-07-07): your own lines dim (you
        know what you said), PMs and lines that mention your name bright,
        join/leave notices dim; wrap continuations hang a 1-col indent so a
        long message reads as ONE message, not three."""
        s = self.state
        me = (s.me_name or "") if s else ""
        cw = self._chat_w()
        rows = []
        for nm, tx in (s.chat if s else []):
            if not nm:                                     # join/leave notice
                sty, parts = DIM, _wrap(f"· {tx}", cw - 1)
            elif str(nm) == ANNOUNCE:
                # the dev's line -- a new release, a heads-up -- used to render in
                # plain INK as "📢: text", i.e. indistinguishable from chatter and
                # reading like a PLAYER NAMED 📢 was talking.  It is the loudest
                # thing in the room: bright, and no name-colon (chat polish 07-14)
                sty, parts = INK_B, _wrap(f"{ANNOUNCE} {tx}", cw - 1)
            else:
                pm = str(nm).startswith("✉")
                mine = bool(me) and (nm == me or str(nm).startswith("✉→"))
                mention = bool(me) and me.lower() in str(tx).lower()
                # mine first: my own echo (chat or ✉→ PM) always reads dim
                sty = DIM if mine else (INK_B if (pm or mention) else INK)
                parts = _wrap(f"{nm}: {tx}", cw - 1)
            rows.append((parts[0], sty))
            rows.extend((" " + ln, sty) for ln in parts[1:])
        return rows
    def _text_lobby(self):
        s = self.state
        others = self._others()
        online = len(s.roster) if s else 0
        me = (s.me_name if s and s.me_name else None) or "connecting…"
        t = Text()
        cw = self._chat_w()
        rows = self._chat_rows()
        self.scroll = max(0, min(self.scroll, max(0, len(rows) - BODY)))
        # ASCII only in this column (the CELL-WIDTH LAW: rjust counts chars)
        in_room = bool(s and getattr(s, "room", None))
        right = (f"▲{self.scroll} back" if self.scroll
                 else (f"{online} in room" if in_room else f"{online} on"))
        # header: identity + the live/scroll marker (folded: no divider column)
        # -- your OWN worn honor shows here (read locally, so it's right even
        # before the roster syncs); a long title marquees, the chrome holds
        worn = data.title_name(persistence.get_title_worn())
        me_line = f"you: {me}" + (f" · ★{worn}" if worn else "")
        mw = cw - ROSTW if self.rost_hidden else CHATW
        mq = getattr(self, "_mq", 0) // 2
        t.append(_fit(marquee(me_line, mw, mq), mw) if cell_len(me_line) > mw
                 else _fit(me_line, mw), style=INK_B)        # confirm your identity
        if not self.rost_hidden:
            t.append("│", style=DIM)
        t.append(right.rjust(ROSTW)[:ROSTW] + "\n", style=INK_B)
        end = len(rows) - self.scroll
        view = rows[max(0, end - BODY):end]
        view = [("", INK)] * (BODY - len(view)) + view
        if not rows:                                       # the empty room
            hint = "— say hi, the room hears you —"
            if cell_len(hint) > cw:                        # folded col fits it; narrow one doesn't
                hint = "— say hi —"
            view[BODY // 2] = (hint.center(cw), DIM)
        sel = min(self.sel, len(others) - 1) if others else 0
        rlo = max(0, min(sel - BODY // 2, len(others) - BODY)) if len(others) > BODY else 0
        for i in range(BODY):
            t.append(_fit(view[i][0], cw), style=view[i][1])
            if self.rost_hidden:                 # the box is folded: chat owns the row
                t.append("\n")
                continue
            t.append("│", style=DIM)
            ridx = rlo + i
            if ridx < len(others):
                pl = others[ridx]
                cur = ridx == sel
                ghost = not pl.get("live", True)     # playing, not in the room
                nm = pl["name"]
                unread = bool(s) and nm in s.unread
                blk = bool(s) and nm in s.blocked
                mark = "✉" if unread else ("✕" if blk else ("·" if ghost else ""))
                sty = SEL if cur else (INK_B if unread else (DIM if (ghost or blk) else INK))
                # a worn honor stars the roster entry -- the room sees who's
                # titled at a glance; an entry too long for the column
                # MARQUEES (field-scroll doctrine) so the star is never lost.
                # marquee is char-based; the _fit wrapper keeps wide glyphs
                # (emoji names) inside the column per the cell-width law
                star = " ★" if (pl.get("pet") or {}).get("title") else ""
                pre, label = (">" if cur else " "), mark + nm + star
                if cell_len(pre + label) > ROSTW:
                    label = marquee(label, ROSTW - 1, getattr(self, "_mq", 0) // 2)
                t.append(_fit(pre + label, ROSTW), style=sty)
            elif i == 0 and not others:
                t.append(_fit(" nobody yet", ROSTW), style=DIM)
            else:
                t.append(_fit("", ROSTW), style=INK)
            t.append("\n")
        if self.pm_to is not None:                           # the input line is a PM compose
            label = f"✉{self.pm_to[1][:8]}: "
        else:
            label = "say: "
        t.append(label, style=INK_B)
        fw = CHATW + ROSTW - cell_len(label)
        shown = self.buf if cell_len(self.buf) < fw else _tail_cells(self.buf, fw - 1)
        caret = "_" if (getattr(self, "_mq", 0) // 5) % 2 == 0 else " "
        t.append(_fit(shown + caret, fw) + "\n", style=INK)
        # the prompt lines: the KEY HINTS are fixed chrome and must never clip
        # off the end -- a 24-char name used to push [Y]/[N] and [Esc] out of
        # the 38-col line entirely (lobby audit 2026-07-07); the NAME field
        # marquees instead (the v0.2.349 field-scroll doctrine)
        w = CHATW + ROSTW + 1
        mq = self._mq // 2 if hasattr(self, "_mq") else 0
        if self.invite_prompt is not None:
            inv = self.invite_prompt
            blurb = self._pet_of(inv.get("from_id"))
            who = f"{inv.get('from_name', '?')} ({blurb})" if blurb else inv.get("from_name", "?")
            tail = f" invites {inv['kind']}  [Y]/[N]"
            t.append(_fit(marquee(who, w - len(tail), mq) + tail, w), style=INK_B)
        elif self.action_for is not None:
            pid, pname, plive = self.action_for
            blurb = self._pet_of(pid)
            who = f"{pname} ({blurb})" if blurb else pname
            if self.state and pname in self.state.blocked:
                acts = "[X]unblock  [ESC]"
            elif plive:
                acts = "[B]attle [J]og [V] DM [M] PM [X]block [ESC]"
            else:
                acts = "not in lobby — [P]ing [V] DM [M] PM [X]block [ESC]"
            full = f"{who}:  {acts}"
            # whole line scrolls when it overflows (Joel 2026-07-09), else static
            t.append(marquee(full, w, mq) if len(full) > w else _fit(full, w), style=INK_B)
        elif self.scroll:
            # scrolled into the log: the line teaches its own way back
            t.append("▲ older — PgUp/PgDn · ESC back to live"[:w], style=DIM)
        else:
            line = self.status
            if self.rost_hidden and line.startswith("↑↓ pick"):
                # the box is folded: ↑↓ drive the log now, not the roster pick
                line = "↑↓ scroll · ← player box · Esc leave"
            elif others and line.startswith("↑↓ pick"):
                p = others[sel]
                if p.get("live", True):
                    blurb = self._pet_of(p["id"])
                    if blurb:
                        tail = " — Enter to act"
                        line = marquee(f"{p['name']}: {blurb}", w - len(tail), mq) + tail
                else:
                    tail = " — Enter to msg"
                    line = marquee(f"{p['name']} is playing", w - len(tail), mq) + tail
            t.append(line[:w], style=DIM)
        return t
