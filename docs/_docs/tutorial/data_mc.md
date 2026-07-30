---
title: Compare data and simulation
permalink: /docs/tutorial_data_mc/
---

## Prerequisites and goal

You need the tutorial’s selection definitions and histogramming workflow. The goal is to apply the same configuration to collision data and semileptonic top simulation, then make a ratio plot.

## Prepare the analysis config

```bash
cp tea/configs/das_exercises/task5_data_mc.py \
  configs/tutorial/data_mc_histograms.py
```

Complete the `TightMuons`, `LooseElectrons`, and `GoodJets` selections, then define control-region event cuts. Run the same configuration once with:

```python
process = "background_ttsemileptonic"
weightsBranchName = "genWeight"
```

and once with:

```python
process = "collision_data_2018"
```

Do not apply a simulation event-weight branch to collision data. Give each process a distinct output path below `results/tutorial/histograms/`.

## Produce matching histograms

```bash
source tea/build.sh
cd bin
./histogrammer --config data_mc_histograms.py
```

Run once per process after changing the process-specific settings, or split them into two explicit configs.

## Plot the comparison

Copy the task-2 plotting config, define the background sample as `SampleType.background` and collision data as `SampleType.data`, then enable:

```python
show_ratio_plots = True
ratio_limits = (0.5, 1.5)
```

Run `plotter.py` as in the previous plotting exercise.

## Expected output

The plot should show a filled simulation histogram, data points with uncertainties, and a ratio panel. Investigate missing files, empty histograms, or incompatible binning before interpreting the ratio.

## Next step

Continue to the optional [expected-limit exercise]({{ "/docs/tutorial_limits/" | relative_url }}) or skip directly to [larger samples]({{ "/docs/tutorial_submission/" | relative_url }}).
