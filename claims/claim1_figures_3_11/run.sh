#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
ANALYSIS_DIR="$REPO_ROOT/SfS_Artifact_Reproduction"
PYTHON_BIN="$REPO_ROOT/.venv-analysis/bin/python"

[[ -d "$ANALYSIS_DIR" ]] || {
    printf 'Error: missing directory: %s\n' "$ANALYSIS_DIR" >&2
    exit 1
}

[[ -f "$ANALYSIS_DIR/reproduce_all.py" ]] || {
    printf 'Error: missing reproduction program: %s/reproduce_all.py\n' \
        "$ANALYSIS_DIR" >&2
    exit 1
}

[[ -x "$PYTHON_BIN" ]] || {
    printf 'Error: analysis environment not found. Run bash install.sh analysis first.\n' >&2
    exit 1
}

cd "$ANALYSIS_DIR"
exec "$PYTHON_BIN" reproduce_all.py
