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
