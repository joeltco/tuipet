"""Memorial screen shown when the pet passes away."""
from __future__ import annotations
from . import data, menu, grid, persistence
from .render import render_scene
from .theme import LCD_ON, LCD_BG, DIM, SIL_DAY

COLS, ROWS = 40, 12   # the ONE locked arena: the grave rests in the home scenery
GRAVE = (data.load_effects().get("grave") or [None])[0]


def _age_str(secs):
    """Readable lifespan for the memorial (was raw minutes)."""
    secs = int(max(0, secs))
    d, rem = divmod(secs, 86400)
    h, rem = divmod(rem, 3600)
    m = rem // 60
    if d:
        return f"{d}d {h}h"
    if h:
        return f"{h}h {m}m"
    return f"{m}m"


class DeathPanel:
    def __init__(self, pet, new_mem=None, old_mem=None, hold=0):
        """new_mem: inheritance data the departed just etched (make_digimemory);
        old_mem: data already banked from an earlier generation.  Both present =
        DVPet's 'You can only have one Digimemory' validation -- the trainer
        chooses which generation's data survives.

        hold: canon deading()'s grave beat -- 20 ticks of just the grave with
        the dieLoop sting (x2) before the memorial takes input.  The fresh-
        death path passes 20; without it the save-mash overshoot lands IN the
        memorial (and 'n' starts a new egg unread)."""
        self.pet = pet
        self.new_mem = new_mem
        self.old_mem = old_mem
        self.asking = bool(new_mem and old_mem)
        self._hold = int(hold)
        self.sfx = "error" if hold else None    # soundConfig dieLoop -> error

    def anim(self):
        if self._hold > 0:
            self._hold -= 1
            if self._hold == 10:
                self.sfx = "error"              # canon loops dieLoop twice

    def key(self, k):
        if self._hold > 0:                      # the grave beat absorbs the mash
            return None
        if self.asking:
            if k in ("e", "enter"):                       # etch the new data over the old
                persistence.bank_digimemory(self.new_mem)
                self.asking = False
            elif k in ("k", "escape"):                    # keep the elder's memory
                self.new_mem = None
                self.asking = False
            return None
        if k == "n":
            return ("done", "new")
        if k in ("escape", "enter", "space"):
            return ("done", None)
        return None

    def strip(self):
        """The epitaph + choices ride the strip under the LCD (box-clip audit
        2026-07-04: the in-LCD stack ran 16 lines and everything below the
        grave was clipped off the physical box).  Long lines marquee."""
        p = self.pet
        if self._hold > 0:
            return "…"                             # deading(): just the grave, no keys yet
        if self.asking:
            # setNewDigimemory validation: only one Digimemory may exist
            return (f"One Digimemory only — [b]E[/] etch {p.name}'s data  "
                    f"[b]K[/] keep {self.old_mem.get('name', '?')}'s")
        rip = f"R.I.P. [b]{p.name}[/] · gen {p.generation} · lived {_age_str(p.age_seconds)}"
        if getattr(p, "death_cause", ""):
            rip += f" · of {p.death_cause}"        # what took it (audit 2026-07-05)
        if self.new_mem:
            m = self.new_mem
            rip += f" · etched Va+{m['vaccine']} D+{m['data']} Vi+{m['virus']}"
        return rip + "  [dim]· N new egg  ESC rest[/]"

    def text(self):
        p = self.pet
        if not GRAVE:
            out = menu.bar("MEMORIAL", "")
            out.append_text(menu.note(f"R.I.P.  {p.name}"))
            return out
        # the memorial is a PLACE (audit 2026-07-04): the grave stands grounded
        # in the pet's home scenery, filling the LCD; words ride the strip
        bgimg = p.background()
        on = SIL_DAY if bgimg else LCD_ON
        return render_scene([grid.center(grid.prep(GRAVE, ph=ROWS * 2))],
                            COLS, ROWS, on, LCD_BG, bgimg=bgimg)
