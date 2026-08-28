#!/bin/bash

set -euo pipefail

if [[ "${TEA_TEST_MICROMAMBA:-}" == "1" ]]; then
  prefix=""
  while [[ "$#" -gt 0 ]]; do
    if [[ "$1" == "--prefix" ]]; then
      prefix="$2"
      shift 2
    else
      shift
    fi
  done
  [[ -n "${prefix}" ]]
  [[ -d "${CONDA_PKGS_DIRS}" ]]
  printf '%s\n' "${CONDA_PKGS_DIRS}" > "${TEA_TEST_CACHE_RECORD}"
  printf '%s\n' "${prefix}" > "${TEA_TEST_PREFIX_RECORD}"
  mkdir -p "${prefix}"
  touch "${prefix}/created-by-mock"
  exit 0
fi

framework_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
test_root="$(mktemp -d)"
trap 'rm -rf "${test_root}"' EXIT

source "${framework_dir}/environment/activate.sh"

test_hash="0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"
test_prefix="${test_root}/environments/tea"
mkdir -p "${test_prefix}"
touch "${test_prefix}/sentinel"

tea_env_prepare() {
  TEA_HOME="${test_root}"
  TEA_ENV_PREFIX="${test_prefix}"
  TEA_ENV_MARKER="${test_prefix}/.tea-environment"
  TEA_ENV_LOCK_HASH="${test_hash}"
  TEA_ENV_PLATFORM="linux-64"
  TEA_ENV_LOCK_FILE="${test_root}/unused.lock"
  TEA_MICROMAMBA=/bin/false
  export TEA_HOME TEA_ENV_PREFIX TEA_ENV_LOCK_HASH TEA_ENV_PLATFORM TEA_MICROMAMBA
}

# Simulate a waiter acquiring the installation lock just after another process
# completed the same environment and released it.
simulate_handoff=1
tea_env_wait_for_lock() {
  mkdir "$1"
  if [[ "${simulate_handoff}" == "1" ]]; then
    printf '%s\n' "${test_hash}" > "$2"
  fi
}

tea_env_ensure

[[ -f "${test_prefix}/sentinel" ]]
[[ ! -d "${test_prefix}.installing" ]]

rm -rf "${test_prefix}"
mkdir -p "${test_root}/tmp"
simulate_handoff=0
TEA_TEST_MICROMAMBA=1
TEA_TEST_CACHE_RECORD="${test_root}/package-cache"
TEA_TEST_PREFIX_RECORD="${test_root}/install-prefix"
TMPDIR="${test_root}/tmp"
export TEA_TEST_MICROMAMBA TEA_TEST_CACHE_RECORD TEA_TEST_PREFIX_RECORD TMPDIR

tea_env_prepare() {
  TEA_HOME="${test_root}"
  TEA_ENV_PREFIX="${test_prefix}"
  TEA_ENV_MARKER="${test_prefix}/.tea-environment"
  TEA_ENV_LOCK_HASH="${test_hash}"
  TEA_ENV_PLATFORM="linux-64"
  TEA_ENV_LOCK_FILE="${test_root}/unused.lock"
  TEA_MICROMAMBA="${BASH_SOURCE[0]}"
  export TEA_HOME TEA_ENV_PREFIX TEA_ENV_LOCK_HASH TEA_ENV_PLATFORM TEA_MICROMAMBA
}

tea_env_ensure

[[ -f "${test_prefix}/created-by-mock" ]]
[[ "$(< "${test_prefix}/.tea-environment")" == "${test_hash}" ]]
package_cache="$(< "${TEA_TEST_CACHE_RECORD}")"
[[ "${package_cache}" == "${TMPDIR}"/tea-environment-install.*/packages ]]
[[ ! -e "${package_cache}" ]]
[[ "$(< "${TEA_TEST_PREFIX_RECORD}")" == "${test_prefix}" ]]
[[ ! -d "${test_prefix}.installing" ]]

rm -rf "${test_prefix}"
TEA_TEST_PUBLISH_RECORD="${test_root}/publish-prefix"
export TEA_TEST_PUBLISH_RECORD

tea_env_should_stage_publish() {
  return 0
}

tea_env_relocate() {
  mkdir -p "$2"
  cp "$1/created-by-mock" "$2/created-by-mock"
}

tea_env_publish() {
  cp -R "$1" "$2"
  printf '%s\n' "$2" > "${TEA_TEST_PUBLISH_RECORD}"
}

tea_env_ensure

[[ -f "${test_prefix}/created-by-mock" ]]
[[ "$(< "${test_prefix}/.tea-environment")" == "${test_hash}" ]]
[[ "$(< "${TEA_TEST_PREFIX_RECORD}")" == "${TMPDIR}"/tea-environment-install.*/environment ]]
publish_prefix="$(< "${TEA_TEST_PUBLISH_RECORD}")"
[[ "${publish_prefix}" == "${test_prefix}.publishing."* ]]
[[ ! -e "${publish_prefix}" ]]
[[ ! -d "${test_prefix}.installing" ]]

echo "tea environment lock, temporary cache, and staged publication checks passed"
