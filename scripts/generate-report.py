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
    load_reviews,
    read_ticket_rows,
    score_ticket,
    trac_url,
    SUMMARY_KEYS,
    COMPONENT_KEYS,
    KEYWORDS_KEYS,
    STATUS_KEYS,
    MILESTONE_KEYS,
)


def review_status(item: dict) -> str:
    review = item.get("review") or {}
    return review.get("status", "").strip().lower()


def group_items(items: list[dict]) -> dict[str, list[dict]]:
    groups = {
        "top": [],
        "shortlist": [],
        "watch": [],
        "rejected": [],
        "completed": [],
    }

    for item in items:
        status = review_status(item)

        if status == "reject":
            groups["rejected"].append(item)
        elif status == "shortlist":
            groups["shortlist"].append(item)
        elif status == "watch":
            groups["watch"].append(item)
        elif status in {"tested", "commented", "props", "committed"}:
            groups["completed"].append(item)
        else:
            groups["top"].append(item)

    return groups


def append_ticket(lines: list[str], index: int, item: dict, duplicate_sources: dict[str, set[str]]) -> None:
    row = item["row"]
    ticket_id = item["ticket_id"]
    review = item.get("review") or {}

    summary = first_value(row, SUMMARY_KEYS, "Untitled ticket")
    component = first_value(row, COMPONENT_KEYS, "Unknown")
    keywords = first_value(row, KEYWORDS_KEYS, "")
    status = first_value(row, STATUS_KEYS, "")
    milestone = first_value(row, MILESTONE_KEYS, "")
    sources = ", ".join(sorted(duplicate_sources[ticket_id]))
    reasons = ", ".join(item["reasons"][:8])

    lines.append(f"#### {index}. [#{ticket_id}]({trac_url(ticket_id)}) — {summary}")
    lines.append("")
    lines.append(f"- Score: **{item['score']}**")
    lines.append(f"- Track/query: {item['query'].get('name', item['query'].get('track', 'unknown'))}")
    lines.append(f"- Sources: {sources}")
    lines.append(f"- Component: {component}")

    if status:
        lines.append(f"- Trac status: {status}")
    if milestone:
        lines.append(f"- Milestone: {milestone}")
    if keywords:
        lines.append(f"- Keywords: {keywords}")

    if review:
        review_state = review.get("status", "")
        review_reason = review.get("reason", "")
        review_notes = review.get("notes", "")
        review_updated = review.get("updated_at", "")

        if review_state:
            lines.append(f"- Review status: **{review_state}**")
        if review_reason:
            lines.append(f"- Review reason: {review_reason}")
        if review_notes:
            lines.append(f"- Review notes: {review_notes}")
        if review_updated:
            lines.append(f"- Review updated: {review_updated}")

    lines.append(f"- Why it ranked: {reasons}")
    lines.append("- Human next step: open ticket, verify current state, test locally if appropriate, then decide whether to comment manually.")
    lines.append("")


def append_section(
    lines: list[str],
    title: str,
    items: list[dict],
    duplicate_sources: dict[str, set[str]],
    limit: int | None = None,
    empty_message: str = "No tickets in this section.",
) -> None:
    lines.append(f"## {title}")
    lines.append("")

    display_items = items if limit is None else items[:limit]

    if not display_items:
        lines.append(empty_message)
        lines.append("")
        return

    for index, item in enumerate(display_items, start=1):
        append_ticket(lines, index, item, duplicate_sources)


def build_report(limit: int = 50) -> str:
    query_list = load_queries()
    query_meta = {q["slug"]: q for q in query_list}
    outcomes = load_outcomes()
    reviews = load_reviews()
    datasets = discover_datasets()

    scored_by_ticket: dict[str, dict] = {}
    duplicate_sources: dict[str, set[str]] = defaultdict(set)

    for dataset in datasets:
        meta = query_meta.get(
            dataset.query_slug,
            {"priority": 50, "name": dataset.query_slug, "track": dataset.query_slug},
        )

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
                "review": reviews.get(ticket_id),
            }

            if ticket_id not in scored_by_ticket or score > scored_by_ticket[ticket_id]["score"]:
                scored_by_ticket[ticket_id] = candidate

    ranked = sorted(
        scored_by_ticket.values(),
        key=lambda item: (-item["score"], int(item["ticket_id"])),
    )

    groups = group_items(ranked)

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
    lines.append(f"- Reviews loaded: {len(reviews)}")
    lines.append(f"- Top opportunity limit: {limit}")
    lines.append("")
    lines.append("## Review Workflow")
    lines.append("")
    lines.append("| Section | Count | Meaning |")
    lines.append("|---|---:|---|")
    lines.append(f"| Top Opportunities | {len(groups['top'])} | Unreviewed or active tickets Radar recommends reviewing first. |")
    lines.append(f"| Shortlisted | {len(groups['shortlist'])} | Tickets manually marked as strong candidates. |")
    lines.append(f"| Watching | {len(groups['watch'])} | Tickets worth monitoring but not acting on yet. |")
    lines.append(f"| Completed / Acted On | {len(groups['completed'])} | Tickets already tested, commented on, propped, or committed. |")
    lines.append(f"| Rejected | {len(groups['rejected'])} | Tickets manually rejected as poor fits. |")
    lines.append("")

    append_section(
        lines,
        "Top Opportunities",
        groups["top"],
        duplicate_sources,
        limit=limit,
        empty_message="No top opportunities found. Run the collector or review rejected/watch statuses.",
    )

    append_section(lines, "Shortlisted", groups["shortlist"], duplicate_sources)
    append_section(lines, "Watching", groups["watch"], duplicate_sources)
    append_section(lines, "Completed / Acted On", groups["completed"], duplicate_sources)
    append_section(lines, "Rejected", groups["rejected"], duplicate_sources)

    lines.append("## Dataset Inventory")
    lines.append("")
    if datasets:
        lines.append("| Query | Date | Rows | File |")
        lines.append("|---|---:|---:|---|")
        for dataset in datasets:
            lines.append(
                f"| {dataset.query_slug} | {dataset.collected_date} | {dataset.row_count} | `{dataset.path}` |"
            )
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
