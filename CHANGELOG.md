# Changelog

Player-facing notes per release — the same line each version shows on its
title screen. Full commit history: [GitHub](https://github.com/joeltco/tuipet/commits/main).

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
