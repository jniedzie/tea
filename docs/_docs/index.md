---
title: Welcome to <code class="monospace">tea</code>
nav_title: Overview
permalink: /docs/home/
redirect_from:
  - /docs/index.html
---

<img src="{{ "/assets/img/tea_logo_black_extended_inv.jpg" | relative_url }}" alt="Toolkit for Efficient Analysis logo" width="400" align="right"/>

`tea`—the Toolkit for Efficient Analysis—is a C++ and Python toolkit for loop-based analysis of ROOT trees. It handles repetitive work such as tree I/O, object collections, event selection, histogramming, plotting, corrections, and batch submission while leaving analysis decisions in readable code and Python configuration.

New users should start with the [guided LLP tutorial]({{ "/docs/tutorial_overview/" | relative_url }}). For a shorter check that the installation works, follow [First analysis]({{ "/docs/first_analysis/" | relative_url }}).

## Main workflow

1. [Install `tea`]({{ "/docs/installation/" | relative_url }}) inside an analysis repository.
2. [Read ROOT trees]({{ "/docs/tree_io/" | relative_url }}) and define object collections.
3. [Select or skim events]({{ "/docs/selecting_skimming/" | relative_url }}).
4. [Produce histograms]({{ "/docs/histogramming/" | relative_url }}) and [make plots]({{ "/docs/plotting/" | relative_url }}).
5. [Submit independent jobs]({{ "/docs/job_submission/" | relative_url }}) when the input grows.

## Get help

For questions, bugs, and feature requests, open a [GitHub issue](https://github.com/jniedzie/tea/issues). The [roadmap]({{ "/docs/roadmap/" | relative_url }}) distinguishes documented workflows from incomplete documentation.

## Analyses using tea

`tea` has supported collider and phenomenology analyses using NanoAOD-like and HepMC-derived ROOT inputs. The [analyses page]({{ "/docs/analyses/" | relative_url }}) keeps this community list separate from the beginner path.
