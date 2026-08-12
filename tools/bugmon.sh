#!/usr/bin/env bash
# tuipet bug monitor: stream NEW player bug reports off the lobby server.
# Each new line in bugs.jsonl becomes one notification.
N=55                       # lines already seen at restart (2026-08-12)
while true; do
  OUT=$(ssh -o ConnectTimeout=15 -o BatchMode=yes root@68.183.59.19 \
        "tail -n +$((N+1)) /opt/tuipet-lobby/bugs.jsonl" 2>/dev/null) || true
  if [ -n "$OUT" ]; then
    while IFS= read -r line; do
      [ -n "$line" ] && echo "NEW BUG REPORT: $line"
      N=$((N+1))
    done <<< "$OUT"
  fi
  sleep 60
done
