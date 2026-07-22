"""The pet's BODY CLOCK (tier-5, 2026-07-17): the per-tick simulation --
hunger, filth, sleep, growth, recovery, mortality, the care effects and
the assistant's rounds.  Nothing here is player-initiated; it is what
time does to the creature."""
from __future__ import annotations
import math  # noqa: F401
import random  # noqa: F401

from . import backgrounds  # noqa: F401
from . import data  # noqa: F401
from . import egg as egg_mod  # noqa: F401
from . import evolution  # noqa: F401
from . import lines as lines_mod  # noqa: F401
from . import shop  # noqa: F401
from . import theme  # noqa: F401
from .petbase import *  # noqa: F401,F403  (constants resolve HERE, per mixin)


class BodyMixin:
    """State contract: the Pet dataclass fields; composed into Pet."""

    # ---- per-tick simulation -------------------------------------------------
    def tick(self, dt):
        """One game-minute of life.  Decomposed into ordered phases (audit
        2026-07); each phase's body is verbatim from the old monolith, and the
        early-return structure (egg / asleep / death) is explicit here."""
        self._tick_clock(dt)
        if self.dead:
            return
        self._tick_growth(dt)
        if self.stage == "Egg":
            self._tick_egg()
            return
        self._tick_recovery(dt)
        if self.dead:                # the 6h-malady clock can end the life here
            return
        self._tick_auto_care(dt)     # the assistant serves awake AND asleep (never an egg)
        if self.asleep:
            self._tick_asleep(dt)
            return
        self._tick_mood_discipline(dt)
        self._tick_hunger(dt)
        self._tick_body(dt)
        self._tick_sleep_pressure(dt)
        if self._tick_mortality(dt):
            return
        if (self.anim in ("idle", "walk") and self.anim_ttl <= 0 and not self.poop
                and not self.sick and random.random() < 0.03 * dt):
            self._special_idle()
        self._maybe_evolve()

    def _tick_clock(self, dt):
        """The world clock: hour rollover (tournament alarm) + weather -- these
        run even over the grave."""
        hr0 = int((self.world_seconds % DAY_LENGTH) / DAY_LENGTH * 24)
        self.world_seconds += dt
        hr1 = int((self.world_seconds % DAY_LENGTH) / DAY_LENGTH * 24)
        if hr1 != hr0 and not self.dead:
            self.tourney_alert = False    # a ring only lasts its cup's hour
            if self.tourney_alarm >= 0:
                from . import tournament as _tourney
                _tourney.schedule(self)   # a day rollover re-rolls (and clears the alarm)
            if self.tourney_alarm >= 0 and self.tourney_alarm in (self.tourney_schedule or []) \
                    and (self.tourney_schedule.index(self.tourney_alarm) == hr1):
                # CurrentTime.setSeconds: on the hour of the alarmed cup's slot,
                # clear the alarm and raise TournamentAlert (the attention call)
                self.tourney_alarm = -1
                self.tourney_alert = True

    def _tick_growth(self, dt):
        """Aging + the ambient systems: X-decay, shop restock, toy interest,
        the gift call, the mood record / birthday, the anim clock."""
        # (the Temporary protoform decay left with the X slim)
        self.age_seconds += dt
        self.stage_seconds += dt
        # (the shop restock credits left with the rolled-slot shop; the
        # DSprite catalog is a fixed shelf -- BASIC VPET 2026-07-16)
        # setItemInterestLapse: toy boredom fades -1 per timer -- a sunny pet
        # (disposition +1) re-engages in 40 game-min, a sour one takes 80
        if self.item_interest > 0:
            self._interest_t = getattr(self, "_interest_t", 0.0) + dt
            timer = (ITEM_INTEREST_LOW_TIMER if self.disposition > 0
                     else ITEM_INTEREST_HIGH_TIMER if self.disposition < 0 else ITEM_INTEREST_TIMER)
            if self._interest_t >= timer:
                self._interest_t = 0.0
                self.item_interest -= 1
        self._check_gift_call(dt)                   # checkGiftCall: a happy pet may find a present
        # checkMoodRecord: sample the mood tier every MoodRecordMin game-min
        if self.stage != "Egg":
            self._mood_rec_t = getattr(self, "_mood_rec_t", 0.0) + dt
            if self._mood_rec_t >= MOOD_RECORD_MIN:
                self._mood_rec_t = 0.0
                m = self.current_mood()
                self.daily_mood[m] = self.daily_mood.get(m, 0) + 1
            # setTimeToAge: every AgeUp (one game day of age) is a BIRTHDAY,
            # judged by the day's MAJOR mood and the missed-day tally
            day = int(self.age_seconds // DAY_LENGTH)
            if day > self.last_birthday:
                self.last_birthday = day
                self._birthday()
        if self.anim_ttl > 0:
            self.anim_ttl -= dt
            if self.anim_ttl <= 0:
                self.anim = "sleep" if self.asleep else "idle"

    def _tick_egg(self):
        """Egg stage: only the hatch trigger (the 3s crack runs at frame cadence
        via advance_hatch; a 1 Hz countdown here would skip the crack frames)."""
        if not self.hatching and self.stage_seconds >= self.EGG_DURATION:
            self.hatching = True
            self._hatch_t = 3.0
            self._set_anim("hatch", 3.0)

    def _tick_recovery(self, dt):
        """Environment + the recovery lapses (they run asleep or awake)."""
        day = int(self.world_seconds // DAY_LENGTH)
        if getattr(self, "_exercise_day", -1) != day:    # DVPet checkExerciseTime: daily reset
            self._exercise_day = day
            self.exercise_today = 0

    def _inc_mistake(self):
        """PhysicalState.incMistake: EVERY care mistake stings the mood first --
        a Happy pet is knocked DOWN TO 100 (MistakeHappyMoodChange, absolute),
        anyone else loses 50 -- then the counters tick (care-mistake audit
        2026-07-05: the counters ticked silently)."""
        if self.current_mood() == "Happy":
            self._set_mood(MISTAKE_HAPPY_MOOD)
        else:
            self._set_mood(self.mood - MISTAKE_MOOD_DEC)
        self.care_mistakes += 1
        self.mistake_day += 1                        # MistakeIncMissedDayChange

    def _tick_asleep(self, dt):
        """The sleep branch: lights neglect, deep-sleep regen, the awakeLapse
        clock with the restless jitter, asleep death checks, desperate poop."""
        # lightsCall (DVPet): sleeping with the room light ON is neglect.
        # AfterMistakeMinutesPostponed is -60, NOT a latch: the mistake REPEATS
        # every 120 lit minutes (a fully lit night is ~4 mistakes); the
        # obedience ding lands ONCE per night (_lightsOffMistake flag).
        if self.lights:
            self._lights_t = getattr(self, "_lights_t", 0.0) + dt
            if self._lights_t >= LIGHTS_MISTAKE_SEC:
                self._lights_t = LIGHTS_MISTAKE_POSTPONE
                if not getattr(self, "_lit_obed_hit", False):
                    self._lit_obed_hit = True
                    self._set_obedience(self.obedience + LIGHTS_MISTAKE_OBED)
                self._inc_mistake()
        # Pen20 DP: sleep restores jogress power -- 3 game-hours = a full meter
        if self.dp < DP_MAX:
            self._dp_t = getattr(self, "_dp_t", 0.0) + dt
            if self._dp_t >= DP_SLEEP_MIN:
                self._dp_t -= DP_SLEEP_MIN
                self.dp += 1
        # (the asleep enthusiasmLapse left with the spirit system;
        # BASIC VPET 2026-07-16)
        # sleepDecay/setAwakeLapse (canon re-audit 2026-07): the wake clock steps
        # by the species AwakeLapseInc; a LIT room stalls it half the time
        # (LightsOnAwakeLapseUnchangedChance -- lit rest is poor rest); the
        # MoreSleepChance jitter lets a mellow pet lie in and a restless one
        # skip ahead, its bonus routed through the ACCUMULATORS like canon
        # (the old code paid energy directly, misreading NapEnergyMin -- a
        # cadence -- as an amount).
        phys = self._phys()
        awake_inc = phys.get("awake_inc", 1)

        def _inc_sleep_minutes(gain):
            # incSleepMinutes: the meter fills by AwakeLapseInc; a crossing pays
            self._sleep_min = getattr(self, "_sleep_min", 0.0) + awake_inc * dt
            if self._sleep_min >= SLEEP_MIN_TO_GAIN:
                self._sleep_min -= SLEEP_MIN_TO_GAIN
                self._set_energy(self.energy + gain)

        def _nap_energy(mult=1):
            # checkNapEnergy: the nap's own accumulator pays NapEnergyGain (1)
            self._nap_e = getattr(self, "_nap_e", 0.0) + awake_inc * dt * mult
            if self._nap_e >= NAP_ENERGY_INC:
                self._nap_e -= NAP_ENERGY_INC
                self._set_energy(self.energy + 1)

        step = awake_inc * dt
        if self.lights and random.randrange(100) < LIGHTS_ON_AWAKE_STALL:
            step = 0.0
        r = random.randrange(MORE_SLEEP_CHANCE) + self.restless * AWAKE_RESTLESS_COEF
        bonus = False
        if r < 0:
            step = max(0.0, step - dt)
        elif r > MORE_SLEEP_CHANCE - 1:
            step += dt
            bonus = True
        if self.nap:
            # canon: a nap PAYS DOWN bedtime pressure (sleepLapse -= inc) -- the
            # old '+=' inverted it -- and, held past ChangeNapToSleepMinutes
            # (+restless coef), the nap BECOMES the night: pressure clears, the
            # accumulator residue rolls into the sleep meter, nap=false
            self.sleep_lapse = max(0.0, self.sleep_lapse - awake_inc * dt)
            self._nap_cycle = getattr(self, "_nap_cycle", 0.0) + dt
            _nap_energy(2 if bonus else 1)
            if (self._nap_cycle >= CHANGE_NAP_TO_SLEEP + self.restless * NAP_TO_SLEEP_RESTLESS
                    and self._in_sleep_window() is not False):   # a line pet's day-doze
                #                          never becomes the night; bedtime does that
                self._sleep_min = (getattr(self, "_sleep_min", 0.0)
                                   + max(0.0, getattr(self, "_nap_e", 0.0) - 1))
                self._nap_cycle = self._nap_e = 0.0
                self.sleep_lapse = 0.0
                self.nap = False
        else:
            _inc_sleep_minutes(NEGATIVE_ENERGY_GAIN if self.energy < 0
                               else getattr(self, "_sleep_energy_gain", 3))
            if bonus:
                _inc_sleep_minutes(BONUS_SLEEP_ENERGY)
        self.awake_lapse += step
        iw = self._in_sleep_window()
        if iw is not None and not self.nap:
            if iw is False:                      # LINES_SPEC §5: 7:00 sharp, no jitter
                self._wake()
        elif self.awake_lapse >= self.awake_limit:
            self._wake()                         # nap wakes take the nap roll inside
        # hungerDecay: asleep the stomach drains only ABOVE the floor
        # (SleepMinHungerDecay=3) -- one heart overnight, then it holds
        if self.hunger > SLEEP_MIN_HUNGER_DECAY:
            self._tick_hunger(dt)
        # canon runs these in bed too: the filth nag+risk, and
        # poopWaitMoodCheck -- the HELD gauge (only a sleeper holds it) nags
        # (the mood lapse / call drain / depression left with the mood system)
        self._filth_effects(dt)
        if self._poop_t >= self._poop_interval:
            self._poop_wait_t = getattr(self, "_poop_wait_t", 0.0) + dt
            if self._poop_wait_t >= 1.0:                 # PoopWaitMin 1 game-min (was 60.0)
                self._poop_wait_t = 0.0
                self._set_mood(self.mood + (LARGE_POOP_WAIT_MOOD
                                            if self._poop_t >= self._poop_interval * 1.5
                                            else POOP_WAIT_MOOD))
        # death does not wait for morning: the caps, the filth/overweight
        # sickness rolls and the sick-death whisper run in bed too, exactly as
        # the "filth risk runs in bed" note promises -- _tick_mortality's own
        # gates freeze ONLY the starvation clock while asleep
        if self._tick_mortality(dt):
            return
        # startPoop: even asleep, a truly DESPERATE gauge (>= 2x max) goes --
        # this must live in the sleep branch (the awake poop block below is
        # unreachable while asleep; latent until the canon day bands landed)
        self._poop_t = getattr(self, "_poop_t", 0) + dt
        if self._poop_t >= self._poop_interval * 2:
            self._poop_t = 0                 # gauge zeroed (DVPet poop())
            self._do_poop(backlog=True)
            self._set_anim("poop", 2.2)

    def _tick_mood_discipline(self, dt):
        """The filth nag + sickness risk, and the childhood personality
        tracker.  (The mood lapse left with the mood system; the obedience
        lapse, refusal expiry, tantrum clock and praise/scold window aging
        left with the discipline system -- BASIC VPET 2026-07-16.  DVPet has
        NO passive energy decay -- energy only moves via activity and sleep.)"""
        self._filth_effects(dt)
        # personalityTracker (taste/rank audit 2026-07-06): childhood care is
        # TALLIED through Fresh/InTraining/Rookie -- energy kept above 75% of
        # max builds restlessness, weight off Healthy builds gluttony (the
        # mood-tier disposition leg left with the mood system);
        # randOnChampion cashes the tally in at the Champion evolution
        self._rank_t = getattr(self, "_rank_t", 0.0) + dt
        if self._rank_t >= 59:
            self._rank_t = 0.0
            if self.stage in ("Fresh", "InTraining", "Rookie"):
                if self.energy >= PCHAMP_HI_ENERGY * self.max_energy:
                    self.energy_rank += 1
                elif self.energy <= PCHAMP_LO_ENERGY * self.max_energy:
                    self.energy_rank -= 1
                wc = evolution.weight_category(self.weight, self._base_weight())
                if wc == "Over":
                    self.weight_rank += 1
                elif wc == "Under":
                    self.weight_rank -= 1

    def _filth_effects(self, dt):
        """checkFilthMoodDec + the filth sickness rolls (canon re-audit 2026-07):
        every FilthMoodDecMin the mess costs species filth_mood x piles; every
        game-min each pile is a sickness risk (chance x piles vs the bound x the
        species multiplier -- the 12000 real-min bound rides the /60 game scale,
        which lands within a hair of the old hand-rolled rate while gaining the
        per-pile scaling and the worse-sick path the flat roll lacked).
        Away, canon's countFilth() reads 0 (poopable gates on _isHome): the
        home mess can't sicken a pet out on the road (sweep 2026-07-06)."""
        if getattr(self, "away", False):
            return
        if self.poop <= 0:
            return
        fm = self._phys().get("filth_mood", -1)
        if fm:
            self._filth_mood_t = getattr(self, "_filth_mood_t", 0.0) + dt
            if self._filth_mood_t >= FILTH_MOOD_DEC_MIN:
                self._filth_mood_t = 0.0
                self._set_mood(self.mood + fm * self.poop)

    def _tick_hunger(self, dt):
        """hunger: the DVPet calorie buffer drains each lapse; emptying it drops
        a hunger heart, then refills.  The care MISTAKE is the call light
        (LINES_SPEC §5, canon on all three devices): hunger empty and unanswered
        for 10 minutes = ONE mistake, then the call is postponed — it no longer
        repeats every calorie cycle while starving."""
        if self.full_until and self.world_seconds < self.full_until:
            return                    # premium-meat satiety (DSprite item)
        # hungerCall: a single mistake per unanswered call, mirroring strengthCall
        if self.hunger == 0 and not self.asleep:
            self._hunger_call_t = getattr(self, "_hunger_call_t", 0.0) + dt
            # ⚖️ DELIBERATE, *not* a clock-unit slip (cadence audit 2026-07-14).
            # Canon gives you 10 GAME-min to answer the call -- and on the real
            # device, which runs in REAL time, that IS ten real minutes.  Under
            # tuipet's 60x compression the literal port would be TEN REAL
            # SECONDS to notice the alarm and feed, or take a PERMANENT care
            # mistake (20 = death; 5 kills an elder).  Unplayable in a terminal
            # you leave in the background.  So the CONTINUOUS pressures (mood
            # drain, filth, sickness rolls) run at the canon game-min cadence,
            # while the DISCRETE PUNISHMENTS keep a fair human response window.
            if self._hunger_call_t >= 600.0:                 # 10 real min to answer
                self._hunger_call_t = -3600.0                # AfterMistakeMinutesPostponed
                self._inc_mistake()
                self.mistake_day += 1  # + HungerDecAtZero MissedDayChange
                self._burn_life(HUNGER_MISTAKE_LIFE_DEC * max(1, self.care_mistakes),
                                f"hunger gnaws at {self.name}'s life")
                # hungerMistakePenalty: obedience +1 -- or -1 for a glutton.
                # NO scold window: canon opens those for refusals and the
                # discipline tantrum only -- neglect costs mistakes/obedience,
                # it never makes the pet "act up" (discipline audit 2026-07-06;
                # the invented window leaked -10 obedience per miss and fed
                # the refusal spiral)
                self._set_obedience(self.obedience
                                    + (HUNGER_MISTAKE_OBED_GLUTTON if self.glutton > 0
                                       else HUNGER_MISTAKE_OBED))
        elif self.hunger > 0:
            self._hunger_call_t = 0.0
        self._cal_t = getattr(self, "_cal_t", 0.0) + dt
        if self._cal_t >= self._hunger_interval:
            self._cal_t = 0.0
            self._set_calories(self.calories + CALORIE_LAPSE_CHANGE
                               + (CALORIE_LAPSE_GERIATRIC_EXTRA if self.is_geriatric else 0))
            if self.calories <= -CALORIE_LIMIT:
                if self.hunger > 0:
                    self.hunger -= 1
                if self.hunger == 0:
                    # starvation (setHunger below zero): the calorie crash sheds weight
                    # every further lapse (StarvationCalorieChange -> ActivityWeightChange)
                    self._set_weight(self.weight - STARVE_WEIGHT_DEC)
                self.calories = CALORIE_LIMIT

    def _tick_body(self, dt):
        """The body's slow clocks: pooping, effort decay, nutrition decay, the
        filth care-mistake, and filth/starvation sickness."""
        # pooping (DVPet poop(): relief mood bump, sheds weight, drops a sized pile)
        self._poop_t = getattr(self, "_poop_t", 0) + dt
        # (a sleeping pet held it above -- only the desperate 2x gauge goes at night)
        if self._poop_t >= self._poop_interval:
            busy = self.anim not in ("idle", "walk") or getattr(self, "_fx_busy", False)
            if busy:
                # canon startPoop: the anim STATE MACHINE blocks the squat --
                # the pet HOLDS it until the action ends (restored 2026-07-19,
                # Joel's report: "it poops during feeding... make sure nothing
                # can get glitchy").  The 07-15 audit had dropped this "by
                # architecture"; the app marks the fx window via _fx_busy so
                # the hold covers the whole visible animation.  Canon bills
                # the hold once: PostponePoopMoodChange -1.  The gauge keeps
                # accruing -- a long hold releases as the big backlog pile.
                if not getattr(self, "_poop_held", False):
                    self._poop_held = True
                    self._set_mood(self.mood - 1)
            else:
                self._poop_held = False
                self._poop_t -= self._poop_interval  # gauge -= bmMax (the remainder carries)
                backlog = self._poop_t >= self._poop_interval / 2
                if backlog:                          # big backlog: bigger pile + extra shed,
                    self._poop_t = 0                 # gauge zeroed (DVPet poop())
                self._do_poop(backlog=backlog)
                self._set_anim("poop", 2.2)          # squat-and-go (DVPet poop())
        # effort decays per species (DVPet calcStrengthDecayLapse): keep training or it slips
        if self.strength > 0:
            self._str_t = getattr(self, "_str_t", 0.0) + dt
            if not self.asleep and self._str_t >= self._strength_interval:
                self._str_t = 0.0
                self.strength -= 1
                if self.strength == 0:
                    self.mistake_day += 1        # StrengthDecAtZeroMissedDayChange
        else:
            # an EMPTY gauge has nothing to decay: the timer idling upward
            # here meant a heal after a long-empty spell was undone ONE TICK
            # later -- and billed a fresh missed-day (gameplay audit
            # 2026-07-19).  A refill starts a whole fresh interval.
            self._str_t = 0.0
        # strengthCall (canon gap closed, audit 2026-07): an EMPTY effort gauge
        # left unattended 10 game-min is a care mistake + obedience -5
        # (strengthMistakePenalty), postponed after one like the other calls
        if self.strength == 0 and not self.asleep:
            self._str_call_t = getattr(self, "_str_call_t", 0.0) + dt
            if self._str_call_t >= 600.0:                    # 10 real min to answer
                #   (the same deliberate response-window rule as the hunger call)
                self._str_call_t = -3600.0                   # AfterMistakeMinutesPostponed
                self._inc_mistake()
                self._set_obedience(self.obedience - 5)      # MistakeStrengthObedienceDec
                # no scold window on neglect (canon; discipline audit 2026-07-06)
                # -- strength drains to 0 on its own species timer, so this one
                # opened "misbehaving!" windows for free on a loop
        else:
            self._str_call_t = 0.0
        # (the nutrition macro lapse left with the nutrition system;
        # BASIC VPET 2026-07-16)
        # Filth acting-up (LINES_SPEC §5): NO real device counts filth as a care
        # mistake (Pen20 says so explicitly — mistakes are unanswered call lights
        # only), so the DVPet poopCall mistake is retired.  Filth keeps its teeth
        # (sickness rolls + mood drain in _filth_effects); an awake pet left amid
        # the mess past the grace still ACTS UP (scold window), postponed after one.
        FILTH_LIMIT = 3                      # the visible "needs cleaning" level
        if self.poop >= FILTH_LIMIT:
            if not self.asleep:              # only ticks while awake; sleep pauses, not resets
                self._filth_t = getattr(self, "_filth_t", 0) + dt
                if self._filth_t >= 1800:    # uncleaned grace before it acts up
                    self._filth_t = -3600    # AfterMistakeMinutesPostponed grace after one
                    self._open_scold()       # left in filth: the pet acts up
        else:
            self._filth_t = 0                # cleaned / under the limit resets the call timer

    def _near_bedtime(self, n):
        """checkMaxHoursBeforeSleep's clock half: asleep aside, is nod-off
        within `n` game-minutes?  Pressure pets read the sleep clock
        (sleepLimit - sleepLapse <= n, canon verbatim); line pets read the
        wall clock to their fixed bedtime."""
        iw = self._in_sleep_window()
        if iw is not None:
            if iw:
                return True
            bt = lines_mod.bedtime_minutes(self)
            return bt is not None and (bt - self.world_seconds % DAY_MINUTES) % DAY_MINUTES <= n
        return self.sleep_limit - self.sleep_lapse <= n

    def _in_sleep_window(self):
        """Line pets sleep by the CLOCK: True/False = inside/outside the form's
        fixed bedtime→7:00 window; None = not a line pet (pressure model)."""
        bt = lines_mod.bedtime_minutes(self) if lines_mod.active(self) else None
        if bt is None:
            return None
        mod = self.world_seconds % DAY_MINUTES
        if bt > self.WAKE_MINUTE:                     # the usual wrap past midnight
            return mod >= bt or mod < self.WAKE_MINUTE
        return bt <= mod < self.WAKE_MINUTE           # a midnight sleeper (24:00 -> 0)

    def _tick_bedtime(self, dt):
        """LINES_SPEC §5: the fixed per-form bedtime replaces the pressure clock.
        Inside the window the pet drops off by itself (a disturb postpones the
        re-sleep); lights-out OUTSIDE the window is a shallow nap, like checkNap.
        The nightly ritual: at bedtime the room is still lit — turning the lights
        off within the grace is the care; a lit sleeper logs the once-per-night
        lights mistake exactly as before."""
        if self.asleep:
            return
        if self._in_sleep_window():
            self._bed_postpone_t = getattr(self, "_bed_postpone_t", 0.0) - dt
            if self._bed_postpone_t > 0:
                return                                # a disturb bought some grumbling time
            self._fall_asleep()
            # the night is the window, not an energy budget: rested checks and
            # the sleep meter size off the real span (bedtime -> 7:00)
            bt = lines_mod.bedtime_minutes(self)
            self.awake_limit = (self.WAKE_MINUTE - bt) % DAY_MINUTES
            self.sleep_limit = DAY_MINUTES - self.awake_limit
        elif not self.lights:
            # the daytime doze waits out the same calcToSleepNapLapse as the
            # pressure model (sleep audit 2026-07-06)
            self._to_nap_t = getattr(self, "_to_nap_t", 0.0) + dt
            if self._to_nap_t < self._calc_to_nap():
                return
            self._to_nap_t = 0.0
            # a daytime doze: same once-per-game-hour mood bonus guard as checkNap
            if self.world_seconds - getattr(self, "_nap_bonus_t", -9e9) >= 60:
                self._nap_bonus_t = self.world_seconds
                self._set_mood(self.mood + ON_NAP_MOOD_INC)
            self.asleep, self.nap = True, True
            # the doze's own length: checkNap's fixed hour (awakeLimit -
            # minutesHour) -- without this the doze inherited the whole
            # previous NIGHT's awake_limit and slept the day away
            self.awake_lapse = max(0.0, self.awake_limit - 60.0)
            self._lights_t = 0.0
            self._lit_obed_hit = False
            self._set_anim("yawn", 1.8)
        else:
            self._to_nap_t = 0.0

    def _calc_to_nap(self):
        """calcToSleepNapLapse: how long the pet sits in the DARK before it
        nods off -- an energetic pet resists (~40 game-min), a drained one
        folds in 20; restless +-1.  (The obedience +1 left with the
        discipline system: the pinned-0 meter billed EVERY pet the extra
        doze minute while the >=75 discount was unreachable -- MED audit
        2026-07-19.)"""
        r = self.restless * TO_SLEEP_NAP_RESTLESS
        return (TO_NAP_HIGH_ENERGY if self.energy > self.max_energy / 2
                else TO_NAP_LOW_ENERGY) + r

    def _tick_sleep_pressure(self, dt):
        """bedtime is a PRESSURE clock, not the sun (setSleepLapse): SleepLapseInc
        per game-min while awake; at the limit the pet drops off by itself --
        babies (inc 9) nap constantly, adults run a free ~24h rhythm.
        checkNap fires only after the DOZE-OFF WAIT (toNapSleepLapse; sleep
        audit 2026-07-06 -- the old instant nap skipped it): lights out, the
        pet sits a calcToSleepNapLapse while, THEN dozes (real sleep instead
        when the pressure is nearly full -- sleepNotNap).
        Line pets sleep by the CLOCK instead (LINES_SPEC §5)."""
        if self._in_sleep_window() is not None:
            self._tick_bedtime(dt)
            return
        if not self.asleep:
            self.sleep_lapse += dt * self._sleep_inc()
            if self.sleep_lapse >= self.sleep_limit:
                self._fall_asleep()
            elif not self.lights:
                self._to_nap_t = getattr(self, "_to_nap_t", 0.0) + dt
                if self._to_nap_t < self._calc_to_nap():
                    return                                  # still blinking in the dark
                self._to_nap_t = 0.0
                edge = SLEEP_NOT_NAP_MIN - self.restless * SLEEP_NOT_NAP_RESTLESS
                if self.sleep_lapse >= self.sleep_limit - edge:
                    self._fall_asleep()                     # close enough to bedtime
                else:
                    # checkNap: a shallow doze that BORROWS the current cycle --
                    # pressure keeps accruing, so real bedtime still arrives on
                    # time.  The +10 nap mood keeps the extra once-per-game-hour
                    # guard (belt over the doze-off wait, canon's own anti-farm)
                    if self.sleep_lapse - getattr(self, "_nap_bonus_lapse", -9e9) >= 60:
                        self._nap_bonus_lapse = self.sleep_lapse
                        self._set_mood(self.mood + ON_NAP_MOOD_INC)
                    self.asleep, self.nap = True, True
                    self._lights_t = 0.0
                    self._lit_obed_hit = False
                    # checkNap's nap length: a SICK or hurt pet takes a fixed
                    # hour (awakeLimit - minutesHour); healthy naps repay the
                    # accrued pressure.  (Canon's end-of-hour 2-hour variant is
                    # a wall-clock alignment quirk tuipet's clock doesn't have.)
                    self.awake_lapse = max(0.0, self.awake_limit - self.sleep_lapse)
                    self._set_anim("yawn", 1.8)
            else:
                self._to_nap_t = 0.0                        # the light resets the wait

    def _check_death_caps(self):
        """The discrete mistake/injury caps + the Pen20 elder-frailty rule:
        ONE copy for both tick paths -- these gates were duplicated between the
        sleep tick and _tick_mortality and had to be edited in lockstep
        (refactor 2026-07-05).  True when the pet died."""
        if self.care_mistakes >= 20:                           # MaxCareMistakes
            self._die("neglect")
            return True
        # Pen20 (LINES_SPEC §5): at the last stages, 5 slips once the evolution
        # window is open = death -- an elder Perfect/Ultimate demands real care
        if (self.stage in ("Ultimate", "Mega") and self.care_mistakes >= 5
                and self.stage_seconds >= self.LATE_STAGE_WINDOW):
            self._die("frailty")
            return True
        return False

    def _check_old_age(self):
        """lapsedLife >= totalLifespan -- canon's one true death trigger.
        True when the pet died."""
        if self.age_seconds >= self.lifespan:
            self._die("old age")
            return True
        return False

    def _burn_life(self, amount, note=None):
        """setTotalLifespan's penalty path (canon re-audit 2026-07): every
        neglect event BURNS lifespan, clamped so a cut can never kill inside
        InstantDeathGracePeriod of now -- death always gives you the grace.
        A `note` marks the burn as a SURFACED event (canon EnableLifePenaltyAnim
        -> Bad_Health_Jeering): app.on_tick flashes it and jeers, so the Life bar
        is felt reacting instead of ticking in silence (Joel 2026-07-22: "does
        the life bar even do anything?")."""
        self.lifespan = max(self.age_seconds + INSTANT_DEATH_GRACE, self.lifespan - amount)
        if note:
            self.life_penalty_note = note

    def _tick_mortality(self, dt):
        """Canon death is ONE trigger -- old age (lapsedLife >= totalLifespan)
        -- reached faster as neglect/cost events BURN lifespan toward it.  LIVE
        burns, each a real trigger in tuipet: the hunger MISTAKE
        (hungerMistakePenalty), the battle ENERGY floor (MinEnergyLifePenalty),
        SICKNESS onset (SickLifeDec -- re-wired 2026-07-22, dropped in the BASIC
        VPET sickness slim), the X-Antibody's one-time price (calcXAntibodyLifeDec),
        and the bonus decay.  DORMANT (systems left in the BASIC VPET slim, so
        nothing fires them; kept as constants, NOT claimed live): Injury / Fatigue
        / WorseMalady / GeriatricFatigue LifeDec.  The discrete caps (20 mistakes /
        20 injuries / 12h starving) are tuipet SAFETY NETS beneath the burns, not
        canon.  Returns True when the pet died this tick."""
        if self._check_death_caps():
            return True
        if self.hunger == 0 and not self.asleep:              # awake-only, like hungerCall()
            self._starve_t = getattr(self, "_starve_t", 0.0) + dt
            if self._starve_t >= 12 * 3600:                   # empty hunger 12h -> death
                self._die("starvation"); return True
        elif self.hunger > 0:
            self._starve_t = 0.0
        # the DSprite sickness (clone rules, 2026-07-17): caught per game-min
        # from filth (never on the road -- countFilth reads 0 away) or from
        # overweight steps; while sick, the clone's per-minute death whisper
        # stands where the classic 6h malady death used to
        if not self.sick:
            p = (SICK_POOP_P if (self.poop > 0
                                 and not getattr(self, "away", False)) else 0.0)
            bw = self._base_weight()
            if bw > 0 and self.weight > bw:
                p += int((self.weight - bw) // (bw * 0.5)) * SICK_OVERWEIGHT_P
            if p > 0 and random.random() < p * dt:
                self.sick = True
                # canon sicken(): ++sickCount THEN setTotalLifespan(-SickLifeDec)
                # (PhysicalState L1846).  This was the headline DEAD burn --
                # sickness from filth/overweight left the Life bar untouched, so
                # it "did nothing" (Joel 2026-07-22).  Re-wired at the live
                # trigger; the SickLifeDec was dropped in the BASIC VPET slim.
                self._burn_life(SICK_LIFE_DEC, f"{self.name}'s illness drains its life")  # noqa: F405
        elif random.random() < DEATH_SICK_P * dt:
            self._die("sickness")
            return True
        # (the old continuous per-second "extra" drain was invented -- canon
        # burns lifespan through the EVENT penalties wired below instead)
        return self._check_old_age()

    # (getEffectEnergyGain / the care-effect tick -- careEffect.csv's whole
    # runtime, whose only shipped effect was the Futon's sleep boost -- left
    # with the staple props: strict-DSprite items, 2026-07-17)

    def _add_filth(self, size):
        """addFilth (poop/filth audit 2026-07-06): below the cap the pile takes
        the next slot; a FULL room UPGRADES the first pile smaller than the new
        mess instead of dropping it (canon's overflow rule -- the old cap
        silently discarded it).  Cap stays Joel's 4 (real-toy match; canon's
        array is 6 -- with its poopCall threshold at 7, provably dead)."""
        if self.poop < POOP_MAX_PILES:
            self.poop += 1
            self.poop_sizes.append(size)
            return
        for i, s in enumerate(self.poop_sizes):
            if s < size:
                self.poop_sizes[i] = size
                break

    def _start_poop(self):
        """DVPet startPoop: drop a sized pile."""
        self._add_filth(self._poop_size())

    # (_advance_bm cut, LOW audit 2026-07-19: the BM-lurch consumables left
    # with the DVPet item system; nothing live called it)

    def _die(self, cause=""):
        self.dead = True
        self.death_cause = cause or self.death_cause   # first cause wins
        self.asleep = False
        self.hatching = False
        self._set_anim("idle", 0)

    def _do_poop(self, backlog=False):
        if self.auto_clean_until and self.world_seconds < self.auto_clean_until:
            self.poop = 0             # the smart potty flushes it (DSprite item)
            self.poop_sizes = []
            return
        """PhysicalState.poop: relief mood bump, weight shed, and a new sized pile
        added to the filth (capped at the _filth array length).  A big BACKLOG
        (gauge still >= bmMax/2 after the poop) makes the pile one size bigger --
        the only source of size-4 piles -- and sheds an extra half weight."""
        self._set_mood(self.mood + POOP_MOOD_INC)                 # PoopMoodInc
        wdec = min(int(self._base_weight() * POOP_WEIGHT_DEC_COEF), POOP_WEIGHT_LIMIT)
        self._set_weight(self.weight - wdec)
        size = self._poop_size()
        if backlog:
            size = min(4, size + 1)
            self._set_weight(self.weight - math.ceil(wdec / 2))
        self._add_filth(size)                    # capped; a full room upgrades a smaller pile

    def _sleep_inc(self):
        """Species sleep-pressure rate (SleepLapseInc: 1 adult / 2 / 9 baby)."""
        return data.load_requirements().get(self.num, {}).get("sleep_lapse_inc", 1)

    def _fall_asleep(self):
        """PhysicalState.sleep(): the pressure clock rolls over -- sleep long
        enough to refill the energy bar (clamped 6..15 game-hours), and the
        next awake stretch is whatever remains of the 24."""
        self.sleep_lapse = 0.0
        self.asleep = True
        self.nap = False
        self._calm_discipline_call()                # bedtime placates the tantrum (canon
        #                                             sleep-onset setDisciplineCall(false))
        self._lights_t = 0.0                        # setAsleep resets _callMinutesLights
        gain = max(1, getattr(self, "_sleep_energy_gain", 3))
        need = math.ceil(max(0, self.max_energy - self.energy) / gain) * 60.0
        self.awake_limit = _clamp(need, MIN_AWAKE_LIMIT, MAX_AWAKE_LIMIT)
        self.sleep_limit = DAY_MINUTES - self.awake_limit
        self._set_anim("yawn", 1.8)

    def _wake(self):
        """setAsleep(false): the wake roll runs on EVERY rise -- natural,
        disturbed or lights-on alike (mood re-audit 2026-07-06; canon disturb()
        funnels through setAsleep(false) unconditionally, so even a grumbled
        wake takes its chances).  A full sleep wakes into the morning tiers; a
        NAP wakes with a +-NapWakeMoodDec swing on 2 rolls of the 5."""
        was_nap = self.nap
        self.asleep = False
        self.nap = False
        self.awake_lapse = 0.0
        self.sleep_limit = DAY_MINUTES - self.awake_limit
        if not self.lights:
            self.lights = True                      # wake: setLights(true)
        wake_anim = "wake"
        r = random.randrange(MORNING_MOOD_CHANCE)
        m = self.current_mood()
        if was_nap:
            if r == 0:
                self._set_mood(self.mood - NAP_WAKE_MOOD_DEC)
                wake_anim = "sad"                    # BadMorning: wakeUp(9)
            elif r == 1:
                self._set_mood(self.mood + NAP_WAKE_MOOD_DEC)
                wake_anim = "happy"                  # GoodMorning: wakeUp(5)
        else:
            # canon wakeUp poses vary with the morning: 7 normal / 5 good /
            # 9 bad / 6 terrible (birthday audit 2026-07-05: it always woke
            # on the plain pose)
            if r == 0:
                self._set_mood(self.mood + BAD_MORNING_MOOD.get(m, -10))
                wake_anim = "sad"                    # BadMorning: wakeUp(9)
            elif r == 1 and m == "Happy":
                self._set_mood(WORST_MORNING_MOOD)
                wake_anim = "surprise"               # TerribleMorning: wakeUp(6)
            elif r == 2:
                self._set_mood(self.mood + GOOD_MORNING_MOOD.get(m, 100))
                wake_anim = "happy"                  # GoodMorning: wakeUp(5)
        self._set_anim(wake_anim, 1.6)

    def _disturbed(self):
        """PhysicalState.disturb(): bothering a sleeper wakes it grumpy.  The
        bookkeeping (count, missed day, postpone, sick risks) only bills REAL
        sleep -- but the mood/spirit dec and the wake land on a NAP too (mood
        re-audit 2026-07-06: canon keeps them outside the !nap guard).  Real
        sleep: nearly-rested (or full energy) it just gets up; otherwise the
        sleep is POSTPONED: it drops back off in DisturbPostpone game-minutes,
        still owing the missed rest."""
        if not self.asleep:
            return "zzz…"
        nap, postponed = self.nap, False
        if not nap:
            self.disturb += 1
            self.mistake_day += 1                   # DisturbanceMissedDayChange
            rested = (self.awake_lapse >= FULL_AWAKE_DISTURB - self.restless * FULL_AWAKE_DISTURB_RESTLESS
                      or self.energy >= self.max_energy)
            if rested:
                self.sleep_lapse = 0.0
            else:
                postponed = True
                postpone = random.randint(*DISTURB_POSTPONE)
                # the lapse regains _sleep_inc per game-min, so a gap of
                # postpone game-minutes is postpone x inc -- the old /inc
                # re-slept a baby (inc 9) in postpone/81 minutes
                self.sleep_lapse = max(0.0, self.sleep_limit - postpone * self._sleep_inc())
                if self._in_sleep_window() is not None:
                    self._bed_postpone_t = float(postpone)   # a line pet re-sleeps by the clock
                # (the missed rest is repaid naturally: _fall_asleep re-sizes the
                # next sleep from the CURRENT energy debt, so nothing is carried)
            # (the rough-waking sickness risks left with the sickness
            # system (BASIC VPET 2026-07-17))
        # DisturbMoodDec{,Restless,NotRestless}: a restless pet WANTED up
        self._set_mood(self.mood - DISTURB_MOOD_DEC.get(self.restless, 10))
        enth = {1: -1, 0: -2, -1: -3}.get(self.restless, -2)   # DisturbEnthusiasmDec*
        self._set_enthusiasm(self.enthusiasm + enth)
        self._wake()                                # setAsleep(false): the wake roll
        if nap:
            return "It stirs from its doze."
        if not postponed:
            return "It grumbles awake."
        self._set_anim("angry", 1.8)                # Sad_Jeering: woken too soon
        return "zzz… mind its sleep!"

    def _special_idle(self):
        """The special-idle families, canon shape (SpriteAnim's 1/1500 rolls;
        personality audit 2026-07-06): the visible TANTRUM while the
        discipline call stands (canon rolls it at 3x the family odds), then
        the personality mood idles -- gated like canon (rested, spirited,
        under-drilled, well) and keyed on the mood TIER: Happy bounces,
        Unhappy fumes, Neutral does nothing.  (The weathering family --
        nice-weather joy, the rain shake, the snow shiver -- left with the
        weather system; BASIC VPET 2026-07-16.)"""
        if getattr(self, "away", False):
            return                                   # no home idles on the road
        # the personality idles: canon gates -- energy >= max/3, spirit >= 0,
        # effort <= limit/2, not unwell (and the TIER, not raw mood)
        if (self.energy < self.max_energy / 3 or self.enthusiasm < 0
                or self.strength > 2):
            return
        m = self.current_mood()
        if m == "Happy":
            self._set_anim(random.choice(("play", "happy")), 2.0)
        elif m in ("Unhappy", "Depressed"):
            self._set_anim(random.choice(("angry", "tantrum")), 2.0)

    def _check_discipline_call(self):
        """A NO-OP: the spontaneous tantrum left with the discipline system."""

    def _tick_auto_care(self, dt):
        """PhysicalState.checkAutoCare, one game-min cadence.  The hourly retainer
        bills first (unpaid -> off duty); then at most one visit per spacing --
        awake: filth > hunger > strength; asleep: filth > a lit room (unless the
        Futon is active, DVPet's !isFuton()).  doAutoCare also walks off duty when
        the pet cannot afford the NEXT visit.  ADAPTATION: DVPet charges when the
        assistant animation ends; a headless tuipet pet applies state (and the
        processAutoCarePrice fee + bond costs) here in the tick, and the app-side
        assistant fx is pure presentation via the assist_event mailbox."""
        if not self.auto_care:
            return
        if getattr(self, "away", False):
            # doAutoCare/checkAutoCare both gate on _isHome: while the pet is
            # OUT (adventuring -- canon's teleport toggles it) the assistant
            # neither bills the retainer nor visits (auto-care audit 2026-07-06)
            return
        self._ac_pay = getattr(self, "_ac_pay", 0.0) + dt
        while self._ac_pay >= AUTO_CARE_PAYMENT_MIN:
            self._ac_pay -= AUTO_CARE_PAYMENT_MIN
            hourly = AUTO_CARE_HOUR_PRICE.get(self.stage, 0)
            if self.bits < hourly:
                self.auto_care = False
                self.assist_note = "The assistant left — the retainer went unpaid."
                return
            self.bits -= hourly
        self._ac_cool = max(0.0, getattr(self, "_ac_cool", 0.0) - dt)
        if self._ac_cool > 0:
            return
        act = None
        if not self.asleep:
            if self.poop > 0:
                act = "clean"
            elif self.hunger == 0:
                act = "feed"
            elif self.strength == 0:
                act = "strength"
        else:
            if self.poop > 0:
                act = "clean"
            elif self.lights:
                act = "lights"
        if act is None:
            return
        price = AUTO_CARE_VISIT_PRICE.get(self.stage, 0)
        if self.bits < price:                            # doAutoCare: can't cover the visit
            self.auto_care = False
            self.assist_note = "The assistant left — it couldn't cover a visit."
            return
        piles, sizes = self.poop, list(self.poop_sizes)
        if act == "clean":
            # Assistant_Clean -> onClean: the standard clean, minus YOUR wash pose
            self.poop, self.poop_sizes = 0, []
            self._set_mood(self.mood + 6)                # CleanMoodInc
            self._filth_t = 0                            # mess handled: the filth call resets
        elif act == "feed":
            # assistantFeed: the AI Food Pill serving -- lands on a sick pet
            # (the plain-meat route refused sickness and BILLED the head-shake;
            # assistant audit 2026-07-19)
            self.feed_meat(assisted=True)
        elif act == "strength":
            self.feed_pill()                             # the tonic tops effort/energy
        elif act == "lights":
            self.lights = False                          # Assistant_Lights -> onLights
        # processAutoCarePrice: the visit fee, and the bond cost of hired care
        self.bits -= price
        self._set_mood(self.mood + AUTO_CARE_MOOD)
        self._set_obedience(self.obedience + AUTO_CARE_OBEDIENCE)
        self._set_enthusiasm(self.enthusiasm + AUTO_CARE_ENTHUSIASM)
        self._ac_cool = AUTO_CARE_VISIT_SPACING
        self.assist_event = (act, piles, sizes)          # the app plays the visit

    def _birthday(self):
        """setTimeToAge's age-up: a mostly-Happy, zero-slip day earns a GOOD
        birthday (+bonus, +lifespan, a Cupcake); a mostly-Unhappy day with slips
        is a BAD one (-bonus, -lifespan, a consolation Candy); anything else is
        normal (a Cookie).  getMajority: a TIE yields no major mood -> normal.
        The slate (missed-days + the mood record) wipes for the new day."""
        counts = self.daily_mood
        best = max(counts.values()) if counts else 0
        tops = [k for k, v in counts.items() if v == best and best > 0]
        major = tops[0] if len(tops) == 1 else None
        if major == "Happy" and self.mistake_day <= MAX_MISTAKE_DAY_BONUS:
            self.lifespan += BONUS_LIFE_INC
            self.evol_bonus += 1
            self.add_item("cupcake")            # a REAL bag treat (TUIPET catalog 2026-07-18)
            self._set_anim("happy", 2.0)                     # Birthday_Good
            self.birthday_note = f"A wonderful day! {self.name} earned a Cupcake!"
        elif major == "Unhappy" and self.mistake_day >= MIN_MISTAKE_DAY_DEC:
            # the life cost rides the birthday's OWN tell (surfaced-burns
            # sweep 2026-07-22) -- a second life note the same tick would
            # just overwrite this flash
            self._burn_life(BONUS_LIFE_DEC)
            if self.evol_bonus > 0:
                self.evol_bonus -= 1
            self.add_item("candy")
            self._set_anim("sad", 2.0)                       # Birthday_Bad
            self.birthday_note = "A rough day cost some life… just a Candy."
        else:
            self.add_item("cookie")
            self._set_anim("happy", 1.5)                     # Birthday_Normal
            self.birthday_note = f"{self.name} is a day older — have a Cookie."
        self.mistake_day = 0
        self.daily_mood = {k: 0 for k in self.daily_mood}

    def _check_gift_call(self, dt):
        """PhysicalState.checkGiftCall + checkGift: every GiftChanceMin game-min,
        a grown, awake, HAPPY pet rolls nextInt(cap - obedience +
        (maxMood - mood) * 0.5 + 70) -- a 0 means it found you a present (the
        better cared-for the pet, the narrower the range).  The pet then calls
        for attention (GiftCall, poses 5/7) until the gift is claimed."""
        self.gift_t += dt
        if self.gift_t < GIFT_CHANCE_MIN:
            return
        self.gift_t = 0.0
        # the Happy-tier gate and the mood term left with the mood system
        # (BASIC VPET 2026-07-16): a WELL pet (not unwell) can find a present,
        # and obedience alone narrows the roll
        if (self.gift or self.asleep or self.stage in ("Egg", "Fresh", "InTraining")
                or self.current_mood() == "Unhappy"
                or getattr(self, "away", False)):   # checkGiftCall gates on _isHome:
            return                                  # presents are found AT HOME
        chance = int(OBEDIENCE_REFUSAL_CAP - self.obedience + GIFT_CHANCE_FACTOR)
        if chance > 0 and random.randrange(chance) == 0:
            self.gift = self._pick_gift()

