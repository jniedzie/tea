import json

input_path = "../tea/data/golden_json/Cert_314472-325175_13TeV_Legacy2018_Collisions18_JSON.txt"
# input_path = "../tea/data/golden_json/Cert_Collisions2022_355100_362760_Golden.txt"
# input_path = "../tea/data/golden_json/Cert_Collisions2023_366442_370790_Golden.txt"

# read JSON file into a dictionary
with open(input_path) as f:
  goldenJson = json.load(f)
