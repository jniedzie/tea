from Logger import warn

from ROOT import TObject, gStyle
import ctypes
import math
import ROOT


class Styler:
  mainXAxisTitleOffset = 1.15
  legacyMainXAxisTitleOffset = 1.7
  ratioXAxisTitleOffset = 1.0
  categoricalMainXAxisTitleOffset = 2.4
  categoricalRatioXAxisTitleOffset = 2.0

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
    # Updated from rendered category labels by configureAutomaticMargins.
    self.categoricalMainXAxisTitleOffsetForLayout = self.categoricalMainXAxisTitleOffset
    self.categoricalRatioXAxisTitleOffsetForLayout = self.categoricalRatioXAxisTitleOffset
    self.regularBottomMargin = self.bottomMargin
    self.categoricalBottomMargin = self.bottomMargin
    self.pendingRatioYAxis = None
    self.pendingRatioTitleOffset = None

    self.__setStyle()

  def setup_ratio_pad(self, pad):
    fraction = getattr(self, "ratioPadFraction", 0.3)
    pad.SetPad(0, 0, 1, fraction)
    self.__setupPadDefaults(pad)
    pad.SetTopMargin(0)
    margins = self.plotMargins or self.automaticMargins
    canvas_bottom_margin = margins.get("bottom", 0.18)
    if canvas_bottom_margin >= fraction:
      raise ValueError("bottom plot margin must be smaller than the ratio pad")
    bottom_margin = canvas_bottom_margin / fraction
    pad.SetBottomMargin(bottom_margin)
    pad.SetLogy(False)

  def setup_main_pad_with_ratio(self, pad):
    fraction = getattr(self, "ratioPadFraction", 0.3)
    pad.SetPad(0, fraction, 1, 1)
    self.__setupPadDefaults(pad)
    pad.SetBottomMargin(0.0)
    margins = self.plotMargins or self.automaticMargins
    canvas_top_margin = margins.get("top", 0.063)
    if canvas_top_margin >= 1 - fraction:
      raise ValueError("top plot margin must be smaller than the main pad")
    top_margin = canvas_top_margin / (1 - fraction)
    pad.SetTopMargin(top_margin)

  def setup_main_pad_without_ratio(self, pad, has_categorical_labels=False):
    # pad.SetPad(0, 0.0, 1, 1)
    self.__setupPadDefaults(pad)
    margins = self.plotMargins or self.automaticMargins
    if self.plotMargins is None:
      bottom_margin = self.categoricalBottomMargin if has_categorical_labels else self.regularBottomMargin
    else:
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

    gStyle.SetPaperSize(20.0, 20.0)

  def configureAutomaticMargins(self, y_ranges, canvas_size, x_labels=(), x_tick_labels=(), has_ratio=False):
    """Choose common left/top/right margins; bottom is measured per plot."""
    if self.plotMargins is not None:
      return

    canvas_width, canvas_height = canvas_size
    measurement_canvas = ROOT.TCanvas("tea_layout_measurement", "", canvas_width, canvas_height)
    measurement_canvas.cd()
    try:
      widest_label = max(
        (self.__widestYAxisLabel(*axis_range) for axis_range in y_ranges),
        default=self.__textWidth("1.2", 43, self.labelFontSize),
      )
      title_thickness = max(
        self.__textHeight("Events", 43, self.labelFontSize), self.__textHeight("Data/MC", 43, self.labelFontSize)
      )
    finally:
      measurement_canvas.Close()

    label_gap = 6
    title_gap = 4
    outer_gap = 8
    left_pixels = widest_label + label_gap + title_gap + title_thickness + outer_gap

    show_labels = getattr(self.config, "show_cms_labels", False)
    labels_outside = getattr(self.config, "label_outside_axes", False)
    if show_labels and labels_outside:
      top_pixels = 26 + 10 + 4
    elif show_labels:
      top_pixels = 20 + 10 + 4
    else:
      top_pixels = self.labelFontSize + 6

    self.leftMargin = max(0.09, left_pixels / canvas_width)
    # ROOT needs an active canvas to return meaningful TLatex bounding boxes.
    # The y-axis measurement canvas above is already closed at this point.
    tick_measurement_canvas = ROOT.TCanvas("tea_tick_layout_measurement", "", canvas_width, canvas_height)
    tick_measurement_canvas.cd()
    tick_label_height = max(
      (self.__textHeight(label, 43, self.labelFontSize) for label in x_tick_labels if label),
      default=0,
    )
    # Categorical labels are drawn vertically below their ticks. Their horizontal
    # extent needs real right-side canvas space, not just the standard tick gap.
    tick_side_pixels = 0.5 * tick_label_height
    self.rightMargin = max(0.02, (12 + tick_side_pixels) / canvas_width)
    self.topMargin = max(0.04, top_pixels / canvas_height)
    self.automaticMargins.update(
      {
        "left": self.leftMargin,
        "right": self.rightMargin,
        "top": self.topMargin,
        "bottom": self.bottomMargin,
      }
    )
    tick_measurement_canvas.Close()
    self.__setStyle()

  @staticmethod
  def categoricalLabels(sources):
    """Read category positions from data bins, never from the display frame."""
    labels = {}
    for source in sources:
      axis = source.GetXaxis()
      for index in range(1, source.GetNbinsX() + 1):
        label = axis.GetBinLabel(index)
        if label:
          labels[axis.GetBinCenter(index)] = str(label)
    return sorted(labels.items())

  def preparePlotLayout(self, hist, sources, canvas, has_ratio=False):
    """Only the bottom margin depends on this plot's tick labels and title."""
    canvas.cd()
    labels = [(x, label) for x, label in self.categoricalLabels(sources)
              if (hist.x_min is None or x >= hist.x_min) and (hist.x_max is None or x <= hist.x_max)]
    height = max(1, canvas.GetWh())
    title_height = self.__textHeight(hist.x_label, 43, self.labelFontSize) if hist.x_label else 0
    if labels:
      label_extent = max(self.__textWidth(label, 43, self.labelFontSize) for _, label in labels)
      bottom_pixels = label_extent + title_height + 32
    else:
      label_extent = self.__textHeight("012345", 43, self.labelFontSize)
      bottom_pixels = max(76, label_extent + title_height + 32)
    bottom = bottom_pixels / height
    if self.plotMargins is None:
      self.regularBottomMargin = self.categoricalBottomMargin = bottom
      self.automaticMargins["bottom"] = bottom
    # Enlarge the ratio pad for long labels while retaining a visible ratio
    # frame. Numeric plots keep the established 30 percent ratio pad.
    self.ratioPadFraction = max(0.3, bottom + 0.16) if has_ratio else 0.3

  @staticmethod
  def prepareDisplayFrame(stack):
    """Separate the plotting coordinates from the data's bin edges/labels.

    SetLimits alone leaves a variable-bin TAxis's edge array unchanged, which
    ROOT uses when painting. A uniform empty frame supports arbitrary display
    limits without modifying the histograms or stretching categorical bins.
    """
    sources = list(stack.GetHists())
    frame = ROOT.TH1D(stack.GetName() + "_display", "", 100,
                      min(h.GetXaxis().GetXmin() for h in sources),
                      max(h.GetXaxis().GetXmax() for h in sources))
    frame.SetDirectory(0)
    stack.SetHistogram(frame)
    ROOT.SetOwnership(frame, False)  # THStack owns its display histogram.

  def drawCategoricalAxis(self, plot, hist, sources, pad):
    labels = self.categoricalLabels(sources)
    if not labels:
      return
    pad.cd()
    axis = plot.GetXaxis()
    xmin, xmax = axis.GetXmin(), axis.GetXmax()
    left, right = pad.GetLeftMargin(), 1 - pad.GetRightMargin()
    bottom, top = pad.GetBottomMargin(), 1 - pad.GetTopMargin()
    height = max(1, pad.GetWh() * pad.GetAbsHNDC())
    label_y = bottom - 10 / height
    longest = 0
    primitives = []
    for center, label in labels:
      if not xmin <= center <= xmax:
        continue
      x = self.__projectToNdc(center, xmin, xmax, hist.log_x, left, right)
      text = ROOT.TLatex()
      text.SetTextFont(43)
      text.SetTextSize(self.labelFontSize)
      text.SetTextAngle(90)
      text.SetTextAlign(32)  # right end at the axis, centered on the bin
      text.SetNDC(True)
      primitives.append(text.DrawLatex(x, label_y, label))
      longest = max(longest, self.__textWidth(label, 43, self.labelFontSize))
      for y, direction in ((bottom, 1), (top, -1)):
        tick = ROOT.TLine()
        primitives.append(tick.DrawLineNDC(x, y, x, y + direction * 7 / height))
    if hist.x_label:
      text = ROOT.TLatex()
      text.SetTextFont(43)
      text.SetTextSize(self.labelFontSize)
      text.SetTextAlign(33)
      text.SetNDC(True)
      primitives.append(text.DrawLatex(right, label_y - (longest + 8) / height, hist.x_label))
    pad._tea_category_primitives = primitives

  def getYAxisRangeForLayout(self, hist, source_histograms, is_ratio=False):
    """Return the final Y range used to size labels before canvases are made."""
    if is_ratio:
      ratio_limits = getattr(self.config, "ratio_limits", None)
      if ratio_limits is not None:
        return ratio_limits

    values = []
    for source in source_histograms or []:
      values.extend(source.GetBinContent(i) for i in range(1, source.GetNbinsX() + 1))
    positive_values = [value for value in values if value > 0]
    content_maximum = max(positive_values) if positive_values else 1.0
    if hist.log_y and not is_ratio:
      content_minimum = min(positive_values) if positive_values else content_maximum / 1000.0
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
        self.__setAutomaticLimits(plot, hist, source_histograms, is_ratio=True)
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
          plot.SetMaximum(self.__addTopLabelClearance(frame.GetMinimum(), frame.GetMaximum()))

    try:
      plot.SetTitle("" if is_ratio else hist.title)
      if hist.x_min is not None and hist.x_max is not None:
        plot.GetXaxis().SetLimits(hist.x_min, hist.x_max)

      x_axis = plot.GetXaxis()
      x_axis.SetTitle(hist.x_label)
      source_histograms = source_histograms or [plot.GetHistogram()]
      has_categorical_labels = any(
        source and any(source.GetXaxis().GetBinLabel(index) for index in range(1, source.GetNbinsX() + 1))
        for source in source_histograms
      )
      if is_ratio:
        x_title_offset = self.ratioXAxisTitleOffset
      elif self.plotMargins is not None:
        x_title_offset = self.legacyMainXAxisTitleOffset
      else:
        x_title_offset = self.mainXAxisTitleOffset
      if has_categorical_labels:
        x_title_offset = (
          self.categoricalRatioXAxisTitleOffsetForLayout if is_ratio
          else self.categoricalMainXAxisTitleOffsetForLayout
        )
      x_axis.SetTitleOffset(x_title_offset)

      x_axis.SetTitleSize(self.labelFontSize)
      x_axis.SetLabelSize(self.labelFontSize)
      if has_categorical_labels:
        # Draw these at their original data coordinates after range selection.
        x_axis.SetLabelSize(0)
        x_axis.SetTitle("")
        x_axis.SetTickLength(0)

      plot.GetYaxis().SetTitle("Data/MC" if is_ratio else hist.y_label)
      plot.GetYaxis().SetTitleSize(self.labelFontSize)

      plot.GetYaxis().SetLabelSize(self.labelFontSize)

      plot.GetYaxis().CenterTitle()
      plot.GetYaxis().SetNdivisions(505)
      self.__setYAxisTitleOffset(plot, is_ratio)

    except Exception:
      warn("Couldn't set axes limits")
      return

  def adjustAxesForLegend(self, plot, hist, source_histograms, legends, pad):
    """Expand automatic axes just enough to keep drawn distributions out of legends.

    The solver evaluates x-only, y-only, and combined extensions.  It never
    shrinks a range and leaves plots without configured legends unchanged.
    """
    if not getattr(self.config, "auto_adjust_axes_for_legend", False):
      return
    if plot is None or pad is None or not source_histograms:
      return

    visible_legends = [legend for legend in legends if legend is not None]
    if not visible_legends:
      return

    x_axis = plot.GetXaxis()
    x_min, x_max = x_axis.GetXmin(), x_axis.GetXmax()
    # THStack.GetMinimum/GetMaximum describe its stacked contents, rather than
    # the visible frame range. The frame is what the legend can overlap.
    frame = plot.GetHistogram() if hasattr(plot, "GetHistogram") else None
    y_min = frame.GetMinimum() if frame is not None else plot.GetMinimum()
    y_max = frame.GetMaximum() if frame is not None else plot.GetMaximum()
    if x_max <= x_min or y_max <= y_min:
      return
    if (hist.log_x and x_min <= 0) or (hist.log_y and y_min <= 0):
      return

    left, right = pad.GetLeftMargin(), 1.0 - pad.GetRightMargin()
    bottom, top = pad.GetBottomMargin(), 1.0 - pad.GetTopMargin()
    if right <= left or top <= bottom:
      return

    legend_boxes = []
    for legend in visible_legends:
      # Before Draw(), ROOT leaves Get*NDC() at zero even though the TLegend
      # constructor has stored valid NDC coordinates in GetX*()/GetY*().
      x1, x2 = legend.GetX1NDC(), legend.GetX2NDC()
      y1, y2 = legend.GetY1NDC(), legend.GetY2NDC()
      if x1 == x2 or y1 == y2:
        x1, x2 = legend.GetX1(), legend.GetX2()
        y1, y2 = legend.GetY1(), legend.GetY2()
      x1, x2 = sorted((x1, x2))
      y1, y2 = sorted((y1, y2))
      # ROOT does not enlarge TLegend's NDC box when a label is wider than
      # the configured rectangle: it paints the text outside the box. Reserve
      # that rendered footprint too, otherwise a narrow upper-right legend
      # still overlaps the high-x distribution.
      x2 = max(x2, x1 + self.__legendTextWidthNdc(legend, pad))
      x1, x2 = max(left, x1), min(right, x2)
      y1, y2 = max(bottom, y1), min(top, y2)
      if x2 > x1 and y2 > y1:
        legend_boxes.append((x1, y1, x2, y2))
    if not legend_boxes:
      return

    # Expand toward the legend horizontally, or leave room above the filled
    # distributions vertically. Fixed endpoints remain authoritative.
    legend_x_center = sum((box[0] + box[2]) / 2 for box in legend_boxes) / len(legend_boxes)
    grow_x_upper = legend_x_center >= (left + right) / 2

    extensions = [index / 100.0 for index in range(101)] + [1.5, 2.0, 3.0]
    # A vertical expansion changes the apparent peak height, especially on a
    # logarithmic axis. Prefer equally small horizontal whitespace and use y
    # only when it is materially cheaper or needed with x.
    y_extension_penalty = 1.75 if hist.log_y else 1.25
    x_range_is_fixed = hist.x_max is not None if grow_x_upper else hist.x_min is not None
    x_extensions = (0.0,) if x_range_is_fixed else extensions
    transform_y = math.log10 if hist.log_y else lambda value: value
    low, high = transform_y(y_min), transform_y(y_max)
    # Cache the actual drawn envelope, including stacked totals and errors.
    bins = []
    for source in source_histograms:
      axis = source.GetXaxis()
      for index in range(1, source.GetNbinsX() + 1):
        value = source.GetBinContent(index) + source.GetBinError(index)
        if value > y_min:
          bins.append((axis.GetBinLowEdge(index), axis.GetBinUpEdge(index), transform_y(value)))
    best = None
    # For each horizontal extension solve the required y maximum directly in
    # screen coordinates. This avoids both grid-sized overshoots and silent
    # failures when the required y extension exceeds the candidate grid.
    for x_extension in x_extensions:
      candidate_x_min, candidate_x_max = self.__extendAxisRange(
        x_min, x_max, x_extension, grow_x_upper, hist.log_x
      )
      required_high = high
      for bin_low, bin_high, value in bins:
        if bin_high <= candidate_x_min or bin_low >= candidate_x_max:
          continue
        x1 = self.__projectToNdc(max(bin_low, candidate_x_min), candidate_x_min, candidate_x_max,
                                hist.log_x, left, right)
        x2 = self.__projectToNdc(min(bin_high, candidate_x_max), candidate_x_min, candidate_x_max,
                                hist.log_x, left, right)
        for lx1, ly1, lx2, _ in legend_boxes:
          if x2 < lx1 - 0.012 or x1 > lx2 + 0.012:
            continue
          fraction = (ly1 - 0.012 - bottom) / (top - bottom)
          required_high = max(required_high, low + (value - low) / fraction) if fraction > 0 else math.inf
      if not math.isfinite(required_high) or (hist.log_y and required_high > 300):
        continue
      if hist.y_max is not None and required_high > high:
        continue
      y_extension = (required_high - high) / (high - low)
      score = x_extension ** 2 + (y_extension_penalty * y_extension) ** 2
      if best is None or score < best[0]:
        best = (score, candidate_x_min, candidate_x_max,
                10 ** required_high if hist.log_y else required_high)
    if best is not None:
      _, candidate_x_min, candidate_x_max, candidate_y_max = best
      if self.__legendOverlapsDistributions(
        source_histograms, legend_boxes, candidate_x_min, candidate_x_max,
        y_min, candidate_y_max, hist.log_x, hist.log_y, left, right, bottom, top,
      ):
        warn("Legend clearance could not be satisfied for " + hist.name)
        return
      x_axis.SetLimits(candidate_x_min, candidate_x_max)
      plot.SetMinimum(y_min)
      plot.SetMaximum(candidate_y_max)
      if frame is not None:
        frame.GetXaxis().SetLimits(candidate_x_min, candidate_x_max)
        frame.SetMinimum(y_min)
        frame.SetMaximum(candidate_y_max)
      pad.Modified()
      return
    warn("Configured axis limits leave no room for the legend in " + hist.name)

  def __legendTextWidthNdc(self, legend, pad):
    """Return the NDC width required by the widest visible legend label."""
    labels = []
    primitives = legend.GetListOfPrimitives()
    if primitives:
      for primitive in primitives:
        if hasattr(primitive, "GetLabel"):
          label = primitive.GetLabel()
          if label:
            labels.append(str(label))
    if not labels:
      return legend.GetX2NDC() - legend.GetX1NDC()

    text_size = legend.GetTextSize()
    canvas_width = pad.GetWw() * pad.GetAbsWNDC()
    if canvas_width <= 0 and pad.GetCanvas():
      canvas_width = pad.GetCanvas().GetWw()
    canvas_width = max(canvas_width, 1)
    # Font 43 uses pixels; other ROOT fonts use the pad-height fraction.
    if text_size <= 1.0:
      canvas_height = pad.GetWh()
      if canvas_height <= 0 and pad.GetCanvas():
        canvas_height = pad.GetCanvas().GetWh()
      text_size *= max(canvas_height, 1)
    pad.cd()
    font = legend.GetTextFont() // 10 * 10 + 3  # measure using pixel precision
    text_pixels = max(self.__textWidth(label, font, text_size) for label in labels)
    box_width = abs(legend.GetX2() - legend.GetX1())
    return box_width * legend.GetMargin() + (text_pixels + 8) / canvas_width

  @staticmethod
  def __extendAxisRange(minimum, maximum, extension, grow_upper, logarithmic):
    if extension == 0:
      return minimum, maximum
    if logarithmic:
      log_minimum, log_maximum = math.log10(minimum), math.log10(maximum)
      span = log_maximum - log_minimum
      if grow_upper:
        log_maximum += extension * span
      else:
        log_minimum -= extension * span
      return 10 ** log_minimum, 10 ** log_maximum
    span = maximum - minimum
    if grow_upper:
      maximum += extension * span
    else:
      minimum -= extension * span
    return minimum, maximum

  @staticmethod
  def __projectToNdc(value, minimum, maximum, logarithmic, ndc_minimum, ndc_maximum):
    if logarithmic:
      if value <= 0:
        return ndc_minimum
      value, minimum, maximum = math.log10(value), math.log10(minimum), math.log10(maximum)
    return ndc_minimum + (value - minimum) / (maximum - minimum) * (ndc_maximum - ndc_minimum)

  def __legendOverlapsDistributions(
      self, source_histograms, legend_boxes, x_min, x_max, y_min, y_max,
      log_x, log_y, left, right, bottom, top,
  ):
    # Leave one percent of the drawable pad as a visual buffer around legends.
    clearance = 0.01
    for source in source_histograms:
      axis = source.GetXaxis()
      for bin_index in range(1, source.GetNbinsX() + 1):
        if axis.GetBinUpEdge(bin_index) <= x_min or axis.GetBinLowEdge(bin_index) >= x_max:
          continue
        value = source.GetBinContent(bin_index) + source.GetBinError(bin_index)
        if value <= y_min:
          continue
        x1 = self.__projectToNdc(axis.GetBinLowEdge(bin_index), x_min, x_max, log_x, left, right)
        x2 = self.__projectToNdc(axis.GetBinUpEdge(bin_index), x_min, x_max, log_x, left, right)
        y2 = self.__projectToNdc(value, y_min, y_max, log_y, bottom, top)
        for legend_x1, legend_y1, legend_x2, legend_y2 in legend_boxes:
          if x2 < legend_x1 - clearance or x1 > legend_x2 + clearance:
            continue
          if y2 >= legend_y1 - clearance and bottom <= legend_y2 + clearance:
            return True
    return False

  def __setAutomaticLimits(self, plot, hist, source_histograms=None, is_ratio=False):
    """Set missing bounds from all plotted contributions, with a small margin."""
    if not hasattr(plot, "GetHistogram"):
      return
    source_histogram = plot.GetHistogram()
    if source_histogram is None:
      return

    source_histograms = source_histograms or [source_histogram]

    occupied_x_ranges = []
    for source in source_histograms:
      occupied_bins = [
        bin_index
        for bin_index in range(1, source.GetNbinsX() + 1)
        if source.GetBinContent(bin_index) != 0
      ]
      if occupied_bins:
        axis = source.GetXaxis()
        occupied_x_ranges.append(
          (axis.GetBinLowEdge(occupied_bins[0]), axis.GetBinUpEdge(occupied_bins[-1]))
        )

    # A categorical axis has one immutable physical bin per label. Changing
    # its numeric limits shifts ROOT's labels relative to those bins, so only
    # continuous histograms receive occupied-bin automatic x ranges.
    has_categorical_labels = any(
      any(source.GetXaxis().GetBinLabel(index) for index in range(1, source.GetNbinsX() + 1))
      for source in source_histograms
    )

    # Histogram booking often reserves a broad diagnostic domain.  Frame the
    # populated bins instead; an empty histogram still falls back to booking.
    if occupied_x_ranges:
      x_min = min(x_range[0] for x_range in occupied_x_ranges)
      x_max = max(x_range[1] for x_range in occupied_x_ranges)
    else:
      x_min = min(h.GetXaxis().GetXmin() for h in source_histograms)
      x_max = max(h.GetXaxis().GetXmax() for h in source_histograms)
    if not has_categorical_labels and (hist.x_min is None or hist.x_max is None):
      if x_min <= 0 or x_max <= 0:
        padding = 0.05 * (x_max - x_min)
        automatic_x_min = x_min - padding
        automatic_x_max = x_max + padding
      else:
        automatic_x_min = 0.7 * x_min
        automatic_x_max = 1.3 * x_max
      plot.GetXaxis().SetLimits(
        hist.x_min if hist.x_min is not None else automatic_x_min,
        hist.x_max if hist.x_max is not None else automatic_x_max,
      )

    if hist.y_min is None or hist.y_max is None:
      minimum, maximum = self.getYAxisRangeForLayout(hist, source_histograms, is_ratio=is_ratio)
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
        minimum, maximum, 5, label_minimum, label_maximum, number_of_divisions, division_width
      )

      if attempt == 0 and not Styler.__usesAxisExponent(label_minimum.value, label_maximum.value, 5):
        return maximum

      axis_range = maximum - minimum
      minimum_clearance = clearance_fraction * axis_range
      current_clearance = maximum - label_maximum.value
      if current_clearance >= minimum_clearance:
        break
      maximum += (minimum_clearance - current_clearance) / (1.0 - clearance_fraction)
    return maximum

  @staticmethod
  def __usesAxisExponent(minimum, maximum, number_of_divisions):
    """Mirror TGaxis's decision to switch numeric labels to x10^n form."""
    max_digits = ROOT.TGaxis.GetMaxDigits()
    largest_magnitude = max(abs(minimum), abs(maximum))
    if largest_magnitude == 0:
      return False

    division_width = abs(maximum - minimum) / number_of_divisions
    if division_width < 10 ** (-max_digits) and math.log10(largest_magnitude) < 0:
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
      central_label_width = self.__centralLogYAxisLabelWidth(minimum, maximum)
    else:
      central_label_width = self.__centralYAxisLabelWidth(minimum, maximum)
    compact_capacity = self.__textWidth("600", 43, self.labelFontSize)
    offset_step = 1.5 * self.labelFontSize
    return 1.35 + max(0.0, (central_label_width - compact_capacity) / offset_step)

  def __centralLogYAxisLabelWidth(self, minimum, maximum):
    if minimum <= 0 or maximum <= 0:
      return self.__textWidth("10^{2}", 43, self.labelFontSize)

    minimum_exponent = math.floor(math.log10(minimum))
    maximum_exponent = math.ceil(math.log10(maximum))
    exponents = list(range(minimum_exponent, maximum_exponent + 1))
    central_exponents = [
      exponent
      for index, exponent in enumerate(exponents)
      if len(exponents) == 1 or 0.3 <= index / (len(exponents) - 1) <= 0.7
    ]

    def label(exponent):
      if exponent == 0:
        return "1"
      if exponent == 1:
        return "10"
      return f"10^{{{exponent}}}"

    return max((self.__textWidth(label(exponent), 43, self.labelFontSize) for exponent in central_exponents), default=0)

  def __centralYAxisLabelWidth(self, minimum, maximum):
    label_minimum, _, number_of_labels, division_width = self.__optimizedYAxisLabels(minimum, maximum)
    if number_of_labels <= 1:
      return self.__widestYAxisLabel(minimum, maximum)

    central_widths = []
    for index in range(number_of_labels):
      relative_position = index / (number_of_labels - 1)
      if 0.3 <= relative_position <= 0.7:
        value = label_minimum + index * division_width
        central_widths.append(self.__textWidth(f"{value:.6g}", 43, self.labelFontSize))
    return max(central_widths, default=0)

  def __widestYAxisLabel(self, minimum, maximum):
    label_minimum, _, number_of_labels, division_width = self.__optimizedYAxisLabels(minimum, maximum)
    return max(
      (
        self.__textWidth(f"{label_minimum + index * division_width:.6g}", 43, self.labelFontSize)
        for index in range(number_of_labels)
      ),
      default=0,
    )

  @staticmethod
  def __optimizedYAxisLabels(minimum, maximum):
    label_minimum = ctypes.c_double()
    label_maximum = ctypes.c_double()
    optimized_divisions = ctypes.c_int()
    division_width = ctypes.c_double()
    ROOT.THLimitsFinder.Optimize(minimum, maximum, 5, label_minimum, label_maximum, optimized_divisions, division_width)
    return (label_minimum.value, label_maximum.value, optimized_divisions.value + 1, division_width.value)

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
