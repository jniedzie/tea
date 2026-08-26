#!/bin/bash

set -euo pipefail

usage() {
    cat <<'EOF'
Usage: ./install.sh [--tea-home ABSOLUTE_PATH] [GIT_REMOTE]

--tea-home selects a persistent shared location for tea dependencies. The
installer otherwise asks for a location and offers ~/.tea as the default.
EOF
}

TEA_HOME_ARG=""
TEA_HOME_EXPLICIT=false
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
            TEA_HOME_EXPLICIT=true
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

TEA_CONFIG_DIR="${XDG_CONFIG_HOME:-${HOME}/.config}/tea"
TEA_CONFIG_FILE="${TEA_CONFIG_DIR}/home"
TEA_HOME_DEFAULT="${HOME}/.tea"

if [[ -z "${TEA_HOME_ARG}" ]] && [[ -n "${TEA_HOME:-}" ]]; then
    TEA_HOME_ARG="${TEA_HOME}"
    TEA_HOME_EXPLICIT=true
elif [[ -z "${TEA_HOME_ARG}" ]] && [[ -r "${TEA_CONFIG_FILE}" ]]; then
    IFS= read -r TEA_HOME_ARG < "${TEA_CONFIG_FILE}"
fi

if [[ -z "${TEA_HOME_ARG}" ]]; then
    TEA_HOME_ARG="${TEA_HOME_DEFAULT}"
fi

if [[ -t 0 ]] && [[ -t 1 ]] && [[ "${TEA_HOME_EXPLICIT}" == false ]]; then
    read -r -p "Where should tea store its shared environment? [${TEA_HOME_ARG}] " TEA_HOME_INPUT
    if [[ -n "${TEA_HOME_INPUT}" ]]; then
        TEA_HOME_ARG="${TEA_HOME_INPUT}"
    fi
fi

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

mkdir -p "${TEA_HOME_ARG}"
TEA_HOME_ARG="$(cd "${TEA_HOME_ARG}" && pwd)"
mkdir -p "${TEA_CONFIG_DIR}"
printf '%s\n' "${TEA_HOME_ARG}" > "${TEA_CONFIG_FILE}"
export TEA_HOME="${TEA_HOME_ARG}"
echo "Using shared tea home: ${TEA_HOME_ARG}"
echo "Saved this choice in ${TEA_CONFIG_FILE}"

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
# Do not let the user's init.defaultBranch setting decide whether the initial
# commits land on main or master.
git symbolic-ref HEAD refs/heads/main

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

git add .
git commit -m "Initial commit"

echo "Creating the locked tea environment and building the analysis"
if ! ./tea/build.sh; then
    echo "Error: the tea environment could not be built." >&2
    echo "Review the build error above, fix its cause, then rerun: ./tea/build.sh" >&2
    echo "The analysis repository and its initial commits were created successfully." >&2
    exit 1
fi

if [ "$SETUP_REMOTE" = true ]; then
    echo "Setting up remote"
    if ! REMOTE_ADD_OUTPUT="$(git remote add origin "${REMOTE_REPOSITORY}" 2>&1)"; then
        echo "Error: could not add '${REMOTE_REPOSITORY}' as the origin remote." >&2
        printf '%s\n' "${REMOTE_ADD_OUTPUT}" >&2
        echo "Check that the URL is correct and that this directory does not already have an origin remote." >&2
        echo "The tea environment was built successfully; only the Git remote setup is incomplete." >&2
        exit 1
    fi

    # An empty repository has no branch to pull. Distinguish that expected
    # state from authentication, network, and invalid-URL failures.
    REMOTE_HAS_BRANCHES=true
    if REMOTE_HEADS="$(git ls-remote --exit-code --heads origin 2>&1)"; then
        :
    else
        LS_REMOTE_STATUS=$?
        if [[ "${LS_REMOTE_STATUS}" -eq 2 ]]; then
            REMOTE_HAS_BRANCHES=false
            REMOTE_HEADS=""
        else
            echo "Error: could not inspect the remote repository '${REMOTE_REPOSITORY}'." >&2
            printf '%s\n' "${REMOTE_HEADS}" >&2
            echo "Check the repository URL, your network connection, and your Git/SSH credentials." >&2
            echo "The tea environment was built successfully; only the Git remote setup is incomplete." >&2
            echo "After restoring access, run: git push -u origin main" >&2
            exit 1
        fi
    fi

    REMOTE_BRANCH="main"
    if [[ "${REMOTE_HAS_BRANCHES}" == true ]]; then
        if [[ "${REMOTE_HEADS}" != *$'\trefs/heads/main'* ]]; then
            REMOTE_HEAD_INFO="$(git ls-remote --symref origin HEAD 2>/dev/null || true)"
            REMOTE_BRANCH="$(awk '$1 == "ref:" && $2 ~ /^refs\/heads\// {sub(/^refs\/heads\//, "", $2); print $2; exit}' <<< "${REMOTE_HEAD_INFO}")"
            if [[ -z "${REMOTE_BRANCH}" ]]; then
                echo "Error: the remote has branches, but neither a 'main' branch nor a default branch could be determined." >&2
                echo "Set the default branch on the Git hosting service, then integrate the remote manually." >&2
                echo "The tea environment was built successfully and the local repository is ready on branch 'main'." >&2
                exit 1
            fi
            git branch -M "${REMOTE_BRANCH}"
        fi

        echo "Integrating existing remote branch '${REMOTE_BRANCH}'"
        if ! PULL_OUTPUT="$(git pull --rebase origin "${REMOTE_BRANCH}" 2>&1)"; then
            echo "Error: could not integrate the existing remote branch '${REMOTE_BRANCH}'." >&2
            printf '%s\n' "${PULL_OUTPUT}" >&2
            echo "Resolve the reported Git problem in this directory, then run:" >&2
            echo "  git pull --rebase origin ${REMOTE_BRANCH}" >&2
            echo "  git push -u origin ${REMOTE_BRANCH}" >&2
            echo "The tea environment was already built successfully; only the Git remote setup is incomplete." >&2
            exit 1
        fi
    else
        echo "Remote repository is empty; skipping the pull."
    fi

    if ! PUSH_OUTPUT="$(git push -u origin "${REMOTE_BRANCH}" 2>&1)"; then
        echo "Error: could not push branch '${REMOTE_BRANCH}' to '${REMOTE_REPOSITORY}'." >&2
        printf '%s\n' "${PUSH_OUTPUT}" >&2
        echo "Check your write permission and any branch-protection rules, then run:" >&2
        echo "  git push -u origin ${REMOTE_BRANCH}" >&2
        echo "The tea environment was already built successfully; only the Git remote setup is incomplete." >&2
        exit 1
    fi
fi

echo
echo "Installation complete. Activate this analysis in the current shell with:"
echo "  source tea/setup.sh"
