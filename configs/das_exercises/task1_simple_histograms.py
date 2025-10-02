# Task 1
#
# Objectives:
# - Produce a ROOT file with histograms of pT and η of all muons in all events using only one input file.
# - Do it for tt semileptonic background sample and for 12 GeV, 100 mm ALP signal.
#
# Hints:
# - The input files are called "output_0.root".
# - The collection name for muons in nanoAOD is "Muon".
# - Check the `base_path` to see where the input files are located.

# The number of events to process. -1 means all events.
nEvents = -1

base_path = "/eos/cms/store/group/committee_schools/2025-cmsdas-hamburg/llp/samples/"

# Fill in these paths. The output path must be some directory where you can write - I recommend that you store it inside of your project directory.
inputFilePath = f"{base_path}/..."
histogramsOutputFilePath = "../results/..."

# You'll need to add some histogram parameters here.
defaultHistParams = (
  #  collection      variable          bins    xmin     xmax     dir
  ("Event", "nMuon", 50, 0, 50, ""),
)

# No need to change this - this is the branch name for event weights in nanoAOD.
weightsBranchName = "genWeight"
