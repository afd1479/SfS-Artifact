#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python3}"

usage() {
    cat <<'EOF'
Usage: bash install.sh [analysis|testbed|all]

Create isolated Python environments and install the SfS dependencies.

  analysis  Install dependencies for reproducing Figures 3--11 (default).
  testbed   Install dependencies used by the Raspberry Pi testbed programs.
  all       Install both environments.

Environment variable:
  PYTHON_BIN  Python 3 interpreter to use (default: python3).

This script installs Python packages only. Raspberry Pi OS packages, IBSS/ad-hoc
network configuration, and Chrony setup require administrator access and are
documented in SfS_RaspberryPi_Testbed_v1.0/docs/RASPBERRY_PI_SETUP.md.
EOF
}

die() {
    printf 'Error: %s\n' "$*" >&2
    exit 1
}

require_python() {
    command -v "$PYTHON_BIN" >/dev/null 2>&1 || \
        die "Python interpreter '$PYTHON_BIN' was not found."
    "$PYTHON_BIN" -c 'import sys; raise SystemExit(0 if sys.version_info.major == 3 else 1)' || \
        die "A Python 3 interpreter is required."
}

install_environment() {
    local label="$1"
    local requirements_file="$2"
    local environment_dir="$3"

    [[ -f "$requirements_file" ]] || \
        die "Missing requirements file: $requirements_file"

    printf '\n[%s] Creating or updating %s\n' "$label" "$environment_dir"
    if [[ ! -x "$environment_dir/bin/python" ]]; then
        "$PYTHON_BIN" -m venv "$environment_dir" || die \
            "Could not create a virtual environment. Install the Python venv package for your operating system and retry."
    fi

    "$environment_dir/bin/python" -m pip install --upgrade pip
    "$environment_dir/bin/python" -m pip install -r "$requirements_file"
    printf '[%s] Installation complete.\n' "$label"
}

install_analysis() {
    install_environment \
        "analysis" \
        "$ROOT_DIR/SfS_Artifact_Reproduction/requirements.txt" \
        "$ROOT_DIR/.venv-analysis"
    printf 'Activate with: source "%s/bin/activate"\n' "$ROOT_DIR/.venv-analysis"
}

install_testbed() {
    install_environment \
        "testbed" \
        "$ROOT_DIR/SfS_RaspberryPi_Testbed_v1.0/requirements.txt" \
        "$ROOT_DIR/.venv-testbed"
    printf 'Activate with: source "%s/bin/activate"\n' "$ROOT_DIR/.venv-testbed"
}

main() {
    local profile="${1:-analysis}"

    case "$profile" in
        -h|--help)
            usage
            ;;
        analysis)
            require_python
            install_analysis
            ;;
        testbed)
            require_python
            install_testbed
            ;;
        all)
            require_python
            install_analysis
            install_testbed
            ;;
        *)
            usage >&2
            die "Unknown installation profile: $profile"
            ;;
    esac
}

main "$@"
