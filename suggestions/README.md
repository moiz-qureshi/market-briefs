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

## Schema

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

Field rules:

- `suggestion` (object, required) with required string fields:
  `advisor`, `action`, `confidence`, `reasoning`, `catalyst`, `risk`, `generated_at_pt`.
- `action` is the advisor's own call: `buy`, `sell`, `hold`, `trim`, `add`,
  `watch`, `avoid`, or similar.
- `confidence`: `high`, `medium`, `low` (or 0-100).
- `generated_at_pt`: ISO-8601 date-time in America/Los_Angeles
  (e.g. `2026-09-22T07:30:00-07:00`).
- `brief_id` (string, optional): when it matches a brief in `briefs/`, the
  suggestion is linked to that brief on the dashboard. Omit it for a general call.

## Notes

- Files here are write-only inputs — never edit `briefs/` or `feed.json`.
- Invalid files are skipped and logged; the advisor will be asked to fix the shape.
