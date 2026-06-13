#!/usr/bin/env python3
"""Shared utilities for WP Core Radar.

The project intentionally stays deterministic and human-in-the-loop:
Radar collects, normalizes, scores, and reports. Humans decide what to test
or comment on in WordPress Trac.
"""

from __future__ import annotations

import csv
import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[1]
DATA_RAW = ROOT / "data" / "raw"
OUTCOMES_CSV = ROOT / "data" / "outcomes" / "outcomes.csv"
QUERIES_JSON = ROOT / "config" / "queries.json"
REPORTS_DIR = ROOT / "reports"

TICKET_ID_KEYS = ("id", "ticket", "Ticket", "ticket_id", "Ticket ID")
SUMMARY_KEYS = ("summary", "Summary")
COMPONENT_KEYS = ("component", "Component")
KEYWORDS_KEYS = ("keywords", "Keywords")
STATUS_KEYS = ("status", "Status")
MILESTONE_KEYS = ("milestone", "Milestone")
OWNER_KEYS = ("owner", "Owner")
MODIFIED_KEYS = ("modified", "Modified", "changetime", "Change Time")
CREATED_KEYS = ("created", "Created", "time", "Created Time")
COMMENTS_KEYS = ("comments", "Comments")


def first_value(row: dict[str, Any], keys: Iterable[str], default: str = "") -> str:
    for key in keys:
        if key in row and row[key] is not None:
            return str(row[key]).strip()
    return default


def normalize_ticket_id(value: str) -> str:
    match = re.search(r"\d+", value or "")
    return match.group(0) if match else ""


def parse_datetime(value: str) -> datetime | None:
    if not value:
        return None
    cleaned = value.strip().replace("Z", "+00:00")
    formats = (
        "%Y-%m-%d %H:%M:%S%z",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d",
        "%m/%d/%Y %H:%M:%S",
        "%m/%d/%Y",
    )
    for fmt in formats:
        try:
            parsed = datetime.strptime(cleaned, fmt)
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=timezone.utc)
            return parsed
        except ValueError:
            continue
    try:
        parsed = datetime.fromisoformat(cleaned)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed
    except ValueError:
        return None


def days_since(value: str, now: datetime | None = None) -> int | None:
    parsed = parse_datetime(value)
    if not parsed:
        return None
    now = now or datetime.now(timezone.utc)
    return max(0, (now - parsed.astimezone(timezone.utc)).days)


def load_queries(path: Path = QUERIES_JSON) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    payload = json.loads(path.read_text(encoding="utf-8"))
    return [q for q in payload.get("queries", []) if q.get("enabled", True)]


def load_outcomes(path: Path = OUTCOMES_CSV) -> dict[str, str]:
    outcomes: dict[str, str] = {}
    if not path.exists():
        return outcomes
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.reader(handle)
        for row in reader:
            if not row or row[0].strip().startswith("#"):
                continue
            ticket_id = normalize_ticket_id(row[0])
            outcome = row[1].strip().lower() if len(row) > 1 else ""
            if ticket_id and outcome:
                outcomes[ticket_id] = outcome
    return outcomes


def infer_query_slug(csv_path: Path) -> str:
    # Preferred convention: data/raw/<source>/<YYYY-MM-DD>/<query_slug>.csv
    stem = csv_path.stem
    if stem and stem.lower() not in {"query", "tickets", "trac"}:
        return stem

    # Fallback: use the closest non-date parent name.
    for parent in csv_path.parents:
        name = parent.name
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", name) and name not in {"raw", "data", "manual"}:
            return name
    return "unknown"


@dataclass(frozen=True)
class Dataset:
    path: Path
    query_slug: str
    collected_date: str
    row_count: int


def discover_datasets(raw_dir: Path = DATA_RAW) -> list[Dataset]:
    datasets: list[Dataset] = []
    for path in sorted(raw_dir.glob("**/*.csv")):
        try:
            with path.open(newline="", encoding="utf-8-sig") as handle:
                row_count = sum(1 for _ in csv.DictReader(handle))
        except Exception:
            row_count = 0
        date_match = re.search(r"\d{4}-\d{2}-\d{2}", str(path))
        collected_date = date_match.group(0) if date_match else "unknown-date"
        datasets.append(Dataset(path=path, query_slug=infer_query_slug(path), collected_date=collected_date, row_count=row_count))
    return datasets


def read_ticket_rows(dataset: Dataset) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with dataset.path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        for raw_row in reader:
            ticket_id = normalize_ticket_id(first_value(raw_row, TICKET_ID_KEYS))
            if not ticket_id:
                continue
            row = {k: (v or "").strip() for k, v in raw_row.items()}
            row["ticket_id"] = ticket_id
            row["query_slug"] = dataset.query_slug
            row["collected_date"] = dataset.collected_date
            row["source_file"] = str(dataset.path.relative_to(ROOT))
            rows.append(row)
    return rows


def score_ticket(row: dict[str, Any], query_meta: dict[str, Any], outcomes: dict[str, str]) -> tuple[int, list[str]]:
    score = int(query_meta.get("priority", 50))
    reasons: list[str] = [f"track priority +{query_meta.get('priority', 50)}"]

    ticket_id = row.get("ticket_id", "")
    keywords = first_value(row, KEYWORDS_KEYS).lower()
    component = first_value(row, COMPONENT_KEYS).lower()
    status = first_value(row, STATUS_KEYS).lower()
    milestone = first_value(row, MILESTONE_KEYS).lower()
    owner = first_value(row, OWNER_KEYS).lower()
    summary = first_value(row, SUMMARY_KEYS)

    if "has-patch" in keywords or "has patch" in keywords:
        score += 35
        reasons.append("has patch +35")
    if "needs-testing" in keywords or "needs testing" in keywords:
        score += 30
        reasons.append("needs testing +30")
    if "dev-feedback" in keywords or "dev feedback" in keywords:
        score += 18
        reasons.append("dev feedback +18")
    if "reporter-feedback" in keywords or "reporter feedback" in keywords:
        score += 10
        reasons.append("reporter feedback +10")
    if "good-first-bug" in keywords or "good first bug" in keywords:
        score += 20
        reasons.append("good first bug +20")
    if component == "media":
        score += 20
        reasons.append("preferred component: Media +20")
    if "accessibility" in component or "accessibility" in keywords:
        score += 18
        reasons.append("accessibility signal +18")
    if milestone and milestone not in {"awaiting review", "future release"}:
        score += 8
        reasons.append("has concrete milestone +8")
    if owner and owner not in {"", "anonymous", "nobody"}:
        score += 6
        reasons.append("has owner +6")
    if status in {"closed", "fixed", "wontfix", "duplicate", "invalid"}:
        score -= 100
        reasons.append("closed/non-actionable -100")

    modified_age = days_since(first_value(row, MODIFIED_KEYS))
    if modified_age is not None:
        if modified_age <= 14:
            score += 20
            reasons.append("recent activity <=14 days +20")
        elif modified_age <= 60:
            score += 10
            reasons.append("recent activity <=60 days +10")
        elif modified_age > 730:
            score -= 10
            reasons.append("stale activity >2 years -10")

    created_age = days_since(first_value(row, CREATED_KEYS))
    if created_age is not None:
        if 30 <= created_age <= 730:
            score += 8
            reasons.append("mature but not ancient +8")
        elif created_age > 3650:
            score -= 8
            reasons.append("very old ticket -8")

    comments_raw = first_value(row, COMMENTS_KEYS)
    if comments_raw.isdigit():
        comments = int(comments_raw)
        if 2 <= comments <= 20:
            score += 7
            reasons.append("healthy comment count +7")
        elif comments > 80:
            score -= 8
            reasons.append("very large thread -8")

    if ticket_id in outcomes:
        outcome = outcomes[ticket_id]
        if outcome == "props":
            score -= 60
            reasons.append("already produced props -60")
        elif outcome == "tested":
            score -= 20
            reasons.append("already tested -20")

    if not summary:
        score -= 10
        reasons.append("missing summary -10")

    return score, reasons


def trac_url(ticket_id: str) -> str:
    return f"https://core.trac.wordpress.org/ticket/{ticket_id}"
