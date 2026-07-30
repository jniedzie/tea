---
title: Plot the histograms
permalink: /docs/tutorial_plotting/
redirect_from:
  - /docs/my_first_plots/
---

## Prerequisites and goal

You need the background histogram file from [Make simple histograms]({{ "/docs/tutorial_histograms/" | relative_url }}). Repeat that configuration with `process = "tta_mAlp-12GeV_ctau-1e2mm"` to produce the matching signal file.

The goal is to overlay the signal on the background and write PDF plots.

## Prepare the plotting config

```bash
cp tea/configs/das_exercises/task2_plotting.py configs/plot_histograms.py
```

Point the two `Sample` entries at:

```python
file_path="../results/tutorial/histograms/background_ttsemileptonic.root"
```

and:

```python
file_path="../results/tutorial/histograms/tta_mAlp-12GeV_ctau-1e2mm.root"
```

Set:

```python
output_path = "../results/tutorial/plots/simple/"
```

Keep histogram names consistent with the previous exercise:

```python
histograms = (
  Histogram("Muon_pt", "", False, True, NormalizationType.to_lumi,
            1, 0, 200, 1, 1e4, "Muon p_{T} [GeV]", "Events"),
  Histogram("Muon_eta", "", False, False, NormalizationType.to_lumi,
            1, -2.4, 2.4, 0, 250, "Muon #eta", "Events"),
)
```

## Run

```bash
source tea/build.sh
cd bin
python3 plotter.py --config plot_histograms.py
```

## Expected output

`results/tutorial/plots/simple/` should contain plots for `Muon_pt` and `Muon_eta`. Confirm that both sample labels appear and that the axes match the configuration. A successful Python exit alone does not verify the rendered plot.

## Next step

[Select and skim events]({{ "/docs/tutorial_skimming/" | relative_url }}).
