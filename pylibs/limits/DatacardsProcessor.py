import os
import ROOT

class DatacardsProcessor:
    def __init__(self, output_path, include_shapes = True):
        self.output_path = output_path
        self.include_shapes = include_shapes
        self.datacards = {}
        self.hists = {}
        
        os.system(f"mkdir -p {output_path}")
        

    def create_new_datacard(self, identifier, obs_hist, mc_hists, nuisances, add_uncertainties_on_zero=False, n_channels=1):
        self.datacards[identifier] = ""
        self.hists[identifier] = {"data_obs": obs_hist}
        
        n_backgrounds = 0
        for name, hist in mc_hists.items():
            if "signal" not in name:
                n_backgrounds += 1
            
            self.hists[identifier][name] = hist
        
        # sort self.hists such that entries starting with "signal_" go first:
        self.hists[identifier] = dict(sorted(self.hists[identifier].items(), key=lambda x: not x[0].startswith("signal_")))
        
        print(f"{self.hists[identifier]=}")
        
        self.__add_header(identifier, n_channels, n_backgrounds)
        self.__add_rates(identifier)
        self.__add_nuisances(identifier, nuisances)
        
        datacard_path = f"{self.output_path}/{identifier}.txt"
        print(f"Storing datacard in {datacard_path}")
        outfile = open(datacard_path, "w")
        outfile.write(self.datacards[identifier])
        
        print(f"Storing histograms in {datacard_path.replace('.txt', '.root')}")
        self.__save_histograms(identifier, add_uncertainties_on_zero)
    
    def __add_header(self, identifier, n_channels, n_backgrounds):
        # define number of parameters
        self.datacards[identifier] += f"imax {n_channels} number of channels\n"
        self.datacards[identifier] += f"jmax {n_backgrounds}  number of backgrounds\n"
        self.datacards[identifier] += "kmax * number of nuisance parameters\n"
        
        # point to the root file for shapes
        if self.include_shapes:
            self.datacards[identifier] += f"shapes * * {identifier}.root $PROCESS $PROCESS_$SYSTEMATIC\n"
        
        # set observed
        obs_rate = self.hists[identifier]["data_obs"].Integral()
        self.datacards[identifier] += "bin bin1\n"
        self.datacards[identifier] += f"observation {obs_rate}\n"
        
        # prepare lines for MC processes
        self.datacards[identifier] += f"bin"
        for _ in range(len(self.hists[identifier])-1):
            self.datacards[identifier] += " bin1"
        self.datacards[identifier] += "\n"

        self.datacards[identifier] += f"process"
        for name in self.hists[identifier]:
            if name == "data_obs":
                continue
            self.datacards[identifier] += f" {name}"
        self.datacards[identifier] += "\n"

        self.datacards[identifier] += "process"
        for i in range(len(self.hists[identifier])-1):
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

        output_file = ROOT.TFile(f"{self.output_path}/{identifier}.root", "recreate")
        
        for name, hist in self.hists[identifier].items():
            if add_uncertainties_on_zero and name == "data_obs":
                hist = self.__add_uncertainties_on_zero(hist)
            hist.SetName(name)
            hist.Write()

        output_file.Close()
        