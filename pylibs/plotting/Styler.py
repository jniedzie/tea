from Logger import *

from ROOT import TObject, gStyle
import ROOT

class Styler:
  
  def __init__(self, config):
    self.config = config
    
    self.topMargin = 0.06
    self.bottomMargin = 0.3
    self.leftMargin = 0.16
    self.rightMargin = 0.15
    
    self.__setStyle()
  
  def setup_ratio_pad(self, pad):
    pad.SetPad(0, 0, 1, 0.3)
    self.__setupPadDefaults(pad)
    pad.SetTopMargin(0)
    pad.SetLogy(False)
    
  def setup_main_pad_with_ratio(self, pad):
    pad.SetPad(0, 0.3, 1, 1)
    self.__setupPadDefaults(pad)
    pad.SetBottomMargin(0.0)
    pad.SetTopMargin(self.topMargin + 0.03)
    
  def setup_main_pad_without_ratio(self, pad):
    # pad.SetPad(0, 0.0, 1, 1)
    self.__setupPadDefaults(pad)
    pad.SetBottomMargin(0.2)
    pad.SetTopMargin(self.topMargin + 0.03)
  
  def __setupPadDefaults(self, pad):
    pad.SetLeftMargin(self.leftMargin)
    pad.SetBottomMargin(self.bottomMargin)
    pad.SetRightMargin(self.rightMargin)
    pad.SetTopMargin(self.topMargin)
    pad.SetTickx(0)
    pad.SetTicky(0)
  
  def __setStyle(self):
    gStyle.SetPadTopMargin(self.topMargin)
    gStyle.SetPadBottomMargin(self.bottomMargin)
    gStyle.SetPadLeftMargin(self.leftMargin)
    gStyle.SetPadRightMargin(self.rightMargin)
    
    gStyle.SetCanvasBorderMode(0)
    gStyle.SetCanvasColor(ROOT.kWhite)
    
    gStyle.SetPadBorderMode(0)
    gStyle.SetPadColor(ROOT.kWhite)
    gStyle.SetPadGridX(False)
    gStyle.SetPadGridY(False)
    gStyle.SetGridColor(0)
    gStyle.SetGridStyle(3)
    gStyle.SetGridWidth(1)

    gStyle.SetFrameBorderMode(0)
    gStyle.SetFrameBorderSize(1)
    gStyle.SetFrameFillColor(0)
    gStyle.SetFrameFillStyle(0)
    gStyle.SetFrameLineColor(1)
    gStyle.SetFrameLineStyle(1)
    gStyle.SetFrameLineWidth(1)

    gStyle.SetHistLineColor(1)
    gStyle.SetHistLineStyle(0)
    gStyle.SetHistLineWidth(1)

    gStyle.SetEndErrorSize(2)
    
    gStyle.SetOptFit(1)
    gStyle.SetFitFormat("5.4g")
    gStyle.SetFuncColor(2)
    gStyle.SetFuncStyle(1)
    gStyle.SetFuncWidth(1)

    gStyle.SetOptDate(0)
    gStyle.SetOptFile(0)
    
    gStyle.SetOptStat(0) # To display the mean and RMS:   SetOptStat("mr")
    gStyle.SetStatColor(ROOT.kWhite)
    gStyle.SetStatFont(42)
    gStyle.SetStatFontSize(0.025)
    gStyle.SetStatTextColor(1)
    gStyle.SetStatFormat("6.4g")
    gStyle.SetStatBorderSize(1)
    gStyle.SetStatH(0.1)
    gStyle.SetStatW(0.15)
    
    gStyle.SetOptTitle(0)
    gStyle.SetTitleFont(42)
    gStyle.SetTitleColor(1)
    gStyle.SetTitleTextColor(1)
    gStyle.SetTitleFillColor(10)
    gStyle.SetTitleFontSize(0.05)
    
    gStyle.SetTitleColor(1, "XYZ")
    gStyle.SetTitleFont(42, "XYZ")
    gStyle.SetTitleSize(0.06, "XYZ")
    gStyle.SetTitleXOffset(0.9)
    gStyle.SetTitleYOffset(1.25)
    
    gStyle.SetLabelColor(1, "XYZ")
    gStyle.SetLabelFont(42, "XYZ")
    gStyle.SetLabelOffset(0.007, "XYZ")
    gStyle.SetLabelSize(0.05, "XYZ")

    gStyle.SetAxisColor(1, "XYZ")
    gStyle.SetStripDecimals(True)
    gStyle.SetTickLength(0.03, "XYZ")
    gStyle.SetNdivisions(510, "XYZ")
    gStyle.SetPadTickX(1)  # To get tick marks on the opposite side of the frame
    gStyle.SetPadTickY(1)

    gStyle.SetOptLogx(0)
    gStyle.SetOptLogy(0)
    gStyle.SetOptLogz(0)

    gStyle.SetPaperSize(20.,20.)

  def setupFigure(self, plot, hist, is_ratio=False):
    if plot is None or type(plot) is TObject:
      return

    if is_ratio:
      plot.SetMinimum(self.config.ratio_limits[0])
      plot.SetMaximum(self.config.ratio_limits[1])
    else:
      if (hist.y_min > 0) or (not hist.log_y and hist.y_min == 0):
        plot.SetMinimum(hist.y_min)
      if (hist.y_max > 0):
        plot.SetMaximum(hist.y_max)
      
    try:
      plot.SetTitle("" if is_ratio else hist.title)
      plot.GetXaxis().SetLimits(hist.x_min, hist.x_max)
      
      plot.GetXaxis().SetTitle(hist.x_label)
      
      plot.GetXaxis().SetTitleOffset(1.0 if is_ratio else 1.7)
      
      if self.config.show_ratio_plots:
        plot.GetXaxis().SetTitleSize(0.12 if is_ratio else 0.06)
        plot.GetXaxis().SetLabelSize(0.1 if is_ratio else 0.06)
      else:
        plot.GetXaxis().SetTitleSize(0.04)
        plot.GetXaxis().SetLabelSize(0.04)
      
      plot.GetYaxis().SetTitle("Data/MC" if is_ratio else hist.y_label)
      plot.GetYaxis().SetTitleSize(0.1 if is_ratio else 0.05)
      plot.GetYaxis().SetTitleOffset(0.5 if is_ratio else 1.5)
      
      plot.GetYaxis().SetLabelSize(0.1 if is_ratio else 0.06)
      
      plot.GetYaxis().CenterTitle()
      plot.GetYaxis().SetNdivisions(505)
      
    except Exception:
      warn("Couldn't set axes limits")
      return
  
  def setupFigure2D(self, plot, hist):
    if plot is None or type(plot) is TObject:
      return

    if (hist.y_min > 0):
      plot.SetMinimum(hist.y_min)
    if (hist.y_max > 0):
      plot.SetMaximum(hist.y_max)
      
    if (hist.z_min > 0):
      plot.SetMinimum(hist.z_min)
    if (hist.z_max > 0):
      plot.SetMaximum(hist.z_max)
    
    try:
      plot.SetTitle(hist.title)
      plot.GetXaxis().SetRangeUser(hist.x_min, hist.x_max)
      plot.GetXaxis().SetTitle(hist.x_label)
      plot.GetXaxis().SetTitleSize(0.04)
      plot.GetXaxis().SetTitleOffset(1.0)
      plot.GetXaxis().SetLabelSize(0.04)
      
      plot.GetYaxis().SetRangeUser(hist.y_min, hist.y_max)
      plot.GetYaxis().SetTitle(hist.y_label)
      plot.GetYaxis().SetTitleSize(0.04)
      plot.GetYaxis().SetTitleOffset(1.2)
      plot.GetYaxis().CenterTitle()
      plot.GetYaxis().SetLabelSize(0.04)
      plot.GetYaxis().SetNdivisions(505)
      
      plot.GetZaxis().SetTitle(hist.z_label)
      plot.GetZaxis().SetTitleSize(0.04)
      plot.GetZaxis().SetTitleOffset(1.3)
      plot.GetZaxis().CenterTitle()
      plot.GetZaxis().SetLabelSize(0.04)
      plot.GetZaxis().SetNdivisions(505)

    except Exception:
      warn("Couldn't set axes limits")
      return
    
  def setupUncertaintyHistogram(self, hist):
    if hasattr(self.config, "background_uncertainty"):
      color = self.config.background_uncertainty_color
    else:
      color = ROOT.kBlack
    
    if hasattr(self.config, "background_uncertainty_alpha"):
      alpha = self.config.background_uncertainty_alpha
    else:
      alpha = 0.3
    
    if hasattr(self.config, "background_uncertainty_style"):
      style = self.config.background_uncertainty_style
    else:
      style = 3244
    
    hist.SetFillColorAlpha(color, alpha)
    hist.SetLineColor(color)
    hist.SetFillStyle(style)
    hist.SetMarkerSize(0.0)