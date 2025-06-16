---
title: Prerequisites
permalink: /docs/prerequisites/
---

### Git setup

In case you're working with an older version of git, we suggest to set default branch name to `main`:

```bash
git config --global init.defaultBranch main
```

### Dependencies

`tea` only depends on `ROOT` libraries and optionally `correctionlib` if you're planning on applying CMS scale factors. 

Below you can find instructions for some common situations, but basically you can just install ROOT your prefered way.

#### lxplus

The only important thing is to use lxplus9, where new versions of cmake, GCC, etc. are available by default. Simply login using:

```bash
ssh -Y username@lxplus9.cern.ch
```

Optionally, install `correctionlib`, which is a package that helps us to deal with scale factors and other corrections:

```bash
python3 -m pip install correctionlib --no-binary=correctionlib
```

In case you see some errors related to `correctionlib`, you can also try installing the latest development version instead (more information [here](https://cms-nanoaod.github.io/correctionlib/install.html)):

```bash
python3 -m pip install git+https://github.com/cms-nanoAOD/correctionlib.git
```

#### Setting environment with Conda

If you prefer to use a Conda environemnt, make sure you have Miniconda or Anaconda installed on your machine - see [Conda installation instructions](https://conda.io/projects/conda/en/latest/user-guide/install/index.html).

Then, create a new conda environment for `tea` (this may take a longer while):

```bash
conda create -c conda-forge --name tea root python=3.8
conda activate tea
```

The activate command has to be repeated in each new session, or added to `~/.bash_profile`.

Optionally, install `correctionlib`, which is a package that helps us to deal with scale factors and other corrections:

```bash
python3 -m pip install correctionlib --no-binary=correctionlib
```

In case you see some errors related to `correctionlib`, you can also try installing the latest development version instead (more information [here](https://cms-nanoaod.github.io/correctionlib/install.html)):

```bash
python3 -m pip install git+https://github.com/cms-nanoAOD/correctionlib.git
```

#### Conda on NAF

If you're working on NAF, you can use an existing Conda environment:

```bash
conda activate /nfs/dust/cms/user/jniedzie/conda/tea
```

Also in this case, the activate command has to be repeated in each new session, or added to `~/.bash_profile`.