---
title: Libs
permalink: /docs/libs/
---

Directories like `core` and `histogramming` contain C++ classes which you can use to implement your analysis. The `extensions` directory contains some general-purpose tools, but is also the place where you can add your own classes. In order to do that, use the `create.py` script:

```
python craete.py --type HistogramFiller --name tthHistogramFiller
```

or

```
python craete.py --type PhysicsObject --name TopQuark
```

or

```
python craete.py --type Event --name tthEvent
```

Depending on what kind of functionality you need, you may choose to create a HistogramFiller, a PhysicsObject, or an Event.

[add more explanation here]