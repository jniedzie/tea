---
title: Tutorial overview
nav_title: Overview and prerequisites
permalink: /docs/tutorial_overview/
---

This tutorial adapts the CMS DAS 2025 Hamburg LLP exercise sequence to the current `tea` repository. You will build a small search for an axion-like particle produced with a top-quark pair and decaying to two muons.

## Prerequisites

You need:

- an installed and built analysis project; see [Installation]({{ "/docs/installation/" | relative_url }});
- ROOT, CMake, a C++17 compiler, and Python;
- access to `/eos/cms/store/group/committee_schools/2025-cmsdas-hamburg/llp/` for the DAS samples;
- an lxplus environment for the EOS and HTCondor steps;
- CMS Combine only for the optional limits step.

If you do not have access to the DAS EOS area, use the repository’s small sample files for the first two exercises and adapt the collection names to their contents. The later LLP-specific exercises require the DAS samples or equivalent NanoAOD files.

## Inputs and outputs

The tutorial uses:

```text
/eos/cms/store/group/committee_schools/2025-cmsdas-hamburg/llp/
├── samples/
└── large_samples/
```

All application commands run from `bin/`, so tutorial output paths begin with `../results/tutorial/`.

## What you will produce

By the end, you will have:

- a skimmed signal tree;
- a custom C++ histogrammer for dimuon observables;
- ROOT histograms for background, signal, and collision data;
- data-vs-simulation plots;
- optionally, a Combine datacard and expected-limit plot;
- a files configuration that scales the workflow to larger samples.

## Learning path

1. [Make simple histograms]({{ "/docs/tutorial_histograms/" | relative_url }})
2. [Plot the histograms]({{ "/docs/tutorial_plotting/" | relative_url }})
3. [Select and skim events]({{ "/docs/tutorial_skimming/" | relative_url }})
4. [Calculate custom histograms]({{ "/docs/tutorial_custom_histograms/" | relative_url }})
5. [Compare data and simulation]({{ "/docs/tutorial_data_mc/" | relative_url }})
6. [Set an expected limit]({{ "/docs/tutorial_limits/" | relative_url }}) (advanced and optional)
7. [Process larger samples]({{ "/docs/tutorial_submission/" | relative_url }})

The first step is [Make simple histograms]({{ "/docs/tutorial_histograms/" | relative_url }}).
