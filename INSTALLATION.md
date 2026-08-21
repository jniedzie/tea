# Installing tea

Tea installs ROOT, correctionlib, Python, CMake, and the platform compiler from
committed lock files. The resulting environment is shared by sibling analyses
and is recreated automatically if it is removed.

## New analysis

Create and enter an empty analysis directory, then download the installer:

```bash
mkdir my_analysis
cd my_analysis
curl -O https://raw.githubusercontent.com/jniedzie/tea/main/install.sh
chmod 700 install.sh
./install.sh git@github.com:YOUR_ACCOUNT/my_analysis.git
```

By default, an analysis at `/work/analyses/my_analysis` uses
`/work/analyses/.tea`. Other analysis repositories under `/work/analyses`
reuse the same environment when they use the same tea dependency lock.

To choose another persistent location, pass an absolute path:

```bash
./install.sh --tea-home /shared/path/.tea \
  git@github.com:YOUR_ACCOUNT/my_analysis.git
```

The installer stores this choice in `${XDG_CONFIG_HOME:-$HOME/.config}/tea/home`.
Tea reads that file directly, so the installer does not need to edit
`.bash_profile`, `.bashrc`, or `.zshrc`. An exported `TEA_HOME` overrides both
the saved and default locations.

The first installation downloads the locked packages and takes longer. Later
analyses reuse the completed environment.

## Use the analysis

In a new terminal, activate the environment and analysis paths:

```bash
source tea/setup.sh
```

Build after changing C++ or adding files:

```bash
source tea/build.sh
```

Both scripts recreate a missing shared environment. After either build script
or setup script has been sourced, applications continue to run normally from
`bin/`:

```bash
cd bin
./histogrammer --config histogrammer_config.py
python plotter.py --config plotter_config.py
```

Prepare the environment on a login node before submitting batch jobs. The
chosen `TEA_HOME` must be visible at the same absolute path on worker nodes.

## Supported platforms

The committed locks cover:

- Linux x86-64 (`linux-64`), with a glibc 2.17 compatibility floor;
- Apple Silicon macOS (`osx-arm64`), macOS 13 or newer;
- Intel macOS (`osx-64`), macOS 13 or newer.

CI validates the Linux lock in an AlmaLinux 9 container and the Apple Silicon
lock on macOS. The same Linux lock is intended for lxplus, NAF, and T2B, but a
CI container cannot prove the worker-node filesystem and operating-system
properties of those sites. After sourcing `tea/setup.sh`, run
`tea/ci/collect-environment.sh SITE_NAME` on a login or representative worker
node when qualifying a new site.

## Updating dependencies

Ordinary tea builds never update dependencies. Maintainers change
`environment/environment.yml`, regenerate all lock files with `conda-lock`,
review the lock diff, and test it in CI. A changed lock creates a new shared
environment while analyses using an older tea lock continue to use the old
one.
