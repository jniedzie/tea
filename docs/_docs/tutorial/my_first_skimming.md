---
title: My first skimmer
permalink: /docs/my_first_skimming/
---

In this excercise we want to create a skimmed sample from `background_dy.root` keeping only events that have at least 1 muon.

---

## Prepare config file

Skimming using existing branches is simple in `tea` and we won’t need to create a new app - we will use the existing `skimmer` app.
Copy the example skimmer config:

```bash
cp tea/configs/examples/skimmer_config.py configs/my_skimmer_config.py
```

Open the config and make the necessary modifications. You could comment out a few things we won’t use:
- `triggerSelection`
- `extraEventCollections`
- `branchesToKeep`
- `branchesToRemove`


The non-obvious thing is `eventCuts`:
- You can use any event-level variable here.
- We will use nMuon and ask for it to be ∈ (1, 9999999).
- You could also do for instance something like “MET_pt”: (30, 999999).

Our config could look like this:

```python
nEvents = -1
printEveryNevents = 1000

inputFilePath = "../tea/samples/background_dy.root"
treeOutputFilePath = "../samples/skimmed/background_dy.root"

eventCuts = {
    "nMuon": (1, 9999999),
}
```

---

## Build & run

Then, build the project and run `skimmer`, specifying the corresponding config file:

```bash
source build.sh
cd bin
./skimmer --config my_skimmer_config.py
```

You should get output like this:

```
CutFlow (sum of gen weights) (sum of raw events):
0_initial 10000 10000
1_trigger 10000 10000
2_nMuon 8387 8387
```

Notice the warning about triggers - since we didn't specify triggers collection, none were applied and the app warns us about this. You can also check the output file with ROOT, or make histograms for it and plot them!
