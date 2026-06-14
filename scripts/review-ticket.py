#!/usr/bin/env python3
"""Record a human review decision for a WordPress Core ticket."""

from __future__ import annotations

import sys
from datetime import datetime, timezone

from radarlib import load_reviews, normalize_ticket_id, save_reviews

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


def usage() -> None:
    print("Usage:")
    print("  python3 scripts/review-ticket.py <ticket> <status> <reason> [notes]")
    print("")
    print("Statuses:")
    print("  " + ", ".join(sorted(VALID_STATUSES)))
    raise SystemExit(1)


def main() -> int:
    if len(sys.argv) < 4:
        usage()

    ticket = normalize_ticket_id(sys.argv[1].strip())
    status = sys.argv[2].strip().lower()
    reason = sys.argv[3].strip()
    notes = sys.argv[4].strip() if len(sys.argv) > 4 else ""

    if not ticket:
        print("Invalid ticket ID.")
        usage()

    if status not in VALID_STATUSES:
        print(f"Invalid status: {status}")
        usage()

    reviews = load_reviews()
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    reviews[ticket] = {
        "status": status,
        "reason": reason,
        "notes": notes,
        "updated_at": now,
    }

    save_reviews(reviews)

    print(f"Recorded review for #{ticket}: {status} — {reason}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
