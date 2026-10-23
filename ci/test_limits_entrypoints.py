"""Exercise the public CLIs with real ROOT files and a local Combine stub."""

import os
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from ci.test_general_limits import REPO, LOG  # noqa: E402
from LimitConfig import output_paths, output_stem, plot_inputs, plot_paths  # noqa: E402
from LimitPoint import read_points  # noqa: E402


class LimitsEntrypointsTest(unittest.TestCase):
  def test_output_contract_and_input_selection(self):
    with tempfile.TemporaryDirectory() as temporary:
      with self.assertRaisesRegex(ValueError, "limits_output_path"):
        output_paths(SimpleNamespace())
      config = SimpleNamespace(limits_output_path=temporary, limit_points=[])
      paths = output_paths(config)
      self.assertTrue(
        all((paths.root / name).is_dir() for name in ("datacards", "limit_results", "diagnostic_plots", "limit_plots"))
      )
      self.assertEqual(output_stem(config), "limits")
      self.assertEqual(plot_paths(config), [paths.plots / "limits.pdf"])
      config.output_formats = (".pdf", "png")
      self.assertEqual([path.suffix for path in plot_paths(config)], [".pdf", ".png"])
      config.limits_input = "explicit.json"
      with self.assertRaisesRegex(ValueError, "either"):
        plot_inputs(config)
      del config.limit_points
      self.assertEqual(output_stem(config), "explicit")
      config.histogram = SimpleNamespace(getName=lambda: "observable")
      config.do_abcd, config.use_abcd_prediction = True, True
      self.assertEqual(output_stem(config), "limits_observable_ABCDpred")

  def test_module_and_file_cli_pipeline(self):
    import ROOT

    with tempfile.TemporaryDirectory() as temporary:
      directory = Path(temporary)
      source = directory / "histograms.root"
      with ROOT.TFile.Open(str(source), "RECREATE"):
        hist = ROOT.TH1D("observable", "", 2, 0, 2)
        hist.Fill(0.5, 2)
        hist.Write()
      stub = directory / "combine"
      stub.write_text("#!/bin/sh\ncat <<'RESULT'\n" + LOG + "\nRESULT\n")
      stub.chmod(0o755)
      env = dict(os.environ)
      env["PYTHONPATH"] = os.pathsep.join(
        [str(directory), *[str(REPO / "pylibs" / name) for name in ("limits", "plotting", "logger", "abcdTools")]]
      )
      config_path = directory / "fixture_config.py"
      for mode in ("module", "file"):
        destination = directory / mode
        config_path.write_text(f"""
from Sample import Sample, SampleType
from Histogram import Histogram
from HistogramNormalizer import NormalizationType
from LimitPlotter import PlotOptions
signal_samples = [Sample(name="charged", type=SampleType.signal, file_path={str(source)!r}, cross_section=1)]
background_samples = [Sample(name="signal_like_background", type=SampleType.background, file_path={str(source)!r})]
samples = signal_samples + background_samples
histogram = Histogram(name="observable", norm_type=NormalizationType.none)
signal_points = {{"charged": {{"id": "charged", "x": 1, "parameters": {{"charge": 1}}, "nominal_cross_section": 1}}}}
limits_output_path = {str(destination)!r}
include_shapes = True
nuisances = {{"model": {{"signal": 1.1}}}}
combine_setup = "export PATH=" + {str(directory)!r} + ":$PATH"
plot_options = PlotOptions()
""")
        argument = "fixture_config" if mode == "module" else str(config_path)
        for script in ("limits_producer.py", "limits_plotter.py"):
          result = subprocess.run(
            [sys.executable, str(REPO / "apps/examples" / script), "--config", argument],
            cwd=directory,
            env=env,
            capture_output=True,
            text=True,
          )
          self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
          self.assertIn(str(destination), result.stdout)
        points = read_points(destination / "limit_results/limits_observable.json")
        self.assertEqual(points[0].status, "ok")
        self.assertGreater((destination / "limit_plots/limits_observable.pdf").stat().st_size, 1000)
        self.assertFalse((destination / "limit_plots/limits_observable.png").exists())
        self.assertTrue((destination / "datacards/datacard_observable_charged.root").exists())
        with config_path.open("a") as output:
          output.write('\noutput_formats = (".pdf", "png")\n')
        result = subprocess.run(
          [sys.executable, str(REPO / "apps/examples/limits_plotter.py"), "--config", argument],
          cwd=directory,
          env=env,
          capture_output=True,
          text=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertGreater((destination / "limit_plots/limits_observable.png").stat().st_size, 1000)


if __name__ == "__main__":
  unittest.main()
