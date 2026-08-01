"""Render locally fetched GitHub contributions as an animated SVG heatmap."""

from __future__ import annotations

import html
import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any


LOGGER = logging.getLogger(__name__)
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = PROJECT_ROOT / "data" / "contributions.json"
DEFAULT_OUTPUT = PROJECT_ROOT / "assets" / "contrib-heatmap.svg"
PALETTE = ("#161b22", "#0e4429", "#006d32", "#26a641", "#39d353")


@dataclass(frozen=True)
class HeatmapConfig:
    """Layout and animation settings for a contribution heatmap SVG."""

    input_path: Path = DEFAULT_INPUT
    output_path: Path = DEFAULT_OUTPUT
    weeks: int = 53
    days: int = 7
    cell_size: int = 12
    cell_gap: int = 4
    padding: int = 28
    label_width: int = 35
    reveal_delay: float = 0.022


def configure_logging() -> None:
    """Configure concise logging for command-line execution."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


def load_contribution_data(input_path: Path) -> dict[str, Any]:
    """Load and validate the contribution JSON produced by the fetch script."""
    if not input_path.is_file():
        raise FileNotFoundError(f"Contribution data does not exist: {input_path}")
    try:
        data = json.loads(input_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"Could not read contribution data: {input_path}") from error
    required_keys = {"username", "contributions", "year_total", "current_streak", "longest_streak", "best_day"}
    if not required_keys <= data.keys() or not isinstance(data["contributions"], list):
        raise ValueError("Contribution data is missing required fields.")
    return data


def contribution_index(contributions: list[dict[str, Any]]) -> dict[tuple[int, int], dict[str, Any]]:
    """Index contribution days by their zero-based calendar week and weekday."""
    indexed: dict[tuple[int, int], dict[str, Any]] = {}
    for day in contributions:
        try:
            key = (int(day["week"]), int(day["weekday"]))
            level = int(day["level"])
            if not 0 <= level < len(PALETTE):
                raise ValueError
        except (KeyError, TypeError, ValueError) as error:
            raise ValueError("Contribution data contains an invalid calendar day.") from error
        indexed[key] = day
    return indexed


def render_cell(week: int, weekday: int, day: dict[str, Any] | None, config: HeatmapConfig) -> str:
    """Render one rounded heatmap cell with a one-time diagonal reveal."""
    x_position = config.padding + config.label_width + week * (config.cell_size + config.cell_gap)
    y_position = config.padding + 39 + weekday * (config.cell_size + config.cell_gap)
    level = int(day["level"]) if day else 0
    count = int(day["count"]) if day else 0
    date_label = str(day["date"]) if day else "Outside contribution range"
    begin = 0.2 + (week + weekday) * config.reveal_delay
    label = html.escape(f"{date_label}: {count} contributions")
    return f'''<rect x="{x_position}" y="{y_position}" width="{config.cell_size}" height="{config.cell_size}" rx="3" fill="{PALETTE[level]}" opacity="0">
  <title>{label}</title><animate attributeName="opacity" from="0" to="1" begin="{begin:.3f}s" dur="0.13s" fill="freeze"/>
</rect>'''


def render_legend(x_position: int, y_position: int, config: HeatmapConfig) -> str:
    """Render the GitHub-green Less-to-More color legend."""
    cells = "".join(
        f'<rect x="{x_position + 43 + index * 18}" y="{y_position - 11}" width="12" height="12" rx="3" fill="{color}"/>'
        for index, color in enumerate(PALETTE)
    )
    return f'<text x="{x_position}" y="{y_position}" class="muted">Less</text>{cells}<text x="{x_position + 143}" y="{y_position}" class="muted">More</text>'


def render_svg(data: dict[str, Any], config: HeatmapConfig) -> str:
    """Render the complete responsive heatmap, legend, and summary footer."""
    indexed_days = contribution_index(data["contributions"])
    grid_width = config.weeks * (config.cell_size + config.cell_gap) - config.cell_gap
    width = config.padding * 2 + config.label_width + grid_width
    grid_bottom = config.padding + 39 + config.days * (config.cell_size + config.cell_gap) - config.cell_gap
    height = grid_bottom + 113
    cells = "\n".join(
        render_cell(week, weekday, indexed_days.get((week, weekday)), config)
        for week in range(config.weeks)
        for weekday in range(config.days)
    )
    best_day = data["best_day"]
    stats = (
        f'{data["year_total"]} contributions',
        f'{data["current_streak"]}-day current streak',
        f'{data["longest_streak"]}-day longest streak',
        f'Best: {best_day["count"]} on {best_day["date"]}',
    )
    stats_markup = "\n".join(
        f'<text x="{config.padding + index * 188}" y="{grid_bottom + 78}" class="stat">{html.escape(stat)}</text>'
        for index, stat in enumerate(stats)
    )
    legend = render_legend(width - 210, grid_bottom + 28, config)
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="100%" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">
<title id="title">{html.escape(str(data["username"]))}'s GitHub contribution heatmap</title>
<desc id="desc">A 53-week contribution grid with locally calculated contribution statistics.</desc>
<rect width="100%" height="100%" rx="16" fill="#0d1117"/>
<style>
  .heading {{ fill: #f0f6fc; font: 600 18px ui-sans-serif, system-ui, sans-serif; }}
  .muted {{ fill: #8b949e; font: 12px ui-sans-serif, system-ui, sans-serif; }}
  .stat {{ fill: #c9d1d9; font: 13px ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace; }}
</style>
<text x="{config.padding}" y="{config.padding}" class="heading">Contribution activity</text>
<text x="{config.padding}" y="{config.padding + 20}" class="muted">Last 53 weeks · generated locally</text>
<text x="{config.padding}" y="{config.padding + 49}" class="muted">Sun</text><text x="{config.padding}" y="{config.padding + 81}" class="muted">Tue</text><text x="{config.padding}" y="{config.padding + 113}" class="muted">Thu</text><text x="{config.padding}" y="{config.padding + 145}" class="muted">Sat</text>
{cells}
{legend}
<path d="M{config.padding} {grid_bottom + 48}H{width - config.padding}" stroke="#30363d"/>
{stats_markup}
</svg>
'''


def build_heatmap(config: HeatmapConfig = HeatmapConfig()) -> Path:
    """Generate the contribution heatmap SVG from the persisted JSON data."""
    svg = render_svg(load_contribution_data(config.input_path), config)
    config.output_path.parent.mkdir(parents=True, exist_ok=True)
    config.output_path.write_text(svg, encoding="utf-8")
    LOGGER.info("Wrote %s", config.output_path)
    return config.output_path


def main() -> None:
    """Build the contribution heatmap SVG."""
    configure_logging()
    try:
        build_heatmap()
    except (FileNotFoundError, OSError, ValueError) as error:
        LOGGER.error("Heatmap generation failed: %s", error)
        raise SystemExit(1) from error


if __name__ == "__main__":
    main()
