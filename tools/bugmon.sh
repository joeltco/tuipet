#!/usr/bin/env bash
# tuipet bug monitor: stream NEW player bug reports off the lobby server.
# Each new line in bugs.jsonl becomes one notification.
# Baseline from the LIVE file, not a hardcoded count: a stale N re-fires every
# report above it (the 2026-10-01 "x" flood would replay 46 lines on every arm).
STATE="${TUIPET_BUGMON_STATE:-$HOME/.tuipet-bugmon-seen}"
LIVE=$(ssh -o ConnectTimeout=15 -o BatchMode=yes root@68.183.59.19 \
         "wc -l < /opt/tuipet-lobby/bugs.jsonl" 2>/dev/null | tr -d ' ')
if [ -z "$LIVE" ]; then
  echo "MONITOR BLIND: cannot reach the lobby to baseline bugs.jsonl — not arming"
  exit 1
fi
# Resume from the last count we actually reported, so reports filed while the
# monitor was down are delivered on the next arm instead of being swallowed --
# the watch is capped at 30m, so that gap recurs for as long as it runs.
# A stored count ABOVE the live one means the file shrank (a cleanup, or a
# rotation); trust the file in that case, there is nothing above it to replay.
N=$(cat "$STATE" 2>/dev/null | tr -cd '0-9')
if [ -z "$N" ] || [ "$N" -gt "$LIVE" ]; then
  N=$LIVE
  echo "MONITOR ARMED: baselined at $N reports in bugs.jsonl"
elif [ "$N" -lt "$LIVE" ]; then
  echo "MONITOR ARMED: resuming at $N of $LIVE reports — $((LIVE-N)) filed while it was down"
else
  echo "MONITOR ARMED: resuming at $N reports in bugs.jsonl"
fi
echo "$N" > "$STATE" 2>/dev/null
FAILS=0
while true; do
  if OUT=$(ssh -o ConnectTimeout=15 -o BatchMode=yes root@68.183.59.19 \
           "tail -n +$((N+1)) /opt/tuipet-lobby/bugs.jsonl" 2>&1); then
    # recovered: say so, otherwise the all-clear after an outage is invisible
    [ "$FAILS" -ge 3 ] && echo "MONITOR OK: lobby reachable again after $FAILS failed polls"
    FAILS=0
    while IFS= read -r line; do
      [ -n "$line" ] && echo "NEW BUG REPORT: $line" && N=$((N+1)) \
        && echo "$N" > "$STATE" 2>/dev/null
    done <<< "$OUT"
  else
    # The old script swallowed this with 2>/dev/null || true, so a dead box, a
    # rotated key or a moved bugs.jsonl all looked exactly like "no new bugs" --
    # silence read as an all-clear while nothing was being watched at all.
    # Announce ONCE per outage (every 30th poll after) so it can't spam.
    FAILS=$((FAILS+1))
    if [ "$FAILS" = 3 ] || [ $((FAILS % 30)) = 0 ]; then
      echo "MONITOR BLIND: lobby unreachable for $FAILS polls — $(echo "$OUT" | tail -1)"
    fi
  fi
  sleep 60
done
