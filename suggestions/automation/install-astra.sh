#!/bin/bash
set -euo pipefail
export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:$PATH"
DEST="$HOME/market-briefs-astra"
mkdir -p "$DEST/logs"
for tool in gh git python3 npm; do
  if ! command -v "$tool" >/dev/null; then
    echo "Missing $tool. Install prerequisites with: brew install gh git python node"
    exit 1
  fi
done
python3 -c 'from zoneinfo import ZoneInfo; ZoneInfo("America/Los_Angeles")'
echo "Installing the Codex CLI locally..."
npm install --prefix "$DEST/runtime" @openai/codex
export PATH="$DEST/runtime/node_modules/.bin:$PATH"
gh auth status >/dev/null 2>&1 || gh auth login --hostname github.com --web --git-protocol https
codex login status >/dev/null 2>&1 || codex login
curl -fSL "https://raw.githubusercontent.com/moiz-qureshi/market-briefs/a8172ec910c0735d0b585463a0ddf459de049384/suggestions/automation/astra-run.py" -o "$DEST/astra-run.py.download"
python3 - "$DEST/astra-run.py.download" <<'PY'
import ast, pathlib, sys
ast.parse(pathlib.Path(sys.argv[1]).read_text())
PY
mv "$DEST/astra-run.py.download" "$DEST/astra-run.py"
python3 - "$DEST" "$(command -v python3)" "$PATH" <<'PY'
import pathlib, shlex, sys
root, python, path = sys.argv[1:]
runner = pathlib.Path(root) / "run.sh"
runner.write_text("#!/bin/bash\nset -euo pipefail\nexport PATH=" + shlex.quote(path) +
                  "\nexec /usr/bin/caffeinate -i " + shlex.quote(python) + " " +
                  shlex.quote(root + "/astra-run.py") + ' "$@"\n')
runner.chmod(0o700)
PY
echo "Testing a real GPT-6 Astra analysis and publication before scheduling..."
"$DEST/run.sh"
python3 - "$DEST" <<'PY'
import pathlib, shlex, subprocess, sys
root = pathlib.Path(sys.argv[1])
old = subprocess.run(["crontab", "-l"], text=True, capture_output=True)
if old.returncode and "no crontab" not in old.stderr.lower():
    raise SystemExit("Cannot read crontab: " + old.stderr)
(root / "crontab.before-install.txt").write_text(old.stdout)
lines, skip = [], False
for line in old.stdout.splitlines():
    if line in ("# BEGIN market-briefs-suggestions-publisher", "# BEGIN market-briefs-astra"):
        skip = True
    elif line in ("# END market-briefs-suggestions-publisher", "# END market-briefs-astra"):
        skip = False
    elif not skip:
        lines.append(line)
if skip:
    raise SystemExit("Incomplete cron marker; existing crontab preserved")
# macOS cron uses system time; the runner gates the six actual Pacific windows.
cmd = "/bin/bash " + shlex.quote(str(root / "run.sh")) + " --scheduled >> " + shlex.quote(str(root / "logs/cron.log")) + " 2>&1"
if "%" in cmd or "\n" in cmd:
    raise SystemExit("Unsupported character in cron path")
lines += ["# BEGIN market-briefs-astra", "15 * * * * " + cmd, "# END market-briefs-astra"]
subprocess.run(["crontab", "-"], input="\n".join(lines) + "\n", text=True, check=True)
if "15 * * * * " + cmd not in subprocess.check_output(["crontab", "-l"], text=True):
    raise SystemExit("Cron verification failed")
PY
echo "Disabling the old rule-based GitHub writer..."
gh workflow disable publish-ranked-suggestions.yml --repo moiz-qureshi/market-briefs
echo "INSTALLED: GPT-6 Astra at 5:15, 6:15, 7:15, 8:15, 9:15 and 10:15 AM Pacific, Monday-Friday."
echo "Manual run: bash \"$DEST/run.sh\""
echo "Cron log: $DEST/logs/cron.log"
echo "Keep this Mac awake and online. Closed-lid sleep or power-off prevents cron from running."
