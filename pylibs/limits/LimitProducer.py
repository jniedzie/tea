"""Analysis-independent datacard production and labeled Combine result collection."""

from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from types import ModuleType, SimpleNamespace
from typing import Mapping, Optional
import re
import copy
import shlex
import subprocess
import warnings

from LimitPoint import LimitPoint, validate_collection, write_points
from LimitConfig import output_stem


def point_for_sample(config, sample) -> Mapping:
  """The config owns coordinates and normalization; never infer either from a sample name."""
  if hasattr(config, "point_for_sample"):
    fields = dict(config.point_for_sample(sample))
  elif hasattr(config, "point_adapter"):
    fields = dict(config.point_adapter(sample.name))
  else:
    fields = dict(config.signal_points[sample.name])
  fields.setdefault("id", sample.name)
  # Sample.cross_section defaults to -1, which is not valid nominal metadata.
  if "nominal_cross_section" not in fields and getattr(sample, "cross_section", -1) > 0:
    fields["nominal_cross_section"] = sample.cross_section
  return fields


def get_datacard_file_name(config, sample) -> str:
  if hasattr(config, "datacard_name"):
    name = config.datacard_name(sample)
  elif getattr(config, "use_combined_limits", False):
    raise ValueError("Combined cards require config.datacard_name(sample); no ALP name inference is performed")
  else:
    name = f"datacard_{config.histogram.getName()}_{sample.name}"
    if getattr(config, "do_abcd", False):
      name += "_ABCD" + ("pred" if config.use_abcd_prediction else "real")
  if not isinstance(name, str) or not name or Path(name).name != name or name in (".", ".."):
    raise ValueError("datacard_name must be a nonempty basename without directories")
  return name.removesuffix(".txt")


def parse_combine_output(text: str, identity: Mapping, blind: bool = False) -> LimitPoint:
  expected, observed = {}, None
  for line in text.splitlines():
    match = re.search(r"Expected\s+([\d.]+)%:\s*r\s*<\s*(\S+)", line)
    if match:
      q = round(float(match[1]) / 100, 6)
      if q in expected:
        raise ValueError(f"Duplicate Combine quantile {q}")
      expected[q] = float(match[2])
    match = re.search(r"Observed Limit:\s*r\s*<\s*(\S+)", line)
    if match and not blind:
      if observed is not None:
        raise ValueError("Duplicate observed limit")
      observed = float(match[1])
  if not expected:
    raise ValueError("No expected quantiles in Combine output")
  return LimitPoint(**identity, expected=expected, observed=observed)


def find_combine(config) -> str:
  if hasattr(config, "combine_setup"):
    return config.combine_setup
  path = shlex.quote(str(Path(config.combine_path).resolve()))
  for setup in (
    f"cd {path} && cmsenv",
    f"cd {path} && source env_lcg.sh",
    f"cd {path} && cmssw-el9 --no-home --command-to-run cmsenv",
    f"cd {path} && cmssw-el7 --no-home --command-to-run cmsenv",
  ):
    if (
      subprocess.run(
        ["bash", "-lc", f"set -e -o pipefail; {setup}; command -v combine >/dev/null"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
      ).returncode
      == 0
    ):
      return setup
  raise RuntimeError("Could not set up Combine; configure combine_setup or combine_path")


def run_combine(config, names: list, method: str = "AsymptoticLimits", condor: bool = False) -> dict:
  """Run isolated per-card commands, returning exit codes. Failed attempts never expose old logs."""
  if not re.fullmatch(r"[A-Za-z0-9_]+", method):
    raise ValueError("Invalid Combine method")
  directory = Path(config.datacards_output_path).resolve()
  setup = find_combine(config)
  commands = []
  for name in names:
    log = directory / f"{name}.log"
    # Preserve prior evidence but ensure collection cannot read a stale success after a failed launch.
    if log.exists():
      attempt = 1
      while log.with_suffix(f".log.previous-{attempt}").exists():
        attempt += 1
      log.rename(log.with_suffix(f".log.previous-{attempt}"))
    job_dir = directory / name
    job_dir.mkdir(exist_ok=True)
    blind = " --run blind" if getattr(config, "blind", False) and method == "AsymptoticLimits" else ""
    extra = " ".join(shlex.quote(str(arg)) for arg in getattr(config, "combine_arguments", ()))
    command = (
      f"set -e -o pipefail; {setup}; cd {shlex.quote(str(job_dir))}; "
      f"combine -M {method} {shlex.quote(str(directory / (name + '.txt')))}{blind} {extra} "
      f"> {shlex.quote(str(log))} 2>&1"
    )
    commands.append(command)
  if condor or getattr(config, "condor", False):
    return _run_condor(directory, names, commands)

  def execute(item: tuple) -> tuple:
    name, command = item
    return name, subprocess.run(["bash", "-lc", command]).returncode

  with ThreadPoolExecutor(max_workers=getattr(config, "limit_workers", None)) as executor:
    return dict(executor.map(execute, zip(names, commands)))


def _run_condor(directory: Path, names: list, commands: list) -> dict:
  """Wait on scheduler job states; disappearance alone does not imply successful completion."""
  import json
  import time
  import uuid

  work = directory / ("condor-" + uuid.uuid4().hex)
  work.mkdir()
  for i, command in enumerate(commands):
    script = work / f"job{i}.sh"
    script.write_text("#!/bin/bash\n" + command + "\n")
    script.chmod(0o755)
  submit = work / "jobs.sub"
  submit.write_text(
    f"executable = {work}/job$(Process).sh\noutput = {work}/$(Process).out\n"
    f"error = {work}/$(Process).err\nlog = {work}/events.log\n"
    "request_cpus = 1\nrequest_memory = 1000MB\ngetenv = True\n"
    '+JobFlavour = "espresso"\nmax_idle = 200\nmax_materialize = 1000\n'
    f"queue {len(names)}\n"
  )
  cluster = subprocess.check_output(["condor_submit", "-terse", str(submit)], text=True).split(".")[0]
  while True:
    active = json.loads(subprocess.check_output(["condor_q", cluster, "-json"], text=True))
    if any(job["JobStatus"] == 5 for job in active):
      raise RuntimeError(f"Held Combine job in cluster {cluster}; inspect {work}")
    if not active:
      break
    time.sleep(10)
  completed = json.loads(subprocess.check_output(["condor_history", cluster, "-json"], text=True))
  codes = {
    job["ProcId"]: job.get("ExitCode", 1) if job.get("JobStatus") == 4 and not job.get("ExitBySignal", False) else 1
    for job in completed
  }
  return {name: codes.get(i, 1) for i, name in enumerate(names)}


def get_limits(config, return_codes: Optional[Mapping] = None, statuses: Optional[Mapping] = None) -> list:
  points = []
  for sample in config.signal_samples:
    identity = point_for_sample(config, sample)
    name = get_datacard_file_name(config, sample)
    if statuses and sample.name in statuses:
      status, message = statuses[sample.name]
      point = LimitPoint(**identity, status=status, message=message)
    elif return_codes is not None and return_codes.get(name, 1) != 0:
      point = LimitPoint(**identity, status="failed", message=f"Combine exit code {return_codes.get(name, 'unknown')}")
    else:
      try:
        text = (Path(config.datacards_output_path) / f"{name}.log").read_text()
        point = parse_combine_output(text, identity, getattr(config, "blind", False))
      except FileNotFoundError:
        point = LimitPoint(**identity, status="unavailable", message="Combine log not found")
      except ValueError as exc:
        point = LimitPoint(**identity, status="failed", message=str(exc))
    if point.status != "ok":
      warnings.warn(f"{point.id}: {point.status}: {point.message}", RuntimeWarning, stacklevel=2)
    points.append(point)
  return validate_collection(points)


def save_limits(config, points=None) -> Path:
  path = (
    Path(config.limits_output)
    if hasattr(config, "limits_output")
    else (Path(config.results_output_path) / (output_stem(config) + ".json"))
  )
  write_points(path, get_limits(config) if points is None else points)
  return path


def produce_limits(config, method: str = "AsymptoticLimits", condor: bool = False) -> list:
  """Create cards, run Combine unless skipped, and persist each signal's status and complete identity."""
  import ROOT
  from HistogramsManager import HistogramsManager
  from DatacardsProcessor import NoSensitivityError

  if method != "AsymptoticLimits":
    raise ValueError("produce_limits supports AsymptoticLimits; use produce_significance for Significance")
  signals = list(getattr(config, "signal_samples", ()))
  others = list(getattr(config, "background_samples", ())) + list(getattr(config, "data_samples", ()))
  identities = [LimitPoint(**point_for_sample(config, sample), status="unavailable") for sample in signals]
  validate_collection(identities)
  names = [get_datacard_file_name(config, sample) for sample in signals]
  if len(names) != len(set(names)):
    raise ValueError("Datacard names collide; include the full model point identity")
  statuses, cards, input_files = {}, [], {}
  try:
    for sample in signals + others:
      if sample.name in input_files:
        raise ValueError(f"Duplicate sample name {sample.name}")
      try:
        file = ROOT.TFile.Open(sample.file_path, "READ")
        if not file or file.IsZombie():
          raise OSError(f"Cannot open {sample.file_path}")
        input_files[sample.name] = file
      except OSError as exc:
        if sample not in signals:
          raise
        statuses[sample.name] = ("unavailable", str(exc))
    for sample, name in zip(signals, names):
      if sample.name in statuses:
        continue
      try:
        point_config = SimpleNamespace(**vars(config)) if isinstance(config, ModuleType) else copy.copy(config)
        point_config.samples = [sample, *others]
        manager = HistogramsManager(point_config, input_files, name)
        for item in (sample, *others):
          manager.addHistosample(config.histogram, item)
        manager.normalizeHistograms()
        manager.buildStacks()
        manager.saveDatacards()
        cards.append(name)
      except NoSensitivityError as exc:
        statuses[sample.name] = ("no_sensitivity", str(exc))
      except (ValueError, OSError, KeyError) as exc:
        statuses[sample.name] = ("failed", str(exc))
    codes = None
    if cards and not getattr(config, "skip_combine", False):
      codes = run_combine(config, cards, method, condor)
    points = get_limits(config, codes, statuses)
    save_limits(config, points)
    return points
  finally:
    for file in input_files.values():
      file.Close()


def produce_significance(config, condor: bool = False, collect_only: bool = False) -> dict:
  """Preserve the example's Significance mode for existing, explicitly named data cards."""
  samples = list(config.data_samples)
  names = [get_datacard_file_name(config, sample) for sample in samples]
  if len(names) != len(set(names)):
    raise ValueError("Significance card names collide")
  missing = [name for name in names if not (Path(config.datacards_output_path) / (name + ".txt")).exists()]
  if missing:
    raise ValueError(f"Significance requires existing datacards: {missing}")
  codes = (
    None
    if collect_only or getattr(config, "skip_combine", False)
    else run_combine(config, names, "Significance", condor)
  )
  values = {}
  for sample, name in zip(samples, names):
    if codes is not None and codes[name] != 0:
      raise RuntimeError(f"Significance failed for {sample.name}: exit {codes[name]}")
    text = (Path(config.datacards_output_path) / (name + ".log")).read_text()
    match = re.search(r"Significance:\s*(\S+)", text)
    if not match:
      raise ValueError(f"No significance found for {sample.name}")
    from LimitPoint import finite_number

    values[sample.name] = finite_number(match[1], "significance")
  return values
