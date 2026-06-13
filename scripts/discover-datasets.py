#!/usr/bin/env python3
"""List discovered WP Core Radar CSV datasets."""

from __future__ import annotations

from radarlib import discover_datasets


def main() -> int:
    datasets = discover_datasets()
    if not datasets:
        print("No datasets found under data/raw.")
        return 0

    print("Discovered datasets:\n")
    for dataset in datasets:
        print(f"- {dataset.query_slug}: {dataset.row_count} rows | {dataset.collected_date} | {dataset.path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
