---
title: Histogramming
permalink: /docs/histogramming/
---

The built-in `histogrammer` turns ROOT tree branches into one- or two-dimensional histograms. Use configuration for existing variables and a custom C++ app when the variable must be calculated.

## Configure existing variables

```python
defaultHistParams = (
  # collection  variable  bins  xmin  xmax  directory
  ("Muon",       "pt",     40,   0,    200,  ""),
  ("Muon",       "eta",    50,  -2.5,  2.5,  ""),
  ("Event",      "nMuon",  10,   0,     10,  ""),
)
```

The histogram names are `Collection_variable`, such as `Muon_pt`. Set `weightsBranchName` to an event-weight branch such as `genWeight`, or omit it when every event should have weight one.

## Run

```bash
cd bin
./histogrammer --config my_histogrammer_config.py
```

Set `histogramsOutputFilePath` in the config. The application also writes cut-flow histograms.

## Calculate new variables

Declare calculated histogram names in `histParams`, then fill those exact names from C++ with `HistogramsHandler::Fill`. The [custom histogram tutorial]({{ "/docs/tutorial_custom_histograms/" | relative_url }}) shows the full pattern.
