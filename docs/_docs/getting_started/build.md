---
title: Build, run, modify
permalink: /docs/build/
---

## Pre-requisites

`tea` only depends on ROOT libraries, but we need to make sure the correct versions of ROOT, Python, GCC, and other packages are installed. We propose to use a Conda environment (however, you may be able to achive it with other solutions too).

### Running on lxplus

The only important thing is to use lxplus9, where new versions of cmake, GCC, etc. are available by default. Simply login using:

```bash
ssh -Y username@lxplus9.cern.ch
```

Then, we need to install `correctionlib`, which is a package that helps us to deal with scale factors and other corrections:

```bash
python3 -m pip install correctionlib --no-binary=correctionlib
```

In case you see some errors related to `correctionlib`, you can also try installing the latest development version instead (more information [here](https://cms-nanoaod.github.io/correctionlib/install.html)):

```bash
python3 -m pip install git+https://github.com/cms-nanoAOD/correctionlib.git
```

### Setting environment with Conda

First, make sure you have Miniconda or Anaconda installed on your machine - see [Conda installation instructions](https://conda.io/projects/conda/en/latest/user-guide/install/index.html).

Then, create a new conda environment for `tea` (this may take a longer while):

```bash
conda create -c conda-forge --name tea root python=3.8
conda activate tea
```

The activate command has to be repeated in each new session, or added to `~/.bash_profile`.

Then, we need to install `correctionlib`, which is a package that helps us to deal with scale factors and other corrections:

```bash
python3 -m pip install correctionlib --no-binary=correctionlib
```

In case you see some errors related to `correctionlib`, you can also try installing the latest development version instead (more information [here](https://cms-nanoaod.github.io/correctionlib/install.html)):

```bash
python3 -m pip install git+https://github.com/cms-nanoAOD/correctionlib.git
```

### Conda on NAF

If you're working on NAF, you can use an existing Conda environment:

```bash
conda activate /nfs/dust/cms/user/jniedzie/conda/tea
```

Also in this case, the activate command has to be repeated in each new session, or added to `~/.bash_profile`.

## Build & run

Building `tea` together with your analysis files is very straighforward. Simply source the build script:

```bash
./tea/build.sh
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