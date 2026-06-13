#!/usr/bin/env python3
"""Run WP Core Radar collection and report generation.

By default this runs every enabled query in config/queries.json by delegating to
scripts/browser-fetch.py <query_slug>, then generates a unified report.

Use --skip-fetch to regenerate reports from existing data only.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from radarlib import ROOT, load_queries


def run(command: list[str]) -> int:
    print("$ " + " ".join(command))
    completed = subprocess.run(command, cwd=ROOT)
    return completed.returncode


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--query", action="append", help="Run only this query slug. Can be used multiple times.")
    parser.add_argument("--skip-fetch", action="store_true", help="Skip browser fetching and only generate reports.")
    parser.add_argument("--continue-on-error", action="store_true", help="Continue if an individual query fetch fails.")
    args = parser.parse_args()

    queries = load_queries()
    if args.query:
        wanted = set(args.query)
        queries = [q for q in queries if q["slug"] in wanted]

    if not queries and not args.skip_fetch:
        print("No enabled queries found. Check config/queries.json.", file=sys.stderr)
        return 1

    if not args.skip_fetch:
        for query in queries:
            slug = query["slug"]
            print(f"\n=== Fetching {slug}: {query.get('name', slug)} ===")
            code = run([sys.executable, "scripts/browser-fetch.py", slug])
            if code != 0:
                message = f"Fetch failed for {slug} with exit code {code}."
                if args.continue_on_error:
                    print(message)
                    continue
                print(message, file=sys.stderr)
                return code

    print("\n=== Generating unified report ===")
    return run([sys.executable, "scripts/generate-report.py"])


if __name__ == "__main__":
    raise SystemExit(main())
