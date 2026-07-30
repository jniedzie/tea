---
title: Selections and skimming events
nav_title: Selections and skimming
permalink: /docs/selecting_skimming/
redirect_from:
  - /docs/skimming/
---

Selection decides which events continue through an analysis. Skimming applies that selection and writes the surviving events to a smaller ROOT tree.

## Define object collections

`extraEventCollections` builds named collections from existing objects:

```python
extraEventCollections = {
  "TightMuons": {
    "inputCollections": ["Muon"],
    "pt": (30.0, 9999999.0),
    "eta": (-2.4, 2.4),
    "pfRelIso04_all": (0.0, 0.15),
    "tightId": True,
  },
}
```

This produces the event-level count `nTightMuons`, which can be used in `eventCuts`.

## Define event cuts

```python
triggerSelection = ("HLT_IsoMu24",)

eventCuts = {
  "MET_pt": (50.0, 9999999.0),
  "nTightMuons": (2, 9999999),
}
```

Ranges are inclusive lower and upper bounds. Use a deliberately large upper bound when only a minimum matters.

## Run the skimmer

Set `inputFilePath`, `treeOutputFilePath`, and branch pruning in the same config, then:

```bash
cd bin
./skimmer --config my_skimmer_config.py
```

The output ROOT file contains only events passing the trigger and event cuts. The cut flow is saved and printed. For a complete exercise, follow [Select and skim events]({{ "/docs/tutorial_skimming/" | relative_url }}).

## Use custom logic

If configuration-only cuts are insufficient, create a custom app and call `EventProcessor` and/or your own selection functions inside the event loop. Keep code in [custom physics objects and events]({{ "/docs/custom_data_model/" | relative_url }}).
