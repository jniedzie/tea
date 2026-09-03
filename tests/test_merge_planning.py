"""merge.py planning logic: merge targets, sample directories, chunking, input_files guards."""

import os
import sys
import types

import pytest

import merge


def make_files_config(**attributes):
  files_config = types.SimpleNamespace(**attributes)
  return files_config


def run_main_with_config(monkeypatch, tmp_path, files_config):
  """Drive merge.main() far enough to hit the config validation, and no further."""
  config_path = tmp_path / "files_config.py"
  config_path.write_text("")
  monkeypatch.setattr(merge, "load_files_config", lambda path: files_config)
  monkeypatch.setattr(sys, "argv", ["merge.py", "--files_config", str(config_path), "--dry"])
  merge.main()


def test_get_merge_targets_lists_both_kinds():
  files_config = make_files_config(output_hists_dir="/base/hists", output_trees_dir="/base/trees")
  assert merge.get_merge_targets(files_config) == [
    ("histograms", "/base/hists"),
    ("trees", "/base/trees"),
  ]


def test_get_merge_targets_skips_empty_dirs():
  # A hist-only stage sets output_trees_dir = "". Taking that literally used to plan a
  # phantom "./_merged" trees job that globs the current working directory.
  files_config = make_files_config(output_hists_dir="/base/hists", output_trees_dir="")
  assert merge.get_merge_targets(files_config) == [("histograms", "/base/hists")]


def test_get_merge_targets_skips_none_dirs():
  files_config = make_files_config(output_hists_dir=None, output_trees_dir="/base/trees")
  assert merge.get_merge_targets(files_config) == [("trees", "/base/trees")]


def test_build_sample_dir_inserts_the_sample_above_the_leaf():
  assert merge.build_sample_dir("/base/results-unmerged", "DYto2L") == "/base/DYto2L/results-unmerged"


def test_build_sample_dir_appends_when_there_is_no_parent():
  assert merge.build_sample_dir("results", "DYto2L") == "results/DYto2L"


def test_chunk_files_splits_into_batches_of_at_most_chunk_size():
  assert merge.chunk_files(["a", "b", "c", "d", "e"], 2) == [["a", "b"], ["c", "d"], ["e"]]


def test_chunk_files_of_an_empty_list_is_empty():
  assert merge.chunk_files([], 3) == []


def test_input_files_must_not_be_empty(monkeypatch, tmp_path):
  files_config = make_files_config(input_files=[], output_hists_dir=str(tmp_path / "hists"))
  with pytest.raises(ValueError, match="non-empty"):
    run_main_with_config(monkeypatch, tmp_path, files_config)


def test_input_files_must_all_exist(monkeypatch, tmp_path):
  existing = tmp_path / "a.root"
  existing.write_text("a")
  files_config = make_files_config(
    input_files=[str(existing), str(tmp_path / "missing.root")],
    output_hists_dir=str(tmp_path / "hists"),
  )
  with pytest.raises(ValueError, match="do not exist"):
    run_main_with_config(monkeypatch, tmp_path, files_config)


def test_input_files_rejects_a_repeated_path(monkeypatch, tmp_path):
  existing = tmp_path / "a.root"
  existing.write_text("a")
  files_config = make_files_config(
    input_files=[str(existing), str(existing)],
    output_hists_dir=str(tmp_path / "hists"),
  )
  with pytest.raises(ValueError, match="more than once"):
    run_main_with_config(monkeypatch, tmp_path, files_config)


def test_input_files_rejects_a_symlinked_duplicate(monkeypatch, tmp_path):
  # results-unmerged/ is itself a symlink, so two tag vintages can name one file through
  # textually distinct paths; hadd would double-count its events and still exit 0.
  real_dir = tmp_path / "vintage_a"
  real_dir.mkdir()
  real_file = real_dir / "ntuple_0.root"
  real_file.write_text("a")
  link_dir = tmp_path / "vintage_b"
  link_dir.symlink_to(real_dir)

  files_config = make_files_config(
    input_files=[str(real_file), str(link_dir / "ntuple_0.root")],
    output_hists_dir=str(tmp_path / "hists"),
  )
  with pytest.raises(ValueError, match="more than once"):
    run_main_with_config(monkeypatch, tmp_path, files_config)


def test_input_files_cannot_be_combined_with_samples(monkeypatch, tmp_path):
  existing = tmp_path / "a.root"
  existing.write_text("a")
  files_config = make_files_config(
    input_files=[str(existing)],
    samples=["DYto2L"],
    output_hists_dir=str(tmp_path / "hists"),
  )
  with pytest.raises(ValueError, match="samples list"):
    run_main_with_config(monkeypatch, tmp_path, files_config)


def test_input_files_cannot_be_combined_with_two_merge_targets(monkeypatch, tmp_path):
  existing = tmp_path / "a.root"
  existing.write_text("a")
  files_config = make_files_config(
    input_files=[str(existing)],
    output_hists_dir=str(tmp_path / "hists"),
    output_trees_dir=str(tmp_path / "trees"),
  )
  with pytest.raises(ValueError, match="exactly one"):
    run_main_with_config(monkeypatch, tmp_path, files_config)


def test_input_files_are_sorted_into_a_deterministic_plan(monkeypatch, tmp_path, capsys):
  # The glob branch gets its determinism from sorted(glob.glob(...)); an explicit list has
  # to be sorted too, or the chunk -> ntuple_N.root mapping depends on config order.
  for name in ("c.root", "a.root", "b.root"):
    (tmp_path / name).write_text(name)

  files_config = make_files_config(
    input_files=[str(tmp_path / "c.root"), str(tmp_path / "a.root"), str(tmp_path / "b.root")],
    output_hists_dir=str(tmp_path / "hists"),
  )
  run_main_with_config(monkeypatch, tmp_path, files_config)

  printed_inputs = [line.split("input: ")[1] for line in capsys.readouterr().out.splitlines() if "input: " in line]
  assert printed_inputs == [str(tmp_path / name) for name in ("a.root", "b.root", "c.root")]


def test_merge_targets_are_required(monkeypatch, tmp_path):
  files_config = make_files_config(samples=["DYto2L"])
  with pytest.raises(ValueError, match="output_hists_dir"):
    run_main_with_config(monkeypatch, tmp_path, files_config)


def test_empty_output_dirs_alone_are_not_a_merge_target(monkeypatch, tmp_path):
  files_config = make_files_config(output_hists_dir="", output_trees_dir="")
  with pytest.raises(ValueError, match="output_hists_dir"):
    run_main_with_config(monkeypatch, tmp_path, files_config)
  assert not os.path.exists(os.path.join(os.getcwd(), "_merged"))


# --- Remote (LFN) inputs and outputs ------------------------------------------------


class FakeCompletedProcess:
  def __init__(self, returncode=0, stdout="", stderr=""):
    self.returncode = returncode
    self.stdout = stdout
    self.stderr = stderr


XRDFS_LISTING = (
  "-rw-r--r--        2026-08-27 14:03:03     13930949 /store/user/u/hists/ntuple_0.root\n"
  "-rw-r--r--        2026-08-27 14:04:11      1048576 /store/user/u/hists/ntuple_1.root\n"
  "drwxr-xr-x        2026-08-27 14:04:11            0 /store/user/u/hists/subdir\n"
  "-rw-r--r--        2026-08-27 14:05:00          512 /store/user/u/hists/log.txt\n"
)


def test_list_input_files_reads_sizes_out_of_the_remote_listing(monkeypatch):
  # One `ls -l` rather than a stat per file: the scratch estimate needs every size, and a
  # sample directory can hold thousands of files.
  commands = []

  def fake_run(command, **kwargs):
    commands.append(command)
    return FakeCompletedProcess(stdout=XRDFS_LISTING)

  monkeypatch.setattr(merge.subprocess, "run", fake_run)
  paths, sizes = merge.list_input_files("/store/user/u/hists", "*.root", "maite.iihe.ac.be:1094")

  assert commands == [["xrdfs", "root://maite.iihe.ac.be:1094", "ls", "-l", "/store/user/u/hists"]]
  assert paths == ["/store/user/u/hists/ntuple_0.root", "/store/user/u/hists/ntuple_1.root"]
  assert sizes["/store/user/u/hists/ntuple_0.root"] == 13930949


def test_list_input_files_treats_an_absent_remote_directory_as_empty(monkeypatch):
  # A sample with nothing merged yet must behave as it does on a POSIX path, where
  # glob.glob simply finds nothing.
  monkeypatch.setattr(
    merge.subprocess,
    "run",
    lambda command, **kwargs: FakeCompletedProcess(
      returncode=54, stderr="[ERROR] Server responded with an error: [3011] No such file or directory\n"
    ),
  )
  assert merge.list_input_files("/store/user/u/absent", "*.root", "door:1094") == ([], {})


def test_list_input_files_raises_on_any_other_xrdfs_failure(monkeypatch):
  monkeypatch.setattr(
    merge.subprocess,
    "run",
    lambda command, **kwargs: FakeCompletedProcess(returncode=51, stderr="[FATAL] Auth failed"),
  )
  with pytest.raises(RuntimeError, match="Auth failed"):
    merge.list_input_files("/store/user/u/hists", "*.root", "door:1094")


def test_list_input_files_stays_local_for_a_posix_directory(monkeypatch, tmp_path):
  monkeypatch.setattr(
    merge.subprocess, "run", lambda *a, **k: pytest.fail("a local directory must not touch the network")
  )
  (tmp_path / "a.root").write_text("aa")
  paths, sizes = merge.list_input_files(str(tmp_path), "*.root", "door:1094")
  assert paths == [str(tmp_path / "a.root")]
  assert sizes == {str(tmp_path / "a.root"): 2}


def test_hadd_reads_lfn_inputs_through_the_redirector():
  # The job tuples keep bare LFNs so path arithmetic keeps working; only the command hadd
  # actually runs carries URLs.
  command = merge.build_hadd_command(
    "/scratch/ntuple_0.root",
    ["/store/user/u/hists/ntuple_0.root"],
    preserve_input_compression=False,
    redirector="maite.iihe.ac.be:1094",
  )
  assert command[-1] == "root://maite.iihe.ac.be:1094//store/user/u/hists/ntuple_0.root"
  assert command[-2] == "/scratch/ntuple_0.root"


def test_condor_merge_job_merges_into_scratch_and_stages(tmp_path):
  script_path = merge.create_condor_job(
    str(tmp_path),
    "histograms",
    "DYto2L/2024",
    0,
    "/store/user/u/hists_merged/ntuple_0.root",
    ["/store/user/u/hists/ntuple_0.root"],
    preserve_input_compression=False,
    hadd_files_per_pass=None,
    hadd_workers=1,
    redirector="maite.iihe.ac.be:1094",
  )
  script = open(script_path).read()

  # hadd writes into the job's own scratch, never onto the destination: an LFN is not a
  # writable local path, and even a POSIX one would show a growing file to the next stage.
  assert "_CONDOR_SCRATCH_DIR" in script
  assert '"$work_dir/ntuple_0.root"' in script
  assert "root://maite.iihe.ac.be:1094//store/user/u/hists/ntuple_0.root" in script
  assert "teaHelpers.stage_output" in script
  assert "mkdir -p /store" not in script


def test_a_remote_output_without_scratch_is_a_hard_error(monkeypatch, tmp_path):
  # Falling through to "merging in the output directory" would ask hadd to write a literal
  # /store/... file on the worker and report success having published nothing.
  files_config = make_files_config(
    samples=[""],
    output_hists_dir="/store/user/u/hists",
    redirector="door:1094",
  )
  monkeypatch.setattr(
    merge,
    "list_input_files",
    lambda input_dir, pattern, redirector: (["/store/user/u/in/ntuple_0.root"], {"/store/user/u/in/ntuple_0.root": 10}),
  )
  monkeypatch.setattr(merge, "contains_top_level_tree", lambda file_path, redirector=None: False)
  monkeypatch.setattr(merge, "choose_scratch_root", lambda required_bytes: None)

  config_path = tmp_path / "files_config.py"
  config_path.write_text("")
  monkeypatch.setattr(merge, "load_files_config", lambda path: files_config)
  monkeypatch.setattr(sys, "argv", ["merge.py", "--files_config", str(config_path)])
  with pytest.raises(RuntimeError, match="requires local scratch"):
    merge.main()
