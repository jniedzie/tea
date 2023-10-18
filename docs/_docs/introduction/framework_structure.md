---
title: Framework structure
permalink: /docs/framework_structure/
---

## Directories overview

The framework contains a few main directories:
- apps
- bin
- build
- configs
- libs
- pylibs
- samples
- templates

plus a number of scripts and files in the main directory. In the following sections each of the main directories will be described.

### apps

Contains both example and user apps. An app uses `tea` libraries/modules and is built into an executable that performs some actions. Examples of apps could be `histogrammer` or `skimmer`.

### bin

All executables and configs will end up here and this is where you should run them. In case of Python files, a symlink will be created, such that no rebuilding is necessary when you make some modifications. It is a temporary directory.

### build

It's a temporary directory where the project is built. This also means that when no new files are added, but modifications are made to some existing files, one can run `make -j install` in this directory to compile and install, without having to configure everything from scratch (which happend when you call `source build.sh`).

### configs

Constains example and user-defined Python configuration files.

### libs

A directory containing `core`, `extensions`, and `histogramming` libraries. It also contains a directory `user_extensions` for user-defined classes.

### pylibs

Contains Python-based modules: `plotting` and `submitter`.

### samples

A few example ROOT files for tests and tutorial exercises.

### templates

Template files for the `create.py` script, which can automatically generate apps, configs, and classes entering C++ libs.
