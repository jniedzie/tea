---
title: Installation
permalink: /docs/installation/
redirect_from:
  - /docs/repo_setup/
  - /docs/prerequisites/
---

`tea` is normally installed as a Git submodule inside an analysis repository.
You need Git, Bash, and either `curl` or `wget`. The installer obtains the
tested versions of CMake, the platform compiler, Python, ROOT, correctionlib,
and their dependencies from version-controlled lock files.

## Prepare the environment

On CERN lxplus, use an EL9 host:

```bash
ssh -Y USERNAME@lxplus9.cern.ch
```

Do not load a separate ROOT or Conda environment first. Tea activates a
self-consistent toolchain while it builds.

## Create the GitHub repository

Create a new repository in your GitHub account before installing `tea`. Use the
name of your analysis and leave the repository empty: do not add a README,
license, or `.gitignore` from the GitHub form.

Copy the repository's SSH URL. It will look like:

```text
git@github.com:YOUR_ACCOUNT/YOUR_ANALYSIS.git
```

## Install tea in the analysis project

Create a local directory, download the installer, and pass the GitHub SSH URL
to it:

```bash
mkdir YOUR_ANALYSIS
cd YOUR_ANALYSIS
curl -O https://raw.githubusercontent.com/jniedzie/tea/main/install.sh
chmod 700 install.sh
./install.sh git@github.com:YOUR_ACCOUNT/YOUR_ANALYSIS.git
```

The installer initializes the local analysis repository, adds `tea/` as a
submodule, connects the GitHub repository, pushes the initial project, creates
the locked dependency environment, and performs the first build. Installing
without a linked GitHub repository is not part of the recommended setup. During
installation, press Enter at the environment-location question to use
`~/.tea`.

## Shared dependency location

`tea` stores dependencies outside the analysis repository and uses `~/.tea` by default. 
Repository placement does not affect this choice. Any `tea` checkout configured with the same location can reuse a matching locked environment, 
and `tea` recreates the environment automatically if it disappears.

You can customize the location of the `tea` environment. This is especially recommended on lxplus and other systems where `~/.tea` may not have enough quota to create the environment. Pass an absolute path (`~/...` is also accepted):

```bash
./install.sh --tea-home /shared/path/.tea \
  git@github.com:YOUR_ACCOUNT/YOUR_ANALYSIS.git
```

The installer records this choice in `${XDG_CONFIG_HOME:-$HOME/.config}/tea/home` and offers the saved choice as the default on later interactive installations. 
It does not modify shell startup files. Setting `TEA_HOME` in the shell overrides the recorded location.

The first checkout downloads the locked packages. Other checkouts using the same location reuse the completed environment. Prepare it on a login node
before submitting batch jobs; `TEA_HOME` must be mounted at the same absolute path on workers.

## Supported systems

The committed environments cover Linux x86-64 with a glibc 2.17 compatibility
floor, Apple Silicon macOS 13 or newer, and Intel macOS 13 or newer. CI tests
AlmaLinux 9 and Apple Silicon macOS. The Linux lock is intended for lxplus,
NAF, and T2B, but access to the chosen shared path and the worker-node OS must
still be qualified at each site. After sourcing `tea/setup.sh`, run
`tea/ci/collect-environment.sh SITE_NAME` on a login or representative worker
node to capture the relevant platform, glibc, filesystem, and tool versions.

## Verify the checkout

From the analysis root, these paths should now exist:

```text
apps/
configs/
libs/user_extensions/
tea/
CMakeLists.txt
```

Continue with [First analysis]({{ "/docs/first_analysis/" | relative_url }}) for a short end-to-end run, or [Build and run]({{ "/docs/build/" | relative_url }}) for build details.
