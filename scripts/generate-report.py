#!/usr/bin/env python3
"""Generate a unified ranked WP Core Radar opportunity report."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from pathlib import Path

from radarlib import (
    REPORTS_DIR,
    discover_datasets,
    first_value,
    load_outcomes,
    load_queries,
    read_ticket_rows,
    score_ticket,
    trac_url,
    SUMMARY_KEYS,
    COMPONENT_KEYS,
    KEYWORDS_KEYS,
    STATUS_KEYS,
    MILESTONE_KEYS,
)


def build_report(limit: int = 50) -> str:
    query_list = load_queries()
    query_meta = {q["slug"]: q for q in query_list}
    outcomes = load_outcomes()
    datasets = discover_datasets()

    scored_by_ticket: dict[str, dict] = {}
    duplicate_sources: dict[str, set[str]] = defaultdict(set)

    for dataset in datasets:
        meta = query_meta.get(dataset.query_slug, {"priority": 50, "name": dataset.query_slug, "track": dataset.query_slug})
        for row in read_ticket_rows(dataset):
            score, reasons = score_ticket(row, meta, outcomes)
            ticket_id = row["ticket_id"]
            duplicate_sources[ticket_id].add(dataset.query_slug)
            candidate = {
                "ticket_id": ticket_id,
                "score": score,
                "reasons": reasons,
                "row": row,
                "query": meta,
            }
            if ticket_id not in scored_by_ticket or score > scored_by_ticket[ticket_id]["score"]:
                scored_by_ticket[ticket_id] = candidate

    ranked = sorted(scored_by_ticket.values(), key=lambda item: (-item["score"], int(item["ticket_id"])))
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    lines: list[str] = []
    lines.append("# WP Core Radar Report")
    lines.append("")
    lines.append(f"Generated: {now}")
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append(f"- Datasets discovered: {len(datasets)}")
    lines.append(f"- Unique tickets scored: {len(ranked)}")
    lines.append(f"- Outcomes loaded: {len(outcomes)}")
    lines.append(f"- Report limit: {limit}")
    lines.append("")
    lines.append("## Top Opportunities")
    lines.append("")

    if not ranked:
        lines.append("No opportunities found. Run the collector or add CSV files under `data/raw/`.")
    else:
        for index, item in enumerate(ranked[:limit], start=1):
            row = item["row"]
            ticket_id = item["ticket_id"]
            summary = first_value(row, SUMMARY_KEYS, "Untitled ticket")
            component = first_value(row, COMPONENT_KEYS, "Unknown")
            keywords = first_value(row, KEYWORDS_KEYS, "")
            status = first_value(row, STATUS_KEYS, "")
            milestone = first_value(row, MILESTONE_KEYS, "")
            sources = ", ".join(sorted(duplicate_sources[ticket_id]))
            reasons = "; ".join(item["reasons"][:8])

            lines.append(f"### {index}. [#{ticket_id}]({trac_url(ticket_id)}) — {summary}")
            lines.append("")
            lines.append(f"- Score: **{item['score']}**")
            lines.append(f"- Track/query: {item['query'].get('name', item['query'].get('track', 'unknown'))}")
            lines.append(f"- Sources: {sources}")
            lines.append(f"- Component: {component}")
            if status:
                lines.append(f"- Status: {status}")
            if milestone:
                lines.append(f"- Milestone: {milestone}")
            if keywords:
                lines.append(f"- Keywords: `{keywords}`")
            lines.append(f"- Why it ranked: {reasons}")
            lines.append("- Human next step: open ticket, verify current state, test locally if appropriate, then decide whether to comment manually.")
            lines.append("")

    lines.append("## Dataset Inventory")
    lines.append("")
    if datasets:
        lines.append("| Query | Date | Rows | File |")
        lines.append("|---|---:|---:|---|")
        for dataset in datasets:
            lines.append(f"| {dataset.query_slug} | {dataset.collected_date} | {dataset.row_count} | `{dataset.path}` |")
    else:
        lines.append("No CSV datasets discovered.")
    lines.append("")
    lines.append("## Guardrail")
    lines.append("")
    lines.append("Radar does not auto-comment on Trac. All contribution decisions remain human-reviewed.")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    report = build_report()
    latest = REPORTS_DIR / "latest.md"
    dated = REPORTS_DIR / f"radar-{datetime.now().strftime('%Y-%m-%d')}.md"
    latest.write_text(report, encoding="utf-8")
    dated.write_text(report, encoding="utf-8")
    print(f"Wrote {latest}")
    print(f"Wrote {dated}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
