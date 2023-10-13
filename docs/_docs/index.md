---
title: Welcome to <code class="monospace">tea</code>!
permalink: /docs/home/
redirect_from: /docs/index.html
---

<img src="{{site.baseurl}}//assets/img/tea_logo_black_extended_inv.jpg" alt="tea_logo" width="400" align="right"/>

`tea` (toolkit for efficient analysis) is a set of tools developed at DESY for analysis of any ROOT trees. 

It is designed for speed (CPU-intensive operations implemented in C++), based on intuitive loop-based logic, while hidding most of the tricky and tedious operations behind a user-friendly API and using Python for configuration and lightweight operations.

To get a feel for how a `tea` app looks like, have a look at an [example app]({{site.baseurl}}/docs/example_app/)


## Features
The framework will help you with:
- reading any kind of flat ntuples stored in ROOT files (e.g. NanoAOD or HEPMC converted to ROOT),
- applying selections,
- saving skimmed trees,
- creating cut flow tables,
- creating histograms,
- plotting histograms,
- submission to HTCondor based grid systems (e.g. lxplus or NAF),

Upcoming features:

- optimization and verification of ABCD method for background estimation,
- estimation of systematic uncertainties,
- applying correction (e.g. Jet Energy Corrections, Jet Energy Resolution, Pile-Up reweighting, etc.),
- calculating limits with Combine, 

<div class="grid-container">
  <div class="image-link">
    <a class="image-link" href="{{site.baseurl}}/docs/general_concepts/">
      <img src="{{site.baseurl}}//assets/img/tea_icons_tree_reader.png" alt="Alt Text">
    </a>
  </div>
  <div class="image-link">
    <a class="image-link" href="{{site.baseurl}}/docs/general_concepts/">
      <img src="{{site.baseurl}}//assets/img/tea_icons_tree_writer.png" alt="Alt Text">
    </a>
  </div>
  <div class="image-link">
    <a class="image-link" href="{{site.baseurl}}/docs/general_concepts/">
      <img src="{{site.baseurl}}//assets/img/tea_icons_grid.png" alt="Alt Text">
    </a>
  </div>
  <div class="image-link">
    <a class="image-link" href="{{site.baseurl}}/docs/general_concepts/">
      <img src="{{site.baseurl}}//assets/img/tea_icons_plotting.png" alt="Alt Text">
    </a>
  </div>
  <div class="image-link">
    <a class="image-link" href="{{site.baseurl}}/docs/general_concepts/">
      <img src="{{site.baseurl}}//assets/img/tea_icons_nano.png" alt="Alt Text">
    </a>
  </div>
  <div class="image-link">
    <a class="image-link" href="{{site.baseurl}}/docs/general_concepts/">
      <img src="{{site.baseurl}}//assets/img/tea_icons_hepmc.png" alt="Alt Text">
    </a>
  </div>
  <div class="image-link">
    <a class="image-link" href="{{site.baseurl}}/docs/general_concepts/">
      <img src="{{site.baseurl}}//assets/img/tea_icons_hist.png" alt="Alt Text">
    </a>
  </div>
  <div class="image-link">
    <a class="image-link" href="{{site.baseurl}}/docs/general_concepts/">
      <img src="{{site.baseurl}}//assets/img/tea_icons_skimming.png" alt="Alt Text">
    </a>
  </div>
</div>

## Analyses implemented with `tea`
So far, `tea` has been used by the following analyses:
- [Search for long-lived ALPs in tt̄ events](https://github.com/jniedzie/tea_ttalps)
- [CMS HGCal beam-test analysis](https://github.com/jniedzie/tea_hgcal)
- [Search for Hexaquarks](https://github.com/jniedzie/tea_hexaquarks)

We would be more than happy to welcome you and your analysis on board! 
You are also invited to contribute to `tea` - help us make it better and more suited for a wide range of scenarios by [creating PRs](https://github.com/jniedzie/tea/pulls), [reporting bugs and creating requests for features](https://github.com/jniedzie/tea/issues).