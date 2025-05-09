from ScaleFactorProducer import ScaleFactorProducer
from CorrectionWriter import CorrectionWriter
from Logger import *

from ROOT import gROOT
import importlib
import sys, os


def getConfig():
    configPath = sys.argv[1]
    if (".py" in configPath):
        configPath = configPath[:-3]
    config = importlib.import_module(configPath)
    return config


def main():
  
    gROOT.SetBatch(True)

    config = getConfig()
    sfProducer = ScaleFactorProducer(config)
    correctionWriter = CorrectionWriter()
    scale_factors = {}

    info("Calculating scale factors...")
    for sfBin, histogram in config.histograms.items():
        background_stack = sfProducer.getBackgroundStack(histogram)
        data_hist = sfProducer.getDataHist(histogram)
        if data_hist is None:
            warn(f"Data histogram not found for {sfBin}. Skipping...")
            continue

        data_yield, data_uncertainty_down, data_uncertainty_up = sfProducer.getYieldAndAsymmetricUncertainties(data_hist)
        background_yield, background_uncertainty_down, background_uncertainty_up = sfProducer.getYieldAndAsymmetricUncertainties(background_stack.GetStack().Last())

        ratio,ratio_uncertainty_down,ratio_uncertainty_up = sfProducer.getDataMCRatio(data_yield, data_uncertainty_down, data_uncertainty_up, background_yield, background_uncertainty_down, background_uncertainty_up)
        scale_factors[sfBin] = [ratio, ratio_uncertainty_up, ratio_uncertainty_down]


    info("Writing corrections...")
    include_variations = False
    for input in config.correction_inputs:
        if input["name"] == "scale_factors":
            include_variations = True
            break

    correction_sfs = []
    for sfBin, sf in scale_factors.items():
        if include_variations:
            correction_sfs.append(sf)
        else:
            correction_sfs.append(sf[0])

    if include_variations:
        info("Writing corrections including variations.")
    else:
        info("Writing corrections without variations. To include variations add 'scale_factors' in correction_inputs.")

    correctionWriter.add_multibinned_correction_for_config(config, correction_sfs)
    correctionWriter.save_json(config.output_name)
    logger_print()

if __name__ == "__main__":
    main()