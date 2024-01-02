---
title: Extra event collections
permalink: /docs/extra_event_collections/
---

Let's say we want to produce a ROOT file with 2 histograms: transverse momenta and pseudorapidity of leptons (e/μ) with φ ∈ (0, 2) from `backgrounds_dy.root` file.

## Prepare config file

For this we can use the existing `histogrammer` app and copy the example histogrammer config:

```bash
cp tea/configs/examples/histogrammer_config.py configs/my_histogrammer_config.py
```

We will use a feature called `extraEventCollections` to achieve our goal. It allows us to define new collections on the fly. All we need to provide are:
- the name of the new collection
- input collections
- (optional) selections on variables that exist in all input collections

For instance, it could look like this:

```python
extraEventCollections = {
    "GoodLeptons": {
        "inputCollections": ("Muon", "Electron"),
        "phi": (0., 2.),
    },
}
```

Then, you can define default histograms using this collection:

```python
defaultHistParams = (
#  collection      variable          bins    xmin     xmax     dir
  ("GoodLeptons" , "pt"            , 400,    0,       200,     ""  ),
  ("GoodLeptons" , "eta"           , 100,    -2.5,    2.5,     ""  ),
)
```

## Build and run

Then, build the project and run `histogrammer`, specifying the corresponding config file:

```bash
./tea/build.sh
cd bin
./histogrammer my_histogrammer_config.py
```

Have a look at the output file - you should see filled-in histograms of lepton pt and η, only for leptons with φ ∈ (0, 2).
