# PHP Legacy Auditor (MCP server)

[![CI](https://github.com/richard/phpscan-mcp/actions/workflows/ci.yml/badge.svg)](https://github.com/richard/phpscan-mcp/actions/workflows/ci.yml)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A **read-only** Model Context Protocol server that audits legacy PHP projects with
four static analysis tools:

| Tool | Purpose |
| --- | --- |
| `run_semgrep_scan` | SAST rules for legacy PHP (`rules/legacy_php.yaml`) |
| `run_psalm_scan` | Type/security analysis (Psalm) |
| `run_progpilot_scan` | Taint analysis for PHP (Progpilot) |
| `run_phpcs_scan` | Code style / PHP coding standards (PHPCS) |

Other tools: `get_auditor_status`, `map_project_structure`, `read_code_context`.

## Requirements

- Python **3.10+**
- PHP **8.1+** (needed by Psalm, Progpilot and PHPCS)
- The official `mcp` SDK (`FastMCP`) — install with `pip install -e .`
- `pydantic` (already a dependency of `mcp`)

### Tool-specific dependencies

Install the dev dependencies with Composer (they ship the PHP binaries):

```bash
composer install --no-interaction --no-progress
```

| Binary | How it is provided |
| --- | --- |
| `semgrep` | Python package, `pip install semgrep` |
| `psalm` | `vendor/bin/psalm` (Composer) |
| `progpilot` | `vendor/bin/progpilot` (Composer) |
| `phpcs` | `vendor/bin/phpcs` (Composer) |

## Configuration

### Allow-listed audit root

The server only ever scans directories **inside** `ALLOWED_AUDIT_ROOT`.
Set it before starting the server:

```bash
export ALLOWED_AUDIT_ROOT=/path/to/legacy-app
python -m php_legacy_auditor.server
```

If `ALLOWED_AUDIT_ROOT` is not set, the tools still run (the server logs a
warning) but the root validation is disabled.

### Server launch

```bash
# With the package installed
mcp serve php_legacy_auditor.server

# Or directly with the SDK
python -m mcp.server.fastmcp php_legacy_auditor.server
```

The FastMCP app is also importable:
`from php_legacy_auditor.server import mcp`.

## Tools reference

| Tool | Arguments | Output |
| --- | --- | --- |
| `get_auditor_status` | — | `allowed_audit_root`, `resolved_allowed_audit_root`, `binaries` |
| `map_project_structure` | `target_dir` | `root`, `source_files`, `probable_php_version`, `entry_points` |
| `read_code_context` | `file_path`, `start_line`, `end_line` | `file`, `lines`, `truncated`, `max_lines_per_call` |
| `run_semgrep_scan` | `target`, `config` | `success`, `findings`, `semgrep_version`, `errors` |
| `run_psalm_scan` | `target`, `config` | `success`, `findings`, `psalm` |
| `run_progpilot_scan` | `target`, `config` | `success`, `status`, `findings`, `bin`, `raw_output_lines` |
| `run_phpcs_scan` | `target`, `standard` | `success`, `status`, `findings`, `bin`, `standard`, `raw_output_lines` |

Every tool is **read-only**: they never modify, delete, or execute the audited
code. Paths are resolved and blocked when they escape `ALLOWED_AUDIT_ROOT`
(`validate_safe_path` / `security.py`). Subprocesses are always invoked with an
argument list and a strict `timeout` (no `shell=True`).

### Output format

Scan tools return a compact JSON event per finding:

```json
{
  "file": "/tmp/app.php",
  "line": 17,
  "severity": "WARNING",
  "rule": "legacy-php-mysql-connect",
  "message": "mysql_connect() is deprecated; use mysqli or PDO",
  "snippet": "<?php mysql_connect(...);"
}
```

## Testing

```bash
# Unit tests (Python level)
python -m pytest tests/ -q

# All four tools on the sample vulnerable app
./scripts/run_all_audits.sh
```

The sample app lives in `tests/sample_vulnerable_app/` and contains classic
legacy PHP vulnerabilties (SQL injection, remote inclusion, `eval()`,
`unserialize()`).

## License

MIT (see `LICENSE`).
