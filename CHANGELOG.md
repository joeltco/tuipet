# Changelog

Player-facing notes per release — the same line each version shows on its
title screen. Full commit history: [GitHub](https://github.com/joeltco/tuipet/commits/main).

## 0.5.209 — THE BANDAGE HAS ITS ANIMATION BACK (2026-07-23)

THE BANDAGE HAS ITS ANIMATION BACK: treating an injured pet now plays the real DVPet bandaging sequence — the dressing is held up, pressed on, and worked through its four frames while your pet holds still, then cheers when it is patched up.

## 0.5.208 — EVERY CONSUMABLE IS EATEN NOW (2026-07-23)

EVERY CONSUMABLE IS EATEN NOW: vitamins, both drinks, the sleep and caffeine pills and the anti-evo chip all play the eating animation with their own ripped artwork, instead of flashing a line of text. The pill always worked this way — now the whole shelf does.

## 0.5.207 — ITEMS PUT ON A SHOW (2026-07-23)

ITEMS PUT ON A SHOW: the textbook now opens and pages while your pet studies, the dumbbell gets lifted, the grow capsule is read, the music player plays — animations that were fully drawn but never wired. Also fixed: a Vitamin's injury guard was lasting essentially forever instead of a day.

## 0.5.206 — DISCIPLINE IS BACK (canon) (2026-07-23)

DISCIPLINE IS BACK (canon): press P to praise or scold. Your pet now throws the occasional tantrum — scold it for +25 manners; ignoring it costs a care mistake. Wins and clean training strikes open proud moments worth praising (+10). The manners gauge lives on the DigiCore PERSON page.

## 0.5.205 — INJURY IS BACK (canon) (2026-07-23)

INJURY IS BACK (canon): battles can wound — especially losses in poor condition — and a hurt pet can't fight until you treat it with the BANDAGE (new in the shop, the device's second med). A Vitamin now also guards against injury for a day. Plus the Pendulum rule: a shaky bar lock costs nothing, and every fight names what's dragging you before the bell.

## 0.5.204 — BATTLES STOP STARVING YOUR PET (2026-07-23)

BATTLES STOP STARVING YOUR PET: every bout sheds weight, and it could grind a pet 30g below its species base — a huge hidden accuracy penalty that grew the MORE you fought. Weight now floors at the species base, like training and travel always did. If your pet is thin, feed it back up — every gram toward base is hit chance back.

## 0.5.203 — DUEL WITH OPEN EYES (2026-07-23)

DUEL WITH OPEN EYES: a tamer's saved lock now shows in the lobby — on the roster blurb, the challenge menu and the invite prompt ("Agumon · Champion · lock mega") — and the fight header shows both locks. A lock swings a duel hard now; nobody should accept one blind.

## 0.5.202 — THE LOCK DECIDES (2026-07-23)

THE LOCK DECIDES: a clean mega lock on the battle bar now steadies your aim AND your guard — hitting the center wins about 4 fights in 5 even untrained, 9 in 10 trained. Equal locks cancel in PvP, so it stays fair. If you hit the center, you win.

## 0.5.201 — YOUR LOCK, ON THE CARD (2026-07-23)

YOUR LOCK, ON THE CARD: every battle now shows the timing grade you locked (mega / normal / miss) on the status card for the whole fight — training always showed its grade, battles never did. No more losing with no idea why.

## 0.5.200 — THE BATTLE BAR NO LONGER EATS YOUR MASH (2026-07-23)

THE BATTLE BAR NO LONGER EATS YOUR MASH: pressing SPACE through the battle intro used to lock the timing bar instantly at the left edge — a miss you never aimed. The bar now arms half a second after it appears, so only a deliberate press locks it. Your training megas were always real; now battles are too.

## 0.5.199 — AN HONEST TIMING BAR (2026-07-23)

AN HONEST TIMING BAR: if you saw the marker hit the center, you hit the center — the lock now forgives the split second between your eyes and your keyboard, the whole 2-pixel marker counts, and the center zone never shrinks below a humanly possible size. Same bar in training and every battle.

## 0.5.198 — THE BATTLE KEY (2026-07-23)

THE BATTLE KEY: press M to fight a rival of your pet's own stage, right at home. It's a real bout — wins, experience and training all count — but pays no bits (adventure keeps the purse), and each fight spends 5 energy, so the tank paces the brawling.

## 0.5.197 — TRAINING IN THE LEDGER (2026-07-23)

TRAINING IN THE LEDGER: the DigiCore POWER page's Drills row now shows both counts that feed the fight — lifetime drills (never reset) and this stage's (they gate evolution and reset when it evolves). The stage count was always working; now you can watch it.

## 0.5.196 — THE WARP OPENS THE DOORS (2026-07-23)

THE WARP OPENS THE DOORS: a Town Transport now lands you at the town for real — after the rest, you get the same visit-or-walk-on choice as arriving on foot, shop and all. It used to rest you and march straight past the town you paid a ticket to reach.

## 0.5.195 — A REAL NIGHT'S REST (2026-07-23)

A REAL NIGHT'S REST: an adventure town now rests your pet to at least HALF its energy tank (it used to give one battle's worth — 'rested up' that a single fight erased). Above half, towns still top you up toward full. The win streak still breaks — rest for safety, pay with the chain.

## 0.5.194 — ROAD SAFETY (2026-07-23)

ROAD SAFETY: a Sleep Pill can no longer be taken on the road — it used to freeze the march in a nap that never ended. And when a spent pet plants its feet out there, the message now names the real ways out (warp to a town or head home) instead of promising a rest the road can't give.

## 0.5.193 — THE GLOOM CLOUD (2026-07-23)

THE GLOOM CLOUD: a discouraged pet finally shows it — the sulk now wears a little storm-cloud emote beside its head, the true opposite of the happy sunshine dance. Real extracted art that's been sitting unused in the sprite files, wired up at last.

## 0.5.192 — A RICHER WORLD (2026-07-23)

A RICHER WORLD: adventure digs now match the land — fish by the seafloor, steak in the mountains, video games in the city — and each map's FINAL zone digs a rare tier worth the march. Every town shop got character too: each map sells a regional specialty (the hardest region stocks the Revive Floppy), and all 26 towns now carry a different signature good — no two shops in the world are alike.

## 0.5.191 — THE RECOVERY DOZE (2026-07-23)

THE RECOVERY DOZE: a drained pet's nap no longer wakes after one bar — lights off, it now sleeps straight through until half its energy is back (and past empty it recovers double-speed), so you don't have to babysit a wake-and-drain loop. Lights on still rouses it. And an empty tank finally says so: status reads "exhausted" instead of "ok".

## 0.5.190 — QUALITY OF LIFE, ROUND 4 (2026-07-23)

QUALITY OF LIFE, ROUND 4 — the lobby feels the network: a dead connection fails fast instead of freezing "Connecting…" for ten seconds, the banner says whether you dropped or never got through, ENTER retries right now instead of waiting out the backoff, chat sent while offline says it's queued, the ladder page can time out and retry, long login messages scroll instead of clipping, and your password shows its last letter while you type it — so the account you create is the one you meant.

## 0.5.189 — QUALITY OF LIFE, ROUND 3 (2026-07-23)

QUALITY OF LIFE, ROUND 3 — home & care: satiety, auto-clean and a hired assistant now wear little badges on the status card, the feed menu warns when Meat would be refused, the lights LED actually follows the lights, SPACE accepts gifts too, keys pressed during a care show answer with a soft click instead of dead silence, and at the grave N really does open the new-egg carousel like the card promises.

## 0.5.188 — QUALITY OF LIFE, ROUND 2 (2026-07-23)

QUALITY OF LIFE, ROUND 2 — menus & shops: the shop remembers where you left off (per tab, and across visits), prices you can't afford show dim across the whole shelf, emptying a stack in the bag can no longer sneak your next press onto a neighbor, the Album and Egg Guide wrap top to bottom and page inside the book, and the menu screens dropped their stale key footers — the hint strip is the one true key line.

## 0.5.187 — QUALITY OF LIFE, ROUND 1 (2026-07-23)

QUALITY OF LIFE, ROUND 1: ESC now ends a decided battle in one press (SPACE still hurries beat by beat, and the hints show on the strip), skip presses no longer vanish at round boundaries, a sick pet's feed menu opens right on the Pill, and a spent pet on the road tells you it needs rest instead of begging to be urged.

## 0.5.186 — EASIER ON THE EARS (2026-07-23)

EASIER ON THE EARS: fresh installs now start at 50% volume instead of full blast. Your saved volume setting is untouched — this only picks the starting point for new tamers (Options → Sound to taste, as always).

## 0.5.185 — STATUS CARDS HOLD THEIR LINES (2026-07-23)

STATUS CARDS HOLD THEIR LINES: a full card audit found text running off the 26-column card and wrapping — the DNA header with a long pet name, the feed dossier, a memorial's long cause of death. All pre-fit now, and a 40-state sweep test renders every card with worst-case names and numbers so a run-off can never ship again.

## 0.5.184 — NO MORE 5/10 AT THE BELL (2026-07-23)

NO MORE 5/10 AT THE BELL: a raid's intro frames (the banner and the foe reveal) carry no HP and fell back to the classic battle's literal 5 — so your tank read 5/10 through the intro, snapping to 10/10 when the fight started. The fallback is raid-aware now: 10/10 from the very first banner frame.

## 0.5.183 — THE BOSS GETS A STAGE (2026-07-23)

THE BOSS GETS A STAGE: the raid page was cramming the 16px boss edge-to-edge in a 16px band — head on the header, feet on a wall of text that DUPLICATED the status card (pool, tries, rank, countdown, twice each on one screen). The LCD is pure scene now, the family law: a tall 10-row stage with sky above the boss and the arena floor under its feet, one context line, and every number lives once — on the card, which now also carries the leaderboard.

## 0.5.182 — RAIDS CLEANED UP (2026-07-23)

RAIDS CLEANED UP: the boss page's stats line could run wider than the LCD and wrap the whole bottom of the screen into a garbled mess — it pre-fits now, and the page holds exactly 12 rows. The boss stands on the arena FLOOR instead of floating over a sky-band crop. And the status card during a volley finally tells the truth: your tank out of 10, the boss's health as the COMMUNITY POOL percentage — never again a 5.5-million-HP boss wearing a five-heart bar.

## 0.5.181 — THE DODGE IS A REAL REFLEX NOW (2026-07-23)

THE DODGE IS A REAL REFLEX NOW: road ambushes used to accept SPACE anywhere in the whole 1.6-second beat — and since SPACE also hurries the march, your mash won dodges by accident before the ! even registered. New grammar, one press per ambush: '! ! ! wait for it…' during the warning (jump early and the duck is SPENT), then 'NOW! — SPACE' as it lunges. Duck the window, eat the pounce, or jump too soon — your reflexes decide, not your mash.

## 0.5.180 — DEAD FOES DON'T SHOOT (2026-07-22)

DEAD FOES DON'T SHOOT: battles used to resolve both volleys at once, so a foe you just dropped to zero still landed its return shot AFTER its bar emptied — and the replay had to show the ghost hit. The engine now resolves in the order the theater plays: your volley first, and a killing blow ends the round on the spot. NPC bracket matches flip a coin for initiative so no entrant gains an edge from list order.

## 0.5.179 — ONE FIGHT, ONE CARD · ONE SHOP, ONE LOOK (2026-07-22)

ONE FIGHT, ONE CARD · ONE SHOP, ONE LOOK: every battle now shows the same live status card — HP bars, foe, verdict — whether it's a cup bout, a wild on the road, the town cup, or a raid volley (the road used to show generic vitals mid-fight). And the town egg market moved onto the shop's own Eggs tab: same tab bar, same shelf, same dossier as every other counter — no more one-off grid screen. One shop family everywhere.

## 0.5.178 — THE SICK CALL POINTS AT THE RIGHT KEY (2026-07-22)

THE SICK CALL POINTS AT THE RIGHT KEY: the alert said 'sick! (I — use a pill)' — but the pill is the FEED menu's second row, free and infinite, not a bag item. A panicked tamer got sent to the wrong screen. It now says 'sick! (F — feed it the pill)'.

## 0.5.177 — THE MORNING TELLS THE TRUTH (2026-07-22)

THE MORNING TELLS THE TRUTH: a good-morning roll used to say 'woke up beaming!' even over a nearly empty energy gauge — a cut-short night (a dawn re-sleep, a midnight bedtime, the 7:00-sharp wake) can end before the tank refills, and beaming over one bar read as a bug. A good morning on a drained tank now says 'up — still weary…'. The sleep audit behind it verified the refill math (a full night fully refills, drained pets recover double) and every action door on a sleeper (refuse or wake-and-grumble, never a silent drain).

## 0.5.176 — EVERY MON MOVES WHEN IT SHOULD (2026-07-22)

EVERY MON MOVES WHEN IT SHOULD: a roster scan found ~35 species whose sheets fill a pose-flip with one identical frame — Bubbmon's dance was frozen solid, others froze their tantrums, startles or wash. Those flips now alternate with a different REAL frame of the same species (its bob), so celebration and agitation always MOVE. Sleep stays exempt on purpose: a still sleeper is the pose. Nothing is drawn — rips only, as always.

## 0.5.175 — BUBBMON DANCES (2026-07-22)

BUBBMON DANCES: a few sprite sheets fill several pose slots with one identical frame — Bubbmon's happy dance and poopdance flipped between two copies of the same image, freezing solid. When a pose-flip resolves to one bitmap, the dance now alternates with a different REAL frame of the same species (its bob), so every mon moves when it celebrates. Nothing is drawn — rips only, as always.

## 0.5.174 — THE EGG WEARS ITS NAME (2026-07-22)

THE EGG WEARS ITS NAME: the carousel's status card now titles the digitama you're browsing — matching an egg to its egg-guide entry used to mean matching the art by eye. The hatch line still names only the destined BABY: an egg will never promise to hatch an egg.

## 0.5.173 — THE DODGE IS REAL NOW (2026-07-22)

THE DODGE IS REAL NOW: ducking an ambush used to make the attacker blink out of existence mid-air — the sail-past hid it behind your mon's own pixels for the whole beat, so a clean SPACE-dodge looked like a glitch. The strike now WHIFFS: the pouncer pulls up short of your crouch and visibly retreats off the right edge, on screen for every tick of the beat. Ducking finally looks as good as it feels.

## 0.5.172 — THE ROAD LOOKS RIGHT (2026-07-22)

THE ROAD LOOKS RIGHT: an adventure animation audit fixed every pop and vanish — ambushers no longer strike from off-screen (your mon scrambles to the wall as the ! blinks), the dug-up treasure never smears over the pet, Life Recovery finally LOOKS like a second wind, runs open without the 8px teleport pop, turn-backs leave from where you stood, a right-side sleeper's zzZ flips to the free side, and parade bosses march in through the edges like everyone else. Every scene is now pixel-pinned in place.

## 0.5.171 — THE FIGHT TALKS BACK (2026-07-22)

THE FIGHT TALKS BACK: the result card now says WHY — won by a whisker or with HP to spare, a draw names the draw-counts-as-loss rule, and a loss coaches the biggest fixable drag (weight off base, an empty belly, low energy, outranked, or just train more). The timing bar finally matters: a clean mega steadies your aim, a shank shakes it. Cups ramp — the semi fights part-trained, the final near-veteran. Plus: alarms ring 1×/2×/3× by urgency, a happy well-kept mon actually bounces again, gen-1 tamers start with 250 bits, every town keeps its own guest good, and the honors ladder climbs to a million.

## 0.5.170 — EVERY ??? HAS A ROAD HOME (2026-07-22)

EVERY ??? HAS A ROAD HOME: an undiscovered album entry used to say only 'keep raising' — with hundreds of masked forms and no map, the collection endgame had no compass. Each ??? now names its route: the digitama line that raises it, or the door that reaches it off the charts — an armor jump, a jogress, or a Field divergence. Routes name eggs and doors, never the forms themselves: the surprise stays sealed.

## 0.5.169 — THE FIRST HOUR EXPLAINS ITSELF (2026-07-22)

THE FIRST HOUR EXPLAINS ITSELF: every care call now names its key (hungry F, sick I, cleaning C — lights always said S), help finally explains the ✗ care-mistake counter that steers every evolution (20 is fatal, 5 for a frail elder) and names the assistant's bits-per-hour retainer, and the egg wait has a shape: the card counts down to hatch and the HUD holds the help pointer for the whole wait instead of flashing it for 4 seconds.

## 0.5.168 — THE QUIET STATES SPEAK UP (2026-07-22)

THE QUIET STATES SPEAK UP: a lone poop pile now asks for a tidy-up in the idle HUD (text only — the 3-pile alarm keeps its job), frailty finally rings its alarm the moment an Ultimate/Mega crosses 3 care mistakes (the one lethal state was the only silent one), and your mon's morning tier reaches the HUD — wake up beaming, on the wrong side, or from an awful night, you'll hear about it instead of guessing from a 2-second pose.

## 0.5.167 — THE CORE NUMBER SAYS WHICH WAY IT COUNTS (2026-07-22)

THE CORE NUMBER SAYS WHICH WAY IT COUNTS: the DigiCore's ◆ meter was a countdown-to-evolve on a growing pet and an age-count on a final form — the same bare glyph, opposite directions. It now reads '◆ 7 to evolve', '◆ 7 of 14 to elder', or '◆ 16 — elder', so one glance tells you whether the core is filling toward a new form or the mon is simply getting old.

## 0.5.166 — DNA TEACHES ITSELF (2026-07-22)

DNA TEACHES ITSELF: the Charge screen now tells you both truths where you spend — charging arms the Divergence road (the line climb ignores it) AND charges clear at every evolution, so arm before the clock fills. The DNA menu names the whole loop in one line, and an armed steer now rides the main-view HUD — no more divergences firing hours after you forgot you set one.

## 0.5.165 — THE DATA BOOK STOPS LYING (2026-07-22)

THE DATA BOOK STOPS LYING: with a DNA divergence armed, the DigiCore's gaze and EVOLVES chart still promised your line's next form — a future the steer was about to override. Now the armed target rides the top of the chart wearing its own ✓ armed tag, the gaze teases the form that will actually come, and ENTER on the armed row reports the charge that fired it. The line rows stay below: another Field catching up re-steers, and a tie disarms.

## 0.5.164 — THE ROAD SHELF IS OPEN (2026-07-22)

THE ROAD SHELF IS OPEN: Town Transport, Disaster Transport and Life Recovery have been in the catalog since v0.5.114 — but no shop tab ever carried the Adventure shelf, so nobody could ever buy one. They now sell under Items (home shop AND town counters, map-clear gates unchanged), show in the bag, and Life Recovery finally does its job: press T on the road for a second wind — hearts back to full where you stand.

## 0.5.163 — A CLOSED GAME IS A STOPPED CLOCK (2026-07-22)

A CLOSED GAME IS A STOPPED CLOCK: your pet no longer lives without you. Quitting used to keep it aging, growing, getting hungry and making a mess for up to 36 hours — an egg could even hatch while you were gone. Now nothing happens while you're away. Come back in five months and your mon is exactly as you left it.

## 0.5.162 — EVERY MENU PAUSES NOW (2026-07-22)

EVERY MENU PAUSES NOW: the lobby was the one screen that kept your pet's clock running — chat for an hour and come back to a hungrier, older mon. It doesn't anymore. Open a menu, any menu, and life waits for you.

## 0.5.161 — THE RECORD CATCHES UP (2026-07-22)

THE RECORD CATCHES UP: the changelog now carries every release of this wild week — the album, the DSprite mortality, the audits, the town cup's show — and from here on, every release writes its own entry the moment it ships.

## 0.5.160 — THE GUIDE TELLS THE DNA STORY (2026-07-22)

THE GUIDE TELLS THE DNA STORY: what DNA is FOR, in one breath — wager bits, mash to bank a Field, charge ONE Field to its threshold, and your next evolution takes that road instead of the chart's. The album's 1218 species are the reason. It was always true; now it's taught.

## 0.5.159 — DNA, FRAME BY FRAME (2026-07-22)

DNA, FRAME BY FRAME: the charge ceremony was audited beat by beat. The chip now sinks fully away at the end instead of blinking out at the floor, and everything else held under the glass — the descent from behind the bezel, the wobble, the wash, the strain, the mash bob and strike flash, and the result's blinking reveal.

## 0.5.158 — THE TOWN CUP GETS ITS SHOW (2026-07-22)

THE TOWN CUP GETS ITS SHOW: the road's championships used to throw you into three bare fights. Now the town cup stages the full event — the field of eight on the bracket, the faceoff, the walk-in introductions, the advancing-field parade, and the champion's podium — the same theater the home cups earned.

## 0.5.157 — THE SHELF TELLS THE TRUTH (2026-07-22)

THE SHELF TELLS THE TRUTH: every shop blurb was checked against what the item actually does — all 36 held, every dial, timer and refusal. And for the cautious: the X-Antibody chip is confirmed SAFE, and always was. The deadly roulette people whisper about belonged to a different item that left the shelf long ago. The mushroom, however, remains exactly as labeled.

## 0.5.156 — THE DNA CHIP FITS THE MOUTH (2026-07-22)

THE DNA CHIP FITS THE MOUTH: charging DNA feeds a field badge to your pet — and that badge was rendering nearly pet-sized, a 14px chip meant for a much taller screen. It now feeds in at proper chip scale, the same way food is scaled for the eating animation.

## 0.5.155 — DNA UNDER THE MICROSCOPE (2026-07-22)

DNA UNDER THE MICROSCOPE: a full audit of the wager, the bands, the charge bills and the Divergence roads — on tuipet's own terms. The math all held. Two truths now get said out loud: an edge-band resonance splashes ONE neighbor (the page claimed both), and the Divergence page warns that charges clear at every evolution — arm before the climb, or the charge dies with it.

## 0.5.154 — THE EGG GUIDE TELLS THE TRUTH TOO (2026-07-22)

THE EGG GUIDE TELLS THE TRUTH TOO: every digitama's unlock story was checked against its real gate. Two were tall tales — Dokimon asked for 'a Mega tournament in Summer' and Hack Egg a 'Fall Champion Cup' that never existed. Both now name the exact cup they want: Summer Open #147 and Fall Open #188. Go win them.

## 0.5.153 — THE GUIDE TELLS THE TRUTH (2026-07-22)

THE GUIDE TELLS THE TRUTH: a full audit checked every line of the help (?) against the game as it actually plays. Verdict: nearly all of it holds — two promises were trimmed to honest ('? answers from home', 'SPACE doubles ENTER on most screens'), and a new test makes sure every key on the bar stays taught forever.

## 0.5.152 — EVERY THEME, LEGIBLE (2026-07-22)

EVERY THEME, LEGIBLE: a contrast audit ran every menu under all eight themes. Your bits were nearly invisible in grey and gameboy — the coin gold now reads dark and clear in both. Six themes came through spotless, and a new test stands guard so no palette edit can ever ship grey-on-grey.

## 0.5.151 — MENU POLISH, ROUND FIVE (2026-07-22)

MENU POLISH, ROUND FIVE: the road's towns and the cup's fight pages went under the glass. One thing read wrong: the faceoff's bare 'Trophy 0' sat beside the challenger's name like it was THEIR record — it now says 'your ★N', the same star your status card wears.

## 0.5.150 — MENU POLISH, ROUND FOUR (2026-07-22)

MENU POLISH, ROUND FOUR: a deep sweep of the screens behind the screens — DNA's five sub-pages, the egg stories, the raid board, the grave's own prompts. One fix shipped: the bag's item count now counts exactly what its shelves can show, so the header can never claim goods you can't see.

## 0.5.149 — MENU POLISH, ROUND THREE (2026-07-22)

MENU POLISH, ROUND THREE: the cup board wears one clean tag per row now — OPEN, then alarm, then +item — instead of cramming both into a slot that cut them mid-word. And the lobby ladder says 'season resets today' when it means today, not 'in 0 days'.

## 0.5.148 — THE LIFE BAR IS GONE (2026-07-22)

THE LIFE BAR IS GONE — and that's the point. No clock counts your pet down anymore. Death rolls the dice the old way now: care mistakes, sickness and old age each raise the odds, and a well-kept young pet simply cannot die. Keep it fed, clean and healthy, and let the days add up.

## 0.5.147 — NO MORE SILENT BURNS (2026-07-22)

NO MORE SILENT BURNS: every cost to your pet's life now announces itself. A missed hunger call, collapsing past empty in battle, a rough birthday — each one flashes its toll and the pet jeers, same as illness and the X-Antibody already did. When the Life bar moves, you'll know exactly why.

## 0.5.146 — THE CORE SHOWS ITS DOOR (2026-07-21)

THE CORE SHOWS ITS DOOR: the digicore's gaze — the silhouette tease of what your pet may become — was easy to walk right past. The CORE page now says it in bold: SPACE: gaze into the core. And if you missed it, the ALBUM is new too — ENTER on the trophy page opens the full bestiary of every species you've ever raised.

## 0.5.145 — THE ALBUM OPENS (2026-07-21)

THE ALBUM OPENS: the digicore trophy page's 'Album 0/1218 discovered' was a scoreboard pointing at a book that didn't exist. Press ENTER on the TROPHIES page and the book is real — every species in dex order, the ones you've raised wearing their name, stage and living sprite, the rest a silhouette and a ??? still waiting to be earned. The guide (?) knows the way there too.

## 0.5.144 — THE ALBUM OPENS (2026-07-21)

THE ALBUM OPENS: the digicore trophy page's 'Album 0/1218 discovered' was a scoreboard pointing at a book that didn't exist. Press ENTER on the TROPHIES page and the book is real — every species in dex order, the ones you've raised wearing their name, stage and living sprite, the rest a silhouette and a ??? still waiting to be earned.

## 0.5.143 — MENU POLISH, ROUND TWO (2026-07-21)

MENU POLISH, ROUND TWO: the shop's Honors tab held its prices four columns left of every other shelf — now the price column stands still when you tab across. And the digicore STATUS page speaks one language for nothing: an unnamed pet and an empty Field both read — instead of a blank and a bare hyphen.

## 0.5.142 — THE LIFE BAR BITES BACK (2026-07-21)

THE LIFE BAR BITES BACK: the life meter is your pet's master death clock, and now neglect actually feeds it. Falling ill from filth or overweight, and taking the X-Antibody, both BURN life again — canon costs that had gone silent — and the pet jeers as they land, so you SEE the bar react instead of watching it drift.

## 0.5.141 — MENU POLISH (2026-07-21)

* **No word runs off a menu.** A heavy-duty sweep of every screen: the
  lobby room footer now says **ESC leave** in full (its old fit-fix had
  dropped the word), the cup bracket's **ESC forfeit** hint fits every
  round name, the memorial strip labels its ESC, the DNA pages spell
  **Nightmare Soldier** (and every field) whole at word boundaries, and
  an unnamed mon's cup intro reads "You answer!" — proper grammar.
* Behind the glass: a menu contact sheet (`tools/menu_sheet.py`) that
  renders every menu state as visible ASCII, and a run-off test net
  pinning the fixes plus a smoke walk over 19 panels.

## 0.5.140 — DEFENDING CHAMPION (2026-07-21)

* **Cups you hold are titles to defend.** The board crowns them (♛), the
  gate announces the defense, and the bracket knows: all seven entrants
  fight **trained** — the same veteran tier as replayed adventure zones
  — while the purse pays **half again** on the same stake. Simulated
  honest: a defense is about one stage harder than a fresh cup, the
  fatter pot keeps it break-even, and a successful defense pays like
  the achievement it is. Town cups defend the same way. The rival and
  the defense announce together when your grudge is in a field you're
  defending — the grand cup drama, complete.

## 0.5.139 — THE RIVAL (2026-07-21)

* **Cup losses have a face now.** The mon that beats you in a fought
  match becomes your **rival** — it re-seeds into every future bracket
  its tier fits (one guaranteed slot, never breaking a cup's stage
  walls), wears a `!` on the bracket tree, gets announced at the gate,
  and the match introductions call it what it is: "— your RIVAL!"
  Walking out of a bracket names nobody; only a real beating earns the
  grudge. Beat your rival anywhere and it settles: **REVENGE!** — clean
  slate until the next mon takes you down. The grudge survives saves
  and evolution; a new generation starts unburdened. No economy touch —
  pure nemesis.

## 0.5.138 — MATCH INTRODUCTIONS (2026-07-21)

* **Every cup match opens like the main event.** SPACE on the faceoff
  page no longer jump-cuts to the fight: the challenger strides in from
  the right and is announced by name, your mon answers from the left,
  the stare-down holds ("Quarterfinal — FIGHT!") — then the bell rings
  itself. The walk-ins land exactly on the fight's corners, the
  entrances clip lawfully at the window, and the show plays out (no
  skips). The faceoff page is still the decision point — ESC backs out
  before you commit; a re-entered match earns its entrance again.

## 0.5.137 — CUP THEATER (2026-07-21)

* **The field advances, visibly.** After each of your wins, the bracket's
  other winners cross the arena one at a time — real roster sprites,
  named as they pass — before the bracket page lands. Three crossings
  after the quarterfinal, one after the semi. The tournament finally
  happens *around* you instead of in a sentence.
* **The award ceremony.** Winning the final no longer cuts to text: your
  champion cheers centre-stage while the arena light pulses on the beat,
  the star row builds, and *then* comes the crowned tree and the purse.
  The elimination path keeps its canon consolation unchanged.
* Both shows lock input and play out — no skips, same law as every
  adventure beat.

## 0.5.136 — THE CUP AUDIT (2026-07-21)

* **All cups audited** — the 325-cup home board, the hourly schedule, the
  featured cup, festival entries, and the town cups. The economy checked
  out clean (break-even for coin-flip pets, skill and care pay, no
  faucets, no save-scum holes). Three edge faults fixed:
* **Town cups vet your mon now.** The road bracket ran no pet gates — a
  starving, sick, or napping pet could fight three recorded bouts. It
  runs the same checks as the home board (a dozing entrant gets woken by
  the poke, like every care key). A refused pet keeps its once-per-visit
  cup for later.
* **Town trophies wear their name.** The trophy room read "cup 912" for
  road trophies; it says "Town Cup #13" now.
* **The cup board fits its box** — the featured row ran 44 of 40 columns
  and clipped; trimmed, and the board joined the render-budget net.

## 0.5.135 — THE ROAD CLIMBS IN ORDER (2026-07-21)

* **The unlock road is sorted by difficulty now.** A Monte-Carlo balance
  audit over the real battle engine showed the old zone order was full
  of walls: Mega wilds at the fourth zone, an 11% boss at the third, a
  mid-game cliff at the all-Mega den, and an endgame easier than map
  one's back half. The road now opens gently (Airdramon's Flower Field,
  Devimon's Factory Night) and climbs monotonically to the deep end —
  Dexmon's lair is the final gate. **Nothing about the zones themselves
  changed**: same rosters, same bounties, same names and standing bests
  — only the order you meet them.
* Your save keeps its conquest **count**; the conquered set maps onto
  the new road's first stops. Map clears, egg gates, the shop shelf,
  and Alphamon's AREA gate all follow the new order correctly.

## 0.5.134 — THE @ LINE KNOWS WHERE YOU ARE (2026-07-21)

* **The status card's @ line goes live.** During an adventure it names
  the zone your mon is actually marching through (boss-trimmed to fit,
  like the Quest line); at home it shows your scene, as ever.
* **The away flag is finally wired.** The body sim's canon home-only
  gates — the AI assistant's billing and visits, the filth count, the
  gift call — all read a flag nothing ever raised: the setter died with
  the old adventure and the rebuild never reconnected it. The landing
  teleport raises it now and the homecoming lowers it, so **the
  assistant no longer bills or visits while your mon is on the road** —
  it minds the house, not the wilderness.

## 0.5.133 — THE VETERAN ROAD (2026-07-21)

* **Conquered zones fight back harder.** Replay a zone you've beaten and
  its wilds and gate boss return as **veterans**: trained and carrying a
  winning record, a genuine ~17-point edge through the real hit formula
  — the same terms your own pet earns, never padded stats. Bounties pay
  **half again** on a veteran road (stacking with streaks and festival
  doubles), feeding the zone's standing score to chase. The frontier and
  fresh zones are untouched, and no new save data: conquered *is* the
  tier. The zone picker tells you before you embark.

## 0.5.132 — THE ROAD REACHES EVOLUTION (2026-07-21)

* **The AREA evolution gate speaks adventure again.** `AREA n` in the
  line charts originally meant "adventure area n cleared"; when adventure
  left, it was re-gated to raid bosses. It's now a dual gate — clear the
  area on the road (Alphamon's `AREA 3` = conquer all of map 4) **or**
  the raid fallback (4 broken bosses) — the same restoration the egg
  unlocks' map rows got. Nobody who earned it through raids loses it.
* For the record, run care effects were already live: every road fight
  bills the body and feeds the WIN/BTL/TR/LV/KO6 channels plus attribute
  power, exactly like any local bout, and the march drains energy,
  calories, and tops effort. Verified, not changed.

## 0.5.131 — THE NIGHT HARDENING PASS (2026-07-21)

* **Every screen from this week's arcs was audited frame by frame** — a
  new contact-sheet tool renders all ~25 adventure/town/shop states as
  visible pixels, and everything from the sick trudge to the sold-out
  shelf was eyeballed. Two real finds fixed: the glint prompt overflowed
  its 40-column lane (now "✦ A glint!"), and the town hub's greeting
  clipped mid-word.
* **A permanent safety net.** New sweeps hold every state to the physical
  laws (12 rows, 40 columns, 40-char strips), animate each one ten ticks
  clean, and mash every key at every state without a crash. Old saves
  from before the town ledger load cleanly (verified). All three ratchet
  gates (ruff, mypy, bandit) at baseline.

## 0.5.130 — TOWN ECONOMIES (2026-07-21)

* **Per-town stock.** Town shops no longer mirror the home catalog: the
  authored town tables are wired back up, splitting the 26 towns into two
  stock families — a shared items shelf plus a food family each, with
  steak exclusive to one side and the anti-evo chip to the other. Town
  counters carry just their two shelves (Food · Items).
* **Local prices.** A town price is the authored ratio scaled to the
  catalog — steak 25% off, chips half, transports at par. No town's
  normal price ever undercuts the home resale (audited, pinned).
* **The rotating deal.** One item per town per day at half off (▾ on the
  shelf) — stable all day, different tomorrow, different next town. On a
  **festival**, the whole counter goes on sale.
* **Buy low, sell high.** A town pays a pittance for what it stocks but
  **70%** of catalog for what it doesn't (home pays 50%). Deals are the
  only below-water prices — catch a family exclusive on deal and carry
  it across the map. Capped at 3 per item per town per day; the shelf
  says "sold out today" when you've cleaned it out.

## 0.5.129 — THE ROAD READS YOUR MON (2026-07-21)

* **Condition walks.** A sick pet drags the collapse/weary trudge at
  **half march pace** — never the healthy stride. A geriatric one walks
  the aged shuffle, same as at home. A sleeping traveller halts the whole
  journey — no strides, no encounters, no finds — napping under its Zzz
  by the roadside until it wakes on its own.
* **Travel refusals.** A pet pushed **past empty** (marching only tires
  it to zero — it's eating ambushes while drained that pushes it over)
  plants its feet with the canon head-shake and won't walk. SPACE urges
  it on (a spent pet just refuses again), a held town warp rests it back
  to willing, ESC turns back home. Manage the tank or the road stops.

## 0.5.128 — THE RUN SCORE (2026-07-21)

* **Every run of substance gets a score.** Rolled from the tallies the
  results card already shows: bits 1:1 (streak/festival scaling and all),
  +10 per win, +5 per find, +25 per life still held at the end, +10 per
  chained win past the first, and +100 for felling the gate boss. Each
  zone keeps its **standing best** on your profile — the zone picker
  shows the number beside every scored zone, and beating it earns the
  **★ new best!** brag on the results card. Bare turn-backs (nothing
  fought, found, or earned) stay out of the books.

## 0.5.127 — THE WIN STREAK (2026-07-21)

* **Chained wins pay better.** Every consecutive fight won on the road
  grows your streak: +25% on bounties per win past the first, capped at
  **double** (and it stacks with the festival double). The chain feeds
  the win that earns it — your second straight win already pays ×1.25,
  and a chained gate-boss kill is the pot payoff. A loss or a flee
  breaks it — and so does **any** town rest, waypoint or warp. That's
  the gamble: push on hurt with the chain alive, or rest safe and start
  over. The march strip wears a **×N** marker from 2 up, and the
  results card brags your run's best chain.

## 0.5.126 — HAZARD DODGES (2026-07-21)

* **The road ambushes you now.** On a marched leg (never on town ground),
  a "!" blinks urgently at the road's edge — then one of the zone's own
  wilds pounces in. Press **SPACE** anywhere in the window to duck: your
  mon drops into the shield pose and the pouncer sails clean over and out
  the far edge. Eat it and the hit-burst lands with a **⚡−2** sting off
  the energy tank. It's never a fight and it never waits on you — a late
  press does nothing, the window is the game. All real art: the pouncer
  is the zone's own roster sprite.

## 0.5.125 — THE TIMED DIG (2026-07-21)

* **Digging is a timing game now.** ENTER on a glint walks your mon out to
  the spot as before — but at the dig, the canon timing bar takes the
  window: the same sprite and the same care-widened mega window as the
  training drill and the battle bell. SPACE locks the spade. Dead-centre
  digs a **second copy** of the find ("Dug up X ×2!"); near it keeps the
  honest single; a wide miss still scrapes the find out — the meter is
  pure upside, only the verdict (and the thunk) says you blew it. One
  full sweep and the spade falls wherever the marker stands, so the
  sequence never waits on you. Battles maxed at 999 never whiff, same
  as everywhere else.

## 0.5.124 — ROAD THEATER: THE FACEOFF, THE DIG, THE PARADE (2026-07-21)

* **The discover sequence is back.** A glint stop now plays the old build's
  full investigate playbook: the mon does the attention bounce with the
  "!" pulsing beside it, and ENTER sends it walking out to the spot to
  dig under suspense dots — the "Dug up X!" verdict and reward chime stay
  sealed until the reveal, then it carries the find back and marches on.
  The loot still lands in your bag the moment you press ENTER.
* **The gate faceoff.** Knocked back at a boss gate, the road is no longer
  empty: your mon squares up at the left edge, stepping and facing the
  gate, while the boss looms half-emerged past the right edge.
* **The zone pulse.** Felling a gate boss flashes the world bright on the
  canon zoneChange beats before the results card.
* **The boss parade.** Clearing a map's FINAL gate chains the BossParade:
  the map's own bosses march across the brightened stage one at a time,
  under the victory line. No skips — the show plays out.

## 0.5.123 — THE MARCH CROSSES THE SCREEN AGAIN (2026-07-21)

* **The adventure walking sequence is back** — restored from the old
  build's own march. Travelling, your mon walks clear across the window,
  exits the right edge fully, and slides back in hidden from the left
  (the lawful exits) instead of stepping in place at a centre anchor —
  a full crossing every ~9-10 seconds, about one per stride. It faces
  the direction of travel, and road beats — a glint, a town, a rest —
  play **where the mon stands**, not snapped back to centre.

## 0.5.122 — DESTINED TO HATCH A BABY, NOT AN EGG (2026-07-21)

* **"Destined to hatch" names the actual baby now.** The named egg banks
  carry display titles ("Kera Digitama", "Nature Spirits Egg"), and the
  destiny cards were printing those — promising an egg would hatch an egg.
  The carousel card, the incubating home card and the egg-select note all
  resolve the true firstborn instead: the Kera egg says **Kuramon**, the
  field eggs say Bubbmon / Pichimon / Mokumon / Nyokimon / Choromon, and so
  on. Mystery pools (Digitama X3) keep their "???" — the surprise is the
  point. The Digitama Guide still lists eggs by their egg names, as a
  book of eggs should.

## 0.5.121 — THE QUEST CARD SAYS WHERE (2026-07-21)

* **The home card's Quest line names your frontier zone.** Instead of a mute
  "not begun", it now shows the zone you're marching toward — "▸ Devimon"
  before your first run, "3/26 ▸ MetalSeadra" partway — using the full zone
  name when it fits the panel and the gate boss's name when it doesn't.
  The counter itself works as it always did: it advances only when you fell
  the **frontier** zone's boss (replays and wild fights never move it), and
  each generation walks the map fresh while your permanent map-clear
  unlocks (road shelf, map eggs) stay on the profile.

## 0.5.120 — THE TURN-AWAY DODGE (2026-07-21)

* **Dodges got dramatic.** An airborne dodger now whips its back to the
  incoming shot — springing toward its own wall, hanging there turned away
  while the orb whiffs past — and lands at touchdown facing forward for the
  classic return hop. A deliberate tuipet flourish on top of the canon leap.
* **The WIN gate's sub-row tells the whole truth now.** The data book note
  under a WIN requirement reads "fed by cup & road, not pvp/raids": the
  rolling 15-fight window moves on cup rounds and adventure road fights
  (wilds + zone bosses) only. Lobby PvP never counted (progression-neutral
  by ruling), and raid attempts have never written anything on the pet —
  the old note just didn't say so.

## 0.5.119 — THE CONSISTENCY AUDIT (2026-07-21)

* **Rev. Floppy has its own icon.** It wore the same sprite as the
  Digimemory — DVPet's own Digimemory glyph, in fact — so the two Medical
  shelves looked identical in the shop and the bag. The floppy now wears a
  proper disk of its own; the Digimemory keeps its rightful art.
* **Fusions can't land on a retired chart anymore.** lines.csv keeps a few
  dormant legacy trees so long-running pets mid-journey keep their chart —
  but a jogress landing on a shared form could get re-anchored *into* one
  of them (a chart no egg hatches). Hatchable lines now always win the
  tie-break; pets already on a dormant chart are left alone, as promised.
* Under the hood: the line curator round-trips the shipped 51 charts
  exactly (shipped line ids, the Digitama X3 pool, dormant charts all
  preserved), and the dormant-chart contract is now written down in
  LINES_SPEC and pinned by tests.

## 0.5.116 — THE HELP SYSTEM TELLS THE TRUTH (2026-07-21)

* **PgUp/PgDn now leap through every long list — as Help has claimed all
  along.** Only the window scrollers (help, egg guide, DigiCore, options,
  lobby) ever implemented it; the *cursor* lists silently ate the key. The
  shop, your bag, the Honors board, the **31-scene** picker, the **24-slot**
  cup board, the 26-zone picker and the hatch carousel all page properly now.
  Walking the scene picker one tap at a time is over.
* **SPACE answers the memorial prompts.** "SPACE works wherever ENTER does"
  is a stated law of the app, and the digimemory etch prompts were the one
  non-typing screen that broke it.
* **Help gained a LEGACY page.** The grave asks a permanent question — etch
  your pet's data for the heir, or keep the care bonus; and if data already
  stands, which generation's survives — and until now the in-game guide never
  mentioned death at all. Help also stops hiding things behind one-word
  entries: the shop's **Honors** tab and what **Options** actually holds
  (themes, sound, cloud sync, your account, updates, every key) are spelled
  out, and **?** finally appears on its own key list.

## 0.5.115 — TOWN EGG SHOPS (2026-07-21)

* **Every town sells eggs now — and each town stocks different ones.** A new
  **Eggs** slot in the town hub opens that town's egg market: a distinct band
  of digitama shown as their real **8×8 egg sprites** (a 2-row grid, the
  selected egg framed). Buy one on the road with bits and it joins your hatch
  carousel. No two town shops feel the same, so it's worth stopping in each.

## 0.5.114 — ADVENTURE IS BACK (2026-07-20)

* **The flagship EXPLORE feature returns as a full rebuild.** Press **a** to
  head out on the road: a teleport out, a march across one of the world's **26
  real zones**, wild encounters, a region boss to fell, **towns** to rest /
  resupply / fight the Town Cup, loot to find, and a results card on return —
  with lives, travel drain, transport items, and progression (conquer a zone
  to open the next).
* **Every pillar now earns eggs.** The egg unlock table was re-spread so each
  system feeds the roster: adventure map-clears, cup wins (a second cup egg —
  Hack via the Fall Champion Cup), raids, links, and — new — **festival days**
  (conquer a zone on a holiday to earn the DORU → Alphamon festival egg). Cups
  and seasonals are no longer egg-hollow.

## 0.5.113 — EGGS HATCH ON BACKGROUNDS THAT FIT (2026-07-20)

* **Re-homed five eggs to backgrounds that match the creature.** Using the
  DVPet habitat legend (not filenames): the Yuramon/Palmon **plant** line moved
  off an island coast into **Green Hollow**; the four **Sky** lines (Puttimon,
  Fufumon, Ryuda, V Egg) left **Frozen Peak** — which is really *Tundra*, cold
  and wrong for warm sky creatures — for **Mountains** (open sky) and, for the
  Veemon egg, **Green Hills**. Frozen Peak stays available as a hand-pick.
  Existing pets keep whatever background they already have.

## 0.5.112 — BACKGROUNDS NAMED RIGHT (2026-07-20)

* **Background scenes are named and organized by what they actually show.**
  Audited by looking at the pixels (and a structural-correlation pass), not the
  filenames: the sandy shore mislabelled "Sandy Seafloor" is now **Beach**; the
  real seafloor is one undersea scene at three lightings — **Seafloor / Deep
  Seafloor / Sunset Seafloor**; and the catalog is grouped into its time-of-day
  families (island sunset/day/night, city + city sunset, boulevard + dusk, bay
  bridge day/night, factory day/night, flower field day/sunset). Scene keys are
  unchanged, so saved pets keep their background.

## 0.5.111 — SMOOTHER PILL CHEW (2026-07-20)

* **The half-eaten pill holds longer.** The pill's eat animation uses the two
  DSprite pill frames (full, half-eaten); the pacing now gives the half-eaten
  frame the middle of the chew so full → half → gone reads clean instead of the
  pill sitting full and then vanishing.

## 0.5.110 — THE UPDATE RESTART ACTUALLY RESTARTS (2026-07-20)

* **Updating from Options now applies on one restart.** After the game
  installs a new release (at launch, or from the Update option), the Update
  row read "restart to apply" — but pressing it re-checked and said "up to
  date" instead of restarting, leaving you on the old code with no way to
  relaunch from Options. ENTER on "restart to apply" now actually restarts
  into the new version.

## 0.5.109 — THE PILL EATS RIGHT (2026-07-20)

* **The pill now eats through its own icon.** The pill you pick off the feed
  menu is the exact sprite your mon chews — full, then a half-eaten pill, then
  gone — the DSprite way (each food eats through its own glyph, like meat).
  Before, feeding the pill played an unrelated capsule that never matched the
  picker.

## 0.5.108 — NO MORE FUEL METER (2026-07-20)

* **The Fuel meter is gone from the feeding screen.** It charted the DVPet
  calorie buffer — a mechanic with no basis in the DSprite build tuipet is
  made from, and one feeding never fed. The feeding card now shows Hunger,
  Weight and Effort (and the satiety window when it applies).

## 0.5.107 — OUT OF BETA (2026-07-20)

* **TuiPet is officially released.** The beta is over. Thanks to everyone
  who played through it. From here on development leans on player bug
  reports — if something breaks or feels off, send it in.

## 0.5.106 — ONE MON PER TITLE (2026-07-20)

* **The title mascot no longer switches.** Attract-mode cycling (added in
  0.5.104) is removed on Joel's ruling — the launch draws one mon and
  keeps it until you press start. The random boot transitions, power-on
  jingle, pulsing prompt and version tag all stand.

## 0.5.105 — THE POWER-ON JINGLE (2026-07-20)

* **The device now sings when it boots.** A 0.28s rising jingle
  (da-di-dii-dii) plays with the power-on flash — baked entirely from the
  device's own ripped beeps (its three tones: trainhit's low, click's
  mid, the menu blip's high, in the native 40ms beep unit; nothing
  synthesized — `tools/make_boot_jingle.py` is the recipe). Respects the
  sound switch and volume slider like every other sound.

## 0.5.104 — THE DEVICE POWERS ON (2026-07-20)

Title-screen polish round (Joel: "lets polish the title screen"):

* **Six boot transitions, one drawn at random each launch.** The
  all-segments power-on flash stays; what follows is now the launch's own
  draw: dissolve, wipe, scan, blinds, iris, or checker. The transition
  window grew from 0.5s to 0.8s so the sweeping effects read as motion.
* **Attract mode.** Every 8 seconds the title mascot transitions to a
  different mon from the roster, replaying the boot's own effect — one
  visual language per power-on.
* **The PRESS ENTER prompt pulses** bold/dim at constant width, and the
  installed version rides the strip beside it (blank on source runs).

## 0.5.103 — ONLINE PLAYS FOR THE LADDER (2026-07-20)

The last open finding of the 2026-07-19 gameplay audit, ruled by Joel
(L17, option a):

* **Online PvP is progression-neutral.** Experience and Mega-kill credit
  always excluded online bouts — opponent cards are untrusted, and two
  colluding tamers could farm anything they feed. But wins, the rolling
  win log, per-stage battle counts and lifetime wins stayed fed, and they
  gate evolutions and eggs: the same farm, different channels. An online
  bout now costs your pet's energy and weight and nothing else — the
  purse still pays, and your standing lives on the season ladder, which
  was built for exactly this (both-sides-confirm, per-pair caps).
  Evolution WIN/BTL gates and the lifetime-wins egg gates are earned in
  the cup and against the world.

## 0.5.102 — THE HOUSE KEEPS ITS WORD (2026-07-20)

The SUSPECT tier of the 2026-07-19 gameplay audit, ruled and shipped
(`AUDIT_2026_07_19.md` records each ruling):

* **A revival never steals a young life.** Being saved from death set the
  age to ~12 game-hours before the end for *every* pet — canon-shaped for
  an old-age death, but a young pet rescued from sickness or poison
  silently lost nearly its whole remaining lifespan. Revival now
  *restores* life, as the canon rule says: old-age rescues get their
  grace exactly as before, and a young pet keeps the life it had.
* **An interrupted DNA wager settles instead of vanishing.** The stake is
  still paid when the mash begins (that part is canon — and refunding it
  would make quitting free insurance on a mash going badly, the same
  logic as the cup's documented forfeit). But a quit or crash mid-mash
  used to keep your bits and give nothing: the paid mash is now
  remembered, and the next launch settles it as the spoiled mash it was —
  a big stake still stabilizes into a real Field — and tells you so.
* **Keeping the elder's memory no longer costs the bonus.** At the
  memorial, choosing to etch and *then* keeping the previous generation's
  memory discarded the fresh etch AND left the lower spent-bonus seed —
  strictly worse than declining up front, and nothing said so. Keeping
  the elder now carries the care bonus exactly like declining; the two
  roads to the same choice pay the same.
* **A suspended terminal no longer stops time.** Ctrl-Z or a closed
  laptop lid froze the pet completely, while a properly *closed* game
  aged — so the kind way to leave was the dishonest one. A real gap in
  the clock now runs through the same gentle offline catch-up a relaunch
  gets, with the same welcome-back note. Menus still pause the world,
  exactly as before.
* **Quit-cycling can't cheat the clocks.** Four sim clocks weren't saved:
  relaunching could bill hunger/effort call mistakes up to 7× faster (or
  forgive one at second 599), dodge the assistant's hourly retainer
  forever, and shed sleep-DP progress. All four now persist, like the
  starvation clock before them.
* Also probed: the "estate lost across devices" suspicion **did not
  reproduce** — a two-device test carried bits, bag, trophies and the DNA
  bank in full. Documented in the audit.

## 0.5.101 — SMALL TRUTHS (2026-07-20)

The LOW tier of the 2026-07-19 gameplay audit (`AUDIT_2026_07_19.md`):
sixteen of the eighteen display/label/dead-code findings, fixed. (L17 —
whether online PvP keeps feeding the win/battle evolution channels — and
the lost LINES_SPEC.md await rulings; the DNA Crystal leg of L9 didn't
reproduce and is documented as such.)

* **Care items say what they do, and no-ops refuse.** The Cheese Burger
  discloses its weight +4, and its care slip now stings like every other
  mistake (mood + the birthday judgment) instead of a silent bare count.
  The Energy Drink fills the meter TO full — a drained pet used to land
  short — and refuses when energy is already full. The Bubble Bath
  refuses when there's nothing to scrub. Refused items stay in the bag.
* **The frailty warning actually shows.** The "getting frail — N more
  slips could be fatal!" line existed but could never reach the box; an
  elder carrying 3+ mistakes now warns before the 5-slip death lands.
* **The cold shower narrates its wake.** "Brrr! AWAKE and bracing." was
  unreachable — the disturb law now runs inside the item so the message
  can tell the truth (a sleeper is still billed like any rude item).
* **A disturbed baby stays up its full grumbling time.** The re-sleep
  math divided by the sleep rate instead of multiplying, so a baby
  (rate 9) dropped back off in seconds.
* **Sleep is no longer a plague ward.** The filth/overweight sickness
  rolls and the sick-death whisper run in bed too, exactly as the sleep
  branch's own comments always promised. Starvation still freezes
  overnight.
* **A line pet's daytime doze is a nap, not a day.** Lights-out dozing
  ran the whole previous night's span; it's now the fixed hour the
  pressure model's checkNap always used.
* **Line pets yawn before bedtime.** The pre-bed yawn roll read only the
  retired pressure clock; it now reads the wall-clock bedtime every
  current pet actually sleeps by.
* **Weekend purses always wear their tag.** A weekend loss paid 150 — the
  same number as a plain draw — so the "(weekend bonus!)" tag hid exactly
  there. The tag now asks the calendar, not the amount.
* **The raid show is honest.** The boss bar no longer dips during a round
  and snaps back to full — it holds, as the "never falls" rule says — and
  an attempt your pet SURVIVES ends on its feet instead of the loser's
  collapse frame. (Dealt damage feeds the community pool unchanged.)
* **Cup fights show their HP.** The battle card (you/foe bars, result,
  reward) now rides the status box during cup bouts; it used to be
  unreachable there. And a local loss discloses the "training +2" every
  local bout grants — it was granted silently under a DEFEAT screen.
* **Chat stops double-printing.** Reconnects and room→main returns replay
  the backlog window; replayed lines are now marked by the server and
  skipped by the pane when already shown.
* **The raid gate speaks when it refuses.** With no account it says so
  (instead of logging you in as the literal name "None"), and a rejected
  login or server error surfaces instead of "Calling the raid gate…"
  forever. Raid rank ties now break by earliest report, as documented.
* **Your ladder row highlights** whatever capitalisation you typed at
  login. Unknown online cards now read "Rookie" (same rank as before —
  the "Child" label was pre-tuipet vocabulary).
* Under the hood: six dead functions cut (`CareMixin.sell`,
  `_apply_item_stats`, `_fruit`, `_erase_mistake`, `_advance_bm`,
  `_stat_total_ok`), and the evolution `check()` docstring no longer
  teaches the removed DNA gate-forgiveness rule.

## 0.5.100 — HAPPY AT LAST (2026-07-20)

The twelve MED findings of the 2026-07-19 gameplay audit
(`AUDIT_2026_07_19.md`), all fixed:

* **Happy is real now.** The mood meter could never say "Happy", and a
  whole reward tier hung dead off it: the good birthday (+lifespan,
  +evolution bonus, the Cupcake), battle power doubling, the happy
  idle bounce, and the report card's +1. Perfect care reaches it now —
  an "ok" pet at top condition is Happy.
* **The report card stops docking a phantom point.** The retired
  obedience meter (pinned at 0 forever) subtracted 1 from every life
  ever graded and delayed every pet's nod-off. Removed systems no
  longer bill live formulas.
* **Jogress doors open for their declared partners.** 41 of 147
  attribute doors could never fire with the very partners their own
  charts declare — the resolver demanded an unrelated ancestry link.
  Any same-stage partner with a listed attribute now opens the door,
  as the charts promise.
* **The battle replay shows the hit that landed.** When your blow
  finished the foe, the foe's simultaneous strike was cut from the
  animation but still subtracted — HP dropped with no visible cause.
  What's applied is what's shown.
* **Cup and invite bouts obey the same health gates as challenges.**
  A pet too starved, sick, or drained to *send* a challenge could
  still grind recorded cup battles and auto-accept incoming invites.
  And a stranger's invite can no longer trigger your pet's visible
  refuse animation.
* **Raid and lobby no longer fight over the connection.** The raid
  screen leaked its live lobby login; opening the lobby afterwards
  left the two sessions evicting each other in an endless
  "reconnecting…" loop.
* **The lobby shrugs off crafted junk.** The server clamps every
  stored presence card to its real fields and sizes, closing a route
  for one hostile client to knock every honest player off the lobby.
  (Server-side — already live.)
* **Quitting a fight is a loss, and it's filed.** ESC mid-fight
  forfeits: the ladder records your loss, and your opponent gets the
  win, the payout, and "Opponent fled — you win!" instead of an
  unconfirmed nothing. Backing out before the fight is seeded stays
  free.
* **The DigiCore meter counts for Megas.** The final-form lifespan
  count-up froze at 14 forever whenever the corpus had onward rows.
* **The data book agrees with itself.** The evolution list sorted
  backwards — least-likely form first, contradicting the silhouette
  beside it — and a held Digimental's requirement row always read
  unmet.
* **Cancelling a retire leaves no trace.** N then ESC at the egg
  carousel appended a duplicate headstone for the still-live pet on
  every attempt — and prematurely recorded it as the previous
  generation.
* **No free X antibodies.** The evolution fallback could force an
  antibody-less pet into an Induced-X form and then lock the antibody
  in as Permanent. The Induced gate now holds everywhere.

## 0.5.99 — FAIR PLAY (2026-07-19)

The six HIGH findings of the 2026-07-19 gameplay audit
(`AUDIT_2026_07_19.md`), all fixed:

* **The sleep items work for every pet.** Since bedtimes moved to the
  wall clock, three 300b items quietly stopped working: the Sleep Pill
  bought ~1 second of sleep (out of hours it now rides the daytime
  doze and sleeps off the energy debt), the Caffeine Pill was a paid
  no-op (it now pushes tonight's nod-off a quarter of the night), and
  the Music Player's clean wake lasted one tick — weaker than throwing
  a burger at the sleeper (it now grants the same grumbling-time grace
  a disturb does, still mistake-free).
* **The life report card grades fairly.** Every Mega graded 0 (a
  sentinel leaked into the growth-curve math) and everything else
  over-graded by hundreds (the longevity leg counted a day 60× too
  small, swamping every ±1 the card is built on). Longevity now counts
  the same days the memorial shows.
* **Quitting is no longer worse than playing.** Offline catch-up ran a
  different, ~6× harsher sim: it starved sleeping pets, voided the
  Steak's 12h satiety and the Port. Potty exactly while you were away,
  froze growth under a running age clock, and let a full night restore
  nothing. It now moves at your pet's own live rates, honors the live
  gates, advances growth with age, and sleep earns its energy and DP.
* **ESC at the cup's timing bar backs out for real.** It recorded a
  silent, stake-losing elimination while the hint said "back out" —
  now it returns to the bracket with the match still waiting, exactly
  like the raid. Leaving the whole cup stays the labeled forfeit.
* **An effort heal sticks.** The decay timer kept running while the
  gauge sat empty, so a Vitamin after a drought was partly undone one
  second later — and billed a fresh missed-day.
* Under the hood: a battle surrender after the bell can no longer file
  a second phantom loss, and the dormant surrender-morale cluster's
  false "consumed by record_battle" comment now tells the truth.

## 0.5.98 — THE INHERITANCE WORKS (2026-07-19)

The five critical findings of the 2026-07-19 gameplay audit
(`AUDIT_2026_07_19.md`), all fixed:

* **The Digimemory chip is real now.** The heir's chip was banked and
  granted but invisible in the bag and inert on use — the whole death
  ceremony fed a payload no pet could ever redeem. It shows under
  Items, and using it grants the ancestor's etched Va/D/Vi plus the
  etched lifespan hours, with the canon inherit show on the LCD. An
  empty husk politely refuses and is kept. Old saves' raw-key chips
  heal on load.
* **A quit can't disinherit the heir.** The etch and the care-grade
  seed banked only when the dying animation finished — closing the
  terminal during the ~2s beat lost a lifetime of bonus. The ceremony
  now runs once per death, wherever the death is noticed, and rides
  the save.
* **The poison mushroom dies properly.** It set dead between ticks,
  so the death-edge detector never fired: no dying beat, no mash-
  rescue window, no banking, and a sleeping pet stayed "asleep" in
  the grave. Death is detected by state now, and the mushroom goes
  through the same door as every other death.
* **Account switching can't destroy your pet.** Switching to an empty
  account with no prior login deleted the only save (and its backup);
  a failed park-upload was ignored; re-logging into your own name let
  a stale cloud save overwrite a newer local pet. Now: a first login
  adopts your pet, a failed park aborts the switch, and same-name
  logins honor the timestamp guard.
* **Forged lobby invites are locked out.** A crafted "accept" could
  force your pet into a recorded battle — or a permanent jogress
  fusion — you never asked for. Responses now only count against an
  invite this device actually sent.

## 0.5.97 — LOGIN MANNERS (2026-07-19)

* **The cell-width law reaches the login.** The name field tail-
  windowed by characters, so an emoji or CJK name (two terminal cells
  per glyph) could run the input line past the box and tear the
  layout. It windows by cells now, like the chat always has.
* **What you see is what logs in.** The name buffer accepted 64
  characters but the confirm silently trimmed to the server's 24. The
  field stops at 24 live; the password keeps its 64.
* **A half-filled confirm speaks up.** ENTER with a missing name or
  password used to do nothing at all — it now says "Name and password
  both, please." with the error tone.
* **One hint surface, one vocabulary.** The in-LCD key line doubled
  the strip and called TAB "switch" while the lobby called it "field"
  — the line is gone and both strips say "field". Under the hood the
  split's stranded leftovers went too: dead imports and the unused
  MAX_PVP_* constants (the real card bounds live in the battle
  engine's clamp).

## 0.5.96 — GUIDE MANNERS (2026-07-19)

* **A roomier book.** Both of the guide's in-LCD key footers doubled
  the message strip (and the list one disagreed on the verb); they're
  gone. The list shows nine eggs per page now, and the detail page has
  a tenth row for long unlock stories.
* **One naming policy.** The status card masked a locked egg's hatch
  name as "???" while the guide's own list and detail header printed
  it openly. The card reveals like the rest — the book's purpose is
  showing what's out there and what earns it.
* **Phase-true card hints.** Inside an egg's story the card now says
  "←→ next egg  ESC back" instead of offering to open the story
  you're already reading.

## 0.5.95 — FUSION MANNERS (2026-07-19)

* **Any key skips the converge.** The fusion cinematic always claimed
  any key would skip to the reveal; only ENTER/SPACE/ESC actually did.
  The stated contract is the real one now.
* **A lend is called a lend.** When you're the one-sided door's
  companion (canon: only Jesmon X makes Jesmon GX), your mon lends its
  data and stays itself — the confirm prompt now reads "[Enter] lend"
  instead of promising a fusion that never comes.

## 0.5.94 — HELPER MANNERS (2026-07-19)

* **The contract, in full.** The assistant card now names its quit
  clause up front — the helper walks off duty the moment it can't
  cover the retainer or the next visit. You used to learn that only
  from the after-the-fact quit note.
* **The verdict rides home.** Hire or dismiss the helper and leave —
  "… is on duty." / "The assistant was dismissed." flashes on the home
  screen. (The old exit payload was discarded by the app, and would
  have been the standing blurb anyway.) Just looking and leaving stays
  silent.
* **One hint surface.** The in-LCD "ENTER toggle" footer duplicated
  the strip's keys; gone, like raid, DM and shop before it.

## 0.5.93 — SHOP MANNERS (2026-07-19)

* **A taller shelf.** The in-LCD key footer duplicated the message
  strip's hints; its row now shows a fifth list row, filling the LCD
  exactly. Buy/sell verdicts and the sealed-Digimental wave tease ride
  the message strip (verdict > tease > hints — the egg carousel's
  grammar), and the hints tell the truth per tab: "ENTER wear" on
  Honors, "ENTER buy" on goods.
* **A no sounds like a no.** An item the pet refuses (and keeps) and
  "Not enough bits." on an honor both played the happy confirm chirp.
  Both are errors now.
* **Leaving mid-verdict carries it home.** ESC right after a buy shows
  the verdict on the home screen — the old check keyed on a value the
  app had already consumed, so it never fired.

## 0.5.92 — LOBBY MANNERS (2026-07-19)

* **The ladder page fits.** With a full top-8 board, "you: rank …" and
  "season resets in …" — the lines you opened the page for — ran off
  the bottom of the LCD. Two decorative blanks are gone; the page is
  exactly 12 rows.
* **A season prize can't be orphaned.** The claim used to mark itself
  "collected" locally *before* asking the server — a dropped socket at
  that moment left the prize owed forever but never claimable. The
  durable note now waits for the server's payout ack; a lost claim
  simply retries next session.
* **Reading a DM counts.** A message arriving while its thread was
  open on your screen still badged the conversation unread. Watching
  it arrive now clears the badge.
* **The action menu tells the whole truth.** The M key (quick-PM
  without leaving the room) was working but advertised nowhere — both
  hint surfaces name it now. A blocked player's strip offers only
  "X unblock · ESC back", matching the in-LCD line. And a dead pet's
  invite auto-decline no longer teaches "press N" — a key the lobby
  doesn't have.
* **One hint surface in the DM thread.** The in-LCD footer duplicated
  the strip's keys; its row now shows one more line of history.

## 0.5.91 — RAID GATE MANNERS (2026-07-19)

* **The gate explains itself.** A refused damage report now shows the
  gate's own reason (the boss fell, or your attempts ran out) instead
  of always guessing "the boss is gone."
* **Walking away isn't a whiff.** Backing out at the timing bar — no
  volley rolled, no attempt spent — says so, instead of the old "Not a
  scratch" miss line.
* **Honest board, honest bonus.** Before your first report the stats
  line shows "you —" rather than a fake rank #0, and the weekend note
  now names its exact truth: weekend *claims* pay 1.5x (UTC, the
  server's clock).
* **Under the hood.** The damage report no longer carries a stage
  field the gate deliberately ignores (the multiplier binds to your
  card's species), and the raid loading page keeps its keys on the
  message strip like every other state of the screen.

## 0.5.90 — THE REPORTS, PART TWO (2026-07-19)

* **The medicine is a pill now.** You asked "where's the pill? that's a
  bottle" — and it was: the old art is DVPet's Med *jar*. The heal now
  eats the Food Pill capsule, a real rip with a true bite-by-bite
  sequence, the same capsule the assistant already fed with. The bottle
  sprite is audited safe: nothing else used it, and it stays in the
  atlas untouched.
* **No more pooping through dinner.** The original device blocks the
  squat while an action is playing — that hold was missing here, so a
  ripe gauge could drop a pile mid-meal. Restored: a busy mon holds it
  until the animation ends (a long hold releases as the big backlog
  pile, and the mood pays canon's postpone price).
* **Short shop icons sit on the floor.** The Giga Meal wasn't cut off —
  the rip is complete against the original atlas — it was top-floating
  over a dead row, which read as clipped. Short art now rests on the
  baseline like every plate should.
* **And two answers.** Effort filling after medicine is by design (the
  pill grants effort +1, straight from the source). The "restart to
  play" message after your in-game update was the auto-updater being
  honest — a *newer* release had landed while you played; it names the
  version it means.

## 0.5.89 — LISTENING TO THE REPORTS (2026-07-19)

* **The scene names, corrected properly this time.** Your reports were
  right and 0.5.85 was wrong twice: "Sunset Shore" is underwater art —
  the warm band is sunlight through the water — so it's Sunset Seafloor
  now, joining Sandy/Blue/Deep. One island wears its three times of day
  honestly (Island Day / Island Sunset / Island Night — "Lone Island"
  hid that it was the same island), and the flower field's two skies
  are Flower Field and Flower Field Sunset.
* **The cliffside eggs hatch on real coast.** Twice re-homed and
  finally right: the island's rock faces over open sea, the one true
  coast in the whole set.
* **The egg carousel, the way you asked.** The LCD is pure scene with a
  taller band — the menu-like text block is gone (the status card and
  message strip were always its home) — and the previous/next egg edges
  peek again at both sides. Cutting them before was the wrong fix.

## 0.5.88 — THE DRILL'S TRUE WORTH (2026-07-19)

* **The drill's documentation caught up to its power.** The training
  module still claimed the saved hit-form "stands ready" for a future
  battle system — but the battle reads it today: every fight fires with
  the form your last drill locked. The docs now say so. The mysterious
  999-battles auto-perfect turned out to be device canon (a maxed
  veteran never whiffs), verified against the clone source and cited so
  it's never "fixed." Two dead remnants from the timing bar's move to
  shared code were swept. No gameplay changes.

## 0.5.87 — ROOM TO CHOOSE (2026-07-19)

* **The egg carousel breathes.** At rest, neighbouring eggs rendered as
  four-pixel slivers mashed against the window borders — clutter that
  read as dirt, not eggs. The resting view now shows your chosen egg
  alone on its home backdrop; neighbours still glide through while you
  browse, because the motion is the carousel. And the screen's bottom
  carried two hint rows saying nearly the same thing — the in-screen
  line now keeps only the dossier, the tease, and ESC; the message
  strip carries the controls, once.

## 0.5.86 — BACK TO SHORE (2026-07-19)

* **The cliffside eggs stand on the shore.** 0.5.85's renaming revealed
  a wiring error it had been hiding: "Cove" turned out to be seabed art,
  and both Cliffside-habitat egg lines (Yuramon's and Ketomon's) were
  wired to it — their hatchlings lived underwater. They hatch on the
  Sunset Shore now, a real coastline with a horizon. The DeepSaver water
  lines stay on the seafloor on purpose — that's home. A scene you
  picked yourself with E is never touched.

## 0.5.85 — SCENES, PROPERLY NAMED (2026-07-19)

* **Recoloured backdrops share a family name.** The scene picker carried
  three undersea floors where only some said so ("Cove" was the sandy
  shallows), and the valley-of-trees composition in green, gold and teal
  under three unrelated names. Now: Sandy/Blue/Deep Seafloor (ranked by
  measured brightness), Green/Golden/Teal Hollow, and the movie bridge
  twins are Bay Bridge and Bay Bridge Night. Display names only — your
  saved scene picks are untouched.

## 0.5.84 — UPDATES THAT SPEAK UP (2026-07-19)

* **The update result always finds you.** Installing takes seconds; if
  you closed the options screen meanwhile, the "Updated! Restart now?"
  offer died with the panel and you learned nothing. The completion now
  also rides the app-wide verdict channel — it flashes wherever you are
  next home. And a close-and-reopen can no longer race a second install
  against the first: the in-flight latch lives above the panel now.
* **The rest of the options screen passed its audit** — every row
  description verified true (including "for keeps," which earlier
  rounds made honest), the sound page's bell-only truthfulness, and the
  confirm grammar all hold.

## 0.5.83 — HELP THAT HELPS (2026-07-19)

* **Help teaches the gift and the grammar.** The ENTER gift-accept had
  no action-bar slot and no help line — a player watching their pet's
  gift-call pose had no documented way to learn the answer. And the
  app-wide key grammar (SPACE works wherever ENTER does; PgUp/PgDn leap
  long lists) had reached the README but never the in-game help, where
  terminal-only players actually look. One line each, both in now.
* **Everything else the help says checked out true** — every control
  line and claim verified against the shipped game after 21 releases of
  change, with zero rot found.

## 0.5.82 — THE SHAPE SWEEP (2026-07-19)

* **Account-switch results always reach you.** "Signed in as…", "Wrong
  password", and the offline warning could be silently missed if you
  opened a screen while the switch worked — you could believe a failed
  switch succeeded. Every background task's verdict now rides one
  channel that waits for you on the home screen.
* **The volume setting saves everywhere.** It lived on a hardcoded path
  that iOS can't write and Erase All never touched — it now sits beside
  the save like every other pref, and Erase All sweeps it (plus the
  sound cache).
* Every other defect pattern from the 21-round audit series — clock
  units, destroy-before-send, billing-after-refusal, silent clips,
  local-vs-UTC — swept the whole codebase clean.

## 0.5.81 — NO REPORT LEFT BEHIND (2026-07-19)

* **Offline bug reports survive everything.** The boot-time retry used
  to clear the stash before sending — quitting mid-retry lost every
  unsent report. It now reads without deleting and rewrites only the
  survivors: a crash leaves the originals, and a bounded duplicate send
  beats a lost report. Damaged stash lines are dropped instead of
  cycling forever.
* **The send verdict always reaches you.** "Sent — thank you", "Offline
  — saved", or the honest failure used to be swallowed if you opened
  another screen during the up-to-8-second send. The verdict now parks
  and flashes the moment you're back on the home screen.

## 0.5.80 — FULL DISCLOSURE AT DINNER (2026-07-19)

* **The feed card tells the whole truth on both rows.** The Pill row
  always disclosed everything down to its weight +5, but the Meat row
  hid its weight +1 behind "the staple." Both rows now read in full —
  weight is a meter you manage, and the menu shouldn't hide an effect
  its sibling admits.
* The rest of the feed screen passed its audit: the exact decompile
  menu glyphs, the robust outcome contract, and the eat/refuse flows
  all verified. A last ghost of the removed injury system was swept
  from the pill's cure check (behavior unchanged).

## 0.5.79 — NO SILENT GOODBYES (2026-07-19)

* **The quarantine warning reaches you.** When a damaged save has to be
  set aside, the game composes a notice naming the kept file — but the
  new-game flow (title → egg carousel) never showed it: the loss looked
  exactly like a first launch, the very thing the notice exists to
  prevent. It now rides the message box right after you pick your new
  egg, so you know the old pet was kept recoverable on disk.
* The rest of the title screen passed its audit — the power-on
  sequence, the mascot draw, the once-per-build news line and the
  welcome-back messages all verified.

## 0.5.78 — TRUE COLOURS (2026-07-19)

* **The theme choice saves everywhere.** theme.txt was the one file
  ignoring the save-directory rules — on iOS your theme silently never
  persisted, and Erase All could miss it. It now lives beside the save
  like every other pref. (XDG users may see a one-time reset to grey.)
* **Every palette colour says what it paints.** The "mood" colour (a
  meter gone since the BASIC strip) is now "care" — it tints the
  care-mistakes row; the "day/night" silhouettes (the arena clock is
  long gone) are now the scene silhouette and the lights-off silhouette;
  and the docs no longer promise a gameboy key colour that was cut, or
  claim "no green" above the pea-soup DMG palette.

## 0.5.77 — THE LABEL WINS (2026-07-19)

* **Timed items deliver the hours on the label.** The Steak promised
  "12h satiety" and delivered 12 minutes; the Port. Potty's "24h
  auto-clean" ran 24 minutes; the Grow Capsule's "+120min" nudged two.
  The steak's own countdown card exposed it — message said hours, card
  counted minutes. The mechanics were tuned up to match the words:
  12 real hours sated, a real day of auto-clean, two real hours of
  growth. Premium prices finally buy premium windows.
* Everything else in the message-vs-mechanic sweep came back clean:
  all sixteen instant effect claims match their numbers exactly, and no
  player message cites a key or system that no longer exists.

## 0.5.76 — STRAIGHT TALK ON DP (2026-07-19)

* **The DP hint tells the truth.** The jogress refusal claimed "protein
  or a night's sleep" refills the meter — but protein feeds left with the
  old nutrition system, and players were feeding steaks for DP that never
  came. Sleep is the one refill (three game-hours fills it), and the hint
  says exactly that now.
* **The fusion engine passed its full audit** — the two-block attribute
  matrix, the both-or-neither online match, the exact-partner and
  one-sided companion doors, canon's energy bill, and the two-phase
  consent all verified. (Canon's sick-partner fusion risk remains
  deliberately unwired, now documented as such.)

## 0.5.75 — ONE TRUE WEEKEND (2026-07-19)

* **The raid page's weekend note follows the relay's clock.** It borrowed
  the cups' local calendar to describe a bonus the server pays on UTC
  weekends — at week edges it promised a bonus that wasn't paying, or
  stayed silent while one was. It now reads the server's own timestamp.
  Cups stay on your local calendar on purpose: their purses pay on your
  device, so your weekend is their truth.
* **The cup system passed its full audit** — deterministic daily board,
  honest purse math with canon truncation, live catalog prizes, the
  winnable featured draw, festival days, and cup wins feeding the egg
  gates. No changes needed.

## 0.5.74 — AN HONEST ASSISTANT (2026-07-19)

* **The assistant feeds a sick pet.** Its feed visit routed through your
  own meat's sickness refusal — so a sick, starving pet's hired helper
  billed the full visit fee every three minutes for a head-shake,
  torching thousands of bits without raising hunger, until it quit over
  the wallet it had emptied itself. It now serves the canon AI Food Pill
  (which a sick pet accepts), so every fee buys care that landed.
  Curing the sickness is still your job — that's the pill in *your* hand.

## 0.5.73 — HONEST HEADSTONES (2026-07-19)

* **LEGACY headstones tell the truth.** The DigiCore LEGACY page was
  reading every elder's age sixty times too long — a pet that lived
  4½ days was carved as "270d" while its own memorial said "4d 12h".
  The headstones now speak the same clock as every other age in the
  game; your ancestors' true ages appear on the next visit (the banked
  records were always correct — only the display lied).

## 0.5.72 — EVERY EGG EARNABLE (2026-07-19)

* **The digitama system passed a full audit.** All 46 eggs verified
  reachable under their own unlock signals, every gate signal confirmed
  fed by live code, the progress lines crash-free on any profile, and
  shell art plus home scenes complete. No player-facing changes —
  everything already worked.
* A new test guard ties the unlock rules' vocabulary to the roster's,
  so a future data edit can never silently seal a family egg.

## 0.5.71 — A CLEAN SHOPFLOOR (2026-07-19)

* **The shop passed a full economy audit.** All 32 catalog items swept
  end to end — buying deducts exactly and refuses the broke in words,
  using consumes or explains, selling returns exactly half; the
  Digimental waves gate honestly and the legacy bag-heal map has no
  orphans. No player-facing changes — everything already worked.
* Housekeeping: the town-counter code (dead since the towns left in
  v0.5.8) is cut, with a pin so it stays gone. `shop.buy` is the one
  purchase path.

## 0.5.70 — COMPANY AT THE GRAVE (2026-07-19)

* **The lobby opens beside a departed pet.** The social room is not a
  care action: chat, private messages, password rooms and the season
  ladder all work while you mourn — claim your award, say goodbye. The
  combat half stays sealed both ways: a dead pet can't send battle or
  jogress invites, and the relay refuses invites sent to one. Every
  care key still leads to the memorial; options was always live.

## 0.5.69 — PLAIN WORDS EVERYWHERE (2026-07-18)

* **Every data file fails in the player's words.** The compressed atlases
  always explained a damaged install ("reinstall it: pip install
  --force-reinstall tuipet") — but the CSV half of the data layer crashed
  with a raw traceback on the same broken install. One shared message
  now covers all fourteen data files.
* Under the hood: the whole data layer passed a referential-integrity
  audit — every icon, effect, catalog, enemy, cup, raid and egg-hatch
  reference resolves against the tables that own them.

## 0.5.68 — HONEST HOUSEKEEPING (2026-07-18)

* **The save warning tells the truth.** One transient disk refusal used
  to stick forever — the quit banner printed "couldn't save" over a pet
  that had been saving fine every ten seconds since. The flag now clears
  when the same file writes clean (and only then — another file's
  success can't mute a save that's still refusing).
* **Erase All erases everything.** Quarantined save copies, the crash
  log and stashed bug reports carried the erased pet's data past the
  typed-YES erase; they die with it now.

## 0.5.67 — THE BOSS STANDS TALL (2026-07-18)

* **Raid bosses render whole.** The raid page's reduced scene was wearing
  the full-screen clip, cutting the top six pixels off every boss — and
  the page itself ran past the LCD, silently clipping its own footer. The
  boss now stands complete and the page fits exactly, with one rotating
  context line (verdict / waiting purse / weekly cadence).
* **One timing bar.** The battle and raid ready screen now sweeps the
  canon pixel bar — HIT! font, outlined track, window ticks — the same
  sprite as the training drill, single-sourced, instead of a text-glyph
  track that looked nothing like it.

## 0.5.66 — A STURDIER RELAY (2026-07-18)

* **Offline messages survive bad connections.** The relay now deletes a
  queued message only after it truly delivered — a connection dying
  mid-login keeps the rest of your mail queued for next time.
* **Ladder payouts are server-confirmed.** The season award now follows
  the raid-reward contract: the server acks the claim and the bits land
  on the ack — a lost message or a second device can't double-collect.
* Relay housekeeping: the anti-farm pair cap can no longer reset
  mid-hour, and the server box shed a month of loose backups.

## 0.5.65 — LOBBY POLISH (2026-07-18)

* **DM threads scroll.** "Thread saved" was true, but everything above
  the window was unreadable — ↑↓ and PgUp/PgDn now walk the whole
  history like the lobby log, sending snaps back live, and the hint line
  advertises the log keys when there's history to read.
* **Raid claim works with caps lock.** C claims in either case, like the
  lobby's letter keys.
* The login hints say what ESC really does (leaves to home), and the
  ladder page dropped its two undocumented close keys.

## 0.5.64 — ONE KEY GRAMMAR (2026-07-18)

* **SPACE works wherever ENTER does.** The DNA stats/roads pages and the
  retire-for-a-new-egg confirm were the last holdouts. (The typed-YES
  erase stays ENTER-only on purpose, and DigiCore's SPACE keeps its own
  job — paging.)
* **PageUp/PageDown leap through every long list** — help, the keys
  page, the 46-egg guide and the evolution requirement checklist page
  lobby-chat style, with the standard scroll blip.

## 0.5.63 — NO MORE CUT-OFF HINTS (2026-07-18)

* **The egg carousel's unlock tease reads whole.** 32 of the 46 unlock
  hints overflowed the footer and were silently cut mid-word — right
  where they told you what earns the egg. The tease now marquees through
  head to tail on a longer beat (control hints still hold still).
* Every screen's message-strip hint line is now pinned to the 40-col
  never-marquee budget — the last 8 unpinned screens joined the sweep.

## 0.5.62 — A TIDY DEVICE (2026-07-18)

* **The action bar, organized.** The three lines now read in the Help
  screen's order — care, then explore, then grow, then manage — with the
  parenthetical hints dimmed, and the Options→Keys page lists bindings in
  the same order the bar shows them.
* **One hint language.** Every screen's key hints agree: "ESC out" leaves
  to home, "ESC back" goes up a level — DigiCore's "close" dialect, a
  verbless "ESC", the cup's "ENTER enter" stutter and the bug reporter's
  odd separators all converted.
* **The key that opens a screen closes it.** `t` closes training, `n`
  closes the egg guide, `?` closes help — and `q` in help now quits the
  app like it does everywhere else.
* **One gate for every refusal.** The cup, DNA lab and raid all refuse
  through the same dead/egg/asleep gate — and a raid press now disturbs a
  sleeper like every other care key (it was the one free poke).

## 0.5.61 — LIVING WORLD (2026-07-18)

* **Adaptive raid bosses.** The shared pool sizes itself to the community:
  a fresh gate opens fellable by a small crew, every kill raises the next
  bar, an escape shrinks it back to what the crowd proved it can do — and
  an escaped boss now pays by your contribution, not a flat consolation.
* **A winnable weekend cup.** The weekend featured cup draws from your
  pet's own bracket (a Mega still gets the open field), and a cross-season
  qualifier wall names the season it's from.
* **An honest DNA lab.** The charge page says what charging is for, the
  wager strip prices every band live (including the one that used to buy
  nothing, silently), and the charge cursor no longer offers the dud Field.
* **Shop with character.** Every item's dossier carries a tagline, and the
  README demo shows the real shelf.
* Housekeeping: year-stale cloud saves prune at the gate, and the relay's
  two day-clocks agree (UTC).

## 0.5.57 – 0.5.60 — the honest lane and THE NEW SHOP (2026-07-18)

* **0.5.60 — THE TUIPET ITEM CATALOG.** The shop rebuilt from scratch:
  29 authored items + the 11 Digimentals, every cell wearing real device
  art. Foods are eaten on the LCD through their own strips; toys play
  their real shows (bounce/ride/recital/TV/bath/shower) and turn live
  dials; birthday treats are real bag items at last; old goods traded in
  one-for-one on load.
* **0.5.59 — the honest update.** The source's refusal gates (a sick or
  messy pet turns down food, training and fights with the head-shake);
  raid gate shows live timers and its true payouts; cup purses show what
  they actually pay and a fallen pet can't be crowned; cloud saves
  hardened against clock drift, oversized saves, and misleading warnings.
* **0.5.58 — meat on the real strip** + a freshly recorded README demo.
* **0.5.57 — the pill is eaten.** The source has no heal animation: the
  pill rides the same eating action as meat. The old floating, half-
  clipped medicine strip is gone.

## 0.3.x–0.5.56 — 2026-07-15 → 2026-07-18 (the fast lane)

Releases in this stretch shipped daily — often hourly — and each carried its
note on the title screen rather than here. The headlines, newest first:

- **0.5.50–0.5.56 — the shop, finished.** The classic four-tab storefront
  returned ([Food] Items Eggs Honors), every item wears a real device icon,
  the dossier shows effects/held/shortfall live, a crest egg names the armor
  form it would trigger *right now*, buy/sell verdicts flash, and sealed
  Digimental waves tease their unlock.
- **0.5.49 — strict-DSprite items.** The borrowed furniture (Toilet, Port.
  Potty, Futon) left with toilet training and the tuck-in; poop lands on the
  floor and the clean action washes it, full classic. Old bags shed the
  fixtures on load.
- **0.5.28–0.5.48 — the polish wave.** Digimental discovery waves; the
  status box rebuilt as one honest module (live data only, every screen);
  real-calendar cups (seasons, weekends, holidays); egg carousel, theme
  picker and options polish; update-then-restart flow; two live crash fixes;
  a full internal modularization (nothing over ~1,200 lines) and a live PvP
  smoke that caught a payout crash.
- **0.5.0–0.5.27 — BASIC VPET.** The clone experiment (0.3.x–0.4.x) was set
  aside and the classic game shipped as 0.5.0, then stripped to a lean,
  faithful core: weather, mood, spirit, nutrition, fatigue/injury, day/night,
  adventure/towns, habitats and the licence economy all retired; raids, the
  0.5-style drill and HP-race battle, condition-earned eggs and egg-wired
  scenes took their place.

## 0.2.476 — 2026-07-14

One voice everywhere: key hints read ENTER/ESC in every screen, the battle give-up prompt agrees with itself, effort is called effort wherever it appears, the bag is always the bag, and a sweep of typos and mixed punctuation is gone.

## 0.2.475 — 2026-07-14

The game remembers out loud now: coming back tells you what happened while you were gone, first-ever stages and species get a ★, past generations rest on the DigiCore LEGACY page, map conquest shows in TROPHIES, rare finds say RARE, and quitting says goodbye properly.

## 0.2.474 — 2026-07-14

Smoother first steps: no login wall before you've met your pet (the lobby asks when you go online), the egg picker opens the egg guide with N, retiring a living pet asks first, and help finally explains the weather.

## 0.2.473 — 2026-07-14

tuipet got tougher: a damaged save is rescued and named instead of silently replaced, a crash saves your pet and files its own report, a second running copy is caught before it eats your save, and cloud sync has an on/off switch in options.

## 0.2.472 — 2026-07-14

Honors shine in the lobby now: titled tamers wear a star right in the roster, your own title sits on the you-line, and long names scroll through the sidebar instead of clipping. (New this week: cup stakes, stage-priced assistant, 9999 DNA wagers, and the HONORS board itself -- titles up to 250k in the shop.)

## 0.2.471 — 2026-07-14

Bits are worth spending! Cups now take a STAKE (a quarter of the purse -- champion nets +75%, a quarterfinal exit eats it), the assistant's retainer scales with your stage, DNA wagers go to 9999 (big ones never spoil and splash the neighbor Fields), and the shop has an HONORS board: tamer titles up to 250k, each with its own inscription, that ride your card in the lobby.

## 0.2.470 — 2026-07-14

Bits are worth spending! Cups now take a STAKE (a quarter of the purse -- champion nets +75%, a quarterfinal exit eats it), the assistant's retainer scales with your stage, DNA wagers go to 9999 (big ones never spoil and splash the neighbor Fields), and the shop has an HONORS board: tamer titles up to 250k that ride your card in the lobby.

## 0.2.469 — 2026-07-13

The attribute trade now reads as a trade. Board Game, Skateboard, Dumbbell, Computer Game, Music Player and Television MOVE power between Vaccine/Data/Virus -- they always did, but the shop showed it as two unrelated numbers. It now says Va->Da15, plainly.

## 0.2.468 — 2026-07-13

The shop stops hiding things. Items now show what they ACTUALLY do: Miracle Drink costs 6 hours of your pet's LIFE, Vitamin costs 1, and the Gold Pill buys you 12 -- none of which was ever shown. Med finally admits it treats illness. Same truth on the shelf, in the bag and on the feed page.

## 0.2.467 — 2026-07-13

Lobby chat polish: emoji and Japanese text used to tear the roster divider off its column -- chat now measures TERMINAL CELLS, not characters. Dev announcements ring out bright instead of hiding in the chatter, and blocking someone finally sweeps away what they already said.

## 0.2.466 — 2026-07-13

A Mega is a MEGA now: 'Mega-class felled' was quietly counting Ultimates too, so the Mega-class eggs and every KO6 evolution came far too cheap -- and a PvP Mega no longer counts at all. The album eggs now span generations instead of all dropping on your very first pet.

## 0.2.465 — 2026-07-13

Neglect has teeth again: filth, a held-in poop and an ignored care call were draining mood 60x too slowly, so leaving your pet in a mess was nearly free. Clean up after it. Attentive owners will not notice a thing.

## 0.2.464 — 2026-07-13

tuipet updates itself now: on launch it quietly installs any newer release and tells you to restart to play it — no more pip commands. Turn it off with a on the options Update row if you would rather do it yourself.

## 0.2.463 — 2026-07-13

The dragon eggs are worth chasing now: Slayerdra, Breakdra and Draco gave the same dragon but cost 6, 26 and 12 species — so two were pointless. Each is now earned a different way: 30 wins, 3 Mega kills, or 6 species raised. Pick your route (n).

## 0.2.462 — 2026-07-13

Egg lines fixed: 21 of the newer digitama were letting their babies evolve into forms their own device chart forbids. Each egg now walks its real line — a Draco egg goes Petitmon, Babydmon, Dracomon, Coredramon, and a DORU egg raises a true DORUmon.

## 0.2.461 — 2026-07-13

The album can be finished now: its target counted 329 duplicate dex rows (one species sits on several device pages), so it read 1218/1547 and could never reach 100%. Both halves now count real species — check it on the digicore (d).

## 0.2.460 — 2026-07-13

The update option now actually updates: g options → Update, ENTER to check, ENTER again to install it right there. Then restart to play the new version. On iOS (which cannot run pip for you) it hands you the command instead of pretending.

## 0.2.459 — 2026-07-13

No more silent failures: if the cloud refuses your saves (because tuipet is open in a newer session) you are now TOLD, instead of quietly losing cross-device progress. Same for a bug report that cannot be sent or saved — tuipet no longer promises what it cannot deliver.

## 0.2.458 — 2026-07-13

Termux sound fix: if you installed the termux-api package but not the Termux:API app, tuipet thought sound was working and went completely silent — no beeps, no bell. It now detects the dead bridge and falls back to the terminal bell, and Options tells you the truth.

## 0.2.457 — 2026-07-13

Sound, honestly: on iPhone/iPad the system blocks audio players outright, so tuipet no longer pretends otherwise — Options reads 'bell (iOS)' and milestones ring the terminal bell. Anywhere else, a player that cannot actually run now retires instead of silently swallowing every beep.

## 0.2.456 — 2026-07-13

iPhone and iPad are officially supported now, via a-Shell — and a real bug came with it: on iOS the home folder is read-only, so saves were failing SILENTLY and pets never persisted. tuipet now saves to a writable folder on every platform, and says so loudly if it ever cannot save.

## 0.2.455 — 2026-07-13

Weather actually happens now: the sky was only rolling 2x a day instead of 144x, so it almost never left Clear — rain, snow and storms were effectively dead. Skies now turn properly, and with last build's temperature fix your habitat's climate finally matters.

## 0.2.454 — 2026-07-13

The weather is REAL: temperature was drifting 20x too slowly to ever catch its season — summer read like winter. It now tracks the clock properly, so summer bakes, nights chill, and storms actually bite. Watch your pet's comfort band.

## 0.2.453 — 2026-07-13

Cups run once an hour: entering a tournament now spends that hour's cup, so bits are earned instead of farmed by re-rolling the same bracket. A fresh cup opens every hour and the whole card resets daily — adventures are worth the road again.

## 0.2.452 — 2026-07-13

Fair fights: lobby battles now clamp an opponent's card to what the game can actually produce, so nobody can turn up with an unkillable mon. Jogress and the relay were audited clean. Your bouts are honest.

## 0.2.451 — 2026-07-13

The road is REAL now: adventures live-tick the life-sim, so your mon gets hungry, sleepy and weathered out there — pack food, watch the alarm, and use the road keys (f, h, i) when it calls. Battles, towns and menus still pause time, and a mon lost on the road is carried home.

## 0.2.450 — 2026-07-13

Adventure feel, pass five: coming home victorious now means something — the zone-cleared line lands over your house as the teleport drops you off. The whole journey is also locked end-to-end by test now: out, march, town, showdown, home.

## 0.2.449 — 2026-07-13

Adventure feel, pass four: reaching a zone boss now STOPS the march at its gate — the boss looms, you square up, and SPACE engages when you're ready. A boss is a showdown you walk into, not another surprise. Wild encounters still strike on the spot.

## 0.2.448 — 2026-07-13

Adventure feel, pass three: a sick mon now TRUDGES the road at half pace with its collapse poses, an elder drags the aged shuffle, and a sleeping traveller naps roadside under its Zzz — the journey (and its encounters) wait until it wakes.

## 0.2.447 — 2026-07-13

Adventure feel, pass two: an ! mark pulses while your mon digs at something off the path and when it spots a discovery, and the victory parade now marches on a bright stage so every boss reads crisp. Keep the reports coming — B files a bug from anywhere.

## 0.2.446 — 2026-07-13

Adventure feel, pass one: your mon now MARCHES clear across the screen as it travels, town gates show the town when you arrive, a waiting zone boss looms at its gate in a real faceoff, and care emotes stopped sitting on your mon's head. More polish passes coming.

## 0.2.445 — 2026-07-13

Frailty warning: an Ultimate or Mega carrying 3+ care mistakes now shows a +frail! badge and calls out how many slips it can survive — elder death no longer strikes from nowhere. Check Care x anytime on the digicore (d) CONDITION page.

## 0.2.444 — 2026-07-13

Adventures now END: beat the zone boss and your mon takes a victory teleport home — one expedition, one boss, done. The next adventure sets out for the next zone. Boss fights are also labeled BOSS on the battle card instead of reading like a random encounter.

## 0.2.443 — 2026-07-13

Honest skies: rain vs snow now follows the temperature on your display — no more flurries at 46 degrees, and an ongoing snow turns to rain the moment it warms past freezing. Found treasures also ride in front of your mon on the walk home instead of clipping into it.

## 0.2.442 — 2026-07-13

Expedition identity: every adventure now wears the habitat its name promises — Cliffside Approach is sea cliffs, Skyfall Pass is the open sky, Sunscorch Dunes is desert — 12 habitats across the world, one per adventure. Found items also show at proper hand size beside your mon.

## 0.2.441 — 2026-07-13

Adventure overhaul: every expedition keeps ONE biome from the first step to the boss, the pet holds a proper stage spot, weather follows you on the road, and no beat can be skipped any more. Also: no more white poses in a dark room, the futon truly keeps you cozy (no freezing status under the covers), and toys like the balloon play fully on-screen.

## 0.2.440 — 2026-07-13

Futon fix: the futon now truly maintains temperature — while your pet is tucked in, its temperature is pinned in place, so it can no longer catch cold under the covers (and a sick pet's fevers and chills hold off too). It still isn't a heater: warm a cold pet up before bed.

## 0.2.439 — 2026-07-12

Theme glow-up: gameboy and paper backgrounds are drawn by a new colour-aware engine — scenes keep their shapes (the desert dunes, the town skyline, the digicore) instead of washing out flat, and the paper theme now renders scenery as clean ink-wash whites. Pick a theme under g options.

## 0.2.438 — 2026-07-12

The DIGITAMA GUIDE (now on the ACTIONS bar) — press n to browse every egg in the game: what you own, what is waiting in a shop, and exactly what earns each locked one, with live progress counters. The carousel still shows only your hatchable eggs; the guide is the map to the rest.

## 0.2.437 — 2026-07-12

The DIGITAMA GUIDE is here — press n on the home screen to browse every egg in the game: what you own, what is waiting in a shop, and exactly what earns each locked one, with live progress counters. The carousel still shows only your hatchable eggs; the guide is the map to the rest.

## 0.2.436 — 2026-07-12

Polish + hardening pass: a full or read-only disk no longer crashes the game when it autosaves, the lobby shrugs off malformed messages instead of freezing, and several menus read cleaner — Options now shows ? and Enter properly, and the battle surrender and travel hints match their screens.

## 0.2.435 — 2026-07-12

Private messages you receive in the lobby are now saved even if you quit straight out of it — no more losing a PM that arrived right before you closed the game.

## 0.2.434 — 2026-07-12

Private messages now reach players who have stepped away: a PM sent while they're offline is held and delivered the next time they open the lobby, and your own copy is always kept.

## 0.2.433 — 2026-07-12

Help menu polish: the how-to now covers Train (it was missing), lists Quit, and the scroll footer shows how much more there is to read instead of repeating the controls.

## 0.2.432 — 2026-07-12

Eggs are earned now: you start with the five classic babies and unlock the rest by reaching stages, clearing region bosses and building your album. Common eggs stock the home shop; the rarest are exclusive to their biome's town.

## 0.2.431 — 2026-07-12

Shop polish: the closed-shop sign is clean and readable again, item effects fit their panel without clipping, and the storefront reads as tuipet's own.

## 0.2.430 — 2026-07-12

Adventures feel alive: standing on the road now behaves like your home biome -- poop, weather and care icons all show -- and the weather changes as you travel between regions. Shops stay in the towns you visit.

## 0.2.429 — 2026-07-11

Attack orbs fixed: mons were firing their attack POSE instead of their projectile. 75 classic species now shoot their real device attack sprite -- flames, bolts, bombs -- in battle, training, and adventure.

## 0.2.428 — 2026-07-11

Visual polish sweep: every screen eyeballed in a full render audit -- no more clipped status text, real arrow scroll markers, and the login and DigiCore now speak the hint language.

## 0.2.427 — 2026-07-11

Device-accurate attacks: the classic V-Pet lineup now fires its REAL hardware attacks -- 81 species with their own body-sized projectiles ripped straight from the devices, 27 of them animated, in battle and training alike.

## 0.2.426 — 2026-07-11

Trust your shots: every attack orb in the game was audited against the real device data -- all 1,597 Digimon verified to fire their correct special or power-tier projectile, and the guarantee is now locked in by the test suite.

## 0.2.425 — 2026-07-11

The lobby is no longer a pause room: time keeps flowing while you chat or read DMs, and your pet's care alarm rings through -- with an on-screen nag on the hint strip. PvP battles and jogress still freeze time, so sessions stay safe.

## 0.2.424 — 2026-07-11

The big audit patch: battle banners, orbs and the teleport wipe stay inside the play window; bag items now match feeding (no more 60x Gold Pill); the versus cheat chart holds its printed pattern; town shelves stock their local goods again; and old or cross-version saves can't crash the game.

## 0.2.423 — 2026-07-10

HP drill polish: the reel no longer cuts away to your mon between picks -- the stage holds steady, wrong picks earn the dummy's taunt, and your mon saves itself for the final volley.

## 0.2.422 — 2026-07-10

Vaccine mash fix: the Hit!! banner no longer covers the meter -- the fill stays pinned at the top and the banner flashes below it, so you can watch the meter WHILE you mash.

## 0.2.421 — 2026-07-10

Training polish: the Vaccine mash fills a real on-screen meter (DM20 canon), the Data partner taunts you when it blocks your shot, and the Virus zone flashes when it's time to STOP.

## 0.2.420 — 2026-07-10

The training menu is back and visible: a proper list of all four drills with a cursor (v0.2.419's scene-preview picker looked like no menu at all).  Arrows pick, 1-4 jump, ENTER starts.

## 0.2.419 — 2026-07-10

The training menu is a real picker now: browse the drills with the arrows and the LCD previews each one's actual stage -- the old text diamond is gone.  1-4 still jump straight in.

## 0.2.418 — 2026-07-10

Hotfix: opening the new Data versus training crashed the app (the status card still read the old turret fields). The card now counts rounds and passes like the HP drill's.

## 0.2.417 — 2026-07-10

The Data drill is now the REAL DM20 versus training: YOU fire high or low past the sparring partner's shield, 3 of 5 rounds to pass -- the fan-made turret is gone, and the manual's secret pattern chart works here too.

## 0.2.416 — 2026-07-10

The Data drill got room to breathe: the shield is now held right in front of your mon, the middle of the stage is open air, and the cannon's shot visibly leaves the muzzle and arcs into the shield.

## 0.2.415 — 2026-07-10

Training impacts hit BIG again: the orb-strike explosion is back to its full 32x16 flash, and the punch drill's Hit!! banner now takes over the whole window like the battle banner.

## 0.2.414 — 2026-07-10

Training's Hit!! banner is crisp again -- the sprite was decoded at the wrong scale (3x of a 4x asset) since day one.

## 0.2.413 — 2026-07-10

The mood bubbles (sun, rain drip, dying) pop whole at head height again -- they were getting cut at the top of the play window.

## 0.2.412 — 2026-07-10

Hotfix: the egg carousel renders whole again (a bad clip was cutting the eggs).

## 0.2.411 — 2026-07-10

The sick mark now floats up at head height beside your mon, the way the real device draws it -- and a sick sleeper keeps its Zzz on top with the skull tucked underneath.

## 0.2.410 — 2026-07-10

Fixes for the window law: meals descend fully on-screen again (no more clipped food), the punch drill's Hit!! banner is back, and the training strike burst is centred in the matrix where it belongs.

## 0.2.409 — 2026-07-10

The 32x16 window law: every sprite now lives inside the true dot matrix like the real device -- nothing hangs over it, things leave only off the sides, rain still soaks the whole LCD, and the training drills were restaged to fit.

## 0.2.408 — 2026-07-10

The LCD is a stage again, the way Bandai built it: your mon gets its whole 32x16 world back -- a skull stands beside it when it's sick, Zzz floats overhead when it sleeps, and every status badge moved to the panel where it belongs.

## 0.2.407 — 2026-07-10

Fixed: a screen's key hints no longer stick to the message box after you leave it (exiting the lobby left its hints up until the next care call).

## 0.2.406 — 2026-07-10

New status rail: every icon (Zzz, conditions, emotes, the care-call '!') now lives in its own fixed rail on the right edge -- nothing rides the pet, sprites never overlap, and your mon keeps clear of the icons and the mess it made.

## 0.2.405 — 2026-07-10

Evolution trees rebuilt from the real devices: every device egg now raises its true line -- Deep Savers is ocean Digimon again, Corona and Luna split for real, dragon eggs fuse into Examon, and Pendulum attribute jogress is live in the lobby.

## 0.2.404 — 2026-07-10

Egg shop audit: duplicate eggs that sold you what you already own are gone -- every egg in the shop now earns its shelf. Win-trophy eggs spread out (25/40/50/60/75/100 wins each unlock something), and a save repair fixes lineage eggs wrongly shown as owned.

## 0.2.403 — 2026-07-10

Nature Spirits is BACK -- Bubbmon returned with his full sprite set, so the Pendulum 1 egg leads the field eggs again. And the DIGICORE evolves page now shows what is next at EVERY age (eggs tease their hatchling) instead of saying "too young".

## 0.2.402 — 2026-07-10

Egg quality pass: every digitama in the game now plays its real device animation -- settle, bobble, crack. The egg select lines up in device order (Ver.1-5, then the Pendulum fields), and town shops tease locked eggs with how to earn them. All killer, no filler.

## 0.2.401 — 2026-07-10

The new digitama came alive: 18 now play their real device settle-and-crack animation, and the one-of-a-kind designs rock in place -- every pixel official, always. Hatch something from the 35 new eggs and go show it off in the lobby!

## 0.2.400 — 2026-07-10

35 NEW EGGS -- the real device digitama, dot-for-dot: DM Version 1-6, Corona & Luna, the six Pendulum field eggs, the DMX eggs and more. Version 6 hatches Bubbmon, a whole new line to raise. Some eggs only unlock by battling or fusing with other tamers online!

## 0.2.399 — 2026-07-09

Every screen talks now: the message box under the LCD pops live key hints for exactly where you are -- attack keys mid-battle, charge hints in DNA, fold/scroll hints in the lobby, and a ✉ nudge the moment someone DMs you. No key is a mystery anymore.

## 0.2.398 — 2026-07-09

Lobby comfort pass: press → to fold the player box away and give the chat the whole screen (↑↓ then scroll the log; ← brings the box back) -- and your private message threads now SURVIVE leaving: close a PM or the lobby and the whole conversation is still there.

## 0.2.397 — 2026-07-09

The dev can speak now: watch for 📢 server announcements -- they land in the lobby chat and flash on your home screen, so news like events, fixes and downtime reaches you in the moment.

## 0.2.396 — 2026-07-09

Town shelves ring true now: Mossford's egg shop matches its mossy woods (a crossed wire had it selling factory eggs) and local specialties charge the town's OWN price -- Dunehaven's famous ice cream is 75 bits, half what the stall was overcharging.

## 0.2.395 — 2026-07-09

New here? Press ? for a Help screen -- every control and a quick how-to (care, adventure, cups, lobby, and how your pet grows), so none of the keys are a mystery.

## 0.2.394 — 2026-07-09

Hit a bug? Press B to report it right from the app -- type what went wrong and it goes straight to the dev (works even outside the lobby, and saves to retry if you are offline). Your version and pet ride along so it can be fixed fast.

## 0.2.393 — 2026-07-09

No more waiting on a cup you can't enter: the home tournament now shows the next hour you can actually win a cup ("next winnable 14:00 Deep Saver Cup"), skipping the ones your pet is locked out of by field, attribute or tier.

## 0.2.392 — 2026-07-09

Every town now hosts its own championship: its biome's field cup sits always-open on the cups board (Coral Deep runs the Deep Saver Cup, Gloamgate the Nightmare Soldier Cup), and the rivals you face in a town's ring skew toward its local kind.

## 0.2.391 — 2026-07-09

The adventure world has a name now: cross real regions like the Coastlands and the Ironlands, and rest in 26 named towns -- Dunehaven, Coral Deep, Frostmere -- each with its own biome greeting and local goods fronting the shelf.

## 0.2.390 — 2026-07-09

Lobby DMs got real: [V]iew a player for a private thread with just your convo (a ✉ badge flags unread ones), and [X] blocks anyone whose vibe is off -- their chat, DMs and invites go quiet.

## 0.2.389 — 2026-07-09

Can't find anyone to battle? Players with the app open but not in the lobby now show as ghosts you can [P]ing -- one key nudges them to hop into the lobby so you can actually battle or jogress.

## 0.2.388 — 2026-07-09

Two ways to get eggs now: EARN the special ones by playing -- raise 5+ Digimon for the dragon egg, win 50 battles for the Jesmon egg, carry the X-Antibody, crack a password -- and they unlock FREE. The rest you discover and buy in the themed town shops.

## 0.2.387 — 2026-07-09

Egg shops spread across the world: each town now stocks eggs matching its habitat -- dragon eggs near fiery lands, sea eggs by the coast. Explore to find them; starters stay on the home counter.

## 0.2.386 — 2026-07-09

More real evolution lines: the Pichimon egg now raises the Sun & Moon line up to Apollomon and Dianamon, joining the Dracomon road to Slayerdramon and Breakdramon.

## 0.2.385 — 2026-07-09

The Dragon line is here: the Petitmon egg now raises Dracomon all the way up to Slayerdramon and Breakdramon. And the egg shop is cheaper -- license eggs now cost 1500 bits, down from 2500.

## 0.2.384 — 2026-07-09

Lobby fix: if a fusion falls through on your partner's side (their pet dozed off or ran low on DP), you're now told right away instead of being left waiting at the fusion screen.

## 0.2.381 — 2026-07-08

DNA fix: charging DNA into a fully-trained pet no longer knocks an Effort heart off it — the charge tops out just shy of full instead of dragging a maxed gauge back down.

## 0.2.380 — 2026-07-08

Three eggs fixed: the Pupumon, Bommon and Sunamon lines no longer strand a well-raised pet at Champion — their best-care roads now climb all the way to Mega like every other line.

## 0.2.379 — 2026-07-08

Tidier cleanups: when your hired helper mucks out after a sleeping pet, the mess now sweeps off to the side with it instead of bunching up under the snoozing mon.

## 0.2.378 — 2026-07-08

Let sleeping mons lie: using a toy, book or item on a sleeping pet now wakes it up grumpy, just like the real device — only the Futon lets it keep dozing. Slip one under a tired pet without disturbing its rest.

## 0.2.377 — 2026-07-08

Your pet listens now! Walking, feeding and training no longer refuse every few seconds — a decently-raised pet obeys, while a neglected one still acts up. No more scolding it just to take one step.

## 0.2.376 — 2026-07-08

Chat & names now take punctuation — apostrophes, !, ?, and symbols all type now. Plus status poses (yawn, sick) play right where your pet stands with its icons kept, and food drops beside the poop instead of onto it.

## 0.2.375 — 2026-07-08

Toys come alive! Every item now plays its real device animation — balls bounce, balloons play, dumbbells lift, showers shower. Plus DNA divergence (DNA ▸ Divergence) and lobby chat scrollback (PgUp).

## 0.2.370 — 2026-07-07

DNA divergence: charge one Field to steer evolution onto the wild road (DNA ▸ Divergence). Lobby chat polished: PgUp scrolls the log, PMs/mentions highlight, your lines dim. Album counter on the DigiCore.

## 0.2.369 — 2026-07-07

DNA can now steer evolution! Charge one Field to its threshold and the next evolution takes the wild road — see DNA ▸ Divergence. Album progress on the DigiCore.
