# option 1: list input files and one output directory
# output files will have the same name as inputs, but be stored the output_dir
# input_file_list = (
#   "../samples/background_dy.root",
#   "../samples/background_tt.root"
#   "../samples/signal_ttz.root"
#   "../samples/data.root"
# )
# output_dir = "../samples/skimmed"


# option 2: list input files and output files (2 paths for trees and hists, respectively - if only one is needed, set the other to "")
# input_output_file_list = (
#   ("../samples/background_dy.root", "../samples/background_dy_skimmed.root", ""),
#   ("../samples/background_tt.root", "../samples/background_tt_skimmed.root", ""),
#   ("../samples/signal_ttz.root", "../samples/signal_ttz_skimmed.root", ""),
#   ("../samples/data.root", "../samples/data_skimmed.root", ""),
# )


# option 3: give DAS dataset name and output path: will run for all files in dataset (or up to max_files)
# dataset = "/TTTo2L2Nu_TuneCP5_13TeV-powheg-pythia8/RunIIAutumn18NanoAODv7-Nano02Apr2020_102X_upgrade2018_realistic_v21-v1/NANOAODSIM"
# output_dir = "../samples/skim"
# max_files = 2


# option 4: give DAS dataset name, output path and specify a particular file name you want to run on
# dataset = "/TTTo2L2Nu_TuneCP5_13TeV-powheg-pythia8/RunIIAutumn18NanoAODv7-Nano02Apr2020_102X_upgrade2018_realistic_v21-v1/NANOAODSIM"
# output_dir = "../samples/skim"
# file_name = "8ED6072D-6880-724A-A0E2-A57C700C78CC.root"


# option 5: only specify local input and output directories
input_directory = "../samples"
output_dir = "../samples/histograms"
