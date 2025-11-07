from ROOT import TGraphAsymmErrors, THStack, TFile, TH1F, TH2F, TH1, TH2
import ROOT
from copy import deepcopy
from array import array
import numpy as np

from Sample import Sample, SampleType
from Logger import warn, error

class ScaleFactorProducer:

    def __init__(self, config = None):
        self.config = None
        self.backgroundSamples = []
        self.dataSamples = []
        self.luminosity = None
        self.histogram = None
        self.histogram2D = None
        self.years_without_data = {}

        if config != None:
            self.config = config
            self.luminosity = self.config.luminosity
            self.setSamples(config.samples)
            if config.histogram1D:
                self.histogram1D = config.histogram1D
            if config.histogram2D:
                self.histogram2D = config.histogram2D

        self.extrapolation_functions = {
            "const": "[0]",
            "lin": "[0] + [1]*x",
            "2Dpoly": "[0] + [1]*x + [2]*x*x",
        }
                

    def setLuminosity(self, luminosity):
        self.luminosity = luminosity


    def setSamples(self, samples):
        self.backgroundSamples = []
        for sample in samples:
            if sample.type == SampleType.background:
                self.backgroundSamples.append(sample)
            if sample.type == SampleType.data:
                self.dataSamples.append(sample)


    def __getRootFile(self, file_path):
        root_file = TFile.Open(file_path)
        if not root_file or root_file.IsZombie():
            error("Error: Unable to open the ROOT file: " + file_path)
        return root_file
    

    def __getInitialWeightSum(self, sample):
        root_file = self.__getRootFile(sample.file_path)
        cut_flow = root_file.Get("cutFlow")
        return cut_flow.GetBinContent(1)
    
    def __clean_bins(self, bins, precision=8):
        rounded_bins = sorted(set(round(b, precision) for b in bins))
        return array('d', rounded_bins)

    def __rebinXaxis(self, hist, hist_name, xmin, xmax):
        original_bins = [hist.GetBinLowEdge(i) for i in range(1, hist.GetNbinsX() + 2)]
        new_bin_edges = [x for x in original_bins if xmin <= x <= xmax]
        if xmax not in new_bin_edges:
            new_bin_edges.append(xmax)
        
        new_n_bins = len(new_bin_edges) - 1
        hist_name = hist_name + "_rebinned"
        new_histogram = TH1F(hist_name, hist_name, new_n_bins, array('d', new_bin_edges))
        for i in range(1, new_n_bins + 1):
            original_bin = hist.FindBin(new_bin_edges[i-1])
            new_histogram.SetBinContent(i, hist.GetBinContent(original_bin))
            new_histogram.SetBinError(i, hist.GetBinError(original_bin))
            original_label = hist.GetXaxis().GetBinLabel(original_bin)
            if original_label != "":
                new_histogram.GetXaxis().SetBinLabel(i, original_label)
        return new_histogram

    def __rebin2D(self, hist, hist_name, xmin, xmax, ymin, ymax):
        if hist.GetDimension() != 2:
            raise ValueError("Histogram is not 2D")
        
        original_bins_x = [hist.GetXaxis().GetBinLowEdge(i) for i in range(1, hist.GetNbinsX() + 2)]
        original_bins_y = [hist.GetYaxis().GetBinLowEdge(i) for i in range(1, hist.GetNbinsY() + 2)]
        epsilon = 1e-6
        new_bin_edges_x = [x for x in original_bins_x if xmin-epsilon <= x <= xmax+epsilon]
        new_bin_edges_y = [y for y in original_bins_y if ymin-epsilon <= y <= ymax+epsilon]
        new_bin_edges_x = self.__clean_bins(new_bin_edges_x)
        new_bin_edges_y = self.__clean_bins(new_bin_edges_y)
        if xmax not in new_bin_edges_x:
            new_bin_edges_x.append(xmax)
        if ymax not in new_bin_edges_y:
            new_bin_edges_y.append(ymax)
        new_n_bins_x = len(new_bin_edges_x) - 1
        new_n_bins_y = len(new_bin_edges_y) - 1

        hist_name = hist_name + "_rebinned"
        new_histogram = TH2F(hist_name, hist_name, new_n_bins_x, array('d', new_bin_edges_x), new_n_bins_y, array('d', new_bin_edges_y))
        for i in range(1, new_n_bins_x + 1):
            for j in range(1, new_n_bins_y + 1):
                original_bin_x = hist.GetXaxis().FindBin(new_bin_edges_x[i-1])
                original_bin_y = hist.GetYaxis().FindBin(new_bin_edges_y[j-1])
                new_histogram.SetBinContent(i, j, hist.GetBinContent(original_bin_x, original_bin_y))
                new_histogram.SetBinError(i, j, hist.GetBinError(original_bin_x, original_bin_y))
                original_label_x = hist.GetXaxis().GetBinLabel(original_bin_x)
                original_label_y = hist.GetYaxis().GetBinLabel(original_bin_y)
                if original_label_x != "":
                    new_histogram.GetXaxis().SetBinLabel(i, original_label_x)
                if original_label_y != "":
                    new_histogram.GetYaxis().SetBinLabel(j, original_label_y)
        return new_histogram


    def __getOneBinnedHistogram(self, histogram):
        n_bins = histogram.GetNbinsX()
        histogram.Rebin(n_bins)
        return histogram


    def __getOneBinnedHistogram2D(self, histogram):
        n_bins_x = histogram.GetNbinsX()
        n_bins_y = histogram.GetNbinsY()
        histogram.Rebin2D(n_bins_x, n_bins_y)
        return histogram


    def __getNormalizedHist(self, histogram, sample):
        if sample.luminosity == None:
            warn("Luminosity is not defined - histograms are not normalized.")
            return histogram
        histogram.Scale(sample.cross_section * sample.luminosity / sample.initial_weight_sum)
        return histogram

    def getBackgroundHistogram1D(self, histogram):
        hist_name = histogram.name
        years_without_data = self.years_without_data[hist_name]
        stack = THStack(hist_name, hist_name)
        for sample in self.backgroundSamples:
            if sample.year in years_without_data:
                continue
            root_file = ROOT.TFile.Open(sample.file_path, "READ")
            histogram.load(root_file)

            n_entries = histogram.hist.GetEntries()
            if n_entries < self.config.exclude_backgrounds_with_less_than:
                warn(
                    (f"Histogram {sample.name} has less than "
                    f"{self.config.exclude_backgrounds_with_less_than} entries and will be excluded.")
                )
                root_file.Close()
                continue

            if "Event" in hist_name:
                # only get bin content of bin 2:    
                bin_content = histogram.hist.GetBinContent(2)
                bin_error = histogram.hist.GetBinError(2)
                new_hist = ROOT.TH1F(
                    histogram.hist.GetName() + "_onebin",
                    histogram.hist.GetTitle() + " (one bin)",
                    1, 0, 1  # 1 bin between 0.5 and 1.5
                )
                new_hist.SetBinContent(1, bin_content)
                new_hist.SetBinError(1, bin_error)
                histogram.set_hist(new_hist)

            histogram.setup(sample)
            sample.initial_weight_sum = self.__getInitialWeightSum(sample)
            normalized_hist = self.__getNormalizedHist(histogram.hist, sample)
            
            stack.Add(deepcopy(normalized_hist))
            root_file.Close()

        stack_items = stack.GetStack()
        if stack_items:
            background_stack_combined = stack_items.Last()
        else:
            background_stack_combined = ROOT.TH1F("empty_hist", "empty_hist", 1, 0, 1)
            background_stack_combined.SetDirectory(0)
        histogram.hist = background_stack_combined
        background_histogram = deepcopy(histogram)
        return background_histogram


    def getBackgroundHistogram2D(self, histogram2D):
        hist_name = histogram2D.name
        years_without_data = self.years_without_data[hist_name]
        stack = THStack(hist_name, hist_name)
        for sample in self.backgroundSamples:
            if sample.year in years_without_data:
                continue
            root_file = ROOT.TFile.Open(sample.file_path, "READ")
            histogram2D.load(root_file)

            n_entries = histogram2D.hist.GetEntries()
            if n_entries < self.config.exclude_backgrounds_with_less_than:
                warn(
                    (f"Histogram {sample.name} has less than "
                    f"{self.config.exclude_backgrounds_with_less_than} entries and will be excluded.")
                )
                root_file.Close()
                continue

            histogram2D.setup()
            sample.initial_weight_sum = self.__getInitialWeightSum(sample)
            normalized_hist = self.__getNormalizedHist(histogram2D.hist, sample)
            normalized_hist.SetBinErrorOption(TH2.kPoisson)
            
            stack.Add(deepcopy(normalized_hist))
            root_file.Close()
        
        stack_items = stack.GetStack()
        if stack_items:
            background_stack_combined = stack_items.Last()
        else:
            background_stack_combined = ROOT.TH1F("empty_hist", "empty_hist", 1, 0, 1)
            background_stack_combined.SetDirectory(0)
        histogram2D.hist = background_stack_combined
        background_histogram = deepcopy(histogram2D)
        return background_histogram


    def getDataHistogram1D(self, histogram1D):
        hist_name = histogram1D.name
        if hist_name not in self.years_without_data:
            self.years_without_data[hist_name] = []

        stack = THStack(hist_name, hist_name)
        for dataSample in self.dataSamples:
            root_file = self.__getRootFile(dataSample.file_path)
            histogram1D.load(root_file)
            histogram1D.setup(dataSample)
            if (histogram1D.hist.Integral() == 0):
                warn(f"Data sample {dataSample.name} has no events for {hist_name}!")
                self.years_without_data[hist_name].append(dataSample.year)
            stack.Add(deepcopy(histogram1D.hist))
            root_file.Close()
        data_stack_combined = stack.GetStack().Last()
        histogram1D.hist = data_stack_combined
        data_histogram1D = deepcopy(histogram1D)
        return data_histogram1D
    

    def getDataHistogram2D(self, histogram2D):
        stack = THStack(hist_name, hist_name)
        for dataSample in self.dataSamples:
            root_file = self.__getRootFile(self.dataSample.file_path)
            histogram2D.load(root_file)
            histogram2D.setup()
            stack.Add(deepcopy(histogram2D.hist))
            if (histogram2D.hist.Integral() == 0):
                warn(f"Data sample {dataSample.name} has no events for {hist_name}!")
                self.years_without_data[hist_name].append(dataSample.year)
            root_file.Close()
        data_stack_combined = stack.GetStack().Last()
        histogram2D.hist = data_stack_combined
        data_histogram2D = deepcopy(histogram2D)
        return data_histogram2D
    

    def getYieldAndAsymmetricUncertainties(self, hist):
        graph = TGraphAsymmErrors(hist)
        if graph.GetN() == 0:
            return 0.0, 0.0, 0.0  # Handle empty hist
        y = float(graph.GetY()[0])
        err_low = float(graph.GetEYlow()[0])
        err_high = float(graph.GetEYhigh()[0])
        return y, err_low, err_high


    def getYieldAndAsymmetricUncertainties2D(self, hist):
        # Sanity check
        assert hist.GetNbinsX() == 1 and hist.GetNbinsY() == 1
        content = hist.GetBinContent(1,1)
        error = hist.GetBinError(1,1)

        hist1D = TH1F("proj", "Projection", 1, 0, 1)
        hist1D.SetBinContent(1, content)
        hist1D.SetBinError(1, error)
        hist1D.SetBinErrorOption(TH1.kPoisson)
        return self.getYieldAndAsymmetricUncertainties(hist1D)



    def getDataMCRatios2D(self, data_histogram, background_histogram):
        data_hist2D = data_histogram.hist.Clone()
        data_hist2D_up = data_hist2D.Clone()
        data_hist2D_down = data_hist2D.Clone()
        data_hist2D.SetBinErrorOption(TH2.kPoisson)
        data_hist2D_up.SetBinErrorOption(TH2.kPoisson)
        data_hist2D_down.SetBinErrorOption(TH2.kPoisson)
        background_hist2D = background_histogram.hist.Clone()
        background_hist2D_up = background_histogram.hist.Clone()
        background_hist2D_down = background_histogram.hist.Clone()
        background_hist2D.SetBinErrorOption(TH2.kPoisson)
        background_hist2D_up.SetBinErrorOption(TH2.kPoisson)
        background_hist2D_down.SetBinErrorOption(TH2.kPoisson)

        nbinsX = background_hist2D.GetNbinsX()
        nbinsY = background_hist2D.GetNbinsY()

        for ix in range(1, nbinsX + 1):
            for iy in range(1, nbinsY + 1):
                data_hist2D_up.SetBinError(ix, iy, data_hist2D.GetBinErrorUp(ix, iy))
                data_hist2D_down.SetBinError(ix, iy, data_hist2D.GetBinErrorLow(ix, iy))
                background_hist2D_up.SetBinError(ix, iy, background_hist2D.GetBinErrorUp(ix, iy))
                background_hist2D_down.SetBinError(ix, iy, background_hist2D.GetBinErrorLow(ix, iy))


        ratio_hist2D_up = data_hist2D_up.Clone()
        ratio_hist2D_down = data_hist2D_down.Clone()
        ratio_up = ratio_hist2D_up.Divide(background_hist2D_up)
        ratio_down = ratio_hist2D_down.Divide(background_hist2D_down)

        if not ratio_up or not ratio_down:
            error("Could not perform Data/MC ratio properly")

        ratios = {}
        for ix in range(1, nbinsX + 1):
            x_bin = round(ratio_hist2D_up.GetXaxis().GetBinLowEdge(ix),2)
            ratios[x_bin] = {}
            for iy in range(1, nbinsY + 1):
                y_bin = round(ratio_hist2D_up.GetYaxis().GetBinLowEdge(iy),2)
                ratio = ratio_hist2D_up.GetBinContent(ix,iy)
                uncertainty_up = ratio_hist2D_up.GetBinError(ix,iy)
                uncertainty_down = ratio_hist2D_down.GetBinError(ix,iy)
                ratios[x_bin][y_bin] = [ratio, ratio+uncertainty_up, ratio-uncertainty_down]
                if ratio == 0:
                    # ratios[x_bin][y_bin] = [1.0, 1.0, 1.0]
                    ratios[x_bin][y_bin] = [None, None, None]
        
        return ratios


    def getDataMCRatioHists2D(self, data_histogram, background_histogram):
        data_hist2D = data_histogram.hist.Clone()
        data_hist2D_up = data_hist2D.Clone()
        data_hist2D_down = data_hist2D.Clone()
        data_hist2D.SetBinErrorOption(TH2.kPoisson)
        data_hist2D_up.SetBinErrorOption(TH2.kPoisson)
        data_hist2D_down.SetBinErrorOption(TH2.kPoisson)
        background_hist2D = background_histogram.hist.Clone()
        background_hist2D_up = background_histogram.hist.Clone()
        background_hist2D_down = background_histogram.hist.Clone()
        background_hist2D.SetBinErrorOption(TH2.kPoisson)
        background_hist2D_up.SetBinErrorOption(TH2.kPoisson)
        background_hist2D_down.SetBinErrorOption(TH2.kPoisson)

        nbinsX = background_hist2D.GetNbinsX()
        nbinsY = background_hist2D.GetNbinsY()

        for ix in range(1, nbinsX + 1):
            for iy in range(1, nbinsY + 1):
                data_hist2D_up.SetBinError(ix, iy, data_hist2D.GetBinErrorUp(ix, iy))
                data_hist2D_down.SetBinError(ix, iy, data_hist2D.GetBinErrorLow(ix, iy))
                background_hist2D_up.SetBinError(ix, iy, background_hist2D.GetBinErrorUp(ix, iy))
                background_hist2D_down.SetBinError(ix, iy, background_hist2D.GetBinErrorLow(ix, iy))

        ratio_hist2D_up = data_hist2D_up.Clone()
        ratio_hist2D_down = data_hist2D_down.Clone()
        ratio_up = ratio_hist2D_up.Divide(background_hist2D_up)
        ratio_down = ratio_hist2D_down.Divide(background_hist2D_down)

        ratio_hist2D = data_hist2D.Clone()
        ratio = ratio_hist2D.Divide(background_hist2D)

        if not ratio:
            error("Could not perform Data/MC ratio properly")

        for ix in range(1, nbinsX + 1):
            for iy in range(1, nbinsY + 1):
                error_up = ratio_hist2D_up.GetBinError(ix,iy)
                error_down = ratio_hist2D_down.GetBinError(ix,iy)
                ratio_hist2D_up.SetBinContent(ix,iy,error_up)
                ratio_hist2D_down.SetBinContent(ix,iy,error_down)

        return ratio_hist2D, ratio_hist2D_up, ratio_hist2D_down

    def getDataMCRatios1D(self, data_histogram, background_histogram):
        data_hist1D = data_histogram.hist.Clone()
        data_hist1D_up = data_hist1D.Clone()
        data_hist1D_down = data_hist1D.Clone()
        data_hist1D.SetBinErrorOption(TH2.kPoisson)
        data_hist1D_up.SetBinErrorOption(TH2.kPoisson)
        data_hist1D_down.SetBinErrorOption(TH2.kPoisson)
        background_hist1D = background_histogram.hist.Clone()
        background_hist1D_up = background_histogram.hist.Clone()
        background_hist1D_down = background_histogram.hist.Clone()
        background_hist1D.SetBinErrorOption(TH2.kPoisson)
        background_hist1D_up.SetBinErrorOption(TH2.kPoisson)
        background_hist1D_down.SetBinErrorOption(TH2.kPoisson)

        nbinsX = background_hist1D.GetNbinsX()

        for ix in range(1, nbinsX + 1):
            data_hist1D_up.SetBinError(ix, data_hist1D.GetBinErrorUp(ix))
            data_hist1D_down.SetBinError(ix, data_hist1D.GetBinErrorLow(ix))
            background_hist1D_up.SetBinError(ix, background_hist1D.GetBinErrorUp(ix))
            background_hist1D_down.SetBinError(ix, background_hist1D.GetBinErrorLow(ix))

        ratio_hist1D_up = data_hist1D_up.Clone()
        ratio_hist1D_down = data_hist1D_down.Clone()
        ratio_up = ratio_hist1D_up.Divide(background_hist1D_up)
        ratio_down = ratio_hist1D_down.Divide(background_hist1D_down)

        if not ratio_up or not ratio_down:
            error("Could not perform Data/MC ratio properly")

        ratios = {}
        for ix in range(1, nbinsX + 1):
            # x_bin = round(ratio_hist1D_up.GetXaxis().GetBinLowEdge(ix),2)
            ratio = ratio_hist1D_up.GetBinContent(ix)
            uncertainty_up = ratio_hist1D_up.GetBinError(ix)
            uncertainty_down = ratio_hist1D_down.GetBinError(ix)
            # ratios[x_bin] = [ratio, ratio+uncertainty_up, ratio-uncertainty_down]
            ratios = [ratio, ratio+uncertainty_up, ratio-uncertainty_down]
            if ratio == 0:
                # ratios[x_bin] = [1.0, 1.0, 1.0]
                ratios = [1.0, 1.0, 1.0]

        return ratios


    def getDataMCRatioHists1D(self, data_histogram, background_histogram):
        data_hist1D = data_histogram.hist.Clone()
        data_hist1D_up = data_hist1D.Clone()
        data_hist1D_down = data_hist1D.Clone()
        data_hist1D.SetBinErrorOption(TH2.kPoisson)
        data_hist1D_up.SetBinErrorOption(TH2.kPoisson)
        data_hist1D_down.SetBinErrorOption(TH2.kPoisson)
        background_hist1D = background_histogram.hist.Clone()
        background_hist1D_up = background_histogram.hist.Clone()
        background_hist1D_down = background_histogram.hist.Clone()
        background_hist1D.SetBinErrorOption(TH2.kPoisson)
        background_hist1D_up.SetBinErrorOption(TH2.kPoisson)
        background_hist1D_down.SetBinErrorOption(TH2.kPoisson)

        nbinsX = background_hist1D.GetNbinsX()

        for ix in range(1, nbinsX + 1):
            data_hist1D_up.SetBinError(ix, data_hist1D.GetBinErrorUp(ix))
            data_hist1D_down.SetBinError(ix, data_hist1D.GetBinErrorLow(ix))
            background_hist1D_up.SetBinError(ix, background_hist1D.GetBinErrorUp(ix))
            background_hist1D_down.SetBinError(ix, background_hist1D.GetBinErrorLow(ix))

        ratio_hist1D_up = data_hist1D_up.Clone()
        ratio_hist1D_down = data_hist1D_down.Clone()
        ratio_up = ratio_hist1D_up.Divide(background_hist1D_up)
        ratio_down = ratio_hist1D_down.Divide(background_hist1D_down)

        ratio_hist1D = data_hist1D.Clone()
        ratio = ratio_hist1D.Divide(background_hist1D)

        if not ratio_up or not ratio_down:
            error("Could not perform Data/MC ratio properly")

        ratios = {}
        for ix in range(1, nbinsX + 1):
            x_bin = round(ratio_hist1D_up.GetXaxis().GetBinLowEdge(ix),2)
            ratio = ratio_hist1D.GetBinContent(ix)
            uncertainty_up = ratio_hist1D_up.GetBinError(ix)
            uncertainty_down = ratio_hist1D_down.GetBinError(ix)
            ratios[x_bin] = [ratio, uncertainty_up, uncertainty_down]
            if ratio == 0:
                ratios[x_bin] = [1.0, 1.0, 1.0]


        for ix in range(1, nbinsX + 1):
            error_up = ratio_hist1D_up.GetBinError(ix)
            error_down = ratio_hist1D_down.GetBinError(ix)
            ratio_hist1D_up.SetBinContent(ix,error_up)
            ratio_hist1D_down.SetBinContent(ix,error_down)

        return ratio_hist1D, ratio_hist1D_up, ratio_hist1D_down


    def getDataMCRatio(self, data_yield, data_uncertainty_down, data_uncertainty_up, background_yield, background_uncertainty_down, background_uncertainty_up):
        if background_yield <= 0:
            return 0.0, 0.0, 0.0

        ratio = data_yield / background_yield

        # Relative uncertainties
        rel_data_low = data_uncertainty_down / data_yield if data_yield > 0 else 0
        rel_data_up = data_uncertainty_up / data_yield if data_yield > 0 else 0
        rel_bkg_low = background_uncertainty_down / background_yield
        rel_bkg_up = background_uncertainty_up / background_yield

        ratio_uncertainty_down = ratio * rel_ratio_low
        ratio_uncertainty_up = ratio * rel_ratio_up

        return ratio, ratio_uncertainty_down, ratio_uncertainty_up
    

    def getDataMCRatioForHists(self, data_hist, background_hist):

        data_hist1D = TH1F("mc_1d", "", 1, 0, 1)
        data_hist1D.SetBinContent(1, data_hist.GetBinContent(1,1))
        data_hist1D.SetBinError(1, data_hist.GetBinError(1,1))

        background_hist1D = TH1F("mc_1d", "", 1, 0, 1)
        background_hist1D.SetBinContent(1, background_hist.GetBinContent(1,1))
        background_hist1D.SetBinError(1, background_hist.GetBinError(1,1))

        graph = TGraphAsymmErrors(data_hist1D, background_hist1D, "pois")
        if graph.GetN() > 0:
            ratio = graph.GetY()[0]
            ratio_err_low = graph.GetEYlow()[0]
            ratio_err_up  = graph.GetEYhigh()[0]
        else:
            ratio, ratio_err_low, ratio_err_up = 0.0, 0.0, 0.0

        return ratio, ratio_err_low, ratio_err_up


    def set_missing_sfs_to_one(self,scale_factors):
        if isinstance(scale_factors, list):
            if scale_factors and scale_factors[0] is None:
                scale_factors[:] = [1.0, 1.0, 1.0]
            return
        
        for _, sfs in scale_factors.items():
            self.set_missing_sfs_to_one(sfs)

    def extrapolate_missing_scale_factors(self, scale_factors, bin_edges, func, in_x, in_y):
        result = []
        if not in_x and not in_y:
            warn(f"Extrapolation set to false for both x and y - will just set missing scale factors to 1.0.")
            self.set_missing_sfs_to_one(scale_factors)
            return result
        if in_x and in_y:
            info(f"Extrapolation set to true for both x and y - will just do extrapolation in x.")
        
        if isinstance(scale_factors, list):
            warn(f"extrapolation does not work for only one scale factor.")
            self.set_missing_sfs_to_one(scale_factors)
            return result

        if func not in self.extrapolation_functions:
            warn(f"Requested extrapolation function {func} is not implemented. Trying just a constant function.")
            func = "const"

        first_value = next(iter(scale_factors.values()), None)
        if isinstance(first_value, list):
            # dict with depth 1
            return [self.extrapolate_scale_factors(scale_factors, bin_edges, func)]

        # dict with depth 2
        if in_x:
            sub_bin_edges = bin_edges[0]
            for key, subdict in scale_factors.items():
                if isinstance(subdict, dict):
                    result_ = self.extrapolate_scale_factors(subdict, sub_bin_edges, func)
                    scale_factors[key] = subdict
                    result.append(result_)
            return result

        result = []
        sub_bin_edges = bin_edges[1]
        all_binx = next(iter(scale_factors.values())).keys()
        for binx in all_binx:
            subdict_y = {biny: scale_factors[biny][binx] for biny in scale_factors}
            result_ = self.extrapolate_scale_factors(subdict_y, sub_bin_edges, func)
            result.append(result_)
            for biny in scale_factors:
                scale_factors[biny][binx] = subdict_y[biny]
        
        return result
            
    def extrapolate_scale_factors(self, scale_factors, bin_edges, func):
        hist_before = {}
        hist_after = {}
        extrapolate_func = {}
        
        bins = sorted(scale_factors.keys())
        available_bins = [b for b in bins if scale_factors[b][0] is not None]
        if not available_bins:
            self.set_missing_sfs_to_one(scale_factors)
            return hist_before, hist_after, extrapolate_func
        bin_centers = [(bin_edges[i] + bin_edges[i+1])/2 for i in range(len(bins))]
        y_before = {}
        # coeffs = {}
        fit_values = {}
        y_after = {}
        for idx,category in enumerate(["nom","up","down"]):
            y_before[category] = np.array([
                scale_factors[b][idx] if scale_factors[b][idx] is not None else np.nan for b in bins
            ])
            valid_indices = ~np.isnan(y_before[category])
            x_fit = np.array([bin_centers[i] for i, valid in enumerate(valid_indices) if valid])
            y_fit = y_before[category][valid_indices]
            graph = ROOT.TGraph(len(x_fit), array('d', x_fit), array('d', y_fit))
            fit_func = ROOT.TF1(f"fit_{category}", self.extrapolation_functions[func] , min(bin_centers), max(bin_centers))
            graph.Fit(fit_func, "Q")
            extrapolate_func[category] = fit_func
            fit_values[category] = np.array([fit_func.Eval(xc) for xc in bin_centers])
            y_after[category] = np.empty(len(bins))
        
        for i, b in enumerate(bins):
            if scale_factors[b][0] is None:
                for category in ["nom","up","down"]:
                    y_after[category][i] = extrapolate_func[category].Eval(bin_centers[i])
                scale_factors[b] = [y_after["nom"][i], y_after["up"][i], y_after["down"][i]]
            else:
                for category in ["nom","up","down"]:
                    y_after[category][i] = y_before[category][i]
        
        hist_fit = {}
        nbins = len(bins)
        edges = np.array(bin_edges, dtype=float)
        for category in ["nom", "up", "down"]:
            hist_before[category] = ROOT.TH1F(f"{category} before", f"{category} Scale Factors Before", nbins, edges)
            hist_fit[category] = ROOT.TH1F(f"{category} linear_fit", f"{category} Linear Fit", nbins, edges)
            hist_after[category] = ROOT.TH1F(f"{category} after", f"{category} Scale Factors After", nbins, edges)

            for i,b in enumerate(bins):
                hist_before[category].SetBinContent(i+1, 0 if np.isnan(y_before[category][i]) else y_before[category][i])
                hist_fit[category].SetBinContent(i+1, fit_values[category][i])
                hist_after[category].SetBinContent(i+1, y_after[category][i])
                        
        return hist_before, hist_after, extrapolate_func


    def getHistsFromScaleFactors2D(self, scale_factors, bin_edges_x, bin_edges_y, z_bin):
        x_edges = array('d', bin_edges_x)
        y_edges = array('d', bin_edges_y)
        nbins_x = len(bin_edges_x)-1
        nbins_y = len(bin_edges_y)-1
        hist2D = ROOT.TH2F("hist2d", "Example 2D Histogram", 
                            nbins_x, x_edges, 
                            nbins_y, y_edges)

        for ix in range(1, nbins_x+1):
            x_edge = bin_edges_x[ix-1]
            x_sf = scale_factors[x_edge]
            for iy in range(1, nbins_y+1):
                y_edge = bin_edges_y[iy-1]
                y_sf = x_sf[y_edge]
                value = y_sf[z_bin]
                hist2D.SetBinContent(ix,iy,value)
        
        return hist2D
