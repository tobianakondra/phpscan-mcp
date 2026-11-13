"""MCP tool: run phpcs scan on a target directory.

PHPCS is a sniffer for PHP code style and PHP security rules.
It is invoked through Composer's vendor/bin, with a hard timeout, on a
target that must resolve inside ALLOWED_AUDIT_ROOT. The server never
modifies files: the tool only reads and reports.
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


def _find_phpcs_binary() -> str | None:
    """Locate the phpcs binary (vendor/bin first, then PATH)."""
    vendor = Path(__file__).resolve().parents[2] / "vendor" / "bin" / "phpcs"
    if vendor.exists():
        return str(vendor)
    which = shutil.which("phpcs")
    return which if which else None


@mcp.tool()
def run_phpcs_scan(target: str, standard: str = "PSR12") -> dict:
    """Run PHPCS on *target* and return a filtered JSON report.

    The tool is read-only. PHPCS is invoked with --report=json, so the
    server parses the JSON output and keeps only the findings that matter.
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

    binary = _find_phpcs_binary()
    if binary is None:
        return {
            "success": False,
            "status": "not_installed",
            "message": "PHPCS binary not found. Install it with: "
            "composer require --dev squizlabs/php_codesniffer",
            "bin": None,
        }

    # PHPCS 3.13 only reports messages when severities are high enough;
    # pass the levels as separate arguments (--runtime-set key value).
    cmd = [
        binary,
        f"--standard={standard}",
        "--report=json",
        f"--report-width={100}",
        str(resolved),
    ]

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
            "message": "PHPCS timed out after 120s",
            "target": str(resolved),
        }

    output = proc.stdout or ""
    errors = proc.stderr or ""

    # PHPCS exits with 0 (no violations), 1 (violations found) or 2
    # (fatal internal error). Only a 3 means a real execution error.
    if proc.returncode not in (0, 1, 2):
        return {
            "success": False,
            "status": "error",
            "message": errors.strip() or "PHPCS failed",
            "target": str(resolved),
            "returncode": proc.returncode,
            "output": output,
        }

    findings = _filter_phpcs_findings(output)
    return {
        "success": True,
        "status": "findings" if findings else "clean",
        "target": str(resolved),
        "findings": findings,
        "bin": shutil.which("phpcs") or "vendor/bin/phpcs",
        "standard": standard,
        "raw_output_lines": len(output.splitlines()),
    }


def _filter_phpcs_findings(json_text: str) -> list[dict]:
    """Parse the PHPCS JSON report and keep the security-relevant lines.

    Only the compact event model is returned:
    file, line, severity, rule, message, snippet.
    PHPCS severity maps to our schema; the detector retains the findings
    that are interesting for a legacy PHP audit.
    """
    try:
        import json

        data = json.loads(json_text)
    except (ValueError, TypeError):
        logger.debug("PHPCS returned non-JSON output, not filtering findings")
        return []

    findings: list[dict] = []
    files = data.get("files", {})
    for file_path, messages in files.items():
        if isinstance(messages, str):
            # PHPCS 3.13 can emit top-level totals as strings; skip them.
            continue
        for message in messages or []:
            if isinstance(message, str):
                # Fallback: one message per line (not expected with --report=json).
                # Keep only real messages; skip totals like 'errors', 'warnings'.
                msg = message.strip()
                if msg.lower() in ("errors", "warnings", "messages", "fixable"):
                    continue
                findings.append(
                    {
                        "file": file_path,
                        "line": None,
                        "rule": "phpcs",
                        "severity": "info",
                        "message": msg,
                        "snippet": "",
                    }
                )
                continue
            # Skip PHPCS metadata (totals) and keep actual messages.
            if message.get("source") is None:
                continue
            parts = message.get("message", "").split(":", 1)
            rule = message.get("source") or "phpcs"
            message_text = parts[1].strip() if len(parts) > 1 else message.get("message", "")
            severity = str(message.get("severity", "")).lower()
            # PHPCS 3.13.x emits only error/warning/notice/info; keep
            # everything (known severities all map).
            findings.append(
                {
                    "file": file_path,
                    "line": message.get("line"),
                    "rule": rule,
                    "severity": severity,
                    "message": message_text,
                    "snippet": "",
                }
            )
    return findings
