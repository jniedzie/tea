#!/bin/bash

_build_sh_is_sourced=0
if [[ "${BASH_SOURCE[0]}" != "$0" ]]; then
  _build_sh_is_sourced=1
  _build_sh_saved_shell_opts="$(set +o)"
  _build_sh_saved_shopt_opts="$(shopt -p dotglob nullglob 2>/dev/null || true)"
fi

build_main() {
set -euo pipefail

start_dir="$(pwd)"
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "${script_dir}/.." && pwd)"
build_dir="${repo_root}/build"
bin_dir="${repo_root}/bin"

mkdir -p "${bin_dir}"
mkdir -p "${build_dir}"

clean_build_dirs() {
  shopt -s dotglob nullglob
  rm -rf "${build_dir}"/* "${bin_dir}"/*
  shopt -u dotglob nullglob
}

if [[ "${1:-}" == "--clean" ]]; then
  echo "Cleaning build and bin directories..."
  clean_build_dirs
fi

current_build_env="$(
  printf 'ROOTSYS=%s\n' "${ROOTSYS:-}"
  printf 'CONDA_PREFIX=%s\n' "${CONDA_PREFIX:-}"
  printf 'PYTHON3=%s\n' "$(command -v python3 || true)"
  printf 'CMAKE=%s\n' "$(command -v cmake || true)"
  printf 'CORRECTION=%s\n' "$(command -v correction || true)"
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
if command -v correction &> /dev/null; then
  read -r -a correction_cmake_args <<< "$(PYTHONNOUSERSITE=1 correction config --cmake)"
  cmake_args=("${correction_cmake_args[@]}" "${cmake_args[@]}")
fi

if ! cmake "${cmake_args[@]}"; then
  echo "Initial CMake configure failed; retrying with a fresh cache..."
  rm -f CMakeCache.txt
  rm -rf CMakeFiles
  cmake "${cmake_args[@]}"
fi

cmake --build . --parallel --target install
# make links to all python files, even if not rebuilding. Include directories (if exist, and recursively):
# configs, utils, tea/configs:
find "${repo_root}" -name "*.py" -type f -exec ln -sf {} "${bin_dir}" \;

export PYTHONPATH="${PYTHONPATH:-}:${bin_dir}/"
cd "${start_dir}"
}

if build_main "$@"; then
  _build_sh_status=0
else
  _build_sh_status=$?
fi

if [[ "${_build_sh_is_sourced}" -eq 1 ]]; then
  eval "${_build_sh_saved_shell_opts}"
  eval "${_build_sh_saved_shopt_opts}"
  unset _build_sh_saved_shell_opts _build_sh_saved_shopt_opts _build_sh_is_sourced
  return "${_build_sh_status}"
fi

exit "${_build_sh_status}"
