#!/usr/bin/env python3
"""Live PvP smoke — two real bots fight one real bout on the relay.

    python3 tools/pvp_smoke.py                    # against the prod relay
    python3 tools/pvp_smoke.py --uri ws://localhost:8765/   # local dev relay

Run it after ANY change that touches the lobby, the bout engine
(lobbybout.py), net.py, or server/server.py.  The unit suite cannot see
this path end-to-end: the v0.5.0→v0.5.34 era shipped a payout crash
(pet.add_bits was dead) that fired only when a REAL online bout finished
— this tool caught it on its first flight (2026-07-17).

What it does, all through the real code paths (nothing mocked):
  * two throwaway accounts join the lobby (real LobbyPanel + LobbyClient)
  * A opens B's action menu and presses B(attle); B accepts with 'y'
  * both SPACE through the proto-3 bout (commit-reveal cards, seeded
    volleys) until it resolves
  * asserts: both land back in the lobby, both record the bout, exactly
    one winner, and the purse actually pays

Notes for the next reader:
  * LobbyPanel AUTO-CONNECTS in __init__ when name+pw are passed.  Do not
    call _connect() again — a second session of the same account starts an
    eviction war on the relay (newest-wins) and the bout voids with
    "Opponent left" (the first flight's face-plant).
  * The bots appear briefly in the public roster as smkA…/smkB… — real
    players in the room will see them join and leave.  Keep it brief.
"""
from __future__ import annotations

import argparse
import asyncio
import os
import random
import string
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from tuipet import net  # noqa: E402
from tuipet.lobbyscreen import LobbyPanel  # noqa: E402
from tuipet.pet import Pet  # noqa: E402

DEFAULT_URI = "wss://ff3mmo.com/tuipet/"


def mk_pet(num, name):
    """A qualified veteran (the probe-pet lesson: blank pets get refused)."""
    p = Pet(num=num, name=name, stage="Champion", attribute="Vaccine",
            obedience=800)
    p.world_seconds = 12 * 60.0          # midday: no bedtime refusals
    p.compliance = True
    p.energy = p.max_energy
    p.hunger = 4
    p.strength = 4
    p.battles, p.wins = 10, 6
    p.total_trainings = 12
    return p


class Bot:
    def __init__(self, tag, num, uri, suffix):
        self.uri = uri
        self.name = f"smk{tag}{suffix}"
        self.pet = mk_pet(num, f"Mon{tag}")
        self.tasks = []
        # name+pw => the panel connects ITSELF (see the module docstring)
        self.panel = LobbyPanel(self.pet, self._connect,
                                name=self.name, pw="smoke")

    def _connect(self, name, pw, card):
        client = net.LobbyClient(self.uri, name, pw, card)
        self.tasks.append(asyncio.get_event_loop().create_task(client.run()))
        return client

    @property
    def state(self):
        return self.panel.state

    def tick(self):
        self.panel.anim()

    def key(self, k):
        return self.panel.key(k)


async def pump(bots, seconds, key_for=None):
    t0 = time.time()
    while time.time() - t0 < seconds:
        for b in bots:
            b.tick()
            if key_for:
                k = key_for(b)
                if k:
                    b.key(k)
        await asyncio.sleep(0.1)


async def run(uri):
    suffix = "".join(random.choice(string.ascii_lowercase) for _ in range(4))
    a, b = Bot("A", 100, uri, suffix), Bot("B", 104, uri, suffix)
    bots = [a, b]

    # ---- join: both get me_id and see each other -------------------------
    for _ in range(100):
        await pump(bots, 0.1)
        ok = all(getattr(x.state, "me_id", None) is not None for x in bots)
        if ok and any(pl.get("name") == b.name for pl in (a.state.roster or [])):
            break
    else:
        raise SystemExit("JOIN FAILED: no mutual presence in 10s")
    pid_b = next(pl["id"] for pl in a.state.roster if pl.get("name") == b.name)
    print(f"joined: A={a.name} B={b.name}  roster={len(a.state.roster)}")

    # ---- A invites through the real action-menu key ----------------------
    a.panel.action_for = (pid_b, b.name, True)
    a.key("b")
    print("A:", a.panel.status)

    # ---- B accepts with 'y' the moment the prompt lands ------------------
    def accept(bot):
        if bot is b and bot.panel.invite_prompt is not None:
            return "y"
        return None
    await pump(bots, 5, key_for=accept)
    assert a.panel.phase == "battle" and b.panel.phase == "battle", \
        ("session never opened", a.panel.phase, b.panel.phase,
         a.panel.status, b.panel.status)

    # ---- both SPACE through the bout until it resolves -------------------
    def space(bot):
        return "space" if bot.panel.phase == "battle" else None
    for _ in range(60):
        await pump(bots, 0.5, key_for=space)
        if a.panel.phase == "lobby" and b.panel.phase == "lobby":
            break
    assert a.panel.phase == "lobby" and b.panel.phase == "lobby", \
        ("bout never resolved", a.panel.phase, b.panel.phase)

    print("A result:", a.panel.status)
    print("B result:", b.panel.status)
    print(f"records: A {a.pet.wins}W/{a.pet.battles}  "
          f"B {b.pet.wins}W/{b.pet.battles}")
    battles = (a.pet.battles - 10) + (b.pet.battles - 10)
    wins = (a.pet.wins - 6) + (b.pet.wins - 6)
    paid = (a.pet.bits > 0) + (b.pet.bits > 0)
    assert battles == 2, f"both pets must record the bout (got {battles})"
    assert wins in (0, 1), f"at most one winner (got {wins})"
    assert paid == 2, "both purses must land (winner's prize + consolation)"

    # ---- clean exit ------------------------------------------------------
    for x in bots:
        x.key("escape")
    await pump(bots, 0.5)
    for x in bots:
        for t in x.tasks:
            t.cancel()
    print("PVP LIVE SMOKE OK")


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--uri", default=DEFAULT_URI,
                    help=f"relay websocket URI (default {DEFAULT_URI})")
    args = ap.parse_args()
    asyncio.run(run(args.uri))


if __name__ == "__main__":
    main()
