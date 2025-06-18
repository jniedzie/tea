---
title: Scale Factors
permalink: /docs/scale_factors/
---

For CMS users: scale factors are handled by `correctionlib` and use values from the official CMS `jsonPOG` repository. The types of scale factors are defined in [`scale_factors_config.py`](https://github.com/jniedzie/tea/blob/main/configs/examples/scale_factors_config.py) and currently include Run 2 and Run 3 SFs for muons (PAT and DSA), muon trigger, b-jets, pileup, and PU jet ID.

To apply them, you can place `applyScaleFactors` in your config (or in files config, in case you're running on multiple files):


```python
applyScaleFactors = {
  # name :     (nominal, variation)
  "muon":         (True, True),
  "muonTrigger":  (True, True),
  "pileup":       (True, True),
  "bTagging":     (True, True),
  "PUjetID":      (True, True),
}
```

As you can see, the second column of values specifies if variations of a given scale factor should also be taken into account in systematics calculation. If yes, selected histograms will be generated with this scale factor being shifted up and down.


If the scale factors you need are missing - feel free to contribute by creating a PR, or create an [issue in GitHub](https://github.com/jniedzie/tea/issues)!