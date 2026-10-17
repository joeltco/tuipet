"""In-game help — the controls and a quick how-to, so a new player isn't left
staring at single-letter keys (Joel 2026-07-09).  Scrolls in the LCD box; open
with ? from the normal home view."""
from __future__ import annotations
from . import menu
from .theme import INK, INK_B, DIM  # noqa: F401  (palette names bound for theme.apply propagation)

VIS = 8                                   # lines shown at once in the box

# (text, kind): 2 = section head (bold), 1 = a control line, 0 = prose (dim)
HELP = [
    ("FIRST STEPS", 2),
    ("filled Hunger circles = fed", 0),
    ("Fresh = stage; None = no attribute.", 0),
    ("DP diamonds: jogress needs full.", 0),
    ("Power V/D/Vi: Vaccine/Data/Virus.", 0),
    ("Quest: next road map; D CORE: stats.", 0),
    ("Battle/road open at In-Training.", 0),
    ("The egg hatches on its own (~60s).", 0),
    ("PHONE / NAVIGATION", 2),
    ("New name + password creates account.", 0),
    ("Returning? Use the same account.", 0),
    ("ESC at sign-in plays locally.", 0),
    ("Web phone: tap the game to type.", 0),
    ("Web extra-key bar: arrows, ESC, TAB,", 0),
    ("and PGUP/PGDN; ~ also means Escape.", 0),
    ("ENTER confirms; ESC goes back.", 1),
    ("SPACE doubles ENTER on most screens;", 0),
    ("PgUp/PgDn leap through long lists.", 0),
    ("Closing the game pauses its clock.", 0),
    ("Menus pause care and growth too.", 0),
    ("? opens Help from the home view.", 1),
    ("CARE", 2),
    ("f feed - meat fills Hunger circles.", 1),
    ("  Free pill cures sickness, restores", 0),
    ("  energy + Effort; adds weight.", 0),
    ("  Clean up first if it refuses.", 0),
    ("h heal - free bandage for injury;", 1),
    ("  a wound also mends with time.", 0),
    ("c clean poop   o lights out to sleep", 1),
    ("v assistant - Rookie+, paid help:", 1),
    ("  fee per visit + a game-hour wage.", 0),
    ("ENTER accepts a found gift", 1),
    ("Both ailments block fights.", 0),
    ("Untreated ailments raise death risk.", 0),
    ("Ignored calls add ✗ care mistakes;", 0),
    ("they steer forms, reset each stage.", 0),
    ("20 is fatal; 2 game days into an", 0),
    ("Ultimate/Mega stage just 5 can be.", 0),
    ("Energy fuels drills, fights and road;", 0),
    ("sleep refills energy and DP.", 0),
    ("p discipline - scold tantrums;", 1),
    ("  praise proud wins. Ignoring costs", 0),
    ("  manners -5, no care mistake.", 0),
    ("Alarms: one beep routine, two a mess,", 0),
    ("three urgent.", 0),
    ("Tap keys during dying to try rescue.", 0),
    ("Any key skips passive home shows.", 0),
    ("CONTROLS + ROAD", 2),
    ("m battle - wins, exp, training;", 1),
    ("  No purse; costs 5 energy, needs 10.", 0),
    ("  Your rival may answer a home bout;", 0),
    ("  D: PERSON keeps the feud score.", 0),
    ("In fights: SPACE locks the bar.", 0),
    ("PERFECT helps aim, guard and damage.", 0),
    ("SPACE hurries the round animation.", 0),
    ("ESC mid-fight ends or forfeits it.", 0),
    ("a adventure - 30 maps, 5 areas of 6.", 1),
    ("  Beat a boss to open the next map.", 0),
    ("  Clearing an area: eggs + stock.", 0),
    ("  The pet walks automatically.", 0),
    ("  SPACE hurries; wait, then duck.", 0),
    ("  Finds: ENTER, then time SPACE.", 0),
    ("Each road has its own foes + finds.", 0),
    ("On the map list, H picks a hunt.", 0),
    ("Hunts improve odds, not guarantees.", 0),
    ("Some eggs need a wild partner win;", 0),
    ("E names the exact foe and road.", 1),
    ("Hidden and X foes are rarer.", 0),
    ("3 lives; losing a fight costs one.", 0),
    ("No lives ends the run; hurt blocks", 0),
    ("bosses. T items: Rest Kit half energy", 0),
    ("+ patch; Life Recovery lives;", 0),
    ("Shortcut goes straight to the boss.", 0),
    ("Enter towns to rest and resupply.", 0),
    ("Town rest restores lives/energy", 0),
    ("and cures sickness and injury.", 0),
    ("Wild wins can drop items.", 0),
    ("First boss wins give map rewards.", 0),
    ("Replay boss bits: once per real day.", 0),
    ("GROW", 2),
    ("Egg routes vary; some branches stop.", 0),
    ("t train - SPACE times the strike;", 1),
    ("  each try: +1 training, +1 Effort.", 0),
    ("  battles lock their own bar.", 0),
    ("  Battles use their own timing bar.", 0),
    ("d digicore - stats; ↑↓ scroll.", 1),
    ("SPACE on CORE: gaze; elsewhere page", 0),
    ("EVOLVES: ENTER for requirements", 0),
    ("  TROPHIES: ENTER opens the ALBUM.", 0),
    ("  LEGACY: ENTER opens HALL OF MEMORY.", 0),
    ("e egg guide - unlocks + live progress.", 1),
    ("Godzilla G-Cells: 0-472 points.", 0),
    ("Local fights and drills change it;", 0),
    ("pills and care slips lower it.", 0),
    ("Fallen kaiju: next-egg fragment.", 0),
    ("ADVANCED", 2),
    ("l lobby - online; type + ENTER chats.", 1),
    ("  Empty ENTER on a tamer: B battle,", 0),
    ("  J jogress, V/M PM, X block, P ping.", 0),
    ("  @+TAB; PgUp/PgDn scroll; ESC leaves.", 0),
    ("  Jogress opens at Rookie: compatible", 0),
    ("  forms, full DP and enough energy.", 0),
    ("r raid - online account required.", 1),
    ("  SPACE raids; C claims your share.", 0),
    ("  Three attempts per UTC day.", 0),
    ("u cups - Rookie+, each game hour.", 1),
    ("  ENTER/F details; Y pays entry.", 0),
    ("  20 energy. Reload/bracket ESC loses.", 0),
    ("x DNA - steer the next evolution:", 1),
    ("  Generate: wager bits, mash SPACE.", 0),
    ("  Mash rate chooses the Field.", 0),
    ("  A spoiled mash returns half.", 0),
    ("  Charge: banked DNA + energy;", 0),
    ("  stops at empty energy; ties disarm.", 0),
    ("  A leading Field can steer growth;", 0),
    ("  its road and care gates must fit.", 0),
    ("  X: Divergence shows your choices.", 0),
    ("s shop   b bag   n scenes", 1),
    ("  Home stock rotates; towns differ.", 0),
    ("  Towns sell eggs and crests.", 0),
    ("  Buy at most one egg per real day.", 0),
    ("  Some eggs must be earned.", 0),
    ("  Last home shop tab sells HONORS.", 0),
    ("  Capsules: finer in festival months.", 0),
    ("g options   i report a bug   q quit", 1),
    ("  themes, sound, cloud sync,", 0),
    ("  account, updates and home keys.", 0),
    ("LEGACY", 2),
    ("At the grave, choose inheritance:", 0),
    ("E etch its data for your heir", 1),
    ("B keep the care bonus instead", 1),
    ("One etch: E replaces banked data;", 0),
    ("K keeps the elder's.", 1),
    ("n starts the next egg.", 1),
    ("Bits, inventory, trophies and banked", 0),
    ("DNA carry; body/applied DNA reset.", 0),
    ("Unhatched re-picks keep the gen.", 0),
    ("HOLIDAYS", 2),
    ("October: Halloween; December: Xmas.", 0),
    ("A: ghost trail / snow hunts all month.", 0),
    ("2x road bits Oct 31 / Dec 25.", 0),
]


class HelpPanel:
    def __init__(self, pet):
        self.pet = pet
        self.top = 0
        self.frame_i = 0
        self.msg = "How to play tuipet."

    def anim(self):
        self.frame_i += 1

    def strip(self):
        return menu.hints(("↑↓", "scroll"), ("PgUp/Dn", "page"), ("ESC", "back"))

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
