"""THE DUEL — an online bout that plays like a battle (0.5.321).

Joel, 2026-07-30: "ok whats going on with pvp battles??? why is it built like
this??? its nothing like battles whatsoever" → "do all three".  The three:

  1. a LIVE timing bar in the duel.  The lock used to be whatever
     `saved_hit_type` your last drill or local fight left behind, so the one
     input that decides a fight happened somewhere else entirely.  It now
     rides the commit — commit = sha256(nonce:grade), sent when you lock,
     revealed only once the peer's commit is in hand — so neither side can
     answer the other's lock and neither can grind the seed.  (Proto 4.)
  2. ROUNDS_ONLINE == ROUNDS_LOCAL.  The 5-round cap was a v0.4.0 wire cost
     from when rounds were exchanged one at a time; it ended 23% of duels on
     a decision and 9% in a draw where a local bout always knocks someone out.
  3. ONE panel for the whole bout — banner, reveal, bar, volleys, verdict —
     instead of a throwaway panel per volley with a text card between them.

The load-bearing property of a seeded duel is that BOTH clients compute the
SAME fight from their own halves.  These tests wire two real panels' relays
into each other and check exactly that, end to end.
"""
import hashlib

import pytest

from tuipet import battle, battlescreen, lobbyscreen
from tuipet.net import LobbyState
from tuipet.pet import Pet

# A volley is a full round_timeline -- the SAME 110 frames a local
# battle round plays (that parity is the point of the change), so at
# 0.1s a tick a duel runs ~11 real seconds per volley.  Budget enough
# ticks for the longest fight these fixtures produce.
TICK_BUDGET = 1500


class _WiredClient:
    """A relay that actually delivers: whatever one panel sends, the other
    panel receives through its real _on_relay."""

    def __init__(self, state, me_id):
        self.state = state
        self.me_id = me_id
        self.peer = None                 # the other panel
        self.reports = []
        self.outbox = []

    def respond(self, *a, **k):
        pass

    def update_pet(self, *a, **k):
        pass

    def ladder_report(self, won, opp):
        self.reports.append((won, opp))

    def relay(self, pid, payload):
        self.outbox.append(payload)
        if self.peer is not None:
            self.peer._on_relay({"from_id": self.me_id, "payload": payload})


def _duo(host_num=100, guest_num=4, host_stage="Champion", guest_stage="Champion"):
    """Two panels, wired, mid-challenge: exactly what the lobby builds when a
    challenge is accepted on both sides."""
    panels = []
    for i, (num, stage) in enumerate(((host_num, host_stage),
                                      (guest_num, guest_stage))):
        pet = Pet(num=num, stage=stage, attribute="Vaccine")
        pet.hunger = pet.strength = 4
        pet.weight = pet._base_weight()
        pet.energy = pet.max_energy
        pet.world_seconds = 600.0
        st = LobbyState()
        # both tamers present and live: an empty roster reads as "the partner
        # vanished" and ends the bout as their forfeit before it starts
        st.connected = True
        st.me_id = 10 + i
        st.roster = [{"id": 10, "name": "tamer0", "pet": {}, "live": True},
                     {"id": 11, "name": "tamer1", "pet": {}, "live": True}]
        pan = lobbyscreen.LobbyPanel(
            pet, lambda n, pw, card, st=st, i=i: _WiredClient(st, 10 + i),
            name=f"tamer{i}", pw="x")
        panels.append(pan)
    host, guest = panels
    host.partner, guest.partner = (11, "tamer1"), (10, "tamer0")
    # Both sides enter the session BEFORE either card lands -- that is the real
    # ordering: the server delivers the accept ack (which enters the session)
    # ahead of the relayed card, both riding one ordered stream from the
    # accepting client.  So the peers are wired only after both are seated, and
    # the two cards are then delivered by hand.
    host._enter_session(11, "tamer1", "battle", True)
    guest._enter_session(10, "tamer0", "battle", False)
    pending = [(host, list(host.client.outbox)), (guest, list(guest.client.outbox))]
    host.client.outbox.clear()
    guest.client.outbox.clear()
    host.client.peer, guest.client.peer = guest, host
    for sender, msgs in pending:
        other = guest if sender is host else host
        for m in msgs:
            other._on_relay({"from_id": sender.client.me_id, "payload": m})
    return host, guest


def _lock(pan, grade):
    """Stand where a given grade lands and press SPACE, the way a player does."""
    pan.bshow.phase = "ready"
    pan.bshow._ready_frame = 0
    pan.bshow.frame_i = battlescreen.LOCK_ARM_T + 1
    if grade == "mega":
        pan.bshow.bar = (pan.bshow.mega_lo + pan.bshow.mega_hi) // 2
    elif grade == "normal":
        pan.bshow.bar = min(battlescreen.BAR_MAX, pan.bshow.mega_hi + 4)
    else:
        pan.bshow.bar = min(battlescreen.BAR_MAX, pan.bshow.mega_hi + 12)
    pan.bshow._bar_hist = [pan.bshow.bar]
    pan._key_battle("space")


# ---- 1. the live lock ------------------------------------------------------

def test_the_duel_opens_on_a_real_timing_bar():
    """Not a stored form: a bar, on the panel, with the rival on screen."""
    host, guest = _duo()
    assert host.bphase == "lock"
    assert isinstance(host.bshow, battlescreen.BattlePanel)
    assert host.bshow.duel is True
    # the panel walks the intro, then arms the bar by itself
    for _ in range(60):
        host.anim()
        if host.bshow.phase == "ready":
            break
    assert host.bshow.phase == "ready"
    # and the readiness line reads the RIVAL's card, not a species copy
    txt = host.bshow.text()
    assert txt is not None
    assert host.bshow._pick.get("side") is not None


def test_the_lock_is_committed_before_either_side_reveals():
    """The anti-cheat shape: my commit goes out when I lock; my reveal waits
    for the peer's commit.  A client that revealed first would hand its rival
    the chance to pick a beating lock."""
    host, guest = _duo()
    _lock(host, "mega")
    kinds = [m.get("t") for m in host.client.outbox]
    assert "commit" in kinds
    assert "reveal" not in kinds, "revealed before the peer committed"
    assert host.bt_my_lock == "mega"
    assert host.bphase == "commit"
    _lock(guest, "normal")
    # both bound now -> both revealed -> both built
    assert "reveal" in [m.get("t") for m in host.client.outbox]
    assert host.battle is not None and guest.battle is not None


def test_both_clients_compute_the_identical_fight():
    """The whole point of a seeded duel."""
    host, guest = _duo()
    _lock(host, "mega")
    _lock(guest, "normal")
    assert host.battle["seq"] == guest.battle["seq"]
    assert host.bphase == guest.bphase == "fight"


def _seeded_duo(host_lock, guest_lock, nonces=(1234, 5678)):
    """A duel with PINNED nonces, so two runs differ only by what was locked."""
    host, guest = _duo()
    host.pet.saved_hit_type = guest.pet.saved_hit_type = "miss"
    host.bt_nonce, guest.bt_nonce = nonces
    _lock(host, host_lock)
    _lock(guest, guest_lock)
    return host, guest


def test_the_live_lock_beats_the_saved_form():
    """The grade earned at the bar is what fights.  Both pets carry a saved
    'miss' from some drill hours ago; with the seed pinned, locking mega has to
    change the fight -- if the stored form still decided it, the two sequences
    would be identical."""
    mega, _ = _seeded_duo("mega", "mega")
    missed, _ = _seeded_duo("miss", "miss")
    assert mega.bt_my_lock == "mega" and missed.bt_my_lock == "miss"
    assert mega.battle["seq"] != missed.battle["seq"], \
        "the bar changed nothing -- the saved form is still deciding duels"
    # and the grade reaches the engine as AIM.  (Not a count of landed hits:
    # two mega locks CANCEL by the Pen20 ruling, and a harder-hitting fight
    # ends in fewer rounds, so sequence lengths are not comparable.)
    foe = battle.Side.of_card(dict(mega.opp_card, hit_type="normal"))
    aimed = battle.Side.of_card(dict(mega.bt_my_card, hit_type="mega"))
    shanked = battle.Side.of_card(dict(mega.bt_my_card, hit_type="miss"))
    assert aimed.hit_chance(foe) > shanked.hit_chance(foe)


def test_a_tampered_reveal_voids_the_bout():
    """The commit is the guard: a grade that does not match it is a void, not
    a fight."""
    host, _guest = _duo()
    _lock(host, "normal")
    host.bt_peer_commit = hashlib.sha256(b"1:mega").hexdigest()
    host.bt_reveal_sent = True
    host.bt_peer_nonce, host.bt_peer_lock = 1, "miss"      # not what was committed
    host._maybe_build()
    assert host.battle is None
    assert "void" in host.bt_outcome.lower()


def test_a_bad_grade_on_the_wire_voids_the_bout():
    host, _guest = _duo()
    _lock(host, "normal")
    host.bt_peer_nonce, host.bt_peer_lock = 5, "MEGA-ULTRA"
    host.bt_peer_commit = hashlib.sha256(b"5:MEGA-ULTRA").hexdigest()
    host.bt_reveal_sent = True
    host._maybe_build()
    assert host.battle is None and "void" in host.bt_outcome.lower()


def test_an_older_client_is_turned_away_not_silently_mismatched():
    """proto 3 fought a different fight (the lock rode the card).  A seeded
    duel is only honest when both engines are the same engine."""
    host, _guest = _duo()
    host.bphase = "card"
    host._battle_begin({"num": 4, "name": "X", "stage": "Champion", "proto": 3})
    assert host.battle is None
    assert "older tuipet" in (host.bt_payload or ("", ""))[1]


def test_a_walked_away_tamer_locks_itself_so_the_peer_is_never_hung():
    """The bar is a shared handshake online: the peer cannot build the fight
    until my grade is committed."""
    host, _guest = _duo()
    for _ in range(60):
        host.anim()
        if host.bshow.phase == "ready":
            break
    for _ in range(battlescreen.DUEL_AUTOLOCK_T + 5):
        host.anim()
        if host.bt_my_commit_sent:
            break
    assert host.bt_my_commit_sent, "nobody locked; the rival waits forever"
    assert host.bt_my_lock in ("mega", "normal", "miss")


# ---- 2. the round cap ------------------------------------------------------

def test_online_rounds_are_local_rounds():
    assert battle.ROUNDS_ONLINE == battle.ROUNDS_LOCAL == 20


def test_a_duel_ends_in_a_knockout_like_a_battle_does():
    """At the old 5-round cap, ~a third of duels ended standing."""
    import random as _r
    ends = {"ko": 0, "other": 0}
    for i in range(200):
        rng = _r.Random(i).random
        me = battle.Side.of_card(battle.battle_card(_fit_pet()))
        foe = battle.Side.of_card(battle.battle_card(_fit_pet()))
        _seq, hhp, ghp = battle.generate(me, foe, rounds=battle.ROUNDS_ONLINE,
                                         rng=rng)
        ends["ko" if (hhp <= 0 or ghp <= 0) else "other"] += 1
    assert ends["other"] <= 2, ends


def _fit_pet():
    p = Pet(num=297, stage="Mega", attribute="Vaccine")
    p.hunger = p.strength = 4
    p.weight = p._base_weight()
    p.energy = p.max_energy
    p.battles, p.wins = 40, 25
    return p


# ---- 3. one panel, whole bout ---------------------------------------------

def test_the_arena_never_blinks_back_to_a_text_card():
    """One panel from the bar to the verdict: it used to be rebuilt per volley
    and dropped in between, which is what made a duel feel like a spreadsheet."""
    host, guest = _duo()
    _lock(host, "mega")
    _lock(guest, "normal")
    panel = host.bshow
    assert panel is not None
    seen_phases = set()
    for _ in range(TICK_BUDGET):
        host.anim()
        if host.bshow is None:
            pytest.fail("the duel dropped its panel mid-bout")
        assert host.bshow is panel, "the duel rebuilt its panel"
        seen_phases.add(host.bshow.phase)
        if host.bphase == "over":
            break
    assert host.bphase == "over", "the duel never finished on its own"
    assert "anim" in seen_phases
    assert panel.phase == "result", panel.phase
    assert panel.duel_result is not None


def test_the_duel_announces_its_own_verdict():
    host, guest = _duo()
    _lock(host, "mega")
    _lock(guest, "miss")
    for _ in range(TICK_BUDGET):
        host.anim()
        if host.bphase == "over":
            break
    assert host.bphase == "over"
    note = host.bshow._result_note()
    assert "record" in note
    assert host.bt_outcome
    assert host.bt_reward and host.bt_reward.startswith("+")


def test_the_two_clients_agree_on_who_won():
    """Both sides file the ladder from their own replay; disagreement is how
    the monthly ladder used to credit nothing."""
    host, guest = _duo()
    _lock(host, "mega")
    _lock(guest, "miss")
    for _ in range(TICK_BUDGET):
        host.anim()
        guest.anim()
        if host.bphase == "over" and guest.bphase == "over":
            break
    assert host.bphase == guest.bphase == "over"
    hw = "WIN" in host.bt_outcome
    gw = "WIN" in guest.bt_outcome
    assert hw != gw or ("DRAW" in host.bt_outcome and "DRAW" in guest.bt_outcome)


def test_space_hurries_a_volley_and_escape_still_forfeits():
    host, guest = _duo()
    _lock(host, "mega")
    _lock(guest, "normal")
    host.anim()
    panel = host.bshow
    if panel.phase == "anim" and len(panel.timeline) > 1:
        panel.i = 0
        host._key_battle("space")
        assert panel.i == len(panel.timeline) - 1
    host._key_battle("escape")
    assert host.phase == "lobby"
    assert host.client.reports and host.client.reports[-1][0] is False


# ---- the stalls (2026-07-30, Joel: "fix the never-reveal stall too") -------

def test_a_rival_who_never_reveals_no_longer_hangs_the_bout():
    """A peer can lock (so its commit lands) and then simply stop.  This side
    used to sit in "commit" forever with ESC as the only exit."""
    host, guest = _duo()
    _lock(host, "mega")
    host.bt_peer_commit = hashlib.sha256(b"77:mega").hexdigest()   # they bound...
    host.client.peer = None                                        # ...then went quiet
    assert host.bphase == "commit"
    for _ in range(lobbyscreen.REVEAL_TIMEOUT_T + 5):
        host.anim()
        if host.bphase == "over":
            break
    assert host.bphase == "over", "the duel still hangs on a silent rival"
    assert "never answered" in host.bt_outcome
    assert host.battle is None


def test_the_reveal_wait_outlasts_the_rivals_own_auto_lock():
    """A rival still working the bar is not stalling: their bar locks itself at
    DUEL_AUTOLOCK_T, so a shorter wait here would void healthy bouts."""
    assert lobbyscreen.REVEAL_TIMEOUT_T > battlescreen.DUEL_AUTOLOCK_T


def test_a_slow_rival_inside_the_window_still_gets_its_duel():
    host, guest = _duo()
    _lock(host, "mega")
    for _ in range(lobbyscreen.REVEAL_TIMEOUT_T - 50):     # nearly out of patience
        host.anim()
    assert host.bphase == "commit", "voided a rival who was still coming"
    _lock(guest, "normal")                                  # they lock at last
    assert host.battle is not None and host.bphase == "fight"


def test_the_rounds_still_advance_with_no_arena_at_all():
    """The panel is optional (built in a try/except so presentation can never
    void a fight); the ROUND PUMP is not.  Without this, a duel whose panel
    failed to build sat in "fight" forever."""
    host, guest = _duo()
    _lock(host, "mega")
    _lock(guest, "normal")
    host.bshow = None                       # as if the arena had failed to build
    for _ in range(TICK_BUDGET):
        host.anim()
        if host.bphase == "over":
            break
    assert host.bphase == "over", "a panel-less duel never finishes"
    assert host.bt_outcome


# ---- the card (0.5.323, Joel: "wheres the status card informatio like the
#      other battles??? ... ITS SOMETHING I ALREADY HAD YOU FUCKING FIX") -----

def test_a_duel_wears_the_battle_card_like_every_other_fight():
    """statusbox.painter_for walks `.sub` to the deepest panel so one battle
    painter serves every fight wherever it runs (the cup/adventure ruling,
    2026-07-22).  The duel held its panel in `bshow`, so the walk stopped at
    the lobby and an online bout wore the LOBBY's card."""
    from tuipet import statusbox
    host, guest = _duo()
    assert host.sub is host.bshow, "the duel does not hand its card down"
    painter = statusbox.painter_for(host)
    assert painter is not None
    # a resolved SUB painter is the dispatcher's wrapper lambda; the lobby's
    # own painter is statusbox.lobby itself.  Identity, not names.
    assert painter is not statusbox.lobby, "a duel is still wearing the lobby card"


def test_the_card_follows_the_duel_and_gives_it_back():
    """Only a DUEL panel takes the card: the jogress shim and the plain lobby
    keep their own, and the card comes home when the bout ends."""
    from tuipet import statusbox
    host, guest = _duo()
    assert statusbox.painter_for(host) is not statusbox.lobby
    _lock(host, "mega")
    _lock(guest, "normal")
    for _ in range(TICK_BUDGET):
        host.anim()
        if host.bphase == "over":
            break
    assert statusbox.painter_for(host) is not statusbox.lobby  # through the result
    host._key_battle("enter")                                   # back to the lobby
    assert host.sub is None
    assert statusbox.painter_for(host) is statusbox.lobby


def test_the_card_paints_a_duel_without_a_local_battle_object():
    """The painter reads m.battle, which is None for the whole duel (the fight
    lives in the seeded engine, not a local Battle).  It must still draw HP,
    the foe, and the locked grade."""
    from tuipet import statusbox
    host, guest = _duo()
    _lock(host, "mega")
    assert host.bshow.battle is None
    assert host.bshow.locked == "mega"

    painted = {}

    class _Stats:
        border_subtitle = ""

        def update(self, text):
            painted["body"] = text

    class _App:
        pet = host.pet
        mode = host.bshow
        stats_w = _Stats()

    statusbox.battle(_App())
    body = painted.get("body", "")
    assert "You" in body and "Foe" in body, body
    assert "mega" in body.lower(), f"the locked grade is missing:\n{body}"
