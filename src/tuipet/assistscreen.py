"""AI Assistant — the auto-care contract (DVPet's Set_AutoCare validation page).

DVPet reaches it from the Praise/Scold screen's option button; tuipet's flat
key map gives it its own key.  Content mirrors drawAutoCareValidation: the
"AI Assistant" card with "{hour}/hour" (only when the stage bills a retainer)
and "{care}/care" for the CURRENT stage, plus the on/off switch.
"""
from __future__ import annotations
from . import data, menu
from .theme import LCD_ON, LCD_BG, INK, INK_B, DIM, SEL, POS, NEG  # noqa: F401  (palette names bound for theme.apply propagation)
from .pet import AUTO_CARE_VISIT_PRICE, AUTO_CARE_HOUR_PRICE


class AssistPanel:
    def __init__(self, pet):
        self.pet = pet
        self.msg = "A helper minds the pet, for a fee."
        self._fresh = False       # a toggle happened THIS visit: its verdict
        #                           rides home on ESC (round 32)

    def strip(self):
        on = getattr(self.pet, "auto_care", False)
        return menu.hints(("ENTER", "dismiss helper" if on else "hire helper"),
                          ("ESC", "out"))

    def anim(self):
        # a frame heartbeat so the app repaints at 10 Hz and an
        # over-wide menu.note can actually SCROLL (marquee sweep
        # 2026-07-15) -- this panel had no animation of its own
        pass

    def key(self, k):
        if k in ("enter", "space"):
            self.msg = self.pet.set_auto_care(not self.pet.auto_care)
            self._fresh = True
        elif k in ("escape", "v"):
            # only a verdict EARNED this visit rides home -- the standing
            # blurb is not news (round 32; the app flashes what it gets)
            return ("done", self.msg if self._fresh else None)
        return None

    def text(self):
        p = self.pet
        out = menu.header("AI ASSISTANT", f"{p.bits}b")
        hour = AUTO_CARE_HOUR_PRICE.get(p.stage, 0)
        care = AUTO_CARE_VISIT_PRICE.get(p.stage, 0)
        if hour > 0:
            out.append(f"  {hour}b/hour\n", style=INK)
        out.append(f"  {care}b/care\n", style=INK)
        if p.auto_care:
            _, by_num = data.load_sprites()
            name = (by_num.get(p.assistant_num) or {}).get("name", "A helper")
            out.append(f"  ON — {name} is on duty\n", style=INK_B)
        else:
            out.append("  OFF\n", style=DIM)
        # the whole contract, quit clause included (round 32: the helper
        # walks off duty the moment it can't cover the retainer or the
        # next visit -- the card must say so up front, not just the
        # after-the-fact quit note)
        out.append("\n  Cleans, feeds a starving or\n"
                   "  drained pet, dims the lights.\n"
                   "  Each visit costs bits — the\n"
                   "  helper quits if they run dry.\n", style=DIM)
        out.append_text(menu.note(self.msg))
        # keys ride the strip (round 32: the footer doubled them)
        return out
