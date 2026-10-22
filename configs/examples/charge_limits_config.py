"""Minimal blind charge scan at fixed mass; illustrative values, not physics results."""

from LimitPoint import LimitPoint
from LimitPlotter import PlotOptions
from CmsLabelsManager import CmsLabel
from Legend import Legend

# Identity and all coordinates survive serialization. Cross sections here are illustrative pb.
limit_points = [
  LimitPoint(
    id=f"M100_Q{charge}",
    x=charge,
    parameters={"mass": 100, "charge": charge},
    nominal_cross_section=cross_section,
    expected={
      q: value * (1.5 - charge) for q, value in {0.025: 0.4, 0.16: 0.7, 0.5: 1.0, 0.84: 1.6, 0.975: 2.4}.items()
    },
  )
  for charge, cross_section in ((1.0, 0.9), (0.333333333333, 0.1), (0.666666666667, 0.4))
]
plot_options = PlotOptions(
  x_title="|q| / e",
  y_title="95% CL upper limit on #sigma",
  y_unit="pb",
  x_range=(0.2, 1.1),
  quantity="cross_section",
  reference="nominal",
  log_y=True,
)
# The same presentation settings used by the regular example plotter.
canvas_size = (800, 600)
show_cms_labels = True
cms_label = CmsLabel.pas
label_outside_axes = True
lumi_label_value = 59700.0  # pb^-1, following regular plotting conventions.
beam_label = "13 TeV"
legend = Legend(0.16, 0.60, 0.58, 0.90)

limits_plot_output = "../outputs/figures/charge-limits-example/pdf/limits.pdf"
limits_png_output = "../outputs/figures/charge-limits-example/png/limits.png"

# For production with Sample objects, provide signal_points keyed by the exact sample name,
# or point_for_sample(sample). Keep x and normalization explicit, as for limit_points above.
signal_points = {
  point.id: {
    "id": point.id,
    "x": point.x,
    "parameters": point.parameters,
    "nominal_cross_section": point.nominal_cross_section,
  }
  for point in limit_points
}
