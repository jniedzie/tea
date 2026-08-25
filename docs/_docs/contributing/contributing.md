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

C++ (`clang-format`) and Python (`ruff format`) are enforced through [pre-commit](https://pre-commit.com/), both locally once the hook is enabled and in CI, where the `lint` job runs `pre-commit run --all-files` regardless of the local setup.

`pre-commit` and `ruff` belong to the locked environment, so activating it is the whole installation step:

```bash
source tea/setup.sh
```

Enable the hook once per checkout, from the root of the `tea` repository:

```bash
pre-commit install
```

Each commit then formats the staged files. If desired, run the CI checks on demand with:

```bash
pre-commit run --all-files
```

When updating a formatter, change the pinned `rev` in `.pre-commit-config.yaml`, and keep the `ruff` version in `environment/environment.yml` equal to the `ruff-pre-commit` `rev` so that the environment and the hook cannot disagree.

### Editor integration

No editor configuration ships with the repository.

- Python: install the `charliermarsh.ruff` extension. It discovers `ruff.toml` from the repository root, and the environment provides a `ruff` of the pinned version, so the editor and the hook agree.
- C++: install `ms-vscode.cpptools` and set `"C_Cpp.formatting": "clangFormat"` and `"C_Cpp.clang_format_style": "file"`, or install `xaver.clang-format` instead. Both read `.clang-format` from the repository root. Since `clang-format` is not on `PATH`, point the extension at the binary the hook installed:

```bash
ls -d ~/.cache/pre-commit/repo*/py_env-*/bin/clang-format
```

Using that path makes the editor and the hook the same executable.

- Format-on-save, in your own `settings.json`:

```json
{
  "editor.formatOnSave": true
}
```

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
