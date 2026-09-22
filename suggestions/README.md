# Suggestions — finance advisor input

This folder receives investment suggestions from Soup's finance advisor as JSON files.
A watcher picks up new/changed files every 30 minutes on weekdays (4:00 AM–5:00 PM PT)
and displays them in the Market Briefs Dashboard under a clearly-attributed
"Suggestions" section. Suggestions are the advisor's own views, shown under the
advisor's name — never as the dashboard's or the brief author's recommendations.

## File naming

Name each file anything descriptive, for example:

- `suggestions/2026-09-22-morning.json`
- `suggestions/2026-09-22-meta-take.json`

Re-push the same filename to update a suggestion.

## Schemas

Two shapes are accepted. Both keep working.

### Single suggestion

```json
{
  "brief_id": "2026-09-22T07-00-pt-post-open",
  "suggestion": {
    "advisor": "Advisor Name",
    "action": "buy",
    "confidence": "high",
    "reasoning": "2-3 sentences on the why.",
    "catalyst": "What could drive this — one line.",
    "risk": "What could invalidate this — one line.",
    "generated_at_pt": "2026-09-22T07:30:00-07:00"
  }
}
```

### Batch of suggestions (ranked list of calls)

One file, as many ranked calls as you want. Each item is displayed as its own
card on the dashboard, all attributed to the same advisor.

```json
{
  "brief_id": "2026-09-22T07-00-pt-post-open",
  "advisor": "Advisor Name",
  "generated_at_pt": "2026-09-22T08:15:00-07:00",
  "suggestions": [
    {
      "action": "buy",
      "symbol": "META",
      "position": "call",
      "strike": 800,
      "expiry": "2026-10-16",
      "confidence": "high",
      "reasoning": "Why this trade — 2-3 sentences.",
      "catalyst": "What could drive it — one line.",
      "risk": "What could invalidate it — one line."
    },
    {
      "action": "sell",
      "symbol": "AAPL",
      "position": "shares",
      "confidence": "medium",
      "reasoning": "Why — 2-3 sentences.",
      "catalyst": "One line.",
      "risk": "One line."
    }
  ]
}
```

Field rules:

- Single shape: `suggestion` (object, required) with required string fields:
  `advisor`, `action`, `confidence`, `reasoning`, `catalyst`, `risk`, `generated_at_pt`.
- Batch shape: top-level `advisor` (non-empty string) and `generated_at_pt`
  (ISO-8601 with timezone offset or Z) are required and apply to every item.
  `suggestions` must be a non-empty array; every item must have `action`,
  `confidence`, `reasoning`, `catalyst`, `risk` (all non-empty strings).
- `action` is the advisor's own call: `buy`, `sell`, `hold`, `trim`, `add`,
  `watch`, `avoid`, or similar.
- `confidence`: `high`, `medium`, `low` (or 0-100).
- `generated_at_pt`: ISO-8601 date-time in America/Los_Angeles
  (e.g. `2026-09-22T07:30:00-07:00`).
- `brief_id` (string, optional): when it matches a brief in `briefs/`, all
  suggestions in the file are linked to that brief on the dashboard. Omit it
  for general calls.
- Per-item extras (both shapes, optional): `symbol`, `position` (e.g. `call`,
  `put`, `shares`), `strike`, `expiry` (`YYYY-MM-DD`). A per-item
  `generated_at_pt` overrides the batch default for that item.

## Notes

- Files here are write-only inputs — never edit `briefs/` or `feed.json`.
- Invalid files are skipped and logged; the advisor will be asked to fix the shape.
