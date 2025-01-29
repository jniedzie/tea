import os
import importlib.util
import uuid
from enum import Enum

from Logger import *

class SubmissionSystem(Enum):
  local = 1
  condor = 2
  unknown = 3

class SubmissionManager:
  def __init__(self, submission_system, app_name, config_path, files_config_path):
    self.app_name = app_name
    self.config_path = config_path
    self.files_config_path = files_config_path
    self.files_config = None
    self.extra_args = None
    
    info(f"Submission system: {submission_system.name}")
    
    self.__setup_files_config()

    if hasattr(self.files_config, "extra_args"):
      self.extra_args = self.files_config.extra_args

    if submission_system == SubmissionSystem.condor:
      self.__create_condor_directories()
  
  def run_locally(self):
    executor = f"python3 " if self.app_name[-3:] == ".py" else f"./"
    self.command = f"{executor}{self.app_name} --config {self.config_path}"
    
    if hasattr(self.files_config, "output_dir"): # option 1 & 3, 4, 5
      self.__run_local_with_output_dir()
    elif hasattr(self.files_config, "input_output_file_list"): # option 2
      self.__run_local_input_output_list()
    elif hasattr(self.files_config, "output_hists_dir") or hasattr(self.files_config, "output_trees_dir"):
      self.__run_local_with_output_dirs()
    else:
      error("SubmissionManager -- Unrecognized input/output option")
  
  def run_condor(self, job_flavour, memory_request, materialize_max, resubmit_job, dry):
    info("Running on condor")
    
    self.job_flavour = job_flavour
    self.memory_request = memory_request
    self.materialize_max = materialize_max
    self.resubmit_job = resubmit_job
    

    self.__setup_temp_file_paths()
    self.__copy_templates()
    
    input_files = self.__get_intput_file_list()
    self.__save_file_list_to_file(input_files)
    self.__set_condor_script_variables(len(input_files))
    self.__set_run_script_variables()
    
    command = f"condor_submit {self.condor_config_name}"
    info(f"Submitting to condor: {command}")
    
    if not dry:  
      os.system(command)
  
  def __create_dir_if_not_exists(self, dir_path):
    if not os.path.exists(dir_path):
      os.makedirs(dir_path)
  
  def __create_condor_directories(self):
    for path in ("error", "log", "output", "tmp"):
      self.__create_dir_if_not_exists(path)
    
  def __setup_files_config(self):
    if self.files_config_path is None:
      fatal("Please provide a files config")
      exit()
    
    info(f"Reading files config from path: {self.files_config_path}")
    spec = importlib.util.spec_from_file_location("files_module", self.files_config_path)
    
    if spec is None:
      fatal(f"Couldn't load config from path: {self.files_config_path}")
      exit()
    
    self.files_config = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(self.files_config)
  
  def __run_command(self, command):
    info(f"\n\nExecuting {command=}")
    os.system(command)
  
  def __get_das_files_list(self, dataset_name):
    dbs_command = ""
    if hasattr(self.files_config, "dbs_instance"):
      dbs_command = f"instance={self.files_config.dbs_instance}"
    das_command = f"dasgoclient -query='file dataset={dataset_name} {dbs_command}'"
    info(f"\n\nExecuting {das_command=}")
    return os.popen(das_command).read().splitlines()
  
  def __get_intput_file_list(self):
    if hasattr(self.files_config, "dataset"):
      max_files = getattr(self.files_config, "max_files", -1)
      files = self.__get_das_files_list(self.files_config.dataset)
      if max_files > 0:
        return files[:max_files]
      return files
    
    if hasattr(self.files_config, "input_file_list"):
      return self.files_config.input_file_list
    
    if hasattr(self.files_config, "input_directory"):
      return os.popen(f"find {self.files_config.input_directory} -maxdepth 1 -name '*.root'").read().splitlines()
    
    fatal("Unrecognized option")
    exit()
  
  # option 1 & 3, 4, 5
  def __run_local_with_output_dir(self):
    
    input_file_list = self.__get_intput_file_list()
    
    if hasattr(self.files_config, "file_name"):
      file_name = self.files_config.file_name
      path = "/".join(input_file_list[0].strip().split("/")[:-1])
      input_file_list = [f"{path}/{file_name}"]
    
    max_files = -1
    if hasattr(self.files_config, "max_files"):
      max_files = self.files_config.max_files
    
    for i, input_file_path in enumerate(input_file_list):
      if max_files > 0 and i >= max_files:
        return
      
      input_file_name = input_file_path.strip().split("/")[-1]
      os.system(f"mkdir -p {self.files_config.output_dir}")
      output_file_path = f"{self.files_config.output_dir}/{input_file_name}"
      command_for_file = f"{self.command} --input_path {input_file_path} --output_path {output_file_path}"
      
      if self.extra_args is not None:
        for key, value in self.extra_args.items():
          command_for_file += f" --{key} {value}"
      
      self.__run_command(command_for_file)
      
  def __run_local_with_output_dirs(self):
    
    input_file_list = self.__get_intput_file_list()
    
    if hasattr(self.files_config, "file_name"):
      file_name = self.files_config.file_name
      path = "/".join(input_file_list[0].strip().split("/")[:-1])
      input_file_list = [f"{path}/{file_name}"]
    
    max_files = -1
    if hasattr(self.files_config, "max_files"):
      max_files = self.files_config.max_files

    output_trees = hasattr(self.files_config, "output_trees_dir")
    output_hists = hasattr(self.files_config, "output_hists_dir")
    
    for i, input_file_path in enumerate(input_file_list):
      if max_files > 0 and i >= max_files:
        return
      
      input_file_name = input_file_path.strip().split("/")[-1]
      if output_trees:
        os.system(f"mkdir -p {self.files_config.output_trees_dir}")
      if output_hists:
        os.system(f"mkdir -p {self.files_config.output_hists_dir}")
      
      output_tree_file_path = f"{self.files_config.output_trees_dir}/{input_file_name}" if output_trees else ""
      output_hist_file_path = f"{self.files_config.output_hists_dir}/{input_file_name}" if output_hists else ""
      command_for_file = f"{self.command} --input_path {input_file_path}" 
      command_for_file += f" --output_trees_path {output_tree_file_path}" if output_trees else ""
      command_for_file += f" --output_hists_path {output_hist_file_path}" if output_hists else ""
      if self.extra_args is not None:
        for key, value in self.extra_args.items():
          command_for_file += f" --{key} {value}"
      self.__run_command(command_for_file)
  
  # option 2
  def __run_local_input_output_list(self):
    info("Running locally with input_output_file_list")
    for input_file_path, output_file_path in self.files_config.input_output_file_list:
      # command_for_file = f"{self.command} --input_path {input_file_path} --output_path {output_file_path}" 
      command_for_file = f"{self.command} --input_path {input_file_path}" 
      command_for_file += f" --output_trees_path {output_tree_file_path}"
      command_for_file += f" --output_hists_path {output_hist_file_path}"
      if self.extra_args is not None:
        for key, value in self.extra_args.items():
          command_for_file += f" --{key} {value}"
      self.__run_command(command_for_file)
        
  def __setup_temp_file_paths(self):
    hash_string = str(uuid.uuid4().hex[:6])
    self.condor_config_name = f"tmp/condor_config_{hash_string}.sub"
    self.condor_run_script_name = f"tmp/condor_run_{hash_string}.sh"
    self.input_files_list_file_name = f"tmp/input_files_{hash_string}.txt"
    
  def __copy_templates(self):
    os.system(f"cp ../tea/templates/condor_config.template.sub {self.condor_config_name}")
    os.system(f"cp ../tea/templates/condor_run.template.sh {self.condor_run_script_name}")
    os.system(f"chmod 700 {self.condor_run_script_name}")
    info(f"Stored condor config at: {self.condor_config_name}")
    info(f"Stored run shell script at: {self.condor_run_script_name}")
    
  def __save_file_list_to_file(self, input_files):
    with open(self.input_files_list_file_name, "w") as file:
      for input_file_path in input_files:
        file.write(f"{input_file_path}\n")
  
  def __setup_voms_proxy(self):
    voms_proxy_path = os.popen("voms-proxy-info -path").read().strip().replace("/", "\/")    
    os.system(f"cp {voms_proxy_path} voms_proxy")
    os.system(f"sed -i 's/<voms_proxy>/{voms_proxy_path}/g' {self.condor_run_script_name}")
  
  def __set_python_executable(self):
    python_executable = os.popen("which python3").read().strip()
    python_executable = python_executable.replace("/", "\/")
    os.system(f"sed -i 's/<python_path>/{python_executable}/g' {self.condor_run_script_name}")
  
  def __set_run_script_variables(self):
    self.__setup_voms_proxy()
    
    # set file name
    if hasattr(self.files_config, "file_name"):
      os.system(f"sed -i 's/<file_name>/--file_name {self.files_config.file_name}/g' {self.condor_run_script_name}")
    else:
      os.system(f"sed -i 's/<file_name>//g' {self.condor_run_script_name}")
    
    # set working directory
    workDir = os.getcwd().replace("/", "\/")
    os.system(f"sed -i 's/<work_dir>/{workDir}/g' {self.condor_run_script_name}")
    
    self.__set_python_executable()
    
    # set the app and app config to execute
    os.system(f"sed -i 's/<app>/{self.app_name}/g' {self.condor_run_script_name}")
    config_path_escaped = self.config_path.replace("/", "\/")
    os.system(f"sed -i 's/<config>/{config_path_escaped}/g' {self.condor_run_script_name}")
    
    # set path to the list of input files
    input_files_list_file_name_escaped = self.input_files_list_file_name.replace("/", "\/")
    os.system(f"sed -i 's/<input_files_list_file_name>/{input_files_list_file_name_escaped}/g' {self.condor_run_script_name}")
    
    # set output directory
    output_trees_dir = ""
    output_hists_dir = ""
    output_trees = hasattr(self.files_config, "output_trees_dir")
    output_hists = hasattr(self.files_config, "output_hists_dir")
    if hasattr(self.files_config, "output_trees_dir"):
      if self.files_config.output_trees_dir != "" :
        output_trees_dir = "--output_trees_dir " + self.files_config.output_trees_dir.replace("/", "\/")
    if hasattr(self.files_config, "output_hists_dir"):
      if self.files_config.output_hists_dir != "" :
        output_hists_dir = "--output_hists_dir " + self.files_config.output_hists_dir.replace("/", "\/")
    os.system(f"sed -i 's/<output_trees_dir>/{output_trees_dir}/g' {self.condor_run_script_name}")
    os.system(f"sed -i 's/<output_hists_dir>/{output_hists_dir}/g' {self.condor_run_script_name}")
    
    extra_args = ""
    if self.extra_args is not None:
        for key, value in self.extra_args.items():
          if isinstance(value, str):
            value = value.replace("/", "\/")
          extra_args += f" --{key} {value}"
    
    print(f"{extra_args=}")
    
    os.system(f"sed -i 's/<extra_args>/{extra_args}/g' {self.condor_run_script_name}")
    
  def __set_condor_script_variables(self, n_files):
    condor_run_script_name_escaped = self.condor_run_script_name.replace("/", "\/")
    os.system(f"sed -i 's/<executable>/{condor_run_script_name_escaped}/g' {self.condor_config_name}")
    os.system(f"sed -i 's/<memory_request>/{self.memory_request}/g' {self.condor_config_name}")
    os.system(f"sed -i 's/<job_flavour>/{self.job_flavour}/g' {self.condor_config_name}")
    os.system(f"sed -i 's/<materialize_max>/{self.materialize_max}/g' {self.condor_config_name}")
  
    if self.resubmit_job is not None:
      os.system(f"sed -i 's/$(ProcId)/{self.resubmit_job}/g' {self.condor_config_name}")
      os.system(f"sed -i 's/<n_jobs>/1/g' {self.condor_config_name}")
    elif hasattr(self.files_config, "file_name"):
      os.system(f"sed -i 's/<n_jobs>/1/g' {self.condor_config_name}")
    else:
      max_files = n_files
      if hasattr(self.files_config, "max_files"):
        max_files = self.files_config.max_files if self.files_config.max_files != -1 else n_files
      os.system(f"sed -i 's/<n_jobs>/{max_files}/g' {self.condor_config_name}")
    

