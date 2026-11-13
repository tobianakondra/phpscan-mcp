"""Server entrypoint: FastMCP server exposing the legacy PHP auditor tools.

Tools are read-only: none of them modifies, deletes, or executes the code
that is being audited.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path

from mcp.server.fastmcp import FastMCP

from .mappers import map_project_structure as _map_project_structure, _read_code_context_lines as _read_code_context
from .phpcs_scanner import run_phpcs_scan as _run_phpcs_scan
from .progpilot_scanner import run_progpilot_scan as _run_progpilot_scan
from .psalm_scanner import run_psalm_scan as _run_psalm_scan
from .security import validate_safe_path
from .semgrep_scanner import run_semgrep_scan as _run_semgrep_scan
from .utils import check_installed_tools

logger = logging.getLogger(__name__)
mcp = FastMCP("php-legacy-auditor")


@mcp.tool()
def get_auditor_status() -> dict:
    """Report the configured allowed audit root and the installed binaries."""
    allowed_root = os.environ.get("ALLOWED_AUDIT_ROOT")
    try:
        resolved_root = validate_safe_path(".") if allowed_root else None
    except ValueError:
        resolved_root = None

    return {
        "allowed_audit_root": allowed_root,
        "resolved_allowed_audit_root": str(resolved_root) if resolved_root else None,
        "binaries": {
            name: {
                "installed": details["installed"],
                "version": details["version"],
            }
            for name, details in check_installed_tools().items()
        },
    }


@mcp.tool()
def map_project_structure(target_dir: str) -> dict:
    """List the structure of a PHP project and hint at its entry points."""
    return _map_project_structure(target_dir)


@mcp.tool()
def read_code_context(file_path: str, start_line: int, end_line: int) -> dict:
    """Read a bounded portion of a PHP file with line numbers."""
    return _read_code_context(Path(file_path), start_line, end_line)


@mcp.tool()
def run_semgrep_scan(target: str, config: str = "rules/legacy_php.yaml") -> dict:
    """Run Semgrep over a PHP project and return the filtered findings."""
    return _run_semgrep_scan(target, config)


@mcp.tool()
def run_progpilot_scan(target: str, config: str | None = None) -> dict:
    """Run Progpilot over a PHP project and return the filtered findings."""
    return _run_progpilot_scan(target, config)


@mcp.tool()
def run_psalm_scan(target: str, config: str = "psalm.xml") -> dict:
    """Run Psalm over a PHP project and return the filtered findings."""
    return _run_psalm_scan(target, config)


@mcp.tool()
def run_phpcs_scan(target: str, standard: str = "PSR12") -> dict:
    """Run PHPCS over a PHP project and return the filtered findings."""
    return _run_phpcs_scan(target, standard)
