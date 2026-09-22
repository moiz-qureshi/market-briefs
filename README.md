# Market Briefs — machine feed (for AI consumers)

This directory is the machine-readable feed of Soup's market news briefs.

## How to consume automatically

1. Read `feed.json` — a JSON array, newest first, capped at 60 entries:
   `[{"file": "<filename>", "brief_id": "...", "generated_at_pt": "...", "type": "premarket|post-open"}]`
2. Load any `<filename>` (same directory) for the full brief JSON.
3. Field definitions and rules: `SCHEMA.md` (same directory). Schema v1 is stable.

## Schedule

- Weekdays (Mon–Fri, America/Los_Angeles):
  - Premarket briefs: 4:00am, 5:00am, 6:00am PT
  - Post-open briefs: 7:00am, 8:00am, 9:00am PT
- Each brief covers roughly the preceding 45 minutes plus overnight context.
- Poll `feed.json`; a new entry means a new brief. `brief_id` values are unique.

## Chat fallback

Every brief is also delivered in chat with the identical JSON inside a
```json code fence, for paste-based consumption when files are unreachable.

## Notes

- All figures are sourced; unknown values are `null`. Never treat a `null` as zero.
- Informational purposes only — not financial advice. The feed never contains
  trade recommendations.
