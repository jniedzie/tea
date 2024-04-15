import ROOT
import importlib
import sys

from HistogramsManager import HistogramsManager

def getConfig():
  configPath = sys.argv[1]
  if (".py" in configPath):
    configPath = configPath[:-3]
  config = importlib.import_module(configPath)
  return config


def main():
    ROOT.gROOT.SetBatch(True)

    config = getConfig()
    manager = HistogramsManager(config)

    input_files = {}

    for sample in config.samples:
        input_files[sample.name] = ROOT.TFile.Open(sample.file_path, "READ")
        
        for hist in config.histograms:
            manager.addHistosample(hist, sample, input_files[sample.name])
        
    manager.buildStacks()
    manager.saveDatacards()
    
    

if __name__ == "__main__":
    main()
