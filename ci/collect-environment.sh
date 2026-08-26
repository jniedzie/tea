#!/usr/bin/env bash
set -u

label="${1:-$(hostname -s 2>/dev/null || printf unknown)}"
output="${2:-tea-environment-${label}.txt}"
output_stem="${output%.txt}"

{
  printf 'label=%s\n' "${label}"
  printf 'captured_utc=%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  printf '\n[operating system]\n'
  uname -a
  printf 'architecture: %s\n' "$(uname -m)"
  if command -v getconf >/dev/null 2>&1; then
    printf 'libc: '
    getconf GNU_LIBC_VERSION 2>/dev/null || printf 'not reported\n'
  fi
  if [[ -r /etc/os-release ]]; then
    cat /etc/os-release
  elif command -v sw_vers >/dev/null 2>&1; then
    sw_vers
  fi

  printf '\n[commands]\n'
  for command_name in bash cmake c++ gcc g++ clang clang++ clang-format python3 root root-config correction pre-commit ruff conda mamba micromamba; do
    command_path="$(command -v "${command_name}" 2>/dev/null || true)"
    printf '%-12s %s\n' "${command_name}" "${command_path:-not found}"
  done

  printf '\n[versions]\n'
  bash --version 2>/dev/null | head -n 1 || true
  cmake --version 2>/dev/null | head -n 1 || true
  c++ --version 2>/dev/null | head -n 1 || true
  python3 --version 2>&1 || true
  root-config --version 2>/dev/null || true
  root-config --features 2>/dev/null || true
  root-config --cxxstandard 2>/dev/null || true
  correction config --version 2>/dev/null || true
  clang-format --version 2>/dev/null || true
  pre-commit --version 2>/dev/null || true
  ruff --version 2>/dev/null || true

  printf '\n[tea environment]\n'
  printf 'TEA_HOME=%s\n' "${TEA_HOME:-not set}"
  printf 'TEA_ENV_PLATFORM=%s\n' "${TEA_ENV_PLATFORM:-not set}"
  printf 'TEA_ENV_PREFIX=%s\n' "${TEA_ENV_PREFIX:-not set}"
  printf 'TEA_ENV_LOCK_HASH=%s\n' "${TEA_ENV_LOCK_HASH:-not set}"
  if [[ -n "${TEA_HOME:-}" ]]; then
    df -P "${TEA_HOME}" 2>/dev/null || true
  fi

  printf '\n[root]\n'
  for root_option in --prefix --incdir --libdir --libs; do
    printf 'root-config %s: ' "${root_option}"
    root-config "${root_option}" 2>/dev/null || true
  done

  printf '\n[python]\n'
  python3 - <<'PY' 2>/dev/null || true
import platform
import sys
import sysconfig
print("executable:", sys.executable)
print("version:", sys.version.replace("\n", " "))
print("platform:", platform.platform())
print("include:", sysconfig.get_path("include"))
PY

  printf '\n[environment modules]\n'
  if command -v module >/dev/null 2>&1; then
    module list 2>&1 || true
  else
    printf 'module command not found\n'
  fi

  printf '\n[conda packages]\n'
  if command -v conda >/dev/null 2>&1; then
    conda info 2>&1 || true
    conda list 2>&1 || true
  else
    printf 'conda not found\n'
  fi
} > "${output}"

printf 'Wrote %s\n' "${output}"

write_environment_export() {
  local destination temporary
  destination="$1"
  shift
  temporary="$(mktemp "${destination}.tmp.XXXXXX")"
  if "$@" > "${temporary}"; then
    mv "${temporary}" "${destination}"
    printf 'Wrote %s\n' "${destination}"
  else
    rm -f "${temporary}"
    printf 'Could not write %s\n' "${destination}" >&2
  fi
}

if command -v conda >/dev/null 2>&1; then
  conda_target=()
  if [[ -n "${CONDA_PREFIX:-}" ]]; then
    conda_target=(--prefix "${CONDA_PREFIX}")
  fi

  write_environment_export \
    "${output_stem}.conda-explicit.txt" \
    conda list --explicit "${conda_target[@]}"

  if [[ "${#conda_target[@]}" -eq 0 ]]; then
    write_environment_export \
      "${output_stem}.conda-environment.yml" \
      conda env export
  elif conda env export --help 2>&1 | grep -q -- '--prefix'; then
    write_environment_export \
      "${output_stem}.conda-environment.yml" \
      conda env export "${conda_target[@]}"
  else
    printf 'Skipping optional YAML export: this conda-env version does not support prefix-based environments.\n' >&2
  fi

  if [[ -n "${CONDA_PREFIX:-}" && -d "${CONDA_PREFIX}/conda-meta" ]]; then
    write_environment_export \
      "${output_stem}.conda-meta.json" \
      python3 - "${CONDA_PREFIX}/conda-meta" <<'PY'
import glob
import json
import os
import sys

records = []
for path in sorted(glob.glob(os.path.join(sys.argv[1], "*.json"))):
    with open(path, encoding="utf-8") as package_file:
        records.append(json.load(package_file))

json.dump(records, sys.stdout, indent=2, sort_keys=True)
sys.stdout.write("\n")
PY
  fi
fi

if [[ -n "${TEA_MICROMAMBA:-}" && -x "${TEA_MICROMAMBA}" && -n "${TEA_ENV_PREFIX:-}" ]]; then
  write_environment_export \
    "${output_stem}.micromamba-list.txt" \
    "${TEA_MICROMAMBA}" list --prefix "${TEA_ENV_PREFIX}"
fi
