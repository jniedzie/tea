import json

goldenJsons = {}
input_path_2018 = "../tea/data/golden_json/Cert_314472-325175_13TeV_Legacy2018_Collisions18_JSON.txt"
input_path_2022 = "../tea/data/golden_json/Cert_Collisions2022_355100_362760_Golden.txt"
input_path_2023 = "../tea/data/golden_json/Cert_Collisions2023_366442_370790_Golden.txt"

# read JSON file into a dictionary
with open(input_path_2018) as f:
  goldenJsons["2018"] = json.load(f)

with open(input_path_2022) as f:
  goldenJsons["2022"] = json.load(f)

with open(input_path_2023) as f:
  goldenJsons["2023"] = json.load(f)
