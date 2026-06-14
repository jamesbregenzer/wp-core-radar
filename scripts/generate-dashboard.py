#!/usr/bin/env python3
"""Generate the public static WP Core Radar dashboard."""

from __future__ import annotations

import html
from datetime import datetime
from pathlib import Path
from typing import Any

from radarlib import (
    KEYWORDS_KEYS,
    STATUS_KEYS,
    SUMMARY_KEYS,
    collect_items,
    discovery_track_label,
    first_value,
    group_items,
    pretty_label,
    priority_tier,
    signal_class,
    signal_labels,
    trac_url,
)

PUBLIC_TOP_LIMIT = 50


def html_badge(label: str, css_prefix: str = "signal") -> str:
    return f'<span class="{css_prefix}-badge {css_prefix}-{html.escape(signal_class(label))}">{html.escape(label)}</span>'


def signal_badges(keywords: str, reasons: list[str]) -> str:
    return " ".join(html_badge(label, "signal") for label in signal_labels(keywords, reasons))


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


def section_html(
    title: str,
    items: list[dict[str, Any]],
    duplicate_sources: dict[str, set[str]],
    limit: int | None = None,
) -> str:
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
    section { margin-top: 32px; }
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
    .signals { min-width: 300px; }
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
    .tier-label-standard { background: #f3f4f6; color: #4b5563; }
    .signal-priority,
    .signal-owner { background: #e0f2fe; color: #075985; }
    .signal-patch,
    .tier-label-immediate { background: #dbeafe; color: #1d4ed8; }
    .signal-testing { background: #dcfce7; color: #166534; }
    .signal-first,
    .tier-label-watching { background: #fef3c7; color: #92400e; }
    .signal-feedback,
    .tier-label-strong { background: #ede9fe; color: #6d28d9; }
    .signal-refresh { background: #ffedd5; color: #9a3412; }
    .signal-recent { background: #ccfbf1; color: #115e59; }
    .signal-component { background: #fce7f3; color: #9d174d; }
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
      tr { display: block; }
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
    {section_html("Top Opportunities", groups["top"], duplicate_sources, limit=PUBLIC_TOP_LIMIT)}
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

    output = radar_dir / "index.html"
    output.write_text(build_dashboard(), encoding="utf-8")

    print(f"Wrote {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
