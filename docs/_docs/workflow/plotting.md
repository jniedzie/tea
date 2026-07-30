---
title: Plotting
permalink: /docs/plotting/
---

`plotter.py` reads histogram ROOT files and produces styled plots. It supports background stacks, overlaid signals, data points, luminosity normalization, legends, uncertainties, and data-to-simulation ratios.

## Define samples

Each `Sample` identifies a ROOT file, its role, normalization, and style:

```python
samples = (
  Sample(
    name="tt_semi",
    file_path="../histograms/background_ttsemileptonic.root",
    type=SampleType.background,
    cross_section=365.34,
    fill_color=ROOT.kRed - 2,
    legend_description="semileptonic t#bar{t}",
  ),
)
```

## Define plots

```python
histograms = (
  Histogram(
    "Muon_pt",                    # name
    "",                           # title
    False,                        # set log-x
    True,                         # set log-y
    NormalizationType.to_lumi,    # normalization type
    1,                            # rebin
    0,                            # x min
    200,                          # x max
    1,                            # y min
    1e4,                          # y max
    "Muon p_{T} [GeV]",           # x label
    "Events",                     # y label
  ),
)
```

The histogram name must match the name stored in each sample file. Set `luminosity` in the unit consistent with your cross-sections unit when using `NormalizationType.to_lumi`.

## Run

```bash
cd bin
python plotter.py --config my_plotter_config.py
```

Plots are written in `output_path`. Start with [Plot the histograms]({{ "/docs/tutorial_plotting/" | relative_url }}) and use `tea/configs/examples/plotter_config.py` as the broader configuration reference.
