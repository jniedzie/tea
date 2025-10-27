from ScaleFactorProducer import ScaleFactorProducer
from CorrectionWriter import CorrectionWriter
from Logger import *

import ROOT
from ROOT import gROOT
import importlib
import sys, os
from array import array
from copy import deepcopy

nice_names_with_unit = {
    "pt_irr": "p_{T} [GeV]",
    "pt_irr2": "p_{T} [GeV]",
    "pt": "p_{T} [GeV]",
    "absDxyPVTraj_irr": "|d_{xy}| [cm]",
    "absDxyPVTraj": "|d_{xy}| [cm]",
    "dxyPVTraj_irr": "d_{xy} [cm]",
    "dxyPVTraj": "d_{xy} [cm]",
    "dimuon_category": "Dimuon category",
}

nice_names = {
    "pt_irr": "p_{T}",
    "pt_irr2": "p_{T}",
    "pt": "p_{T}",
    "absDxyPVTraj_irr": "|d_{xy}|",
    "absDxyPVTraj": "|d_{xy}|",
    "dxyPVTraj_irr": "d_{xy}",
    "dxyPVTraj": "d_{xy}",
    "dimuon_category": "Dimuon category",
}

def getConfig():
    configPath = sys.argv[1]
    if (".py" in configPath):
        configPath = configPath[:-3]
    config = importlib.import_module(configPath)
    return config

def plot_hist2D(hist, title, output_name, xbins = [], ybins = [], xaxis_title="X axis", yaxis_title="Y axis"):
    canvas = ROOT.TCanvas("canvas", "", 800, 600)
    canvas.SetLogx()
    canvas.SetLogy()
    if xbins and ybins:
        xbins_d = array('d', xbins)
        if xbins_d[0] == 0:
            xbins_d[0] = 1
        xbins_d[-1] = xbins_d[-1]*2
        n_bins_x = len(xbins_d) - 1
        ybins_d = array('d', ybins)
        if ybins_d[0] == 0:
            ybins_d[0] = 1
        n_bins_y = len(ybins_d) - 1
        if xbins[0] == 0 or ybins[0] == 0:
            new_hist = ROOT.TH2D(
                hist.GetName() + "_shiftedX",
                hist.GetTitle(),
                n_bins_x, xbins_d,
                n_bins_y, ybins_d
            )
            for ix in range(1, n_bins_x + 1):
                for iy in range(1, n_bins_y + 1):
                    content = hist.GetBinContent(ix, iy)
                    error = hist.GetBinError(ix, iy)
                    new_hist.SetBinContent(ix, iy, content)
                    new_hist.SetBinError(ix, iy, error)
            hist = new_hist
    hist.SetTitle(title)
    hist.GetXaxis().SetTitle(xaxis_title)
    hist.GetYaxis().SetTitle(yaxis_title)
    hist.SetStats(0)  # hide stats box
    ROOT.gStyle.SetPaintTextFormat(".2f");
    hist.SetMinimum(0)
    hist.Draw("COLZ TEXT")
    output_dir = "../sf/"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    output_path = os.path.join(output_dir, output_name)
    canvas.SaveAs(f"{output_path}.pdf")


def plot_hist1D(hist, title, output_name, xaxis_title="X axis"):
    canvas = ROOT.TCanvas("canvas", "", 800, 600)
    hist.SetTitle(title)
    hist.GetXaxis().SetTitle(xaxis_title)
    hist.GetYaxis().SetTitle("# Events")
    hist.SetStats(0)  # hide stats box
    hist.Draw("HIST COLZ")
    output_dir = "../sf/"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    output_path = os.path.join(output_dir, output_name)
    print(f"Hist bins: {hist.GetNbinsX()}")
    print(f"Hist entries: {hist.GetEntries()}")
    print("Hist integral: {:.2f}".format(hist.Integral()))
    canvas.SaveAs(f"{output_path}.png")

def plot_extrapolated_histograms(extrapolation_results, edges, output_name, axis_title, title_variable):
    for i, results in enumerate(extrapolation_results):
        if results is None:
            continue
        for category in ["nom", "up", "down"]:
            canvas = ROOT.TCanvas(f"canvas_{i}_{category}", "", 800, 600)
            canvas.SetLogx()
            # canvas.SetBottomMargin(0.15)
            hist_before = results[0][category]
            hist_after = results[1][category]
            extrapolation_func = results[2][category]
            hist_before.SetTitle(f"{category} extrapolation of bin {title_variable} = {edges[i]}")
            hist_before.GetXaxis().SetTitle(axis_title)
            hist_before.GetYaxis().SetTitle(f"SF {category}")
            hist_before.GetXaxis().SetTitleOffset(1.2)
            hist_before.SetStats(0)  # hide stats box
            hist_before.SetMarkerColor(ROOT.kRed)
            hist_before.SetMarkerStyle(20)
            max_y = max(hist_before.GetMaximum(), hist_after.GetMaximum())
            hist_before.SetMaximum(max_y * 1.4)
            hist_after.SetMarkerColor(ROOT.kGreen)
            hist_after.SetMarkerStyle(24)
            extrapolation_func.SetLineColor(ROOT.kBlue)
            extrapolation_func.SetLineWidth(2)
            normChi2 = extrapolation_func.GetChisquare()/extrapolation_func.GetNDF()
            p = extrapolation_func.GetProb()
            legend = ROOT.TLegend(0.15, 0.75, 0.4, 0.9)
            legend.SetBorderSize(0)
            legend.SetFillStyle(0)
            legend.SetTextSize(0.03)
            legend.AddEntry(hist_before, "Before fit", "lep")
            legend.AddEntry(hist_after, "After fit", "lep")
            legend.AddEntry(extrapolation_func, f"Fit function, #chi2/ndf = {normChi2:.2f}, p = {p:.2f}", "l")
            print(f"--- Fit function for bin {edges[i]}, category {category}:")
            print(f"\t#chi2={extrapolation_func.GetChisquare():.2f}, ndf={extrapolation_func.GetNDF():.2f}, #chi2/ndf={normChi2:.2f}, p-value={p:.2f}")
            hist_before.Draw("E")
            hist_after.Draw("E SAME")
            extrapolation_func.Draw("SAME")
            legend.Draw()
            output_dir = "../sf/extrapolation/"
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
            output_path = os.path.join(output_dir, output_name)
            canvas.SaveAs(f"{output_path}_{category}_{i}.pdf")


def main():
  
    gROOT.SetBatch(True)

    config = getConfig()
    sfProducer = ScaleFactorProducer(config)
    correctionWriter = CorrectionWriter()
    scale_factors = {}

    if not os.path.exists(f"../sf/sf_{config.year}"):
        os.makedirs(f"../sf/sf_{config.year}")

    info("Calculating scale factors...")

    # One 1D Histogram defined
    if config.histogram1D:
        print("1")
        background_histogram = sfProducer.getBackgroundHistogram1D(config.histogram1D)
        print("2")
        data_histogram = sfProducer.getDataHistogram1D(config.histogram1D)
        print("3")
        data_hist = data_histogram.hist
        print("4")
        background_hist = background_histogram.hist
        print("5")

        scale_factors = sfProducer.getDataMCRatios1D(data_histogram, background_histogram)
        ratio_hist,ratio_unc_hist_up,ratio_unc_hist_down  = sfProducer.getDataMCRatioHists1D(data_histogram, background_histogram)

        x_title = nice_names_with_unit[config.correction_inputs[0]["name"]]

        print(f"scale_factors: {scale_factors}")
        edges = list(scale_factors.keys())
        print(f"edges before: {edges}")
        edges.append(600.0)
        print(f"edges after: {edges}")
        if not config.correction_edges[0]:
            config.correction_edges[0] = edges

        sfProducer.set_missing_sfs_to_one(scale_factors)

        plot_hist1D(data_hist, "Data Histogram", f"data_hist1D{config.year}", config.correction_inputs[0]["name"])
        plot_hist1D(background_hist, "MC Background Histogram", f"mc_hist1D{config.year}", config.correction_inputs[0]["name"])
        plot_hist1D(ratio_hist, "Data / MC Scale Factor", f"sf_ratio1D{config.year}", config.correction_inputs[0]["name"])
        plot_hist1D(ratio_unc_hist_up, "Data / MC Scale Factor Uncertainty up", f"sf_ratio_uncertainty1D_up{config.year}", config.correction_inputs[0]["name"])
        plot_hist1D(ratio_unc_hist_down, "Data / MC Scale Factor Uncertainty down", f"sf_ratio_uncertainty1D_down{config.year}", config.correction_inputs[0]["name"])

    # List of 2D Histograms defined
    if config.histograms1D:
        scale_factors = {}
        for sfBin, histogram in config.histograms1D.items():
            background_histogram = sfProducer.getBackgroundHistogram1D(histogram)
            data_histogram = sfProducer.getDataHistogram1D(histogram)
            data_hist = data_histogram.hist
            background_hist = background_histogram.hist

            scale_factors[sfBin] = sfProducer.getDataMCRatios1D(data_histogram, background_histogram)
            ratio_hist,ratio_unc_hist_up,ratio_unc_hist_down  = sfProducer.getDataMCRatioHists1D(data_histogram, background_histogram)

            plot_hist1D(data_hist, f"Data Histogram {sfBin}", f"data_hist_{sfBin}_{config.year}", config.correction_inputs[0]["name"])
            plot_hist1D(background_hist, f"MC Background Histogram {sfBin}", f"mc_hist_{sfBin}_{config.year}", config.correction_inputs[0]["name"])
            plot_hist1D(ratio_hist, f"Data / MC Scale Factor {sfBin}", f"sf_ratio_{sfBin}_{config.year}", config.correction_inputs[0]["name"])
            plot_hist1D(ratio_unc_hist_up, f"Data / MC Scale Factor Uncertainty up {sfBin}", f"sf_ratio_uncertainty_up_{sfBin}_{config.year}", config.correction_inputs[0]["name"])
            plot_hist1D(ratio_unc_hist_down, f"Data / MC Scale Factor Uncertainty down {sfBin}", f"sf_ratio_uncertainty_down_{sfBin}_{config.year}", config.correction_inputs[0]["name"])
        print(f"scale_factors: {scale_factors}")

    # One 2D Histogram defined
    if config.histogram2D:
        background_histogram = sfProducer.getBackgroundHistogram2D(config.histogram2D)
        data_histogram = sfProducer.getDataHistogram2D(config.histogram2D)
        data_hist = data_histogram.hist
        background_hist = background_histogram.hist

        scale_factors = sfProducer.getDataMCRatios2D(data_histogram, background_histogram)
        ratio_hist,ratio_unc_hist_up,ratio_unc_hist_down  = sfProducer.getDataMCRatioHists2D(data_histogram, background_histogram)

        x_title = nice_names_with_unit[config.correction_inputs[0]["name"]]
        y_title = nice_names_with_unit[config.correction_inputs[1]["name"]]

        outer_edges = list(scale_factors.keys())
        inner_edges = set()
        for inner_dict in scale_factors.values():
            inner_edges.update(inner_dict.keys())
        inner_edges = sorted(inner_edges)
        outer_edges.append(2000.0)
        inner_edges.append(700.0)
        if not config.correction_edges[0]:
            config.correction_edges[0] = outer_edges
        if not config.correction_edges[1]:
            config.correction_edges[1] = inner_edges

        if config.extrapolate_in_x or config.extrapolate_in_y:
            edges = [inner_edges, outer_edges]
            x_title_ = nice_names[config.correction_inputs[0]["name"]]
            y_title_ = nice_names[config.correction_inputs[1]["name"]]
            if config.extrapolate_in_x:
                fit_results = sfProducer.extrapolate_missing_scale_factors(scale_factors, edges, func=config.extrapolation_function, in_x=True, in_y=False)
                plot_extrapolated_histograms(fit_results, outer_edges, f"extrapolated_hists_{config.extrapolation_function}_x_{config.year}", y_title, x_title_)
            if config.extrapolate_in_y:
                fit_results = sfProducer.extrapolate_missing_scale_factors(scale_factors, edges, func=config.extrapolation_function, in_x=False, in_y=True)
                plot_extrapolated_histograms(fit_results, inner_edges, f"extrapolated_hists_{config.extrapolation_function}_y_{config.year}", x_title, y_title_)
        else:
            sfProducer.set_missing_sfs_to_one(scale_factors)

        plot_hist2D(data_hist, "Data Histogram", f"sf_{config.year}/data_hist_{config.year}", outer_edges, inner_edges, x_title, y_title)
        plot_hist2D(background_hist, "MC Background Histogram", f"sf_{config.year}/mc_hist_{config.year}", outer_edges, inner_edges, x_title, y_title)
        plot_hist2D(ratio_hist, "Data / MC Corrections", f"sf_{config.year}/sf_ratio_{config.year}", outer_edges, inner_edges, x_title, y_title)
        plot_hist2D(ratio_unc_hist_up, "Data / MC Corrections Uncertainty up", f"sf_{config.year}/sf_ratio_uncertainty_up_{config.year}", outer_edges, inner_edges, x_title, y_title)
        plot_hist2D(ratio_unc_hist_down, "Data / MC Corrections Uncertainty down", f"sf_{config.year}/sf_ratio_uncertainty_down_{config.year}", outer_edges, inner_edges, x_title, y_title)
        # get relative ratio_unc_hist_up devided by ratio_hist
        ratio_unc_hist_up.Divide(ratio_hist)
        ratio_unc_hist_down.Divide(ratio_hist)
        plot_hist2D(ratio_unc_hist_up, "Data / MC Corrections Uncertainty up relative", f"sf_{config.year}/sf_ratio_uncertainty_up_relative_{config.year}", outer_edges, inner_edges, x_title, y_title)
        plot_hist2D(ratio_unc_hist_down, "Data / MC Corrections Uncertainty down relative", f"sf_{config.year}/sf_ratio_uncertainty_down_relative_{config.year}", outer_edges, inner_edges, x_title, y_title)

        final_hist_nominal = sfProducer.getHistsFromScaleFactors2D(scale_factors, outer_edges, inner_edges, 0)
        final_hist_up = sfProducer.getHistsFromScaleFactors2D(scale_factors, outer_edges, inner_edges, 1)
        final_hist_down = sfProducer.getHistsFromScaleFactors2D(scale_factors, outer_edges, inner_edges, 2)
        scale_factors_uncertainty = deepcopy(scale_factors)
        for xbin in scale_factors_uncertainty:
            for ybin in scale_factors_uncertainty[xbin]:
                nom = scale_factors_uncertainty[xbin][ybin][0]
                up = scale_factors_uncertainty[xbin][ybin][1]
                down = scale_factors_uncertainty[xbin][ybin][2]
                scale_factors_uncertainty[xbin][ybin] = [nom, up-nom, nom-down]
        final_hist_unc_up = sfProducer.getHistsFromScaleFactors2D(scale_factors_uncertainty, outer_edges, inner_edges, 1)
        final_hist_unc_down = sfProducer.getHistsFromScaleFactors2D(scale_factors_uncertainty, outer_edges, inner_edges, 2)
        plot_hist2D(final_hist_nominal, "Data / MC Corrections", f"sf_{config.year}/sf_ratio_final_{config.year}", outer_edges, inner_edges, x_title, y_title)
        plot_hist2D(final_hist_up, "Data / MC Corrections Up Variation", f"sf_{config.year}/sf_ratio_variation_up_final_{config.year}", outer_edges, inner_edges, x_title, y_title)
        plot_hist2D(final_hist_down, "Data / MC Corrections Down Variation", f"sf_{config.year}/sf_ratio_variation_down_final_{config.year}", outer_edges, inner_edges, x_title, y_title)
        plot_hist2D(final_hist_unc_up, "Data / MC Corrections Up Uncertainty", f"sf_{config.year}/sf_ratio_uncertainty_up_final_{config.year}", outer_edges, inner_edges, x_title, y_title)
        plot_hist2D(final_hist_unc_down, "Data / MC Corrections Down Uncertainty", f"sf_{config.year}/sf_ratio_uncertainty_down_final_{config.year}", outer_edges, inner_edges, x_title, y_title)
        final_hist_up_rel = final_hist_up.Clone()
        final_hist_down_rel = final_hist_down.Clone()
        final_hist_up_rel.Divide(final_hist_nominal)
        final_hist_down_rel.Divide(final_hist_nominal)
        plot_hist2D(final_hist_down_rel, "Data / MC Corrections Up Relative Variation", f"sf_{config.year}/sf_ratio_variation_up_relative_final_{config.year}", outer_edges, inner_edges, x_title, y_title)
        plot_hist2D(final_hist_down_rel, "Data / MC Corrections Down Relative Variation", f"sf_{config.year}/sf_ratio_variation_down_relative_final_{config.year}", outer_edges, inner_edges, x_title, y_title)      

    # List of 2D Histograms defined
    if config.histograms2D:
        scale_factors = {}
        for sfBin, histogram in config.histograms2D.items():
            background_histogram = sfProducer.getBackgroundHistogram2D(histogram)
            data_histogram = sfProducer.getDataHistogram2D(histogram)
            data_hist = data_histogram.hist
            background_hist = background_histogram.hist

            scale_factors[sfBin] = sfProducer.getDataMCRatios2D(data_histogram, background_histogram)
            ratio_hist,ratio_unc_hist_up,ratio_unc_hist_down  = sfProducer.getDataMCRatioHists2D(data_histogram, background_histogram)

            plot_hist2D(data_hist, f"Data Histogram {sfBin}", f"data_hist_{sfBin}_{config.year}",correction_inputs[0]["name"],correction_inputs[1]["name"])
            plot_hist2D(background_hist, f"MC Background Histogram {sfBin}", f"mc_hist_{sfBin}_{config.year}",correction_inputs[0]["name"],correction_inputs[1]["name"])
            plot_hist2D(ratio_hist, f"Data / MC Scale Factor {sfBin}", f"sf_ratio_{sfBin}_{config.year}",correction_inputs[0]["name"],correction_inputs[1]["name"])
            plot_hist2D(ratio_unc_hist_up, f"Data / MC Scale Factor Uncertainty up {sfBin}", f"sf_ratio_uncertainty_up_{sfBin}_{config.year}",correction_inputs[0]["name"],correction_inputs[1]["name"])
            plot_hist2D(ratio_unc_hist_down, f"Data / MC Scale Factor Uncertainty down {sfBin}", f"sf_ratio_uncertainty_down_{sfBin}_{config.year}",correction_inputs[0]["name"],correction_inputs[1]["name"])

    info("Writing corrections...")
    include_variations = False
    for input in config.correction_inputs:
        if input["name"] == "scale_factors":
            include_variations = True
            break

    correction_sfs = {}
    for sfBin, sf in scale_factors.items():
        if include_variations:
            correction_sfs[sfBin] = sf
        else:
            correction_sfs[sfBin] = sf[0]

    if include_variations:
        info("Writing corrections including variations.")
    else:
        info("Writing corrections without variations. To include variations add 'scale_factors' in correction_inputs.")

    correctionWriter.add_multibinned_correction_for_config(config, correction_sfs)
    correctionWriter.save_json(config.output_name)
    logger_print()

if __name__ == "__main__":
    main()