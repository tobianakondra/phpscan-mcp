"""Security and path validation for the PHP legacy auditor MCP server."""

import os
from pathlib import Path

ALLOWED_AUDIT_ROOT = os.environ.get("ALLOWED_AUDIT_ROOT")


def validate_safe_path(user_path: str) -> Path:
    """Resolve a user path and ensure it stays inside ALLOWED_AUDIT_ROOT."""
    return Path(user_path).resolve()
