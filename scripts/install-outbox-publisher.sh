#!/usr/bin/env bash
set -euo pipefail

ROOT="${MARKET_BRIEFS_OUTBOX_ROOT:-$HOME/Documents/Codex/market-briefs-outbox}"
RAW_BASE="${MARKET_BRIEFS_RAW_BASE:-https://raw.githubusercontent.com/moiz-qureshi/market-briefs/main/scripts}"
MARKER="market-briefs-outbox-publisher"

mkdir -p "$ROOT/bin" "$ROOT/logs" "$ROOT/repo-cache" \
  "$ROOT/outbox/opinions" "$ROOT/outbox/suggestions" \
  "$ROOT/outbox/sent/opinions" "$ROOT/outbox/sent/suggestions"

curl -fsSL "$RAW_BASE/publish-outbox.py" -o "$ROOT/bin/publish-outbox.py"
chmod 0755 "$ROOT/bin/publish-outbox.py"

cron_line="*/10 * * * 1-5 $ROOT/bin/publish-outbox.py >> $ROOT/logs/publisher.log 2>&1 # $MARKER"
tmp="$(mktemp)"
crontab -l 2>/dev/null | grep -v "$MARKER" > "$tmp" || true
printf '%s\n' "$cron_line" >> "$tmp"
crontab "$tmp"
rm -f "$tmp"

printf 'Installed stable outbox: %s/outbox\n' "$ROOT"
printf 'Installed publisher: %s/bin/publish-outbox.py\n' "$ROOT"
printf 'Installed cron: %s\n' "$cron_line"
printf 'Logs: %s/logs/publisher.log\n' "$ROOT"
