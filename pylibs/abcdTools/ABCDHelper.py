from ctypes import c_double

class ABCDHelper:
    def __init__(self, config):
        self.config = config

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

        a_err = c_double(0)
        b_err = c_double(0)
        c_err = c_double(0)
        d_err = c_double(0)

        a = hist.IntegralAndError(1, point[0], point[1], hist.GetNbinsY(), a_err)
        b = hist.IntegralAndError(1, point[0], 1, point[1], b_err)
        c = hist.IntegralAndError(point[0], hist.GetNbinsX(), point[1], hist.GetNbinsY(), c_err)
        d = hist.IntegralAndError(point[0], hist.GetNbinsX(), 1, point[1], d_err)

        return a, b, c, d, a_err.value, b_err.value, c_err.value, d_err.value

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
        significance_hist.Scale(1/self.config.rebin_optimization**2)
        
        return significance_hist

    def get_signal_contramination_hist(self, signal_hist):
        signal_contamination_hist = signal_hist.Clone()
        signal_contamination_hist.SetTitle("")

        total_signal = signal_hist.Integral()

        for i in range(1, signal_contamination_hist.GetNbinsX() + 1):
            for j in range(1, signal_contamination_hist.GetNbinsY() + 1):
                n_signal_b = signal_hist.Integral(1, i, 1, j)
                n_signal_c = signal_hist.Integral(i, signal_contamination_hist.GetNbinsX(), j, signal_contamination_hist.GetNbinsY())
                n_signal_d = signal_hist.Integral(i, signal_contamination_hist.GetNbinsX(), 1, j)   
                n_signal = max(n_signal_b, n_signal_c, n_signal_d)
                signal_contamination_hist.SetBinContent(i, j, n_signal / total_signal if total_signal > 0 else 0)

        signal_contamination_hist.Rebin2D(self.config.rebin_optimization, self.config.rebin_optimization)
        signal_contamination_hist.Scale(1/self.config.rebin_optimization**2)
        return signal_contamination_hist

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

    def get_optimal_point(self, significance_hist, signal_contamination_hist, optimization_hists):
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

                values = {name: hist.GetBinContent(hist.FindBin(x_value, y_value)) for name, hist in optimization_hists.items()}

                signal_contamination = signal_contamination_hist.GetBinContent(signal_contamination_hist.FindBin(x_value, y_value))

                if values["error"] > self.config.max_error:
                    continue

                if values["closure"] > self.config.max_closure:
                    continue

                if values["min_n_events"] < self.config.min_n_events:
                    continue
                
                if signal_contamination > self.config.max_signal_contamination:
                    continue

                if significance > max_significance:
                    max_significance = significance
                    best_point = (i, j)

        return best_point

    def get_nice_name(self, name):
        return self.config.nice_names[name] if name in self.config.nice_names else name

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

        _, b, _, d, _, _, _, _ = self.get_abcd(
            hist, self.config.abcd_point, values_instead_of_bins=True)
        abcd_ratio = b/d if d > 0 else 1
        hist_prediction.Scale(abcd_ratio)

        return hist_prediction

    def get_closure(self, true, pred):
        closure = -1
        if true > 0:
            closure = abs(true - pred) / true
        return closure

    def get_error(self, a, b, c, d, a_err, b_err, c_err, d_err, prediction):
        error = -1
        
        prediction_err = ((b_err/b)**2 + (c_err/c)** 2 + (d_err/d)**2)**0.5
        prediction_err *= prediction

        if prediction_err > 0 and a_err > 0:
            error = abs(a - prediction)
            error /= (prediction_err**2 + a_err**2)**0.5
            
        return error

    # -----------------------------------------------------------------------
    # Private methods
    # -----------------------------------------------------------------------

    def __get_optimization_hist(self, background_hist, hist_type):
        optimization_hist = background_hist.Clone()

        optimization_hist.SetTitle("")

        for i in range(1, optimization_hist.GetNbinsX() + 1):
            for j in range(1, optimization_hist.GetNbinsY() + 1):

                a, b, c, d, a_err, b_err, c_err, d_err = self.get_abcd(background_hist, (i, j))

                closure = -1
                error = -1
                min_n_events = -1

                if a > 0 and b > 0 and c > 0 and d > 0:
                    prediction = c/d * b
                    closure = self.get_closure(a, prediction)
                    error = self.get_error(a, b, c, d, a_err, b_err, c_err, d_err, prediction)
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

        optimization_hist.Rebin2D(self.config.rebin_optimization, self.config.rebin_optimization)
        optimization_hist.Scale(1/self.config.rebin_optimization**2)

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
