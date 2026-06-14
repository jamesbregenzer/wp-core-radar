#!/usr/bin/env python3
"""Generate the public static WP Core Radar dashboard."""

from __future__ import annotations

import html
import re
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

from radarlib import (
    KEYWORDS_KEYS,
    STATUS_KEYS,
    SUMMARY_KEYS,
    discover_datasets,
    first_value,
    load_outcomes,
    load_queries,
    load_reviews,
    read_ticket_rows,
    score_ticket,
    trac_url,
)


PRIORITY_TARGET_LIMIT = 12
PRIORITY_TARGET_MIN_SCORE = 150
COMPLETED_REVIEW_STATUSES = {"tested", "commented", "props", "committed"}


def review_status(item: dict[str, Any]) -> str:
    review = item.get("review") or {}
    return review.get("status", "").strip().lower()


def priority_tier(item: dict[str, Any]) -> tuple[str, str]:
    score = item.get("score", 0)

    if score >= 165:
        return "immediate", "Immediate Review"
    if score >= 150:
        return "strong", "Strong Candidate"
    if score >= 130:
        return "watching", "Worth Watching"

    return "standard", "Standard"


def is_priority_target(item: dict[str, Any]) -> bool:
    if review_status(item):
        return False

    if item.get("score", 0) < PRIORITY_TARGET_MIN_SCORE:
        return False

    reasons = " ".join(item.get("reasons", [])).lower()

    has_action_signal = (
        "needs testing" in reasons
        or "has patch" in reasons
        or "good first bug" in reasons
    )

    has_recent_or_manageable_signal = (
        "recent activity" in reasons
        or "healthy comment count" in reasons
        or "has owner" in reasons
    )

    has_stale_penalty = (
        "very old ticket" in reasons
        or "stale activity" in reasons
        or "very large thread" in reasons
        or "already produced props" in reasons
        or "already tested" in reasons
    )

    return has_action_signal and has_recent_or_manageable_signal and not has_stale_penalty


def group_items(items: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    groups: dict[str, list[dict[str, Any]]] = {
        "priority": [],
        "top": [],
        "shortlist": [],
        "watch": [],
        "completed": [],
        "rejected": [],
    }

    for item in items:
        status = review_status(item)

        if status == "reject":
            groups["rejected"].append(item)
        elif status == "shortlist":
            groups["shortlist"].append(item)
        elif status == "watch":
            groups["watch"].append(item)
        elif status in COMPLETED_REVIEW_STATUSES:
            groups["completed"].append(item)
        elif is_priority_target(item) and len(groups["priority"]) < PRIORITY_TARGET_LIMIT:
            groups["priority"].append(item)
        else:
            groups["top"].append(item)

    return groups


def collect_items() -> tuple[list[dict[str, Any]], dict[str, set[str]], dict[str, Any]]:
    query_list = load_queries()
    query_meta = {query["slug"]: query for query in query_list}
    outcomes = load_outcomes()
    reviews = load_reviews()
    datasets = discover_datasets()

    scored_by_ticket: dict[str, dict[str, Any]] = {}
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

    return ranked, duplicate_sources, {
        "datasets": datasets,
        "outcomes": outcomes,
        "reviews": reviews,
    }


def pretty_label(value: str) -> str:
    words = value.replace("_", " ").replace("-", " ").strip().split()
    return " ".join(word.upper() if word.lower() in {"ui", "ux"} else word.capitalize() for word in words)


def clean_reason_label(reason: str) -> str:
    reason = re.sub(r"[+-]\d+", "", reason)
    return pretty_label(reason.strip(" ,"))


def signal_class(label: str) -> str:
    lowered = label.lower()

    if "priority" in lowered:
        return "priority"
    if "patch" in lowered:
        return "patch"
    if "testing" in lowered or "unit test" in lowered:
        return "testing"
    if "first bug" in lowered or "good first" in lowered:
        return "first"
    if "feedback" in lowered:
        return "feedback"
    if "owner" in lowered:
        return "owner"
    if "refresh" in lowered:
        return "refresh"

    return "standard"


def signal_badge(label: str) -> str:
    css_class = signal_class(label)
    return f'<span class="signal-badge signal-{html.escape(css_class)}">{html.escape(label)}</span>'


def signal_badges(keywords: str, reasons: list[str]) -> str:
    labels = [pretty_label(keyword) for keyword in keywords.split()]
    labels.extend(clean_reason_label(reason) for reason in reasons)

    seen: set[str] = set()
    badges: list[str] = []

    for label in labels:
        key = label.lower()
        if not label or key in seen:
            continue

        seen.add(key)
        badges.append(signal_badge(label))

    return " ".join(badges)


def discovery_track_label(sources: set[str]) -> str:
    return ", ".join(pretty_label(source) for source in sorted(sources))


def ticket_row(item: dict[str, Any], duplicate_sources: dict[str, set[str]]) -> str:
    row = item["row"]
    ticket_id = item["ticket_id"]
    tier_class, tier_label = priority_tier(item)

    summary = first_value(row, SUMMARY_KEYS, "Untitled ticket")
    keywords = first_value(row, KEYWORDS_KEYS, "")
    signals = signal_badges(keywords, item["reasons"])
    trac_status = pretty_label(first_value(row, STATUS_KEYS, ""))
    discovery_track = discovery_track_label(duplicate_sources[ticket_id])
    track = item["query"].get("name", item["query"].get("track", "unknown"))

    return f"""
<tr class="tier-{html.escape(tier_class)}">
  <td class="score" data-label="Score">{item["score"]}</td>
  <td data-label="Tier"><span class="tier-label tier-label-{html.escape(tier_class)}">{html.escape(tier_label)}</span></td>
  <td data-label="Ticket"><a href="{html.escape(trac_url(ticket_id))}">#{html.escape(ticket_id)}</a></td>
  <td data-label="Summary">{html.escape(summary)}</td>
  <td data-label="Track">{html.escape(track)}</td>
  <td data-label="Trac Status">{html.escape(trac_status)}</td>
  <td data-label="Discovery Track">{html.escape(discovery_track)}</td>
  <td data-label="Signals" class="signals">{signals}</td>
</tr>
"""


def section_html(title: str, items: list[dict[str, Any]], duplicate_sources: dict[str, set[str]], limit: int | None = None) -> str:
    display_items = items if limit is None else items[:limit]
    rows = "\n".join(ticket_row(item, duplicate_sources) for item in display_items)

    if not rows:
        rows = '<tr><td colspan="8" class="empty">No tickets in this section.</td></tr>'

    return f"""
<section>
  <h2>{html.escape(title)} <span>{len(items)}</span></h2>
  <div class="table-wrap">
    <table>
      <thead>
        <tr>
          <th>Score</th>
          <th>Tier</th>
          <th>Ticket</th>
          <th>Summary</th>
          <th>Track</th>
          <th>Trac Status</th>
          <th>Discovery Track</th>
          <th>Signals</th>
        </tr>
      </thead>
      <tbody>
        {rows}
      </tbody>
    </table>
  </div>
</section>
"""


def dashboard_css() -> str:
    return """
    body {
      font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      margin: 0;
      background: #f6f7f7;
      color: #1d2327;
    }
    header {
      padding: 32px;
      background: #1d2327;
      color: white;
    }
    header h1 {
      margin: 0 0 8px;
      font-size: 32px;
    }
    header p {
      margin: 0;
      color: #c3c4c7;
    }
    main {
      padding: 24px 32px 48px;
    }
    .summary {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
      gap: 16px;
      margin-bottom: 24px;
    }
    .card {
      background: white;
      border: 1px solid #dcdcde;
      border-radius: 8px;
      padding: 16px;
    }
    .card strong {
      display: block;
      font-size: 28px;
      margin-bottom: 4px;
    }
    .card-blue { border-left: 6px solid #2563eb; }
    .card-purple { border-left: 6px solid #7c3aed; }
    .card-amber { border-left: 6px solid #d97706; }

    section {
      margin-top: 32px;
    }
    h2 {
      display: flex;
      gap: 8px;
      align-items: baseline;
    }
    h2 span {
      font-size: 14px;
      color: #646970;
      font-weight: 500;
    }
    .table-wrap {
      overflow-x: auto;
      background: white;
      border: 1px solid #dcdcde;
      border-radius: 8px;
    }
    table {
      width: 100%;
      border-collapse: collapse;
      font-size: 14px;
    }
    th,
    td {
      padding: 10px 12px;
      border-bottom: 1px solid #f0f0f1;
      text-align: left;
      vertical-align: top;
    }
    th {
      background: #f0f0f1;
      white-space: nowrap;
      position: sticky;
      top: 0;
    }
    tr.tier-immediate { border-left: 6px solid #2563eb; }
    tr.tier-strong { border-left: 6px solid #7c3aed; }
    tr.tier-watching { border-left: 6px solid #d97706; }
    tr.tier-standard { border-left: 6px solid transparent; }

    td.score {
      font-weight: 700;
      font-size: 18px;
    }
    .signals {
      min-width: 300px;
    }
    .signal-badge,
    .tier-label {
      display: inline-block;
      border-radius: 999px;
      padding: 4px 8px;
      margin: 0 4px 5px 0;
      font-size: 12px;
      font-weight: 700;
      white-space: nowrap;
    }
    .signal-standard,
    .tier-label-standard {
      background: #f3f4f6;
      color: #4b5563;
    }
    .signal-priority,
    .signal-owner {
      background: #e0f2fe;
      color: #075985;
    }
    .signal-patch,
    .tier-label-immediate {
      background: #dbeafe;
      color: #1d4ed8;
    }
    .signal-testing {
      background: #dcfce7;
      color: #166534;
    }
    .signal-first,
    .tier-label-watching {
      background: #fef3c7;
      color: #92400e;
    }
    .signal-feedback,
    .tier-label-strong {
      background: #ede9fe;
      color: #6d28d9;
    }
    .signal-refresh {
      background: #ffedd5;
      color: #9a3412;
    }
    a {
      color: #2271b1;
      font-weight: 600;
    }
    .empty {
      color: #646970;
      font-style: italic;
    }
    footer {
      padding: 24px 32px;
      color: #646970;
      font-size: 13px;
    }

    @media (max-width: 900px) {
      header { padding: 24px 18px; }
      header h1 { font-size: 26px; }
      main { padding: 18px; }
      .summary { grid-template-columns: repeat(2, minmax(0, 1fr)); }

      table,
      thead,
      tbody,
      th,
      td,
      tr {
        display: block;
      }

      thead { display: none; }

      tr {
        padding: 14px;
        border-bottom: 1px solid #dcdcde;
      }

      td {
        border: 0;
        padding: 6px 0;
      }

      td::before {
        content: attr(data-label);
        display: block;
        color: #646970;
        font-size: 12px;
        font-weight: 700;
        text-transform: uppercase;
        margin-bottom: 2px;
      }

      td.score { font-size: 24px; }
    }

    @media (max-width: 520px) {
      .summary { grid-template-columns: 1fr; }
    }
    """


def build_dashboard() -> str:
    ranked, duplicate_sources, summary = collect_items()
    groups = group_items(ranked)
    generated = datetime.now().strftime("%Y-%m-%d %H:%M")

    immediate_count = sum(1 for item in groups["priority"] if priority_tier(item)[0] == "immediate")
    strong_count = sum(1 for item in groups["priority"] if priority_tier(item)[0] == "strong")
    watching_count = sum(1 for item in groups["top"] if priority_tier(item)[0] == "watching")

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>WP Core Radar Dashboard</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <style>
{dashboard_css()}
  </style>
</head>
<body>
  <header>
    <h1>WP Core Radar Dashboard</h1>
    <p>Generated {html.escape(generated)}. Radar recommends opportunities only. Humans make contribution decisions.</p>
  </header>

  <main>
    <div class="summary">
      <div class="card"><strong>{len(ranked)}</strong>Unique tickets scored</div>
      <div class="card"><strong>{len(groups["priority"])}</strong>Priority targets</div>
      <div class="card card-blue"><strong>{immediate_count}</strong>Immediate Review</div>
      <div class="card card-purple"><strong>{strong_count}</strong>Strong Candidates</div>
      <div class="card card-amber"><strong>{watching_count}</strong>Worth Watching</div>
      <div class="card"><strong>{len(summary["reviews"])}</strong>Reviews loaded</div>
    </div>

    {section_html("Priority Targets", groups["priority"], duplicate_sources)}
    {section_html("Top Opportunities", groups["top"], duplicate_sources, limit=50)}
    {section_html("Shortlisted", groups["shortlist"], duplicate_sources)}
    {section_html("Watching", groups["watch"], duplicate_sources)}
    {section_html("Completed / Acted On", groups["completed"], duplicate_sources)}
    {section_html("Rejected", groups["rejected"], duplicate_sources)}
  </main>

  <footer>
    WP Core Radar does not auto-comment on Trac or automate contribution activity.
  </footer>
</body>
</html>
"""


def main() -> int:
    radar_dir = Path("docs") / "radar"
    radar_dir.mkdir(parents=True, exist_ok=True)

    dashboard = build_dashboard()
    output = radar_dir / "index.html"
    output.write_text(dashboard, encoding="utf-8")

    print(f"Wrote {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
