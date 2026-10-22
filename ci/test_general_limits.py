#!/usr/bin/env python3
"""Small schema, ROOT rendering and end-to-end producer fixtures; no external Combine jobs."""

from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import warnings

REPO = Path(__file__).resolve().parents[1]
for directory in ("limits", "plotting", "logger", "abcdTools"):
  sys.path.insert(0, str(REPO / "pylibs" / directory))
from LimitPoint import LimitPoint, QUANTILES, read_points, write_points, scale_point  # noqa: E402
from LimitPlotter import PlotOptions, prepare_segments, plot_limits  # noqa: E402
from LimitProducer import (  # noqa: E402
  get_datacard_file_name,
  parse_combine_output,
  get_limits,
  produce_limits,
  run_combine,
  save_limits,
  produce_significance,
)
from LimitConfig import load_config  # noqa: E402

EXPECTED = dict(zip(QUANTILES, (1, 2, 3, 5, 8)))
LOG = "\n".join(f"Expected {100 * q:5.1f}%: r < {v}" for q, v in EXPECTED.items())


class GeneralLimitsTest(unittest.TestCase):
  def setUp(self):
    self.temp = tempfile.TemporaryDirectory()
    self.addCleanup(self.temp.cleanup)
    self.path = Path(self.temp.name)

  def point(self, x=1, **kwargs):
    return LimitPoint(id=str(x), x=x, expected=EXPECTED, **kwargs)

  def test_imports_have_no_root_config_parser_or_file_side_effects(self):
    script = f"""
import builtins, sys
sys.path.insert(0, {str(REPO / "pylibs/limits")!r})
sys.argv = ['irrelevant', '--unrecognized']
import LimitPoint, LimitConfig, LimitPlotter, LimitProducer
assert 'ROOT' not in sys.modules
assert 'Sample' not in sys.modules
"""
    subprocess.run([sys.executable, "-c", script], check=True)

  def test_alp_legacy_and_expected_only(self):
    config = load_config(str(REPO / "configs/examples/alp_limits_config.py"))
    path = self.path / "alp.txt"
    path.write_text("alp_12_1e2: ['9', '1', '2', '3', '5', '8']\nsignal_tta_mAlp-2p5GeV_ctau-1e2mm: [1, 2, 3, 5, 8]\n")
    points = read_points(path, config.point_adapter)
    self.assertEqual(points[0].parameters, {"mass": 12, "ctau": 100})
    self.assertIsNone(points[1].observed)
    self.assertEqual(config.plot_options.reference, "nominal")
    self.assertEqual(points[0].nominal_cross_section, config.reference_cross_section)
    scaled = prepare_segments(points, config.plot_options)[0]
    self.assertEqual([p.x for p in scaled], [2.5, 12])
    self.assertAlmostEqual(scaled[0].expected[0.84], 5e-4)
    self.assertAlmostEqual(scaled[1].observed, 9e-4)
    write_points(self.path / "points.json", points)
    self.assertEqual(read_points(self.path / "points.json"), points)
    with self.assertRaises(ValueError):
      read_points(path)

  def test_complete_identity_charge_scaling_and_missing_metadata(self):
    points = [self.point(x, parameters={"mass": 100, "charge": x}, nominal_cross_section=x * x) for x in (1, 0.3, 0.6)]
    segment = prepare_segments(points, PlotOptions(quantity="cross_section"))[0]
    self.assertEqual([p.parameters["charge"] for p in segment], [0.3, 0.6, 1])
    for point in segment:
      for q in QUANTILES:
        self.assertAlmostEqual(point.expected[q], EXPECTED[q] * point.x**2)
    with self.assertRaisesRegex(ValueError, "nominal_cross_section"):
      prepare_segments([points[0], self.point(2)], PlotOptions(quantity="cross_section"))
    input_sigma = LimitPoint(
      id="direct_sigma", x=1, expected=EXPECTED, quantity="cross_section", nominal_cross_section=2
    )
    self.assertEqual(scale_point(input_sigma, "cross_section"), input_sigma)
    self.assertEqual(scale_point(input_sigma, "r").expected[0.5], 1.5)
    with self.assertRaisesRegex(ValueError, "share x"):
      prepare_segments([points[0], LimitPoint(id="other_charge", x=1, expected=EXPECTED)], PlotOptions())

  def test_missing_and_malformed_points(self):
    points = [self.point(3), LimitPoint(id="missing", x=2, status="no-sensitivity"), self.point()]
    with self.assertWarnsRegex(RuntimeWarning, "no_sensitivity"):
      segments = prepare_segments(points, PlotOptions())
    self.assertEqual([[p.x for p in group] for group in segments], [[1], [3]])
    for expected in (
      {0.5: 1},
      {**EXPECTED, 0.16: float("nan")},
      {**EXPECTED, 0.16: 7},
      {**EXPECTED, 0.5: float("inf")},
      {**EXPECTED, 0.025: -1},
    ):
      with self.subTest(expected=expected), self.assertRaises(ValueError):
        LimitPoint(id="bad", x=1, expected=expected)
    self.assertEqual(self.point(status="succeeded").status, "ok")

  def test_labeled_combine_parser_and_failed_collection(self):
    identity = {"id": "M100_Q0.3", "x": 0.3, "parameters": {"mass": 100, "charge": 0.3}}
    point = parse_combine_output(LOG, identity)
    self.assertEqual(point.expected, EXPECTED)
    self.assertIsNone(point.observed)
    self.assertEqual(parse_combine_output(LOG + "\nObserved Limit: r < 10", identity).observed, 10)
    self.assertIsNone(parse_combine_output(LOG + "\nObserved Limit: r < 10", identity, blind=True).observed)
    for text in ("\n".join(LOG.splitlines()[1:]), LOG + "\nExpected 50.0%: r < 3"):
      with self.assertRaises(ValueError):
        parse_combine_output(text, identity)
    sample = SimpleNamespace(name="arbitrary", cross_section=-1)
    config = SimpleNamespace(
      signal_samples=[sample],
      signal_points={sample.name: identity},
      datacard_name=lambda sample: "explicit-card",
      datacards_output_path=self.path,
    )
    with self.assertWarns(RuntimeWarning):
      self.assertEqual(get_limits(config)[0].status, "unavailable")
    (self.path / "explicit-card.log").write_text(LOG)
    with self.assertWarns(RuntimeWarning):
      self.assertEqual(get_limits(config, {"explicit-card": 7})[0].status, "failed")
    config.limits_output = self.path / "explicit.json"
    save_limits(config, [point])
    self.assertTrue(config.limits_output.exists())
    with self.assertRaises(ValueError):
      get_datacard_file_name(SimpleNamespace(use_combined_limits=True), sample)

  def test_actual_root_rendering(self):
    import ROOT

    ROOT.gROOT.SetBatch(True)
    config = load_config(str(REPO / "configs/examples/charge_limits_config.py"))
    canvas = plot_limits(config.limit_points, config.plot_options, plot_config=config)
    self.addCleanup(canvas.Close)
    legend = next(obj for obj in canvas._limit_objects if isinstance(obj, ROOT.TLegend))
    self.assertEqual(
      [entry.GetLabel() for entry in legend.GetListOfPrimitives()],
      ["Theory", "", "95% CL upper limits", "Median expected", "68% expected", "95% expected"],
    )
    from PlotCanvas import save_canvas

    for suffix in ("pdf", "png"):
      output = self.path / ("charge." + suffix)
      save_canvas(canvas, output)
      self.assertGreater(output.stat().st_size, 1000)
    points = [self.point(observed=4), LimitPoint(id="failed", x=2, status="failed")]
    with self.assertWarns(RuntimeWarning):
      isolated = plot_limits(points, PlotOptions(reference="r1", show_observed=True))
    self.addCleanup(isolated.Close)
    bands = [obj for obj in isolated._limit_objects if isinstance(obj, ROOT.TGraphAsymmErrors)]
    self.assertEqual(len(bands), 2)
    self.assertEqual(bands[0].GetErrorYlow(0), 2)
    self.assertEqual(bands[0].GetErrorYhigh(0), 5)
    self.assertEqual(bands[1].GetErrorYlow(0), 1)
    self.assertEqual(bands[1].GetErrorYhigh(0), 2)
    self.assertEqual(bands[0].GetN(), 1)
    legend = next(obj for obj in isolated._limit_objects if isinstance(obj, ROOT.TLegend))
    entries = list(legend.GetListOfPrimitives())
    self.assertEqual(
      [entry.GetLabel() for entry in entries],
      ["r = 1", "", "95% CL upper limits", "Observed", "Median expected", "68% expected", "95% expected"],
    )
    self.assertEqual(entries[3].GetOption().lower(), "lp")
    isolated.SaveAs(str(self.path / "single.pdf"))

  def test_regular_plot_presentation_settings(self):
    import ROOT
    from CmsLabelsManager import CmsLabel
    from Legend import Legend

    ROOT.gROOT.SetBatch(True)
    config = SimpleNamespace(
      canvas_size=(900, 700),
      plot_margins={"left": 0.16, "bottom": 0.18, "top": 0.10, "right": 0.04},
      cms_label=CmsLabel.thesis,
      lumi_label_value=41900,
      beam_label="13.6 TeV",
      legend=Legend(0.60, 0.65, 0.94, 0.88, text_size=20),
    )
    canvas = plot_limits([self.point()], PlotOptions(x_range=(0.5, 1.5), y_range=(-1, 12)), plot_config=config)
    self.addCleanup(canvas.Close)
    pad = canvas.GetPad(1)
    self.assertAlmostEqual(pad.GetLeftMargin(), 0.16)
    self.assertAlmostEqual(pad.GetBottomMargin(), 0.18)
    plot = next(obj for obj in canvas._limit_objects if isinstance(obj, ROOT.TMultiGraph))
    self.assertEqual(plot.GetXaxis().GetTitleFont(), 43)
    self.assertEqual(plot.GetYaxis().GetLabelSize(), 26)
    self.assertEqual(plot.GetXaxis().GetXmin(), 0.5)
    self.assertEqual(plot.GetXaxis().GetXmax(), 1.5)
    self.assertEqual(plot.GetHistogram().GetMinimum(), -1)
    self.assertEqual(plot.GetHistogram().GetMaximum(), 12)
    legend = next(obj for obj in canvas._limit_objects if isinstance(obj, ROOT.TLegend))
    self.assertEqual(legend.GetTextFont(), 43)
    self.assertEqual(legend.GetTextSize(), 20)
    labels = [obj.GetTitle() for obj in pad.GetListOfPrimitives() if isinstance(obj, ROOT.TLatex)]
    self.assertIn("CMS", labels)
    self.assertIn("Work in progress", labels)
    self.assertIn("41.9 fb^{-1} (13.6 TeV)", labels)

  def test_producer_with_arbitrary_signal_names_and_real_datacards(self):
    import ROOT
    from Sample import Sample, SampleType
    from Histogram import Histogram
    from HistogramNormalizer import NormalizationType

    ROOT.gROOT.SetBatch(True)
    samples = []
    for name, kind, weight in (
      ("charged_A", SampleType.signal, 2),
      ("charged_B", SampleType.signal, 0),
      ("not_a_signal_background", SampleType.background, 10),
    ):
      path = self.path / (name + ".root")
      with ROOT.TFile.Open(str(path), "RECREATE"):
        hist = ROOT.TH1D("observable", "", 2, 0, 2)
        if weight:
          hist.Fill(0.5, weight)
        hist.Write()
        cutflow = ROOT.TH1D("cutFlow", "", 2, 0, 2)
        cutflow.SetBinContent(1, 10)
        cutflow.SetBinContent(2, weight)
        cutflow.Write()
      samples.append(Sample(name=name, file_path=str(path), type=kind, cross_section=1))
    missing = Sample(name="charged_C", file_path=str(self.path / "missing.root"), type=SampleType.signal)
    config = SimpleNamespace(
      signal_samples=samples[:2] + [missing],
      background_samples=samples[2:],
      samples=samples + [missing],
      histogram=Histogram(name="observable", norm_type=NormalizationType.to_lumi),
      signal_points={
        sample.name: {"id": sample.name, "x": i, "parameters": {"mass": 100, "charge": i}}
        for i, sample in enumerate(samples[:2] + [missing], 1)
      },
      datacards_output_path=self.path / "cards",
      plots_output_path=self.path / "plots",
      results_output_path=self.path / "results",
      include_shapes=True,
      luminosity=10,
      skip_combine=False,
      blind=True,
      nuisances={"model": {"charged_A": 1.1}},
    )

    def fake_combine(config, names, *args):
      for name in names:
        (config.datacards_output_path / (name + ".log")).write_text(LOG)
      return {name: 0 for name in names}

    with patch("LimitProducer.run_combine", side_effect=fake_combine), warnings.catch_warnings():
      warnings.simplefilter("ignore", RuntimeWarning)
      points = produce_limits(config)
    self.assertEqual([point.status for point in points], ["ok", "no_sensitivity", "unavailable"])
    card = config.datacards_output_path / "datacard_observable_charged_A.txt"
    text = card.read_text()
    self.assertIn("process signal not_a_signal_background", text)
    self.assertIn("model lnN 1.1 -", text)
    self.assertIn("rate 2.0 10.0", text)
    self.assertTrue(card.with_suffix(".root").exists())
    self.assertFalse((config.datacards_output_path / "datacard_observable_charged_B.txt").exists())
    reread = read_points(config.results_output_path / "limits_observable.json")
    self.assertEqual(reread, points)

  def test_significance_collect_only_never_launches(self):
    (self.path / "card.txt").write_text("existing card")
    (self.path / "card.log").write_text("Significance: 2.75\n")
    config = SimpleNamespace(
      data_samples=[SimpleNamespace(name="observation")],
      datacard_name=lambda sample: "card",
      datacards_output_path=self.path,
      skip_combine=False,
    )
    with patch("LimitProducer.run_combine") as run:
      self.assertEqual(produce_significance(config, collect_only=True), {"observation": 2.75})
      run.assert_not_called()

  def test_command_failure_isolated_outputs_and_stale_logs(self):
    for name in ("one", "two"):
      (self.path / (name + ".txt")).write_text("fake card")
      (self.path / (name + ".log")).write_text(LOG)
    config = SimpleNamespace(datacards_output_path=self.path, combine_setup="true", blind=True)
    with patch("LimitProducer.subprocess.run", return_value=SimpleNamespace(returncode=9)) as run:
      codes = run_combine(config, ["one", "two"])
    self.assertEqual(codes, {"one": 9, "two": 9})
    self.assertTrue((self.path / "one.log.previous-1").exists())
    self.assertFalse((self.path / "one.log").exists())
    commands = [call.args[0][-1] for call in run.call_args_list]
    self.assertTrue(all("--run blind" in command for command in commands))
    self.assertTrue((self.path / "one").is_dir())
    self.assertTrue((self.path / "two").is_dir())


if __name__ == "__main__":
  unittest.main()
