#!/usr/bin/env bash
set -euo pipefail

ROOT="${MARKET_BRIEFS_OUTBOX_ROOT:-$HOME/Documents/Codex/market-briefs-outbox}"
RAW_BASE="${MARKET_BRIEFS_RAW_BASE:-https://raw.githubusercontent.com/moiz-qureshi/market-briefs/main/scripts}"
MARKER="market-briefs-outbox-publisher"
LABEL="com.moiz.market-briefs-outbox"
PLIST="$HOME/Library/LaunchAgents/$LABEL.plist"

mkdir -p "$ROOT/bin" "$ROOT/logs" "$ROOT/repo-cache" \
  "$ROOT/outbox/opinions" "$ROOT/outbox/suggestions" \
  "$ROOT/outbox/sent/opinions" "$ROOT/outbox/sent/suggestions" \
  "$HOME/Library/LaunchAgents"

curl -fsSL "$RAW_BASE/publish-outbox.py" -o "$ROOT/bin/publish-outbox.py"
chmod 0755 "$ROOT/bin/publish-outbox.py"

cat > "$ROOT/bin/run-publisher-weekdays.sh" <<RUNNER
#!/usr/bin/env bash
set -euo pipefail
# macOS date: 1=Monday ... 5=Friday. Stay quiet on weekends.
day="\$(date +%u)"
[ "\$day" -ge 1 ] && [ "\$day" -le 5 ] || exit 0
"$ROOT/bin/publish-outbox.py" >> "$ROOT/logs/publisher.log" 2>&1
RUNNER
chmod 0755 "$ROOT/bin/run-publisher-weekdays.sh"

cron_line="*/10 * * * 1-5 $ROOT/bin/run-publisher-weekdays.sh # $MARKER"
tmp="$(mktemp)"
if (crontab -l 2>/dev/null | grep -v "$MARKER" > "$tmp" || true) && \
   printf '%s\n' "$cron_line" >> "$tmp" && \
   crontab "$tmp" 2>/tmp/market-briefs-crontab.err; then
  rm -f "$tmp" /tmp/market-briefs-crontab.err
  scheduler="cron"
  scheduler_detail="$cron_line"
else
  rm -f "$tmp"
  cat > "$PLIST" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>$LABEL</string>
  <key>ProgramArguments</key>
  <array>
    <string>/bin/bash</string>
    <string>$ROOT/bin/run-publisher-weekdays.sh</string>
  </array>
  <key>StartInterval</key>
  <integer>600</integer>
  <key>StandardOutPath</key>
  <string>$ROOT/logs/launchd.out.log</string>
  <key>StandardErrorPath</key>
  <string>$ROOT/logs/launchd.err.log</string>
</dict>
</plist>
PLIST
  launchctl unload "$PLIST" >/dev/null 2>&1 || true
  launchctl load "$PLIST"
  scheduler="launchd"
  scheduler_detail="$PLIST"
fi

printf 'Installed stable outbox: %s/outbox\n' "$ROOT"
printf 'Installed publisher: %s/bin/publish-outbox.py\n' "$ROOT"
printf 'Installed runner: %s/bin/run-publisher-weekdays.sh\n' "$ROOT"
printf 'Installed scheduler: %s (%s)\n' "$scheduler" "$scheduler_detail"
printf 'Logs: %s/logs/publisher.log\n' "$ROOT"
