"""Generate an animated macOS-terminal profile information card as SVG."""

from __future__ import annotations

import html
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any


LOGGER = logging.getLogger(__name__)
PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_PATH = PROJECT_ROOT / "assets" / "info-card.svg"

# Edit this one dictionary to change every value shown in the info card.
PROFILE: dict[str, Any] = {
    "name": "Vaistnav Kumar",
    "role": "🚀 AI Engineer | Voice AI | Full Stack Developer",
    "location": "India, Tirupati",
    "current_focus": "AI Voice Agents & Healthcare SaaS",
    "languages": ["Python", "TypeScript", "JavaScript"],
    "tech_stack": [
        "Next.js",
        "React",
        "FastAPI",
        "Tailwind CSS",
        "Supabase",
        "PostgreSQL",
        "LiveKit",
        "Docker",
    ],
    "frameworks": ["Next.js", "React", "FastAPI", "Tailwind CSS"],
    "cloud": ["Supabase", "Google Cloud", "Vercel", "Cloudflare", "GitHub Actions"],
    "database": ["PostgreSQL", "Supabase", "Firebase"],
    "interests": ["Voice AI", "AI Agents", "Automation", "Healthcare SaaS"],
    "social_links": {"GitHub": "https://github.com/VaistnavKumar"},
}


@dataclass(frozen=True)
class InfoCardConfig:
    """Layout and animation settings for the generated information card."""

    output_path: Path = OUTPUT_PATH
    width: int = 1040
    padding: int = 36
    title_bar_height: int = 74
    line_height: int = 35
    row_delay: float = 0.24


def configure_logging() -> None:
    """Configure concise logging for command-line execution."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


def join_values(value: str | list[str] | dict[str, str]) -> str:
    """Format scalar, list, and link dictionary values for terminal display."""
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        return ", ".join(value)
    return " · ".join(f"{name}: {url}" for name, url in value.items())


def profile_lines(profile: dict[str, Any]) -> list[tuple[str, str]]:
    """Convert the profile dictionary to ordered terminal field/value rows."""
    field_order = (
        ("Name", "name"),
        ("Role", "role"),
        ("Location", "location"),
        ("Current Focus", "current_focus"),
        ("Languages", "languages"),
        ("Tech Stack", "tech_stack"),
        ("Frameworks", "frameworks"),
        ("Cloud", "cloud"),
        ("Database", "database"),
        ("Interests", "interests"),
        ("Social Links", "social_links"),
    )
    return [(label, join_values(profile[key])) for label, key in field_order]


def render_line(label: str, value: str, index: int, config: InfoCardConfig) -> str:
    """Render an information row with a one-time terminal-style reveal."""
    y_position = config.title_bar_height + config.padding + index * config.line_height
    begin = 0.35 + index * config.row_delay
    escaped_label = html.escape(label)
    escaped_value = html.escape(value)
    return f'''  <text x="{config.padding}" y="{y_position}" class="line" opacity="0">
    <tspan class="prompt">❯</tspan><tspan class="label"> {escaped_label}:</tspan><tspan class="value"> {escaped_value}</tspan>
    <animate attributeName="opacity" from="0" to="1" begin="{begin:.2f}s" dur="0.12s" fill="freeze"/>
  </text>'''


def render_svg(lines: list[tuple[str, str]], config: InfoCardConfig) -> str:
    """Render a responsive SVG terminal window containing profile information."""
    height = config.title_bar_height + config.padding * 2 + len(lines) * config.line_height
    rows_markup = "\n".join(
        render_line(label, value, index, config)
        for index, (label, value) in enumerate(lines)
    )
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="100%" viewBox="0 0 {config.width} {height}" role="img" aria-labelledby="title desc">
<title id="title">Vaistnav Kumar profile information</title>
<desc id="desc">An animated terminal card containing Vaistnav Kumar's professional profile.</desc>
<rect width="100%" height="100%" rx="20" fill="#0d1117"/>
<path d="M20 0h1000a20 20 0 0 1 20 20v54H0V20A20 20 0 0 1 20 0z" fill="#161b22"/>
<circle cx="37" cy="37" r="9" fill="#ff5f57"/><circle cx="67" cy="37" r="9" fill="#febc2e"/><circle cx="97" cy="37" r="9" fill="#28c840"/>
<text x="520" y="43" text-anchor="middle" class="window-title">vaistnav@github-profile — zsh</text>
<style>
  .window-title {{ fill: #8b949e; font: 500 16px ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace; }}
  .line {{ font: 16px ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace; }}
  .prompt {{ fill: #3fb950; }} .label {{ fill: #79c0ff; }} .value {{ fill: #c9d1d9; }}
</style>
{rows_markup}
</svg>
'''


def build_info_card(config: InfoCardConfig = InfoCardConfig()) -> Path:
    """Generate the information card from the single configurable profile map."""
    lines = profile_lines(PROFILE)
    svg = render_svg(lines, config)
    config.output_path.parent.mkdir(parents=True, exist_ok=True)
    config.output_path.write_text(svg, encoding="utf-8")
    LOGGER.info("Wrote %s with %d profile fields", config.output_path, len(lines))
    return config.output_path


def main() -> None:
    """Build the profile information card."""
    configure_logging()
    build_info_card()


if __name__ == "__main__":
    main()
