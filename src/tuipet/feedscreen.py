"""Feed menu — DVPet's Food_Inventory page, driven ENTIRELY by foods.csv.

DVPet's FEED button lists the foods you OWN.  What you own is in the data:
each food's StartingQuantity seeds it (Meat/Fish/Fruit/Vegetable start at 99),
CanDec=false means eating never depletes it (those four are the infinite
staples), and everything else starts at 0 and is bought at the shop, consumed
per bite (Consumable.decQuantity).  ShowInInventory=false foods (Med, Vitamin)
belong to the heal flows and never appear here.

Picking a food calls Pet.feed(food) -- the full applyFood effect set -- and the
app plays the eat animation with that food's real icon.
"""
from __future__ import annotations
from . import data, menu
from .theme import INK, INK_B, DIM, ACCENT, POS  # noqa: F401  (theme.apply propagation)


def food_qty(pet, food):
    """DVPet Consumable quantity: a CanDec=false food is pinned at its
    StartingQuantity (never eaten down); a normal food is whatever the bag holds."""
    if not food.get("can_dec"):
        return int(food.get("start", 0))
    return pet.inventory.get(food["key"], 0)


def feedable(pet):
    """The Food_Inventory listing: ShowInInventory foods you own, csv order."""
    return [f for f in data.load_foods() if f.get("show") and food_qty(pet, f) > 0]


def _effect_line(food):
    """One terse readout of what a food does."""
    bits = []
    if int(food.get("hunger", 0)) > 0:
        bits.append(f"hunger +{int(food['hunger'])}")
    if int(food.get("strength", 0)) > 0:
        # a strength food also banks +1 DP toward a jogress (Pen20 meter) --
        # unlabelled, protein's whole point was invisible (audit 2026-07-04)
        bits.append(f"strength +{int(food['strength'])} DP+1")
    if int(food.get("energy", 0)):
        bits.append(f"energy {int(food['energy']):+d}")
    if int(food.get("mood", 0)):
        bits.append(f"mood {int(food['mood']):+d}")
    return "  ".join(bits) or "a snack"


class FeedPanel:
    def __init__(self, pet):
        self.pet = pet
        self.cursor = 0
        self.frame_i = 0
        self.options = feedable(pet)

    def anim(self):
        self.frame_i += 1

    def key(self, k):
        n = len(self.options)
        if not n:
            if k in ("escape", "enter", "space", "f"):
                return ("done", None)
            return None
        if k in ("up", "k"):
            self.cursor = (self.cursor - 1) % n
        elif k in ("down", "j"):
            self.cursor = (self.cursor + 1) % n
        elif k in ("enter", "space"):
            food = self.options[self.cursor]
            if food_qty(self.pet, food) <= 0:
                return None
            msg = self.pet.feed(food)
            if self.pet.refused:                     # checkRefused blew the meal off entirely
                return ("done", ("refused", food, msg))
            fed = self.pet.anim == "eat"
            if fed and food.get("can_dec"):          # Consumable.decQuantity (staples never dec)
                left = self.pet.inventory.get(food["key"], 0) - 1
                if left <= 0:
                    self.pet.inventory.pop(food["key"], None)
                else:
                    self.pet.inventory[food["key"]] = left
            return ("done", ("fed" if fed else "full", food, msg))
        elif k in ("escape", "f"):
            return ("done", None)
        return None

    def text(self):
        p = self.pet
        from .pet import DP_MAX
        out = menu.header("FEED", f"hunger {p.hunger}/4  str {p.strength}/4  "
                                  f"DP {getattr(p, 'dp', 0)}/{DP_MAX}")
        if not self.options:
            out.append_text(menu.blanks(2))
            out.append_text(menu.note("The pantry is empty."))
            out.append("  Buy food at the shop ([o]).\n", style=DIM)
            out.append_text(menu.blanks(3))
            out.append_text(menu.footer("ESC out"))
            return out
        sel = self.options[self.cursor]
        qty = food_qty(p, sel)
        tw = menu.W - menu.IC_W - 2
        info = [sel["name"][:tw], _effect_line(sel)[:tw],
                "x∞" if not sel.get("can_dec") else f"x{qty}", ""]
        menu.icon_info(out, menu.item_icon(sel), info)

        def fmt(f, i):
            q = food_qty(p, f)
            tag = "" if not f.get("can_dec") else f"  x{q}"
            return f"{f['name']}{tag}"

        self.cursor = menu.list_window(out, self.options, self.cursor, 3, fmt)
        out.append_text(menu.footer("↑↓ pick   ENTER feed   ESC out"))
        return out
