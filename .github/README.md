# Welcome to TEA!

## Introduction
TEA stands for Toolkit for Efficient Analysis. It is a set of loop-based tools built in C++ and Python, which will help you with:
- reading any kind of flat ntuples stored in ROOT files (e.g. NanoAOD or HEPMC converted to ROOT),
- applying selections,
- saving skimmed trees,
- creating cut flow tables,
- creating histograms,
- plotting histograms.

Upcoming features:
- submission to HTCondor based grid systems (e.g. lxplus or NAF),
- optimization and verification of ABCD method for background estimation,
- estimation of systematic uncertainties,
- applying correction (e.g. Jet Energy Corrections, Jet Energy Resolution, Pile-Up reweighting, etc.),
- calculating limits with Combine,
- ...

For these instructions we will use a scenario in which you start working on a ttH analysis.

## Getting started

### Repositories setup

We highly recommend that you keep your analysis code in a git repository, while (optionally) downloading updates in the TEA framework from our repository. In order to do that:

1. Create your analysis repository on github (go to your profile -> repositories -> new, pick a suitable name and create). Don't add any README, licence or gitignore.
2. Create an empty directory for your analysis:
```bash
mkdir tea_ttH_analysis
cd tea_ttH_analysis
```
4. Clone TEA repository:
```bash
git clone https://github.com/jniedzie/tea.git .
```
5. Setup git remotes:
```bash
git remote set-url origin git@github.com:your_username/your_repo.git
git remote add upstream git@github.com:jniedzie/tea.git
git push origin main
```

Now you can regularly push to your repository:
```bash
git add path_to_file
git commit -m "Commit message"
git push origin main
```

while from time to time you can also pull changes from TEA repository:
```bash
git pull --rebase upstream main
```

Keep in mind that if you modify parts for the framework itself, you will have to resolve conflicts when updating TEA.
You can (and should!) modify README.md though - it will be ignored when pulling changes from upstream.

### Conda environment

To make sure you're using supported versions of Python and ROOT, we recommend to craete a conda environment for TEA:

```bash
conda create -c conda-forge --name tea root python=3.8
conda activate tea
```

### Building and running the project

Building TEA together with your analysis files is very straighforward:

```
mkdir build
cd build
cmake ..
make -j install
```

Once compiled, you can execute any of the apps directly from the `bin` directory (all configs will also be installed in this directory), e.g. `./skimmer skimmer_config.py`.

## General concepts

TEA has a very simple structure, with libraries, apps and configs:

```
\apps
  \examples
  \ttH_analysis
\configs
  \examples
  \ttH_analysis
\libs
  \core
  \extensions
  \histogramming
```

### Apps

The `apps` directory contains apps, which use the library to perform certain tasks, such as skimming the data or creating histograms. Whenever you want to implement a new app, you will simply call the `create.py` script first to create a skeleton for your new app:

```
python craete.py --type app --name ttH_loose_skimming --path ttH_analysis
```

This will automatically create required directories, a C++ file, and a Python config. You also don't need to worry about CMake, linking or any of these things - it will work automagically.
Once you create your app, you can open your C++ file from `apps/ttH_analysis/ttH_loose_skimming.cpp` and the config from `configs/ttH_analysis/ttH_loose_skimming.py`.

In the `apps/examples` directory you will find some ideas for how to fill in your C++ file. You can use a number of tools such as event reader/writer, config manager, histogram handler or profiler to achieve your task. In most cases, your `main` function will contain a loop over events, in which
you will apply selections, fill histograms, or add events to the output file.

### Configs

Configs in TEA are written in Python, which allows to generate some settings programatically (e.g. imagine you want to create a large number of histograms with names `hist1`, `hist2`, `hist3`, etc. - you can do that in a loop). It also means you don't have to recompile anything when changing some options.

### Libs

Directories like `core` and `histogramming` contain C++ classes which you can use to implement your analysis. The `extensions` directory contains some general-purpose tools, but is also the place where you can add your own classes. In order to do that, use the `create.py` script:

```
python craete.py --type HistogramFiller --name tthHistogramFiller
```

or

```
python craete.py --type PhysicsObject --name TopQuark
```

or

```
python craete.py --type Event --name tthEvent
```

Depending on what kind of functionality you need, you may choose to create a HistogramFiller, a PhysicsObject, or an Event.

[add more explanation here]




