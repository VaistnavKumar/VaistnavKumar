"""Generate a configurable animated skill-progress SVG for a GitHub profile."""

from __future__ import annotations

import html
import logging
from dataclasses import dataclass
from pathlib import Path


LOGGER = logging.getLogger(__name__)
PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_PATH = PROJECT_ROOT / "assets" / "skills.svg"

# Edit this dictionary to update every displayed category, skill, and percentage.
SKILLS: dict[str, list[tuple[str, int]]] = {
    "Languages": [("Python", 95), ("JavaScript", 85), ("TypeScript", 80)],
    "Frameworks": [
        ("Next.js", 90),
        ("React", 85),
        ("FastAPI", 95),
        ("Tailwind CSS", 90),
    ],
    "DevOps": [("Docker", 75), ("Git & GitHub", 90), ("GitHub Actions", 85)],
    "AI & Automation": [
        ("AI Voice Agents", 95),
        ("LiveKit", 90),
        ("Google Gemini", 90),
        ("OpenAI API", 90),
        ("n8n Automation", 95),
        ("REST APIs", 95),
        ("Webhook Integration", 95),
        ("Prompt Engineering", 90),
    ],
    "Databases": [("PostgreSQL", 80), ("Supabase", 90), ("Firebase", 70)],
    "Cloud": [("Google Cloud", 75), ("Vercel", 90), ("Cloudflare", 75)],
}


@dataclass(frozen=True)
class SkillsConfig:
    """Layout and animation settings for the skills visualization."""

    output_path: Path = OUTPUT_PATH
    width: int = 1040
    padding: int = 34
    column_gap: int = 46
    section_gap: int = 24
    bar_height: int = 9
    bar_width: int = 404
    line_height: int = 37
    animation_delay: float = 0.1


def configure_logging() -> None:
    """Configure concise logging for command-line execution."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


def validate_skills(skills: dict[str, list[tuple[str, int]]]) -> None:
    """Reject empty categories and percentages outside the valid 0–100 range."""
    if not skills:
        raise ValueError("At least one skill category is required.")
    for category, entries in skills.items():
        if not category or not entries:
            raise ValueError("Every skill category must have a name and entries.")
        for name, percentage in entries:
            if not name or not 0 <= percentage <= 100:
                raise ValueError(f"Invalid skill entry in {category!r}.")


def split_columns(
    skills: dict[str, list[tuple[str, int]]],
) -> tuple[
    list[tuple[str, list[tuple[str, int]]]],
    list[tuple[str, list[tuple[str, int]]]],
]:
    """Distribute categories across two columns with similar visual heights."""
    left: list[tuple[str, list[tuple[str, int]]]] = []
    right: list[tuple[str, list[tuple[str, int]]]] = []
    left_height = right_height = 0
    for category, entries in skills.items():
        category_height = len(entries) + 1
        if left_height <= right_height:
            left.append((category, entries))
            left_height += category_height
        else:
            right.append((category, entries))
            right_height += category_height
    return left, right


def column_height(categories: list[tuple[str, list[tuple[str, int]]]], config: SkillsConfig) -> int:
    """Calculate the vertical space required for a column of skill categories."""
    row_count = sum(len(entries) + 1 for _, entries in categories)
    return row_count * config.line_height + (len(categories) - 1) * config.section_gap


def render_category(
    category: str,
    entries: list[tuple[str, int]],
    x_position: int,
    y_position: int,
    start_index: int,
    config: SkillsConfig,
) -> tuple[str, int, int]:
    """Render one skill category and return its SVG markup and next positions."""
    markup = [f'<text x="{x_position}" y="{y_position}" class="category">{html.escape(category)}</text>']
    y_position += config.line_height
    animation_index = start_index
    for name, percentage in entries:
        begin = 0.35 + animation_index * config.animation_delay
        fill_width = config.bar_width * percentage / 100
        markup.append(
            f'''<text x="{x_position}" y="{y_position}" class="skill">{html.escape(name)}</text>
<text x="{x_position + config.bar_width}" y="{y_position}" text-anchor="end" class="percentage">{percentage}%</text>
<rect x="{x_position}" y="{y_position + 9}" width="{config.bar_width}" height="{config.bar_height}" rx="4.5" fill="#21262d"/>
<rect x="{x_position}" y="{y_position + 9}" width="0" height="{config.bar_height}" rx="4.5" fill="#58a6ff"><animate attributeName="width" from="0" to="{fill_width:.2f}" begin="{begin:.2f}s" dur="0.55s" fill="freeze"/></rect>'''
        )
        y_position += config.line_height
        animation_index += 1
    return "\n".join(markup), y_position + config.section_gap, animation_index


def render_column(
    categories: list[tuple[str, list[tuple[str, int]]]],
    x_position: int,
    config: SkillsConfig,
) -> str:
    """Render all categories allocated to one progress-bar column."""
    y_position = 91
    animation_index = 0
    markup: list[str] = []
    for category, entries in categories:
        section, y_position, animation_index = render_category(
            category,
            entries,
            x_position,
            y_position,
            animation_index,
            config,
        )
        markup.append(section)
    return "\n".join(markup)


def render_svg(config: SkillsConfig) -> str:
    """Render the complete two-column animated skills SVG."""
    validate_skills(SKILLS)
    left, right = split_columns(SKILLS)
    content_height = max(column_height(left, config), column_height(right, config))
    height = max(360, 91 + content_height + config.padding)
    right_x = config.padding + config.bar_width + config.column_gap
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="100%" viewBox="0 0 {config.width} {height}" role="img" aria-labelledby="title desc">
<title id="title">Vaistnav Kumar technical skills</title>
<desc id="desc">Animated progress bars showing languages, frameworks, DevOps, AI, databases, and cloud skills.</desc>
<rect width="100%" height="100%" rx="16" fill="#0d1117"/>
<style>
  .heading {{ fill: #f0f6fc; font: 600 20px ui-sans-serif, system-ui, sans-serif; }}
  .subtitle {{ fill: #8b949e; font: 13px ui-sans-serif, system-ui, sans-serif; }}
  .category {{ fill: #79c0ff; font: 600 15px ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace; }}
  .skill {{ fill: #c9d1d9; font: 13px ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace; }}
  .percentage {{ fill: #8b949e; font: 13px ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace; }}
</style>
<text x="{config.padding}" y="38" class="heading">Skills &amp; toolkit</text>
<text x="{config.padding}" y="60" class="subtitle">Proficiency self-assessment · generated locally</text>
{render_column(left, config.padding, config)}
{render_column(right, right_x, config)}
</svg>
'''


def build_skills_svg(config: SkillsConfig = SkillsConfig()) -> Path:
    """Generate the skills progress-bar SVG from the configurable skills map."""
    svg = render_svg(config)
    config.output_path.parent.mkdir(parents=True, exist_ok=True)
    config.output_path.write_text(svg, encoding="utf-8")
    LOGGER.info("Wrote %s", config.output_path)
    return config.output_path


def main() -> None:
    """Build the animated skills SVG."""
    configure_logging()
    try:
        build_skills_svg()
    except (OSError, ValueError) as error:
        LOGGER.error("Skills SVG generation failed: %s", error)
        raise SystemExit(1) from error


if __name__ == "__main__":
    main()
