# Reusable limits

`pylibs/limits/LimitPoint.py`, `LimitPlotter.py`, and `LimitProducer.py` provide the
reusable interface. Importing them does not parse arguments, load a config, read
data, or import ROOT. ROOT is needed when drawing or making histogram datacards. TEA's normal build exposes these modules in `bin/`.
Use the Python interfaces directly; the former `limits_plotter.py` and
`limits_producer.py` CLI wrappers have been removed. `LimitConfig.load_config`
explicitly loads a config by module basename or Python file path when needed.

## Records and plotting

```python
from LimitPoint import LimitPoint
from LimitPlotter import PlotOptions, plot_limits
from PlotCanvas import save_canvas

points = [LimitPoint(
  id="M100_Q0.3", x=0.3, parameters={"mass": 100, "charge": 0.3},
  metadata={"selection": "example"}, nominal_cross_section=0.09,
  expected={0.025: 0.4, 0.16: 0.7, 0.5: 1.0, 0.84: 1.6, 0.975: 2.4},
)]
canvas = plot_limits(points, PlotOptions(
  x_title="|q| / e", y_title="95% CL upper limit on #sigma", y_unit="pb",
  quantity="cross_section", reference="nominal", log_y=True,
  annotations=("m = 100 GeV",), luminosity=59.7, collision_energy="13 TeV",
))
save_canvas(canvas, "outputs/figures/example/pdf/limits.pdf")
save_canvas(canvas, "outputs/figures/example/png/limits.png")
```

`LimitPoint` stores a unique complete `id`, finite numeric `x`, arbitrary
`parameters` and `metadata`, five labeled `expected` quantiles, optional
`observed`, optional positive `nominal_cross_section`, `quantity` (default `r`),
`status` (default `ok`), and a diagnostic `message`. No model name is interpreted.
All five quantiles must be finite, positive, and nondecreasing. Observed is
optional, finite and positive when supplied. Missing, extra, duplicate numeric
quantile labels and unordered quantiles are rejected. Equal quantiles are valid.

`quantity="cross_section"` on PlotOptions converts input r using
σ95(point) = r95(point) × σnominal(point), for **every** quantile and observed.
Records already in cross-section units can set their own `quantity` accordingly;
they are drawn without another conversion. Conversion back to r divides by the
same factor. Units must match the chosen normalization and axis unit; there is
no implicit pb/fb conversion. `constant_scale` explicitly overrides per-point
normalization when conversion is needed, retaining the former
`reference_cross_section` behavior. Otherwise missing normalization raises an
error naming that point, without looking at neighboring points.
`reference="r1"` draws r=1 in the chosen units; `reference="nominal"` uses each
point's nominal cross section (or 1 in r units). The nominal reference requires
explicit nominal metadata even if a constant conversion override is supplied.

The limit layer builds only bands, expected/observed curves, references and gap
segments. `GraphPlotter.draw_graphs` delegates presentation to the regular
plotter's `Styler`, `Legend` and `CmsLabelsManager`. Histogram and graph plots
also share `PlotCanvas.save_canvas`, including aspect-correct PDF export.
There is no separate limit font, margin, label-position or legend-clearance
implementation.

`PlotOptions` controls titles/units, `x_range`/`y_range`, `log_x`/`log_y`, numeric
`tick_labels` (x), `y_tick_labels`, observed visibility, conversion and reference.
Standalone calls can set `canvas_size`, `plot_margins`, `legend_bounds`,
`cms_label` (a CmsLabel member name or enum), `label_outside_axes`, luminosity in
fb⁻¹ and collision-energy text. Free-form `experiment_label` has been replaced
by the same `CmsLabel` enum used for regular plots.

Pass `plot_limits(points, options, plot_config=config)` to reuse a regular
presentation config directly: `canvas_size`, `plot_margins`, `show_cms_labels`,
`cms_label`, `label_outside_axes`, `lumi_label_value` in **pb⁻¹**, `beam_label`,
and a `Legend` instance in `legend`. These override standalone defaults. Graph
configs may also supply `x_tick_labels`, `y_tick_labels`, and `annotations`.
Annotations are text rows in the shared legend so clearance accounts for them.
Ratio plots are disabled for limits. The normal Styler calculates automatic
ranges and measured margins, including uncertainty envelopes and legend
clearance. Explicit ranges are respected; log ranges require positive bounds.
Returned canvases retain their graphs; `canvas._limit_segments` and
`canvas._limit_objects` remain available for validation.

Points are sorted numerically. IDs must be unique. Distinct points with the same
x are preserved by the record format and **rejected for one curve**: select a
fixed-parameter slice or call the plotter separately for each slice. This avoids
silently overwriting different lifetimes or masses. `unavailable`, `failed`, and
`no_sensitivity` points may omit limits. They generate warnings and split curves
and bands at their x coordinate. `succeeded` and `no-sensitivity` are accepted
aliases for `ok` and `no_sensitivity`. Missing observed limits split the observed
curve separately. An isolated expected point uses nested asymmetric vertical
uncertainty bars. A completely invalid collection raises `No valid limit points`.
Include explicit missing records at known scan coordinates: the renderer cannot
infer missing scan points omitted entirely from the input.

`write_points(path, points)` and `read_points(path)` round-trip JSON:

```json
{"schema_version": 1, "points": [
  {"id": "M100_Q0.3", "x": 0.3, "parameters": {"mass": 100, "charge": 0.3},
   "nominal_cross_section": 0.09,
   "expected": {"0.025": 0.4, "0.16": 0.7, "0.5": 1, "0.84": 1.6, "0.975": 2.4}}
]}
```

Analysis-specific collections (for example ECP's `expected_r`) should construct
LimitPoint records explicitly, mapping their labeled expected dictionary to
`expected`, scan coordinate to `x`, full model identity to `id` and parameters,
and each point's own normalization to `nominal_cross_section`. Do not replace
missing cross sections with a lookup result from another point.

For old text `name: [observed, q025, q16, q50, q84, q975]`, pass
`read_points(path, point_adapter)`; `point_adapter(name)` returns identity/x and
optional parameter/metadata/normalization fields. Five values are expected-only.
`configs/examples/alp_limits_config.py` explicitly implements the three old ALP
name patterns, retains lifetime, and reproduces the old log axes, titles,
luminosity and constant scale. `configs/das_exercises/task6_limits_config.py`
now supplies its explicit ALP adapter. No ALP patterns remain in reusable code.

`configs/examples/charge_limits_config.py` is a minimal, self-contained blind
charge scan at fixed mass with point-specific illustrative cross sections:

```python
import ROOT
import charge_limits_config as config
from LimitPlotter import plot_limits
from PlotCanvas import save_canvas

ROOT.gROOT.SetBatch(True)
canvas = plot_limits(config.limit_points, config.plot_options, plot_config=config)
for path in (config.limits_plot_output, config.limits_png_output):
  save_canvas(canvas, path)
```

A config can provide `limit_points` directly, or callers can load `limits_input`
using `read_points(config.limits_input, config.point_adapter)` for legacy text.
`plot_options` is preferred; `LimitConfig.plot_options(config)` translates legacy
flat presentation fields. The caller selects input files and output destinations;
`limits_plot_output` and `limits_png_output` are example config conventions.

## Producing limits

`produce_limits(config)` creates histogram cards, invokes Combine unless
`skip_combine=True`, and returns/persists **all** signal records, including
failures. `get_limits(config, return_codes=None, statuses=None)` only collects
existing logs; `save_limits(config, points)` writes labeled JSON. To collect
without opening histograms or making cards:

```python
from LimitProducer import get_limits, save_limits

points = get_limits(config)
save_limits(config, points)
```

`parse_combine_output(text, identity, blind=False)` parses labeled percentages,
so line ordering and the presence of observed output do not affect expected
quantile assignments. Duplicate, incomplete and invalid output fails the point.

The config provides:

- `signal_samples`, `background_samples`, optional `data_samples`, their union
  `samples`, a TEA `histogram`, `nuisances`, `luminosity`, `include_shapes`, and
  `datacards_output_path`, `plots_output_path`, `results_output_path`.
- `signal_points[exact_sample_name]`, or `point_for_sample(sample)`, or
  `point_adapter(sample.name)`, returning `id`, `x` and optional parameters,
  metadata and nominal normalization. Positive `sample.cross_section` is the
  fallback normalization for **that same sample only**. It must correspond to
  the signal template normalization used in the card. If templates use an
  arbitrary reference cross section, use that reference, not the theory value.
- Optional `datacard_name(sample)` returning a basename, including all parameters
  needed to avoid collisions. Ordinary default names preserve the full sample
  name. Combined-card users **must** supply this callback; the ALP example shows
  the former mass/lifetime/category naming convention explicitly.
- `combine_setup` (a shell environment setup command), or legacy `combine_path`;
  `blind=True` supplies `--run blind` and drops observed output;
  optional `combine_arguments` is a sequence of individual arguments.
  `limit_workers` optionally limits local concurrency. `limits_output` overrides
  the default `results_output_path/limits_<histogram>[_ABCDpred|real].json`.

`configs/examples/limits_config.py` provides the ttZ producer example and fixes
its signal's SampleType. Input ROOT files must contain the selected observable
and the normalization `cutFlow` when normalizing to luminosity. Missing signals
are unavailable; zero signal yield (also in the selected ABCD region) is
no-sensitivity. Invalid rates fail instead of producing zero-divisions or tiny
fabricated signal yields. Datacards use canonical `signal` regardless of the
sample's name; sample-specific nuisances are translated to that canonical name.
Background names may contain the word signal, but `signal` and `data_obs` are
reserved names.

Combine runs in one working directory per card, preventing ROOT-output filename
collisions. Existing logs are preserved as `.log.previous-N` before a new attempt;
failed commands cannot reuse an old success. Exit codes determine failure even
if a partial log contains limits. Condor mode checks held states and history exit
codes rather than interpreting disappearance as success. No scheduler or Combine
jobs are started during fixture tests.

## Compatibility changes and validation

The example CLI wrappers have been removed. Import reusable functions from
the modules above; there is no argument parser or command compatibility shim.
New producer output is labeled JSON instead of positional text. Legacy text remains readable with an explicit config
adapter. Blind input needs no observed placeholder. Duplicate x values require
an explicit slice. Combined filenames require a callback. Partial collections
are written and returned; inspect each record's status/message and apply an
analysis-specific recovery or exit policy. Fatal collection/config errors still raise.

`produce_significance(config, collect_only=False)` handles existing datacards
named by the config's data samples. It requires those cards to exist; it does not
regenerate a single-signal card from an arbitrary data sample. It checks exits
and parses finite significance values separately from limit records.

Run `python3 ci/test_general_limits.py` in a ROOT-enabled TEA environment. Fixtures
cover import safety, legacy ALP scaling, five-quantile blind inputs, charge scans,
identity collisions, missing normalization, missing points, isolated asymmetric
uncertainties, malformed quantiles, labeled Combine logs, failed exits/stale logs,
and real ROOT datacards with arbitrary signal/background names, empty and missing
signals. PDF/PNG rendering is exercised in temporary directories. Combine is
stubbed; real installation and batch integration require the user's environment.
