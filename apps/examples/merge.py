import argparse
import os
import sys
import importlib.util

parser = argparse.ArgumentParser(description="Merge root files.")
parser.add_argument("--files_config", type=str, help="Path to the files config.")


args = parser.parse_args()

spec = importlib.util.spec_from_file_location("files_config", args.files_config)
files_config = importlib.util.module_from_spec(spec)
sys.modules["files_config"] = files_config
spec.loader.exec_module(files_config)

samples = files_config.samples
output_hist_dir = files_config.output_hists_dir

for sample in samples:
    input_files = f"{output_hist_dir}/{sample}/*.root"
    output_file = f"{output_hist_dir}/{sample}_histograms.root"
    
    command = f"hadd -f -j -k {output_file} {input_files}"
    print(f"Running command: {command}")
    os.system(command)
    