#!/bin/bash

set -euo pipefail

job_sandbox="$PWD"
<proxy_setup>
# Use the selected analysis runtime without inherited generator/ROOT settings.
unset PYTHONPATH PYTHONHOME LD_LIBRARY_PATH LD_PRELOAD ROOTSYS
<runtime_setup>

job_number=$1
echo "Executing job number $job_number"

cd <work_dir>
exec <python_path> condor_runner.py --app <app> --config <config> --file_index $job_number --input_files_file_name <input_files_list_file_name> <output_trees_dir> <output_hists_dir> <file_name> <extra_args>
