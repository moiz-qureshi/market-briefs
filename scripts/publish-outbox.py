#!/usr/bin/env python3
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(os.environ.get('MARKET_BRIEFS_OUTBOX_ROOT', Path.home() / 'Documents/Codex/market-briefs-outbox')).expanduser()
OUTBOX = ROOT / 'outbox'
REPO_DIR = ROOT / 'repo-cache' / 'market-briefs'
REPO_URL = os.environ.get('MARKET_BRIEFS_REPO_URL', 'https://github.com/moiz-qureshi/market-briefs.git')
BRANCH = os.environ.get('MARKET_BRIEFS_BRANCH', 'main')
LOG_PREFIX = '[market-briefs-outbox]'

ACTIONS = {'buy', 'sell', 'hold', 'trim', 'add', 'watch', 'avoid'}
OPINION_ACTIONS = {'watch', 'lean-long', 'lean-short', 'avoid'}
CONFIDENCE = {'high', 'medium', 'low'}
POSITIONS = {'call', 'put', 'shares'}
EXPIRY = re.compile(r'^\d{4}-\d{2}-\d{2}$')


def log(message):
    print(f'{LOG_PREFIX} {message}', flush=True)


def run(cmd, cwd=None):
    subprocess.run(cmd, cwd=cwd, check=True)


def sentence_count(text):
    return len([x for x in re.split(r'(?<=[.!?])\s+', text.strip()) if x])


def has_tz(value):
    dt = datetime.fromisoformat(value)
    return dt.tzinfo is not None and dt.utcoffset() is not None


def validate_opinion(path, data):
    errors = []
    if data.get('brief_id') != path.stem:
        errors.append('brief_id must match filename')
    opinion = data.get('opinion')
    if not isinstance(opinion, dict):
        return ['opinion must be an object']
    for key in ('agent', 'action', 'confidence', 'reasoning', 'catalyst', 'risk', 'generated_at_pt'):
        if not isinstance(opinion.get(key), str) or not opinion[key].strip():
            errors.append(f'missing opinion.{key}')
    if opinion.get('action') not in OPINION_ACTIONS:
        errors.append('invalid opinion action')
    if opinion.get('confidence') not in CONFIDENCE:
        errors.append('invalid opinion confidence')
    if isinstance(opinion.get('reasoning'), str) and not 2 <= sentence_count(opinion['reasoning']) <= 3:
        errors.append('opinion reasoning must be 2-3 sentences')
    if '\n' in opinion.get('catalyst', '') or '\n' in opinion.get('risk', ''):
        errors.append('opinion catalyst/risk must be single-line')
    try:
        if not has_tz(opinion.get('generated_at_pt', '')):
            errors.append('opinion generated_at_pt must be timezone-aware')
    except Exception as exc:
        errors.append(f'opinion generated_at_pt invalid: {exc}')
    return errors


def validate_suggestions(path, data):
    errors = []
    if data.get('advisor') != 'Codex-Suggestions':
        errors.append('advisor must be Codex-Suggestions')
    try:
        if not has_tz(data.get('generated_at_pt', '')):
            errors.append('generated_at_pt must be timezone-aware')
    except Exception as exc:
        errors.append(f'generated_at_pt invalid: {exc}')
    suggestions = data.get('suggestions')
    if not isinstance(suggestions, list) or not (1 <= len(suggestions) <= 3):
        errors.append('suggestions must contain 1-3 items')
    for idx, item in enumerate(suggestions or [], 1):
        for key in ('action', 'confidence', 'reasoning', 'catalyst', 'risk'):
            if not isinstance(item.get(key), str) or not item[key].strip():
                errors.append(f'item {idx} missing {key}')
        if item.get('action') not in ACTIONS:
            errors.append(f'item {idx} invalid action')
        if item.get('confidence') not in CONFIDENCE:
            errors.append(f'item {idx} invalid confidence')
        if 'position' in item and item['position'] not in POSITIONS:
            errors.append(f'item {idx} invalid position')
        if 'strike' in item and not isinstance(item['strike'], (int, float)):
            errors.append(f'item {idx} strike must be numeric')
        if 'expiry' in item and not EXPIRY.fullmatch(str(item['expiry'])):
            errors.append(f'item {idx} expiry must be YYYY-MM-DD')
        if isinstance(item.get('reasoning'), str) and not 2 <= sentence_count(item['reasoning']) <= 3:
            errors.append(f'item {idx} reasoning must be 2-3 sentences')
        if '\n' in item.get('catalyst', '') or '\n' in item.get('risk', ''):
            errors.append(f'item {idx} catalyst/risk must be single-line')
    return errors


def collect_files():
    files = []
    validators = {'opinions': validate_opinion, 'suggestions': validate_suggestions}
    for lane, validator in validators.items():
        lane_dir = OUTBOX / lane
        lane_dir.mkdir(parents=True, exist_ok=True)
        for src in sorted(lane_dir.glob('*.json')):
            if src.name.startswith('.') or '/' in src.name:
                raise SystemExit(f'{src}: unsafe filename')
            data = json.loads(src.read_text())
            errors = validator(src, data)
            if errors:
                raise SystemExit(f'{src}: ' + '; '.join(errors))
            files.append((src, lane, data))
    return files


def ensure_repo():
    if not REPO_DIR.exists():
        REPO_DIR.parent.mkdir(parents=True, exist_ok=True)
        log(f'cloning {REPO_URL} into {REPO_DIR}')
        run(['git', 'clone', '--branch', BRANCH, REPO_URL, str(REPO_DIR)])
    run(['git', 'fetch', 'origin', BRANCH], cwd=REPO_DIR)
    run(['git', 'checkout', BRANCH], cwd=REPO_DIR)
    run(['git', 'pull', '--ff-only', 'origin', BRANCH], cwd=REPO_DIR)


def main():
    files = collect_files()
    if not files:
        log('no outbox files')
        return
    ensure_repo()
    staged_paths = []
    for src, lane, _data in files:
        dst = REPO_DIR / lane / src.name
        dst.parent.mkdir(exist_ok=True)
        shutil.copyfile(src, dst)
        staged_paths.append(f'{lane}/{src.name}')
    run(['git', 'add', '--', *staged_paths], cwd=REPO_DIR)
    changed = subprocess.run(['git', 'diff', '--cached', '--name-only'], cwd=REPO_DIR, text=True, capture_output=True, check=True).stdout.splitlines()
    if changed:
        for path in changed:
            if not (path.startswith('opinions/') or path.startswith('suggestions/')):
                raise SystemExit(f'refusing to commit unexpected path: {path}')
        message = 'Publish market briefs outbox'
        if len(changed) == 1:
            only = changed[0]
            if only.startswith('opinions/'):
                message = f'Add opinion for {Path(only).stem}'
            else:
                body = json.loads((REPO_DIR / only).read_text())
                message = f"Add ranked suggestions for {body.get('brief_id') or 'batch'}"
        run(['git', 'commit', '-m', message], cwd=REPO_DIR)
        run(['git', 'push', 'origin', BRANCH], cwd=REPO_DIR)
    else:
        log('already published')
    stamp = datetime.now().strftime('%Y%m%d-%H%M%S')
    for src, lane, _data in files:
        sent = OUTBOX / 'sent' / lane / stamp
        sent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src), str(sent / src.name))
        log(f'archived {src.name}')


if __name__ == '__main__':
    main()
