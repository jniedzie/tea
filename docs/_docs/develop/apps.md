---
title: Apps
permalink: /docs/apps/
---

The `apps` directory contains apps, which use the library to perform certain tasks, such as skimming the data or creating histograms. Whenever you want to implement a new app, you will simply call the `create.py` script first to create a skeleton for your new app:

```
python craete.py --type app --name ttH_loose_skimming --path ttH_analysis
```

This will automatically create required directories, a C++ file, and a Python config. You also don't need to worry about CMake, linking or any of these things - it will work automagically.
Once you create your app, you can open your C++ file from `apps/ttH_analysis/ttH_loose_skimming.cpp` and the config from `configs/ttH_analysis/ttH_loose_skimming.py`.

In the `apps/examples` directory you will find some ideas for how to fill in your C++ file. You can use a number of tools such as event reader/writer, config manager, histogram handler or profiler to achieve your task. In most cases, your `main` function will contain a loop over events, in which
you will apply selections, fill histograms, or add events to the output file.