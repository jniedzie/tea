---
title: Calculate custom histograms
permalink: /docs/tutorial_custom_histograms/
redirect_from:
  - /docs/custom_histogrammer/
---

## Prerequisites and goal

Complete the selection exercise and be comfortable rebuilding C++. The goal is to calculate observables that do not exist as input branches, starting with the invariant mass of the best dimuon candidate.

## Generate the app

From the analysis root:

```bash
python3 tea/create.py --type task4_histogrammer --name llp_histogrammer
```

This creates `apps/llp_histogrammer.cpp` and `configs/llp_histogrammer.py` from the current DAS exercise templates.

## Define calculated histograms

In `configs/llp_histogrammer.py`, complete `histParams`:

```python
histParams = (
  ("Dimuon", "minv", 100, 0, 100, ""),
  ("Dimuon", "logLxy", 70, -4, 3, ""),
)
```

Keep the `TightMuons`, `LooseMuons`, and `LooseElectrons` collections internally consistent with the event cuts. Set:

```python
process = "tta_mAlp-12GeV_ctau-1e2mm"
inputFilePath = f"{base_path}/{process}/output_0.root"
histogramsOutputFilePath = f"../results/tutorial/histograms/{process}/after_selections.root"
```

## Fill the variables

The generated app already converts an `Event` to `NanoEvent` and retrieves `GetBestDimuonVertex()`. Its `HistogramsHandler::Fill` names must match the config-generated names:

```cpp
histogramsHandler->Fill("Dimuon_minv", bestDimuon->GetInvariantMass());
```

Add the displacement observable using methods implemented by `NanoDimuonVertex`; consult the header in `tea/libs/extensions/include/NanoDimuonVertex.hpp` for the exact current method rather than guessing it.

## Build and run

```bash
source tea/build.sh
cd bin
./llp_histogrammer --config llp_histogrammer.py
```

## Expected output

The ROOT file under `results/tutorial/histograms/tta_mAlp-12GeV_ctau-1e2mm/` should contain the declared dimuon histograms and a cut flow. Confirm that the histograms have entries and physically sensible ranges.

## Next step

[Compare data and simulation]({{ "/docs/tutorial_data_mc/" | relative_url }}).
