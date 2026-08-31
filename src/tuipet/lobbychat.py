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

# ⛔ THE ONE DEFINITION of the lobby's layout budget (2026-08-13).  The
# 2026-07-17 module split COPIED this block into lobbybout and lobbyscreen
# instead of importing it, so three modules each held their own 25/12/8/400 and
# a later edit to any one of them would have silently missed the other two --
# the widths agree only by luck.  They live here, next to the law and the
# _fit/_wrap helpers that spend them; the other two re-import from this module.
CHATW = 25              # the chat column's OLD width, kept as the budget's unit
ROSTW = 12              # the header's right slot (the old player-box column)
LCDW = CHATW + ROSTW + 1   # 38 — the whole LCD line; the chat owns all of it now
BODY = 9                # chat rows visible at once
DM_BODY = 10            # a DM thread has no status row, so it gets one more
CHAT_MAX = 400          # server MAX_CHAT: the local input buffer stops here too

# ⛔ THE ROSTER LEFT THE LCD (Joel 2026-08-31).  It used to be a 12-cell column
# beside the chat, where three tiers of presence rode on three MARKS -- "°"
# offline, "·" ghost, nothing live.  Joel read that column for a week as a room
# with four people in it; three of them were offline DM threads that the column
# had no room to label.  A mark is not a label.  The roster now lives on the
# STATUS CARD (statusbox.lobby), grouped under words -- IN THE ROOM / ELSEWHERE
# / THREADS -- which is the raid-uncramp move (2026-07-23) applied to the one
# screen that never got it: the numbers live on the card, the LCD plays the room.
# The chat inherits the full 38 cells, the width the retired fold already proved.

# The id an OFFLINE thread-partner carries.  They aren't on the server's
# roster, so they have no connection id -- but they still need a roster row,
# because that row is the only door into a saved conversation (see _others).
# The server reads a pm's `to_name` whenever the id misses, which is exactly
# what this id does, so a message still sends (and queues) to them.
OFFLINE_ID = -1

# The room's default footer lines (menu audit 2026-07-21: the open-room line
# ended in a BARE "· ESC" — the 2026-07-07 fit-fix had dropped its word, and
# on Joel's live screen it read as a run-off).  WHOLE WORDS ONLY, <= 38 cells;
# ↑↓ pick lives on the strip below, so the LCD line doesn't repeat it.  These
# are also the "default status" sentinels _text_lobby rewrites in place.
HINTS_OPEN = "ENTER chat · TAB ranks · ESC leave"


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
                if self.state is not None and not self.state.connected:
                    # the lobby twin's queued note (QOL sweep 2026-07-23)
                    self.status = "Offline — queued, sends on reconnect."
                elif self.state is not None and not any(
                        p.get("name") == self.dm_peer[1] for p in self.state.roster):
                    # THEY'RE away, not us.  The server stores the pm and hands
                    # it over on their next login, but the thread only shows our
                    # own echo -- without this line a reply into an empty room
                    # reads as a message that went nowhere.
                    self.status = f"✉ queued — {self.dm_peer[1]} is offline."
            self.buf = ""
            return None
        if k == "up":
            self.dm_scroll += 1                # older; _text_dm clamps
            return None
        if k == "down":
            self.dm_scroll = max(0, self.dm_scroll - 1)
            return None
        if k == "pageup":
            self.dm_scroll += DM_BODY - 1      # older; _text_dm clamps
            return None
        if k == "pagedown":
            self.dm_scroll = max(0, self.dm_scroll - (DM_BODY - 1))
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
        body = DM_BODY       # the old in-LCD key footer's row, given to the
        #                      history (round 30: the strip already carries
        #                      ENTER send / ESC back -- one hint surface).
        #                      PINNED, not BODY+n: the thread has no status row,
        #                      so its arithmetic is its own (header 1 + 10 + the
        #                      composer 1 = the 12-row LCD exactly)
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
        # CELLS, like the main composer 120 lines down -- this line was the one
        # input in the file still measuring characters, so the cell-width law
        # in the module header held everywhere except the DM box (2026-08-12)
        fw = w - cell_len(label)
        shown = self.buf if cell_len(self.buf) < fw else _tail_cells(self.buf, fw - 1)
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
        """The chat's width -- the WHOLE LCD line since the roster left it."""
        return LCDW
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
        """THE ROOM, full width: identity, the chat, the composer, ONE status
        line.  The roster, the picked tamer's dossier and the action verbs all
        moved to the status card (2026-08-31): this line used to multiplex five
        different jobs and MARQUEE the ones that would not fit, which is how a
        12-key action menu came to scroll past like a news ticker."""
        s = self.state
        t = Text()
        w = LCDW
        mq = getattr(self, "_mq", 0) // 2
        rows = self._chat_rows()
        self.scroll = max(0, min(self.scroll, max(0, len(rows) - BODY)))
        me = (s.me_name if s and s.me_name else None) or "connecting…"
        # header: identity left, the LCD's OWN indicator right -- the room you
        # are in, or how far back you have scrolled.  The head-count moved to
        # the card with the roster (it was the same number said twice).
        # ASCII only in the right slot (the CELL-WIDTH LAW: rjust counts chars)
        worn = data.title_name(persistence.get_title_worn())
        me_line = f"you: {me}" + (f" · ★{worn}" if worn else "")
        room = str(getattr(s, "room", None) or "") if s else ""
        right = (f"▲{self.scroll} back" if self.scroll
                 else (f"/{room}" if room else ""))
        mw = w - ROSTW
        t.append(_fit(marquee(me_line, mw, mq), mw) if cell_len(me_line) > mw
                 else _fit(me_line, mw), style=INK_B)
        t.append(_fit(right.rjust(ROSTW), ROSTW) + "\n", style=INK_B)
        end = len(rows) - self.scroll
        view = rows[max(0, end - BODY):end]
        view = [("", INK)] * (BODY - len(view)) + view
        if not rows:                                       # the empty room
            view[BODY // 2] = ("— say hi, the room hears you —".center(w), DIM)
        for ln, sty in view:
            t.append(_fit(ln, w) + "\n", style=sty)
        if self.pm_to is not None:                           # the input line is a PM compose
            label = f"✉{self.pm_to[1][:8]}: "
        else:
            label = "say: "
        t.append(label, style=INK_B)
        fw = w - cell_len(label)
        shown = self.buf if cell_len(self.buf) < fw else _tail_cells(self.buf, fw - 1)
        caret = "_" if (getattr(self, "_mq", 0) // 5) % 2 == 0 else " "
        t.append(_fit(shown + caret, fw) + "\n", style=INK)
        # THE LAST LINE HAS ONE JOB: say what just happened.  An invite is the
        # one thing allowed to take it -- it is a question the room is asking
        # you right now, and it expires.  (Text.append does not parse markup,
        # so the literal [Y]/[N] brackets are safe here in a way they would
        # NOT be on the status card.)
        clearing = getattr(self, "confirm_clear", None)   # getattr like _mq:
        #     anim()/text() run for half-built rigs too
        if clearing is not None:
            # the room stays on the card behind this, with the doomed row still
            # picked -- you can see exactly what you are about to forget
            ask = f"clear the thread with {clearing[1]}?"
            tail = "  [Y]/[N]"
            t.append(_fit(marquee(ask, w - len(tail), mq) + tail, w)
                     if cell_len(ask) > w - len(tail)
                     else _fit(ask + tail, w), style=INK_B)
        elif self.invite_prompt is not None:
            inv = self.invite_prompt
            blurb = self._pet_of(inv.get("from_id"))
            who = f"{inv.get('from_name', '?')} ({blurb})" if blurb else inv.get("from_name", "?")
            tail = f" invites {inv['kind']}  [Y]/[N]"
            t.append(_fit(marquee(who, w - len(tail), mq) + tail, w), style=INK_B)
        elif self.scroll:
            # scrolled into the log: the line teaches its own way back
            t.append("▲ older — PgUp/PgDn · ESC back to live"[:w], style=DIM)
        else:
            line = self.status
            if line.endswith("…") and ("Connecting" in line or "retry" in line
                                       or "reconnecting" in line or "Retrying" in line):
                # liveness: the static wait line read as a hang (QOL 2026-07-23)
                line = line[:-1] + "." * (1 + (mq // 5) % 3)
            t.append(line[:w], style=DIM)
        return t
