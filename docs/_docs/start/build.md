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

Both `build.sh` and `setup.sh` select the exact dependency lock for the current
platform. If its shared environment is missing, they recreate it. Dependency
versions are not resolved or updated during an ordinary build.

In a new terminal where no rebuild is needed, activate the same environment
and analysis paths with:

```bash
source tea/setup.sh
```

The environment appears as `(tea)` in an interactive Bash prompt. Tea keeps
the existing prompt formatting, including colours and multiline layouts, and
only prepends that short label; the internal lock hash remains part of the
storage path rather than the displayed name.

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

No environment-specific runner is needed. After sourcing `build.sh` or
`setup.sh`, continue to use `python app_name.py` and `./app_name` directly.

## Build after changes

Run the same build command after adding generated code, adding a Python config,
or changing C++:

```bash
source tea/build.sh
```

The script reuses the existing build when it can, so there is no separate
incremental-build command to remember. Python configs and scripts are linked
into `bin/`; editing an existing Python file does not require another build.

When a tea update changes the dependency lock, the shared environment path also
changes. `build.sh` detects the new compiler and library paths and clears stale
CMake state automatically.
