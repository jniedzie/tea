# Migrating an existing analysis

The migration preserves the analysis repository, its `tea` submodule history,
and any existing Conda environment.

## 1. Review the checkout

From the analysis root, make sure analysis and submodule changes are committed
or intentionally retained:

```bash
git status
git -C tea status
```

## 2. Update `tea`

Update the submodule to the `tea` revision containing the locked environment:

```bash
git -C tea fetch origin
git -C tea switch main
git -C tea pull --ff-only
git add tea
git commit -m "Update tea build environment"
```

If the change is still being tested on a feature branch, switch to that branch
instead of `main` and record its commit in the analysis repository.

## 3. Remove obsolete macOS settings

Older generated `CMakeLists.txt` files contain these unconditional lines:

```cmake
set(CMAKE_OSX_ARCHITECTURES "arm64")
SET(CMAKE_OSX_DEPLOYMENT_TARGET 13.2)
```

Delete both lines. The locked compiler toolchain now selects the correct macOS
architecture. No equivalent change is needed in analysis files that do not
contain these lines.

## 4. Select the environment location

The `tea` environment location defaults to `~/.tea`, independently of the analysis repository's location. To use the default, no configuration is needed. To select a different location, save it explicitly (replace `/shared/path/.tea` below):

```bash
mkdir -p "${XDG_CONFIG_HOME:-$HOME/.config}/tea"
printf '%s\n' /shared/path/.tea > "${XDG_CONFIG_HOME:-$HOME/.config}/tea/home"
```

You can instead export `TEA_HOME`; it takes precedence over the saved setting.

## 5. Rebuild once from a clean CMake state

```bash
source tea/build.sh --clean
```

The first invocation downloads and creates the locked environment. Future
builds and any other `tea` checkout using the same environment location reuse it.
The old external Conda environment is not deleted; remove it later only after
the migrated analysis has been validated.

## 6. Validate before submitting full jobs

```bash
cd bin
python -c 'import ROOT, correctionlib; print(ROOT.gROOT.GetVersion(), correctionlib.__version__)'
```

Then run one compiled application on a representative small input as the final migration check (e.g., `./histogrammer --config histogrammer_config.py`).
On batch systems, confirm that `TEA_HOME` is mounted at the same path on worker nodes.
