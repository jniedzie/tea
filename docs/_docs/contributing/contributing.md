---
title: Contributing
permalink: /docs/contributing/
---

Contributions are welcome through the [tea GitHub repository](https://github.com/jniedzie/tea).

## Before changing the framework

Confirm that the behavior belongs in reusable `tea` code rather than the analysis repository’s `apps/` or `libs/user_extensions/`. Keep a change focused and include a reproducer for bugs.

## Validate a change

Build from a clean enough environment to exercise CMake configuration:

```bash
source tea/build.sh
```

Run the relevant application on a small ROOT file. Plotting and documentation changes also need rendered visual inspection; a successful build is not equivalent to correct output.

## Formatting

C++ (`clang-format`) and Python (`ruff format`) are enforced through [pre-commit](https://pre-commit.com/), both locally once the hook is enabled and in CI, where the `lint` job runs `pre-commit run --all-files` regardless of the local setup. It is installed when `tea` is installed with `install.sh`.

`pre-commit` and `ruff` belong to the locked environment, so activating it is the whole installation step:

```bash
source tea/setup.sh
```

Each commit then formats the staged files. If desired, run the CI checks on demand with:

```bash
pre-commit run --all-files
```

When updating a formatter, change the pinned `rev` in `.pre-commit-config.yaml`, and keep the `ruff` version in `environment/environment.yml` equal to the `ruff-pre-commit` `rev` so that the environment and the hook cannot disagree.

### Editor integration

When VS Code is available, `source tea/build.sh` creates or updates the analysis
project's top-level `.vscode/settings.json` and `.vscode/extensions.json`. The
generated settings use the `tea` environment's Python, Ruff, and clang-format
executables and the repository's `ruff.toml` and `.clang-format` files. Python
files are formatted on save with Autopep8 using two-space indentation and a
120-character line length; Ruff remains enabled for diagnostics. C++ formatting
uses clang-format through the Microsoft C/C++ extension. Existing unrelated
workspace settings and extension recommendations are preserved.

VS Code recommends, but does not install automatically, these extensions:

- `ms-python.python`
- `ms-python.autopep8`
- `charliermarsh.ruff`
- `ms-vscode.cpptools`

After opening or reloading the project, VS Code checks which recommendations are
missing and can offer **Install**, **Show Recommendations**, or **Don't Show
Again for this Repository**. The last choice is remembered for that repository
on that machine, so declining does not cause a prompt on every reload. The
recommendations remain available from **Extensions: Show Recommended
Extensions** in the Command Palette.

If missing recommendations are listed but no notification appears, open the VS
Code user settings and remove `"extensions.ignoreRecommendations": true` or set
it to `false`, then run **Developer: Reload Window**. This is a user preference;
`tea` does not override it in the project settings.

If an existing `.vscode/settings.json` or `.vscode/extensions.json` contains
JSON comments or invalid JSON, `tea` leaves that file unchanged and prints a
warning instead of risking the loss of user content.

### A hook fails with a bad interpreter

Hooks build a small virtual environment from whichever Python ran `pre-commit`. Inside the tea environment that interpreter lives under `TEA_HOME`, where environments are keyed by the contents of the lock files. Changing a lock retires the previous environment, which can leave a cached hook referring to an interpreter that no longer exists. Discard the cached hook environments and let the next run rebuild them:

```bash
pre-commit clean
```

## Documentation

Documentation lives on the `gh-pages` branch under `docs/`. Preview it with:

```bash
cd docs
./run.sh
```

Open `http://localhost:4000/tea/docs/home/` while the command remains running. Stop it with Ctrl-C.
