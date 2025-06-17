---
title: My first plots
permalink: /docs/my_first_plots/
---

The goal of this exercise is to create PDF files with plots of pt and η of electrons from the [My first histogrammer]({{site.baseurl}}/docs/my_first_histogrammer/) exercise. If you haven't already, complete this exercise first, as we will need files created there as an input for this exercise.

---

## Prepare config file

Start by copying an example plotter config:

```bash
cp tea/configs/examples/minimal_plotter_config.py configs/my_plotter_config.py
```

Open the file and apply modifications listed in the following subsections.

### Samples, input, output

First, we need to specify samples to include in the `samples` dictionary - in our case it’s just one DY sample. Names of parameters in the `Sample` initializer should be quite self-explanatory. One should also provide the `output_path` where plots will be stored.

An example of this part of the config:

```python
samples = (
  Sample(
    name="DY",
    file_path="../samples/histograms/background_dy.root",
    type=SampleType.background,
    cross_section=0.4,
    line_alpha=0.0,
    fill_color=ROOT.kRed-2,
    fill_alpha=0.7,
    marker_size=0.0,
    legend_description="DY"
  ),
)

output_path = "../plots"
```

### Defining histograms

Next, we need to define histograms to plot. In our case, this will be `Electron_pt` and `Electron_eta` - if not sure which histograms can be plotted, you can check directly in the histograms file. There are a few options to normalize histograms - we will normalize to luminosity * cross-section.

In this case, it’s also important that we provide the luminosity we want to scale to:

```python
histograms = (
#            name            title             logy    norm_type                  rebin xmin xmax ymin ymax  xlabel         ylabel
  Histogram("Electron_pt" , "Electron p_{T}",  True,   NormalizationType.to_lumi, 5,   0  , 150,  1,   1e3 , "p_{T} [GeV]", "# events (2018)"),
  Histogram("Electron_eta", "Electron #eta",   False,  NormalizationType.to_lumi, 5,  -2.4, 2.4,  0,   70  , "#eta"       , "# events (2018)"),
)

luminosity = 63670. # pb^-1 (2018)
```

### Legends and other visuals

Finally, let’s specify:
- Where to put the legend: we only have one background, but in principle, you could specify positions of signals and data legends here as well.
- The canvas size.
- We should turn off ratio plotting (since we only have one sample).

Here's an example of this part of the config:

```python
canvas_size = (800, 600)
show_ratio_plots = False

legends = {
  SampleType.background: Legend(0.7, 0.8, 0.85, 0.85, "f"),
}
```

### Complete config example

Putting everything together, here's a complete config:

```python
import ROOT
from Sample import Sample, SampleType
from Legend import Legend
from Histogram import Histogram
from HistogramNormalizer import NormalizationType

samples = (
  Sample(
    name="DY",
    file_path="../samples/histograms/background_dy.root",
    type=SampleType.background,
    cross_section=0.4,
    line_alpha=0.0,
    fill_color=ROOT.kRed-2,
    fill_alpha=0.7,
    marker_size=0.0,
    legend_description="DY"
  ),
)
output_path = "../plots"

histograms = (
#            name            title             logx   logy    norm_type                  rebin xmin xmax ymin ymax  xlabel         ylabel
  Histogram("Electron_pt" , "Electron p_{T}",  False, True,   NormalizationType.to_lumi, 5,   0  , 150,  1,   1e3 , "p_{T} [GeV]", "# events (2018)"),
  Histogram("Electron_eta", "Electron #eta",   False, False,  NormalizationType.to_lumi, 5,  -2.4, 2.4,  0,   70  , "#eta"       , "# events (2018)"),
)
luminosity = 63670. # pb^-1 (2018)

legends = {
  SampleType.background: Legend(0.7, 0.8, 0.85, 0.85, "f"),
}

canvas_size = (800, 600)
show_ratio_plots = False

plotting_options = {
    SampleType.background: "hist",
    SampleType.signal: "nostack hist",
    SampleType.data: "nostack e",
}
```

---

## Build & run

Now we are ready to build and run:

```bash
source tea/build.sh
cd bin
python plotter.py my_plotter_config.py
```

Have a look at `plots` directory - you should get nice PDF files with electron pt and η there!
