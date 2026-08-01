"""Fetch and summarize a public GitHub contribution calendar without a token."""

from __future__ import annotations

import argparse
import json
import logging
import re
from dataclasses import asdict, dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Sequence

import requests
from bs4 import BeautifulSoup, Tag


LOGGER = logging.getLogger(__name__)
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_USERNAME = "VaistnavKumar"
DEFAULT_OUTPUT = PROJECT_ROOT / "data" / "contributions.json"
CONTRIBUTIONS_URL = "https://github.com/users/{username}/contributions"
REQUEST_HEADERS = {
    "Accept": "text/html,application/xhtml+xml",
    "User-Agent": "github-profile-svg-builder/1.0",
}
COUNT_PATTERN = re.compile(r"([\d,]+) contributions? on", re.IGNORECASE)


@dataclass(frozen=True)
class ContributionDay:
    """One public GitHub contribution-calendar cell."""

    date: str
    count: int
    level: int
    week: int
    weekday: int


@dataclass(frozen=True)
class FetchConfig:
    """Network and output settings for contribution collection."""

    username: str
    output_path: Path
    timeout_seconds: int = 30


def configure_logging() -> None:
    """Configure concise logging for command-line execution."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


def parse_args(arguments: Sequence[str] | None = None) -> FetchConfig:
    """Parse the optional username and JSON output path."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--username", default=DEFAULT_USERNAME)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parsed = parser.parse_args(arguments)
    username = parsed.username.strip()
    if not re.fullmatch(r"[A-Za-z\d](?:[A-Za-z\d-]{0,37}[A-Za-z\d])?", username):
        parser.error("--username must be a valid GitHub username.")
    return FetchConfig(username, parsed.output.expanduser().resolve())


def fetch_calendar_html(config: FetchConfig) -> str:
    """Request a user's publicly rendered GitHub contribution calendar."""
    url = CONTRIBUTIONS_URL.format(username=config.username)
    try:
        response = requests.get(url, headers=REQUEST_HEADERS, timeout=config.timeout_seconds)
        response.raise_for_status()
    except requests.RequestException as error:
        raise RuntimeError(f"Could not fetch GitHub contributions: {error}") from error
    return response.text


def tooltip_counts(soup: BeautifulSoup) -> dict[str, int]:
    """Map contribution cell IDs to counts exposed in adjacent GitHub tooltips."""
    counts: dict[str, int] = {}
    for tooltip in soup.find_all("tool-tip"):
        target = tooltip.get("for")
        text = tooltip.get_text(" ", strip=True)
        match = COUNT_PATTERN.search(text)
        if target:
            counts[target] = int(match.group(1).replace(",", "")) if match else 0
    return counts


def parse_contribution_days(html: str) -> list[ContributionDay]:
    """Parse all date cells from GitHub's public calendar HTML."""
    soup = BeautifulSoup(html, "html.parser")
    counts_by_id = tooltip_counts(soup)
    days: list[ContributionDay] = []

    for cell in soup.select("[data-date][data-level]"):
        if not isinstance(cell, Tag):
            continue
        date_text = cell.get("data-date")
        level_text = cell.get("data-level")
        if not date_text or level_text is None:
            continue
        try:
            parsed_date = date.fromisoformat(date_text)
            level = int(level_text)
            week = int(cell.get("data-ix", "0"))
        except (TypeError, ValueError) as error:
            raise ValueError("GitHub returned an invalid contribution calendar cell.") from error
        count = counts_by_id.get(cell.get("id", ""), 0)
        days.append(
            ContributionDay(
                date=parsed_date.isoformat(),
                count=count,
                level=level,
                week=week,
                weekday=(parsed_date.weekday() + 1) % 7,
            )
        )

    if not days:
        raise ValueError("No contribution days were found in GitHub's response.")
    return sorted(days, key=lambda day: day.date)


def longest_streak(days: list[ContributionDay]) -> int:
    """Return the greatest number of consecutive dates with contributions."""
    best = current = 0
    for day in days:
        if day.count > 0:
            current += 1
            best = max(best, current)
        else:
            current = 0
    return best


def current_streak(days: list[ContributionDay]) -> int:
    """Return the active streak ending on the calendar's most recent date."""
    streak = 0
    for day in reversed(days):
        if day.count == 0:
            break
        streak += 1
    return streak


def monthly_totals(days: list[ContributionDay]) -> dict[str, int]:
    """Aggregate public contribution counts by ISO year-month."""
    totals: dict[str, int] = {}
    for day in days:
        month = day.date[:7]
        totals[month] = totals.get(month, 0) + day.count
    return totals


def build_payload(username: str, days: list[ContributionDay]) -> dict[str, object]:
    """Build the complete JSON document consumed by the heatmap renderer."""
    best_day = max(days, key=lambda day: (day.count, day.date))
    return {
        "username": username,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "contributions": [asdict(day) for day in days],
        "year_total": sum(day.count for day in days),
        "current_streak": current_streak(days),
        "longest_streak": longest_streak(days),
        "best_day": {"date": best_day.date, "count": best_day.count},
        "monthly_totals": monthly_totals(days),
    }


def save_payload(payload: dict[str, object], output_path: Path) -> Path:
    """Write contribution data as stable, readable JSON."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return output_path


def fetch_contributions(config: FetchConfig) -> Path:
    """Fetch, parse, summarize, and persist the public contribution calendar."""
    LOGGER.info("Fetching public contributions for %s", config.username)
    days = parse_contribution_days(fetch_calendar_html(config))
    output_path = save_payload(build_payload(config.username, days), config.output_path)
    LOGGER.info("Wrote %s with %d contribution days", output_path, len(days))
    return output_path


def main(arguments: Sequence[str] | None = None) -> None:
    """Run public contribution collection with user-facing error reporting."""
    configure_logging()
    try:
        fetch_contributions(parse_args(arguments))
    except (RuntimeError, OSError, ValueError) as error:
        LOGGER.error("Contribution fetch failed: %s", error)
        raise SystemExit(1) from error


if __name__ == "__main__":
    main()
