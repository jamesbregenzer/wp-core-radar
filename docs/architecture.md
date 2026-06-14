# WP Core Radar Architecture

WP Core Radar is a deterministic, human-in-the-loop contribution intelligence workflow for WordPress Core.

## Pipeline

```text
WordPress Trac
  ↓
Browser-assisted CSV fetcher
  ↓
Archived raw datasets
  ↓
Automatic dataset discovery
  ↓
Deterministic scoring
  ↓
Unified opportunity report
  ↓
Human review and local testing
  ↓
Manual Trac contribution
  ↓
Outcome tracking
```

## Guardrails

Radar never auto-comments on Trac and never attempts to automate contribution activity. It identifies opportunities, explains why they ranked, and leaves contribution decisions to a human reviewer.

## Phase 2 additions

Phase 2 adds multi-query support and unified reporting:

- `config/queries.json` defines enabled Trac query tracks.
- `scripts/run-radar.py` loops through enabled queries.
- `scripts/discover-datasets.py` inventories archived CSV files.
- `scripts/generate-report.py` discovers all datasets and writes a unified ranked report.
- `scripts/radarlib.py` centralizes parsing, scoring, outcome loading, and report helpers.

## Dataset conventions

Preferred archive convention:

```text
data/raw/<source>/<YYYY-MM-DD>/<query_slug>.csv
```

The discovery layer is intentionally tolerant. If older imports used `query.csv`, Radar still attempts to infer the source from the path.

## Scoring principles

Scoring is deterministic and explainable. Each ranked ticket includes the major score reasons so the report is useful as a portfolio artifact and as a real contribution workflow tool.

Initial scoring includes:

- Query/track priority
- Has patch
- Needs testing
- Dev feedback
- Reporter feedback
- Good first bug
- Preferred components such as Media
- Accessibility signals
- Recent activity
- Ticket age
- Comment count
- Known outcomes

## Human workflow

The report's recommended next step is always:

1. Open the Trac ticket.
2. Verify the current ticket state.
3. Test locally if appropriate.
4. Decide whether to comment manually.
5. Record contribution outcomes in `data/outcomes/outcomes.csv` and review decisions in `data/reviews/reviews.json`.

## Public and admin boundaries

The public dashboard is static and published under `/radar/`. The admin workflow is intentionally a separate, authenticated path for future deployment. Admin write-back should remain narrowly scoped to review metadata in `data/reviews/reviews.json`; it should not become a general repository editor.
