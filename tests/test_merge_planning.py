"""merge.py planning logic: merge targets, sample directories, chunking, input_files guards."""

import json
from pathlib import Path
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
  monkeypatch.setattr(merge, "load_files_config", lambda path, **kwargs: files_config)
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
  with pytest.raises(ValueError, match="tree/histogram outputs"):
    run_main_with_config(monkeypatch, tmp_path, files_config)


def test_empty_output_dirs_alone_are_not_a_merge_target(monkeypatch, tmp_path):
  monkeypatch.chdir(tmp_path)
  files_config = make_files_config(output_hists_dir="", output_trees_dir="")
  with pytest.raises(ValueError, match="tree/histogram outputs"):
    run_main_with_config(monkeypatch, tmp_path, files_config)
  assert not (tmp_path / "_merged").exists()


class FakeCompletedProcess:
  def __init__(self, returncode=0, stdout="", stderr=""):
    self.returncode = returncode
    self.stdout = stdout
    self.stderr = stderr


XRDFS_LISTING = (
  "-rw- 2026-08-27 14:03:03 13930949 /store/user/u/hists/ntuple_0.root\n"
  "-rw-r--r-- user group 1048576 2026-08-27 14:04:11 /store/user/u/hists/ntuple_1.root\n"
  "drwxr-xr-x user group 0 2026-08-27 14:04:11 /store/user/u/hists/subdir\n"
  "-rw- 2026-08-27 14:05:00 512 /store/user/u/hists/log.txt\n"
)


def test_list_input_files_reads_sizes_out_of_the_remote_listing(monkeypatch):
  commands = []

  def fake_run(command, **kwargs):
    commands.append(command)
    return FakeCompletedProcess(stdout=XRDFS_LISTING)

  monkeypatch.setattr(merge.subprocess, "run", fake_run)
  paths, sizes = merge.list_input_files("/store/user/u/hists", "*.root", "maite.iihe.ac.be:1094")

  assert commands == [["xrdfs", "root://maite.iihe.ac.be:1094", "ls", "-l", "/store/user/u/hists"]]
  assert paths == ["/store/user/u/hists/ntuple_0.root", "/store/user/u/hists/ntuple_1.root"]
  assert sizes["/store/user/u/hists/ntuple_0.root"] == 13930949


def test_list_input_files_warns_and_uses_an_incomplete_remote_listing(monkeypatch):
  warnings = []
  monkeypatch.setattr(
    merge.subprocess,
    "run",
    lambda command, **kwargs: FakeCompletedProcess(
      stdout=XRDFS_LISTING,
      stderr="[WARN] Result may be incomplete: directory listing limit reached\n",
    ),
  )
  monkeypatch.setattr(merge, "warn", warnings.append)

  paths, sizes = merge.list_input_files("/store/user/u/hists", "*.root", "door:1094")

  assert paths == ["/store/user/u/hists/ntuple_0.root", "/store/user/u/hists/ntuple_1.root"]
  assert sizes["/store/user/u/hists/ntuple_0.root"] == 13930949
  assert warnings == [
    "Incomplete xrdfs listing for /store/user/u/hists: [WARN] Result may be incomplete: directory listing limit reached"
  ]


def test_list_input_files_rejects_a_listing_without_a_file_size(monkeypatch):
  monkeypatch.setattr(
    merge.subprocess,
    "run",
    lambda command, **kwargs: FakeCompletedProcess(
      stdout="-rw-r--r-- user group unknown 2026-08-27 14:04:11 /store/user/u/hists/ntuple.root\n"
    ),
  )
  with pytest.raises(RuntimeError, match="Could not read file size"):
    merge.list_input_files("/store/user/u/hists", "*.root", "door:1094")


def test_list_input_files_treats_an_absent_remote_directory_as_empty(monkeypatch):
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
  command = merge.build_hadd_command(
    "/scratch/ntuple_0.root",
    ["/store/user/u/hists/ntuple_0.root"],
    preserve_input_compression=False,
    redirector="maite.iihe.ac.be:1094",
  )
  assert command[-1] == "root://maite.iihe.ac.be:1094//store/user/u/hists/ntuple_0.root"
  assert command[-2] == "/scratch/ntuple_0.root"


def test_condor_merge_job_merges_into_scratch_and_stages(monkeypatch, tmp_path):
  script_path, job_path = merge.create_condor_job(
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
    stage_url_base="davs://door.example:2880",
  )
  script = Path(script_path).read_text()
  job = json.loads(Path(job_path).read_text())
  assert '--job-file "$job_sandbox/' in script
  assert job["input_files"] == ["/store/user/u/hists/ntuple_0.root"]
  assert job["redirector"] == "maite.iihe.ac.be:1094"
  assert job["stage_url_base"] == "davs://door.example:2880"
  assert "mkdir -p /store" not in script

  commands = []
  checked = []
  published = []
  monkeypatch.setattr(merge, "ensure_root_compiler_environment", lambda: None)
  monkeypatch.setattr(merge, "run_command", commands.append)
  monkeypatch.setattr(merge, "validate_root_file", checked.append)
  monkeypatch.setattr(merge, "stage_output", lambda *args, **kwargs: published.append((args, kwargs)))
  merge.run_condor_merge(job)
  command = commands[0]
  working_output = command[-2]
  assert command[-1] == "root://maite.iihe.ac.be:1094//store/user/u/hists/ntuple_0.root"
  assert working_output != job["output_file"]
  assert Path(working_output).name == "ntuple_0.root"
  assert checked == [command[-1], working_output]
  assert published == [((working_output, job["output_file"]), {"url_base": job["stage_url_base"]})]
  assert not Path(working_output).parent.exists()


@pytest.mark.parametrize(
  ("input_path", "expected_url"),
  [
    ("/store/user/u/a.root", "root://door:1094//store/user/u/a.root"),
    ("/eos/home-u/user/a.root", "root://eoshome-u.cern.ch//eos/user/u/user/a.root"),
    ("/eos/user/u/user/a.root", "root://eoshome-u.cern.ch//eos/user/u/user/a.root"),
    ("root://other:1094//store/user/u/a.root?token=abc", "root://other:1094//store/user/u/a.root?token=abc"),
  ],
)
@pytest.mark.parametrize("input_keys", [0, 1])
def test_condor_worker_validates_remote_inputs_with_root(monkeypatch, tmp_path, input_path, expected_url, input_keys):
  # Exercise the real validator: mocking validate_root_file hid the URL/local-path
  # mismatch that rejected every remote input before hadd could run.
  opened = []
  published = []
  commands = []

  def open_file(path, mode):
    opened.append(path)
    assert mode == "READ"
    return types.SimpleNamespace(
      IsZombie=lambda: False,
      GetNkeys=lambda: input_keys if path == expected_url else 1,
      TestBit=lambda bit: False,
      Close=lambda: None,
    )

  root = types.SimpleNamespace(
    gErrorIgnoreLevel=1000,
    kFatal=6000,
    TFile=types.SimpleNamespace(Open=open_file, kRecovered=1),
  )
  monkeypatch.setitem(sys.modules, "ROOT", root)
  monkeypatch.setattr(merge, "ensure_root_compiler_environment", lambda: None)
  monkeypatch.setattr(merge, "stage_output", lambda *args, **kwargs: published.append((args, kwargs)))

  def run_hadd(command):
    commands.append(command)
    assert command[-1] == expected_url
    Path(command[-2]).write_text("merged output")

  monkeypatch.setattr(merge, "run_command", run_hadd)
  job = dict(
    output_file=str(tmp_path / "merged.root"),
    input_files=[input_path],
    preserve_input_compression=False,
    hadd_files_per_pass=None,
    hadd_workers=1,
    redirector="door:1094",
  )
  if input_keys:
    merge.run_condor_merge(job)
    assert len(commands) == len(published) == 1
    assert opened == [expected_url, commands[0][-2]]
  else:
    with pytest.raises(RuntimeError, match="no_keys"):
      merge.run_condor_merge(job)
    assert opened == [expected_url]
    assert not commands
    assert not published
  assert root.gErrorIgnoreLevel == 1000


@pytest.mark.parametrize("worker_directory", ["condor", "sandbox"])
def test_condor_job_resolves_local_paths_before_changing_worker_directory(monkeypatch, tmp_path, worker_directory):
  submission_dir = tmp_path / "submission"
  (submission_dir / "inputs").mkdir(parents=True)
  (submission_dir / "inputs" / "a.root").write_text("input payload")
  condor_dir = submission_dir / "condor"
  condor_dir.mkdir()
  worker_dir = submission_dir / worker_directory
  worker_dir.mkdir(exist_ok=True)
  monkeypatch.chdir(submission_dir)
  _, job_path = merge.create_condor_job(
    str(condor_dir), "histograms", "sample", 0, "merged/a.root", ["inputs/a.root"], False, None, 1
  )
  job = json.loads(Path(job_path).read_text())
  monkeypatch.chdir(worker_dir)
  monkeypatch.setattr(merge, "ensure_root_compiler_environment", lambda: None)
  monkeypatch.setattr(merge.teaHelpers, "get_facility", lambda: "default")

  def validate_local_file(path):
    assert Path(path).is_file(), f"worker cannot find {path} from {Path.cwd()}"

  def run_hadd(command):
    Path(command[-2]).write_text(Path(command[-1]).read_text())

  monkeypatch.setattr(merge, "validate_root_file", validate_local_file)
  monkeypatch.setattr(merge, "run_command", run_hadd)
  merge.run_condor_merge(job)
  assert job["input_files"] == [str(submission_dir / "inputs" / "a.root")]
  assert job["output_file"] == str(submission_dir / "merged" / "a.root")
  assert (submission_dir / "merged" / "a.root").read_text() == "input payload"
  assert not (worker_dir / "merged").exists()


@pytest.mark.parametrize(
  "remote_path",
  [
    "/store/user/u/a.root",
    "/eos/user/u/user/a.root",
    "root://door:1094//store/user/u/a.root?token=abc",
    "srm://door.example/store/user/u/a.root",
    "gsiftp://door.example/store/user/u/a.root",
  ],
)
def test_condor_job_keeps_remote_paths_unchanged(tmp_path, remote_path):
  _, job_path = merge.create_condor_job(
    str(tmp_path), "histograms", "sample", 0, remote_path, [remote_path], False, None, 1
  )
  job = json.loads(Path(job_path).read_text())
  assert job["input_files"] == [remote_path]
  assert job["output_file"] == remote_path


@pytest.mark.parametrize(
  ("input_file_sizes", "expected_request"),
  [
    ({"a.root": 1000, "b.root": 1500, "c.root": 2000}, "request_disk = 1048576K"),
    (
      {"a.root": 1000, "b.root": 200_000_000, "c.root": 300_000_000},
      "request_disk = 1220704K",
    ),
  ],
)
def test_condor_submit_requests_disk_for_the_largest_merge(monkeypatch, tmp_path, input_file_sizes, expected_request):
  jobs = [
    ("histograms", "A", 0, "/input/A", "/output/A", "/output/A/ntuple_0.root", ["a.root"]),
    (
      "histograms",
      "B",
      0,
      "/input/B",
      "/output/B",
      "/output/B/ntuple_0.root",
      ["b.root", "c.root"],
    ),
  ]
  monkeypatch.setattr(merge, "get_facility", lambda: "other")
  monkeypatch.setattr(merge, "run_command", lambda command: None)

  merge.submit_condor_jobs(
    str(tmp_path),
    jobs,
    input_file_sizes,
    preserve_input_compression=False,
    hadd_files_per_pass=None,
    hadd_workers=1,
  )

  submit_file = (tmp_path / "merge.sub").read_text()
  assert expected_request in submit_file


def test_a_remote_output_without_scratch_is_a_hard_error(monkeypatch, tmp_path):
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
  monkeypatch.setattr(merge, "load_files_config", lambda path, **kwargs: files_config)
  monkeypatch.setattr(sys, "argv", ["merge.py", "--files_config", str(config_path)])
  with pytest.raises(RuntimeError, match="requires local scratch"):
    merge.main()


def test_preceding_step_outputs_take_precedence_over_directory_discovery(monkeypatch, tmp_path, capsys):
  expected = str(tmp_path / "hists" / "expected.root")
  files_config = make_files_config(
    output_hists_dir=str(tmp_path / "hists"),
    input_output_file_list=[("raw.root", None, expected)],
  )
  monkeypatch.setattr(merge, "collect_jobs", lambda *args: pytest.fail("exact outputs must exclude directory globs"))
  run_main_with_config(monkeypatch, tmp_path, files_config)
  assert f"input: {expected}" in capsys.readouterr().out


def test_remote_incomplete_inventory_requires_opt_in_and_keeps_only_nonempty_files(monkeypatch):
  paths = ["/store/user/u/hists/good.root", "/store/user/u/hists/empty.root", "/store/user/u/hists/missing.root"]
  jobs = [("histograms", "sample", 0, "", "hists_merged", "hists_merged/ntuple_0.root", paths)]
  commands = []

  def fake_run(command, **kwargs):
    commands.append(command)
    if command[-1].endswith("missing.root"):
      return FakeCompletedProcess(returncode=54)
    return FakeCompletedProcess(stdout="Size: 17\n" if command[-1].endswith("good.root") else "Size: 0\n")

  monkeypatch.setattr(merge.subprocess, "run", fake_run)
  with pytest.raises(RuntimeError, match="2 missing/empty inputs"):
    merge.select_available_jobs(jobs, False, "door:1094")
  selected = merge.select_available_jobs(jobs, True, "door:1094")
  assert selected == [(*jobs[0][:-1], [paths[0]])]
  assert all(command[:3] == ["xrdfs", "root://door:1094", "stat"] for command in commands)


@pytest.mark.parametrize("mode", ["preceding_outputs", "raw_groups"])
def test_explicit_merge_modes_reject_symlinked_duplicates(tmp_path, mode):
  original = tmp_path / "a.root"
  original.write_text("a")
  alias = tmp_path / "alias.root"
  alias.symlink_to(original)
  with pytest.raises(ValueError, match="Duplicate"):
    if mode == "preceding_outputs":
      merge.collect_explicit_jobs([("raw_a", None, str(original)), ("raw_b", None, str(alias))])
    else:
      merge.collect_input_group_jobs({str(tmp_path / "out"): [str(original), str(alias)]})


def test_input_groups_batch_exact_paths_with_provenance_and_remote_key_checks(monkeypatch):
  inspected = []
  paths = ["/store/user/u/c.root", "/store/user/u/a.root", "/store/user/u/b.root"]
  monkeypatch.setattr(
    merge, "skip_files_without_keys", lambda files, redirector: inspected.append((files, redirector)) or files
  )
  jobs = merge.collect_input_group_jobs(
    {"/store/user/u/merged": paths}, chunk_size=2, provenance_tag="abc123", skip_no_keys=True, redirector="door:1094"
  )
  assert [job[5] for job in jobs] == [
    "/store/user/u/merged/ntuple_0_abc123.root",
    "/store/user/u/merged/ntuple_1_abc123.root",
  ]
  assert [job[-1] for job in jobs] == [sorted(paths)[:2], sorted(paths)[2:]]
  assert inspected == [(sorted(paths), "door:1094")]


def test_condor_merge_failure_does_not_publish(monkeypatch):
  job = dict(
    output_file="/store/user/u/merged/a.root",
    input_files=["/store/user/u/input/a.root"],
    preserve_input_compression=False,
    hadd_files_per_pass=None,
    hadd_workers=1,
    redirector="door:1094",
  )
  monkeypatch.setattr(merge, "ensure_root_compiler_environment", lambda: None)
  monkeypatch.setattr(merge, "validate_root_file", lambda path: None)
  monkeypatch.setattr(merge, "stage_output", lambda *args: pytest.fail("failed merge must not publish"))

  def fail_hadd(command):
    raise RuntimeError("hadd failed")

  monkeypatch.setattr(merge, "run_command", fail_hadd)
  with pytest.raises(RuntimeError, match="hadd failed"):
    merge.run_condor_merge(job)
