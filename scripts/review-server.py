#!/usr/bin/env python3
"""Local admin review console for WP Core Radar."""

from __future__ import annotations

import html
import importlib.util
import re
import subprocess
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from radarlib import (
    ROOT,
    trac_url,
    first_value,
    SUMMARY_KEYS,
    COMPONENT_KEYS,
    KEYWORDS_KEYS,
    STATUS_KEYS,
    MILESTONE_KEYS,
    OWNER_KEYS,
    COMMENTS_KEYS,
    MODIFIED_KEYS,
    CREATED_KEYS,
)

dashboard_path = Path(__file__).resolve().parent / "generate-dashboard.py"
spec = importlib.util.spec_from_file_location("generate_dashboard", dashboard_path)
generate_dashboard = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(generate_dashboard)

collect_items = generate_dashboard.collect_items
group_items = generate_dashboard.group_items
priority_tier = generate_dashboard.priority_tier

HOST = "127.0.0.1"
PORT = 8765


def run_command(command: list[str]) -> None:
    subprocess.run(command, cwd=ROOT, check=False)


def item_summary(item: dict) -> str:
    return first_value(item["row"], SUMMARY_KEYS, "Untitled ticket")


def copy_context(item: dict) -> str:
    row = item["row"]
    ticket_id = item["ticket_id"]
    _, tier_label = priority_tier(item)
    review = item.get("review") or {}

    lines = [
        "Please review this WordPress Core contribution opportunity and give me a green light, yellow light, or red light.",
        "",
        f"Ticket: #{ticket_id}",
        f"URL: {trac_url(ticket_id)}",
        f"Summary: {item_summary(item)}",
        f"Score: {item['score']}",
        f"Priority tier: {tier_label}",
        f"Track: {item['query'].get('name', item['query'].get('track', 'unknown'))}",
        "",
        "Ticket fields:",
        f"- Component: {first_value(row, COMPONENT_KEYS, 'Unknown')}",
        f"- Status: {first_value(row, STATUS_KEYS, 'Unknown')}",
        f"- Milestone: {first_value(row, MILESTONE_KEYS, 'Unknown')}",
        f"- Owner: {first_value(row, OWNER_KEYS, 'Unknown')}",
        f"- Keywords: {first_value(row, KEYWORDS_KEYS, '')}",
        f"- Comments: {first_value(row, COMMENTS_KEYS, 'Unknown')}",
        f"- Created: {first_value(row, CREATED_KEYS, 'Unknown')}",
        f"- Modified: {first_value(row, MODIFIED_KEYS, 'Unknown')}",
        "",
        "Radar scoring details:",
    ]

    for reason in item["reasons"]:
        lines.append(f"- {reason}")

    if review:
        lines.extend([
            "",
            "Current review state:",
            f"- Status: {review.get('status', '')}",
            f"- Reason: {review.get('reason', '')}",
            f"- Notes: {review.get('notes', '')}",
            f"- Updated: {review.get('updated_at', '')}",
        ])

    lines.extend([
        "",
        "What I need from you:",
        "- Is this likely a good WordPress Core contribution opportunity for me?",
        "- What should I check before spending time on it?",
        "- Should I reject, watch, shortlist, or test this ticket?",
    ])

    return "\n".join(lines)


def action_form(ticket_id: str) -> str:
    safe_ticket = html.escape(ticket_id)

    return f"""
    <form method="post" action="/radar/admin/review" class="decision-form">
      <input type="hidden" name="ticket" value="{safe_ticket}">
      <select name="status" aria-label="Review decision" required>
        <option value="" selected>Choose action...</option>
        <option value="shortlist">Shortlist</option>
        <option value="watch">Watch</option>
        <option value="reject">Reject</option>
        <option value="tested">Tested</option>
        <option value="commented">Commented</option>
        <option value="props">Props</option>
        <option value="committed">Committed</option>
      </select>
      <input type="text" name="reason" placeholder="Reason / note" class="conditional-field">
      <button type="submit" class="conditional-field" disabled>Save</button>
    </form>
    """


def reason_badges(reasons: list[str]) -> str:
    labels = []

    for reason in reasons:
        lower = reason.lower()

        if "has patch" in lower:
            labels.append(("patch", "Has Patch"))
        elif "needs testing" in lower:
            labels.append(("testing", "Needs Testing"))
        elif "good first bug" in lower:
            labels.append(("first", "Good First Bug"))
        elif "dev feedback" in lower:
            labels.append(("feedback", "Dev Feedback"))
        elif "reporter feedback" in lower:
            labels.append(("feedback", "Reporter Feedback"))
        elif "has owner" in lower:
            labels.append(("owner", "Has Owner"))
        elif "recent activity" in lower:
            labels.append(("recent", "Recent Activity"))
        elif "preferred component" in lower:
            labels.append(("component", "Preferred Component"))

    if not labels:
        labels.append(("standard", "Scored Candidate"))

    seen = set()
    badges = []

    for badge_class, label in labels:
        if label in seen:
            continue

        seen.add(label)
        badges.append(
            f'<span class="reason-badge reason-{html.escape(badge_class)}">{html.escape(label)}</span>'
        )

    return " ".join(badges)


def score_breakdown(reasons: list[str]) -> str:
    rows = []

    for reason in reasons:
        match = re.search(r"([+-]\d+)", reason)
        points = match.group(1) if match else ""
        label = reason.replace(points, "").strip(" ,") if points else reason

        point_class = "positive" if points.startswith("+") else "negative" if points.startswith("-") else "neutral"

        rows.append(
            f'<li><span class="score-points score-{point_class}">{html.escape(points)}</span> '
            f'<span>{html.escape(label)}</span></li>'
        )

    return "<ul class=\"score-breakdown\">" + "".join(rows) + "</ul>"


def table_html(title: str, items: list[dict], limit: int | None = None) -> str:
    display_items = items if limit is None else items[:limit]
    rows = []

    for item in display_items:
        ticket_id = item["ticket_id"]
        tier_class, tier_label = priority_tier(item)
        reasons = reason_badges(item["reasons"])
        breakdown = score_breakdown(item["reasons"])
        context = html.escape(copy_context(item), quote=True)

        rows.append(f"""
        <tr class="ticket-row tier-{html.escape(tier_class)}" data-ticket="{html.escape(ticket_id)}">
          <td class="expand" data-label="Details">
            <button type="button" class="expand-button" aria-label="Toggle details" data-ticket="{html.escape(ticket_id)}">▶</button>
          </td>
          <td class="score" data-label="Score">{item["score"]}</td>
          <td data-label="Tier"><span class="tier-label tier-label-{html.escape(tier_class)}">{html.escape(tier_label)}</span></td>
          <td data-label="Ticket"><a href="{html.escape(trac_url(ticket_id))}" target="_blank">#{html.escape(ticket_id)}</a></td>
          <td data-label="Summary">{html.escape(item_summary(item))}</td>

        </tr>
        <tr class="tray-row" data-tray="{html.escape(ticket_id)}">
          <td colspan="5">
            <div class="tray">
              <h3>Ticket #{html.escape(ticket_id)}</h3>
              <p><strong>{html.escape(item_summary(item))}</strong></p>

              <div class="tray-section tray-workspace">
                <div>
                  <h4>Tools</h4>
                  <div class="tools">
                    <a class="button-link" href="{html.escape(trac_url(ticket_id))}" target="_blank">Open Trac</a>
                    <button type="button" class="copy-button" data-context="{context}">Copy Details</button>
                  </div>
                </div>

                <div>
                  <h4>Decision</h4>
                  <div class="actions">{action_form(ticket_id)}</div>
                </div>
              </div>
              <div class="tray-section">
                <h4>Ranking signals</h4>
                <div class="tray-reasons">{reasons}</div>
              </div>
              <div class="tray-section">
                <h4>Score breakdown</h4>
                {breakdown}
                <p class="score-total">Final score: <strong>{item["score"]}</strong></p>
              </div>
            </div>
          </td>
        </tr>
        """)

    if not rows:
        rows.append("""
        <tr>
          <td colspan="5" class="empty">No tickets in this section.</td>
        </tr>
        """)

    return f"""
    <section>
      <h2>{html.escape(title)} <span>{len(items)}</span></h2>
      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th></th>
              <th>Score</th>
              <th>Tier</th>
              <th>Ticket</th>
              <th>Summary</th>

            </tr>
          </thead>
          <tbody>
            {''.join(rows)}
          </tbody>
        </table>
      </div>
    </section>
    """


def page_html(message: str = "") -> str:
    ranked, duplicate_sources, summary = collect_items()
    groups = group_items(ranked)

    message_html = f'<div class="notice">{html.escape(message)}</div>' if message else ""
    immediate_count = sum(1 for item in groups["priority"] if priority_tier(item)[0] == "immediate")
    strong_count = sum(1 for item in groups["priority"] if priority_tier(item)[0] == "strong")
    watching_count = sum(1 for item in groups["top"] if priority_tier(item)[0] == "watching")

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>WP Core Radar Admin</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <style>
    body {{
      font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      margin: 0;
      background: #f6f7f7;
      color: #1d2327;
    }}
    header {{
      padding: 28px 32px;
      background: #1d2327;
      color: #fff;
    }}
    header h1 {{
      margin: 0 0 6px;
    }}
    header p {{
      margin: 0;
      color: #c3c4c7;
    }}
    main {{
      padding: 24px 32px 48px;
    }}
    .notice {{
      background: #edfaef;
      border: 1px solid #68de7c;
      padding: 12px 14px;
      border-radius: 8px;
      margin-bottom: 18px;
    }}
    .summary {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
      gap: 14px;
      margin-bottom: 24px;
    }}
    .card {{
      background: white;
      border: 1px solid #dcdcde;
      border-radius: 8px;
      padding: 14px;
    }}
    .card strong {{
      display: block;
      font-size: 26px;
      margin-bottom: 4px;
    }}
    .card-blue {{ border-left: 6px solid #2563eb; }}
    .card-purple {{ border-left: 6px solid #7c3aed; }}
    .card-amber {{ border-left: 6px solid #d97706; }}

    section {{
      margin-top: 32px;
    }}
    h2 {{
      display: flex;
      gap: 8px;
      align-items: baseline;
    }}
    h2 span {{
      font-size: 14px;
      color: #646970;
      font-weight: 500;
    }}
    .table-wrap {{
      overflow-x: auto;
      background: white;
      border: 1px solid #dcdcde;
      border-radius: 8px;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 13px;
    }}
    th, td {{
      padding: 8px 10px;
      border-bottom: 1px solid #f0f0f1;
      text-align: left;
      vertical-align: top;
    }}
    th {{
      background: #f0f0f1;
      white-space: nowrap;
    }}
    tr.tier-immediate {{ border-left: 6px solid #2563eb; }}
    tr.tier-strong {{ border-left: 6px solid #7c3aed; }}
    tr.tier-watching {{ border-left: 6px solid #d97706; }}
    tr.tier-standard {{ border-left: 6px solid transparent; }}

    .expand {{
      width: 36px;
      text-align: center;
    }}
    .expand-button {{
      background: transparent;
      color: #646970;
      border: 0;
      cursor: pointer;
      font-size: 16px;
      padding: 4px;
    }}
    .expand-button:hover {{
      color: #1d2327;
    }}
    .tray-row {{
      display: none;
      border-left: 6px solid #dcdcde;
    }}
    .tray-row.is-open {{
      display: table-row;
    }}
    .tray-row td {{
      background: #fbfbfc;
      padding: 0;
    }}
    .tray {{
      padding: 18px 22px;
      border-top: 1px solid #f0f0f1;
    }}
    .tray h3 {{
      margin: 0 0 8px;
    }}
    .tray p {{
      margin: 0 0 8px;
    }}
    .tray-section {{
      margin-top: 14px;
    }}
    .tray-section h4 {{
      margin: 0 0 8px;
      font-size: 13px;
      text-transform: uppercase;
      letter-spacing: 0.03em;
      color: #646970;
    }}
    .tray-reasons {{
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
    }}
    .tray-workspace {{
      display: grid;
      grid-template-columns: minmax(160px, 220px) minmax(260px, 1fr);
      gap: 24px;
      align-items: start;
      padding: 14px;
      background: #fff;
      border: 1px solid #dcdcde;
      border-radius: 8px;
    }}
    .score-breakdown {{
      list-style: none;
      padding: 0;
      margin: 0;
      display: grid;
      gap: 6px;
    }}
    .score-breakdown li {{
      display: flex;
      gap: 8px;
      align-items: baseline;
    }}
    .score-points {{
      display: inline-block;
      min-width: 42px;
      font-weight: 800;
      font-variant-numeric: tabular-nums;
    }}
    .score-positive {{
      color: #008a20;
    }}
    .score-negative {{
      color: #b32d2e;
    }}
    .score-neutral {{
      color: #646970;
    }}
    .score-total {{
      margin-top: 10px;
    }}
    .score {{
      font-size: 18px;
      font-weight: 700;
    }}
    .tier-label {{
      display: inline-block;
      border-radius: 999px;
      padding: 4px 8px;
      font-size: 12px;
      font-weight: 700;
      white-space: nowrap;
    }}
    .tier-label-immediate {{
      background: #dbeafe;
      color: #1d4ed8;
    }}
    .tier-label-strong {{
      background: #ede9fe;
      color: #6d28d9;
    }}
    .tier-label-watching {{
      background: #fef3c7;
      color: #92400e;
    }}
    .tier-label-standard {{
      background: #f3f4f6;
      color: #4b5563;
    }}
    .reasons {{
      min-width: 220px;
    }}
    .reason-badge {{
      display: inline-block;
      border-radius: 999px;
      padding: 4px 7px;
      margin: 0 4px 4px 0;
      font-size: 12px;
      font-weight: 700;
      white-space: nowrap;
      background: #f3f4f6;
      color: #4b5563;
    }}
    .reason-patch {{ background: #dbeafe; color: #1d4ed8; }}
    .reason-testing {{ background: #dcfce7; color: #166534; }}
    .reason-first {{ background: #fef3c7; color: #92400e; }}
    .reason-feedback {{ background: #ede9fe; color: #6d28d9; }}
    .reason-owner {{ background: #e0f2fe; color: #075985; }}
    .reason-recent {{ background: #ccfbf1; color: #115e59; }}
    .reason-component {{ background: #fce7f3; color: #9d174d; }}

    a {{
      color: #2271b1;
      font-weight: 700;
    }}
    form {{
      display: grid;
      grid-template-columns: minmax(180px, 1fr);
      gap: 8px;
      align-items: center;
      min-width: 260px;
    }}
    .decision-form.has-decision {{
      grid-template-columns: minmax(180px, 1fr);
    }}
    input[type="text"],
    select {{
      width: 100%;
      box-sizing: border-box;
      padding: 8px;
      border: 1px solid #c3c4c7;
      border-radius: 6px;
      background: white;
    }}
    button, .button-link {{
      border: 0;
      border-radius: 6px;
      padding: 7px 9px;
      cursor: pointer;
      font-weight: 700;
      background: #2271b1;
      color: white;
      text-decoration: none;
      display: inline-block;
      font-size: 13px;
    }}
    .decision-form button {{
      background: #2271b1;
    }}
    .decision-form button:disabled {{
      background: #c3c4c7;
      cursor: not-allowed;
    }}
    .conditional-field {{
      display: none;
    }}
    .decision-form.has-decision .conditional-field {{
      display: block;
    }}
    .copy-button {{ background: #7c3aed; }}
    .tools {{
      display: grid;
      grid-template-columns: 1fr;
      gap: 6px;
      min-width: 120px;
      max-width: 140px;
    }}
    .tools .button-link,
    .tools .copy-button {{
      width: 100%;
      box-sizing: border-box;
      text-align: center;
    }}
    .empty {{
      color: #646970;
      font-style: italic;
    }}
    @media (max-width: 900px) {{
      header, main {{
        padding-left: 18px;
        padding-right: 18px;
      }}
      .summary {{
        grid-template-columns: repeat(2, minmax(0, 1fr));
      }}
      table, thead, tbody, th, td, tr {{
        display: block;
      }}
      thead {{
        display: none;
      }}
      tr {{
        padding: 14px;
      }}
      td {{
        border: 0;
        padding: 6px 0;
      }}
      td::before {{
        content: attr(data-label);
        display: block;
        color: #646970;
        font-size: 12px;
        font-weight: 700;
        text-transform: uppercase;
        margin-bottom: 2px;
      }}
      form {{
        display: grid;
        grid-template-columns: 1fr;
      }}
    }}
  </style>
</head>
<body>
  <header>
    <h1>WP Core Radar Admin</h1>
    <p>Private review console. Decisions are written to data/reviews/reviews.csv.</p>
  </header>
  <main>
    {message_html}

    <div class="summary">
      <div class="card"><strong>{len(ranked)}</strong>Unique tickets</div>
      <div class="card"><strong>{len(groups["priority"])}</strong>Priority targets</div>
      <div class="card card-blue"><strong>{immediate_count}</strong>Immediate Review</div>
      <div class="card card-purple"><strong>{strong_count}</strong>Strong Candidates</div>
      <div class="card card-amber"><strong>{watching_count}</strong>Worth Watching</div>
      <div class="card"><strong>{len(groups["rejected"])}</strong>Rejected</div>
    </div>

    {table_html("Priority Targets", groups["priority"])}
    {table_html("Top Opportunities", groups["top"], limit=50)}
    {table_html("Shortlisted", groups["shortlist"])}
    {table_html("Watching", groups["watch"])}
    {table_html("Completed / Acted On", groups["completed"])}
    {table_html("Rejected", groups["rejected"])}
  </main>

  <script>
    document.addEventListener("change", function(event) {{
      const select = event.target.closest("select[name='status']");
      if (!select) return;

      const form = select.closest("form");
      const save = form.querySelector("button[type='submit']");

      if (select.value) {{
        form.classList.add("has-decision");
        save.disabled = false;
      }} else {{
        form.classList.remove("has-decision");
        save.disabled = true;
      }}
    }});

    document.addEventListener("click", function(event) {{
      const expandButton = event.target.closest(".expand-button");
      if (!expandButton) return;

      const row = expandButton.closest("tr");
      const tray = row ? row.nextElementSibling : null;

      if (!tray || !tray.classList.contains("tray-row")) return;

      const isOpen = tray.classList.toggle("is-open");
      expandButton.textContent = isOpen ? "▼" : "▶";
    }});

    document.addEventListener("click", async function(event) {{
      const button = event.target.closest(".copy-button");
      if (!button) return;

      try {{
        await navigator.clipboard.writeText(button.dataset.context || "");
        const original = button.textContent;
        button.textContent = "Copied";
        setTimeout(() => button.textContent = original, 1400);
      }} catch (error) {{
        alert("Could not copy review context.");
      }}
    }});
  </script>
</body>
</html>
"""


class Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        parsed = urlparse(self.path)

        if parsed.path not in {"/", "/radar/admin", "/radar/admin/"}:
            self.send_error(404)
            return

        self.respond(page_html())

    def do_POST(self) -> None:
        parsed = urlparse(self.path)

        if parsed.path not in {"/review", "/radar/admin/review"}:
            self.send_error(404)
            return

        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length).decode("utf-8")
        data = parse_qs(body)

        ticket = data.get("ticket", [""])[0]
        status = data.get("status", [""])[0]
        reason = data.get("reason", [""])[0] or "Reviewed from admin console"

        if not ticket or not status:
            self.respond(page_html("Missing ticket or status."))
            return

        run_command([sys.executable, "scripts/review-ticket.py", ticket, status, reason])
        run_command([sys.executable, "scripts/generate-report.py"])
        run_command([sys.executable, "scripts/generate-dashboard.py"])

        self.respond(page_html(f"Recorded #{ticket} as {status}: {reason}"))

    def respond(self, content: str) -> None:
        encoded = content.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)


def main() -> int:
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"WP Core Radar Admin running at http://{HOST}:{PORT}")
    print(f"Admin route also available at http://{HOST}:{PORT}/radar/admin")
    print("Press Ctrl+C to stop.")
    server.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
