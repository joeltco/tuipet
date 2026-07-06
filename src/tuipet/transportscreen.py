"""Transport items (DVPet Phoenix/Birdra/Garuda/Wha) — warp across the Digital World.

Zone / Continent Transport pick a destination; Town / Disaster Transport are instant.
All set the pet's persistent world position (adv_map / adv_zone / adv_loc), so the
NEXT Adventure begins there.  Arrival points are canon (PhysicalState.transport):
Phoenix lands at the zone's first town, Birdra moves you to the town AND rests,
Garuda lands one step shy of the next boss, Wha changes continent.  The ticket is
consumed only on a confirmed warp.

The continent warp plays canon's whaTransport RIDE (SpriteAnim): the pet holds
the ticket up, WHAMON (dex 193) surfaces from the water on the left, swims over,
gulps the traveller aboard and swims off the right edge.  Both mons share the
LCD side-by-side (jogress faceoff grammar) and never overlap.
"""
from __future__ import annotations
from . import data, menu
from . import grid
from . import strikefx
from .render import render_scene, downsample
from .theme import LCD_ON, LCD_BG, SIL_DAY

COLS, ROWS = 40, 12

# items.csv AnimationType -> warp behaviour
KIND = {"WhaTransport": "continent", "PhoenixTransport": "zone",
        "BirdraTransport": "town", "GarudaTransport": "danger"}
TITLE = {"continent": "CONTINENT WARP", "zone": "ZONE WARP",
         "town": "TOWN WARP", "danger": "DANGER WARP"}

# canon carriers (SpriteAnim whaTransport / transport): real roster mons
CARRIER = {"continent": 193,  # Whamon surfaces and swims you across the sea
           "town": 97,        # Birdramon
           "danger": 234,     # Garudamon
           "zone": 292}       # Phoenixmon
# the whamon ride timeline (0.1s ticks), scaled from canon's 64-interval playbook
RIDE_STING_T = 5              # whaTransportUseTicket sting + the ticket held up
RIDE_TICKET_T = 12            # ticket beat ends; Whamon starts surfacing
RIDE_RISE_T = 22              # fully surfaced (rises over 10 ticks, canon 12..21)
RIDE_SWIM_T = 34              # swum across to the traveller (canon 22..33)
RIDE_GULP_T = 38              # pose-6 mouth-open beat: the pet vanishes aboard
RIDE_END_T = 64               # swum off the right edge (canon endAnim at 64)
# the bird ride (canon transport()): the carrier swoops from ABOVE, scoops the
# traveller off the top-left, and the pet DROPS from the sky at the destination
BIRD_STING_T = 7              # transportUseTicket sting (canon frame 7)
BIRD_TICKET_T = 14            # bird appears (canon 14), descends 15..24
BIRD_DOWN_T = 25              # landed alongside; wing-flap beat
BIRD_LIFT_T = 31              # transportLiftOff -> wash; the pet is scooped
BIRD_GONE_T = 46              # flown off the top-left; the empty travel beat
BIRD_FALL_T = 50              # the pet falls from the sky at the destination
BIRD_LAND_T = 61              # touchdown: the 9/10 bounce (flyTransportFall -> alarm)
BIRD_END_T = 72


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
        self.ride = None              # a running whamon-ride playbook {t, msg}
        self.sfx = None

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
            # Birdra rides only where a town EXISTS (canon isTownClose gates
            # the ticket; transport audit 2026-07-06 -- the townless fallback
            # was a free warp-to-start with an energy refill)
            if any(z.get("towns") for z in self.maps[mi]["zones"]):
                return [("Warp to the nearest town  (rest)", mi, 0)]
            return []
        zi = max(0, min(self.pet.adv_zone, len(self.maps[mi]["zones"]) - 1))
        return [("Warp toward the nearest enemy", mi, zi)]

    def key(self, k):
        if self.ride is not None:
            if k in ("space", "enter", "escape"):
                if self.ride["t"] < self.ride["end"]:
                    self.ride["t"] = self.ride["end"]  # skip to the arrival hold
                else:
                    return ("done", self.ride["msg"])
            return None
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
                # Birdra: the CLOSEST town across the map's zones (canon
                # getClosestTownZone walks the zone chain; transport audit
                # 2026-07-06 -- the old hop only knew the current zone), then
                # the rest (the walk-in town rest can't trigger on a landing)
                zones = self.maps[mi]["zones"]
                start = max(0, min(self.pet.adv_zone, len(zones) - 1))
                for zj in sorted(range(len(zones)), key=lambda j: abs(j - start)):
                    tw = zones[zj].get("towns") or ()
                    if tw:
                        self.pet.adv_zone = zi = zj
                        zone = zones[zj]
                        self.pet.adv_loc = tw[0][0]
                        self.pet._set_energy(self.pet.max_energy)
                        break
            elif self.kind == "danger":
                # Garuda: one step shy of the NEXT boss AHEAD -- getNextBoss
                # chases FORWARD across zones (the old pick took the current
                # zone's first boss and could warp you BACKWARD)
                here = int(getattr(self.pet, "adv_loc", 0) or 0)
                zones = self.maps[mi]["zones"]
                target = None
                for zj in range(zi, len(zones)):
                    floor = here if zj == zi else -1
                    ahead = sorted(b.get("location") or zones[zj].get("total_steps", 10000)
                                   for b in zones[zj].get("bosses", ())
                                   if (b.get("location") or zones[zj].get("total_steps", 10000)) > floor)
                    if ahead:
                        target = (zj, ahead[0])
                        break
                if target is None:                     # nothing ahead: the zone gate
                    target = (zi, zone.get("total_steps", 1))
                self.pet.adv_zone, bloc = target[0], target[1]
                zi = target[0]
                self.pet.adv_loc = max(0, bloc - 1)
            else:                                              # continent: the map's gate
                self.pet.adv_loc = 0
            n = self.pet.inventory.get(self.item_key, 1) - 1        # consume the ticket
            if n <= 0:
                self.pet.inventory.pop(self.item_key, None)
            else:
                self.pet.inventory[self.item_key] = n
            dest = {"continent": f"Continent {mi + 1}", "zone": f"Zone {zi + 1}",
                    "town": "the town", "danger": "the next boss"}[self.kind]
            # every canon transport plays its ride (whaTransport / transport())
            wha = self.kind == "continent"
            self.ride = {"t": 0, "msg": f"Warped to {dest}!", "wha": wha,
                         "end": RIDE_END_T if wha else BIRD_END_T}
            return None
        elif k in ("escape", "o"):
            return ("done", None)                              # cancel — ticket kept
        return None

    def anim(self):
        if self.ride is None:
            return
        prev = self.ride["t"]
        t = self.ride["t"] = min(prev + 1, self.ride["end"])
        if t == prev:                 # holding at the arrival frame
            return
        if self.ride["wha"]:
            if t == RIDE_STING_T:
                self.sfx = "happy"    # soundConfig transportUseTicket -> happy
            elif t == RIDE_GULP_T:
                self.sfx = "eat"      # gulped aboard
            elif t == RIDE_END_T:
                self.sfx = "reward"   # arrival
        else:
            if t == BIRD_STING_T:
                self.sfx = "happy"    # transportUseTicket -> happy
            elif t == BIRD_LIFT_T:
                self.sfx = "wash"     # transportLiftOff -> wash
            elif t in (BIRD_LAND_T, BIRD_LAND_T + 6):
                self.sfx = "alarm"    # flyTransportFall -> alarm
            elif t == BIRD_END_T:
                self.sfx = "reward"

    def _frames(self, num):
        return data.frames_for(num, getattr(self.pet, "egg_type", 0))

    def _ticket_overlay(self, pet_x):
        raw = data.load_icons().get(self.item_key)
        if not (raw and raw[0]):
            return []
        icon = downsample(raw[0], 3)
        return strikefx.blit(icon, pet_x - len(icon[0]) - 2, grid.TOP + 1)

    def _bird_scene(self):
        """Canon transport(): the carrier bird swoops down from ABOVE, scoops
        the traveller off the top-left, and after the empty travel beat the pet
        DROPS from the sky at the destination and bounces (poses 9/10)."""
        t = self.ride["t"]
        place, overlay = [], []
        pf = self._frames(self.pet.num)
        bf = self._frames(CARRIER[self.kind])

        def lifted(rows, pad):
            w = max(len(r) for r in rows)
            return rows + ["0" * w] * pad if pad > 0 else rows
        if t < BIRD_LIFT_T:                            # waiting on the right
            pose = 1 if t < BIRD_STING_T else (5 if t < BIRD_TICKET_T else 0)
            pet_rows = grid.prep((pf[pose] if pose < len(pf) else None) or pf[0])
            pet_x = grid.X1 - grid.width(pet_rows)
            place.append((pet_rows, pet_x, False))
            if BIRD_STING_T <= t < BIRD_TICKET_T:
                overlay = self._ticket_overlay(pet_x)
            if t >= BIRD_TICKET_T:                     # the bird descends alongside
                wing = bf[(t // 3) % 2] or bf[0]
                prog = min(1.0, (t - BIRD_TICKET_T) / (BIRD_DOWN_T - BIRD_TICKET_T))
                rows = grid.prep(lifted(wing, round(14 * (1 - prog))))
                place.append((rows, pet_x - grid.width(grid.prep(wing)), False))
        elif t < BIRD_GONE_T:                          # scooped: flies off up-left alone
            wing = bf[(t // 3) % 2] or bf[0]
            prog = (t - BIRD_LIFT_T) / (BIRD_GONE_T - 1 - BIRD_LIFT_T)
            rows = grid.prep(lifted(wing, round(14 * prog)))
            w = grid.width(rows)
            x0 = grid.X1 - 16 - w
            place.append((rows, round(x0 + (-w - x0) * prog), False))
        elif t < BIRD_FALL_T:                          # the empty travel beat
            pass
        elif t < BIRD_LAND_T:                          # dropped off from the sky
            prog = (t - BIRD_FALL_T) / (BIRD_LAND_T - 1 - BIRD_FALL_T)
            rows = grid.prep(lifted(pf[9] or pf[0], round(14 * (1 - prog))))
            place.append((rows, grid.X0 + 8, False))
        else:                                          # the 9/10 touchdown bounce, then up
            pose = (10, 9)[(t // 2) % 2] if t < self.ride["end"] else 0
            rows = grid.prep((pf[pose] if pose < len(pf) else None) or pf[0])
            place.append((rows, grid.X0 + 8, False))
        return menu.paint(place, self.pet.background(),
                          rows=ROWS, cols=COLS, overlay=overlay)

    def _ride_scene(self):
        """Canon whaTransport, one beat at a time: ticket up (sting) -> Whamon
        surfaces bottom-left -> swims right to the traveller -> mouth-open gulp
        (the pet vanishes aboard) -> swims off the right edge."""
        if not self.ride["wha"]:
            return self._bird_scene()
        t = self.ride["t"]
        place = []
        overlay = []
        pf = self._frames(self.pet.num)
        # the traveller waits on the RIGHT (canon character at the right edge)
        pet_pose = 1 if t < RIDE_STING_T else (5 if t < RIDE_TICKET_T else 0)
        pet_rows = grid.prep((pf[pet_pose] if pet_pose < len(pf) else None) or pf[0])
        pet_x = grid.X1 - grid.width(pet_rows)
        if t < RIDE_GULP_T:                            # aboard (hidden) from the gulp on
            # canon 34: the pet turns to FACE the arriving whale (mirrored)
            place.append((pet_rows, pet_x, t >= RIDE_SWIM_T))
        if RIDE_STING_T <= t < RIDE_TICKET_T:          # the ticket held up beside it
            overlay = self._ticket_overlay(pet_x)
        wf = self._frames(CARRIER["continent"])
        if t >= RIDE_TICKET_T and t < RIDE_END_T:
            swim = wf[(t // 3) % 2] or wf[0]
            rise_x = grid.X0 - 12                      # canon: enters mostly off-screen left
            if t < RIDE_RISE_T:                        # surfacing: rises out of the water
                k = max(1, round(len(swim) * (t - RIDE_TICKET_T + 1) / (RIDE_RISE_T - RIDE_TICKET_T)))
                rows = ["0" * len(swim[0])] * (len(swim) - k) + swim[:k]
                place.append((grid.prep(rows), rise_x, True))
            else:
                if t >= RIDE_GULP_T - 2 and t < RIDE_GULP_T + 2:
                    swim = (wf[6] if len(wf) > 6 else None) or swim   # the gulp
                rows = grid.prep(swim)
                w = grid.width(rows)
                stop = pet_x - w                       # flush ALONGSIDE the pet, never over it
                if t < RIDE_SWIM_T:                    # crossing
                    x = round(rise_x + (stop - rise_x) * ((t - RIDE_RISE_T + 1) / (RIDE_SWIM_T - RIDE_RISE_T)))
                elif t < RIDE_GULP_T + 2:              # alongside for the gulp
                    x = stop
                else:                                  # off the right edge, traveller aboard
                    x = round(stop + (COLS - stop) * ((t - RIDE_GULP_T - 1) / (RIDE_END_T - RIDE_GULP_T - 1)))
                place.append((rows, x, True))          # mirrored: swimming right
        return menu.paint(place, self.pet.background(),
                          rows=ROWS, cols=COLS, overlay=overlay)

    def strip(self):
        if self.ride is None:
            return ""
        if self.ride["t"] >= self.ride["end"]:
            return f"{self.ride['msg']}  [dim]· ENTER done[/]"
        return "[dim]SPACE skip[/]"

    def text(self):
        if self.ride is not None:
            return self._ride_scene()
        out = menu.header(TITLE[self.kind],
                          f"at {self.pet.adv_map + 1}-{self.pet.adv_zone + 1}")
        out.append_text(menu.note(self.name))
        out.append_text(menu.blanks(1))
        self.cursor = menu.list_window(out, self.options, self.cursor, 6,
                                       lambda o, i: o[0])
        out.append_text(menu.footer("↑↓ pick   ENTER warp   ESC cancel"))
        return out
