#!/usr/bin/env bash
# Run every legacy PHP auditor tool on the sample vulnerable app and print a
# consolidated JSON report.
set -euo pipefail

cd "$(dirname "$0")/.."

export ALLOWED_AUDIT_ROOT="${ALLOWED_AUDIT_ROOT:-/tmp/php_legacy_auditor_step2}"

mkdir -p "$ALLOWED_AUDIT_ROOT"
: > "$ALLOWED_AUDIT_ROOT/.keep"

exec python3 scripts/test_all.py
