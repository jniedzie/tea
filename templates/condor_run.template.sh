#!/bin/bash

export X509_USER_PROXY=`pwd`/voms_proxy

job_number=$1
echo "Executing job number $job_number"
cd <work_dir>
<python_path> condor_runner.py --app <app> --config <config> --file_index $job_number --input_files_file_name <input_files_list_file_name> <output_trees_dir> <output_hists_dir> <file_name> <extra_args>
