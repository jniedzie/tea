---
title: My first histogrammer
permalink: /docs/my_first_histogrammer/
---

In our first example we will produce a ROOT file with histograms of transverse momentum and pseudorapidity of all electrons in `backgrounds_dy.root` file. 

---

## Prepare config file

Creating histograms for default branches is trivial in `tea` - we will use the default `histogrammer` app for that. We will need a config, and since we don’t want to modify anything that’s part of `tea`, let’s copy the example histogrammer config:

```bash
cp tea/configs/examples/histogrammer_config.py configs/my_histogrammer_config.py
```

Open the config and make the necessary modifications:
- Number of events to run on (-1 means all).
- Input & output paths (hint: look at `“samples”` directory).
- Names of collections and variables we want to look at.
- Name of the weights branch (if not provided, w=1).
- You can comment out what we don’t need, like `extraEventCollections` or `histParams`.

An example config could look like this:

```python
nEvents = -1
printEveryNevents = 1000

inputFilePath = "../tea/samples/background_dy.root"
histogramsOutputFilePath = "../samples/histograms/background_dy.root"

defaultHistParams = (
#  collection  variable   bins    xmin    xmax     dir
  ("Electron", "pt"  ,    400,     0    , 200,     ""  ),
  ("Electron", "eta" ,    100,    -2.5  , 2.5,     ""  ),
)
```

---

## Build & run

Then, build the project and run `histogrammer`, specifying the corresponding config file:

```bash
source tea/build.sh
cd bin
./histogrammer --config my_histogrammer_config.py
```

Have a look at the output file - you should see histograms of electron pt and η.
