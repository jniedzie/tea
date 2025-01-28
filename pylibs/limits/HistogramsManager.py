from Logger import *
from Sample import SampleType
from HistogramNormalizer import HistogramNormalizer
from DatacardsProcessor import DatacardsProcessor

import ROOT

import copy
import os

class HistogramsManager:
    def __init__(self, config):
        self.config = config

        self.normalizer = HistogramNormalizer(config)
        self.datacardsProcessor = DatacardsProcessor(config.output_path, config.include_shapes)

        self.stacks = {sample_type: self.__getStackDict(
            sample_type) for sample_type in SampleType}
        
        self.histsAndSamples = {}
        
        self.data_included = any(
            sample.type == SampleType.data for sample in self.config.samples)
        self.backgrounds_included = any(
            sample.type == SampleType.background for sample in self.config.samples)

        
        self.histosamples = []
        self.data_integral = {}
        self.background_integral = {}

        if not os.path.exists(os.path.dirname(self.config.output_path)):
            os.makedirs(os.path.dirname(self.config.output_path))
    
    def addHistosample(self, hist, sample, input_file):
        hist.load(input_file)

        if not hist.isGood():
            warn(f"No good histogram {hist.getName()} for sample {sample.name}")
            return

        self.histosamples.append((copy.deepcopy(hist), sample))

        if sample.type is SampleType.data:
            self.data_integral[hist.getName()] = hist.hist.Integral()

    def buildStacks(self):
        for hist, sample in self.histosamples:
            if not hist.isGood():
                continue

            if sample.type != SampleType.background:
                continue

            self.normalizer.normalize(hist, sample, self.__getDataIntegral(
                hist), self.__getBackgroundIntegral(hist))

            if hist.getName() in self.background_integral:
                self.background_integral[hist.getName()
                                         ] += hist.hist.Integral()
            else:
                self.background_integral[hist.getName()] = hist.hist.Integral()

        for hist, sample in self.histosamples:
            if not hist.isGood():
                continue

            if sample.type == SampleType.background:
                continue

            self.normalizer.normalize(hist, sample, self.__getDataIntegral(
                hist), self.__getBackgroundIntegral(hist))

        for hist, sample in self.histosamples:
            if not hist.isGood():
                continue

            hist.setup(sample)
            self.stacks[sample.type][hist.getName()].Add(hist.hist)

    def saveDatacards(self):
        
        hists = {}
        
        for hist, sample in self.histosamples:
            identifier = hist.getName()
            
            if identifier not in hists:
                hists[identifier] = {}
            
            if sample.type == SampleType.data:
                hists[identifier]["data_obs"] = hist.hist
            else:
                hists[identifier][sample.name] = hist.hist
            
        for identifier, hists_per_sample in hists.items():
            
            mc_hists = hists_per_sample
            
            if "data_obs" in hists_per_sample:
                obs_hist = hists_per_sample["data_obs"]
                mc_hists.pop("data_obs")
            else:
                obs_hist = self.__get_backgrounds_sum_hist(hists_per_sample)
            
            self.datacardsProcessor.create_new_datacard(identifier, obs_hist, mc_hists, self.config.nuisances, self.config.add_uncertainties_on_zero)
            
    def __get_backgrounds_sum_hist(self, hists):
        backgrounds_sum_hist = None
        for name, hist in hists.items():
            if "signal" not in name:
                if backgrounds_sum_hist is None:
                    backgrounds_sum_hist = hist.Clone()
                else:
                    backgrounds_sum_hist.Add(hist)
                    
        if backgrounds_sum_hist is None:
            backgrounds_sum_hist = ROOT.TH1D()
            backgrounds_sum_hist.Fill(0.0, 1e-99)
        
        return backgrounds_sum_hist
    
    def __getStackDict(self, sample_type):
        hists_dict = {}

        for hist in self.config.histograms:
            title = hist.getName() + sample_type.name
            hists_dict[hist.getName()] = ROOT.THStack(title, title)

        return hists_dict
    
    def __getDataIntegral(self, input_hist):
        if input_hist.getName() in self.data_integral.keys():
            return self.data_integral[input_hist.getName()]
        return None
            
    def __getBackgroundIntegral(self, input_hist):
        if input_hist.getName() in self.background_integral.keys():
            return self.background_integral[input_hist.getName()]
        return None
