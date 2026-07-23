"""THE status box — every right-hand card in one module (Joel 2026-07-17:
"MODULIZE THE STATUS BOX").

One card per surface, registry-dispatched; app.py only delegates.  The rule
of this file: **a card may only show LIVE data** — when a system leaves the
game, its rows leave here the same day.  The move itself killed three liars:
the feeding readout's protein/mineral/vitamin bars (the nutrition system was
removed 2026-07-16; the macros are frozen at their 6/6/6 starter values
forever), the DNA card's "spirit/mood" charge bill (both systems are gone —
the real bill is ENERGY, 1/unit on your own Field, doubled off-Field), and
the home card's Power/HP rows (moved/retired earlier the same day).

Every painter takes the app (pet, mode, stats_w, sound) and writes the
26-col card; `card()` is the shared frame.  Fit is pinned by
tests/test_status_box*.py against CARD 26x16.
"""
from __future__ import annotations

from . import backgrounds
from . import data
from . import egg as egg_mod
from . import persistence
from . import theme
from .arena import bar, hearts

CARD_W = 26   # the card interior: #stats width 30 - round border 2 - padding 2
#               (run-off sweep 2026-07-23: wider lines WRAP inside the box and
#               shove the card's tail off the bottom; fit-fixes ship pre-clipped)
DIV = "[dim]" + "─" * CARD_W + "[/]"


# ---- shared helpers (moved from app.py; the old _names stay importable) ----

def gen_subtitle(pet):
    """'gen N', wearing the bought honor when one is worn (the honors board,
    prestige sink 2026-07-14)."""
    t = data.title_name(persistence.get_title_worn())
    return f"gen {pet.generation} · {t}" if t else f"gen {pet.generation}"


def age_compact(seconds):
    """d/h then h/m then m/s -- raw total minutes read as noise on an older
    pet ('4325m40s', status-box audit 2026-07-04)."""
    s = int(max(0, seconds))
    if s >= 86400:
        return f"{s // 86400}d{(s % 86400) // 3600:02d}h"
    if s >= 3600:
        return f"{s // 3600}h{(s % 3600) // 60:02d}m"
    return f"{s // 60}m{s % 60:02d}s"


def care_deco(pet, word=None):
    """The care badges shown beside the status word -- one list, shared by the
    home Stats panel and every card that wants them.  Order is priority: the
    lowest ones drop first on overflow."""
    T = theme
    if word is None:
        word = pet.status_word()
    deco = []
    if pet.asleep and word != "asleep": deco.append("[blue]Zzz[/]")
    if pet.sick and word != "sick": deco.append(f"[{T.NEG}]+sick[/]")
    # (the +tired/+hurt/+med/+bnd/+vit badges left with the fatigue/injury
    # and medicine-item systems; BASIC VPET 2026-07-16)
    if pet.is_frail(): deco.append(f"[{T.NEG}]+frail![/]")
    if pet.poop: deco.append(f"[{T.COIN}]~poop x{pet.poop}[/]")
    # (the ✦care-effect badge left with the Futon's careEffect runtime;
    # strict-DSprite items 2026-07-17)
    # the standing buffs, visible at HOME (QOL 2026-07-23): satiety and
    # auto-clean only ever showed in the transient eat readout, and a
    # hired assistant (billing per visit!) showed nowhere at all.  Lowest
    # priority: they drop first when the need badges pile up.
    def _left(until):
        s = int(until - pet.world_seconds)
        return f"{s // 3600}h" if s >= 3600 else f"{max(1, s // 60)}m"
    full = getattr(pet, "full_until", 0.0)
    if full and pet.world_seconds < full:
        deco.append(f"[{T.POS}]sated {_left(full)}[/]")
    tidy = getattr(pet, "auto_clean_until", 0.0)
    if tidy and pet.world_seconds < tidy:
        deco.append(f"[{T.POS}]tidy {_left(tidy)}[/]")
    if getattr(pet, "auto_care", False):
        deco.append(f"[{T.COIN}]helper[/]")
    return deco


def status_line(status, deco, width=26):
    """Assemble the status word + deco glyphs, bounded to `width` visible cols
    so the Stats box never wraps past its 16-row height. Drops the lowest-priority
    deco that would overflow (rare: only when asleep+sick+poop+effect pile up)."""
    from rich.text import Text
    used = len(status) + 3                      # the status word + 3 spaces
    shown = []
    for d in deco:
        vis = len(Text.from_markup(d).plain)
        add = vis + (2 if shown else 0)         # 2-space separator between glyphs
        if used + add <= width:
            shown.append(d)
            used += add
    return f"[b]{status}[/]   " + "  ".join(shown)


def card(app, title, lines, subtitle=""):
    """The shared card frame: bold title, divider, body."""
    app.stats_w.border_subtitle = subtitle
    body = [f"[b]{title}[/]", DIV] + lines
    app.stats_w.update("\n".join(body))


# ---- the HOME vitals (the Stats widget delegates here) ---------------------

def _zone_display(name, avail):
    """A zone's display name shortened to `avail` visible cols: the full
    name when it fits, else its gate BOSS (zone names are "{Boss}'s
    {biome}", and the boss IS the destination), else a plain clip."""
    if len(name) <= avail:
        return name
    return name.split("'s ", 1)[0][:avail]


def _frontier_name(pet, avail):
    """The frontier zone's display name (the stats column is 26 wide,
    zone names run to 32)."""
    from . import adventure
    return _zone_display(adventure.ZONES[adventure.frontier(pet)]["name"], avail)


def _where(pet):
    """The @ line's place, <=16 cols: the run's zone while the mon is AWAY
    on the road (pet.away_where, set by the landing teleport), the home
    scene otherwise."""
    if getattr(pet, "away", False):
        return _zone_display(getattr(pet, "away_where", "") or "?", 16)
    return backgrounds.name(pet.bg_pick
                            or backgrounds.scene_for_egg(pet.egg_type))[:16]


def adventure_line(pet):
    """The home card's quest readout -- LIVE from pet.adv_progress (zones
    conquered of the 26), plus the FRONTIER zone's name (Joel 2026-07-21:
    "show the frontier zone name on the card") -- the road the pet walks
    next.  8-col label + 18 content cols; '★ all cleared' at the end.
    Single source for the adventure readout (status-box liveness rule)."""
    from . import adventure
    total = len(adventure.ZONES)
    prog = max(0, min(int(getattr(pet, "adv_progress", 0) or 0), total))
    if prog >= total:
        return f"Quest   [{theme.POS}]★ all {total} cleared[/]"
    if prog <= 0:
        return f"Quest   [dim]▸ {_frontier_name(pet, 16)}[/]"
    count = f"{prog}/{total} "
    return f"Quest   {count}[dim]▸ {_frontier_name(pet, 16 - len(count))}[/]"


def home_lines(pet):
    T = theme
    word = pet.status_word()
    deco = care_deco(pet, word)
    age = age_compact(pet.age_seconds)
    xm = f" [b {T.ACCENT}]X[/]" if pet.x_antibody != "None" else ""
    return [
        f"[b]{pet.name[:22]}[/]{xm}",
        f"[dim]{pet.stage}{(' · ' + pet.attribute) if pet.attribute else ''}[/]",
        DIV,
        f"Hunger  {hearts(pet.hunger)}",
        f"Effort  {hearts(pet.strength)}",
        f"Energy  {bar(pet.energy_pct(), 12, T.ENERGY)}",
        DIV,
        # (the Power ledger lives on the DigiCore DATA page, next to the
        # corpus gates that read it; the HP fragment was the retired classic
        # battle's trained-HP -- home-card audit 2026-07-17)
        f"Weight  {pet.weight}g · [{T.COIN}]{pet.bits}b[/]",
        # care mistakes decide the evolution road (every line's CM gates)
        # and 20 is lethal.  Stage-scoped: they reset on evolve.
        (f"Care    [{T.POS}]spotless[/]" if pet.care_mistakes == 0 else
         f"Care    [{T.NEG if pet.care_mistakes >= 10 else T.CARE}]"
         f"✗{pet.care_mistakes} this stage[/]"),
        f"DP      [{T.ACCENT}]{'◆' * getattr(pet, 'dp', 0)}[/][dim]{'◇' * (4 - getattr(pet, 'dp', 0))}[/]",
        f"Battle  {pet.wins}W/{pet.battles}   [{T.COIN}]★{pet.trophies}[/]",
        adventure_line(pet),
        # the @ line is WHERE THE MON STANDS (liveness law, Joel 2026-07-21
        # "shouldnt the @ say what zone the mon is in during adventure?"):
        # the run's zone while it's away on the road, the home scene otherwise
        f"@{_where(pet)} [dim]{age}[/]",
        # (the Life bar left as a DVPet relic -- DSprite mortality, Joel
        # 2026-07-22: death is the hazard roll, there is no meter to show;
        # the elder tell is the aged shuffle sprite)
        status_line(word, deco),
    ]


def egg_lines(pet):
    mins, secs = divmod(int(pet.age_seconds), 60)
    return [
        "[b]Digitama[/] [dim]· egg[/]",
        DIV,
        "[dim]a new life is warming[/]",
        "",
        "Destined to hatch",
        # the destined BABY, not the egg's display title ("Kera Digitama"
        # promised an egg would hatch an egg); a pool keeps its mystery
        f"  [b]{egg_mod.destined_name(pet.egg_type) or '???'}[/]",
        DIV,
        f"Age     {mins}m{secs:02d}s",
        # the wait has a shape now (gameplay polish #21, 2026-07-22): the
        # card said only "hatches on its own" over a rising Age -- with no
        # ETA the first minute read as a mystery stall.  LIVE data: the
        # real incubation clock.
        _hatch_line(pet),
        "",
        "[dim]keep it cosy — it[/]",
        "[dim]hatches on its own[/]",
    ]


def _hatch_line(pet):
    left = max(0, int(pet.EGG_DURATION - pet.stage_seconds))
    if left <= 0:
        return "Hatch   [b]any moment now…[/]"
    return f"Hatch   in ~{left}s"


def grave_lines(pet):
    return [
        f"[b]{pet.name[:16]}[/] [dim]· rest[/]",
        DIV,
        "[dim]a life remembered[/]",
        "",
        f"Lived    {age_compact(pet.age_seconds)}",
        f"Reached  {pet.stage}",
        # pre-fit: a long cause ran the 26-col card (run-off sweep
        # 2026-07-23) -- the label row holds 17 cause chars
        f"Cause    {(getattr(pet, 'death_cause', '') or 'unknown')[:17]}",
        f"Attrib   {pet.attribute}",
        f"Record   {pet.wins}W / {pet.battles}",
        DIV,
        "[dim]gone, but not[/]",
        "[dim]forgotten.[/]",
        "",
        "[dim]press N for a new egg[/]",
    ]


# ---- mode cards ------------------------------------------------------------

def title(app):
    card(app, "TUIPET", ["[dim]a terminal v-pet[/]", "", "",
                         "[dim]a creature awaits[/]", "",
                         "[dim]press ENTER[/]", "[dim]to begin[/]"])


def eggselect(app):
    m = app.mode
    # carousel = hatchable eggs ONLY (Joel 2026-07-12: no silhouettes,
    # no goals); the badge/shown branches below stay defensive in case a
    # locked egg ever leaks onto it.  Carousel polish 2026-07-18: the card
    # names the egg's wired HOME scene, keeps a multi-target digitama's
    # mystery, and badges a never-raised species.
    idx = m.carousel[m.i] if m.carousel else 0
    state = m.states.get(idx, "owned")
    targets = egg_mod.hatch_targets(idx)
    if state == "locked":
        shown, badge = "???", "[dim]sealed[/]"
    elif len(targets) > 1:
        shown, badge = "???", "[dim]two fates stir[/]"
    else:
        shown = egg_mod.destined_name(idx)     # the BABY, not the egg's title
        fresh = bool(targets) and \
            data.canonical_num(targets[0]) not in persistence.get_album()
        badge = ("[b]★ never raised[/]" if fresh
                 else {"temp": "[dim]this gen only[/]"}.get(state, "[dim]ready[/]"))
    # the egg wears its NAME (Joel 2026-07-22: "shouldnt the egg carousel
    # screen show the name of the egg?") -- the browsed digitama had no
    # label anywhere, so matching it to its egg-guide entry meant matching
    # art by eye.  The old title ruling only banned the egg's name on the
    # HATCH line (an egg must not promise to hatch an egg); the egg's own
    # title over the dossier is exactly what that line left room for.
    ename = "???" if state == "locked" else egg_mod.hatch_name(idx)
    scene = backgrounds.name(backgrounds.scene_for_egg(idx))
    card(app, "New Egg", [f"[dim]{m.i + 1} of {m.n} · {m.locked} locked[/]",
                          f"[b]{ename[:22]}[/]", "",
                          "Destined to hatch", f"  [b]{shown}[/]",
                          f"  {badge}", "",
                          f"Home   {scene[:18]}", "",
                          "[dim]←→ browse  ENTER pick[/]"])


def scenes(app):
    """The browsed scene's dossier: the LCD shows the SCENE, this card
    carries the words (picker restore 2026-07-17)."""
    m = app.mode
    row = m.rows[m.cursor]
    name = m._name(row)
    state = "picked" if row == app.pet.bg_pick else \
        ("the default" if not row and not app.pet.bg_pick else "a preview")
    card(app, "Scenes", [f"[dim]{m.cursor + 1} of {len(m.rows)}[/]", "",
                         "On the wall", f"  [b]{name[:24]}[/]",
                         f"  [dim]{state}[/]", "",
                         (m.msg or "")[:26],
                         "[dim]↑↓ browse  ENTER hang[/]"])


def feed(app):
    """FEED: the two rows' true effects beside the live gauges."""
    p, m = app.pet, app.mode
    # both rows disclose in FULL, weight included -- the meat row used to
    # hide its +1 while the pill admitted its +5 (feed audit 2026-07-19)
    # pre-fit to the 26-col card (run-off sweep 2026-07-23: the meat row
    # ran 29 and wrapped the card) -- full disclosure kept, across three
    # short rows instead of two long ones
    sel = min(getattr(m, "cursor", 0), 1)
    row = ("Meat — hunger +1,", "Pill — cures sickness,")[sel]
    tail = ("weight +1 · the staple", "effort +1 · energy +7")[sel]
    tail2 = ("", "weight +5")[sel]
    if sel == 0:
        # meat's refusal gates, visible BEFORE the pick (QOL 2026-07-23):
        # the menu used to close on a refusal you couldn't see coming
        from .petcare import FULL_HUNGER
        T = theme
        if p.sick:
            tail2 = f"[{T.NEG}]refused — sick: the Pill[/]"
        elif p.poop:
            tail2 = f"[{T.NEG}]refused — clean first (C)[/]"
        elif p.hunger >= FULL_HUNGER:
            tail2 = f"[{T.NEG}]refused — belly is full[/]"
    card(app, "Feed", [
        f"Hunger   {hearts(p.hunger)}",
        f"Effort   {hearts(p.strength)}",
        f"Weight   {p.weight}g" + ("   [b]sick[/]" if p.sick else ""),
        "", f"[b]{row}[/]", f"[b]{tail}[/]",
        f"[b]{tail2}[/]" if tail2 else "",
        "", "[dim]↑↓ pick  ENTER feed[/]"],
        subtitle=gen_subtitle(p))


def eat(app):
    """The live feeding readout (plays while the eat fx runs).  What is live:
    the hunger hearts filling, weight, effort, and the premium-meat satiety
    window.  (The Fuel/calorie bar left 2026-07-20: calories is a DVPet-only
    mechanic with no DSprite basis and a drain-only buffer, so the readout
    charted a value feeding never touched.)"""
    p, T = app.pet, theme
    full = getattr(p, "full_until", 0.0)
    sated = full and p.world_seconds < full
    lines = [
        f"[b]{p.name[:14]}[/] [dim]· feeding[/]", DIV,
        f"Hunger   {hearts(p.hunger)}",
        DIV,
        f"Weight   {p.weight}g",
        f"Effort   {hearts(p.strength)}",
        (f"[{T.POS}]sated · {age_compact(full - p.world_seconds)} left[/]"
         if sated else ""),
    ]
    app.stats_w.border_subtitle = gen_subtitle(p)
    app.stats_w.update("\n".join(lines))


def shop(app):
    """SHOP/BAG: the selected entry's dossier."""
    from . import shop as shop_mod
    T = theme
    p, m = app.pet, app.mode
    rows = m._rows()
    if not rows:
        card(app, "Shop" if m.mode == "shop" else "Bag",
             ["", "[dim]nothing here[/]", "",
              f"Bits   [b]{p.bits}b[/]"])
        return
    e = rows[min(m.cursor, len(rows) - 1)]
    ttl = "Shop" if m.mode == "shop" else "Bag"
    if e.get("title_id") is not None:
        state = ("worn" if e.get("worn")
                 else "owned" if e.get("owned") else f"{e['price']}b")
        lines = [f"[b]{e['name'][:24]}[/]", "[dim]a tamer honor[/]",
                 f"Status  {state}", "",
                 f"Bits    [b]{p.bits}b[/]", "",
                 "[dim]ENTER buys, then wears[/]"]
    else:
        have = p.inventory.get(e["key"], 0)
        if str(e["key"]).startswith("egg_of_"):
            # the crest egg's LIVE answer (the same evolution.check the
            # item runs; shop polish 2026-07-17)
            names = shop_mod.crest_answer(p, e["key"])
            eff = (f"[{T.POS}]answers: {' / '.join(names)[:18]}[/]" if names
                   else "[dim]nothing answers it yet[/]")
        else:
            eff = f"[dim]{shop_mod.effect_line(e)[:26]}[/]"
        if m.mode == "shop":
            short = e["price"] - p.bits
            price = (f"Price   [{T.NEG}]{e['price']}b · short {short}[/]"
                     if short > 0 else f"Price   {e['price']}b")
        else:
            price = f"Sells   {shop_mod.resell_price(e)}b"
        lines = [f"[b]{e['name'][:24]}[/]", eff, "",
                 price,
                 f"Owned   x{have}",
                 f"Bits    [b]{p.bits}b[/]", "",
                 ("[dim]ENTER buy[/]" if m.mode == "shop"
                  else "[dim]ENTER use  R sell[/]")]
    card(app, ttl, lines, subtitle=gen_subtitle(p))


def eggguide(app):
    """DIGITAMA GUIDE: the browsed egg's dossier."""
    m = app.mode
    state = m.states.get(m.i, "locked")
    # the name shows for EVERY egg -- the guide's own list and detail
    # header always revealed it; the card's "???" mask was the one
    # surface disagreeing (round 34: the book's purpose is showing
    # what's out there)
    name = egg_mod.hatch_name(m.i)
    live = egg_mod.unlock_progress(m.i, m.prog)
    rule = m.rules.get(m.i)
    keeps = ("this gen only" if rule is not None and not rule["can_perm"]
             else "forever")
    hints = ("←→ next egg  ESC back" if m.detail
             else "ENTER story  ↑↓ browse")     # phase-true (round 34)
    card(app, "Digitama", [
        f"[dim]{m.i + 1} of {m.n}[/]", "",
        f"Hatches  [b]{name[:16]}[/]",
        f"State    {state}",
        f"Keeps    {keeps}", "",
        (f"[b]{live[:26]}[/]" if live and state == "locked" else ""),
        f"[dim]{hints}[/]"])


def digicore(app):
    """DIGICORE: which data page is up, and whose core it is."""
    p, m = app.pet, app.mode
    page = m.pages[min(m.i, len(m.pages) - 1)][0]
    card(app, "DigiCore", [
        f"[b]{p.name[:16]}[/]",
        f"[dim]{p.stage} · {p.attribute}[/]", "",
        f"Page   [b]{page[:18]}[/]",
        f"[dim]{m.i + 1} of {len(m.pages)}[/]", "",
        (m.note or "")[:26],
        "[dim]←→ pages  SPACE core[/]"],
        subtitle=gen_subtitle(p))


def raid(app):
    """RAID: the boss, the shared pool, your standing — ALL the numbers
    live HERE (scene-screen law, raid uncramp 2026-07-23: the LCD page
    duplicated every one of these lines and crushed the boss for it)."""
    from .raidscreen import _fmt as _fmt_dmg
    m = app.mode
    v = m.view or {}
    b = m._boss()
    if not b:
        card(app, "Raid", ["", "[dim]calling the gate…[/]"])
        return
    pool, mx = int(b.get("hp", 0)), max(1, int(b.get("max_hp", 1)))
    pct = max(0, min(100, pool * 100 // mx))
    rank, mine = (list(v.get("you") or (0, 0)) + [0, 0])[:2]
    standing = m._standing()
    left = max(0, int((b.get("end" if standing else "start", 0)
                       - v.get("now", 0))))
    when = "%dd %dh" % (left // 86400, left % 86400 // 3600)
    top = v.get("top") or []
    lead = (f"{str(top[0][0])[:10]} · {_fmt_dmg(top[0][1])}" if top else "—")
    card(app, "Raid", [
        f"[b]{b.get('name', '?')[:18]}[/]",
        (f"Pool   {bar(pct, 11, theme.NEG)} {pct}%" if standing
         else "[dim]incoming boss[/]"),
        (f"[dim]{when} left[/]" if standing else f"[dim]in {when}[/]"),
        "",
        (f"You    #{rank} · {_fmt_dmg(mine)}" if rank
         else "You    [dim]— not on the board[/]"),
        f"Top    {lead}",
        f"Tries  {v.get('attempts', 0)} today",
        ("[b]purse waiting — C[/]" if v.get("award") else ""),
        "[dim]SPACE raid  C claim[/]"],
        subtitle=gen_subtitle(app.pet))


def lobby(app):
    """LOBBY: your card and the room."""
    m = app.mode
    st = m.state
    if st is None or getattr(st, "me_id", None) is None:
        card(app, "Lobby", ["", "[dim]connecting…[/]"])
        return
    roster = list(getattr(st, "roster", []) or [])
    links = persistence.get_progress().get("connections", 0)
    card(app, "Lobby", [
        f"[b]{(m._last_name or '?')[:18]}[/]",
        f"[dim]{app.pet.name[:14]} rides along[/]", "",
        f"Here   {len(roster)} tamer" + ("s" if len(roster) != 1 else ""),
        f"Links  {links} lifetime", "",
        "[dim]type to chat · ENTER[/]",
        "[dim]↑↓ pick a tamer[/]"])


def help_(app):
    from . import update
    try:
        ver = update.current_version()
    except Exception:
        ver = "?"
    snd = "on" if app.sound else "off"
    card(app, "Help", [
        f"tuipet [b]v{ver}[/]", "",
        f"Sound  {snd}",
        f"Gen    {app.pet.generation}", "",
        "[dim]the guide scrolls[/]",
        "[dim]on the display[/]", "",
        "[dim]↑↓ scroll  ESC out[/]"])


def options(app):
    from . import optionsscreen as _opts
    m = app.mode
    row = _opts._ROWS[min(m.cursor, len(_opts._ROWS) - 1)]
    desc = _opts._DESC.get(row, "")
    card(app, "Options", [
        f"[b]{_opts._LABEL.get(row, row.title())}[/]", "",
        f"[dim]{desc[:26]}[/]",
        f"[dim]{desc[26:52]}[/]", "",
        (m.msg or "")[:26], "",
        "[dim]ENTER toggles[/]"])


def bug(app):
    m = app.mode
    n = len(getattr(m, "buf", ""))
    card(app, "Bug Report", [
        "[dim]straight to the dev[/]", "",
        f"Typed  {n} chars", "",
        "[dim]say what you did and[/]",
        "[dim]what went wrong[/]", "",
        "[dim]ENTER send  ESC out[/]"])


def death(app):
    p = app.pet
    days = int(getattr(p, "age_seconds", 0) // 86400)
    cause = getattr(p, "death_cause", "") or "old age"
    card(app, "In Memory", [
        f"[b]{p.name[:18]}[/]",
        f"[dim]{p.stage} · gen {p.generation}[/]", "",
        f"Lived  {days} day" + ("s" if days != 1 else ""),
        f"Of     {cause[:20]}", "",
        "[dim]its data can live on[/]",
        "[dim]in the next egg[/]"])


def assist(app):
    from .pet import AUTO_CARE_VISIT_PRICE
    p = app.pet
    on = getattr(p, "auto_care", False)
    fee = AUTO_CARE_VISIT_PRICE.get(p.stage, 200)
    card(app, "Assistant", [
        f"Helper  [b]{'hired' if on else 'off'}[/]", "",
        f"Visit   ~{fee}b",
        f"Bits    [b]{p.bits}b[/]", "",
        "[dim]cleans and feeds while[/]",
        "[dim]you are away[/]", "",
        "[dim]ENTER hire/dismiss[/]"])


class _SubView:
    """Painters read app.mode; this lends `app` out with the EMBEDDED panel
    as the mode, so a host screen can hand its card to the sub's painter
    (the cup's bouts ran with no visible HP: painter_for dispatches on the
    top-level mode only, and BattlePanel is never top-level)."""
    __slots__ = ("_app", "mode")

    def __init__(self, app, mode):
        self._app, self.mode = app, mode

    def __getattr__(self, k):
        return getattr(self._app, k)


def tournament(app):
    # (the cup's own sub->battle hand-off moved into painter_for -- the
    # dispatcher lends every host's card to its embedded fight now)
    p, t, T = app.pet, app.mode.tourney, theme
    app.stats_w.border_subtitle = gen_subtitle(p)
    if t is None:                      # cup-select phase (no bout yet)
        card(app, "Cup", ["", "Pick a cup", "to enter."],
             subtitle=gen_subtitle(p))
        return
    if t.over and t.champion:
        lines = [f"[b]{p.name[:14]}[/] [dim]· cup[/]", DIV,
                 f"[b]{t.name[:24]}[/]", "",
                 f"[{T.POS}]★ CHAMPION ★[/]", "",
                 f"Trophy   [{T.COIN}]★{p.trophies}[/]",
                 f"Reward   [{T.COIN}]+{t.reward_bits}b[/]", DIV,
                 "[dim]you took the cup![/]"]
    elif t.over:
        lines = [f"[b]{p.name[:14]}[/] [dim]· cup[/]", DIV,
                 f"[b]{t.name[:24]}[/]", "",
                 f"[{T.NEG}]eliminated[/]",
                 f"[dim]in the {t.round_name}[/]", "",
                 f"Trophy   [{T.COIN}]★{p.trophies}[/]", DIV,
                 "[dim]train up, try again[/]"]
    else:
        lines = [
            f"[b]{p.name[:14]}[/] [dim]· cup[/]", DIV,
            f"[b]{t.name[:24]}[/]",
            f"Match    {t.round + 1} / 3",
            f"Trophy   [{T.COIN}]★{p.trophies}[/]",
            DIV,
            f"Effort   {hearts(p.strength)}",
            f"Energy   {bar(p.energy_pct(), 11, T.ENERGY)}",
            f"Form     {getattr(p, 'saved_hit_type', 'normal')}",
            DIV,
            "[dim]fight for the cup[/]",
        ]
    app.stats_w.update("\n".join(lines))


def discipline(app):
    """The praise/scold picker's card (canon restoration B): the gauge,
    the open moment, and what each verb would land."""
    p, T = app.pet, theme
    app.stats_w.border_subtitle = gen_subtitle(p)
    if p.discipline_call:
        moment = f"[{T.NEG}]acting up![/]"
    elif p.world_seconds <= getattr(p, "praise_window", 0.0):
        moment = f"[{T.POS}]a proud moment[/]"
    else:
        moment = "[dim]calm[/]"
    lines = [f"[b]{p.name[:14]}[/] [dim]· lessons[/]", DIV,
             f"Manners  {bar(p.obedience, 11, T.POS)} {p.obedience}",
             f"Moment   {moment}", DIV,
             "[dim]scold a tantrum: +25[/]",
             "[dim]praise a proud win: +10[/]",
             "[dim]ignored tantrums cost ✗[/]"]
    app.stats_w.update("\n".join(lines))


def training(app):
    """The 0.5 drill's card (2026-07-17): one timing bar, so one card --
    the four-drill readouts left with the classic training system."""
    p, tp, T = app.pet, app.mode, theme
    app.stats_w.border_subtitle = gen_subtitle(p)
    eff = hearts(p.strength)
    energy = bar(p.energy_pct(), 11, T.ENERGY)
    window = tp.mega_hi - tp.mega_lo + 1
    form = getattr(p, "saved_hit_type", "normal")
    if tp.phase == "bar":
        lines = [f"[b]{p.name[:14]}[/] [dim]· train[/]", DIV,
                 "[b]time the strike[/]", "",
                 f"Window   {window}px",
                 f"Form     {form}",
                 f"Effort   {eff}", f"Energy   {energy}",
                 DIV, "[dim]SPACE locks the bar[/]"]
    else:
        lines = [f"[b]{p.name[:14]}[/] [dim]· train[/]", DIV,
                 "[b]the strike[/]", "",
                 f"Grade    {tp.grade or ''}",
                 f"Energy   {energy}", DIV, ""]
    app.stats_w.update("\n".join(lines))


def battle(app):
    p, m, T = app.pet, app.mode, theme
    b = m.battle                    # None until the timing bar locks (0.5)
    app.stats_w.border_subtitle = gen_subtitle(p)
    enemy = m.enemy or {}
    raid = bool(getattr(m, "raid", False))
    tag = f" [{T.NEG}]BOSS[/]" if enemy.get("boss") else ""
    from .battle import RAID_PLAYER_HP
    dflt = RAID_PLAYER_HP if raid else 5   # pre-lock: the raid fights from 10
    pet_max = b.pet_max if b else dflt
    foe_max = b.enemy_max if b else 5
    php = getattr(m, "hud_php", b.pet_hp if b else dflt)
    fhp = getattr(m, "hud_fhp", b.enemy_hp if b else 5)
    pp = int(100 * php / pet_max) if pet_max else 0
    fp = int(100 * fhp / foe_max) if foe_max else 0
    if raid:
        # the boss's real health is the COMMUNITY POOL (raid audit
        # 2026-07-23: the card leaked RaidBout's 5/5 display stub -- a
        # 5.5M shared boss shown as a five-heart foe)
        pool = enemy.get("pool")
        if pool:
            phv, pmx = int(pool[0]), max(1, int(pool[1]))
            pct = max(0, min(100, phv * 100 // pmx))
            foe_line = f"Pool {bar(pct, 11, T.NEG)} {pct}%"
        else:
            foe_line = "Pool [dim]shared — held by the gate[/]"
    else:
        foe_line = f"Foe  {bar(fp, 11, T.NEG)} {fhp}/{foe_max}"
    lines = [
        f"[b]{p.name[:14]}[/] [dim]· {'raid' if raid else 'battle'}[/]", DIV,
        f"vs [b]{enemy.get('name', '?')[:14]}[/]{tag}", "",
        f"You  {bar(pp, 11, T.POS)} {php}/{pet_max}",
        foe_line,
        DIV,
    ]
    # the locked grade, VISIBLE (transparency 2026-07-23: training showed
    # its Grade, battle showed NOTHING -- the intro-mash bug locked a miss
    # and the player had no way to see it happen.  Never again: every
    # fight wears its lock.)
    if getattr(m, "locked", None):
        g = m.locked
        gsty = T.POS if g == "mega" else (T.NEG if g == "miss" else "")
        lines.append(f"Lock [{gsty}]{g}[/]" if gsty else f"Lock {g}")
    if m.done_anim and raid:
        res = (f"[{T.POS}]STOOD YOUR GROUND[/]" if m.won
               else f"[{T.NEG}]KNOCKED OUT[/]")
        lines += [res, f"[b]dealt {getattr(b, 'dealt', 0)}[/] [dim]→ the gate[/]",
                  "", "[dim]SPACE  continue[/]"]
    elif m.done_anim:
        res = f"[{T.POS}]VICTORY![/]" if m.won else f"[{T.NEG}]DEFEAT[/]"
        lines += [res, f"[dim]{(b.reward if b else '') or ''}"[:30] + "[/]",
                  "", "[dim]SPACE  continue[/]"]
    elif getattr(m, "phase", "") == "ready":
        lines += [f"[dim]{(m.hud_note or '')[:26]}[/]", "",
                  "[dim]SPACE  lock the bar[/]"]
    else:
        lines += [f"[dim]{(m.hud_note or '')[:24]}[/]", "",
                  "[dim]SPACE skip · ESC end it[/]"]
    app.stats_w.update("\n".join(lines))


def dna(app):
    p, m, T = app.pet, app.mode, theme
    app.stats_w.border_subtitle = gen_subtitle(p)
    f = m.field
    same = f == p.field
    own, chg = p.dna_owned.get(f, 0), p.dna_applied.get(f, 0)
    # the charge bill, TRUTHFULLY (modularize audit 2026-07-17): the old
    # line billed "spirit/mood" -- both systems are gone.  applyDNA's real
    # cost is ENERGY: 1/unit on your own Field, doubled off-Field (and the
    # off-field sickness risk left with the sickness rebuild).
    cost = "energy -1/ea (own Field)" if same else "energy -2/ea (off Field)"
    from . import evolution
    reqs = data.load_requirements()
    dna_t = [t for t in data.load_evolutions().get(p.num, [])
             if reqs.get(t) and any(g[0] != "None" for g in reqs[t]["dna"].values())]
    unlocked = sum(1 for t in dna_t if evolution._dna_ok(p, reqs[t]))
    screen = {"home": "menu", "charge": "charge", "stats": "stats",
              "reqs": "requirements", "bet": "generate", "mash": "generate",
              "result": "generate"}.get(m.phase, "menu")
    import textwrap
    last_rows = [f"[dim]{s}[/]" for s in textwrap.wrap(m.last or "", 24)[:2]]
    last_rows += [""] * (2 - len(last_rows))
    lines = [
        # dynamic fit (run-off sweep 2026-07-23: a 14-char name + 'DNA ·
        # generate' ran 30 cols): the NAME gives way, the tail stays whole
        f"[b]{p.name[:max(4, CARD_W - 9 - len(screen))]}[/]"
        f" [dim]· DNA · {screen}[/]", DIV,
        f"Bits     [{T.COIN}]{p.bits}[/]",
        f"Field    {data.pretty_field(f)}" + ("  [dim](own)[/]" if same else ""),
        f"Banked   {own}     Charged {chg}",
        f"Share    {p.dna_percent(f)}%    [dim]x{m.amount}[/]",
        f"Unlocks  [b]{unlocked}[/]/{len(dna_t)} form(s)",
        DIV,
        f"[dim]{cost}[/]",
        *last_rows,
        "[dim]own Field charges cheap[/]",
        "[dim]ESC steps back out[/]",
    ]
    app.stats_w.update("\n".join(lines))


# ---- dispatch ---------------------------------------------------------------

def _registry():
    """Panel class -> painter.  Built lazily: importing every screen at
    module import would be a cycle magnet."""
    from . import (assistscreen, backgroundscreen, battlescreen, bugscreen,
                   deathscreen, digicorescreen, disciplinescreen, dnascreen,
                   eggguidescreen, eggselectscreen, feedscreen, helpscreen,
                   lobbyscreen, optionsscreen, raidscreen, shopscreen,
                   titlescreen, tournamentscreen, training as training_mod)
    return (
        (titlescreen.TitlePanel, title),
        (disciplinescreen.DisciplinePanel, discipline),
        (eggselectscreen.EggSelectPanel, eggselect),
        (tournamentscreen.TournamentPanel, tournament),
        (training_mod.TrainingPanel, training),
        (battlescreen.BattlePanel, battle),
        (dnascreen.DNAPanel, dna),
        (backgroundscreen.BackgroundPanel, scenes),
        (feedscreen.FeedPanel, feed),
        (shopscreen.ShopPanel, shop),
        (eggguidescreen.EggGuidePanel, eggguide),
        (digicorescreen.DigiCorePanel, digicore),
        (raidscreen.RaidPanel, raid),
        (lobbyscreen.LobbyPanel, lobby),
        (helpscreen.HelpPanel, help_),
        (optionsscreen.OptionsPanel, options),
        (bugscreen.BugReportPanel, bug),
        (deathscreen.DeathPanel, death),
        (assistscreen.AssistPanel, assist),
    )


def painter_for(mode):
    """The painter for a mode instance, or None (home screen -> vitals).

    SUB CHAINS RESOLVE FIRST (modularize 2026-07-22, Joel: "why are
    adventure battles and cup battles different?? the status box in cup
    shows so much more"): the cup used to hand its card to its embedded
    BattlePanel by itself while every OTHER host (the road's wilds, the
    town cup two layers deep, the raid volley) fell through to generic
    vitals -- same fight, different card.  The dispatcher now walks
    mode.sub recursively and lends the card to the DEEPEST registered
    panel, so one battle painter serves every fight wherever it runs.
    Resolution happens per paint, so a sub opening/closing re-routes on
    the next frame."""
    if mode is None:
        return None
    sub = getattr(mode, "sub", None)
    if sub is not None:
        subfn = painter_for(sub)
        if subfn is not None:
            return lambda app: subfn(_SubView(app, sub))
    for cls, fn in _registry():
        if isinstance(mode, cls):
            return fn
    return None
