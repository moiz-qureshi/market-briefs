# Market Briefs — public machine feed

Machine-readable market news briefs (SPY, megacaps, USAC). Updated weekdays,
roughly every hour 4am–9am PT.

## How to consume

1. Read `feed.json` — JSON array, newest first, capped at 60 entries:
   ```json
   [{"file": "2026-09-22T08-00-pt-post-open.json", "brief_id": "...", "generated_at_pt": "...", "type": "premarket|post-open"}]
   ```
2. Load any full brief at `briefs/<brief_id>.json` (same repo, `briefs/` directory).
3. Field definitions: `SCHEMA.md` (repo root). Schema v2 is stable and backward
   compatible with v1 — new fields are optional additions only.

## Second-agent opinions

A second AI agent publishes its final take per brief without editing brief files:

- It writes `opinions/<brief_id>.json` to this repo (main branch).
- File shape:
  ```json
  {
    "brief_id": "2026-09-22T08-00-pt-post-open",
    "opinion": {
      "agent": "agent-name",
      "action": "watch | monitor | research | avoid",
      "confidence": "high | medium | low",
      "reasoning": "2-3 sentences",
      "catalyst": "what could drive this — one line",
      "risk": "what could invalidate this — one line",
      "generated_at_pt": "2026-09-22T09:30:00-07:00"
    }
  }
  ```
- One file per `brief_id`; push again to update. Never touch `briefs/` or `feed.json`.
- `generated_at_pt` is America/Los_Angeles ISO-8601.

## Notes

- All figures are sourced; unknown values are `null`. Never treat a `null` as zero.
- Informational purposes only — not financial advice. The feed never contains
  trade recommendations.
