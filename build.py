"""Regenerate every locally hosted GitHub profile asset in one command."""

from __future__ import annotations

import logging
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


LOGGER = logging.getLogger(__name__)
PROJECT_ROOT = Path(__file__).resolve().parent


@dataclass(frozen=True)
class BuildStep:
    """One named generator script in the profile build pipeline."""

    name: str
    script: Path


BUILD_STEPS = (
    BuildStep("prepare portrait", PROJECT_ROOT / "scripts" / "prep_photo.py"),
    BuildStep("render ASCII portrait", PROJECT_ROOT / "scripts" / "make_ascii_svg.py"),
    BuildStep("render information card", PROJECT_ROOT / "scripts" / "make_info_card.py"),
    BuildStep("fetch contributions", PROJECT_ROOT / "scripts" / "fetch_contributions.py"),
    BuildStep("render contribution heatmap", PROJECT_ROOT / "scripts" / "render_heatmap_svg.py"),
    BuildStep("render skills", PROJECT_ROOT / "scripts" / "render_skills.py"),
    BuildStep("render timeline", PROJECT_ROOT / "scripts" / "render_timeline.py"),
    BuildStep("render terminal dashboard", PROJECT_ROOT / "scripts" / "render_terminal.py"),
    BuildStep("render footer", PROJECT_ROOT / "scripts" / "render_footer.py"),
)


def configure_logging() -> None:
    """Configure concise logging for the top-level asset build."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


def validate_build_inputs() -> None:
    """Fail early when a required generator or source portrait is absent."""
    required_paths = [PROJECT_ROOT / "photo.jpg", *(step.script for step in BUILD_STEPS)]
    missing_paths = [path.relative_to(PROJECT_ROOT) for path in required_paths if not path.is_file()]
    if missing_paths:
        missing = ", ".join(str(path) for path in missing_paths)
        raise FileNotFoundError(f"Required build inputs are missing: {missing}")


def run_step(step: BuildStep) -> None:
    """Run one generator script and raise immediately if it fails."""
    LOGGER.info("Building: %s", step.name)
    environment = os.environ.copy()
    environment.setdefault("TQDM_DISABLE", "1")
    subprocess.run(
        [sys.executable, str(step.script)],
        cwd=PROJECT_ROOT,
        env=environment,
        check=True,
    )


def build_profile() -> None:
    """Execute every profile generator in dependency-safe order."""
    validate_build_inputs()
    for step in BUILD_STEPS:
        run_step(step)
    LOGGER.info("Profile assets regenerated successfully.")


def main() -> None:
    """Run the complete profile build with clear failure logging."""
    configure_logging()
    try:
        build_profile()
    except (FileNotFoundError, subprocess.CalledProcessError) as error:
        LOGGER.error("Profile build failed: %s", error)
        raise SystemExit(1) from error


if __name__ == "__main__":
    main()
