from ROOT import TGraphAsymmErrors, THStack, TFile, TH1F, TH1
from copy import deepcopy
from array import array

from Sample import Sample, SampleType
from Logger import warn

class ScaleFactorProducer:

    def __init__(self, config = None):
        self.config = None
        self.backgroundSamples = []
        self.dataSample = None
        self.luminosity = None

        if config != None:
            self.config = config
            self.luminosity = self.config.luminosity
            self.setSamples(config.samples)
                

    def setLuminosity(self, luminosity):
        self.luminosity = luminosity


    def setSamples(self, samples):
        self.backgroundSamples = []
        for sample in samples:
            if sample.type == SampleType.background:
                self.backgroundSamples.append(sample)
            if sample.type == SampleType.data:
                self.dataSample = sample


    def __getRootFile(self, file_path):
        root_file = TFile.Open(file_path)
        if not root_file or root_file.IsZombie():
            print("Error: Unable to open the ROOT file: " + file_path)
        return root_file
    

    def __getInitialWeightSum(self,root_file):
        cut_flow = root_file.Get("cutFlow")
        return cut_flow.GetBinContent(1)
    

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


    def __getOneBinnedHistogram(self, histogram):
        n_bins = histogram.GetNbinsX()
        histogram.Rebin(n_bins)
        return histogram


    def __getNormalizedHist(self, histogram, sample):
        if self.luminosity == None:
            warn("Luminosity is not defined - histograms are not normalized.")
            return histogram
        histogram.Scale(sample.cross_section * self.luminosity / sample.initial_weight_sum)
        return histogram


    def getBackgroundStack(self, histogram):
        hist_name = histogram.name
        stack = THStack(hist_name, hist_name)
        for sample in self.backgroundSamples:
            root_file = self.__getRootFile(sample.file_path)

            sample.initial_weight_sum = self.__getInitialWeightSum(root_file)

            hist = deepcopy(root_file.Get(hist_name))
            if not hist or hist.ClassName() == "TObject":
                warn("Error: Histogram "+hist_name+" not found in the file " + sample.file_path)
                root_file.Close()
                break

            rebinned_hist = deepcopy(self.__rebinXaxis(hist, hist_name, histogram.x_min, histogram.x_max))
            one_binned_hist = self.__getOneBinnedHistogram(rebinned_hist)
            normalized_hist = self.__getNormalizedHist(one_binned_hist, sample)
            normalized_hist.SetBinErrorOption(TH1.kPoisson)
            stack.Add(normalized_hist)
            root_file.Close()
        return stack


    def getDataHist(self, histogram):
        hist_name = histogram.name
        root_file = self.__getRootFile(self.dataSample.file_path)
        hist = deepcopy(root_file.Get(hist_name))
        if not hist or hist.ClassName() == "TObject":
            warn("Error: Histogram "+hist_name+" not found in the file " + self.dataSample.file_path)
            root_file.Close()
            return None
        
        rebinned_hist = deepcopy(self.__rebinXaxis(hist, hist_name, histogram.x_min, histogram.x_max))
        one_binned_hist = self.__getOneBinnedHistogram(rebinned_hist)
        one_binned_hist.SetBinErrorOption(TH1.kPoisson)
        root_file.Close()
        return one_binned_hist
    

    def getYieldAndAsymmetricUncertainties(self, hist):
        graph = TGraphAsymmErrors(hist)
        if graph.GetN() == 0:
            return 0.0, 0.0, 0.0  # Handle empty hist
        y = float(graph.GetY()[0])
        err_low = float(graph.GetEYlow()[0])
        err_high = float(graph.GetEYhigh()[0])
        return y, err_low, err_high


    def getDataMCRatio(self, data_yield, data_uncertainty_down, data_uncertainty_up, background_yield, background_uncertainty_down, background_uncertainty_up):
        ratio = data_yield / background_yield if background_yield > 0 else 0
        data_low  = data_yield - data_uncertainty_down
        data_high = data_yield + data_uncertainty_up
        background_low  = background_yield  - background_uncertainty_down
        background_high = background_yield  + background_uncertainty_up

        ratio_low = data_low / background_high if background_high > 0 else 0
        ratio_high = data_high / background_low if background_low > 0 else 0

        ratio_uncertainty_down = ratio - ratio_low
        ratio_uncertainty_up   = ratio_high - ratio
        return ratio, ratio_uncertainty_down, ratio_uncertainty_up
    
