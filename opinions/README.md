# Opinions — finance advisor per-brief analysis

This folder receives one analysis file per market brief from Soup's finance advisor.
A watcher picks up new/changed files every 30 minutes on weekdays (4:00 AM–5:00 PM PT)
and attaches each opinion to its brief in the Market Briefs Dashboard, clearly attributed
to the advisor — never as the dashboard's or the brief author's recommendations.

## Two lanes — don't confuse them

- `opinions/` (this folder): ONE file per brief — your overall take on that brief
  (action, confidence, reasoning, catalyst, risk).
- `suggestions/`: your RANKED TRADE IDEAS — as many as you want, batched in one file
  or split across files, pushed any time. See `suggestions/README.md`.

You are never limited to one file total. Push an opinion for every brief AND a
suggestions batch whenever you have ranked calls. The two lanes are independent.

## File naming

`opinions/<brief_id>.json`, for example:

- `opinions/2026-09-23T09-00-pt-post-open.json`

Re-push the same filename to update an opinion.

## Schema

```json
{
  "brief_id": "2026-09-23T09-00-pt-post-open",
  "opinion": {
    "agent": "Advisor Name",
    "action": "bullish",
    "confidence": "high",
    "reasoning": "2-3 sentences on the why.",
    "catalyst": "What could drive this — one line.",
    "risk": "What could invalidate this — one line.",
    "generated_at_pt": "2026-09-23T09:15:00-07:00"
  }
}
```

Field rules:

- Top-level `brief_id` (string, required) should match a brief file in `briefs/`
  — see `feed.json` for the current list. The opinion is displayed on that brief.
- `opinion` (object, required) with required string fields: `agent`, `action`,
  `confidence`, `reasoning`, `catalyst`, `risk`, `generated_at_pt`.
- `action` is the advisor's own take: `bullish`, `bearish`, `watch`, `trim`,
  `buy`, `sell`, `hold`, or similar.
- `confidence`: `high`, `medium`, `low` (or 0-100).
- `generated_at_pt`: ISO-8601 date-time in America/Los_Angeles
  (e.g. `2026-09-23T09:15:00-07:00`).

## Notes

- Files here are write-only inputs — never edit `briefs/` or `feed.json`.
- Invalid files are skipped and logged; the advisor will be asked to fix the shape.
- Ranked trade ideas do NOT go here — they go in `suggestions/`.
