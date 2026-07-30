---
title: Process larger samples
permalink: /docs/tutorial_submission/
---

## Prerequisites and goal

You need an application and config that work on one file. The goal is to separate file bookkeeping from analysis behavior and run the same job over every tutorial process.

## Prepare the files config

```bash
cp tea/configs/das_exercises/task7_files_config.py \
  configs/tutorial/large_samples.py
```

The provided `samples` list covers data, top background, and five signal masses. Keep the base path:

```python
base_path = "/eos/cms/store/group/committee_schools/2025-cmsdas-hamburg/llp/large_samples/"
```

Update the app config to import the copied files config and derive its input and output paths. Test one sample locally before submitting the complete list.

## Test one job

```bash
source tea/build.sh
cd bin
python3 submitter.py \
  --app llp_histogrammer \
  --config llp_histogrammer.py \
  --files_config large_samples.py \
  --local
```

Use `--local_parallel` only after the sequential run succeeds.

## Submit to HTCondor

```bash
python3 submitter.py \
  --app llp_histogrammer \
  --config llp_histogrammer.py \
  --files_config large_samples.py \
  --condor \
  --job_flavour microcentury \
  --memory 2
```

Use `--dry` first if you want to inspect the generated submission. See [Submitting jobs]({{ "/docs/job_submission/" | relative_url }}) for all options.

## Merge and validate the outputs

Each process should have a distinct set of ROOT outputs. Check that all expected files exist, open successfully, and contain the same histogram keys. Then merge each process:

```bash
python3 merge.py --files_config large_samples.py
```

The example files config writes merged files such as `background_ttsemileptonic_histograms.root` below `results/tutorial/histograms_large_stat/` after you adapt its output directory.

## Plot the larger samples

Copy the matching plotting configuration:

```bash
cp ../tea/configs/das_exercises/task7_plotting.py \
  ../configs/tutorial/large_sample_plots.py
cd ..
source tea/build.sh
cd bin
python plotter.py --config large_sample_plots.py
```

Update its file and output paths if you changed the task-7 directory names. Verify the background/data comparison and ratio before drawing a physics conclusion.

## Optional statistical follow-up

The DAS sequence returns to the limit workflow after the larger-sample checks and also provides `task7_significance_config.py`. Both require a validated Combine environment, consistent merged histograms, and an analysis-approved treatment of collision data. Use the [expected-limit exercise]({{ "/docs/tutorial_limits/" | relative_url }}) as the technical starting point; do not treat the tutorial configuration as an analysis result.

## Expected output

You should have one merged ROOT file per process, large-statistics comparison plots, and—only if you completed the optional statistical step—new Combine logs and result files.

## Where to go next

Return to the [analysis workflow]({{ "/docs/tree_io/" | relative_url }}) for focused reference pages, or learn how to [write a custom app]({{ "/docs/custom_app/" | relative_url }}).
