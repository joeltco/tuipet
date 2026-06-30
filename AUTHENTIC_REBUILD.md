# tuipet — Authentic 20th-Anniversary Rebuild Plan

**Decided 2026-06-29.** Pivot away from cloning DVPet (a fan emulator built on ripped
Bandai assets). Goal: an **authentic** all-in-one Digimon v-pet covering **every 16×16
monochrome dot-matrix device documented on humulos** — i.e. the classic 32×16-screen line:

- **Digital Monster Original (dm)** — 1997 Ver.1–5
- **Digital Monster Ver.20th (dm20)** — 20th revival of the original DM
- **Digital Monster X (dmx)** — low-res 16×16 screen (same model family as the Ver.20th;
  NOT the higher-res Pendulum X). Brings the **X-Antibody** roster + **X-evolution**.
- **Digimon Pendulum Original (pen)** — 1998–99 Ver.1–5 (+5.5)
- **Digimon Pendulum Ver.20th (pen20)** — 20th revival of the original Pendulum

**Render: MONOCHROME 1-bit sprites on COLOR backgrounds.** (User decision 2026-06-29.)
- **Sprites: monochrome, always** — 1-bit dot art, dark silhouette (`SIL_DAY` ink). Unchanged.
- **Backgrounds: color** — KEEP DVPet's habitat scenes + day/night, re-fit to 32×16. (Weather DROPPED.)
The 32×16 dot GRID is locked. The only thing dropped from the old spec is the *whole-screen*
1-bit look (blank LCD / no color bg); the pet ink stays 1-bit either way. (Authenticity note:
real mono devices had a blank LCD — the color bg is a deliberate aesthetic choice.)

**EXCLUDED.** The dividing line is SPRITE SIZE, not color:
- *Color 16×16 devices* (excluded by the mono-only decision): Digital Monster Color (dmc),
  Pendulum Color (penc), Digivice 25th Color (dvc), D-3 25th Color (d3c), and the Color
  crossover editions (Xros 15th dmxw, Godzilla 70th dmgz, Monster Hunter 20th dmh).
- *Larger-sprite / hi-res devices* (not 16×16 at all): Pendulum Z (penz), Vital Bracelet BE
  (vbbe), Vital Bracelet Digital Monster (vbdm) — bigger LCD + side-scrolling menu
  (Pendulum Progress/X lineage) or color hi-res. Don't pull these.

Keep the online layer (battles + jogress). Rebuild sounds clean + Termux-friendly.

This file is the durable spec; the conversation that produced it will be compacted.

---

## 0a. GUIDING PHILOSOPHY — classic v-pet purist (decided 2026-06-29)

The whole pivot is about authenticity. These principles override convenience:

1. **Clean-sourced data — do NOT inherit DVPet's roster blob.** DVPet's `digimon.csv`
   (1,219 mons) is a fan SUPERSET with custom stats, invented evolution conditions, and
   non-canon entries. Building a purist pet on it repeats the copy-of-a-copy problem.
   Rebuild each device's roster + **exact evolution conditions** (care mistakes, training,
   overfeed, weight, battles, win-ratio, sleep timing, version-locks) from humulos's
   per-version tables + wikimon; sprites from authentic 16×16 rips (Spriters Resource /
   official Digimon Channel dot archives). Fixes authenticity AND the ethics in one move.
2. **Per-device / per-version faithful emulation with a SELECTOR — not a blended roster
   soup.** Each run is true to ONE device's roster, rules, sleep schedule, and battle
   behavior. Authentic precedent: DM20 itself is an all-in-one (Ver.1–5 with a version
   picker), as is Pen20. Keep per-device/version provenance in the data.
3. **Cross-device battle + jogress over the wire is itself authentic** — that's exactly
   what the real connector port did. The online layer IS the purist connectivity. Keep it.
4. **Authentic mechanics, REAL-TIME.** Shadow-boxing training (pet right / shadow left /
   high-low), real care-meter, real-time aging + sleep windows, poop/sick/call timing,
   canonical death conditions, attribute triangle (Vaccine→Virus→Data→Vaccine) + power for
   battle. No invented drills, no accelerated clock. DMX adds X-Antibody/X-evolution;
   Pendulum adds areas/version themes — keep those per device.
5. **Completeness, honestly.** Source every monster the real device had — incl. the gaps
   DVPet lacks (see §3a: N.E.O + several DMX X-forms) — rather than quietly omitting them.
   Keep the roster CLEAN: no fan-made / non-canon mons (the mono-16×16-only rule enforces this).

Mantra: **clean-sourced, per-device-faithful, real-time, monochrome — verified against
the canon, not DVPet.**

### Rebuild strategy (decided 2026-06-29)
**In-place, on branch `feat/authentic-rebuild`** — NOT a from-zero rewrite. It's a
"keep-the-chassis, replace-the-game" rebuild:
- **KEEP (chassis, authentic-agnostic):** `render.py` (resize 40×24→32×16, lock mono),
  `net.py` / `cloudsync.py` / `persistence.py` + the lobby server (online + saves),
  `app.py` Textual shell + screen/menu framework (strip weather/day-night hooks),
  `sound.py` **playback mechanism** (keep player, swap content for chiptune).
- **REBUILD from canon:** `data.py` + `data/` (clean DM20 data + new 16×16 atlas — NO
  DVPet csv/sprites), `evolution.py`, `pet.py` (real-time care/aging), `training.py`
  (shadow-box), `egg.py`, `battle*.py`/`jogress*.py`/`dna*.py` (reskin to 32×16 + triangle).
- **DELETE:** `weather.py`, day/night, habitat backgrounds, DVPet drills/data/sprites/sounds;
  and (pending §8 audit) likely `adventure*.py`/`tournament*.py`/`digicore*.py`/`shop*.py`
  (classic DM/Pendulum had no shop/adventure/tournament — just feed/train/battle/clean/heal/
  sleep/jogress; Pendulum's light "areas" are the one maybe-keep).
- **PyPI: HOLD republish** until the bundled ripped DVPet/Bandai assets are gone (current
  published wheel ships them — the ethics concern). Keep shipping nothing new meanwhile.

---

## 0. Ground-truth sources (authentic — NOT DVPet anymore)

DVPet (`_decompiled/`, `_extract/`, `raw_resources/`) is **deprecated as ground truth**.
It is a fan composite of many devices and ripped art — exactly what we're moving away
from. Use it only for cross-checking logic, never as the canon.

New canon sources:
- **humulos.com/digimon/** — index of all 15 device guides. **WebFetch works on this
  domain** (confirmed). The five mono-16×16 devices we want: `/digimon/dm/`,
  `/digimon/dm20/`, `/digimon/dmx/`, `/digimon/pen/`, `/digimon/pen20/`. Each guide =
  per-version rosters + exact evolution requirements (care mistakes / training / overfeed /
  battles / win-ratio / weight / sleep). Pendulum (pen/pen20) versions = Nature Spirits /
  Deep Savers / Nightmare Soldiers / Wind Guardians / Metal Empire (+ Pendulum's 5.5 —
  verify which the originals/20th include). dmx = X-Antibody roster + X-evolution mechanic.
  **⚠ The pen/pen20 WebFetch returned a CONTAMINATED list** (modern non-Pendulum mons —
  Herissmon/Appmon, Ludomon, Bryweludramon/PenZ-era); use per-version pages and cross-check
  wikimon, don't trust a single broad fetch for Pendulum. dm/dm20/dmx fetches looked clean. See §3a.
  Roster extraction must be per-version anyway; fetch `/digimon/<dev>/checklist/` and
  `/digimon/<dev>/<version#>/` per version. (dmx `/checklist/` works; dm20 uses `/list/`.)
- **wikimon.net** — per-Digimon data, evolution lines, version exclusives.
- **The Spriters Resource → LCD Handhelds → "Digimon Digital Monster Ver. 20th"** — the
  16×16 LCD sprite rips. (WebFetch 403s on spriters-resource; download via browser / `!`
  shell with a normal user-agent, or use the withthewill archive below.)
- **withthewill.net / lcd.withthewill.net (FileIsland)** — community 16×16 v-pet sprite
  archives + mechanics writeups.
- **lostintranslationmon.com** — device mechanics (training, battle, evolution, care).

When data is missing: say so and flag for verification. **Never fabricate stats/sprites.**

---

## 1. Authentic hardware spec (CONFIRMED)

- **Dot-matrix field: 32 dots wide × 16 dots tall.** (Confirmed: "original v-pets prior to
  Pendulum Progress (2002) were always 16×16 sprites on a 32×16 screen.") In tuipet this is
  a logical PLAY WINDOW anchored inside the existing 40×24 LCD (see rendering implication
  below) — the LCD canvas itself is NOT resized.
- **Creature sprites: 16×16 dots.** So the play field is exactly 2 sprites wide, 1 tall.
- COLOR LCD (DVPet background kept): the color day/night scene fills the field; the
  creature is a dark 1-bit silhouette over it. Dot grid is 32×16; the COLOR is in the bg.
- The **menu icon row** (feed / light / training / battle / status / clean / heal /
  call pictograms) is a row of *fixed LCD segment icons*, SEPARATE from the 32×16 dot
  field — not drawn in the dot matrix. Render it as its own UI strip.

### tuipet rendering implication — REVISED 2026-06-29 (anchor-only, NOT a resize)
- **DO NOT resize the LCD.** Keep `SCREEN_COLS, SCREEN_ROWS = 40, 12` (40×24px), keep the
  backgrounds at current resolution, keep the HUD, keep the themes/palettes. (User: "this
  should be a pretty big relief of work." Big-resize + bg re-downsample + HUD/theme rework
  all CANCELLED.)
- **32×16 = a logical PLAY WINDOW anchored inside the 40×24 canvas**, NOT the canvas itself:
  - horizontally CENTERED: `PLAY_X0 = (40-32)//2 = 4`, window x ∈ [4, 36).
  - bottom-aligned 2px from the border: window y ∈ [px_h-2-16, px_h-2) = [6, 22).
  - **anchor-only (no clipping)** — sprites are positioned within the window but may overflow
    into the margin; all sprites are 16-wide so overflow won't happen in practice.
  - Left 16-cell = action/enemy/food (x≈4); right 16-cell = the mon's home (x≈20).
- **NICE FACT: the single idle mon already satisfies this.** `render_screen` already does
  `ox=(40-16)//2=12` (centered) and `oy=px_h-16-2=6` (2px from bottom) → identical. So the
  anchor window only changes TWO-sprite scenes (battle) + the feed/action cell + roam bounds.
- Weather still STRIPPED (separate decision). No menu-icon row in the dots (TUI chrome only).

---

## 2. STRIP list (remove entirely)

- **Weather — STRIP** (2026-06-29 user decision: "drop weather"). Remove `weather.py`,
  `_weather_overlay`, the rain/snow/cloud particle overlay, `pet.weather`, and the
  weather-chance/precipitation columns' effect. Weather is a SEPARATE layer from the
  background — dropping it does not touch the background art or day/night.
- **Day/night — KEPT**. `day_phase`, SIL_DAY/SIL_NIGHT, time-of-day bg tint all stay;
  the day-phase background strips re-downsample from the 104×513 source to 32×16.
- ~~Habitat photo backgrounds~~ **KEPT**. `pet.background()` / habitat bgimg stay; the
  16 color habitat scenes re-downsample from source PNGs to 32×16. (Open: whether the
  habitat SIM mechanics — seasons/temperature/field-affinity affecting the pet — stay or
  go is a §4-mechanics decision, separate from keeping the visual backgrounds.)
- **All DVPet-derived sprites/art/sounds** bundled in `src/tuipet/data/` that came from
  `raw_resources/` / `_extract/`. Replace with authentic 16×16 LCD rips (or original art).
- **DVPet-style training drills** (the cannon/shield "Data" drill, the power-bar "Virus"
  drill, the mash "Vaccine" drill, HP icon-match). Replace with the **one authentic
  training minigame** (see §4).
- DVPet-specific extras that aren't on DM20/Pen20 (audit `shop.py`, `adventure.py`,
  `digicore`, `tournament`, `dna/jogress` vs what the real devices actually have — keep
  what's authentic, cut the rest). Jogress + battle stay (§5).
- Distribution concern: the current PyPI wheel ships extracted DVPet/Bandai assets. Once
  art is replaced with clean/licensed sprites, that problem goes away. Until then, be
  careful about publishing.

---

## 3. Monsters & evolution (five mono-16×16 devices: dm, dm20, dmx, pen, pen20)

Extract all five from humulos + wikimon **per device/version** (NOT as one merged pool — see
§0a.2). dm20 ≈ dm (revival) and pen20 ≈ pen — heavy overlap, but keep each device's roster +
version provenance distinct so the selector can run each faithfully. **dmx** adds the
X-Antibody Digimon and the X-evolution mechanic (Digimon can gain the X-Antibody → an
X-form line); fold that into the evolution engine. **Do NOT seed from DVPet's `digimon.csv`**
(fan superset) — rebuild clean from canon.


### DM20 = original Digital Monster, Ver.1–5
- **Ver.1**: Botamon→Koromon→Agumon/Betamon→Greymon, Tyranomon, Devimon, Meramon, Airdramon,
  Seadramon, Numemon, … → MetalGreymon, etc.
- **Ver.2**: Punimon→Tunomon→Gabumon/Elecmon→Garurumon, Kabuterimon, Angemon, Kentarosmon, …
- **Ver.3**: Poyomon→Tokomon→Patamon/Kunemon→Unimon, Ogremon, Bakemon, Kabuterimon, …
- **Ver.4**: Yuramon→Tanemon→Piyomon/Palmon→Birdramon, Togemon, Monochromon, Leomon, Kuwagamon, …
- **Ver.5**: Zurumon→Pagumon→Gazimon/Gizamon→DarkTyranomon, Cyclomon, Devidramon, …
- Plus DM20's **10 special/secret evolution lines** (Zuba, Hack, Slayerdra, Breakdra,
  Corona, Luna, Taichi, Yamato, DORU, Meicoo).
- (Above rosters are the humulos summary — **extract the full per-version monster list +
  exact sprites + evolution conditions from humulos/wikimon before building.**)

### Pen20 = original Digimon Pendulum, Ver.1–5 (areas/factions)
- **Ver.1 Nature Spirits**, **Ver.2 Deep Savers**, **Ver.3 Nightmare Soldiers**,
  **Ver.4 Wind Guardians**, **Ver.5 Metal Empire** (verify Pen20's exact included set;
  original Pendulum also had 5.5 — confirm whether Pen20 bundles it).
- Pendulum adds: shake/jogress culture, version-locked rosters, area/stage feel.

### Evolution data model to extract per Digimon
`stage` (Baby I / Baby II / Child / Adult / Perfect / Ultimate), `attribute`
(Vaccine/Data/Virus/Free), `version`, and **evolution conditions**: care mistakes range,
training count range, overfeed range, weight, battle count, win-ratio, minimum age/time,
sleep handling. Store as data tables (JSON) keyed by device+version.

## 3a. Roster-gap audit vs DVPet (done 2026-06-29)

Diffed all five device rosters (485 unique) against DVPet/tuipet's `digimon.csv` (1,219)
with a JP→EN / alt-spelling map. **Most apparent gaps were just spelling** — DVPet uses
English-dub names, humulos uses Japanese. Confirmed-present-under-alt-name examples:
Bubbmon=**Babumon**, Tunomon=Tsunomon, Caprimon=Kapurimon, Lilimon=Lilymon, Peti
Meramon=DemiMeramon, Death Meramon=SkullMeramon, Hanumon=Apemon, Karatuki Numemon=
ShellNumemon, Anomalocarimon=Scorpiomon, Vamdemon=Myotismon, Omegamon=Omnimon, Dukemon=
Gallantmon, Hououmon=Phoenixmon, etc. (**LESSON: always romanization-map before claiming a
mon is missing — a literal string search is what wrongly said "no Bubbmon" in an earlier
session.**)

**Gaps — mostly RESOLVED by the corpus pull:**
- **N.E.O** — **DROPPED per user 2026-06-29 ("forget neo").** Not building it.
- **DMX X-Antibody forms** (Scorpiomon X / Anomalocarimon X, BlackWarGreymon X, Palmon X,
  Pegasmon X, Plesiomon X, etc.) — **PRESENT in wayland-vpets** `dmall/`+`dmx/`. No longer a gap.
- **DM20 "Taichi's / Yamato's" partner variants** — minor; re-confirm in wayland (may be base-mon flavor).
- Net: **effectively no roster/sprite gap left.** Sprites come from wayland-vpets (canon-sourced).

**⚠ DATA CAVEAT:** the humulos **pen / pen20** fetch came back CONTAMINATED — it returned
modern non-Pendulum mons (Herissmon = an *Appmon*, Ludomon, Bryweludramon = Pendulum
Z-era), so that page is a broader/combined list, NOT the faithful 1998-Pendulum revival
roster. dm / dm20 / dmx fetches looked clean (81 / 154 / 166). **Re-pull pen & pen20 from
clean per-version pages before trusting any Pendulum-side roster or gap.**

---

## 4. Authentic training = SHADOW BOXING (replaces all DVPet drills)

Confirmed mechanic: **your Digimon stands on the RIGHT, a "shadow" duplicate on the LEFT.**
You press the **top button = attack HIGH, middle button = attack LOW**; the shadow tries
to **block**. Score hits over a fixed number of rounds; result feeds the training stat
(which gates evolution). This is the real DM/Pendulum training — drop the cannon/shield
invention entirely. (Pendulum training may differ slightly — verify Pen20's training and
whether it's identical to DM20's; build the authentic one(s).)

---

## 5. Keep (online layer)

- **Battles** (`battle.py`, `battlescreen.py`, `net.py`, lobby) — keep, but re-skin to the
  32×16 authentic battle presentation (two 16×16 sprites facing off, the real attack-power
  bar / hit animation). Battle resolution should follow the authentic vpet formula
  (attribute triangle Vaccine>Virus>Data>Vaccine, power/effort stats).
- **Jogress / DNA digivolution** (`jogress.py`, `dnascreen.py`, `digicorescreen.py`) — keep
  the online jogress connection; make the *results* authentic to DM20/Pen20 jogress trees.
- Server: `reference_tuipet_lobby_server` (pm2 `tuipet-lobby`, wss://ff3mmo.com/tuipet/).
  Wire protocol can stay; the payloads/rosters change to authentic data.

---

## 6. Sounds — clean + Termux-simple via "tone transfer"

- Real v-pets use a **piezo buzzer**: simple square-wave beeps + short melodies.
- Goal: the **simplest possible sound system** that works under **Termux** (Android).
  Termux has no reliable general audio; the robust path is generating tones (frequency +
  duration sequences) and playing tiny WAVs, or using a minimal beeper. **Square-wave /
  chiptune synthesis of the authentic jingles** ("tone transfer" = take the real device's
  melodies and re-synthesize them as clean simple tones) instead of shipping sampled WAVs.
- Deliverable: a `sound.py` that, given a melody (list of (freq_hz, ms)), renders/plays it
  with the lightest dependency that runs on Termux + Linux + macOS. Capture the authentic
  jingles as note sequences (evolve, eat, happy, attack, win/lose, call, refuse, death).
- **OPEN QUESTION for the user**: confirm the exact "tone transfer" intent — pure
  square-wave chiptune re-synthesis of the real melodies? And the target playback path on
  Termux (e.g. `play-audio` on a generated WAV, `sox`, or a pure-Python PCM writer)?

---

## 7. Build order — DM20 first as the gold reference (after compaction)

Purist approach (§0a): nail ONE device end-to-end, then add the rest. **Start with DM20.**

0. **Reference corpus** lives in `corpus/` (see `corpus/README.md` + `corpus/sources.json`).
   It's the research layer — mine everything (fan + canon + docs), tag provenance, canon
   wins, NOT bundled in the wheel. Session rosters already persisted at
   `corpus/canon/humulos/<dev>/roster.txt`; DVPet fan data registered in place. The unified
   `corpus/db/digimon.json` (schema in README) is the "one database" we build the game from.
1. **DM20 data extraction first** (no code churn): scrape humulos per-version + wikimon into
   the corpus → clean JSON tables — DM20 Ver.1–5 + the 10 special lines: **branching
   evolution conditions** (CM/training/overfeed/weight/win — the one thing wayland lacks).
   **Sprites + per-device stage timers come from `corpus/fan/wayland-vpets`** (canon-sourced,
   named per device, 16px native upscaled x4 — downsample /4 + split frames). **Do NOT seed
   from DVPet's csv.**
2. **Resolution cutover**: 40×24 → 32×16 (8 rows) across render/app/battle/scenes; add the
   separate menu-icon strip. Verify at default terminal size.
3. **Strip** weather / day-night / habitat bg / DVPet drills / non-authentic features.
4. **Authentic mechanics**: shadow-boxing training; real-time care/aging/sleep/poop/sick/
   call/death timing.
5. **Evolution engine** driven by the clean DM20 tables (care mistakes, training, weight,
   battles, win-ratio, time, version-locks).
6. **Battle/jogress re-skin** to authentic presentation + attribute triangle (online = the
   authentic cross-device connectivity).
7. **Sounds** rebuild (chiptune tone synthesis, Termux path).
8. **Then add DMX** (X-Antibody/X-evolution; source the missing X-forms + N.E.O — §3a), then
   **Pendulum** (after re-pulling clean pen/pen20 per-version data — §3a caveat).
9. Replace any remaining ripped art; only then revisit PyPI publishing.

---

## 8. Existing tuipet modules (inventory to audit against authenticity)

`app.py, pet.py, evolution.py, egg.py, battle*.py, jogress*.py, dna*.py, digicore*.py,
adventure*.py, tournament*.py, shop*.py, training.py, render.py, anim.py, weather.py
(DELETE), theme.py, sound.py (REBUILD), net.py/cloudsync.py/persistence.py (online — keep),
data.py + data/ (REPLACE assets).`

Audit each: authentic to DM20/Pen20? keep / re-skin / cut.
