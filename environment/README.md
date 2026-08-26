# Dependency lock maintenance

Users do not need `conda-lock`; `build.sh` and `setup.sh` consume the committed
explicit locks with an existing `micromamba` from `PATH`, when available. If it
is not installed, Tea downloads and verifies its pinned micromamba executable.

To intentionally update the dependency set, install `conda-lock`, edit
`environment.yml`, and regenerate every supported platform from this directory:

```bash
conda-lock lock \
  --kind explicit \
  --file environment.yml \
  --platform linux-64 \
  --platform osx-arm64 \
  --platform osx-64 \
  --filename-template 'conda-{platform}.lock'
```

`virtual-packages.yml` fixes the assumed glibc and macOS compatibility floors.
Review all three lock diffs and let CI install them without an existing cache.
Changing a lock changes the shared environment path automatically; never edit
an explicit lock by hand.

The formatting tools are pinned in `environment.yml` and must match
`.pre-commit-config.yaml`. In particular, Tea uses clang-format 19.1.7 because
clang-format 22 requires libxml2 2.14.6 or newer, while ROOT 6.34.10 requires
libxml2 2.13.x.
