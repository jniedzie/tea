#!/bin/bash

set -euo pipefail

usage() {
    cat <<'EOF'
Usage: ./install.sh [--tea-home ABSOLUTE_PATH] [GIT_REMOTE]

--tea-home selects a persistent shared location for tea dependencies. Without
it, sibling analysis repositories automatically use ../.tea.
EOF
}

TEA_HOME_ARG=""
REMOTE_REPOSITORY=""
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
        --*)
            echo "Unknown option: $1" >&2
            usage >&2
            exit 2
            ;;
        *)
            if [[ -n "${REMOTE_REPOSITORY}" ]]; then
                echo "Only one Git remote may be provided" >&2
                usage >&2
                exit 2
            fi
            REMOTE_REPOSITORY="$1"
            shift
            ;;
    esac
done

if [[ -n "${TEA_HOME_ARG}" ]]; then
    if [[ "${TEA_HOME_ARG}" != /* ]]; then
        echo "--tea-home must be an absolute path" >&2
        exit 2
    fi
    mkdir -p "${TEA_HOME_ARG}"
    TEA_HOME_ARG="$(cd "${TEA_HOME_ARG}" && pwd)"
    TEA_CONFIG_DIR="${XDG_CONFIG_HOME:-${HOME}/.config}/tea"
    mkdir -p "${TEA_CONFIG_DIR}"
    printf '%s\n' "${TEA_HOME_ARG}" > "${TEA_CONFIG_DIR}/home"
    export TEA_HOME="${TEA_HOME_ARG}"
    echo "Using shared tea home: ${TEA_HOME_ARG}"
    echo "Saved this choice in ${TEA_CONFIG_DIR}/home"
fi

SETUP_REMOTE=true
if [[ -z "${REMOTE_REPOSITORY}" ]]; then
    echo "No remote repository provided. Git setup will be skipped."
    SETUP_REMOTE=false
fi

# create necessary directories
echo "Creating necessary directories"
mkdir -p apps bin build configs utils libs/user_extensions/include

# initialize git repository
echo "Initializing git repository"
git init

echo "Adding tea as a submodule"
git submodule add git@github.com:jniedzie/tea.git tea
git submodule update --init --recursive
git commit -m "Add tea as a submodule"

# copy and removing files
echo "Copying CMakelists.txt from tea"
cp tea/templates/CMakeLists.template.txt CMakeLists.txt
cp tea/templates/gitignore.template .gitignore
cp tea/templates/UserExtensionsHelpers.template.hpp libs/user_extensions/include/UserExtensionsHelpers.hpp
rm install.sh

if [ "$SETUP_REMOTE" = true ]; then
    echo "Setting up remote"
    git remote add origin "${REMOTE_REPOSITORY}"
    git add .
    git commit -m "Initial commit"

    # take what's in the repo already (like gitignore, README, etc.) and push all other files
    git pull --rebase origin main
    git push -u origin main
fi

echo "Creating the locked tea environment and building the analysis"
./tea/build.sh

echo
echo "Installation complete. Activate this analysis in the current shell with:"
echo "  source tea/setup.sh"
