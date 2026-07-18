"""The app's ACTION handlers (tier-3 split, 2026-07-17): every key on
the actions bar — the action_* entry, its _after_* close-callback, and the
_do result-flash — as a mixin over TuiPetApp's state (screen_w/stats_w/
mode/pet/_open_mode).  app.py keeps the shell: widgets, the 10Hz clock,
repaint, mode plumbing."""
from __future__ import annotations

import random  # noqa: F401

from . import assistscreen  # noqa: F401
from . import backgroundscreen  # noqa: F401
from . import bugscreen  # noqa: F401
from . import data  # noqa: F401
from . import deathscreen  # noqa: F401
from . import digicorescreen  # noqa: F401
from . import dnascreen  # noqa: F401
from . import egg as egg_mod  # noqa: F401
from . import eggguidescreen  # noqa: F401
from . import eggselectscreen  # noqa: F401
from . import feedscreen  # noqa: F401
from . import helpscreen  # noqa: F401
from . import lobbyscreen  # noqa: F401
from . import net  # noqa: F401
from . import persistence  # noqa: F401
from . import shopscreen  # noqa: F401
from . import statusbox  # noqa: F401
from . import theme  # noqa: F401
from . import titlescreen  # noqa: F401
from . import tournament  # noqa: F401
from . import tournamentscreen  # noqa: F401
from . import training  # noqa: F401
from . import optionsscreen  # noqa: F401
from .appboot import _lobby_uri  # noqa: F401
from .pet import Pet  # noqa: F401


class ActionsMixin:
    """State contract: self.pet / self.mode / self.screen_w / self.stats_w /
    self._open_mode / self._close_mode / self.flash / self.repaint."""

    def _after_title(self, _=None):
        # The account wall used to stand HERE: name + password demanded on
        # first launch, before the player had seen a single pet (sweep
        # 2026-07-14).  The account only matters online -- the lobby asks for
        # one when it's first opened, and sync starts on the next autosave.
        self._post_title()

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
        if result and result[0] == "restart":
            # the update's restart offer: save, leave Textual cleanly, and
            # main() re-execs the NEW code once the terminal is restored
            self.autosave()
            self._restart_after_exit = True
            self.exit()
            return
        if result and result[0] == "new":
            self.action_new()
            return
        if result and result[0] == "account":
            self.run_worker(self._switch_account(result[1], result[2]),
                            name="switch", exclusive=False)
            return
        if result and result[0] == "erase":
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
        elif outcome == "healed":
            # the pill is EATEN (decompile EATING state): the same eat fx as
            # meat, on the ripped pill bite strip (pill-anim fix 2026-07-18)
            self.screen_w.start_fx("eat", icon, pet=self.pet)
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

    def action_scenes(self):
        """The E scene picker (restored 2026-07-17): egg default, pick overrides."""
        self._open_mode(backgroundscreen.BackgroundPanel(self.pet), self._after_scenes)

    def _after_scenes(self, msg):
        if msg:
            self.flash(msg)
        self.repaint()

    def action_shop(self):
        self._open_mode(shopscreen.ShopPanel(self.pet), self._after_shop)

    def action_inventory(self):
        self._open_mode(shopscreen.ShopPanel(self.pet, start_mode="bag"), self._after_shop)

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
        elif msg:
            self.flash(msg)
        self.repaint()

    def action_raid(self):
        from . import raidscreen
        if self.pet.stage in ("Egg", "Fresh"):
            self._do("Too young for a raid."); return
        if self.pet.asleep:
            self._do("zzz… asleep"); return
        self._open_mode(raidscreen.RaidPanel(self.pet, self._lobby_connect),
                        self._after_raid)

    def _after_raid(self, msg):
        if msg:
            self.flash(msg)
        self.autosave()
        self.repaint()

    def action_gift(self):
        if self.mode is not None or self.screen_w.fx is not None or not self.pet.gift:
            return
        key = self.pet.gift
        msg = self.pet.claim_gift()
        if msg:
            self.screen_w.start_fx("gift", icon=key)   # gifting() amble, chains to cheer (giftEnd)
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

