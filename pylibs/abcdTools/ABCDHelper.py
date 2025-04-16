from Logger import warn

import math
from ctypes import c_double
import ROOT


class ABCDHelper:
  def __init__(self, config=None, max_error=None, max_closure=None, min_n_events=None, max_signal_contamination=None, max_overlap=None):
    self.config = config

    self.max_error = max_error
    self.max_closure = max_closure
    self.min_n_events = min_n_events
    self.max_signal_contamination = max_signal_contamination
    self.max_overlap = max_overlap
    self.signal_overlap = {}

  def flip_hist_vertically(self, hist):
    # The method changes the y-axis from Y to -Y. The range of the axis will
    # be changed from (a, b) to (-b, -a), and the value on the y-axis will be changed
    # from y to -y. The x-axis will not be changed.

    flipped_hist = ROOT.TH2F(hist.GetName() + "_flipped", hist.GetTitle(),
                             hist.GetNbinsX(), hist.GetXaxis().GetXmin(), hist.GetXaxis().GetXmax(),
                             hist.GetNbinsY(), -hist.GetYaxis().GetXmax(), -hist.GetYaxis().GetXmin())

    for i in range(1, hist.GetNbinsX() + 1):
      for j in range(1, hist.GetNbinsY() + 1):
        flipped_hist.SetBinContent(i, hist.GetNbinsY()+1-j, hist.GetBinContent(i, j))
        flipped_hist.SetBinError(i,  hist.GetNbinsY()+1-j, hist.GetBinError(i, j))

    flipped_hist.GetXaxis().SetTitle(hist.GetXaxis().GetTitle())
    flipped_hist.GetYaxis().SetTitle("-")
    flipped_hist.SetFillColorAlpha(hist.GetFillColor(), 0.5)

    return flipped_hist

  def flip_hist_horizontally(self, hist):
    # The method changes the x-axis from X to -X. The range of the axis will
    # be changed from (a, b) to (-b, -a), and the value on the x-axis will be changed
    # from x to -x. The y-axis will not be changed.

    flipped_hist = ROOT.TH2F(hist.GetName() + "_flipped", hist.GetTitle(),
                             hist.GetNbinsX(), -hist.GetXaxis().GetXmax(), -hist.GetXaxis().GetXmin(),
                             hist.GetNbinsY(), hist.GetYaxis().GetXmin(), hist.GetYaxis().GetXmax())

    for i in range(1, hist.GetNbinsX() + 1):
      for j in range(1, hist.GetNbinsY() + 1):
        flipped_hist.SetBinContent(hist.GetNbinsX()+1-i, j, hist.GetBinContent(i, j))
        flipped_hist.SetBinError(hist.GetNbinsX()+1-i, j, hist.GetBinError(i, j))

    flipped_hist.GetXaxis().SetTitle("-")
    flipped_hist.GetYaxis().SetTitle(hist.GetYaxis().GetTitle())
    flipped_hist.SetFillColorAlpha(hist.GetFillColor(), 0.5)

    return flipped_hist

  def get_abcd(self, hist, point, raw_errors=False):
    # The method returns the number of events in the four regions
    # of the ABCD plane, given a 2D histogram and a point in the
    # histogram. The point is a tuple (x_bin, y_bin).
    #
    # A  |  C
    # -------
    # B  |  D

    a_err = c_double(0)
    b_err = c_double(0)
    c_err = c_double(0)
    d_err = c_double(0)

    x_min_bin = 1
    x_pre_bin = point[0]-1
    x_post_bin = point[0]
    x_max_bin = hist.GetNbinsX()

    y_min_bin = 1
    y_pre_bin = point[1]-1
    y_post_bin = point[1]
    y_max_bin = hist.GetNbinsY()

    a = hist.IntegralAndError(x_min_bin, x_pre_bin, y_post_bin, y_max_bin, a_err)
    b = hist.IntegralAndError(x_min_bin, x_pre_bin, y_min_bin, y_pre_bin, b_err)
    c = hist.IntegralAndError(x_post_bin, x_max_bin, y_post_bin, y_max_bin, c_err)
    d = hist.IntegralAndError(x_post_bin, x_max_bin, y_min_bin, y_pre_bin, d_err)

    if x_pre_bin < x_min_bin:
      a = 0
      a_err = c_double(0)
      b = 0
      b_err = c_double(0)

    if y_pre_bin < y_min_bin:
      b = 0
      b_err = c_double(0)
      d = 0
      d_err = c_double(0)

    if x_post_bin > x_max_bin:
      c = 0
      c_err = c_double(0)
      d = 0
      d_err = c_double(0)

    if y_post_bin > y_max_bin:
      a = 0
      a_err = c_double(0)
      c = 0
      c_err = c_double(0)

    if raw_errors:
      a_err = a**0.5 if a > 0 else 0
      b_err = b**0.5 if b > 0 else 0
      c_err = c**0.5 if c > 0 else 0
      d_err = d**0.5 if d > 0 else 0
    else:
      a_err = a_err.value
      b_err = b_err.value
      c_err = c_err.value
      d_err = d_err.value

    return a, b, c, d, a_err, b_err, c_err, d_err

  def get_overlap_coefficient(self, signal_hist, background_hist, mass, ctau):
    if (mass, ctau) in self.signal_overlap:
      return self.signal_overlap[(mass, ctau)]

    background_hist = background_hist.Clone()
    signal_hist = signal_hist.Clone()
    background_hist.Scale(1.0 / background_hist.Integral())
    signal_hist.Scale(1.0 / signal_hist.Integral())

    numerator = 0.0
    sig_norm = 0.0
    bck_norm = 0.0

    for i in range(1, background_hist.GetNbinsX() + 1):
      for j in range(1, background_hist.GetNbinsY() + 1):

        bck = background_hist.GetBinContent(i, j)
        sig = signal_hist.GetBinContent(i, j)

        if sig <= 0 or bck <= 0:  # in some corner cases, MC histograms can have negative-content bins
          continue

        numerator += sig*bck
        sig_norm += sig * sig
        bck_norm += bck * bck

    coeff = numerator / math.sqrt(sig_norm*bck_norm) if sig_norm > 0 and bck_norm > 0 else 0.0
    self.signal_overlap[(mass, ctau)] = coeff
    return coeff  # 1 = identical, 0 = no overlap

  def get_significance_hist(self, signal_hist, background_hist):
    # The method returns a 2D histogram with the significance
    # of the signal over the background in each bin of the
    # 2D histogram. The significance is calculated as:
    #
    # significance = n_signal / sqrt(n_signal + n_background)

    if signal_hist is None or not isinstance(signal_hist, ROOT.TH2):
      warn("ABCDHelper.get_significance_hist: signal_hist is None")
      return None

    significance_hist = signal_hist.Clone()
    significance_hist.SetTitle("")

    x_min_bin = 1
    y_max_bin = signal_hist.GetNbinsY()

    for i in range(1, significance_hist.GetNbinsX() + 1):
      for j in range(1, significance_hist.GetNbinsY() + 1):

        x_pre_bin = i
        y_post_bin = j+1

        n_signal = signal_hist.Integral(x_min_bin, x_pre_bin, y_post_bin, y_max_bin)
        n_background = background_hist.Integral(x_min_bin, x_pre_bin, y_post_bin, y_max_bin)

        significance_hist.SetBinContent(i, j, self.__get_significance(n_signal, n_background))

    return significance_hist

  def get_signal_contramination_hist(self, signal_hist):
    if signal_hist is None or not isinstance(signal_hist, ROOT.TH2):
      warn("ABCDHelper.get_signal_contramination_hist: signal_hist is None")
      return None

    signal_contamination_hist = signal_hist.Clone()
    signal_contamination_hist.SetTitle("")

    total_signal = signal_hist.Integral()

    x_min_bin = 1
    x_max_bin = signal_contamination_hist.GetNbinsX()
    y_min_bin = 1
    y_max_bin = signal_contamination_hist.GetNbinsY()

    for i in range(1, signal_contamination_hist.GetNbinsX() + 1):
      for j in range(1, signal_contamination_hist.GetNbinsY() + 1):

        x_pre_bin = i
        x_post_bin = i+1
        y_pre_bin = j
        y_post_bin = j+1

        n_signal_b = signal_hist.Integral(x_min_bin, x_pre_bin, y_min_bin, y_pre_bin)
        n_signal_c = signal_hist.Integral(x_post_bin, x_max_bin, y_post_bin, y_max_bin)
        n_signal_d = signal_hist.Integral(x_post_bin, x_max_bin, y_min_bin, y_pre_bin)

        n_signal = max(n_signal_b, n_signal_c, n_signal_d)
        signal_contamination_hist.SetBinContent(i, j, n_signal / total_signal if total_signal > 0 else 0)

    return signal_contamination_hist

  def get_optimization_hists(self, background_hist):
    # The method returns three 2D histograms with the optimization
    # parameters for each bin of the 2D histogram. The optimization
    # parameters are:
    #
    # - Closure: The percentage difference between the observed
    #   number of events in region A and the prediction using the
    #   other regions.
    #
    # - Error: The number of standard deviations between the observed
    #   number of events in region A and the prediction using the
    #   other regions.
    #
    # - Min N Events: The minimum number of events in the four regions
    #   of the ABCD plane.

    optimization_params = ("closure", "error", "min_n_events")
    optimization_hists = {name: self.__get_optimization_hist(
        background_hist, name) for name in optimization_params}

    return optimization_hists

  def get_optimal_point_for_significance(self, significance_hists, signal_contamination_hists, optimization_hists):
    # Returns the bin with the highest significance that satisfies
    # the optimization criteria. The optimization criteria are:
    #
    # - The error is less than the maximum error.
    # - The closure is less than the maximum closure.
    # - The minimum number of events in the four regions is greater
    #   than the minimum number of events.
    # - The signal contamination is less than the maximum signal contamination.
    #

    max_significance = 0
    best_point = None

    first_hist = next(iter(significance_hists.values()))
    if first_hist is None or not isinstance(first_hist, ROOT.TH2):
      warn("ABCDHelper.get_optimal_point_for_significance: first_hist is None")
      return None

    for i in range(1, first_hist.GetNbinsX() + 1):
      for j in range(1, first_hist.GetNbinsY() + 1):
        values = {name: hist.GetBinContent(i, j) for name, hist in optimization_hists.items()}

        if values["error"] < 0 or values["error"] > self.max_error:
          warn("ABCDHelper.get_optimal_point_for_significance: error is too high")
          continue

        if values["closure"] < 0 or values["closure"] > self.max_closure:
          warn("ABCDHelper.get_optimal_point_for_significance: closure is too high")
          continue

        if values["min_n_events"] < 0 or values["min_n_events"] < self.min_n_events:
          warn("ABCDHelper.get_optimal_point_for_significance: min_n_events is too low")
          continue

        total_significance = 0

        for hist_name, significance_hist in significance_hists.items():
          signal_contamination_hist = signal_contamination_hists[hist_name]

          if significance_hist is None:
            warn("ABCDHelper.get_optimal_point_for_significance: significance_hist is None")
            return best_point

          significance = significance_hist.GetBinContent(i, j)

          signal_contamination = signal_contamination_hist.GetBinContent(i, j)

          if signal_contamination < 0 or signal_contamination > self.max_signal_contamination:
            warn("ABCDHelper.get_optimal_point_for_significance: signal contamination is too high")
            continue

          total_significance += significance

        if total_significance > max_significance:
          max_significance = total_significance
          best_point = (i, j)

    if best_point is None:
      return None

    return best_point

  def is_point_good_for_signal(self, signal_hist, background_hist, ctau, mass,
                               signal_contamination_hist, optimization_hists, point):
    if point is None:
      return False

    values = {name: hist.GetBinContent(*point) for name, hist in optimization_hists.items()}

    if "error" in values and values["error"] > self.max_error:
      warn("ABCDHelper.is_point_good_for_signal: error is too high")
      return False

    if "closure" in values and values["closure"] > self.max_closure:
      warn("ABCDHelper.is_point_good_for_signal: closure is too high")
      return False

    if "min_n_events" in values and values["min_n_events"] < self.min_n_events:
      warn("ABCDHelper.is_point_good_for_signal: min_n_events is too low")
      return False

    signal_contamination = signal_contamination_hist.GetBinContent(*point)

    if signal_contamination > self.max_signal_contamination:
      warn("ABCDHelper.is_point_good_for_signal: signal contamination is too high")
      return False

    overlap = self.get_overlap_coefficient(signal_hist, background_hist, mass, ctau)
    if overlap > self.max_overlap:
      warn("ABCDHelper.is_point_good_for_signal: signal overlap is too high")
      return False

    return True

  def get_optimal_point_for_param(self, optimization_hists, param):

    optimization_hist = optimization_hists[param]
    other_hists = {name: hist for name, hist in optimization_hists.items() if name != param}

    best_point = None
    min_value = 999999
    max_value = 0

    for i in range(1, optimization_hist.GetNbinsX() + 1):
      for j in range(1, optimization_hist.GetNbinsY() + 1):
        optimization_value = optimization_hist.GetBinContent(i, j)

        if not self.is_point_good_for_signal(optimization_hist, other_hists, (i, j)):
          continue

        if (param == "error" or param == "closure") and optimization_value < min_value:
          min_value = optimization_value
          best_point = (i, j)
        if (param == "min_n_events") and optimization_value > max_value:
          max_value = optimization_value
          best_point = (i, j)

    if best_point is None:
      return None

    return best_point

  def get_nice_name(self, name):
    return self.config.nice_names[name] if name in self.config.nice_names else name

  def get_projection_true(self, hist, x_max):
    if hist is None or type(hist) is not ROOT.TH2:
      return None

    hist_clone = hist.Clone()
    hist_clone.GetYaxis().SetRangeUser(self.config.abcd_point[1], x_max)

    hist_true = hist_clone.ProjectionY(hist.GetName() + "_projection_true", 1, self.config.abcd_point[0])
    return hist_true

  def get_projection_prediction(self, hist, x_max):
    hist_clone = hist.Clone()
    hist_clone.GetYaxis().SetRangeUser(self.config.abcd_point[1], x_max)

    hist_prediction = hist_clone.ProjectionY("projection_c", self.config.abcd_point[0], hist_clone.GetNbinsX())

    _, b, _, d, _, _, _, _ = self.get_abcd(hist, self.config.abcd_point)
    abcd_ratio = b/d if d > 0 else 1
    hist_prediction.Scale(abcd_ratio)

    return hist_prediction

  def get_closure(self, true, pred):
    closure = -1
    if true != 0:
      closure = abs(true - pred) / true

    return closure

  def get_error(self, a, a_err, prediction, prediction_err):
    error = -1

    if prediction_err != 0 and a_err != 0:
      error = abs(a - prediction)
      error /= (prediction_err**2 + a_err**2)**0.5

    return error

  # -----------------------------------------------------------------------
  # Private methods
  # -----------------------------------------------------------------------

  def get_prediction(self, b, c, d, b_err, c_err, d_err):
    if b <= 0 or c <= 0 or d <= 0:
      warn("ABCDHelper.get_prediction: b, c or d is less than or equal to 0")
      return 0, 0
    
    prediction = c/d * b
    prediction_err = ((b_err/b)**2 + (c_err/c) ** 2 + (d_err/d)**2)**0.5

    return prediction, prediction_err

  def __get_optimization_hist(self, background_hist, hist_type):
    optimization_hist = background_hist.Clone()

    optimization_hist.SetTitle("")

    for i in range(1, optimization_hist.GetNbinsX() + 1):
      for j in range(1, optimization_hist.GetNbinsY() + 1):

        values = self.get_abcd(background_hist, (i, j))
        a, b, c, d, a_err, b_err, c_err, d_err = values

        closure = -1
        error = -1
        min_n_events = -1

        if a != 0 and b != 0 and c != 0 and d != 0:
          prediction, prediction_err = self.get_prediction(b, c, d, b_err, c_err, d_err)
          closure = self.get_closure(a, prediction)
          error = self.get_error(a, a_err, prediction, prediction_err)
          min_n_events = min(a, b, c, d)

        value = None

        if hist_type == "closure":
          value = closure
        elif hist_type == "error":
          value = error
        elif hist_type == "min_n_events":
          value = min_n_events
        else:
          print("ABCDHelper.__get_optimization_hist: ")
          print(f"Invalid hist type: {hist_type}")
          return None

        optimization_hist.SetBinContent(i, j, value)

    default_value = optimization_hist.GetMaximum() if hist_type != "min_n_events" else 0
    self.__replace_default_values(optimization_hist, default_value)

    return optimization_hist

  def __get_significance(self, n_signal, n_background):
    significance = 0.0
    if n_background > 0:
      significance = float(n_signal) / (n_signal + n_background)**0.5
    return significance

  def __replace_default_values(self, hist, default):
    for i in range(1, hist.GetNbinsX() + 1):
      for j in range(1, hist.GetNbinsY() + 1):
        if hist.GetBinContent(i, j) == -1:
          hist.SetBinContent(i, j, default)
