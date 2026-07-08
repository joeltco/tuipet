# GHOST CUP + LEADERBOARD — implementation plan

**⛔ PARKED 2026-07-07 (Joel: "park it for now").** Verdict from the audit
discussion: the standalone mode is redundant with the existing cup system
(an always-open home-cup clone + a bits faucet). If this revives, prefer the
SLIM version: seed 1–3 real-save ghost cards into the EXISTING hourly cup
brackets (scarcity stays, no ghost trophy, no economy patch) + ship the
standings page as specced. Do not start either without Joel's go-ahead.

*Drafted 2026-07-07 (v0.2.358 baseline). Joel's decisions: one ladder fed by
Ghost Cup + live PvP; weekly seasons; everything lives in the CUP page (`u`),
not the lobby. No code has been written — this is the whole plan.*

*Audited 2026-07-07 against v0.2.363: every reuse claim re-verified in code;
the ghost-trophy hygiene items, the trophy_label ghost branch, the SyncClient
queue correction, the fired-once result hook, and the PvP forfeit/draw rules
below came out of that audit. Prod server md5 parity was verified at draft
time but could not be re-checked during the audit (no prod read auth) —
re-verify as step zero of the server deploy.*

## The idea

An online tournament that works with **zero concurrent players**. The server
already stores every account's full pet save (23 on prod today) — so a bracket
can be seeded with *real players' pets at their real trained strength*, fought
locally against the battle AI, exactly like the offline cup fights its rolled
entrants. Your pet appears in other people's brackets the same way. Results
post to a weekly server-side ladder; live lobby PvP wins feed the same ladder.
The long-deferred leaderboard ships as part of this.

Why ghosts and not live brackets: prod has ~12 accounts with 1–2 online at
once. A live bracket almost never fires; a ghost bracket is always open.

## What already exists (verified in code, 2026-07-07)

| Piece | Where | Reuse |
|---|---|---|
| Full saves per account | `server/server.py` `SAVES` (saves.json, 23 entries) | ghost cards extracted from these |
| Bracket engine | `tournament.Tournament` (8 slots, 7 entrants + YOU, `current_opponent()/record()/over/champion`) | gains an `entrants=` seed |
| Entrant dict shape | `_mk_entrant`: `{num,name,stage,attribute,hp,bits,vaccine,data_power,virus}` | ghost cards map 1:1 |
| Card math | `battle.battle_card` (hp=full_health stand-in, raw powers — documented deltas) | same fields server-side |
| Always-on connection | `net.SyncClient` (the sync ghost, app-lifetime, account-authed) | carries bracket/result/board messages — **but its send loop is save-only; a real outgoing queue is NEW work (see net.py below)** |
| Cup UI | `tournamentscreen.TournamentPanel` (select → bracket → fight → tree) | gains two entries + one page |
| Local server test fixture | `tests/test_lobby.py::_spawn` (spawns `server/server.py` on a free port) | integration tests for the new messages |
| Server dispatch | `server.py handler()` — `elif t == "...":` chain at line ~330 (audit: drifted from ~257, still clean) | four new message types slot in — do NOT copy the `if not client.live: continue` guard from invite/relay; sync ghosts must pass |

Local `server/server.py` is byte-identical to prod (md5 verified).

## Server changes (`server/server.py`)

New file `standings.json` (env `TUIPET_STANDINGS`), shape:

```json
{ "season": "2026-W28",
  "table": { "joel": {"pts": 12, "titles": 1, "rounds": 4, "pvp_w": 2, "pvp_l": 0} },
  "hall": [ {"season": "2026-W27", "champion": "mp", "pts": 21} ] }
```

- `_season()` → ISO year-week (`time.strftime("%G-W%V")`).
- `_roll_season()` — lazy, on any standings access: stored season ≠ current →
  archive the top scorer into `hall` (cap ~12 entries), reset `table`, stamp
  the new season. No cron needed. **Empty-table guard**: a season nobody
  scored archives NO hall entry (don't write a null champion row).
- Four new message types (all require a logged-in connection; `sync_only`
  connections allowed — that's the carrier):
  - `{"t":"cup_bracket"}` → `{"t":"cup_bracket","cards":[...]}` — up to 7
    cards drawn from `SAVES` **excluding the requester's own account**,
    shuffled. Card = whitelisted fields only (never the whole save):
    `{owner, num, name, stage, attribute, hp, vaccine, data_power, virus}`
    where `hp` = save's `full_health` (client defaults it if absent). Skip
    saves that are eggs/dead (`stage=="Egg"`, `num<0`, `dead`).
  - `{"t":"cup_result","rounds":0-3,"champion":bool}` → scores the season
    table: `pts += rounds*1 + champion*5`, `rounds += rounds`,
    `titles += champion`. Clamp rounds to 0..3; one result per message,
    no rate limiting in V1 (friends-server trust model — same as save sync).
  - `{"t":"pvp_result","won":bool}` → `pts += 3 if won`, `pvp_w/l += 1`.
    Each client reports its OWN outcome (host and guest both send one).
    Trust model: client-reported, like everything else on this server —
    the ff3mmo arbiter doctrine deliberately does NOT port here.
  - `{"t":"board"}` → `{"t":"board","season","ends","table":[sorted rows],
    "hall":[last 3]}` — `ends` = seconds until the ISO week rolls (client
    renders a countdown).
- Atomic write like saves.json (`.tmp` + `os.replace`), throttled (write on
  score, not on read).
- **Wire-compat**: old clients never send these types; old servers reply
  nothing — the client times out gracefully ("Can't reach the cup server").

## Client changes

### `net.py` — SyncClient grows the cup channel
- **Audit correction**: `SyncClient._send_loop` is save-ONLY — a `_pending`
  slot plus a wake event, deliberately single-slot (newest save wins). The
  cup channel needs a real outgoing queue ADDED alongside it (an
  `asyncio.Queue` like LobbyClient's, drained in the same `_send_loop`
  select), plus `self.cup_cards = self.board = None` in `__init__`. This is
  new plumbing, not reuse.
- Sends: `cup_bracket()`, `cup_result(rounds, champion)`, `board()` — via
  that new queue.
- `_handle` additions: `t=="cup_bracket"` → `self.cup_cards = m["cards"]`;
  `t=="board"` → `self.board = m`. Panel polls these (the state-snapshot
  idiom every panel already uses). Reset to `None` before each request.
- `LobbyClient` gains `pvp_result(won)` (one-line send) — live PvP reports
  over the lobby connection it already has.

### `tournament.py`
- `Tournament(pet, trophy, entrants=None)` — when `entrants` is given, skip
  the pool roll and use them (pad to 7 with `_mk_entrant` rolls if the server
  sent fewer — a mixed real/AI field is the small-population fallback).
  **Padding rolls from `_eligible_forms(pet, trophy)`** — so the donor cup
  must be an OPEN cup (no field/attr/stage walls) or padding inherits its
  restrictions.
- `ghost_trophy()` — a synthetic trophy dict: copy a mid **open** real cup's
  purse fields, override `id=9001, ghost=True`, AND (audit hygiene — each of
  these leaks a real side effect if left at the donor's values):
  - `same_day_retry=True` — else `_finish` appends 9001 to the persisted
    `pet.fought_today`
  - `item=-1, food_id=-1, food_amt=0` — else a donor cup with a prize makes
    the ghost cup an infinitely farmable item fountain
- `trophy_label()` gains a ghost branch (`t.get("ghost") → "GHOST CUP"`) —
  `Tournament.__init__` names the bracket via `trophy_label`, which ignores
  any `name` key; without the branch the UI reads "Classic Open #9002".
- `ghost_entrants(cards)` — server cards → entrant dicts (`bits=(0,0)`,
  carry `owner` through for display; Battle ignores unknown keys).
- `record()` guard: `trophy.get("ghost")` skips the `trophies_won` write
  (the trophy room keys on tournament.csv ids — an unknown id must not land
  there) **and skips `persistence.tourney_add`** (it feeds the egg-unlock
  gates and the digicore career count — same pollution doctrine; audit:
  tournament.py:358, egg.py:109, digicorescreen.py:200). `pet.trophies`
  (the count) still increments; bits purse still pays via the copied fields.
  Battle stats record normally (cup parity).

### `tournamentscreen.py`
- Select page: two new footer keys — **`g` GHOST CUP** and **`l` STANDINGS**
  (the hour-slot list stays untouched; strip/footer budget re-measured, the
  38-col static-chrome lesson from v0.2.357 applies).
- `g`: `tournament.eligibility`-style gates (asleep/young — reuse
  `can_enter`), then `sync.cup_bracket()` → new phase `ghost_wait`
  ("reaching the cup server…", ESC cancels). `anim()` polls
  `sync.cup_cards`; on arrival → `Tournament(pet, ghost_trophy(),
  entrants=ghost_entrants(cards))` → the EXISTING bracket/fight/tree flow,
  unchanged. Timeout ~6s → "Can't reach the cup server." No sync (offline /
  no account) → same message, immediately.
- On `tourney.over` for a ghost cup: `sync.cup_result(t.round, t.champion)`
  (fire-and-forget; a dropped result is one lost score, not a wedge).
  **Fired-once flag required**: `over` gets set from TWO sites in
  `TournamentPanel.key` (the battle-done `record()` and the ESC-forfeit
  `record(False)`) — guard with a `_reported` flag on the tourney. An ESC
  walk-out still reports: `t.round` at that point = rounds actually won,
  which is exactly the +1/round scoring.
- `l`: phase `board` — request `sync.board()`, poll, render: season + days
  left, top rows (rank · name · pts · W-L), your row highlighted, reigning
  hall champion. 12×40 budget; long names field-marquee (the .349 doctrine);
  ESC back to select.
- Bracket page displays a ghost entrant as `owner's petname` where `owner`
  exists (field-clipped/marqueed).

### `lobbyscreen.py`
- At bout end (`_apply_result` → `over` branch, and the forfeit path):
  `self.client.pvp_result(won)` — forfeits report `won=False`.
- **The abort-RECEIVER reports `won=True`** (audit: without this, a player
  about to lose can always deny the winner their +3 by ESC-quitting — the
  bout voided and nobody scored; every close bout would end in a rage-quit).
  A voided bout from a genuine disconnect still reports nothing on the
  dropped side — only the survivor scores.
- A **draw** (double-KO) reports `won=False` from BOTH sides — both book a
  pvp_l, neither gets points. Intentional, not a bug.

### `app.py`
- `action_tournament` passes the sync handle:
  `TournamentPanel(self.pet, sync=self._sync)`.

## Scoring (V1, tune later)

| Event | Points |
|---|---|
| Ghost-cup round won | +1 (max 3/cup) |
| Ghost-cup title | +5 |
| Live PvP win | +3 |

Weekly ISO seasons; champion archived to the hall on rollover.

## Tests

- **Unit**: `Tournament(entrants=)` seeds exactly (no dex roll);
  `ghost_entrants` field mapping; ghost `record()` skips `trophies_won` AND
  `persistence.tourney_add` but pays/eliminates normally; a ghost champion
  leaves `fought_today` untouched and grants no item/food;
  `trophy_label(ghost_trophy())` == "GHOST CUP"; the result hook fires
  exactly once (battle-done and ESC-forfeit paths both); padding when the
  server sends <7.
- **Server integration** (the `_spawn` fixture): login → `cup_bracket`
  excludes self + is egg/dead-free; `cup_result`+`pvp_result` → `board`
  totals match; season rollover (pre-write standings.json with a stale
  season, assert archive + reset on next access).
- **Screen**: `ghost_wait` → bracket with a stubbed sync; board page renders
  in budget with 24-char names (rolled marquee pin); offline path shows the
  error and stays usable.
- **Panel smoke**: the board page joins the sweep (hard rule).

## Smoke + deploy sequence

1. Suite + goldens (both should stay byte-identical — no pet-model changes).
2. Headless smoke: local `_spawn` server → real app → `u` → `g` → fight at
   least one ghost round → result lands in standings.json → `l` shows it.
3. **Server deploy needs Joel's explicit approval naming the target**
   (scp → `/opt/tuipet-lobby/server.py`, `pm2 restart tuipet-lobby`, id 2 —
   never touch pm2 id 0). Step zero: re-verify local/prod `server.py` md5
   parity (last verified 2026-07-07; the .363 audit couldn't re-check).
   Deploy server FIRST (new types are additive;
   old clients unaffected), verify clean boot + account count, THEN
   `./deploy.sh patch -y` for the client.
4. Live smoke vs wss://ff3mmo.com/tuipet/ with a throwaway account: bracket
   arrives with real prod pets, a result scores, the board renders.

## Open questions (defaults chosen, flag if wrong)

- Ghost cup entry fee/purse: V1 pays the copied cup purse in bits and costs
  nothing to enter. Could add an entry fee later.
- Re-entry: unlimited ghost cups per day in V1. Honest framing (audit): the
  weekly reset is NOT a cap — at ~8 pts per three fights, the grindiest
  player wins every week; the ladder measures playtime as much as strength.
  A daily entry cap is the knob if that gets silly.
- Trust model (audit, restated plainly): any logged-in client can script
  `{"t":"cup_result","rounds":3,"champion":true}` in a loop. The ladder is
  honor-system, full stop — accepted for a 23-account friends server.
- The board shows account names (the lobby already does); no opt-out in V1.
- Ghost difficulty: cards are used raw (real trained pets). A fresh Rookie
  will get flattened by someone's Mega — that's the ladder being honest.
  Could tier brackets by stage later if it feels bad.
