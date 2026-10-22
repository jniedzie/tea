"""Explicit adapter reproducing the former ALP plot's coordinates, scale and presentation."""

import re
from LimitPlotter import PlotOptions

results_output_path = "../limits/results"
limits_input = f"{results_output_path}/limits_Muon_pt.txt"
output_path = "../plots/alp-limits-example"
output_formats = ["pdf"]
reference_cross_section = 1e-4
category = ""  # Set the original category suffix for combined cards.


def point_adapter(name: str) -> dict:
  patterns = (
    r"signal_tta_mAlp-(\d+p?\d*)GeV_ctau-(\S+)mm",
    r"mass_(\d+p?\d*)_ctau_([-\deEpP.]+)",
    r"alp_(\d+p?\d*)_(\S+)",
  )
  for pattern in patterns:
    match = re.fullmatch(pattern, name)
    if match:
      mass, ctau = (float(value.replace("p", ".").replace("P", ".")) for value in match.groups())
      return {
        "id": name,
        "x": mass,
        "parameters": {"mass": mass, "ctau": ctau},
        "nominal_cross_section": reference_cross_section,
      }
  raise ValueError(f"Unrecognized ALP point: {name}")


# Select one lifetime before plotting when several points share a mass.
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
  constant_scale=reference_cross_section,
  reference="nominal",
  show_observed=False,
)


def datacard_name(sample) -> str:
  # Opt-in adapter for old combined ALP card filenames; never fall back to mass=ctau=0.
  match = re.search(r"mAlp-([0-9p.]+)GeV_ctau-([0-9eE.+-]+)mm", sample.name)
  if not match:
    raise ValueError(f"Unrecognized combined ALP card name: {sample.name}")
  return f"combined_datacard_{match[1]}_{match[2]}{category}"
