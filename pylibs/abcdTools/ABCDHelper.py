

class ABCDHelper:
    def __init__(self, config):
        self.config = config

        self.nice_names = {
            "Lxy": "L_{xy} (cm)",
            "LxySignificance": "L_{xy} significance",
            "absCollinearityAngle": "|#theta_{coll}|",
            "3Dangle": "#alpha_{3D}",
            "LogLxy": "log_{10}[L_{xy} (cm)]",
            "LogLxySignificance": "log_{10}[L_{xy} significance]",
            "LogAbsCollinearityAngle": "log_{10}[|#theta_{coll}|]",
            "Log3Dangle": "log_{10}[#alpha_{3D}]",
        }

    def get_abcd(self, hist, point, values_instead_of_bins=False):
        # The method returns the number of events in the four regions
        # of the ABCD plane, given a 2D histogram and a point in the
        # histogram. The point is a tuple (x, y) where x is the bin
        # number in the x-axis and y is the bin number in the y-axis.
        #
        # A  |  C
        # -------
        # B  |  D

        if values_instead_of_bins:
            point = (hist.GetXaxis().FindBin(
                point[0]), hist.GetYaxis().FindBin(point[1]))

        a = hist.Integral(1, point[0], point[1], hist.GetNbinsY())
        b = hist.Integral(1, point[0], 1, point[1])
        c = hist.Integral(point[0], hist.GetNbinsX(), point[1], hist.GetNbinsY())
        d = hist.Integral(point[0], hist.GetNbinsX(), 1, point[1])

        return a, b, c, d

    def get_significance_hist(self, signal_hist, background_hist):
        # The method returns a 2D histogram with the significance
        # of the signal over the background in each bin of the
        # 2D histogram. The significance is calculated as:
        #
        # significance = n_signal / sqrt(n_signal + n_background)

        significance_hist = signal_hist.Clone()
        significance_hist.SetTitle("")

        for i in range(1, significance_hist.GetNbinsX() + 1):
            for j in range(1, significance_hist.GetNbinsY() + 1):
                n_signal = signal_hist.Integral(1, i, 1, j)
                n_background = background_hist.Integral(1, i, 1, j)
                significance_hist.SetBinContent(
                    i, j, self.__get_significance(n_signal, n_background))

        significance_hist.Rebin2D(self.config.rebin_optimization, self.config.rebin_optimization)
        return significance_hist

    def get_optimization_hists(self, background_hist):
        # The method returns three 2D histograms with the optimization
        # parameters for each bin of the 2D histogram. The optimization
        # parameters are:
        #
        # - Closure: The percentage difference between the observed
        #   number of events in region A and the prediction using the
        #   other regions.
        #
        # - Error: The number of standard deviations between the observed
        #   number of events in region A and the prediction using the
        #   other regions.
        #
        # - Min N Events: The minimum number of events in the four regions
        #   of the ABCD plane.

        optimization_params = ("closure", "error", "min_n_events")
        optimization_hists = {name: self.__get_optimization_hist(
            background_hist, name) for name in optimization_params}

        return optimization_hists

    def get_optimal_point(self, significance_hist, optimization_hists):
        # Returns the bin with the highest significance that satisfies
        # the optimization criteria. The optimization criteria are:
        #
        # - The error is less than the maximum error.
        # - The closure is less than the maximum closure.
        # - The minimum number of events in the four regions is greater
        #   than the minimum number of events.
        #

        max_significance = 0
        best_point = None

        for i in range(1, significance_hist.GetNbinsX() + 1):
            for j in range(1, significance_hist.GetNbinsY() + 1):
                significance = significance_hist.GetBinContent(i, j)

                x_value = significance_hist.GetXaxis().GetBinCenter(i)
                y_value = significance_hist.GetYaxis().GetBinCenter(j)

                values = {name: hist.GetBinContent(hist.FindBin(
                    x_value, y_value)) for name, hist in optimization_hists.items()}

                if values["error"] > self.config.max_error:
                    continue

                if values["closure"] > self.config.max_closure:
                    continue

                if values["min_n_events"] < self.config.min_n_events:
                    continue

                if significance > max_significance:
                    max_significance = significance
                    best_point = (i, j)

        return best_point

    def get_nice_name(self, name):
        return self.nice_names[name]

    def get_projection_true(self, hist):
        hist_clone = hist.Clone()
        hist_clone.GetYaxis().SetRangeUser(self.config.abcd_point[1], self.config.variable_2_max)

        hist_true = hist_clone.ProjectionY(
            hist.GetName() + "_projection_true", 
            1,
            hist_clone.GetXaxis().FindBin(self.config.abcd_point[0])
        )
        return hist_true

    def get_projection_prediction(self, hist):
        hist_clone = hist.Clone()
        hist_clone.GetYaxis().SetRangeUser(self.config.abcd_point[1], self.config.variable_2_max)

        hist_prediction = hist_clone.ProjectionY(
            "projection_c",
            hist_clone.GetXaxis().FindBin(self.config.abcd_point[0]),
            hist_clone.GetNbinsX()
        )

        _, b, _, d = self.get_abcd(
            hist, self.config.abcd_point, values_instead_of_bins=True)
        abcd_ratio = b/d if d > 0 else 1
        hist_prediction.Scale(abcd_ratio)

        return hist_prediction

    # -----------------------------------------------------------------------
    # Private methods
    # -----------------------------------------------------------------------

    def __get_optimization_hist(self, background_hist, hist_type):
        optimization_hist = background_hist.Clone()

        optimization_hist.SetTitle("")

        for i in range(1, optimization_hist.GetNbinsX() + 1):
            for j in range(1, optimization_hist.GetNbinsY() + 1):

                a, b, c, d = self.get_abcd(background_hist, (i, j))

                closure = -1
                error = -1
                min_n_events = -1

                if a > 0 and b > 0 and c > 0 and d > 0:
                    prediction = c/d * b
                    closure = abs((a - prediction) / a * 100)

                    a_err = a**0.5
                    b_err = b**0.5
                    c_err = c**0.5
                    d_err = d**0.5

                    prediction_err = ((b_err/b)**2 + (c_err/c)
                                      ** 2 + (d_err/d)**2)**0.5
                    prediction_err *= prediction

                    if prediction_err > 0 and a_err > 0:
                        error = abs(a - prediction)
                        error /= (prediction_err**2 + a_err**2)**0.5

                    min_n_events = min(a, b, c, d)

                value = None

                if hist_type == "closure":
                    value = closure
                elif hist_type == "error":
                    value = error
                elif hist_type == "min_n_events":
                    value = min_n_events
                else:
                    print("ABCDHelper.__get_optimization_hist: ")
                    print(f"Invalid hist type: {hist_type}")
                    return None

                optimization_hist.SetBinContent(i, j, value)

        default_value = optimization_hist.GetMaximum() if hist_type != "min_n_events" else 0
        self.__replace_default_values(optimization_hist, default_value)

        optimization_hist.Rebin2D(
            self.config.rebin_optimization, self.config.rebin_optimization)

        return optimization_hist

    def __get_significance(self, n_signal, n_background):
        significance = 0.0
        if n_background > 0:
            significance = float(n_signal) / (n_signal + n_background)**0.5
        return significance

    def __replace_default_values(self, hist, default):
        for i in range(1, hist.GetNbinsX() + 1):
            for j in range(1, hist.GetNbinsY() + 1):
                if hist.GetBinContent(i, j) == -1:
                    hist.SetBinContent(i, j, default)
