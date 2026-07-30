---
title: First analysis
permalink: /docs/first_analysis/
---

This quick start builds `tea`, reads the included DY sample, and writes a ROOT file containing electron histograms. It assumes that you completed [Installation]({{ "/docs/installation/" | relative_url }}).

## Build tea

Run from the analysis root:

```bash
source tea/build.sh
```

The build places the ready-to-run example config at
`bin/minimal_histogrammer_config.py`. Open that file and look through it before
running the application:

```python
nEvents = 1000

inputFilePath = "../tea/samples/background_dy.root"
histogramsOutputFilePath = "../results/minimal_histograms.root"

defaultHistParams = (
  #  collection      variable          bins    xmin     xmax     dir
  ("Electron",       "pt",             40,     0,       200,     ""),
  ("Electron",       "eta",            50,    -2.5,      2.5,    ""),
)
```

Paths in application configs are resolved while running from `bin/`, which is
why the input starts with `../tea/`.

## Run the histogrammer

```bash
cd bin
./histogrammer --config minimal_histogrammer_config.py
```

The application creates the output directory when needed. Expected output:
`results/minimal_histograms.root`, with `Electron_pt`, `Electron_eta`, and
cut-flow histograms.

## What happened

The built-in `histogrammer` opened the ROOT `Events` tree, created collections from NanoAOD-style branch names, filled the requested histograms, and saved them. No custom C++ code was needed.

Continue with the [full tutorial]({{ "/docs/tutorial_overview/" | relative_url }}), which develops this workflow into a small long-lived-particle analysis.
