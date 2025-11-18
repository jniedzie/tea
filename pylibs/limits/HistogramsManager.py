from Logger import warn, info, fatal
from Sample import Sample, SampleType
from HistogramNormalizer import HistogramNormalizer, NormalizationType
from DatacardsProcessor import DatacardsProcessor
from Histogram import Histogram, Histogram2D
from ABCDHelper import ABCDHelper

import ROOT

import copy
import os


class HistogramsManager:
  def __init__(self, config, input_files, datacard_file_name):
    self.config = config
    self.input_files = input_files

    self.normalizer = HistogramNormalizer(config)
    self.datacardsProcessor = DatacardsProcessor(config, datacard_file_name)
    self.abcd_helper = ABCDHelper(config)

    self.stacks = {sample_type: self.__getStackDict(sample_type) for sample_type in SampleType}

    self.histsAndSamples = {}

    self.data_included = any(sample.type == SampleType.data for sample in self.config.samples)
    self.backgrounds_included = any(sample.type == SampleType.background for sample in self.config.samples)

    self.histosamples = []

    if not os.path.exists(os.path.dirname(self.config.datacards_output_path)):
      os.makedirs(os.path.dirname(self.config.datacards_output_path))

    if not os.path.exists(os.path.dirname(self.config.plots_output_path)):
      os.makedirs(os.path.dirname(self.config.plots_output_path))

  def addHistosample(self, hist, sample):
    file = self.__get_file(sample)
    hist.load(file)
    hist.setup(sample)

    if not hist.isGood():
      warn(f"No good histogram {hist.getName()} for sample {sample.name}")
      return

    self.histosamples.append((copy.deepcopy(hist), sample))

  def normalizeHistograms(self):
    for hist, sample in self.histosamples:
      self.normalizer.normalize(hist, sample, None, None)

  def buildStacks(self):
    for hist, sample in self.histosamples:
      self.stacks[sample.type][hist.getName()].Add(hist.hist)

  def saveDatacards(self):

    # turn histosamples (tuple) into a dictionary (hist_name, sample_name -> hist, sample)
    obs_histosample = None
    signal_histosample = None
    background_histosamples = {}

    hist_name = None

    for hist, sample in self.histosamples:
      if hist_name is not None and hist_name != hist.getName():
        fatal(f"Histogram name {hist.getName()} does not match previous histogram name {hist_name}")
        exit(1)

      if sample.type == SampleType.data:
        obs_histosample = (hist, sample)
      elif sample.type == SampleType.signal:
        signal_histosample = (hist, sample)
      elif sample.type == SampleType.background:
        n_entries = hist.hist.GetEntries()
        if n_entries < self.config.exclude_backgrounds_for_years[sample.year]:
          warn(
              (f"Histogram {sample.name} has less than "
              f"{self.config.exclude_backgrounds_for_years[sample.year]} entries and will be excluded.")
          )
          continue
        background_histosamples[sample.name] = (hist, sample)

      hist_name = hist.getName()

    if obs_histosample is None:
      obs_histosample = self.__get_backgrounds_sum_hist(background_histosamples)

    self.datacardsProcessor.create_new_datacard(
        hist_name,
        obs_histosample,
        background_histosamples,
        signal_histosample,
        self.config.nuisances,
        self.input_files,
        self.config.add_uncertainties_on_zero
    )

  def __get_backgrounds_sum_hist(self, hists):
    backgrounds_sum_hist = None
    for _, (hist, _) in hists.items():
      if backgrounds_sum_hist is None:
        backgrounds_sum_hist = hist.hist.Clone()
      else:
        backgrounds_sum_hist.Add(hist.hist)

    if backgrounds_sum_hist is None and self.config.do_abcd:
      warn("No background histograms found, creating a dummy histogram for ABCD method")
      backgrounds_sum_hist = ROOT.TH2D()
      backgrounds_sum_hist.Fill(0.0, 1e-99)
    elif backgrounds_sum_hist is None:
      warn("No background histograms found, creating a dummy histogram")
      backgrounds_sum_hist = ROOT.TH1D()
      backgrounds_sum_hist.Fill(0.0, 1e-99)

    if hasattr(self.config, "do_abcd") and self.config.do_abcd:
      hist = Histogram2D(
          name="data_obs",
          norm_type=NormalizationType.to_lumi,
          x_rebin=self.config.rebin_2D,
          y_rebin=self.config.rebin_2D,
      )
    else:
      hist = Histogram(
          name="data_obs",
          norm_type=NormalizationType.to_lumi,
          rebin=self.config.rebin if hasattr(self.config, "rebin") else 1,
      )

    sample = Sample(name="bkg", type=SampleType.background)

    hist.set_hist(backgrounds_sum_hist)
    # hist.setup(sample)

    return (hist, sample)

  def __getStackDict(self, sample_type):
    hists_dict = {}
    title = self.config.histogram.getName() + sample_type.name
    hists_dict[self.config.histogram.getName()] = ROOT.THStack(title, title)

    return hists_dict

  def __get_file(self,sample):
    try:
        file = ROOT.TFile.Open(sample.file_path, "READ")
    except OSError:
      fatal(f"Couldn't open file {sample.file_path}")
      exit(1)
    return file
  