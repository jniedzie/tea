import sys
from pathlib import Path
from types import SimpleNamespace

import ROOT


def main() -> None:
  source_dir = Path(sys.argv[1])
  input_path = Path(sys.argv[2])
  output_dir = Path(sys.argv[3])
  sys.path.insert(0, str(source_dir / "pylibs" / "plotting"))

  from Histogram import Profile2D
  from HistogramPlotter import HistogramPlotter
  from Sample import Sample, SampleType

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
  config = SimpleNamespace(
    samples=(sample,),
    histograms=(),
    profiles2D=(profile,),
    output_path=str(output_dir),
    output_formats=("png",),
    canvas_size=(400, 300),
    show_ratio_plots=False,
  )

  plotter = HistogramPlotter(config)
  input_file = ROOT.TFile.Open(str(input_path), "READ")
  if not input_file or input_file.IsZombie():
    raise RuntimeError(f"Could not open profile test file: {input_path}")

  plotter.addProfilesample2D(profile, sample, input_file)
  if len(plotter.profilesamples2D) != 1:
    raise AssertionError("The configured TProfile2D was not loaded")

  loaded_profile = plotter.profilesamples2D[0][0]
  source_bin = loaded_profile.hist.FindBin(0.5, 0.5)
  if abs(loaded_profile.hist.GetBinContent(source_bin) - 8.0) > 1e-12:
    raise AssertionError("The profile mean changed while loading")

  plotter.drawProfiles2D()
  rebinned_bin = loaded_profile.hist.FindBin(0.5, 0.5)
  if abs(loaded_profile.hist.GetBinContent(rebinned_bin) - 8.0) > 1e-12:
    raise AssertionError("The profile mean changed while plotting")

  output_path = output_dir / "profiles_response_test.png"
  if not output_path.is_file() or output_path.stat().st_size == 0:
    raise AssertionError(f"Profile plot was not created: {output_path}")

  input_file.Close()


if __name__ == "__main__":
  main()
