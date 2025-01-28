import os
import ROOT

from Logger import error

class DatacardsProcessor:
    def __init__(self, output_path, include_shapes = True):
        self.output_path = output_path + ".txt"
        self.include_shapes = include_shapes
        self.datacards = {}
        self.hists = {}
        
        # get directory from the full path:
        os.system(f"mkdir -p {os.path.dirname(output_path)}")
        

    def create_new_datacard(self, identifier, obs_hist, mc_hists, nuisances, add_uncertainties_on_zero=False):
        self.datacards[identifier] = ""
        
        if type(obs_hist) == ROOT.TObject or obs_hist is None:
            error("DatacardsProcessor::create_new_datacard: obs_hist is not a histogram.")
        
        self.hists[identifier] = {"data_obs": obs_hist}
        
        n_backgrounds = 0
        n_signals = 0
        
        for name, hist in mc_hists.items():
            if "signal" not in name:
                n_backgrounds += 1
            else:
                n_signals += 1
            
            self.hists[identifier][name] = hist
        
        
        # remove processes with integral < 1e-90, and if they were backgrounds, decrease n_backgrounds
        to_remove = []
        for name, hist in self.hists[identifier].items():
            if hist.Integral() < 1e-90 and "data_obs" not in name:
                to_remove.append(name)
                if "signal" not in name:
                    n_backgrounds -= 1
                else:
                    n_signals -= 1

        for name in to_remove:
            del self.hists[identifier][name]
        
        # if there are no backgrounds, add a dummy background with integral 0
        if n_backgrounds == 0:
            self.hists[identifier]["background_dummy"] = self.__get_dummy_histogram(identifier)
            n_backgrounds = 1
            
        if n_signals == 0:
            self.hists[identifier]["signal_dummy"] = self.__get_dummy_histogram(identifier)
            n_signals = 1
        
        # sort self.hists such that entries starting with "signal_" go first:
        self.hists[identifier] = dict(sorted(self.hists[identifier].items(), key=lambda x: not x[0].startswith("signal_")))
        
        self.__add_header(identifier, n_signals, n_backgrounds)
        self.__add_rates(identifier)
        self.__add_nuisances(identifier, nuisances)
        
        
        print(f"Storing datacard in {self.output_path}")
        outfile = open(self.output_path, "w")
        outfile.write(self.datacards[identifier])
        
        print(f"Storing histograms in {self.output_path.replace('.txt', '.root')}")
        self.__save_histograms(identifier, add_uncertainties_on_zero)
    
    def __get_dummy_histogram(self, identifier):
        hist = list(self.hists[identifier].values())[0].Clone()
        hist.Reset()
        
        for i in range(1, hist.GetNbinsX()):
            hist.SetBinContent(i, 1e-99)
            
        return hist
    
    def __add_header(self, identifier, n_channels, n_backgrounds):
        # define number of parameters
        self.datacards[identifier] += f"imax {n_channels} number of channels\n"
        self.datacards[identifier] += f"jmax {n_backgrounds}  number of backgrounds\n"
        self.datacards[identifier] += "kmax * number of nuisance parameters\n"
        
        # point to the root file for shapes
        if self.include_shapes:
            # get file name from the full path:
            file_name = self.output_path.split("/")[-1].replace(".txt", ".root")
            self.datacards[identifier] += f"shapes * * {file_name} $PROCESS $PROCESS_$SYSTEMATIC\n"
        
        # set observed
        if "data_obs" not in self.hists[identifier]:
            obs_rate = 0
        else:
            obs_rate = self.hists[identifier]["data_obs"].Integral()
        self.datacards[identifier] += "bin bin1\n"
        self.datacards[identifier] += f"observation {obs_rate}\n"
        
        # prepare lines for MC processes
        self.datacards[identifier] += f"bin"
        for name in self.hists[identifier]:
            if name == "data_obs":
                continue
            self.datacards[identifier] += " bin1"
        self.datacards[identifier] += "\n"

        self.datacards[identifier] += f"process"
        for name in self.hists[identifier]:
            if name == "data_obs":
                continue
            self.datacards[identifier] += f" {name}"
        self.datacards[identifier] += "\n"

        self.datacards[identifier] += "process"
        for i, name in enumerate(self.hists[identifier]):
            if name == "data_obs":
                continue
            self.datacards[identifier] += f" {i}"
        self.datacards[identifier] += "\n"
        
    def __add_rates(self, identifier):
        self.datacards[identifier] += f"rate"
        
        for name, hist in self.hists[identifier].items():
            if name == "data_obs":
                continue
            self.datacards[identifier] += f" {hist.Integral()}"
        self.datacards[identifier] += "\n"

    def __add_nuisances(self, identifier, nuisances):
        
        for param_name, values in nuisances.items():
            self.datacards[identifier] += f"{param_name} lnN"
            
            for name in self.hists[identifier]:
                if name == "data_obs":
                    continue
                
                if name in values:
                    self.datacards[identifier] += f" {values[name]}"
                else:
                    self.datacards[identifier] += " -"
            self.datacards[identifier] += "\n"

        self.datacards[identifier] += "bin1   autoMCStats  10\n"

    def __add_uncertainties_on_zero(self, hist):
        for i in range(1, hist.GetNbinsX()):
            if hist.GetBinContent(i) != 0:
                continue
            hist.SetBinError(i, 1.84)

        return hist

    def __save_histograms(self, identifier, add_uncertainties_on_zero=False):

        output_file = ROOT.TFile(self.output_path.replace(".txt", ".root"), "recreate")
        
        for name, hist in self.hists[identifier].items():
            if add_uncertainties_on_zero and name == "data_obs":
                hist = self.__add_uncertainties_on_zero(hist)
            hist.SetName(name)
            hist.Write()

        output_file.Close()
        