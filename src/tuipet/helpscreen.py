"""In-game help — the controls and a quick how-to, so a new player isn't left
staring at single-letter keys (Joel 2026-07-09).  Scrolls in the LCD box; open
with ? from anywhere on the home screen."""
from __future__ import annotations
from . import menu
from .theme import INK, INK_B, DIM  # noqa: F401  (palette names bound for theme.apply propagation)

VIS = 8                                   # lines shown at once in the box

# (text, kind): 2 = section head (bold), 1 = a control line, 0 = prose (dim)
HELP = [
    ("CARE", 2),
    # claims audit 2026-07-25; re-truthed 2026-07-26 with the bandage's
    # final door, the H key ("bits/hour" was half the assistant's bill)
    ("f feed - meat fills; the pill", 1),
    ("  cures sickness, free and infinite", 0),
    ("h heal - bandage a battle injury,", 1),
    ("  free (a wound also mends with time)", 0),
    ("c clean poop", 1),
    ("o lights   v assistant - paid help:", 1),
    # menus audit 2026-10-14: billing and late-stage clocks use game time.
    ("  a fee per visit + a game-hour wage", 0),
    ("  once it's Rookie or older", 0),
    ("ENTER accepts a found gift", 1),
    # the ✗ counter finally explained (gameplay polish #18, 2026-07-22):
    # it steers every line's CM gates and 20 is lethal -- the single most
    # important growth driver was an unexplained glyph on the status card
    ("Ignored calls add ✗ care mistakes", 0),
    ("(status card): they pick which form", 0),
    ("comes next and reset each stage.", 0),
    # ("elder" was the wrong axis here -- the 5-mistake death is 2 game-days
    # INTO an Ultimate/Mega stage, never the age-15 elder; audit 2026-07-25)
    ("20 is fatal - 2 game days into an", 0),
    ("Ultimate/Mega stage just 5 can be.", 0),
    # the energy dial explained (gameplay polish #6, 2026-07-22): no
    # passive decay BY DESIGN -- it is the ACTION meter, so the gauge only
    # reads "broken" to a player nobody told what spends it
    ("Energy fuels drills, fights and the", 0),
    ("road; sleep refills it each night.", 0),
    # the two ailments, two meds (canon restoration 2026-07-23; the
    # bandage's final door, the H key -- 2026-07-26)
    ("Two ailments: SICKNESS (filth or", 0),
    ("fat) takes the pill, free on F.", 0),
    ("Battle INJURY takes H - free; a", 0),
    ("wound also closes with time. Both", 0),
    ("block fights and whisper to death.", 0),
    ("p discipline - praise & scold:", 1),
    ("  scold a tantrum (+manners), praise", 0),
    ("  a proud win; ignored tantrums", 0),
    ("  cost manners -5, no care mistake", 0),
    # the alarm legend (#8): the ring count is the message
    ("Alarms count the urgency: one beep", 0),
    ("routine, two a mess, three urgent.", 0),
    ("", 0),
    ("EXPLORE", 2),
    ("m battle - fight a matched rival:", 1),
    ("  a real bout (wins, exp, training)", 0),
    # "costs 5" alone implied a bout could start at 5-9 energy; the entry
    # gate is BATTLE_MIN_ENERGY = 10 (audit 2026-07-25)
    ("  but no purse; costs 5 energy (10", 0),
    ("  in the tank to start)", 0),
    # the named rival (Joel 2026-07-26: "build the named rival too")
    ("  every 3rd bout your named RIVAL", 0),
    ("  answers - the feud's score lives", 0),
    ("  on the digicore PERSON page", 0),
    ("a adventure - head out on the road", 1),
    # the 2026-10-14 world: 30 maps, one run each; the fuller page is
    # adventure call #26 = A (Joel 2026-10-15)
    ("  30 maps, 5 areas of 6: fell a map's", 0),
    ("  boss to open the next. Clearing an", 0),
    ("  area opens new eggs + shop stock.", 0),
    ("  Towns sell eggs and crests.", 0),
    ("  SPACE hurries and ducks pounces;", 0),
    ("  a find: time SPACE to dig it up.", 0),
    ("  3 lives - a lost fight costs one,", 0),
    ("  none left ends the run. A hurt pet", 0),
    ("  can't face the boss. T road items:", 0),
    ("  Rest Kit half energy + patch,", 0),
    ("  Life Recovery lives, Shortcut", 0),
    ("  straight to the boss", 0),
    ("r raid - the community boss: fight", 1),
    ("  10-round volleys, break the shared", 0),
    ("  pool together, claim the purse", 0),
    ("u cup - hourly tournaments; win", 1),
    ("  trophies to unlock new eggs; a", 0),
    ("  champion banks the cup's own prize", 0),
    ("l lobby - go online: chat, and", 1),
    ("  battle / jogress other players", 0),
    ("", 0),
    ("GROW", 2),
    ("Eggs hatch, then evolve by HOW you", 0),
    ("raise them - care, train, battles.", 0),
    ("Each egg has its own line to a Mega.", 0),
    # evolution audit 2026-10-14: a chart's Mega route isn't every branch.
    ("Some branches stop early.", 0),
    # final sweep 2026-10-14: explain the Godzilla chart's live dial.
    ("Godzilla G-Cells: 0-472 points.", 0),
    ("Local fights and drills change it;", 0),
    ("pills and care slips lower it.", 0),
    ("A fallen kaiju may leave a fragment", 0),
    ("for your next Godzilla Egg.", 0),
    # "a clean hit saves your battle form" read backwards: EVERY grade
    # saves, only MEGA is worth anything, and fights lock their own bar
    # (battle audit 2026-10-14: proto 4 applies this to lobby duels too)
    ("t train - time the strike: PERFECT", 1),
    # battle audit 2026-10-14: lobby commits a live lock, not the saved drill.
    ("  sharpens aim; every attempt trains", 0),
    ("  effort; battles lock their own bar", 0),
    # the DNA arc told as ONE story (Joel 2026-07-22: "what does dna even
    # do lol" -- the pages teach the pieces, the guide tells the loop)
    ("x DNA - steer the next evolution:", 1),
    ("  wager bits, mash to bank a Field,", 0),
    ("  charge a road Field to its threshold", 0),
    ("  unique leader arms; ties disarm", 0),
    ("  growth picks one road destination", 0),
    ("  charges clear at every evolution", 0),
    ("  energy: -1/unit, off-Field -2;", 0),
    ("  a charge stops at empty energy", 0),
    ("  Effort rises up to three hearts", 0),
    ("d digicore - the pet's data book", 1),
    # DigiCore audit 2026-10-14: SPACE changes meaning after the cover.
    ("  SPACE on CORE: gaze; elsewhere page", 0),
    ("  EVOLVES: ENTER for requirements", 0),
    ("  ↑↓ scroll long rows / requirements", 0),
    ("  ENTER on its trophy page opens the", 0),
    ("  ALBUM - every species, in dex order", 0),
    # the lineage's own book (Joel 2026-07-26: "build the hall of memory")
    ("  on its LEGACY page, the HALL OF", 0),
    ("  MEMORY - every elder, remembered", 0),
    ("e egg guide - every digitama + what", 1),
    ("  earns it, with live progress", 0),
    ("", 0),
    ("MANAGE", 2),
    ("s shop   b bag   n scenes", 1),
    ("  the shop's last tab sells HONORS -", 0),
    ("  titles that ride your status card", 0),
    # the expansion (2026-07-26): the one line the capsules need
    ("  a CAPSULE opens into a surprise,", 0),
    ("  finer on festival days", 0),
    ("g options   i report a bug   q quit", 1),
    ("  themes, sound, cloud sync, your", 0),
    ("  account, updates, every key", 0),
    # honest reach (help audit 2026-07-22): with a screen open every key
    # belongs to that screen -- ? answers from home.  SPACE=ENTER holds on
    # MOST screens, not all (digicore pages on SPACE; the road prompts
    # split the pair -- ENTER enters/digs, SPACE walks on; the erase
    # confirm types) -- hence "most" below (claims audit 2026-07-25)
    ("? this guide, any time you're home", 1),
    ("SPACE doubles ENTER on most screens;", 0),
    ("PgUp/PgDn leap through long lists.", 0),
    ("", 0),
    ("LEGACY", 2),
    ("Neglect, hunger, sickness or age", 0),
    ("take it in the end. The grave asks", 0),
    ("what carries to the next one:", 0),
    ("E etch its data for your heir", 1),
    ("B keep the care bonus instead", 1),
    ("Only one etch may stand: if data is", 0),
    ("already banked, E takes the new one,", 0),
    ("K keeps the elder's.", 0),
    ("n starts the next egg.", 1),
    # egg audit 2026-10-14: explain the existing estate and re-pick rules.
    ("Bits, inventory, trophies and", 0),
    ("banked DNA carry; body and applied", 0),
    ("DNA reset. Unused data carries too.", 0),
    ("Unhatched re-picks keep the gen.", 0),
    ("", 0),
    ("TIPS", 2),
    ("Feed when hungry, clean the poop,", 0),
    ("and let it sleep at night. Win cups,", 0),
    ("fell raids, link with tamers, play a", 0),
    ("festival for free egg unlocks; towns", 0),
    ("also sell permanent egg shortcuts.", 0),
]
# (the full item catalog was tried in the guide 2026-07-24 and REVERTED:
# it doubled the guide's length and only mirrored what the shop dossier
# already shows live -- name, price and effect -- at the point of purchase.
# The shop is the item reference; the guide teaches the systems.)


class HelpPanel:
    def __init__(self, pet):
        self.pet = pet
        self.top = 0
        self.frame_i = 0
        self.msg = "How to play tuipet."

    def anim(self):
        self.frame_i += 1

    def strip(self):
        return menu.hints(("↑↓", "scroll"), ("ESC", "back"))

    def _max_top(self):
        return max(0, len(HELP) - VIS)

    def key(self, k):
        if k in ("up", "k"):
            self.top = max(0, self.top - 1)
        elif k in ("down", "j"):
            self.top = min(self._max_top(), self.top + 1)
        elif k == "pageup":                  # page jumps, lobby-chat style
            self.top = max(0, self.top - (VIS - 1))
        elif k == "pagedown":
            self.top = min(self._max_top(), self.top + (VIS - 1))
        elif k in ("escape", "question_mark"):
            # ? (the opening key) also closes; q now falls through to the
            # global save-and-quit like every other screen -- help was the
            # one panel where q meant something else (tidy audit 2026-07-18)
            return ("done", None)
        return None

    def _more_cue(self):
        """A scroll affordance for the footer -- it says THERE IS more (the
        message strip already says HOW to move), so the two never echo."""
        up, dn = self.top > 0, self.top < self._max_top()
        if up and dn:
            return "▲▼ more"
        if dn:
            return "▼ more below"
        if up:
            return "▲ more above"
        return ""

    def text(self):
        self.top = max(0, min(self.top, self._max_top()))
        pos = "%d-%d/%d" % (self.top + 1, min(self.top + VIS, len(HELP)), len(HELP))
        out = menu.header("HELP", pos)
        for text, kind in HELP[self.top:self.top + VIS]:
            style = INK_B if kind == 2 else (INK if kind == 1 else DIM)
            out.append((text or " ") + "\n", style=style)
        out.append_text(menu.footer(self._more_cue()))
        return out
