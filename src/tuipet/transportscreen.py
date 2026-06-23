"""Transport items (DVPet Phoenix/Birdra/Garuda/Wha) — warp across the Digital World.

Zone / Continent Transport pick a destination; Town / Disaster Transport are instant.
All set the pet's persistent world position (adv_map / adv_zone), so the NEXT Adventure
begins there. Town Transport rests the pet; Disaster Transport forces an encounter on the
next adventure leg (pet.adv_seek). The ticket is consumed only on a confirmed warp.
"""
from __future__ import annotations
from . import data, menu

# items.csv AnimationType -> warp behaviour
KIND = {"WhaTransport": "continent", "PhoenixTransport": "zone",
        "BirdraTransport": "town", "GarudaTransport": "danger"}
TITLE = {"continent": "CONTINENT WARP", "zone": "ZONE WARP",
         "town": "TOWN WARP", "danger": "DANGER WARP"}


class TransportPanel:
    def __init__(self, pet, key):
        self.pet = pet
        self.item_key = key
        e = data.consumable_by_key(key) or {}
        self.name = e.get("name", "Transport")
        self.kind = KIND.get(e.get("action"), "zone")
        self.maps = data.load_maps()
        self.cursor = 0
        self.frame_i = 0
        self.options = self._options()

    def _options(self):
        mi = max(0, min(self.pet.adv_map, len(self.maps) - 1))
        if self.kind == "continent":
            return [(f"Continent {i + 1}   ({len(m['zones'])} zones)", i, 0)
                    for i, m in enumerate(self.maps)]
        if self.kind == "zone":
            return [(f"Zone {zi + 1}", mi, zi)
                    for zi in range(len(self.maps[mi]["zones"]))]
        if self.kind == "town":
            return [("Warp to the nearest town  (rest)", mi, 0)]
        zi = max(0, min(self.pet.adv_zone, len(self.maps[mi]["zones"]) - 1))
        return [("Warp toward the nearest enemy", mi, zi)]

    def anim(self):
        self.frame_i += 1

    def key(self, k):
        if k in ("up", "k"):
            self.cursor = (self.cursor - 1) % len(self.options)
        elif k in ("down", "j"):
            self.cursor = (self.cursor + 1) % len(self.options)
        elif k in ("enter", "space"):
            _, mi, zi = self.options[self.cursor]
            self.pet.adv_map, self.pet.adv_zone = mi, zi
            if self.kind == "town":
                self.pet.energy = self.pet.max_energy          # a town rests the pet
            elif self.kind == "danger":
                self.pet.adv_seek = True                       # forced encounter next leg
            n = self.pet.inventory.get(self.item_key, 1) - 1        # consume the ticket
            if n <= 0:
                self.pet.inventory.pop(self.item_key, None)
            else:
                self.pet.inventory[self.item_key] = n
            dest = {"continent": f"Continent {mi + 1}", "zone": f"Zone {zi + 1}",
                    "town": "the town", "danger": "danger"}[self.kind]
            return ("done", f"Warped to {dest}!")
        elif k in ("escape", "o"):
            return ("done", None)                              # cancel — ticket kept
        return None

    def text(self):
        out = menu.header(TITLE[self.kind],
                          f"at {self.pet.adv_map + 1}-{self.pet.adv_zone + 1}")
        out.append_text(menu.note(self.name))
        out.append_text(menu.blanks(1))
        VIS = 6
        lo = max(0, min(self.cursor - VIS // 2, len(self.options) - VIS))
        for i in range(lo, min(lo + VIS, len(self.options))):
            out.append_text(menu.row(self.options[i][0], i == self.cursor))
        out.append_text(menu.blanks(VIS - min(VIS, len(self.options))))
        out.append_text(menu.footer("↑↓ pick   ENTER warp   ESC cancel"))
        return out
