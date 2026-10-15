"""THE SLEEP AUDIT — the pins (2026-07-25).

Joel: "lets do a full blown sleep audit next."

S1 (FIXED) — THE RAID BOARD FOUGHT A SLEEPING PET.  The raid gate landed
in the battle audit (2026-07-25) copying the BODY half of the house rule
— "a volley is a fight you CHOOSE, so the body answers first" — and left
the SLEEP half behind.  Measured on the real panel: a sleeping pet threw
a full volley with `asleep=True, disturb=0`, the bout launched, and the
pet slept through its own raid.  It was the ONLY fight door in the game
that neither woke the sleeper nor refused: the home key (`can_battle`),
both cups (`can_enter`), training, adventure, jogress and every care key
wake it and bill the disturb; the lobby is the deliberate opposite and
refuses without touching the pet, because a stranger's invite is not the
player's finger.  Fixed in raidscreen.key(): the sleeper answers first.

S2 (DOC, not behaviour) — LINES_SPEC §5 said a lit sleeper logs "the
once-per-night lights mistake".  The shipped device books one every 120
lit minutes (measured: 1.5/3.5/5.5/7.5/9.5h into a lit 10-hour night, so
~5 a night), which is canon-derived and deliberate — `_tick_asleep` says
so in a dated comment.  The CONTRACT was the wrong half; §5 now matches
the device.  The behaviour is pinned here so the next reader of that
paragraph doesn't "fix" the code to it.

CLEARED, not defects (each was measured before it was believed):
  * Waking a sleeper costs a DISTURB, never a care mistake — and the
    disturb is real currency: 208 corpus forms gate on it and a single
    one flips `select()`.  An earlier reading of "mistakes 0->1" on a fed
    sleeper was an OVERFEED slip on a full pet, which never woke at all.
  * Per-form bedtimes (20:00 / 21:00 / 22:00 / 23:00 / midnight) with a
    7:00-sharp wake for every one — LINES_SPEC §5 exactly.
  * `battle_condition()` returning None on a sleeper is BY DESIGN: it is
    documented as the pure condition half, and its callers own the sleep
    clause.  After S1 they all do.
"""
import pytest

from tuipet import lines as L
from tuipet import tournament
from tuipet.pet import DAY_LENGTH, Pet
from tuipet.raidscreen import RaidPanel

# real line rows, one per distinct corpus bedtime (load_lines, 2026-07-25)
BEDTIME_ROWS = {"20:00": ("ver1", 1411), "21:00": ("ver1", 1455),
                "22:00": ("ver1", 37), "23:00": ("ver1", 93),
                "24:00": ("ver1", 102), "00:00": ("nsp", 286)}


def _liner(num=1455, line_id="ver1", hour=23.0, **kw):
    """A LINE pet — the only kind a player ever hatches.  A bare Pet(...)
    has no `line_id`, so it falls back to the legacy pressure model and
    never sees the wall-clock bedtime this file is about."""
    p = Pet(num=num, stage="Champion", attribute="Vaccine", obedience=500)
    p.line_id = line_id
    p.energy, p.hunger, p.strength = p.max_energy, 4, 4
    p.weight = p._base_weight()
    p.world_seconds = hour * 60.0
    p.evo_blocked = True                  # isolate the body from the charts
    for k, v in kw.items():
        setattr(p, k, v)
    return p


def _sleeper(**kw):
    """A line pet actually asleep, in a DARK room (no lights mistakes)."""
    p = _liner(**kw)
    p.lights = False
    for _ in range(400):
        p.tick(1.0)
        p.lights = False
        if p.asleep:
            return p
    raise AssertionError("the fixture never fell asleep")


class _FakeRelay:
    """The raid gate's answer: a boss standing, attempts left."""
    raid = {"attempts": 3, "now": 100,
            "boss": {"start": 0, "hp": 5000, "max_hp": 5000,
                     "num": 200, "name": "Boss"}}

    def raid_get(self):
        pass

    def raid_hit(self, dealt):
        pass


# ---- S1: the raid board -------------------------------------------------

def test_the_raid_board_does_not_fight_a_sleeping_pet():
    """The bug, pinned: press SPACE on a sleeper and a bout used to
    launch with the pet still asleep and no disturb billed."""
    p = _sleeper()
    panel = RaidPanel(p, connect=False, client=_FakeRelay())
    panel.key("space")
    assert panel.sub is None, "a sleeping pet threw a raid volley"
    assert not p.asleep, "the poke must wake it, like every sibling door"
    assert p.disturb == 1, "the poke must bill the disturb"


def test_the_second_press_volleys():
    """Waking is a REFUSAL of that press, not a lost turn — exactly the
    can_battle/can_enter shape.  Press again and the fight happens."""
    p = _sleeper()
    panel = RaidPanel(p, connect=False, client=_FakeRelay())
    panel.key("space")
    panel.key("space")
    assert panel.sub is not None
    assert p.disturb == 1, "the second press must not bill a second disturb"


def test_an_awake_pet_still_raids():
    """The fix must not cost the ordinary player a thing."""
    p = _liner(hour=12.0)
    panel = RaidPanel(p, connect=False, client=_FakeRelay())
    panel.key("space")
    assert panel.sub is not None
    assert p.disturb == 0


def test_the_raid_board_still_asks_the_body():
    """S1 added the sleep clause ABOVE the body gate; the body gate that
    the battle audit installed must survive underneath it."""
    p = _liner(hour=12.0, injured=True)
    panel = RaidPanel(p, connect=False, client=_FakeRelay())
    panel.key("space")
    assert panel.sub is None
    assert panel.msg == "Too hurt to fight."


# ---- the door parity table ----------------------------------------------

@pytest.mark.parametrize("door,state", [
    pytest.param(lambda p: p.can_battle(), {}, id="home-battle-key"),
    pytest.param(lambda p: tournament.can_enter(p), {}, id="cup"),
    pytest.param(lambda p: p.can_train(), {}, id="training"),
    pytest.param(lambda p: p.praise(), {}, id="praise"),
    pytest.param(lambda p: p.scold(), {}, id="scold"),
    pytest.param(lambda p: p.heal(), {"sick": True}, id="care-pill"),
    pytest.param(lambda p: p.heal_bandage(), {"injured": True}, id="bandage"),
    pytest.param(lambda p: p.feed_meat(), {"hunger": 2}, id="feed"),
])
def test_every_player_poke_that_lands_wakes_the_sleeper(door, state):
    """ONE law across every door the player's own finger opens: one
    disturb, and never a care mistake."""
    p = _sleeper(**state)
    door(p)
    assert not p.asleep
    assert p.disturb == 1
    assert p.care_mistakes == 0


def test_a_refused_care_act_leaves_the_sleeper_alone():
    """The other half of the feed rule, documented at feed_meat: "Feeding
    a sleeper DISTURBS it first (refusals don't wake it)".  A sick pet
    head-shakes at meat, and the head-shake costs nothing.  NOTE: the
    FIGHT doors order this the other way (can_battle takes the sleep
    clause ABOVE the body gate, so a sick sleeper wakes to be refused) —
    both orderings are canon-dated; see SLEEP_AUDIT_2026_07_25.md §4."""
    p = _sleeper(sick=True)
    p.feed_meat()
    assert p.asleep
    assert p.disturb == 0


def test_a_strangers_invite_never_touches_the_pet():
    """The deliberate opposite, and the reason the parity table above is
    a rule about the PLAYER's finger: the lobby refuses a remote invite
    without waking, without a disturb (asleep sweep 2026-07-06)."""
    from tuipet.lobbyscreen import LobbyPanel

    class _Stub:                       # the gate reads nothing but .pet
        pass

    stub = _Stub()
    stub.pet = _sleeper()
    assert LobbyPanel._session_gate(stub, "battle") == "zzz… asleep"
    assert stub.pet.asleep and stub.pet.disturb == 0


def test_waking_a_sleeper_is_never_a_care_mistake():
    """The disturb is the price; the care-mistake ladder is NOT.  (The
    one measured 'mistake' on a fed sleeper was an overfeed on a full
    pet — an act that never woke it.)"""
    p = _sleeper()
    p.clean()
    assert p.disturb == 1
    assert p.care_mistakes == 0


def test_the_disturb_is_real_evolution_currency():
    """Waking it costs something that MATTERS, or the price is a lie."""
    from tuipet import data, evolution
    reqs = data.load_requirements()
    gated = [n for n, r in reqs.items() if r["disturb"][0] != "None"]
    assert len(gated) > 150, "the disturb gate should span the corpus"
    # `select()` breaks ties randomly, so pin the DETERMINISTIC layer it
    # scores from: a form whose gate reads disturbs scores higher for a
    # pet that has some, and sits further from the threshold.
    num = min(n for n in gated if reqs[n]["disturb"][0] == "GreaterThan")
    calm, poked = _liner(hour=12.0), _liner(hour=12.0, disturb=5)
    calm.evo_blocked = poked.evo_blocked = False
    assert evolution.fulfilled(poked, num) > evolution.fulfilled(calm, num)
    assert evolution.deviation(poked, num) > evolution.deviation(calm, num)


# ---- the night itself ---------------------------------------------------

@pytest.mark.parametrize("bedtime,row", sorted(BEDTIME_ROWS.items()))
def test_every_line_form_wakes_at_seven_sharp(bedtime, row):
    """LINES_SPEC §5: bedtime is per-form, the wake is universal."""
    line_id, num = row
    p = _liner(num=num, line_id=line_id)
    assert L.bedtime_minutes(p) == (int(bedtime.split(":")[0]) % 24) * 60
    assert p.WAKE_MINUTE == 420


def test_the_night_is_a_window_not_an_energy_budget():
    """A 21:00 sleeper sleeps ten hours, on the wall clock."""
    p = _liner(hour=20.5)
    p.lights = False
    fell = woke = None
    for i in range(int(DAY_LENGTH)):
        was = p.asleep
        p.tick(1.0)
        p.lights = False
        if not was and p.asleep and fell is None:
            fell = i
        if was and not p.asleep and fell is not None:
            woke = i
            break
    assert woke is not None, "it never woke"
    assert 9.5 <= (woke - fell) / 60 <= 10.5


def test_the_nightly_ritual_refills_the_tank():
    """Lights out AT bedtime — the ritual §5 describes — is a full night
    and a full tank."""
    p = _liner(hour=20.9, energy=2)
    p.lights = True
    fell = woke = None
    for i in range(int(DAY_LENGTH)):
        was = p.asleep
        p.tick(1.0)
        if p.asleep:
            p.lights = False            # the player turns them off
        if not was and p.asleep and fell is None:
            fell = i
        if was and not p.asleep and fell is not None:
            woke = i
            break
    assert (woke - fell) / 60 == pytest.approx(10.0, abs=0.5)
    assert p.energy == p.max_energy


def test_lights_out_before_bedtime_is_a_doze_not_the_night():
    """§5: lights-out OUTSIDE the window is the shallow daytime doze, and
    a drained pet dozes back to HALF a tank (recovery doze, v0.5.191) —
    it is not the night, and it must not be mistaken for a short one."""
    p = _liner(hour=20.5, energy=0)      # 20:30, half an hour before bed
    p.lights = False
    for _ in range(int(DAY_LENGTH)):
        was = p.asleep
        p.tick(1.0)
        p.lights = False
        if was and not p.asleep:
            break
    assert p.energy == p.max_energy // 2


# ---- S2: the lit night --------------------------------------------------

def test_a_lit_night_books_one_mistake():
    """Care call #15 = A (Joel 2026-10-15): once per night again, after a
    ten-minute grace (the canon cadence booked ~5 a lit night)."""
    p = _liner(hour=20.5)
    p.lights = True
    hits, slept = [], False
    for i in range(int(DAY_LENGTH)):
        before = p.care_mistakes
        was = p.asleep
        p.tick(1.0)
        p.lights = True                       # the player never gets up
        if p.care_mistakes > before:
            hits.append(i / 60)
        slept = slept or p.asleep
        if slept and was and not p.asleep:
            break                             # the night, and only the night
    assert len(hits) == 1, f"a fully lit night costs one, saw {hits}"


def test_the_obedience_ding_lands_once_per_night():
    """The half of the lights rule that IS a latch (_lit_obed_hit)."""
    p = _liner(hour=20.5)
    p.lights = True
    drops, slept = 0, False
    for _ in range(int(DAY_LENGTH)):
        before = p.obedience
        was = p.asleep
        p.tick(1.0)
        p.lights = True
        if p.obedience != before:
            drops += 1
        slept = slept or p.asleep
        if slept and was and not p.asleep:
            break                       # the night is over; the DAY has its
            #                             own obedience sources (hunger call)
    assert drops == 1


# ---- the morning --------------------------------------------------------

@pytest.mark.parametrize("frac,weary", [(1.0, False), (0.5, False),
                                        (0.4, True), (0.05, True)])
def test_the_good_morning_note_tells_the_truth_about_the_tank(monkeypatch,
                                                              frac, weary):
    """v0.5.177, Joel: "my mon woke up 'beaming' with only one energy
    bar".  The mood ROLL stays canon; the NOTE reports the night."""
    from tuipet import petbody
    p = _sleeper(hour=6.0)
    p.energy = max(1, int(p.max_energy * frac))
    p.nap = False
    monkeypatch.setattr(petbody.random, "randrange", lambda n: 2)  # good roll
    p._wake()
    assert ("still weary" in p.wake_note) is weary, p.wake_note


def test_a_disturbed_wake_leaves_no_stale_morning_note():
    p = _sleeper()
    p.wake_note = "STALE"
    p.clean()
    assert p.wake_note == ""


# ---- the item-sleep law -------------------------------------------------

@pytest.mark.parametrize("key,wakes,disturbs", [
    ("music_player", True, False),      # the alarm: its whole point
    # (cold_shower retired 2026-07-27 -- its rude wake was Music Player's
    #  niche done worse; the disturb-inside grammar it pinned lives on in
    #  the "anything else" row below)
    ("sleeping_pill", False, False),    # pointless on a sleeper
    ("ball", True, True),               # anything else DISTURBS, then applies
])
def test_an_item_on_a_sleeper(key, wakes, disturbs):
    p = _sleeper()
    p.add_item(key)
    p.use_item(key)
    assert (not p.asleep) is wakes
    assert (p.disturb > 0) is disturbs


# ---- the time law -------------------------------------------------------

def test_sleep_only_runs_on_the_main_view():
    """TIME LAW: one tick site, and it returns behind ANY menu — so a pet
    can neither fall asleep nor wake behind a panel."""
    import inspect

    from tuipet import app
    src = inspect.getsource(app)
    assert src.count("self.pet.tick(") == 1, "a second tick site appeared"
    body = src.split("self.pet.tick(")[0]
    assert "if self.mode is not None:" in body


# ---- the status card ----------------------------------------------------

@pytest.mark.parametrize("state", [
    {}, {"poop": 3, "hunger": 0}, {"sick": True, "injured": True, "poop": 2},
    {"nap": True},
])
def test_the_sleep_status_card_fits_its_box(state):
    from rich.text import Text

    from tuipet import statusbox
    p = _sleeper(**state)
    p.asleep = True                       # hold the state the card renders
    word = p.status_word()
    lines = [statusbox.status_line(word, statusbox.care_deco(p, word))]
    lines += list(statusbox.home_lines(p))
    for line in lines:
        assert len(Text.from_markup(str(line)).plain) <= statusbox.CARD_W


def test_a_wake_cancels_the_pills_owed_lights_out():
    """Sleep audit r2 (2026-07-28): the pill owes the room to its eat show
    (0.5.288) -- but a wake DURING the show (alarm, disturb) left the debt
    armed, and the fx-end hook then darkened the room on an AWAKE pet."""
    p = _sleeper()
    p._wake()                                     # any wake path funnels here
    p.add_item("sleeping_pill")
    p.use_item("sleeping_pill")
    assert p.asleep and p.pending_lights_out and p.lights
    p.add_item("music_player")
    p.use_item("music_player")                    # the clean wake, mid-show
    assert not p.asleep
    assert not p.pending_lights_out, "the debt outlived the sleep it served"
    assert p.lights, "the room must stay lit around an awake pet"
