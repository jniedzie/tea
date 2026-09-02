#!/bin/bash

# The proxy lives in the submit directory (copied there by SubmissionManager). Condor may
# or may not have transferred it into the job's scratch directory, so probe both places
# rather than pointing X509_USER_PROXY at a path that does not exist on this node.
if [ -f "$PWD/voms_proxy" ]; then
  export X509_USER_PROXY="$PWD/voms_proxy"
elif [ -f "<work_dir>/voms_proxy" ]; then
  export X509_USER_PROXY="<work_dir>/voms_proxy"
fi

job_number=$1
echo "Executing job number $job_number"

# needed to trick condor on EOS with "-spool" option to transfer some output file
touch condor_dummy.out

cd <work_dir>
<python_path> condor_runner.py --app <app> --config <config> --facility <facility> --file_index $job_number --input_files_file_name <input_files_list_file_name> <output_trees_dir> <output_hists_dir> <file_name> <extra_args>
