from Logger import warn

from ROOT import TObject, gStyle
import ROOT


class Styler:

  def __init__(self, config):
    self.config = config

    self.topMargin = 0.06
    self.bottomMargin = 0.4
    self.leftMargin = 0.16
    self.rightMargin = 0.17

    self.labelFontSize = 26
    
    self.__setStyle()

  def setup_ratio_pad(self, pad):
    pad.SetPad(0, 0, 1, 0.3)
    self.__setupPadDefaults(pad)
    pad.SetTopMargin(0)
    pad.SetBottomMargin(self.bottomMargin + 0.2)
    pad.SetLogy(False)

  def setup_main_pad_with_ratio(self, pad):
    pad.SetPad(0, 0.3, 1, 1)
    self.__setupPadDefaults(pad)
    pad.SetBottomMargin(0.0)
    pad.SetTopMargin(self.topMargin + 0.03)

  def setup_main_pad_without_ratio(self, pad):
    # pad.SetPad(0, 0.0, 1, 1)
    self.__setupPadDefaults(pad)
    pad.SetBottomMargin(0.2)
    pad.SetTopMargin(self.topMargin + 0.03)

  def __setupPadDefaults(self, pad):
    pad.SetLeftMargin(self.leftMargin)
    pad.SetBottomMargin(self.bottomMargin)
    pad.SetRightMargin(self.rightMargin)
    pad.SetTopMargin(self.topMargin)
    pad.SetTickx(0)
    pad.SetTicky(0)

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
    exponent_x_offset = -0.08 if label_outside_axes else 0.0
    exponent_y_offset = 0.01 if label_outside_axes else 0.0
    ROOT.TGaxis.SetExponentOffset(exponent_x_offset, exponent_y_offset, "y")

    gStyle.SetOptLogx(0)
    gStyle.SetOptLogy(0)
    gStyle.SetOptLogz(0)

    gStyle.SetPaperSize(20., 20.)

  def setupFigure(self, plot, hist, is_ratio=False, source_histograms=None):
    if plot is None or type(plot) is TObject:
      return

    if is_ratio:
      ratio_limits = getattr(self.config, "ratio_limits", None)
      if ratio_limits is None:
        self.__setAutomaticLimits(plot, hist, source_histograms)
      else:
        plot.SetMinimum(ratio_limits[0])
        plot.SetMaximum(ratio_limits[1])
    else:
      self.__setAutomaticLimits(plot, hist, source_histograms)
      if hist.y_min is not None and ((hist.y_min > 0) or (not hist.log_y and hist.y_min == 0)):
        plot.SetMinimum(hist.y_min)
      if hist.y_max is not None and hist.y_max > 0:
        plot.SetMaximum(hist.y_max)

    try:
      plot.SetTitle("" if is_ratio else hist.title)
      if hist.x_min is not None and hist.x_max is not None:
        plot.GetXaxis().SetLimits(hist.x_min, hist.x_max)

      plot.GetXaxis().SetTitle(hist.x_label)

      plot.GetXaxis().SetTitleOffset(1.0 if is_ratio else 1.7)

      plot.GetXaxis().SetTitleSize(self.labelFontSize)
      plot.GetXaxis().SetLabelSize(self.labelFontSize)

      plot.GetYaxis().SetTitle("Data/MC" if is_ratio else hist.y_label)
      plot.GetYaxis().SetTitleSize(self.labelFontSize)
      plot.GetYaxis().SetTitleOffset(1.5)

      plot.GetYaxis().SetLabelSize(self.labelFontSize)

      plot.GetYaxis().CenterTitle()
      plot.GetYaxis().SetNdivisions(505)

    except Exception:
      warn("Couldn't set axes limits")
      return

  def __setAutomaticLimits(self, plot, hist, source_histograms=None):
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
      values = []
      for source in source_histograms:
        values.extend(source.GetBinContent(i)
                      for i in range(1, source.GetNbinsX() + 1))
      positive_values = [value for value in values if value > 0]
      maximum = max(positive_values) if positive_values else 1.0
      if hist.log_y:
        minimum = min(positive_values) if positive_values else maximum / 1000.0
        automatic_y_min = 0.7 * minimum
      else:
        automatic_y_min = min(values) if values else 0.0
        automatic_y_min = min(0.0, automatic_y_min)
      automatic_y_max = 1.3 * maximum
      minimum = hist.y_min
      if minimum is None or (hist.log_y and minimum <= 0):
        minimum = automatic_y_min
      maximum = hist.y_max
      if maximum is None or maximum <= 0:
        maximum = automatic_y_max
      plot.SetMinimum(minimum)
      plot.SetMaximum(maximum)

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
