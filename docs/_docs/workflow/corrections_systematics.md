---
title: Corrections and systematic variations
nav_title: Corrections and systematics
permalink: /docs/corrections_systematics/
redirect_from:
  - /docs/scale_factors/
  - /docs/systematics/
---

`tea` can read CMS correction sets through `correctionlib`, with `jsonPOG` being a submodule included in `tea`. Some common Scale Factors (SFs) are configured in `tea/configs/examples/scale_factors_config.py`. You can use these keys in your config (or files config for multiple files submission, which has a higher presedence):

## Select corrections

```python
applyScaleFactors = {
  # name:          (apply nominal, produce variations)
  "muon":          (True, True),
  "muonTrigger":   (True, True),
  "pileup":        (True, True),
  "bTagging":      (True, True),
  "PUjetID":       (True, True),
}
```

If the SFs you need are not included in the `scale_factors_config.py`, you can create your own config, and/or propose a PR to `tea` including more keys.

## Variation histograms

The implementation of histograms with variations is currently quite rough -> We are working on improving it and providing a full documentation.

