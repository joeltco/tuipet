"""Shop model -- category-organized, unlocked by evolution stage.

Everyday items live in four categories (Food / Medicine / Toys / Chips), each
revealing in price tiers as the pet grows up (data.shop_catalog assigns every
consumable a shop_cat + unlock_stage). Special items (evolution / transport /
X-gear) are NOT sold here -- they come from drops / DNA. Simple economy: fixed
list price, resell at a fixed fraction.
"""
from __future__ import annotations
from . import data

CATEGORIES = ["food", "medicine", "toy", "chip"]
CAT_LABEL = {"food": "Food", "medicine": "Medicine", "toy": "Toys", "chip": "Chips"}
RESELL_DIV = 4                      # resell value = price // 4


def unlocked(pet, category):
    """Items in `category` unlocked at the pet's current stage, cheapest first."""
    pr = data.stage_rank(getattr(pet, "stage", "Mega"))
    out = [e for e in data.shop_catalog()
           if e["shop_cat"] == category and data.stage_rank(e["unlock_stage"]) <= pr]
    out.sort(key=lambda e: e["price"])
    return out


def purchase_price(e):
    return e["price"]


def resell_price(e):
    return max(1, e["price"] // RESELL_DIV) if e.get("price") else 0
