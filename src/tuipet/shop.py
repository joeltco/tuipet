"""The shop: a fixed catalog of priced items (the DSprite item system,
cloned from the v0.4.x rebuild -- BASIC VPET 2026-07-16).

Every priced entry in vitems.json is on the shelf, grouped by its own
category column; buying moves it into the bag at face value; the bag can
sell it back for half.  Effects live in Pet.use_item — the token text here
mirrors those exact effects so the shelf, the bag and the belly can never
disagree.  The DVPet rolled-slot/town-hours shop machine is retired; the
town counters serve the same catalog.  The digitama-licence shelf was cut
2026-07-17 ("i never wanted egg licenses"): eggs unlock by condition only,
like the real devices -- the shop sells goods, never digitama.
"""
from __future__ import annotations
import random
from functools import lru_cache
from math import gcd as _gcd
from typing import NamedTuple

from . import data


class Item(NamedTuple):
    """One catalog entry, with its fields NAMED (items refactor P1,
    2026-07-23).  The authored table below stays a plain aligned tuple
    literal -- it reads better as a table and the churn of 37 keyword
    calls buys nothing -- but every CONSUMER now says `.category`
    instead of `v[3]`, which was the actual complaint (scoping board
    P-A).

    Still a tuple, so indexing keeps working.  The first SIX fields are
    the authored contract and must never be reordered -- P2 appended to
    the end, and anything later appends further.

    P2 (2026-07-23) added the last three:

    * `touches` -- the LIVE pet stats this item's `use_item` handler
      moves DIRECTLY.  This is the yardstick for "redo them all to fit
      everything we got going on" (plan §2 goal 2): a pin walks it and
      fails if an item aims at a stat that is dormant or does not exist.
      Side channels are deliberately NOT listed -- `_set_energy` bills
      obedience when a drop lands in the red, and `_disturbed()` bills a
      care mistake, but those belong to those helpers, not to the item.
    * `where` -- "home" (usable from the bag) or "road" (spent on the
      march; the home bag refuses it).  Replaces reading intent out of
      refusal STRINGS (scoping board P-F).
    * `tier` -- rarity slot.  DECLARED, NOT POPULATED: it is the hook the
      distribution arc attaches to (plan §7), and populating it here
      would be inventing an economy nobody has ruled on."""
    name: str
    icon: str
    price: int | None       # None = never sold (grant-only treats)
    category: str
    effect: str             # the text mirroring use_item (see plan §1g)
    flavor: str
    touches: tuple = ()     # LIVE pet stats the handler moves directly
    where: str = "home"     # "home" | "road"
    tier: str | None = None  # distribution arc populates this


# ============================ THE TUIPET CATALOG ============================
# Authored 2026-07-18 (Joel: "we can pretty much make anything we want. i
# need you to make tuipet items" / "you can make the items whatever you
# want using the sprites").  The law of the set: DSprite is the mechanics
# GRAMMAR, DVPet is the ART -- every entry wears a real DVPet atlas strip
# (all 59 foods + 84 items carry 4-frame rips; zero placeholders), and
# every effect lands on a meter that is LIVE today.  vitems.json stays a
# pristine rip: it now feeds only the 11 Digimentals; the consumable shelf
# is THIS table.  price None = never sold (birthday-only treats).
# key: (name, icon, price, category, effect-text mirroring use_item, tagline)
# -- authored positionally, then wrapped into `Item` (P1) so every reader
# gets named fields.  Keep the alignment: this table is meant to be read.
_AUTHORED = {
    # ---- FOOD (eaten on the LCD through their own 4-frame strips) ----------
    "fish":            ("Fish",            "f:1",  50,   "Feed", "hunger +1", "the everyday catch"),
    "vegetable":       ("Vegetable",       "f:3",  150,  "Feed", "hunger +1 · weight -1", "crunchy diet fare"),
    "tuna":            ("Tuna",            "f:14", 400,  "Feed", "hunger +2 · energy +1", "a hearty catch"),
    "cake":            ("Cake",            "f:6",  300,  "Feed", "hunger +1 · energy +2 · weight +2", "a celebration slice"),
    "cheese_burger":   ("Cheese burger",   "f:57", 50,   "Feed", "fills the belly · weight +4", "greasy, regrettable"),
    "giga_meal":       ("Giga Meal",       "f:28", 800,  "Feed", "fills belly · energy +4 · weight +6", "a feast fit for a Mega"),
    "steak":           ("Steak",           "f:8",  2000, "Feed", "fills belly · 12h satiety", "the premium table"),
    "poison_mushroom": ("Poison Mushroom", "f:13", 200,  "Feed", "DO NOT FEED", "it does look delicious"),
    "cupcake":         ("Cupcake",         "f:55", None, "Feed", "hunger +1 · energy +1", "a birthday's reward"),
    "cookie":          ("Cookie",          "f:54", None, "Feed", "hunger +1 · energy +1", "a birthday's treat"),
    "candy":           ("Candy",           "f:7",  None, "Feed", "hunger +1 · energy +1", "a consolation sweet"),
    # ---- MEDICINE (the two ailments: sick and injured) ----------------------
    "vitamin":         ("Vitamin",         "f:5",  500,  "Cure", "effort FULL · injury guard", "effort in a capsule"),
    # (the BANDAGE's FINAL door, 2026-07-26: after one era as the F menu's
    #  third row (R3) and one afternoon as a 300b shelf item (v0.5.277,
    #  tag-only, never published), Joel settled it -- "remove bandage as an
    #  item alltogether and just add an h heal hotkey".  The injury cure is
    #  the H key: a free care BUTTON with the i:80 rip and the Bandaging
    #  show; the canon time-heal (injLapse) stays underneath.  No shelf
    #  entry may ever sell either ailment cure again.)
    "miracle_drink":   ("Miracle Drink",   "f:18", 7777, "Cure", "wipes the WHOLE slate · energy +12", "the expensive absolution"),
    # ---- CARE (upkeep: sleep, lights, filth, the mistake slate) -------------
    "sleeping_pill":   ("Sleep Pill",      "f:34", 300,  "Rest", "sleep now", "lights out, no argument"),
    "caffeine_pill":   ("Caffeine Pill",   "f:38", 300,  "Rest", "bedtime pushed later", "tonight runs long"),
    "music_player":    ("Music Player",    "i:9",  300,  "Rest", "wake now, no grudge", "a gentle waking song"),
    "textbook":        ("Textbook",        "i:0",  1500, "Manners", "obedience +20", "study makes a good pupil"),
    "port_potty":      ("Port. Potty",     "i:83", 2000, "Rest", "clean + auto-clean 24h", "it cleans itself"),
    # ---- TRAINING (the body: effort, weight, drills) ------------------------
    "energy_drink":    ("Energy Drink",    "f:17", 200,  "Rest", "energy to FULL", "instant pep"),
    "slim_drink":      ("Slim Drink",      "f:23", 100,  "Drill", "weight -10", "the crash diet"),
    "dumbbell":        ("Dumbbell",        "i:7",  300,  "Drill", "training +10", "reps in a box"),
    # ---- EVOLUTION (the gates: growth, locks, X, DNA) -----------------------
    "grow_capsule":    ("Grow Capsule",    "i:78", 500,  "Evolve", "growth: a quarter of this stage", "time in a bottle"),
    "anti_evo_chip":   ("Anti-Evo Chip",   "f:32", 1000, "Evolve", "toggle evolution lock", "holds this form"),
    "x_antibody":      ("X-Antibody",      "i:79", 2000, "Evolve", "the X-Antibody takes hold", "the X factor"),
    "dna_crystal":     ("DNA Crystal",     "i:35", 1500, "Power", "+10 own-Field DNA banked", "a Field's worth of code"),
    # ---- THE ATTRIBUTE CHIPS (items refactor P6, 2026-07-23) ---------------
    # The one LIVE lever with no purchasable support: Va/D/Vi powers gate
    # hundreds of evolution rows (>10 / >20 / >25 / >50) and the only ways to
    # move them were winning battles (+1 each) and the inheritance-only
    # Digimemory.  Canon rows, canon prices, canon +15/+30 -- a chip is worth
    # about fifteen wins.  Uncapped, exactly like the win path they shortcut.
    "vaccine_chip":    ("Vaccine Chip",    "f:10", 1500, "Power", "Vaccine power +15", "a shot of order"),
    "data_chip":       ("Data Chip",       "f:11", 1500, "Power", "Data power +15", "a shot of logic"),
    "virus_chip":      ("Virus Chip",      "f:12", 1500, "Power", "Virus power +15", "a shot of chaos"),
    "vaccine_chip_g":  ("Vaccine Chip G",  "f:20", 3000, "Power", "Vaccine power +30", "the golden dose"),
    "data_chip_g":     ("Data Chip G",     "f:21", 3000, "Power", "Data power +30", "the golden dose"),
    "virus_chip_g":    ("Virus Chip G",    "f:22", 3000, "Power", "Virus power +30", "the golden dose"),
    "omni_chip_g":     ("Omni Chip G",     "f:33", 8000, "Power", "all three powers +30", "every colour at once"),
    # ---- LEGACY (death and inheritance -- NOT medicine, which is why the
    # old "Medical" name had to go: it never held a med) ---------------------
    # i:64 (the notched-square disk glyph): i:32 is DVPet's own Digimemory
    # sprite, and two catalog entries sharing an icon broke key_for_icon
    # (consistency audit 2026-07-21) -- the floppy wears its own rip now
    "revive_floppy":   ("Rev. Floppy",     "i:64", 2500, "Cure", "raise the dead", "one more chance"),
    "digimemory":      ("Digimemory",      "i:32", None, "Evolve", "the ancestor's Va·D·Vi", "its data lives on"),
    # ---- PLAY (the shows the engine already ships; small LIVE stat dials:
    # exercise sheds weight, couch time buys energy at a weight price) --------
    "ball":            ("Ball",            "i:3",  100,  "Drill", "play! weight -1", "a grand kickabout"),
    "skateboard":      ("Skateboard",      "i:6",  500,  "Drill", "ride! weight -2 · energy -1", "shred the living room"),
    "xylophone":       ("Xylophone",       "i:63", 800,  "Rest", "a recital · DP +1", "music hath charms"),
    "video_game":      ("Video Game",      "i:65", 600,  "Rest", "couch time · DP +1 · weight +1", "one more level…"),
    "television":      ("Television",      "i:10", 1000, "Rest", "deep couch · DP +2 · weight +1", "glued to the screen"),
    # ---- ADVENTURE (the road's own shelf -- cleared maps open it) -----------
    "town_transport":     ("Town Transport",   "i:29", 500,  "Road", "on the road: T-warp to a town + rest", "a Birdramon ride"),
    "disaster_transport": ("Disaster Transp.", "i:30", 250,  "Road", "on the road: T-dash to the boss + ambush", "a Garudamon ride"),
    "life_recovery":      ("Life Recovery",    "i:27", 1000, "Road", "restore adventure lives on the road", "a second wind"),
    # ======================= THE EXPANSION (2026-07-26) =====================
    # Joel: "bring in all 99 unused items ... spread out ... your call".
    # Every row below is an authored source row (foods.csv / items.csv):
    # real rip, real name, real DefaultPrice, stats off the authored columns
    # (weight = Calories // 2 for new rows; Mood/Enthusiasm/Stress stay
    # dormant).  price None = never sold (source price 0): those rows are
    # EARNED -- drops, digs, gifts, capsules, cup prizes.  The 11 Digimentals
    # (i:15-25) are NOT here: they live on the crest shelf (one door), and
    # i:35 "Blue Crystal" stays out (its rip is the shipped dna_crystal's).
    # Board file: ITEM_EXPANSION_2026_07_26.md.
    "meat":            ("Meat",                "f:0",  None,  "Feed", "hunger +1 · weight +2", "the classic slab, to go"),
    "fruit":           ("Fruit",               "f:2",  None,  "Feed", "hunger +1 · obedience -1", "sweet, and a little spoiling"),
    "bread":           ("Bread",               "f:24", 100,   "Feed", "hunger +1 · weight +1", "a warm honest loaf"),
    "cheese":          ("Cheese",              "f:49", 200,   "Feed", "hunger +1 · weight +2", "aged to please"),
    "broccoli":        ("Broccoli",            "f:51", 100,   "Feed", "hunger +1 · obedience +2", "eat it. no arguments."),
    "orange":          ("Orange",              "f:42", 300,   "Feed", "hunger +1 · obedience -1", "zest for the road"),
    "honey":           ("Honey",               "f:31", 500,   "Feed", "hunger +1 · energy +1 · obedience -5 · weight +1", "spoils them rotten"),
    "chocolate_egg":   ("Chocolate Egg",       "f:58", 300,   "Feed", "hunger +1 · weight +1 · a TOY inside", "a toy hides inside"),
    "burnt_food":      ("Burnt Food",          "f:56", None,  "Feed", "hunger +1 · saps effort · obedience +5", "somebody wasn't watching"),
    "yellow_pepper":   ("Yellow Pepper",       "f:35", 100,   "Feed", "hunger +1 · Virus power +1 · obedience +1", "a spark of chaos"),
    "green_pepper":    ("Green Pepper",        "f:36", 100,   "Feed", "hunger +1 · Data power +1 · obedience +1", "a spark of logic"),
    "red_pepper":      ("Red Pepper",          "f:37", 100,   "Feed", "hunger +1 · Vaccine power +1 · obedience +1", "a spark of order"),
    "med":             ("Med",                 "f:4",  None,  "Cure", "cures sickness", "the field pill"),
    "elixir":          ("Elixir",              "f:15", 2000,  "Cure", "NO care slips for a day", "absolution in a bottle"),
    "vitamin_g":       ("Vitamin G",           "f:16", 2000,  "Cure", "effort FULL · CANNOT be wounded for a day", "the golden ward"),
    # THE CURE LADDER (2026-07-27, Joel: "fill the cure hole").  care_mistakes
    # is the deadliest meter in the game -- 21 reads, it gates evolutions and
    # it KILLS -- and until now exactly one item touched it, at 7777b.  These
    # two give the slate a ladder instead of a single luxury.  Both wear art
    # freed by the same day's cuts: nothing is drawn, ever.
    "cold_compress":   ("Cold Compress",       "i:67", 2000,  "Cure", "ONE care slip erased · costs energy", "relief, the hard way"),
    "gold_pill":       ("Gold Pill",           "f:19", 10000, "Cure", "energy FULL · nothing tires it for a day", "vitality, gilded"),
    "supplement":      ("Supplement",          "f:25", 100,   "Drill", "effort FULL · obedience +5 · weight +1", "discipline in a dose"),
    "food_pill":       ("Food Pill",           "f:41", 100,   "Feed", "fills belly · obedience +5 · weight +3", "a meal, compressed"),
    "ai_supplement":   ("AI Supplement",       "f:43", None,  "Drill", "effort +1", "the assistant's own blend"),
    "ai_food_pill":    ("AI Food Pill",        "f:44", None,  "Cure", "hunger +1", "the assistant's ration"),
    "hp_chip":         ("HP Chip",             "f:26", 1500,  "Power", "all three powers +5", "vitality etched in silicon"),
    "hp_chip_g":       ("HP Chip G",           "f:27", 3000,  "Power", "all three powers +10", "the golden constitution"),
    "hedonism_101":    ("Hedonism 101",        "i:1",  2000,  "Manners", "manners OBLITERATED · DO NOT STUDY", "the forbidden syllabus"),
    "book":            ("Book",                "i:2",  1000,  "Manners", "obedience +5 · manners HOLD for a day", "a well-thumbed guide"),
    "board_game":      ("Board Game",          "i:5",  2000,  "Power", "Vaccine power -15 · Data power +15 · obedience +5", "logic beats order"),
    "computer_game":   ("Computer Game",       "i:8",  2000,  "Power", "Virus power -15 · Data power +15", "logic tames chaos"),
    "trampoline":      ("Trampoline",          "i:13", 2500,  "Drill", "bounce! effort +1 · weight -1", "gravity, negotiable"),
    "x_program":       ("X-Program Sample",    "i:14", None,  "Evolve", "belly + effort emptied · the X takes hold", "survive it, transcend"),
    "zone_transport":  ("Zone Transport",      "i:28", 750,   "Road", "on the road: a safe T-lift up the road", "a Birdramon lift"),
    "continent_transport":("Continent Transport", "i:31", 1000,  "Road", "on the road: rest to half tank, anywhere", "a Whamon camp"),
    "digitron":        ("Digitron",            "i:33", 6000,  "Evolve", "a dark evolution, if one answers", "a mysterious dark fluid"),
    "horn_helmet":     ("Horn Helmet",         "i:34", 3000,  "Evolve", "evolve: Kabuterimon, if the body is ready", "the beetle's crown"),
    "grey_claws":      ("Grey Claws",          "i:36", 3000,  "Evolve", "evolve: Greymon, if the body is ready", "the tyrant's grip"),
    "water_bottle":    ("Water Bottle",        "i:37", 3000,  "Evolve", "evolve: Seadramon, if the body is ready", "the serpent's sea"),
    "torn_tatter":     ("Torn Tatter",         "i:38", 3000,  "Evolve", "evolve: Bakemon, if the body is ready", "the ghost's shroud"),
    "white_wings":     ("White Wings",         "i:39", 3000,  "Evolve", "evolve: Angemon, if the body is ready", "the angel's lift"),
    "black_wings":     ("Black Wings",         "i:40", 3000,  "Evolve", "evolve: Devimon, if the body is ready", "the fallen's lift"),
    "metal_armor":     ("Metal Armor",         "i:41", 3000,  "Evolve", "evolve: MetalMamemon, if the body is ready", "the mercenary's shell"),
    "flaming_wings":   ("Flaming Wings",       "i:42", 3000,  "Evolve", "evolve: Birdramon, if the body is ready", "the firebird's pinions"),
    "toy_oven":        ("Toy Oven",            "i:66", 500,   "Feed", "fresh-baked! hunger -1 (makes room)", "smells like seconds"),
    "capsule_a":       ("Capsule",             "i:68", 100,   "Treasure", "open: a surprise item (finer on festivals)", "the corner-shop gacha"),
    "capsule_b":       ("Blue Capsule",             "i:69", None,  "Treasure", "open: an uncommon surprise", "a cut above the counter"),
    "capsule_c":       ("Green Capsule",             "i:70", None,  "Treasure", "open: an uncommon surprise", "road-found, road-worthy"),
    "capsule_d":       ("Red Capsule",             "i:72", None,  "Treasure", "open: a rare surprise", "warm to the touch"),
    "capsule_e":       ("Silver Capsule",             "i:73", None,  "Treasure", "open: a rare surprise", "heavier than it looks"),
    "capsule_f":       ("Gold Capsule",             "i:74", None,  "Treasure", "open: a fine surprise", "it practically hums"),
    "capsule_g":       ("Prism Capsule",             "i:75", None,  "Treasure", "open: a fine surprise", "light bends around it"),
    "capsule_h":       ("Royal Capsule",             "i:76", None,  "Treasure", "open: the finest surprise", "festival stock, the good shelf"),
    "prank_capsule_a": ("Rattling Capsule",             "i:71", None,  "Treasure", "open: a surprise. probably fine.", "something inside is ALIVE"),
    "prank_capsule_b": ("Hissing Capsule",             "i:77", None,  "Treasure", "open: a surprise. definitely fine.", "do you smell smoke?"),
    "futon":           ("Futon",               "i:81", 1000,  "Rest", "the next daytime doze rests to FULL", "deepest daytime sleep"),
    "human_fire_spirit":("Human Fire Spirit",   "i:43", None,  "Evolve", "a spirit evolution, if one answers", "an elemental inheritance"),
    "human_light_spirit":("Human Light Spirit",  "i:44", None,  "Evolve", "a spirit evolution, if one answers", "an elemental inheritance"),
    "human_ice_spirit":("Human Ice Spirit",    "i:45", None,  "Evolve", "a spirit evolution, if one answers", "an elemental inheritance"),
    "human_wind_spirit":("Human Wind Spirit",   "i:46", None,  "Evolve", "a spirit evolution, if one answers", "an elemental inheritance"),
    "human_thunder_spirit":("Human Thndr. Spirit", "i:47", None,  "Evolve", "a spirit evolution, if one answers", "an elemental inheritance"),
    "human_earth_spirit":("Human Earth Spirit",  "i:48", None,  "Evolve", "a spirit evolution, if one answers", "an elemental inheritance"),
    "human_water_spirit":("Human Water Spirit",  "i:49", None,  "Evolve", "a spirit evolution, if one answers", "an elemental inheritance"),
    "human_wood_spirit":("Human Wood Spirit",   "i:50", None,  "Evolve", "a spirit evolution, if one answers", "an elemental inheritance"),
    "human_metal_spirit":("Human Metal Spirit",  "i:51", None,  "Evolve", "a spirit evolution, if one answers", "an elemental inheritance"),
    "human_dark_spirit":("Human Dark Spirit",   "i:52", None,  "Evolve", "a spirit evolution, if one answers", "an elemental inheritance"),
    "beast_fire_spirit":("Beast Fire Spirit",   "i:53", None,  "Evolve", "a spirit evolution, if one answers", "an elemental inheritance"),
    "beast_light_spirit":("Beast Light Spirit",  "i:54", None,  "Evolve", "a spirit evolution, if one answers", "an elemental inheritance"),
    "beast_ice_spirit":("Beast Ice Spirit",    "i:55", None,  "Evolve", "a spirit evolution, if one answers", "an elemental inheritance"),
    "beast_wind_spirit":("Beast Wind Spirit",   "i:56", None,  "Evolve", "a spirit evolution, if one answers", "an elemental inheritance"),
    "beast_thunder_spirit":("Beast Thndr. Spirit", "i:57", None,  "Evolve", "a spirit evolution, if one answers", "an elemental inheritance"),
    "beast_earth_spirit":("Beast Earth Spirit",  "i:58", None,  "Evolve", "a spirit evolution, if one answers", "an elemental inheritance"),
    "beast_water_spirit":("Beast Water Spirit",  "i:59", None,  "Evolve", "a spirit evolution, if one answers", "an elemental inheritance"),
    "beast_wood_spirit":("Beast Wood Spirit",   "i:60", None,  "Evolve", "a spirit evolution, if one answers", "an elemental inheritance"),
    "beast_metal_spirit":("Beast Metal Spirit",  "i:61", None,  "Evolve", "a spirit evolution, if one answers", "an elemental inheritance"),
    "beast_dark_spirit":("Beast Dark Spirit",   "i:62", None,  "Evolve", "a spirit evolution, if one answers", "an elemental inheritance"),
}

# ---------------------------------------------------------------------------
# WHAT EACH ITEM ACTUALLY MOVES (items refactor P2, 2026-07-23)
#
# Read out of petcare.use_item's handlers one by one -- NOT inferred from
# the effect text, which is the very thing that can drift (plan §1g).
# Every name here is a real Pet dataclass field; test_catalog_touches.py
# proves that and proves none of them is a DORMANT stat.
#
# Omitted on purpose: the indirect billing inside shared helpers.
# `_set_energy` stings obedience when a drop lands in the red and
# `_disturbed()` books a care mistake -- those are the helpers' effects,
# not the item's, and listing them would make every energy item look like
# a discipline item.
_TOUCHES = {
    # ---- FOOD ----
    "fish": ("hunger",),
    "vegetable": ("hunger", "weight"),
    "tuna": ("hunger", "energy"),
    "cake": ("hunger", "energy", "weight"),
    "cupcake": ("hunger", "energy"),
    "cookie": ("hunger", "energy"),
    "candy": ("hunger", "energy"),
    # (care_mistakes dropped 2026-08-01, "canonize all care mistakes": the
    #  Bandai record names OVERFEEDING as explicitly NOT a care mistake)
    "cheese_burger": ("hunger", "weight"),
    "giga_meal": ("hunger", "energy", "weight"),
    "steak": ("hunger", "full_until"),
    "poison_mushroom": ("dead",),          # _die(): the one lethal entry
    # ---- CARE ----
    "energy_drink": ("energy",),
    "slim_drink": ("weight",),
    "vitamin": ("strength", "vitamin_lapse"),
    "miracle_drink": ("care_mistakes", "mistake_day", "energy"),
    "sleeping_pill": ("asleep", "lights", "nap"),
    # BOTH channels, because it really does use both (item sweep
    # 2026-07-24: a line pet -- every hatch -- pushes bedtime through the
    # grace clock, and only a pressure pet moves sleep_lapse.  Declaring
    # one and moving the other is exactly the drift `touches` exists to
    # catch, and the behavioural pin now catches it.)
    "caffeine_pill": ("sleep_lapse", "_bed_postpone_t"),
    "music_player": ("asleep", "lights", "nap", "awake_lapse"),
    "textbook": ("obedience",),
    "port_potty": ("poop", "poop_sizes", "auto_clean_until"),
    # ---- GROWTH ----
    "dumbbell": ("stage_trainings",),
    "grow_capsule": ("stage_seconds",),
    "anti_evo_chip": ("evo_blocked",),
    "x_antibody": ("x_antibody",),
    "dna_crystal": ("dna_owned",),
    "vaccine_chip": ("vaccine",),
    "data_chip": ("data_power",),
    "virus_chip": ("virus",),
    "vaccine_chip_g": ("vaccine",),
    "data_chip_g": ("data_power",),
    "virus_chip_g": ("virus",),
    "omni_chip_g": ("vaccine", "data_power", "virus"),
    "revive_floppy": ("dead",),
    "digimemory": ("vaccine", "data_power", "virus", "digimemory"),
    # ---- TOYS ----
    "ball": ("weight",),
    "skateboard": ("weight", "energy"),
    "xylophone": ("dp",),
    "video_game": ("dp", "weight"),
    "television": ("dp", "weight"),
    # ---- ADVENTURE ----
    # Empty by design: from the HOME bag these three only refuse.  Their
    # real work is adventure-run state (the march's location, its lives),
    # which is not Pet state and does not belong in this namespace.
    # `where="road"` is what carries that meaning.
    "town_transport": (),
    "disaster_transport": (),
    "life_recovery": (),
    # ---- THE EXPANSION (2026-07-26): read out of the new handlers ----------
    "meat": ('hunger', 'weight'),
    "fruit": ('hunger', 'obedience'),
    "bread": ('hunger', 'weight'),
    "cheese": ('hunger', 'weight'),
    "broccoli": ('hunger', 'obedience'),
    "orange": ('hunger', 'obedience'),
    "honey": ('hunger', 'energy', 'obedience', 'weight'),
    "chocolate_egg": ('hunger', 'weight'),
    "burnt_food": ('hunger', 'strength', 'obedience'),
    "yellow_pepper": ("hunger", "obedience", "virus"),
    "green_pepper": ("hunger", "obedience", "data_power"),
    "red_pepper": ("hunger", "obedience", "vaccine"),
    "med": ('sick',),
    "elixir": ('pardon_lapse',),
    "vitamin_g": ('strength', 'ward_lapse'),
    "cold_compress": ('care_mistakes', 'energy'),
    "gold_pill": ('energy', 'tonic_lapse'),
    "supplement": ('strength', 'obedience', 'weight'),
    "food_pill": ('hunger', 'obedience', 'weight'),
    "ai_supplement": ('strength',),
    "ai_food_pill": ('hunger',),
    "hp_chip": ('vaccine', 'data_power', 'virus'),
    "hp_chip_g": ('vaccine', 'data_power', 'virus'),
    "hedonism_101": ('obedience',),
    "book": ('obedience', 'manners_lapse'),
    "board_game": ('vaccine', 'data_power', 'obedience'),
    "computer_game": ('virus', 'data_power'),
    "trampoline": ('strength', 'weight'),
    "x_program": ('hunger', 'strength', 'energy', 'x_antibody'),
    "zone_transport": (),
    "continent_transport": (),
    "digitron": ('num',),
    "horn_helmet": ('num',),
    "grey_claws": ('num',),
    "water_bottle": ('num',),
    "torn_tatter": ('num',),
    "white_wings": ('num',),
    "black_wings": ('num',),
    "metal_armor": ('num',),
    "flaming_wings": ('num',),
    "toy_oven": ('hunger',),
    "capsule_a": (),
    "capsule_b": (),
    "capsule_c": (),
    "capsule_d": (),
    "capsule_e": (),
    "capsule_f": (),
    "capsule_g": (),
    "capsule_h": (),
    "prank_capsule_a": (),
    "prank_capsule_b": (),
    "futon": ('futon_doze',),
    "human_fire_spirit": ('num',),
    "human_light_spirit": ('num',),
    "human_ice_spirit": ('num',),
    "human_wind_spirit": ('num',),
    "human_thunder_spirit": ('num',),
    "human_earth_spirit": ('num',),
    "human_water_spirit": ('num',),
    "human_wood_spirit": ('num',),
    "human_metal_spirit": ('num',),
    "human_dark_spirit": ('num',),
    "beast_fire_spirit": ('num',),
    "beast_light_spirit": ('num',),
    "beast_ice_spirit": ('num',),
    "beast_wind_spirit": ('num',),
    "beast_thunder_spirit": ('num',),
    "beast_earth_spirit": ('num',),
    "beast_water_spirit": ('num',),
    "beast_wood_spirit": ('num',),
    "beast_metal_spirit": ('num',),
    "beast_dark_spirit": ('num',),
}

# ---------------------------------------------------------------------------
# TIERED RARITY (distribution arc, 2026-07-24 -- Joel ruled D1 "stock and
# find").  The tier is DERIVED FROM THE CANON PRICE, never hand-assigned:
# 20 of the 40 priced entries carry DVPet's own DefaultPrice, and P5/P6
# deliberately took those numbers, so price already IS the game's opinion of
# an item's worth.  Deriving means no economy gets invented here -- the bands
# are just a reading of data that was already there.
#
# The ladder falls out cleanly: 14 common, 12 uncommon, 9 rare, 5 legendary.
# Grant-only treats (price None) have no band and read as common wherever a
# weight is needed -- a birthday cupcake is the commonest thing there is.
TIER_BANDS = ((300, "common"), (1000, "uncommon"), (2500, "rare"))
TIER_TOP = "legendary"
TIER_ORDER = ("common", "uncommon", "rare", "legendary")


def tier_for_price(price):
    """The band a price falls in, or None for a grant-only item.

    ⛔NO LONGER THE TIER SOURCE (2026-08-02, Joel: "yeah decouple rarity from
    price").  Kept because it is still a readable statement of what an item
    COSTS in band terms, and the retired-ruling comment above is history worth
    keeping -- but `tier` comes from `tier_for_supply` now.  Do not wire this
    back into CATALOG."""
    if price is None:
        return None
    for ceiling, name in TIER_BANDS:
        if price <= ceiling:
            return name
    return TIER_TOP


# ⭐⭐RARITY IS SUPPLY, NOT PRICE (2026-08-02, Joel's named order).
#
# The old rule derived `tier` FROM PRICE, on the reasoning that "price was
# already the game's opinion of an item's worth".  True -- but worth is not
# scarcity, and the economy audit that day showed why it mattered: at ~440
# bits per real minute of adventuring, the dearest good in the game is a
# 23-minute walk.  "Legendary" meant "expensive", expensive meant twenty
# minutes, and rarity was decorative.
#
# The authored CSVs already carry the game's opinion of SCARCITY, in columns
# nothing was reading: DefaultStockChance (how often a shop stocks it at all)
# and DefaultMaxStock (how many it will ever carry).  Their product is the
# expected number of copies on a shelf -- a real supply number, authored
# per item, with nothing to do with price.  So this invents no economy
# either; it reads the OTHER column that was always there.
#
# Measured: price-vs-supply correlation r = -0.16 (was +1.00 by construction).
# The Gold Pill stays legendary -- but now because a shop carries exactly ONE,
# not because it costs 10000b.  The 3000b evolution relics drop to common,
# because shops always stock them.  A 100b capsule becomes the rarest thing
# in the game, because it is.
_SUPPLY_CAP = 30.0          # DefaultMaxStock -1 == no ceiling: as common as it gets
SUPPLY_BANDS = ((1.0, "legendary"), (4.0, "rare"), (10.0, "uncommon"))


def _authored_supply():
    """{icon -> expected copies on a shelf} from the authored stock columns."""
    import csv as _csv
    import os as _os
    out = {}
    here = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "data")
    for fn, pre, idc in (("items.csv", "i", "ItemIdentificationNum"),
                         ("foods.csv", "f", "FoodIdentificationNum")):
        try:
            with open(_os.path.join(here, fn), encoding="utf-8") as fh:
                rows = list(_csv.DictReader(fh))
        except OSError:
            continue
        if not rows:
            continue
        cc = next((c for c in rows[0] if c.startswith("DefaultStockChance")), None)
        cm = next((c for c in rows[0] if c.startswith("DefaultMaxStock")), None)
        if not cc or not cm:
            continue
        for r in rows:
            try:
                chance = int(str(r[cc]).split(";")[0] or 0)
                mx = int(r[cm] or 0)
            except (TypeError, ValueError):
                continue
            out[f"{pre}:{r[idc]}"] = chance / 100.0 * (_SUPPLY_CAP if mx < 0 else mx)
    return out


_SUPPLY = _authored_supply()


def supply_score(icon):
    """Expected copies of `icon` on a shelf, or None when unauthored."""
    return _SUPPLY.get(icon)


def tier_for_supply(icon, price=None):
    """The band an item's AUTHORED SUPPLY falls in, or None for a grant-only
    good.  An unauthored icon (tuipet's own additions) falls back to the price
    ladder rather than silently reading as the commonest thing there is."""
    if price is None:
        return None
    s = supply_score(icon)
    if s is None:
        return tier_for_price(price)
    for ceiling, name in SUPPLY_BANDS:
        if s <= ceiling:
            return name
    return "common"


# How much RARER a tier is, both on the shelf and on the road.  One curve
# for both levers so "rare" means one thing in this game.
TIER_WEIGHT = {"common": 8, "uncommon": 4, "rare": 2, "legendary": 1}
# Daily town stock ceiling by tier (capped further by TOWN_DAILY_CAP).
TIER_STOCK = {"common": 3, "uncommon": 2, "rare": 1, "legendary": 1}


# grant-only keys whose rarity is NOT "commonest thing there is" (the
# birthday-treat default): the endgame spirits and the elite X sample roll
# at legendary weight wherever a weighted pick sees them (2026-07-26).
_WEIGHT_OVERRIDE = {k: TIER_WEIGHT["legendary"] for k in (
    "x_program",
    "human_fire_spirit", "human_light_spirit", "human_ice_spirit",
    "human_wind_spirit", "human_thunder_spirit", "human_earth_spirit",
    "human_water_spirit", "human_wood_spirit", "human_metal_spirit",
    "human_dark_spirit",
    "beast_fire_spirit", "beast_light_spirit", "beast_ice_spirit",
    "beast_wind_spirit", "beast_thunder_spirit", "beast_earth_spirit",
    "beast_water_spirit", "beast_wood_spirit", "beast_metal_spirit",
    "beast_dark_spirit")}


def tier_weight(key):
    """Roll weight for `key` -- the find pools and any weighted shelf pick."""
    if key in _WEIGHT_OVERRIDE:
        return _WEIGHT_OVERRIDE[key]
    v = CATALOG.get(key)
    return TIER_WEIGHT.get((v.tier if v else None) or "common", 1)


def tier_stock(key):
    v = CATALOG.get(key)
    return TIER_STOCK.get((v.tier if v else None) or "common", 1)


_ROAD_ONLY = frozenset({"town_transport", "disaster_transport",
                        "life_recovery",
                        # the expansion (2026-07-26): the escape rope and
                        # the portable camp are road tools like their kin
                        "zone_transport", "continent_transport"})

# THE catalog: the authored table, field-named.  Everything downstream
# reads this, never `_AUTHORED`.
CATALOG = {
    _k: Item(*_v,
             touches=_TOUCHES.get(_k, ()),
             where="road" if _k in _ROAD_ONLY else "home",
             tier=tier_for_supply(_v[1], _v[2]))
    for _k, _v in _AUTHORED.items()
}

# the road's shelf unlocks by CLEARING MAPS (the profile `maps` set): once a
# tamer has beaten a continent, the transports/recovery it needs go on sale.
# key -> how many maps must be cleared.  Same earned-access rule as the eggs.
ADVENTURE_GATES = {
    "town_transport": 1, "disaster_transport": 1, "life_recovery": 2,
    # the expansion (2026-07-26): the escape rope opens with the first
    # cleared map; the portable camp is the deepest tool (matches its kin)
    "zone_transport": 1, "continent_transport": 2,
}


def adventure_open(key, prog=None):
    """Is this road-shelf item unlocked (enough maps cleared)?  Non-gated keys
    are always open."""
    need = ADVENTURE_GATES.get(key)
    if need is None:
        return True
    if prog is None:
        from . import persistence
        prog = persistence.get_progress()
    return len(prog.get("maps", ()) or ()) >= need


# sprite icon (i:/f:) -> the CATALOG key that wears it: adventure loot is
# authored by data id, but the bag/use system speaks CATALOG keys (the same
# "the bag could neither show nor use" trap the i:32 heal fixed) -- so found
# loot maps back through this to a real, usable entry.
_BY_ICON: dict[str, str] = {}
for _k, _v in CATALOG.items():
    _BY_ICON.setdefault(_v.icon, _k)


def key_for_icon(icon):
    """The CATALOG key whose sprite is `icon`, or None (unmapped loot).
    A RETIRED key's icon resolves to its heir -- authored loot rows, cup
    prizes and town stock lines written against a cut item keep paying."""
    k = _BY_ICON.get(icon)
    if k is not None:
        return k
    old = _RETIRED_ICONS.get(icon)
    return RETIRED.get(old) if old else None


# Which frame of an item's sheet IS the item, for every still cell that
# shows one (shop row, bag row, adventure find).  Frame 0 otherwise.
#
# The Music Player's sheet leads with a generic disc that isn't the item at
# all -- the box is frame 1 (Joel 2026-07-27: "the icon shpuld be what the
# other frame is, and the icon shouldnt even be used").  The MusicBox fx
# skips the disc too, so frame 0 of i:9 is now drawn nowhere.
_ICON_FRAME = {"music_player": 1}

# ...and when NO frame of an item's sheet can survive the 10-column cell,
# the cell borrows a DIFFERENT rip outright (Joel 2026-07-28: "use the orb").
# i:9's box is 13px wide with a note-trail overhead -- at cell scale it
# crunched to a smudge; the beamed-note orb (special 42, Gekomon's own shot,
# the same rip the MusicBox show flies) is natively 8x8 and fits the cell
# 1:1.  Still-cells only: the SHOW keeps playing the box's real frames.
_ICON_ART = {"music_player": ("special", "42")}


def icon_art(key):
    """A still-cell's substitute sprite for `key` (catalog key or raw icon
    key), or None to use the sheet frame.  Falls back to None if the orb
    bank is missing so the frame path always still renders something."""
    k = key if key in CATALOG else (key_for_icon(key) or "")
    ref = _ICON_ART.get(k)
    if not ref:
        return None
    from . import data_world
    group, idx = ref
    return (data_world.load_orbs().get(group) or {}).get(idx)


def icon_frame(key):
    """The display frame for a CATALOG key or a raw icon key ('i:9')."""
    k = key if key in CATALOG else (key_for_icon(key) or "")
    return _ICON_FRAME.get(k, 0)

# compat views over the one table (shelf text / icons / tests import these)
EFFECTS = {k: v.effect for k, v in CATALOG.items()}
ICON_KEYS = {k: v.icon for k, v in CATALOG.items()}
FLAVORS = {k: v.flavor for k, v in CATALOG.items()}   # the dossier taglines

# (FOOD_KEYS -- the Food-category set -- CUT 2026-07-25 on Joel's order.
# It was the SECOND answer to "is this eaten", and the item-show audit
# 2026-07-23 already settled that question on the SHEET: item_is_eaten
# reads the `f:` prefix, which is why the six food-sheet consumables --
# both drinks, both pills, the vitamin, the anti-evo chip -- eat like the
# pill instead of flashing text.  The category set said NO to all six, so
# the two never agreed; it had no live consumer left by the item sweep.
# Do not reintroduce a second is-it-eaten test.)
# Items whose use has its OWN door and must never be hijacked by a
# generic item show: the memory chip's inherit flow, the two road
# transports and the road's Life Recovery (all spent on the march), and
# the Revive Floppy -- its canon type is Play, but it is used on a DEAD
# pet and the bag is unreachable at the grave, so that show could only
# ever be wrong or unplayable (item-show audit 2026-07-23).
_OWN_FLOW = frozenset({"digimemory", "town_transport", "disaster_transport",
                       "life_recovery", "revive_floppy",
                       # the expansion (2026-07-26): evolution keys play the
                       # evolution itself; the road tools and the futon run
                       # their own doors
                       "zone_transport", "continent_transport", "futon",
                       "digitron", "horn_helmet", "grey_claws",
                       "water_bottle", "torn_tatter", "white_wings",
                       "black_wings", "metal_armor", "flaming_wings",
                       "human_fire_spirit", "human_light_spirit",
                       "human_ice_spirit", "human_wind_spirit",
                       "human_thunder_spirit", "human_earth_spirit",
                       "human_water_spirit", "human_wood_spirit",
                       "human_metal_spirit", "human_dark_spirit",
                       "beast_fire_spirit", "beast_light_spirit",
                       "beast_ice_spirit", "beast_wind_spirit",
                       "beast_thunder_spirit", "beast_earth_spirit",
                       "beast_water_spirit", "beast_wood_spirit",
                       "beast_metal_spirit", "beast_dark_spirit"})


def item_is_eaten(key):
    """True when USING this item should play the EAT show.

    The canon rule is the SHEET (item-show audit 2026-07-23, Joel "do
    the eat show for the consumables too"): foods.csv carries no
    AnimationType column at all, because eating IS the animation --
    exactly how the pill already works ("the pill is EATEN, the
    source's EATING action, same as meat", pill-anim fix 2026-07-18).
    So every `f:` item eats: the 11 foods as before, plus the six
    food-sheet CONSUMABLES that used to flash bare text -- both
    drinks, both pills, the vitamin and the anti-evo chip.  `i:`
    items take a script instead (see item_script)."""
    return ICON_KEYS.get(key, "").startswith("f:")


def item_script(key):
    """The canon SHOW for a catalog item, or None.

    ONE SOURCE (item-show audit 2026-07-23, Joel: "is all of that
    already wired in?"): items.csv carries an AnimationType for every
    row, and our icon key `i:N` IS that row id -- so the mapping is
    free.  This replaces TOY_SCRIPTS, a 7-entry hand-map that
    duplicated the column and left 19 items with ripped art and no
    show at all.  Returns None for anything without an implemented
    script, for own-door items, and for `f:` consumables -- food-sheet
    items are EATEN (foods.csv has no AnimationType at all) and ride
    the eat fx, exactly like the pill."""
    if key in _OWN_FLOW:
        return None
    from . import itemfx
    if key in itemfx._SCRIPT_OVERRIDE:      # a canon type with no usable show,
        return itemfx._SCRIPT_OVERRIDE[key]  # remapped to a fitting one (2026-07-24)
    icon = ICON_KEYS.get(key, "")
    if not icon.startswith("i:"):
        return None
    act = (data.consumable_by_key(icon) or {}).get("action") or ""
    return act if act in itemfx.SCRIPTS else None

# old-catalog keys -> their heirs (the save-heal maps bags 1:1 on load;
# nobody loses goods when the shelf turns over)
# THE RETIRED LEDGER (item refactor 2026-07-27).  Every key cut by the
# refactor names an HEIR: owned copies convert 1:1 in the bag heal
# (persistence._heal_bag), and any authored channel still speaking the old
# icon -- a loot row, a cup prize, a town stock line -- resolves to the heir
# through key_for_icon's fallback below.  Nobody loses goods; no authored
# data goes dark.
# the icons the RETIRED keys wore, for key_for_icon's fallback (static on
# purpose: the rows are gone from CATALOG, so nothing can derive these; the
# test suite pins that every entry here names a live heir)
_RETIRED_ICONS = {
    "f:45": "nuts", "f:46": "oats", "f:48": "egg", "f:50": "guava",
    "f:47": "milk", "f:40": "chicken_soup", "f:29": "rice", "f:53": "salmon",
    "f:52": "beans", "f:39": "ice_cream", "f:9": "banana",
    "f:30": "bitter_herbs", "i:12": "balloon", "i:26": "bubble_bath",
    "i:11": "toy_car", "i:4": "stuffed_animal",
    # (no i:67 row: cold_compress WEARS the shower art now, so the live icon
    # table already routes it -- the shower literally continues as the compress)
    "i:82": "toilet",
}

RETIRED = {
    "balloon": "ball",
    "banana": "cake",
    "beans": "broccoli",
    "bitter_herbs": "book",
    "bubble_bath": "ball",
    "chicken_soup": "bread",
    "cold_shower": "cold_compress",
    "egg": "bread",
    "gluttons_platter": "giga_meal",
    "guava": "bread",
    "ice_cream": "cake",
    "milk": "bread",
    "nuts": "bread",
    "oats": "bread",
    "rice": "cheese",
    "salmon": "cheese",
    "stuffed_animal": "ball",
    "toilet": "port_potty",
    "toy_car": "ball",
}

LEGACY_KEYS = {
    "best_fruit": "tuna", "normal_fruit": "fish", "worst_fruit": "vegetable",
    "deadly_fruit": "poison_mushroom", "junk_food": "cheese_burger",
    "premium_meat": "steak", "super_carrot": "slim_drink",
    "care_mistake_eraser": "miracle_drink", "alarm_clock": "music_player",
    "time_gear": "grow_capsule", "training_pack": "dumbbell",
    "poop_clean_pill": "port_potty",
    # the inheritance chip circulated under its raw icon key -- a key the
    # bag could neither show nor use (gameplay audit 2026-07-19)
    "i:32": "digimemory",
}

# the crest eggs: used from the bag, they trigger the classic ARMOR evolution
# (Pet._crest_egg -> evolution.item_select via the Digimental ids)
ARMOR_CATEGORY = "Armor-Spirit"

# the Digimental waves (Joel 2026-07-17: "wire the gates") -- the canon
# discovery order, on the same earned-access rule as the egg carousel:
# sealed ones simply don't appear.  Courage & Hope open armor evolution
# from day one; the crest seven follow the FIRST armor evolution; the 02
# pair rides lifetime wins; Miracles is golden (raids); Destiny is the
# movie one (generation 5).  Gate signals are persistence.get_progress().
DIGIMENTAL_GATES = {
    "egg_of_courage": None,
    "egg_of_hope": None,
    "egg_of_friendship": ("armor_evos", 1),
    "egg_of_love": ("armor_evos", 1),
    "egg_of_knowledge": ("armor_evos", 1),
    "egg_of_sincerity": ("armor_evos", 1),
    "egg_of_reliability": ("armor_evos", 1),
    "egg_of_light": ("wins", 25),
    "egg_of_kindness": ("wins", 25),
    "egg_of_miracles": ("raids", 2),
    "egg_of_destiny": ("max_gen", 5),
}


def digimental_open(key, prog=None):
    """Is this Digimental's wave reached?  (Non-digimental keys are open.)"""
    gate = DIGIMENTAL_GATES.get(key)
    if gate is None:
        return True
    if prog is None:
        from . import persistence
        prog = persistence.get_progress()
    sig, need = gate
    return int(prog.get(sig, 0)) >= need


# --- per-town egg market (Joel 2026-07-21: "different towns sell different
# eggs -- all shops feel unique").  Each town stocks a DISTINCT band of the
# earnable digitama, shown as the real 8x8 egg thumbnails; buying one owns it
# outright (bits -> persistence.egg_own).  Eggs still unlock FREE by condition
# elsewhere -- a town is the road shortcut, priced.
EGG_STOCK_PER_TOWN = 6


def _sellable_eggs():
    """The digitama a town may stock: every egg that ISN'T a free starter
    (the five START babies you already own) and CAN be owned.  A can_perm
    FALSE row is a lineage egg -- hatchable only the generation its
    condition holds, never permanently ownable (eggmigrate._sane_owned
    strips exactly these from eggs_owned "however they snuck in"), so the
    buy-outright shortcut must not sell what a repair pass deletes (egg
    audit 2026-07-25: towns 0/2/5 sold all five lineage eggs)."""
    from . import egg as egg_mod, data
    rules = data.load_egg_unlock()
    return [i for i in range(egg_mod.count())
            if not (rules.get(i) or {}).get("start")
            and (rules.get(i) or {}).get("can_perm", True)]


def town_egg_stock(town_id, count=EGG_STOCK_PER_TOWN):
    """The DISTINCT set of eggs THIS town sells -- a stable band over the
    earnable digitama, rotated by town so no two town shops feel the same."""
    pool = _sellable_eggs()
    if not pool:
        return []
    count = min(count, len(pool))
    # a stride CO-PRIME with the pool keeps every town's band distinct --
    # stepping by the band width alone collapsed to len(pool)/count bands
    # the moment the width divided the pool (egg audit 2026-07-25: cutting
    # the 5 lineage eggs left a 36-egg pool, and 26 towns fell into 6 bands)
    stride = count
    while len(pool) > 1 and _gcd(stride, len(pool)) != 1:
        stride += 1
    start = (int(town_id) * stride) % len(pool)
    return [pool[(start + i) % len(pool)] for i in range(count)]


def egg_price(idx):
    """A town egg's bit price -- earned eggs are a treat, so the buy-outright
    shortcut costs real bits.  Starters (never stocked) are free."""
    from . import data
    rule = data.load_egg_unlock().get(idx) or {}
    return 0 if rule.get("start") else 800

# (the DVPet staple props -- Toilet/Port. Potty/Futon, items.csv 81-83, and
# their uses/cap stock maths -- left 2026-07-17: strict-DSprite items
# ("go strict").  DSprite's catalog has no furniture; the shelf is exactly
# vitems.json.)

# the source shop prices any entry with no explicit price at a flat default
# (`e.price || 1e3`); the 11 crest eggs ship priceless, so without this they
# never reach the shelf.  Faithful to the source default, not invented.
DEFAULT_PRICE = 1000

def _price(v):
    return int(v.get("price") or DEFAULT_PRICE)


def _usable(key, category):
    """Only goods Pet.use_item can actually APPLY are sold.  Since the
    TUIPET catalog (2026-07-18) the consumables are authored in CATALOG;
    vitems contributes only the Digimentals (its theme_* skins,
    storage_drive and retired consumables never reach the shelf)."""
    return category == ARMOR_CATEGORY or key in CATALOG


def catalog():
    """Every buyable entry: [{key, name, price, category}], price order.
    The consumable shelf is the authored CATALOG (price None = unsold);
    the 11 Digimentals still come from vitems.json.  A Digimental whose
    wave isn't reached is SEALED: it stays off the shelf entirely (the
    egg-carousel rule), though entry() still resolves it so an
    already-owned one renders in the bag."""
    from . import persistence
    prog = persistence.get_progress()
    out = []
    for k, v in CATALOG.items():
        if v.price is not None and adventure_open(k, prog):  # road shelf gated by maps
            out.append({"key": k, "name": v.name, "price": v.price,
                        "category": v.category})
    for k, v in data.load_vitems().items():
        if isinstance(v, dict) and v.get("category") == ARMOR_CATEGORY \
                and digimental_open(k, prog):
            out.append({"key": k, "name": v.get("name", k),
                        "price": _price(v),
                        "category": ARMOR_CATEGORY})
    out.sort(key=lambda e: (e["category"], e["price"], e["name"]))
    return out


def entry(key):
    """Resolve any key: the authored CATALOG first (an unsold treat still
    renders in the bag at a nominal resale), then vitems (Digimentals)."""
    c = CATALOG.get(key)
    if c is not None:
        return {"key": key, "name": c.name,
                "price": c.price if c.price is not None else 100,
                "category": c.category}
    v = data.load_vitems().get(key)
    if not isinstance(v, dict):
        return None
    return {"key": key, "name": v.get("name", key),
            "price": _price(v),
            "category": v.get("category", "Item")}


def categories():
    have = {e["category"] for e in catalog()}
    out = [c for c in CATEGORY_ORDER if c in have]
    return out + sorted(have - set(out))


def shelf(cat):
    return [e for e in catalog() if e["category"] == cat]


# shelf tabs in PLAY order -- everyday care first, the relics last (shop
# polish 2026-07-17: the old alphabetical order opened the shop on a
# two-item Armor-Spirit tab).  Unknown categories append alphabetically.
# EIGHT TABS BY ACT (item refactor 2026-07-27, Joel: "all items need to be
# completely refactored and catagorized"): each tab names the thing the
# player wants to HAPPEN, in play order -- feed first, the doors late.
CATEGORY_ORDER = ("Feed", "Rest", "Cure", "Drill", "Manners", "Power",
                  "Treasure", "Evolve", "Road", ARMOR_CATEGORY)


def crest_answer(pet, key):
    """The forms THIS pet's armor jump would land right now -- the same
    evolution.check gate the crest egg runs on use (display only, no
    roll).  [] when nothing answers (not a crest key, egg/dead, gates
    unmet)."""
    from . import evolution
    from .pet import Pet
    item_id = Pet._CREST_IDS.get(key, -1)
    if (item_id < 0 or pet is None or getattr(pet, "num", -1) < 0
            or getattr(pet, "dead", False) or pet.stage == "Egg"):
        return []
    _, by_num = data.load_sprites()
    return sorted({by_num[t]["name"]
                   for t in data.load_evolutions().get(pet.num, [])
                   if t in by_num and not data.is_placeholder(t)
                   and evolution.check(pet, t, item=item_id)})


# the sealed-wave tease texts, keyed by gate -- live numbers filled from
# persistence.get_progress() (the egg carousel's locked-hint pattern).
# Kept SHORT: they ride the 38-col shop footer, and footers never marquee.
_WAVE_TEASE = {
    ("armor_evos", 1): "your 1st armor evo wakes the crest 5",
    ("wins", 25): "wins {have}/25 wake Light & Kindness",
    ("raids", 2): "raids {have}/2 wake Miracles",
    ("max_gen", 5): "generation {have}/5 wakes Destiny",
}


def wave_status(prog=None):
    """(sealed_count, closest-wave tease) from live DIGIMENTAL_GATES
    progress -- (0, '') once every relic is on the shelf."""
    if prog is None:
        from . import persistence
        prog = persistence.get_progress()
    sealed = [g for k, g in DIGIMENTAL_GATES.items()
              if g is not None and not digimental_open(k, prog)]
    if not sealed:
        return 0, ""

    def ratio(g):
        sig, need = g
        return min(1.0, int(prog.get(sig, 0)) / need)
    # DETERMINISTIC TIE-BREAK (shops audit 2026-07-25).  `max(set(...))`
    # walked a SET, so when two sealed waves tied on ratio the winner fell
    # out of string-hash iteration order -- which Python randomises PER
    # PROCESS.  Measured: the same save printed "wins 0/25 wake Light &
    # Kindness" or "generation 0/5 wakes Destiny" depending on the launch,
    # and 7% of sampled progress states tie (any player at gen 5+ with no
    # armor evo and no wins sits in one).  A shop's character is supposed
    # to be STABLE -- the same law that keeps a town's guest good crc32-
    # ordered and its deal fixed for the day.  Ties now break toward the
    # NEAREST goal in absolute terms (smallest `need`), which is also the
    # more useful tease: "your 1st armor evo" over "wins 0/25".
    sig, need = max(sorted(set(sealed)), key=lambda g: (ratio(g), -g[1]))
    have = min(int(prog.get(sig, 0)), need)
    tease = _WAVE_TEASE.get((sig, need), "more relics stir out there")
    return len(sealed), tease.format(have=have, need=need)


def effect_line(e):
    if e.get("category") == ARMOR_CATEGORY:
        return "an armor evolution (the right Child)"
    k = e["key"]
    eff = EFFECTS.get(k, "a curiosity")
    fl = FLAVORS.get(k)
    # the dossier speaks effect AND character ("polish up the shop
    # descriptions" 2026-07-18) -- but the info block holds exactly two
    # 26-col rows, so a long effect keeps the stage to itself
    if fl:
        import textwrap
        joined = f"{eff} — {fl}"
        if len(textwrap.wrap(joined, 26)) <= 2:
            return joined
    return eff


def buy(pet, e):
    """-> (message, sfx)."""
    if pet.bits < e["price"]:
        return (f"Need {e['price']}b — you have {pet.bits}b.", "error")
    pet.spend_bits(e["price"])
    pet.add_item(e["key"])
    return (f"Bought {e['name']}!", "confirm")


def resell_price(e):
    # a town-priced bag row carries its LOCAL sell price (buy-low/sell-high,
    # shops arc 2026-07-21); home keeps the flat half
    if "sell_price" in e:
        return max(1, int(e["sell_price"]))
    return max(1, e.get("price", 0) // 2)


def sell(pet, e):
    if pet.inventory.get(e["key"], 0) <= 0:
        return ("You don't have that.", "error")
    pet.take_item(e["key"])                    # classic take_item returns None
    pet.bits += resell_price(e)
    return (f"Sold {e['name']} for {resell_price(e)}b.", "confirm")


# (the OLD town storefront chain -- home_shop_open / town_shop_open /
# town_shop_hours / roll_town_shop / slot_label / slot_info / sell_info /
# purchase_price + Pet.buy_slot -- CUT 2026-07-19, Joel: "cut the town
# chain".  The hours/rolled-slot machine stays dead.  What follows is the
# NEW town economy Joel ordered 2026-07-21 ("shops, town shops, deals"):
# deterministic, no rolls, no opening hours -- the authored data driving
# tuipet-idiom systems.)

# -- the town economy (shops arc, 2026-07-21) --------------------------------
# towns.csv override lists -> shopConsumable.csv econ rows -> CATALOG
# identities.  The 26 towns split into TWO authored stock families (a shared
# items shelf + two food families) -- that split IS the trade map: a town
# pays DEMAND rates for goods it doesn't stock.
TOWN_DEMAND_NUM, TOWN_DEMAND_DEN = 7, 10   # unstocked goods: towns pay 70%
#                                            (home pays 50%; canon towns pay
#                                            price//ResellFactor for their
#                                            OWN stock -- they have plenty)
TOWN_DAILY_CAP = 3        # tuipet's own per-(town,item,day) purchase bound.
#                           DVPet's 25-50-steak crates served ITS economy;
#                           against tuipet's catalog even ratio-scaled deal
#                           margins would compound into a printer at 50/day.

# PRICE LAW: a town price is the AUTHORED RATIO scaled to tuipet's catalog --
# catalog_price * row_price / DefaultPrice (the Default* cols are DVPet's own
# home economy, so the ratio IS the authored "towns discount steak 25%, halve
# chips, sell furniture at par" structure).  Raw row prices against tuipet's
# repriced catalog were money printers (375b steak vs 2000b catalog: +625
# per home flip); the ratio keeps every flip at-or-below water and makes
# DEALS the only trade window -- by design.


def _today_ordinal(today=None):
    from . import tournament
    d = today if today is not None else tournament._today()
    return d.toordinal()


@lru_cache(maxsize=1)
def _town_maps():
    """town_id -> the MAP whose zone hosts the town (the road's own
    geography; item diversity audit 2026-07-23)."""
    from . import data
    out = {}
    for mp in data.load_maps():
        for z in mp["zones"]:
            for _lo, _hi, tid in z.get("towns", ()):
                out[tid] = z["map"]
    return out


# P4 (item diversity audit 2026-07-23, Joel: "do it all"): each MAP's
# towns carry ONE regional specialty beyond the authored base, so the
# five maps read differently before the guest good even lands.  REDEALT
# from the grown catalog (Joel 2026-07-26: "yeah redeal the specialties
# too") -- same depth logic, new faces: the starter map sells the toy
# surprise, the mid maps comfort and cunning, and the deep maps keep the
# premium-tier slots (the old map-4 Revive Floppy rule): map 4 deals the
# dark fluid, map 5 the gilded pill.
_MAP_SPECIALTY = {1: "chocolate_egg", 2: "futon", 3: "board_game",
                  4: "digitron", 5: "gold_pill"}


def _econ_stub(key):
    """A synthetic econ row for non-authored shelf rows (guest/regional):
    catalog price, standard factors, capped stock -- no money printer."""
    v = CATALOG[key]
    return {"price": v.price, "sale_factor": 2, "resell_factor": 2,
            "max_stock": 2, "is_food": v.category == "Feed",
            "consumable_id": -1}


def _base_rows(town_id):
    """The town's authored shelf + its map's regional specialty:
    [(sid, catalog_key, econ_row, local_price)] in list order (items shelf
    first, then the food family).  local_price is the PRICE-LAW ratio (see
    above); rows whose consumable has no living CATALOG identity are
    dropped -- their systems (chips, furniture) aren't in tuipet, and
    dormant data stays dormant."""
    from . import data
    t = data.load_towns().get(town_id)
    if not t:
        return []
    ov = data.load_shop_overrides()
    foods, items = data._load_consumables()
    rows = []
    for sid in t["items_override"] + t["foods_override"]:
        o = ov.get(sid)
        if not o or o["price"] <= 0:
            continue
        icon = ("f:" if o["is_food"] else "i:") + str(o["consumable_id"])
        k = key_for_icon(icon)
        if not k:
            continue
        e = entry(k)
        default = ((foods if o["is_food"] else items).get(o["consumable_id"])
                   or {}).get("price", 0)
        if e and default > 0:
            local = max(1, round(e["price"] * o["price"] / default))
        else:
            local = o["price"]
        if any(k == have for _s, have, _o, _l in rows):
            # RETIRED resolution can land two authored rows on one heir (a
            # town that stocked both the toilet and the port-potty now has
            # two port-potty lines): the shelf keeps the FIRST, because a
            # duplicate row breaks the one-key-one-row grammar everything
            # downstream (deal dedup included) assumes (refactor 2026-07-27)
            continue
        rows.append((sid, k, o, local))
    sk = _MAP_SPECIALTY.get(_town_maps().get(town_id))
    if sk and sk not in {k for _sid, k, _o, _p in rows}:
        rows.append((f"regional:{town_id}", sk, _econ_stub(sk),
                     CATALOG[sk].price))
    return rows


@lru_cache(maxsize=1)
def _guest_deal():
    """town_id -> its standing guest good, dealt WITHOUT replacement
    across ALL towns (item diversity audit 2026-07-23: the old per-town
    crc32 pick birthday-collided -- 8 items served 2-3 towns each, and
    towns 11+12 were byte-identical shops).  The pool is the UNGATED
    priced catalog minus Adventure (its map-clear gate must hold) and
    minus the Poison Mushroom (a town's one signature good is never a
    trap -- the raid-pool rule).  26 towns, 36 candidates: every town's
    guest is unique game-wide.  crc32-ordered, so the deal is STABLE --
    a town's character stays permanent (the guest-good law); the daily
    deal already rotates.

    COVERAGE FIRST (2026-07-24, Joel "pull them into town rotation"): the
    guest slot exists for VARIETY, so it fills gaps before it spends a slot
    on a good already sold in some town's authored base.  15 goods live in a
    base somewhere; the other 21 need a guest slot to appear anywhere, and 21
    fits in 26 slots with room to spare -- yet the old pure-crc32 order let a
    few slots land on base-covered goods, stranding tuna, cheese_burger and
    the ball in NO town at all.  Sorting the not-in-any-base goods to the
    FRONT covers every one of the 21 (still crc32 WITHIN each band, so the
    deal stays stable), and the leftover slots go to base-covered goods."""
    import zlib
    pool = [k for k, v in CATALOG.items()
            if v.price is not None and v.category != "Road"
            and k != "poison_mushroom"]
    base_anywhere = set()
    for tid in _town_maps():
        base_anywhere.update(k for _sid, k, _o, _p in _base_rows(tid))
    pool.sort(key=lambda k: (k in base_anywhere,
                             zlib.crc32(f"guest2:{k}".encode())))
    taken, out = set(), {}
    for tid in sorted(_town_maps()):
        stocked = {k for _sid, k, _o, _p in _base_rows(tid)}
        pick = (next((k for k in pool
                      if k not in taken and k not in stocked), None)
                or next((k for k in pool if k not in stocked), None))
        if pick:
            taken.add(pick)
            out[tid] = pick
    return out


def _town_rows(town_id):
    """The full town shelf: authored base + regional specialty + the
    standing guest good (gameplay polish #24; re-dealt collision-free in
    the item diversity audit 2026-07-23) + THE ROAD SHELF.

    The road shelf (item sweep 2026-07-24): a town counter carries every
    Adventure item, not just the two the authored overrides happen to
    name.  `shopConsumable.csv` stocks i:29/i:30 (the two transports) in
    all 26 towns and has no row for i:27, so Life Recovery -- the road
    tool you most need WHILE ON THE ROAD -- was the one buyable good no
    counter in the world sold.  The guest slot could never fix it: its
    pool excludes Adventure precisely because the map-clear gate has to
    hold, and a guest row is ungated.

    These rows are the shelf's IDENTITY, gate or no gate.  What a tamer
    may actually buy today is `_open_rows`."""
    rows = _base_rows(town_id)
    gk = _guest_deal().get(town_id)
    if gk:
        rows.append((f"guest:{town_id}", gk, _econ_stub(gk),
                     CATALOG[gk].price))
    have = {k for _sid, k, _o, _p in rows}
    for k, v in CATALOG.items():
        if v.category == "Road" and k not in have:
            rows.append((f"road:{town_id}:{k}", k, _econ_stub(k), v.price))
    return rows


def _open_rows(town_id, prog=None):
    """The town shelf a tamer can actually SHOP today: `_town_rows` minus
    anything whose earned-access gate is still shut.

    THE GATE HELD IN EXACTLY ONE SHOP (item sweep 2026-07-24).  The road
    shelf unlocks by CLEARING MAPS -- `catalog()` has honoured that since
    v0.5.114, so the home shop hides a locked transport.  Town counters
    never asked: town 0 sits on map 1's FIRST leg, and it sold Town
    Transport and Disaster Transport to a tamer who had cleared nothing.
    An earned-access rule that any starting town sells around is not a
    rule.  (Read fresh each call rather than cached: `_guest_deal`'s
    lru_cache reads `_base_rows`, which stays progress-free, so no cache
    can freeze a tamer's progress into a town's shelf.)"""
    if prog is None:
        from . import persistence
        prog = persistence.get_progress()
    return [r for r in _town_rows(town_id) if adventure_open(r[1], prog)]


def _deal_index(seed, count, today=None):
    """A daily rotating index in [0, count), crc32-seeded on (seed, day):
    stable all day, different tomorrow.  DEDUPED (2026-07-24, Joel: "dedup
    the town deal") -- it never repeats YESTERDAY's pick, so no shelf shows
    the same deal two days running.  (With a single item there is nothing
    to rotate to; it stays put.)

    The dedup compares against yesterday's FINAL (post-bump) pick, not its
    raw index -- if it compared raws, a day that was itself bumped could be
    silently repeated by today.  So the picks are walked FORWARD from a
    fixed lookback: each day bumps off the previous day's final.  Any error
    in the window's first day washes out long before today."""
    if count <= 0:
        return None
    if count == 1:
        return 0
    import zlib
    def raw(day):
        return zlib.crc32(f"{seed}:{day}".encode()) % count
    day = _today_ordinal(today)
    final = raw(day - _DEAL_LOOKBACK)
    for d in range(day - _DEAL_LOOKBACK + 1, day + 1):
        r = raw(d)
        if r == final:                       # would repeat yesterday's pick
            r = (r + 1) % count
        final = r
    return final


_DEAL_LOOKBACK = 32          # days walked to stabilise the dedup chain


def town_deal_sid(town_id, today=None, prog=None):
    """The town's ONE rotating daily deal: seeded on (town, day) -- stable
    all day, different tomorrow, different next town, and never the same as
    yesterday (dedup 2026-07-24).

    Dealt over the OPEN rows only: a deal on a row the tamer can't see is
    no deal at all (the v0.5.164 lesson -- the deal rolled onto the
    invisible Adventure shelf about half of all days)."""
    rows = _open_rows(town_id, prog)
    if not rows:
        return None
    return rows[_deal_index(town_id, len(rows), today)][0]


# the home shop's daily bargain -- half off, like a town deal, but home
# stays otherwise fixed-price (the reliable shelf).  Dealt from the always-
# stocked priced goods (no gated Adventure item, no egg), so the deal is
# never something you can't see on the shelf.
HOME_DEAL_FACTOR = 2


@lru_cache(maxsize=1)
def _home_deal_pool():
    return sorted(k for k, v in CATALOG.items()
                  if v.price is not None and v.category != "Road")


def home_deal_key(today=None):
    """The home shelf's ONE rotating daily deal key (2026-07-24, Joel: "add
    the home daily deal") -- seeded on the day, deduped vs yesterday."""
    pool = _home_deal_pool()
    i = _deal_index("home", len(pool), today)
    return pool[i] if i is not None else None


HOME_SHOP_ID = "home"        # the deal ledger's pseudo-town (see home_stock)

# keys whose contents out-value their price BY CONSTRUCTION (the capsule
# rolls the gift pool), so the always-open home shelf must ration them
# like a deal row or mint bits (expansion audit 2026-07-26)
HOME_RATIONED = frozenset({"capsule_a"})


# THE HOME COUNTER, refactored (2026-07-27, Joel: "shops need the same
# thing... daily items. not all at once like the home shop. basic items
# sure but cmon").  Home stops being the whole catalog on one wall.  It
# carries the STAPLES -- the basics a tamer must always be able to buy --
# and a rotating DAILY BAND drawn from everything else, tier-weighted so
# a legendary drops in rarely and a common often.  ~20 rows a day, and
# the week has texture.  Towns are untouched: they were already the
# curated half of the economy.
HOME_STAPLES = frozenset({
    # feed basics: the ladder's everyday rungs
    "fish", "bread", "cheese", "vegetable",
    # rest basics: the night and the tank
    "sleeping_pill", "music_player", "energy_drink",
    # drill + cure basics
    "dumbbell", "slim_drink", "supplement",
    # the gacha counter never closes -- its RATION is the guard, not absence
    "capsule_a",
})
HOME_BAND_SIZE = 10


def home_band(today=None):
    """The day's rotating guest rows.

    A SHUFFLED CYCLE, not a random draw (audit 2026-07-27): the first cut
    of this was tier-weighted sampling, and a 40-day probe caught it simply
    never dealing Flaming Wings -- a shelf that MAY show a thing eventually
    is the slot machine, not the store.  Joel's actual question ("are items
    spread out evenly thoughout the week?") is the spec: the non-staple pool
    is shuffled once per EPOCH (seeded, so every device deals the same week)
    and dealt out in day-sized hands, so every sellable key is guaranteed a
    home-shelf day each cycle (~1 week).  Rarity stays where it belongs --
    in prices, town curation and the tier rations -- not in whether the
    counter will ever stock the good at all."""
    pool = [k for k, v in sorted(CATALOG.items())
            if v.price is not None and k not in HOME_STAPLES
            and v.category != "Road"]        # road rows ride their own gate
    if not pool:
        return []
    days = -(-len(pool) // HOME_BAND_SIZE)          # hands per full cycle
    o = _today_ordinal(today)
    epoch, day = divmod(o, days)
    deck = list(pool)
    random.Random(f"homeband:{epoch}").shuffle(deck)
    hand = deck[day * HOME_BAND_SIZE:(day + 1) * HOME_BAND_SIZE]
    # the last hand of a short deck tops up from the front, never short-shelves
    if len(hand) < HOME_BAND_SIZE:
        hand += deck[:HOME_BAND_SIZE - len(hand)]
    return hand


def _ration_left(shop_id, key, taken):
    """Today's remaining ration for a tier-limited row -- THE one place the
    arithmetic lives (assembly dedup 2026-07-27: home and town each hand-
    rolled this line, the seam where the two shelves could drift)."""
    return max(0, tier_stock(key) - int(taken.get(f"{shop_id}:{key}", 0)))


def home_stock(today=None, pet=None):
    """The home shelf: staples + the day's band + the deal, decorated the
    same way a town counter is (shops-look-the-same law).

    Pricing and rationing are unchanged from the audit rulings: staples and
    band rows sell UNLIMITED at full catalog price (a flip at catalog is
    always a loss -- item sweep 2026-07-24), the one deal row and the
    capsule keep their daily tier rations, and a spent deal ration falls
    back to full price rather than a shut door."""
    deal = home_deal_key(today)
    band = set(home_band(today))
    taken = _town_taken(pet, today) if pet is not None else {}
    out = []
    for e in catalog():
        k = e["key"]
        if (k != deal and k not in HOME_STAPLES and k not in band
                and e["category"] not in (ARMOR_CATEGORY, "Road")):
            # not on today's shelf -- come back tomorrow.  TWO shelves
            # bypass the band, because both are DOORS, not stock: the
            # Digimental shelf (the crest system's single door) and the
            # ROAD shelf (map-clear gated -- a tamer who just earned the
            # warp must not wait three days to buy it; the gate IS its
            # scarcity).  Everything else rotates.
            continue
        if k in HOME_RATIONED and k != deal:
            # THE CAPSULE RATION (expansion audit 2026-07-26): its contents
            # out-value its price by construction, so the always-open shelf
            # rations it like a deal row or it prints bits
            left = _ration_left(HOME_SHOP_ID, k, taken)
            out.append(dict(e, left=left, town_id=HOME_SHOP_ID))
            continue
        if k == deal:
            base = e["price"]
            left = _ration_left(HOME_SHOP_ID, k, taken)
            e = (dict(e, deal=True, base_price=base, left=left,
                      town_id=HOME_SHOP_ID,
                      price=max(1, base // HOME_DEAL_FACTOR)) if left > 0
                 else dict(e, deal_spent=True))
        out.append(e)
    return out


def _stocked(town_id, key):
    """This town's shelf row for `key`, or None (the demand test)."""
    for _sid, k, o, local in _town_rows(town_id):
        if k == key:
            return o, local
    return None


def _town_taken(pet, today=None):
    """The day's purchase ledger for this pet ({} once the day turns)."""
    tb = getattr(pet, "town_bought", None) or {}
    return tb if tb.get("day") == _today_ordinal(today) else {}


def town_stock(town_id, today=None, pet=None):
    """The town shop's shelves as ready entries [{key,name,price,category,
    base_price,deal,left,town_id}].  The day's rotating deal (and, on a
    FESTIVAL, every row -- the festival market) sells at the canon
    checkSale price: price // SaleFactor.  `left` is the authored maxStock
    minus the day's take (the anti-pump: town prices are DVPet's own,
    far under the catalog -- the daily cap is what makes the demand
    resale a treat instead of a printer)."""
    from . import adventure, persistence
    prog = persistence.get_progress()
    deal = town_deal_sid(town_id, today, prog)
    fest = bool(adventure.active_holiday(today))
    taken = _town_taken(pet, today) if pet is not None else {}
    out = []
    for sid, k, o, local in _open_rows(town_id, prog):
        e = entry(k)
        if not e:
            continue
        on = fest or sid == deal
        price = local // max(1, o["sale_factor"]) if on else local
        # TIERED STOCK (D1, 2026-07-24): rarity now limits how many a town
        # will part with in a day, on the same ladder the road rolls -- a
        # legendary good is one-per-town-per-day, a common one three.  The
        # authored maxStock and the global daily cap still bound it.
        # the authored maxStock and the global cap still bound the shared ration
        left = min(_ration_left(town_id, k, taken),
                   max(0, min(o["max_stock"], TOWN_DAILY_CAP)
                       - int(taken.get(f"{town_id}:{k}", 0))))
        out.append(dict(e, price=max(1, price), base_price=local,
                        deal=on, left=left, town_id=town_id))
    return out


def town_egg_rows(town_id):
    """The town's digitama band as SHOP ROWS (shops-look-the-same,
    2026-07-22: Joel — "the egg tabs in town shops are different than the
    normal shops, why arent these things modulized").  Same entry shape
    the shelf renders everywhere; `egg_idx` rides the existing menu icon
    plumbing (shop eggs draw their real egg frames)."""
    from . import egg as egg_mod
    owned = egg_mod.owned_now()          # earned-but-unbanked counts as owned
    return [{"key": f"egg:{i}", "name": egg_mod.hatch_name(i)[:18],
             "price": egg_price(i), "category": "Digitama",
             "egg_idx": i, "owned": i in owned, "town_id": town_id}
            for i in town_egg_stock(town_id)]


def town_egg_buy(pet, idx):
    """Buy a digitama outright (bits -> persistence.egg_own) -> (msg, sfx).
    THE single buy path — the town egg panel and the shop's Eggs tab both
    call here (single-source law)."""
    from . import data, egg as egg_mod, persistence
    rule = data.load_egg_unlock().get(idx)
    if rule is not None and not rule["can_perm"]:
        # the single buy path guards what the shelf filter promises: a
        # lineage egg is never permanently ownable (egg audit 2026-07-25)
        return ("A lineage egg — it hatches for those who earn it.", "error")
    if idx in egg_mod.owned_now():       # same read as the shelf: never sell
        return ("You already own that egg.", "error")   # what's already earned
    price = egg_price(idx)
    if not pet.spend_bits(price):
        return (f"{price}b — not enough bits.", "error")
    persistence.egg_own(idx)
    return (f"Bought the {egg_mod.hatch_name(idx)} egg — "
            "it's on your carousel!", "reward")


def town_buy(pet, e, today=None):
    """A town counter purchase: blocked once the day's authored stock is
    gone, recorded in the pet's daily ledger otherwise.

    THE LIVE ROW, never the caller's copy (live-play audit 2026-07-25):
    this is the ONE rationed counter door, and it trusted the entry dict
    it was handed -- a stale row replayed after the ration was spent
    oversold the deal at the deal price.  The UI rebuilds rows every
    keypress so no key reaches it today, but any future caller that
    caches a row would mint discounted stock.  Re-fetch the row from its
    own builder and buy THAT: forged/stale `left` and `price` both die
    here."""
    tid = e.get("town_id", HOME_SHOP_ID)
    rows = (home_stock(today, pet) if tid == HOME_SHOP_ID
            else town_stock(tid, today, pet))
    live = next((r for r in rows if r.get("key") == e.get("key")
                 and r.get("left") is not None), None)
    if live is None or live.get("left", 0) <= 0:
        return ("Sold out today — come back tomorrow.", "error")
    e = live
    msg, sfx = buy(pet, e)
    if sfx == "confirm":
        day = _today_ordinal(today)
        tb = getattr(pet, "town_bought", None) or {}
        if tb.get("day") != day:
            tb = {"day": day}                  # a new day sweeps the ledger
        k = f"{e['town_id']}:{e['key']}"
        tb[k] = int(tb.get(k, 0)) + 1
        pet.town_bought = tb
    return (msg, sfx)


def town_sell_price(key, town_id):
    """Buy-low/sell-high: a good this town STOCKS resells at the canon
    local_price // ResellFactor (it has plenty); one it DOESN'T stock is
    in DEMAND -- 70% of catalog price, better than home's half.  The
    trade window: buy a family's exclusive ON DEAL, carry it to the
    OTHER family's towns."""
    hit = _stocked(town_id, key)
    if hit is not None:
        o, local = hit
        return max(1, local // max(1, o["resell_factor"]))
    e = entry(key)
    if not e:
        return 1
    return max(1, e["price"] * TOWN_DEMAND_NUM // TOWN_DEMAND_DEN)
