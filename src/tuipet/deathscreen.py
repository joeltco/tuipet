"""Memorial screen shown when the pet passes away."""
from __future__ import annotations
from . import data, menu, grid, persistence
from .theme import LCD_ON, LCD_BG, DIM, SIL_DAY  # noqa: F401  (palette names bound for theme.apply propagation)

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
    def __init__(self, pet, hold=20, **_legacy):
        """hold: the grave beat -- 20 ticks of just the grave with the die
        sting before the memorial takes input (a save-mash overshoot used to
        land IN the memorial and 'n' started a new egg unread)."""
        self.pet = pet
        self._hold = int(hold)
        self.sfx = "error" if hold else None

    def anim(self):
        self._mq = getattr(self, "_mq", 0) + 1  # drives the strip field marquee
        if self._hold > 0:
            self._hold -= 1
            if self._hold == 10:
                self.sfx = "error"              # the die sting loops twice

    def key(self, k):
        if self._hold > 0:                      # the grave beat absorbs the mash
            return None
        if k == "n":
            return ("done", "new")
        if k in ("escape", "enter", "space"):
            return ("done", None)
        return None

    def strip(self):
        """The epitaph + choices ride the strip under the LCD."""
        p = self.pet
        if self._hold > 0:
            return "…"                             # just the grave, no keys yet
        from .render import marquee
        mq = getattr(self, "_mq", 0) // 2
        rip = (f"R.I.P. {p.name} · gen {p.generation} · "
               f"day {p.age_days}")
        if getattr(p, "death_cause", ""):
            rip += f" · of {p.death_cause}"
        if p.inventory.get("revive_floppy"):
            rip += " · a revive floppy waits in the bag (i)"
        return f"[b]{marquee(rip, 22, mq)}[/] [dim]· N new egg · ESC[/]"

    def text(self):
        p = self.pet
        if not GRAVE:
            out = menu.bar("MEMORIAL", "")
            out.append_text(menu.note(f"R.I.P.  {p.name}"))
            return out
        # the memorial is a PLACE: the grave stands grounded in the pet's
        # home scenery; words ride the strip
        return menu.paint([grid.center(grid.prep(GRAVE, ph=ROWS * 2))],
                          p.background(), rows=ROWS, cols=COLS)
