"""Weather & temperature — a port of DVPet's PhysicalState weather model.

DVPet drives weather from a per-habitat config: each season sets a base day
temperature range, the weather type subtracts a temp factor, time of day
subtracts another, and the pet's per-species ideal band turns the resulting
temperature into mood / sickness / energy effects. We use DVPet's default
Habitat constants and its checkWeather/calcWeather state machine verbatim.

Canon re-audit 2026-07: every constant here matches config.csv column 1
verbatim (WeatherChangeChance IS 7 -- an older comment claimed a scaled-down
deviation that never existed).  The transition machine is line-for-line.
"""
from __future__ import annotations
import random

# --- DVPet config.csv constants ---
MAX_TEMP = 100
FREEZING_TEMP = 32
UPPER_IDEAL = 30           # how far above the ideal band before "too hot"
LOWER_IDEAL = 30           # ...and below before "too cold"
IDEAL_TEMP_INC = 3         # mood gained per check when comfortable
IDEAL_TEMP_DEC = 3         # mood lost per check when too hot/cold
WEATHER_CHANGE_CHANCE = 7
CLOUDY_COEFFICIENT = 0.9

_WEATHER_TEMP_FACTOR = {   # Config *TempFactor: weather lowers temperature
    "Cloudy": 2, "Drizzling": 3, "Raining": 5, "LightSnow": 5,
    "Snowing": 7, "HeavyRain": 7, "HeavySnow": 10,
}
NIGHT_TEMP_FACTOR = 10
MORNING_TEMP_FACTOR = 3

# Habitat climate now comes from each habitat record (data.load_habitats); these
# functions take a `hab` dict so weather varies by where the pet lives.
SEASONS = ["Spring", "Summer", "Fall", "Winter"]
RAIN = {"Raining", "Drizzling", "HeavyRain"}
SNOW = {"Snowing", "LightSnow", "HeavySnow"}
PRECIP = RAIN | SNOW

# --- tuipet clock cadences (seconds) ---
# TWO deliberate scale families (the filth-arc doctrine): ENVIRONMENT pacing
# (weather transitions, temp drift) rides the x60 wall-clock scale so skies
# don't strobe; STAT lapses ride 1 game-min == 1s like the mood/obedience
# family.  IdealTempMoodMin 29 is a MOOD lapse -- canon runs it in minLapse
# right beside moodLapse -- so it belongs to the stat family (weather audit
# 2026-07-06: the old 1800s ran it on the environment scale, making climate
# comfort 62x weaker than canon's design; a comfortable compatible home now
# SUSTAINS happiness against the Happy decay, an unfit one drains it).
# WeatherCheckMin=10 (config.csv): canon rolls the weather every 10 GAME
# MINUTES.  tuipet's clock maps one game minute onto one real second (a game
# day = DAY_LENGTH 1440s = 1440 game min), so that is 10 REAL SECONDS.  We
# shipped 600.0 -- "10 minutes" converted with REAL minutes, 60x too rare:
# the roll fired 2.4x a game day instead of 144x, and the observed result was
# ZERO weather changes across a full day.  The whole weather system (precip
# art, the huddle/shield poses, the storm tints, the temp factors) was
# effectively dead.  Same unit bug as TEMP_RATE (weather audit 2026-07-13);
# IDEAL_TEMP_MOOD_SEC=29 was always right, which is what exposed the pattern.
WEATHER_CHECK_SEC = 10.0    # == canon's 10 game minutes
# TempLapseMin=1 (config.csv, all three columns): canon moves the temperature
# by ONE unit per GAME MINUTE toward its target.  tuipet's clock maps a game
# day onto DAY_LENGTH=1440s, i.e. one game minute == one real second, so the
# canon-faithful rate is 1.0/sec.  We shipped 0.05 -- TWENTY TIMES too slow:
# a season lasts one game day (24 real min) but a winter->summer climb
# (0->70) took ~23 min, so the reading NEVER caught up to the season.  Joel
# saw it as "18 degrees in the summer time?" (bug report 2026-07-13); the
# same lag muted every night chill and every storm.
TEMP_RATE = 1.0             # units/sec == DVPet's 1 per game minute (TempLapseMin)
IDEAL_TEMP_MOOD_SEC = 29.0  # IdealTempMoodMin 29 (stat family)
# (no bad-temp/incompatible-habitat sick cadence: both checks are data-dead in
# the classic column -- see pet._temperature_effects)


def _calc_weather(weather, warm):
    """calcWeather: pick the rain vs snow variant by warmth (dayTemp>freezing)."""
    if weather in ("Snowing", "Raining"):
        return "Raining" if warm else "Snowing"
    if weather in ("HeavySnow", "HeavyRain"):
        return "HeavyRain" if warm else "HeavySnow"
    return "Drizzling" if warm else "LightSnow"


def next_weather(weather, season, day_temp, hab, feel_temp=None):
    """checkWeather: DVPet's weather transition state machine, per habitat.

    `feel_temp` is the temperature the PLAYER SEES (the pet's current
    reading, which drifts slowly and can sit pinned under a futon) -- the
    rain-vs-snow pick follows it, so the sky never snows over a 46-degree
    display (bug report 2026-07-13, "light snow at 46?").  Each roll
    re-picks the variant, so precip flips rain<->snow exactly when the
    visible temperature crosses freezing."""
    chance = hab["weather_chance"]
    change = hab["weather_change"] or 100
    if chance <= 0:
        return "Clear"                       # no weather frame -> no weather
    season_mod = hab["precip_mod"][season]
    cloud_mod = hab["cloud_mod"] if weather == "Cloudy" else 0
    warm = (day_temp if feel_temp is None else feel_temp) > FREEZING_TEMP
    if weather in ("Clear", "Cloudy"):
        prob = random.randint(0, chance - 1) + season_mod + cloud_mod
        if prob > chance - 1:
            if weather == "Clear":
                return "Cloudy" if random.randint(0, 1) == 1 else _calc_weather(weather, warm)
            return _calc_weather(weather, warm)
        p2 = random.randint(0, change - 1) + season_mod
        return "Cloudy" if p2 >= change * CLOUDY_COEFFICIENT else "Clear"
    # already precipitating: escalate, ease, or clear
    prob = random.randint(0, change - 1) - season_mod
    weather = _calc_weather(weather, warm)
    if prob > change * 0.5:
        p = random.randint(0, WEATHER_CHANGE_CHANCE - 1)
        if weather in ("Drizzling", "LightSnow"):
            if p <= 2:
                return "Cloudy"
            if p == 3:
                return "Clear"
            if p <= 6:
                return "Raining" if weather == "Drizzling" else "Snowing"
        elif weather in ("Raining", "Snowing"):
            if p == 0:
                return "Cloudy"
            if p <= 4:
                return "Drizzling" if weather == "Raining" else "LightSnow"
            if p <= 6:
                return "HeavyRain" if weather == "Raining" else "HeavySnow"
        elif weather in ("HeavyRain", "HeavySnow") and p < 4:
            return "Raining" if weather == "HeavyRain" else "Snowing"
    return weather


def adjusted_day_temp(day_temp, weather, phase, hab):
    """getAdjustedDayTemp: day temp minus weather and habitat time-of-day factors.

    tuipet's dawn maps to DVPet's Morning; day/dusk have no time factor."""
    t = day_temp - _WEATHER_TEMP_FACTOR.get(weather, 0)
    if phase == "night":
        t -= hab["night_tf"]
    elif phase == "dawn":
        t -= hab["morning_tf"]
    return max(0, t)


def season_for_day(day_index):
    return SEASONS[day_index % len(SEASONS)]
