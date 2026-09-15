"""Stage-out helpers: URL derivation, atomic publish and the retry backoff."""

import os
import statistics

import pytest

import teaHelpers


def test_dcache_url_from_bare_pnfs_path():
  assert teaHelpers._dcache_gfal_url("/pnfs/iihe/cms/store/user/x/out.root") == (
    teaHelpers.GFAL_DOOR + "/pnfs/iihe/cms/store/user/x/out.root"
  )


def test_dcache_url_strips_the_local_mount_prefix():
  local_path = f"{teaHelpers.DCACHE_LOCAL_PREFIX}/pnfs/iihe/cms/store/user/x/out.root"
  assert teaHelpers._dcache_gfal_url(local_path) == (teaHelpers.GFAL_DOOR + "/pnfs/iihe/cms/store/user/x/out.root")


def test_dcache_url_is_none_for_a_non_pnfs_path(tmp_path):
  assert teaHelpers._dcache_gfal_url(str(tmp_path / "out.root")) is None


def test_dcache_url_is_none_for_a_non_pnfs_dcache_subtree():
  assert teaHelpers._dcache_gfal_url(f"{teaHelpers.DCACHE_LOCAL_PREFIX}/other/out.root") is None


def test_dcache_url_is_none_when_dot_dot_escapes_pnfs():
  # realpath collapses the traversal, so this names /etc/passwd and must not be handed to
  # the door as if it were a pnfs path.
  assert teaHelpers._dcache_gfal_url("/pnfs/../etc/passwd") is None


def test_eos_url_for_the_home_instance_form():
  assert teaHelpers.eos_xrootd_url("/eos/home-t/tiepolo/results/out.root") == (
    "root://eoshome-t.cern.ch//eos/user/t/tiepolo/results/out.root"
  )


def test_eos_url_for_the_user_form():
  assert teaHelpers.eos_xrootd_url("/eos/user/t/tiepolo/results/out.root") == (
    "root://eoshome-t.cern.ch//eos/user/t/tiepolo/results/out.root"
  )


def test_eos_url_is_none_for_a_non_eos_path(tmp_path):
  assert teaHelpers.eos_xrootd_url(str(tmp_path / "out.root")) is None


def test_stage_output_publishes_atomically(tmp_path):
  source = tmp_path / "scratch" / "out.root"
  source.parent.mkdir()
  source.write_text("payload")
  destination = tmp_path / "final" / "out.root"

  teaHelpers.stage_output(str(source), str(destination), "default")

  assert destination.read_text() == "payload"
  assert not list(destination.parent.glob(".*stage-*"))


def test_stage_output_leaves_no_partial_file_when_the_transport_fails(tmp_path, monkeypatch):
  source = tmp_path / "out.root"
  source.write_text("new payload")
  destination = tmp_path / "final" / "out.root"
  destination.parent.mkdir()
  destination.write_text("previous good payload")

  def failing_transport(local_path, stage_path):
    # Fail the way a real transfer does: after some bytes have already been written.
    with open(stage_path, "w") as partial_file:
      partial_file.write("half a")
    raise RuntimeError("transport died mid-write")

  monkeypatch.setattr(teaHelpers, "TRANSPORTS", {"default": failing_transport})
  monkeypatch.setattr(teaHelpers, "GFAL_COPY_MAX_ATTEMPTS", 1)

  with pytest.raises(RuntimeError, match="transport died mid-write"):
    teaHelpers.stage_output(str(source), str(destination), "default")

  # The destination still holds the previous complete file, and no temp file is orphaned.
  assert destination.read_text() == "previous good payload"
  assert not list(destination.parent.glob(".*stage-*"))


def test_stage_output_retries_until_the_transport_succeeds(tmp_path, monkeypatch):
  source = tmp_path / "out.root"
  source.write_text("payload")
  destination = tmp_path / "out_final.root"
  attempts = []

  def flaky_transport(local_path, stage_path):
    attempts.append(stage_path)
    if len(attempts) < 3:
      raise RuntimeError("transient failure")
    teaHelpers._transport_filesystem(local_path, stage_path)

  monkeypatch.setattr(teaHelpers, "TRANSPORTS", {"default": flaky_transport})
  monkeypatch.setattr(teaHelpers, "GFAL_COPY_RETRY_BASE_WAIT_SECONDS", 0)
  monkeypatch.setattr(teaHelpers, "GFAL_COPY_RETRY_EXPO_HALF_LIFE_SECONDS", 1e-6)

  teaHelpers.stage_output(str(source), str(destination), "default")

  assert len(attempts) == 3
  assert destination.read_text() == "payload"


def test_stage_budget_stops_the_retries(tmp_path, monkeypatch):
  source = tmp_path / "out.root"
  source.write_text("payload")
  destination = tmp_path / "out_final.root"
  attempts = []

  def always_failing_transport(local_path, stage_path):
    attempts.append(stage_path)
    raise RuntimeError("transport is down")

  monkeypatch.setattr(teaHelpers, "TRANSPORTS", {"default": always_failing_transport})
  teaHelpers.begin_stage_budget(0.0)
  try:
    with pytest.raises(RuntimeError, match="budget"):
      teaHelpers.stage_output(str(source), str(destination), "default")
  finally:
    teaHelpers.clear_stage_budget()

  # The first attempt still runs; the budget only suppresses the waiting retries.
  assert len(attempts) == 1
  assert not destination.exists()


def test_backoff_stays_within_the_bounds_the_retry_comment_claims():
  # The comment on the retry loop promises a 20 s floor, a ~80 s median and a ~107 s mean.
  # These are the numbers the distribution was chosen for, so they are worth pinning.
  import math
  import random

  rng = random.Random(1234)
  waits = [
    teaHelpers.GFAL_COPY_RETRY_BASE_WAIT_SECONDS
    + rng.expovariate(math.log(2) / teaHelpers.GFAL_COPY_RETRY_EXPO_HALF_LIFE_SECONDS)
    for _ in range(200000)
  ]

  assert min(waits) >= teaHelpers.GFAL_COPY_RETRY_BASE_WAIT_SECONDS
  assert statistics.mean(waits) == pytest.approx(107, abs=2)
  assert statistics.median(waits) == pytest.approx(80, abs=2)


def test_preflight_accepts_a_filesystem_facility(tmp_path):
  ok, reason = teaHelpers.stage_preflight([str(tmp_path / "out.root")], "default")
  assert ok
  assert reason


def test_preflight_passes_when_no_output_needs_the_remote_transport(tmp_path):
  # A vub job whose outputs are ordinary filesystem paths does not need gfal at all.
  ok, reason = teaHelpers.stage_preflight([str(tmp_path / "out.root")], "vub")
  assert ok
  assert "falls back" in reason


def test_preflight_fails_without_a_proxy(monkeypatch):
  monkeypatch.setattr(teaHelpers.shutil, "which", lambda binary: f"/usr/bin/{binary}")
  monkeypatch.delenv("X509_USER_PROXY", raising=False)
  ok, reason = teaHelpers.stage_preflight(["/pnfs/iihe/cms/store/user/x/out.root"], "vub")
  assert not ok
  assert "X509_USER_PROXY" in reason


def test_preflight_fails_when_the_proxy_file_is_missing(monkeypatch, tmp_path):
  monkeypatch.setattr(teaHelpers.shutil, "which", lambda binary: f"/usr/bin/{binary}")
  monkeypatch.setenv("X509_USER_PROXY", str(tmp_path / "does_not_exist"))
  ok, reason = teaHelpers.stage_preflight(["/pnfs/iihe/cms/store/user/x/out.root"], "vub")
  assert not ok
  assert "readable" in reason


def test_preflight_fails_when_the_transport_binary_is_missing(monkeypatch, tmp_path):
  proxy = tmp_path / "voms_proxy"
  proxy.write_text("proxy")
  monkeypatch.setenv("X509_USER_PROXY", str(proxy))
  monkeypatch.setattr(teaHelpers.shutil, "which", lambda binary: None)
  ok, reason = teaHelpers.stage_preflight(["/pnfs/iihe/cms/store/user/x/out.root"], "vub")
  assert not ok
  assert "gfal-copy" in reason


def test_preflight_passes_with_a_proxy_and_a_binary(monkeypatch, tmp_path):
  proxy = tmp_path / "voms_proxy"
  proxy.write_text("proxy")
  monkeypatch.setenv("X509_USER_PROXY", str(proxy))
  monkeypatch.setattr(teaHelpers.shutil, "which", lambda binary: f"/usr/bin/{binary}")
  ok, reason = teaHelpers.stage_preflight(["/pnfs/iihe/cms/store/user/x/out.root"], "vub")
  assert ok
  assert "gfal-copy" in reason


def test_naf_and_lxplus_use_remote_transports():
  assert teaHelpers.get_transport("naf") is teaHelpers._transport_gfal
  assert teaHelpers.get_transport("vub") is teaHelpers._transport_gfal
  assert teaHelpers.get_transport("lxplus") is teaHelpers._transport_xrootd
  assert teaHelpers.get_transport("default") is teaHelpers._transport_filesystem
  assert teaHelpers.get_transport("something_new") is teaHelpers._transport_filesystem


def test_lfn_destination_url_applies_the_site_prefix():
  assert teaHelpers.stage_dest_url("/store/user/x/out.root") == (
    teaHelpers.STAGE_URL_BASE + teaHelpers.STAGE_LFN_PREFIX + "/store/user/x/out.root"
  )


def test_lfn_is_checked_before_the_pnfs_case():
  # realpath("/store/...") returns the string unchanged on a machine with no such path, so
  # a pnfs-first ordering would fall through to None and the caller would write a literal
  # "/store/..." file locally.
  assert teaHelpers.stage_dest_url("/store/user/x/out.root") is not None


def test_destination_url_honours_an_explicit_door():
  assert teaHelpers.stage_dest_url("/store/user/x/out.root", "davs://other.example:2880") == (
    "davs://other.example:2880" + teaHelpers.STAGE_LFN_PREFIX + "/store/user/x/out.root"
  )


def test_destination_url_is_none_for_an_ordinary_local_path(tmp_path):
  assert teaHelpers.stage_dest_url(str(tmp_path / "out.root")) is None


def test_transport_follows_the_destination_not_the_facility():
  # An LFN output needs gfal wherever the job runs; the facility table only gets to choose
  # when the destination resolves to no door URL.
  assert teaHelpers.select_transport("/store/user/x/out.root", "lxplus") is teaHelpers._transport_gfal
  assert teaHelpers.select_transport("/store/user/x/out.root", "default") is teaHelpers._transport_gfal
  assert teaHelpers.select_transport("/eos/user/t/x/out.root", "lxplus") is teaHelpers._transport_xrootd


def test_stage_output_to_an_lfn_copies_straight_to_the_destination(tmp_path, monkeypatch):
  source = tmp_path / "out.root"
  source.write_text("payload")
  staged = []

  def fake_gfal(local_path, stage_path, url_base=None):
    staged.append((local_path, stage_path, url_base))

  monkeypatch.setattr(teaHelpers, "_transport_gfal", fake_gfal)

  teaHelpers.stage_output(str(source), "/store/user/x/out.root", "lxplus")

  # No dot-file name and no os.makedirs of a local "/store" tree: the destination is
  # written directly, and gfal-copy -p creates the remote parent.
  assert staged == [(str(source), "/store/user/x/out.root", None)]
  assert not os.path.exists("/store/user/x")


def test_stage_output_passes_an_explicit_door_through(tmp_path, monkeypatch):
  source = tmp_path / "out.root"
  source.write_text("payload")
  staged = []
  monkeypatch.setattr(
    teaHelpers, "_transport_gfal", lambda local, stage, url_base=None: staged.append(url_base)
  )

  teaHelpers.stage_output(str(source), "/store/user/x/out.root", "lxplus", "davs://other.example:2880")

  assert staged == ["davs://other.example:2880"]


def test_preflight_demands_gfal_for_an_lfn_output_on_lxplus(monkeypatch, tmp_path):
  proxy = tmp_path / "voms_proxy"
  proxy.write_text("proxy")
  monkeypatch.setenv("X509_USER_PROXY", str(proxy))
  monkeypatch.setattr(teaHelpers.shutil, "which", lambda binary: f"/usr/bin/{binary}")
  ok, reason = teaHelpers.stage_preflight(["/store/user/x/out.root"], "lxplus")
  assert ok
  assert "gfal-copy" in reason

  monkeypatch.delenv("X509_USER_PROXY")
  ok, reason = teaHelpers.stage_preflight(["/store/user/x/out.root"], "lxplus")
  assert not ok
  assert "X509_USER_PROXY" in reason


def test_read_url_spells_an_lfn_with_a_double_slash():
  assert teaHelpers.read_url("/store/user/x/out.root", "maite.iihe.ac.be:1094") == (
    "root://maite.iihe.ac.be:1094//store/user/x/out.root"
  )
  assert teaHelpers.read_url("/store/user/x/out.root", "root://door") == "root://door//store/user/x/out.root"


def test_read_url_leaves_a_local_path_alone(tmp_path):
  assert teaHelpers.read_url(str(tmp_path / "out.root")) == str(tmp_path / "out.root")
