from HistogramPlotter import HistogramPlotter

from ROOT import TFile
import importlib
import sys

def main():

  configPath = sys.argv[1]
  if (".py" in configPath):
    configPath = configPath[:-3]
  config = importlib.import_module(configPath)
  
  plotter = HistogramPlotter(config)
  
  names = ("signal", "background", "data")
  hists = {name: plotter.getStackDict(name) for name in names}
  hists_eff = {name: plotter.getStackDict(name, True) for name in names}
  legends = {name: plotter.getLegendDicts(name) for name in names}
  legends_eff = {name: plotter.getLegendDicts(name, True) for name in names}

  backgrounds_included = False
  data_included = False

  input_files = {}
  
  for name, file_info in config.files.items():
    file_name, file_type = file_info
    input_path = config.input_paths[file_type]
    skim = config.skim
    input_files[name] = TFile.Open(input_path+"/"+name+"/"+skim+"/"+file_name, "READ")

    plotter.addHistsToStacks(input_files, name, hists, legends, file_type)
    plotter.addHistsToStacks(input_files, name, hists_eff, legends_eff, file_type, True)

    backgrounds_included |= file_type == "background"
    data_included |= file_type == "data"

  plotter.drawStacks(backgrounds_included, data_included, hists, legends)
  plotter.drawStacks(backgrounds_included, data_included, hists_eff, legends_eff, True)


if __name__ == "__main__":
  main()
