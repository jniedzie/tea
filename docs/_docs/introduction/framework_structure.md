---
title: Framework structure
permalink: /docs/framework_structure/
---

## Directories overview

After setting up the framework as explained in [Installation]({{site.baseurl}}/docs/repo_setup/), you will see the following directories/files:
- apps/
- bin/
- build/
- configs/
- libs/
- tea/
- CMakeLists.txt

### apps

Contains your apps. An app uses `tea` libraries/modules and is built into an executable that performs some actions. Examples of apps could be a `histogrammer` or a `skimmer`.

### bin

All executables and configs will end up here and this is where you should run them. In case of python files, a symlink will be created, such that no rebuilding is necessary when you make some modifications. It is a temporary directory, so don't store anything important there.

### build

It's a temporary directory where the project is built. This also means that when no new files are added, but modifications are made to some existing files, one can run `make -j install` in this directory to compile and install, without having to configure everything from scratch (which happens when you call `./tea/build.sh`).

### configs

Constains your python configuration files.

### libs

A directory containing `user_extensions` library for user-defined classes.

### tea

The core framework is located in `tea` directory. Typically, you don't need to modify anything there. Also, the example apps and configs from `tea` will be copied to `bin` directory once you build the project as explained in [Build & run]({{site.baseurl}}/docs/build/), so unless you're a `tea` developer, there's no need to enter this directory.

### utils

This is a directory for any standalone python tools you may want to write for your analysis. Maybe it's a custom plotting script, or some merging script. They are independent from `tea`, but could include some stuff from your tea configs - just put whatever you want there, it will be linked in the `bin` directory.

### CMakeLists

This is the top-level CMake project definition, which builds your libraries, apps, links them against `tea` libraries, as well as makes links to python configs and modules. You don't need to modify this file by hand - newly added apps/configs/classes will be automatically recognized.
