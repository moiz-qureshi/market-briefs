#!/usr/bin/env python3
"""Generate a ranked suggestions batch from the newest synthetic market brief.

This intentionally uses only repository data and deterministic heuristics so it can
run inside GitHub Actions without any local laptop permissions or external API keys.
"""
from __future__ import annotations

import argparse
import json
import re
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

PT = ZoneInfo("America/Los_Angeles")
ACTIONS = {"buy", "sell", "hold", "trim", "add", "watch", "avoid"}
CONFIDENCE = {"high", "medium", "low"}
POSITIONS = {"call", "put", "shares"}


def parse_dt(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def newest_feed_item(feed: list[dict]) -> dict:
    stamped = []
    for index, item in enumerate(feed):
        stamp = item.get("generated_at_pt") or item.get("published_at")
        if stamp:
            stamped.append((parse_dt(stamp), -index, item))
    if stamped:
        return max(stamped, key=lambda x: (x[0], x[1]))[2]
    if not feed:
        raise SystemExit("feed.json is empty")
    return feed[0]


def text_blob(brief: dict) -> str:
    parts = [brief.get("analysis", "")]
    for item in brief.get("headlines", []):
        parts.extend([item.get("headline", ""), item.get("why_it_matters", ""), item.get("ticker", "")])
    snapshot = brief.get("market_snapshot", {})
    parts.extend(str(v) for v in snapshot.values())
    usac = brief.get("usac") or {}
    parts.extend(str(v) for v in usac.values())
    return "\n".join(parts)


def sentence_count(text: str) -> int:
    return len([s for s in re.split(r"(?<=[.!?])\s+", text.strip()) if s])


def make_suggestions(brief: dict, opinion: dict | None) -> list[dict]:
    blob = text_blob(brief).lower()
    snapshot = brief.get("market_snapshot", {})
    suggestions: list[dict] = []
    missing_opinion = opinion is None

    ten_y = snapshot.get("treasury_10y_pct")
    wti = snapshot.get("wti_usd")
    wti_day = snapshot.get("wti_day_pct")

    oil_stress = any(term in blob for term in ["brent", "wti", "crude", "oil"]) and (
        (isinstance(wti, (int, float)) and wti >= 90) or
        (isinstance(wti_day, (int, float)) and wti_day >= 1.5) or
        "energy" in blob
    )
    rate_stress = (isinstance(ten_y, (int, float)) and ten_y >= 5.0) or any(
        term in blob for term in ["yield", "rate-hike", "hike", "duration"]
    )
    tech_pressure = any(term in blob for term in ["nasdaq", "qqq", "tech", "semis", "ai-safety", "meta fell", "chip"])
    nvda_support = "nvda" in blob or "nvidia" in blob
    nvda_buyback = "buyback" in blob or "repurchase" in blob
    ba_pressure = "boeing" in blob and any(term in blob for term in ["glitch", "737 max", "software"])

    if oil_stress:
        suggestions.append({
            "action": "add",
            "symbol": "XLE",
            "position": "shares",
            "confidence": "medium",
            "reasoning": "The newest synthetic brief keeps crude and energy at the center of the tape, with oil strength reinforcing inflation and rate pressure while energy equities are described as relative winners. XLE is the clean diversified equity expression for that synthetic setup, and the call updates earlier history where falling-oil diplomacy supported trimming energy exposure. Confidence stays medium because the generator uses repo facts only and any fast diplomatic reversal would quickly unwind the oil premise." if not missing_opinion else "The newest synthetic brief keeps crude and energy at the center of the tape, with oil strength reinforcing inflation and rate pressure while energy equities are described as relative winners. XLE is the clean diversified equity expression for that synthetic setup, and the missing matching opinion file keeps this from ranking as high conviction. Confidence stays medium because the generator uses repo facts only and any fast diplomatic reversal would quickly unwind the oil premise.",
            "catalyst": "Sustained crude strength and energy-sector relative strength could extend the rotation into XLE.",
            "risk": "Iran de-escalation, a crude reversal, or broad risk-off selling could invalidate the add."
        })

    if rate_stress and tech_pressure:
        suggestions.append({
            "action": "trim",
            "symbol": "QQQ",
            "position": "shares",
            "confidence": "medium",
            "reasoning": "The newest synthetic brief frames higher Treasury yields and oil-driven inflation pressure as the main force weighing on rate-sensitive growth and AI-adjacent technology. Trimming oversized QQQ exposure is a risk-control expression rather than an aggressive short, especially while Nvidia has company-specific support that can keep parts of the complex bid. The upcoming macro-data window in the brief makes the setup actionable, but missing breadth and live execution data keep conviction at medium.",
            "catalyst": "Persistent yield pressure into PCE and jobs data could deepen growth-stock valuation compression.",
            "risk": "Falling yields, credible diplomacy, or broad AI leadership could make the trim premature."
        })

    if nvda_support and nvda_buyback:
        suggestions.append({
            "action": "watch",
            "symbol": "NVDA",
            "position": "shares",
            "confidence": "medium",
            "reasoning": "The synthetic brief gives Nvidia a company-specific support line through its large buyback authorization and relative strength versus the weaker AI and semiconductor tape. That support is worth watching, but an authorization is not the same as executed buying and does not remove the macro headwind from higher yields. Wait for NVDA to hold its opening range and outperform QQQ before upgrading from watch to add.",
            "catalyst": "Sustained relative strength and evidence of buyback support could improve the entry setup.",
            "risk": "Higher yields, AI-spending concerns, or a failed opening-range hold could overwhelm the buyback narrative."
        })

    if ba_pressure and len(suggestions) < 3:
        suggestions.append({
            "action": "avoid",
            "symbol": "BA",
            "position": "shares",
            "confidence": "medium",
            "reasoning": "The newest synthetic brief describes Boeing's software issue as moving from a headline shock to a delivery and certification overhang. Avoiding fresh BA exposure is cleaner than shorting because the timing of fixes, FAA review, and airline acceptance can shift abruptly. This is an entry-avoidance call until the delivery path and certification risk are clearer.",
            "catalyst": "More delivery refusals or certification delays could keep pressure on Boeing shares.",
            "risk": "A credible fix timeline or regulator comfort could quickly reduce the overhang."
        })

    if not suggestions:
        suggestions.append({
            "action": "watch",
            "symbol": "SPY",
            "position": "shares",
            "confidence": "low",
            "reasoning": "The newest synthetic brief does not provide enough clean, ranked conviction for a directional trade. Watching SPY preserves market context while avoiding forced exposure when signals are thin or contradictory. Upgrade only after the brief shows clearer breadth, macro direction, or company-specific follow-through.",
            "catalyst": "Clearer breadth and macro confirmation could turn the setup into an actionable index call.",
            "risk": "A sharp move before confirmation could make the watch stance late."
        })

    return suggestions[:3]


def validate_batch(batch: dict, expected_brief_id: str) -> None:
    errors = []
    if batch.get("brief_id") != expected_brief_id:
        errors.append("brief_id mismatch")
    if batch.get("advisor") != "Codex-Suggestions":
        errors.append("advisor missing or wrong")
    generated = batch.get("generated_at_pt")
    try:
        dt = datetime.fromisoformat(generated)
        if dt.tzinfo is None or dt.utcoffset() is None:
            errors.append("generated_at_pt not timezone-aware")
    except Exception as exc:
        errors.append(f"generated_at_pt invalid: {exc}")
    suggestions = batch.get("suggestions")
    if not isinstance(suggestions, list) or not 1 <= len(suggestions) <= 3:
        errors.append("suggestions must contain 1-3 entries")
    for i, item in enumerate(suggestions or [], 1):
        for key in ("action", "confidence", "reasoning", "catalyst", "risk"):
            if not isinstance(item.get(key), str) or not item[key].strip():
                errors.append(f"item {i} missing {key}")
        if item.get("action") not in ACTIONS:
            errors.append(f"item {i} invalid action")
        if item.get("confidence") not in CONFIDENCE:
            errors.append(f"item {i} invalid confidence")
        if "position" in item and item["position"] not in POSITIONS:
            errors.append(f"item {i} invalid position")
        if "strike" in item and not isinstance(item["strike"], (int, float)):
            errors.append(f"item {i} strike must be numeric")
        if "expiry" in item and not re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(item["expiry"])):
            errors.append(f"item {i} expiry must be YYYY-MM-DD")
        if sentence_count(item.get("reasoning", "")) not in (2, 3):
            errors.append(f"item {i} reasoning must be 2-3 sentences")
        if "\n" in item.get("catalyst", "") or "\n" in item.get("risk", ""):
            errors.append(f"item {i} catalyst/risk must be single-line")
    if errors:
        raise SystemExit("Validation failed: " + "; ".join(errors))


def in_publish_window(now: datetime) -> bool:
    return now.weekday() < 5 and now.hour in {5, 6, 7, 8, 9, 10}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--enforce-window", action="store_true", help="Skip unless current America/Los_Angeles time is a weekday 5-10 AM run window.")
    args = parser.parse_args()

    now = datetime.now(PT).replace(microsecond=0)
    if args.enforce_window and not in_publish_window(now):
        print(f"Outside publish window in America/Los_Angeles: {now.isoformat()}")
        return

    root = Path.cwd()
    feed = json.loads((root / "feed.json").read_text())
    latest = newest_feed_item(feed)
    brief_id = latest["brief_id"]
    brief_path = root / "briefs" / latest.get("file", f"{brief_id}.json")
    brief = json.loads(brief_path.read_text())

    opinion_path = root / "opinions" / f"{brief_id}.json"
    opinion = json.loads(opinion_path.read_text()) if opinion_path.exists() else None

    batch = {
        "brief_id": brief_id,
        "advisor": "Codex-Suggestions",
        "generated_at_pt": now.isoformat(),
        "suggestions": make_suggestions(brief, opinion),
    }
    validate_batch(batch, brief_id)

    out = root / "suggestions" / f"{brief_id}-ranked.json"
    out.parent.mkdir(exist_ok=True)
    text = json.dumps(batch, indent=2) + "\n"
    if out.exists() and out.read_text() == text:
        print(f"No change: {out}")
    else:
        out.write_text(text)
        print(f"Wrote {out}")


if __name__ == "__main__":
    main()
