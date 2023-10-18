---
title: Custom physics objects
permalink: /docs/custom_physics_objects/
---

Custom physics objects let you add some special functionality on top of the `PhysicsObject`. Imagine you work on an analysis involving top quarks and you want an easy way to check if given top quark is boosted or not. You can create a custom physics object (see [create.py script]({{site.baseurl}}/docs/create_script/) for details), for instance:

```bash
python create.py --name TopQuark --type PhysicsObject
```

Then, in your app or HistogramsFiller, etc., you can simply convert PhysicsObject to TopQuark (no need to implement the conversion, it will be added automatically) and call your custom method:

```cpp
auto topQuark = asTopQuark(physicsObject);
bool isBoosted = topQuark->IsBoosted();
```
