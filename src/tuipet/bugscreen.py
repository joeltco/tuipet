"""Bug report — type what went wrong; it's sent to the lobby server so the dev
can read it and fix it (Joel 2026-07-09).  A one-shot submit that needs no lobby
login; if the network's down the app stashes it and retries next launch."""
from __future__ import annotations
from . import menu
from .theme import INK, INK_B, DIM  # noqa: F401  (palette names bound for theme.apply propagation)

MAXLEN = 1000          # a bug report is a sentence or two, not an essay
BODY_W = 38            # the LCD box's writable width
VIEW_ROWS = 6          # wrapped lines shown (the box is ~12 rows total)


def wrap(s, w):
    """Word-wrap into <=w-wide lines, hard-splitting any over-long token."""
    out, line = [], ""
    for word in s.split(" "):
        while len(word) > w:                       # a pasted URL etc.
            if line:
                out.append(line); line = ""
            out.append(word[:w]); word = word[w:]
        if line and len(line) + 1 + len(word) > w:
            out.append(line); line = word
        else:
            line = (line + " " + word) if line else word
    out.append(line)
    return out


class BugReportPanel(menu.SubHost):
    def __init__(self, pet):
        self.pet = pet
        self.buf = ""
        self.frame_i = 0
        self.captures_text = True         # typing wins over the global q-quit
        self.msg = "What went wrong? It goes to the dev."
        self.sub = None

    def anim(self):
        if self.sub_anim():
            return
        self.frame_i += 1

    def strip(self):
        return "[dim]to the dev —[/] " + \
            menu.hints(("ENTER", "send"), ("ESC", "cancel"))

    def key(self, k):
        if k == "escape":
            return ("done", None)
        if k == "enter":
            text = self.buf.strip()
            if not text:
                self.msg = "Type the bug first — or ESC to cancel."
                self.sfx = "error"
                return None
            return ("done", ("bug", text))
        if k == "backspace":
            self.buf = self.buf[:-1]
        elif k == "space":
            self.buf += " "
        elif len(k) == 1 and k.isprintable():
            self.buf += k
        self.buf = self.buf[:MAXLEN]
        return None

    def text(self):
        out = menu.header("REPORT A BUG", "%d/%d" % (len(self.buf), MAXLEN))
        lines = wrap(self.buf, BODY_W) if self.buf else [""]
        caret = "_" if (self.frame_i // 5) % 2 == 0 else " "
        lines[-1] = (lines[-1] + caret)[:BODY_W]
        view = lines[-VIEW_ROWS:]
        view = view + [""] * (VIEW_ROWS - len(view))    # pad to a steady box
        for ln in view:
            out.append(ln + "\n", style=INK if self.buf else DIM)
        out.append_text(menu.note(self.msg, tick=self.frame_i))
        out.append_text(menu.footer("type  ENTER send  ESC cancel"))
        return out
