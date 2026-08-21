from Logger import warn

from ROOT import TObject, gStyle
import ctypes
import math
import ROOT


class Styler:
  mainXAxisTitleOffset = 1.15
  legacyMainXAxisTitleOffset = 1.7
  ratioXAxisTitleOffset = 1.0

  def __init__(self, config):
    self.config = config

    self.topMargin = 0.06
    self.bottomMargin = 0.12
    self.leftMargin = 0.13
    self.rightMargin = 0.04
    self.automaticMargins = {
        "left": self.leftMargin,
        "right": self.rightMargin,
        "top": 0.06,
        "bottom": self.bottomMargin,
    }

    self.plotMargins = getattr(self.config, "plot_margins", None)
    if self.plotMargins is not None:
      if not isinstance(self.plotMargins, dict):
        raise TypeError("plot_margins must be a dictionary")
      unknown_margins = set(self.plotMargins) - {"left", "right", "top", "bottom"}
      if unknown_margins:
        raise ValueError(f"Unknown plot margins: {', '.join(sorted(unknown_margins))}")
      if any(not 0 <= value < 1 for value in self.plotMargins.values()):
        raise ValueError("plot_margins values must be between 0 and 1")
      self.leftMargin = self.plotMargins.get("left", self.leftMargin)
      self.rightMargin = self.plotMargins.get("right", self.rightMargin)
      if self.leftMargin + self.rightMargin >= 1:
        raise ValueError("left and right plot margins must sum to less than 1")

    self.labelFontSize = 26
    self.pendingRatioYAxis = None
    self.pendingRatioTitleOffset = None
    
    self.__setStyle()

  def setup_ratio_pad(self, pad):
    pad.SetPad(0, 0, 1, 0.3)
    self.__setupPadDefaults(pad)
    pad.SetTopMargin(0)
    margins = self.plotMargins or self.automaticMargins
    canvas_bottom_margin = margins.get("bottom", 0.18)
    if canvas_bottom_margin >= 0.3:
      raise ValueError("bottom plot margin must be less than 0.3 for ratio plots")
    bottom_margin = canvas_bottom_margin / 0.3
    pad.SetBottomMargin(bottom_margin)
    pad.SetLogy(False)

  def setup_main_pad_with_ratio(self, pad):
    pad.SetPad(0, 0.3, 1, 1)
    self.__setupPadDefaults(pad)
    pad.SetBottomMargin(0.0)
    margins = self.plotMargins or self.automaticMargins
    canvas_top_margin = margins.get("top", 0.063)
    if canvas_top_margin >= 0.7:
      raise ValueError("top plot margin must be less than 0.7 for ratio plots")
    top_margin = canvas_top_margin / 0.7
    pad.SetTopMargin(top_margin)

  def setup_main_pad_without_ratio(self, pad):
    # pad.SetPad(0, 0.0, 1, 1)
    self.__setupPadDefaults(pad)
    margins = self.plotMargins or self.automaticMargins
    bottom_margin = margins.get("bottom", 0.2)
    top_margin = margins.get("top", 0.09)
    if top_margin + bottom_margin >= 1:
      raise ValueError("top and bottom plot margins must sum to less than 1")
    pad.SetBottomMargin(bottom_margin)
    pad.SetTopMargin(top_margin)

  def __setupPadDefaults(self, pad):
    pad.SetLeftMargin(self.leftMargin)
    pad.SetBottomMargin(self.bottomMargin)
    pad.SetRightMargin(self.rightMargin)
    pad.SetTopMargin(self.topMargin)
    pad.SetTickx(1)
    pad.SetTicky(1)

  def __setStyle(self):
    gStyle.SetPadTopMargin(self.topMargin)
    gStyle.SetPadBottomMargin(self.bottomMargin)
    gStyle.SetPadLeftMargin(self.leftMargin)
    gStyle.SetPadRightMargin(self.rightMargin)

    gStyle.SetCanvasBorderMode(0)
    gStyle.SetCanvasColor(ROOT.kWhite)

    gStyle.SetPadBorderMode(0)
    gStyle.SetPadColor(ROOT.kWhite)
    gStyle.SetPadGridX(False)
    gStyle.SetPadGridY(False)
    gStyle.SetGridColor(0)
    gStyle.SetGridStyle(3)
    gStyle.SetGridWidth(1)

    gStyle.SetFrameBorderMode(0)
    gStyle.SetFrameBorderSize(1)
    gStyle.SetFrameFillColor(0)
    gStyle.SetFrameFillStyle(0)
    gStyle.SetFrameLineColor(1)
    gStyle.SetFrameLineStyle(1)
    gStyle.SetFrameLineWidth(1)

    gStyle.SetHistLineColor(1)
    gStyle.SetHistLineStyle(0)
    gStyle.SetHistLineWidth(1)

    gStyle.SetEndErrorSize(2)

    gStyle.SetOptFit(1)
    gStyle.SetFitFormat("5.4g")
    gStyle.SetFuncColor(2)
    gStyle.SetFuncStyle(1)
    gStyle.SetFuncWidth(1)

    gStyle.SetOptDate(0)
    gStyle.SetOptFile(0)

    gStyle.SetOptStat(0)  # To display the mean and RMS:   SetOptStat("mr")
    gStyle.SetStatColor(ROOT.kWhite)
    gStyle.SetStatFont(43)
    gStyle.SetStatFontSize(self.labelFontSize)
    gStyle.SetStatTextColor(1)
    gStyle.SetStatFormat("6.4g")
    gStyle.SetStatBorderSize(1)
    gStyle.SetStatH(0.1)
    gStyle.SetStatW(0.15)

    gStyle.SetOptTitle(0)
    gStyle.SetTitleFont(43)
    gStyle.SetTitleColor(1)
    gStyle.SetTitleTextColor(1)
    gStyle.SetTitleFillColor(10)
    gStyle.SetTitleFontSize(self.labelFontSize)

    gStyle.SetTitleColor(1, "XYZ")
    gStyle.SetTitleFont(43, "XYZ")
    gStyle.SetTitleSize(18, "XYZ")
    gStyle.SetTitleXOffset(0.9)
    gStyle.SetTitleYOffset(1.25)

    gStyle.SetLabelColor(1, "XYZ")
    gStyle.SetLabelFont(43, "XYZ")
    gStyle.SetLabelOffset(0.007, "XYZ")
    gStyle.SetLabelSize(18, "XYZ")

    gStyle.SetAxisColor(1, "XYZ")
    gStyle.SetStripDecimals(True)
    gStyle.SetTickLength(0.03, "XYZ")
    gStyle.SetNdivisions(510, "XYZ")
    gStyle.SetPadTickX(1)  # To get tick marks on the opposite side of the frame
    gStyle.SetPadTickY(1)

    # TGaxis, rather than the histogram's TAxis, controls the position of the
    # automatically drawn scientific-notation exponent.
    label_outside_axes = getattr(self.config, "label_outside_axes", False)
    exponent_x_offset = -0.065 if label_outside_axes else 0.0
    exponent_y_offset = 0.01 if label_outside_axes else 0.0
    ROOT.TGaxis.SetExponentOffset(exponent_x_offset, exponent_y_offset, "y")

    gStyle.SetOptLogx(0)
    gStyle.SetOptLogy(0)
    gStyle.SetOptLogz(0)

    gStyle.SetPaperSize(20., 20.)

  def configureAutomaticMargins(
      self, y_ranges, canvas_size, x_labels=(), has_ratio=False):
    """Choose one compact set of margins that fits every configured plot."""
    if self.plotMargins is not None:
      return

    canvas_width, canvas_height = canvas_size
    measurement_canvas = ROOT.TCanvas(
        "tea_layout_measurement", "", canvas_width, canvas_height)
    measurement_canvas.cd()
    try:
      widest_label = max(
          (self.__widestYAxisLabel(*axis_range) for axis_range in y_ranges),
          default=self.__textWidth("1.2", 43, self.labelFontSize))
      title_thickness = max(
          self.__textHeight("Events", 43, self.labelFontSize),
          self.__textHeight("Data/MC", 43, self.labelFontSize))
    finally:
      measurement_canvas.Close()

    label_gap = 6
    title_gap = 4
    outer_gap = 8
    left_pixels = (widest_label + label_gap + title_gap
                   + title_thickness + outer_gap)

    show_labels = getattr(self.config, "show_cms_labels", False)
    labels_outside = getattr(self.config, "label_outside_axes", False)
    if show_labels and labels_outside:
      top_pixels = 26 + 10 + 4
    elif show_labels:
      top_pixels = 20 + 10 + 4
    else:
      top_pixels = self.labelFontSize + 6

    self.leftMargin = max(0.09, left_pixels / canvas_width)
    self.rightMargin = max(0.02, 12 / canvas_width)
    self.topMargin = max(0.04, top_pixels / canvas_height)
    # Reserve the actual vertical space used by the horizontal tick labels and
    # title.  This must be kept in sync with setupFigure: a fixed pixel value
    # is not sufficient when a title has superscripts/subscripts or when the
    # configured font size changes.
    x_label_height = self.__textHeight("012345", 43, self.labelFontSize)
    x_title_height = max(
        (self.__textHeight(label, 43, self.labelFontSize)
         for label in x_labels if label),
        default=self.__textHeight("X", 43, self.labelFontSize))
    x_title_offset = (self.ratioXAxisTitleOffset if has_ratio
                      else self.mainXAxisTitleOffset)
    bottom_pixels = max(
        84,
        x_label_height + x_title_offset * self.labelFontSize
        + x_title_height + 12)
    self.bottomMargin = max(0.10, bottom_pixels / canvas_height)
    self.automaticMargins.update({
        "left": self.leftMargin,
        "right": self.rightMargin,
        "top": self.topMargin,
        "bottom": self.bottomMargin,
    })
    self.__setStyle()

  def getYAxisRangeForLayout(self, hist, source_histograms, is_ratio=False):
    """Return the final Y range used to size labels before canvases are made."""
    if is_ratio:
      ratio_limits = getattr(self.config, "ratio_limits", None)
      if ratio_limits is not None:
        return ratio_limits

    values = []
    for source in source_histograms or []:
      values.extend(source.GetBinContent(i)
                    for i in range(1, source.GetNbinsX() + 1))
    positive_values = [value for value in values if value > 0]
    content_maximum = max(positive_values) if positive_values else 1.0
    if hist.log_y and not is_ratio:
      content_minimum = (min(positive_values) if positive_values
                         else content_maximum / 1000.0)
      automatic_minimum = 0.7 * content_minimum
    else:
      automatic_minimum = min(0.0, min(values) if values else 0.0)
    automatic_maximum = 1.3 * content_maximum

    minimum = hist.y_min
    if minimum is None or ((hist.log_y and not is_ratio) and minimum <= 0):
      minimum = automatic_minimum
    maximum = hist.y_max
    if maximum is None or maximum <= 0:
      maximum = automatic_maximum
    if not hist.log_y or is_ratio:
      maximum = self.__addTopLabelClearance(minimum, maximum)
    return minimum, maximum

  def setupFigure(self, plot, hist, is_ratio=False, source_histograms=None):
    if plot is None or type(plot) is TObject:
      return

    if is_ratio:
      ratio_limits = getattr(self.config, "ratio_limits", None)
      if ratio_limits is None:
        self.__setAutomaticLimits(
            plot, hist, source_histograms, is_ratio=True)
      else:
        plot.SetMinimum(ratio_limits[0])
        plot.SetMaximum(ratio_limits[1])
    else:
      self.__setAutomaticLimits(plot, hist, source_histograms)
      if hist.y_min is not None and ((hist.y_min > 0) or (not hist.log_y and hist.y_min == 0)):
        plot.SetMinimum(hist.y_min)
      if hist.y_max is not None and hist.y_max > 0:
        plot.SetMaximum(hist.y_max)
      if not hist.log_y:
        frame = plot.GetHistogram()
        if frame is not None:
          plot.SetMaximum(self.__addTopLabelClearance(
              frame.GetMinimum(), frame.GetMaximum()))

    try:
      plot.SetTitle("" if is_ratio else hist.title)
      if hist.x_min is not None and hist.x_max is not None:
        plot.GetXaxis().SetLimits(hist.x_min, hist.x_max)

      plot.GetXaxis().SetTitle(hist.x_label)

      if is_ratio:
        x_title_offset = self.ratioXAxisTitleOffset
      elif self.plotMargins is not None:
        x_title_offset = self.legacyMainXAxisTitleOffset
      else:
        x_title_offset = self.mainXAxisTitleOffset
      plot.GetXaxis().SetTitleOffset(x_title_offset)

      plot.GetXaxis().SetTitleSize(self.labelFontSize)
      plot.GetXaxis().SetLabelSize(self.labelFontSize)

      plot.GetYaxis().SetTitle("Data/MC" if is_ratio else hist.y_label)
      plot.GetYaxis().SetTitleSize(self.labelFontSize)

      plot.GetYaxis().SetLabelSize(self.labelFontSize)

      plot.GetYaxis().CenterTitle()
      plot.GetYaxis().SetNdivisions(505)
      self.__setYAxisTitleOffset(plot, is_ratio)

    except Exception:
      warn("Couldn't set axes limits")
      return

  def __setAutomaticLimits(
      self, plot, hist, source_histograms=None, is_ratio=False):
    """Set missing bounds from all plotted contributions, with a small margin."""
    if not hasattr(plot, "GetHistogram"):
      return
    source_histogram = plot.GetHistogram()
    if source_histogram is None:
      return

    source_histograms = source_histograms or [source_histogram]

    x_min = min(h.GetXaxis().GetXmin() for h in source_histograms)
    x_max = max(h.GetXaxis().GetXmax() for h in source_histograms)
    if hist.x_min is None or hist.x_max is None:
      if x_min <= 0 or x_max <= 0:
        padding = 0.05 * (x_max - x_min)
        automatic_x_min = x_min - padding
        automatic_x_max = x_max + padding
      else:
        automatic_x_min = 0.7 * x_min
        automatic_x_max = 1.3 * x_max
      plot.GetXaxis().SetLimits(
          hist.x_min if hist.x_min is not None else automatic_x_min,
          hist.x_max if hist.x_max is not None else automatic_x_max)

    if hist.y_min is None or hist.y_max is None:
      minimum, maximum = self.getYAxisRangeForLayout(
          hist, source_histograms, is_ratio=is_ratio)
      plot.SetMinimum(minimum)
      plot.SetMaximum(maximum)

  @staticmethod
  def __addTopLabelClearance(minimum, maximum):
    """Keep ROOT's uppermost major tick label clear of the axis exponent."""
    axis_range = maximum - minimum
    if axis_range <= 0:
      return maximum

    # setupFigure uses five primary Y-axis divisions. Ask ROOT for the same
    # optimized major-label range that TGaxis will paint, then extend the
    # maximum only if its last label is too close to the frame top.
    clearance_fraction = 0.05
    for attempt in range(3):
      label_minimum = ctypes.c_double()
      label_maximum = ctypes.c_double()
      number_of_divisions = ctypes.c_int()
      division_width = ctypes.c_double()
      ROOT.THLimitsFinder.Optimize(
          minimum, maximum, 5, label_minimum, label_maximum,
          number_of_divisions, division_width)

      if attempt == 0 and not Styler.__usesAxisExponent(
          label_minimum.value, label_maximum.value, 5):
        return maximum

      axis_range = maximum - minimum
      minimum_clearance = clearance_fraction * axis_range
      current_clearance = maximum - label_maximum.value
      if current_clearance >= minimum_clearance:
        break
      maximum += ((minimum_clearance - current_clearance)
                  / (1.0 - clearance_fraction))
    return maximum

  @staticmethod
  def __usesAxisExponent(minimum, maximum, number_of_divisions):
    """Mirror TGaxis's decision to switch numeric labels to x10^n form."""
    max_digits = ROOT.TGaxis.GetMaxDigits()
    largest_magnitude = max(abs(minimum), abs(maximum))
    if largest_magnitude == 0:
      return False

    division_width = abs(maximum - minimum) / number_of_divisions
    if (division_width < 10 ** (-max_digits)
        and math.log10(largest_magnitude) < 0):
      return True

    if largest_magnitude >= 1:
      exponent = math.log10(largest_magnitude)
    else:
      exponent = math.log10(largest_magnitude * 0.0001)
    label_digits = int(exponent) + 1
    return label_digits > max_digits or label_digits < -max_digits

  def __setYAxisTitleOffset(self, plot, is_ratio):
    """Size the title gap for the widest tick label and share it across pads."""
    y_axis = plot.GetYaxis()
    required_offset = self.__requiredYAxisTitleOffset(plot)

    if is_ratio:
      y_axis.SetTitleOffset(required_offset)
      self.pendingRatioYAxis = y_axis
      self.pendingRatioTitleOffset = required_offset
      return

    shared_offset = required_offset
    if self.pendingRatioYAxis is not None:
      shared_offset = max(shared_offset, self.pendingRatioTitleOffset)
      self.pendingRatioYAxis.SetTitleOffset(shared_offset)
      self.pendingRatioYAxis = None
      self.pendingRatioTitleOffset = None
    y_axis.SetTitleOffset(shared_offset)

  def __requiredYAxisTitleOffset(self, plot):
    frame = plot.GetHistogram() if hasattr(plot, "GetHistogram") else None
    if frame is None:
      return 1.5

    minimum = frame.GetMinimum()
    maximum = frame.GetMaximum()
    if maximum <= minimum:
      return 1.5

    if ROOT.gPad is not None and ROOT.gPad.GetLogy():
      central_label_width = self.__centralLogYAxisLabelWidth(
          minimum, maximum)
    else:
      central_label_width = self.__centralYAxisLabelWidth(minimum, maximum)
    compact_capacity = self.__textWidth(
        "600", 43, self.labelFontSize)
    offset_step = 1.5 * self.labelFontSize
    return 1.35 + max(
        0.0,
        (central_label_width - compact_capacity) / offset_step)

  def __centralLogYAxisLabelWidth(self, minimum, maximum):
    if minimum <= 0 or maximum <= 0:
      return self.__textWidth("10^{2}", 43, self.labelFontSize)

    minimum_exponent = math.floor(math.log10(minimum))
    maximum_exponent = math.ceil(math.log10(maximum))
    exponents = list(range(minimum_exponent, maximum_exponent + 1))
    central_exponents = [
        exponent for index, exponent in enumerate(exponents)
        if len(exponents) == 1
        or 0.3 <= index / (len(exponents) - 1) <= 0.7]

    def label(exponent):
      if exponent == 0:
        return "1"
      if exponent == 1:
        return "10"
      return f"10^{{{exponent}}}"

    return max(
        (self.__textWidth(label(exponent), 43, self.labelFontSize)
         for exponent in central_exponents),
        default=0)

  def __centralYAxisLabelWidth(self, minimum, maximum):
    label_minimum, _, number_of_labels, division_width = (
        self.__optimizedYAxisLabels(minimum, maximum))
    if number_of_labels <= 1:
      return self.__widestYAxisLabel(minimum, maximum)

    central_widths = []
    for index in range(number_of_labels):
      relative_position = index / (number_of_labels - 1)
      if 0.3 <= relative_position <= 0.7:
        value = label_minimum + index * division_width
        central_widths.append(self.__textWidth(
            f"{value:.6g}", 43, self.labelFontSize))
    return max(central_widths, default=0)

  def __widestYAxisLabel(self, minimum, maximum):
    label_minimum, _, number_of_labels, division_width = (
        self.__optimizedYAxisLabels(minimum, maximum))
    return max(
        (self.__textWidth(
            f"{label_minimum + index * division_width:.6g}",
            43, self.labelFontSize)
         for index in range(number_of_labels)),
        default=0)

  @staticmethod
  def __optimizedYAxisLabels(minimum, maximum):
    label_minimum = ctypes.c_double()
    label_maximum = ctypes.c_double()
    optimized_divisions = ctypes.c_int()
    division_width = ctypes.c_double()
    ROOT.THLimitsFinder.Optimize(
        minimum, maximum, 5, label_minimum, label_maximum,
        optimized_divisions, division_width)
    return (label_minimum.value, label_maximum.value,
            optimized_divisions.value + 1, division_width.value)

  @staticmethod
  def __textWidth(text, font, size):
    latex = ROOT.TLatex()
    latex.SetTextFont(font)
    latex.SetTextSize(size)
    latex.SetText(0, 0, text)
    width = ctypes.c_uint()
    height = ctypes.c_uint()
    latex.GetBoundingBox(width, height)
    return width.value

  @staticmethod
  def __textHeight(text, font, size):
    latex = ROOT.TLatex()
    latex.SetTextFont(font)
    latex.SetTextSize(size)
    latex.SetText(0, 0, text)
    width = ctypes.c_uint()
    height = ctypes.c_uint()
    latex.GetBoundingBox(width, height)
    return height.value

  def setupFigure2D(self, plot, hist):
    if plot is None or type(plot) is TObject:
      return

    # Avoid TTF pixel fonts for 2D plots; use relative sizes to prevent FT_Set_Char_Size errors.
    label_size = 0.04
    pad = ROOT.gPad
    if pad is not None and pad.GetWh() > 0:
      label_size = self.labelFontSize / float(pad.GetWh())
    label_font = 42

    if hist.z_min is not None and (hist.z_min > 0):
      plot.SetMinimum(hist.z_min)
    if hist.z_max is not None and (hist.z_max > 0):
      plot.SetMaximum(hist.z_max)

    try:
      plot.SetTitle(hist.title)
      if hist.x_min is not None and hist.x_max is not None:
        plot.GetXaxis().SetRangeUser(hist.x_min, hist.x_max)
      plot.GetXaxis().SetTitle(hist.x_label)
      plot.GetXaxis().SetTitleFont(label_font)
      plot.GetXaxis().SetTitleSize(label_size)
      plot.GetXaxis().SetTitleOffset(1.0)
      plot.GetXaxis().SetLabelFont(label_font)
      plot.GetXaxis().SetLabelSize(label_size)

      if hist.y_min is not None and hist.y_max is not None:
        plot.GetYaxis().SetRangeUser(hist.y_min, hist.y_max)
      plot.GetYaxis().SetTitle(hist.y_label)
      plot.GetYaxis().SetTitleFont(label_font)
      plot.GetYaxis().SetTitleSize(label_size)
      plot.GetYaxis().SetTitleOffset(1.2)
      plot.GetYaxis().CenterTitle()
      plot.GetYaxis().SetLabelFont(label_font)
      plot.GetYaxis().SetLabelSize(label_size)
      plot.GetYaxis().SetNdivisions(505)

      plot.GetZaxis().SetTitle(hist.z_label)
      plot.GetZaxis().SetTitleFont(label_font)
      plot.GetZaxis().SetTitleSize(label_size)
      plot.GetZaxis().SetTitleOffset(1.3)
      plot.GetZaxis().CenterTitle()
      plot.GetZaxis().SetLabelFont(label_font)
      plot.GetZaxis().SetLabelSize(label_size)
      plot.GetZaxis().SetNdivisions(505)

    except Exception:
      warn("Couldn't set axes limits")
      return

  def setupUncertaintyHistogram(self, hist):
    if hasattr(self.config, "background_uncertainty"):
      color = self.config.background_uncertainty_color
    else:
      color = ROOT.kBlack

    if hasattr(self.config, "background_uncertainty_alpha"):
      alpha = self.config.background_uncertainty_alpha
    else:
      alpha = 0.3

    if hasattr(self.config, "background_uncertainty_style"):
      style = self.config.background_uncertainty_style
    else:
      style = 3244

    hist.SetFillColorAlpha(color, alpha)
    hist.SetLineColor(color)
    hist.SetFillStyle(style)
    hist.SetMarkerSize(0.0)
