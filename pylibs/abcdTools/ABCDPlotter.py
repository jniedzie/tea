import ROOT
import os

from ABCDHelper import ABCDHelper
from ABCDHistogramsHelper import ABCDHistogramsHelper


class ABCDPlotter:
    def __init__(self, config):
        self.config = config

        self.abcdHelper = ABCDHelper(config)
        self.histogramsHelper = ABCDHistogramsHelper(config)

        self.hist_name = config.variable_1 + "_vs_" + config.variable_2 + config.region

        self.background_files = {}
        self.background_hists = {}
        self.data_file = None
        self.signal_files = {}
        self.signal_hists = {}
        self.canvases = None
        self.projections_pads = {}
        self.significance_hists = {}
        self.contamination_hists = {}
        self.lines = {}
        self.projections_legend = ROOT.TLegend(*config.projections_legend_position)
        self.signal_projections = {}
        self.ratio_hist = None
        self.ratio_hist_err = None

        os.makedirs(config.output_path, exist_ok=True)

        self.setup_canvases()
        self.load_background_histograms()
        self.load_signal_hists()

        self.setup_backgrounds_sum_histogram()
        self.optimization_hists = self.abcdHelper.get_optimization_hists(self.background_hist)
        
        self.setup_signal_hists()
        self.true_projection_hist = self.abcdHelper.get_projection_true(self.background_hist)
        self.prediction_projection_hist = self.abcdHelper.get_projection_prediction(self.background_hist)

        self.true_projection_hist, self.smart_binning = self.histogramsHelper.rebin(
            self.true_projection_hist)
        self.prediction_projection_hist, _ = self.histogramsHelper.rebin(
            self.prediction_projection_hist, self.smart_binning)

    def plot_optimization_hists(self):
        for name, hist in self.optimization_hists.items():
            hist.GetXaxis().SetTitle(self.abcdHelper.get_nice_name(self.config.variable_1))
            hist.GetYaxis().SetTitle(self.abcdHelper.get_nice_name(self.config.variable_2))
            hist.GetZaxis().SetTitle(self.config.z_params[name][0])
            hist.GetZaxis().SetTitleOffset(1.9)

            self.canvases[name].cd()
            hist.Draw("colz")
            ROOT.gPad.SetLogz(self.config.z_params[name][3])
            hist.GetZaxis().SetRangeUser(self.config.z_params[name][1], self.config.z_params[name][2])

    def plot_per_signal_hists(self):
        clones = {}

        label = ROOT.TLatex()
        label.SetTextSize(0.07)

        for i_mass, mass in enumerate(self.config.masses):
            for i_ctau, ctau in enumerate(self.config.ctaus):
                if (mass, ctau) not in self.signal_hists:
                    continue

                clones["background"] = self.background_hist.Clone()
                clones[(mass, ctau)] = self.signal_hists[(mass, ctau)].Clone()

                clones["background"].Rebin2D(self.config.rebin_grid, self.config.rebin_grid)
                clones[(mass, ctau)].Rebin2D(self.config.rebin_grid, self.config.rebin_grid)

                i_pad = 1 + i_mass * len(self.config.ctaus) + i_ctau
                mass_label = f"{mass.replace('p', '.')} GeV, {ctau} mm"

                self.canvases["grid"].cd(i_pad)
                self.set_pad_style()
                clones["background"].DrawNormalized("BOX")
                clones[(mass, ctau)].DrawNormalized("BOX SAME")
                label.DrawLatexNDC(*self.config.signal_label_position, mass_label)

                self.canvases["significance"].cd(i_pad)
                self.set_pad_style()
                self.significance_hists[(mass, ctau)].Draw("colz")
                label.DrawLatexNDC(*self.config.signal_label_position, mass_label)

    def plot_and_save_best_abcd_points(self):
        best_point = None
        best_x = None
        best_y = None

        file_path = f"{self.config.output_path}/best_points.txt"
        with open(file_path, "w") as f:
            f.write("mass, ctau, best_x, best_y, closure, error, min_n_events, significance, contamination\n")

            for i_mass, mass in enumerate(self.config.masses):
                for i_ctau, ctau in enumerate(self.config.ctaus):
                    if (mass, ctau) not in self.signal_hists:
                        continue

                    best_point = self.abcdHelper.get_optimal_point(
                        self.significance_hists[(mass, ctau)],
                        self.contamination_hists[(mass, ctau)],
                        self.optimization_hists
                    )

                    if best_point is None:
                        continue

                    significance_hist = self.significance_hists[(mass, ctau)]

                    best_x = significance_hist.GetXaxis(
                    ).GetBinCenter(best_point[0])
                    best_y = significance_hist.GetYaxis(
                    ).GetBinCenter(best_point[1])

                    values = {name: hist.GetBinContent(
                        best_point[0], best_point[1]) for name, hist in self.optimization_hists.items()}

                    significance = significance_hist.GetBinContent(
                        best_point[0], best_point[1])

                    contamination = self.contamination_hists[(mass, ctau)].GetBinContent(
                        best_point[0], best_point[1])

                    f.write(f"{mass}, {ctau}, {best_x:.2f}, {best_y:.2f}, ")
                    f.write(f"{values['closure']:.2f}, {values['error']:.2f}, ")
                    f.write(f"{values['min_n_events']:.1f}, {significance:.3f}, ")
                    f.write(f"{contamination:.2f}\n")

                    i_pad = 1 + i_mass * len(self.config.ctaus) + i_ctau

                    self.lines[i_pad] = (ROOT.TLine(best_x, self.config.variable_2_min, best_x, self.config.variable_2_max),
                                         ROOT.TLine(self.config.variable_1_min, best_y, self.config.variable_1_max, best_y))

                    self.lines[i_pad][0].SetLineColor(self.config.abcd_line_color)
                    self.lines[i_pad][1].SetLineColor(self.config.abcd_line_color)

                    self.lines[i_pad][0].SetLineWidth(self.config.abcd_line_width)
                    self.lines[i_pad][1].SetLineWidth(self.config.abcd_line_width)

                    self.canvases["grid"].cd(i_pad)
                    self.lines[i_pad][0].Draw()
                    self.lines[i_pad][1].Draw()

                    self.canvases["significance"].cd(i_pad)
                    self.lines[i_pad][0].Draw()
                    self.lines[i_pad][1].Draw()

            f.close()
            print(f"\nBest points saved to {file_path}\n")

    def plot_background_projections(self):
        self.true_projection_hist.SetLineColor(self.config.true_background_color)
        self.true_projection_hist.SetFillColorAlpha(self.config.true_background_color, 0.5)
        self.true_projection_hist.SetMarkerStyle(20)
        self.true_projection_hist.SetMarkerSize(0.2)
        self.true_projection_hist.SetMarkerColor(self.config.true_background_color)

        self.prediction_projection_hist.SetLineColor(self.config.predicted_background_color)
        self.prediction_projection_hist.SetMarkerStyle(20)
        self.prediction_projection_hist.SetMarkerSize(0.2)
        self.prediction_projection_hist.SetMarkerColor(self.config.predicted_background_color)

        self.projections_legend.AddEntry(self.true_projection_hist, self.config.true_background_description, "fl")
        self.projections_legend.AddEntry(self.prediction_projection_hist,
                                         self.config.predicted_background_description, "pl")

        self.projections_pads["main"].cd()
        self.true_projection_hist.Draw("PLE2")
        self.prediction_projection_hist.Draw("SAME PE")

        self.true_projection_hist.GetYaxis().SetRangeUser(0, self.config.y_max)
        self.true_projection_hist.GetYaxis().SetTitle(self.config.projection_y_title)
        self.true_projection_hist.GetYaxis().SetTitleOffset(1.2)
        self.true_projection_hist.GetYaxis().SetLabelSize(0.04)
        self.true_projection_hist.GetYaxis().SetTitleSize(0.04)

    def plot_signal_projections(self):
        for mass in self.config.masses:
            for ctau in self.config.ctaus:
                if (mass, ctau) not in self.signal_hists:
                    continue

                self.signal_projections[(mass, ctau)] = self.abcdHelper.get_projection_true(
                    self.signal_hists[(mass, ctau)])
                self.signal_projections[(mass, ctau)], _ = self.histogramsHelper.rebin(
                    self.signal_projections[(mass, ctau)], self.smart_binning)

                color = self.config.signal_colors[(mass, ctau)] if (
                    mass, ctau) in self.config.signal_colors else ROOT.kRed
                self.signal_projections[(mass, ctau)].SetLineColor(color)

                # normalize signal to background in A
                scale = self.true_projection_hist.Integral(
                )/self.signal_projections[(mass, ctau)].Integral() if self.signal_projections[(mass, ctau)].Integral() > 0 else 1
                self.signal_projections[(mass, ctau)].Scale(scale)

                self.signal_projections[(mass, ctau)].Draw("SAME")

                self.projections_legend.AddEntry(
                    self.signal_projections[(mass, ctau)],
                    f"Signal {mass} GeV, {ctau} mm", "l"
                )

        self.projections_legend.Draw()

    def plot_projections_ratio(self):
        self.projections_pads["ratio"].cd()

        self.ratio_hist = self.prediction_projection_hist.Clone()
        self.ratio_hist.SetTitle("")
        self.ratio_hist.Divide(self.true_projection_hist,
                               self.prediction_projection_hist, 1.0, 1.0, "B")

        self.ratio_hist_err = self.true_projection_hist.Clone()
        for i in range(1, self.ratio_hist_err.GetNbinsX() + 1):
            A = self.true_projection_hist.GetBinContent(i)
            err_A = self.true_projection_hist.GetBinError(i)

            if A > 0:
                err_ratio = ((err_A / A) ** 2 + (err_A / A) ** 2) ** 0.5
            else:
                err_ratio = 0

            self.ratio_hist_err.SetBinContent(i, 1)
            self.ratio_hist_err.SetBinError(i, err_ratio)

        self.ratio_hist_err.SetFillColorAlpha(ROOT.kRed, 0.5)

        self.ratio_hist.GetXaxis().SetTitle(
            self.abcdHelper.get_nice_name(self.config.variable_1))
        self.ratio_hist.GetXaxis().SetTitleOffset(1.1)
        self.ratio_hist.GetXaxis().SetLabelSize(0.1)
        self.ratio_hist.GetXaxis().SetTitleSize(0.1)

        self.ratio_hist.GetYaxis().SetTitle(self.config.ratio_y_title)
        self.ratio_hist.GetYaxis().SetTitleOffset(0.5)
        self.ratio_hist.GetYaxis().SetLabelSize(0.1)
        self.ratio_hist.GetYaxis().SetTitleSize(0.1)

        self.ratio_hist.Draw()
        self.ratio_hist_err.Draw("SAME PLE2")

        self.ratio_hist.GetYaxis().SetRangeUser(0, self.config.y_max_ratio)

    def save_canvases(self):
        line_x = ROOT.TLine(
            self.config.abcd_point[0], self.config.variable_2_min, self.config.abcd_point[0], self.config.variable_2_max)
        line_y = ROOT.TLine(self.config.variable_1_min,
                            self.config.abcd_point[1], self.config.variable_1_max, self.config.abcd_point[1])

        line_x.SetLineColor(self.config.abcd_line_color)
        line_x.SetLineWidth(self.config.abcd_line_width)

        line_y.SetLineColor(self.config.abcd_line_color)
        line_y.SetLineWidth(self.config.abcd_line_width)

        for key, canvas in self.canvases.items():
            
            if key in ["closure", "error", "min_n_events"]:
                canvas.cd()
                line_x.Draw()
                line_y.Draw()

            canvas.Update()
            canvas.SaveAs(f"{self.config.output_path}/abcd_hists_{key}.pdf")

    def print_params_for_selected_point(self):
        x_value, y_value = self.config.abcd_point

        x_index = self.optimization_hists["error"].GetXaxis().FindFixBin(x_value)
        y_index = self.optimization_hists["error"].GetYaxis().FindFixBin(y_value)

        a, b, c, d, a_err, b_err, c_err, d_err = self.abcdHelper.get_abcd(self.background_hist, self.config.abcd_point, values_instead_of_bins=True)

        print(f"\n\nSelected point: {x_value}, {y_value}")
        print(f"True background in A: {a:.2f} +/- {a_err:.2f}")

        closure = -1
        error = -1
        min_n_events = -1
        prediction = None

        if a > 0 and b > 0 and c > 0 and d > 0:
            prediction = c/d * b
            prediction_err = ((b_err/b)**2 + (c_err/c)** 2 + (d_err/d)**2)**0.5
            prediction_err *= prediction
            closure = self.abcdHelper.get_closure(a, prediction)
            error = self.abcdHelper.get_error(a, b, c, d, a_err, b_err, c_err, d_err, prediction)
            min_n_events = min(a, b, c, d)
            print(f"Predicted background in A: {prediction:.2f} +/- {prediction_err:.2f}")

        print("\n\nOptimization values:")
        print(f"Closure: {closure:.2f}, error: {error:.2f}, min_n_events: {min_n_events:.1f}")
        
        for mass in self.config.masses:
            for ctau in self.config.ctaus:
                if (mass, ctau) not in self.signal_hists:
                    continue

                hist = self.significance_hists[(mass, ctau)]

                x_index = hist.GetXaxis().FindFixBin(x_value)
                y_index = hist.GetYaxis().FindFixBin(y_value)

                print(f"Signal {mass} GeV, {ctau} mm:", end=" ")
                print(f"Significance: {hist.GetBinContent(x_index, y_index):.2f}", end=" ")
                print(f"Contamination: {self.contamination_hists[(mass, ctau)].GetBinContent(x_index, y_index):.2f}")

    def load_background_histograms(self):
        for path, cross_section in self.config.background_params:
            intput_path = self.config.background_path_pattern.format(path, self.config.skim, self.config.hist_dir)
            file_path = f"{self.config.base_path}/{intput_path}"

            self.background_files[path] = ROOT.TFile.Open(file_path)

            if not self.background_files[path]:
                print(f"Could not open file {file_path}")
                continue

            self.background_hists[path] = self.background_files[path].Get(self.hist_name)

            if not self.background_hists[path]:
                print(f"Could not open histogram {self.hist_name} in file {file_path}")
                continue

            inital_events = self.background_files[path].Get("cutFlow").GetBinContent(1)
            self.background_hists[path].Scale(self.config.lumi*cross_section/inital_events)

    def setup_backgrounds_sum_histogram(self):
        if self.config.do_data:
            file_path = f"{self.config.base_path}/{self.config.data_path}"
            self.data_file = ROOT.TFile.Open(file_path)
            
            if not self.data_file:
                print(f"Could not open file {file_path}")
                return
            
            self.background_hist = self.data_file.Get(self.hist_name)
            
            if not self.background_hist:
                print(f"Could not open histogram {self.hist_name} in file {file_path}")
                return
        else:
            self.background_hist = self.background_hists[self.config.background_params[0][0]].Clone()
            for path, _ in self.config.background_params[1:]:
                self.background_hist.Add(self.background_hists[path])

        self.background_hist.SetFillColorAlpha(self.config.background_color, 0.5)
        self.background_hist.SetTitle("")

    def load_signal_hists(self):
        for mass in self.config.masses:
            for ctau in self.config.ctaus:
                input_path = self.config.signal_path_pattern.format(mass, ctau, self.config.skim, self.config.hist_dir)

                try:
                    self.signal_files[input_path] = ROOT.TFile(f"{self.config.base_path}/{input_path}")
                except OSError:
                    continue

                self.signal_hists[(mass, ctau)] = self.signal_files[input_path].Get(self.hist_name)
                self.signal_hists[(mass, ctau)].SetName(f"signal_{mass}_{ctau}")
                self.signal_hists[(mass, ctau)].SetFillColorAlpha(self.config.signal_color, 0.5)

    def setup_canvases(self):
        self.canvases = {
            "grid": ROOT.TCanvas("grid", "grid", 1000, 1000),
            "significance": ROOT.TCanvas("significance", "significance", 1000, 1000),
            "closure": ROOT.TCanvas("closure", "closure", 200, 200),
            "error": ROOT.TCanvas("error", "error", 200, 200),
            "min_n_events": ROOT.TCanvas("min_n_events", "min_n_events", 200, 200),
            "projections": ROOT.TCanvas("projections", "projections", 200, 200),
        }

        for key in ["grid", "significance"]:
            self.canvases[key].Divide(
                len(self.config.ctaus), len(self.config.masses))

        for key in ["closure", "error", "min_n_events"]:
            self.canvases[key].cd()
            ROOT.gPad.SetLeftMargin(0.15)
            ROOT.gPad.SetRightMargin(0.25)
            ROOT.gPad.SetTopMargin(0.15)
            ROOT.gPad.SetBottomMargin(0.15)

        self.canvases["projections"].cd()

        self.projections_pads["main"] = ROOT.TPad("pad_main", "pad_main", 0, 0.3, 1, 1)
        self.projections_pads["main"].SetBottomMargin(0)
        self.projections_pads["main"].Draw()

        self.projections_pads["ratio"] = ROOT.TPad("pad_ratio", "pad_ratio", 0, 0, 1, 0.3)
        self.projections_pads["ratio"].SetTopMargin(0)
        self.projections_pads["ratio"].SetBottomMargin(0.3)
        self.projections_pads["ratio"].Draw()

    def set_pad_style(self):
        ROOT.gPad.SetLeftMargin(0.0)
        ROOT.gPad.SetRightMargin(0.0)
        ROOT.gPad.SetTopMargin(0.0)
        ROOT.gPad.SetBottomMargin(0.0)

    def setup_signal_hists(self):
        for mass in self.config.masses:
            for ctau in self.config.ctaus:
                if (mass, ctau) not in self.signal_hists:
                    continue

                self.significance_hists[(mass, ctau)] = self.abcdHelper.get_significance_hist(
                    self.signal_hists[(mass, ctau)], self.background_hist)

                self.contamination_hists[(mass, ctau)] = self.abcdHelper.get_signal_contramination_hist(
                    self.signal_hists[(mass, ctau)])
