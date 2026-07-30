---
title: Installation
permalink: /docs/installation/
redirect_from:
  - /docs/repo_setup/
  - /docs/prerequisites/
---

`tea` is normally installed as a Git submodule inside an analysis repository. You need Git, CMake 3.14 or newer, a C++17 compiler, Python 3 with development headers, and ROOT. `correctionlib` is optional unless your analysis applies CMS corrections.

## Prepare the environment

On CERN lxplus, use an EL9 host:

```bash
ssh -Y USERNAME@lxplus9.cern.ch
```

Use a ROOT installation compatible with your compiler and Python. Confirm the main tools before installing:

```bash
root-config --version
cmake --version
python3 --version
```

For CMS corrections, install `correctionlib` in the same Python environment:

```bash
python3 -m pip install correctionlib --no-binary=correctionlib
```

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
submodule, connects the GitHub repository, and pushes the initial project.
Installing without a linked GitHub repository is not part of the recommended
setup.

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
