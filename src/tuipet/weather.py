"""Weather & temperature — a port of DVPet's PhysicalState weather model.

DVPet drives weather from a per-habitat config: each season sets a base day
temperature range, the weather type subtracts a temp factor, time of day
subtracts another, and the pet's per-species ideal band turns the resulting
temperature into mood / sickness / energy effects. We use DVPet's default
Habitat constants and its checkWeather/calcWeather state machine verbatim.

The one deliberate deviation: WEATHER_CHANCE is scaled down from DVPet's 250
(checked every 10 in-game minutes) so precipitation actually shows up on
tuipet's compressed clock. The transition algorithm itself is unchanged.
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
WEATHER_CHECK_SEC = 18.0
TEMP_RATE = 4.0            # temperature lapses this fast toward its target
IDEAL_TEMP_MOOD_SEC = 12.0
BAD_TEMP_SICK_SEC = 8.0
BAD_TEMP_SICK_CHANCE = 0.015


def _calc_weather(weather, warm):
    """calcWeather: pick the rain vs snow variant by warmth (dayTemp>freezing)."""
    if weather in ("Snowing", "Raining"):
        return "Raining" if warm else "Snowing"
    if weather in ("HeavySnow", "HeavyRain"):
        return "HeavyRain" if warm else "HeavySnow"
    return "Drizzling" if warm else "LightSnow"


def next_weather(weather, season, day_temp, hab):
    """checkWeather: DVPet's weather transition state machine, per habitat."""
    chance = hab["weather_chance"]
    change = hab["weather_change"] or 100
    if chance <= 0:
        return "Clear"
    season_mod = hab["precip_mod"][season]
    cloud_mod = hab["cloud_mod"] if weather == "Cloudy" else 0
    warm = day_temp > FREEZING_TEMP
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
