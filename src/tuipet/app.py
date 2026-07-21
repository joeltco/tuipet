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

from . import statusbox
from .appactions import ActionsMixin
from .appboot import (  # noqa: F401  (re-export: tuipet.app.X keeps resolving)
    MIN_COLS, MIN_ROWS, _load_sound, _lobby_uri, _preflight, _save_sound,
    _sound_path, host_platform)
from . import data
from . import menu
from . import eggselectscreen
from . import persistence
from . import net
from . import lobbyscreen
from . import titlescreen
from . import deathscreen
from . import sound
from . import update as update_check
from . import cloudsync
from .pet import Pet

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
# (page jumps joined the scrollers 2026-07-18; they blip like any cursor move)
_NAV_KEYS = frozenset({"up", "down", "left", "right", "j", "k", "h", "l", "tab",
                       "pageup", "pagedown"})

HUD_W = 40              # message-box content width (CSS #msg: 44 - 2 border - 2 padding)


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
    theme's KEY colour -- cyan on EVERY theme today (the per-theme key
    colours died with the putty-shell revert, Joel 2026-07-05 "this looks
    bad"; the magenta this docstring used to promise was archaeology --
    naming audit 2026-07-19).  Was a module constant with `b cyan` baked
    in, unreachable by theme.apply (shell polish 2026-07-05).

    Reading order mirrors the Help screen's sections — CARE, then
    EXPLORE, then GROW, then MANAGE — one layout language across the bar,
    Help and the Options→Keys page (bar tidy 2026-07-18).  GROW's egg
    guide wraps onto line 3: the line only holds 71 cells."""
    k = f"b {theme.KEY}"
    return (
        f"[{k}]f[/] feed [dim](meat·pill)[/]  [{k}]c[/] clean  [{k}]s[/] lights  [{k}]v[/] assist\n"
        f"[{k}]a[/] adventure  [{k}]r[/] raid  [{k}]u[/] cup  [{k}]l[/] lobby [dim](pvp)[/]  [{k}]t[/] train  [{k}]x[/] DNA  [{k}]d[/] digicore\n"
        f"[{k}]n[/] eggs  [{k}]o[/] shop  [{k}]i[/] bag  [{k}]e[/] scenes  [{k}]g[/] options  [{k}]b[/] bug  [{k}]?[/] help  [{k}]q[/] quit"
    )


# the status-card helpers live in statusbox (Joel 2026-07-17: "MODULIZE
# THE STATUS BOX"); the old underscore names stay importable for callers
# and the test suite
_gen_subtitle = statusbox.gen_subtitle
_age_compact = statusbox.age_compact
_care_deco = statusbox.care_deco
_status_line = statusbox.status_line


class Stats(Static):
    """The right-hand card widget.  Every card body lives in statusbox --
    this widget only chooses home/egg/grave and writes the lines."""

    def paint(self, pet: Pet):
        if pet.dead:
            return self._paint_grave(pet)
        if pet.num == -1 or pet.stage == "Egg":
            return self._paint_egg(pet)
        self.border_subtitle = _gen_subtitle(pet)
        self.update("\n".join(statusbox.home_lines(pet)))

    def _paint_egg(self, pet):
        self.border_subtitle = _gen_subtitle(pet)
        self.update("\n".join(statusbox.egg_lines(pet)))

    def _paint_grave(self, pet):
        self.border_subtitle = _gen_subtitle(pet)
        self.update("\n".join(statusbox.grave_lines(pet)))


class TuiPetApp(ActionsMixin, App):
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
    WHATS_NEW = ("The adventure march is back: travelling, your mon walks "
                 "clear across the window — out the right edge, back in "
                 "from the left — facing the way it's going, and road "
                 "stops happen right where it stands.")

    BINDINGS = [
        # battle + jogress are LOBBY-ONLY (Joel 2026-07-07: "battles and
        # jogress should be online pvp only"); fusion needs a real partner
        # from the roster.  PvE lives in Adventure (rebuild started
        # 2026-07-20 -- the flagship EXPLORE feature), raids and the cup.
        # Order = the ACTIONS bar / Help-screen reading order (CARE,
        # EXPLORE, GROW, MANAGE) so the Options→Keys page tells the same
        # story (bar tidy 2026-07-18).
        ("f", "feed", "Feed"), ("c", "clean", "Clean"),
        ("s", "sleep", "Lights"), ("v", "assist", "Assistant"),
        ("a", "adventure", "Adventure"),
        ("r", "raid", "Raid"), ("u", "tournament", "Cup"),
        ("l", "lobby", "Lobby"),
        ("t", "train", "Train"), ("x", "dna", "DNA"),
        ("d", "digicore", "DigiCore"), ("n", "eggguide", "Egg Guide"),
        ("o", "shop", "Shop"), ("i", "inventory", "Bag"),
        ("e", "scenes", "Scenes"), ("g", "options", "Options"),
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
                    # ...and never SWALLOW the notice either: the new-game
                    # path skips the welcome hud (title -> carousel, strips
                    # own the box every frame), so the message rode nothing
                    # and the loss looked exactly like a first launch -- the
                    # thing the 07-14 sweep existed to prevent (title audit
                    # 2026-07-19).  It joins the first surviving surface:
                    # the post-pick flash in _after_egg_pick.
                    self._boot_notice = msg
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
        self._sync_worker = self.run_worker(self._sync.run(), name="sync",
                                            exclusive=False)

    def _stop_sync(self):
        """Tear the pusher down for real: the stop flag alone left the old
        account's connection parked in `async for` until the socket dropped --
        a live sync ghost in the roster after every account switch (netplay
        audit 2026-07-18).  Cancel the worker like the lobby's."""
        if self._sync is not None:
            self._sync._stop = True
            self._sync = None
        w = getattr(self, "_sync_worker", None)
        if w is not None:
            w.cancel()
            self._sync_worker = None

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


    def _post_title(self):
        if self._new_game:
            self._open_mode(eggselectscreen.EggSelectPanel(self.pet), self._after_egg_pick)
        else:
            self._hud(self._welcome)
            self.repaint()

    def _death_ceremony(self, hold=0):
        """The ONE banking ceremony for a death, wherever it's noticed --
        the dying-fx completion, or a relaunch that finds the pet already
        dead.  The etch and the careBonusOnReset seed used to exist only in
        the fx branch, so a quit/crash during the dying beat silently
        disinherited the heir (gameplay audit 2026-07-19).  Runs once per
        death (pet.death_banked rides the save); after that every care key
        leads back to the bare memorial.

        UnlockInheritance (onDie with _bonus > 0): the departed CAN etch
        its Digimemory -- canon's DigiMemory_Validation is a real choice
        (declining keeps the bonus for the heir), so the panel asks; the
        etch is the walk-out default.  A held UNUSED payload is
        device-lifetime (canon item 32 survives resetToEgg): back to the
        bank first (digimemory audit 2026-07-06), where the only-one
        prompt covers it."""
        p = self.pet
        if p.death_banked:
            self._open_mode(deathscreen.DeathPanel(
                p, old_mem=persistence.peek_digimemory()), self._after_death)
            return
        if p.digimemory:
            persistence.bank_digimemory(dict(p.digimemory))
            p.digimemory = {}
        b0 = p.evol_bonus
        new_mem = p.make_digimemory()
        grade_spent = p.final_care_grade()   # the etch path's seed
        p.evol_bonus = b0
        grade_kept = p.final_care_grade()    # the decline path's seed
        p.evol_bonus = 0                     # the life is spent either way
        old_mem = persistence.peek_digimemory()
        banked_new = False
        if new_mem and not old_mem:
            persistence.bank_digimemory(new_mem)    # default: etched
            banked_new = True
        persistence.bank_bonus_seed(grade_spent)    # default seed; B re-banks
        p.death_banked = True
        persistence.save(p)
        self._open_mode(deathscreen.DeathPanel(p, hold=hold, new_mem=new_mem,
                                               old_mem=old_mem, grade_kept=grade_kept,
                                               banked_new=banked_new), self._after_death)

    def _grant_digimemory(self, pet):
        """Hand the banked inheritance data to the next generation: the payload
        rides the pet's save; the Digimemory chip appears in its bag (DVPet
        items persist across resetToEgg -- tuipet's generations carry only
        this one).  The raw "i:32" icon key it used to ride is healed to the
        named key on load (shop.LEGACY_KEYS; gameplay audit 2026-07-19)."""
        mem = persistence.take_digimemory()
        if mem:
            pet.digimemory = dict(mem)
            # the inherited ESTATE bag may already carry the elder's unused
            # husk (the re-banked-payload case) -- never a second chip for
            # one payload (digimemory audit 2026-07-06)
            if pet.inventory.get("digimemory", 0) <= 0:
                pet.add_item("digimemory")
        # the departed's care grade seeds this generation's bonus (careBonusOnReset)
        pet.evol_bonus = persistence.take_bonus_seed()


    def autosave(self):
        persistence.save(self.pet)
        self._start_sync()              # idempotent: picks up a re-enabled cloud toggle
        self._warn_if_unsaveable()
        self._warn_if_cloud_dropped()
        self._note_progress()
        self._push_cloud()              # mirror the autosave up to the cloud

    def _warn_if_cloud_dropped(self):
        """The cloud is refusing (or we're refusing to send) this device's
        saves.  The local save is fine, but cross-device sync is dead -- and
        we used to never mention it (swallowed-failure sweep 2026-07-13), or
        worse, blame "a newer session" for every cause (audit 2026-07-18:
        format rejections and oversized saves wore the wrong warning)."""
        sync = getattr(self, "_sync", None)
        if sync is None:
            return
        if getattr(sync, "cloud_dropped", False):
            msg = ("⚠ Cloud sync off — tuipet is open in a newer session. "
                   "This device saves locally only.")
        elif getattr(sync, "save_invalid", False):
            msg = ("⚠ Cloud sync off — the server rejected this save's "
                   "format. This device saves locally only.")
        elif getattr(sync, "save_too_big", False):
            msg = ("⚠ Cloud sync off — this pet's save is too large to "
                   "sync. This device saves locally only.")
        elif getattr(sync, "last_error", ""):
            msg = f"⚠ Cloud sync trouble — {sync.last_error}"
        else:
            return
        if getattr(self, "_cloud_warned", None) == msg:
            return                       # one flash per distinct cause
        self._cloud_warned = msg
        self.flash(f"[{theme.NEG}]{msg}[/]")

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
            # quit, options and the LOBBY stay live beside the grave (Joel
            # 2026-07-19: the social room is not a care action -- chat, DMs,
            # ladder and rooms all work; battles/jogress stay refused by
            # can_battle/can_jogress and the server's session gate).
            if event.key not in ("q", "g", "l"):
                event.stop()
                event.prevent_default()
                # every care key leads to the memorial (the dead-gate law) --
                # and if this death's etch/seed ceremony hasn't run yet (a
                # relaunch mid-dying-beat), it runs HERE, so the inheritance
                # can never be lost to a quit (gameplay audit 2026-07-19).
                # An untouched relaunch still gets the dying beat + mash
                # window from the tick's state check instead.
                self._death_ceremony()
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


    def _verdict(self, msg):
        """Deliver an ASYNC WORKER's outcome so it actually REACHES the
        player (the swallow class -- rounds 19/21/22): a worker can finish
        while any screen is open, whose strip overwrites the hud every
        frame.  Home -> flash now; in a mode -> park it, the ✉-drain
        pattern shows it back home.  EVERY async worker with a player
        verdict routes here (bug sends, account switches, ...)."""
        if self.mode is None:
            self.flash(msg)
        else:
            self._verdict_note = msg

    def _drain_verdict(self):
        note = getattr(self, "_verdict_note", "")
        if note and self.mode is None:
            self._verdict_note = ""
            self.flash(note)

    async def _send_bug(self, text, meta, name):
        ok = await net.submit_bug(_lobby_uri(), text, meta, name=name)
        if ok:
            self._verdict("Bug report sent \u2014 thank you!")
        elif persistence.add_pending_bug(dict(meta, text=text, name=name)):
            self._verdict("Offline \u2014 saved; it will send next time you are online.")
        else:
            # the stash failed too (a read-only save dir): do not promise a
            # send we cannot make (swallowed-failure sweep 2026-07-13)
            self._verdict(f"[{theme.NEG}]Couldn't send or save that report \u2014 sorry.[/]")

    async def _flush_bugs(self):
        """Best-effort resend of stashed bugs.  READ-then-rewrite (bug audit
        2026-07-19): the old take-then-send deleted the stash up front, so
        a quit mid-flush lost every unsent report (the round-5 PM lesson).
        A crash now leaves the original file -- a bounded duplicate send
        beats a lost report (the server's per-connection cap absorbs it)."""
        pending = persistence.peek_pending_bugs()
        if not pending:
            return
        left, outage = [], False
        for rec in pending:
            text, name = rec.get("text", ""), rec.get("name", "")
            if not text:
                continue          # a damaged line: drop it, never re-stash forever
            if outage:            # already hit an outage: keep the rest, in order
                left.append(rec)
                continue
            meta = {kk: vv for kk, vv in rec.items() if kk not in ("text", "name")}
            if not await net.submit_bug(_lobby_uri(), text, meta, name=name):
                left.append(rec)
                outage = True
        persistence.write_pending_bugs(left)

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
        self._verdict("Switching account…")
        verdict, save = await asyncio.to_thread(
            cloudsync.probe, _lobby_uri(), name, pw)
        if verdict == "badpw":
            self._verdict("Wrong password for that name.")
            self.beep("error", bell=False)
            return
        if verdict != "ok":
            self._verdict("Can't reach the lobby — try again online.")
            self.beep("error", bell=False)
            return
        if save is not None:
            # validate BEFORE committing to the switch: an unreadable cloud
            # blob must not cost the player their current login (the same
            # strict probe sync_down_at_startup runs)
            pet_probe, _ = persistence.pet_from_save(dict(save),
                                                     catch_up=False, strict=True)
            if pet_probe is None:
                self._verdict("That cloud save is unreadable — kept your account.")
                self.beep("error", bell=False)
                return
        persistence.save(self.pet)                   # park the pet with the OLD account
        if old_name == name:
            # re-login to the SAME account: never park, never delete -- only
            # refresh from a STRICTLY newer cloud copy.  This path used to
            # skip the sync_down_at_startup timestamp guard, so a day-old
            # cloud save could overwrite a newer local pet -- and a cloud
            # with NO save yet fell through to delete() and destroyed the
            # local pet's only copies (gameplay audit 2026-07-19).
            if save is not None and (float(save.get("_saved_at") or 0)
                                     > persistence.local_saved_at()):
                persistence.write_save_dict(save)
                loaded, msg = persistence.load()
                self.pet = loaded or Pet.new_egg()
                self._verdict(f"Signed in as {_hud_esc(name)} — {msg or 'welcome back!'}")
                self.repaint()
            else:
                self._verdict(f"Signed in as {_hud_esc(name)} — this device is current.")
            return
        if old_name:
            parked = await asyncio.to_thread(        # last-write-wins guarded upload
                cloudsync.push_save, _lobby_uri(), old_name, old_pw,
                persistence.to_save_dict(self.pet))
            if not parked:
                # push_save also answers False when the OLD cloud is already
                # newer (another device carries this pet) -- that counts as
                # parked.  Distinguish it from a real failed send.
                cloud = await asyncio.to_thread(
                    cloudsync.pull_save, _lobby_uri(), old_name, old_pw)
                parked = bool(cloud) and (float(cloud.get("_saved_at") or 0)
                                          >= persistence.local_saved_at())
            if not parked:
                # the switch may not proceed until the pet has a durable copy
                # somewhere -- the ignored push + delete() pair destroyed
                # save.json AND .bak (gameplay audit 2026-07-19)
                self._verdict(f"Couldn't park your pet with {_hud_esc(old_name)}"
                              " — kept your account.")
                self.beep("error", bell=False)
                return
        self._stop_sync()                            # the old pusher must stop first
        #                                              (cancelled, not just flagged)
        persistence.set_account(name, pw)
        if save is not None:
            persistence.write_save_dict(save)
            loaded, msg = persistence.load()
            self.pet = loaded or Pet.new_egg()
            self._start_sync()
            self._verdict(f"Signed in as {_hud_esc(name)} — {msg or 'welcome back!'}")
            self.repaint()
        elif old_name:
            persistence.delete()                     # parked above: the old pet must not leak in
            self.pet = Pet.new_egg()                 # placeholder until the carousel picks
            self._start_sync()
            self._verdict(f"Signed in as {_hud_esc(name)} — a fresh start.")
            self._open_mode(eggselectscreen.EggSelectPanel(self.pet),
                            self._after_egg_pick)
        else:
            # no old account: the local pet was never parked ANYWHERE, and
            # deleting it here destroyed its only copies.  Adopt it into the
            # new account instead -- exactly what the first lobby login does:
            # the pet stays local and the sync pushes it up.
            self._start_sync()
            self._verdict(f"Signed in as {_hud_esc(name)} — your pet syncs here now.")
            self.repaint()

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
        if (painter := self._status_painter()) is not None:
            painter()
        else:
            # data/digicore browses in the LCD; keep live vitals on the right
            self.stats_w.paint(self.pet)

    def _status_painter(self):
        """The mode's card painter, dispatched from statusbox's registry
        (one module owns every card -- Joel 2026-07-17: "MODULIZE THE
        STATUS BOX")."""
        fn = statusbox.painter_for(self.mode)
        if fn is None:
            return None
        return lambda: fn(self)

    def _status_eggselect(self):
        statusbox.eggselect(self)

    def _status_eat(self):
        statusbox.eat(self)

    def _status_card(self, title, lines):
        statusbox.card(self, title, lines)

    def on_frame(self):                        # single DVPet interval clock (10 Hz, 0.1s): main view AND sub-screens
        menu.TICK += 1                         # the shared note marquee clock: no screen clips a message
        self._hud_marquee()                    # scroll any over-long HUD message (independent of the LCD)
        self._drain_pms()                      # ✉ alerts ride the message box (presence 2026-07-05)
        self._drain_verdict()                  # a parked worker-verdict flashes back home (rounds 19/21/22)
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
                    self._death_ceremony(hold=20)
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
            # (the HeavyRain thunder roll -- the FLASH + the disposition-keyed
            # startle -- left with the weather system; BASIC VPET 2026-07-16)
            p = self.pet
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

    # a real hole in the 1 Hz cadence = the process was SUSPENDED (Ctrl-Z /
    # laptop lid); ordinary event-loop lag never reaches this
    SUSPEND_GAP_S = 120.0

    def on_tick(self):
        # the sim's proxy for "an animation is playing": the poop deferral
        # (canon startPoop state-machine block, restored 2026-07-19) holds
        # the squat through the whole VISIBLE fx, not just the anim ttl
        import time as _time
        now = _time.monotonic()
        gap = now - getattr(self, "_tick_wall", now)
        self._tick_wall = now
        if getattr(self, "pet", None) is not None:
            self.pet._fx_busy = getattr(getattr(self, "screen_w", None), "fx", None) is not None
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
            live = (isinstance(m, lobbyscreen.LobbyPanel)
                    and m.phase in ("lobby", "dm"))
            if not live:
                return
            poop0 = self.pet.poop
            self._suspend_catch_up(gap)
            self.pet.fx_hold = True     # evolution waits for the main view --
            #                             its strobe belongs to the home screen
            self.pet.tick(1.0)
            p = self.pet
            if p.dead and not p.death_banked and not self._dying_fx:
                # death can't wait for ESC: leave the room, play the memorial.
                # STATE, not a was_dead tick edge: a death set while the sim
                # was paused (the bag's poison mushroom) landed between ticks
                # and the edge never saw it -- no dying beat, no mash window,
                # no banking (gameplay audit 2026-07-19)
                if getattr(p, "away", False):
                    p.away = False            # the road ends here
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
        poop0 = self.pet.poop
        self._suspend_catch_up(gap)
        # an evolution must not swap the sprite UNDER a playing animation (the
        # clean-fx incident 2026-07-04: the pet transformed mid-sweep and the
        # evolve strobe played on the already-evolved form) -- hold the check
        # until the screen is quiet; the counters keep and it fires next tick
        self.pet.fx_hold = self.screen_w.fx is not None
        self.pet.tick(1.0)
        p = self.pet
        if p.dead and not p.death_banked and not self._dying_fx:
            # STATE, not a was_dead tick edge (see the mode branch above):
            # any un-ceremonied death gets its dying beat -- including one
            # set between ticks (poison mushroom) or loaded at relaunch
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
        elif needs or p.is_frail():   # frailty warns here too: it has no beep, and
            #  needs_care() alone never surfaced _need_message's frail branch
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

    def _suspend_catch_up(self, gap):
        """SUSPECT S4 ruling 2026-07-20: a process suspend (Ctrl-Z, a closed
        laptop lid) stopped the interval clock dead -- no ticks -- and the
        next autosave restamped _saved_at, so `_offline` never saw the hole:
        an OPEN pet lived a free pause while a CLOSED one aged.  A real gap
        in the tick cadence now routes through the SAME bounded offline
        catch-up a relaunch gets.  (The canon menu freeze stays a freeze: a
        gap that ends inside a paused sub-screen never reaches this.)"""
        if gap <= self.SUSPEND_GAP_S or self.pet is None or self.pet.dead:
            return
        off = persistence._offline(self.pet, min(gap, persistence.MAX_OFFLINE))
        if off:
            self.flash(off)

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
        else:                 return ""
        return f"[{theme.NEG}]\u26a0 {msg}[/]"


    # (the home battle + jogress actions were retired 2026-07-07 -- lobby-only
    # now; adventure/cup/town keep their own embedded BattlePanels and the
    # lobby keeps JogressPanel as its fusion-scene shim)

    # (praise/scold left with the discipline system; BASIC VPET 2026-07-16)


    # (the home h heal key retired: the pill rides the F feed menu now --
    # BASIC VPET 2026-07-16; the road's h key keeps working via pet.heal())


    def _hatch_new(self, egg_type, gen):
        if egg_type is None:                        # cancelled -> keep the current pet
            self._do("Kept your current partner.")
            return
        if egg_type == "guide":
            # N on the carousel: consult the guide, then come back to the
            # pick with the SAME generation in hand.  (This sentinel was
            # only handled on the fresh-start path -- the retire/death path
            # crashed on it: Termux crash 2026-07-18, egg_type='guide'.)
            from . import eggguidescreen, eggselectscreen
            self._open_mode(eggguidescreen.EggGuidePanel(self.pet),
                            lambda _=None: self._open_mode(
                                eggselectscreen.EggSelectPanel(self.pet),
                                lambda et: self._hatch_new(et, gen)))
            return
        # the generational COMMIT: nothing mutates until the pick is real
        # (an ESC-cancelled carousel used to have already appended a
        # headstone and overwritten last_gen -- gameplay audit 2026-07-19)
        if not self.pet.dead:
            # a LIVE retire skips the death flow entirely: canon resetDigimon
            # runs careBonusOnReset dead or alive, and a live reset never
            # offers the etch -- the FULL adjusted bonus carries to the heir
            # (digimemory audit 2026-07-06; this seed used to be lost)
            persistence.bank_bonus_seed(self.pet.final_care_grade())
        persistence.snapshot_prev_gen(self.pet)   # previous-generation egg gates
        self.pet = Pet.new_egg(generation=gen, egg_type=egg_type)
        self._grant_digimemory(self.pet)
        persistence.save(self.pet)
        self._do(f"A new egg appeared! (generation {gen})")




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
    if getattr(app, "_restart_after_exit", False):
        # the update's restart offer: the terminal is back to normal here,
        # so exec the NEW install in place.  The console script re-execs
        # itself; a `python -m tuipet` launch falls back to the interpreter.
        import sys as _sys
        argv0 = _sys.argv[0]
        if argv0 and _os.access(argv0, _os.X_OK) and not argv0.endswith(".py"):
            _os.execv(argv0, _sys.argv)
        _os.execv(_sys.executable, [_sys.executable, "-m", "tuipet"])
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
