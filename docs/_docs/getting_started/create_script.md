---
title: Creating apps/classes
permalink: /docs/create_script/
---

`create.py` script is located in the main `tea` directory. It allows to... create different things, such as apps, configs, and used classes.

Run `python create.py --help` to check what arguments it expects:

```bash
usage: create.py [-h] --name NAME --type TYPE [--path PATH]

options:
  --name NAME  Name of the class/app to add
  --type TYPE  Type of the extension to add: PhysicsObject, Event, HistogramFiller, app, printer, histogrammer
```

Have a look at sections below for description of different apps and classes you can create. Once you run the command, you will get names of created/modified files.

## Creating an app

There are different types of apps we can create:
- printer: prints information from the input tree
- histogrammer: creates files with histograms
- app: general-purpose app, which contains everything you need (and some stuff you don't...)

When creating an app, you should specify which of these types you want, and specify the name.

An example of a complete command could be:

```bash
python create.py --name ttZ_analysis_print_events --type printer
```

## Creating a custom class

In case you want to create a custom class, you have the following options:
- PhysicsObject: wrapper on top of PhysicsObject (such as Jet, GenParticle, Photon, etc.)
- Event: a custom event which can provide special functionality, 
- HistogramsFiller: a custom histograms filler creating histograms which are filled with something more complicated than simply values already stored in the input tree branches

For a custom class, Simply select the appropriate type and give it a name, e.g.:

```bash
python create.py --name TopQuark --type PhysicsObject
```
