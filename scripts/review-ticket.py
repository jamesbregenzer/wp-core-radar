#!/usr/bin/env python3
"""Record a human review decision for a WordPress Core ticket."""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone

from radarlib import VALID_REVIEW_STATUSES, load_reviews, normalize_ticket_id, save_reviews


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("ticket", help="WordPress Trac ticket ID or URL.")
    parser.add_argument("status", choices=sorted(VALID_REVIEW_STATUSES), help="Review decision status.")
    parser.add_argument("reason", help="Short reason or note shown in review metadata.")
    parser.add_argument("notes", nargs="?", default="", help="Optional longer review notes.")
    args = parser.parse_args()

    ticket = normalize_ticket_id(args.ticket)
    if not ticket:
        print("Invalid ticket ID.", file=sys.stderr)
        return 1

    reviews = load_reviews()
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    reviews[ticket] = {
        "status": args.status,
        "reason": args.reason.strip(),
        "notes": args.notes.strip(),
        "updated_at": now,
    }

    save_reviews(reviews)
    print(f"Recorded review for #{ticket}: {args.status} — {args.reason}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
