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

import textwrap

from . import backgrounds
from . import data
from . import egg as egg_mod
from . import persistence
from . import theme
from .arena import bar, hearts
from .petbase import DISOBEY_BELOW

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
    # ENERGY, not raw terminal blue (theme audit 2026-07-28): the Zzz was
    # the last hard-coded colour tag in the app, one shade on EVERY theme
    # beside siblings that all ride the palette.  Sleep restores energy;
    # the badge wears the energy readout's tint.
    if pet.asleep and word != "asleep": deco.append(f"[{T.ENERGY}]Zzz[/]")
    if pet.sick and word != "sick": deco.append(f"[{T.NEG}]+sick[/]")
    # +hurt RESTORED (badge audit 2026-07-24, Joel "see if we are missing any
    # other badges"): injury came back with canon restoration but its badge
    # did not.  status_word ranks sick/asleep/elderly ABOVE injured, so a
    # sick+injured pet showed only "sick" -- the player pilled it and never
    # learned it also needed a BANDAGE (a different cure that coexists with
    # sickness by design).  Mirrors +sick: shown unless injured IS the word.
    # (the +tired badge stays gone -- is_fatigued() is hardwired False; the
    # +med/+bnd/+vit item badges stay gone with the medicine-ITEM system.)
    if pet.is_injured() and word != "injured": deco.append(f"[{T.NEG}]+hurt[/]")
    if pet.is_frail(): deco.append(f"[{T.NEG}]+frail![/]")
    if pet.poop: deco.append(f"[{T.COIN}]~poop x{pet.poop}[/]")
    # +rude (badge audit 2026-07-24): manners drives feed/train/battle
    # refusals below DISOBEY_BELOW, but the gauge lives only on DigiCore --
    # a pet "turns its nose up!" with no on-card reason.  This is the ONLY
    # signal that a refusal is EARNED disobedience, not a bug.  Below the
    # ailments/needs in priority: a hungry, defiant pet shows the hunger
    # first.  Discipline (praise/scold/p) or a Textbook lifts it back.
    if getattr(pet, "obedience", DISOBEY_BELOW) < DISOBEY_BELOW:
        deco.append(f"[{T.CARE}]+rude[/]")
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


def cell_len_(text):
    """Terminal CELLS of `text` -- the card budget's only honest ruler."""
    from rich.cells import cell_len
    return cell_len(text)


def _fit_cells(text, budget):
    """`text` clipped to `budget` TERMINAL CELLS, ellipsised when it does not
    fit.  Cells, never len(): a 2-cell glyph passes a char budget and blows
    the render (THE CELL LAW, bug report #32)."""
    from rich.cells import cell_len
    if cell_len(text) <= budget:
        return text
    out = ""
    for ch in text:
        if cell_len(out + ch) > budget - 1:
            break
        out += ch
    return out.rstrip() + "…"


def wrap(text, max_lines, width=CARD_W):
    """Word-wrap PLAIN text into card rows on WORD boundaries (card audit
    2026-07-24, Joel "words are getting cut off").  The Options card used a
    raw text[:26] / [26:52] slice, which split "auto-install" mid-glyph and
    dropped a message's tail past 26 chars.  Caps at max_lines; an over-long
    tail ends the last kept line with an ellipsis instead of a silent
    amputation.  Callers wrap the result in their own markup."""
    # break_on_hyphens=False keeps "auto-install" whole rather than snapping
    # it at the hyphen; break_long_words still splits a lone word wider than
    # the card so nothing can silently overrun.
    lines = textwrap.wrap(text, width, break_on_hyphens=False) if text else []
    if len(lines) > max_lines:
        lines = lines[:max_lines]
        lines[-1] = lines[-1][:width - 1].rstrip() + "…"
    return lines


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
    """The @ line's PLACE, <=16 cols: on the road it's the current zone's
    BIOME, the home scene otherwise -- both read as a place the pet stands.

    Zone names are "{Boss}'s {biome}"; the @ line shows the biome half, NOT
    the boss (@-habitat fix 2026-07-24, Joel "does it display the correct
    habitat name while in adventure?").  The boss is the Quest line's
    OBJECTIVE -- clipping the @ to it made the road read "@WarGreymon", a
    monster's name where a place belongs, and stacked two bosses on adjacent
    rows.  The biome (<=13 cols) is the habitat, and matches the home scene
    the @ shows off the road."""
    if getattr(pet, "away", False):
        zone = getattr(pet, "away_where", "") or "?"
        return zone.split("'s ", 1)[-1][:16]        # the biome half, not the boss
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


def festival_line():
    """TODAY's festival, named -- or None on an ordinary day.

    ⭐Bug report 2026-08-01 (Joel): "whyyyy is there a sun pixel sprite stuck
    on the lcd screen?"  It was the Crest of Courage, the Odaiba Memorial Day
    decoration -- a prop that quietly appeared in the arena's corner on four
    dates a year, named NOWHERE on the home screen, so the only thing a player
    could conclude was that a pixel had got stuck.  ⛔THE PROP WAS THEN CUT
    (2026-08-01, "cut it"): it cost the mon half its roam and bred collision
    bugs.  THIS BANNER IS NOW THE ONLY ON-SCREEN SIGN A FESTIVAL IS RUNNING --
    do not let it rot.  (The road card names it too, in statusbox.road.)"""
    from . import tournament
    return tournament.holiday()


def home_lines(pet):
    from . import lines as _lines           # DMX level: exp vs canon thresholds
    T = theme
    word = pet.status_word()
    deco = care_deco(pet, word)
    age = age_compact(pet.age_seconds)
    xm = f" [b {T.ACCENT}]X[/]" if pet.x_antibody != "None" else ""
    lvl = _lines._pet_level(pet)
    fest = festival_line()
    return [
        f"[b]{pet.name[:22]}[/]{xm}",
        f"[dim]{pet.stage}{(' · ' + pet.attribute) if pet.attribute else ''}[/]",
    ] + ([f"[{T.COIN}]★ {fest[:24]}[/]"] if fest else []) + [
        DIV,
        f"Hunger  {hearts(pet.hunger)}",
        f"Effort  {hearts(pet.strength)}",
        f"Energy  {bar(pet.energy_pct(), 12, T.ENERGY)}",
        DIV,
        # (the HP fragment was the retired classic battle's trained-HP --
        # home-card audit 2026-07-17.  The Va/Da/Vi Power ledger and the DMX
        # Level, once DigiCore-only, now ride the two battle rows below --
        # both were live progression the main card never showed, home-card
        # surfacing 2026-07-24 "evaluate what we can fit".)
        f"Weight  {pet.weight}g · [{T.COIN}]{pet.bits}b[/]",
        # care mistakes decide the evolution road (every line's CM gates)
        # and 20 is lethal.  Stage-scoped: they reset on evolve.
        (f"Care    [{T.POS}]spotless[/]" if pet.care_mistakes == 0 else
         f"Care    [{T.NEG if pet.care_mistakes >= 10 else T.CARE}]"
         f"✗{pet.care_mistakes} this stage[/]"),
        f"DP      [{T.ACCENT}]{'◆' * getattr(pet, 'dp', 0)}[/][dim]{'◇' * (4 - getattr(pet, 'dp', 0))}[/]",
        # battle progression, once DigiCore-only: wins/level/trophies on one
        # row, the Va/Da/Vi attribute powers on the next.  Level folds in free
        # (DMX 1-10, capped by stage); the powers colour by attribute --
        # Vaccine green, Data blue, Virus red -- and are uncapped, so a big
        # number is real, not a glitch (chips + wins both feed them).
        # LIFE/POS/NEG are the theme roles that deliver that trio (theme
        # audit 2026-07-28): the row shipped with D on ACCENT, and accent
        # IS the neg hex on mono and amber -- Data and Virus rendered as
        # literal twins there, near-twins on grey (both red-family).
        f"Battle  {pet.wins}W/{pet.battles} [dim]Lv[/]{lvl} [{T.COIN}]★{pet.trophies}[/]",
        f"Power   [{T.LIFE}]V{pet.vaccine}[/] [{T.POS}]D{pet.data_power}[/] "
        f"[{T.NEG}]Vi{pet.virus}[/]",
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
    # the festival prop draws over an EGG's arena too (arenafx._effect_overlay
    # blits it before the `pet.num == -1` return), so the egg card names the
    # day for the same reason the home card does -- 12 rows, room to spare
    fest = festival_line()
    return [
        "[b]Digitama[/] [dim]· egg[/]",
        DIV,
    ] + ([f"[{theme.COIN}]★ {fest[:24]}[/]", ""] if fest else []) + [
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
    # word-wrap the picker message (card audit 2026-07-24): "pick a scene —
    # it hangs behind the mon" (38) and "Back to the egg's own scene." (28)
    # were sliced at [:26], losing the tail.
    sc_lines = [f"[dim]{m.cursor + 1} of {len(m.rows)}[/]", "",
                "On the wall", f"  [b]{name[:24]}[/]",
                f"  [dim]{state}[/]", ""]
    sc_lines += wrap(m.msg or "", 2)
    sc_lines.append("[dim]↑↓ browse  ENTER hang[/]")
    card(app, "Scenes", sc_lines)


def feed(app):
    """FEED: the selected row's true effects beside the live gauges."""
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
        # word-wrap the effect blurb (card audit 2026-07-24): an effect_line
        # runs to 51 chars ("ride! weight -2 · energy -1 — shred the living
        # room") and a crest's answer list past 18 -- both were sliced flat.
        if str(e["key"]).startswith("egg_of_"):
            # the crest egg's LIVE answer (the same evolution.check the
            # item runs; shop polish 2026-07-17)
            names = shop_mod.crest_answer(p, e["key"])
            eff = ([f"[{T.POS}]{ln}[/]" for ln in wrap("answers: " + " / ".join(names), 2)]
                   if names else ["[dim]nothing answers it yet[/]"])
        else:
            eff = [f"[dim]{ln}[/]" for ln in wrap(shop_mod.effect_line(e), 3)]
        if m.mode == "shop":
            short = e["price"] - p.bits
            price = (f"Price   [{T.NEG}]{e['price']}b · short {short}[/]"
                     if short > 0 else f"Price   {e['price']}b")
        else:
            price = f"Sells   {shop_mod.resell_price(e)}b"
        lines = [f"[b]{e['name'][:24]}[/]", *eff, "",
                 price,
                 f"Owned   x{have}",
                 f"Bits    [b]{p.bits}b[/]", "",
                 ("[dim]ENTER buy[/]" if m.mode == "shop"
                  else "[dim]ENTER use  R sell[/]")]
    card(app, ttl, lines, subtitle=gen_subtitle(p))


def album(app):
    """THE ALBUM: the collection at a glance, and the browsed form's dossier.

    ⭐Joel's named order 2026-08-04 ("build the album and hall cards"), off the
    all-cards audit that found this screen falling through to bare vitals --
    you opened the bestiary and the box on the right still read out your pet's
    hunger.  The panel's own LCD is the book (list, then the 16x16 rip); the
    card is what a book has and a scoreboard doesn't: WHERE YOU ARE in it, and
    the route to the entry under the cursor.

    Everything here is LIVE off the panel's own data -- `roster`/`seen` are
    `data.album_roster()` and `persistence.get_album()` -- so the card cannot
    disagree with the page it sits beside (status-box liveness law)."""
    m, T = app.mode, theme
    total = max(1, m.n)
    seen = len(m.seen)
    pct = seen * 100 // total
    num = m.roster[m.i] if m.n else None
    found = num in m.seen if num is not None else False
    rec = data.record_for(num) if num is not None else {}
    # the MASK is the panel's own language: a discovered form wears its name,
    # one still out there stays "???" (the digicore hidden-evo reveal rule)
    name = _fit_cells(rec.get("name", "?"), CARD_W - 9) if found else "???"
    stage = rec.get("stage", "") if found else "—"
    # and for an undiscovered one, the card carries the ROUTE -- the panel
    # computes it already (albumscreen.route_hint), it just had nowhere on
    # the right to live
    tail = []
    if not found and num is not None:
        from .albumscreen import route_hint
        try:
            hint = route_hint(num)
        except Exception:
            hint = ""
        tail = [f"[dim]{ln}[/]" for ln in wrap(hint, 3)] if hint else []
    # the gauge wears the raid/road card's grammar -- label, bar, percent on
    # ONE row -- rather than floating an unlabelled bar of its own
    card(app, "Album", [
        f"[dim]{m.i + 1} of {m.n}[/]", "",
        f"Found  {bar(pct, 11, T.POS)} {pct}%",
        f"[dim]{seen} of {total} forms[/]", "",
        f"Name    [b]{name}[/]",
        f"Stage   {stage}"]
        # the route only earns its separator when there IS a route (a found
        # form has none, and two blank rows in a row is wasted budget --
        # the all-cards audit's own trailing-blank finding)
        + ([""] + tail if tail else [])
        + ["", "[dim]ENTER view  ↑↓ browse[/]"],
        subtitle=gen_subtitle(app.pet) if app.pet else "")


def hall(app):
    """THE HALL OF MEMORY: the lineage's ledger, and the elder under the
    cursor.

    ⭐Joel's named order 2026-08-04 ("build the album and hall cards").  The
    album remembers SPECIES, the hall remembers INDIVIDUALS -- so this card
    reads the LINE (how many have come before, how deep the generations run)
    beside the one life the page is showing.  Rows are
    `progress.legacy`, newest first, exactly as the panel reads them."""
    m, T = app.mode, theme
    if not m.n:
        card(app, "Hall", ["", "[dim]no elders yet[/]", "",
                           "[dim]a generation is written[/]",
                           "[dim]here when it ends[/]"])
        return
    r = m.elders[min(m.i, m.n - 1)] if m.n else {}
    gens = max((int(x.get("gen", 1)) for x in m.elders), default=0)
    fell = sum(1 for x in m.elders if x.get("dead"))
    age = age_compact(float(r.get("age", 0.0)))
    wins = int(r.get("wins", 0))
    lines = [
        f"[dim]{m.i + 1} of {m.n}[/]", "",
        f"Line    [b]{m.n}[/] elder" + ("s" if m.n != 1 else ""),
        f"Deepest [b]gen {gens}[/]",
        f"Fell    {fell}", "",
        f"[b]{_fit_cells(str(r.get('name', '?')), CARD_W - 1)}[/]",
        f"[dim]gen {int(r.get('gen', 1))} · {str(r.get('stage', '?'))[:12]}[/]",
        f"Lived   {age}",
        f"Won     {wins}W · [{T.COIN}]★{int(r.get('cups', 0))}[/]",
    ]
    if r.get("dead"):
        cause = str(r.get("cause", "") or "old age")
        lines.append(f"[{T.NEG}]† {_fit_cells(cause, CARD_W - 2)}[/]")
    lines += ["", "[dim]ENTER page  ↑↓ browse[/]"]
    card(app, "Hall", lines,
         subtitle=gen_subtitle(app.pet) if app.pet else "")


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
    # the goal WRAPS to two card lines -- the one-slice clip froze the dual
    # map gate mid-word ("clear adventure map 1 (or", Joel 2026-07-28)
    goal = wrap(live, 2) if live and state == "locked" else [""]
    card(app, "Digitama", [
        f"[dim]{m.i + 1} of {m.n}[/]", "",
        f"Hatches  [b]{name[:16]}[/]",
        f"State    {state}",
        f"Keeps    {keeps}", ""]
        + [f"[b]{g}[/]" if g else "" for g in goal]
        + [f"[dim]{hints}[/]"])


def digicore(app):
    """DIGICORE: which data page is up, and whose core it is."""
    p, m = app.pet, app.mode
    page = m.pages[min(m.i, len(m.pages) - 1)][0]
    dc_lines = [
        f"[b]{p.name[:16]}[/]",
        f"[dim]{p.stage} · {p.attribute}[/]", "",
        f"Page   [b]{page[:18]}[/]",
        f"[dim]{m.i + 1} of {len(m.pages)}[/]", ""]
    dc_lines += wrap(m.note or "", 2)          # note carries mode-change lines
    dc_lines.append("[dim]←→ pages  SPACE core[/]")
    card(app, "DigiCore", dc_lines, subtitle=gen_subtitle(p))


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


def _esc(text):
    """Player-typed text on a MARKUP surface.  Card lines are rich markup
    STRINGS, so a tamer named "[b" would swallow the rest of the card (or
    raise) the moment it was painted.  The LCD is a rich Text object and
    parses no markup, which is why this guard lives only here."""
    from rich.markup import escape
    return escape(str(text))


def _presence_word(pl):
    """The three tiers of presence, IN WORDS (Joel 2026-08-31).

    They used to be three MARKS in a 12-cell column -- "°" offline, "·" a
    ghost, nothing at all for someone actually in the room.  Joel read that
    column for a week as a room with people in it; the three names were
    offline DM threads, and the column had no width to say so.  A mark is
    not a label: on the card there is room for the word."""
    from .lobbychat import OFFLINE_ID
    if pl.get("id") == OFFLINE_ID:
        return "offline"
    return "in the room" if pl.get("live", True) else "elsewhere"


def _lobby_entries(m, st):
    """The roster as LABELLED GROUPS: (kind, payload, roster_index) rows,
    ready to window.  Grouping is what makes the presence tiers readable --
    a header names each one and carries its count, so an offline thread can
    never sit under a heading that says anyone is here."""
    from .lobbychat import OFFLINE_ID
    others = list(m._others())
    live, ghosts, threads = [], [], []
    for i, pl in enumerate(others):
        if pl.get("id") == OFFLINE_ID:
            threads.append((i, pl))
        elif not pl.get("live", True):
            ghosts.append((i, pl))
        else:
            live.append((i, pl))
    ent = []
    # the head-count includes YOU -- you are in the room you are counting
    ent.append(("hdr", f"IN THE ROOM  {len(live) + 1}", None))
    if live:
        ent.extend(("row", pl, i) for i, pl in live)
    else:
        ent.append(("dim", "just you", None))
    for title, members in (("ELSEWHERE", ghosts), ("THREADS", threads)):
        if not members:
            continue
        ent.append(("gap", "", None))
        ent.append(("hdr", f"{title}  {len(members)}", None))
        ent.extend(("row", pl, i) for i, pl in members)
    return others, ent


def _lobby_row(pl, st, cur):
    """One roster row: the pick marker, the name, the worn honor, and the
    badge that says something is waiting on it.

    THE HONOR IS PINNED.  In the old 12-cell column a titled name had to
    MARQUEE for its ★ to come round into view (honors 2026-07-14); the card
    has the width to just show it, so a long name loses its TAIL and never
    its star -- the room still sees who is titled at a glance."""
    nm = str(pl.get("name", "?"))
    unread = bool(st) and nm in getattr(st, "unread", set())
    blocked = bool(st) and nm in getattr(st, "blocked", set())
    star = " ★" if (pl.get("pet") or {}).get("title") else ""
    badge = " ✉" if unread else (" ✕" if blocked else "")
    mark = "▸" if cur else " "
    room = CARD_W - 2 - cell_len_(star) - cell_len_(badge)
    txt = _esc(f"{mark} {_fit_cells(nm, room)}{star}{badge}")
    if cur:
        return f"[b]{txt}[/]"
    return f"[dim]{txt}[/]" if (blocked or not pl.get("live", True)) else txt


def _lobby_room(app, m, st):
    """THE ROOM card: who is here, grouped and named."""
    others, ent = _lobby_entries(m, st)
    sel = min(max(0, getattr(m, "sel", 0)), max(0, len(others) - 1))
    rows = 10                      # the list's viewport inside the card:
    #                                the 14 body rows less name/pet/gap/pick
    # keep the PICKED row on screen (it is the one ENTER acts on)
    at = next((n for n, e in enumerate(ent) if e[2] == sel), 0)
    lo = 0 if len(ent) <= rows else max(0, min(at - rows // 2, len(ent) - rows))
    out = []
    for kind, payload, idx in ent[lo:lo + rows]:
        if kind == "hdr":
            out.append(f"[b]{_esc(payload)}[/]")
        elif kind == "dim":
            out.append(f"[dim]{_esc(payload)}[/]")
        elif kind == "gap":
            out.append("")
        else:
            out.append(_lobby_row(payload, st, idx == sel))
    out += [""] * (rows - len(out))
    # the pick line: what the LCD's last row used to marquee at you
    if others:
        pl = others[sel]
        blurb = m._pet_of(pl["id"]) if pl.get("live", True) else ""
        tail = blurb or _presence_word(pl)
        pick = _fit_cells(f"{pl.get('name', '?')} · {tail}", CARD_W)
    else:
        pick = "nobody else is on"
    links = persistence.get_progress().get("connections", 0)
    ride = _fit_cells(f"{app.pet.name} · {links} link"
                      + ("s" if links != 1 else ""), CARD_W)
    card(app, "Lobby", [f"[b]{_esc(_fit_cells(m._last_name or '?', CARD_W))}[/]",
                        f"[dim]{_esc(ride)}[/]", ""] + out
                       + [f"[dim]{_esc(pick)}[/]"])


def _lobby_action(app, m, st):
    """THE PICKED TAMER: their dossier and the verbs, standing still.

    These verbs used to live on the LCD's last line, which is 38 cells wide
    and already had five other jobs -- so "[B]attle [J]og [V/M] PM [X]block
    [ESC]" MARQUEED past like a news ticker.  A menu you have to wait for is
    not a menu."""
    pid, pname, plive = m.action_for
    blocked = bool(st) and pname in getattr(st, "blocked", set())
    pl = next((q for q in (getattr(st, "roster", []) or []) if q.get("id") == pid),
              {"id": pid, "live": plive})
    dossier = m._pet_of(pid)
    lines = [f"[b]{_esc(_fit_cells(pname, CARD_W))}[/]",
             f"[dim]{_esc(_presence_word(pl))}[/]"]
    for part in wrap(dossier, 2) if dossier else []:
        lines.append(f"[dim]{_esc(part)}[/]")
    lines.append("")
    if blocked:
        verbs = [("X", "unblock")]
    elif plive:
        verbs = [("B", "battle"), ("J", "jogress"), ("V", "open thread"),
                 ("M", "quick PM"), ("X", "block")]
    else:
        from .lobbychat import OFFLINE_ID
        verbs = ([] if pid == OFFLINE_ID else [("P", "ping")]) \
            + [("V", "open thread"), ("M", "quick PM"), ("X", "block")]
    # THE CARD IS THE STANDING MENU, so the wipe is advertised HERE for every
    # kind of row -- the 40-col strip cannot fit it beside a live peer's four
    # verbs.  Offered only when there is something to forget.
    if m._has_thread(pname):
        verbs = verbs + [("D", "clear thread")]
    lines += [f"[b]{k}[/]  {_esc(word)}" for k, word in verbs]
    lines += [""] * max(0, 13 - len(lines))
    lines.append("[dim]ESC  back[/]")
    card(app, "Tamer", lines[:14])


def _lobby_thread(app, m, st):
    """THE OPEN THREAD: who you are talking to, and whether they can hear it."""
    pid, pname = m.dm_peer
    pl = next((q for q in (getattr(st, "roster", []) or []) if q.get("id") == pid),
              {"id": pid, "live": False})
    said = len((getattr(st, "dms", {}) or {}).get(pname, []))
    here = pl.get("live", True) and any(q.get("id") == pid
                                        for q in (getattr(st, "roster", []) or []))
    lines = [f"[b]✉ {_esc(_fit_cells(pname, CARD_W - 2))}[/]",
             f"[dim]{_esc(_presence_word(pl))}[/]", ""]
    dossier = m._pet_of(pid)
    for part in wrap(dossier, 2) if dossier else []:
        lines.append(f"[dim]{_esc(part)}[/]")
    lines += ["", f"Said   {said} line" + ("s" if said != 1 else ""),
              "[dim]thread saved[/]", ""]
    lines.append("[dim]they read it now[/]" if here
                 else "[dim]queued till they log in[/]")
    lines += [""] * max(0, 13 - len(lines))
    lines.append("[dim]ESC  back to the room[/]")
    card(app, "Thread", lines[:14])


def _lobby_ladder(app, m):
    """THE SEASON: the LCD page lists the rungs, the card holds YOUR standing."""
    lad = getattr(m.client, "ladder", None) if m.client else None
    if not lad:
        card(app, "Ladder", ["", "[dim]fetching the season…[/]"])
        return
    rank, wins = (list(lad.get("you") or (0, 0)) + [0, 0])[:2]
    days = int(lad.get("days_left") or 0)
    top = list(lad.get("top") or [])
    lead = f"{_fit_cells(str(top[0][0]), 12)} · {int(top[0][1])}W" if top else "—"
    card(app, "Ladder", [
        f"[b]season {_esc(str(lad.get('season', '?')))}[/]",
        "[dim]online wins only[/]", "",
        (f"You    #{rank} · {wins}W" if rank else "You    [dim]unranked[/]"),
        f"Top    {_esc(lead)}",
        f"Rungs  {len(top)} filled", "",
        ("[dim]resets today[/]" if days == 0
         else f"[dim]resets in {days} day" + ("s" if days != 1 else "") + "[/]")])


def _lobby_session(app, m):
    """A SESSION with no panel of its own: the jogress handshake, or a duel
    whose arena failed to build.  (A duel that HAS its panel never reaches
    here -- LobbyPanel.sub hands the card to the BattlePanel.)"""
    who = m.partner[1] if m.partner else "?"
    if m.phase == "jogress":
        res = (m.jresult or {}).get("name")
        lines = [f"[b]✦ with {_esc(_fit_cells(who, 18))}[/]", ""]
        if res:
            lines += [f"[dim]{_esc(_fit_cells(app.pet.name, CARD_W - 2))}[/]",
                      f"[dim]+ {_esc(_fit_cells(m.partner_species or who, CARD_W - 4))}[/]",
                      f"[b]→ {_esc(_fit_cells(res, CARD_W - 4))}[/]", ""]
            lines.append("[dim]both must say yes[/]" if m.j_peer_two_phase
                         else "[dim]ENTER completes it[/]")
        elif m.jphase == "failed":
            lines += wrap(m.fail_reason or "No resonance.", 3)
        else:
            lines.append("[dim]syncing DNA…[/]")
        card(app, "Jogress", lines[:14])
        return
    lines = [f"[b]vs {_esc(_fit_cells(who, 22))}[/]",
             f"[dim]{_esc(_fit_cells(app.pet.name, CARD_W))} stands in[/]", ""]
    if m.bphase == "over":
        outcome = m.bt_outcome or "—"          # hoisted, same 3.10/3.11 rule
        lines += [f"[b]{_esc(_fit_cells(outcome, CARD_W))}[/]"]
        if m.bt_reward:
            lines += [f"[dim]{_esc(part)}[/]" for part in wrap(m.bt_reward, 2)]
    else:
        oc = m.opp_card or {}
        lines += [f"You    {m.my_hp}/{m.my_max}",
                  f"Them   {m.opp_hp}/{m.opp_max}", "",
                  f"[dim]{_esc(_fit_cells(str(oc.get('name', '?')), 12))}"
                  f" · {_esc(str(oc.get('stage', '?'))[:9])}[/]"]
    card(app, "Duel", lines[:14])


def lobby(app):
    """LOBBY: the room, and whatever the room is doing right now.

    ONE painter, phase-dispatched -- the card used to print "Here N tamer /
    Links N / type to chat" through every one of these phases, so a duel, a
    fusion and an open DM thread all wore the chat lobby's hints (the
    status-box liveness rule, applied to the last screen that broke it)."""
    m = app.mode
    st = m.state
    if getattr(m, "phase", None) == "login" or st is None \
            or getattr(st, "me_id", None) is None:
        card(app, "Lobby", ["", "[dim]connecting…[/]"])
        return
    phase = getattr(m, "phase", "lobby")
    if phase == "ladder":
        _lobby_ladder(app, m)
    elif phase in ("jogress", "battle"):
        _lobby_session(app, m)
    elif phase == "dm" and m.dm_peer:
        _lobby_thread(app, m, st)
    elif m.action_for is not None:
        _lobby_action(app, m, st)
    else:
        _lobby_room(app, m, st)


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
    # word-wrap (card audit 2026-07-24): desc runs to 53 chars and the update
    # msg to ~49; the old [:26]/[26:52]/[:26] slices cut words mid-glyph and
    # dropped the msg's action hint.  Body budget = 14 rows (16 - title/DIV);
    # desc<=3 + msg<=4 + 5 fixed leaves headroom.
    lines = [f"[b]{_opts._LABEL.get(row, row.title())}[/]", ""]
    lines += [f"[dim]{ln}[/]" for ln in wrap(desc, 3)]
    lines.append("")
    if m.msg:
        lines += wrap(m.msg, 4)
        lines.append("")
    lines.append("[dim]ENTER toggles[/]")
    card(app, "Options", lines)


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


def zonepick(app):
    """THE ZONE PICKER: what you are about to walk into.

    ⭐Joel's named order 2026-08-04 ("do the zone picker one too"), the last of
    the three the all-cards audit found on bare vitals.

    The panel's own list already carries the NAME, the conquered mark and the
    standing best, so the card does not repeat them (a screen shows a fact
    ONCE).  It carries what the list cannot: the GATE BOSS you have to fell to
    win, how long the road is, whether there is a town on it -- and the
    device's own verdict on the body, read from the SAME call the gate will
    make when you arrive (`battle_condition(check_energy=False)`, the road's
    energy law).  The road card learned that lesson the hard way: a refusal
    that only speaks after forty legs is a refusal that speaks too late."""
    from . import adventure
    p, m, T = app.pet, app.mode, theme
    app.stats_w.border_subtitle = gen_subtitle(p)
    if not m.indices:
        card(app, "Adventure", ["", "[dim]no roads open yet[/]"])
        return
    zi = m.indices[min(m.cursor, len(m.indices) - 1)]
    z = adventure.ZONES[zi]
    boss = (z.get("bosses") or [None])[0]
    conquered = adventure.is_conquered(p, zi)
    best = m.bests.get(zi)
    towns = len(z.get("town_legs") or ())
    # the title, WITHOUT restating the Gate row: `_zone_display` shortens a
    # long zone name to its BOSS ("MasterTyrannomon's Factory Night" ->
    # "MasterTyrannomon"), which is right on the home card and wrong here --
    # the boss already has its own row two lines down.  Keep the BIOME half
    # instead; it is the part the Gate row cannot tell you.
    title = z["name"]
    if cell_len_(title) > CARD_W:
        title = title.split("'s ", 1)[-1] if "'s " in title else title
    lines = [
        f"[b]{_fit_cells(title, CARD_W)}[/]",
        f"[dim]zone {m.indices.index(zi) + 1} of {len(m.indices)} open[/]", DIV,
        f"Gate    [{T.NEG}]{_fit_cells(boss.get('name', '?') if boss else 'no boss', CARD_W - 8)}[/]",
        f"Road    {z['steps']} legs",
        f"Rest    {towns} town" + ("s" if towns != 1 else ""),
        f"Best    {best if best else '[dim]—[/]'}",
        DIV,
    ]
    # the festival and the veteran road are the picker's OWN two notes; the
    # card echoes only the one the list is not already showing
    if m.holiday:
        lines.append(f"[{T.COIN}]★ {_fit_cells(m.holiday, CARD_W - 2)}[/]")
    elif conquered:
        lines.append("[dim]veteran road[/]")
    else:
        lines.append("")
    # THE BODY'S VERDICT, before the walk instead of after it
    cond = p.battle_condition(check_energy=False)
    if cond:
        lines.append(f"[{T.NEG}]{_fit_cells(cond, CARD_W)}[/]")
    elif p.asleep:
        lines.append(f"[{T.NEG}]fast asleep[/]")
    else:
        lines.append(f"Energy  [b]{p.energy}[/]")
    lines += ["", "[dim]ENTER go  ↑↓ pick[/]"]
    app.stats_w.update("\n".join(lines))


def road(app):
    """THE ROAD: the live run — how far, how hurt, what it earned.

    Joel's named order 2026-07-30 ("yeah give the road its own card").  The
    walk had NO painter at all: `painter_for` fell through to the HOME vitals,
    so a run that lasts forty legs showed the same card as standing in the
    yard, and every number the road actually generates — legs walked, lives
    left, bits, fights, loot, the chain — existed only in the run-results card
    at the END, or on the 40-cell strip that has room for exactly one of them
    at a time.

    Grammar is the FIGHT family's, not `card()`'s: `{pet} · road` + DIV, the
    gauge row shaped like the battle card's `You {bar} 3/5`, then the run
    ledger in the run-summary's own labels (Bits / Fights / Loot / Chain).  A
    wild encounter swaps this card for the battle card and back, so the two
    must read as one screen (layout-consistency law)."""
    from . import adventure
    p, m, T = app.pet, app.mode, theme
    a = m.adv
    app.stats_w.border_subtitle = gen_subtitle(p)
    lives = int(getattr(a, "lives", 0))
    hp = hearts(lives, adventure.MAX_LIVES)
    if getattr(m, "_at_gate", False):
        # squared up at the gate: the road is walked, the BOSS is the number
        gauge = f"Gate [{T.NEG}]{_zone_display(a.boss_name, 21)}[/]"
    else:
        gauge = f"Road {bar(a.pct, 11, T.POS)} {a.loc}/{a.total}"
    # the two flex rows: a live chain outranks the festival banner, and the
    # T hint only exists while a road item is actually held
    flex = ""
    if a.streak >= 2:
        flex = f"Chain  [{T.POS}]×{a.streak}[/]"
    elif a.holiday:
        # word-safe, not a raw slice (card audit 2026-07-24): 'Odaiba
        # Memorial Day' is the longest real name and fits whole
        flex = f"[{T.COIN}]★ {wrap(a.holiday, 1, CARD_W - 2)[0]}[/]"
    elif a.replay:
        flex = "[dim]veteran road[/]"
    warp = "[dim]T warp — a road item[/]" if a.held_transports() else ""
    # ⭐THE WOUND LINE, ON SCREEN (road item audit 2026-07-31, Joel: "do 1 and
    # 3").  `record_battle` calls a body "bad" under BATTLE_MIN_ENERGY and
    # rolls the injury table at bad_nv instead of good_nv -- 10% a bout
    # instead of 0.3%.  Measured over 600 runs: 391/400 cross the line by the
    # median leg 19, HALF of all road fights happen under it, and 40% of runs
    # come home wounded.  Nothing named it.  (The road's own refusal is the
    # decoy -- see AdventurePanel._check_spent: energy alone never plants a
    # pet, only a hazard knock past empty does.)
    from .petbase import BATTLE_MIN_ENERGY
    energy_line = (f"Energy [{T.NEG}]{p.energy}[/] [dim]· wounds easy[/]"
                   if p.energy < BATTLE_MIN_ENERGY else f"Energy [b]{p.energy}[/]")
    # ...and WHAT THE GATE WILL SAY, the moment it is true, instead of after
    # forty legs.  Same source the gate itself reads (check_energy=False --
    # the road's own energy law, D3 ruling), so the card cannot drift from it.
    cond = p.battle_condition(check_energy=False)
    lines = [
        f"[b]{p.name[:14]}[/] [dim]· road[/]", DIV,
        f"[b]{_zone_display(a.name, 26)}[/]",
        gauge,
        f"Lives  {hp}",
        energy_line]
    if cond:
        lines.append(f"[{T.NEG}]{cond[:26]}[/]")
    lines += [
        DIV,
        f"Bits   [{T.COIN}]+{a.bits_earned}b[/]",
        f"Fights {a.wins}W/{a.fights}",
        f"Loot   {a.finds}",
        flex, DIV,
        "[dim]SPACE hurry · ESC home[/]",
        warp,
    ]
    app.stats_w.update("\n".join(lines))


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
        # WHO YOU FACE (cup audit 2026-07-25): the faceoff and the
        # introductions used to name the challenger in a caption row UNDER
        # a full-height arena -- four rows past the LCD, so it was clipped
        # off screen and the fight opened against a stranger.  The card is
        # where a fight's context lives (the battle card's own law), so the
        # foe lives here now.
        opp = t.current_opponent() if not t.over else None
        foe = (f"vs [b]{opp['name'][:12]}[/][dim][{opp['attribute'][:2]}][/]"
               if isinstance(opp, dict) else "")
        lines = [
            f"[b]{p.name[:14]}[/] [dim]· cup[/]", DIV,
            f"[b]{t.name[:24]}[/]",
            f"Match    {t.round + 1} / 3",
            foe,
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
    from .petbase import MAX_OBEDIENCE as _MAXOBED
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
             # bar() takes a PERCENT -- the gauge is 0..MAX_OBEDIENCE (150,
             # canon), so scale it or a 100/150 pet reads as full
             f"Manners  {bar(p.obedience * 100 // _MAXOBED, 11, T.POS)}"
             f" {p.obedience}",
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
        if enemy.get("pool_gone"):
            # the boss rotated while this volley played (RaidPanel._pump_pool):
            # the gate's pool is a DIFFERENT boss's now, so show neither
            foe_line = "Pool [dim]this boss is gone[/]"
        elif pool:
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
        # readiness_line is <=26, but the result-anim note ("a draw — counts
        # as a loss · record 12W/30", ~40) also rides hud_note -- wrap so it
        # is not sliced (card audit 2026-07-24).
        lines += [f"[dim]{ln}[/]" for ln in wrap(m.hud_note or "", 2)]
        lines += ["", "[dim]SPACE  lock the bar[/]"]
    else:
        lines += [f"[dim]{ln}[/]" for ln in wrap(m.hud_note or "", 2)]
        lines += ["", "[dim]SPACE skip · ESC end it[/]"]
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
        # ⭐THE (own) MARKER WAS A THIRD COPY, AND IT CLIPPED (card audit
        # 2026-08-04).  Measured: "Field    Virus Buster  (own)" is 28 cells
        # against the 26-wide box, and 7 of the 10 DNA fields overflowed the
        # same way whenever the card showed the pet's OWN field -- which is
        # the commonest case there is.  Textual wrapped the tail onto the
        # box's invisible next row (the CELL LAW, bug #32's family).
        # It was also redundant: the cost row below already says "(own Field)"
        # or "(off Field)", and the static hint says "own Field charges
        # cheap".  A screen shows a fact ONCE -- so the marker goes, and the
        # NAME is clipped to the budget so no future field can overflow here.
        f"Field    {_fit_cells(data.pretty_field(f), CARD_W - 9)}",
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
    from . import (adventurescreen, albumscreen, assistscreen,
                   backgroundscreen, battlescreen, bugscreen, hallscreen,
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
        (albumscreen.AlbumPanel, album),
        (hallscreen.HallPanel, hall),
        (digicorescreen.DigiCorePanel, digicore),
        (raidscreen.RaidPanel, raid),
        (adventurescreen.AdventurePanel, road),
        (adventurescreen.ZonePickPanel, zonepick),
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
