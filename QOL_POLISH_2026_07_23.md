# QOL POLISH — 2026-07-23

Joel: "lets do some heavy QOL polishing."  Four-family friction audit
(main view + care, menus + shops, battle family, town + online).
QOL = friction removal ONLY: no new systems, no removals, no art.
Every fix ships pre-clipped (card 26x16), strip owns the keys,
scene-screen law holds.

Order of attack: highest player impact first, batched by file locality,
one release per batch.

## Batch 1 — the skip cluster + the pill reflex

- [x] B1 Whole-fight fast-forward: the bout is precomputed, but skip is
      per-round (~20 timed SPACE taps through a decided fight).  ESC
      during the round anim jumps straight to the result.
      (battlescreen.py skip branch)
- [x] B2 Skip debounce re-arms every round (`self.i >= SKIP_DEBOUNCE`
      with `i` reset each round) — the first 0.6s of EVERY round eats
      skip presses.  Gate on total elapsed frames instead.
- [x] B3 Skip hint never reaches the strip during the round anim (card
      whispers it only).  Strip gets a dim `SPACE hurry`.
- [x] C1 Feed menu opens on Meat even when the pet is sick and the HUD
      says "F — feed it the pill".  Sick pet → cursor opens on Pill.
      (feedscreen.py)
- [x] B4 Adventure "Refuses to walk!" never says WHY (energy) and
      invites a dead SPACE-mash.  Say the reason + the real outs.
      (adventurescreen.py refuse strip)

## Batch 2 — menus & shops

- [ ] M1 Album + Egg Guide lists are the ONLY cursor lists that don't
      wrap top↔bottom (their own detail views DO wrap ←→).  Wrap them.
- [ ] M2 Bag: using/selling the last of a stack shifts the list under
      the cursor → next press hits a NEIGHBOR item.  Anchor the cursor.
- [ ] M3 Shop shelf shows affordability only on the selected row — dim
      the price on rows you can't afford, whole shelf at a glance.
- [ ] M4 Shop tabs reset cursor to 0 on every tab/bag switch — per-tab
      cursor memory for the panel's lifetime.
- [ ] M5 Sound/Options/Themes render a static footer that CONTRADICTS
      the live strip ("↑↓ pick ENTER go" vs "←→ volume").  The strip
      owns the keys — drop the stale footers.
- [ ] M6 Album/Egg-Guide DETAIL views step one entry per ←→ with no
      PgUp/PgDn, while the lists they came from page fine.  Route page
      keys in detail too.
- [ ] M7 Shop always reopens Food/row 0 — remember last (tab, cursor)
      per session and reopen there.
- [ ] M8 (low) At the exact end rows, ↑↓ wraps but PgUp/PgDn clamps —
      two idioms disagree at the same spot.  Page keys wrap when
      already at the end.

## Batch 3 — main view & care

- [ ] C2 Care keys swallowed silently during care fx — no blip, no
      note; players mash.  Acknowledge the key (soft blip / "one
      moment…" flash).
- [ ] C3 Satiety (12h) / auto-clean (24h) buffs invisible at home —
      compact deco badges (`sated 3h` / `tidy 8h`) via care_deco.
- [ ] C4 Hired assistant (bills per visit!) invisible at home — add a
      `helper` deco badge when auto_care is on.
- [ ] C5 LCD border subtitle "● on" is set ONCE and lies after lights
      out — reflect pet.lights ("● on"/"● off").
- [ ] C6 Space is dead for accepting a gift; only Enter works, while
      panels accept both.  Bind Space to gift too.
- [ ] C7 Bare grave card says "press N for a new egg" but N re-opens
      the full memorial, not the carousel.  Make N deliver what it
      promises.
- [ ] C8 Exhausted "S — rest" prompt answers with a flat "Lights off."
      and the pet keeps standing until the doze timer — flash a
      "settling down to rest…" variant so the action reads as working.
- [ ] C9 Feed card doesn't mark Meat as refusable (full belly / filth
      on the floor) — annotate the row ("— full" / "— clean first")
      before the player commits.

## Batch 4 — town & online

- [ ] O1 Lobby/raid websocket connect has NO open_timeout — a dead
      host freezes "Connecting…" ~10s.  (submit_bug already caps at
      its timeout; cloudsync at 3s.)  Cap it at ~5s.  (net.py:51)
- [ ] O2 FIRST-ever failed connect mislabeled "Connection lost —
      reconnecting…" — branch on _had_welcome: never-connected reads
      "Can't reach the lobby — retrying…".
- [ ] O3 Chat sent while the socket is down vanishes from the input
      with no feedback (it IS queued) — status line: "Offline —
      message queued, will send on reconnect."  (lobby + DM twin)
- [ ] O4 No key to hurry the 30s reconnect backoff — Enter/R while
      reconnecting resets the backoff and retries now.
- [ ] O5 "Connecting…" is static text — animate trailing dots so the
      wait shows liveness.
- [ ] O6 Ladder page "fetching the rankings…" forever if the reply
      never lands — after a few seconds: "couldn't reach the ladder —
      TAB retry / ESC back".
- [ ] O7 Login-rejection note hard-clipped at 38 cols loses the
      actionable tail — marquee it like every other over-wide line.
- [ ] O8 (low) First-launch password field: no way to verify what you
      typed before it becomes your permanent sync password — minimal
      reveal (hold-to-peek or length cue).
- [ ] O9 Startup cloud pull blocks launch ~3s silently when offline —
      print "checking cloud save…" before the blocking pull
      (matches _preflight's pre-UI print style).
- [ ] O10 (low) Town hub re-enters with cursor forced to row 0 every
      stop on a multi-town run — keep the last choice for the session.

## Ruled out during the audit (do NOT do)

- towneggscreen.py is dead/unrouted — leave it alone (removals need
  named orders).
- Boss-death / teleport / parade / ceremony shows stay non-skippable —
  deliberate under own-game law.
- The dodge mechanic was just redesigned (one press per ambush) — not
  touched.
- No optimistic local echo in chat (double-echo risk) — status-line
  feedback only.
