#!/bin/bash

set -euo pipefail

usage() {
  cat <<'EOF'
Usage: ./tea/migrate.sh --tea-home ABSOLUTE_PATH

Migrate an existing analysis to Tea's managed build environment. The command
records the shared environment location, removes obsolete macOS CMake settings,
performs a clean build, configures VS Code, and installs Tea's pre-commit hooks.
EOF
}

TEA_HOME_ARG=""
while [[ "$#" -gt 0 ]]; do
  case "$1" in
    --tea-home)
      if [[ "$#" -lt 2 ]]; then
        echo "Missing path after --tea-home" >&2
        usage >&2
        exit 2
      fi
      TEA_HOME_ARG="$2"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

if [[ -z "${TEA_HOME_ARG}" ]]; then
  echo "--tea-home is required; choose a persistent absolute path for the shared Tea environment." >&2
  usage >&2
  exit 2
fi

# The patterns below intentionally match a literal user-supplied tilde.
# shellcheck disable=SC2088
case "${TEA_HOME_ARG}" in
  "~")
    TEA_HOME_ARG="${HOME}"
    ;;
  "~/"*)
    TEA_HOME_ARG="${HOME}/${TEA_HOME_ARG:2}"
    ;;
esac

if [[ "${TEA_HOME_ARG}" != /* ]]; then
  echo "The tea environment location must be an absolute path (or start with ~/)." >&2
  exit 2
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
CMAKE_FILE="${WORKSPACE_DIR}/CMakeLists.txt"
TEA_CONFIG_DIR="${XDG_CONFIG_HOME:-${HOME}/.config}/tea"
TEA_CONFIG_FILE="${TEA_CONFIG_DIR}/home"

if [[ ! -f "${CMAKE_FILE}" ]]; then
  echo "Could not find the analysis CMake file: ${CMAKE_FILE}" >&2
  exit 1
fi

mkdir -p "${TEA_HOME_ARG}"
TEA_HOME_ARG="$(cd "${TEA_HOME_ARG}" && pwd)"
mkdir -p "${TEA_CONFIG_DIR}"
printf '%s\n' "${TEA_HOME_ARG}" > "${TEA_CONFIG_FILE}"
export TEA_HOME="${TEA_HOME_ARG}"
echo "Using shared tea home: ${TEA_HOME_ARG}"
echo "Saved this choice in ${TEA_CONFIG_FILE}"

temporary_cmake="$(mktemp "${CMAKE_FILE}.migration.XXXXXX")"
trap 'rm -f "${temporary_cmake}"' EXIT
awk '
  {
    normalized = tolower($0)
    gsub(/[[:space:]]/, "", normalized)
    if (normalized == "set(cmake_osx_architectures\"arm64\")" ||
        normalized == "set(cmake_osx_deployment_target13.2)") {
      next
    }
    print
  }
' "${CMAKE_FILE}" > "${temporary_cmake}"

if cmp -s "${CMAKE_FILE}" "${temporary_cmake}"; then
  echo "No obsolete macOS CMake settings found"
else
  command cat "${temporary_cmake}" > "${CMAKE_FILE}"
  echo "Removed obsolete macOS settings from ${CMAKE_FILE}"
fi

"${SCRIPT_DIR}/build.sh" --clean
"${SCRIPT_DIR}/environment/configure_project.sh"

echo "Migration complete. Review CMakeLists.txt and the generated .vscode settings, then validate a representative analysis job."
