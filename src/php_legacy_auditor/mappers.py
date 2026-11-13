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


def read_code_context(target_file: str, lines_before: int = 5, lines_after: int = 5) -> str:
    """Return a snippet of source code around the relevant region."""
    path = Path(target_file)
    if not path.is_file():
        return ""
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return ""
    start = max(0, len(lines) - lines_before - 1)
    snippet = "\n".join(lines[start : start + lines_before + lines_after])
    return snippet
    """Return a compact structure view of a target directory."""
    root = Path(target_dir)
    return {
        "root": str(root),
        "source_files": [],
        "file_count": 0,
        "entry_point_count": 0,
    }
