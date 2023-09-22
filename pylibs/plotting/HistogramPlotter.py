from ROOT import TFile, TCanvas, TLegend, TObject
import ROOT
import os
import os.path


class HistogramPlotter:
  def __init__(self, config):
    self.config = config
    
    total_backgrounds_entries, total_backgrounds_integral, total_backgrounds_cross_section = self.__getTotalBackgroundsIntegral()
    self.total_backgrounds_entries = total_backgrounds_entries
    self.total_backgrounds_integral = total_backgrounds_integral
    self.total_backgrounds_cross_section = total_backgrounds_cross_section
  
  def setupLegend(self, legend):
    legend.SetBorderSize(0)
    # legend.SetFillColor(0)
    # legend.SetFillStyle(0)
    legend.SetTextFont(42)
    legend.SetTextSize(0.035)

  def getStackDict(self, file_type, efficiency=False):
    hists_dict = {}
    variables = self.config.efficiency_plots if efficiency else self.config.variables

    for name, params in variables.items():
      variable = params[0] if efficiency else name
      title = variable + file_type
      if efficiency:
        title += "_eff"
      hists_dict[name] = ROOT.THStack(title, title)

    return hists_dict

  def getLegendDicts(self, file_type, efficiency=False):
    legends_dict = {}
    legend_position = self.config.legend_position[file_type]
    variables = self.config.efficiency_plots if efficiency else self.config.variables
    
    for name in variables.keys():
      legend = TLegend(legend_position[0], legend_position[1], legend_position[2], legend_position[3])
      self.setupLegend(legend)
      legends_dict[name] = legend

    return legends_dict

  def addHistsToStacks(self, input_files, file_name, hists, legends, file_type, efficiency=False):
    variables = self.config.efficiency_plots if efficiency else self.config.variables

    cross_section = self.config.cross_sections[file_name]
    lumi = self.config.luminosity_2018
    
    file_type = self.config.files[file_name][1]
    
    background_count = 0
    
    first = True
    for name, values in variables.items():
      params = self.config.variables[values[0]] if efficiency else values
      hist_name = values[0] if efficiency else name
        

      hist = input_files[file_name].Get(hist_name)
      if not self.__checkHist(hist):
        print(f"Couldn't find hist or it is empty: {hist_name}")
        continue

      if efficiency:
        hist = self.__getEfficiencyHist(hist)

      normalization_type = params[2]
      self.__normalizeHist(hist, normalization_type, file_type, lumi, cross_section)
      
      self.__setupHist(hist, params, self.config.lines[file_name], file_type)
      hists[file_type][name].Add(hist)
      legends[file_type][name].AddEntry(hist, self.config.legends[file_name], self.config.legend_types[file_type])
      
      if file_type == "background" and first:
        background_count += hist.Integral()
        first = False
        
    return background_count

  def drawStacks(self, backgrounds_included, data_included, hists, legends, efficiency=False):

    # create output path if it doesn't exist
    if not os.path.exists(self.config.output_path):
      os.makedirs(self.config.output_path)

    variables = self.config.efficiency_plots if efficiency else self.config.variables


    for name, params in variables.items():
      
      title = "canvas_"+name
      if efficiency:
        title += "_eff"
      
      hist_params = self.config.variables[params[0]] if efficiency else params
        
      canvas = TCanvas(title, title, 800, 600)
      canvas.cd()
      canvas.SetLogy(hist_params[1])
      
      if backgrounds_included:
        hists["background"][name].Draw("hist")
        self.__setupFigure(hists["background"][name], hist_params)
        hists["signal"][name].Draw("nostack same")
      else:
        hists["signal"][name].Draw("hist nostack")
        self.__setupFigure(hists["signal"][name], hist_params)

      if data_included:
        hists["data"][name].Draw("nostack same P")

      legends["signal"][name].Draw()
      legends["background"][name].Draw()
      legends["data"][name].Draw()

      canvas.Update()
      canvas.SaveAs(self.config.output_path+"/"+name+".pdf")
  

  def __normalizeHist(self, hist, normalization_type, sample_type, lumi, cross_section):
    
    if normalization_type == "norm1":
      if sample_type == "background":
        hist.Scale(lumi*cross_section/self.total_backgrounds_integral)
      else:
        hist.Scale(1./hist.Integral())
    elif normalization_type == "to_background":
      if sample_type == "background":
        # TODO: should do this one properly, dividing by initial number of events
        hist.Scale(lumi*cross_section/hist.Integral())
      else:
        hist.Scale(lumi*self.total_backgrounds_cross_section/hist.Integral())

  def __setupHist(self, hist, params, linestyles, sample_type):
    line_color, line_style = linestyles
    
    if sample_type == "signal":
      hist.SetLineStyle(line_style)
      hist.SetLineColor(line_color)
    elif sample_type == "data":
      hist.SetLineColor(ROOT.kBlack)
      hist.SetMarkerStyle(20)
      hist.SetMarkerSize(1)
      hist.SetMarkerColor(ROOT.kBlack)
    else:
      hist.SetLineColorAlpha(line_color, 0)
      hist.SetFillColorAlpha(line_color, 0.7)
    
    hist.Rebin(params[3])
    hist.Sumw2(False)

  def __setupFigure(self, stack, params):
    if stack is None or type(stack) is TObject:
      return

    title, _, _, _, xmin, xmax, ymin, ymax, xlabel, ylabel = params

    if (ymin > 0):
      stack.SetMinimum(ymin)
    if (ymax > 0):
      stack.SetMaximum(ymax)
      
    try:
      stack.GetXaxis().SetLimits(xmin, xmax)
      stack.GetXaxis().SetTitle(xlabel)
      stack.GetYaxis().SetTitle(ylabel)
      stack.SetTitle(title)
    except:
      print("Couldn't set axes limits")
      return

  def __getEfficiencyHist(self, input_hist):
    hist = input_hist.Clone()
    initial = hist.GetBinContent(1)
    for bin in range(1, hist.GetNbinsX()+2):
      hist.SetBinContent(bin, hist.GetBinContent(bin)/initial)
    return hist

  def __checkHist(self, hist):
    if hist is None or type(hist) is TObject:
      return False
    if hist.GetEntries() == 0:
      return False
    return True

  def __getTotalBackgroundsIntegral(self):
    entries = 0
    integral = 0
    cross_section = 0
    
    for sample_name, file_info in self.config.files.items():
      file_name, file_type = file_info
      
      if file_type != "background":
        continue
      
      input_path = self.config.input_paths[file_type]
      file = TFile.Open(input_path+"/"+sample_name+"/"+self.config.skim+"/"+file_name, "READ")

      hist_name, _ = next(iter(self.config.variables.items()))
      hist = file.Get(hist_name) 


      integral += hist.Integral() * self.config.luminosity_2018 * self.config.cross_sections[sample_name]
      entries += hist.Integral()
      cross_section += self.config.cross_sections[sample_name]
      
    return entries, integral, cross_section
