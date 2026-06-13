#!/usr/bin/env python3

import csv
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REVIEWS_FILE = ROOT / "data" / "reviews" / "reviews.csv"

VALID_STATUSES = {
    "new",
    "shortlist",
    "watch",
    "reject",
    "tested",
    "commented",
    "props",
    "committed",
}

def usage():
    print("Usage:")
    print("  python3 scripts/review-ticket.py <ticket> <status> <reason> [notes]")
    print("")
    print("Statuses:")
    print("  " + ", ".join(sorted(VALID_STATUSES)))
    sys.exit(1)

def load_reviews():
    if not REVIEWS_FILE.exists():
        return []

    with REVIEWS_FILE.open(newline="") as file:
        return list(csv.DictReader(file))

def save_reviews(rows):
    REVIEWS_FILE.parent.mkdir(parents=True, exist_ok=True)

    with REVIEWS_FILE.open("w", newline="") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=["ticket", "status", "reason", "notes", "updated_at"],
        )
        writer.writeheader()
        writer.writerows(rows)

def main():
    if len(sys.argv) < 4:
        usage()

    ticket = sys.argv[1].strip()
    status = sys.argv[2].strip().lower()
    reason = sys.argv[3].strip()
    notes = sys.argv[4].strip() if len(sys.argv) > 4 else ""

    if status not in VALID_STATUSES:
        print(f"Invalid status: {status}")
        usage()

    rows = load_reviews()
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    updated = False
    for row in rows:
        if row["ticket"] == ticket:
            row["status"] = status
            row["reason"] = reason
            row["notes"] = notes
            row["updated_at"] = now
            updated = True
            break

    if not updated:
        rows.append({
            "ticket": ticket,
            "status": status,
            "reason": reason,
            "notes": notes,
            "updated_at": now,
        })

    save_reviews(rows)

    print(f"Recorded review for #{ticket}: {status} — {reason}")

if __name__ == "__main__":
    main()
