"""Memorial screen shown when the pet passes away."""
from __future__ import annotations
from . import data, menu, grid, persistence
from .theme import LCD_ON, LCD_BG, DIM, SIL_SCENE  # noqa: F401  (palette names bound for theme.apply propagation)

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
    def __init__(self, pet, new_mem=None, old_mem=None, hold=0, grade_kept=0,
                 banked_new=False):
        """new_mem: inheritance data the departed CAN etch (make_digimemory);
        old_mem: data already banked from an earlier generation.

        Canon's DigiMemory_Validation is a real Yes/No (digimemory audit
        2026-07-06): declining the etch keeps the care bonus for the heir --
        grade_kept is that path's seed (the app pre-banked the etch default;
        B re-banks the kept grade and, when banked_new, un-banks the memory).
        After an etch with old data standing, the only-one prompt picks which
        generation's data survives (the tuipet agency over canon's silent
        overwrite, kept from the earlier arc).

        hold: canon deading()'s grave beat -- 20 ticks of just the grave with
        the dieLoop sting (x2) before the memorial takes input.  The fresh-
        death path passes 20; without it the save-mash overshoot lands IN the
        memorial (and 'n' starts a new egg unread)."""
        self.pet = pet
        self.new_mem = new_mem
        self.old_mem = old_mem
        self.grade_kept = int(grade_kept)
        self.banked_new = bool(banked_new)
        self.ask_etch = bool(new_mem)           # DigiMemory_Validation: etch or carry?
        self.asking = False                     # the only-one prompt, after an etch
        self._hold = int(hold)
        self.sfx = "error" if hold else None    # soundConfig dieLoop -> error

    def anim(self):
        self._mq = getattr(self, "_mq", 0) + 1  # drives the strip field marquee
        if self._hold > 0:
            self._hold -= 1
            if self._hold == 10:
                self.sfx = "error"              # canon loops dieLoop twice

    def key(self, k):
        if self._hold > 0:                      # the grave beat absorbs the mash
            return None
        if self.ask_etch:
            if k in ("e", "enter"):                       # Yes: etch the data
                self.ask_etch = False
                if self.old_mem:                          # ...old data standing ->
                    self.asking = True                    # the only-one prompt
            elif k in ("b", "escape"):                    # No: the bonus carries instead
                persistence.bank_bonus_seed(self.grade_kept)
                if self.banked_new:                       # un-bank the etch default
                    persistence.take_digimemory()
                self.new_mem = None
                self.ask_etch = False
            return None
        if self.asking:
            if k in ("e", "enter"):                       # etch the new data over the old
                persistence.bank_digimemory(self.new_mem)
                self.asking = False
            elif k in ("k", "escape"):                    # keep the elder's memory
                # the etch has nowhere to live, so the bonus CARRIES instead,
                # exactly like B at the first prompt -- E-then-K used to
                # discard new_mem AND leave the lower spent-path seed banked,
                # a strict loss vs pressing B (SUSPECT S3 ruling 2026-07-20)
                persistence.bank_bonus_seed(self.grade_kept)
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
        # every state is budgeted to HUD_W 40 (menu-bounds audit 2026-07-07):
        # long fields marquee via render.marquee; the KEY HINTS stand still
        # (the old one-line epitaph ran to ~68 wide and the whole strip slid,
        # hints included)
        from .render import marquee
        mq = getattr(self, "_mq", 0) // 2
        if self.ask_etch:
            # DigiMemory_Validation: etch the data, or carry the care bonus
            return (f"[b]E[/] etch {marquee(p.name, 10, mq)}'s data · "
                    f"[b]B[/] bonus +{self.grade_kept}")
        if self.asking:
            # setNewDigimemory validation: only one Digimemory may exist
            return (f"Only one: [b]E[/] {marquee(p.name, 10, mq)} · "
                    f"[b]K[/] {marquee(self.old_mem.get('name', '?'), 10, mq)}")
        rip = f"R.I.P. {p.name} · gen {p.generation} · lived {_age_str(p.age_seconds)}"
        if getattr(p, "death_cause", ""):
            rip += f" · of {p.death_cause}"        # what took it (audit 2026-07-05)
        if self.new_mem:
            m = self.new_mem
            rip += f" · etched Va+{m['vaccine']} D+{m['data']} Vi+{m['virus']}"
        return f"[b]{marquee(rip, 22, mq)}[/] [dim]· N new egg · ESC[/]"

    def text(self):
        p = self.pet
        if not GRAVE:
            out = menu.bar("MEMORIAL", "")
            out.append_text(menu.note(f"R.I.P.  {p.name}"))
            return out
        # the memorial is a PLACE (audit 2026-07-04): the grave stands grounded
        # in the pet's home scenery, filling the LCD; words ride the strip
        return menu.paint([grid.center(grid.prep(GRAVE, ph=ROWS * 2))],
                          p.background(), rows=ROWS, cols=COLS)
