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

## Update an older macOS CMake file

If the analysis `CMakeLists.txt` contains these unconditional settings, remove
them:

```cmake
set(CMAKE_OSX_ARCHITECTURES "arm64")
SET(CMAKE_OSX_DEPLOYMENT_TARGET 13.2)
```

The managed toolchain now chooses the architecture. Analyses without these
lines need no CMake edit.

## Select storage

`tea` uses `~/.tea` by default, independently of the analysis repository's location. You can use a different location - this is especially recommended on lxplus and other systems where `~/.tea` may not have enough quota to create the environment. Save it without editing a shell startup file:

```bash
mkdir -p "${XDG_CONFIG_HOME:-$HOME/.config}/tea"
printf '%s\n' /shared/path/.tea > "${XDG_CONFIG_HOME:-$HOME/.config}/tea/home"
```

Alternatively, export `TEA_HOME=/shared/path/.tea`; an exported value has precedence over the saved setting. On a batch system, select a path visible on both login and worker nodes.

## Build and validate

Perform one clean build so no objects from the old compiler or ROOT remain:

```bash
source tea/build.sh --clean
```

The first invocation downloads the locked environment. Later builds and other
tea checkouts using the same storage location and lock reuse it. Confirm the
active versions:

```bash
cd bin
python -c 'import ROOT, correctionlib; print(ROOT.gROOT.GetVersion(), correctionlib.__version__)'
```

Run a representative small input through a compiled application before a full
batch submission. The old external Conda environment is not deleted; remove it
only after the migrated analysis has been validated.
