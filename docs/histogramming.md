# Three-dimensional histograms

`HistogramsHandler` supports TH3D histograms alongside TH1D, TH2D and TProfile2D.
Declare their binning and output directory in the Python configuration, then fill
all three coordinates manually in C++.

```python
histParams3D = (
  ("position", 20, -10, 10, 20, -10, 10, 30, -15, 15, "positions"),
)
irregularHistParams3D = (
  ("position_variable", (-10, 0, 10), [-10, 0, 10], (-15, 0, 15), "positions"),
)
SFvariationVariables = ("position", "position_variable")
```

Regular definitions contain a name followed by `(bins, min, max)` for x, y and z.
Variable-bin definitions contain a name followed by the x, y and z edge sequences.
Each accepts an optional final directory string; omitting it writes to the ROOT
file's top level. Edge sequences can be lists or tuples. Bounds and edges use
double precision.

Bin counts must be positive integers, bounds must be finite and increasing, and
each edge sequence must contain at least two finite, strictly increasing numeric
values. Invalid definitions are logged and skipped.

```cpp
histogramsHandler->SetEventWeights({{"default", eventWeight}, {"up", upWeight}});
histogramsHandler->Fill("position", x, y, z);
histogramsHandler->Fill("position_variable", x, y, z);
histogramsHandler->SaveHistograms();
```

`Fill(name, x, y, value)` selects the object by its configured name: the final
value is the z coordinate for TH3D and the measured profile value for TProfile2D.
Using the same name for both types is rejected during handler initialization.
Weights come from `SetEventWeights`; the default weight before that call is one.

Histograms selected by `SFvariationVariables` receive one variation for each
non-default weight present at the first `SetEventWeights` call. Variations start
empty, including when nominal fills preceded that call. Later calls update the
weights without creating additional variations. Saved variation names follow
`name_variation`, in the nominal histogram's configured directory.

Retrieve an individual object with `GetHistogram3D({name, variation})`, where an
empty variation string selects the nominal histogram. `GetHistograms3D()` returns
a copy of the map of nominal and variation pointers, matching existing getters.
Histograms defined but never filled are reported when saving. Large histograms
with more than four million regular bins generate a warning when saved.

TH3D support does not add automatic branch filling, plotting, mixed regular and
variable axes, or an unweighted multidimensional fill API.
