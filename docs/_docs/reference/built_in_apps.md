---
title: Built-in applications
permalink: /docs/built_in_apps/
---

The build installs the C++ executables and links the Python applications from
`tea/apps/examples/` into `bin/`. The applications below are the complete set
of built-in entry points in that directory. They normally take a Python config;
run `APP --help` (or `python3 APP.py --help`) for the options in the checkout
you are using.

## C++ applications

| App | Description | Main output |
| --- | --- | --- |
| `histogrammer` | Reads a ROOT `Events` tree, constructs the configured event collections, fills the default one- and two-dimensional variables, and records the cut flow. It is intended for variables already available in the input tree; calculated analysis variables belong in a custom histogrammer. | Configured histogram ROOT file, including the cut-flow histograms |
| `skimmer` | Reads a ROOT `Events` tree, applies the configured trigger and event selections, and writes only events that pass. The writer can also prune branches according to the skimmer configuration. | Selected/pruned ROOT tree and cut-flow information |
| `hepmc2root` | Converts an ASCII HepMC event file into a ROOT `Events` tree containing event-level information and fixed-size particle arrays, so it can be read by ROOT-based analysis code. | ROOT file with a HepMC-derived `Events` tree |

## Python applications

| App | Description | Main output |
| --- | --- | --- |
| `plotter.py` | Reads histogram ROOT files for the configured samples and draws one- and two-dimensional histograms, stacked backgrounds, signal overlays, data points, and configured ratios. | Plot files written to the config's output directory |
| `submitter.py` | Runs another tea application over a files configuration. It supports sequential local jobs, local parallel jobs, and HTCondor submission, with optional logging and resubmission of failed jobs. | Per-input-file trees or histograms, plus optional job logs |
| `merge.py` | Builds a merge plan from a files configuration and combines ROOT tree and/or histogram outputs in batches with `hadd`. It can run locally, submit merge jobs to HTCondor, or show a dry-run plan. | Merged ROOT files in derived output directories |
| `abcd_plotter.py` | Performs the ABCD background-estimation study configured by the user: evaluates correlation and closure, searches for acceptable binning, applies quality thresholds, and produces background, signal, projection, ratio, and optimal-point plots. | ABCD diagnostic and optimization plots, parameters, and logs |
| `sf_writer.py` | Builds one- or two-dimensional data/MC scale factors from configured histograms, evaluates configured uncertainty variations and extrapolations, produces validation plots, and writes the result as a correctionlib JSON file. | Scale-factor plots and a correction JSON file |
| `limits_producer.py` | Creates datacards from the configured signal/background histograms and invokes the CMS Combine method selected on the command line, locally or through HTCondor. It also extracts expected limits and significances into result files. | Datacards, Combine logs, and limits/significance result files |
| `limits_plotter.py` | Reads the limits result file produced by `limits_producer.py` and draws expected (and, where configured, observed) Brazil-band limit graphs over the configured scan. | PDF limit plots |

The `abcd_plotter.py`, `sf_writer.py`, and limit applications require their
corresponding analysis configuration and external packages. In particular,
`limits_producer.py` requires a working CMS Combine environment when it is run
for limit production; `submitter.py` and the Condor modes require the relevant
HTCondor commands and site configuration.

The repository also installs Python libraries and example/configuration files
alongside these applications. Libraries such as `HistogramPlotter`,
`ScaleFactorProducer`, and `SubmissionManager` are implementation components,
not additional command-line applications. Likewise, the files in
`configs/examples/` and `configs/das_exercises/` are configs rather than
built-in apps.

## Discover options

Python apps expose current arguments through:

```bash
python3 APP.py --help
```

C++ apps use the arguments declared in their source or generated template.
