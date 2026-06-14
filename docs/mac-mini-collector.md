# Mac Mini Collector

The collector is designed to run from the local Mac Mini environment where browser-assisted Trac CSV downloads are reliable.

## Why browser-assisted collection exists

WordPress Trac CSV exports can be easiest to collect through a normal browser session. The collector opens Firefox, waits for `query.csv` to download, imports it into the repository archive, and then closes Firefox.

## Collection command

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

## Archive convention

Imported CSV files are archived under:

```text
data/raw/manual/YYYY-MM-DD/<query_slug>.csv
```

This makes the dataset history inspectable and lets reports be regenerated from committed raw data.
