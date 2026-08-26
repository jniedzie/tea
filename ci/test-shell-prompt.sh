#!/bin/bash

set -euo pipefail

if [[ "$-" != *i* ]]; then
  echo "Run this check with an interactive Bash shell: bash -i ci/test-shell-prompt.sh" >&2
  exit 1
fi

framework_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
original_prompt=$'\[\033[01;32m\]user@host\[\033[00m\]:\n\[\033[01;34m\]work\[\033[00m\]\\$ '
PS1="${original_prompt}"

source "${framework_dir}/environment/activate.sh"
tea_env_activate

[[ "${TEA_ENV_NAME}" == "tea" ]]
[[ "${TEA_ENV_PREFIX}" == "${TEA_HOME}/environments/tea" ]]
[[ "${CONDA_DEFAULT_ENV}" == "tea" ]]
[[ "${CONDA_PROMPT_MODIFIER}" == "(tea) " ]]
[[ "${PS1}" == "(tea) ${original_prompt}" ]]

# Activating again must not grow another prompt prefix.
tea_env_activate
[[ "${PS1}" == "(tea) ${original_prompt}" ]]

echo "tea shell prompt check passed"
