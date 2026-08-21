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

C++ (`clang-format`) and Python (`ruff format`) are enforced via [pre-commit](https://pre-commit.com/), both locally (once installed) and in CI — the `lint` job runs `pre-commit run --all-files` regardless of whether the local hook is enabled.

These tools are not provisioned by `install.sh`/`build.sh`, so install them yourself:

- [ruff](https://docs.astral.sh/ruff/installation/)
- [pre-commit](https://pre-commit.com/#install)
- `clang-format`: ships with [LLVM](https://releases.llvm.org/download.html), or install via your package manager, e.g. `brew install clang-format`, `apt install clang-format`, `conda install -c conda-forge clang-format`.

Once installed, enable the hook once per checkout from the repo root:

```bash
pre-commit install
```

After that, every commit auto-formats staged files. Run it on demand (what CI does) with:

```bash
pre-commit run --all-files
```

### VS Code

No editor config ships with the repo, so set this up yourself:

- Python: install the `charliermarsh.ruff` extension — it auto-discovers `ruff.toml`.
- C++: install `ms-vscode.cpptools` and set `"C_Cpp.formatting": "clangFormat"` and `"C_Cpp.clang_format_style": "file"`, or install `xaver.clang-format` instead — both pick up `.clang-format` from the repo root.
- Format-on-save, in your own `settings.json`:

```json
{
  "editor.formatOnSave": true
}
```

## Documentation

Documentation lives on the `gh-pages` branch under `docs/`. Preview it with:

```bash
cd docs
./run.sh
```

Open `http://localhost:4000/tea/docs/home/` while the command remains running. Stop it with Ctrl-C.
