---
title: Configuration
permalink: /docs/configuration/
redirect_from:
  - /docs/configs/
---

`tea` configurations are Python modules. They may calculate repeated values or import helpers, but their final public variables form the interface consumed by C++ or Python applications.

## Common fields

| Field | Used for |
| --- | --- |
| `nEvents` | Maximum events; `-1` means all. |
| `printEveryNevents` | Progress-message interval. |
| `inputFilePath` | Input ROOT file. |
| `histogramsOutputFilePath` | Histogram ROOT output. |
| `treeOutputFilePath` | Skimmed tree output. |
| `eventsTreeNames` | Input event-tree names. |
| `weightsBranchName` | Per-event weight branch. |
| `defaultHistParams` | Existing collection variables to histogram. |
| `histParams` | Calculated histograms filled from C++. |
| `extraEventCollections` | Selected or combined object collections. |
| `triggerSelection` | Required trigger branches. |
| `eventCuts` | Event-level ranges and collection counts. |
| `branchesToKeep` / `branchesToRemove` | Output-tree pruning. |

Not every app reads every field. Start from the example config for the selected app and remove only options you have confirmed are optional.

## Python imports

The build links configs and framework Python modules into `bin/`. Run from `bin/` after sourcing `tea/build.sh`, or ensure the equivalent module paths are available.

## Paths

Shipped configs assume execution from `bin/`; relative inputs and outputs therefore commonly start with `../`. Prefer paths derived from one clearly named base directory over repeated literals.
