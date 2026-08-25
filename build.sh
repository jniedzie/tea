#!/bin/bash

_build_sh_sourced=0
if [ -n "${ZSH_VERSION:-}" ]; then
  case "${ZSH_EVAL_CONTEXT:-}" in
    *:file*) _build_sh_sourced=1 ;;
  esac
  _build_sh_self="${(%):-%x}"
elif [ -n "${BASH_SOURCE+x}" ]; then
  [[ "${BASH_SOURCE[0]}" != "$0" ]] && _build_sh_sourced=1
  _build_sh_self="${BASH_SOURCE[0]}"
else
  echo "tea: unsupported shell; use bash or zsh" >&2
  # `return` when sourced, `exit` when executed: never kill the caller's shell.
  return 1 2>/dev/null || exit 1
fi

_build_sh_restore_history=0
if [[ "${_build_sh_sourced}" -eq 1 && -n "${BASH_VERSION:-}" && $- == *i* ]]; then
  if set -o | grep -q '^history[[:space:]]*on$'; then
    _build_sh_restore_history=1
    set +o history
  fi
fi

_build_sh_script_dir="$(cd "$(dirname "${_build_sh_self}")" && pwd)"
# shellcheck source=environment/activate.sh
source "${_build_sh_script_dir}/environment/activate.sh"
if tea_env_activate; then
  _build_sh_status=0
else
  _build_sh_status=$?
  [[ "${_build_sh_restore_history}" -eq 1 ]] && set -o history
  if [[ "${_build_sh_sourced}" -eq 1 ]]; then
    return "${_build_sh_status}"
  fi
  exit "${_build_sh_status}"
fi

build_main() (
  set -euo pipefail

  repo_root="$(cd "${_build_sh_script_dir}/.." && pwd)"
  build_dir="${repo_root}/build"
  bin_dir="${repo_root}/bin"

  mkdir -p "${bin_dir}" "${build_dir}"

  if [[ "${1:-}" == "--clean" ]]; then
    echo "Cleaning build and bin directories..."
    find "${build_dir}" "${bin_dir}" -mindepth 1 -maxdepth 1 -exec rm -rf {} +
  fi

  current_build_env="$(
    printf 'ROOTSYS=%s\n' "${ROOTSYS:-}"
    printf 'CONDA_PREFIX=%s\n' "${CONDA_PREFIX:-}"
    printf 'PYTHON3=%s\n' "$(command -v python3 || true)"
    printf 'CMAKE=%s\n' "$(command -v cmake || true)"
    printf 'CORRECTION=%s\n' "$(command -v correction || true)"
    printf 'ROOT_CONFIG=%s\n' "$(command -v root-config || true)"
    if command -v root-config >/dev/null 2>&1; then
      printf 'ROOT_CONFIG_PREFIX=%s\n' "$(root-config --prefix 2>/dev/null || true)"
      printf 'ROOT_CONFIG_INCDIR=%s\n' "$(root-config --incdir 2>/dev/null || true)"
      printf 'ROOT_CONFIG_LIBDIR=%s\n' "$(root-config --libdir 2>/dev/null || true)"
      printf 'ROOT_CONFIG_CXXSTANDARD=%s\n' "$(root-config --cxxstandard 2>/dev/null || true)"
    fi
  )"

  env_stamp_file="${build_dir}/.build_env"
  if [[ -f "$env_stamp_file" ]] && ! diff -q "$env_stamp_file" <(printf '%s' "$current_build_env") >/dev/null; then
    echo "Build environment changed; clearing cached CMake state..."
    rm -f "${build_dir}/CMakeCache.txt"
    rm -rf "${build_dir}/CMakeFiles"
  fi
  printf '%s' "$current_build_env" > "$env_stamp_file"

  cd "${build_dir}"

  cmake_args=("${repo_root}")
  if command -v correction >/dev/null 2>&1; then
    correction_cmake_args=()
    while IFS= read -r correction_cmake_arg; do
      [[ -n "${correction_cmake_arg}" ]] && correction_cmake_args+=("${correction_cmake_arg}")
    done < <(PYTHONNOUSERSITE=1 correction config --cmake | tr '[:space:]' '\n')
    if [[ "${#correction_cmake_args[@]}" -gt 0 ]]; then
      cmake_args=("${correction_cmake_args[@]}" "${cmake_args[@]}")
    fi
  fi

  if ! cmake "${cmake_args[@]}"; then
    echo "Initial CMake configure failed; retrying with a fresh cache..."
    rm -f CMakeCache.txt
    rm -rf CMakeFiles
    cmake "${cmake_args[@]}" || return $?
  fi

  cmake --build . --parallel --target install || return $?

  # Link python files even when CMake has nothing to rebuild.
  find "${repo_root}" \
    -path "${bin_dir}" -prune -o \
    -path "${build_dir}" -prune -o \
    -name "*.py" -type f -exec ln -sf {} "${bin_dir}" \; || return $?
)

if build_main "$@"; then
  _build_sh_status=0
  export PYTHONPATH="$(cd "${_build_sh_script_dir}/.." && pwd)/bin${PYTHONPATH:+:${PYTHONPATH}}"
else
  _build_sh_status=$?
fi

unset -f build_main

if [[ "${_build_sh_sourced}" -eq 1 ]]; then
  [[ "${_build_sh_restore_history}" -eq 1 ]] && set -o history
  unset _build_sh_sourced _build_sh_restore_history _build_sh_script_dir _build_sh_self
  return "${_build_sh_status}"
fi

unset _build_sh_sourced _build_sh_restore_history _build_sh_script_dir _build_sh_self
exit "${_build_sh_status}"
