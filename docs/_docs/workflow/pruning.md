---
title: Pruning trees
permalink: /docs/pruning/
---

Pruning removes unneeded branches when a skimmer writes its output. Selection removes events; pruning removes columns.

## Choose branches

```python
branchesToKeep = (
  "Muon_*",
  "nMuon",
  "PatMuonVertex_*",
  "nPatMuonVertex",
)

branchesToRemove = (
  "Muon_fsrPhotonIdx",
)
```

The writer first disables all branches, enables matches from `branchesToKeep`, then disables matches from `branchesToRemove`. ROOT wildcards such as `*` are supported.

## Preserve collection sizes

When keeping a vector branch, also keep the scalar branch that gives the collection size. NanoAOD normally follows the `Collection_variable` and `nCollection` convention. Some branches require `specialBranchSizes`; inspect the input tree before assuming a non-standard mapping.

## Verify the output

After skimming, compare the input and output trees:

```bash
rootls -t input.root
rootls -t output.root
```

Confirm both the intended branch list and that the output tree can be read before deleting the input.
