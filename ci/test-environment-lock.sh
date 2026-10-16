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

# A real lock records its installer, and an existing lock reports that owner
# immediately. Replace sleep only for the timeout case so this test stays fast.
lock_dir="${test_root}/probe.installing"
ready_path="${test_root}/probe.ready"
tea_env_wait_for_lock "${lock_dir}" "${ready_path}"
grep -q '^host=.' "${lock_dir}/owner"
grep -Eq '^pid=[0-9]+$' "${lock_dir}/owner"
cp "${lock_dir}/owner" "${test_root}/original-owner"
sleep() { :; }
lock_status=0
tea_env_wait_for_lock "${lock_dir}" "${ready_path}" 2> "${test_root}/lock-error" || lock_status=$?
[[ "${lock_status}" -eq 2 ]]
grep -q 'waiting for installation lock' "${test_root}/lock-error"
grep -q '^host=' "${test_root}/lock-error"
grep -q 'timed out' "${test_root}/lock-error"
cmp "${lock_dir}/owner" "${test_root}/original-owner"
touch "${ready_path}"
lock_status=0
tea_env_wait_for_lock "${lock_dir}" "${ready_path}" || lock_status=$?
[[ "${lock_status}" -eq 1 ]]
rm -rf "${lock_dir}" "${ready_path}"

# A mkdir permission failure is not an occupied lock. Mock the failure so the
# test also works when run by accounts that can write every temporary folder.
mkdir() {
  if [[ "$1" == "${test_root}/permission.installing" ]]; then
    echo "mkdir: permission denied" >&2
    return 1
  fi
  command mkdir "$@"
}
lock_status=0
tea_env_wait_for_lock "${test_root}/permission.installing" "${ready_path}" \
  2> "${test_root}/permission-error" || lock_status=$?
unset -f mkdir
unset -f sleep
[[ "${lock_status}" -eq 2 ]]
grep -q 'unable to create installation lock.*permission denied' "${test_root}/permission-error"
if grep -q 'waiting' "${test_root}/permission-error"; then
  echo "a permission failure must not wait for an installation lock" >&2
  exit 1
fi

# The owner can release a lock just after a waiter gets mkdir's exists error.
lock_dir="${test_root}/released.installing"
mkdir "${lock_dir}"
mkdir() {
  if [[ -d "$1" ]]; then
    rmdir "$1"
    echo "mkdir: file exists" >&2
    return 1
  fi
  command mkdir "$@"
}
tea_env_wait_for_lock "${lock_dir}" "${ready_path}"
unset -f mkdir
[[ -f "${lock_dir}/owner" ]]
rm -rf "${lock_dir}"

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
  printf 'host=test-installer\npid=%s\n' "${BASHPID:-$$}" > "$1/owner"
  if [[ "${simulate_handoff}" == "1" ]]; then
    printf '%s\n' "${test_hash}" > "$2"
  fi
}

tea_env_ensure

[[ -f "${test_prefix}/sentinel" ]]
[[ ! -d "${test_prefix}.installing" ]]

# An interrupted install or a changed lock must preserve the existing runtime.
simulate_handoff=0
rm "${test_prefix}/.tea-environment"
install_status=0
tea_env_ensure 2> "${test_root}/missing-marker-error" || install_status=$?
[[ "${install_status}" -ne 0 ]]
[[ -f "${test_prefix}/sentinel" ]]
[[ ! -e "${test_prefix}/.tea-environment" ]]
[[ ! -d "${test_prefix}.installing" ]]
grep -q 'refusing to replace an existing environment' "${test_root}/missing-marker-error"
printf '%s\n' old-lock > "${test_prefix}/.tea-environment"
install_status=0
tea_env_ensure 2> "${test_root}/changed-lock-error" || install_status=$?
[[ "${install_status}" -ne 0 ]]
[[ -f "${test_prefix}/sentinel" ]]
[[ "$(< "${test_prefix}/.tea-environment")" == old-lock ]]
[[ ! -d "${test_prefix}.installing" ]]
grep -q 'separate TEA_HOME' "${test_root}/changed-lock-error"

rm -rf "${test_prefix}"
mkdir -p "${test_root}/tmp"
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

echo "tea environment lock, prefix preservation, temporary cache, and staged publication checks passed"
