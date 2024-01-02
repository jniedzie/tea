---
title: Job submission
permalink: /docs/job_submission/
---

## Overview

A convenient way to run your jobs is by using a `submitter`. It is really useful when you need to run on a large number of files, using some computing grid (e.g. lxplus, NAF...), but it can also be handy if you're running locally.

`submitter` takes a few command line arguments - execute `python submitter.py --help` to see a list. Let's now go through the arguments and explain each of them.

**&ndash;&ndash;app** [required]

Simply tell the `submitter` which app to run (e.g. `histogrammer` if you want to produce histograms).

**&ndash;&ndash;config** [required]

Specify a path to a config file. It can be exactly the same config you were using to run without submitter.

**&ndash;&ndash;files_config**

Path to a files config file, which specifies input and output files. Since there are many options here, we will explain it in detail later on.

**&ndash;&ndash;local**

If this flag is included, the code will run locally.

**&ndash;&ndash;condor**

If this flag is included (and **&ndash;&ndash;local** is not) the code will run on HTCondor.

**&ndash;&ndash;job_flavour**

Specify HTCondor job flavour (used if **&ndash;&ndash;condor** included). Available options are:
- espresso (20 min) [default]
- microcentury (1h)
- longlunch (2h)
- workday (8h)
- tomorrow (1d)
- testmatch (3d)
- nextweek (1w)

**&ndash;&ndash;resubmit_job**
Imagine that you submitted 100 jobs, but job 77 crashed. You can use this flag to resubmit a job with a specific number (corresponding to a specific file from the input files list).

**&ndash;&ndash;dry**
If this flag is included (and **&ndash;&ndash;condor** was selected), all files will be prepared, but the job won't actually be submitted. This can be useful to verify that all temporary files were generated correctly, before using large amount of resources.

## Files config

When using `submitter`, most of the time you will want to run on more than one file. The instructions on where input files are located and where to store the output should be provided in a separate config file, e.g. `input_file_list.py`. You can find an example in `configs/examples/input_file_list.py`.

There are many ways you can let `submitter` know aobut input/output files. Let us go through them one-by-one.

#### Option 1

List input files and specify one output directory. Output files will have the same name as inputs, but be stored the output directory:

```python
input_file_list = (
  "tea/samples/background_dy.root",
  "tea/samples/signal_ttz.root"
  "tea/samples/data.root"
)
output_dir = "histograms"
```

#### Option 2

List input files and for each of them specify the exact output file. This can be useful if you don't want input and output files to have the same name, or you want to put different files in different directories. Remember, since configs will be properly interpreted, you could also write some Python code that will generate this list for you.

```python
input_output_file_list = (
  ("tea/samples/background_dy.root", "background_hists/background_dy.root"),
  ("tea/samples/signal_ttz.root", "signal_hists/signal_ttz.root"),
)
```

#### Option 3

The favorite option of CMS useres: you can simply specify a DAS dataset name and output path. It will run over all files in the dataset (unless `max_files` is specified and different from -1):

```python
dataset = "/TTTo2L2Nu_TuneCP5_13TeV-powheg-pythia8/RunIIAutumn18NanoAODv7-Nano02Apr2020_102X_upgrade2018_realistic_v21-v1/NANOAODSIM"
output_dir = "../samples/ttbar_hists"
max_files = 10
```

#### Option 4

This is an extension of **option 3**, allowing to run on one specific file from a DAS dataset. Useful when you know that one file was not processed properly and want to resubmit this specific job:

```python
dataset = "/TTTo2L2Nu_TuneCP5_13TeV-powheg-pythia8/RunIIAutumn18NanoAODv7-Nano02Apr2020_102X_upgrade2018_realistic_v21-v1/NANOAODSIM"
output_dir = "../samples/ttbar_hists"
file_name = "8ED6072D-6880-724A-A0E2-A57C700C78CC.root"
```

#### Option 5

Finally, we can also run on all files in a specified directory. Output files will have the same names as inputs, but placed in the output directory:

```python
input_directory = "samples"
output_dir = "samples/histograms"
```

## Example command

Once you prepared your app, config and files config, it's time to test the submission:

```bash
python submitter.py --app histogrammer --config histogrammer_config --files_config input_file_list --condor --dry
```

This will produce a few temporary files in `bin/tmp/` directory.

## Advanced submitter options

There are a few more advanced options for very specific cases:
- you can specify a job number to resubmit, which is useful if you know that, e.g. job number 77 failed. Simply add `--resubmit_job 77` to your command to only run this one
- in the files config, you can use a DAS dataset name as the input path. For this to work you need to first create a VOMS proxy, e.g.:

```bash
voms-proxy-init --rfc --voms cms -valid 100:00
```
- you also have an option to limit the number of files you run on (`max_files` variable) or specify an input file name (`file_name` variable), which may be useful for tests, or in case you know a job for a specific file failed.
