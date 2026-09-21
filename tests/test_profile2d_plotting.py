import sys
from pathlib import Path
from types import SimpleNamespace

import ROOT


def main() -> None:
  source_dir = Path(sys.argv[1])
  input_path = Path(sys.argv[2])
  output_dir = Path(sys.argv[3])
  sys.path.insert(0, str(source_dir / "pylibs" / "plotting"))

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
  )
  histogram = Histogram2D(
    name="counts",
    norm_type=NormalizationType.none,
    x_label="x",
    y_label="y",
    z_label="Events / bin",
  )
  root_histogram = ROOT.TH2D("counts", "", 2, 0.0, 2.0, 2, -1.0, 1.0)
  root_histogram.Fill(0.5, 0.5)
  histogram.set_hist(root_histogram)
  config = SimpleNamespace(
    samples=(sample,),
    histograms=(),
    histograms2D=(histogram,),
    profiles2D=(profile,),
    output_path=str(output_dir),
    output_formats=("png",),
    canvas_size=(400, 300),
    plot_margins={"right": 0.05},
    show_ratio_plots=False,
  )

  plotter = HistogramPlotter(config)
  margin_canvas = ROOT.TCanvas("margin_canvas", "", 400, 300)
  plotter.styler.setup_2d_pad(margin_canvas)
  expected_margin = max(Styler.minimum2DRightMargin, Styler.minimum2DRightMarginPixels / float(margin_canvas.GetWw()))
  if abs(margin_canvas.GetRightMargin() - expected_margin) > 1e-6:
    raise AssertionError("The minimum 2D right margin was not applied")

  wider_styler = Styler(SimpleNamespace(plot_margins={"right": 0.45}))
  wider_canvas = ROOT.TCanvas("wider_canvas", "", 400, 300)
  wider_styler.setup_2d_pad(wider_canvas)
  if abs(wider_canvas.GetRightMargin() - 0.45) > 1e-6:
    raise AssertionError("A larger configured 2D right margin was not preserved")

  input_file = ROOT.TFile.Open(str(input_path), "READ")
  if not input_file or input_file.IsZombie():
    raise RuntimeError(f"Could not open profile test file: {input_path}")

  plotter.addProfilesample2D(profile, sample, input_file)
  plotter.histosamples2D.append((histogram, sample))
  if len(plotter.profilesamples2D) != 1:
    raise AssertionError("The configured TProfile2D was not loaded")

  loaded_profile = plotter.profilesamples2D[0][0]
  source_bin = loaded_profile.hist.FindBin(0.5, 0.5)
  if abs(loaded_profile.hist.GetBinContent(source_bin) - 8.0) > 1e-12:
    raise AssertionError("The profile mean changed while loading")

  plotter.drawHists2D()
  plotter.drawProfiles2D()
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

  output_paths = (output_dir / "counts_test.png", output_dir / "profiles_response_test.png")
  for output_path in output_paths:
    if not output_path.is_file() or output_path.stat().st_size == 0:
      raise AssertionError(f"2D plot was not created: {output_path}")

  input_file.Close()


if __name__ == "__main__":
  main()
