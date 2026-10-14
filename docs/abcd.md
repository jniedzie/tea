# Generic ABCD optimization and plots

Run `python -u abcd_plotter.py --config my_abcd_config` from the analysis `bin/`
after building and sourcing `tea/setup.sh`. Config names are bare module basenames.
The driver requires no ttalps modules. Plots are PDF only.

## Configured inputs

Use ordinary `Sample` objects for backgrounds, data and signals. A signal model
has an arbitrary stable ID, a display label, optional physics parameters and
one or more contributing samples. Contributions from different years are
normalized separately and merged within their model, never across alternative models.

```python
from Sample import Sample, SampleType

luminosity = 100000.  # pb⁻¹
background_samples = [
    Sample(name="background", file_path="background.root",
           type=SampleType.background, cross_section=1.),
]
signal_models = {
    "model_one": {
        "label": "m=100 GeV, q=1/3",
        "parameters": {"mass": 100., "charge": 1/3},
        "samples": [Sample(name="signal", file_path="signal.root",
                           type=SampleType.signal, cross_section=.1)],
    },
}
optimization_signals = list(signal_models)
variable_1 = "timing"  # y
variable_2 = "ionization"  # x
background_collection = signal_collection = "ABCD"
category = "_SR"
region = "SR"
rebin_2D = 5
optimization_param = "significance"
output_path = "plots/abcd"
output_formats = ("pdf",)
nice_names = {"timing": "Timing", "ionization": "Ionization"}
```

ROOT names default to `<collection>_<variable_1>_vs_<variable_2><category>`.
`background_hist_name` and `signal_hist_name` override them. `do_data=True`
uses `data_samples` for the background plane; data are not scaled. Analysis
blinding rules remain the responsibility of the analysis.

MC scaling is L × σ / W, where L is luminosity in pb⁻¹, σ is the cross section
in pb and W is the initial generator-weight sum. Positive `Sample.luminosity`
overrides config `luminosity`; positive `Sample.initial_weight_sum` overrides
`cutFlow` bin one. MC still requires `cutFlow`. Inputs, stored squared weights,
positive finite normalization and compatible axes are checked explicitly.
Rebinning must exactly merge base bins and retain an interior boundary.

For analyses that already load and normalize inputs, use
`ABCDPlotter.from_histograms(config, planes, models, selected, result, maps,
normalization)`. `planes` maps analysis regions to `background` and model-ID
histograms. `models` supplies labels and parameters; `result` and `maps` come
from `ABCDSearch.search`. This entry point never normalizes or rebins inputs.
ECP uses this interface with its storage and provenance adapters.

## Common cuts

`optimization_signals` defaults to all configured models. Every selected model
must pass at a common boundary; diagnostic-only models do not constrain selection.
The objective is Σᵢ Sᵢ / √(Sᵢ + B), where i labels selected models, Sᵢ is its
signal-region yield and B is the background yield in that region. It is a
ranking score, not a combined discovery significance for alternative models.

Search all four original-plane quadrants in A/B/C/D order. For physical cut
boundaries, the low side uses `<` and the high side uses `>=`; bin indices
identify the first high-side bin. Flow bins are excluded. Prediction,
significance, leakage, validation and projections share this boundary convention.
Stored squared-weight errors determine discrepancies and prediction errors;
signed bins are preserved. Empty required models produce `unavailable`, no
valid boundary produces `rejected`, and malformed inputs fail the command.

Defaults: `max_closure=.2`, `max_error=2`, `min_n_events=20`,
`max_signal_contamination=.2`, `min_signals=1`; correlation and overlap vetoes
are disabled. CLI arguments override config values. Closure means relative
background nonclosure; error means discrepancy in combined uncertainty units;
minimum events applies to every background region; contamination is each
model's fraction of its total in-range yield in each control region.
`min_signals` never relaxes the all-selected-model requirement. Optional
`overlap_metric` selects `cosine` (default) or `intersection`; signed planes
have undefined probability overlap and fail an enabled overlap constraint.

Fixed-point mode sets `optimization_param=None`,
`abcd_point={"x": physical_x_edge, "y": physical_y_edge}`, and `signal_bin`
to the original quadrant. The same constraints apply without optimization.

## Diagnostics and migration

Outputs include original-orientation background/model grids, common and
per-model significance/leakage maps, background prediction versus simulation
projections, signal overlays and ratio panels, and model score summaries.
`result.json` records the model set, all individual scores, summed score,
physical boundaries, directions, normalization and region evaluations.
`metric_maps.npz` stores undefined cells as NaN; PDFs label their display convention.

`nice_names`, `canvas_size` (scalar or width/height tuple), and `z_params`
(metric title, minimum, maximum, logarithmic flag) control drawing.
Signals retain physical yields; an optional `signal_display_scale` is explicitly
labelled. `standard_rebin=1` is the projection default. Exact custom projection
edges use `custom_rebin=True` and `custom_projections_binning`; alternatively
`smart_rebin=True` with `smart_rebin_max_error` chooses bins from stored errors.
Custom edges must span the selected signal side. True/predicted projections
and signals share bins. Prediction covariance records the shared control
normalization uncertainty, and ratio errors use independent weighted errors.

Old ttalps configs require explicit input migration: replace `masses`, `ctaus`,
`signal_path_pattern`, `signal_cross_section` and framework physics lookups with
`signal_models` and ordinary samples. Keep analysis lookups inside the config.
Replace fixed bin-index points with physical edges. Drawing settings such as
labels and metric ranges remain supported. The old `common_signals_optimization`
subset behavior is replaced by the strict selected-model common search.

Candidate entries may share an event. Stored bin errors omit that event
covariance, so simulations and cut rankings remain exploratory.
