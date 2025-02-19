import ROOT
import array


class ABCDHistogramsHelper:
    def __init__(self, config):
        self.config = config

    def rebin(self, hist, binning=None):
        if not self.config.smart_rebin and not self.config.custom_rebin:
            hist.Rebin(self.config.standard_rebin)
            return hist, None

        if binning is None:
            if self.config.custom_rebin and not self.config.smart_rebin:
                binning = self.config.custom_projections_binning
            elif self.config.smart_rebin and not self.config.custom_rebin:
                binning = self.__get_optimal_binning(hist)
            else:
                print("HistogramsHelper.rebin: Invalid rebinning configuration: ")
                print(f"smart_rebin: {self.config.smart_rebin}, custom_rebin: {self.config.custom_rebin}")
                print("Choose either smart_rebin, custom_rebin or none (then standard rebining will be done)")
                return None, None

        hist_new = ROOT.TH1D(
            hist.GetName() + "_rebin",
            hist.GetTitle() + "_rebin",
            len(binning) - 1,
            array.array('d', binning)
        )

        for i in range(1, hist.GetNbinsX() + 1):
            content = hist.GetBinContent(i)
            error = hist.GetBinError(i)
            bin_center = hist.GetBinCenter(i)

            # Find the corresponding new bin
            new_bin = hist_new.FindBin(bin_center)

            # Accumulate content and error in the new bin
            new_content = hist_new.GetBinContent(new_bin) + content
            new_error2 = hist_new.GetBinError(
                new_bin)**2 + error**2  # Sum of squares

            hist_new.SetBinContent(new_bin, new_content)
            hist_new.SetBinError(new_bin, new_error2**0.5)

        # hist_new.Sumw2()

        hist_new.SetLineColor(hist.GetLineColor())
        hist_new.SetMarkerStyle(hist.GetMarkerStyle())
        hist_new.SetMarkerSize(hist.GetMarkerSize())
        hist_new.SetMarkerColor(hist.GetMarkerColor())

        return hist_new, binning

    # ----------------------------------------------------------------------------------------------
    # Private methods
    # ----------------------------------------------------------------------------------------------

    def __get_optimal_binning(self, hist):
        nbins = hist.GetNbinsX()
        bin_edges = [hist.GetBinLowEdge(1)]  # Start with the first bin edge
        current_sum = 0
        current_error2 = 0  # Sum of squared errors

        for i in range(1, nbins + 1):
            content = hist.GetBinContent(i)
            error = hist.GetBinError(i)

            current_sum += content
            current_error2 += error**2

            #  if error is small enough, add the bin edge and start a new bin (reset)
            if current_sum > 0 and current_error2**0.5/current_sum < self.config.smart_rebin_max_error:
                bin_edges.append(hist.GetBinLowEdge(i))
                current_sum = content
                current_error2 = error**2

        bin_edges.append(hist.GetBinLowEdge(nbins + 1))

        return bin_edges
