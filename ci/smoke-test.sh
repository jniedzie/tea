#!/usr/bin/env bash
set -euo pipefail

bin_dir="${1:?install directory is required}"
source_dir="${2:?source directory is required}"
output_dir="${3:?output directory is required}"

mkdir -p "${output_dir}"
export PYTHONPATH="${bin_dir}${PYTHONPATH:+:${PYTHONPATH}}"
if [[ "$(uname -s)" == "Darwin" ]]; then
  export DYLD_LIBRARY_PATH="${bin_dir}${DYLD_LIBRARY_PATH:+:${DYLD_LIBRARY_PATH}}"
else
  export LD_LIBRARY_PATH="${bin_dir}${LD_LIBRARY_PATH:+:${LD_LIBRARY_PATH}}"
fi

"${bin_dir}/histogrammer" \
  --config "${source_dir}/configs/examples/histogrammer_config.py" \
  --input_path "${source_dir}/samples/background_dy.root" \
  --output_hists_path "${output_dir}/histograms.root"

"${bin_dir}/skimmer" \
  --config "${source_dir}/configs/examples/skimmer_config.py" \
  --input_path "${source_dir}/samples/background_dy.root" \
  --output_trees_path "${output_dir}/skim.root"

python3 - "${output_dir}/histograms.root" "${output_dir}/skim.root" <<'PY'
import sys
import ROOT

for path in sys.argv[1:]:
    root_file = ROOT.TFile.Open(path)
    if not root_file or root_file.IsZombie():
        raise SystemExit(f"Could not open smoke-test output: {path}")
    if not root_file.GetListOfKeys().GetSize():
        raise SystemExit(f"Smoke-test output is empty: {path}")
    root_file.Close()
PY
