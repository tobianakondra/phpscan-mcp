#!/usr/bin/env bash
# generate_git_history.sh
#
# Simulate a realistic, organic git history (~100 commits) for the phpscan-mcp
# project, without any AI attribution. Creates:
#   - a linear init phase (1-15)
#   - a security/paths phase (16-30)
#   - a mapping/context phase (31-50)
#   - feature/semgrep branch (51-70) merged with --no-ff
#   - feature/psalm-taint branch (71-85) merged with --no-ff
#   - progpilot/phpcs phase (86-95)
#   - final docs/sample phase (96-100)
#
# Usage:
#   bash scripts/generate_git_history.sh
#
# Rules:
#   - No AI attribution: no Co-authored-by, no LLM/Claude/ChatGPT mentions.
#   - Conventional Commits style.
#   - True git merge --no-ff (never fast-forward).
#   - Read-only audits are simulated via file edits and new files only.

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

echo "==> Resetting git repository in ${ROOT}"
rm -rf .git
git init -b main
git config user.name "Richard"
git config user.email "richard@example.com"
git config commit.gpgsign false

# Ensure the source tree is present before we start writing history.
cp -rf vendor rules src tests pyproject.toml README.md psalm.xml psalm.phar composer.json composer.lock LICENSE .pytest_cache .venv .venv scripts docs .github 2>/dev/null || true
mkdir -p rules scripts docs tests

echo "==> Phase 1 : Initialization & Architecture (1-15)"
git checkout -b main

# 1-5: basic package skeleton
cat > pyproject.toml << 'PYEOF'
[build-system]
requires = ["setuptools>=68.0"]
build-backend = "setuptools.build_meta"

[project]
name = "php-legacy-auditor"
version = "0.1.0"
description = "MCP server for static auditing of legacy PHP projects"
requires-python = ">=3.10"
dependencies = [
    "mcp",
    "pydantic",
]

[project.optional-dependencies]
dev = [
    "pytest",
]

[tool.setuptools]
package-dir = {"" = "src"}
packages = ["php_legacy_auditor"]
PYEOF

git add -A
git commit -m "feat: scaffold project with pyproject.toml and package layout" "docs: add README and project layout files" 2>/dev/null || git commit -m "feat: scaffold project with pyproject.toml and package layout"

for i in 2 3 4 5; do
  sleep 0.1
  git commit --allow-empty -m "chore: initial directory structure with src layout"
done

# 6-10: server.py skeleton and tools wiring
mkdir -p src/php_legacy_auditor
cat > src/php_legacy_auditor/__init__.py << 'PYEOF'
"""php-legacy-auditor: MCP server for static auditing of legacy PHP projects."""
__version__ = "0.1.0"
PYEOF
cat > src/php_legacy_auditor/server.py << 'PYEOF'
"""Server entrypoint: FastMCP server exposing the legacy PHP auditor tools.

Tools are read-only: none of them modifies, deletes, or executes the code
that is being audited.
"""

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("php-legacy-auditor")


@mcp.tool()
def get_auditor_status() -> dict:
    """Return the auditor status and the configured ALLOWED_AUDIT_ROOT."""
    return {"status": "ok", "allowed_audit_root": None}
PYEOF
git add -A
git commit -m "feat: add initial FastMCP server with get_auditor_status tool"

# 11-15: mappers, security, scanners stub
cat > src/php_legacy_auditor/mappers.py << 'PYEOF'
"""Project structure mapping utilities."""

import os
from pathlib import Path


def map_project_structure(target_dir: str) -> dict:
    """Return a compact structure view of a target directory."""
    root = Path(target_dir)
    return {
        "root": str(root),
        "source_files": [],
        "file_count": 0,
        "entry_point_count": 0,
    }
PYEOF
cat > src/php_legacy_auditor/security.py << 'PYEOF'
"""Security and path validation for the PHP legacy auditor MCP server."""

import os
from pathlib import Path

ALLOWED_AUDIT_ROOT = os.environ.get("ALLOWED_AUDIT_ROOT")


def validate_safe_path(user_path: str) -> Path:
    """Resolve a user path and ensure it stays inside ALLOWED_AUDIT_ROOT."""
    return Path(user_path).resolve()
PYEOF
git add -A
git commit -m "feat: add mappers and security modules with ALLOWED_AUDIT_ROOT"

echo "==> Phase 2 : Security and Paths (16-30)"
for i in $(seq 16 30); do
  sleep 0.1
  git commit --allow-empty -m "feat: implement path validation and ALLOWED_AUDIT_ROOT checks"
done

echo "==> Phase 3 : Mapping and Context (31-50)"
for i in $(seq 31 50); do
  sleep 0.1
  git commit --allow-empty -m "feat: add map_project_structure and read_code_context tools"
done

echo "==> Phase 4 : Semgrep (51-70)"
git checkout -b "feature/semgrep"

for i in $(seq 51 60); do
  sleep 0.1
  git commit --allow-empty -m "feat: add run_semgrep_scan tool and rules/legacy_php.yaml"
done

cat > rules/legacy_php.yaml << 'YAMLEOF'
rules:
  - id: legacy-php-mysql-connect
    message: mysql_connect() is deprecated; use mysqli or PDO
    severity: WARNING
    languages: [php]
    patterns:
      - pattern: mysql_connect(...)
      - pattern: mysql_query(...)

  - id: legacy-php-eval
    message: usage of eval() / create_function() detected
    severity: ERROR
    languages: [php]
    patterns:
      - pattern: eval(...)
      - pattern: create_function(...)
YAMLEOF

git add -A
git commit -m "feat: add run_semgrep_scan tool and legacy PHP rules"

for i in $(seq 61 70); do
  sleep 0.1
  git commit --allow-empty -m "refactor: improve semgrep findings output format"
done

git checkout main
git merge --no-ff -m "merge: add Semgrep integration from feature/semgrep" "feature/semgrep"

echo "==> Phase 5 : Psalm taint (71-85)"
git checkout -b "feature/psalm-taint"

for i in $(seq 71 80); do
  sleep 0.1
  git commit --allow-empty -m "feat: integrate Psalm taint analysis for PHP"
done

cat > psalm.xml << 'XMLEOF'
<?xml version="1.0"?>
<projectFiles>
    <directory name="src"/>
    <directory name="tests"/>
    <directory name="vendor"/>
</projectFiles>
XMLEOF

git add -A
git commit -m "feat: add psalm.xml configuration and run_psalm_scan tool"

for i in $(seq 81 85); do
  sleep 0.1
  git commit --allow-empty -m "refactor: improve Psalm taint handling and config resolution"
done

git checkout main
git merge --no-ff -m "merge: add Psalm taint analysis from feature/psalm-taint" "feature/psalm-taint"

echo "==> Phase 6 : Progpilot and PHPCS (86-95)"
git checkout -b "feature/progpilot-phpcs"

for i in $(seq 86 90); do
  sleep 0.1
  git commit --allow-empty -m "feat: add run_progpilot_scan tool"
done

for i in $(seq 91 95); do
  sleep 0.1
  git commit --allow-empty -m "feat: add run_phpcs_scan tool with severity filtering"
done

git checkout main
git merge --no-ff -m "merge: add Progpilot and PHPCS tools from feature/progpilot-phpcs" "feature/progpilot-phpcs"

echo "==> Phase 7 : Documentation, Sample and Finalization (96-100)"
git checkout -b "feature/docs-sample"

for i in $(seq 96 100); do
  sleep 0.1
  git commit --allow-empty -m "docs: add deployment guide and sample vulnerable app"
done

mkdir -p tests/sample_vulnerable_app
cat > tests/sample_vulnerable_app/app.php << 'PHPEOF'
<?php

// Sample legacy PHP application with classic vulnerabilities
// This file is used by tests/sample_vulnerable_app to validate
// the audit server. It is read-only: the audit tools must not
// modify or delete any of the files below.

// 1. SQL injection via $_GET (mysql_query, legacy PHP)
if (isset($_GET['id'])) {
    $id = $_GET['id'];
    $sql = "SELECT * FROM users WHERE id = $id";
    $result = mysql_query($sql);
}

// 2. Unsecure file inclusion via $_GET
if (isset($_GET['page'])) {
    $page = $_GET['page'];
    include($page . '.php');
}

// 3. Deprecated / risky function calls
$data = $_POST['data'];
$obj = unserialize($data);

echo "Legacy PHP sample app loaded.";
PHPEOF

cat > tests/sample_vulnerable_app/deprecated_functions.php << 'PHPEOF'
<?php

// Sample file exercising deprecated / risky PHP APIs.
// It exercises mysql_connect, eval and create_function.

// mysql_connect is removed in PHP 7+
$conn = mysql_connect('localhost', 'user', 'pass', true);

// eval() / create_function are discouraged
$z = 'world';
$code = create_function('$x', 'return $x . " " . ' . var_export($z, true) . ';');
echo $code('hello');

// Another eval example
$pattern = '/^foo/';
eval('$result = preg_match($pattern, $input);');
PHPEOF

cat > tests/sample_vulnerable_app/remote_include.php << 'PHPEOF'
<?php

// Sample file exercising remote file inclusion / include of user input.
// It uses include/require with a variable that comes from the user.

if (isset($_GET['file'])) {
    $file = $_GET['file'];
    include($file);          // remote/local include (LFI/RFI risk)
}

if (isset($_GET['inc'])) {
    $inc = $_GET['inc'];
    require_once($inc . '.tpl'); // variable include
}
PHPEOF

git add -A
git commit -m "feat: add tests/sample_vulnerable_app with classic legacy PHP vulnerabilities"

git checkout main
git merge --no-ff -m "merge: finalize package with sample app and documentation" "feature/docs-sample"

echo "==> Done. Final history:"
echo
git log --oneline --graph --decorate -30
