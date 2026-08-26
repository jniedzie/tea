# Dependency lock maintenance

Users do not need `conda-lock`; `build.sh` and `setup.sh` consume the committed
explicit locks with an existing `micromamba` from `PATH`, when available. If it
is not installed, `tea` downloads and verifies its pinned micromamba executable.
`tea` ignores user micromamba/Conda rc files while creating this environment and
uses temporary installation storage under `${TMPDIR:-/tmp}`. On a local
filesystem, micromamba creates the environment directly at its final path. On
AFS, EOS, NFS, and similar network filesystems, `tea` instead creates the complete
environment locally, uses `conda-pack --dest-prefix` to rewrite embedded paths
to the final shared prefix, and publishes the relocated tree with 32 bounded
parallel copy workers. The completed sibling directory is renamed into place,
so another process never observes a partially published environment. Temporary
installation data is removed afterward. Normal activation still honors user
settings.

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
`tea` installs the active lock at the stable, editor-friendly prefix
`${TEA_HOME:-~/.tea}/environments/tea`. Changing a lock replaces that
environment, and activation removes obsolete hash-named environments created by
older `tea` versions. Never edit an explicit lock by hand. If the same home
directory is shared concurrently across different operating systems, configure
a separate `TEA_HOME` for each system.

The formatting tools are pinned in `environment.yml` and must match
`.pre-commit-config.yaml`. In particular, `tea` uses clang-format 19.1.7 because
clang-format 22 requires libxml2 2.14.6 or newer, while ROOT 6.34.10 requires
libxml2 2.13.x.

`conda-pack` is part of the locked environment because network-storage installs
use it for prefix-safe local staging. Do not replace that relocation with a
symlink: micromamba resolves the symlink and embeds the temporary physical path.

`tea` depends on conda-forge's `root_base`, not the `root` metapackage.
`root_base` contains ROOT, PyROOT, `root-config`, and `hadd`; the metapackage
also installs notebook tooling, Numba, and Fortran compilers that `tea` does
not use.

The canonical VS Code configuration is stored in `templates/.vscode`.
`environment/configure_vscode.py` copies and merges those templates into the
analysis project's top-level `.vscode` directory, replacing `tea` placeholders
with concrete paths to its Python, Ruff, configuration, and clang-format. It is
a one-time setup, so `install.sh` offers it once as a question (`--vscode` and
`--no-vscode` answer it non-interactively) and `build.sh` never runs it. An
already installed analysis, and any analysis migrated from an older `tea`, runs
it directly; `MIGRATION.md` gives the command. No VS Code installation is
required at configuration time, and the files are ready if the project is later
opened in VS Code. Existing unrelated settings and recommendations are
preserved. Python formatting uses
Autopep8 with `tea`'s two-space indentation, which can also recover some invalid
indentation that Ruff cannot parse; Ruff remains enabled for diagnostics. A
settings file that uses JSON comments is left unchanged with a warning because
rewriting JSON-with-comments safely would risk losing user formatting or
comments.
