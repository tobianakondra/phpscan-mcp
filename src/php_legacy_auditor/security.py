"""Security and path validation for the PHP legacy auditor MCP server."""

from __future__ import annotations

import os
import subprocess
from contextlib import contextmanager
from pathlib import Path

import shutil

ALLOWED_AUDIT_ROOT = os.environ.get("ALLOWED_AUDIT_ROOT")


BINARIES = (
    "semgrep",
    "psalm",
    "progpilot",
    "phpcs",
    "php",
)


def _env_allowed_root() -> Path | None:
    """Return the resolved ALLOWED_AUDIT_ROOT, or None if unset."""
    raw = os.environ.get("ALLOWED_AUDIT_ROOT")
    if not raw:
        return None

    return Path(raw).expanduser().resolve()


def subprocess_run(
    cmd: list[str],
    *,
    capture_output: bool = False,
    text: bool = False,
    timeout: int | None = None,
) -> subprocess.CompletedProcess[str]:
    """Run a command without a shell, returning the completed process."""
    return subprocess.run(
        cmd,
        shell=False,
        capture_output=capture_output,
        text=text,
        timeout=timeout,
    )


def validate_safe_path(
    user_path: str,
    *,
    required_extension: str | None = None,
    allow_unset_root: bool = False,
) -> Path:
    """Resolve *user_path* and ensure it stays inside the allowed audit root.

    Raises ``ValueError`` when the path is outside the allowed root or when a
    required extension is required and the target is a file with a different
    extension. When *allow_unset_root* is true, the missing environment root is
    not treated as a failure (used for unit tests only).
    """
    raw = Path(user_path)
    if not raw.is_absolute():
        resolved = (Path.cwd() / raw).resolve()
    else:
        resolved = raw.resolve()

    allowed_root = _env_allowed_root()
    if allowed_root is None and not allow_unset_root:
        raise ValueError(
            "ALLOWED_AUDIT_ROOT is not set. Refusing to run auditing outside "
            "an explicitly configured audit root."
        )

    if allowed_root is not None:
        try:
            resolved.relative_to(allowed_root)
        except ValueError as exc:
            raise ValueError(
                f"Path {user_path!r} resolves outside ALLOWED_AUDIT_ROOT "
                f"{allowed_root}"
            ) from exc

    if required_extension is not None and resolved.is_file():
        if resolved.suffix.lower() != required_extension.lower():
            raise ValueError(
                f"Expected a {required_extension} file, got {resolved.suffix}"
            )
    return resolved


@contextmanager
def _temp_env(root: Path):
    """Temporarily set ALLOWED_AUDIT_ROOT for test integrity."""
    old = os.environ.get("ALLOWED_AUDIT_ROOT")
    os.environ["ALLOWED_AUDIT_ROOT"] = str(root)
    try:
        yield
    finally:
        if old is None:
            os.environ.pop("ALLOWED_AUDIT_ROOT", None)
        else:
            os.environ["ALLOWED_AUDIT_ROOT"] = old


def check_installed_tools() -> dict[str, dict[str, object]]:
    """Check the presence and version of the static analysis binaries.

    Returns a mapping tool name -> {binary, installed, version}.
    """
    results: dict[str, dict[str, object]] = {}
    for binary in BINARIES:
        path = shutil.which(binary)
        if path is None:
            results[binary] = {
                "binary": binary,
                "installed": False,
                "version": None,
            }
            continue

        try:
            version_result = subprocess_run(
                [path, "--version"],
                capture_output=True,
                text=True,
                timeout=15,
            )
        except subprocess.TimeoutExpired:
            version_result = None

        version = ""
        if version_result is not None:
            version = (version_result.stdout or version_result.stderr).splitlines()[0].strip()
            if not version:
                version = version_result.stderr.strip().splitlines()[0] if version_result.stderr else ""

        results[binary] = {
            "binary": path,
            "installed": True,
            "version": version or None,
        }
    return results
