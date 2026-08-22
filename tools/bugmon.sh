#!/usr/bin/env bash
# tuipet bug monitor: stream NEW player bug reports off the lobby server.
# Each new line in bugs.jsonl becomes one notification.
N=56                       # lines already seen at restart (2026-08-18)
FAILS=0
while true; do
  if OUT=$(ssh -o ConnectTimeout=15 -o BatchMode=yes root@68.183.59.19 \
           "tail -n +$((N+1)) /opt/tuipet-lobby/bugs.jsonl" 2>&1); then
    # recovered: say so, otherwise the all-clear after an outage is invisible
    [ "$FAILS" -ge 3 ] && echo "MONITOR OK: lobby reachable again after $FAILS failed polls"
    FAILS=0
    while IFS= read -r line; do
      [ -n "$line" ] && echo "NEW BUG REPORT: $line" && N=$((N+1))
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
