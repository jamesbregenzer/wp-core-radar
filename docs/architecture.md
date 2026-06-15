# WP Core Radar Architecture

WP Core Radar is a deterministic, human-in-the-loop contribution intelligence workflow for WordPress Core.

## System Overview

```text
WordPress Trac
  ↓
Mac Mini browser-assisted collector
  ↓
Archived raw CSV datasets
  ↓
Deterministic scoring and grouping
  ↓
Markdown report + public dashboard + admin data export
  ↓
GitHub repository
  ↓
Cloudflare Pages static origin
  ↓
Cloudflare Worker routing and protected admin UI
```

The Mac Mini remains central because the CSV collection step depends on the local browser/network environment. GitHub is the source of truth after the Mac Mini pushes generated files. Cloudflare Pages hosts the static artifacts, and the Cloudflare Worker provides path-based routing plus the protected admin review console.

## Public / Private Split

```text
/radar/          Public, static dashboard
/radar/admin/    Protected Worker-rendered admin UI
```

The public dashboard is read-only. It is safe to publish because it contains scored ticket recommendations, public Trac links, and constrained review metadata.

The admin route is not part of the static dashboard. It is rendered by the Cloudflare Worker, requires authentication, reads the generated admin data JSON, and writes only to `data/reviews/reviews.json` through the GitHub API.

Admin write-back should remain narrowly scoped to `data/reviews/reviews.json`. It should not become a general repository editor.

## Data Flow

1. Query tracks are configured in `config/queries.json`.
2. `scripts/browser-fetch.py` opens each configured query in Firefox and waits for `query.csv`.
3. `scripts/import-download.py` archives the downloaded CSV under `data/raw/manual/YYYY-MM-DD/`.
4. `scripts/radarlib.py` discovers datasets, normalizes ticket rows, loads outcomes/reviews, scores tickets, and groups workflow sections.
5. `scripts/generate-report.py` writes `reports/latest.md` and a dated report.
6. `scripts/generate-dashboard.py` writes `docs/radar/index.html` and `docs/radar/admin-data.json`.
7. The Mac Mini commits and pushes changed data, docs, and report files to GitHub.
8. Cloudflare Pages deploys the static dashboard output.
9. The Cloudflare Worker routes `/radar/` to the Pages origin and handles `/radar/admin/` directly.

## Worker Routing Model

The current routing model supports the longer-term goal of using `james.bregenzer.dev` as a portfolio-style domain with project subdirectories.

```text
james.bregenzer.dev/             Main personal site or landing page
james.bregenzer.dev/radar/       WP Core Radar public dashboard
james.bregenzer.dev/radar/admin/ WP Core Radar protected admin console
```

Additional projects can later be mounted at their own path prefixes and proxied to separate Cloudflare Pages or GitHub Pages origins.

## Shared Logic

Core parsing, scoring, grouping, review status handling, and presentation labels belong in `scripts/radarlib.py`.

Script-specific files should focus on their output format:

- `generate-dashboard.py` renders public HTML and admin data JSON.
- `generate-report.py` renders Markdown.
- `review-server.py` renders the local development admin console.
- `run-radar.py` orchestrates collection and generation.

## Guardrails

Radar never auto-comments on Trac and never attempts to automate contribution activity. It identifies opportunities, explains why they ranked, and leaves contribution decisions to a human reviewer.

## Dataset Conventions

Preferred archive convention:

```text
data/raw/<source>/<YYYY-MM-DD>/<query_slug>.csv
```

Current browser-assisted imports use:

```text
data/raw/manual/YYYY-MM-DD/<query_slug>.csv
```

The discovery layer remains tolerant of older archived paths, but new imports should follow the current convention.
