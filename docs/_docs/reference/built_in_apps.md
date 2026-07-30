---
title: Built-in applications
permalink: /docs/built_in_apps/
---

The build installs C++ executables and links Python applications from `tea/apps/examples/` into `bin/`.

## Core analysis applications

| App | Purpose | Main output |
| --- | --- | --- |
| `histogrammer` | Fill configured tree variables. | Histogram ROOT file |
| `skimmer` | Select events and prune branches. | ROOT tree and cut flow |
| `plotter.py` | Plot histogram samples. | PDF or image files |
| `submitter.py` | Run an app over file sets. | Per-job outputs |

## Specialized applications

The repository also contains helpers for merging, scale-factor writing, HepMC conversion, ABCD studies, and limit production. Some require extra software or analysis-specific configuration. Their presence is not a guarantee that a complete workflow is documented.

## Discover options

Python apps expose current arguments through:

```bash
python3 APP.py --help
```

C++ apps use the arguments declared in their source or generated template. See the task page for the normal command before adding optional overrides.
