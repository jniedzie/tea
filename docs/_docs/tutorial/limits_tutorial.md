---
title: Set an expected limit
permalink: /docs/tutorial_limits/
redirect_from:
  - /docs/limits/
---

## Prerequisites and scope

This is an advanced, optional exercise. It requires matching signal and background histograms for several signal masses plus a working CMS Combine environment. Combine is not installed by `tea`, and the example `combine_path` is site-specific.

The goal is to produce datacards, run `AsymptoticLimits`, and draw an expected limit. This page does not present limits as a finished turnkey feature for arbitrary analyses.

## Prepare the configuration

```bash
cp tea/configs/das_exercises/task6_limits_config.py \
  configs/tutorial/expected_limits.py
```

Update:

- `combine_path` to a working `CMSSW_*/src` containing Combine;
- every sample path to the histogram files you produced;
- `histogram` to a discriminating histogram present with identical binning in every file;
- `reference_cross_section` to a numerically reasonable reference;
- the luminosity and nuisance model to match the samples.

For current `limits_producer.py`, also set:

```python
use_combined_limits = False
```

## Run

From `bin/`:

```bash
python3 limits_producer.py --config expected_limits.py
python3 limits_plotter.py --config expected_limits.py
```

## Expected output

The configured output directories should contain text datacards, Combine logs, a limits text file, and a PDF Brazil plot. Read the Combine logs and check the datacards; the existence of a PDF is not sufficient validation.

## Next step

[Process larger samples]({{ "/docs/tutorial_submission/" | relative_url }}) with the submitter.
