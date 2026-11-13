"""Semgrep wrapper: run the installed binary and convert raw JSON into the auditor's event model."""

from __future__ import annotations

import os
import json
import subprocess
import sys
from pathlib import Path

from .security import ALLOWED_AUDIT_ROOT, validate_safe_path


def _validate_target(target: str) -> Path:
    """Ensure the Semgrep target resolves inside ALLOWED_AUDIT_ROOT."""
    if not ALLOWED_AUDIT_ROOT:
        return Path(target).expanduser()
    root = validate_safe_path(str(Path(ALLOWED_AUDIT_ROOT)))
    candidate = Path(target).expanduser()
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise ValueError(
            f"Semgrep target {target!r} is outside the allowed audit root {root}"
        ) from exc
    return candidate


def _semgrep_executable() -> str:
    """Location of the Semgrep binary installed in the audit virtualenv."""
    return str(Path(sys.prefix) / "bin" / "semgrep")


def run_semgrep_scan(
    target: str,
    config: str = "rules/legacy_php.yaml",
    exit_on_error: bool = False,
) -> dict:
    """Run Semgrep on a single target and return the filtered JSON results.

    Returns a dict with:
        - success: bool
        - semgrep_version: str
        - target: str
        - errors: list[str]
        - findings: list[dict]  # file, line, severity, rule, message, snippet
    """
    binary = _semgrep_executable()
    try:
        version = subprocess.run(
            [binary, "--version"], capture_output=True, text=True, timeout=30
        )
        version = (version.stdout or version.stderr).strip().splitlines()[0]
    except Exception as exc:  # pragma: no cover - defensive
        version = f"unknown ({exc})"

    if not Path(binary).exists():
        return {
            "success": False,
            "error": f"Semgrep binary not found at {binary}",
            "semgrep_version": version,
            "findings": [],
        }

    cmd = [
        binary,
        "scan",
        "--config",
        config,
        "--json",
        str(_validate_target(target)),
    ]
    try:
        proc = subprocess.run(
            cmd, capture_output=True, text=True, timeout=300
        )
    except subprocess.TimeoutExpired as exc:
        return {
            "success": False,
            "error": f"Semgrep timed out after 300s: {exc}",
            "semgrep_version": version,
            "findings": [],
        }

    if proc.returncode not in (0, 1):
        return {
            "success": False,
            "error": proc.stderr.strip() or proc.stdout.strip() or f"semgrep exit {proc.returncode}",
            "semgrep_version": version,
            "findings": [],
        }

    try:
        payload = json.loads(proc.stdout or "{}")
    except json.JSONDecodeError as exc:
        return {
            "success": False,
            "error": f"semgrep produced invalid JSON: {exc}",
            "semgrep_version": version,
            "findings": [],
        }

    findings = _filter_semgrep_output(payload)
    return {
        "success": True,
        "semgrep_version": version,
        "target": str(Path(target).expanduser()),
        "errors": [],
        "findings": findings,
    }


def _filter_semgrep_output(payload: dict) -> list[dict]:
    """Flatten the Semgrep JSON payload into the compact auditor event model."""
    findings: list[dict] = []

    results = payload.get("results") or []
    for result in results:
        message = result.get("extra", {}).get("message") or result.get("check_name") or "Semgrep finding"
        severity = _severity_from_result(result)
        for issue in result.get("issues", []) or []:
            start = issue.get("start") or {}
            end = issue.get("end") or {}
            line = start.get("line") or end.get("line")
            snippet = _first_snippet(result)
            findings.append(
                {
                    "file": result.get("path"),
                    "line": line,
                    "severity": severity,
                    "rule": result.get("check_id") or result.get("extra", {}).get("rule_id") or result.get("check_name"),
                    "message": message,
                    "snippet": snippet,
                }
            )

    if not findings and payload.get("results"):
        for result in payload["results"]:
            line = (result.get("extra", {}) or {}).get("start_line")
            findings.append(
                {
                    "file": result.get("path"),
                    "line": line,
                    "severity": _severity_from_result(result),
                    "rule": result.get("check_id") or result.get("extra", {}).get("rule_id") or result.get("check_name"),
                    "message": result.get("extra", {}).get("message") or result.get("check_name"),
                    "snippet": _first_snippet(result),
                }
            )
    return findings


def _severity_from_result(result: dict) -> str:
    extra = result.get("extra") or {}
    sev = extra.get("severity")
    if sev:
        return str(sev).upper()
    msg = str(result.get("extra", {}).get("message") or "")
    if "eval" in msg.lower() or "command" in msg.lower():
        return "ERROR"
    if "deprecated" in msg.lower() or "obsolete" in msg.lower():
        return "INFO"
    return "WARNING"


def _first_snippet(result: dict) -> str | None:
    body = result.get("snapshot", {}).get("body")
    if body:
        return body.splitlines()[0][:120] if isinstance(body, str) else str(body)[:120]
    return None
