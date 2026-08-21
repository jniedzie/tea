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

"${bin_dir}/histogrammer" \
  --config "${source_dir}/templates/config.template.py" \
  --input_path "${source_dir}/samples/background_dy.root" \
  --output_hists_path "${output_dir}/zero-selectors.root"

python3 - "${output_dir}/histograms.root" "${output_dir}/skim.root" "${output_dir}/zero-selectors.root" \
  "${source_dir}/samples/background_dy.root" <<'PY'
import sys
import ROOT

for path in sys.argv[1:4]:
    root_file = ROOT.TFile.Open(path)
    if not root_file or root_file.IsZombie():
        raise SystemExit(f"Could not open smoke-test output: {path}")
    if not root_file.GetListOfKeys().GetSize():
        raise SystemExit(f"Smoke-test output is empty: {path}")
    root_file.Close()

input_file = ROOT.TFile.Open(sys.argv[4])
events = input_file.Get("Events")
expected_zero = 0
for event_index, event in enumerate(events):
    if event_index == 100:
        break
    expected_zero += sum(not bool(value) for value in event.Muon_isGlobal)

selector_file = ROOT.TFile.Open(sys.argv[3])
range_hist = selector_file.Get("NonGlobalMuonsByRange_isGlobal")
scalar_hist = selector_file.Get("NonGlobalMuons_isGlobal")
if not range_hist or not scalar_hist:
    raise SystemExit("Missing zero-selector regression histograms")

range_entries = int(range_hist.GetEntries())
scalar_entries = int(scalar_hist.GetEntries())
if range_entries != expected_zero or scalar_entries != expected_zero:
    raise SystemExit(
        "Zero-selector regression failed: "
        f"expected {expected_zero}, range selected {range_entries}, scalar selected {scalar_entries}"
    )

selector_file.Close()
input_file.Close()
PY
