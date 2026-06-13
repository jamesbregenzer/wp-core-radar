#!/usr/bin/env python3
"""Local admin review console for WP Core Radar."""

from __future__ import annotations

import html
import importlib.util
import subprocess
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from radarlib import ROOT, trac_url

dashboard_path = Path(__file__).resolve().parent / "generate-dashboard.py"
spec = importlib.util.spec_from_file_location("generate_dashboard", dashboard_path)
generate_dashboard = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(generate_dashboard)

collect_items = generate_dashboard.collect_items
group_items = generate_dashboard.group_items

HOST = "127.0.0.1"
PORT = 8765


def run_command(command: list[str]) -> None:
    subprocess.run(command, cwd=ROOT, check=False)


def action_form(ticket_id: str) -> str:
    safe_ticket = html.escape(ticket_id)

    return f"""
    <form method="post" action="/review">
      <input type="hidden" name="ticket" value="{safe_ticket}">
      <input type="text" name="reason" placeholder="Reason / note">
      <button name="status" value="shortlist">Shortlist</button>
      <button name="status" value="watch">Watch</button>
      <button name="status" value="reject">Reject</button>
      <button name="status" value="tested">Tested</button>
      <button name="status" value="commented">Commented</button>
    </form>
    """


def item_summary(item: dict) -> str:
    row = item["row"]
    return row.get("summary") or row.get("Summary") or "Untitled ticket"


def item_review_label(item: dict) -> str:
    review = item.get("review") or {}
    status = review.get("status", "")
    reason = review.get("reason", "")

    if not status:
        return ""

    label = f"<strong>{html.escape(status)}</strong>"
    if reason:
        label += f"<br><span>{html.escape(reason)}</span>"

    return label


def table_html(title: str, items: list[dict], limit: int | None = None) -> str:
    display_items = items if limit is None else items[:limit]

    rows = []

    for item in display_items:
        ticket_id = item["ticket_id"]
        reasons = ", ".join(item["reasons"][:5])

        rows.append(f"""
        <tr>
          <td class="score">{item["score"]}</td>
          <td><a href="{html.escape(trac_url(ticket_id))}" target="_blank">#{html.escape(ticket_id)}</a></td>
          <td>{html.escape(item_summary(item))}</td>
          <td>{html.escape(reasons)}</td>
          <td>{item_review_label(item)}</td>
          <td class="actions">{action_form(ticket_id)}</td>
        </tr>
        """)

    if not rows:
        rows.append("""
        <tr>
          <td colspan="6" class="empty">No tickets in this section.</td>
        </tr>
        """)

    return f"""
    <section>
      <h2>{html.escape(title)} <span>{len(items)}</span></h2>
      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Score</th>
              <th>Ticket</th>
              <th>Summary</th>
              <th>Why Ranked</th>
              <th>Review</th>
              <th>Action</th>
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
      font-size: 14px;
    }}
    th, td {{
      padding: 10px 12px;
      border-bottom: 1px solid #f0f0f1;
      text-align: left;
      vertical-align: top;
    }}
    th {{
      background: #f0f0f1;
    }}
    .score {{
      font-size: 20px;
      font-weight: 700;
    }}
    a {{
      color: #2271b1;
      font-weight: 700;
    }}
    form {{
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
    }}
    input[type="text"] {{
      min-width: 220px;
      padding: 8px;
      border: 1px solid #c3c4c7;
      border-radius: 6px;
    }}
    button {{
      border: 0;
      border-radius: 6px;
      padding: 8px 10px;
      cursor: pointer;
      font-weight: 700;
      background: #2271b1;
      color: white;
    }}
    button[value="reject"] {{
      background: #b32d2e;
    }}
    button[value="watch"] {{
      background: #996800;
    }}
    button[value="tested"],
    button[value="commented"] {{
      background: #008a20;
    }}
    .empty {{
      color: #646970;
      font-style: italic;
    }}
    @media (max-width: 800px) {{
      header, main {{
        padding-left: 18px;
        padding-right: 18px;
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
      form {{
        display: grid;
      }}
      input[type="text"] {{
        min-width: 0;
        width: 100%;
        box-sizing: border-box;
      }}
    }}
  </style>
</head>
<body>
  <header>
    <h1>WP Core Radar Admin</h1>
    <p>Private local review console. Decisions are written to data/reviews/reviews.csv.</p>
  </header>
  <main>
    {message_html}

    <div class="summary">
      <div class="card"><strong>{len(ranked)}</strong>Unique tickets</div>
      <div class="card"><strong>{len(groups["top"])}</strong>Top opportunities</div>
      <div class="card"><strong>{len(groups["shortlist"])}</strong>Shortlisted</div>
      <div class="card"><strong>{len(groups["watch"])}</strong>Watching</div>
      <div class="card"><strong>{len(groups["completed"])}</strong>Completed</div>
      <div class="card"><strong>{len(groups["rejected"])}</strong>Rejected</div>
    </div>

    {table_html("Top Opportunities", groups["top"], limit=50)}
    {table_html("Shortlisted", groups["shortlist"])}
    {table_html("Watching", groups["watch"])}
    {table_html("Completed / Acted On", groups["completed"])}
    {table_html("Rejected", groups["rejected"])}
  </main>
</body>
</html>
"""


class Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        self.respond(page_html())

    def do_POST(self) -> None:
        parsed = urlparse(self.path)

        if parsed.path != "/review":
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
    print("Press Ctrl+C to stop.")
    server.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
