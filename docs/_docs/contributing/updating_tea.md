---
title: Updating tea
permalink: /docs/updating_tea/
---

`tea` is a Git submodule of the analysis repository. Update it explicitly and review the recorded submodule commit.

## Update the submodule

From the analysis root:

```bash
git -C tea fetch origin
git -C tea switch main
git -C tea pull --ff-only
git add tea
git commit -m "Update tea"
```

If your analysis intentionally tracks another `tea` branch, switch to that branch rather than silently replacing it with `main`.

## Rebuild

```bash
source tea/build.sh
```

Run the analysis smoke test or a representative small sample before processing full data. A submodule update can change C++, Python configs, and command-line behavior together.
