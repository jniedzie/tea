#!/usr/bin/env python3
"""Check CERN Condor staging, proxy transport, and wrapper failure behavior."""

import importlib.util
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import MagicMock, patch


FRAMEWORK = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("submission_manager", FRAMEWORK / "pylibs/submitter/SubmissionManager.py")
MODULE = importlib.util.module_from_spec(SPEC)
with patch.dict(sys.modules, {"ROOT": MagicMock(), "Logger": MagicMock(), "teaHelpers": MagicMock()}):
  SPEC.loader.exec_module(MODULE)


class CondorSubmissionTest(unittest.TestCase):
  def manager(self):
    manager = MODULE.SubmissionManager.__new__(MODULE.SubmissionManager)
    manager.submission_system = MODULE.SubmissionSystem.condor
    manager.condor_stage_dir = None
    manager.condor_transfer_files = []
    manager.condor_spool = False
    return manager

  def test_factory_paths_default_to_afs_instead_of_eos_checkout(self):
    manager = self.manager()
    staging_root = "/afs/cern.ch/user/t/test/.local/state/tea/condor"
    staging_dir = staging_root + "/submission"
    with (
      patch.object(MODULE, "get_facility", return_value="lxplus"),
      patch.dict(os.environ, {"HOME": "/afs/cern.ch/user/t/test", "TEA_CONDOR_DIR": staging_root}),
      patch.object(MODULE.os.path, "realpath", side_effect=lambda path: path),
      patch.object(MODULE.os, "makedirs"),
      patch.object(MODULE.tempfile, "mkdtemp", return_value=staging_dir) as make_temporary,
    ):
      manager._SubmissionManager__setup_temp_file_paths()
    self.assertEqual(make_temporary.call_args.kwargs["dir"], staging_root)
    self.assertEqual(manager.condor_stage_dir, staging_dir)
    for path in (manager.condor_config_name, manager.condor_run_script_name, manager.input_files_list_file_name):
      self.assertTrue(path.startswith(staging_dir + "/"))
    self.assertEqual(manager.condor_transfer_files, [manager.input_files_list_file_name])

  def test_invalid_materialization_limit_is_rejected(self):
    for limit in (0, -1):
      with self.subTest(limit=limit):
        args = SimpleNamespace(job_flavour="espresso", memory=1, max_materialize=limit)
        with self.assertRaisesRegex(ValueError, "--max_materialize must be at least 1"):
          self.manager().run_condor(args)

  def test_eos_checkout_runtime_or_staging_enables_spooling(self):
    afs = "/afs/cern.ch/user/t/test"
    eos = "/eos/home-t/test"
    for work_dir, python, staging_root, spool in (
      (eos + "/analysis/bin", afs + "/env/bin/python", afs + "/condor", True),
      (afs + "/analysis/bin", eos + "/env/bin/python", afs + "/condor", True),
      (afs + "/analysis/bin", afs + "/env/bin/python", "/eos/user/t/test/condor", True),
      (afs + "/analysis/bin", afs + "/env/bin/python", afs + "/condor", False),
    ):
      with self.subTest(work_dir=work_dir, python=python, staging_root=staging_root):
        manager = self.manager()
        with (
          patch.object(MODULE, "get_facility", return_value="lxplus"),
          patch.dict(os.environ, {"TEA_CONDOR_DIR": staging_root}),
          patch.object(MODULE.os, "getcwd", return_value=work_dir),
          patch.object(MODULE.sys, "executable", python),
          patch.object(MODULE.os.path, "realpath", side_effect=lambda path: path),
          patch.object(MODULE.os, "makedirs"),
          patch.object(MODULE.tempfile, "mkdtemp", return_value=staging_root + "/submission"),
        ):
          manager._SubmissionManager__setup_temp_file_paths()
        self.assertEqual(manager.condor_spool, spool)

  def test_local_parallel_keeps_local_paths(self):
    manager = self.manager()
    manager.submission_system = MODULE.SubmissionSystem.local_parallel
    with (
      patch.object(MODULE, "get_facility", return_value="lxplus"),
      patch.object(MODULE.tempfile, "mkdtemp") as make_temporary,
    ):
      manager._SubmissionManager__setup_temp_file_paths()
    make_temporary.assert_not_called()
    self.assertIsNone(manager.condor_stage_dir)
    self.assertFalse(manager.condor_spool)
    self.assertTrue(manager.condor_run_script_name.startswith("tmp/"))

  def test_submit_command_and_factory_options_match_spooling_mode(self):
    for spool, save_logs, dry in ((False, True, False), (True, True, False), (True, False, False), (True, True, True)):
      with self.subTest(spool=spool, save_logs=save_logs, dry=dry), tempfile.TemporaryDirectory() as temporary:
        manager = self.manager()
        manager.files_config = SimpleNamespace(input_file_list=["input.root"])
        manager.app_name = "selector"
        manager.config_path = "config.py"
        manager.extra_args = None
        args = SimpleNamespace(
          job_flavour="espresso",
          memory=1,
          max_materialize=500,
          resubmit_job=None,
          resubmit_failed=False,
          save_logs=save_logs,
          dry=dry,
        )
        work_dir = "/eos/user/t/test/analysis/bin" if spool else "/afs/cern.ch/user/t/test/analysis/bin"
        python = "/eos/home-t/test/env/bin/python" if spool else "/afs/cern.ch/user/t/test/env/bin/python"

        def copy_templates(manager=manager):
          shutil.copyfile(FRAMEWORK / "templates/condor_run.template.sh", manager.condor_run_script_name)
          shutil.copyfile(FRAMEWORK / "templates/condor_config_lxplus.template.sub", manager.condor_config_name)

        with (
          patch.object(MODULE, "get_facility", return_value="lxplus"),
          patch.dict(os.environ, {"TEA_CONDOR_DIR": temporary, "LD_LIBRARY_PATH": "/test/conda/lib"}),
          patch.object(MODULE.os, "getcwd", return_value=work_dir),
          patch.object(MODULE.sys, "executable", python),
          patch.object(manager, "_SubmissionManager__copy_templates", side_effect=copy_templates),
          patch.object(manager, "_SubmissionManager__setup_voms_proxy", return_value="unset X509_USER_PROXY"),
          patch.object(MODULE, "info") as messages,
          patch.object(MODULE.subprocess, "run", return_value=SimpleNamespace(stdout="12345.0 - 12345.0\n")) as submit,
        ):
          jobs = manager.run_condor(args)
        expected = ["condor_submit", "-spool", "-terse"] if spool else ["condor_submit"]
        if dry:
          submit.assert_not_called()
          self.assertEqual(manager.condor_cluster_ids, [])
          self.assertFalse((Path(manager.condor_stage_dir) / "cluster_id").exists())
          continue
        submit.assert_called_once()
        self.assertEqual(submit.call_args.args[0], expected + [manager.condor_config_name])
        self.assertEqual(submit.call_args.kwargs["cwd"], manager.condor_stage_dir)
        self.assertNotIn("LD_LIBRARY_PATH", submit.call_args.kwargs["env"])
        self.assertTrue(submit.call_args.kwargs["check"])
        self.assertEqual(jobs, [(manager.condor_run_script_name, 1, manager.submission_id)])
        if spool:
          self.assertEqual(manager.condor_cluster_ids, [12345])
          self.assertEqual((Path(manager.condor_stage_dir) / "cluster_id").read_text(), "12345\n")
          output = "\n".join(call.args[0] for call in messages.call_args_list)
          self.assertIn("condor_transfer_data 12345", output)
          self.assertEqual("only after retrieval" in output, save_logs)
          self.assertEqual(submit.call_args.kwargs["stdout"], subprocess.PIPE)
          self.assertTrue(submit.call_args.kwargs["text"])
        else:
          self.assertEqual(manager.condor_cluster_ids, [])
          self.assertFalse((Path(manager.condor_stage_dir) / "cluster_id").exists())
        script = Path(manager.condor_run_script_name).read_text()
        self.assertIn(f"exec {python} condor_runner.py", script)
        subprocess.run(["bash", "-n", manager.condor_run_script_name], check=True)
        description = Path(manager.condor_config_name).read_text()
        self.assertEqual("max_materialize" in description, not spool)
        self.assertEqual("max_idle" in description, not spool)
        self.assertIn("should_transfer_files   = YES", description)
        self.assertIn(manager.input_files_list_file_name, description)

  def test_valid_proxy_and_manifest_are_transferred_and_cd_failure_is_fatal(self):
    with tempfile.TemporaryDirectory() as temporary:
      stage = Path(temporary)
      proxy = stage / "source_proxy"
      proxy.write_text("test proxy contents")
      manager = self.manager()
      manager.condor_stage_dir = str(stage)
      manager.condor_run_script_name = str(stage / "run.sh")
      manager.condor_config_name = str(stage / "job.sub")
      manager.input_files_list_file_name = str(stage / "inputs.txt")
      Path(manager.input_files_list_file_name).write_text("input.root\n")
      manager.condor_transfer_files = [manager.input_files_list_file_name]
      manager.files_config = SimpleNamespace(output_trees_dir="/eos/user/t/test/output")
      manager.app_name = "selector"
      manager.config_path = "config.py"
      manager.extra_args = None
      manager.save_logs = True
      manager.resubmit_job = None
      manager.memory_request = 1
      manager.materialize_max = 500
      manager.job_flavour = "espresso"
      shutil.copyfile(FRAMEWORK / "templates/condor_run.template.sh", manager.condor_run_script_name)
      shutil.copyfile(FRAMEWORK / "templates/condor_config_lxplus.template.sub", manager.condor_config_name)
      results = [SimpleNamespace(returncode=0, stdout=str(proxy)), SimpleNamespace(returncode=0)]
      with (
        patch.object(MODULE.shutil, "which", return_value="voms-proxy-info"),
        patch.object(MODULE.subprocess, "run", side_effect=results),
        patch.object(MODULE.os, "getcwd", return_value=str(stage / "missing bin")),
        patch.object(MODULE, "get_facility", return_value="lxplus"),
      ):
        manager._SubmissionManager__set_run_script_variables()
        manager._SubmissionManager__set_condor_script_variables(501)
      self.assertEqual((stage / "voms_proxy").read_text(), "test proxy contents")
      self.assertEqual((stage / "voms_proxy").stat().st_mode & 0o777, 0o600)
      script = Path(manager.condor_run_script_name).read_text()
      submit = Path(manager.condor_config_name).read_text()
      self.assertIn('X509_USER_PROXY="$job_sandbox/voms_proxy"', script)
      self.assertIn('"$job_sandbox/inputs.txt"', script)
      self.assertIn(f"initialdir            = {stage}", submit)
      self.assertIn(f"transfer_input_files  = {stage}/inputs.txt,{stage}/voms_proxy", submit)
      self.assertIn("max_materialize       = 500", submit)
      self.assertIn("queue 501", submit)
      self.assertIn(f"log                   = {stage}/log/$(ClusterId).log", submit)
      self.assertNotIn("condor_dummy.out", submit)
      subprocess.run(["bash", "-n", manager.condor_run_script_name], check=True)
      result = subprocess.run(["bash", manager.condor_run_script_name, "0"], cwd=stage, capture_output=True)
      self.assertNotEqual(result.returncode, 0)
      self.assertIn(b"missing bin", result.stderr)
      self.assertNotIn(b"condor_runner.py", result.stderr)

  def test_expired_proxy_does_not_override_worker_authentication(self):
    manager = self.manager()
    results = [SimpleNamespace(returncode=0, stdout="/tmp/expired_proxy"), SimpleNamespace(returncode=1)]
    with (
      patch.object(MODULE.shutil, "which", return_value="voms-proxy-info"),
      patch.object(MODULE.subprocess, "run", side_effect=results),
    ):
      setup = manager._SubmissionManager__setup_voms_proxy()
    self.assertEqual(setup, "unset X509_USER_PROXY")
    self.assertEqual(manager.condor_transfer_files, [])


if __name__ == "__main__":
  unittest.main()
