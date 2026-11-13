"""Project structure mapping utilities."""

from pathlib import Path


def map_project_structure(target_dir: str) -> dict:
    """Return a compact structure view of a target directory.

    The summary counts only files with a known PHP source extension.
    """
    root = Path(target_dir)
    source_extensions = {".php", ".phtml", ".inc", ".sql", ".module", ".info"}
    file_count = 0
    entry_points = []

    if root.is_dir():
        for path in root.rglob("*"):
            if not path.is_file():
                continue
            if path.suffix.lower() in source_extensions:
                file_count += 1
                if path.name in {"index.php", "main.php", "config.php", "app.php"}:
                    entry_points.append(str(path))

    return {
        "root": str(root),
        "file_count": file_count,
        "probable_entry_points": entry_points,
    }


def read_code_context(
    target_file: str,
    visible_start: int,
    visible_end: int,
    max_lines: int = 200,
) -> dict:
    """Return a snippet of source code around the requested region.

    The result is capped at *max_lines* and reports whether it was truncated.
    """
    path = Path(target_file)
    if not path.is_file():
        return {
            "visible_start": 0,
            "visible_end": 0,
            "truncated": False,
            "lines": [],
        }

    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return {
            "visible_start": 0,
            "visible_end": 0,
            "truncated": False,
            "lines": [],
        }

    total = len(lines)
    start = max(0, visible_start - 1)
    end = min(total, visible_end)

    if end - start > max_lines:
        end = start + max_lines

    snippet = lines[start:end]
    truncated = end - start >= max_lines or total > max_lines
    return {
        "visible_start": start + 1,
        "visible_end": end,
        "truncated": truncated,
        "lines": [
            {"line": start + offset + 1, "content": content}
            for offset, content in enumerate(snippet)
        ],
    }
