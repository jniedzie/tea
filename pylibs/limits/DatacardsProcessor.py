import ROOT
from ctypes import c_double
from copy import deepcopy
from pathlib import Path
import math

from Logger import error, warn, info
from ABCDHelper import ABCDHelper
from HistogramNormalizer import HistogramNormalizer, NormalizationType
from Histogram import Histogram2D
from Sample import Sample, SampleType
from LimitConfig import output_paths


class NoSensitivityError(ValueError):
  """No positive signal yield exists in the fitted region."""


class DatacardsProcessor:
  def __init__(self, config, datacard_file_name):
    self.config = config
    self.paths = output_paths(config)
    self.datacard_file_name = datacard_file_name

    self.datacard = None
    self.histosamples = {}

    self.do_abcd = config.do_abcd if hasattr(config, "do_abcd") else False

    self.abcd_helper = ABCDHelper()
    self.normalizer = HistogramNormalizer(config)

  def create_new_datacard(
    self,
    hist_name,
    obs_histosample,
    bkg_histosamples,
    signal_histosample,
    nuisances,
    input_files,
    add_uncertainties_on_zero=False,
  ):
    self.datacard = ""
    self.histosamples = {}
    if signal_histosample is None:
      raise NoSensitivityError("Signal histogram is absent or empty")
    if obs_histosample is None or type(obs_histosample[0]) is ROOT.TObject:
      raise ValueError("Observation histogram is absent")
    if type(signal_histosample[0]) is ROOT.TObject:
      raise ValueError("Signal is not a histogram")
    signal_yield = signal_histosample[0].hist.Integral()
    if not math.isfinite(signal_yield) or signal_yield < 0:
      raise ValueError("Signal yield must be finite and nonnegative")
    if signal_yield == 0:
      raise NoSensitivityError("Signal yield is zero")
    if any(name in ("signal", "data_obs") for name in bkg_histosamples):
      raise ValueError("Background names cannot use reserved names signal/data_obs")

    self.histosamples["data_obs"] = obs_histosample
    self.histosamples["signal"] = signal_histosample

    for sample_name, histosample in bkg_histosamples.items():
      self.histosamples[sample_name] = histosample

    n_backgrounds = len(bkg_histosamples)
    n_backgrounds = self.__remove_empty_histograms(n_backgrounds)
    self.background_names = [
      name for name, (_, sample) in self.histosamples.items() if sample.type == SampleType.background
    ]
    if n_backgrounds == 0:
      self.histosamples["background_dummy"] = self.__get_dummy_histogram()
      n_backgrounds = 1
      self.background_names = ["background_dummy"]

    # Combine assigns the first process index 0 to the canonical signal.
    self.histosamples = dict(sorted(self.histosamples.items(), key=lambda item: item[1][1].type != SampleType.signal))

    nuisances_for_sample = deepcopy(nuisances)
    signal_name = signal_histosample[1].name
    for values in nuisances_for_sample.values():
      if isinstance(values, dict) and signal_name in values:
        if "signal" in values and values["signal"] != values[signal_name]:
          raise ValueError(f"Conflicting nuisances for {signal_name} and signal")
        values["signal"] = values.pop(signal_name)
    nuisances_updated = {}
    for k, v in nuisances_for_sample.items():
      if isinstance(v, dict):
        nuisances_updated[k] = v

    if self.do_abcd:
      self.__flip_signal_to_region_a()
      signal_rate = self.abcd_helper.get_abcd(self.histosamples["signal"][0].hist, self.config.abcd_point)[0]
      if not math.isfinite(signal_rate) or signal_rate < 0:
        raise ValueError("Invalid signal yield in ABCD signal region")
      if signal_rate == 0:
        raise NoSensitivityError("Signal yield is zero in ABCD signal region")
      self.__insert_background_sum_hist()
      nuisances_varations = self.__fill_in_variation_nuisances(
        hist_name, self.histosamples["signal"][1].name, nuisances_for_sample, input_files
      )
      for k, v in nuisances_varations.items():
        nuisances_updated[k] = v

      if self.config.use_abcd_prediction and nuisances_for_sample:
        nuisances_closure = self.__fill_closure_nuisance(nuisances_for_sample)
        for k, v in nuisances_closure.items():
          nuisances_updated[k] = v

        if "abcd_unc" in nuisances:
          self.__insert_background_sum_hist_for_shifted_points()
          nuisances_abcd = self.__fill_abcd_nuisance(nuisances_for_sample)
          for k, v in nuisances_abcd.items():
            nuisances_updated[k] = v

    self.__add_header(n_backgrounds)
    self.__add_rates()
    self.__add_nuisances(nuisances_updated)

    datacards_path = str(self.paths.datacards / (self.datacard_file_name + ".txt"))
    info(f"Storing datacard in {datacards_path}")
    Path(datacards_path).parent.mkdir(parents=True, exist_ok=True)
    with open(datacards_path, "w") as outfile:
      outfile.write(self.datacard)

    info(f"Storing histograms in {datacards_path.replace('.txt', '.root')}")
    self.__save_histograms(add_uncertainties_on_zero)
    return Path(datacards_path)

  def __flip_signal_to_region_a(self):
    histograms = {key: hist.hist for key, (hist, sample) in self.histosamples.items()}
    histograms = self.abcd_helper.flip_signal_to_region_a(histograms, self.config.signal_bin)

    for key in self.histosamples:
      self.histosamples[key][0].set_hist(histograms[key])

  def __remove_empty_histograms(self, n_backgrounds):
    to_remove = []
    for name, (hist, sample) in self.histosamples.items():
      rate = hist.hist.Integral()
      if not math.isfinite(rate) or rate < 0:
        raise ValueError(f"{name}: invalid histogram yield {rate}")
      if (
        rate == 0
        and sample.type == SampleType.background
        and not getattr(self.config, "retain_zero_backgrounds", False)
      ):
        to_remove.append(name)
        n_backgrounds -= 1

    for name in to_remove:
      del self.histosamples[name]

    return n_backgrounds

  def __fill_in_variation_nuisances(self, hist_name, sample_name, nuisances, input_files):
    nuisances_updated = {}
    for variation_name, value_tuple in nuisances.items():
      if not isinstance(value_tuple, tuple):
        continue

      if value_tuple[0] != "variation":
        continue

      cms_variation_name = value_tuple[1]

      # If we run over a specific dimuon category we don't want to apply variations from other categories
      if "dimuon" in variation_name:
        if not cms_variation_name.endswith(self.config.category):
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

      histograms = self.abcd_helper.flip_signal_to_region_a({"signal": variation_hist.hist}, self.config.signal_bin)
      variation_hist.set_hist(histograms["signal"])

      # get number of events in the signal bin
      n_base = self.abcd_helper.get_abcd(hist.hist, self.config.abcd_point)[0]
      n_variation = self.abcd_helper.get_abcd(variation_hist.hist, self.config.abcd_point)[0]

      if n_base != 0:
        variation = n_variation / n_base
        for symmetric_variation in getattr(self.config, "symmetric_variations", ()):
          if symmetric_variation in cms_variation_name:
            variation = abs(variation - 1) + 1
      else:
        variation = 0
        warn(f"Histogram {hist_name} has no events in the signal bin. Setting variation to 0.")

      if cms_variation_name not in nuisances_updated:
        nuisances_updated[cms_variation_name] = {"signal": [0.0, 0.0]}

      idx = 1
      if "down" in variation_name or "Dn" in variation_name:
        idx = 0
      if nuisances_updated[cms_variation_name]["signal"][idx] != 0.0:
        warn(f"Overwriting existing variation value for {cms_variation_name} and signal bin")
      nuisances_updated[cms_variation_name]["signal"][idx] = variation

    return nuisances_updated

  def __fill_closure_nuisance(self, nuisances):
    nuisances_updated = {}

    if "abcd_nonClosure" not in nuisances:
      return nuisances_updated

    bkg_hist = self.histosamples["bkg"][0].hist
    a = bkg_hist.GetBinContent(1, 2)
    b = bkg_hist.GetBinContent(1, 1)
    c = bkg_hist.GetBinContent(2, 2)
    d = bkg_hist.GetBinContent(2, 1)
    prediction = self.abcd_helper.get_prediction(b, c, d, 0, 0, 0)[0]
    closure = -1
    if a == 0:
      warn("region a is equal to 0! TODO: fix!")
    else:
      closure = abs(prediction - a) / a

    for key, value_tuple in nuisances.items():
      if value_tuple[0] == "closure":
        cms_variation_name = value_tuple[1]
        nuisances_updated[cms_variation_name] = {"bkg": [1 + closure]}

    return nuisances_updated

  def __fill_abcd_nuisance(self, nuisances):
    nuisances_updated = {}

    if "abcd_unc" not in nuisances:
      info("abcd_unc not in list of nuisances - will not add any ABCD uncertainty")
      return nuisances_updated

    max_rel_unc = -1
    for bkg_name in ("bkg_xup", "bkg_xdown", "bkg_yup", "bkg_ydown"):
      bkg_hist = self.histosamples[bkg_name][0].hist
      b = bkg_hist.GetBinContent(1, 1)
      c = bkg_hist.GetBinContent(2, 2)
      d = bkg_hist.GetBinContent(2, 1)
      b_err = bkg_hist.GetBinError(1, 1)
      c_err = bkg_hist.GetBinError(2, 2)
      d_err = bkg_hist.GetBinError(2, 1)
      prediction, prediction_err = self.abcd_helper.get_prediction(b, c, d, b_err, c_err, d_err)
      if prediction == 0:
        warn(f"Prediction is 0 for variation {bkg_name}, skipping ABCD uncertainty calculation for this variation.")
        continue
      rel_unc = prediction_err / prediction
      if rel_unc > max_rel_unc:
        max_rel_unc = rel_unc

    # nominal value
    bkg_hist = self.histosamples["bkg"][0].hist
    b = bkg_hist.GetBinContent(1, 1)
    c = bkg_hist.GetBinContent(2, 2)
    d = bkg_hist.GetBinContent(2, 1)
    b_err = bkg_hist.GetBinError(1, 1)
    c_err = bkg_hist.GetBinError(2, 2)
    d_err = bkg_hist.GetBinError(2, 1)
    nom_prediction, nom_prediction_err = self.abcd_helper.get_prediction(b, c, d, b_err, c_err, d_err)
    rel_unc_nom = nom_prediction_err / nom_prediction

    info(f"---- predicted A: {nom_prediction:.3f} +/- {nom_prediction_err:.3f}")

    abcd_unc = 1.0
    if rel_unc_nom < max_rel_unc:
      abcd_unc = max_rel_unc - rel_unc_nom

    info(f"---- abcd_unc: {abcd_unc:.3f}")

    for key, value_tuple in nuisances.items():
      if not isinstance(value_tuple, tuple):
        continue
      if value_tuple[0] == "abcd":
        cms_variation_name = value_tuple[1]
        nuisances_updated[cms_variation_name] = {"bkg": [1 + abcd_unc]}

    return nuisances_updated

  def __insert_background_sum_hist(self, abcd_point=None, histosample_name="bkg"):
    background_sum_a = 0
    background_sum_b = 0
    background_sum_c = 0
    background_sum_d = 0
    raw_sum_a = 0
    raw_sum_d = 0
    a_unc2 = 0
    d_unc2 = 0

    if not abcd_point:
      abcd_point = self.config.abcd_point

    hist_sum = None

    for name, (hist, sample) in self.histosamples.items():
      if name not in self.background_names:
        continue

      abcd_values = self.abcd_helper.get_abcd(hist.hist, abcd_point)
      if hist_sum is None:
        hist_sum = hist.hist.Clone()
      else:
        hist_sum.Add(hist.hist)

      a = abcd_values[0]
      d = abcd_values[3]
      a_raw = a / hist.norm_scale if hist.norm_scale != 0 else 0
      d_raw = d / hist.norm_scale if hist.norm_scale != 0 else 0

      background_sum_a += abcd_values[0]
      background_sum_b += abcd_values[1]
      background_sum_c += abcd_values[2]
      background_sum_d += abcd_values[3]
      raw_sum_a += a_raw
      raw_sum_d += d_raw
      a_unc2 += hist.norm_scale**2 * a_raw if hist.norm_scale != 0 else 0
      d_unc2 += hist.norm_scale**2 * d_raw if hist.norm_scale != 0 else 0

    a_unc = a_unc2**0.5
    d_unc = d_unc2**0.5
    info(f"---- histosample_name: {histosample_name}")
    info(f"---- raw_sum_a: {raw_sum_a:.3f}")
    info(f"---- raw_sum_d: {raw_sum_d:.3f}")
    info(f"---- background_sum_a: {background_sum_a:.3f} +/- {a_unc:.3f}")
    info(f"---- a_unc2: {a_unc2:.3f}")
    info(f"---- background_sum_b: {background_sum_b:.3f}")
    info(f"---- background_sum_c: {background_sum_c:.3f}")
    info(f"---- background_sum_d: {background_sum_d:.3f} +/- {d_unc:.3f}")
    info(f"---- d_unc2: {d_unc2:.3f}")

    hist = ROOT.TH2D(histosample_name, histosample_name, 2, 0, 2, 2, 0, 2)
    hist.SetBinContent(1, 2, background_sum_a)
    hist.SetBinContent(1, 1, background_sum_b)
    hist.SetBinContent(2, 2, background_sum_c)
    hist.SetBinContent(2, 1, background_sum_d)

    # setting bin errors to zero in cases where we get negative MC weights
    a_err = background_sum_a**0.5 if background_sum_a > 0 else 0
    b_err = background_sum_b**0.5 if background_sum_b > 0 else 0
    c_err = background_sum_c**0.5 if background_sum_c > 0 else 0
    d_err = background_sum_d**0.5 if background_sum_d > 0 else 0

    hist.SetBinError(1, 2, a_err)
    hist.SetBinError(1, 1, b_err)
    hist.SetBinError(2, 2, c_err)
    hist.SetBinError(2, 1, d_err)

    histogram = Histogram2D(
      name=histosample_name,
      norm_type=None,
      x_rebin=self.config.rebin_2D,
      y_rebin=self.config.rebin_2D,
    )
    histogram.set_hist(hist)
    self.histosamples[histosample_name] = (histogram, Sample(name=histosample_name, type=SampleType.background))

  def __insert_background_sum_hist_for_shifted_points(self):
    abcd_point_xup = (self.config.abcd_point[0] + 1, self.config.abcd_point[1])
    abcd_point_xdown = (self.config.abcd_point[0] - 1, self.config.abcd_point[1])
    abcd_point_yup = (self.config.abcd_point[0], self.config.abcd_point[1] + 1)
    abcd_point_ydown = (self.config.abcd_point[0], self.config.abcd_point[1] - 1)
    self.__insert_background_sum_hist(abcd_point_xup, "bkg_xup")
    self.__insert_background_sum_hist(abcd_point_xdown, "bkg_xdown")
    self.__insert_background_sum_hist(abcd_point_yup, "bkg_yup")
    self.__insert_background_sum_hist(abcd_point_ydown, "bkg_ydown")

  def __get_dummy_histogram(self):
    hist = deepcopy(next(hist for hist, sample in self.histosamples.values() if sample.type == SampleType.signal))
    sample = Sample(name="background_dummy", type=SampleType.background)
    hist.hist.Reset()
    for i in range(1, hist.hist.GetNcells()):
      hist.hist.SetBinContent(i, 1e-99)
    return hist, sample

  def __add_header(self, n_backgrounds):
    # define number of parameters
    self.datacard += "imax 1 number of channels\n"
    self.datacard += f"jmax {1 if self.do_abcd else n_backgrounds}  number of backgrounds\n"
    self.datacard += "kmax * number of nuisance parameters\n"

    # point to the root file for shapes
    if self.config.include_shapes:
      # get file name from the full path:

      if ".txt" not in self.datacard_file_name:
        file_name = self.datacard_file_name + ".root"
      else:
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
      obs_rate = self.histosamples["data_obs"][0].hist.Integral()
    if not math.isfinite(obs_rate) or obs_rate < 0:
      raise ValueError("Observation yield must be finite and nonnegative")
    self.datacard += "bin bin1\n"
    observation = obs_rate if getattr(self.config, "asimov_observation", False) else round(obs_rate)
    self.datacard += f"observation {observation}\n"

    # prepare lines for MC processes
    self.datacard += "bin"

    if self.do_abcd:
      self.datacard += " bin1  bin1"
    else:
      for name, (_, sample) in self.histosamples.items():
        if sample.type == SampleType.data:
          continue
        self.datacard += " bin1"
    self.datacard += "\n"

    self.datacard += "process"
    if self.do_abcd:
      self.datacard += " signal bkg"
    else:
      for name, (_, sample) in self.histosamples.items():
        if sample.type == SampleType.data:
          continue
        self.datacard += f" {name}"
    self.datacard += "\n"

    self.datacard += "process"
    if self.do_abcd:
      self.datacard += " 0 1"
    else:
      background_index = 1
      for _, (_, sample) in self.histosamples.items():
        if sample.type == SampleType.data:
          continue
        index = 0 if sample.type == SampleType.signal else background_index
        self.datacard += f" {index}"
        if sample.type == SampleType.background:
          background_index += 1
    self.datacard += "\n"

  def __add_rates(self):
    self.datacard += "rate"

    statistical_errors = {}

    if self.do_abcd:
      for name, (hist, sample) in self.histosamples.items():
        if sample.type == SampleType.signal:
          abcd_values = self.abcd_helper.get_abcd(hist.hist, self.config.abcd_point, raw_errors=False)
          signal_rate, _, _, _, signal_rate_err, _, _, _ = abcd_values
          break

      bkg_hist = self.histosamples["bkg"][0].hist
      a = bkg_hist.GetBinContent(1, 2)
      b = bkg_hist.GetBinContent(1, 1)
      c = bkg_hist.GetBinContent(2, 2)
      d = bkg_hist.GetBinContent(2, 1)

      if self.config.use_abcd_prediction:
        rate, rate_err = self.abcd_helper.get_prediction(b, c, d, b**0.5, c**0.5, d**0.5)
      else:
        rate, rate_err = a, a**0.5

      if not math.isfinite(rate) or rate < 0 or not math.isfinite(rate_err):
        raise ValueError("Invalid ABCD background rate or uncertainty")
      rate = rate if rate > 0 else 1e-99
      rate_err = 1 + rate_err / rate if rate > 0 else 1.0

      if not math.isfinite(signal_rate_err) or signal_rate_err < 0:
        raise ValueError("Invalid signal uncertainty in ABCD signal region")
      signal_rate_err = 1 + signal_rate_err / signal_rate if signal_rate > 0 else 1.0

      self.datacard += f" {signal_rate} {rate}"
      statistical_errors["signal"] = signal_rate_err
      statistical_errors["bck"] = rate_err
    else:
      for name, (hist, sample) in self.histosamples.items():
        if sample.type == SampleType.data:
          continue

        rate_err = c_double(0)
        rate = hist.hist.IntegralAndError(1, hist.hist.GetNbinsX(), rate_err)

        if not math.isfinite(rate) or rate < 0 or not math.isfinite(rate_err.value):
          raise ValueError(f"{name}: invalid rate or uncertainty")
        self.datacard += f" {rate}"
        statistical_errors[name] = 1 + rate_err.value / rate if rate > 0 else 1.0

    self.datacard += "\n"

    # add a row with statistical errors
    if not getattr(self.config, "include_mc_stat_uncertainties", True):
      return
    for name, stat_error in statistical_errors.items():
      self.datacard += f"stat_err_{name} lnN\t"
      for name_, stat_error_ in statistical_errors.items():
        if name_ == name:
          self.datacard += f" {stat_error_}"
        else:
          self.datacard += " -"
      self.datacard += "\n"

  def __get_first_background_name(self):
    first_background_name = None

    for name, (_, sample) in self.histosamples.items():
      if sample.type == SampleType.background:
        first_background_name = name
        break

    return first_background_name

  def __add_nuisances(self, nuisances):
    first_background_name = self.__get_first_background_name()

    for param_name, values in nuisances.items():
      get_max_variation = False
      for symmetric_variation in getattr(self.config, "symmetric_variations", ()):
        if symmetric_variation in param_name:
          get_max_variation = True

      self.datacard += f"{param_name} lnN"

      if self.do_abcd:
        signal_unc = "-"
        bkg_unc = "-"

        if "signal" in values:
          signal_unc_ = values["signal"]
          signal_unc = self.__get_variation_string(signal_unc_, get_max_variation)

        if "bkg" in values:
          bkg_unc_ = values["bkg"]
          bkg_unc = self.__get_variation_string(bkg_unc_, get_max_variation)

        elif first_background_name in values:
          bkg_unc_ = values[first_background_name]
          bkg_unc = self.__get_variation_string(bkg_unc_, get_max_variation)

        self.datacard += f" {signal_unc} {bkg_unc}"

      else:
        for name, (_, sample) in self.histosamples.items():
          if sample.type == SampleType.data:
            continue

          if name in values:
            self.datacard += f" {values[name]}"
          elif "signal" in values and sample.type == SampleType.signal:
            self.datacard += f" {values['signal']}"
          else:
            self.datacard += " -"
      self.datacard += "\n"

    if not self.do_abcd and self.config.include_shapes and getattr(self.config, "include_mc_stat_uncertainties", True):
      self.datacard += "bin1   autoMCStats  10\n"

  def __get_variation_string(self, unc, get_max_variation):
    if isinstance(unc, list):
      if len(unc) == 1:
        return unc[0]
      elif isinstance(unc[0], float) and isinstance(unc[1], float):
        if get_max_variation:
          return f"{max(unc[0], unc[1]):.3f}"
        else:
          return f"{unc[0]:.3f}/{unc[1]:.3f}"
      error(f"Unexpected format for uncertainty: {unc}")
      return
    return unc

  def __add_uncertainties_on_zero(self, hist):
    for i in range(1, hist.GetNbinsX() + 1):
      if hist.GetBinContent(i) != 0:
        continue
      hist.SetBinError(i, 1.84)

    return hist

  def __get_signal_hist(self):
    for name, (hist, sample) in self.histosamples.items():
      if sample.type == SampleType.signal:
        return hist.hist

    return None

  def __save_histograms(self, add_uncertainties_on_zero=False):
    output_path = str(self.paths.datacards / self.datacard_file_name)
    output_file = ROOT.TFile(f"{output_path}.root", "recreate")

    for name, (hist, sample) in self.histosamples.items():
      if add_uncertainties_on_zero and sample.type == SampleType.data:
        hist.set_hist(self.__add_uncertainties_on_zero(hist.hist))
      hist.set_hist_name(name)
      hist.hist.Write()

    # for 2D histograms, create a debugging plot with a sum of all background and the signal
    data_obs = self.histosamples["data_obs"][0].hist.Clone()
    signal_hist = self.__get_signal_hist()

    if self.do_abcd and data_obs is not None and signal_hist is not None:
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

      if data_obs.Integral() > 0:
        data_obs.DrawNormalized("BOX")
      else:
        data_obs.Draw("BOX")
      signal_hist.DrawNormalized("SAME BOX")

      canvas.Update()
      canvas.Write()
      plots_path = str(self.paths.diagnostics / self.datacard_file_name)
      canvas.SaveAs(f"{plots_path}.pdf")
      canvas.Close()

    output_file.Close()
