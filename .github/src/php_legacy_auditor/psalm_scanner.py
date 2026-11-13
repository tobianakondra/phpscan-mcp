"""MCP tool: run psalm scan on a target directory.

Psalm is a static analysis tool for PHP. It is invoked through Composer's
vendor/bin, with a hard timeout, on a target that must resolve inside
ALLOWED_AUDIT_ROOT. The server never modifies files: the tool only reads and
reports.
"""

from __future__ import annotations

import logging
import shutil
import subprocess
from pathlib import Path

from mcp.server.fastmcp import FastMCP

from php_legacy_auditor.security import (
    ALLOWED_AUDIT_ROOT,
    validate_safe_path,
)

logger = logging.getLogger(__name__)
mcp = FastMCP("php-legacy-auditor")


def _find_psalm_binary() -> str | None:
    """Locate the psalm binary (vendor/bin first, then PATH)."""
    vendor = Path(__file__).resolve().parents[2] / "vendor" / "bin" / "psalm"
    if vendor.exists():
        return str(vendor)
    which = shutil.which("psalm")
    return which if which else None


@mcp.tool()
def run_psalm_scan(target: str, config: str = "psalm.xml") -> dict:
    """Run Psalm on *target* and return the filtered JSON report.

    The tool is read-only. Psalm is invoked through Composer's vendor/bin,
    with a hard timeout, on a target that must resolve inside
    ALLOWED_AUDIT_ROOT.
    """
    if ALLOWED_AUDIT_ROOT is None:
        return {
            "success": False,
            "error": "ALLOWED_AUDIT_ROOT is not configured",
            "status": "error",
        }

    resolved = validate_safe_path(target, allow_unset_root=True)
    if not isinstance(resolved, Path):
        return {"success": False, "error": str(resolved), "status": "error"}

    binary = _find_psalm_binary()
    if binary is None:
        return {
            "success": False,
            "status": "not_installed",
            "message": "Psalm binary not found. Install it with: "
            "composer require --dev vimeo/psalm",
            "bin": None,
        }

    cmd = [
        binary,
        "--no-cache",
        "--show-info=false",
        "--output-format=json",
        "--config",
        config,
        "--",
        str(resolved),
    ]

    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=180,
        )
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "status": "timeout",
            "message": "Psalm timed out after 180s",
            "target": str(resolved),
        }

    output = proc.stdout or ""
    errors = proc.stderr or ""

    # Psalm exits 0 for no issues, 1 for internal error, 2 for issues found.
    if proc.returncode not in (0, 1, 2):
        return {
            "success": False,
            "status": "error",
            "message": errors.strip() or "Psalm failed",
            "target": str(resolved),
            "returncode": proc.returncode,
            "output": output,
        }

    findings = _filter_psalm_findings(output)
    return {
        "success": True,
        "status": "findings" if findings else "clean",
        "target": str(resolved),
        "findings": findings,
        "bin": shutil.which("psalm") or "vendor/bin/psalm",
        "config": config,
        "raw_output_lines": len(output.splitlines()),
    }


def _filter_psalm_findings(json_text: str) -> list[dict]:
    """Parse Psalm's JSON report into the compact event model."""
    try:
        import json

        data = json.loads(json_text)
    except (ValueError, TypeError):
        logger.debug("Psalm returned non-JSON output, not filtering findings")
        return []

    if isinstance(data, list):
        issues = data
    else:
        issues = data.get("issues", [])

    findings: list[dict] = []
    for issue in issues:
        findings.append(
            {
                "file": issue.get("file_name") or issue.get("filePath", ""),
                "line": issue.get("line_from") or issue.get("line"),
                "rule": issue.get("shortcode", "psalm"),
                "severity": issue.get("severity", "info"),
                "message": issue.get("message", ""),
                "snippet": issue.get("snippet", ""),
            }
        )
    return findings
