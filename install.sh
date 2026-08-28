#!/usr/bin/env bash

# Kept compatible with bash 3.2 (the /bin/bash shipped by macOS): no associative
# arrays, no `mapfile`, no `${var^^}`.

set -euo pipefail

usage() {
    cat <<'EOF'
Usage: ./install.sh [OPTIONS] [--] [GIT_REMOTE]

GIT_REMOTE is the analysis' Git repository. It may be empty (a new analysis is
created and committed locally) or already contain an analysis (it is checked
out and the tea build files are added to it). Without a remote, Git setup is
limited to a local repository.

Options:
  --tea-home PATH     Persistent shared location for tea's dependencies. The
                      installer otherwise asks and offers ~/.tea as the default.
  --vscode            Create a VS Code workspace configuration.
  --no-vscode         Do not create one. The installer otherwise asks; without
                      a terminal it defaults to --no-vscode. The configuration
                      can be created at any later time.
  -y, --yes           Never block on a question: take each prompt's own default
                      (keep the tea home shown, keep existing build files,
                      create the VS Code configuration). --no-vscode still wins.
  --dry-run           Report every change that would be made and make none.
  -h, --help          Show this message.

The installer never pushes and never rewrites history. It makes local commits
and prints the Git commands needed to publish them.
EOF
}

say() { printf '%s\n' "$*"; }
warn_out() { printf '%s\n' "$*" >&2; }
die() { printf '%s\n' "$*" >&2; exit "${2:-1}"; }

TEA_HOME_ARG=""
TEA_HOME_EXPLICIT=false
CONFIGURE_VSCODE=""
REMOTE_REPOSITORY=""
REMOTE_REPOSITORY_SET=false
ASSUME_YES=false
DRY_RUN=false
END_OF_OPTIONS=false

while [[ "$#" -gt 0 ]]; do
    if [[ "${END_OF_OPTIONS}" == true ]]; then
        if [[ "${REMOTE_REPOSITORY_SET}" == true ]]; then
            warn_out "Only one Git remote may be provided"
            usage >&2
            exit 2
        fi
        REMOTE_REPOSITORY="$1"
        REMOTE_REPOSITORY_SET=true
        shift
        continue
    fi
    case "$1" in
        --tea-home)
            if [[ "$#" -lt 2 ]]; then
                warn_out "Missing path after --tea-home"
                usage >&2
                exit 2
            fi
            TEA_HOME_ARG="$2"
            TEA_HOME_EXPLICIT=true
            shift 2
            ;;
        --vscode)
            CONFIGURE_VSCODE=true
            shift
            ;;
        --no-vscode)
            CONFIGURE_VSCODE=false
            shift
            ;;
        -y|--yes)
            ASSUME_YES=true
            shift
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        --)
            END_OF_OPTIONS=true
            shift
            ;;
        --*|-?*)
            warn_out "Unknown option: $1"
            usage >&2
            exit 2
            ;;
        *)
            if [[ "${REMOTE_REPOSITORY_SET}" == true ]]; then
                warn_out "Only one Git remote may be provided"
                usage >&2
                exit 2
            fi
            REMOTE_REPOSITORY="$1"
            REMOTE_REPOSITORY_SET=true
            shift
            ;;
    esac
done

# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------

WORK_DIR=""
cleanup() {
    [[ -n "${WORK_DIR}" ]] && rm -rf "${WORK_DIR}"
    return 0
}
trap cleanup EXIT
WORK_DIR="$(mktemp -d)"

is_interactive() {
    [[ "${ASSUME_YES}" == false ]] && [[ -t 0 ]] && [[ -t 1 ]]
}

# Ask a yes/no question. $2 is the default taken when the answer is empty, when
# --yes was given, or when there is no terminal to ask on.
ask_yes_no() {
    local prompt="$1" default="$2" reply=""
    if ! is_interactive; then
        printf '%s\n' "${default}"
        return 0
    fi
    read -r -p "${prompt} " reply </dev/tty || true
    case "${reply}" in
        [Yy]*) printf 'true\n' ;;
        [Nn]*) printf 'false\n' ;;
        *)     printf '%s\n' "${default}" ;;
    esac
}

# Every mutating action goes through run(), so --dry-run has nothing to forget.
run() {
    if [[ "${DRY_RUN}" == true ]]; then
        local rendered=""
        rendered="$(printf ' %q' "$@")"
        printf 'would run:%s\n' "${rendered}"
        return 0
    fi
    "$@"
}

dry_note() {
    [[ "${DRY_RUN}" == true ]] && printf 'would %s\n' "$*"
    return 0
}

# ---------------------------------------------------------------------------
# Preflight. Everything that makes the installer fail halfway through is
# checked here, before a single directory, commit, or clone is created.
# ---------------------------------------------------------------------------

command -v git >/dev/null 2>&1 ||
    die "Error: 'git' is not installed or not on PATH. Install Git, then rerun the installer."

if ! git config --get user.email >/dev/null 2>&1 || ! git config --get user.name >/dev/null 2>&1; then
    warn_out "Error: Git has no commit identity configured, so the installer cannot commit."
    warn_out "Set one, then rerun the installer:"
    warn_out "  git config --global user.name 'Your Name'"
    warn_out "  git config --global user.email 'you@example.com'"
    exit 1
fi

# Without a terminal, a remote that wants credentials must fail rather than sit
# forever on an invisible prompt inside a command substitution.
if ! is_interactive; then
    export GIT_TERMINAL_PROMPT=0
    export GIT_SSH_COMMAND="${GIT_SSH_COMMAND:-ssh -o BatchMode=yes}"
fi

CURRENT_DIR="$(pwd -P)"

SETUP_REMOTE=true
if [[ -z "${REMOTE_REPOSITORY}" ]]; then
    say "No remote repository provided. Git setup will be limited to this directory."
    SETUP_REMOTE=false
fi

# ---------------------------------------------------------------------------
# Repository state.
#
# An installation either creates a new analysis or adds tea to an analysis that
# already exists, locally or on the remote. Everything below is written so that
# the second case never overwrites, recreates, or re-commits what is already
# there: the state of the directory and of the remote is established first, and
# only what is genuinely missing is added afterwards.
#
# A repository this installer created on an earlier, failed run must not be
# mistaken for the user's own pre-existing analysis, so the installer leaves a
# marker inside .git while it is working and removes it once it has finished.
# ---------------------------------------------------------------------------

EXISTING_REPOSITORY=false
IN_PROGRESS_MARKER=""
DETACHED_HEAD=false
CAN_COMMIT=true

if GIT_TOPLEVEL="$(git rev-parse --show-toplevel 2>/dev/null)"; then
    GIT_TOPLEVEL="$(cd "${GIT_TOPLEVEL}" && pwd -P)"
    if [[ "${GIT_TOPLEVEL}" != "${CURRENT_DIR}" ]]; then
        warn_out "Error: ${CURRENT_DIR} lies inside the Git repository in ${GIT_TOPLEVEL}."
        warn_out "Install the analysis in its own directory, outside that repository."
        exit 1
    fi
    GIT_DIR_PATH="$(cd "$(git rev-parse --git-dir)" && pwd -P)"
    IN_PROGRESS_MARKER="${GIT_DIR_PATH}/tea-install-in-progress"
    if [[ -e "${IN_PROGRESS_MARKER}" ]]; then
        say "Resuming an installation that did not finish; this repository was created by the installer."
    else
        EXISTING_REPOSITORY=true
        say "Installing into the existing Git repository in ${CURRENT_DIR}"
    fi

    # Committing onto a detached HEAD produces commits nothing points at.
    if ! git symbolic-ref --quiet HEAD >/dev/null 2>&1; then
        DETACHED_HEAD=true
        CAN_COMMIT=false
        warn_out "Warning: this repository has a detached HEAD."
        warn_out "The build files will be installed and staged, but not committed."
        warn_out "Check out a branch and commit them yourself once the installer has finished."
    fi
fi

# ---------------------------------------------------------------------------
# tea home. The location is resolved and canonicalized now because the build
# needs it, but the machine-wide choice in ~/.config/tea/home is only recorded
# once the environment has actually been built with it.
# ---------------------------------------------------------------------------

TEA_CONFIG_DIR="${XDG_CONFIG_HOME:-${HOME}/.config}/tea"
TEA_CONFIG_FILE="${TEA_CONFIG_DIR}/home"
TEA_HOME_DEFAULT="${HOME}/.tea"

TEA_HOME_SAVED=""
if [[ -r "${TEA_CONFIG_FILE}" ]]; then
    # An empty or truncated config file must not abort the installation: `read`
    # reports EOF with status 1, which errexit would treat as a fatal error.
    IFS= read -r TEA_HOME_SAVED < "${TEA_CONFIG_FILE}" || true
fi

# Only --tea-home is an explicit choice for *this* installation. A TEA_HOME
# exported for some other analysis, and the saved choice, seed the default but
# do not silently redefine it.
TEA_HOME_FROM_ENV=false
if [[ -z "${TEA_HOME_ARG}" ]]; then
    if [[ -n "${TEA_HOME:-}" ]]; then
        TEA_HOME_ARG="${TEA_HOME}"
        TEA_HOME_FROM_ENV=true
    elif [[ -n "${TEA_HOME_SAVED}" ]]; then
        TEA_HOME_ARG="${TEA_HOME_SAVED}"
    fi
fi

if [[ -z "${TEA_HOME_ARG}" ]]; then
    TEA_HOME_ARG="${TEA_HOME_DEFAULT}"
fi

if [[ "${TEA_HOME_FROM_ENV}" == true ]] && [[ -n "${TEA_HOME_SAVED}" ]] &&
        [[ "${TEA_HOME_SAVED}" != "${TEA_HOME_ARG}" ]]; then
    warn_out "Note: TEA_HOME is set to ${TEA_HOME_ARG}, but ${TEA_CONFIG_FILE} says ${TEA_HOME_SAVED}."
    warn_out "Using TEA_HOME for this installation; the saved default is left unchanged."
fi

if [[ "${TEA_HOME_EXPLICIT}" == false ]] && is_interactive; then
    TEA_HOME_INPUT=""
    # A closed or exhausted standard input must not abort the installation.
    read -r -p "Where should tea store its shared environment? [${TEA_HOME_ARG}] " TEA_HOME_INPUT </dev/tty || true
    if [[ -n "${TEA_HOME_INPUT}" ]]; then
        TEA_HOME_ARG="${TEA_HOME_INPUT}"
        TEA_HOME_EXPLICIT=true
    fi
fi

# shellcheck disable=SC2088  # literal tilde matched on purpose, then expanded
case "${TEA_HOME_ARG}" in
    "~")   TEA_HOME_ARG="${HOME}" ;;
    "~/"*) TEA_HOME_ARG="${HOME}/${TEA_HOME_ARG:2}" ;;
    "~"*)
        die "The tea environment location must be an absolute path; '~user' paths are not expanded. Write the path out in full." 2
        ;;
esac

if [[ "${TEA_HOME_ARG}" != /* ]]; then
    die "The tea environment location must be an absolute path (or start with ~/)." 2
fi

if [[ "${DRY_RUN}" == true ]] && [[ ! -d "${TEA_HOME_ARG}" ]]; then
    dry_note "create the tea home ${TEA_HOME_ARG}"
else
    mkdir -p "${TEA_HOME_ARG}" ||
        die "Error: could not create the tea environment location ${TEA_HOME_ARG}. Choose a writable path with --tea-home."
    TEA_HOME_ARG="$(cd "${TEA_HOME_ARG}" && pwd -P)"
    [[ -w "${TEA_HOME_ARG}" ]] ||
        die "Error: the tea environment location ${TEA_HOME_ARG} is not writable. Choose another path with --tea-home."
fi

export TEA_HOME="${TEA_HOME_ARG}"
say "Using shared tea home: ${TEA_HOME_ARG}"

# ---------------------------------------------------------------------------
# The remote is inspected before anything is created locally. An analysis that
# already exists there has to be checked out rather than reconstructed, because
# a second, independently created history cannot be merged into it without
# conflicts in the files both sides contain.
# ---------------------------------------------------------------------------

REMOTE_HAS_BRANCHES=false
REMOTE_BRANCH="main"

if [[ "${SETUP_REMOTE}" == true ]]; then
    say "Inspecting the remote repository"
    LS_REMOTE_ERR="${WORK_DIR}/ls-remote.err"
    # Diagnostics are captured separately: merging them into the ref listing
    # would put SSH banners and host-key notices into data that is parsed below.
    if REMOTE_HEADS="$(git ls-remote --exit-code --heads "${REMOTE_REPOSITORY}" 2>"${LS_REMOTE_ERR}")"; then
        REMOTE_HAS_BRANCHES=true
    else
        LS_REMOTE_STATUS=$?
        if [[ "${LS_REMOTE_STATUS}" -eq 2 ]]; then
            REMOTE_HEADS=""
            say "The remote repository is empty; a new analysis will be created."
        else
            warn_out "Error: could not inspect the remote repository '${REMOTE_REPOSITORY}'."
            cat "${LS_REMOTE_ERR}" >&2 || true
            warn_out "Check the repository URL, your network connection, and your Git/SSH credentials."
            warn_out "Nothing was created; rerun the installer once the remote is reachable."
            exit 1
        fi
    fi

    if [[ "${REMOTE_HAS_BRANCHES}" == true ]]; then
        # "<sha>\trefs/heads/<name>" per line. Matching this as a glob against
        # the whole listing makes 'maintenance' look like 'main'.
        REMOTE_BRANCH_NAMES="$(awk -F'\t' '$2 ~ /^refs\/heads\// { sub(/^refs\/heads\//, "", $2); print $2 }' <<< "${REMOTE_HEADS}")"

        if ! grep -qxF -- "main" <<< "${REMOTE_BRANCH_NAMES}"; then
            REMOTE_HEAD_INFO="$(git ls-remote --symref "${REMOTE_REPOSITORY}" HEAD 2>/dev/null || true)"
            REMOTE_BRANCH="$(awk '$1 == "ref:" && $2 ~ /^refs\/heads\// { sub(/^refs\/heads\//, "", $2); print $2; exit }' <<< "${REMOTE_HEAD_INFO}")"
            if [[ -z "${REMOTE_BRANCH}" ]]; then
                warn_out "Error: the remote has branches, but neither a 'main' branch nor a default branch could be determined."
                warn_out "It has: $(tr '\n' ' ' <<< "${REMOTE_BRANCH_NAMES}")"
                warn_out "Set the default branch on the Git hosting service, then rerun the installer."
                exit 1
            fi
            if ! grep -qxF -- "${REMOTE_BRANCH}" <<< "${REMOTE_BRANCH_NAMES}"; then
                warn_out "Error: the remote's default branch '${REMOTE_BRANCH}' is not among its branches."
                warn_out "Set the default branch on the Git hosting service, then rerun the installer."
                exit 1
            fi
        fi

        git check-ref-format --branch "${REMOTE_BRANCH}" >/dev/null 2>&1 ||
            die "Error: the remote's default branch name '${REMOTE_BRANCH}' is not a valid branch name."
    fi
fi

# ---------------------------------------------------------------------------
# Create the analysis skeleton.
# ---------------------------------------------------------------------------

say "Creating necessary directories"
run mkdir -p apps bin build configs utils libs/user_extensions/include

if [[ -z "${IN_PROGRESS_MARKER}" ]] && [[ "${EXISTING_REPOSITORY}" == false ]]; then
    say "Initializing git repository"
    run git init
    # Do not let the user's init.defaultBranch setting decide whether the
    # initial commits land on main or master.
    run git symbolic-ref HEAD "refs/heads/${REMOTE_BRANCH}"
    if [[ "${DRY_RUN}" == false ]]; then
        IN_PROGRESS_MARKER="$(cd "$(git rev-parse --git-dir)" && pwd -P)/tea-install-in-progress"
        date > "${IN_PROGRESS_MARKER}"
    else
        dry_note "mark the new repository as created by the installer"
    fi
fi

if [[ "${SETUP_REMOTE}" == true ]]; then
    if ORIGIN_URL="$(git config --get remote.origin.url 2>/dev/null)"; then
        if [[ "${ORIGIN_URL}" != "${REMOTE_REPOSITORY}" ]]; then
            warn_out "Error: this repository already has an 'origin' remote: ${ORIGIN_URL}"
            warn_out "Remove or rename that remote, or rerun the installer without a Git remote."
            exit 1
        fi
        say "The 'origin' remote already points at ${REMOTE_REPOSITORY}"
    else
        say "Setting up remote"
        run git remote add origin "${REMOTE_REPOSITORY}"
    fi
fi

# Only an analysis that starts here gets an initial commit.
SETUP_COMMIT_MESSAGE="Initial commit"
if [[ "${EXISTING_REPOSITORY}" == true ]] || [[ "${REMOTE_HAS_BRANCHES}" == true ]]; then
    SETUP_COMMIT_MESSAGE="Add the tea build files"
fi

if [[ "${EXISTING_REPOSITORY}" == false ]] && [[ "${REMOTE_HAS_BRANCHES}" == true ]] &&
        ! git rev-parse --verify --quiet HEAD >/dev/null 2>&1; then
    say "The remote already contains an analysis; checking out its branch '${REMOTE_BRANCH}'"
    if [[ "${DRY_RUN}" == true ]]; then
        dry_note "fetch and check out origin/${REMOTE_BRANCH}"
    else
        FETCH_ERR="${WORK_DIR}/fetch.err"
        if ! git fetch origin "${REMOTE_BRANCH}" 2>"${FETCH_ERR}"; then
            warn_out "Error: could not fetch branch '${REMOTE_BRANCH}' from '${REMOTE_REPOSITORY}'."
            cat "${FETCH_ERR}" >&2 || true
            warn_out "Check your network connection and your Git/SSH credentials, then rerun the installer."
            exit 1
        fi
        CHECKOUT_ERR="${WORK_DIR}/checkout.err"
        if ! git checkout -B "${REMOTE_BRANCH}" "origin/${REMOTE_BRANCH}" 2>"${CHECKOUT_ERR}"; then
            warn_out "Error: could not check out branch '${REMOTE_BRANCH}'."
            cat "${CHECKOUT_ERR}" >&2 || true
            warn_out "Files already present in ${CURRENT_DIR} may collide with the ones in the repository."
            warn_out "Install an existing analysis into an empty directory."
            exit 1
        fi
    fi
fi

# ---------------------------------------------------------------------------
# The tea submodule. Presence of a `tea` directory is not the same as tea being
# installed: an interrupted run leaves an empty one behind.
# ---------------------------------------------------------------------------

TEA_IS_REGISTERED=false
if git config --file .gitmodules --get submodule.tea.url >/dev/null 2>&1; then
    TEA_IS_REGISTERED=true
fi

if [[ "${TEA_IS_REGISTERED}" == true ]]; then
    say "tea is already part of this analysis; updating the submodule"
    # Scoped to tea: an existing analysis may have other submodules that are
    # deliberately checked out somewhere other than their recorded commit.
    run git submodule update --init --recursive -- tea
elif [[ -e tea ]] && [[ ! -e tea/build.sh ]]; then
    warn_out "Error: a 'tea' entry exists here but is not a tea checkout (tea/build.sh is missing)."
    warn_out "Remove it, then rerun the installer:"
    warn_out "  rm -rf tea"
    exit 1
elif [[ -e tea ]]; then
    say "A tea checkout is already present but not registered as a submodule; leaving it alone."
else
    say "Adding tea as a submodule"
    run git submodule add git@github.com:jniedzie/tea.git tea
    run git submodule update --init --recursive -- tea
    # Commit the two paths explicitly: an analysis that already exists may have
    # unrelated staged changes that are none of the installer's business.
    if [[ "${CAN_COMMIT}" == true ]]; then
        if [[ "${DRY_RUN}" == true ]]; then
            dry_note "commit .gitmodules and tea"
        elif ! git diff --cached --quiet -- .gitmodules tea; then
            git commit -m "Add tea as a submodule" -- .gitmodules tea
        fi
    else
        say "Leaving .gitmodules and tea staged; commit them once HEAD is on a branch."
    fi
fi

# ---------------------------------------------------------------------------
# Install the build files. A file the analysis already has is its own: it is
# kept unless it differs from the tea template and the user explicitly asks for
# the template instead. Overwriting it unconditionally used to discard the
# analysis' build configuration and, on an installation against an existing
# remote, turned every such file into a rebase conflict.
#
# .gitignore is the exception: it is a line-oriented list with no ordering or
# structure, so an existing one is merged with the template rather than being
# an all-or-nothing choice between the two.
# ---------------------------------------------------------------------------

INSTALLED_FILES=()
DIFF_PREVIEW_LINES=40
TEA_IGNORE_HEADER="# --- added by tea ---"

create_from_template() {
    local template="$1" destination="$2"
    run mkdir -p "$(dirname "${destination}")"
    run cp "${template}" "${destination}"
    INSTALLED_FILES+=("${destination}")
    if [[ "${DRY_RUN}" == true ]]; then
        say "Would create ${destination} from ${template}"
    else
        say "Created ${destination} from ${template}"
    fi
}

# Append the template's entries that the destination does not already contain,
# leaving everything the analysis added in place.
merge_ignore_template() {
    local template="$1" destination="$2"
    local missing="${WORK_DIR}/ignore-missing" line

    : > "${missing}"
    while IFS= read -r line || [[ -n "${line}" ]]; do
        case "${line}" in
            ''|'#'*) continue ;;
        esac
        grep -qxF -- "${line}" "${destination}" || printf '%s\n' "${line}" >> "${missing}"
    done < "${template}"

    if [[ ! -s "${missing}" ]]; then
        say "Keeping ${destination}; it already covers every entry in ${template}"
        return 0
    fi

    say "Adding the tea entries missing from ${destination}:"
    sed 's/^/  /' "${missing}"

    if [[ "${DRY_RUN}" == true ]]; then
        dry_note "append them to ${destination}"
        return 0
    fi

    # Do not glue the first appended entry onto an unterminated last line.
    if [[ -s "${destination}" ]] && [[ -n "$(tail -c 1 "${destination}")" ]]; then
        printf '\n' >> "${destination}"
    fi
    if ! grep -qxF -- "${TEA_IGNORE_HEADER}" "${destination}"; then
        printf '\n%s\n' "${TEA_IGNORE_HEADER}" >> "${destination}"
    fi
    cat "${missing}" >> "${destination}"
    INSTALLED_FILES+=("${destination}")
    say "Updated ${destination}"
}

install_template() {
    local template="$1" destination="$2" strategy="${3:-replace}"
    local difference reply

    if [[ ! -e "${template}" ]]; then
        # On a dry run the tea clone was only narrated, so its templates are not
        # on disk yet. That is expected, not a broken checkout.
        if [[ "${DRY_RUN}" == true ]] && [[ ! -e tea/build.sh ]]; then
            dry_note "install ${destination} from ${template}"
            INSTALLED_FILES+=("${destination}")
            return 0
        fi
        die "Error: the tea template ${template} is missing. Is the tea submodule complete?"
    fi

    if [[ ! -e "${destination}" ]]; then
        create_from_template "${template}" "${destination}"
        return 0
    fi

    if cmp -s "${template}" "${destination}"; then
        say "Keeping ${destination}; it already matches the tea template"
        return 0
    fi

    if [[ "${strategy}" == "merge-lines" ]]; then
        merge_ignore_template "${template}" "${destination}"
        return 0
    fi

    # diff reports differing files with status 1, which errexit would treat as
    # a failed installation.
    difference="$(diff -u "${destination}" "${template}" || true)"

    say "The existing ${destination} differs from ${template}:"
    # `sed -n` with a plain range reads its whole input, so nothing upstream
    # dies of SIGPIPE under `pipefail`.
    printf '%s\n' "${difference}" | sed -n "1,${DIFF_PREVIEW_LINES}p"
    if [[ "$(printf '%s\n' "${difference}" | wc -l)" -gt "${DIFF_PREVIEW_LINES}" ]]; then
        say "  [diff truncated; see: diff -u ${destination} ${template}]"
    fi

    reply="$(ask_yes_no "Replace ${destination} with the tea template? [y/N]" false)"
    if [[ "${reply}" == true ]]; then
        if [[ "${DRY_RUN}" == false ]]; then
            cp "${destination}" "${destination}.orig"
            say "Saved the previous version as ${destination}.orig"
        else
            dry_note "save the previous version as ${destination}.orig"
        fi
        run cp "${template}" "${destination}"
        INSTALLED_FILES+=("${destination}")
        say "Replaced ${destination} with ${template}"
    else
        say "Kept ${destination}"
    fi
}

install_template tea/templates/CMakeLists.template.txt CMakeLists.txt
install_template tea/templates/gitignore.template .gitignore merge-lines
install_template tea/templates/UserExtensionsHelpers.template.hpp \
    libs/user_extensions/include/UserExtensionsHelpers.hpp

if [[ "${#INSTALLED_FILES[@]}" -gt 0 ]]; then
    if [[ "${CAN_COMMIT}" == false ]]; then
        say "Staging the build files; HEAD is detached, so they are not committed."
        run git add -- "${INSTALLED_FILES[@]}"
    elif [[ "${DRY_RUN}" == true ]]; then
        dry_note "commit ${#INSTALLED_FILES[@]} build file(s) as '${SETUP_COMMIT_MESSAGE}'"
    else
        git add -- "${INSTALLED_FILES[@]}"
        if git diff --cached --quiet -- "${INSTALLED_FILES[@]}"; then
            say "The build files already match the last commit; nothing to commit"
        else
            git commit -m "${SETUP_COMMIT_MESSAGE}" -- "${INSTALLED_FILES[@]}"
        fi
    fi
else
    say "All build files were already in place; nothing to commit"
fi

# ---------------------------------------------------------------------------
# Build the environment. This is the long step; its output is not captured so
# that a slow conda solve does not look like a hang.
# ---------------------------------------------------------------------------

if [[ "${DRY_RUN}" == true ]]; then
    dry_note "build the tea environment with ./tea/build.sh"
else
    say "Creating the locked tea environment and building the analysis"
    if ! ./tea/build.sh; then
        warn_out "Error: the tea environment could not be built."
        warn_out "Review the build error above, fix its cause, then rerun: ./tea/build.sh"
        warn_out "The analysis repository and its commits were created successfully."
        warn_out "You can also rerun this installer; it will resume where it stopped."
        exit 1
    fi

    # The machine-wide default is only recorded once an environment has actually
    # been built at this location.
    mkdir -p "${TEA_CONFIG_DIR}"
    if [[ "${TEA_HOME_EXPLICIT}" == true ]] || [[ -z "${TEA_HOME_SAVED}" ]]; then
        printf '%s\n' "${TEA_HOME_ARG}" > "${TEA_CONFIG_FILE}"
        say "Saved this choice in ${TEA_CONFIG_FILE}"
    fi
fi

# ---------------------------------------------------------------------------
# Optional extras. Neither of these is worth failing the installation over.
# ---------------------------------------------------------------------------

if [[ -z "${CONFIGURE_VSCODE}" ]]; then
    CONFIGURE_VSCODE="$(ask_yes_no "Configure this analysis for VS Code? [Y/n]" "$(is_interactive && echo true || echo false)")"
fi

print_vscode_instructions() {
    cat <<'EOF'
  source tea/setup.sh
  python tea/environment/configure_vscode.py \
      --workspace "$(pwd)" --framework "$(pwd)/tea" --environment "${TEA_ENV_PREFIX}"
EOF
}

if [[ "${CONFIGURE_VSCODE}" == true ]]; then
    if [[ "${DRY_RUN}" == true ]]; then
        dry_note "configure the VS Code workspace"
    else
        say "Configuring the VS Code workspace"
        if ! (
            source tea/environment/activate.sh && tea_env_activate &&
                "${TEA_ENV_PREFIX}/bin/python" tea/environment/configure_vscode.py \
                    --workspace "${CURRENT_DIR}" \
                    --framework "${CURRENT_DIR}/tea" \
                    --environment "${TEA_ENV_PREFIX}"
        ); then
            warn_out "Warning: could not configure the VS Code workspace."
            warn_out "The environment was built successfully; only .vscode is missing. To retry, run:"
            print_vscode_instructions >&2
        fi
    fi
else
    say "Skipping the VS Code configuration. To create it later, run:"
    print_vscode_instructions
fi

if [[ "${DRY_RUN}" == true ]]; then
    dry_note "install tea's pre-commit hooks"
else
    say "Installing pre-commit hooks for tea"
    if ! ( source tea/environment/activate.sh && tea_env_activate && cd tea && pre-commit install ); then
        warn_out "Warning: could not install tea's pre-commit hooks."
        warn_out "Formatting will not run automatically on commits in tea/. To retry, run:"
        warn_out "  (cd tea && pre-commit install)"
    fi
fi

# ---------------------------------------------------------------------------
# Finish. The installer commits locally and stops there: publishing an analysis
# is the user's decision, and rebasing a repository that already has history
# would rewrite commits the installer knows nothing about.
# ---------------------------------------------------------------------------

if [[ -n "${IN_PROGRESS_MARKER}" ]] && [[ "${DRY_RUN}" == false ]]; then
    rm -f "${IN_PROGRESS_MARKER}"
fi

# The installer is downloaded into the analysis directory and is not part of it.
# Removed last, so that every failure above leaves it available for a rerun.
if [[ "${DRY_RUN}" == true ]]; then
    dry_note "remove install.sh"
elif ! git ls-files --error-unmatch install.sh >/dev/null 2>&1; then
    rm -f install.sh
fi

LOCAL_BRANCH="$(git symbolic-ref --short HEAD 2>/dev/null || true)"

say ""
if [[ "${DRY_RUN}" == true ]]; then
    say "Dry run complete. Nothing was changed."
    exit 0
fi

say "Installation complete. Activate this analysis in the current shell with:"
say "  source tea/setup.sh"

if [[ "${DETACHED_HEAD}" == true ]]; then
    say ""
    say "HEAD is detached, so the build files were staged but not committed:"
    say "  git switch -c <branch>"
    say "  git commit -m '${SETUP_COMMIT_MESSAGE}'"
elif [[ "${SETUP_REMOTE}" == true ]] && [[ -n "${LOCAL_BRANCH}" ]]; then
    say ""
    say "The commits are local. To publish them:"
    if [[ "${REMOTE_HAS_BRANCHES}" == true ]]; then
        say "  git pull --rebase origin ${LOCAL_BRANCH}"
    fi
    say "  git push -u origin ${LOCAL_BRANCH}"
fi
