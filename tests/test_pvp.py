"""Online PvP battle (lobbyscreen): host-authoritative auto-clash on the DM20 engine.

Two panels ferry relays to each other through a fake client; the host resolves the
whole clash and relays the outcome, and both sides must land on a consistent, mirrored
result.  record_battle's persistence side effects are sandboxed by conftest.
"""
from tuipet import lobbyscreen, battle, species
from tuipet.pet import Pet


class _FakeClient:
    peer = None

    def relay(self, pid, payload):
        # deliver to the peer, tagged with the id the RECEIVER knows the sender by
        self.peer._on_relay({"from_id": self.peer.partner[0], "payload": payload})

    def update_pet(self, card):
        pass


def _panel(pet, partner_id, partner_name):
    p = lobbyscreen.LobbyPanel(pet, on_connect=lambda *a, **k: None)
    p.partner = (partner_id, partner_name)
    p.client = _FakeClient()
    p.phase = "battle"
    return p


def _wired(host_pet, guest_pet):
    host = _panel(host_pet, "G", "Guest")
    guest = _panel(guest_pet, "H", "Host")
    host.client.peer = guest
    guest.client.peer = host
    host.is_host, host.bphase = True, "card"
    guest.is_host, guest.bphase = False, "card"
    # exchange cards: guest gets the host's, host gets the guest's -> host resolves + relays
    guest._battle_begin(battle.battle_card(host_pet))
    host._battle_begin(battle.battle_card(guest_pet))
    return host, guest


def test_pvp_reaches_consistent_mirrored_outcome():
    host_pet = Pet(num=next(x["num"] for x in species.roster() if x["stage"] == "Adult"), stage="Adult")
    host_pet.vaccine = 20
    guest_pet = Pet(num=next(x["num"] for x in species.roster() if x["stage"] == "Child"), stage="Child")
    host, guest = _wired(host_pet, guest_pet)

    assert host.bphase == "over" and guest.bphase == "over"
    # HP mirrors across the two clients
    assert host.my_hp == guest.opp_hp and host.opp_hp == guest.my_hp
    # exactly one winner, or a mutual draw
    win = "★ YOU WIN! ★"
    assert (host.bt_outcome == win) != (guest.bt_outcome == win) or host.bt_outcome == "DRAW"


def test_pvp_guest_records_its_own_result():
    host_pet = Pet(num=next(x["num"] for x in species.roster() if x["stage"] == "Adult"), stage="Adult")
    guest_pet = Pet(num=next(x["num"] for x in species.roster() if x["stage"] == "Child"), stage="Child")
    host, guest = _wired(host_pet, guest_pet)
    b0 = guest_pet.battles
    guest._key_battle("enter")                    # closing the result records the guest's battle
    assert guest_pet.battles == b0 + 1
    assert guest.phase == "lobby"
