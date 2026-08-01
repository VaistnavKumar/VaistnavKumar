"""Generate an animated vertical career timeline as a self-contained SVG."""

from __future__ import annotations

import html
import logging
from dataclasses import dataclass
from pathlib import Path


LOGGER = logging.getLogger(__name__)
PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_PATH = PROJECT_ROOT / "assets" / "timeline.svg"

# Edit this list to update every timeline milestone.
MILESTONES: list[dict[str, str | list[str]]] = [
    {
        "year": "2022",
        "title": "Started Programming Journey",
        "details": ["Began building a foundation in software development."],
    },
    {
        "year": "2023",
        "title": "Built Full-Stack Web Applications",
        "details": ["Developed modern web experiences from frontend to backend."],
    },
    {
        "year": "2024",
        "title": "Graduated & Began Freelancing",
        "details": [
            "Completed B.Sc. in Information Technology.",
            "Started delivering client-focused software projects.",
        ],
    },
    {
        "year": "2025",
        "title": "Applied AI to Healthcare",
        "details": [
            "Built AI voice agents and an appointment-booking SaaS.",
            "Worked on healthcare automation workflows.",
        ],
    },
    {
        "year": "2026",
        "title": "Founded KB AI",
        "details": [
            "Built multi-agent AI systems.",
            "Developing production AI SaaS products.",
        ],
    },
]


@dataclass(frozen=True)
class TimelineConfig:
    """Layout and animation settings for the vertical timeline."""

    output_path: Path = OUTPUT_PATH
    width: int = 1040
    padding: int = 38
    line_x: int = 180
    first_y: int = 112
    row_height: int = 112
    card_x: int = 220
    card_width: int = 770
    card_height: int = 82
    reveal_delay: float = 0.42


def configure_logging() -> None:
    """Configure concise logging for command-line execution."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


def validate_milestones(milestones: list[dict[str, str | list[str]]]) -> None:
    """Ensure each configurable milestone contains usable display content."""
    if not milestones:
        raise ValueError("At least one timeline milestone is required.")
    for milestone in milestones:
        if not isinstance(milestone.get("year"), str) or not milestone["year"]:
            raise ValueError("Every milestone must include a year.")
        if not isinstance(milestone.get("title"), str) or not milestone["title"]:
            raise ValueError("Every milestone must include a title.")
        details = milestone.get("details")
        if not isinstance(details, list) or not all(isinstance(detail, str) for detail in details):
            raise ValueError("Every milestone must include a list of detail strings.")


def render_details(details: list[str], x_position: int, y_position: int) -> str:
    """Render a detail list as multiline SVG tspans."""
    return "".join(
        f'<tspan x="{x_position}" dy="{0 if index == 0 else 19}">{html.escape(detail)}</tspan>'
        for index, detail in enumerate(details)
    )


def render_milestone(
    milestone: dict[str, str | list[str]],
    index: int,
    config: TimelineConfig,
) -> str:
    """Render one timeline node, year, and animated milestone card."""
    y_position = config.first_y + index * config.row_height
    begin = 0.3 + index * config.reveal_delay
    year = html.escape(str(milestone["year"]))
    title = html.escape(str(milestone["title"]))
    details = milestone["details"]
    if not isinstance(details, list):
        raise ValueError("Milestone details must be a list.")
    return f'''<text x="{config.line_x - 28}" y="{y_position + 5}" text-anchor="end" class="year" opacity="0">{year}<animate attributeName="opacity" from="0" to="1" begin="{begin:.2f}s" dur="0.15s" fill="freeze"/></text>
<circle cx="{config.line_x}" cy="{y_position}" r="8" fill="#0d1117" stroke="#58a6ff" stroke-width="4" opacity="0"><animate attributeName="opacity" from="0" to="1" begin="{begin:.2f}s" dur="0.15s" fill="freeze"/></circle>
<g opacity="0"><animate attributeName="opacity" from="0" to="1" begin="{begin + 0.1:.2f}s" dur="0.2s" fill="freeze"/>
  <rect x="{config.card_x}" y="{y_position - 38}" width="{config.card_width}" height="{config.card_height}" rx="12" fill="#161b22" stroke="#30363d"/>
  <text x="{config.card_x + 24}" y="{y_position - 9}" class="title">{title}</text>
  <text x="{config.card_x + 24}" y="{y_position + 15}" class="detail">{render_details(details, config.card_x + 24, y_position + 15)}</text>
</g>'''


def render_svg(config: TimelineConfig) -> str:
    """Render the complete animated timeline SVG."""
    validate_milestones(MILESTONES)
    line_end = config.first_y + (len(MILESTONES) - 1) * config.row_height
    height = line_end + config.padding + 50
    milestones_markup = "\n".join(
        render_milestone(milestone, index, config)
        for index, milestone in enumerate(MILESTONES)
    )
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="100%" viewBox="0 0 {config.width} {height}" role="img" aria-labelledby="title desc">
<title id="title">Vaistnav Kumar career timeline</title>
<desc id="desc">An animated vertical timeline from 2022 to 2026.</desc>
<rect width="100%" height="100%" rx="16" fill="#0d1117"/>
<style>
  .heading {{ fill: #f0f6fc; font: 600 20px ui-sans-serif, system-ui, sans-serif; }}
  .subtitle {{ fill: #8b949e; font: 13px ui-sans-serif, system-ui, sans-serif; }}
  .year {{ fill: #79c0ff; font: 600 16px ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace; }}
  .title {{ fill: #f0f6fc; font: 600 16px ui-sans-serif, system-ui, sans-serif; }}
  .detail {{ fill: #8b949e; font: 13px ui-sans-serif, system-ui, sans-serif; }}
</style>
<text x="{config.padding}" y="38" class="heading">Career timeline</text>
<text x="{config.padding}" y="60" class="subtitle">A path from code curiosity to production AI systems</text>
<path d="M{config.line_x} {config.first_y}V{line_end}" stroke="#58a6ff" stroke-width="3" stroke-linecap="round" pathLength="1" stroke-dasharray="1" stroke-dashoffset="1"><animate attributeName="stroke-dashoffset" from="1" to="0" begin="0.15s" dur="1.8s" fill="freeze"/></path>
{milestones_markup}
</svg>
'''


def build_timeline_svg(config: TimelineConfig = TimelineConfig()) -> Path:
    """Generate the timeline SVG from the configurable milestone list."""
    svg = render_svg(config)
    config.output_path.parent.mkdir(parents=True, exist_ok=True)
    config.output_path.write_text(svg, encoding="utf-8")
    LOGGER.info("Wrote %s", config.output_path)
    return config.output_path


def main() -> None:
    """Build the animated timeline SVG."""
    configure_logging()
    try:
        build_timeline_svg()
    except (OSError, ValueError) as error:
        LOGGER.error("Timeline SVG generation failed: %s", error)
        raise SystemExit(1) from error


if __name__ == "__main__":
    main()
