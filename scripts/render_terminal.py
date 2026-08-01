"""Generate an animated macOS-terminal dashboard SVG with an ASCII portrait."""

from __future__ import annotations

import html
import logging
from dataclasses import dataclass
from pathlib import Path

from make_ascii_svg import (
    AsciiSvgConfig,
    load_grayscale_image,
    pixels_to_ascii,
    resize_for_characters,
)


LOGGER = logging.getLogger(__name__)
PROJECT_ROOT = Path(__file__).resolve().parents[1]
SOURCE_IMAGE = PROJECT_ROOT / "source-prepped.png"
OUTPUT_PATH = PROJECT_ROOT / "assets" / "terminal.svg"

# Edit this dictionary to update the terminal dashboard contents.
TERMINAL_PROFILE = {
    "user": "vaistnav",
    "host": "ai-workstation",
    "title": "vaistnav@github-profile — zsh",
    "commands": [
        "whoami",
        "cat /etc/profile",
        "echo $CURRENT_MISSION",
    ],
    "system_info": [
        ("Name", "Vaistnav Kumar"),
        ("Role", "AI Engineer | Voice AI | Full Stack"),
        ("Location", "Tirupati, India"),
        ("Focus", "AI Voice Agents & Healthcare SaaS"),
        ("Stack", "Python · Next.js · FastAPI · Supabase"),
        ("Voice", "LiveKit · OpenAI API · Google Gemini"),
        ("Status", "Building production AI SaaS products"),
    ],
    "mission": "Designing helpful voice-first AI systems.",
}


@dataclass(frozen=True)
class TerminalConfig:
    """Layout and animation settings for the terminal dashboard."""

    source_image: Path = SOURCE_IMAGE
    output_path: Path = OUTPUT_PATH
    width: int = 1060
    height: int = 550
    padding: int = 36
    title_bar_height: int = 72
    portrait_columns: int = 30
    portrait_font_size: int = 10
    portrait_line_height: int = 12
    row_delay: float = 0.12


def configure_logging() -> None:
    """Configure concise logging for command-line execution."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


def portrait_rows(config: TerminalConfig) -> list[str]:
    """Convert the prepared image into compact rows for the embedded portrait."""
    ascii_config = AsciiSvgConfig(
        input_path=config.source_image,
        output_path=config.output_path,
        columns=config.portrait_columns,
    )
    image = resize_for_characters(load_grayscale_image(config.source_image), ascii_config)
    return pixels_to_ascii(image, ascii_config.density_ramp)


def terminal_row(text: str, y_position: int, index: int, config: TerminalConfig, css_class: str) -> str:
    """Render one text line with a clip-based one-time typing animation."""
    x_position = 278
    begin = 0.3 + index * config.row_delay
    clip_id = f"typing-clip-{index}"
    escaped_text = html.escape(text)
    return f'''<clipPath id="{clip_id}"><rect x="{x_position}" y="{y_position - 18}" width="0" height="24"><animate attributeName="width" from="0" to="730" begin="{begin:.2f}s" dur="0.42s" fill="freeze"/></rect></clipPath>
<text x="{x_position}" y="{y_position}" class="{css_class}" clip-path="url(#{clip_id})">{escaped_text}</text>'''


def portrait_markup(rows: list[str], config: TerminalConfig) -> str:
    """Render the embedded monochrome ASCII portrait inside the terminal."""
    x_position = config.padding
    y_start = config.title_bar_height + 37
    return "\n".join(
        f'<text x="{x_position}" y="{y_start + index * config.portrait_line_height}" class="portrait" xml:space="preserve" opacity="0">{html.escape(row)}<animate attributeName="opacity" from="0" to="1" begin="{0.2 + index * 0.045:.2f}s" dur="0.01s" fill="freeze"/></text>'
        for index, row in enumerate(rows)
    )


def render_svg(config: TerminalConfig) -> str:
    """Render the full terminal dashboard as one self-contained SVG."""
    rows = portrait_rows(config)
    commands = TERMINAL_PROFILE["commands"]
    info = TERMINAL_PROFILE["system_info"]
    text_rows = [
        f"{TERMINAL_PROFILE['user']}@{TERMINAL_PROFILE['host']}:~$ {commands[0]}",
        "Vaistnav Kumar",
        f"{TERMINAL_PROFILE['user']}@{TERMINAL_PROFILE['host']}:~$ {commands[1]}",
        *[f"{key:<9}: {value}" for key, value in info],
        f"{TERMINAL_PROFILE['user']}@{TERMINAL_PROFILE['host']}:~$ {commands[2]}",
        TERMINAL_PROFILE["mission"],
    ]
    y_start = config.title_bar_height + 42
    rows_markup = "\n".join(
        terminal_row(
            row,
            y_start + index * 27,
            index,
            config,
            "prompt" if "$ " in row else "output",
        )
        for index, row in enumerate(text_rows)
    )
    final_y = y_start + len(text_rows) * 27
    cursor_begin = 0.3 + len(text_rows) * config.row_delay
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="100%" viewBox="0 0 {config.width} {config.height}" role="img" aria-labelledby="title desc">
<title id="title">Vaistnav Kumar terminal dashboard</title>
<desc id="desc">A macOS-style terminal with an ASCII portrait and typed system information.</desc>
<rect width="100%" height="100%" rx="20" fill="#0d1117"/>
<path d="M20 0h1020a20 20 0 0 1 20 20v52H0V20A20 20 0 0 1 20 0z" fill="#161b22"/>
<circle cx="38" cy="36" r="9" fill="#ff5f57"/><circle cx="68" cy="36" r="9" fill="#febc2e"/><circle cx="98" cy="36" r="9" fill="#28c840"/>
<text x="530" y="42" text-anchor="middle" class="window-title">{html.escape(TERMINAL_PROFILE['title'])}</text>
<path d="M246 98V512" stroke="#30363d"/>
<style>
  .window-title {{ fill: #8b949e; font: 500 16px ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace; }}
  .portrait {{ fill: #86efac; font: 10px ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace; }}
  .prompt {{ fill: #3fb950; font: 15px ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace; }}
  .output {{ fill: #c9d1d9; font: 15px ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace; }}
  .cursor {{ fill: #3fb950; }}
</style>
{portrait_markup(rows, config)}
{rows_markup}
<rect x="278" y="{final_y - 16}" width="9" height="17" class="cursor" opacity="0"><set attributeName="opacity" to="1" begin="{cursor_begin:.2f}s" fill="freeze"/><animate attributeName="opacity" values="1;0;1" dur="0.9s" begin="{cursor_begin:.2f}s" repeatCount="indefinite"/></rect>
</svg>
'''


def build_terminal(config: TerminalConfig = TerminalConfig()) -> Path:
    """Generate the terminal dashboard SVG from local portrait and profile data."""
    svg = render_svg(config)
    config.output_path.parent.mkdir(parents=True, exist_ok=True)
    config.output_path.write_text(svg, encoding="utf-8")
    LOGGER.info("Wrote %s", config.output_path)
    return config.output_path


def main() -> None:
    """Build the terminal dashboard."""
    configure_logging()
    try:
        build_terminal()
    except (FileNotFoundError, OSError, TypeError, ValueError) as error:
        LOGGER.error("Terminal dashboard generation failed: %s", error)
        raise SystemExit(1) from error


if __name__ == "__main__":
    main()
