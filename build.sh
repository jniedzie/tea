#!/bin/bash

_build_sh_sourced=0
[[ "${BASH_SOURCE[0]}" != "$0" ]] && _build_sh_sourced=1

_build_sh_restore_history=0
if [[ "${_build_sh_sourced}" -eq 1 && $- == *i* ]]; then
  if set -o | grep -q '^history[[:space:]]*on$'; then
    _build_sh_restore_history=1
    set +o history
  fi
fi

build_main() (
  set -euo pipefail

  script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  repo_root="$(cd "${script_dir}/.." && pwd)"
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
    read -r -a correction_cmake_args <<< "$(PYTHONNOUSERSITE=1 correction config --cmake)"
    cmake_args=("${correction_cmake_args[@]}" "${cmake_args[@]}")
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
  _build_sh_script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  export PYTHONPATH="${PYTHONPATH:-}:$(cd "${_build_sh_script_dir}/.." && pwd)/bin/"
else
  _build_sh_status=$?
fi

unset -f build_main

if [[ "${_build_sh_sourced}" -eq 1 ]]; then
  [[ "${_build_sh_restore_history}" -eq 1 ]] && set -o history
  unset _build_sh_sourced _build_sh_restore_history _build_sh_script_dir
  return "${_build_sh_status}"
fi

unset _build_sh_sourced _build_sh_restore_history _build_sh_script_dir
exit "${_build_sh_status}"
