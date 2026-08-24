#!/bin/bash

# Internal environment bootstrap used by build.sh and setup.sh. This file is
# sourced; it intentionally does not provide a separate user-facing command.

tea_env_sha256() {
  if command -v sha256sum >/dev/null 2>&1; then
    sha256sum "$1" | awk '{print $1}'
  elif command -v shasum >/dev/null 2>&1; then
    shasum -a 256 "$1" | awk '{print $1}'
  else
    echo "tea: neither sha256sum nor shasum is available" >&2
    return 1
  fi
}

tea_env_platform() {
  case "$(uname -s):$(uname -m)" in
    Linux:x86_64|Linux:amd64)
      printf '%s\n' linux-64
      ;;
    Darwin:arm64|Darwin:aarch64)
      printf '%s\n' osx-arm64
      ;;
    Darwin:x86_64|Darwin:amd64)
      printf '%s\n' osx-64
      ;;
    *)
      echo "tea: unsupported platform $(uname -s)/$(uname -m)" >&2
      return 1
      ;;
  esac
}

tea_env_framework_dir() {
  cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd
}

tea_env_config_file() {
  printf '%s/tea/home\n' "${XDG_CONFIG_HOME:-${HOME}/.config}"
}

tea_env_resolve_home() {
  local config_file configured_home

  if [[ -n "${TEA_HOME:-}" ]]; then
    configured_home="${TEA_HOME}"
  else
    config_file="$(tea_env_config_file)"
    if [[ -r "${config_file}" ]]; then
      IFS= read -r configured_home < "${config_file}"
    else
      configured_home="${HOME}/.tea"
    fi
  fi

  if [[ "${configured_home}" != /* ]]; then
    echo "tea: TEA_HOME must be an absolute path: ${configured_home}" >&2
    return 1
  fi

  mkdir -p "${configured_home}" || return 1
  TEA_HOME="$(cd "${configured_home}" && pwd)"
  export TEA_HOME
}

tea_env_download() {
  local url destination
  url="$1"
  destination="$2"

  if command -v curl >/dev/null 2>&1; then
    curl --fail --location --retry 3 --output "${destination}" "${url}"
  elif command -v wget >/dev/null 2>&1; then
    wget --tries=3 --output-document="${destination}" "${url}"
  else
    echo "tea: curl or wget is required for the first installation" >&2
    return 1
  fi
}

tea_env_wait_for_lock() {
  local lock_dir ready_path attempts
  lock_dir="$1"
  ready_path="$2"
  attempts=0

  while ! mkdir "${lock_dir}" 2>/dev/null; do
    if [[ -e "${ready_path}" ]]; then
      return 1
    fi
    attempts=$((attempts + 1))
    if [[ "${attempts}" -ge 300 ]]; then
      echo "tea: timed out waiting for installation lock ${lock_dir}" >&2
      return 2
    fi
    sleep 1
  done
  return 0
}

tea_env_ensure_micromamba() (
  set -euo pipefail

  local version release_tag platform checksum url tool_dir tool_path available_tool
  local lock_dir temporary actual_checksum lock_status
  version="2.8.1"
  release_tag="2.8.1-0"
  platform="$1"

  available_tool="$(type -P micromamba || true)"
  if [[ -n "${available_tool}" ]] && "${available_tool}" --version >/dev/null 2>&1; then
    printf '%s\n' "${available_tool}"
    exit 0
  fi

  case "${platform}" in
    linux-64)
      checksum="9689782d863c05a1bf5d2d371ba527104e7a4eb4310c1637d8653b751aed9c82"
      ;;
    osx-arm64)
      checksum="de71a646b73af92dd663e6ddc78993a6a4d47ea28b5d8908c3cc2b9c3077e528"
      ;;
    osx-64)
      checksum="b2bd613791c0a524883d7cb66505d630bf15badd1f492bc93ba78550a3a1a94b"
      ;;
    *)
      echo "tea: no micromamba bootstrap is configured for ${platform}" >&2
      exit 1
      ;;
  esac

  tool_dir="${TEA_HOME}/tools/micromamba/${version}"
  tool_path="${tool_dir}/micromamba"
  if [[ -x "${tool_path}" ]] && [[ "$(tea_env_sha256 "${tool_path}")" == "${checksum}" ]]; then
    printf '%s\n' "${tool_path}"
    exit 0
  fi

  mkdir -p "${tool_dir}"
  lock_dir="${tool_dir}.installing"
  lock_status=0
  tea_env_wait_for_lock "${lock_dir}" "${tool_path}" || lock_status=$?
  if [[ "${lock_status}" -eq 1 ]]; then
    if [[ "$(tea_env_sha256 "${tool_path}")" == "${checksum}" ]]; then
      printf '%s\n' "${tool_path}"
      exit 0
    fi
    echo "tea: the shared micromamba binary has an unexpected checksum" >&2
    exit 1
  elif [[ "${lock_status}" -ne 0 ]]; then
    exit "${lock_status}"
  fi

  trap 'rm -f "${temporary:-}"; rmdir "${lock_dir}" 2>/dev/null || true' EXIT
  temporary="${tool_path}.download.$$"
  url="https://github.com/mamba-org/micromamba-releases/releases/download/${release_tag}/micromamba-${platform}"
  echo "tea: downloading pinned micromamba ${version} for ${platform}..." >&2
  tea_env_download "${url}" "${temporary}"
  actual_checksum="$(tea_env_sha256 "${temporary}")"
  if [[ "${actual_checksum}" != "${checksum}" ]]; then
    echo "tea: micromamba checksum verification failed" >&2
    exit 1
  fi
  chmod 700 "${temporary}"
  mv "${temporary}" "${tool_path}"
  printf '%s\n' "${tool_path}"
)

tea_env_prepare() {
  local framework_dir platform lock_file lock_hash env_prefix marker

  tea_env_resolve_home || return 1
  framework_dir="$(tea_env_framework_dir)" || return 1
  platform="$(tea_env_platform)" || return 1
  lock_file="${framework_dir}/environment/conda-${platform}.lock"
  if [[ ! -r "${lock_file}" ]]; then
    echo "tea: dependency lock not found for ${platform}: ${lock_file}" >&2
    return 1
  fi

  lock_hash="$(tea_env_sha256 "${lock_file}")" || return 1
  env_prefix="${TEA_HOME}/environments/${platform}/${lock_hash}"
  marker="${env_prefix}/.tea-environment"

  TEA_ENV_PLATFORM="${platform}"
  TEA_ENV_LOCK_FILE="${lock_file}"
  TEA_ENV_LOCK_HASH="${lock_hash}"
  TEA_ENV_PREFIX="${env_prefix}"
  TEA_ENV_MARKER="${marker}"
  TEA_MICROMAMBA="$(tea_env_ensure_micromamba "${platform}")" || return 1
  export TEA_ENV_PLATFORM TEA_ENV_LOCK_FILE TEA_ENV_LOCK_HASH TEA_ENV_PREFIX TEA_MICROMAMBA
}

tea_env_ensure() (
  set -euo pipefail

  local lock_dir lock_status marker_hash
  tea_env_prepare

  if [[ -r "${TEA_ENV_MARKER}" ]]; then
    IFS= read -r marker_hash < "${TEA_ENV_MARKER}"
    if [[ "${marker_hash}" == "${TEA_ENV_LOCK_HASH}" ]]; then
      exit 0
    fi
  fi

  mkdir -p "$(dirname "${TEA_ENV_PREFIX}")"
  lock_dir="${TEA_ENV_PREFIX}.installing"
  lock_status=0
  tea_env_wait_for_lock "${lock_dir}" "${TEA_ENV_MARKER}" || lock_status=$?
  if [[ "${lock_status}" -eq 1 ]]; then
    IFS= read -r marker_hash < "${TEA_ENV_MARKER}"
    [[ "${marker_hash}" == "${TEA_ENV_LOCK_HASH}" ]]
    exit $?
  elif [[ "${lock_status}" -ne 0 ]]; then
    exit "${lock_status}"
  fi

  trap 'rmdir "${lock_dir}" 2>/dev/null || true' EXIT

  if [[ -e "${TEA_ENV_PREFIX}" ]]; then
    case "${TEA_ENV_PREFIX}" in
      "${TEA_HOME}"/environments/*)
        rm -rf "${TEA_ENV_PREFIX}"
        ;;
      *)
        echo "tea: refusing to replace unexpected path ${TEA_ENV_PREFIX}" >&2
        exit 1
        ;;
    esac
  fi

  echo "tea: creating shared ${TEA_ENV_PLATFORM} environment at ${TEA_ENV_PREFIX}" >&2
  MAMBA_ROOT_PREFIX="${TEA_HOME}/micromamba" \
    "${TEA_MICROMAMBA}" create --yes --prefix "${TEA_ENV_PREFIX}" --file "${TEA_ENV_LOCK_FILE}"
  printf '%s\n' "${TEA_ENV_LOCK_HASH}" > "${TEA_ENV_MARKER}"
)

tea_env_activate() {
  local activation_code activation_status nounset_was_enabled
  local prompt_base prompt_is_set prompt_modifier

  # Prefix activation normally makes micromamba use the full environment path
  # as its display name. Keep that content-addressed path internal and preserve
  # the user's prompt (including colour escapes and embedded newlines).
  prompt_base=""
  prompt_is_set=0
  prompt_modifier="${CONDA_PROMPT_MODIFIER:-}"
  if [[ "$-" == *i* ]] && [[ -n "${PS1+x}" ]]; then
    prompt_base="${PS1}"
    if [[ -n "${prompt_modifier}" ]] && [[ "${prompt_base}" == "${prompt_modifier}"* ]]; then
      prompt_base="${prompt_base#"${prompt_modifier}"}"
    fi
    prompt_is_set=1
  fi

  tea_env_prepare || return 1
  tea_env_ensure || return 1
  activation_code="$(MAMBA_CHANGEPS1=false MAMBA_ROOT_PREFIX="${TEA_HOME}/micromamba" \
    "${TEA_MICROMAMBA}" shell activate --shell bash --prefix "${TEA_ENV_PREFIX}")" || return 1

  # Conda-forge activation hooks are not consistently safe under `set -u`.
  # Restore the caller's nounset setting immediately after evaluating them.
  nounset_was_enabled=0
  if [[ "$-" == *u* ]]; then
    nounset_was_enabled=1
    set +u
  fi
  activation_status=0
  eval "${activation_code}" || activation_status=$?
  if [[ "${nounset_was_enabled}" -eq 1 ]]; then
    set -u
  fi
  if [[ "${activation_status}" -ne 0 ]]; then
    return "${activation_status}"
  fi

  TEA_ENV_NAME="tea"
  CONDA_DEFAULT_ENV="${TEA_ENV_NAME}"
  CONDA_PROMPT_MODIFIER="(${TEA_ENV_NAME}) "
  if [[ "${prompt_is_set}" -eq 1 ]]; then
    PS1="${CONDA_PROMPT_MODIFIER}${prompt_base}"
  fi

  export TEA_ENV_NAME TEA_ENV_PREFIX TEA_ENV_LOCK_HASH TEA_ENV_PLATFORM
  export CONDA_DEFAULT_ENV CONDA_PROMPT_MODIFIER
  export PYTHONNOUSERSITE=1
}
