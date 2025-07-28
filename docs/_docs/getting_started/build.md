---
title: Build & run
permalink: /docs/build/
---


## Build & run

Building `tea` together with your analysis files is very straighforward. Simply run the build script:

```bash
source tea/build.sh
```

Once compiled, you can go to `bin` directory and execute any of the apps directly from there (all configs will also be installed in this directory), e.g.: 

```bash
cd bin
./skimmer skimmer_config.py
```

## Repeated compilation

The above script is useful for first-time build, as well as for when major changes to the project are introduced. However, it is a bit slower, since it always removes `build` and `bin` directories and sets everything up from scratch. If you want to re-compile the project quickly, make sure python paths are set up (only needed once per session, and is done automatically when using `build.sh` script):

```bash
source tea/setup.sh
```

Then, simply go to `build` directory and run:

```bash
cd build
make -j install
```

## Modifications to Python files

All Python files are just symlinked in `bin` directory, therefore you don't need to re-build or re-compile when making changes to Python files.