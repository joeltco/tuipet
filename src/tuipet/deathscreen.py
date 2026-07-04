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
    def __init__(self, pet, new_mem=None, old_mem=None):
        """new_mem: inheritance data the departed just etched (make_digimemory);
        old_mem: data already banked from an earlier generation.  Both present =
        DVPet's 'You can only have one Digimemory' validation -- the trainer
        chooses which generation's data survives."""
        self.pet = pet
        self.new_mem = new_mem
        self.old_mem = old_mem
        self.asking = bool(new_mem and old_mem)

    def key(self, k):
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

    def _mem_line(self, out):
        if self.new_mem:
            m = self.new_mem
            out.append(f"Inheritance data etched:  Va+{m['vaccine']} | "
                       f"D+{m['data']} | Vi+{m['virus']}\n", style=DIM)

    def text(self):
        p = self.pet
        out = menu.bar("MEMORIAL", "")
        if GRAVE:
            # the memorial is a PLACE too (audit 2026-07-04): the grave stands
            # grounded in the pet's home scenery, not on a bare pale strip
            bgimg = p.background()
            on = SIL_DAY if bgimg else LCD_ON
            out.append_text(render_scene([grid.center(grid.prep(GRAVE, ph=ROWS * 2))],
                                         COLS, ROWS, on, LCD_BG, bgimg=bgimg))
            out.append("\n")
        out.append_text(menu.note(f"R.I.P.  {p.name}"))
        out.append(f"gen {p.generation}  ·  lived {_age_str(p.age_seconds)}  ·  {p.stage}\n", style=DIM)
        if self.asking:
            # setNewDigimemory validation: only one Digimemory may exist
            out.append(f"You can only have one Digimemory.\n", style=DIM)
            out.append_text(menu.footer(f"E  etch {p.name}'s data      K  keep {self.old_mem.get('name', '?')}'s"))
            return out
        self._mem_line(out)
        out.append_text(menu.footer("N  a new egg      ESC  let it rest"))
        return out
