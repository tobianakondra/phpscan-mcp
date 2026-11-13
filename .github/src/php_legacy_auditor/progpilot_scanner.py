"""MCP tool: run progpilot scan on a target directory.

Progpilot is a static application security testing (SAST) tool for PHP.
It is invoked as a subprocess with a strict argument list (no shell=True),
with a hard timeout, on a target that must resolve inside ALLOWED_AUDIT_ROOT.
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


def _find_progpilot_binary() -> str | None:
    """Locate the progpilot binary (PATH first, then vendor/bin)."""
    if shutil.which("progpilot"):
        return "progpilot"
    vendor = Path(__file__).resolve().parents[2] / "vendor" / "bin" / "progpilot"
    if vendor.exists():
        return str(vendor)
    return None


@mcp.tool()
def run_progpilot_scan(target: str, config: str | None = None) -> dict:
    """Run Progpilot on *target* and return a filtered JSON report.

    Progpilot output is parsed into the compact event model:
    file, line, severity, rule, message, snippet.
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

    binary = _find_progpilot_binary()
    if binary is None:
        return {
            "success": False,
            "status": "not_installed",
            "message": "Progpilot binary not found. Install it with: "
            "composer require --dev designsecurity/progpilot",
            "bin": None,
        }

    cmd = [binary, str(resolved)]
    if config:
        cmd += ["--configuration", config]

    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120,
        )
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "status": "timeout",
            "message": "Progpilot timed out after 120s",
            "target": str(resolved),
        }

    output = proc.stdout or ""
    errors = proc.stderr or ""

    if proc.returncode not in (0, 1):
        return {
            "success": False,
            "status": "error",
            "message": errors.strip() or "Progpilot failed",
            "target": str(resolved),
            "returncode": proc.returncode,
            "output": output,
        }

    if proc.returncode == 0 and not output.strip():
        return {
            "success": True,
            "status": "clean",
            "target": str(resolved),
            "findings": [],
            "bin": shutil.which("progpilot") or "vendor/bin/progpilot",
        }

    findings = _parse_progpilot_lines(output)
    return {
        "success": True,
        "status": "findings" if findings else "clean",
        "target": str(resolved),
        "findings": findings,
        "bin": shutil.which("progpilot") or "vendor/bin/progpilot",
        "raw_output_lines": len(output.splitlines()),
    }


def _parse_progpilot_lines(output: str) -> list[dict]:
    """Parse Progpilot's text output into the compact finding model.

    The exact Progpilot text format varies between versions; the parser is
    deliberately tolerant and keeps only the useful fields.
    """
    findings: list[dict] = []
    for raw in output.splitlines():
        line = raw.strip()
        if not line or line.startswith("Progpilot"):
            continue
        parts = line.split(":")
        if len(parts) < 2:
            continue
        file_part = parts[0].strip()
        rest = ":".join(parts[1:]).strip()
        line_no = None
        message = rest
        for chunk in rest.split():
            if chunk.isdigit():
                try:
                    line_no = int(chunk)
                    message = rest[len(chunk) :].strip()
                    break
                except ValueError:
                    pass
        if not file_part.endswith(".php"):
            continue
        findings.append(
            {
                "file": file_part,
                "line": line_no,
                "rule": "progpilot",
                "severity": "warning",
                "message": message or line,
                "snippet": "",
            }
        )
    return findings
