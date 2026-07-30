"""THE JOGRESS HANDSHAKE, end to end (audit 2026-07-30, Joel: "look at jogress
too... make sure thats all wired up correctly").

Two REAL wired panels walk the whole fusion: payload exchange, both sides'
resolve_online, the two-phase commit, and the actual fuse.  The pairing under
test is the one Joel is going to test with -- BlitzGreymon (#297, ver1) +
CresGarurumon (#398, ver2) -> Omnimon Alter-S (#399) -- a LINES_SPEC §6 DM20
capstone declared from BOTH parents, so the fusion is mutual.

Why this file exists: the pairing resolves through two channels that can
disagree.  A CresGarurumon with no line_id has an EMPTY fusion list and lands
in the one-sided COMPANION role instead (it lends its power and stays itself).
Both outcomes are legal canon -- which is exactly why the mutual case needs a
pin, or a silently line-less partner would look like a working fusion while
only one pet actually changed.
"""
from tuipet import data, jogress, lines as lines_mod, lobbyscreen
from tuipet.net import LobbyState
from tuipet.pet import DP_MAX, Pet


class _WiredClient:
    def __init__(self, state, me_id):
        self.state, self.me_id, self.peer = state, me_id, None
        self.outbox = []

    def respond(self, *a, **k):
        pass

    def update_pet(self, *a, **k):
        pass

    def relay(self, pid, payload):
        self.outbox.append(payload)
        if self.peer is not None:
            self.peer._on_relay({"from_id": self.me_id, "payload": payload})


def _mk(num, line_id, name):
    _, by = data.load_sprites()
    rec = by[num]
    p = Pet(num=num, name=name, stage=rec["stage"], attribute=rec["attribute"])
    p.hatched = True
    p.hunger = p.strength = 4
    p.weight = p._base_weight()
    p.energy = p.max_energy
    p.dp = DP_MAX                       # Pen20: a jogress takes the FULL meter
    p.world_seconds = 12 * 60.0         # midday: no bedtime refusal
    p.compliance = True
    p.line_id = line_id
    return p


def _panels(a_num, a_line, b_num, b_line):
    out = []
    for i, (num, line, nm) in enumerate(((a_num, a_line, "blitz"),
                                         (b_num, b_line, "cres"))):
        st = LobbyState()
        st.connected = True
        st.me_id = 20 + i
        st.roster = [{"id": 20, "name": "tamerA", "pet": {}, "live": True},
                     {"id": 21, "name": "tamerB", "pet": {}, "live": True}]
        pan = lobbyscreen.LobbyPanel(
            _mk(num, line, nm),
            lambda n, pw, card, st=st, i=i: _WiredClient(st, 20 + i),
            name=f"tamer{'AB'[i]}", pw="x")
        out.append(pan)
    a, b = out
    a.partner, b.partner = (21, "tamerB"), (20, "tamerA")
    # same ordering as a duel: both seated before either payload lands
    a._enter_session(21, "tamerB", "jogress", True)
    b._enter_session(20, "tamerA", "jogress", False)
    pending = [(a, list(a.client.outbox)), (b, list(b.client.outbox))]
    a.client.outbox.clear()
    b.client.outbox.clear()
    a.client.peer, b.client.peer = b, a
    for sender, msgs in pending:
        other = b if sender is a else a
        for m in msgs:
            other._on_relay({"from_id": sender.client.me_id, "payload": m})
    return a, b


def _yes(pan):
    """Press Enter like a player: the first press skips the fusion CONVERGE
    animation (jshow.phase == "fusing"), the next one is the confirm."""
    for _ in range(4):
        if pan.j_confirmed or pan.phase != "jogress":
            return
        pan._key_jogress("enter")


def _no(pan):
    """Decline -- also past the converge."""
    for _ in range(4):
        if pan.phase != "jogress":
            return
        if pan.jshow is not None and pan.jshow.phase == "fusing":
            pan._key_jogress("enter")
            continue
        pan._key_jogress("escape")
        return


# ---- the data itself -------------------------------------------------------

def test_the_capstone_is_declared_from_both_parents():
    """ver1 gives BlitzGreymon the door via 398; ver2 gives CresGarurumon the
    same door via 297.  Both halves must exist or the fusion is one-sided."""
    ver1 = lines_mod.load_lines()["ver1"]
    ver2 = lines_mod.load_lines()["ver2"]
    assert any(r["num"] == 399 and r["jogress"] == 398
               for r in ver1["children"].get(297, []))
    assert any(r["num"] == 399 and r["jogress"] == 297
               for r in ver2["children"].get(398, []))


def test_the_door_is_partner_exact_not_attribute_shaped():
    """`partners` empty is load-bearing: it stops the attribute fallback from
    opening a capstone with a stand-in of the right attribute."""
    blitz = _mk(297, "ver1", "blitz")
    doors = [o for o in jogress.options(blitz) if o["num"] == 399]
    assert doors, "the capstone door did not open for a ver1 BlitzGreymon"
    assert doors[0]["partners"] == []
    assert doors[0]["partner_num"] == 398


# ---- the handshake ---------------------------------------------------------

def test_both_sides_resolve_the_same_fusion():
    a, b = _panels(297, "ver1", 398, "ver2")
    assert a.jphase == "result" and b.jphase == "result", (a.jphase, b.jphase)
    assert a.jresult["num"] == b.jresult["num"] == 399
    assert not a.jresult.get("companion") and not b.jresult.get("companion")
    assert a.jshow is not None and b.jshow is not None      # the real scene plays


def test_a_lineless_partner_is_a_companion_not_a_fusion():
    """The trap this file was written for: same species, no line, and the
    fusion quietly becomes one-sided."""
    a, b = _panels(297, "ver1", 398, "")
    assert a.jresult and a.jresult["num"] == 399             # I still fuse
    assert b.jresult and b.jresult.get("companion")          # they only lend
    assert b.jshow is None                                   # text page, no scene


def test_the_fusion_needs_BOTH_yeses_and_then_changes_both_pets():
    a, b = _panels(297, "ver1", 398, "ver2")
    assert a.j_peer_two_phase and b.j_peer_two_phase
    _yes(a)                                     # one yes is not enough
    assert a.pet.num == 297 and b.pet.num == 398
    assert a.j_confirmed and not a.j_partner_confirmed
    _yes(b)                                     # ...and now both
    assert a.pet.num == 399, "the confirming side never fused"
    assert b.pet.num == 399, "the partner never fused"


def test_either_side_can_decline_and_nobody_fuses():
    a, b = _panels(297, "ver1", 398, "ver2")
    _no(b)
    assert a.pet.num == 297 and b.pet.num == 398
    assert a.phase == "lobby" and b.phase == "lobby"


def test_a_confirmed_side_can_still_back_out_of_a_silent_partner():
    """No stall: ESC is live even after confirming, so a partner who goes quiet
    at the result screen can never trap you (the duel's reveal stall has no
    twin here)."""
    a, b = _panels(297, "ver1", 398, "ver2")
    _yes(a)
    assert a.j_confirmed and a.phase == "jogress"
    a._key_jogress("escape")
    assert a.phase == "lobby"
    assert a.pet.num == 297 and b.pet.num == 398


def test_a_partner_that_vanishes_ends_the_fusion():
    a, b = _panels(297, "ver1", 398, "ver2")
    a._on_relay({"from_id": 21, "payload": {"kind": "jogress", "abort": True}})
    assert a.jphase == "failed" or a.phase == "lobby"
    assert a.pet.num == 297


def test_the_fusion_spends_the_meter_and_the_energy():
    """canon PhysicalState.jogress: DP to zero, energy -66% of max."""
    a, b = _panels(297, "ver1", 398, "ver2")
    e0, max_e = a.pet.energy, a.pet.max_energy
    _yes(a)
    _yes(b)
    assert a.pet.dp == 0
    assert a.pet.energy < e0
    import math
    assert a.pet.energy == max(0, e0 + math.ceil(-0.66 * max_e))


# ---- the cinematic, timed against canon (0.5.324) --------------------------
#
# Joel: "i thought the actual fusion part of the animation was supposed to be
# longer or something. if this is how dsprite and dvpet does it, whatever" --
# it was NOT how DVPet does it.  SpriteAnim.startJogressAnim runs to
# `_interval * 32` and `_interval = targetFPS / 10`, so one interval is one
# 0.1s tick: canon is a 3.2-second beat with pose flips on the eights.
# We shipped 22 ticks and a single 0.6s flip.

def test_the_converge_runs_for_canons_full_beat():
    from tuipet import jogressscreen as js
    assert js.FUSE_STEPS == 32, "canon's startJogressAnim ends at interval*32"
    assert js.FUSE_STEPS / 10 == 3.2


def test_the_parents_flip_pose_on_the_eights():
    """canon sets pose 1 at frame 0, 5 at 8, 1 at 16, 5 at 24."""
    from tuipet import jogressscreen as js
    assert js.POSE_BEAT == 8
    poses = [1 if (i // js.POSE_BEAT) % 2 == 0 else 5 for i in range(js.POSE_T)]
    runs = []
    for p in poses:
        if not runs or runs[-1][0] != p:
            runs.append([p, 0])
        runs[-1][1] += 1
    assert [r[0] for r in runs] == [1, 5, 1], runs
    assert all(r[1] == 8 for r in runs), runs


def test_the_connect_card_is_a_real_rip_that_marches():
    """canon jogressFlash alternates jogressConnectStart <-> ...Flash every
    `_interval * 2`.  The art is EXTRACTED (tools/extract_jogress_overlay.py),
    never drawn -- if the atlas is missing the fusion must still run."""
    from tuipet import jogressscreen as js
    assert js.FLASH_BEAT == 2
    assert len(js.CONNECT_FRAMES) == 2, "the connect card needs both frames"
    a, b = js.CONNECT_FRAMES
    assert len(a) == len(b) and len(a[0]) == len(b[0]), "frames must share a box"
    assert a != b, "the stripes do not march"
    assert set("".join(a)) <= {"0", "1"}


def test_the_wait_after_your_yes_plays_the_connect_card():
    a, b = _panels(297, "ver1", 398, "ver2")
    _yes(a)                                     # my yes is in, theirs is not
    assert a.j_confirmed and not a.j_partner_confirmed
    assert a.jshow is not None and a.jshow.phase == "waiting"
    first = a.jshow.text()
    for _ in range(3):                          # the card animates while waiting
        a.jshow.anim()
    assert a.jshow.text() is not None
    assert first is not None
    _yes(b)                                     # they answer -> the fusion lands
    assert a.pet.num == 399 and b.pet.num == 399


def test_a_missing_connect_atlas_never_blocks_a_fusion():
    from tuipet import jogressscreen as js
    saved = js.CONNECT_FRAMES
    try:
        js.CONNECT_FRAMES = []
        a, b = _panels(297, "ver1", 398, "ver2")
        _yes(a)
        assert a.jshow.text() is not None       # a bare scene, not a crash
        _yes(b)
        assert a.pet.num == 399
    finally:
        js.CONNECT_FRAMES = saved
