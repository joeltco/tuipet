"""Feed menu — the classic DM20 two-staple feed screen (Meat / Protein).

The real device has exactly two feed options: **Meat** fills the hunger stomach,
**Protein** builds Strength/DP (it never fills, so you can feed it to a full pet).
Any owned bag-foods (bought at the shop) are appended below the two staples.

Picking a food calls Pet.feed(food), which applies the food's full effect set --
hunger / strength / energy / mood / obedience / enthusiasm / nutrition -- each
scaled by DVPet's fullness modifier.  The app plays the eat animation on confirm.
"""
from __future__ import annotations
from . import data, menu
from .theme import INK, INK_B, DIM, ACCENT, POS  # noqa: F401  (theme.apply propagation)
from .render import downsample


def _staples():
    """Meat + Protein, resolved from foods.csv (with safe fallbacks) so the full
    effect fields ride along.  Protein prefers a real strength food."""
    by = {f["name"]: f for f in data.load_foods()}
    meat = dict(by.get("Meat") or {"name": "Meat", "hunger": 1, "mood": 5,
                                    "category": "Meat", "protein": 10})
    src = by.get("Protein") or by.get("Vitamin") or by.get("Supplement") \
        or {"name": "Protein", "hunger": 0, "strength": 1, "category": "None"}
    prot = dict(src)
    prot["name"] = "Protein"
    return [meat, prot]


def _effect_line(food):
    """One terse readout of what a food does (mirrors the DM20 feel)."""
    bits = []
    if int(food.get("hunger", 0)) > 0:
        bits.append(f"hunger +{int(food['hunger'])}")
    if int(food.get("strength", 0)) > 0:
        bits.append(f"strength +{int(food['strength'])}")
    if int(food.get("energy", 0)):
        bits.append(f"DP {int(food['energy']):+d}")
    if int(food.get("mood", 0)):
        bits.append(f"mood {int(food['mood']):+d}")
    return "  ".join(bits) or "a snack"


class FeedPanel:
    def __init__(self, pet):
        self.pet = pet
        self.cursor = 0
        self.frame_i = 0
        self.options = self._options()

    def _options(self):
        """The two staples, then any feedable foods owned in the bag."""
        opts = list(_staples())
        owned = data.load_foods()
        by = {f["name"]: f for f in owned}
        for key, n in self.pet.inventory.items():
            if n <= 0 or not key.startswith("f:"):
                continue
            e = data.consumable_by_key(key)
            f = e and by.get(e.get("name"))
            if f:
                f = dict(f)
                f["key"] = key                       # a bag food is consumed on feed
                f["owned"] = n
                opts.append(f)
        return opts

    def anim(self):
        self.frame_i += 1

    def key(self, k):
        n = len(self.options)
        if k in ("up", "k", "left", "h"):
            self.cursor = (self.cursor - 1) % n
        elif k in ("down", "j", "right", "l"):
            self.cursor = (self.cursor + 1) % n
        elif k in ("enter", "space"):
            food = self.options[self.cursor]
            key = food.get("key")
            if key:                                  # a bag food: must be in stock
                if self.pet.inventory.get(key, 0) <= 0:
                    return None
            msg = self.pet.feed(food)
            fed = self.pet.anim == "eat"
            if fed and key:                          # consume the bag food only on a real bite
                left = self.pet.inventory.get(key, 0) - 1
                if left <= 0:
                    self.pet.inventory.pop(key, None)
                else:
                    self.pet.inventory[key] = left
            return ("done", ("fed" if fed else "full", food, msg))
        elif k in ("escape", "f"):
            return ("done", None)
        return None

    def _icon(self, food):
        key = food.get("key")
        if not key:                                  # staples: Meat=f:0, Protein=f:5 (Vitamin sprite)
            key = "f:0" if food["name"] == "Meat" else "f:5"
        raw = data.load_icons().get(key)
        if not raw:
            return None
        fr = raw[self.frame_i // 4 % len(raw)] if len(raw) > 1 else raw[0]
        return downsample(fr, 2)                     # 24px source -> ~12px

    def text(self):
        p = self.pet
        out = menu.header("FEED", f"hunger {p.hunger}/4  str {p.strength}/4")
        sel = self.options[self.cursor]
        # the selected food's icon + effect readout
        icon = self._icon(sel)
        eff = _effect_line(sel)
        rows = icon or []
        for i in range(3):
            line = rows[i] if i < len(rows) else ""
            from rich.text import Text
            t = Text()
            t.append(("".join("█" if c == "1" else " " for c in line)).ljust(14), style=INK_B)
            if i == 0:
                t.append(sel["name"][:20], style=INK_B)
            elif i == 1:
                t.append(eff[:20], style=INK)
            elif i == 2 and sel.get("owned"):
                t.append(f"x{sel['owned']}", style=DIM)
            t.append("\n")
            out.append_text(t)
        out.append_text(menu.blanks(1))
        # the list
        vis = 3
        lo = max(0, min(self.cursor - vis // 2, len(self.options) - vis))
        shown = 0
        for i in range(lo, min(lo + vis, len(self.options))):
            f = self.options[i]
            tag = f"  x{f['owned']}" if f.get("owned") else ""
            out.append_text(menu.row(f"{f['name']}{tag}", i == self.cursor))
            shown += 1
        out.append_text(menu.blanks(vis - shown))
        out.append_text(menu.footer("↑↓ pick   ENTER feed   ESC out"))
        return out
