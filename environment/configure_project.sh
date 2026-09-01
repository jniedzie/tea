#!/bin/bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FRAMEWORK_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
WORKSPACE_DIR="$(cd "${FRAMEWORK_DIR}/.." && pwd)"

# The path is resolved at runtime so the script also works outside the current checkout.
# shellcheck disable=SC1091
source "${SCRIPT_DIR}/activate.sh"
tea_env_activate

"${TEA_ENV_PREFIX}/bin/python" \
  "${SCRIPT_DIR}/configure_vscode.py" \
  --workspace "${WORKSPACE_DIR}" \
  --framework "${FRAMEWORK_DIR}" \
  --environment "${TEA_ENV_PREFIX}"

echo "Installing pre-commit hooks for tea"
(
  cd "${FRAMEWORK_DIR}"
  pre-commit install
)
