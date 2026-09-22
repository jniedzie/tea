import sys
from pathlib import Path
from types import SimpleNamespace

import ROOT


def main() -> None:
  module_dir = Path(sys.argv[1])
  input_path = Path(sys.argv[2])
  output_dir = Path(sys.argv[3])
  sys.path.insert(0, str(module_dir))

  from Histogram import Histogram2D, Profile2D
  from HistogramNormalizer import NormalizationType
  from HistogramPlotter import HistogramPlotter
  from Sample import Sample, SampleType
  from Styler import Styler

  ROOT.gROOT.SetBatch(True)
  sample = Sample(name="test", file_path=str(input_path), type=SampleType.data, cross_section=1.0)
  profile = Profile2D(
    name="profiles/response",
    title="Response",
    x_rebin=2,
    y_rebin=2,
    x_label="x",
    y_label="y",
    z_label="Mean response",
    z_min=-5.0,
    z_max=0.0,
  )
  histogram = Histogram2D(
    name="counts",
    norm_type=NormalizationType.none,
    x_label="x",
    y_label="y",
    z_label="Events / bin",
    z_min=-2.0,
    z_max=0.0,
    comparable_axes=True,
  )
  root_histogram = ROOT.TH2D("counts", "", 2, 0.0, 2.0, 2, 0.0, 2.0)
  root_histogram.Fill(0.5, 0.5)
  histogram.set_hist(root_histogram)
  comparable_profile = Profile2D(
    name="comparable_profile",
    x_label="x",
    y_label="y",
    z_label="Mean response",
    comparable_axes=True,
  )
  root_comparable_profile = ROOT.TProfile2D("comparable_profile", "", 2, 0.0, 2.0, 2, 0.0, 2.0)
  root_comparable_profile.Fill(0.5, 0.5, 4.0)
  comparable_profile.set_hist(root_comparable_profile)
  config = SimpleNamespace(
    samples=(sample,),
    histograms=(),
    histograms2D=(histogram,),
    profiles2D=(profile,),
    output_path=str(output_dir),
    output_formats=("png",),
    canvas_size=(400, 300),
    plot_margins={"left": 0.17, "right": 0.05, "top": 0.08, "bottom": 0.19},
    show_ratio_plots=False,
    show_grid_2D=True,
    show_y_equals_x_2D=True,
  )

  plotter = HistogramPlotter(config)
  margin_canvas = ROOT.TCanvas("margin_canvas", "", 400, 300)
  plotter.styler.setup_2d_pad(margin_canvas)
  expected_margin = max(Styler.minimum2DRightMargin, Styler.minimum2DRightMarginPixels / float(margin_canvas.GetWw()))
  expected_margins = {"left": 0.17, "right": expected_margin, "top": 0.08, "bottom": 0.19}
  actual_margins = {
    "left": margin_canvas.GetLeftMargin(),
    "right": margin_canvas.GetRightMargin(),
    "top": margin_canvas.GetTopMargin(),
    "bottom": margin_canvas.GetBottomMargin(),
  }
  for name, expected in expected_margins.items():
    if abs(actual_margins[name] - expected) > 1e-6:
      raise AssertionError(f"The configured 2D {name} margin was not applied")
  if abs(margin_canvas.GetRightMargin() - expected_margin) > 1e-6:
    raise AssertionError("The minimum 2D right margin was not applied")

  wider_styler = Styler(SimpleNamespace(plot_margins={"right": 0.45}))
  wider_canvas = ROOT.TCanvas("wider_canvas", "", 400, 300)
  wider_styler.setup_2d_pad(wider_canvas)
  if abs(wider_canvas.GetRightMargin() - 0.45) > 1e-6:
    raise AssertionError("A larger configured 2D right margin was not preserved")

  square_margins = {"left": 0.2, "right": 0.4, "top": 0.1, "bottom": 0.2}
  square_styler = Styler(SimpleNamespace(plot_margins=square_margins))
  square_canvas = ROOT.TCanvas("square_canvas", "", 400, 300)
  square_styler.setup_2d_pad(square_canvas, square_frame=True)
  for name, minimum in square_margins.items():
    actual = getattr(square_canvas, f"Get{name.title()}Margin")()
    if actual + 1e-6 < minimum:
      raise AssertionError(f"Square-frame layout reduced the configured {name} margin")
  if abs(square_canvas.GetLeftMargin() - square_margins["left"]) > 1e-6:
    raise AssertionError("Square-frame layout changed the configured left margin")
  if abs(square_canvas.GetBottomMargin() - square_margins["bottom"]) > 1e-6:
    raise AssertionError("Square-frame layout changed the configured bottom margin")
  square_width = square_canvas.GetWw() * (1.0 - square_canvas.GetLeftMargin() - square_canvas.GetRightMargin())
  square_height = square_canvas.GetWh() * (1.0 - square_canvas.GetTopMargin() - square_canvas.GetBottomMargin())
  if abs(square_width - square_height) > 1.0:
    raise AssertionError("The configured square-frame margins did not produce a square frame")

  invalid_margin_styler = Styler(SimpleNamespace(plot_margins={"top": 0.6, "bottom": 0.4}))
  invalid_margin_canvas = ROOT.TCanvas("invalid_margin_canvas", "", 400, 300)
  try:
    invalid_margin_styler.setup_2d_pad(invalid_margin_canvas)
  except ValueError as exception:
    if "no drawable frame" not in str(exception):
      raise
  else:
    raise AssertionError("Invalid effective 2D margins were accepted")

  input_file = ROOT.TFile.Open(str(input_path), "READ")
  if not input_file or input_file.IsZombie():
    raise RuntimeError(f"Could not open profile test file: {input_path}")

  plotter.addProfilesample2D(profile, sample, input_file)
  plotter.profilesamples2D.append((comparable_profile, sample))
  plotter.histosamples2D.append((histogram, sample))
  if len(plotter.profilesamples2D) != 2:
    raise AssertionError("The configured TProfile2D was not loaded")

  loaded_profile = plotter.profilesamples2D[0][0]
  source_bin = loaded_profile.hist.FindBin(0.5, 0.5)
  if abs(loaded_profile.hist.GetBinContent(source_bin) - 8.0) > 1e-12:
    raise AssertionError("The profile mean changed while loading")

  captured_canvases = {}
  save_canvas = plotter._HistogramPlotter__save_canvas

  def capture_canvas(canvas, path: str) -> None:
    canvas.Update()
    lines = [item for item in canvas.GetListOfPrimitives() if item.InheritsFrom("TLine")]
    captured_canvases[Path(path).stem] = {
      "frame_width": canvas.GetWw() * (1.0 - canvas.GetLeftMargin() - canvas.GetRightMargin()),
      "frame_height": canvas.GetWh() * (1.0 - canvas.GetTopMargin() - canvas.GetBottomMargin()),
      "grid_x": canvas.GetGridx(),
      "grid_y": canvas.GetGridy(),
      "lines": [
        (line.GetX1(), line.GetY1(), line.GetX2(), line.GetY2(), line.GetLineColor(), line.GetLineStyle())
        for line in lines
      ],
    }
    save_canvas(canvas, path)

  plotter._HistogramPlotter__save_canvas = capture_canvas
  plotter.drawHists2D()
  plotter.drawProfiles2D()
  if (
    abs(histogram.hist.GetMinimum() - histogram.z_min) > 1e-12
    or abs(histogram.hist.GetMaximum() - histogram.z_max) > 1e-12
  ):
    raise AssertionError("Negative or zero TH2D color limits were not applied")
  if (
    abs(loaded_profile.hist.GetMinimum() - profile.z_min) > 1e-12
    or abs(loaded_profile.hist.GetMaximum() - profile.z_max) > 1e-12
  ):
    raise AssertionError("Negative or zero TProfile2D color limits were not applied")
  if histogram.hist.GetZaxis().GetTitle() != "Events / bin":
    raise AssertionError("The TH2D colorbar title was not set")
  if abs(histogram.hist.GetZaxis().GetTitleOffset() - Styler.colorbarTitleOffset) > 1e-6:
    raise AssertionError("The TH2D colorbar title offset was not applied")
  if histogram.hist.GetZaxis().GetLabelSize() <= 0:
    raise AssertionError("The TH2D colorbar labels were not styled")
  if loaded_profile.hist.GetZaxis().GetTitle() != "Mean response":
    raise AssertionError("The TProfile2D colorbar title was not set")
  if abs(loaded_profile.hist.GetZaxis().GetTitleOffset() - Styler.colorbarTitleOffset) > 1e-6:
    raise AssertionError("The TProfile2D colorbar title offset was not applied")
  if loaded_profile.hist.GetZaxis().GetLabelSize() <= 0:
    raise AssertionError("The TProfile2D colorbar labels were not styled")
  rebinned_bin = loaded_profile.hist.FindBin(0.5, 0.5)
  if abs(loaded_profile.hist.GetBinContent(rebinned_bin) - 8.0) > 1e-12:
    raise AssertionError("The profile mean changed while plotting")

  for plot_name in ("counts_test", "comparable_profile_test"):
    canvas_state = captured_canvases[plot_name]
    if abs(canvas_state["frame_width"] - canvas_state["frame_height"]) > 1.0:
      raise AssertionError(f"The comparable plot frame is not square: {plot_name}")
    if not canvas_state["grid_x"] or not canvas_state["grid_y"]:
      raise AssertionError(f"The configured 2D grid was not drawn: {plot_name}")
    if canvas_state["lines"] != [(0.0, 0.0, 2.0, 2.0, ROOT.kBlack, ROOT.kSolid)]:
      raise AssertionError(f"The y=x line is incorrect: {plot_name}")

  if captured_canvases["profiles_response_test"]["lines"]:
    raise AssertionError("The y=x line was drawn on a non-comparable plot")
  if histogram.hist.GetXaxis().GetNdivisions() != histogram.hist.GetYaxis().GetNdivisions():
    raise AssertionError("The comparable TH2D axes do not use the same tick divisions")
  if comparable_profile.hist.GetXaxis().GetNdivisions() != comparable_profile.hist.GetYaxis().GetNdivisions():
    raise AssertionError("The comparable TProfile2D axes do not use the same tick divisions")

  no_grid_canvas = ROOT.TCanvas("no_grid_canvas", "", 400, 300)
  plotter.styler.setup_2d_pad(no_grid_canvas, square_frame=True)
  if no_grid_canvas.GetGridx() or no_grid_canvas.GetGridy():
    raise AssertionError("Comparable axes forced the grid on")

  unequal_axes = Histogram2D(name="unequal", comparable_axes=True)
  unequal_root = ROOT.TH2D("unequal", "", 2, 0.0, 2.0, 2, -1.0, 1.0)
  try:
    plotter.styler.getComparable2DAxisRange(unequal_root, unequal_axes)
  except ValueError as exception:
    if "equal x/y ranges" not in str(exception):
      raise
  else:
    raise AssertionError("Unequal comparable axes were accepted")

  unequal_log_axes = Histogram2D(name="unequal_log", log_x=True, comparable_axes=True)
  try:
    plotter.styler.getComparable2DAxisRange(root_histogram, unequal_log_axes)
  except ValueError as exception:
    if "matching x/y log settings" not in str(exception):
      raise
  else:
    raise AssertionError("Mismatched comparable log settings were accepted")

  zero_origin_log_axes = Histogram2D(name="zero_origin_log", log_x=True, log_y=True, comparable_axes=True)
  zero_origin_log_root = ROOT.TH2D("zero_origin_log", "", 2, 0.0, 2.0, 4, 0.0, 2.0)
  try:
    plotter.styler.getComparable2DAxisRange(zero_origin_log_root, zero_origin_log_axes)
  except ValueError as exception:
    if "positive x/y ranges" not in str(exception):
      raise
  else:
    raise AssertionError("Comparable log axes starting at zero were accepted")

  positive_log_axes = Histogram2D(name="positive_log", log_x=True, log_y=True, comparable_axes=True)
  positive_log_root = ROOT.TH2D("positive_log", "", 2, 1.0, 100.0, 4, 1.0, 100.0)
  if plotter.styler.getComparable2DAxisRange(positive_log_root, positive_log_axes) != (1.0, 100.0):
    raise AssertionError("Valid positive comparable log axes were rejected")

  output_paths = (
    output_dir / "counts_test.png",
    output_dir / "profiles_response_test.png",
    output_dir / "comparable_profile_test.png",
  )
  for output_path in output_paths:
    if not output_path.is_file() or output_path.stat().st_size == 0:
      raise AssertionError(f"2D plot was not created: {output_path}")

  input_file.Close()


if __name__ == "__main__":
  main()
