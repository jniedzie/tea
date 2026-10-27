from ROOT import TCanvas, gStyle, THStack, TEfficiency, TMultiGraph
import ROOT
import os
import os.path
import copy
from array import array
from typing import Any

from Sample import SampleType
from Styler import Styler
from HistogramNormalizer import HistogramNormalizer, NormalizationType
from CmsLabelsManager import CmsLabelsManager
from PlotCanvas import save_canvas
from Logger import info, warn, error, fatal, install_root_warning_collector, ProgressBar


class HistogramPlotter:
  def __init__(self, config):
    install_root_warning_collector()
    gStyle.SetOptStat(0)

    self.config = config

    self.normalizer = HistogramNormalizer(config)
    self.styler = Styler(config)
    self.cmsLabelsManager = CmsLabelsManager(config)

    self.legends = {}
    self.show_signal_stat_uncertainty = getattr(config, "show_signal_stat_uncertainty", False)
    self.signal_uncertainties = {}

    self.stacks = {sample_type: self.__getStackDict(sample_type) for sample_type in SampleType}

    if hasattr(self.config, "histogramsRatio"):
      self.ratiohists = {sample_type: self.__getRatioDict(sample_type) for sample_type in SampleType}
    else:
      self.ratiohists = None

    self.histsAndSamples = {}

    self.data_included = any(sample.type == SampleType.data for sample in self.config.samples)
    self.backgrounds_included = any(sample.type == SampleType.background for sample in self.config.samples)

    self.show_ratios = self.backgrounds_included and self.data_included and self.config.show_ratio_plots

    self.histosamples = []
    self.ratiosamples = []
    self.histosamples2D = []
    self.profilesamples2D = []
    # Check duplicates without scanning every histogram from earlier samples.
    self.histosample_keys = set()
    self.histosample2D_keys = set()
    self.ratiosample_keys = set()
    self.data_integral = {}
    self.total_backgrounds_integral = {}

    if hasattr(self.config, "bkgRawEventsThreshold"):
      self.bkgRawEventsThreshold = self.config.bkgRawEventsThreshold
    else:
      self.bkgRawEventsThreshold = 0

    self.output_formats = ["pdf"]
    if hasattr(self.config, "output_formats"):
      self.output_formats = self.config.output_formats

    if not os.path.exists(self.config.output_path):
      os.makedirs(self.config.output_path)
    info(f"Output directory: {os.path.abspath(self.config.output_path)}")

  def __histosampleExists(self, hist, sample):
    return (hist.getName(), sample.name) in self.histosample_keys

  def __histosample2DExists(self, hist, sample):
    return (hist.getName(), sample.name) in self.histosample2D_keys

  def __histosampleRatioExists(self, hist_pass, hist_tot, sample):
    key = (hist_pass.getName() + "_pass", hist_tot.getName() + "_tot", sample.name)
    return key in self.ratiosample_keys

  def __profilesample2DExists(self, profile: Any, sample: Any) -> bool:
    for p, s in self.profilesamples2D:
      if p.getName() == profile.getName() and s.name == sample.name:
        return True
    return False

  def addHistosample(self, hist, sample, input_file):
    if self.__histosampleExists(hist, sample):
      # warn(f"Skipping adding histogram {hist.getName()} for sample {sample.name} because it already exists")
      return
    hist.load(input_file)

    if not hist.isGood():
      return

    if sample.type == SampleType.background and hist.entries < self.bkgRawEventsThreshold:
      return

    self.histosamples.append((copy.deepcopy(hist), copy.deepcopy(sample)))
    self.histosample_keys.add((hist.getName(), sample.name))

  def addHistosample2D(self, hist, sample, input_file):
    if self.__histosample2DExists(hist, sample):
      warn(f"Skipping adding 2D histogram {hist.getName()} for sample {sample.name} because it already exists")
      return
    hist.load(input_file)

    if not hist.isGood():
      warn(f"Some histograms were missing for some of the samples.")
      return

    self.histosamples2D.append((copy.deepcopy(hist), sample))
    self.histosample2D_keys.add((hist.getName(), sample.name))

  def addProfilesample2D(self, profile: Any, sample: Any, input_file: Any) -> None:
    if self.__profilesample2DExists(profile, sample):
      warn(f"Skipping adding 2D profile {profile.getName()} for sample {sample.name} because it already exists")
      return
    profile.load(input_file)

    if not profile.isGood():
      warn("Some 2D profiles were missing for some of the samples.")
      return

    self.profilesamples2D.append((copy.deepcopy(profile), sample))

  def addHistosampleRatio(self, input_hist_pass, input_hist_tot, sample, input_file):
    if self.__histosampleRatioExists(input_hist_pass, input_hist_tot, sample):
      warn(
        f"Skipping adding ratio histogram for {input_hist_pass.getName()} / {input_hist_tot.getName()} for sample {sample.name} because it already exists"
      )
      return
    input_hist_pass.load(input_file)
    input_hist_tot.load(input_file)

    if not input_hist_pass.isGood():
      warn(f"No good histogram {input_hist_pass.getName()} for sample {sample.name}")
      return
    if not input_hist_tot.isGood():
      warn(f"No good histogram {input_hist_tot.getName()} for sample {sample.name}")
      return

    hist_pass = copy.deepcopy(input_hist_pass)
    hist_pass.name = input_hist_pass.getName() + "_pass"
    hist_tot = copy.deepcopy(input_hist_tot)
    hist_tot.name = input_hist_tot.getName() + "_tot"

    self.ratiosamples.append((copy.deepcopy(hist_pass), copy.deepcopy(hist_tot), sample))
    self.ratiosample_keys.add((hist_pass.getName(), hist_tot.getName(), sample.name))

  def setupLegends(self):
    already_added = []
    labels = {}

    for hist, sample in self.histosamples:
      labels[hist.getName()] = hist.legend_label
      if hist.getName() not in self.legends.keys():
        self.legends[hist.getName()] = {}

      if sample.custom_legend is not None:
        self.legends[hist.getName()][sample.name] = sample.custom_legend.getRootLegend()
      elif (hist.getName(), sample.type) not in already_added:
        legend = self.config.legends[sample.type] if hasattr(self.config, "legends") else None
        self.legends[hist.getName()][sample.type] = legend.getRootLegend() if legend is not None else None
        already_added.append((hist.getName(), sample.type))

    for hist_pass, hist_tot, sample in self.ratiosamples:
      hist = copy.deepcopy(hist_pass)
      hist.name = hist.name.replace("pass", "ratio")
      labels[hist.getName()] = hist.legend_label
      if hist.getName() not in self.legends.keys():
        self.legends[hist.getName()] = {}

      if sample.custom_legend is not None:
        self.legends[hist.getName()][sample.name] = sample.custom_legend.getRootLegend()
      elif (hist.getName(), sample.type) not in already_added:
        self.legends[hist.getName()][sample.type] = self.config.legends[sample.type].getRootLegend()
        already_added.append((hist.getName(), sample.type))

    # The selection describes the whole plot. Put it in the highest legend
    # once, while preserving each legend's own sample-group title.
    for name, label in labels.items():
      visible = [legend for legend in self.legends[name].values() if legend is not None]
      if label and visible:
        legend = max(visible, key=lambda item: item.GetY2())
        title = legend.GetHeader()
        legend.SetHeader(f"{title} ({label})" if title else label)

  def __getDataIntegral(self, input_hist):
    if input_hist.getName() in self.data_integral.keys():
      return self.data_integral[input_hist.getName()]
    return None

  def __getBackgroundIntegral(self, input_hist):
    if input_hist.getName() in self.total_backgrounds_integral.keys():
      return self.total_backgrounds_integral[input_hist.getName()]
    return None

  def __sortHistosamples(self):
    if hasattr(self.config, "custom_stacks_order"):
      try:
        self.histosamples.sort(key=lambda x: self.config.custom_stacks_order.index(x[1].name))
      except ValueError:
        error("Couldn't sort histograms by custom order. Falling back to default order.")

        for _, sample in self.histosamples:
          if sample.name not in self.config.custom_stacks_order:
            error(f"Couldn't find sample {sample.name} in custom order list.")

        self.histosamples.sort(key=lambda x: x[1].cross_section, reverse=False)
    else:
      self.histosamples.sort(key=lambda x: x[1].cross_section, reverse=False)

  def buildStacks(self):
    self.__sortHistosamples()

    # calculate valid histogram specific background cross sections
    for n, (hist, sample) in enumerate(self.histosamples):
      if sample.type != SampleType.background:
        continue

      hist.setup(sample)
      hist_normalized = self.normalizer.getBackgroundNormalizedToLumi(hist, sample)
      # Density plots divide by bin width in setup. Match the displayed area,
      # retaining the ordinary bin sum for count plots and other modes.
      integral = (
        hist_normalized.Integral("width")
        if hist.norm_type in (NormalizationType.to_background, NormalizationType.to_data) and hist.scale_by_bin_width
        else hist_normalized.Integral()
      )
      if hist.getName() in self.total_backgrounds_integral:
        self.total_backgrounds_integral[hist.getName()] += integral
      else:
        self.total_backgrounds_integral[hist.getName()] = integral

    # normalize and setup data for data integral
    for hist, sample in self.histosamples:
      if sample.type != SampleType.data:
        continue

      if not hist.isGood():
        warn(f"Some histograms were missing for some of the samples.")
        continue

      hist.setup(sample)
      self.data_integral[hist.getName()] = (
        hist.hist.Integral("width") if hist.scale_by_bin_width else hist.hist.Integral()
      )

    # normalize background
    for hist, sample in self.histosamples:
      if sample.type != SampleType.background:
        continue

      if not hist.isGood():
        warn(f"Some histograms were missing for some of the samples.")
        continue

      self.normalizer.normalize(hist, sample, self.__getDataIntegral(hist), self.__getBackgroundIntegral(hist))

    self.normalizer.print_to_data_scales()

    # normalize signal
    for hist, sample in self.histosamples:
      if sample.type != SampleType.signal:
        continue

      if not hist.isGood():
        warn(f"Some histograms were missing for some of the samples.")
        continue

      hist.setup(sample)

      self.normalizer.normalize(hist, sample, self.__getDataIntegral(hist), self.__getBackgroundIntegral(hist))

    for hist, sample in self.histosamples:
      if not hist.isGood():
        warn(f"Some histograms were missing for some of the samples.")
        continue

      if hist.getName().endswith("_ratio") or hist.getName().endswith("_denom"):
        continue

      self.stacks[sample.type][hist.getName()].Add(hist.hist)

      key = sample.type if sample.custom_legend is None else sample.name
      opt = self.config.legends[sample.type].options if hasattr(self.config, "legends") else None

      options = opt if sample.custom_legend is None else sample.custom_legend.options

      if sample.legend_description != "" and self.legends[hist.getName()][key] is not None:
        self.legends[hist.getName()][key].AddEntry(hist.hist, sample.legend_description, options)

  def buildStacksRatio(self):
    if not hasattr(self.config, "histogramsRatio"):
      return

    for hist_pass, hist_tot, sample in self.ratiosamples:
      self.normalizer.normalize(
        hist_pass, sample, self.__getDataIntegral(hist_pass), self.__getBackgroundIntegral(hist_pass)
      )
      self.normalizer.normalize(
        hist_tot, sample, self.__getDataIntegral(hist_tot), self.__getBackgroundIntegral(hist_tot)
      )

      hist_pass.setup(sample)
      hist_tot.setup(sample)

      hist_ratio = copy.deepcopy(hist_pass)
      hist_ratio.name = hist_ratio.name.replace("pass", "ratio")
      hist = TEfficiency()
      hist.SetName(hist_ratio.getName())
      hist.SetTitle(hist_ratio.getName())

      hist_pass.hist.Sumw2(False)
      hist_tot.hist.Sumw2(False)
      hist.SetPassedHistogram(hist_pass.hist, "f")
      hist.SetTotalHistogram(hist_tot.hist, "f")

      graph = hist.CreateGraph()
      hist_ratio.hist = graph

      hist_ratio.setupRatio(sample)
      self.ratiohists[sample.type][hist_ratio.getName()].Add(hist_ratio.hist)

      key = sample.type if sample.custom_legend is None else sample.name
      self.legends[hist_ratio.getName()][key].AddEntry(
        hist_ratio.hist, sample.legend_description, self.config.legends[sample.type].options
      )

  def __drawLineAtOne(self, canvas, ratio_stack):
    if not self.show_ratios or ratio_stack is None:
      return

    ratio_histogram = ratio_stack.GetHistogram()
    if ratio_histogram is None:
      return
    x_axis = ratio_histogram.GetXaxis()
    x_min = x_axis.GetXmin()
    x_max = x_axis.GetXmax()

    global line
    line = ROOT.TGraph(2, array("d", [x_min, x_max]), array("d", [1.0, 1.0]))
    line.SetLineColor(ROOT.kBlack)
    line.SetLineStyle(ROOT.kDashed)
    line.SetBit(ROOT.TGraph.kClipFrame)

    canvas.cd(2)
    line.Draw("L same")

  def __drawRatioPlot(self, canvas, hist):
    if not self.show_ratios:
      return None

    global ratio_hist
    ratio_hist = self.__getRatioStack(hist)
    if ratio_hist:
      canvas.cd(2)
      self.styler.prepareDisplayFrame(ratio_hist)
      ratio_hist.Draw("p e0")
      ratio_histograms = ratio_hist.GetStack()
      source_histograms = [ratio_histograms.Last()] if ratio_histograms and ratio_histograms.GetSize() > 0 else None
      self.styler.setupFigure(ratio_hist, hist, is_ratio=True, source_histograms=source_histograms)
    return ratio_hist

  def __drawUncertainties(self, canvas, hist):
    global background_uncertainty_hist
    background_uncertainty_hist = self.__getBackgroundUncertaintyHist(hist)
    if background_uncertainty_hist is None:
      return

    canvas.cd(1)
    self.styler.setupUncertaintyHistogram(background_uncertainty_hist)
    background_uncertainty_hist.Draw("same e2")

    if not self.show_ratios:
      return

    global ratio_uncertainty
    ratio_uncertainty = background_uncertainty_hist.Clone("ratio_uncertainty_" + hist.getName())
    ratio_uncertainty.Divide(ratio_uncertainty)

    canvas.cd(2)
    ratio_uncertainty.Draw("same e2")

  def __drawLegends(self, canvas, hist):
    canvas.cd(1)

    if hist.getName() not in self.legends:
      warn(f"Couldn't find legends for some histograms.")
      return

    for legend in self.legends[hist.getName()].values():
      if legend is not None:
        legend.Draw()

  def __getSignalUncertaintyHistograms(self, hist):
    if not self.show_signal_stat_uncertainty:
      return []
    options = self.config.plotting_options[SampleType.signal].lower()
    if "e" in options.replace("nostack", "").replace("same", ""):
      return []  # The configured draw option already shows error bars.
    stack = self.stacks[SampleType.signal][hist.getName()]
    if stack.GetNhists() == 0:
      return []
    # Overlaid curves keep their own errors; stacked boundaries use the
    # cumulative statistical errors, with the same heights as the drawing.
    return list(stack.GetHists() if "nostack" in options else stack.GetStack())

  def __drawSignalUncertainties(self, canvas, hist):
    self.signal_uncertainties[hist.getName()] = []
    canvas.cd(1)
    for source in self.__getSignalUncertaintyHistograms(hist):
      graph = self._hist_to_graph(source, horizontal_errors=False)
      graph.SetLineColor(source.GetLineColor())
      graph.SetLineWidth(source.GetLineWidth())
      graph.SetMarkerSize(0)
      graph.Draw("same Z")
      self.signal_uncertainties[hist.getName()].append(graph)

  def _hist_to_graph(self, hist, horizontal_errors=True):
    n = hist.GetNbinsX()
    x = []
    y = []
    ex = []
    ey_up = []
    ey_down = []

    for i in range(1, n + 1):
      x.append(hist.GetBinCenter(i))
      y.append(hist.GetBinContent(i))
      ex.append(hist.GetBinWidth(i) / 2 if horizontal_errors else 0)
      ey_up.append(hist.GetBinErrorUp(i))
      ey_down.append(hist.GetBinErrorLow(i))

    return ROOT.TGraphAsymmErrors(
      n, array("d", x), array("d", y), array("d", ex), array("d", ex), array("d", ey_down), array("d", ey_up)
    )

  def __drawHists(self, canvas, hist):
    canvas.cd(1)

    firstPlotted = False

    for sample_type in SampleType:
      options = self.config.plotting_options[sample_type]
      options = f"{options} same" if firstPlotted else options
      stack = self.stacks[sample_type][hist.getName()]
      if stack.GetNhists() > 0:
        if not firstPlotted:
          self.styler.prepareDisplayFrame(stack)
        stack.Draw(options)
        firstPlotted = True

    # Apply automatic limits only after every sample has been drawn.  A
    # THStack's axis is established by its first draw, while subsequent
    # stacks (signals/data) can contain larger contributions.
    plotted_histograms = self.__getPlottedHistograms(hist)

    first_stack = next(
      (
        self.stacks[sample_type][hist.getName()]
        for sample_type in SampleType
        if self.stacks[sample_type][hist.getName()].GetNhists() > 0
      ),
      None,
    )
    if first_stack is not None:
      self.styler.setupFigure(
        first_stack,
        hist,
        source_histograms=plotted_histograms,
        error_histograms=self.__getPlottedHistograms(hist, errors_only=True),
      )

  def __drawRatioHists(self, canvas, hist):
    canvas.cd(1)

    firstPlotted = False

    for sample_type in SampleType:
      options = ""
      options = f"{options} same" if firstPlotted else options
      ratio = self.ratiohists[sample_type][hist.getName()]
      ratio.Draw(options)
      self.styler.setupFigure(ratio, hist, False)

      firstPlotted = True

  def __setup_canvas(self, canvas, hist):
    sources = self.__getPlottedHistograms(hist)
    self.styler.preparePlotLayout(
      hist,
      sources,
      canvas,
      self.show_ratios,
      legends=self.legends.get(hist.getName(), {}).values(),
    )
    has_categorical_labels = any(
      source.GetXaxis().GetLabels()
      and any(source.GetXaxis().GetBinLabel(index) for index in range(1, source.GetNbinsX() + 1))
      for source in sources
    )
    if self.show_ratios:
      canvas.Divide(1, 2)
      self.styler.setup_ratio_pad(canvas.GetPad(2))
      self.styler.setup_main_pad_with_ratio(canvas.GetPad(1))
    else:
      canvas.Divide(1, 1)
      self.styler.setup_main_pad_without_ratio(canvas.GetPad(1), has_categorical_labels)

    canvas.GetPad(1).SetLogx(hist.log_x)
    canvas.GetPad(1).SetLogy(hist.log_y)

  def __getPlottedHistograms(self, hist, errors_only=False):
    plotted_histograms = []
    for sample_type in SampleType:
      stack = self.stacks[sample_type][hist.getName()]
      if stack.GetNhists() == 0:
        continue

      options = self.config.plotting_options[sample_type].lower()
      if errors_only:
        # The background band is drawn independently of the stack options.
        if sample_type == SampleType.background:
          plotted_histograms.append(self.__getBackgroundUncertaintyHist(hist))
        elif sample_type == SampleType.signal:
          plotted_histograms.extend(self.__getSignalUncertaintyHistograms(hist))
        if "e" not in options.replace("nostack", "").replace("same", ""):
          continue
      # Components keep small contributions visible on logarithmic axes.
      # Only stacked drawing needs their sum; a nostack overlay never draws it.
      plotted_histograms.extend(item for item in stack.GetHists())
      if "nostack" not in options:
        stack_histograms = stack.GetStack()
        if stack_histograms and stack_histograms.GetSize() > 0:
          plotted_histograms.append(stack_histograms.Last())
    return plotted_histograms

  def __configureAutomaticMargins(self):
    if self.styler.plotMargins is not None:
      return

    y_ranges = []
    for hist in self.config.histograms:
      sources = self.__getPlottedHistograms(hist)
      if sources:
        y_ranges.append(
          self.styler.getYAxisRangeForLayout(
            hist,
            sources,
            error_histograms=self.__getPlottedHistograms(hist, errors_only=True),
          )
        )

      if not self.show_ratios:
        continue
      ratio_stack = self.__getRatioStack(hist)
      if ratio_stack is None or ratio_stack.GetNhists() == 0:
        continue
      ratio_sources = [item for item in ratio_stack.GetHists()]
      y_ranges.append(self.styler.getYAxisRangeForLayout(hist, ratio_sources, is_ratio=True))

    x_labels = [hist.x_label for hist in self.config.histograms]
    x_tick_labels = []
    for hist in self.config.histograms:
      for source in self.__getPlottedHistograms(hist):
        axis = source.GetXaxis()
        if not axis.GetLabels():
          continue
        x_tick_labels.extend(
          axis.GetBinLabel(index) for index in range(1, source.GetNbinsX() + 1) if axis.GetBinLabel(index)
        )
    self.styler.configureAutomaticMargins(
      y_ranges, self.config.canvas_size, x_labels, x_tick_labels=x_tick_labels, has_ratio=self.show_ratios
    )

  def drawStacks(self):
    info("Preparing plot layout...")
    self.__configureAutomaticMargins()
    for hist in ProgressBar.iterate(self.config.histograms, label="Drawing plots"):
      sources = self.__getPlottedHistograms(hist)
      if not sources:
        warn(f"Skipping plot {hist.getName()}: no selected sample has drawable entries.")
        continue
      has_categorical_labels = bool(self.styler.categoricalLabels(sources))
      canvas_size = (
        getattr(self.config, "categorical_canvas_size", self.config.canvas_size)
        if has_categorical_labels
        else self.config.canvas_size
      )
      canvas = TCanvas(hist.getName(), hist.getName(), canvas_size[0], canvas_size[1])
      self.__setup_canvas(canvas, hist)

      ratio_stack = self.__drawRatioPlot(canvas, hist)
      self.__drawHists(canvas, hist)
      self.__drawUncertainties(canvas, hist)
      self.__drawSignalUncertainties(canvas, hist)
      self.__drawLegends(canvas, hist)

      # The uncertainty band is drawn after the first stack range pass and can
      # itself enter the legend area. Re-evaluate against the drawn legend and
      # include that band, so the final rendered frame—not just the stack—is
      # legend-safe.
      first_stack = next(
        (
          self.stacks[sample_type][hist.getName()]
          for sample_type in SampleType
          if self.stacks[sample_type][hist.getName()].GetNhists() > 0
        ),
        None,
      )
      if first_stack is not None:
        final_sources = self.__getPlottedHistograms(hist)
        error_sources = self.__getPlottedHistograms(hist, errors_only=True)
        self.styler.adjustAxesForLegend(
          first_stack,
          hist,
          final_sources,
          self.legends.get(hist.getName(), {}).values(),
          canvas.GetPad(1),
          error_histograms=error_sources,
        )
        pad = canvas.GetPad(1)
        # The legend solver already paints adjusted axes. Update only pending
        # drawing changes when it left the axes alone.
        pad.Update()
        if self.show_ratios and ratio_stack is not None:
          # The main frame includes every sample and the final legend clearance.
          # Reuse its coordinates after both passes so ratio bins, labels and
          # the unity line stay aligned even when data have a shorter tail.
          x_axis = first_stack.GetXaxis()
          ratio_stack.GetXaxis().SetLimits(x_axis.GetXmin(), x_axis.GetXmax())
          ratio_pad = canvas.GetPad(2)
          ratio_pad.SetLogx(pad.GetLogx())
          ratio_pad.Modified()
          ratio_pad.Update()
          self.__drawLineAtOne(canvas, ratio_stack)
          self.styler.drawCategoricalAxis(ratio_stack, hist, final_sources, ratio_pad)
        else:
          self.styler.drawCategoricalAxis(first_stack, hist, final_sources, pad)

      # The export refreshes the finished pad, including labels and borders.
      self.cmsLabelsManager.drawLabels(canvas.GetPad(1), update=False)

      # Keep every frame border identical and on top of plotted objects.
      pad_count = 2 if self.show_ratios else 1
      for pad_index in range(1, pad_count + 1):
        pad = canvas.GetPad(pad_index)
        frame = pad.GetFrame()
        frame.SetLineWidth(1)
        frame.SetBorderSize(1)
        frame.SetBorderMode(0)
        frame.SetFillColor(0)
        frame.SetFillStyle(0)
        pad.RedrawAxis()
        self.styler.drawDeLoggifiedXAxis(hist, pad, show_labels=pad_index == pad_count)
      for output_format in self.output_formats:
        path = self.config.output_path + "/" + hist.getName() + "." + output_format
        save_canvas(canvas, path)

  def __drawObjects2D(self, objects: list[tuple[Any, Any]], object_label: str, normalize: bool) -> None:
    canvas_size = getattr(self.config, "canvas_size_2Dhists", self.config.canvas_size)

    for hist, sample in ProgressBar.iterate(objects, label=f"Drawing {object_label}s"):
      if hist.hist is None or type(hist.hist) is ROOT.TObject:
        error(f"{object_label} {hist.getName()} for sample {sample.name} is not valid.")
        continue

      if normalize:
        self.normalizer.normalize(hist, sample)

      hist_rebinned = hist.hist.Rebin2D(hist.x_rebin, hist.y_rebin)
      title = hist.getOutputName() + "_" + sample.name
      canvas = TCanvas(title, title, canvas_size[0], canvas_size[1])
      canvas.cd()
      self.styler.setup_2d_pad(canvas, square_frame=hist.comparable_axes)
      if getattr(self.config, "show_grid_2D", False):
        canvas.SetGridx(True)
        canvas.SetGridy(True)
      hist_rebinned.Draw("colz")
      self.styler.setupFigure2D(hist_rebinned, hist)
      comparable_axis_range = self.styler.getComparable2DAxisRange(hist_rebinned, hist)

      canvas.SetLogx(hist.log_x)
      canvas.SetLogy(hist.log_y)
      canvas.SetLogz(hist.log_z)
      diagonal = None
      if comparable_axis_range is not None and getattr(self.config, "show_y_equals_x_2D", False):
        minimum, maximum = comparable_axis_range
        diagonal = ROOT.TLine(minimum, minimum, maximum, maximum)
        diagonal.SetLineColor(ROOT.kBlack)
        diagonal.SetLineStyle(ROOT.kSolid)
        diagonal.Draw("same")
      canvas.Update()
      for output_format in self.output_formats:
        extension = output_format.lstrip(".")
        save_canvas(canvas, self.config.output_path + "/" + title + "." + extension)

  def drawHists2D(self):
    if hasattr(self.config, "histograms2D"):
      self.__drawObjects2D(self.histosamples2D, "2D histogram", normalize=True)

  def drawProfiles2D(self) -> None:
    if hasattr(self.config, "profiles2D"):
      self.__drawObjects2D(self.profilesamples2D, "2D profile", normalize=False)

  def drawRatioStacks(self):
    if not hasattr(self.config, "histogramsRatio"):
      return

    for hist_nom, hist_denom in ProgressBar.iterate(self.config.histogramsRatio, label="Drawing ratio plots"):
      hist_nom.name = hist_nom.getName() + "_ratio"

      canvas = TCanvas(hist_nom.getName(), hist_nom.getName(), self.config.canvas_size[0], self.config.canvas_size[1])
      self.__setup_canvas(canvas, hist_nom)

      self.__drawRatioHists(canvas, hist_nom)
      self.__drawLegends(canvas, hist_nom)
      self.cmsLabelsManager.drawLabels(canvas.GetPad(1), update=False)

      self.styler.drawDeLoggifiedXAxis(hist_nom, canvas.GetPad(1))
      path = self.config.output_path + "/" + hist_nom.getName() + ".pdf"
      save_canvas(canvas, path)

  def __get_hists_sum(self, hist, doRatio=False):
    base_sample_type = SampleType.data if doRatio else SampleType.background

    try:
      base_hist = self.stacks[base_sample_type][hist.getName()].GetHists()[0]
    except Exception:
      return None

    title = "backgrounds_" + ("sum" if doRatio else "unc") + "_" + hist.getName()
    backgrounds_sum = base_hist.Clone(title)
    backgrounds_sum.SetDirectory(0)
    backgrounds_sum.Reset()

    for background_hist in self.stacks[SampleType.background][hist.getName()].GetHists():
      backgrounds_sum.Add(background_hist)

    if not doRatio:
      return backgrounds_sum

    ratio_hist = base_hist.Clone("ratio_" + hist.getName())
    ratio_hist.Divide(backgrounds_sum)
    ratio_stack = THStack("ratio_stack_" + hist.getName(), "ratio_stack_" + hist.getName())
    ratio_stack.Add(ratio_hist)

    return ratio_stack

  def __getRatioStack(self, hist):
    return self.__get_hists_sum(hist, doRatio=True)

  def __getBackgroundUncertaintyHist(self, hist):
    uncertainty_hist = self.__get_hists_sum(hist, doRatio=False)

    if uncertainty_hist is None:
      return None

    if hist.error > 0:
      for i in range(1, uncertainty_hist.GetNbinsX() + 1):
        bin_content = uncertainty_hist.GetBinContent(i)
        stat_error = uncertainty_hist.GetBinError(i)
        syst_error = bin_content * hist.error
        uncertainty_hist.SetBinError(i, (stat_error**2 + syst_error**2) ** (1 / 2))

    return uncertainty_hist

  def __getStackDict(self, sample_type):
    hists_dict = {}

    for hist in self.config.histograms:
      title = hist.getName() + sample_type.name
      hists_dict[hist.getName()] = ROOT.THStack(title, title)

    return hists_dict

  def __getRatioDict(self, sample_type):
    hists_dict = {}

    for hist_nom, hist_denom in self.config.histogramsRatio:
      title = hist_nom.getName() + "_ratio_" + sample_type.name
      hists_dict[hist_nom.getName() + "_ratio"] = TMultiGraph(title, title)

    return hists_dict
