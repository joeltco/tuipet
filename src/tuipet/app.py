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
from rich.markup import escape as _esc
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Static

from . import data
from . import menu
from . import egg as egg_mod
from . import training
from . import battlescreen
from . import shopscreen
from . import backgroundscreen
from . import backgrounds as bgs_mod
from . import feedscreen
from . import eggselectscreen
from . import persistence
from . import net
from . import lobbyscreen
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
    hearts, bar, _FX, GRAVESTONE, POOP_W, POOP_PAD,
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
        f"[{k}]f[/] feed  [{k}]c[/] clean  [{k}]h[/] pill  [{k}]s[/] lights  [{k}]t[/] train\n"
        f"[{k}]l[/] lobby (battle·jogress)  [{k}]n[/] new egg  [{k}]o[/] shop  [{k}]i[/] bag\n"
        f"[{k}]e[/] scenes  [{k}]g[/] options  [{k}]b[/] bug  [{k}]?[/] help  [{k}]q[/] quit"
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
    if pet.call_on: deco.append(f"[{T.NEG}]+call![/]")
    if pet.poop: deco.append(f"[{T.COIN}]~poop x{pet.poop}[/]")
    if pet.evo_blocked: deco.append("[dim]+evo-lock[/]")
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
        cur, need = pet.evolution_progress()
        self.border_subtitle = _gen_subtitle(pet)
        rec = pet.species or {}
        lines = [
            f"[b]{(pet.name or rec.get('name', '?'))[:22]}[/]",
            f"[dim]{pet.stage}{(' · ' + pet.attribute) if pet.attribute else ''}[/]",
            div,
            f"Hunger  {hearts(pet.hunger)}",
            f"Effort  {hearts(pet.strength)}",
            f"Energy  {bar(pet.energy_pct() * 100, 12, T.ENERGY)} {pet.energy}",
            f"Weight  {pet.weight}g   [{T.COIN}]{pet.bits}b[/]",
            div,
            f"Train   {pet.trainings_cur_stage} [dim]this stage[/]",
            f"Battle  {pet.wins}W/{pet.battles}",
            f"Care    {pet.care_mistakes} [dim]mistakes[/]",
            f"Growth  {bar(cur * 100 // max(1, need), 12, T.LIFE)}",
            f"@{bgs_mod.name(pet.bg_current)[:16]} [dim]day {pet.age_days}[/]",
            _status_line(word, deco),
        ]
        self.update("\n".join(lines))

    def _paint_egg(self, pet):
        self.border_subtitle = _gen_subtitle(pet)
        div = f"[dim]{'─' * 26}[/]"
        lines = [
            f"[b]{egg_mod.egg_name(pet.egg_type)[:22]}[/] [dim]· egg[/]",
            div,
            "[dim]a new life is warming[/]",
            "",
            "Destined to hatch",
            f"  [b]{egg_mod.hatch_name(pet.egg_type)}[/]",
            div,
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
            f"Lived    {pet.age_days} day{'s' if pet.age_days != 1 else ''}",
            f"Reached  {pet.stage}",
            f"Cause    {getattr(pet, 'death_cause', '') or 'unknown'}",
            f"Attrib   {pet.attribute}",
            f"Record   {pet.wins}W / {pet.battles}",
            div,
            "[dim]a revive floppy can[/]",
            "[dim]bring it back — or[/]",
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
    WHATS_NEW = ("THE FEED MENU GOES ON THE LCD: choosing meat or pill is now "
                 "the canon icon picker — a little drumstick over a capsule "
                 "with a cursor arrow, drawn right on the screen like the "
                 "original, instead of a text list.")

    BINDINGS = [
        # battle + jogress are LOBBY-ONLY (Joel 2026-07-07)
        ("f", "feed", "Feed"), ("t", "train", "Train"),
        ("c", "clean", "Clean"), ("h", "heal", "Pill"),
        ("o", "shop", "Shop"),
        ("i", "inventory", "Bag"), ("e", "habitat", "Scenes"),
        ("n", "new", "New egg"),
        ("l", "lobby", "Lobby"),
        ("s", "sleep", "Lights"), ("g", "options", "Options"),
        ("b", "bug", "Bug"), ("question_mark", "help", "Help"), ("q", "quit", "Quit"),
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
        # The UNDER-CONSTRUCTION gate (Joel 2026-07-15) stands here instead,
        # for now: the game needs the PIN, the lobby stays open to everyone.
        if not persistence.load_settings().get("construction_ok"):
            self._open_mode(titlescreen.GatePanel(), self._after_gate)
            return
        self._post_title()

    def _after_gate(self, result):
        if result == "play":                    # right PIN: sticks per device
            s = persistence.load_settings()
            s["construction_ok"] = True
            persistence.save_settings(s)
            self._post_title()
        elif result == "lobby":                 # the open door past the lock
            name, pw = persistence.get_account()
            self._open_mode(lobbyscreen.LobbyPanel(self.pet, self._lobby_connect,
                            name=name, pw=pw),
                            self._after_gate_lobby)
        else:                                   # ESC: back out to the title
            self._open_mode(titlescreen.TitlePanel(), self._after_title)

    def _after_gate_lobby(self, result=None):
        # tear the connection down like any lobby exit, then land back on the
        # GATE -- never the home screen (that would walk around the lock)
        self._after_lobby(result)
        self._open_mode(titlescreen.GatePanel(), self._after_gate)

    def _post_title(self):
        if self._new_game:
            self._open_mode(eggselectscreen.EggSelectPanel(self.pet), self._after_egg_pick)
        else:
            self._hud(self._welcome)
            self.repaint()

    def _after_death(self, result):
        if result == "new":
            self.action_new()
        else:
            self.repaint()

    def _after_egg_pick(self, egg_type):
        if egg_type is None:                       # backed out -> return to the title
            self._open_mode(titlescreen.TitlePanel(), self._after_title)
            return
        self._new_game = False                     # the fresh start is settled
        self.pet = Pet.new_egg(egg_type=egg_type)
        self.flash("Take good care of your egg!  (? = help)")
        self.repaint()

    def autosave(self):
        # a fresh start is NOT settled until the carousel pick: self.pet is a
        # random placeholder egg through title->gate->carousel, and persisting
        # it made the next launch load a pre-picked egg and skip choose-your-egg
        # ("it auto-selected an egg for me"; round-3 audit 2026-07-16).  The
        # pick clears _new_game, and autosave resumes on the chosen egg.
        if self._new_game:
            return
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
            if event.key not in ("q", "g", "i"):   # the BAG stays reachable:
                #                                      a revive floppy raises the dead
                event.stop()
                event.prevent_default()
                self._open_mode(deathscreen.DeathPanel(self.pet), self._after_death)
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
            update_hint=lambda: getattr(self, "_update_msg", ""),
            updated_to=lambda: getattr(self, "_updated_to", None)),
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
            # browse screens keep live vitals on the right
            self.stats_w.paint(self.pet)

    def _status_painter(self):
        """The mode's live status-panel painter (one table for repaint AND
        on_frame -- the two hand-rolled dispatches drifted; audit 2026-07)."""
        table = ((training.TrainingPanel, self._status_training),
                 (battlescreen.BattlePanel, self._status_battle),
                 (feedscreen.FeedPanel, self._status_feed),
                 (backgroundscreen.BackgroundPanel, self._status_background))
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

    def _status_training(self):
        p, tp, T = self.pet, self.mode, theme
        self.stats_w.border_subtitle = _gen_subtitle(p)
        div = f"[dim]{'─' * 26}[/]"
        zone = tp.mega_hi - tp.mega_lo + 1
        if tp.phase == "bar":
            foot = ["[dim]stop the marker in[/]", "[dim]the zone[/]"]
        elif tp.phase == "done":
            foot = [(f"[{T.POS}]{tp.result}[/]" if tp.success
                     else f"[{T.NEG}]{tp.result}[/]"), ""]
        else:
            foot = ["[dim]...firing[/]", ""]
        lines = [f"[b]{p.name[:14]}[/] [dim]· train[/]", div,
                 f"Form     [b]{getattr(p, 'saved_hit_type', 'normal')}[/]",
                 f"Zone     {zone} wide [dim](care!)[/]",
                 f"Stage    {p.trainings_cur_stage} drills",
                 f"Lifetime {p.total_trainings}",
                 div,
                 f"Effort   {hearts(p.strength)}",
                 f"Energy   {bar(p.energy_pct() * 100, 11, T.ENERGY)}",
                 div] + foot
        self.stats_w.update("\n".join(lines))

    def _status_battle(self):
        p, m, T = self.pet, self.mode, theme
        e = m.enemy
        self.stats_w.border_subtitle = _gen_subtitle(p)
        div = f"[dim]{'─' * 26}[/]"
        php = getattr(m, "hud_php", 5)
        fhp = getattr(m, "hud_fhp", 5)
        pp = int(100 * php / 5)
        fp = int(100 * fhp / 5)
        tag = f" [{T.NEG}]BOSS[/]" if e.get("boss") else ""
        lines = [
            f"[b]{p.name[:14]}[/] [dim]· battle[/]", div,
            f"vs [b]{e['name'][:14]}[/]{tag}", "",
            f"You  {bar(pp, 11, T.POS)} {php}/5",
            f"Foe  {bar(fp, 11, T.NEG)} {fhp}/5",
            div,
        ]
        if m.done_anim:
            res = f"[{T.POS}]VICTORY![/]" if m.won else f"[{T.NEG}]DEFEAT[/]"
            reward = getattr(m.battle, "reward", "") if m.battle else ""
            lines += [res, f"[dim]{(reward or '')[:24]}[/]", "", "[dim]SPACE  continue[/]"]
        else:
            hint = ("SPACE lock the bar" if getattr(m, "phase", "") == "ready"
                    else "SPACE  skip")
            lines += [f"[dim]{(m.hud_note or '')[:24]}[/]", "", f"[dim]{hint}[/]"]
        self.stats_w.update("\n".join(lines))

    def _status_feed(self):
        """Feed-menu readout: the LCD carries the meat/pill icons, this card
        carries the words (canon splits picture from text, like the picker)."""
        p, m, T = self.pet, self.mode, theme
        self.stats_w.border_subtitle = _gen_subtitle(p)
        div = f"[dim]{'─' * 26}[/]"

        def opt(i, label, effect):
            mark = "▸" if m.cursor == i else " "
            style = "b" if m.cursor == i else "dim"
            return f"[{style}]{mark} {label:<5}[/] [dim]{effect}[/]"

        lines = [
            f"[b]{p.name[:14]}[/] [dim]· feed[/]", div,
            f"Hunger   {hearts(p.hunger)}",
            f"Effort   {hearts(p.strength)}",
            f"Energy   {bar(p.energy_pct() * 100, 11, T.ENERGY)}",
            div,
            opt(0, "Meat", "fills the belly"),
            opt(1, "Pill", "mends & fuels"),
        ]
        self.stats_w.update("\n".join(lines))

    def _status_eat(self):
        """Feeding readout: belly + weight, live while the eat anim plays."""
        p, T = self.pet, theme
        self.stats_w.border_subtitle = _gen_subtitle(p)
        div = f"[dim]{'─' * 26}[/]"
        lines = [
            f"[b]{p.name[:14]}[/] [dim]· feeding[/]", div,
            f"Hunger   {hearts(p.hunger)}",
            f"Effort   {hearts(p.strength)}",
            f"Energy   {bar(p.energy_pct() * 100, 11, T.ENERGY)}",
            div,
            f"Weight   {p.weight}g",
            "[dim]meat fills the belly;[/]",
            "[dim]the pill mends & fuels[/]",
        ]
        self.stats_w.update("\n".join(lines))

    def _status_background(self):
        """The browsed scene's dossier: the LCD shows the SCENE, this card
        carries the words (picker rebuild 2026-07-15)."""
        p, m, T = self.pet, self.mode, theme
        self.stats_w.border_subtitle = _gen_subtitle(p)
        div = f"[dim]{'─' * 26}[/]"
        key = m.rows[m.cursor]
        msg = m.msg or ""
        pr = bgs_mod.price(key)
        lines = [f"[b]{bgs_mod.name(key)[:20]}[/]", div,
                 f"Status   {m._tag(key)}",
                 f"Price    {'free' if pr == 0 else f'{pr}b'}",
                 f"Bits     [{T.COIN}]{p.bits}b[/]", div,
                 msg[:26], msg[26:52], "",
                 "[dim]try the view before[/]", "[dim]you pay for it[/]"]
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
            elif self._dying_fx:               # dying beat finished -> the memorial
                self._dying_fx = False
                persistence.save(self.pet)
                self._open_mode(deathscreen.DeathPanel(self.pet),
                                self._after_death)
            else:                              # any other fx just finished -> restore the HUD
                self.repaint()
        else:
            p = self.pet
            if p.stage == "Egg":
                was = p.hatching
                done = p.advance_hatch(0.1)
                if done and not was:
                    self.beep("hatch")
                if done and p.hatch_t >= 33:      # 3s of crack-wobble, then out
                    p._hatch_into_fresh()
                    star = ("  [b]★ a NEW species for the album![/]"
                            if not persistence.album_has(p.num) else "")
                    self.flash(f"[b]{p.name or data.record_for(p.num)['name']}[/] hatched!{star}")
            sc.advance(self.pet)
            sc.paint(self.pet)

    def on_tick(self):
        if self.mode is not None:
            # a sub-screen is open -> pause the life-sim (the canon menu
            # freeze) -- EXCEPT the lobby's chat contexts (Joel 2026-07-13:
            # "make the lobby tick, alarm and all").  Sessions (battle/
            # jogress), login and every menu keep the freeze: a pet must not
            # starve or die mid-volley or mid-menu.
            m = self.mode
            live = (isinstance(m, lobbyscreen.LobbyPanel)
                    and m.phase in ("lobby", "dm"))
            if not live:
                # a TRUE freeze: keep the pet's clock current so the frozen
                # menu minutes don't build a replay debt.  Pet.tick's drift
                # guard (>120s lag -> catch_up) otherwise replayed the frozen
                # time on the next live tick, charging calls the player could
                # not answer while in the menu (round-3 audit 2026-07-16).
                # _min_acc is left ALONE -- a partial minute in flight resumes
                # after the menu; only wall_time is pinned so no debt accrues.
                import time as _t
                if self.pet.stage != "Egg" and self.pet.num >= 0 and not self.pet.dead:
                    self.pet.wall_time = _t.time()
                return
            was_dead = self.pet.dead
            poop0 = self.pet.poop
            self.pet.tick(1.0)
            p = self.pet
            if p.dead and not was_dead:
                # death can't wait for ESC: leave the room, play the memorial
                if getattr(p, "away", False):
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
        name = _esc(p.name) or "Your pet"
        if p.asleep and p.lights:               # the one asleep call
            msg = f"{name} is trying to sleep — lights off! ([b]S[/])"
        elif p.sick:          msg = f"{name} is sick — a pill ([b]H[/]) cures it!"
        elif p.hunger == 0:   msg = f"{name} is hungry!"
        elif p.strength == 0: msg = f"{name}'s strength is empty — pill or fruit!"
        elif p.poop:          msg = f"{name} needs cleaning!"
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
        reason = training.can_train(self.pet)
        if reason:
            self._do(reason); return
        if self.pet.asleep:                     # dragging a sleeper to the bar
            self.pet.disturb_sleep()            # = the canon disturb mistake
            self.flash("It wakes up grumpy…")
        self._open_mode(training.TrainingPanel(self.pet), self._after_train)

    def _after_train(self, msg):
        if msg:
            self.flash(msg)
        self.repaint()

    # (the home battle + jogress actions were retired 2026-07-07 -- lobby-only
    # now; adventure/cup/town keep their own embedded BattlePanels and the
    # lobby keeps JogressPanel as its fusion-scene shim)

    def action_shop(self):
        self._open_mode(shopscreen.ShopPanel(self.pet), self._after_shop)
    def action_inventory(self):
        self._open_mode(shopscreen.ShopPanel(self.pet, start_mode="bag"), self._after_shop)

    def action_habitat(self):
        self._open_mode(backgroundscreen.BackgroundPanel(self.pet), self._after_habitat)

    def _after_habitat(self, msg):
        if msg:
            self.flash(msg)
        self.repaint()

    def _after_shop(self, msg):
        if isinstance(msg, tuple) and msg and msg[0] == "eat":
            self.screen_w.start_fx("eat", msg[1], pet=self.pet)
        elif isinstance(msg, tuple) and msg and msg[0] == "evolve":
            # an item evolution (crest egg / X-antibody): the same strobe
            self.flash(self._evolve_msg(msg[1]))
            self.screen_w.start_fx("evolve", old_num=msg[1])
        elif msg:
            self.flash(msg)
        self.repaint()

    def action_clean(self):
        if self.screen_w.fx is not None:
            return
        poop = self.pet.poop
        sizes0 = list(self.pet.poop_sizes)
        had = self.pet.clean()
        if had:
            self.screen_w.start_fx("clean", poop=poop)
            self.screen_w.fx["sizes"] = sizes0
            self.beep("wash", bell=False)
            self._do("All clean!")
        else:
            self._do("Nothing to clean.")

    def action_heal(self):
        if self.screen_w.fx is not None:
            return
        was_sick = self.pet.sick
        out = self.pet.feed_pill()
        if out == "healed":
            self.screen_w.start_fx("heal", icon="i:80")
            self._do("Cured!" if was_sick else "A tonic — strength and pep.")
        elif out == "refuse":
            self.screen_w.start_fx("spit")
            self._do(f"{self.pet.name} doesn't need it.")
        else:
            self._do("Not now.")

    def action_sleep(self):                          # the "s" key: lights toggle
        self.beep("confirm", bell=False)
        on = self.pet.toggle_lights()
        self._do("Lights on." if on else "Lights out. Sweet dreams.")

    def action_new(self):
        gen = self.pet.generation + 1
        self._open_mode(eggselectscreen.EggSelectPanel(self.pet),
                        lambda et: self._hatch_new(et, gen))

    def _hatch_new(self, egg_type, gen):
        if egg_type is None:                        # cancelled -> keep the current pet
            self._do("Kept your current partner.")
            return
        keep = self.pet
        self.pet = Pet.new_egg(generation=gen, egg_type=egg_type)
        # possessions persist across generations -- but NOT bg_current: the
        # new egg opens on ITS OWN scene (the gallery keeps every owned pick)
        self.pet.name = ""
        self.pet.bits = keep.bits
        self.pet.inventory = dict(keep.inventory)
        self.pet.bg_owned = list(keep.bg_owned)
        self.pet.album = list(keep.album)
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
