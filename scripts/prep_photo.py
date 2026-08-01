"""Prepare a portrait for the GitHub-profile ASCII SVG generator."""

from __future__ import annotations

import argparse
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

import cv2
import numpy as np
from PIL import Image
from rembg import remove


LOGGER = logging.getLogger(__name__)
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = PROJECT_ROOT / "photo.jpg"
DEFAULT_OUTPUT = PROJECT_ROOT / "source-prepped.png"


@dataclass(frozen=True)
class PhotoPreparationConfig:
    """Paths and processing settings for a prepared portrait."""

    input_path: Path
    output_path: Path
    clip_limit: float = 2.0
    tile_grid_size: tuple[int, int] = (8, 8)


def configure_logging() -> None:
    """Configure concise logging for command-line execution."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


def parse_args(arguments: Sequence[str] | None = None) -> PhotoPreparationConfig:
    """Parse optional input and output paths from command-line arguments."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input",
        type=Path,
        default=DEFAULT_INPUT,
        help=f"Source portrait (default: {DEFAULT_INPUT.name}).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help=f"Prepared PNG (default: {DEFAULT_OUTPUT.name}).",
    )
    parsed = parser.parse_args(arguments)
    return PhotoPreparationConfig(
        input_path=parsed.input.expanduser().resolve(),
        output_path=parsed.output.expanduser().resolve(),
    )


def load_photo(input_path: Path) -> Image.Image:
    """Load an input image as RGB and reject missing or invalid files."""
    if not input_path.is_file():
        raise FileNotFoundError(f"Input photo does not exist: {input_path}")

    try:
        with Image.open(input_path) as image:
            return image.convert("RGB")
    except OSError as error:
        raise ValueError(f"Could not read input photo: {input_path}") from error


def remove_background(image: Image.Image) -> Image.Image:
    """Remove the image background and return a transparent RGBA cutout."""
    result = remove(image)
    if not isinstance(result, Image.Image):
        raise TypeError("Background removal did not return an image.")
    return result.convert("RGBA")


def composite_on_white(cutout: Image.Image) -> Image.Image:
    """Place an alpha-aware cutout onto an opaque white RGB background."""
    background = Image.new("RGBA", cutout.size, "white")
    background.alpha_composite(cutout)
    return background.convert("RGB")


def apply_clahe_and_sharpen(
    image: Image.Image,
    config: PhotoPreparationConfig,
) -> Image.Image:
    """Create a contrast-enhanced, sharpened grayscale portrait."""
    image_array = np.asarray(image)
    grayscale = cv2.cvtColor(image_array, cv2.COLOR_RGB2GRAY)
    clahe = cv2.createCLAHE(
        clipLimit=config.clip_limit,
        tileGridSize=config.tile_grid_size,
    )
    enhanced = clahe.apply(grayscale)
    sharpened = cv2.filter2D(
        enhanced,
        ddepth=-1,
        kernel=np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]]),
    )
    return Image.fromarray(sharpened, mode="L")


def prepare_photo(config: PhotoPreparationConfig) -> Path:
    """Process a portrait and write the grayscale, white-background PNG."""
    LOGGER.info("Loading %s", config.input_path)
    source = load_photo(config.input_path)
    LOGGER.info("Removing background")
    cutout = remove_background(source)
    LOGGER.info("Compositing on white, enhancing contrast, and sharpening")
    prepared = apply_clahe_and_sharpen(composite_on_white(cutout), config)

    config.output_path.parent.mkdir(parents=True, exist_ok=True)
    prepared.save(config.output_path, format="PNG", optimize=True)
    LOGGER.info("Wrote %s (%dx%d)", config.output_path, *prepared.size)
    return config.output_path


def main(arguments: Sequence[str] | None = None) -> None:
    """Run photo preparation and report a clear command-line error on failure."""
    configure_logging()
    try:
        prepare_photo(parse_args(arguments))
    except (FileNotFoundError, OSError, TypeError, ValueError) as error:
        LOGGER.error("Photo preparation failed: %s", error)
        raise SystemExit(1) from error


if __name__ == "__main__":
    main()
