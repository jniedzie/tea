# Dependency lock maintenance

Users do not need `conda-lock`; `build.sh` and `setup.sh` consume the committed
explicit locks with an existing `micromamba` from `PATH`, when available. If it
is not installed, Tea downloads and verifies its pinned micromamba executable.

To intentionally update the dependency set, install `conda-lock`, edit
`environment.yml`, and regenerate every supported platform from this directory:

```bash
conda-lock lock \
  --kind explicit \
  --file environment.yml \
  --platform linux-64 \
  --platform osx-arm64 \
  --platform osx-64 \
  --filename-template 'conda-{platform}.lock'
```

`virtual-packages.yml` fixes the assumed glibc and macOS compatibility floors.
Review all three lock diffs and let CI install them without an existing cache.
Tea installs the active lock at the stable, editor-friendly prefix
`${TEA_HOME:-~/.tea}/environments/tea`. Changing a lock replaces that
environment, and activation removes obsolete hash-named environments created by
older `tea` versions. Never edit an explicit lock by hand. If the same home
directory is shared concurrently across different operating systems, configure
a separate `TEA_HOME` for each system.

The formatting tools are pinned in `environment.yml` and must match
`.pre-commit-config.yaml`. In particular, Tea uses clang-format 19.1.7 because
clang-format 22 requires libxml2 2.14.6 or newer, while ROOT 6.34.10 requires
libxml2 2.13.x.

The canonical VS Code configuration is stored in `templates/.vscode`. When VS
Code is installed, `build.sh` copies and merges those templates into the
analysis project's top-level `.vscode` directory, replacing Tea placeholders
with concrete paths to its Python, Ruff, configuration, and clang-format. This
also happens during installation because `install.sh` runs `build.sh`. Existing
unrelated settings and recommendations are preserved. Python formatting uses
Autopep8 with Tea's two-space indentation, which can also recover some invalid
indentation that Ruff cannot parse; Ruff remains enabled for diagnostics. A
settings file that uses JSON comments is left unchanged with a warning because
rewriting JSON-with-comments safely would risk losing user formatting or
comments.
