"""Convert a prepared portrait into an animated, GitHub-compatible ASCII SVG."""

from __future__ import annotations

import argparse
import html
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from PIL import Image


LOGGER = logging.getLogger(__name__)
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = PROJECT_ROOT / "source-prepped.png"
DEFAULT_OUTPUT = PROJECT_ROOT / "assets" / "ascii.svg"
DEFAULT_RAMP = "@%#*+=-:. "


@dataclass(frozen=True)
class AsciiSvgConfig:
    """Settings that control ASCII conversion and SVG appearance."""

    input_path: Path
    output_path: Path
    columns: int = 78
    density_ramp: str = DEFAULT_RAMP
    foreground: str = "#86efac"
    background: str = "#07110b"
    font_size: int = 12
    line_height: int = 14
    padding: int = 24
    row_delay: float = 0.055


def configure_logging() -> None:
    """Configure concise logging for command-line execution."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


def parse_args(arguments: Sequence[str] | None = None) -> AsciiSvgConfig:
    """Parse command-line options into a validated ASCII SVG configuration."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--columns", type=int, default=78)
    parser.add_argument("--ramp", default=DEFAULT_RAMP)
    parsed = parser.parse_args(arguments)

    if parsed.columns < 12:
        parser.error("--columns must be at least 12.")
    if len(parsed.ramp) < 2:
        parser.error("--ramp must contain at least two characters.")

    return AsciiSvgConfig(
        input_path=parsed.input.expanduser().resolve(),
        output_path=parsed.output.expanduser().resolve(),
        columns=parsed.columns,
        density_ramp=parsed.ramp,
    )


def load_grayscale_image(input_path: Path) -> Image.Image:
    """Load a source image as grayscale, with clear errors for invalid inputs."""
    if not input_path.is_file():
        raise FileNotFoundError(f"Prepared photo does not exist: {input_path}")
    try:
        with Image.open(input_path) as image:
            return image.convert("L")
    except OSError as error:
        raise ValueError(f"Could not read prepared photo: {input_path}") from error


def resize_for_characters(image: Image.Image, config: AsciiSvgConfig) -> Image.Image:
    """Resize an image while compensating for terminal character proportions."""
    source_width, source_height = image.size
    character_aspect_ratio = 0.52
    rows = max(
        1,
        round(source_height / source_width * config.columns * character_aspect_ratio),
    )
    return image.resize((config.columns, rows), Image.Resampling.LANCZOS)


def pixels_to_ascii(image: Image.Image, density_ramp: str) -> list[str]:
    """Map each grayscale pixel to one density-ramp character."""
    ramp_maximum = len(density_ramp) - 1
    if hasattr(image, "get_flattened_data"):
        pixels = list(image.get_flattened_data())
    else:
        pixels = list(image.getdata())
    characters = [density_ramp[pixel * ramp_maximum // 255] for pixel in pixels]
    width, height = image.size
    return ["".join(characters[row * width : (row + 1) * width]) for row in range(height)]


def svg_text_row(row: str, index: int, config: AsciiSvgConfig) -> str:
    """Render one ASCII row with a one-time timed opacity reveal."""
    x_position = config.padding
    y_position = config.padding + config.font_size + index * config.line_height
    begin = 0.2 + index * config.row_delay
    escaped_row = html.escape(row)
    return (
        f'  <text x="{x_position}" y="{y_position}" class="ascii-row" '
        f'xml:space="preserve" opacity="0">{escaped_row}'
        f'<animate attributeName="opacity" from="0" to="1" '
        f'begin="{begin:.3f}s" dur="0.01s" fill="freeze"/>'
        "</text>"
    )


def render_svg(rows: list[str], config: AsciiSvgConfig) -> str:
    """Create a responsive animated SVG containing all ASCII rows and cursor."""
    if not rows:
        raise ValueError("Cannot render an SVG without ASCII rows.")

    content_width = config.columns * config.font_size * 0.61
    width = round(content_width + config.padding * 2)
    height = config.padding * 2 + config.font_size + (len(rows) - 1) * config.line_height
    cursor_begin = 0.2 + len(rows) * config.row_delay
    cursor_y = config.padding + config.font_size + len(rows) * config.line_height
    rows_markup = "\n".join(svg_text_row(row, index, config) for index, row in enumerate(rows))

    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="100%" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">
<title id="title">Animated ASCII portrait of Vaistnav Kumar</title>
<desc id="desc">A monochrome terminal-style ASCII portrait that types in one row at a time.</desc>
<rect width="100%" height="100%" rx="16" fill="{config.background}"/>
<style>
  .ascii-row {{ fill: {config.foreground}; font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace; font-size: {config.font_size}px; }}
  .cursor {{ fill: {config.foreground}; }}
</style>
{rows_markup}
<rect class="cursor" x="{config.padding}" y="{cursor_y}" width="{config.font_size * 0.61:.2f}" height="{config.line_height - 2}" opacity="0">
  <set attributeName="opacity" to="1" begin="{cursor_begin:.3f}s" fill="freeze"/>
  <animate attributeName="opacity" values="1;0;1" dur="0.9s" begin="{cursor_begin:.3f}s" repeatCount="indefinite"/>
</rect>
</svg>
'''


def build_ascii_svg(config: AsciiSvgConfig) -> Path:
    """Convert a prepared image into the configured animated ASCII SVG."""
    LOGGER.info("Loading %s", config.input_path)
    resized_image = resize_for_characters(load_grayscale_image(config.input_path), config)
    rows = pixels_to_ascii(resized_image, config.density_ramp)
    svg = render_svg(rows, config)
    config.output_path.parent.mkdir(parents=True, exist_ok=True)
    config.output_path.write_text(svg, encoding="utf-8")
    LOGGER.info("Wrote %s (%d columns, %d rows)", config.output_path, config.columns, len(rows))
    return config.output_path


def main(arguments: Sequence[str] | None = None) -> None:
    """Run ASCII SVG generation and report user-facing input errors."""
    configure_logging()
    try:
        build_ascii_svg(parse_args(arguments))
    except (FileNotFoundError, OSError, TypeError, ValueError) as error:
        LOGGER.error("ASCII SVG generation failed: %s", error)
        raise SystemExit(1) from error


if __name__ == "__main__":
    main()
