import json

goldenJsons = {}
input_paths = {
  "2016preVFP": "../tea/data/golden_json/Cert_271036-284044_13TeV_Legacy2016_Collisions16_JSON.txt",
  "2016postVFP": "../tea/data/golden_json/Cert_271036-284044_13TeV_Legacy2016_Collisions16_JSON.txt",
  "2017": "../tea/data/golden_json/Cert_294927-306462_13TeV_UL2017_Collisions17_GoldenJSON.txt",
  "2018": "../tea/data/golden_json/Cert_314472-325175_13TeV_Legacy2018_Collisions18_JSON.txt",
  "2022preEE": "../tea/data/golden_json/Cert_Collisions2022_355100_362760_Golden.txt",
  "2022postEE": "../tea/data/golden_json/Cert_Collisions2022_355100_362760_Golden.txt",
  "2023preBPix": "../tea/data/golden_json/Cert_Collisions2023_366442_370790_Golden.txt",
  "2023postBPix": "../tea/data/golden_json/Cert_Collisions2023_366442_370790_Golden.txt",
}

# read JSON file into a dictionary

for year, input_path in input_paths.items():
  with open(input_path) as f:
    goldenJsons[year] = json.load(f)
