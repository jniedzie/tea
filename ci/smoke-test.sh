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

skim_file = ROOT.TFile.Open(sys.argv[2])
events = skim_file.Get("Events")
n_entries = events.GetEntries()
if n_entries == 0:
    raise SystemExit("Smoke-test skim tree has no entries")

for branch_name in ("dimuonMass", "Muon_ptSquared", "muonPt"):
    if not events.GetBranch(branch_name):
        raise SystemExit(f"branchesToAdd branch missing from skim output: {branch_name}")

for i in range(n_entries):
    events.GetEntry(i)
    n_muon = events.nMuon
    if len(events.Muon_ptSquared) != n_muon:
        raise SystemExit(
            f"Muon_ptSquared length ({len(events.Muon_ptSquared)}) != nMuon ({n_muon}) at entry {i}"
        )

    if n_muon < 2 and events.dimuonMass != -1:
        raise SystemExit(
            f"dimuonMass ({events.dimuonMass}) != -1 for entry {i} with only {n_muon} muon(s)"
        )

    for j in range(n_muon):
        expected = events.Muon_pt[j] ** 2
        if abs(events.Muon_ptSquared[j] - expected) > max(1e-3, abs(expected) * 1e-5):
            raise SystemExit(
                f"Muon_ptSquared[{j}] ({events.Muon_ptSquared[j]}) != expected ({expected}) at entry {i}"
            )

    muon_pts = list(events.muonPt)
    if len(muon_pts) != n_muon:
        raise SystemExit(f"muonPt length ({len(muon_pts)}) != nMuon ({n_muon}) at entry {i}")
    for j in range(n_muon):
        expected = events.Muon_pt[j]
        if abs(muon_pts[j] - expected) > max(1e-3, abs(expected) * 1e-5):
            raise SystemExit(f"muonPt[{j}] ({muon_pts[j]}) != expected ({expected}) at entry {i}")
skim_file.Close()
PY
