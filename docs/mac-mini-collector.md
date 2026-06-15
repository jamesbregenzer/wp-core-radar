# Mac Mini Collector

The Mac Mini is an intentional part of the WP Core Radar architecture. It is the collection/build runner because the Trac CSV export workflow is most reliable from the local browser/network environment.

## Responsibilities

The Mac Mini is responsible for:

1. Opening configured WordPress Trac CSV queries in Firefox.
2. Waiting for `query.csv` to finish downloading.
3. Importing the CSV into `data/raw/manual/YYYY-MM-DD/<query_slug>.csv`.
4. Regenerating the Markdown report, public dashboard, and admin data export.
5. Committing and pushing changed data/report/dashboard files to GitHub.

The Mac Mini creates `docs/radar/admin-data.json`, which the protected Worker admin console reads. It does not create, host, or authenticate the production `/radar/admin/` page. The scheduled run remains the production mechanism that reconciles review writes from GitHub with regenerated dashboard/admin data.

GitHub is the source of truth after the Mac Mini pushes changes. Cloudflare Pages deploys the public dashboard from the committed `docs/` output, and the Cloudflare Worker serves the protected admin UI.

## Why GitHub Actions does not collect data

GitHub-hosted runners do not have the same local browser/network context as the Mac Mini. Because the Trac export flow depends on that environment, normal GitHub Actions should not replace the collector.

GitHub Actions may still be useful for checks after the Mac Mini pushes, but not as the primary collector.

## Main commands

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

## Generated dashboard files

The dashboard generation step writes both the public dashboard and the data payload consumed by the protected Worker admin console:

```text
docs/radar/index.html
docs/radar/admin-data.json
```

The public dashboard includes a header link to `/radar/admin/`. The protected admin route itself is rendered by the Cloudflare Worker, not by the static Pages output.

## Scheduled runner

Scheduled collection should use the wrapper script:

```bash
scripts/run-scheduled-radar.sh
```

The wrapper intentionally keeps scheduling, Git synchronization, and publishing concerns outside the collector itself. It performs this sequence:

1. `git pull --rebase origin main`
2. `python3 scripts/run-radar.py`
3. `git add data docs reports`
4. Commit changed files with `Update radar data`
5. Push to `origin/main`

The local LaunchAgent should call the wrapper rather than embedding workflow logic directly in the `.plist` file.

## LaunchAgent cadence

The current recommended cadence is every six hours:

```xml
<key>StartInterval</key>
<integer>21600</integer>
```

Use `RunAtLoad` while testing so the job runs immediately after loading. After the job is confirmed stable, `RunAtLoad` can remain enabled or be removed depending on whether immediate catch-up behavior is desired after login/restart.

## Logs

The LaunchAgent writes logs to:

```text
logs/launchagent.out.log
logs/launchagent.err.log
```

Check them with:

```bash
tail -n 100 logs/launchagent.out.log
tail -n 100 logs/launchagent.err.log
```

## macOS privacy note

When the LaunchAgent runs outside Terminal, macOS privacy controls may prevent Python from reading files in `~/Downloads`, even when the same command works manually in Terminal.

If the log contains an error like:

```text
PermissionError: [Errno 1] Operation not permitted: '/Users/thor/Downloads/query.csv'
```

then grant Full Disk Access, or at minimum Files and Folders access for Downloads, to the Python executable used by the scheduled runner:

```text
/usr/local/opt/python@3.14/bin/python3.14
```

This is a macOS permission issue, not a repository or GitHub issue. The manual run can succeed because Terminal already has access, while the LaunchAgent process does not.

## Archive convention

Imported CSV files are archived under:

```text
data/raw/manual/YYYY-MM-DD/<query_slug>.csv
```

This makes dataset history inspectable and lets reports be regenerated from committed raw data.
