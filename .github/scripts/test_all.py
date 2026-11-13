#!/usr/bin/env python3
"""Global end-to-end test script for the legacy PHP auditor server.

Run::

    python3 scripts/test_all.py

The script is responsible for instantiating the MCP server tools (through the
``mcp`` package) and for calling the underlying Python helpers, then prints a
single consolidated JSON report.  It does not modify any audited file: all four
tools are read-only.
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
import tempfile
from pathlib import Path

# Make the package importable no matter where the script is launched from.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from php_legacy_auditor.server import mcp  # noqa: E402
from php_legacy_auditor.utils import run_tool  # noqa: E402

REPORT = {}


def _sample_dir() -> Path:
    """Directory scanned by the tools: under ALLOWED_AUDIT_ROOT."""
    allowed = os.environ.get("ALLOWED_AUDIT_ROOT")
    if allowed:
        return Path(allowed) / "sample_vulnerable_app"
    # Fallback, when ALLOWED_AUDIT_ROOT is not set (defaulting to a temp dir
    # would require the directory to exist, so we fall back to the repo one).
    return PROJECT_ROOT / "tests" / "sample_vulnerable_app"


SAMPLE_DIR = _sample_dir()


async def _call_tool(name: str, arguments: dict) -> dict:
    """Call an MCP tool and return the parsed (JSON) result."""
    result = await mcp.call_tool(name, arguments)
    text = result[0].text
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {"raw": text, "status": "not_json"}


def run_semgrep(target: str) -> dict:
    return _call_tool("run_semgrep_scan", {"target": target, "config": "rules/legacy_php.yaml"})


def run_psalm(target: str) -> dict:
    return _call_tool("run_psalm_scan", {"target": target})


def run_progpilot(target: str) -> dict:
    return _call_tool("run_progpilot_scan", {"target": target})


def run_phpcs(target: str, standard: str = "PSR12") -> dict:
    return _call_tool("run_phpcs_scan", {"target": target, "standard": standard})


def run_php_context(source: str, start_line: int, end_line: int) -> dict:
    return _call_tool("read_code_context", {"file_path": source, "start_line": start_line, "end_line": end_line})


def run_map_structure(target: str) -> dict:
    return _call_tool("map_project_structure", {"target_dir": target})


async def _main() -> int:
    with tempfile.TemporaryDirectory(prefix="audit-test-") as tmp:
        allowed_root = os.environ.get("ALLOWED_AUDIT_ROOT", tmp)
        os.environ["ALLOWED_AUDIT_ROOT"] = allowed_root

        report: dict = {
            "sample_dir": str(SAMPLE_DIR),
            "allowed_audit_root": allowed_root,
            "tools": {},
        }

        # 1. Static structure
        report["tools"]["map_project_structure"] = await run_map_structure(str(SAMPLE_DIR))
        # 2. Sample directory as a whole
        report["tools"]["map_project_structure/sample1"] = await run_map_structure(str(SAMPLE_DIR))
        # 3. Code context (250-300 on a 300-line file)
        report["tools"]["read_code_context/sample1"] = await run_php_context(
            str(SAMPLE_DIR / "app.php"), 250, 300
        )
        # 4. Semgrep
        report["tools"]["run_semgrep_scan"] = await run_semgrep(str(SAMPLE_DIR))
        # 5. Psalm
        report["tools"]["run_psalm_scan"] = await run_psalm(str(SAMPLE_DIR))
        # 6. Progpilot
        report["tools"]["run_progpilot_scan"] = await run_progpilot(str(SAMPLE_DIR))
        # 7. PHPCS
        report["tools"]["run_phpcs_scan"] = await run_phpcs(str(SAMPLE_DIR), standard="PSR12")

        print(json.dumps(report, indent=2))
    return 0


def main() -> int:
    try:
        return asyncio.run(_main())
    except Exception:
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
