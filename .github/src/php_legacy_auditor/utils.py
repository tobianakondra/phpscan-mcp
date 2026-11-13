"""Utility helpers shared across the MCP tool implementations."""

from __future__ import annotations

import subprocess
from pathlib import Path

from .security import check_installed_tools


def run_tool(
    binary: str,
    args: list[str],
    *,
    timeout: int = 120,
    cwd: str | None = None,
) -> subprocess.CompletedProcess[str]:
    """Run a static analysis binary without a shell.

    ``shell=False`` is always used: arguments are passed as an argument list.
    The process is killed on timeout.
    """
    cmd = [binary, *args]
    return subprocess.run(
        cmd,
        shell=False,
        capture_output=True,
        text=True,
        timeout=timeout,
        cwd=cwd,
    )


def installed(binaries: tuple[str, ...]) -> dict[str, dict[str, object]]:
    """Return presence/version details for the requested binaries."""
    return check_installed_tools()


__all__ = ["run_tool", "installed"]
