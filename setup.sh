#!/bin/bash

if [ -n "${ZSH_VERSION:-}" ]; then
  case "${ZSH_EVAL_CONTEXT:-}" in
    *:file*) ;;
    *)
      echo "setup.sh must be sourced: source tea/setup.sh" >&2
      exit 2
      ;;
  esac
  _tea_setup_self="${(%):-%x}"
elif [ -n "${BASH_SOURCE+x}" ]; then
  if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
    echo "setup.sh must be sourced: source tea/setup.sh" >&2
    exit 2
  fi
  _tea_setup_self="${BASH_SOURCE[0]}"
else
  echo "tea: unsupported shell; use bash or zsh" >&2
  return 2 2>/dev/null || exit 2
fi

_tea_setup_script_dir="$(cd "$(dirname "${_tea_setup_self}")" && pwd)"
_tea_setup_repo_root="$(cd "${_tea_setup_script_dir}/.." && pwd)"

# shellcheck source=environment/activate.sh
source "${_tea_setup_script_dir}/environment/activate.sh"
tea_env_activate || return $?

export PYTHONPATH="${_tea_setup_repo_root}/bin${PYTHONPATH:+:${PYTHONPATH}}"
export LD_LIBRARY_PATH="${_tea_setup_repo_root}/bin${LD_LIBRARY_PATH:+:${LD_LIBRARY_PATH}}"

unset _tea_setup_script_dir _tea_setup_repo_root _tea_setup_self
