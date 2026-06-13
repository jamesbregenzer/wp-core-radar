#!/usr/bin/env python3
"""Run the WP Core Radar collection and reporting pipeline."""

from __future__ import annotations

import argparse
import subprocess
import sys

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
                    print(message, file=sys.stderr)
                    continue

                print(message, file=sys.stderr)
                return code

    print("\n=== Generating Markdown report ===")
    code = run([sys.executable, "scripts/generate-report.py"])
    if code != 0:
        return code

    print("\n=== Generating HTML dashboard ===")
    code = run([sys.executable, "scripts/generate-dashboard.py"])
    if code != 0:
        return code

    print("\nRadar run complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
