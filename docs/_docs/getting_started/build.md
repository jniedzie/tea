---
title: Build, run, modify
permalink: /docs/build/
---

## Pre-requisites

To make sure you're using supported versions of Python and ROOT, we recommend to craete a conda environment for `tea`:

```bash
conda create -c conda-forge --name tea root python=3.8
```

Then, activate it (has to be repeated in each new session, or added to `~/.bash_profile`):

```bash
conda activate tea
```

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