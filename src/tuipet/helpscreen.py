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
    ("  a fee per visit + an hourly wage", 0),
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
    ("20 is fatal - and 2 days into an", 0),
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
    ("  cost a care mistake", 0),
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
    # the 2026-10-14 world: 30 maps, one run each
    ("  cross a map, fell its boss to open", 0),
    ("  the next. Towns sell eggs and", 0),
    ("  map clears unlock more of them", 0),
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
    # "a clean hit saves your battle form" read backwards: EVERY grade
    # saves, only MEGA is worth anything, and home fights lock their own
    # bar -- the saved form is what LOBBY rivals face (audit 2026-07-25)
    ("t train - time the strike: PERFECT", 1),
    ("  locks the power form your lobby", 0),
    ("  rivals will face", 0),
    # the DNA arc told as ONE story (Joel 2026-07-22: "what does dna even
    # do lol" -- the pages teach the pieces, the guide tells the loop)
    ("x DNA - steer the next evolution:", 1),
    ("  wager bits, mash to bank a Field,", 0),
    ("  charge ONE Field to its threshold;", 0),
    ("  the next evolution takes that road", 0),
    ("d digicore - the pet's data book", 1),
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
    ("", 0),
    ("TIPS", 2),
    ("Feed when hungry, clean the poop,", 0),
    ("and let it sleep at night. Win cups,", 0),
    ("fell raids, link with tamers, play a", 0),
    ("festival - every egg is earned.", 0),
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
        return menu.hints(("↑↓", "scroll"), ("ESC", "out"))

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
