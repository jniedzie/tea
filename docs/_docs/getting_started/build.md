---
title: Build, run, modify
permalink: /docs/build/
---

## Pre-requisites

`tea` only depends on ROOT libraries, however we need to make sure the correct versions of ROOT, Python and GCC are installed. There are many ways to achieve that - here we propose two: 
- option 1: using packages installed on CVMFS (available on lxplus)
- option 2: using Conda to setup an environment,

### Option 1: Setting environment from CVMFS

If you're working on lxplus, or other system with access to CVMFS, you can simply source a version of ROOT available there:

```bash
source /cvmfs/sft.cern.ch/lcg/releases/LCG_104/ROOT/6.28.04/x86_64-centos7-gcc11-opt/ROOT-env.sh
```

### Option 2: Setting environment with Conda

First, make sure you have Miniconda or Anaconda installed on your machine - see [Conda installation instructions](https://conda.io/projects/conda/en/latest/user-guide/install/index.html).

Then, create a new conda environment for `tea` (this may take a longer while):

```bash
conda create -c conda-forge --name tea root python=3.8
conda activate tea
```

The activate command has to be repeated in each new session, or added to `~/.bash_profile`.

## Build & run

Building `tea` together with your analysis files is very straighforward. Simply source the build script:

```
source build.sh
```

Once compiled, you can go to `bin` directory and execute any of the apps directly from there (all configs will also be installed in this directory), e.g.: 

```bash
./skimmer skimmer_config.py
```

## Repeated compilation

The above script is useful for first-time build, as well as for when major changes to the project are introduced. However, it is a bit slower, since it always removes `build` and `bin` directories and sets everything up from scratch. If you want to re-compile the project quickly, simply go to `build` directory and run:

```bash
make -j install
```

## Modifications to Python files

All Python files are just symlinked in `bin` directory, therefore you don't need to re-build or re-compile when making changes to Python files.