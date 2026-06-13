from pathlib import Path
from datetime import datetime
import csv

ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "data" / "raw" / "manual" / "2026-06-13" / "media_has_patch.csv"
REPORT = ROOT / "reports" / "latest.md"

def score_ticket(row):
    score = 0
    reasons = []

    keywords = row.get("Keywords", "").lower()
    status = row.get("Status", "").lower()
    ticket_type = row.get("Type", "").lower()
    priority = row.get("Priority", "").lower()
    owner = row.get("Owner", "").strip()

    if "has-patch" in keywords:
        score += 30
        reasons.append("+30 has-patch")

    if "needs-testing" in keywords:
        score += 30
        reasons.append("+30 needs-testing")

    if "dev-feedback" in keywords:
        score += 25
        reasons.append("+25 dev-feedback")

    if "reporter-feedback" in keywords:
        score += 15
        reasons.append("+15 reporter-feedback")

    if "has-screenshots" in keywords:
        score += 10
        reasons.append("+10 has-screenshots")

    if "has-unit-tests" in keywords:
        score += 10
        reasons.append("+10 has-unit-tests")

    if status == "assigned":
        score += 10
        reasons.append("+10 assigned status")

    if ticket_type == "feature request":
        score -= 10
        reasons.append("-10 feature request")

    if owner:
        score -= 5
        reasons.append("-5 owner assigned")

    if priority == "high":
        score += 20
        reasons.append("+20 high priority")

    if priority == "low":
        score -= 10
        reasons.append("-10 low priority")

    return score, reasons

def main():
    with INPUT.open(newline="") as f:
        rows = list(csv.DictReader(f))

    scored = []
    for row in rows:
        score, reasons = score_ticket(row)
        scored.append((score, row, reasons))

    scored.sort(key=lambda item: item[0], reverse=True)

    lines = []
    lines.append("# WP Core Radar — Latest Report")
    lines.append("")
    lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("")
    lines.append(f"Source: `{INPUT.relative_to(ROOT)}`")
    lines.append("")
    lines.append("## Top Opportunities")
    lines.append("")

    for score, row, reasons in scored[:10]:
        ticket = row.get("Ticket", "").lstrip("\ufeff")
        summary = row.get("Summary", "")
        status = row.get("Status", "")
        ticket_type = row.get("Type", "")
        priority = row.get("Priority", "")
        keywords = row.get("Keywords", "")

        lines.append(f"### Score {score} — #{ticket}: {summary}")
        lines.append("")
        lines.append(f"- Status: `{status}`")
        lines.append(f"- Type: `{ticket_type}`")
        lines.append(f"- Priority: `{priority}`")
        lines.append(f"- Keywords: `{keywords}`")
        lines.append(f"- Ticket: https://core.trac.wordpress.org/ticket/{ticket}")
        lines.append("")
        lines.append("Reasons:")
        for reason in reasons:
            lines.append(f"- {reason}")
        lines.append("")

    REPORT.write_text("\n".join(lines))
    print(f"Wrote {REPORT.relative_to(ROOT)}")

if __name__ == "__main__":
    main()
