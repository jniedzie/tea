"""ALP mass slice with explicit metadata and labeled JSON input."""

from typing import TYPE_CHECKING

from LimitPlotter import PlotOptions

if TYPE_CHECKING:
  from Sample import Sample

limits_output_path = "../limits/alp-limits-example"
limits_input = "../limits/limit_results/limits_Muon_pt.json"
output_formats = ["pdf"]
category = ""  # Set the category suffix for combined cards.

# Keep the complete identity and normalization alongside the scan coordinates.
# Use these same records when producing the input JSON; select one lifetime per plot.
signal_points = {
  f"alp_{mass}_1e2": {
    "id": f"alp_{mass}_1e2",
    "x": mass,
    "parameters": {"mass": mass, "ctau": 100.0},
    "nominal_cross_section": 1e-4,
    "metadata": {"combined_card": f"combined_datacard_{mass}_1e2"},
  }
  for mass in (1, 2, 12, 30, 60)
}

plot_options = PlotOptions(
  x_title="m_{a} [GeV]",
  y_title="#sigma(pp #rightarrow t#bar{t}a) #times B(a #rightarrow #mu#mu) [pb]",
  x_range=(1, 60),
  y_range=(1e-6, 1e-1),
  legend_bounds=(0.60, 0.58, 0.94, 0.90),
  log_x=True,
  log_y=True,
  luminosity=63.67,
  collision_energy="13 TeV",
  quantity="cross_section",
  reference="nominal",
  show_observed=False,
)


def datacard_name(sample: "Sample") -> str:
  return signal_points[sample.name]["metadata"]["combined_card"] + category
