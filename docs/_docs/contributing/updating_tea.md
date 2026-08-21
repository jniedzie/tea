---
title: Updating tea
permalink: /docs/updating_tea/
---

`tea` is a Git submodule of the analysis repository. Update it explicitly and review the recorded submodule commit.

## Update the submodule

From the analysis root:

```bash
git -C tea fetch origin
git -C tea switch main
git -C tea pull --ff-only
git add tea
git commit -m "Update tea"
```

If your analysis intentionally tracks another `tea` branch, switch to that branch rather than silently replacing it with `main`.

## Rebuild

```bash
source tea/build.sh
```

When migrating from the former externally managed ROOT/Conda setup, use
`source tea/build.sh --clean` once. A changed dependency lock selects a new
shared environment and invalidates stale CMake state automatically during
later updates.

Older macOS analysis repositories may contain these unconditional lines in the
top-level `CMakeLists.txt`:

```cmake
set(CMAKE_OSX_ARCHITECTURES "arm64")
SET(CMAKE_OSX_DEPLOYMENT_TARGET 13.2)
```

Remove both lines when migrating. The locked compiler toolchain selects the
platform architecture. See [Migrate an existing analysis]({{ "/docs/migration/" | relative_url }}) for the complete procedure.

Run the analysis smoke test or a representative small sample before processing
full data. A submodule update can change C++, Python configs, command-line
behavior, and the locked dependency stack together.
