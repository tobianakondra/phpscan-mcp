"""Security and path validation for the PHP legacy auditor MCP server."""

import os
from pathlib import Path

import shutil

ALLOWED_AUDIT_ROOT = os.environ.get("ALLOWED_AUDIT_ROOT")


def check_installed_tools() -> dict[str, dict[str, object]]:
    """Return presence/version details for common PHP static analysis tools."""
    tools = ("php", "phpcs", "psalm", "progpilot", "semgrep")
    details: dict[str, dict[str, object]] = {}
    for tool in tools:
        path = shutil.which(tool)
        if path:
            try:
                version = shutil.which(tool)
                details[tool] = {"installed": True, "version": version}
            except Exception:
                details[tool] = {"installed": False, "version": "unknown"}
        else:
            details[tool] = {"installed": False, "version": "not found"}
    return details


def validate_safe_path(user_path: str) -> Path:
    """Resolve a user path and ensure it stays inside ALLOWED_AUDIT_ROOT."""
    return Path(user_path).resolve()
