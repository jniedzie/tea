---
title: Build and run
nav_title: Build and run
permalink: /docs/build/
---

## Full build

From the analysis root:

```bash
source tea/build.sh
```

The script configures CMake, builds and installs the project into `bin/`, links Python files there, and updates `PYTHONPATH` for the current shell. It preserves the existing build unless you request a clean build:

```bash
source tea/build.sh --clean
```

## Run an application

Applications are designed to run from `bin/`:

```bash
cd bin
./histogrammer --config histogrammer_config.py
./skimmer --config skimmer_config.py
python plotter.py --config minimal_plotter_config.py
```

These commands use example configs linked into `bin/` by the build. Python
applications provide `--help`; for compiled C++ applications, follow the
command shown on the relevant documentation page. Run the applications from
`bin/` so that relative paths in the example configs resolve correctly.

## Build after changes

Run the same build command after adding generated code, adding a Python config,
or changing C++:

```bash
source tea/build.sh
```

The script reuses the existing build when it can, so there is no separate
incremental-build command to remember. Python configs and scripts are linked
into `bin/`; editing an existing Python file does not require another build.
