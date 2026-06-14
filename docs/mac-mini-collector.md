# Mac Mini Collector

The Mac Mini is an intentional part of the WP Core Radar architecture. It is the collection/build runner because the Trac CSV export workflow is most reliable from the local browser/network environment.

## Responsibilities

The Mac Mini is responsible for:

1. Opening configured WordPress Trac CSV queries in Firefox.
2. Waiting for `query.csv` to finish downloading.
3. Importing the CSV into `data/raw/manual/YYYY-MM-DD/<query_slug>.csv`.
4. Regenerating the Markdown report and public dashboard.
5. Committing and pushing changed data/report files when updates are ready.

GitHub and Cloudflare are responsible for source control and static hosting after the Mac Mini pushes changes.

## Why GitHub Actions does not collect data

GitHub-hosted runners do not have the same local browser/network context as the Mac Mini. Because the Trac export flow depends on that environment, normal GitHub Actions should not replace the collector.

GitHub Actions may be useful later for checks after the Mac Mini pushes, but not as the primary collector.

## Main Commands

Run all enabled query tracks:

```bash
python3 scripts/run-radar.py
```

Run one query track:

```bash
python3 scripts/run-radar.py --query general_needs_testing
```

Skip collection and rebuild reports only:

```bash
python3 scripts/run-radar.py --skip-fetch
```

Continue collecting remaining tracks if one browser fetch fails:

```bash
python3 scripts/run-radar.py --continue-on-error
```

## Archive Convention

Imported CSV files are archived under:

```text
data/raw/manual/YYYY-MM-DD/<query_slug>.csv
```

This makes dataset history inspectable and lets reports be regenerated from committed raw data.

## Scheduling

No scheduler should be assumed unless it exists in the Mac Mini environment. The intended future setup is a macOS LaunchAgent that runs `scripts/run-radar.py` on a predictable cadence.

The LaunchAgent should call a small wrapper script rather than embedding complex logic directly in a `.plist` file.
