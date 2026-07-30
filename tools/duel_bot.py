#!/usr/bin/env python3
"""DUEL BOT — a sparring partner that sits in the lobby and answers invites.

    python3 tools/duel_bot.py                       # prod relay, default pet
    python3 tools/duel_bot.py --pet cres            # CresGarurumon (jogress partner)
    python3 tools/duel_bot.py --jogress decline     # walk the fusion, never commit
    python3 tools/duel_bot.py --uri ws://localhost:8765/

It runs the REAL client (LobbyPanel + LobbyClient), so whatever it does is
what a second player would do -- no mocks, no shortcuts.

WHAT IT ANSWERS
  * a BATTLE invite: accepts, then works the timing bar like a player.  The
    bar is real: the bot presses SPACE while the marker is inside its mega
    window, so it locks a genuine grade instead of taking a free win.
  * a JOGRESS invite: accepts, walks the fusion scene, and then either
    confirms or declines (--jogress, default confirm).

⚠ THE FUSION IS PERMANENT.  BlitzGreymon + CresGarurumon -> Omnimon Alter-S
  transforms BOTH pets, and there is no undo.  The two-phase commit means it
  only happens if YOU confirm too, so --jogress confirm is safe to leave
  running -- nothing fuses until you press Enter on your own screen.

NAMING: the account is smk-prefixed on purpose.  server._ladder_report drops
any bout with an smk* name on either side, so this bot can never climb the
public season ladder (2026-07-28: 11 rigs sat on the live ladder the day the
ads went out).  The cost is that duels against it do not credit the ladder --
everything else (the bar, the seeded fight, the arena, the result, jogress)
is exercised end to end.
"""
from __future__ import annotations

import argparse
import asyncio
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from tuipet import battlescreen, data, jogress, net  # noqa: E402
from tuipet.lobbyscreen import LobbyPanel  # noqa: E402
from tuipet.pet import DP_MAX, Pet  # noqa: E402

DEFAULT_URI = "wss://ff3mmo.com/tuipet/"

# num, line, label -- the pets the bot can hold
PETS = {
    "cres": (398, "ver2", "CresGaru"),      # BlitzGreymon's jogress partner
    "blitz": (297, "ver1", "BlitzBot"),     # a mirror match
    "wargrey": (100, "", "WarBot"),         # a plain sparring Mega
}


def mk_pet(num, line_id, name):
    """A qualified veteran: blank or unfit pets get their invites refused."""
    _, by = data.load_sprites()
    rec = by[num]
    p = Pet(num=num, name=name, stage=rec["stage"], attribute=rec["attribute"])
    p.hatched = True
    p.world_seconds = 12 * 60.0        # midday: no bedtime refusals
    p.compliance = True
    p.energy = p.max_energy
    p.hunger = 4
    p.strength = 4
    p.weight = p._base_weight()
    p.dp = DP_MAX                     # Pen20: a jogress needs the FULL meter
    p.battles, p.wins = 40, 22        # a believable record for the hit formula
    p.total_trainings = 400
    p.stage_trainings = 40
    if line_id:
        p.line_id = line_id           # load-bearing for jogress: a line-less
        #                               partner only ever LENDS its power
    return p


class Bot:
    """Same construction as tools/pvp_smoke.py: name+pw make the panel connect
    ITSELF.  Never call _connect again -- a second session of one account
    starts an eviction war on the relay (newest wins) and voids the bout."""

    def __init__(self, uri, num, line_id, label, account):
        self.uri = uri
        self.pet = mk_pet(num, line_id, label)
        self.name = account
        self.tasks = []
        self.panel = LobbyPanel(self.pet, self._connect,
                                name=account, pw="smoke")
        self.log_t = 0.0
        self.bouts = 0
        self.fusions = 0

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


def bar_is_hot(panel):
    """True when the timing bar's marker is inside the mega window.  The bot
    plays the bar honestly -- it reads the same marker the player sees, with
    the same latency grace the grader gives a human."""
    show = getattr(panel, "bshow", None)
    if show is None or getattr(show, "phase", "") != "ready":
        return False
    if show.frame_i - show._ready_frame < battlescreen.LOCK_ARM_T:
        return False                       # the bar has not armed yet
    return show.mega_lo <= show.bar <= show.mega_hi


async def run(uri, pet_key, jog_mode, account, quiet):
    num, line_id, label = PETS[pet_key]
    bot = Bot(uri, num, line_id, label, account)
    doors = [o["name"] for o in jogress.options(bot.pet)]
    print(f"duel bot up: {label} #{num} {bot.pet.stage} {bot.pet.attribute}"
          f"  line={line_id or '(none)'}  account={account}")
    print(f"  jogress doors: {doors or '(none)'}   on a fusion: {jog_mode}")
    print(f"  relay: {uri}")
    print("  waiting for invites — Ctrl-C to stop.", flush=True)

    last_seen = 0.0
    while True:
        bot.tick()
        p = bot.panel

        # ---- answer an invite -------------------------------------------
        if p.invite_prompt is not None:
            kind = p.invite_prompt.get("kind")
            who = p.invite_prompt.get("from_name", "?")
            print(f"[{time.strftime('%H:%M:%S')}] {kind} invite from {who} → accept",
                  flush=True)
            bot.key("y")

        # ---- a duel: work the bar, then let it play ---------------------
        if p.phase == "battle":
            if p.bphase == "lock":
                if bar_is_hot(p):
                    bot.key("space")            # a real, earned lock
                elif getattr(p.bshow, "phase", "") == "intro":
                    bot.key("space")            # skip the banner to the bar
            elif p.bphase == "over":
                if p.bt_outcome and time.time() - last_seen > 1:
                    print(f"[{time.strftime('%H:%M:%S')}] bout over: "
                          f"{p.bt_outcome}  (bot lock: {p.bt_my_lock})", flush=True)
                    last_seen = time.time()
                    bot.bouts += 1
                bot.key("enter")                # back to the lobby, ready again

        # ---- a fusion: walk the scene, then confirm or decline ----------
        if p.phase == "jogress":
            if p.jphase == "result":
                show = getattr(p, "jshow", None)
                if show is not None and getattr(show, "phase", "") == "fusing":
                    bot.key("enter")            # skip the converge to the reveal
                elif not p.j_confirmed:
                    res = (p.jresult or {}).get("name", "?")
                    if jog_mode == "confirm":
                        print(f"[{time.strftime('%H:%M:%S')}] fusion → {res}: "
                              f"bot CONFIRMS (waiting on you)", flush=True)
                        bot.key("enter")
                        bot.fusions += 1
                    else:
                        print(f"[{time.strftime('%H:%M:%S')}] fusion → {res}: "
                              f"bot DECLINES (--jogress decline)", flush=True)
                        bot.key("escape")
            elif p.jphase == "failed":
                print(f"[{time.strftime('%H:%M:%S')}] fusion failed: "
                      f"{p.fail_reason}", flush=True)
                bot.key("enter")

        # ---- keep it fit between tests ----------------------------------
        # A bout bills the BODY (energy, weight) and a sleepy or drained pet
        # starts REFUSING invites -- battle_condition gates the accept side
        # too.  A sparring partner that quietly stops answering after a few
        # duels is worse than none, so top it up whenever it is idle.
        if p.phase == "lobby":
            bot.pet.energy = bot.pet.max_energy
            bot.pet.hunger = bot.pet.strength = 4
            bot.pet.weight = bot.pet._base_weight()
            bot.pet.dp = DP_MAX
            bot.pet.asleep = False
            bot.pet.sick = bot.pet.injured = False
            bot.pet.poop, bot.pet.poop_sizes = 0, []
            bot.pet.world_seconds = 12 * 60.0     # never wanders into bedtime

        # ---- a fused bot is no longer the partner you wanted ------------
        if bot.pet.num != num:
            print(f"[{time.strftime('%H:%M:%S')}] the bot's pet became "
                  f"#{bot.pet.num} — restoring {label} for the next test",
                  flush=True)
            bot.pet = mk_pet(num, line_id, label)
            bot.panel.pet = bot.pet
            if bot.panel.client:
                bot.panel.client.update_pet(bot.panel._card())

        if not quiet and time.time() - bot.log_t > 300:
            bot.log_t = time.time()
            others = [o.get("name") for o in (p._others() or [])]
            print(f"[{time.strftime('%H:%M:%S')}] alive · phase={p.phase} "
                  f"· bouts={bot.bouts} · lobby={others}", flush=True)

        await asyncio.sleep(0.1)          # the app's own 0.1s interval clock


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--uri", default=DEFAULT_URI)
    ap.add_argument("--pet", default="cres", choices=sorted(PETS))
    ap.add_argument("--jogress", default="confirm", choices=("confirm", "decline"))
    ap.add_argument("--account", default="smkduelbot")
    ap.add_argument("--quiet", action="store_true")
    a = ap.parse_args()
    try:
        asyncio.run(run(a.uri, a.pet, a.jogress, a.account, a.quiet))
    except KeyboardInterrupt:
        print("\nduel bot down.")


if __name__ == "__main__":
    main()
