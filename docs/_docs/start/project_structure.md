---
title: Project structure
permalink: /docs/project_structure/
redirect_from:
  - /docs/framework_structure/
  - /docs/libs/
---

An analysis keeps its code outside the `tea` submodule. This makes framework updates reviewable and prevents analysis-specific classes from being mixed into the shared toolkit.

## Analysis directories

- `apps/`: C++ applications compiled into executables.
- `configs/`: Python configuration files.
- `libs/user_extensions/`: analysis-specific C++ classes and their headers.
- `utils/`: optional analysis helpers.
- `tea/`: the framework Git submodule.
- `CMakeLists.txt`: includes the framework and analysis build rules.

## Generated directories

- `build/`: CMake state and intermediate build products.
- `bin/`: installed executables, libraries, and links to Python files.

Both are generated. Do not store analysis results or source files in them.

Dependency environments are stored outside the analysis repository. Sibling
analyses use `<parent>/.tea` by default, or the persistent `TEA_HOME` selected
during installation. An environment is identified by its platform and lock
hash, allowing old and new tea dependency sets to coexist.

## Framework extension points

Reusable framework code lives under `tea/libs/`:

- `core`: tree I/O, events, collections, configuration, cuts, logging, and corrections.
- `histogramming`: histogram creation and filling.
- `extensions`: NanoAOD and HepMC convenience classes.
- `pylibs`: plotting, submission, scale-factor, ABCD, and limit helpers.

Put analysis-specific extensions in `libs/user_extensions/`, not in these
framework directories.

## Add user code with tea/create.py

Use [`tea/create.py`]({{ "/docs/custom_app/" | relative_url }}) whenever you add
a C++ application, physics object, event class, or histogram filler. Do not
create C++ source files by hand. The generator puts files in the expected
directories, adds the required conversion helpers, and makes sure the next
build discovers the new code.

Python configuration files may be created by hand. Run `source tea/build.sh`
after adding a config so it is linked into `bin/`. Once a Python file has been
linked, editing it does not require another build.
