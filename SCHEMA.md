# Market Brief JSON Schema (v1)

Every brief is emitted as a single JSON object. Stable schema — fields are never
renamed or removed; new optional fields may be added.

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
    "treasury_10y_pct": 4.93,
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
- `ticker`: `"SPY"` for broad-market items, `"USAC"` for USA Compression items,
  `"NONE"` for macro items with no single ticker.
- `usac`: an object when there is company news; when there is no fresh USAC news,
  still emit the object with `"headline": null` and carry-forward context in
  `why_it_matters`.
- No trade calls, buy/sell recommendations, position sizes, or price targets —
  ever. This feed is informational only.
