"""tuipet — a terminal Digimon V-Pet rendered with halfblock sprites."""
from __future__ import annotations
# Force 24-bit color BEFORE importing Textual: SSH sessions usually do not carry
# COLORTERM, so Textual would auto-downgrade to xterm-256 and the muted background
# palette (e.g. the teal night hills #507070/#406060) all round to the same gray
# cube-color #5f5f5f -- flattening the ground into a featureless gray block. Modern
# terminals (Termux, etc.) support truecolor; advertise it unless the user set otherwise.
import os as _os
import random
if not _os.environ.get("COLORTERM"):
    _os.environ["COLORTERM"] = "truecolor"
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Static

from . import data
from . import menu
from . import egg as egg_mod
from . import training
from . import battlescreen
from . import dnascreen
from . import transportscreen
from . import adventurescreen
from . import shopscreen
from . import eggguidescreen
from . import habitatscreen
from . import assistscreen
from . import feedscreen
from . import digicorescreen
from . import eggselectscreen
from . import persistence
from . import net
from . import lobbyscreen
from . import tournament
from . import tournamentscreen
from . import bugscreen
from . import helpscreen
from . import titlescreen
from . import optionsscreen
from . import deathscreen
from . import sound
from . import update as update_check
from . import cloudsync
from .pet import Pet
import os

from . import theme
# arena.py owns the LCD renderer; pull the names app.py and the tests still
# reach through `tuipet.app.*` back into this namespace (modularization 2026-07-08).
from .arena import (  # noqa: F401  (full re-export: preserve tuipet.app.* for callers/tests)
    Screen, SCREEN_COLS, SCREEN_ROWS, SPRITE_W, PET_BASE_X, _FxCtx,
    hearts, bar, _FX, GRAVESTONE, POOP_W, POOP_PAD, WEATHER_GLYPH,
    _sky_icon, _RAIN, _SNOW, _PRECIP_N, _scale_hex, _weather_overlay,
    _evol_strobe, _filth_right, _filth_pts, COND_W, COND_H, SICK_ZONE,
    PLAY_HOP, PLAY_LEAD, PLAY_HOP_H, GIFT_OUT, GIFT_BACK, GIFT_HOLD,
    _HIDDEN_STATUS_ICONS, _effect_overlay, _sick_mark_up,
)

import re as _re
# navigation keys: pressing one in a sub-screen plays the scroll blip (unless the
# screen sets its own sfx) — every list cursor-move beeps, V-Pet style
_NAV_KEYS = frozenset({"up", "down", "left", "right", "j", "k", "h", "l", "tab"})

HUD_W = 40              # message-box content width (CSS #msg: 44 - 2 border - 2 padding)


def host_platform():
    """The platform name for bug reports (hostinfo owns the detection so the
    sound backend and the bug feed can never disagree about the host)."""
    from . import hostinfo
    return hostinfo.host_platform()
HUD_GAP = "      "      # blank run between marquee wraps so the looped text reads cleanly
HUD_STEP = 2            # advance the marquee every N frames (10 Hz clock -> ~0.2 s/char)
HUD_HOLD = 8            # marquee steps to hold on the message head before scrolling (~1.6 s)
_HUD_MARKUP = _re.compile(r"\[/?[^\]]*\]")
def _hud_plain(t):
    """Visible text of a Rich-markup string (tags stripped) for width measurement."""
    return _HUD_MARKUP.sub("", t)
def _hud_esc(t):
    """Escape '[' so a plain marquee window is never parsed as Rich markup."""
    return t.replace("[", "\\[")


def keys_markup():
    """The action bar, rebuilt per theme: the shortcut letters wear the
    theme's KEY colour (gameboy = the A/B button magenta; the plain themes
    keep the old cyan).  Was a module constant with `b cyan` baked in --
    unreachable by theme.apply (shell polish 2026-07-05)."""
    k = f"b {theme.KEY}"
    return (
        f"[{k}]f[/] feed  [{k}]p[/] play  [{k}]c[/] clean  [{k}]h[/] heal  [{k}]r[/] praise  [{k}]k[/] scold  [{k}]s[/] lights  [{k}]v[/] assist\n"
        f"[{k}]t[/] train  [{k}]a[/] adventure  [{k}]u[/] cup  [{k}]l[/] lobby (battle·jogress)  [{k}]x[/] DNA  [{k}]n[/] eggs\n"
        f"[{k}]o[/] shop  [{k}]i[/] bag  [{k}]e[/] habitat  [{k}]d[/] digicore  [{k}]g[/] options  [{k}]b[/] bug  [{k}]?[/] help  [{k}]q[/] quit"
    )


def _sound_path():
    return os.path.join(persistence.SAVE_DIR, "sound.txt")


def _load_sound():
    try:
        return open(_sound_path()).read().strip() != "off"
    except OSError:
        return True


def _save_sound(on):
    try:
        os.makedirs(persistence.SAVE_DIR, exist_ok=True)
        with open(_sound_path(), "w") as fh:
            fh.write("on" if on else "off")
    except OSError:
        pass



def _gen_subtitle(pet):
    """'gen N', wearing the bought honor when one is worn (the honors board,
    prestige sink 2026-07-14)."""
    t = data.title_name(persistence.get_title_worn())
    return f"gen {pet.generation} · {t}" if t else f"gen {pet.generation}"


def _age_compact(seconds):
    """d/h then h/m then m/s -- raw total minutes read as noise on an older
    pet ('4325m40s', status-box audit 2026-07-04)."""
    s = int(max(0, seconds))
    if s >= 86400:
        return f"{s // 86400}d{(s % 86400) // 3600:02d}h"
    if s >= 3600:
        return f"{s // 3600}h{(s % 3600) // 60:02d}m"
    return f"{s // 60}m{s % 60:02d}s"


def _temp_str(pet):
    """The HUD temperature — an armed thermostat shows where it's headed
    (48°→62°), so the heat you set from the Habitat screen reads back."""
    if getattr(pet, "heat_on", None) and pet.heat_on():
        return f"{int(pet.temp)}→{int(pet.temp_goal)}°"
    return f"{int(pet.temp)}°"


def _care_deco(pet, word=None):
    """The care badges shown beside the status word -- one list, shared by the
    home Stats panel and the adventure card (Joel 2026-07-12: adventure shows
    the same icons).  Order is priority: the lowest ones drop first on overflow."""
    T = theme
    if word is None:
        word = pet.status_word()
    deco = []
    if pet.asleep and word != "asleep": deco.append("[blue]Zzz[/]")
    if pet.sick and word != "sick": deco.append(f"[{T.NEG}]+sick[/]")
    if pet.is_fatigued() and word != "fatigued": deco.append(f"[{T.NEG}]+tired[/]")
    if pet.is_injured() and word != "injured": deco.append(f"[{T.NEG}]+hurt[/]")
    if pet.is_freezing() and word != "freezing": deco.append("[blue]+cold[/]")
    if pet.is_overheating() and word != "overheating": deco.append(f"[{T.NEG}]+hot[/]")
    if pet.is_frail(): deco.append(f"[{T.NEG}]+frail![/]")
    if getattr(pet, "praise_flag", False): deco.append(f"[{T.POS}]+praise![/]")
    if getattr(pet, "scold_flag", False) or getattr(pet, "discipline_call", False):
        deco.append(f"[{T.NEG}]+scold![/]")
    if pet.poop: deco.append(f"[{T.COIN}]~poop x{pet.poop}[/]")
    if getattr(pet, "effect_id", -1) >= 0: deco.append(f"[{T.POS}]\u2726{pet.effect_name()}[/]")
    if pet.has_medicine(): deco.append(f"[{T.NEG}]+med[/]")
    if pet.has_bandage(): deco.append("[dim]+bnd[/dim]")
    if pet.has_vitamin(): deco.append(f"[{T.POS}]+vit[/]")
    return deco


def _status_line(status, deco, width=26):
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


class Stats(Static):
    def paint(self, pet: Pet):
        if pet.dead:
            return self._paint_grave(pet)
        if pet.num == -1 or pet.stage == "Egg":
            return self._paint_egg(pet)
        T = theme
        div = f"[dim]{'─' * 26}[/]"
        word = pet.status_word()
        deco = _care_deco(pet, word)
        age = _age_compact(pet.age_seconds)
        sky, skycol = _sky_icon(pet)
        aff = pet._affinity()
        amark = (f"[{T.POS}]" + chr(0x2665) + "[/]" if aff > 0
                 else (f"[{T.NEG}]" + chr(0x2716) + "[/]" if aff < 0 else "[dim]·[/dim]"))
        xm = f" [b {T.ACCENT}]X[/]" if pet.x_antibody != "None" else ""
        lifepct = max(0, int((pet.lifespan - pet.age_seconds) / max(1, pet.lifespan) * 100))
        lifecol = T.NEG if pet.is_geriatric else T.LIFE
        self.border_subtitle = _gen_subtitle(pet)
        lines = [
            f"[b]{pet.name[:22]}[/]{xm}",
            f"[dim]{pet.stage}{(' · ' + pet.attribute) if pet.attribute else ''}[/]",
            div,
            f"Hunger  {hearts(pet.hunger)}",
            f"Effort  {hearts(pet.strength)}",
            f"Energy  {bar(pet.energy_pct(), 12, T.ENERGY)}",
            f"Mood    {bar(pet.mood_pct(), 12, T.MOOD)}",
            div,
            f"Power   [{T.POS}]●{pet.vaccine}[/] [{T.ENERGY}]■{pet.data_power}[/] [{T.MOOD}]▲{pet.virus}[/]"
            f" [{T.ACCENT}]◆{getattr(pet, 'dp', 0)}[/]",
            f"HP {pet.full_health}/{pet.max_health()}  Wt {pet.weight}g  [{T.COIN}]{pet.bits}b[/]",
            f"Battle  {pet.wins}W/{pet.battles}   [{T.COIN}]\u2605{pet.trophies}[/]",
            f"@{pet.habitat_obj()['name'][:14]} {amark} [dim]{pet.season}[/]",
            f"[{skycol}]{sky}[/] [dim]{pet.weather} {_temp_str(pet)}[/] [dim]{age}[/]",
            f"Life    {bar(lifepct, 12, lifecol)}",
            _status_line(word, deco),
        ]
        self.update("\n".join(lines))

    def _paint_egg(self, pet):
        mins, secs = divmod(int(pet.age_seconds), 60)
        self.border_subtitle = _gen_subtitle(pet)
        div = f"[dim]{'─' * 26}[/]"
        lines = [
            "[b]Digitama[/] [dim]· egg[/]",
            div,
            "[dim]a new life is warming[/]",
            "",
            "Destined to hatch",
            f"  [b]{egg_mod.hatch_name(pet.egg_type)}[/]",
            div,
            f"Age     {mins}m{secs:02d}s",
            "",
            "[dim]keep it cosy — it[/]",
            "[dim]hatches on its own[/]",
        ]
        self.update("\n".join(lines))

    def _paint_grave(self, pet):
        self.border_subtitle = _gen_subtitle(pet)
        div = f"[dim]{'─' * 26}[/]"
        lines = [
            f"[b]{pet.name[:16]}[/] [dim]· rest[/]",
            div,
            "[dim]a life remembered[/]",
            "",
            f"Lived    {_age_compact(pet.age_seconds)}",
            f"Reached  {pet.stage}",
            f"Cause    {getattr(pet, 'death_cause', '') or 'unknown'}",
            f"Attrib   {pet.attribute}",
            f"Record   {pet.wins}W / {pet.battles}",
            div,
            "[dim]gone, but not[/]",
            "[dim]forgotten.[/]",
            "",
            "[dim]press N for a new egg[/]",
        ]
        self.update("\n".join(lines))


class TuiPetApp(App):
    CSS = """
    Screen { align: center middle; }
    #wrap { width: auto; height: auto; }
    #top { width: auto; height: auto; }
    #left { width: 44; height: auto; }
    #lcd { border: thick #7a7e78; padding: 0 1; background: #c6c9cc; width: 44; height: 14; }
    #msg {
        border: round #7a7e78; padding: 0 1; width: 44; height: 3; margin-top: 1;
        color: #7d8186; content-align: left middle;
    }
    #stats { border: round #7a7e78; padding: 0 1; width: 30; height: 18; margin-left: 1; }
    #keys {
        border: round #7a7e78; padding: 0 1; width: 75; height: 5; margin-top: 1; color: #7d8186;
    }
    """
    # the release-news line (title-screen msg box, first launch per build) --
    # UPDATE THIS WITH EVERY RELEASE that ships something player-visible
    WHATS_NEW = ("CLOUDY NIGHTS ARE NIGHTS: every habitat now has a real "
                 "overcast night sky - dark clouds over its own night ground, "
                 "moon tucked away. No more noon skies at midnight.")

    BINDINGS = [
        # battle + jogress are LOBBY-ONLY (Joel 2026-07-07: "battles and
        # jogress should be online pvp only. we have adventure already") --
        # PvE combat lives in adventure and the cup; fusion needs a real
        # partner from the roster
        ("f", "feed", "Feed"), ("t", "train", "Train"),
        ("p", "play", "Play"), ("c", "clean", "Clean"), ("h", "heal", "Heal"),
        ("r", "praise", "Praise"), ("k", "scold", "Scold"),
        ("a", "adventure", "Adventure"), ("o", "shop", "Shop"), ("i", "inventory", "Bag"), ("e", "habitat", "Habitat"),
        ("d", "digicore", "DigiCore"),
        ("n", "eggguide", "Egg Guide"),
        ("u", "tournament", "Cup"), ("x", "dna", "DNA"),
        ("l", "lobby", "Lobby"),
        ("s", "sleep", "Lights"), ("v", "assist", "Assistant"), ("g", "options", "Options"),
        ("b", "bug", "Bug"), ("question_mark", "help", "Help"), ("q", "quit", "Quit"),
        ("enter", "gift", "Accept gift"),
    ]

    def __init__(self, pet: Pet | None = None):
        super().__init__()
        self._welcome = "Welcome! Raise your pet."
        self._new_game = False
        if pet is None:
            loaded, msg = persistence.load()
            if loaded is not None:
                pet, self._welcome = loaded, (msg or "Welcome back!")
            else:
                self._new_game = True
                if msg:          # a QUARANTINED corrupt save -- never play it
                    self._welcome = msg     # off as a first launch (sweep 07-14)
        self.pet = pet or Pet.new_egg()
        self.mode = None            # active in-display panel (no pop-up screens)
        self._dying_fx = False      # playing the death animation before the memorial
        self._mode_close = None
        self.sound = _load_sound()
        self._needs = False
        self._flash_t = 0           # ticks an action flash holds before a care-need re-asserts
        self._showing_need = False
        self._update_msg = None     # set by the background PyPI check when a newer release exists
        self._showing_update = False
        self._sync = None           # background cloud-save push client (net.SyncClient), or None
        self._hud_scroll = None     # plain text being marquee-scrolled, or None when it fits
        self._hud_off = 0           # marquee window offset
        self._hud_hold = 0          # steps left to hold on the head before scrolling
        self._hud_tick = 0          # frame counter for the marquee throttle

    def compose(self) -> ComposeResult:
        with Vertical(id="wrap"):
            with Horizontal(id="top"):
                with Vertical(id="left"):
                    yield Screen(id="lcd")
                    yield Static("Welcome! Raise your pet.", id="msg")
                yield Stats(id="stats")
            yield Static(keys_markup(), id="keys")

    def on_mount(self):
        self.screen_w = self.query_one("#lcd", Screen)
        self.stats_w = self.query_one("#stats", Stats)
        self.msg_w = self.query_one("#msg", Static)
        self.keys_w = self.query_one("#keys", Static)
        self.screen_w.border_title = "TUIPET"
        self.stats_w.border_title = "STATUS"
        self.keys_w.border_title = "ACTIONS"
        self.screen_w.border_subtitle = "● on"
        wn = self._whats_new()
        if wn:                       # first launch on a new build: the news
            self._welcome = f"{wn}  ·  {self._welcome}"   # rides the msg box
        self._hud(self._welcome)
        theme.apply(theme.load_choice())
        self._restyle()
        self.repaint()
        self._open_mode(titlescreen.TitlePanel(), self._after_title)   # the panel's strip() carries PRESS ENTER
        self.set_interval(0.1, self.on_frame)    # single DVPet interval clock: 1 tick == 0.1s (main view AND sub-screens)
        self.set_interval(1.0, self.on_tick)
        self.set_interval(10.0, self.autosave)
        self.run_worker(self._check_update(), name="update", exclusive=False)
        self.run_worker(self._flush_bugs(), name="bugflush", exclusive=False)
        self._start_sync()

    def _whats_new(self):
        """One 'WHAT'S NEW' line in the msg box, on the FIRST launch of a new
        build only (Joel 2026-07-07: release news belongs on the title
        screen).  The seen stamp lives in settings so it survives pets and
        rides the .bak rotation like every app-level pref."""
        from . import update
        cur = update.current_version()
        if not cur:
            return None
        s = persistence.load_settings()
        if s.get("seen_version") == cur:
            return None
        s["seen_version"] = cur
        persistence.save_settings(s)
        if self._new_game:
            # a first-EVER install also has no seen_version, but release news
            # names systems a brand-new player hasn't met (honors, DNA
            # wagers...) -- stamp it seen and say nothing (sweep 2026-07-14)
            return None
        return f"WHAT'S NEW in v{cur}: {self.WHATS_NEW}"

    def _drain_pms(self):
        """Private messages land on the always-on sync connection; surface
        them as ✉ flashes in the home message box.  While the LOBBY is open
        its chat already shows them (the server delivers to both connections)
        -- drop the duplicates; in any other sub-screen they stay queued and
        flash when you're back home (presence 2026-07-05)."""
        sync = getattr(self, "_sync", None)
        if sync is None or not getattr(sync, "inbox", None):
            return
        if isinstance(self.mode, lobbyscreen.LobbyPanel):
            st = self.mode.state
            if st is None:
                return                     # login phase: keep them queued
            if not st.connected:
                # PMs that arrived BEFORE this lobby session's client existed
                # (queued under another sub-screen, or landing in the connect
                # window) are in no chat history -- the old clear() burned
                # them unseen (message audit 2026-07-06).  Seed the fresh
                # pane; once CONNECTED the lobby client receives its own
                # copy, so then (and only then) the ghost's are duplicates.
                for nm, tx in sync.inbox:
                    st.chat.append((nm if nm == "📢" else f"✉{nm}", tx))
                del st.chat[:-net.CHAT_CAP]
            sync.inbox.clear()
            return
        if self.mode is not None:
            return                             # queued: flashes back on the home screen
        if self._flash_t > 0:
            return                             # one ✉ at a time: let the current flash hold
        nm, tx = sync.inbox.pop(0)
        # a PM's sender name AND body are REMOTE strings -- escape their '[' so
        # a message like '[/]' can't unbalance this markup and crash the render
        # (Rich-brackets hard rule, remote-triggered; chat-input audit 2026-07-07).
        # The lobby chat pane is already safe (Text.append renders literally);
        # this flash is the one markup-parsed sink for remote text.
        if nm == "📢":                       # a server announcement, not a peer's ✉
            self.flash(f"📢 [b]{_hud_esc(tx)}[/]")
        else:
            self.flash(f"✉ [b]{_hud_esc(nm)}[/]: {_hud_esc(tx)}")
        self.beep("menu", bell=False)

    def _start_sync(self):
        """Spin up the background cloud-save push client once an account exists
        (idempotent). The startup pull already ran in main(); this handles pushes."""
        if self._sync is not None:
            return
        if not persistence.sync_enabled():
            return                       # opted out (TUIPET_NO_SYNC or the options toggle)
        name, pw = persistence.get_account()
        if not name:
            return                       # no account yet (first launch) — started after account setup
        self._sync = net.SyncClient(_lobby_uri(), name, pw)
        self.run_worker(self._sync.run(), name="sync", exclusive=False)

    def _push_cloud(self):
        """Queue the current pet's save for upload (no-op until the account/sync exists)."""
        if self._sync is not None and self.pet is not None and persistence.sync_enabled():
            self._sync.push_save(persistence.to_save_dict(self.pet))

    async def _check_update(self):
        """Background, once per launch: ask PyPI for a newer tuipet and INSTALL
        it (Joel 2026-07-14: "make it so the game automatically checks and
        updates itself... then they have to restart for it to be the new one").

        Never blocks the game: this runs off the UI thread and the player keeps
        playing the version they launched.  Python already imported that code,
        so a fresh install can only take effect on the NEXT launch -- the nudge
        says exactly that, and never claims a live swap.

        Honest about what it cannot do (the silent-failure law): where we cannot
        run pip for the player -- iOS sandboxes subprocesses, a source checkout
        has no release to install over -- we fall back to telling them the
        command.  A failed install says so and hands the command over too; it
        never pretends the update happened.
        """
        import asyncio
        latest = await asyncio.to_thread(update_check.latest_if_newer)
        if not latest:
            return
        if not persistence.get_auto_update():          # the player opted out
            self._update_msg = f"⬆ tuipet {latest} out — {update_check.manual_command()}"
            return
        if update_check.upgrade_argv() is None:        # iOS / source: cannot self-install
            self._update_msg = f"⬆ tuipet {latest} out — {update_check.manual_command()}"
            return
        self._update_msg = f"⬆ installing tuipet {latest}…"
        ok, _msg = await asyncio.to_thread(update_check.run_upgrade)
        if ok:
            self._updated_to = latest
            self._update_msg = f"✔ tuipet {latest} installed — restart to play it"
        else:
            self._update_msg = f"⬆ tuipet {latest} out — {update_check.manual_command()}"

    def _after_title(self, _=None):
        # The account wall used to stand HERE: name + password demanded on
        # first launch, before the player had seen a single pet (sweep
        # 2026-07-14).  The account only matters online -- the lobby asks for
        # one when it's first opened, and sync starts on the next autosave.
        self._post_title()

    def _post_title(self):
        if self._new_game:
            self._open_mode(eggselectscreen.EggSelectPanel(self.pet), self._after_egg_pick)
        else:
            self._hud(self._welcome)
            self.repaint()

    def _grant_digimemory(self, pet):
        """Hand the banked inheritance data to the next generation: the payload
        rides the pet's save; item 32 appears in its bag (DVPet items persist
        across resetToEgg -- tuipet's generations carry only this one)."""
        mem = persistence.take_digimemory()
        if mem:
            pet.digimemory = dict(mem)
            # the inherited ESTATE bag may already carry the elder's unused
            # husk (the re-banked-payload case) -- never a second chip for
            # one payload (digimemory audit 2026-07-06)
            if pet.inventory.get("i:32", 0) <= 0:
                pet.add_item("i:32")
        # the departed's care grade seeds this generation's bonus (careBonusOnReset)
        pet.evol_bonus = persistence.take_bonus_seed()

    def _after_death(self, result):
        if result == "new":
            self.action_new()
        else:
            self.repaint()

    def _after_egg_pick(self, egg_type):
        if egg_type is None:                       # backed out -> return to the title
            self._open_mode(titlescreen.TitlePanel(), self._after_title)
            return
        if egg_type == "guide":                    # N: consult the egg guide, then
            self._open_mode(eggguidescreen.EggGuidePanel(self.pet),   # come back
                            lambda _=None: self._open_mode(
                                eggselectscreen.EggSelectPanel(self.pet),
                                self._after_egg_pick))
            return
        self._new_game = False                     # the fresh start is settled
        self.pet = Pet.new_egg(egg_type=egg_type)
        self._grant_digimemory(self.pet)
        self.flash("Take good care of your egg!  (? = help)")
        self.repaint()

    def autosave(self):
        persistence.save(self.pet)
        self._start_sync()              # idempotent: picks up a re-enabled cloud toggle
        self._warn_if_unsaveable()
        self._warn_if_cloud_dropped()
        self._note_progress()
        self._push_cloud()              # mirror the autosave up to the cloud

    def _warn_if_cloud_dropped(self):
        """The server is REFUSING our cloud saves (a newer session of this
        account owns them).  The local save is fine, but cross-device sync is
        dead -- and we used to never mention it (swallowed-failure sweep
        2026-07-13)."""
        sync = getattr(self, "_sync", None)
        if sync is None or not getattr(sync, "cloud_dropped", False):
            return
        if getattr(self, "_cloud_warned", False):
            return
        self._cloud_warned = True
        self.flash(f"[{theme.NEG}]⚠ Cloud sync off — tuipet is open in a newer "
                   f"session. This device saves locally only.[/]")

    def _warn_if_unsaveable(self):
        """A save dir the OS refuses used to fail SILENTLY -- the pet simply
        never persisted and the player found out by losing it (iOS's read-only
        home, support pass 2026-07-13).  Say it once, loudly, with the fix."""
        if not persistence.save_failed or getattr(self, "_save_warned", False):
            return
        self._save_warned = True
        self.beep("alarm")
        self.flash(f"[{theme.NEG}]⚠ CAN'T SAVE — your pet will not persist! "
                   f"Set TUIPET_SAVE_DIR to a writable folder.[/]")

    def _note_progress(self):
        """Record cross-generation egg-unlock milestones from the live pet."""
        p = self.pet
        if p is None or p.stage in ("", "Egg"):
            return
        persistence.note_generation(p.generation)
        if p.stage in data.STAGE_ORDER:
            persistence.note_stage_index(data.STAGE_ORDER.index(p.stage))
        if getattr(p, "x_antibody", "None") != "None":
            persistence.note_xanti()

    def on_unmount(self):
        persistence.save(self.pet)
        self._flush_dms_on_quit()       # a lobby quit must not drop PMs from this session
        self._flush_cloud_on_quit()     # capture the final state cloud-side on any exit

    def _flush_dms_on_quit(self):
        """Quitting straight from the lobby must persist DMs received this
        session: incoming PMs live only in memory until a read/leave saves
        them, so a hard quit (Ctrl-C, terminal close) would otherwise drop
        them (the 'A' gap, 2026-07-12)."""
        if isinstance(self.mode, lobbyscreen.LobbyPanel):
            try:
                self.mode._save_dms()
            except Exception:
                pass

    def _flush_cloud_on_quit(self):
        """Best-effort blocking push so the final state is captured cloud-side."""
        if self._sync is None:
            return
        try:
            name, pw = persistence.get_account()
            cloudsync.push_save(_lobby_uri(), name, pw,
                                persistence.to_save_dict(self.pet), timeout=2.0)
        except Exception:
            pass

    def on_key(self, event):
        fx = getattr(getattr(self, "screen_w", None), "fx", None)
        if fx is not None and fx.get("kind") == "dying":
            # dying(): the pet is a BUTTON -- frantic taps can save it
            # (numHits > HitsToSave x (savedFromDeath + 1))
            self._revive_hits = getattr(self, "_revive_hits", 0) + 1
            self.beep("click", bell=False)
            event.stop()
            event.prevent_default()
            return
        if (self.mode is None and not self.pet.dead
                and getattr(self.screen_w, "fx", None) is not None
                and event.key != "q"):
            # canon disableMainMenu: the WHOLE menu locks while an animation
            # plays (Joel 2026-07-06).  The 8 mutating care actions always
            # guarded; the browse menus could still open mid-ceremony -- now
            # every binding waits for the show.  q (quit) stays live; the
            # dying-fx revive mash is handled above this gate.
            event.stop()
            event.prevent_default()
            return
        if self.mode is None and self.pet.dead:
            # A departed pet can DO nothing (the device shows only the grave).
            # ONE chokepoint ahead of every global binding -- the per-action
            # can_*() gates kept slipping (a dead mon could still adventure,
            # Joel 2026-07-05).  Any care key leads back to the memorial;
            # quit and options stay live beside the grave.
            if event.key not in ("q", "g"):
                event.stop()
                event.prevent_default()
                self._open_mode(deathscreen.DeathPanel(
                    self.pet, old_mem=persistence.peek_digimemory()), self._after_death)
            return
        if self.mode is not None:
            event.stop()
            event.prevent_default()      # a panel owns the keyboard: don't fire global BINDINGS
            # Textual names punctuation keys ("." -> "full_stop", "!" ->
            # "exclamation_mark"), so a panel's `len(k) == 1 and k.isprintable()`
            # text test silently dropped every non-alphanumeric.  For a
            # text-capturing panel, forward the actual typed character instead of
            # the key NAME (nav keys carry no printable character, so they still
            # arrive by name; space stays "space" via its explicit handling).
            k = event.key
            ch = getattr(event, "character", None)
            if (getattr(self.mode, "captures_text", False)
                    and ch is not None and len(ch) == 1
                    and ch.isprintable() and not ch.isspace()):
                k = ch
            result = self.mode.key(k)
            snd = getattr(self.mode, "sfx", None)
            if snd:
                self.beep(snd, bell=False)
                self.mode.sfx = None
            elif getattr(self.mode, "captures_text", False):
                pass                                # typing: no nav/confirm blips (audit 2026-07)
            elif event.key in _NAV_KEYS:
                self.beep("scroll", bell=False)     # cursor-move blip for every list screen
            elif event.key == "enter":
                self.beep("confirm", bell=False)    # menu confirm (a screen's own sfx wins above)
            elif event.key == "escape":
                self.beep("cancel", bell=False)     # back/cancel
            if result is not None and result[0] == "done":
                self._close_mode(result[1])
            elif result is not None and result[0] == "quit":
                self.action_quit()                  # a screen asked to quit the app (e.g. q on the title)
            elif event.key == "q" and not getattr(self.mode, "captures_text", False):
                self.action_quit()                  # QoL: q quits from any non-text screen, not just the main view
            else:
                self.repaint()

    def _mode_strip(self):
        """A scene panel's one-line strip (note + key hints) rides the #msg box
        under the LCD -- the box sat BLANK during every sub-screen while the
        panels stacked that chrome inside the LCD and overflowed its 12 rows
        (the 2026-07-04 box-clip audit).  _hud gives long strips the marquee."""
        m = self.mode
        while getattr(m, "sub", None) is not None:   # the DEEPEST panel owns the strip
            m = m.sub                                # (town inside adventure, battle inside town)
        strip = getattr(m, "strip", None)
        self._hud(strip() if strip is not None else "")

    def _open_mode(self, panel, on_close=None):
        self.mode = panel
        self._mode_close = on_close
        # clear the message strip so a screen never shows the PREVIOUS screen's
        # farewell flash; scene panels put their own strip() here instead
        if getattr(self, "msg_w", None) is not None:
            self._hud("")
            self._mode_strip()
        self.repaint()

    def _close_mode(self, result):
        cb = self._mode_close
        self.mode = None
        self._mode_close = None
        # a screen's strip must never outlive it (Joel 2026-07-10: the lobby's
        # hints stuck to the main view -- with no care need pending, on_tick's
        # message cascade never rewrites an already-filled box).  Clear BEFORE
        # the callback so a farewell flash or a chained _open_mode still paints
        # onto a clean box.
        if getattr(self, "msg_w", None) is not None:
            self._hud("")
        if cb:
            cb(result)
        else:
            self.repaint()

    # ---- multiplayer lobby ----------------------------------------------
    def action_help(self):
        self._open_mode(helpscreen.HelpPanel(self.pet), lambda _=None: self.repaint())

    def action_bug(self):
        self._open_mode(bugscreen.BugReportPanel(self.pet), self._after_bug)

    def _after_bug(self, result=None):
        if isinstance(result, tuple) and result and result[0] == "bug":
            name = persistence.get_account()[0] or ""
            self.run_worker(self._send_bug(result[1], self._bug_meta(), name),
                            name="bug", exclusive=False)
            self._hud("Sending your report\u2026")
        self.repaint()

    async def _send_bug(self, text, meta, name):
        ok = await net.submit_bug(_lobby_uri(), text, meta, name=name)
        if ok:
            self._hud("Bug report sent \u2014 thank you!")
        elif persistence.add_pending_bug(dict(meta, text=text, name=name)):
            self._hud("Offline \u2014 saved; it will send next time you are online.")
        else:
            # the stash failed too (a read-only save dir): do not promise a
            # send we cannot make (swallowed-failure sweep 2026-07-13)
            self._hud(f"[{theme.NEG}]Couldn't send or save that report \u2014 sorry.[/]")

    async def _flush_bugs(self):
        """Best-effort resend of any bugs stashed while offline."""
        pending = persistence.take_pending_bugs()
        left = []
        for rec in pending:
            if left:                       # already hit an outage: keep the rest
                left.append(rec); continue
            text, name = rec.get("text", ""), rec.get("name", "")
            meta = {kk: vv for kk, vv in rec.items() if kk not in ("text", "name")}
            if not (text and await net.submit_bug(_lobby_uri(), text, meta, name=name)):
                left.append(rec)
        for rec in left:
            persistence.add_pending_bug(rec)

    def _bug_meta(self):
        import platform as _pf
        try:
            from importlib.metadata import version as _v
            ver = _v("tuipet")
        except Exception:
            ver = ""
        p = self.pet
        return {"version": ver,
                "platform": "%s py%s" % (host_platform(), _pf.python_version()),
                "pet": {"num": getattr(p, "num", 0), "name": getattr(p, "name", ""),
                        "stage": getattr(p, "stage", ""),
                        "gen": getattr(p, "generation", 0)}}

    def action_lobby(self):
        if self.mode is not None:
            return
        name, pw = persistence.get_account()
        self._open_mode(lobbyscreen.LobbyPanel(self.pet, self._lobby_connect,
                        name=name, pw=pw),
                        self._after_lobby)

    def _lobby_connect(self, name, pw, card):
        """Create + start the WebSocket client; the app owns its worker lifecycle."""
        persistence.set_account(name, pw)
        uri = _lobby_uri()
        client = net.LobbyClient(uri, name, pw, card)
        self._lobby_worker = self.run_worker(client.run(), name="lobby", exclusive=False)
        return client

    def _after_lobby(self, result=None):
        # The lobby panel applies its own jogress/battle results in-place (you stay
        # in the lobby between sessions), so here we just tear down the connection.
        w = getattr(self, "_lobby_worker", None)
        if w is not None:
            w.cancel()
            self._lobby_worker = None
        self.repaint()

    def action_quit(self):
        persistence.save(self.pet)
        self.exit()

    def _handle_exception(self, error: Exception) -> None:
        # Last-chance honesty (sweep 2026-07-14): save the pet, keep the
        # traceback, queue a bug report -- THEN let Textual show its crash
        # screen.  A raw panic used to be the whole story, with the last ~10s
        # of play lost and the reporter never offered.
        try:
            persistence.save(self.pet)
        except Exception:
            pass
        log = None
        try:
            log = persistence.write_crash_log(error)
        except Exception:
            pass
        try:
            import traceback
            tail = "".join(traceback.format_exception(
                type(error), error, error.__traceback__))[-1500:]
            persistence.add_pending_bug(dict(
                self._bug_meta(), name=persistence.get_account()[0],
                text=f"[auto] crash: {error!r}\n{tail}"))
        except Exception:
            pass
        self._crash_note = ("tuipet crashed — your pet was saved."
                            + (f"  Details: {log}" if log else "")
                            + "  A report goes out next launch.")
        super()._handle_exception(error)

    def beep(self, name=None, bell=True):
        if not self.sound:
            return
        if name and sound.play(name):
            return
        if bell:
            self.bell()

    def _toggle_sound(self):
        """The options-menu sound switch (the panel carries its own message)."""
        self.sound = not self.sound
        _save_sound(self.sound)
        if self.sound:
            self.bell()

    def _restyle(self):
        # the DMG-shell reading (2026-07-05): the LCD's thick frame is the
        # screen BEZEL, the round boxes are the SHELL body, the titles/key
        # hints are printed LABEL text -- plain themes fall back to border/mid
        try:
            for w in (self.screen_w, self.stats_w, self.msg_w, self.keys_w):
                w.styles.border = ("round", theme.SHELL)
                w.styles.border_title_color = theme.LABEL
            self.screen_w.styles.border = ("thick", theme.BEZEL)
            self.screen_w.styles.border_subtitle_color = theme.ACCENT
            self.screen_w.styles.background = theme.LCD_BG
            self.msg_w.styles.color = theme.LABEL
            self.keys_w.styles.color = theme.LABEL
            self.keys_w.update(keys_markup())   # the shortcut letters re-tint too
        except Exception:
            pass

    def action_options(self):
        """The OPTIONS menu gathers the app-level switches (theme / sound /
        account / update / keys / new egg / erase) under one key -- g/m/n gave
        the action bar its breathing room back (Joel 2026-07-04)."""
        if self.mode is not None:
            return
        self._open_mode(optionsscreen.OptionsPanel(
            self.pet, lambda: self.sound, self._toggle_sound,
            on_theme_change=self._restyle,
            bindings=self.BINDINGS,
            update_hint=lambda: getattr(self, "_update_msg", "")),
            self._after_options)

    def _after_options(self, result):
        self._restyle()                             # a previewed theme may have settled
        if result and result[0] == "new":
            self.action_new()
            return
        if result and result[0] == "account":
            self.run_worker(self._switch_account(result[1], result[2]),
                            name="switch", exclusive=False)
            return
        if result and result[0] == "erase":
            if self._sync is not None:              # the pusher must not re-seed the cloud
                self._sync._stop = True
                self._sync = None
            persistence.erase_all()
            self.pet = Pet.new_egg()                # placeholder until the carousel picks
            # a fresh start IS a new game: without this flag the post-title flow
            # skipped the egg-select carousel and kept the placeholder egg
            # (Joel 2026-07-05: "automatically selected an egg for me??")
            self._new_game = True
            self._open_mode(titlescreen.TitlePanel(), self._after_title)
            self.flash("All data erased — a fresh start.")
            return
        self.repaint()

    async def _switch_account(self, name, pw):
        """Sign in as another account (OPTIONS → Account).  The current pet is
        parked with the OLD account's cloud first (switch back any time), then
        the new account's cloud save replaces the local one — or the egg
        carousel opens when it has none.  A wrong password or an unreachable
        lobby aborts WITHOUT switching (probe distinguishes the two — pull_save
        can't, and a typo'd password must not strand the player on a fresh
        start).  Device-lifetime progress (album, lifetime wins, owned eggs)
        stays local, like canon's device-scoped Shared file."""
        import asyncio
        old_name, old_pw = persistence.get_account()
        self.flash("Switching account…")
        verdict, save = await asyncio.to_thread(
            cloudsync.probe, _lobby_uri(), name, pw)
        if verdict == "badpw":
            self.flash("Wrong password for that name.")
            self.beep("error", bell=False)
            return
        if verdict != "ok":
            self.flash("Can't reach the lobby — try again online.")
            self.beep("error", bell=False)
            return
        if save is not None:
            # validate BEFORE committing to the switch: an unreadable cloud
            # blob must not cost the player their current login (the same
            # strict probe sync_down_at_startup runs)
            pet_probe, _ = persistence.pet_from_save(dict(save),
                                                     catch_up=False, strict=True)
            if pet_probe is None:
                self.flash("That cloud save is unreadable — kept your account.")
                self.beep("error", bell=False)
                return
        persistence.save(self.pet)                   # park the pet with the OLD account
        if old_name and old_name != name:
            await asyncio.to_thread(                 # last-write-wins guarded upload
                cloudsync.push_save, _lobby_uri(), old_name, old_pw,
                persistence.to_save_dict(self.pet))
        if self._sync is not None:                   # the old pusher must stop first
            self._sync._stop = True
            self._sync = None
        persistence.set_account(name, pw)
        if save is not None:
            persistence.write_save_dict(save)
            loaded, msg = persistence.load()
            self.pet = loaded or Pet.new_egg()
            self._start_sync()
            self.flash(f"Signed in as {_hud_esc(name)} — {msg or 'welcome back!'}")
            self.repaint()
        else:
            persistence.delete()                     # the old pet must not leak in
            self.pet = Pet.new_egg()                 # placeholder until the carousel picks
            self._start_sync()
            self.flash(f"Signed in as {_hud_esc(name)} — a fresh start.")
            self._open_mode(eggselectscreen.EggSelectPanel(self.pet),
                            self._after_egg_pick)

    def _center(self, text):
        from rich.text import Text
        n = text.plain.count("\n") + 1
        pad = max(0, (SCREEN_ROWS - n) // 2)
        if not pad:
            return text
        out = Text("\n" * pad)
        out.append_text(text)
        return out

    def repaint(self):
        if self.mode is not None:
            self.screen_w.update(self._center(self.mode.text()))
            self._mode_strip()
        else:
            self.screen_w.paint(self.pet)
        if isinstance(self.mode, titlescreen.TitlePanel):
            self._status_card("TUIPET", ["[dim]a terminal v-pet[/]", "", "",
                                         "[dim]a creature awaits[/]", "",
                                         "[dim]press ENTER[/]", "[dim]to begin[/]"])
        elif isinstance(self.mode, eggselectscreen.EggSelectPanel):
            self._status_eggselect()
        elif (painter := self._status_painter()) is not None:
            painter()
        else:
            # data/digicore browses in the LCD; keep live vitals on the right
            self.stats_w.paint(self.pet)

    def _status_painter(self):
        """The mode's live status-panel painter (one table for repaint AND
        on_frame -- the two hand-rolled dispatches drifted; audit 2026-07)."""
        table = ((adventurescreen.AdventurePanel, self._status_adventure),
                 (tournamentscreen.TournamentPanel, self._status_tournament),
                 (training.TrainingPanel, self._status_training),
                 (battlescreen.BattlePanel, self._status_battle),
                 (habitatscreen.HabitatPanel, self._status_habitat),
                 (dnascreen.DNAPanel, self._status_dna))
        for cls, painter in table:
            if isinstance(self.mode, cls):
                return painter
        return None

    def _status_eggselect(self):
        m = self.mode
        # carousel = hatchable eggs ONLY (Joel 2026-07-12: no silhouettes,
        # no goals); the badge/shown branches below stay defensive in case a
        # locked/buyable egg ever leaks onto it.
        idx = m.carousel[m.i] if m.carousel else 0
        state = m.states.get(idx, ("owned", 0))[0]
        badge = {"temp": "[dim]this gen only[/]", "locked": "[dim]sealed[/]",
                 "buyable": "[dim]sealed[/]"}.get(state, "[dim]ready[/]")
        shown = "???" if state in ("locked", "buyable") else egg_mod.hatch_name(idx)
        self._status_card("New Egg", [f"[dim]{m.i + 1} of {m.n}[/]",
                                      f"[dim]{m.locked} still locked[/]", "",
                                      "Destined to hatch", f"  [b]{shown}[/]",
                                      f"  {badge}", "",
                                      "[dim]←→ browse  ENTER pick[/]"])

    def _status_card(self, title, lines):
        self.stats_w.border_subtitle = ""
        body = [f"[b]{title}[/]", f"[dim]{'─' * 26}[/]"] + lines
        self.stats_w.update("\n".join(body))

    def _status_tournament(self):
        p, t, T = self.pet, self.mode.tourney, theme
        self.stats_w.border_subtitle = _gen_subtitle(p)
        if t is None:                      # cup-select phase (no bout yet)
            self._status_card("Cup", [f"[dim]{p.season} season[/]", "", "Pick a cup", "to enter."])
            return
        div = f"[dim]{'─' * 26}[/]"
        if t.over and t.champion:
            lines = [f"[b]{p.name[:14]}[/] [dim]· cup[/]", div,
                     f"[b]{t.name[:24]}[/]", "",
                     f"[{T.POS}]\u2605 CHAMPION \u2605[/]", "",
                     f"Trophy   [{T.COIN}]\u2605{p.trophies}[/]",
                     f"Reward   [{T.COIN}]+{t.reward_bits}b[/]", div,
                     "[dim]you took the cup![/]"]
        elif t.over:
            lines = [f"[b]{p.name[:14]}[/] [dim]· cup[/]", div,
                     f"[b]{t.name[:24]}[/]", "",
                     f"[{T.NEG}]eliminated[/]",
                     f"[dim]in the {t.round_name}[/]", "",
                     f"Trophy   [{T.COIN}]\u2605{p.trophies}[/]", div,
                     "[dim]train up, try again[/]"]
        else:
            lines = [
                f"[b]{p.name[:14]}[/] [dim]· cup[/]", div,
                f"[b]{t.name[:24]}[/]",
                f"Match    {t.round + 1} / 3",
                f"Trophy   [{T.COIN}]\u2605{p.trophies}[/]",
                div,
                f"Effort   {hearts(p.strength)}",
                f"Energy   {bar(p.energy_pct(), 11, T.ENERGY)}",
                f"Power    [{T.POS}]●{p.vaccine}[/] [{T.ENERGY}]■{p.data_power}[/] [{T.MOOD}]▲{p.virus}[/]",
                div,
                "[dim]fight for the cup[/]",
            ]
        self.stats_w.update("\n".join(lines))

    def _status_training(self):
        from .training import (GAMES, VACCINE_WINDOW, HP_ROUNDS, VIRUS_BAR_MIN,
                               DATA_ROUNDS, DATA_PASS)
        p, tp, T = self.pet, self.mode, theme
        self.stats_w.border_subtitle = _gen_subtitle(p)
        div = f"[dim]{'-' * 26}[/]".replace("-", "\u2500")
        eff = hearts(p.strength)
        energy = bar(p.energy_pct(), 11, T.ENERGY)
        power = f"[{T.POS}]●{p.vaccine}[/] [{T.ENERGY}]■{p.data_power}[/] [{T.MOOD}]▲{p.virus}[/]"
        label = GAMES[tp.gi][1]
        gk = tp.gkey
        if tp.phase == "menu":
            lines = [f"[b]{p.name[:14]}[/] [dim]\u00b7 train[/]", div,
                     "[b]choose a drill[/]", "",
                     f"Effort   {eff}", f"Power    {power}", f"Energy   {energy}",
                     div, "[dim]pick what to build[/]"]
        elif tp.phase == "done":
            verdict = f"[{T.POS}]drill complete[/]" if tp.success else f"[{T.NEG}]needs work[/]"
            lines = [f"[b]{p.name[:14]}[/] [dim]\u00b7 train[/]", div,
                     f"[b]{label}[/]", "", verdict, "",
                     f"Effort   {eff}", f"Energy   {energy}", div,
                     f"[dim]{(tp.result or '')[:24]}[/]"]
        else:
            if gk == "hp":
                dots = "\u25cf" * tp.rounds_won + "\u25cb" * (HP_ROUNDS - tp.rep) + "\u00b7" * (tp.rep - tp.rounds_won)
                prog, prog2 = f"Round    {min(tp.rep + 1, HP_ROUNDS)} / {HP_ROUNDS}", f"Won      {dots}"
                target = f"Effort   {eff}"
            elif gk == "vaccine":
                tpct = max(0, tp.timer) / VACCINE_WINDOW * 100
                prog, prog2 = f"Hits     {tp.taps} / {tp.vaccine_target}", f"Time     {bar(tpct, 11, T.MOOD)}"
                target = f"Vaccine  [{T.POS}]{p.vaccine}[/]"
            elif gk == "data":
                # the versus card counts like the HP card: round + passes
                # (canon rebuild 2026-07-13 -- the old card read the retired
                # turret fields and CRASHED the live drill, Joel's phone report)
                prog = f"Round    {min(tp.tt_round + 1, DATA_ROUNDS)} / {DATA_ROUNDS}"
                prog2 = f"Past     {tp.tt_past} / {DATA_PASS}"
                target = f"Data     [{T.ENERGY}]{p.data_power}[/]"
            else:
                prog, prog2 = f"Power    {int(tp.pos)}", f"Need     {VIRUS_BAR_MIN}"
                target = f"Virus    [{T.MOOD}]{p.virus}[/]"
            # the card's flavour slot carries the CONTROLS now -- the in-LCD
            # footer that used to is gone (box-clip audit 2026-07-04).  Split on
            # the hints' own triple-space gap so a key stays WITH its action
            # (a hard [:26] slice cut every hint mid-word -- audit 07-04)
            parts = [s.strip() for s in tp._hint().split("   ") if s.strip()]
            if len(parts) >= 2 and all(len(s) <= 26 for s in parts[:2]):
                h1, h2 = parts[0], "  ".join(parts[1:])[:26]
            else:
                import textwrap
                h1, h2 = (textwrap.wrap(tp._hint(), 26) + ["", ""])[:2]
            lines = [f"[b]{p.name[:14]}[/] [dim]\u00b7 train[/]", div,
                     f"[b]{label}[/]", prog, prog2, div,
                     target, f"Energy   {energy}", div,
                     f"[dim]{h1}[/]", f"[dim]{h2}[/]"]
        self.stats_w.update("\n".join(lines))

    def _status_battle(self):
        p, m, T = self.pet, self.mode, theme
        b = m.battle
        self.stats_w.border_subtitle = _gen_subtitle(p)
        div = f"[dim]{'─' * 26}[/]"
        php = getattr(m, "hud_php", b.pet_hp)
        fhp = getattr(m, "hud_fhp", b.enemy_hp)
        pp = int(100 * php / b.pet_max) if b.pet_max else 0
        fp = int(100 * fhp / b.enemy_max) if b.enemy_max else 0
        tag = f" [{T.NEG}]BOSS[/]" if b.enemy.get("boss") else ""
        lines = [
            f"[b]{p.name[:14]}[/] [dim]· battle[/]", div,
            f"vs [b]{b.enemy['name'][:14]}[/]{tag}", "",
            f"You  {bar(pp, 11, T.POS)} {php}/{b.pet_max}",
            f"Foe  {bar(fp, 11, T.NEG)} {fhp}/{b.enemy_max}",
            div,
        ]
        if m.done_anim:
            res = f"[{T.POS}]VICTORY![/]" if m.won else f"[{T.NEG}]DEFEAT[/]"
            lines += [res, f"[dim]{(b.reward or '')[:24]}[/]", "", "[dim]SPACE  continue[/]"]
        else:
            hint = "↑↓ ENTER pick" if getattr(m, "phase", "") == "menu" else "SPACE  skip"
            lines += [f"[dim]{(m.hud_note or '')[:24]}[/]", "", f"[dim]{hint}[/]"]
        self.stats_w.update("\n".join(lines))

    def _status_eat(self):
        """DVPet feeding readout: the calorie (hunger) buffer plus the protein/mineral/
        vitamin macros, shown live while the eat animation plays."""
        from .pet import CALORIE_LIMIT, MAX_MACRO, GOOD_NUTRITION_MIN
        p, T = self.pet, theme
        self.stats_w.border_subtitle = _gen_subtitle(p)
        div = "[dim]" + chr(0x2500) * 26 + "[/]"   # no backslash inside an f-string (SyntaxError on py3.10/3.11)
        def mbar(v, col):
            return bar(min(100, v * 100 // MAX_MACRO), 11, col)
        well = (p.nutr_protein >= GOOD_NUTRITION_MIN and p.nutr_mineral >= GOOD_NUTRITION_MIN
                and p.nutr_vitamin >= GOOD_NUTRITION_MIN)
        lines = [
            f"[b]{p.name[:14]}[/] [dim]\u00b7 feeding[/]", div,
            f"Calorie  {hearts(p.hunger)}",
            f"Fuel     {bar(p.calories * 100 // CALORIE_LIMIT, 12, T.COIN)}",
            div,
            f"Protein  {mbar(p.nutr_protein, T.POS)}",
            f"Mineral  {mbar(p.nutr_mineral, T.ENERGY)}",
            f"Vitamin  {mbar(p.nutr_vitamin, T.MOOD)}",
            div,
            f"Weight {p.weight}g",
            (f"[{T.POS}]well nourished[/]" if well else "[dim]a varied diet helps[/]"),
        ]
        self.stats_w.update("\n".join(lines))

    def _status_dna(self):
        p, m, T = self.pet, self.mode, theme
        self.stats_w.border_subtitle = _gen_subtitle(p)
        div = f"[dim]{'─' * 26}[/]"
        f = m.field
        same = f == p.field
        own, chg = p.dna_owned.get(f, 0), p.dna_applied.get(f, 0)
        cost = "spirit -3/ea  mood+" if same else "spirit -6/ea  mood-  ill?"
        from . import data, evolution
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
            f"[b]{p.name[:14]}[/] [dim]· DNA · {screen}[/]", div,
            f"Bits     [{T.COIN}]{p.bits}[/]",
            f"Field    {data.pretty_field(f)}" + ("  [dim](own)[/]" if same else ""),
            f"Banked   {own}     Charged {chg}",
            f"Share    {p.dna_percent(f)}%    [dim]x{m.amount}[/]",
            f"Unlocks  [b]{unlocked}[/]/{len(dna_t)} form(s)",
            div,
            f"[dim]{cost}[/]",
            *last_rows,
            "[dim]own Field * charges cheap[/]",
            "[dim]ESC steps back out[/]",
        ]
        self.stats_w.update("\n".join(lines))

    def _status_habitat(self):
        """The browsed habitat's dossier: the LCD shows the SCENE, this card
        carries the words (habitat audit 2026-07-04)."""
        p, m, T = self.pet, self.mode, theme
        self.stats_w.border_subtitle = _gen_subtitle(p)
        div = f"[dim]{'─' * 26}[/]"
        h = m.rows[m.cursor]
        msg = m.msg or ""
        cl = m.climate(h)
        if "  Wi " in cl:                     # split the ranges: no ° clips
            su, wi = cl.split("  Wi ")
            climate_rows = [f"Summer   {su[3:]}", f"Winter   {wi}"]
        else:
            climate_rows = [f"Climate  {cl[:17]}"]
        lines = [f"[b]{h['name'][:20]}[/]", div,
                 f"Status   {m._tag(h)}",
                 f"Fit      {m._aff_word(h)}",
                 *climate_rows,
                 f"Bits     [{T.COIN}]{p.bits}b[/]", div,
                 msg[:26], msg[26:52], "",
                 "[dim]try the view before[/]", "[dim]you pay for it[/]"]
        self.stats_w.update("\n".join(lines))

    def _status_town(self, m):
        """The town's numbers + message: the lobby is a bare arena now, so the
        card carries what the in-LCD header/note used to (box-clip audit)."""
        p, T = self.pet, theme
        self.stats_w.border_subtitle = _gen_subtitle(p)
        div = f"[dim]{'─' * 26}[/]"
        if m.sub is not None:                              # a cup bout in town
            e = m.sub.battle.enemy
            lines = [f"[b]{p.name[:14]}[/] [dim]· town cup[/]", div,
                     f"vs [b]{e['name'][:14]}[/]",
                     f"HP you {m.sub.hud_php}  foe {m.sub.hud_fhp}", div,
                     f"[dim]{(m.sub.hud_note or '')[:24]}[/]"]
        else:
            msg = m.msg or ""
            lines = [f"[b]TOWN {m.town['id']}[/] [dim]· {p.season}[/]", div,
                     f"Bits     [{T.COIN}]{p.bits}b[/]",
                     f"Bag      {sum(p.inventory.values())}",
                     div, msg[:26], msg[26:52]]
        self.stats_w.update("\n".join(lines))

    def _status_adventure(self):
        p, a, T = self.pet, self.mode.adv, theme
        from . import townscreen
        if isinstance(self.mode.sub, townscreen.TownPanel):
            return self._status_town(self.mode.sub)        # visiting: the town card
        self.stats_w.border_subtitle = _gen_subtitle(p)
        div = f"[dim]{'─' * 26}[/]"
        lives = "♥" * a.lives + "[dim]·[/]" * (3 - a.lives)
        power = f"[{T.POS}]●{p.vaccine}[/] [{T.ENERGY}]■{p.data_power}[/] [{T.MOOD}]▲{p.virus}[/]"
        # mid-encounter battle ONLY -- a road-side care panel (feed/bag,
        # road-keys 2026-07-07) keeps the travelling card underneath
        if self.mode.sub is not None and hasattr(self.mode.sub, "battle"):
            e = self.mode.sub.battle.enemy
            # boss-ness from the panel's own pending flag (bug report
            # 2026-07-13: the gate fight read as a random encounter -- the
            # enemy record never carries a "boss" key)
            was_boss = bool(getattr(self.mode, "_pending", None)
                            and self.mode._pending[0])
            tag = f" [{T.NEG}]BOSS[/]" if was_boss else ""
            foot = (["[dim]the zone boss guards[/]",
                     "[dim]the gate — end it![/]"] if was_boss else
                    ["[dim]a wild foe blocks[/]",
                     "[dim]the path — fight![/]"])
            lines = [
                f"[b]{p.name[:14]}[/] [dim]· battle[/]",
                div,
                f"vs [b]{e['name'][:14]}[/]{tag}",
                f"Lives    {lives}",
                div,
                f"Effort   {hearts(p.strength)}",
                f"Energy   {bar(p.energy_pct(), 11, T.ENERGY)}",
                f"Power    {power}",
                div,
            ] + foot
        else:                                               # travelling
            # the zone ribbon (legibility arc 2026-07-07): REAL geography on
            # the journey card -- towns.csv gates, uncleared enemies.csv
            # bosses, the pet's live step (adventure.ribbon)
            road = "".join(f"[b]{c}[/]" if c == "◆"
                           else f"[{T.COIN}]T[/]" if c == "T"
                           else f"[{T.NEG}]B[/]" if c == "B"
                           else "[dim]·[/]" for c in a.ribbon())
            from . import world
            _mn = a.maps[a.mi]["map"]
            from .arena import _sky_icon
            sky, skycol = _sky_icon(p)
            lines = [
                f"[b]{p.name[:14]}[/] [dim]· away[/]",
                div,
                f"[b]{world.region_name(_mn)[:24]}[/]",
                f"{world.zone_name(_mn, a.zone['zone'])[:20]} [dim]{a.pct}%[/]",
                f"Lives    {lives}",
                f"Road     {road}",
                f"Bag      {sum(p.inventory.values())}   [{T.COIN}]{p.bits}b[/]",
                div,
                f"Hunger   {hearts(p.hunger)}",
                f"Energy   {bar(p.energy_pct(), 11, T.ENERGY)}",
                f"Power    {power}",
                f"[{skycol}]{sky}[/] [dim]{p.weather} {_temp_str(p)}[/]",
                div,
                _status_line(p.status_word(), _care_deco(p)),
            ]
        self.stats_w.update("\n".join(lines))

    def on_frame(self):                        # single DVPet interval clock (10 Hz, 0.1s): main view AND sub-screens
        menu.TICK += 1                         # the shared note marquee clock: no screen clips a message
        self._hud_marquee()                    # scroll any over-long HUD message (independent of the LCD)
        self._drain_pms()                      # ✉ alerts ride the message box (presence 2026-07-05)
        if self.mode is not None:
            if hasattr(self.mode, "anim"):
                self.mode.anim()
                snd = getattr(self.mode, "sfx", None)   # drain anim-driven sfx (battle hits, lobby) — on_key only covers keypress
                if snd:
                    self.beep(snd, bell=False)
                    self.mode.sfx = None
                self.screen_w.update(self._center(self.mode.text()))
                self._mode_strip()
                painter = self._status_painter()
                if painter is not None:
                    painter()
                ac = getattr(self.mode, "auto_close", None)
                if ac is not None:
                    # a panel finished its own exit beat (the adventure
                    # homecoming fade) and asks to close from anim()
                    self.mode.auto_close = None
                    self._close_mode(ac[1])
            return
        sc = self.screen_w
        if sc.fx:
            sc.advance_fx()
            sc.paint(self.pet)
            if sc.fx:
                # beat-scripted fx sounds: eat's per-bite map + the generic snds map
                # (refuse head-shakes, the evolve burst, the dnaWash entry, ...)
                snd = (sc.fx.get("bite_snds", {}).get(sc.fx["step"])
                       or sc.fx.get("snds", {}).get(sc.fx["step"]))
                if snd:
                    self.beep(snd, bell=False)
                if sc.fx["kind"] == "eat":     # live DVPet feeding readout (calorie + P/M/V)
                    self._status_eat()
                elif (sc.fx["kind"] == "play" and sc.fx["step"] >= PLAY_LEAD
                        and (sc.fx["step"] - PLAY_LEAD) % PLAY_HOP == 0):
                    self.beep("happy", bell=False)   # DVPet jumping(): a chirp at each hop's launch
            elif getattr(self, "_pending_evolve", None) is not None and self.screen_w.fx is None:
                old_num, self._pending_evolve = self._pending_evolve, None
                self.screen_w.start_fx("evolve", old_num=old_num)
            elif self._dying_fx:               # dying beat finished: saved, or the memorial
                self._dying_fx = False
                hits = getattr(self, "_revive_hits", 0)
                self._revive_hits = 0
                from .pet import HITS_TO_SAVE
                if hits > HITS_TO_SAVE * (self.pet.saved_from_death + 1):
                    old_num = self.pet.save_from_death()
                    if old_num is not None:            # the dark rebirth
                        self.flash(f"[b]{self.pet.name}![/] It came back... changed.")
                        self.screen_w.start_fx("evolve", old_num=old_num)
                    else:
                        self.flash(f"[b]{self.pet.name}[/] clings to life!")
                        self.screen_w.start_fx("cheer")
                    persistence.save(self.pet)
                else:
                    # UnlockInheritance (onDie with _bonus > 0): the departed CAN
                    # etch its Digimemory -- canon's DigiMemory_Validation is a
                    # real choice (declining keeps the bonus for the heir), so
                    # the panel asks; the etch is the walk-out default.  A held
                    # UNUSED payload is device-lifetime (canon item 32 survives
                    # resetToEgg): back to the bank first (digimemory audit
                    # 2026-07-06), where the only-one prompt covers it.
                    if self.pet.digimemory:
                        persistence.bank_digimemory(dict(self.pet.digimemory))
                        self.pet.digimemory = {}
                    b0 = self.pet.evol_bonus
                    new_mem = self.pet.make_digimemory()
                    grade_spent = self.pet.final_care_grade()   # the etch path's seed
                    self.pet.evol_bonus = b0
                    grade_kept = self.pet.final_care_grade()    # the decline path's seed
                    self.pet.evol_bonus = 0                     # the life is spent either way
                    old_mem = persistence.peek_digimemory()
                    banked_new = False
                    if new_mem and not old_mem:
                        persistence.bank_digimemory(new_mem)    # default: etched
                        banked_new = True
                    persistence.bank_bonus_seed(grade_spent)    # default seed; B re-banks
                    persistence.save(self.pet)
                    self._open_mode(deathscreen.DeathPanel(self.pet, hold=20, new_mem=new_mem,
                                                           old_mem=old_mem, grade_kept=grade_kept,
                                                           banked_new=banked_new), self._after_death)
            else:                              # any other fx just finished -> restore the HUD
                self.repaint()
        else:
            if self.pet.hatching:
                ht0 = getattr(self.pet, "_hatch_t", 3.0)
                done = self.pet.advance_hatch(0.1)
                # the hatch chirp marks the WOBBLE ACCELERATING (device-exact,
                # GML 2026-07-14: the chirp lands as the egg's alarm quickens),
                # i.e. interval 10 of the 3.0s rock -- was DVPet's t0.6 beat
                if ht0 > 2.0 >= getattr(self.pet, "_hatch_t", 0.0):
                    self.beep("hatch")
                if done:
                    p = self.pet
                    self.flash(f"[b]{p.name}[/] hatched!")
            # DVPet Weather.precipitate: HeavyRain rolls thunder (nextInt(500)==0
            # per frame); the FLASH + the startled idle keep playing, but the
            # crack SFX is retired (Joel 2026-07-04: weather stays visual-only)
            p = self.pet
            if (p.weather == "HeavyRain" and not p.dead and p.stage != "Egg"
                    and getattr(sc, "thunder_i", 0) <= 0 and random.randint(0, 499) == 0):
                sc.thunder_i = 14
                if p.anim in ("idle", "walk") and not p.asleep:
                    # surprising() -- disposition-keyed (startle audit
                    # 2026-07-06): the sour pet barely flinches, the SUNNY
                    # one jumps out of its skin (canon's inversion)
                    p._set_anim({-1: "startle_sour", 1: "startle_sunny"}
                                .get(p.disposition, "startle"), 1.4)
            # DVPet poopDance: a special-idle roll while the gauge is full --
            # tuipet fires the poop the moment the gauge fills, so the nervous
            # dance rolls while the need APPROACHES (>=80% of the interval)
            # canon rolls ONCE and picks UNIFORMLY among the eligible tells
            # (yawning/poopdance audit 2026-07-06; the old elif hard-favoured
            # the dance whenever both were due)
            if (not p.dead and p.stage != "Egg" and not p.asleep
                    and p.anim in ("idle", "walk")):
                specials = []
                if getattr(p, "_poop_t", 0) >= 0.8 * p._poop_interval:
                    specials.append("poopdance")
                if p.near_bedtime():
                    specials.append("yawn")      # the full yawning() stretch fx
                if specials and random.randrange(40) == 0:
                    sc.start_fx(random.choice(specials))
            sc.advance(self.pet)
            sc.paint(self.pet)

    def on_tick(self):
        if self.mode is not None:
            # a sub-screen is open -> pause the life-sim (the canon menu
            # freeze) -- EXCEPT the lobby's chat contexts (Joel 2026-07-13:
            # "make the lobby tick, alarm and all") and the OPEN ROAD (Joel
            # 2026-07-13 again: "make adventures live-tick the sim" -- a long
            # expedition carries real hunger/sleep/sickness risk).  Sessions
            # (battle/jogress), login, teleports and every road-side sub
            # (town, feed, bag) keep the freeze: a pet must not starve or die
            # mid-volley or mid-menu.
            m = self.mode
            live = ((isinstance(m, lobbyscreen.LobbyPanel)
                     and m.phase in ("lobby", "dm"))
                    or (isinstance(m, adventurescreen.AdventurePanel)
                        and m.sub is None
                        and getattr(m, "_trans", None) is None))
            if not live:
                return
            was_dead = self.pet.dead
            poop0 = self.pet.poop
            self.pet.fx_hold = True     # evolution waits for the main view --
            #                             its strobe belongs to the home screen
            self.pet.tick(1.0)
            p = self.pet
            if p.dead and not was_dead:
                # death can't wait for ESC: leave the room, play the memorial
                if getattr(p, "away", False):
                    p.go_home_habitat()       # the road ends here: bring it home
                    p.away = False
                self._close_mode(None)
                self.beep("death")
                self.flash("")
                self.screen_w.start_fx("dying")
                self._dying_fx = True
                self._revive_hits = 0
                return
            if p.poop > poop0:          # the pile still lands audibly off-screen
                sz = (p.poop_sizes[-1] if getattr(p, "poop_sizes", None) else 2)
                self.beep("smallPoop" if sz == 1 else ("largePoop" if sz > 2 else "poop"),
                          bell=False)
            # the care alarm, canon nag cadence (onset ring + every ~90s);
            # its on-screen half rides the lobby strip (LobbyPanel._care_cue)
            needs = p.needs_attention()
            if needs and not self._needs:
                self.beep("alarm")
                self._nag_t = 0.0
            elif needs:
                self._nag_t = getattr(self, "_nag_t", 0.0) + 1.0
                if self._nag_t >= 90:
                    self._nag_t = 0.0
                    self.beep("alarm")
            self._needs = needs
            return
        prev = (self.pet.num, self.pet.stage)
        was_dead = self.pet.dead
        poop0 = self.pet.poop
        # an evolution must not swap the sprite UNDER a playing animation (the
        # clean-fx incident 2026-07-04: the pet transformed mid-sweep and the
        # evolve strobe played on the already-evolved form) -- hold the check
        # until the screen is quiet; the counters keep and it fires next tick
        self.pet.fx_hold = self.screen_w.fx is not None
        self.pet.tick(1.0)
        p = self.pet
        if p.dead and not was_dead:
            self.beep("death")            # death.wav, like DVPet's dying() sound
            self.flash("")
            self.screen_w.start_fx("dying")   # exhausted pose beat, then the memorial
            self._dying_fx = True
            self._revive_hits = 0
        elif (p.num, p.stage) != prev:
            if prev[1] == "Egg":
                self.beep("hatch")
                star = ("  [b]★ a NEW species for the album![/]"
                        if not persistence.album_has(p.num) else "")
                self.flash(f"[b]{p.name}[/] hatched!{star}")
                # hatch has NO evolve dither -- the egg already shook; the Fresh just appears
            else:
                # _evolve sounds INSIDE the strobe (fx snds beat 5), like DVPet evolveAnim.
                # design call (polish 2026-07): an evolution landing mid-fx WAITS for
                # the current animation instead of truncating it (death still overrides)
                self.flash(self._evolve_msg(prev[0]))
                if self.screen_w.fx is None:
                    self.screen_w.start_fx("evolve", old_num=prev[0])
                else:
                    self._pending_evolve = prev[0]
        elif getattr(p, "_toilet_event", None):
            tev = p._toilet_event
            p._toilet_event = None
            if self.screen_w.fx is None:          # the self-visit plays poopToilet
                self.screen_w.start_fx("toilet", icon=tev)
            else:
                self.beep("poop", bell=False)
        elif p.poop > poop0:
            # DVPet playPoopSound keys the byte poop() RETURNS -- the SIZE of the
            # new pile (f==1 small, f>2 large, else normal) -- not the pile count
            # (poop-anim audit 2026-07-05: a small fourth pile barked largePoop)
            sz = (p.poop_sizes[-1] if getattr(p, "poop_sizes", None) else 2)
            poop_snd = "smallPoop" if sz == 1 else ("largePoop" if sz > 2 else "poop")
            if self.screen_w.fx is None:
                # DVPet poop(): squat/sway then the pile lands at t18 with its sound
                self.screen_w.start_fx("poop", poop=poop0)
                self.screen_w.fx["snds"] = {18: poop_snd}
            else:
                self.beep(poop_snd, bell=False)
        # AI Assistant rounds (checkAutoCare): play the visit, flash the quit notes
        ev = getattr(p, "assist_event", None)
        if ev and self.screen_w.fx is None:
            p.assist_event = None
            act, piles, sizes = ev
            self.screen_w.start_fx("assist", pet=p, poop=piles,
                                   icon="f:44" if act == "feed" else ("f:43" if act == "strength" else None))
            self.screen_w.fx["act"] = act
            self.screen_w.fx["sizes"] = sizes
            self.screen_w.fx["helper"] = p.assistant_num
            if act in ("feed", "strength"):
                # assistantFeed: the drop-off round is short; the REAL eat anim
                # (with its own bite sounds / pace / grimace) chains after
                self.screen_w.fx["steps"] = 12
                self.screen_w.fx["chain_eat"] = self.screen_w.fx["icon"]
                self.screen_w.fx["pet_ref"] = p
        note = getattr(p, "assist_note", "")
        if note:
            self.flash(note)
            p.assist_note = ""
        # a lifetime-win gate crossed mid-battle: announce it back home
        note = getattr(p, "egg_unlock_note", "")
        if note:
            self.flash(note)
            # a whole new raisable species earned: the champion fanfare, not
            # the same chirp as picking up an Oats (sweep 2026-07-14)
            self.beep("champion", bell=False)
            p.egg_unlock_note = ""
        # birthday (setTimeToAge age-up): announce the day's verdict
        if p.birthday_note:
            self.flash(p.birthday_note)
            self.beep("reward" if "Cupcake" in p.birthday_note or "Cookie" in p.birthday_note else "lose", bell=False)
            p.birthday_note = ""
        # tournament alarm (TournamentAlert): the alarmed cup's hour arrived --
        # onset ring, then the same attention bounce as the gift call
        if p.tourney_alert and not getattr(self, "_cup_alert_seen", False):
            self.beep("alarm")
        self._cup_alert_seen = p.tourney_alert
        if p.tourney_alert and p.anim == "idle" and self.screen_w.fx is None:
            p._set_anim("happy", 1.2)
        # gift call (DVPet GiftCall): onset chime, then the attention bounce
        # (poses 5/7, like DVPet attention(5,7)) until the present is claimed
        if p.gift and not getattr(self, "_gift_seen", False):
            self.beep("reward", bell=False)
        self._gift_seen = bool(p.gift)
        if p.gift and p.anim == "idle" and self.screen_w.fx is None:
            p._set_anim("happy", 1.2)
        # care-need call (classic V-pet nag): alert on onset, then every ~90s
        needs = p.needs_attention()
        if needs and not self._needs:
            self.beep("alarm")
            self._nag_t = 0.0
        elif needs:
            self._nag_t = getattr(self, "_nag_t", 0.0) + 1.0
            if self._nag_t >= 90:
                self._nag_t = 0.0
                self.beep("alarm")
        self._needs = needs
        # the alarm's on-screen half: announce the active care need in the HUD box,
        # yielding to a fresh action flash and clearing once the need is met
        if self._flash_t > 0:
            self._flash_t -= 1
            self._showing_update = False
        elif needs:
            self._hud(self._need_message(p))
            self._showing_need = True
            self._showing_update = False
        elif p.tourney_alert:
            self._hud("ALERT — Tournament open! [b]U[/] to enter")
            self._showing_need = True           # reuse the clear-on-resolve flag
            self._showing_update = False
        elif p.gift:
            self._hud(f"[b]{p.name}[/] has a present for you! ENTER to accept")
            self._showing_need = True           # reuse the clear-on-resolve flag
            self._showing_update = False
        elif self._showing_need:
            self._hud("")
            self._showing_need = False
        elif self._update_msg and not self._showing_update:
            self._hud(self._update_msg)     # gentle update nudge when idle (set once so the marquee can scroll)
            self._showing_update = True
        if self.screen_w.fx is None:   # during a care fx on_frame owns the paint; repainting here flashes the status box
            self.repaint()

    FLASH_HOLD = 4                  # seconds an action result holds before the care-need shows

    def _hud(self, markup):
        """Single entry point for the message box.  Any message wider than the box
        is marquee-scrolled (see _hud_marquee) so it is never clipped; messages that
        fit render as-is with their Rich markup.  Re-sending the SAME text is a
        no-op: on_tick re-asserts persistent messages every second, and resetting
        the hold each time froze the marquee on its first window (audit 2026-07)."""
        if markup == getattr(self, "_hud_text", None):
            return
        self._hud_text = markup
        if len(_hud_plain(markup)) <= HUD_W:
            self._hud_scroll = None
            self.msg_w.update(markup)
        else:
            self._hud_scroll = _hud_plain(markup)   # scroll plain text (overflow msgs carry no markup)
            self._hud_off = 0
            self._hud_hold = HUD_HOLD
            self._hud_tick = 0
            self.msg_w.update(_hud_esc(self._hud_scroll[:HUD_W]))

    def _hud_marquee(self):
        """Advance the message marquee one step.  Called from the 10 Hz frame clock;
        a no-op unless the current message overflows the box."""
        if self._hud_scroll is None:
            return
        self._hud_tick = (self._hud_tick + 1) % HUD_STEP
        if self._hud_tick:
            return                                  # throttle: scroll once per HUD_STEP frames
        if self._hud_hold > 0:
            self._hud_hold -= 1
            return                                  # pause on the head (and at each wrap)
        loop = self._hud_scroll + HUD_GAP
        self.msg_w.update(_hud_esc((loop + loop)[self._hud_off:self._hud_off + HUD_W]))
        self._hud_off += 1
        if self._hud_off >= len(loop):
            self._hud_off = 0
            self._hud_hold = HUD_HOLD               # hold again when it loops back to the head

    def flash(self, text):
        self._hud(text)
        self._flash_t = self.FLASH_HOLD

    def _evolve_msg(self, old_num):
        """'Koromon evolved into Agumon (Rookie)!' -- old name -> NEW NAME, stage
        in parentheses.  The old form ('X! evolved to InTraining!') read as if
        the stage were the pet's NAME (Joel, 2026-07-04: 'the babys name is
        intraining????'), because the species name never appeared."""
        _, by = data.load_sprites()
        old = by.get(old_num, {}).get("name") or "It"
        msg = f"[b]{old}[/] evolved into [b]{self.pet.name}[/] ({self.pet.stage})!"
        # genuine FIRSTS get named (sweep 2026-07-14): a first-ever Mega and a
        # first-ever species read no bigger than a baby's first bump before.
        # Both checks race nothing: the progress stamps trail on autosave and
        # album_add fires inside save(), so at THIS tick both still say "new".
        extra = []
        if self.pet.stage in data.STAGE_ORDER:
            if data.STAGE_ORDER.index(self.pet.stage) > \
                    persistence.get_progress().get("max_stage", 0):
                extra.append(f"your first {self.pet.stage} ever")
        if not persistence.album_has(self.pet.num):
            extra.append("a NEW species for the album")
        if extra:
            msg += f"  [b]★ {' · '.join(extra)}![/]"
        return msg

    def _need_message(self, p):
        """HUD announcement for the pet's most urgent unmet care need (or '')."""
        name = p.name or "Your pet"
        if p.asleep and p.lights:               # lightsCall: the one asleep call
            msg = f"{name} is trying to sleep — lights off! ([b]S[/])"
        elif p.sick:          msg = f"{name} is sick!"
        elif p.hunger == 0:   msg = f"{name} is hungry!"
        elif p.strength == 0: msg = f"{name}'s effort gauge is empty — train it!"
        elif p.poop >= 3:     msg = f"{name} needs cleaning!"
        elif p.energy <= 0:   msg = f"{name} is exhausted!"
        elif p.is_frail():
            left = max(0, 5 - p.care_mistakes)
            msg = (f"{name} is getting frail — "
                   + (f"{left} more slip{'s' if left != 1 else ''} could be fatal!"
                      if left else "handle with perfect care!"))
        elif p.scold_flag:    msg = f"{name} is misbehaving!"
        elif p.discipline_call: msg = f"{name} is throwing a tantrum — scold it!"
        else:                 return ""
        return f"[{theme.NEG}]\u26a0 {msg}[/]"

    def _do(self, result):
        self.flash(result)
        self.repaint()

    def action_feed(self):
        if self.screen_w.fx is not None:        # let the current care animation finish before acting again
            return
        reason = self.pet.can_feed()            # egg/asleep/dead -> flash the reason, no menu
        if reason:
            self._do(reason); return
        self._open_mode(feedscreen.FeedPanel(self.pet), self._after_feed)

    def _after_feed(self, result):
        # result: ("fed"|"full"|"refused", food, msg); None on cancel.  A refusal
        # plays no food fx -- the refuse pose (State.Refusing) is already on the pet
        if not result:
            self.repaint(); return
        outcome, food, msg = result
        icon = food.get("key", "f:0")               # the food's REAL icon rides the eat fx
        # eat(): the wolf-down modifier is decided BEFORE the meal (a starving
        # pet that just ate has hunger>0 -- reading it here was always False)
        starving = getattr(self.pet, "_last_meal_starving", False)
        if outcome == "fed" and self.pet.anim == "eat":
            self.screen_w.start_fx("eat", icon, pet=self.pet, starving=starving)   # SFX per-bite in the fx loop
        elif outcome == "full":
            self.screen_w.start_fx("spit", icon)  # _refuse fires on each head-shake (fx snds)
        self._do(msg)
    def action_train(self):
        reason = self.pet.can_train()
        if reason:
            self._do(reason); return
        self._open_mode(training.TrainingPanel(self.pet), self._after_train)

    def _after_train(self, msg):
        if msg:
            self.flash(msg)
        # DVPet onExerciseFinish: success -> setPraise(true) -> the cheer(true) fx;
        # anything less -> State.Jeering -> jeer(true, _angry).  apply_training left
        # the verdict in pet.anim (happy/sad; the sim is paused while the drill is
        # open, so it's still fresh here).
        if self.pet.anim == "happy":
            self.screen_w.start_fx("cheer")
        elif self.pet.anim == "sad":
            self.screen_w.start_fx("jeer")
        elif self.pet.anim == "refuse":
            # canon canExercise: _refused -> State.Refusing -- the head-shake plays
            # back on the LCD after onPreTrain dumps the menu (spit == refuse(); no icon)
            self.screen_w.start_fx("spit")
        self.repaint()

    # (the home battle + jogress actions were retired 2026-07-07 -- lobby-only
    # now; adventure/cup/town keep their own embedded BattlePanels and the
    # lobby keeps JogressPanel as its fusion-scene shim)

    def action_praise(self):
        if self.screen_w.fx is not None:        # let the current care animation finish before acting again
            return
        msg = self.pet.praise()
        if self.pet.anim == "happy":                # the praise lands -> DVPet cheer()
            self.screen_w.start_fx("cheer")         # (its _happy sound is fx-scripted)
        elif self.pet.anim == "surprise":           # mis-praised a misbehaver ->
            self.screen_w.start_fx("cheer", good=False)   # Bad_Praise: cheer(false)
        self._do(msg)

    def action_scold(self):
        if self.screen_w.fx is not None:        # let the current care animation finish before acting again
            return
        msg = self.pet.scold()
        if self.pet.anim == "angry":                # the scold lands -> DVPet jeer()
            self.screen_w.start_fx("jeer")          # (its _angry sound is fx-scripted)
        elif self.pet.anim == "sad":                # scolded an innocent -> Bad_Scold:
            self.screen_w.start_fx("jeer", good=False)   # the sad slump
        self._do(msg)

    def action_tournament(self):
        err = tournament.can_enter(self.pet)   # single source of entry gating (young/asleep/no-cup)
        if err:
            self._do(err); return
        self.pet.tourney_alert = False         # answering the call silences it
        self._open_mode(tournamentscreen.TournamentPanel(self.pet), self._after_cup)

    def _after_cup(self, msg):
        verdict = None
        if isinstance(msg, tuple):           # (last, champion) from a played bracket
            msg, verdict = msg
        if msg:
            self.flash(msg)
        # the post-cup emotional beat rides the HOUSE screen (anim hardening
        # 2026-07-14: every reference celebrates a win / sulks a loss back
        # home for a few seconds; tuipet's losing() fx sat built but unwired)
        if verdict is not None and self.screen_w.fx is None and not self.pet.dead:
            self.screen_w.start_fx("cheer" if verdict else "losing")
        self.repaint()

    def action_dna(self):
        reason = self.pet.can_charge_dna()
        if reason:
            self._do(reason); return
        self._open_mode(dnascreen.DNAPanel(self.pet), self._after_dna)

    def _after_dna(self, result=None):
        self.autosave()
        if isinstance(result, tuple) and result and result[0] == "charged":
            _, field, amount = result          # DVPet applyDNA -> DNA_Feeding -> main view
            self.screen_w.start_fx("dna_charge", icon=field, pet=self.pet)
            self.beep("compatible", bell=False)   # the DNA charge/absorb beep (no dedicated dna rip)
            self.flash("%s absorbed %d %s DNA" % (self.pet.name, amount, data.pretty_field(field)))
        else:
            self.repaint()

    def action_shop(self):
        self._open_mode(shopscreen.ShopPanel(self.pet), self._after_shop)
    def action_inventory(self):
        self._open_mode(shopscreen.ShopPanel(self.pet, start_mode="bag"), self._after_shop)

    def action_habitat(self):
        self._open_mode(habitatscreen.HabitatPanel(self.pet), self._after_habitat)

    def action_assist(self):
        self._open_mode(assistscreen.AssistPanel(self.pet), lambda _=None: self.repaint())

    def action_eggguide(self):
        # the digitama unlock book -- read-only, safe at any stage
        self._open_mode(eggguidescreen.EggGuidePanel(self.pet), lambda _=None: self.repaint())

    def action_digicore(self):
        self._open_mode(digicorescreen.DigiCorePanel(self.pet), self._after_digicore)

    def _after_digicore(self, msg):
        if isinstance(msg, tuple) and msg and msg[0] == "evolve":
            # modeChange -> State.Evolving: the same strobe as any evolution
            self.flash(f"[b]{msg[2] if len(msg) > 2 else 'MODE CHANGE!'}[/]")
            self.screen_w.start_fx("evolve", old_num=msg[1])
        self.repaint()

    def _after_habitat(self, msg):
        if msg:
            self.flash(msg)
        self.repaint()

    def _after_shop(self, msg):
        if isinstance(msg, tuple) and msg and msg[0] == "eat":
            self.screen_w.start_fx("eat", msg[1], pet=self.pet,
                                   starving=getattr(self.pet, "_last_meal_starving", False))
        elif isinstance(msg, tuple) and msg and msg[0] == "evolve":
            # _evolve sounds INSIDE the strobe (fx snds beat 5), like DVPet evolveAnim.
            # msg[2] = an ItemEvol's key: the Digimental's icon frames head the
            # strobe with canon itemEvolve's parade
            ik = msg[2] if len(msg) > 2 else None
            self.flash(self._evolve_msg(msg[1]))
            self.screen_w.start_fx("evolve", old_num=msg[1], icon=ik)
        elif isinstance(msg, tuple) and msg and msg[0] == "toilet":
            # a manual visit: poopToilet with the item on the floor
            self.screen_w.start_fx("toilet", icon=msg[1])
        elif isinstance(msg, tuple) and msg and msg[0] == "play":
            # the Trampoline (Jump): DVPet jumping() -- the pet hops over it
            self.screen_w.start_fx("play", icon=msg[1])
        elif isinstance(msg, tuple) and msg and msg[0] == "item_use":
            # every other AnimationType plays its own canon script (itemfx)
            self.screen_w.start_fx("item", icon=msg[1], script=msg[2])
        elif isinstance(msg, tuple) and msg and msg[0] == "inherit":
            mem = msg[1]
            self.flash(f"[b]{mem.get('name', '?')}[/]'s power lives on!  "
                       f"Va+{mem.get('vaccine', 0)} D+{mem.get('data', 0)} Vi+{mem.get('virus', 0)}")
            self.screen_w.start_fx("inherit", pet=self.pet)
            self.screen_w.fx["ancestor"] = mem.get("num", -1)
        elif isinstance(msg, tuple) and msg and msg[0] == "transport":
            self._open_mode(transportscreen.TransportPanel(self.pet, msg[1]), self._after_transport)
            return
        elif msg:
            self.flash(msg)
        self.repaint()

    def _after_transport(self, msg):
        if msg:
            self.flash(msg)
        self.autosave()
        self.repaint()

    def action_adventure(self):
        if self.pet.stage in ("Egg", "Fresh"):
            self._do("Too young to adventure."); return
        if self.pet.asleep:
            self._do("zzz… asleep"); return
        refused = self.pet.check_refused()          # canTravel: checkRefused ...
        self.pet.check_compliant()                  # ... ; checkCompliant
        if refused:
            self._do(f"{self.pet.name} refuses to go!"); return
        def _back(msg=None):
            if msg:
                self.flash(msg)          # the victory line lands over the house
            self.repaint()
        self._open_mode(adventurescreen.AdventurePanel(self.pet), _back)

    def action_gift(self):
        if self.mode is not None or self.screen_w.fx is not None or not self.pet.gift:
            return
        key = self.pet.gift
        msg = self.pet.claim_gift()
        if msg:
            self.screen_w.start_fx("gift", icon=key)   # gifting() amble, chains to cheer (giftEnd)
            self._do(msg)

    def action_play(self):
        if self.screen_w.fx is not None:        # let the current care animation finish before acting again
            return
        msg = self.pet.play()
        if self.pet.anim == "play":
            self.screen_w.start_fx("play")       # the DVPet jumping() hop; SFX fires per-hop in the fx loop
        self._do(msg)
    def action_clean(self):
        if self.screen_w.fx is not None:        # let the current care animation finish before acting again
            return
        poop = self.pet.poop
        sizes0 = list(self.pet.poop_sizes)      # clean() wipes them; the fx still shows the piles
        msg = self.pet.clean()
        if self.pet.anim == "wash":
            self.screen_w.start_fx("clean", poop=poop)
            self.screen_w.fx["sizes"] = sizes0
            self.beep("wash", bell=False)
        self._do(msg)
    def action_heal(self):
        if self.screen_w.fx is not None:        # let the current care animation finish before acting again
            return
        msg = self.pet.heal()
        if self.pet.anim == "heal":
            # DVPet bandage(): the treatment anim (item strip on the hurt pose),
            # which chains into cheer(true, _happy) at its beat 23.
            self.screen_w.start_fx("heal", icon="i:80")
        self._do(msg)
    def action_sleep(self):                                     # the "s" key is the LIGHTS toggle
        self.beep("confirm", bell=False)                        # a button blip on the lights on/off press
        self._do(self.pet.toggle_lights())
    def action_new(self):
        if not self.pet.dead:
            # a LIVE retire skips the death flow entirely: canon resetDigimon
            # runs careBonusOnReset dead or alive, and a live reset never
            # offers the etch -- the FULL adjusted bonus carries to the heir
            # (digimemory audit 2026-07-06; this seed used to be lost)
            persistence.bank_bonus_seed(self.pet.final_care_grade())
        persistence.snapshot_prev_gen(self.pet)   # previous-generation egg gates
        gen = self.pet.generation + 1
        self._open_mode(eggselectscreen.EggSelectPanel(self.pet),
                        lambda et: self._hatch_new(et, gen))

    def _hatch_new(self, egg_type, gen):
        if egg_type is None:                        # cancelled -> keep the current pet
            self._do("Kept your current partner.")
            return
        self.pet = Pet.new_egg(generation=gen, egg_type=egg_type)
        self._grant_digimemory(self.pet)
        persistence.save(self.pet)
        self._do(f"A new egg appeared! (generation {gen})")


def _lobby_uri():
    return os.environ.get("TUIPET_LOBBY_URL", "wss://ff3mmo.com/tuipet/")  # live lobby (TLS); override for local dev


MIN_COLS, MIN_ROWS = 77, 24     # the fixed layout: #left 44 + #stats 30 + chrome


def _preflight():
    """Fail loud and in plain words BEFORE the UI takes the terminal over
    (sweep 2026-07-14): damaged assets exit with the fix; a cramped window or
    a non-UTF-8 locale get a readable warning, then the game runs anyway --
    a clipped game beats a locked-out player."""
    try:
        data.load_sprites()
        data.load_orbs()
    except data.AssetsError as e:
        print(e)
        raise SystemExit(1)
    import shutil
    import sys
    import time as _t
    warn = []
    cols, rows = shutil.get_terminal_size()
    if cols < MIN_COLS or rows < MIN_ROWS:
        warn.append(f"⚠ tuipet lays out for {MIN_COLS}×{MIN_ROWS}; this terminal is "
                    f"{cols}×{rows} — expect clipping.\n  (Enlarge the window, shrink "
                    f"the font, or rotate the phone.)")
    enc = (getattr(sys.stdout, "encoding", "") or "").lower()
    if enc and "utf" not in enc:
        warn.append(f"⚠ tuipet draws with Unicode but this terminal reports '{enc}'.\n"
                    f"  If the art looks wrong:  export LANG=C.UTF-8")
    if warn:
        print("\n".join(warn))
        _t.sleep(2.5)


def main():
    _preflight()
    other = persistence.acquire_instance_lock()
    if other and not _os.environ.get("TUIPET_FORCE"):
        print(f"tuipet is already running (pid {other}) — two copies would fight "
              f"over one save.\nClose the other one first, or set TUIPET_FORCE=1 "
              f"to override.")
        raise SystemExit(1)
    # Cross-device: pull a newer cloud save down BEFORE the app loads the pet, so
    # the normal load path picks it up (no mid-session swapping). Fail-soft.
    if persistence.sync_enabled():
        try:
            name, pw = persistence.get_account()
            cloudsync.sync_down_at_startup(_lobby_uri(), name, pw)
        except Exception:
            pass
    app = TuiPetApp()
    try:
        app.run()
    finally:
        persistence.release_instance_lock()
    if getattr(app, "_crash_note", None):
        print(app._crash_note)          # after Textual restores the terminal
    elif persistence.save_failed:
        # never print "Saved" over a disk that refused (silent-failure law)
        print("⚠ tuipet couldn't save — set TUIPET_SAVE_DIR to a writable folder.")
    elif getattr(app, "pet", None) is not None:
        nm = getattr(app.pet, "name", "") or "your pet"
        print(f"Saved ✓ — {nm} will be waiting.")


if __name__ == "__main__":
    main()
