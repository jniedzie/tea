---
title: Make simple histograms
permalink: /docs/tutorial_histograms/
redirect_from:
  - /docs/my_first_histogrammer/
---

## Prerequisites and goal

Complete the [tutorial setup]({{ "/docs/tutorial_overview/" | relative_url }}) and build `tea`. The goal is to histogram the muon multiplicity, transverse momentum, and pseudorapidity for a semileptonic top background sample.

## Prepare the configuration

From the analysis root:

```bash
cp tea/configs/das_exercises/task1_simple_histograms.py \
  configs/tutorial/simple_histograms.py
```

Set the paths and histogram definitions:

```python
base_path = "/eos/cms/store/group/committee_schools/2025-cmsdas-hamburg/llp/samples"
process = "background_ttsemileptonic"

inputFilePath = f"{base_path}/{process}/output_0.root"
histogramsOutputFilePath = f"../results/tutorial/histograms/{process}.root"

defaultHistParams = (
  ("Event", "nMuon", 50, 0, 50, ""),
  ("Muon", "pt", 400, 0, 200, ""),
  ("Muon", "eta", 100, -2.5, 2.5, ""),
)

weightsBranchName = "genWeight"
```

## Build and run

Rebuild so the new config is linked into `bin/`, then run:

```bash
source tea/build.sh
cd bin
./histogrammer --config simple_histograms.py
```

## Expected output

`results/tutorial/histograms/background_ttsemileptonic.root` should contain `Event_nMuon`, `Muon_pt`, `Muon_eta`, and cut-flow histograms. Inspect the keys with:

```bash
rootls ../results/tutorial/histograms/background_ttsemileptonic.root
```

If the file is missing, check the input path and create the output directory from the tutorial overview.

## Next step

[Plot the histograms]({{ "/docs/tutorial_plotting/" | relative_url }}) and overlay an LLP signal.
