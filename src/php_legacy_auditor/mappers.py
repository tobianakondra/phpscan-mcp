"""Project structure mapping utilities."""

import os
from pathlib import Path


def map_project_structure(target_dir: str) -> dict:
    """Return a compact structure view of a target directory."""
    root = Path(target_dir)
    return {
        "root": str(root),
        "source_files": [],
        "file_count": 0,
        "entry_point_count": 0,
    }
