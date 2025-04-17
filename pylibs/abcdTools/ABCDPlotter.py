import ROOT
import os

from ABCDHelper import ABCDHelper
from ABCDHistogramsHelper import ABCDHistogramsHelper
from Logger import fatal, warn, info


class ABCDPlotter:
  def __init__(self, config, max_error, max_closure, min_n_events, max_signal_contamination, max_overlap):
    self.config = config

    self.abcdHelper = ABCDHelper(config, max_error, max_closure, min_n_events, max_signal_contamination, max_overlap)
    self.histogramsHelper = ABCDHistogramsHelper(config)

    self.hist_name = f"{config.collection}_{config.variable_1}_vs_{config.variable_2}{config.category}"

    self.background_files = {}
    self.background_hists = {}
    self.background_hist = None
    self.data_file = None
    self.signal_files = {}
    self.signal_hists = {}
    self.canvases = None
    self.projections_pads = {}
    self.significance_hists = {}
    self.contamination_hists = {}
    self.lines = {}
    self.projections_legend = ROOT.TLegend(*config.projections_legend_position)
    self.signal_projections = {}
    self.ratio_hist = None
    self.ratio_hist_err = None

    self.variable_1_min = None
    self.variable_1_max = None
    self.variable_2_min = None
    self.variable_2_max = None

    os.makedirs(config.output_path, exist_ok=True)

    self.__setup_canvases()
    self.__load_background_histograms()
    self.__setup_backgrounds_sum_histogram()
    self.__load_signal_hists()

    self.__flip_signal_to_region_a()

    self.optimization_hists = self.abcdHelper.get_optimization_hists(self.background_hist)

    self.__setup_signal_hists()
    self.true_projection_hist = self.abcdHelper.get_projection_true(self.background_hist, self.variable_2_max)
    self.prediction_projection_hist = self.abcdHelper.get_projection_prediction(
        self.background_hist, self.variable_2_max)

    self.true_projection_hist, self.smart_binning = self.histogramsHelper.rebin(self.true_projection_hist)
    self.prediction_projection_hist, _ = self.histogramsHelper.rebin(
        self.prediction_projection_hist, self.smart_binning)

  def plot_optimization_hists(self):
    for name, hist in self.optimization_hists.items():
      hist.GetYaxis().SetTitle(hist.GetYaxis().GetTitle() + self.abcdHelper.get_nice_name(self.config.variable_1))
      hist.GetXaxis().SetTitle(hist.GetXaxis().GetTitle() + self.abcdHelper.get_nice_name(self.config.variable_2))
      hist.GetZaxis().SetTitle(self.config.z_params[name][0])
      hist.GetZaxis().SetTitleOffset(1.9)

      self.canvases[name].cd()
      hist.Draw("colz")
      ROOT.gPad.SetLogz(self.config.z_params[name][3])
      hist.GetZaxis().SetRangeUser(self.config.z_params[name][1], self.config.z_params[name][2])

  def __flip_signal_to_region_a(self):

    background_mean_x = self.background_hist.GetMean(1)
    background_mean_y = self.background_hist.GetMean(2)

    # A  |  C
    # -------
    # B  |  D

    signal_region_count = {
        "A": 0,
        "B": 0,
        "C": 0,
        "D": 0
    }

    for mass, ctau in self.signal_hists:
      signal_hist = self.signal_hists[(mass, ctau)]

      if signal_hist is None or not isinstance(signal_hist, ROOT.TH2):
        continue

      # get mean if the signal in x and y dimentions
      mean_x = signal_hist.GetMean(1)
      mean_y = signal_hist.GetMean(2)

      if mean_x < background_mean_x and mean_y > background_mean_y:
        signal_region_count["A"] += 1
      elif mean_x < background_mean_x and mean_y < background_mean_y:
        signal_region_count["B"] += 1
      elif mean_x > background_mean_x and mean_y > background_mean_y:
        signal_region_count["C"] += 1
      elif mean_x > background_mean_x and mean_y < background_mean_y:
        signal_region_count["D"] += 1

    max_region = max(signal_region_count, key=signal_region_count.get)

    if max_region == "A":
      pass  # already in region A
    elif max_region == "B":
      warn("Signal in region B, flipping to region A")
      self.background_hist = self.abcdHelper.flip_hist_vertically(self.background_hist)
      for mass, ctau in self.signal_hists:
        if (mass, ctau) not in self.signal_hists:
          continue

        signal_hist = self.signal_hists[(mass, ctau)]

        if signal_hist is None or not isinstance(signal_hist, ROOT.TH2):
          continue

        self.signal_hists[(mass, ctau)] = self.abcdHelper.flip_hist_vertically(signal_hist)

    elif max_region == "C":
      warn("Signal in region C, flipping to region A")
      self.background_hist = self.abcdHelper.flip_hist_horizontally(self.background_hist)
      for mass, ctau in self.signal_hists:
        if (mass, ctau) not in self.signal_hists:
          continue

        signal_hist = self.signal_hists[(mass, ctau)]

        if signal_hist is None or not isinstance(signal_hist, ROOT.TH2):
          continue

        self.signal_hists[(mass, ctau)] = self.abcdHelper.flip_hist_horizontally(signal_hist)
    elif max_region == "D":
      warn("Signal in region D, flipping to region A")
      self.background_hist = self.abcdHelper.flip_hist_vertically(self.background_hist)
      self.background_hist = self.abcdHelper.flip_hist_horizontally(self.background_hist)

      for mass, ctau in self.signal_hists:
        if (mass, ctau) not in self.signal_hists:
          continue

        signal_hist = self.signal_hists[(mass, ctau)]

        if signal_hist is None or not isinstance(signal_hist, ROOT.TH2):
          continue

        signal_hist = self.abcdHelper.flip_hist_vertically(signal_hist)
        self.signal_hists[(mass, ctau)] = self.abcdHelper.flip_hist_horizontally(signal_hist)

    if self.variable_1_min is None:
      self.variable_1_min = self.background_hist.GetXaxis().GetXmin()
      self.variable_1_max = self.background_hist.GetXaxis().GetXmax()
      self.variable_2_min = self.background_hist.GetYaxis().GetXmin()
      self.variable_2_max = self.background_hist.GetYaxis().GetXmax()

  def get_n_signals_with_overlap_with_background_below(self, threshold):
    n_signals = 0
    for mass, ctau in self.signal_hists:
      signal_hist = self.signal_hists[(mass, ctau)]
      if signal_hist is None or not isinstance(signal_hist, ROOT.TH2):
        continue

      coeff = self.abcdHelper.get_overlap_coefficient(
        self.signal_hists[(mass, ctau)],
        self.background_hist, mass, ctau
      )
      if coeff < threshold:
        n_signals += 1

    return n_signals

  def plot_per_signal_hists(self):
    clones = {}

    label = ROOT.TLatex()
    label.SetTextSize(0.07)

    for i_mass, mass in enumerate(self.config.masses):
      for i_ctau, ctau in enumerate(self.config.ctaus):
        if (mass, ctau) not in self.signal_hists:
          continue

        if self.signal_hists[(mass, ctau)] is None or not isinstance(self.signal_hists[(mass, ctau)], ROOT.TH2):
          continue

        clones["background"] = self.background_hist.Clone()
        clones[(mass, ctau)] = self.signal_hists[(mass, ctau)].Clone()

        i_pad = 1 + i_mass * len(self.config.ctaus) + i_ctau
        mass_label = f"{mass.replace('p', '.')} GeV, {ctau} mm"

        self.canvases["grid"].cd(i_pad)
        self.set_pad_style()
        clones["background"].GetYaxis().SetTitle(clones["background"].GetYaxis().GetTitle() +
                                                 self.abcdHelper.get_nice_name(self.config.variable_1))
        clones["background"].GetXaxis().SetTitle(clones["background"].GetXaxis().GetTitle() +
                                                 self.abcdHelper.get_nice_name(self.config.variable_2))
        clones["background"].GetYaxis().SetTitleOffset(1.0)
        clones["background"].GetXaxis().SetTitleOffset(1.0)
        clones["background"].DrawNormalized("BOX")

        clones[(mass, ctau)].DrawNormalized("BOX SAME")
        label.DrawLatexNDC(*self.config.signal_label_position, mass_label)

        overlap = self.abcdHelper.get_overlap_coefficient(
          self.signal_hists[(mass, ctau)],
          self.background_hist,
          mass, ctau)
        label.DrawLatexNDC(0.13, 0.92, f"Overlap: {overlap:.2f}")

        self.canvases["significance"].cd(i_pad)
        self.set_pad_style()
        if self.significance_hists[(mass, ctau)] is not None:
          self.significance_hists[(mass, ctau)].Draw("colz")
        label.DrawLatexNDC(*self.config.signal_label_position, mass_label)

  def plot_background_hist(self):
    clone = self.background_hist.Clone()
    clone.GetYaxis().SetTitle(clone.GetYaxis().GetTitle() + self.abcdHelper.get_nice_name(self.config.variable_1))
    clone.GetXaxis().SetTitle(clone.GetXaxis().GetTitle() + self.abcdHelper.get_nice_name(self.config.variable_2))
    self.canvases["background"].cd()
    ROOT.gStyle.SetOptStat(0)

    clone.DrawNormalized("BOX")

    # print correlation between variables in the plot
    correlation = clone.GetCorrelationFactor()
    label = ROOT.TLatex()
    label.SetTextSize(0.03)
    label.DrawLatexNDC(0.15, 0.85, f"Correlation: {correlation:.2f}")

    return correlation

  def calculate_best_points(self):

    self.best_points = {}

    if self.config.optimization_param == "significance":
      if self.config.common_signals_optimization:
        self.best_points["all"] = self.abcdHelper.get_optimal_point_for_significance(
            self.significance_hists, self.contamination_hists, self.optimization_hists)
      else:
        for mass in self.config.masses:
          for ctau in self.config.ctaus:
            if (mass, ctau) not in self.signal_hists:
              continue

            if self.config.optimization_param == "significance":
              self.best_points[(mass, ctau)] = self.abcdHelper.get_optimal_point_for_significance(
                  {(mass, ctau): self.significance_hists[(mass, ctau)]},
                  {(mass, ctau): self.contamination_hists[(mass, ctau)]},
                  self.optimization_hists
              )
    else:
      self.best_points["all"] = self.abcdHelper.get_optimal_point_for_param(
          self.optimization_hists, self.config.optimization_param)

  def print_params_for_best_point(self):

    if "all" in self.best_points:
      best_point = self.best_points["all"]
      if best_point is None:
        warn("Best point not found")
        return

      i, j = best_point
      error = self.optimization_hists["error"].GetBinContent(i, j)
      closure = self.optimization_hists["closure"].GetBinContent(i, j)
      min_n_events = self.optimization_hists["min_n_events"].GetBinContent(i, j)

      info("Best point for all signals: ")
      info(f"{self.config.variable_1} = {best_point[0]}, {self.config.variable_2} = {best_point[1]}")
      info(f"Error: {error:.2f}, Closure: {closure:.2f}, Min n events: {min_n_events:.1f}")

    else:
      for mass in self.config.masses:
        for ctau in self.config.ctaus:
          if (mass, ctau) not in self.signal_hists:
            continue

          best_point = self.best_points[(mass, ctau)]
          if best_point is None:
            warn(f"Best point for {mass} GeV, {ctau} mm not found")
            continue

          error = self.optimization_hists["error"].GetBinContent(i, j)
          closure = self.optimization_hists["closure"].GetBinContent(i, j)
          min_n_events = self.optimization_hists["min_n_events"].GetBinContent(i, j)

          info(f"Best point for {mass} GeV, {ctau} mm: ")
          info(f"{self.config.variable_1} = {best_point[0]}, {self.config.variable_2} = {best_point[1]}")
          info(f"Error: {error:.2f}, Closure: {closure:.2f}, Min n events: {min_n_events:.1f}")

  def get_n_signals_with_good_binning(self):
    n_points_found = 0

    for mass in self.config.masses:
      for ctau in self.config.ctaus:
        if (mass, ctau) not in self.signal_hists:
          continue

        if self.abcdHelper.is_point_good_for_signal(
            self.signal_hists[(mass, ctau)],
            self.background_hist,
            ctau, mass,
            self.contamination_hists[(mass, ctau)],
            self.optimization_hists,
            self.best_points["all"] if "all" in self.best_points else self.best_points[(mass, ctau)],
        ):
          n_points_found += 1

    return n_points_found

  def plot_and_save_best_abcd_points(self):

    file_path = f"{self.config.output_path}/best_points_{self.config.variable_1}_vs_{self.config.variable_2}.txt"
    with open(file_path, "w") as f:
      f.write("mass, ctau, best_x, best_y, closure, error, min_n_events, significance, contamination\n")

      for i_mass, mass in enumerate(self.config.masses):
        for i_ctau, ctau in enumerate(self.config.ctaus):
          if (mass, ctau) not in self.signal_hists:
            continue

          best_point = self.best_points["all"] if "all" in self.best_points else self.best_points[(mass, ctau)]

          if best_point is None:
            warn(f"Best point for {mass} GeV, {ctau} mm not found")
            continue

          if not self.abcdHelper.is_point_good_for_signal(
              self.signal_hists[(mass, ctau)],
              self.background_hist,
              ctau, mass,
              self.contamination_hists[(mass, ctau)],
              self.optimization_hists,
              best_point,
          ):
            warn(f"Best point for {mass} GeV, {ctau} mm is not good")
            continue

          significance_hist = self.significance_hists[(mass, ctau)]
          if significance_hist is None or not isinstance(significance_hist, ROOT.TH2):
            warn(f"Significance histogram for {mass} GeV, {ctau} mm not found")
            continue

          i, j = best_point
          values = {name: hist.GetBinContent(i, j) for name, hist in self.optimization_hists.items()}
          significance = significance_hist.GetBinContent(i, j)
          contamination = self.contamination_hists[(mass, ctau)].GetBinContent(i, j)

          f.write(f"{mass}, {ctau}, {best_point[0]:.2f}, {best_point[1]:.2f}, ")
          f.write(f"{values['closure']:.2f}, {values['error']:.2f}, ")
          f.write(f"{values['min_n_events']:.1f}, {significance:.3f}, ")
          f.write(f"{contamination:.2f}\n")

          i_pad = 1 + i_mass * len(self.config.ctaus) + i_ctau

          line_x = self.background_hist.GetXaxis().GetBinLowEdge(i)
          line_y = self.background_hist.GetYaxis().GetBinLowEdge(j)

          self.lines[i_pad] = (ROOT.TLine(line_x, self.variable_2_min, line_x, self.variable_2_max),
                               ROOT.TLine(self.variable_1_min, line_y, self.variable_1_max, line_y))

          self.lines[i_pad][0].SetLineColor(self.config.abcd_line_color)
          self.lines[i_pad][1].SetLineColor(self.config.abcd_line_color)

          self.lines[i_pad][0].SetLineWidth(self.config.abcd_line_width)
          self.lines[i_pad][1].SetLineWidth(self.config.abcd_line_width)

          self.canvases["grid"].cd(i_pad)
          ROOT.gStyle.SetOptStat(0)
          self.lines[i_pad][0].Draw()
          self.lines[i_pad][1].Draw()
          self.canvases["grid"].Update()

          self.canvases["significance"].cd(i_pad)
          ROOT.gStyle.SetOptStat(0)
          self.lines[i_pad][0].Draw()
          self.lines[i_pad][1].Draw()
          self.canvases["significance"].Update()

      f.close()
      info(f"\nBest points saved to {file_path}\n")

  def plot_background_projections(self):

    if self.true_projection_hist is None:
      return

    self.true_projection_hist.SetLineColor(self.config.true_background_color)
    self.true_projection_hist.SetFillColorAlpha(self.config.true_background_color, 0.5)
    self.true_projection_hist.SetMarkerStyle(20)
    self.true_projection_hist.SetMarkerSize(0.2)
    self.true_projection_hist.SetMarkerColor(self.config.true_background_color)

    self.prediction_projection_hist.SetLineColor(self.config.predicted_background_color)
    self.prediction_projection_hist.SetMarkerStyle(20)
    self.prediction_projection_hist.SetMarkerSize(0.2)
    self.prediction_projection_hist.SetMarkerColor(self.config.predicted_background_color)

    self.projections_legend.AddEntry(self.true_projection_hist, self.config.true_background_description, "fl")
    self.projections_legend.AddEntry(self.prediction_projection_hist,
                                     self.config.predicted_background_description, "pl")

    self.projections_pads["main"].cd()
    self.true_projection_hist.Draw("PLE2")
    self.prediction_projection_hist.Draw("SAME PE")

    self.true_projection_hist.GetYaxis().SetRangeUser(0, self.config.y_max)
    current_title = self.true_projection_hist.GetYaxis().GetTitle()
    new_title = current_title + self.config.projection_y_title
    self.true_projection_hist.GetYaxis().SetTitle(new_title)
    self.true_projection_hist.GetYaxis().SetTitleOffset(1.2)
    self.true_projection_hist.GetYaxis().SetLabelSize(0.04)
    self.true_projection_hist.GetYaxis().SetTitleSize(0.04)

  def plot_signal_projections(self):
    for mass in self.config.masses:
      for ctau in self.config.ctaus:
        if (mass, ctau) not in self.signal_hists:
          continue

        self.signal_projections[(mass, ctau)] = self.abcdHelper.get_projection_true(
            self.signal_hists[(mass, ctau)], self.variable_2_max)
        self.signal_projections[(mass, ctau)], _ = self.histogramsHelper.rebin(
            self.signal_projections[(mass, ctau)], self.smart_binning)

        if self.signal_projections[(mass, ctau)] is None:
          continue

        color = self.config.signal_colors[(mass, ctau)] if (
            mass, ctau) in self.config.signal_colors else ROOT.kRed
        self.signal_projections[(mass, ctau)].SetLineColor(color)

        # normalize signal to background in A
        signal_integral = self.signal_projections[(mass, ctau)].Integral()
        scale = (self.true_projection_hist.Integral() / signal_integral if signal_integral > 0 else 1)
        self.signal_projections[(mass, ctau)].Scale(scale)

        self.signal_projections[(mass, ctau)].Draw("SAME")

        self.projections_legend.AddEntry(
            self.signal_projections[(mass, ctau)],
            f"Signal {mass} GeV, {ctau} mm", "l"
        )

    self.projections_legend.Draw()

  def plot_projections_ratio(self):
    if self.prediction_projection_hist is None or not isinstance(self.prediction_projection_hist, ROOT.TH1):
      return

    if self.true_projection_hist is None or not isinstance(self.true_projection_hist, ROOT.TH1):
      return

    self.projections_pads["ratio"].cd()

    self.ratio_hist = self.prediction_projection_hist.Clone()
    self.ratio_hist.SetTitle("")
    self.ratio_hist.Divide(self.prediction_projection_hist,
                           self.true_projection_hist,
                           1.0, 1.0, "B")

    self.ratio_hist_err = self.true_projection_hist.Clone()
    for i in range(1, self.ratio_hist_err.GetNbinsX() + 1):
      A = self.true_projection_hist.GetBinContent(i)
      err_A = self.true_projection_hist.GetBinError(i)

      if A > 0:
        err_ratio = ((err_A / A) ** 2 + (err_A / A) ** 2) ** 0.5
      else:
        err_ratio = 0

      self.ratio_hist_err.SetBinContent(i, 1)
      self.ratio_hist_err.SetBinError(i, err_ratio)

    self.ratio_hist_err.SetFillColorAlpha(ROOT.kRed, 0.5)

    self.ratio_hist.GetXaxis().SetTitle(self.ratio_hist.GetXaxis().GetTitle() +
                                        self.abcdHelper.get_nice_name(self.config.variable_2))
    self.ratio_hist.GetXaxis().SetTitleOffset(1.1)
    self.ratio_hist.GetXaxis().SetLabelSize(0.1)
    self.ratio_hist.GetXaxis().SetTitleSize(0.1)

    self.ratio_hist.GetYaxis().SetTitle(self.config.ratio_y_title)
    self.ratio_hist.GetYaxis().SetTitleOffset(0.5)
    self.ratio_hist.GetYaxis().SetLabelSize(0.1)
    self.ratio_hist.GetYaxis().SetTitleSize(0.1)

    self.ratio_hist.Draw()
    self.ratio_hist_err.Draw("SAME PLE2")

    self.ratio_hist.GetYaxis().SetRangeUser(0, self.config.y_max_ratio)

  def __get_lines(self):
    i, j = self.config.abcd_point
    x = self.background_hist.GetXaxis().GetBinLowEdge(i)
    y = self.background_hist.GetYaxis().GetBinLowEdge(j)

    line_x = ROOT.TLine(x, self.variable_2_min, x, self.variable_2_max)
    line_y = ROOT.TLine(self.variable_1_min, y, self.variable_1_max, y)

    line_x.SetLineColor(self.config.abcd_line_color)
    line_x.SetLineWidth(self.config.abcd_line_width)

    line_y.SetLineColor(self.config.abcd_line_color)
    line_y.SetLineWidth(self.config.abcd_line_width)

    return line_x, line_y

  def save_background_canvas(self):
    canvas = self.canvases["background"]
    canvas.cd()

    lines = self.__get_lines()
    lines[0].Draw()
    lines[1].Draw()

    canvas.Update()
    canvas.SaveAs(
        f"{self.config.output_path}/abcd_hists_background_"
        f"{self.config.variable_1}_vs_{self.config.variable_2}.pdf"
    )

  def save_canvases(self):
    lines = self.__get_lines()

    for key, canvas in self.canvases.items():
      if key in ["closure", "error", "min_n_events", "background"]:
        canvas.cd()
        ROOT.gStyle.SetOptStat(0)
        lines[0].Draw()
        lines[1].Draw()

      canvas.Update()
      canvas.SaveAs(
          f"{self.config.output_path}/abcd_hists_{key}_"
          f"{self.config.variable_1}_vs_{self.config.variable_2}.pdf"
      )

  def print_params_for_selected_point(self):
    a, b, c, d, a_err, b_err, c_err, d_err = self.abcdHelper.get_abcd(self.background_hist, self.config.abcd_point)

    info(f"\n\nSelected point: {self.config.abcd_point[0]:.2f}, {self.config.abcd_point[1]:.2f}")
    i, j = self.config.abcd_point
    info(f"{i=}, {j=}")

    info(f"True background in A: {a:.2f} +/- {a_err:.2f}")
    closure = -1
    error = -1
    min_n_events = -1
    prediction = None

    if a != 0 and b != 0 and c != 0 and d != 0:
      prediction = c/d * b
      prediction_err = ((b_err/b)**2 + (c_err/c) ** 2 + (d_err/d)**2)**0.5
      prediction_err *= prediction
      closure = self.abcdHelper.get_closure(a, prediction)
      error = self.abcdHelper.get_error(a, b, c, d, a_err, b_err, c_err, d_err, prediction)
      min_n_events = min(a, b, c, d)
      info(f"Predicted background in A: {prediction:.2f} +/- {prediction_err:.2f}")

    info("\n\nOptimization values (re-calculated):")
    info(f"Closure: {closure:.2f}, error: {error:.2f}, min_n_events: {min_n_events:.1f}")

    # extract optimization values from histograms for a cross check
    closure = self.optimization_hists["closure"].GetBinContent(i, j)
    error = self.optimization_hists["error"].GetBinContent(i, j)
    min_n_events = self.optimization_hists["min_n_events"].GetBinContent(i, j)

    info("\nOptimization values (from hists):")
    info(f"Closure: {closure:.2f}, error: {error:.2f}, min_n_events: {min_n_events:.1f}")

    info("\n\nSignal parameters:")
    for mass in self.config.masses:
      for ctau in self.config.ctaus:
        if (mass, ctau) not in self.signal_hists:
          continue

        significance_hist = self.significance_hists[(mass, ctau)]
        contamination_hist = self.contamination_hists[(mass, ctau)]

        if significance_hist is None or type(significance_hist) is not ROOT.TH2D:
          continue

        if contamination_hist is None or type(contamination_hist) is not ROOT.TH2D:
          continue

        significance = significance_hist.GetBinContent(i, j)
        contamination = contamination_hist.GetBinContent(i, j)
        info(f"Signal {mass} GeV, {ctau} mm: Significance: {significance:.2e} Contamination: {contamination:.2e}")

    info("\n\n")

  def __load_background_histograms(self):

    for path, cross_section in self.config.background_params:
      intput_path = self.config.background_path_pattern.format(path, self.config.skim[0], self.config.hist_dir)
      file_path = f"{self.config.base_path}/{intput_path}"

      try:
        self.background_files[path] = ROOT.TFile.Open(file_path)
      except OSError:
        warn(f"Could not open file {file_path}")
        continue

      if not self.background_files[path]:
        warn(f"Could not open file {file_path}")
        continue

      self.background_hists[path] = self.background_files[path].Get(self.hist_name)

      if not self.background_hists[path]:
        warn(f"Could not open histogram {self.hist_name} in file {file_path}")
        continue

      inital_events = self.background_files[path].Get("cutFlow").GetBinContent(1)
      self.background_hists[path].Scale(self.config.lumi*cross_section/inital_events)

  def __setup_backgrounds_sum_histogram(self):
    if self.config.do_data:
      file_path = f"{self.config.base_path}/{self.config.data_path}"
      self.data_file = ROOT.TFile.Open(file_path)

      if not self.data_file:
        warn(f"Could not open file {file_path}")
        return

      self.background_hist = self.data_file.Get(self.hist_name)

      if not self.background_hist:
        warn(f"Could not open histogram {self.hist_name} in file {file_path}")
        return
    else:
      for path, _ in self.config.background_params:
        if path not in self.background_hists or not self.background_hists[path]:
          continue

        if self.background_hists[path] is None or self.background_hists[path].Integral() == 0:
          continue

        self.background_hist = self.background_hists[path].Clone()
        break

      if not self.background_hist:
        fatal("No background histograms found")
        exit()

      for path, _ in self.config.background_params[1:]:
        if path not in self.background_hists or not self.background_hists[path]:
          continue
        self.background_hist.Add(self.background_hists[path])

    self.background_hist.SetFillColorAlpha(self.config.background_color, 0.5)
    self.background_hist.SetTitle("")

    self.background_hist.Rebin2D(self.config.rebin_2D, self.config.rebin_2D)

  def __load_signal_hists(self):
    for mass in self.config.masses:
      for ctau in self.config.ctaus:
        input_path = self.config.signal_path_pattern.format(mass, ctau, self.config.skim[0], self.config.hist_dir)

        try:
          self.signal_files[input_path] = ROOT.TFile(f"{self.config.base_path}/{input_path}")
        except OSError:
          continue

        self.signal_hists[(mass, ctau)] = self.signal_files[input_path].Get(self.hist_name)
        if self.signal_hists[(mass, ctau)] is None or not isinstance(self.signal_hists[(mass, ctau)], ROOT.TH2):
          info(f"Could not open histogram {self.hist_name} in file {input_path}")
          continue

        self.signal_hists[(mass, ctau)].SetName(f"signal_{mass}_{ctau}")
        self.signal_hists[(mass, ctau)].SetFillColorAlpha(self.config.signal_color, 0.5)

        self.signal_hists[(mass, ctau)].Rebin2D(self.config.rebin_2D, self.config.rebin_2D)

  def __setup_canvases(self):
    self.canvases = {
        "grid": ROOT.TCanvas(
            "grid", "grid",
            self.config.canvas_size * len(self.config.ctaus),
            self.config.canvas_size * len(self.config.masses)
        ),
        "background": ROOT.TCanvas("background", "background", self.config.canvas_size, self.config.canvas_size),
        "significance": ROOT.TCanvas(
            "significance", "significance",
            self.config.canvas_size * len(self.config.ctaus),
            self.config.canvas_size * len(self.config.masses)
        ),
        "closure": ROOT.TCanvas("closure", "closure", self.config.canvas_size, self.config.canvas_size),
        "error": ROOT.TCanvas("error", "error", self.config.canvas_size, self.config.canvas_size),
        "min_n_events": ROOT.TCanvas("min_n_events", "min_n_events", self.config.canvas_size, self.config.canvas_size),
        "projections": ROOT.TCanvas("projections", "projections", self.config.canvas_size, self.config.canvas_size),
    }

    for key in ["grid", "significance"]:
      self.canvases[key].Divide(
          len(self.config.ctaus), len(self.config.masses))

    for key in ["closure", "error", "min_n_events", "background"]:
      self.canvases[key].cd()
      ROOT.gPad.SetLeftMargin(0.15)
      ROOT.gPad.SetRightMargin(0.25)
      ROOT.gPad.SetTopMargin(0.15)
      ROOT.gPad.SetBottomMargin(0.15)

    self.canvases["projections"].cd()

    self.projections_pads["main"] = ROOT.TPad("pad_main", "pad_main", 0, 0.3, 1, 1)
    self.projections_pads["main"].SetBottomMargin(0)
    self.projections_pads["main"].Draw()

    self.projections_pads["ratio"] = ROOT.TPad("pad_ratio", "pad_ratio", 0, 0, 1, 0.3)
    self.projections_pads["ratio"].SetTopMargin(0)
    self.projections_pads["ratio"].SetBottomMargin(0.3)
    self.projections_pads["ratio"].Draw()

  def set_pad_style(self):
    ROOT.gPad.SetLeftMargin(0.08)
    ROOT.gPad.SetRightMargin(0.0)
    ROOT.gPad.SetTopMargin(0.0)
    ROOT.gPad.SetBottomMargin(0.08)

  def __setup_signal_hists(self):
    for mass in self.config.masses:
      for ctau in self.config.ctaus:
        if (mass, ctau) not in self.signal_hists:
          continue

        self.significance_hists[(mass, ctau)] = self.abcdHelper.get_significance_hist(
            self.signal_hists[(mass, ctau)], self.background_hist)

        self.contamination_hists[(mass, ctau)] = self.abcdHelper.get_signal_contramination_hist(
            self.signal_hists[(mass, ctau)])

  def __get_input_dict(self, input_path):
    results = {}

    with open(input_path, "r") as f:
      lines = f.readlines()

      for line in lines[1:]:
        parts = line.split(",")

        mass = float(parts[0].replace("p", "."))
        ctau = float(parts[1])

        best_x = float(parts[2])
        best_y = float(parts[3])

        closure = float(parts[4])
        error = float(parts[5])
        min_n_events = float(parts[6])
        significance = float(parts[7])
        contamination = float(parts[8])

        results[(mass, ctau)] = {
            "best_x": best_x,
            "best_y": best_y,
            "closure": closure,
            "error": error,
            "min_n_events": min_n_events,
            "significance": significance,
            "contamination": contamination
        }

    return results

  def plot_optimal_points(self):
    ROOT.gStyle.SetOptStat(0)

    region = self.config.do_region
    collection = self.config.collection
    do_data = self.config.do_data

    input_path = (
        f"../abcd/results_{region}_{collection}_"
        f"{'data' if do_data else 'mc'}{self.config.category}/best_points_"
        f"{self.config.variable_1}_vs_{self.config.variable_2}.txt"
    )
    results = self.__get_input_dict(input_path)

    mass_to_bin = {
        0.35: 1,
        1: 2,
        2: 3,
        12: 4,
        30: 5,
        60: 6,
    }

    ctau_to_bin = {
        1e-5: 1,
        1e0: 2,
        1e1: 3,
        1e2: 4,
        1e3: 5,
        1e5: 6,
    }

    canvas = ROOT.TCanvas("canvas", "", 800, 800)
    hist = ROOT.TH2D("hist", "", len(mass_to_bin), 0, len(mass_to_bin), len(ctau_to_bin), 0, len(ctau_to_bin))

    for mass, x in mass_to_bin.items():
      hist.GetXaxis().SetBinLabel(x, str(mass))

    for ctau, y in ctau_to_bin.items():
      hist.GetYaxis().SetBinLabel(y, f"{ctau:.0e}")

    assigned_colors = {}

    max_so_far = 1

    for (mass, ctau), params in results.items():
      x = mass_to_bin[mass]
      y = ctau_to_bin[ctau]

      best_x = params["best_x"]
      best_y = params["best_y"]

      if (best_x, best_y) not in assigned_colors:
        assigned_colors[(best_x, best_y)] = max_so_far
        max_so_far += 1

      hist.SetBinContent(x, y, assigned_colors[(best_x, best_y)])

    hist.Draw("colz")

    latex = ROOT.TLatex()
    latex.SetTextSize(0.03)
    latex.SetTextAlign(22)  # Center alignment

    for (mass, ctau), params in results.items():
      x = mass_to_bin[mass]
      y = ctau_to_bin[ctau]
      best_x = params["best_x"]
      best_y = params["best_y"]
      x = hist.GetXaxis().GetBinCenter(x)
      y = hist.GetYaxis().GetBinCenter(y)
      latex.DrawLatex(x, y, f"{best_x}, {best_y}")

    canvas.SaveAs(
        f"../abcd/results_{region}_{collection}_{'data' if do_data else 'mc'}{self.config.category}/best_points_"
        f"{self.config.variable_1}_vs_{self.config.variable_2}.pdf")
