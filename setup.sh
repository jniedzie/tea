#!/bin/bash

if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
  echo "setup.sh must be sourced: source tea/setup.sh" >&2
  exit 2
fi

_tea_setup_script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
_tea_setup_repo_root="$(cd "${_tea_setup_script_dir}/.." && pwd)"

# shellcheck source=environment/activate.sh
source "${_tea_setup_script_dir}/environment/activate.sh"
tea_env_activate || return $?

export PYTHONPATH="${_tea_setup_repo_root}/bin${PYTHONPATH:+:${PYTHONPATH}}"
export LD_LIBRARY_PATH="${_tea_setup_repo_root}/bin${LD_LIBRARY_PATH:+:${LD_LIBRARY_PATH}}"

unset _tea_setup_script_dir _tea_setup_repo_root
