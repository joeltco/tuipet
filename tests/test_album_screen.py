"""The album SCREEN — the browsable bestiary over the persistence album
(built 2026-07-21).  The count on digicore TROPHIES fronted a book that
didn't exist; these pins hold the book and its scoreboard to ONE source
(data.album_roster) and the reveal language to the shipped conventions:
undiscovered = "???" + silhouette, discovered = name, stage and the real
rip.  A leaked name here is a spoiler bug, not a cosmetic one."""
from tuipet import data, digicore, persistence
from tuipet.albumscreen import AlbumPanel
from tuipet.digicorescreen import DigiCorePanel
from tuipet.pet import Pet


def _pet():
    return Pet.from_num(29)


def test_the_book_and_its_scoreboard_share_one_denominator():
    """AlbumPanel pages == data.album_roster() == the TROPHIES Album total."""
    pan = AlbumPanel(_pet())
    assert pan.n == len(data.album_roster())
    album_row = dict(digicore._trophy_rows(_pet()))["Album"]
    assert album_row.endswith(f"/{pan.n} discovered")


def test_undiscovered_entries_never_leak_a_name():
    """Fresh device: every list row is a masked '???' — no roster name may
    appear anywhere in the rendered book (the hidden-evo reveal doctrine)."""
    pan = AlbumPanel(_pet())
    plain = pan.text().plain
    assert "???" in plain and "0/" in plain
    _, by = data.load_sprites()
    for num in pan.roster[:9]:                   # the 9 rows on the page
        assert by[num]["name"] not in plain


def test_a_discovered_entry_wears_name_and_stage():
    persistence.album_add(29)
    pan = AlbumPanel(_pet())
    pan.i = pan.roster.index(29)
    plain = pan.text().plain
    assert "Agumon" in plain and "Rookie" in plain
    assert "No. #29" in plain
    assert "1/" in plain.split("\n")[0]          # the header numerator moved


def test_detail_pages_render_seen_sprite_and_unseen_silhouette():
    """Seen detail = the live rip with the info line; unseen = silhouette +
    'not yet discovered', name masked.  Both must actually put PIXELS on the
    page — a blank image is the egg-crash class, not a style choice."""
    persistence.album_add(29)
    pan = AlbumPanel(_pet())
    pan.i = pan.roster.index(29)
    pan.key("enter")
    txt = pan.text()
    assert "AGUMON" in txt.plain and "Rookie" in txt.plain
    assert any("▀" in ln for ln in txt.plain.split("\n"))
    # pixel proof: the blit landed — image cells carry "fg on bg" styles, and
    # an all-background image renders exactly ONE such style
    styles = {str(s.style) for s in txt.spans if " on " in str(s.style)}
    assert len(styles) > 1, "seen detail image rendered blank"
    pan.key("escape")
    pan.i = 0
    pan.key("enter")
    up = pan.text()
    assert "???" in up.plain and "not yet discovered" in up.plain
    _, by = data.load_sprites()
    assert by[pan.roster[0]]["name"] not in up.plain
    sil = {str(s.style) for s in up.spans if " on " in str(s.style)}
    assert len(sil) > 1, "unseen silhouette rendered blank"


def test_key_walk_clamps_and_exits():
    pan = AlbumPanel(_pet())
    pan.key("pageup")
    assert pan.i == 0
    pan.key("pagedown")
    assert pan.i == 8
    for _ in range(3):
        pan.key("up")
    pan.key("enter")
    assert pan.detail
    pan.key("right")
    pan.key("left")
    pan.key("escape")
    assert not pan.detail
    assert pan.key("escape") == ("done", None)


def test_trophies_page_opens_the_album_and_space_still_pages():
    """ENTER on TROPHIES = the album sentinel; SPACE keeps paging (the
    EVOLVES enter-picks/space-pages split).  The page teaches its door."""
    dc = DigiCorePanel(_pet(), start="TROPHIES")
    assert dc.pages[dc.i][0] == "TROPHIES"
    assert "ENTER: the album" in dc.text().plain
    assert dc.key("enter") == ("done", ("album",))
    dc2 = DigiCorePanel(_pet(), start="TROPHIES")
    assert dc2.key("space") is None                 # paged, no sentinel
    assert dc2.pages[dc2.i][0] != "TROPHIES"
    # unknown start titles fall to the cover, and ENTER there stays inert
    cover = DigiCorePanel(_pet(), start="NO-SUCH-PAGE")
    assert cover.i == 0


# --- the route home (gameplay polish #15, 2026-07-22) ------------------------

def test_an_unseen_entry_names_its_route_home():
    """The book was a checklist with the HOW invisible: 'keep raising'
    over hundreds of masked entries while lines.load_lines() knew the
    answer.  Routes name eggs and doors, never masked forms."""
    from tuipet import albumscreen
    assert albumscreen.route_hint(29).startswith("raised on the ")   # a line member
    assert albumscreen.route_hint(492) == "an armor jump reaches it"


def test_every_roster_form_gets_a_route_class():
    from tuipet import albumscreen, data
    hints = {n: albumscreen.route_hint(n) for n in data.album_roster()}
    for n, h in hints.items():
        assert (h.startswith("raised on") or h.endswith("reaches it")
                or h == "keep raising"), (n, h)
    # the map is genuinely informative: the bare fallback is the rare case
    bare = sum(1 for h in hints.values() if h == "keep raising")
    assert bare < len(hints) * 0.1, f"{bare}/{len(hints)} routeless"


def test_the_unseen_detail_page_carries_the_route():
    from tuipet.albumscreen import AlbumPanel
    from tuipet.pet import Pet
    pan = AlbumPanel(Pet(num=100, stage="Champion"))
    unseen = next(i for i, n in enumerate(pan.roster) if n not in pan.seen)
    pan.i, pan.detail = unseen, True
    plain = pan.text().plain
    assert "not yet discovered" in plain
    assert ("raised on" in plain or "reaches it" in plain
            or "keep raising" in plain)
    assert "???" in plain                     # the name mask is untouched
