---
title: Custom histogrammer
permalink: /docs/custom_histogrammer/
---

This is probably the most complex excercise, involving creation of a custom app, modifying the config, and adding a custom HistogramsFiller. The task is the following: Produce a histogram of Δφ between each pair of electron-muon in events from `backgrounds_dy.root` file.

## Create and fill in a custom HistogramsFiller

Using `create.py` script (see [create.py script]({{site.baseurl}}/docs/create_script/) for details) to create a new HistogramsFiller class:

```bash
python create.py --type HistogramsFiller --name TTZHistogramsFiller
```

Open the .cpp file produced. The only method we’re interested in is Fill(...), which... fills histograms. It receives an event and has access to `HistogramsHandler` (as well as `EventProcessor` and `ConfigManager`, but we don’t need that now). You also don’t need to define histograms here, but simply use `histogramsHandler->Fill(“hist_name”, value, weight)` to fill the histogram. For simplicity, let’s assume Δφ = |φμ - φe|. The example code would look like this:

```cpp
void TTZHistogramsFiller::Fill(const std::shared_ptr<Event> event) {
  auto muons = event->GetCollection("Muon");
  auto electrons = event->GetCollection("Electron");

  for(auto muon : *muons) {
    float muonPhi = muon->Get("phi");

    for(auto electron : *electrons) {
      float electronPhi = electron->Get("phi");
      float deltaPhi = fabs(muonPhi - electronPhi);
      histogramsHandler->Fill("electron_muon_delta_phi", deltaPhi, GetWeight(event));
    }
  }
}
```

## Create custom histogrammer app

In order to call our `TTZHistogramsFiller`, we will need to also create a custom histogrammer app. Use `create.py` script (see [create.py script]({{site.baseurl}}/docs/create_script/) for details):

```bash
python create.py --type histogrammer --name ttZ_analysis_histogrammer --path ttZ_analysis
```

Open the .cpp file and create an instance of `TTZHistogramsFiller`. In the event loop, call the Fill(...) method of our TTZHistogramsFiller. The example (skipping typical parts of an app which were auto-generated) would look like this:

```cpp
#include "TTZHistogramsFiller.hpp"
// ...
int main(int argc, char **argv) {
  // ...
  auto ttZhistogramsFiller = make_unique<TTZHistogramsFiller>(histogramsHandler);
  // ...
  for (int iEvent = 0; iEvent < eventReader->GetNevents(); iEvent++) {
    auto event = eventReader->GetEvent(iEvent);
    ttZhistogramsFiller->Fill(event);
  }
  // ...
  histogramsHandler->SaveHistograms();
  return 0;
}
```

## Prepare the config

In the config file, apart from defining input/output files and other typical values, we should define a custom histogram:

```python
histParams = (
    ("electron_muon_delta_phi",      100,  0,      7,     ""),
)
```

## Build and run

Finally, build the project and run the app, specifying the corresponding config file:

```bash
source build.sh
cd bin
./ttZ_analysis_histogrammer ttZ_analysis_histogrammer_config.py
```

Have a look at the output file - you should see filled-in histogram of Δφ between electrons and muons.
