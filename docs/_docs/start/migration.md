---
title: Migrate an existing analysis
nav_title: Migration
permalink: /docs/migration/
---

The locked build environment can be adopted without deleting an existing
analysis or its old Conda environment.

## Review and update

From the analysis root, first make sure local work is committed or
intentionally retained:

```bash
git status
git -C tea status
```

Then update the submodule and record its new commit:

```bash
git -C tea fetch origin
git -C tea switch main
git -C tea pull --ff-only
git add tea
git commit -m "Update tea build environment"
```

When testing an unmerged tea feature, switch the submodule to that feature
branch instead of `main`.

## Run the migration

Choose a persistent location for the shared Tea environment, then run the
migration script from the analysis root:

```bash
./tea/migrate.sh --tea-home /shared/path/.tea
```

The script performs all one-time setup that a new project receives from
`install.sh`:

- records the selected location in
  `${XDG_CONFIG_HOME:-$HOME/.config}/tea/home`;
- removes the obsolete `CMAKE_OSX_ARCHITECTURES` and
  `CMAKE_OSX_DEPLOYMENT_TARGET` lines from an older `CMakeLists.txt`, if
  present;
- performs a clean build using the managed environment;
- configures the analysis workspace for VS Code; and
- runs `pre-commit install` in the `tea` submodule.

The command is safe to rerun if it is interrupted. It does not delete the old
external Conda environment; remove that environment only after validating the
migrated analysis.

`tea` uses `~/.tea` for new installations by default, independently of the
analysis repository's location, but the migration command requires the choice
to be explicit. A different location is especially recommended on lxplus and
other systems where `~/.tea` may not have enough quota for the approximately
3 GB environment. On lxplus, prefer AFS when possible. EOS also works, but
creating the environment there is much slower. On a batch system, select a path
visible at the same absolute location on login and worker nodes.

## Validate

After the migration finishes, confirm the active versions:

```bash
cd bin
python -c 'import ROOT, correctionlib; print(ROOT.gROOT.GetVersion(), correctionlib.__version__)'
```

Run a representative small input through a compiled application before a full
batch submission. Later builds and other Tea checkouts using the same storage
location and lock reuse the completed environment.
