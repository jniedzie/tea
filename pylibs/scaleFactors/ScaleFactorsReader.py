import json
from Logger import *

class ScaleFactorsReader:
  def __init__(self):
    self.jsonSubLevelKey = "abseta_pt"
  
  def __getFile(self, filePath):
    file = None
    
    try:
      with open(filePath) as json_file:
        file = json.load(json_file)
    except FileNotFoundError:
      warn("Couldn't find the file: " + filePath + ". Trying to open the file without the tea path.")
      try:
        with open(filePath.replace("tea", "")) as json_file:
          file = json.load(json_file)
      except FileNotFoundError:
        fatal("Couldn't find the file: " + filePath + ".")
        exit(1)
    
    return file
  
  def getMuonScaleFactors(self, filePath):
    
    json_content = self.__getFile(filePath)
    
    result = {}
    
    for jsonTopLevelKey, values in json_content.items():
      muonSFs = {}
      abseta_pt_data = values[self.jsonSubLevelKey]
    
      if abseta_pt_data is None:
        fatal("Couldn't find the top level key in the JSON file: " + filePath)
        exit(1)
      
      for abseta_key, values_for_eta in abseta_pt_data.items():
        if "abseta" not in abseta_key:
          continue
        
        eta_bin = self.__stringToTuple(abseta_key.replace("abseta:", "").strip("[]"))      
        muonSFs[eta_bin] = {}
        
        for pt_key, values in values_for_eta.items():
          pt_bin = self.__stringToTuple(pt_key.replace("pt:", "").strip("[]"))        
          muonSFs[eta_bin][pt_bin] = values

      result[jsonTopLevelKey] = muonSFs

    return result
  
  def getMuonTriggerScaleFactors(self, filePath):
    
    json_content = self.__getFile(filePath)
    
    result = {}
    
    for object in json_content["corrections"]:
      if not self.__goodTriggerEntry(object):
        continue
      
      name = object["name"]
      eta_edges = object["data"]["edges"]
      muonSFs = {}
      
      for i_eta, eta_block in enumerate(object["data"]["content"]):
        eta_bin = (eta_edges[i_eta], eta_edges[i_eta+1])
        muonSFs[eta_bin] = {}
        
        pt_edges = eta_block["edges"]
        sf_values = self.__getTriggerSFvalues(eta_block["content"])
        
        for i_pt, sf in enumerate(sf_values):
          pt_bin = (pt_edges[i_pt], pt_edges[i_pt+1])
          muonSFs[eta_bin][pt_bin] = {}
          muonSFs[eta_bin][pt_bin]["value"] = sf
    
      result[name] = muonSFs

    return result

  def getBtaggingScaleFactors(self, filePath):
    
    json_content = self.__getFile(filePath)
    
    result = {}
    
    corrections = json_content["corrections"]
    
    for correction_dict in corrections:
      
      name = correction_dict["name"]
      if "deepJet_mujets" not in name:
        continue

      if "generic_formulas" in correction_dict:
        generic_formula = correction_dict["generic_formulas"][0]
        expression = generic_formula["expression"]
      
      data = correction_dict["data"]["content"]
      
      central_data = None
      
      for data_dict in data:
        if data_dict["key"] == "central":
          central_data = data_dict["value"]["content"]
          break
      
      if central_data is None:
        fatal("Couldn't find the central data in the JSON file: " + filePath)
        exit(1)
      
      for data_dict in central_data:
        wp_name = data_dict["key"]
        values_list = data_dict["value"]["content"]
        
        params = None
        
        for values_dict in values_list:
          jet_id = values_dict["key"]
          if jet_id == 5:
            params = values_dict["value"]["content"][0]["content"][0]["parameters"]
        
        if params is None:
          fatal("Couldn't find the parameters in the JSON file: " + filePath)
          exit(1)
        
        result[name+"_"+wp_name] = (expression, params)
    
    return result

  def __getTriggerSFvalues(self, data):
    sf_values = []
    
    for values in data:
      if values['input'] != "scale_factors":
        continue
      for scaleFactors in values["content"]:
        if scaleFactors["key"] == "nominal":
          sf_values.append(scaleFactors["value"])
    
    return sf_values

  def __goodTriggerEntry(self, object):
    has_charge = False
    has_eta = False
    
    for entry in object["inputs"]:
      if entry["name"] == "charge":
        has_charge = True
      
      if entry["name"] == "eta":
        has_eta = True
    
    if has_charge or not has_eta:
      return False
  
    return True

  def __stringToTuple(self, input_string):
    return (float(input_string.split(",")[0].strip()), float(input_string.split(",")[1].strip()))
