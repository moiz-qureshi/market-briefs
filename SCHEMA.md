# Market Brief JSON Schema (v2)

Every brief is emitted as a single JSON object. Stable schema — fields are never
renamed or removed; new optional fields may be added.

v2 adds (all optional, backward compatible with v1):
- `analysis`: the assistant's own assessment of what the news means — connects
  the dots across headlines, notes what changed vs. prior briefs, flags what's
  noise vs. signal. Informational only; never trade calls.
- `community_signals`: notable discussion threads from community/index sources
  (Hacker News, Reddit, etc.) relevant to the brief's stories.
- `opinion`: reserved for a second AI agent's final take. `null` until supplied.

```json
{
  "brief_id": "2026-09-22T06-00-pt-premarket",
  "generated_at_pt": "2026-09-22T06:00:00-07:00",
  "type": "premarket",
  "market_snapshot": {
    "dow_futures_pct": 0.3,
    "sp500_futures_pct": 0.1,
    "nasdaq100_futures_pct": 0.0,
    "sp500_vs_record_pct": -0.4,
    "vix": 14.69,
    "vix_change": -0.8,
    "treasury_10y_pct": 4.93,
    "treasury_10y_change_bps": 5.0,
    "sp500_advance_decline": "1.8:1",
    "volume_vs_20d_avg_pct": 12.5,
    "breadth_notes": "free-text breadth color, e.g. 7 of 11 sectors green; for premarket briefs these describe the prior regular session",
    "wti_usd": 93.0,
    "wti_day_pct": -3.0,
    "gold_usd": 4360.0,
    "gold_day_pct": -0.5,
    "btc_usd": 86000.0,
    "notes": "free-text color, e.g. Monday recap"
  },
  "headlines": [
    {
      "ticker": "META",
      "headline": "what happened",
      "why_it_matters": "one plain-logic line on price-action relevance",
      "sentiment": "positive",
      "confirmation": "confirmed",
      "source": "https://..."
    }
  ],
  "usac": {
    "headline": "what happened (or null headline when no fresh news)",
    "why_it_matters": "...",
    "sentiment": "neutral",
    "source": "https://..."
  },
  "watch_next": ["item 1", "item 2"],
  "analysis": "free-text assessment: what changed, what matters, what's noise",
  "community_signals": [
    {
      "platform": "hackernews",
      "title": "thread title",
      "url": "https://news.ycombinator.com/item?id=...",
      "takeaway": "what the discussion adds beyond the headlines"
    },
    {
      "platform": "reddit",
      "title": "thread title",
      "url": "https://www.reddit.com/r/.../comments/...",
      "takeaway": "..."
    }
  ],
  "opinion": {
    "agent": "name of the opining agent",
    "action": "the agent's read, e.g. watch / monitor / research / avoid",
    "confidence": "high | medium | low (or 0-100)",
    "reasoning": "2-3 sentences of reasoning",
    "catalyst": "what could drive this — one line",
    "risk": "what could invalidate this — one line",
    "generated_at_pt": "2026-09-22T09:30:00-07:00"
  },
  "disclaimer": "Not financial advice — for informational purposes only."
}
```

## Field rules

- `brief_id`: `{YYYY-MM-DD}T{HH-MM}-pt-{premarket|post-open}`.
- `generated_at_pt`: ISO-8601 with `-07:00` (PDT) or `-08:00` (PST) offset.
- `type`: `"premarket"` for the 4am/5am/6am PT briefs, `"post-open"` for 7am/8am/9am PT.
- Numeric snapshot fields: report ONLY figures a sourced page actually shows; use
  `null` when unknown. Never invent prices or percentages.
- `sentiment`: one of `"positive"`, `"negative"`, `"neutral"`.
- `confirmation`: one of `"confirmed"`, `"single-source"`, `"unconfirmed"`.
  Use `"single-source"`/`"unconfirmed"` when a headline rests on one outlet or
  lacks official confirmation, and say so in `why_it_matters`.
- `sp500_advance_decline`: string ratio like `"1.8:1"` (advancers:decliners).
- `volume_vs_20d_avg_pct`: total volume vs 20-day average, percent.
- `vix_change`: point change vs prior reading. `treasury_10y_change_bps`:
  basis-point change vs the prior brief. For premarket briefs these describe the
  prior regular session — say so in `breadth_notes`.
- `sp500_advance_decline`: string ratio like `"1.8:1"` (advancers:decliners).
- `volume_vs_20d_avg_pct`: total volume vs 20-day average, percent.
- `vix_change`: point change vs prior reading. `treasury_10y_change_bps`:
  basis-point change vs the prior brief. For premarket briefs these describe the
  prior regular session — say so in `breadth_notes`.
- `ticker`: `"SPY"` for broad-market items, `"USAC"` for USA Compression items,
  `"NONE"` for macro items with no single ticker.
- `usac`: an object when there is company news; when there is no fresh USAC news,
  still emit the object with `"headline": null` and carry-forward context in
  `why_it_matters`.
- `community_signals[].platform`: one of `"hackernews"`, `"reddit"`, `"other"`.
  Only include threads that add something the headlines don't. Never invent URLs.
- `opinion`: `null` until a second agent supplies one. Fields: `agent` (string),
  `action` (string: the agent's read, e.g. watch / monitor / research / avoid),
  `confidence` (high|medium|low or 0-100), `reasoning` (2-3 sentences),
  `catalyst` (what could drive this — one line), `risk` (what could invalidate
  this — one line), `generated_at_pt` (ISO-8601 PT). The second agent does NOT
  edit brief files; it writes `opinions/<brief_id>.json` (see repo README) and the
  pipeline merges it into the dashboard.
- `analysis` is assessment, not advice. No trade calls, buy/sell recommendations,
  position sizes, or price targets — ever. This feed is informational only.
