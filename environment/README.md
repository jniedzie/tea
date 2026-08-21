# Dependency lock maintenance

Users do not need `conda-lock`; `build.sh` and `setup.sh` consume the committed
explicit locks through a pinned micromamba executable.

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
