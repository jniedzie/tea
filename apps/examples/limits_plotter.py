#!/usr/bin/env python3
import ROOT
import argparse
import importlib
import re
import ast
import os

parser = argparse.ArgumentParser()
parser.add_argument("--config", type=str, default="", help="Path to the config file.")
config = None
input_path = None


def load_limits():
  data = {}

  patterns = [
    re.compile(r"signal_tta_mAlp-(\d+p?\d*)GeV_ctau-(\S+)mm: \[(.*?)\]"),
    re.compile(r"mass_(\d+p?\d*)_ctau_([-\deEpP\.]+): \[(.*?)\]"),
    re.compile(r"alp_(\d+p?\d*)_(\S+): \[(.*?)\]"),
  ]

  with open(input_path, "r") as f:
    for line in f:
      for pattern in patterns:
        match = pattern.match(line.strip())
        if match:
          break

      point, separator, values_str = line.strip().partition(": ")
      point_coordinates = getattr(config, "limit_points", {})
      if point in point_coordinates:
        mass = float(point_coordinates[point])
      elif match:
        mass_str, _, _ = match.groups()
        mass = float(mass_str.replace("p", "."))
      else:
        raise ValueError(f"No x coordinate configured for limit point {point!r}")
      values = ast.literal_eval(values_str)
      values = [None if value is None else float(value) for value in values]
      data[mass] = values
  return dict(sorted(data.items()))


def draw_legend(graphs):
  legend = ROOT.TLegend(0.60, 0.60, 0.9, 0.75)
  legend.SetBorderSize(0)
  legend.SetFillStyle(0)
  legend.SetTextFont(42)
  legend.SetTextSize(0.04)

  for graph, title in graphs:
    legend.AddEntry(graph, title, "L")
  legend.DrawClone()


def draw_cms_label():
  tex = ROOT.TLatex(0.15, 0.92, getattr(config, "experiment_label", "#bf{CMS} #it{Preliminary}"))
  tex.SetNDC()
  tex.SetTextFont(42)
  tex.SetTextSize(0.045)
  tex.SetLineWidth(2)
  tex.DrawClone()


def draw_lumi_label():
  label = getattr(config, "luminosity_label", f"#scale[0.8]{{pp, {config.luminosity / 1000:.0f} fb^{{-1}} (#sqrt{{s}} = 13 TeV)}}")
  tex = ROOT.TLatex(0.60, 0.92, label)
  tex.SetNDC()
  tex.SetTextFont(42)
  tex.SetTextSize(0.045)
  tex.SetLineWidth(2)
  tex.DrawClone()


class BrazilGraph:
  def __init__(self, config, show_obs=False):

    self.obs_graph = self.__get_central_graph()
    self.exp_graph = self.__get_central_graph(expected=True)
    self.exp_graph_1sigma = self.__get_band_graph()
    self.exp_graph_2sigma = self.__get_band_graph(config.x_title, config.y_title, two_sigma=True)

    self.show_obs = show_obs

    self.x_min = config.x_min
    self.x_max = config.x_max
    self.y_min = config.y_min
    self.y_max = config.y_max

  def __get_central_graph(self, expected=False):
    graph = ROOT.TGraph()
    graph.SetLineColor(ROOT.kBlack)
    graph.SetLineWidth(2)
    graph.SetLineStyle(2 if expected else 1)
    return graph

  def __get_band_graph(self, x_title="", y_title="", two_sigma=False):
    graph = ROOT.TGraphAsymmErrors()
    graph.SetLineWidth(0)
    graph.SetFillColorAlpha(ROOT.kYellow + 1 if two_sigma else ROOT.kGreen + 1, 1.0)
    graph.GetXaxis().SetTitleSize(0.05)
    graph.GetYaxis().SetTitleSize(0.05)
    graph.GetXaxis().SetLabelSize(0.04)
    graph.GetYaxis().SetLabelSize(0.04)
    graph.GetXaxis().SetTitleOffset(1.1)
    graph.GetYaxis().SetTitleOffset(1.1)
    graph.GetXaxis().SetTitle(x_title)
    graph.GetYaxis().SetTitle(y_title)

    return graph

  def set_point(self, i, x_value, r_value, scale):
    if r_value[0] is not None:
      self.obs_graph.SetPoint(i, x_value, r_value[0] * scale)
    self.exp_graph.SetPoint(i, x_value, r_value[3] * scale)

    self.exp_graph_1sigma.SetPoint(i, x_value, r_value[3] * scale)
    self.exp_graph_1sigma.SetPointError(i, 0, 0, (r_value[3] - r_value[2]) * scale, (r_value[4] - r_value[3]) * scale)

    self.exp_graph_2sigma.SetPoint(i, x_value, r_value[3] * scale)
    self.exp_graph_2sigma.SetPointError(i, 0, 0, (r_value[3] - r_value[1]) * scale, (r_value[5] - r_value[3]) * scale)

  def draw(self):
    self.exp_graph_2sigma.Draw("A3")
    self.exp_graph_1sigma.Draw("3same")
    self.exp_graph.Draw("Lsame")
    if self.show_obs:
      self.obs_graph.Draw("Lsame")

    self.exp_graph_2sigma.GetXaxis().SetLimits(self.x_min, self.x_max)
    self.exp_graph_2sigma.SetMinimum(self.y_min)
    self.exp_graph_2sigma.SetMaximum(self.y_max)

  def draw_legend(self):
    legend = ROOT.TLegend(0.20, 0.65, 0.45, 0.9)
    legend.SetBorderSize(0)
    legend.SetFillStyle(0)
    legend.SetTextFont(42)
    legend.SetTextSize(0.04)
    if self.show_obs:
      legend.AddEntry(self.obs_graph, "Observed", "L")
    legend.AddEntry(self.exp_graph, "Expected", "L")
    legend.AddEntry(self.exp_graph_1sigma, "Expected #pm 1 #sigma", "F")
    legend.AddEntry(self.exp_graph_2sigma, "Expected #pm 2 #sigma", "F")
    legend.DrawClone()


def draw_brazil_plots():

  graph = BrazilGraph(config)
  limits = load_limits()

  for i, (mass, r_value) in enumerate(limits.items()):
    if len(r_value) != 6:
      print(f"Invalid number of values for {mass}: {r_value}")
      continue

    scales = getattr(config, "reference_cross_sections", {})
    graph.set_point(i, mass, r_value, scales.get(mass, config.reference_cross_section))

  canvas = ROOT.TCanvas("canvas", "", 800, 600)
  canvas.cd()
  canvas.SetLogx(getattr(config, "log_x", True))
  canvas.SetLogy(getattr(config, "log_y", True))
  ROOT.gPad.SetLeftMargin(0.15)
  ROOT.gPad.SetBottomMargin(0.15)

  graph.draw()

  legend_params = []

  draw_cms_label()
  draw_lumi_label()

  graph.draw_legend()
  draw_legend(legend_params)

  # Redraw the axis to make sure they are on top of the bands
  canvas.RedrawAxis()
  canvas.Update()
  input_file_name = input_path.split("/")[-1]
  output_path = getattr(config, "plots_output_path", config.results_output_path)
  os.makedirs(output_path, exist_ok=True)
  canvas.SaveAs(f"{output_path}/{input_file_name.replace('.txt', '')}.pdf")


def main():
  global config, input_path
  args = parser.parse_args()
  config = importlib.import_module(args.config.replace(".py", "").replace("/", "."))
  input_path = f"{config.results_output_path}/limits_{config.histogram.getName()}.txt"
  ROOT.gROOT.SetBatch(True)
  draw_brazil_plots()


if __name__ == "__main__":
  main()
