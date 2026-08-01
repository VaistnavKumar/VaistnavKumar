"""Generate an animated terminal-style footer SVG for the profile README."""

from __future__ import annotations

import html
import logging
from dataclasses import dataclass
from pathlib import Path


LOGGER = logging.getLogger(__name__)
PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_PATH = PROJECT_ROOT / "assets" / "footer.svg"

# Edit this list to change the terminal footer message.
FOOTER_LINES = [
    "────────────────────────────────────────",
    "Thanks for visiting.",
    "Have a nice day.",
    "$",
]


@dataclass(frozen=True)
class FooterConfig:
    """Layout and animation settings for the terminal footer."""

    output_path: Path = OUTPUT_PATH
    width: int = 860
    height: int = 188
    padding: int = 32
    line_height: int = 28
    row_delay: float = 0.28


def configure_logging() -> None:
    """Configure concise logging for command-line execution."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


def validate_lines(lines: list[str]) -> None:
    """Ensure the footer has the divider, message, and final shell prompt."""
    if len(lines) < 2 or not all(isinstance(line, str) and line for line in lines):
        raise ValueError("Footer lines must contain at least two non-empty strings.")
    if lines[-1] != "$":
        raise ValueError("The last footer line must be the terminal prompt '$'.")


def render_line(line: str, index: int, config: FooterConfig) -> str:
    """Render a terminal line with a one-time opacity reveal."""
    y_position = config.padding + 24 + index * config.line_height
    begin = 0.2 + index * config.row_delay
    color = "#3fb950" if line == "$" else "#c9d1d9"
    return f'<text x="{config.padding}" y="{y_position}" fill="{color}" class="terminal-line" opacity="0">{html.escape(line)}<animate attributeName="opacity" from="0" to="1" begin="{begin:.2f}s" dur="0.12s" fill="freeze"/></text>'


def render_svg(config: FooterConfig) -> str:
    """Render the complete footer SVG with an indefinitely blinking cursor."""
    validate_lines(FOOTER_LINES)
    rows_markup = "\n".join(
        render_line(line, index, config) for index, line in enumerate(FOOTER_LINES)
    )
    cursor_begin = 0.2 + len(FOOTER_LINES) * config.row_delay
    cursor_x = config.padding + 16
    cursor_y = config.padding + 10 + (len(FOOTER_LINES) - 1) * config.line_height
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="100%" viewBox="0 0 {config.width} {config.height}" role="img" aria-labelledby="title desc">
<title id="title">Profile footer</title>
<desc id="desc">A terminal footer thanking visitors, followed by a blinking command cursor.</desc>
<rect width="100%" height="100%" rx="16" fill="#0d1117"/>
<style>.terminal-line {{ font: 16px ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace; }}</style>
{rows_markup}
<rect x="{cursor_x}" y="{cursor_y}" width="9" height="18" fill="#3fb950" opacity="0"><set attributeName="opacity" to="1" begin="{cursor_begin:.2f}s" fill="freeze"/><animate attributeName="opacity" values="1;0;1" dur="0.9s" begin="{cursor_begin:.2f}s" repeatCount="indefinite"/></rect>
</svg>
'''


def build_footer_svg(config: FooterConfig = FooterConfig()) -> Path:
    """Generate the terminal footer SVG from the configurable message lines."""
    svg = render_svg(config)
    config.output_path.parent.mkdir(parents=True, exist_ok=True)
    config.output_path.write_text(svg, encoding="utf-8")
    LOGGER.info("Wrote %s", config.output_path)
    return config.output_path


def main() -> None:
    """Build the animated terminal footer."""
    configure_logging()
    try:
        build_footer_svg()
    except (OSError, ValueError) as error:
        LOGGER.error("Footer SVG generation failed: %s", error)
        raise SystemExit(1) from error


if __name__ == "__main__":
    main()
