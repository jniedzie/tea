---
title: Select and skim events
permalink: /docs/tutorial_skimming/
redirect_from:
  - /docs/my_first_skimming/
---

## Prerequisites and goal

You need access to the DAS signal file. The goal is to keep events with missing transverse momentum and at least two tight muons, while writing only the muon and displaced-dimuon collections needed later.

## Prepare the skimmer config

```bash
cp tea/configs/das_exercises/task3_skimmer.py configs/skim_signal.py
```

Complete the event selection:

```python
eventCuts = {
  "MET_pt": (50, 9999999),
  "nTightMuons": (2, 9999999),
}
```

Keep the relevant collection branches and their sizes:

```python
branchesToKeep = (
  "Muon_*",
  "nMuon",
  "PatMuonVertex_*",
  "nPatMuonVertex",
  "MET_*",
  "genWeight",
)
```

Write inside the shared tutorial output tree:

```python
treeOutputFilePath = "../results/tutorial/trees/tta_mAlp-12GeV_ctau-1e2mm.root"
```

## Run

```bash
source tea/build.sh
cd bin
./skimmer --config skim_signal.py
```

## Expected output

The terminal prints a cut flow. The output tree should contain fewer entries and fewer branches than the input:

```bash
rootls -t ../results/tutorial/trees/tta_mAlp-12GeV_ctau-1e2mm.root
```

Verify that the collections and their size branches are readable.

## Next step

[Calculate custom histograms]({{ "/docs/tutorial_custom_histograms/" | relative_url }}) from dimuon candidates.
