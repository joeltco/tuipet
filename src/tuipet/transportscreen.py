"""Transport items (DVPet Phoenix/Birdra/Garuda/Wha) — warp across the Digital World.

Zone / Continent Transport pick a destination; Town / Disaster Transport are instant.
All set the pet's persistent world position (adv_map / adv_zone / adv_loc), so the
NEXT Adventure begins there.  Arrival points are canon (PhysicalState.transport):
Phoenix lands at the zone's first town, Birdra moves you to the town AND rests,
Garuda lands one step shy of the next boss, Wha changes continent.  The ticket is
consumed only on a confirmed warp.
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
        self.options = self._options()

    def _options(self):
        mi = max(0, min(self.pet.adv_map, len(self.maps) - 1))
        if self.kind == "continent":
            # canon drawMapSelect honours per-map unlock flags: a continent is
            # reachable once the one before it is beaten (a Wha ticket must not
            # skip the progression; audit 2026-07-05 -- ALL 5 were listed)
            from . import persistence
            beaten = persistence.get_progress().get("maps", set())
            return [(f"Continent {i + 1}   ({len(m['zones'])} zones)", i, 0)
                    for i, m in enumerate(self.maps)
                    if i == 0 or (i - 1) in beaten or i <= self.pet.adv_map]
        if self.kind == "zone":
            return [(f"Zone {zi + 1}", mi, zi)
                    for zi in range(len(self.maps[mi]["zones"]))]
        if self.kind == "town":
            return [("Warp to the nearest town  (rest)", mi, 0)]
        zi = max(0, min(self.pet.adv_zone, len(self.maps[mi]["zones"]) - 1))
        return [("Warp toward the nearest enemy", mi, zi)]

    def key(self, k):
        if k in ("up", "k"):
            self.cursor = (self.cursor - 1) % len(self.options)
        elif k in ("down", "j"):
            self.cursor = (self.cursor + 1) % len(self.options)
        elif k in ("enter", "space"):
            _, mi, zi = self.options[self.cursor]
            self.pet.adv_map, self.pet.adv_zone = mi, zi
            zone = self.maps[mi]["zones"][zi]
            towns = zone.get("towns") or ()
            # canon arrival points (PhysicalState.transport, audit 2026-07-04):
            # every warp used to dump you at step 0
            if self.kind == "zone":
                # Phoenix lands at the zone's FIRST TOWN (towns[0].range[0])
                self.pet.adv_loc = towns[0][0] if towns else 0
            elif self.kind == "town":
                # Birdra MOVES you to the town (toTravelTown), then the rest
                self.pet.adv_loc = towns[0][0] if towns else 0
                self.pet._set_energy(self.pet.max_energy)
            elif self.kind == "danger":
                # Garuda lands one step shy of the NEXT BOSS (e.location - 1)
                bosses = sorted(b.get("location") or zone.get("total_steps", 10000)
                                for b in zone.get("bosses", ()))
                self.pet.adv_loc = max(0, (bosses[0] if bosses else 0) - 1)
            else:                                              # continent: the map's gate
                self.pet.adv_loc = 0
            n = self.pet.inventory.get(self.item_key, 1) - 1        # consume the ticket
            if n <= 0:
                self.pet.inventory.pop(self.item_key, None)
            else:
                self.pet.inventory[self.item_key] = n
            dest = {"continent": f"Continent {mi + 1}", "zone": f"Zone {zi + 1}",
                    "town": "the town", "danger": "the next boss"}[self.kind]
            return ("done", f"Warped to {dest}!")
        elif k in ("escape", "o"):
            return ("done", None)                              # cancel — ticket kept
        return None

    def text(self):
        out = menu.header(TITLE[self.kind],
                          f"at {self.pet.adv_map + 1}-{self.pet.adv_zone + 1}")
        out.append_text(menu.note(self.name))
        out.append_text(menu.blanks(1))
        self.cursor = menu.list_window(out, self.options, self.cursor, 6,
                                       lambda o, i: o[0])
        out.append_text(menu.footer("↑↓ pick   ENTER warp   ESC cancel"))
        return out
