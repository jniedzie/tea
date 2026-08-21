nEvents = 1000

inputFilePath = "../tea/samples/background_dy.root"
histogramsOutputFilePath = "../results/minimal_histograms.root"

# fmt: off
defaultHistParams = (
  #  collection      variable          bins    xmin     xmax     dir
  ("Electron",       "pt",             40,     0,       200,     ""),
  ("Electron",       "eta",            50,    -2.5,      2.5,    ""),
)
# fmt: on
