---
title: Contributing
permalink: /docs/contributing/
---

Contributions are welcome through the [tea GitHub repository](https://github.com/jniedzie/tea).

## Before changing the framework

Confirm that the behavior belongs in reusable `tea` code rather than the analysis repository’s `apps/` or `libs/user_extensions/`. Keep a change focused and include a reproducer for bugs.

## Validate a change

Build from a clean enough environment to exercise CMake configuration:

```bash
source tea/build.sh
```

Run the relevant application on a small ROOT file. Plotting and documentation changes also need rendered visual inspection; a successful build is not equivalent to correct output.

## Documentation

Documentation lives on the `gh-pages` branch under `docs/`. Preview it with:

```bash
cd docs
./run.sh
```

Open `http://localhost:4000/tea/docs/home/` while the command remains running. Stop it with Ctrl-C.
