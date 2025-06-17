---
title: Pruning
permalink: /docs/pruning/
---

In case you want to read a tree, (optionally) perform some operations, and then save only some of the input branches - you should use the mechanism called tree pruning. In `tea` this is trivial - all you need to do is add two tuples/lists to your config file:

```python
# First, branches to keep will be marked to be kept (empty tuple would result in no branches being kept)
branchesToKeep = (
    "*",
    # "Muon_*",
)

# then, on top of that, branches to remove will be marked to be removed (can be an empty tuple)
branchesToRemove = (
    "L1*",
    "HLT*",
    "Flag*",
)
```

The order in which branches to be stored are defined is the following:
- By default, all branches are switched off.
- Then, all branches in `branchesToKeep` are turned on.
- Finally, branches listed in `branchesToRemove` are turned off again.

In the example above, the wildcard character `"*"` turns all branches on, and then all branches statging with `"L1"`, `"HLT"` or `"Flag"` are turned off.

This logic allows you to specify only a few branches you want to keep (then you would leave `branchesToRemove` empty), or just a few you want to remove (then you put `"*"` in `branchesToKeep`, and list a few branches in `branchesToRemove`).
