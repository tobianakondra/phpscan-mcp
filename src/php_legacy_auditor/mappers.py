"""Structural mapping tools for legacy PHP projects."""

from __future__ import annotations

import re
from pathlib import Path

from .security import validate_safe_path

SUPPORTED_EXTENSIONS = {".php", ".inc", ".html", ".sql"}
ENTRY_POINT_HINTS = ("$_GET", "$_POST", "$_REQUEST", "$_FILES", "$_COOKIE")
MAX_LINES_PER_CALL = 200


def _text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except UnicodeDecodeError:
        return path.read_bytes().decode("utf-8", errors="replace")


def map_project_structure(target_dir: str) -> dict:
    """Return a structural summary of a PHP project rooted at *target_dir*."""
    root = validate_safe_path(target_dir, allow_unset_root=True)
    if not root.is_dir():
        raise ValueError(f"Audit root does not exist or is not a directory: {target_dir}")

    source_files: list[dict] = []
    entry_point_candidates: list[dict] = []
    php_syntax_versions: set[str] = set()

    declared_version = root / "composer.json"
    if declared_version.is_file():
        try:
            import json

            payload = json.loads(declared_version.read_text(encoding="utf-8"))
            php_min = payload.get("require", {}).get("php")
            if php_min:
                php_syntax_versions.add(str(php_min).strip('"`'))
        except (ValueError, OSError):
            pass

    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        suffix = path.suffix.lower()
        if suffix in SUPPORTED_EXTENSIONS:
            source_files.append(
                {
                    "path": str(path.relative_to(root)),
                    "extension": suffix,
                    "size": path.stat().st_size,
                }
            )
        if path.name in {"index.php", "index.html", "index.htm"}:
            entry_point_candidates.append({"file": str(path.relative_to(root)), "reason": "root index"})

    candidate_paths = [p for p in root.iterdir() if p.is_file()]
    for path in candidate_paths:
        if path.suffix.lower() != ".php":
            continue
        text = _text(path)
        for marker in ENTRY_POINT_HINTS:
            if marker in text:
                entry_point_candidates.append(
                    {
                        "file": str(path.relative_to(root)),
                        "reason": f"contains {marker}",
                    }
                )
                break

    if len(php_syntax_versions) == 1:
        probable_php_version = next(iter(php_syntax_versions))
    elif declared_version.is_file():
        probable_php_version = "unknown (composer.json present, version not declared)"
    else:
        probable_php_version = "unknown"

    return {
        "root": str(root),
        "probable_php_version": probable_php_version,
        "source_files": source_files,
        "file_count": len(source_files),
        "probable_entry_points": entry_point_candidates[:20],
        "entry_point_count": len(entry_point_candidates),
    }


def read_code_context(file_path: str, start_line: int, end_line: int) -> dict:
    """Return a compact, line-numbered snippet of *file_path* [start_line, end_line]."""
    path = validate_safe_path(file_path, required_extension=".php", allow_unset_root=True)
    if not path.is_file():
        raise ValueError(f"Not a file: {file_path}")

    if start_line < 1:
        raise ValueError("start_line must be >= 1")
    if end_line < start_line:
        raise ValueError("end_line must be >= start_line")

    return _read_code_context_lines(path, start_line, end_line)


def _read_code_context_lines(path: Path, start_line: int, end_line: int) -> dict:
    lines = _text(path).splitlines()
    total = len(lines)

    visible_start = max(start_line, 1)
    visible_end = min(end_line, total)
    if visible_start > visible_end:
        visible_start = visible_end = min(start_line, total)

    snippet = []
    for index in range(visible_start - 1, visible_end):
        snippet.append({"line": index + 1, "content": lines[index]})

    if len(snippet) >= MAX_LINES_PER_CALL:
        snippet = snippet[:MAX_LINES_PER_CALL]

    return {
        "file": str(path),
        "total_lines": total,
        "start_line": start_line,
        "end_line": end_line,
        "visible_start": visible_start,
        "visible_end": visible_end,
        "lines": snippet,
        "truncated": end_line > visible_end,
        "max_lines_per_call": MAX_LINES_PER_CALL,
    }
