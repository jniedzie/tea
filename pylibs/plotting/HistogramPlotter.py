from ROOT import TCanvas, gStyle, THStack, TEfficiency, TMultiGraph
import ROOT
import os
import os.path
import copy
from array import array

from Sample import SampleType
from Styler import Styler
from HistogramNormalizer import HistogramNormalizer,NormalizationType
from CmsLabelsManager import CmsLabelsManager
from Logger import *
from Histogram import Histogram


class HistogramPlotter:
    def __init__(self, config):
        gStyle.SetOptStat(0)

        self.config = config

        self.normalizer = HistogramNormalizer(config)
        self.styler = Styler(config)
        self.cmsLabelsManager = CmsLabelsManager(config)

        self.legends = {}

        self.stacks = {sample_type: self.__getStackDict(
            sample_type) for sample_type in SampleType}
        self.ratiohists = {sample_type: self.__getRatioDict(
            sample_type) for sample_type in SampleType}
        self.histsAndSamples = {}
        self.hists2d = {sample_type: {} for sample_type in SampleType}

        self.data_included = any(
            sample.type == SampleType.data for sample in self.config.samples)
        self.backgrounds_included = any(
            sample.type == SampleType.background for sample in self.config.samples)

        self.show_ratios = self.backgrounds_included and self.data_included and self.config.show_ratio_plots

        self.histosamples = []
        self.ratiosamples = []
        self.histosamples2D = []
        self.data_integral = {}
        self.background_integral = {}

        if not os.path.exists(self.config.output_path):
            os.makedirs(self.config.output_path)

    def addHistosample(self, hist, sample, input_file):
        hist.load(input_file)

        if not hist.isGood():
            warn(
                f"No good histogram {hist.getName()} for sample {sample.name}")
            return

        self.histosamples.append((copy.deepcopy(hist), sample))

        if sample.type is SampleType.data:
            self.data_integral[hist.getName()] = hist.hist.Integral()

    def addHistosample2D(self, hist, sample, input_file):
        hist.load(input_file)

        if not hist.isGood():
            warn(
                f"No good histogram {hist.getName()} for sample {sample.name}")
            return
        
        

        self.histosamples2D.append((copy.deepcopy(hist), sample))

    def addHistosampleRatio(self, input_hist_pass, input_hist_tot, sample, input_file):
        input_hist_pass.load(input_file)
        input_hist_tot.load(input_file)
        
        if not input_hist_pass.isGood():
            warn(
                f"No good histogram {input_hist_pass.getName()} for sample {sample.name}")
            return
        if not input_hist_tot.isGood():
            warn(
                f"No good histogram {input_hist_tot.getName()} for sample {sample.name}")
            return

        hist_pass = copy.deepcopy(input_hist_pass)
        hist_pass.name = input_hist_pass.getName()+'_pass'
        hist_tot = copy.deepcopy(input_hist_tot)
        hist_tot.name = input_hist_tot.getName()+'_tot'
        
        self.ratiosamples.append((copy.deepcopy(hist_pass), copy.deepcopy(hist_tot), sample))

    def setupLegends(self):
        already_added = []

        for hist, sample in self.histosamples:
            if hist.getName() not in self.legends.keys():
                self.legends[hist.getName()] = {}

            if sample.custom_legend is not None:
                self.legends[hist.getName(
                )][sample.name] = sample.custom_legend.getRootLegend()
            elif (hist.getName(), sample.type) not in already_added:
                self.legends[hist.getName(
                )][sample.type] = self.config.legends[sample.type].getRootLegend()
                already_added.append((hist.getName(), sample.type))
        
        for hist_pass, hist_tot, sample in self.ratiosamples:
            hist = copy.deepcopy(hist_pass)
            hist.name = hist.name.replace("pass", "ratio")
            if hist.getName() not in self.legends.keys():
                self.legends[hist.getName()] = {}
            
            if sample.custom_legend is not None:
                self.legends[hist.getName(
                )][sample.name] = sample.custom_legend.getRootLegend()
            elif (hist.getName(), sample.type) not in already_added:
                self.legends[hist.getName(
                )][sample.type] = self.config.legends[sample.type].getRootLegend()
                already_added.append((hist.getName(), sample.type))

    def __getDataIntegral(self, input_hist):
        if input_hist.getName() in self.data_integral.keys():
            return self.data_integral[input_hist.getName()]
        return None

    def __getBackgroundIntegral(self, input_hist):
        if input_hist.getName() in self.background_integral.keys():
            return self.background_integral[input_hist.getName()]
        return None

    def __sortHistosamples(self):
        if hasattr(self.config, "custom_stacks_order"):
            try:
                self.histosamples.sort(
                    key=lambda x: self.config.custom_stacks_order.index(x[1].name))
            except ValueError:
                error(
                    "Couldn't sort histograms by custom order. Falling back to default order.")

                for _, sample in self.histosamples:
                    if sample.name not in self.config.custom_stacks_order:
                        error(
                            f"Couldn't find sample {sample.name} in custom order list.")

                self.histosamples.sort(
                    key=lambda x: x[1].cross_section, reverse=False)
        else:
            self.histosamples.sort(
                key=lambda x: x[1].cross_section, reverse=False)

    def buildStacks(self):
        self.__sortHistosamples()

        for hist, sample in self.histosamples:
            if not hist.isGood():
                warn(
                    f"No good histogram {hist.getName()} for sample {sample.name}")
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
                warn(
                    f"No good histogram {hist.getName()} for sample {sample.name}")
                continue

            if sample.type == SampleType.background:
                continue

            print(f"Normalizing {hist.getName()} for sample {sample.name}")
            self.normalizer.normalize(hist, sample, self.__getDataIntegral(
                hist), self.__getBackgroundIntegral(hist))

        for hist, sample in self.histosamples:
            if not hist.isGood():
                warn(
                    f"No good histogram {hist.getName()} for sample {sample.name}")
                continue

            if hist.getName().endswith('_ratio') or hist.getName().endswith('_denom'):
                continue

            hist.setup(sample)

            self.stacks[sample.type][hist.getName()].Add(hist.hist)

            key = sample.type if sample.custom_legend is None else sample.name

            if sample.legend_description != "":
                self.legends[hist.getName()][key].AddEntry(
                    hist.hist, sample.legend_description, self.config.legends[sample.type].options)

    def addHists2D(self, input_file, sample):
        if not hasattr(self.config, "histograms2D"):
            return

        for hist in self.config.histograms2D:
            hist.load(input_file)

            if not hist.isGood():
                warn(
                    f"No good histogram {hist.getName()} for sample {sample.name}")
                continue

            hist.setup()
            self.hists2d[sample.type][hist.getName()] = hist.hist

    def buildStacksRatio(self):
        if not hasattr(self.config, "histogramsRatio"):
            return

        for hist_pass, hist_tot, sample in self.ratiosamples:

            self.normalizer.normalize(hist_pass, sample, self.__getDataIntegral(
                hist_pass), self.__getBackgroundIntegral(hist_pass))
            self.normalizer.normalize(hist_tot, sample, self.__getDataIntegral(
                hist_tot), self.__getBackgroundIntegral(hist_tot))

            hist_pass.setup(sample)
            hist_tot.setup(sample)

            hist_ratio = copy.deepcopy(hist_pass)
            hist_ratio.name = hist_ratio.name.replace("pass", "ratio")
            hist = TEfficiency()
            hist.SetName(hist_ratio.getName())
            hist.SetTitle(hist_ratio.getName())

            hist_pass.hist.Sumw2(False)
            hist_tot.hist.Sumw2(False)
            hist.SetPassedHistogram(hist_pass.hist, "f")
            hist.SetTotalHistogram(hist_tot.hist, "f")

            graph = hist.CreateGraph()
            hist_ratio.hist = graph

            hist_ratio.setupRatio(sample)
            self.ratiohists[sample.type][hist_ratio.getName()].Add(hist_ratio.hist)

            key = sample.type if sample.custom_legend is None else sample.name
            self.legends[hist_ratio.getName()][key].AddEntry(hist_ratio.hist, sample.legend_description, self.config.legends[sample.type].options)            

    def __drawLineAtOne(self, canvas, hist):
        if not self.show_ratios:
            return

        global line
        line = ROOT.TLine(hist.x_min, 1, hist.x_max, 1)
        line.SetLineColor(ROOT.kBlack)
        line.SetLineStyle(ROOT.kDashed)

        canvas.cd(2)
        line.Draw()

    def __drawRatioPlot(self, canvas, hist):
        if not self.show_ratios:
            return

        global ratio_hist
        ratio_hist = self.__getRatioStack(hist)
        if ratio_hist:

            canvas.cd(2)
            ratio_hist.Draw("p")
            self.styler.setupFigure(ratio_hist, hist, is_ratio=True)

    def __drawUncertainties(self, canvas, hist):
        global background_uncertainty_hist
        background_uncertainty_hist = self.__getBackgroundUncertaintyHist(hist)
        if background_uncertainty_hist is None:
            return

        canvas.cd(1)
        self.styler.setupUncertaintyHistogram(background_uncertainty_hist)
        background_uncertainty_hist.Draw("same e2")

        if not self.show_ratios:
            return

        global ratio_uncertainty
        ratio_uncertainty = background_uncertainty_hist.Clone(
            "ratio_uncertainty_"+hist.getName())
        ratio_uncertainty.Divide(ratio_uncertainty)

        canvas.cd(2)
        ratio_uncertainty.Draw("same e2")

    def __drawLegends(self, canvas, hist):
        canvas.cd(1)

        if hist.getName() not in self.legends:
            warn(f"Couldn't find legends for histogram: {hist.getName()}")
            return

        for legend in self.legends[hist.getName()].values():
            legend.Draw()

    def _hist_to_graph(self, hist):

        n = hist.GetNbinsX()
        x = []
        y = []
        ex = []
        ey_up = []
        ey_down = []

        for i in range(1, n+1):
            x.append(hist.GetBinCenter(i))
            y.append(hist.GetBinContent(i))
            ex.append(hist.GetBinWidth(i)/2)
            ey_up.append(hist.GetBinErrorUp(i))
            ey_down.append(hist.GetBinErrorLow(i))
            
        return ROOT.TGraphAsymmErrors(n, array('d', x), array('d', y), array('d', ex), array('d', ex), array('d', ey_down), array('d', ey_up))



    def __drawHists(self, canvas, hist):
        canvas.cd(1)

        firstPlotted = False

        for sample_type in SampleType:
            options = self.config.plotting_options[sample_type]
            options = f"{options} same" if firstPlotted else options
            stack = self.stacks[sample_type][hist.getName()]
            if stack.GetNhists() > 0:
                # if these only one histogram in the stack, plot this histogram
                if stack.GetNhists() == 1:
                    graph = self._hist_to_graph(stack.GetHists()[0])
                    graph.SetMarkerStyle(20)
                    graph.SetMarkerSize(1)
                    graph.SetMarkerColor(ROOT.kBlack)
                    graph.DrawClone("PEsame")
                else:
                    stack.Draw(options)
                self.styler.setupFigure(stack, hist)
                firstPlotted = True

    def __drawRatioHists(self, canvas, hist):
        canvas.cd(1)

        firstPlotted = False

        for sample_type in SampleType:
            options = ""
            options = f"{options} same" if firstPlotted else options
            ratio = self.ratiohists[sample_type][hist.getName()]
            ratio.Draw(options)
            self.styler.setupFigure(ratio, hist, False)

            firstPlotted = True

    def __setup_canvas(self, canvas, hist):
        if self.show_ratios:
            canvas.Divide(1, 2)
            self.styler.setup_ratio_pad(canvas.GetPad(2))
            self.styler.setup_main_pad_with_ratio(canvas.GetPad(1))
        else:
            canvas.Divide(1, 1)
            self.styler.setup_main_pad_without_ratio(canvas.GetPad(1))

        canvas.GetPad(1).SetLogx(hist.log_x)
        canvas.GetPad(1).SetLogy(hist.log_y)

    def drawStacks(self):

        for hist in self.config.histograms:
            canvas = TCanvas(hist.getName(), hist.getName(
            ), self.config.canvas_size[0], self.config.canvas_size[1])
            self.__setup_canvas(canvas, hist)

            self.__drawRatioPlot(canvas, hist)
            self.__drawLineAtOne(canvas, hist)
            self.__drawHists(canvas, hist)
            self.__drawUncertainties(canvas, hist)
            self.__drawLegends(canvas, hist)
            self.cmsLabelsManager.drawLabels(canvas)
            
            # make sure plot border is on top of everything else
            canvas.GetPad(1).GetFrame().SetLineWidth(2)
            canvas.GetPad(1).GetFrame().SetBorderSize(2)
            canvas.GetPad(1).GetFrame().SetBorderMode(0)
            canvas.GetPad(1).GetFrame().SetFillColor(0)
            canvas.GetPad(1).GetFrame().SetFillStyle(0)
            canvas.GetPad(1).RedrawAxis()
            canvas.RedrawAxis()
            canvas.Update()

            originalErrorLevel = ROOT.gErrorIgnoreLevel
            ROOT.gErrorIgnoreLevel = ROOT.kError
            path = self.config.output_path+"/"+hist.getName()+".pdf"
            info(f"Saving file: {path}")
            canvas.SaveAs(path)
            canvas.SaveAs(path.replace(".pdf", ".C"))
            ROOT.gErrorIgnoreLevel = originalErrorLevel

    def drawHists2D(self):
        if not hasattr(self.config, "histograms2D"):
            return

        for hist, sample in self.histosamples2D:
            self.normalizer.normalize(hist, sample)

            hist_rebinned = hist.hist.Rebin2D(hist.x_rebin,hist.y_rebin)

            title = hist.getName() + "_" + sample.name
            canvas = TCanvas(
                title, title, self.config.canvas_size_2Dhists[0], self.config.canvas_size_2Dhists[1])
            canvas.cd()
            hist_rebinned.Draw("colz")
            self.styler.setupFigure2D(hist_rebinned, hist)

            canvas.SetLogz(hist.log_z)
            canvas.Update()
            canvas.SaveAs(self.config.output_path+"/"+title+".pdf")

    def drawRatioStacks(self):
      
        for hist_nom, hist_denom in self.config.histogramsRatio:
            hist_nom.name = hist_nom.getName()+'_ratio'

            canvas = TCanvas(hist_nom.getName(), hist_nom.getName(), self.config.canvas_size[0], self.config.canvas_size[1])
            self.__setup_canvas(canvas, hist_nom)
            
            self.__drawRatioHists(canvas, hist_nom)
            self.__drawLegends(canvas, hist_nom)
            self.cmsLabelsManager.drawLabels(canvas)
                  
            canvas.Update()
            
            originalErrorLevel = ROOT.gErrorIgnoreLevel
            ROOT.gErrorIgnoreLevel = ROOT.kError
            path = self.config.output_path+"/"+hist_nom.getName()+".pdf"
            info(f"Saving file: {path}")
            canvas.SaveAs(path)
            ROOT.gErrorIgnoreLevel = originalErrorLevel

    def __get_hists_sum(self, hist, doRatio=False):
        base_sample_type = SampleType.data if doRatio else SampleType.background

        try:
            base_hist = self.stacks[base_sample_type][hist.getName()].GetHists()[
                0]
        except Exception:
            return None

        title = "backgrounds_" + \
            ("sum" if doRatio else "unc") + "_" + hist.getName()
        backgrounds_sum = base_hist.Clone(title)
        backgrounds_sum.Reset()

        for background_hist in self.stacks[SampleType.background][hist.getName()].GetHists():
            backgrounds_sum.Add(background_hist)

        if not doRatio:
            return backgrounds_sum

        ratio_hist = base_hist.Clone("ratio_"+hist.getName())
        ratio_hist.Divide(backgrounds_sum)
        ratio_stack = THStack("ratio_stack_"+hist.getName(),
                              "ratio_stack_"+hist.getName())
        ratio_stack.Add(ratio_hist)

        return ratio_stack

    def __getRatioStack(self, hist):
        return self.__get_hists_sum(hist, doRatio=True)

    def __getBackgroundUncertaintyHist(self, hist):
        uncertainty_hist = self.__get_hists_sum(hist, doRatio=False)
        
        if uncertainty_hist is None:
            return None
        
        if hist.error > 0:
            for i in range(1, uncertainty_hist.GetNbinsX()+1):
                bin_content = uncertainty_hist.GetBinContent(i)
                stat_error = uncertainty_hist.GetBinError(i)
                syst_error = bin_content * hist.error
                uncertainty_hist.SetBinError(i, (stat_error**2 + syst_error**2)**(1/2))

        return uncertainty_hist

    def __getStackDict(self, sample_type):
        hists_dict = {}

        for hist in self.config.histograms:
            title = hist.getName() + sample_type.name
            hists_dict[hist.getName()] = ROOT.THStack(title, title)

        return hists_dict

    def __getRatioDict(self, sample_type):
        hists_dict = {}

        for hist_nom, hist_denom in self.config.histogramsRatio:
            title = hist_nom.getName() + '_ratio_' + sample_type.name
            hists_dict[hist_nom.getName()+'_ratio'] = TMultiGraph(title,title)

        return hists_dict
