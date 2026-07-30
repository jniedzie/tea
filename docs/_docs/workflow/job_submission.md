---
title: Submitting jobs
nav_title: Submitting jobs
permalink: /docs/job_submission/
---

`submitter.py` is the canonical interface for running one app over many files. It supports sequential local execution, parallel local execution, and HTCondor.

## Prepare two configs

The app config defines analysis behavior. The files config defines samples and input/output paths. For example, a files config can expose a list of `samples` plus `input_directory` and `output_hists_dir`; the app config imports it and builds its paths.

Use `tea/configs/das_exercises/task7_files_config.py` and the corresponding task config as a working example.

## Run locally

Run on lxplus (or some other supported node), from `bin/`:

```bash
python submitter.py \
  --app histogrammer \
  --config task4_advanced_histograms.py \
  --files_config task7_files_config.py \
  --local
```

Use `--local_parallel` instead of `--local` to run independent jobs concurrently. Limit workers with `--local_parallel_jobs N`.

## Submit to HTCondor

```bash
python3 submitter.py \
  --app histogrammer \
  --config task4_advanced_histograms.py \
  --files_config task7_files_config.py \
  --condor \
  --job_flavour workday \
  --memory 2
```

Add `--dry` to prepare without submitting and `--save_logs` when persistent Condor logs are needed.

## Command-line reference

Exactly one execution mode is required: `--local`, `--local_parallel`, or `--condor`.

| Option | Purpose |
| --- | --- |
| `--app NAME` | Executable or Python app name. Required. |
| `--config PATH` | App configuration. Required. |
| `--files_config PATH` | Input/output and sample configuration. |
| `--local` | Run jobs sequentially on the current host. |
| `--local_parallel` | Run Condor-style jobs with local workers. |
| `--local_parallel_jobs N` | Set the number of local workers. |
| `--condor` | Submit jobs to HTCondor. |
| `--job_flavour NAME` | HTCondor runtime class; default `espresso`. |
| `--memory GB` | Requested memory in GB; default 1. |
| `--max_materialize N` | Limit simultaneously materialized Condor jobs. |
| `--save_logs` | Keep Condor log files. |
| `--dry` | Prepare a Condor submission without submitting it. |
| `--resubmit_job N` | Resubmit one indexed job. |
| `--resubmit_failed` | Resubmit jobs with missing or corrupt ROOT output. |

Run `python3 submitter.py --help` in the built environment for the authoritative options in your checkout.
