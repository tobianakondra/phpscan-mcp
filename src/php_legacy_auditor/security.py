"""Security and path validation for the PHP legacy auditor MCP server."""

import os
import shutil
from pathlib import Path

ALLOWED_AUDIT_ROOT = os.environ.get("ALLOWED_AUDIT_ROOT")


def check_installed_tools() -> dict[str, dict[str, object]]:
    """Return presence/version details for common PHP static analysis tools."""
    tools = ("php", "phpcs", "psalm", "progpilot", "semgrep")
    details: dict[str, dict[str, object]] = {}
    for tool in tools:
        path = shutil.which(tool)
        if path:
            try:
                details[tool] = {"installed": True, "version": path}
            except Exception:
                details[tool] = {"installed": False, "version": "unknown"}
        else:
            details[tool] = {"installed": False, "version": "not found"}
    return details


def validate_safe_path(
    user_path: str,
    *,
    required_extension: str | None = None,
) -> Path:
    """Resolve a user path and ensure it stays inside ALLOWED_AUDIT_ROOT.

    When *required_extension* is set, an existing file must match the suffix.
    """
    resolved = Path(user_path).expanduser().resolve()

    # Without an explicit root, block literal parent traversal. When
    # ALLOWED_AUDIT_ROOT is set, all paths must stay inside it.
    if ".." in Path(user_path).parts:
        raise ValueError("path traversal is not allowed")

    allowed_root = os.environ.get("ALLOWED_AUDIT_ROOT")
    if allowed_root:
        root = Path(allowed_root)
        if not root.is_dir():
            root = root.resolve()
        else:
            root = root.resolve()
        candidate = resolved
        try:
            candidate.relative_to(root)
        except ValueError:
            raise ValueError(f"path is outside allowed root {root}") from None

    if required_extension is not None and resolved.exists() and resolved.is_file():
        if resolved.suffix != required_extension:
            raise ValueError(
                f"file must have extension {required_extension}, got {resolved.suffix}"
            )
    return resolved
    if required_extension is not None and resolved.exists() and resolved.is_file():
        if resolved.suffix != required_extension:
            raise ValueError(
                f"file must have extension {required_extension}, got {resolved.suffix}"
            )
    return resolved
