import ROOT
from ctypes import c_double

from Logger import error, warn, info
from ABCDHelper import ABCDHelper
from HistogramNormalizer import HistogramNormalizer, NormalizationType
from Histogram import Histogram2D


class DatacardsProcessor:
  def __init__(self, config, datacard_file_name):
    self.config = config
    self.datacard_file_name = datacard_file_name

    self.datacard = None
    self.histosamples = {}

    self.do_abcd = config.do_abcd

    self.abcd_helper = ABCDHelper()
    self.normalizer = HistogramNormalizer(config)

  def create_new_datacard(
      self, hist_name, obs_histosample, bkg_histosamples, signal_histosample, 
      nuisances, input_files, add_uncertainties_on_zero=False
  ):
    self.datacard = ""

    if type(obs_histosample[0]) == ROOT.TObject or obs_histosample is None:
      error("DatacardsProcessor::create_new_datacard: obs_histosample is not a histogram.")
      return

    if type(signal_histosample[0]) == ROOT.TObject or signal_histosample is None:
      error("DatacardsProcessor::create_new_datacard: signal_histosample is not a histogram.")
      return

    self.histosamples["data_obs"] = obs_histosample
    self.histosamples["signal"] = signal_histosample

    for sample_name, histosample in bkg_histosamples.items():
      self.histosamples[sample_name] = histosample

    n_backgrounds = len(bkg_histosamples)
    n_backgrounds = self.__remove_empty_histograms(n_backgrounds)
    if n_backgrounds == 0:
      self.histosamples["background_dummy"] = self.__get_dummy_histogram()
      n_backgrounds = 1

    # sort self.histosamples such that entries starting with "signal_" go first:
    self.histosamples = dict(sorted(self.histosamples.items(), key=lambda x: not x[0].startswith("signal")))

    if self.do_abcd:
      self.__insert_background_sum_hist()
      nuisances = self.__fill_in_variation_nuisances(
          hist_name, self.histosamples["signal"][1].name, nuisances, input_files)

      if self.config.use_abcd_prediction:
        self.__fill_closure_nuisance(nuisances)

    self.__add_header(n_backgrounds)
    self.__add_rates()
    self.__add_nuisances(nuisances)

    datacards_path = self.config.datacards_output_path + self.datacard_file_name + ".txt"
    info(f"Storing datacard in {datacards_path}")
    outfile = open(datacards_path, "w")
    outfile.write(self.datacard)

    info(f"Storing histograms in {datacards_path.replace('.txt', '.root')}")
    self.__save_histograms(add_uncertainties_on_zero)

  def __remove_empty_histograms(self, n_backgrounds):
    to_remove = []
    for name, (hist, _) in self.histosamples.items():
      if hist.hist.Integral() < 1e-90 and "data_obs" not in name:
        to_remove.append(name)
        if "signal" not in name:
          n_backgrounds -= 1

    for name in to_remove:
      del self.histosamples[name]

    return n_backgrounds

  def __fill_in_variation_nuisances(self, hist_name, sample_name, nuisances, input_files):
    for variation_name, value in nuisances.items():
      if not isinstance(value, str):
        continue

      if value != "variation":
        continue

      hist, sample = self.histosamples["signal"]

      variation_hist = Histogram2D(
          name=f"{variation_name}/{hist_name}_{variation_name}",
          norm_type=NormalizationType.to_lumi,
          x_rebin=self.config.rebin_2D,
          y_rebin=self.config.rebin_2D,
      )

      variation_hist.load(input_files[sample_name])
      variation_hist.setup(sample)
      self.normalizer.normalize(variation_hist, sample, None, None)

      # get number of events in the signal bin
      n_base = self.abcd_helper.get_abcd(hist.hist, self.config.abcd_point)[0]
      n_variation = self.abcd_helper.get_abcd(variation_hist.hist, self.config.abcd_point)[0]
      variation = abs(n_variation - n_base) / n_base
      nuisances[variation_name] = {"signal": 1+variation}

    return nuisances

  def __fill_closure_nuisance(self, nuisances):

    bkg_hist = self.histosamples["bkg"][0].hist
    a = bkg_hist.GetBinContent(1, 2)
    b = bkg_hist.GetBinContent(1, 1)
    c = bkg_hist.GetBinContent(2, 2)
    d = bkg_hist.GetBinContent(2, 1)
    prediction = self.abcd_helper.get_prediction(b, c, d, 0, 0, 0)[0]
    closure = abs(prediction - a) / a
    
    for key, value in nuisances.items():
      if value == "closure":
        nuisances[key] = {"bkg": 1+closure}

  def __insert_background_sum_hist(self):
    background_sum_a = 0
    background_sum_b = 0
    background_sum_c = 0
    background_sum_d = 0

    background_sum_a_err = 0
    background_sum_b_err = 0
    background_sum_c_err = 0
    background_sum_d_err = 0

    for name, (hist, sample) in self.histosamples.items():
      if name == "data_obs" or "signal" in name:
        continue

      abcd_values = self.abcd_helper.get_abcd(hist.hist, self.config.abcd_point, raw_errors=True)
      a, b, c, d, a_err, b_err, c_err, d_err = abcd_values

      background_sum_a += a
      background_sum_b += b
      background_sum_c += c
      background_sum_d += d

      background_sum_a_err += a_err**2
      background_sum_b_err += b_err**2
      background_sum_c_err += c_err**2
      background_sum_d_err += d_err**2

    background_sum_a_err = background_sum_a_err**0.5
    background_sum_b_err = background_sum_b_err**0.5
    background_sum_c_err = background_sum_c_err**0.5
    background_sum_d_err = background_sum_d_err**0.5

    hist = ROOT.TH2D("bkg", "bkg", 2, 0, 2, 2, 0, 2)
    hist.SetBinContent(1, 2, background_sum_a)
    hist.SetBinContent(1, 1, background_sum_b)
    hist.SetBinContent(2, 2, background_sum_c)
    hist.SetBinContent(2, 1, background_sum_d)

    hist.SetBinError(1, 2, background_sum_a_err)
    hist.SetBinError(1, 1, background_sum_b_err)
    hist.SetBinError(2, 2, background_sum_c_err)
    hist.SetBinError(2, 1, background_sum_d_err)

    histogram = Histogram2D(
        name="bkg",
        norm_type=NormalizationType.to_lumi,
        x_rebin=self.config.rebin_2D,
        y_rebin=self.config.rebin_2D,
    )
    histogram.set_hist(hist)
    self.histosamples["bkg"] = (histogram, sample)

  def __get_dummy_histogram(self):
    hist = list(self.histosamples.values())[0].Clone()
    hist.hist.Reset()

    for i in range(1, hist.GetNbinsX()):
      hist.hist.SetBinContent(i, 1e-99)

    return hist

  def __add_header(self, n_backgrounds):
    # define number of parameters
    self.datacard += "imax 1 number of channels\n"
    self.datacard += f"jmax {1 if self.do_abcd else n_backgrounds}  number of backgrounds\n"
    self.datacard += "kmax * number of nuisance parameters\n"

    # point to the root file for shapes
    if self.config.include_shapes:
      # get file name from the full path:
      file_name = self.datacard_file_name.replace(".txt", ".root")
      self.datacard += f"shapes * * {file_name} $PROCESS $PROCESS_$SYSTEMATIC\n"

    # set observed
    if "data_obs" not in self.histosamples:
      obs_rate = 0
    elif self.do_abcd:
      if self.config.use_abcd_prediction:
        bkg_hist = self.histosamples["bkg"][0].hist
        b = bkg_hist.GetBinContent(1, 1)
        c = bkg_hist.GetBinContent(2, 2)
        d = bkg_hist.GetBinContent(2, 1)

        b_err = bkg_hist.GetBinError(1, 1)
        c_err = bkg_hist.GetBinError(2, 2)
        d_err = bkg_hist.GetBinError(2, 1)

        obs_rate, _ = self.abcd_helper.get_prediction(b, c, d, b_err, c_err, d_err)
      else:
        obs_rate = self.histosamples["bkg"][0].hist.GetBinContent(1, 2)
    else:
      obs_rate = self.histosamples["data_obs"].Integral()
    self.datacard += "bin bin1\n"
    self.datacard += f"observation {round(obs_rate)}\n"

    # prepare lines for MC processes
    self.datacard += "bin"

    if self.do_abcd:
      self.datacard += " bin1  bin1"
    else:
      for name in self.histosamples:
        if name == "data_obs":
          continue
        self.datacard += " bin1"
    self.datacard += "\n"

    self.datacard += "process"
    if self.do_abcd:
      self.datacard += " signal bkg"
    else:
      for name in self.histosamples:
        if name == "data_obs":
          continue
        self.datacard += f" {name}"
    self.datacard += "\n"

    self.datacard += "process"
    if self.do_abcd:
      self.datacard += " 0 1"
    else:
      index = 0
      for name in self.histosamples:
        if name == "data_obs":
          continue
        self.datacard += f" {index}"
        index += 1
    self.datacard += "\n"

  def __add_rates(self):
    self.datacard += "rate"

    statistical_errors = {}

    if self.do_abcd:
      for name, (hist, sample) in self.histosamples.items():
        if "signal" in name:
          abcd_values = self.abcd_helper.get_abcd(hist.hist, self.config.abcd_point, raw_errors=True)
          signal_rate, _, _, _, signal_rate_err, _, _, _ = abcd_values
          break

      bkg_hist = self.histosamples["bkg"][0].hist
      a = bkg_hist.GetBinContent(1, 2)
      b = bkg_hist.GetBinContent(1, 1)
      c = bkg_hist.GetBinContent(2, 2)
      d = bkg_hist.GetBinContent(2, 1)

      a_err = bkg_hist.GetBinError(1, 2)
      b_err = bkg_hist.GetBinError(1, 1)
      c_err = bkg_hist.GetBinError(2, 2)
      d_err = bkg_hist.GetBinError(2, 1)

      if self.config.use_abcd_prediction:
        rate, rate_err = self.abcd_helper.get_prediction(b, c, d, b_err, c_err, d_err)
      else:
        rate, rate_err = a, a_err

      if rate <= 0:
        warn("DatacardsProcessor::add_rates: rate is less than 0. Setting it to 1e-99")
        self.datacard += f" {signal_rate} 1e-99"
        statistical_errors["signal"] = 1.0
        statistical_errors["bck"] = 1.0
      else:
        self.datacard += f" {signal_rate} {rate}"
        statistical_errors["signal"] = 1 + signal_rate_err/signal_rate
        statistical_errors["bck"] = 1 + rate_err/rate
    else:
      for name, hist in self.histosamples.items():
        if name == "data_obs":
          statistical_errors[name] = None
          continue

        rate_err = c_double(0)
        rate = hist.IntegralAndError(1, hist.GetNbinsX(), rate_err)

        self.datacard += f" {rate}"
        statistical_errors[name] = 1 + rate_err.value/rate

    self.datacard += "\n"

    # add a row with statistical errors
    self.datacard += "stat_err lnN\t"
    for name, stat_error in statistical_errors.items():
      if stat_error is None:
        self.datacard += " -"
      else:
        self.datacard += f" {stat_error}"

    self.datacard += "\n"

  def __add_nuisances(self, nuisances):

    if self.do_abcd:
      first_background_name = None

      for name in self.histosamples:
        if name == "data_obs":
          continue

        if "signal" not in name:
          first_background_name = name
          break

    for param_name, values in nuisances.items():
      self.datacard += f"{param_name} lnN"

      if self.do_abcd:
        if "signal" in values:
          self.datacard += f" {values['signal']} -"
        if "bkg" in values:
          self.datacard += f" - {values['bkg']}"
        if first_background_name in values:
          self.datacard += f" - {values[first_background_name]}"
      else:
        for name in self.histosamples:
          if name == "data_obs":
            continue

          if name in values:
            self.datacard += f" {values[name]}"
          elif "signal" in values and "signal" in name:
            self.datacard += f" {values['signal']}"
          else:
            self.datacard += " -"
      self.datacard += "\n"

    if not self.do_abcd:
      self.datacard += "bin1   autoMCStats  10\n"

  def __add_uncertainties_on_zero(self, hist):
    for i in range(1, hist.GetNbinsX()):
      if hist.GetBinContent(i) != 0:
        continue
      hist.SetBinError(i, 1.84)

    return hist

  def __get_signal_hist(self):
    signal_hist = None

    for name, (hist, sample) in self.histosamples.items():
      if "signal" in name:
        signal_hist = hist.hist
        break

    return signal_hist

  def __save_histograms(self, add_uncertainties_on_zero=False):

    output_path = self.config.datacards_output_path + self.datacard_file_name
    output_file = ROOT.TFile(f"{output_path}.root", "recreate")

    for name, (hist, sample) in self.histosamples.items():
      if add_uncertainties_on_zero and name == "data_obs":
        hist.set_hist(self.__add_uncertainties_on_zero(hist.hist))
      hist.set_hist_name(name)
      hist.hist.Write()

    # for 2D histograms, create a debugging plot with a sum of all background and the signal
    data_obs = self.histosamples["data_obs"][0].hist.Clone()
    signal_hist = self.__get_signal_hist()

    if data_obs is not None and signal_hist is not None:
      canvas = ROOT.TCanvas("canvas", "canvas", 200, 200)

      data_obs.SetLineColor(ROOT.kBlack)
      data_obs.SetFillColorAlpha(ROOT.kBlack, 0.5)
      data_obs.SetMarkerStyle(20)
      data_obs.SetMarkerSize(0.2)
      data_obs.SetMarkerColor(ROOT.kBlack)

      signal_hist.SetLineColor(ROOT.kRed)
      signal_hist.SetFillColorAlpha(ROOT.kRed, 0.5)
      signal_hist.SetMarkerStyle(20)
      signal_hist.SetMarkerSize(0.2)
      signal_hist.SetMarkerColor(ROOT.kRed)

      data_obs.DrawNormalized("BOX")
      signal_hist.DrawNormalized("SAME BOX")

      canvas.Update()
      canvas.Write()
      plots_path = self.config.plots_output_path + self.datacard_file_name
      canvas.SaveAs(f"{plots_path}.pdf")

    output_file.Close()
