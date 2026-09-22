# Validating the condor stage-out path on a real facility

The scratch + stage-out path added in PR #126 and remediated afterwards cannot be
exercised on a laptop: it only engages when `_CONDOR_SCRATCH_DIR` is set by a real
HTCondor starter, and its transports (`gfal-copy` to dCache, `xrdcp` to EOS) need a
facility's storage and a valid VOMS proxy. This page lists the checks that must be run
**on the submit nodes themselves**, in the order that fails cheapest first.

Everything else is already covered without a facility:

| Already verified                                                                                             | How                                                                                    |
| ------------------------------------------------------------------------------------------------------------ | -------------------------------------------------------------------------------------- |
| URL derivation, atomic publish, backoff bounds, pre-flight outcomes, merge planning and `input_files` guards | `pytest tests/` (also a CI job — "Python unit tests")                                  |
| Generated `tmp/condor_run_<id>.sh` carries `--facility` and the two-location proxy probe                     | dry submission, see step 1                                                             |
| Scratch → validate → publish, exit codes, degrade-to-direct-write                                            | `condor_runner.py` driven by hand with `_CONDOR_SCRATCH_DIR` set, filesystem transport |
| `merge.py --dry` unchanged against `main` on the glob path; the phantom `./_merged` trees job is gone        | dry merge, see step 2                                                                  |

What is left is everything that depends on a real worker node, a real proxy and real
storage. Run the steps below on the facility named in each heading.

Pytest is part of the locked environment

---

## 1. Any facility — dry submission (2 minutes, no jobs run)

```bash
cd <analysis>/bin
python3 ecp_batch.py hist --group bkg --year 2024 --condor --dry --save_logs
```

Then inspect the two generated files that the submission would have used:

```bash
cat tmp/condor_run_<id>.sh
cat tmp/condor_config_<id>.sub
```

Expected in `tmp/condor_run_<id>.sh`:

- The proxy probe, with `<work_dir>` already substituted:
  ```sh
  if [ -f "$PWD/voms_proxy" ]; then
    export X509_USER_PROXY="$PWD/voms_proxy"
  elif [ -f "/afs/.../bin/voms_proxy" ]; then
    export X509_USER_PROXY="/afs/.../bin/voms_proxy"
  fi
  ```
  Neither branch may contain a literal `<work_dir>`, and `X509_USER_PROXY` must no longer
  be set unconditionally to `` `pwd`/voms_proxy ``.
- `--facility <name>` on the `condor_runner.py` line, with `<name>` being the facility you
  are actually on (`vub`, `lxplus`, `naf`) — **not** `default` and not the literal
  `<facility>`. A `default` here means `get_facility()` failed to recognize the submit
  node's hostname and every transport would fall back to a plain filesystem copy.

Expected in `tmp/condor_config_<id>.sub`: with `--save_logs`, `output`/`error`/`log`
pointing under `output/<id>/`, `error/<id>/`, `log/<id>/`.

## 2. Any facility — merge regression (5 minutes, no jobs run)

```bash
cd <analysis>/bin
python3 merge.py --files_config <a files config with real unmerged output> --dry -n 2 > /tmp/merge_new.txt
git -C ../tea stash        # or check out main's merge.py to a temp path
python3 merge.py --files_config <same config> --dry -n 2 > /tmp/merge_old.txt
diff /tmp/merge_old.txt /tmp/merge_new.txt
```

Consider hist_wtruth, there might be some unmerged hists there.
you can delete *_wtruth merged directories only for the purpose if this test, and only when the unmerged files are still there, and it is necessary.

Expected: the only difference is that a hist-only config (`output_trees_dir = ""`) no
longer plans a `[trees]` section against `./<sample>` / `./<sample>_merged`. Any other
difference in the planned batches is a regression.

## 3. VUB — one job, `--devel` (the important one)

```bash
source ~/cern.sh
voms
cd <analysis>/bin
python3 ecp_batch.py hist --group bkg --year 2024 --condor --devel --save_logs
```

When the job finishes, read its `.out` (under `output/<id>/`) and check the three things
below. **"In order" means the order the job does them in, not the order they appear in the
file** — see the note after the list.

1. `Stage-out pre-flight passed for facility 'vub': gfal-copy stage-out ready for N output(s)`
   — if instead you see _pre-flight failed_, read the reason: it names the missing piece
   (`gfal-copy` not on PATH, `X509_USER_PROXY` unset, proxy file unreadable). For an LFN
   destination this failure is fatal: the application does not run, because writing an
   LFN as a local `/store/...` path cannot produce a valid remote output.
2. `Executing command_args=[...]` with `--output_hists_path $_CONDOR_SCRATCH_DIR/hists/...`
   (and `--output_trees_path .../trees/...` for a skim). The app must be writing into
   scratch, not into `/pnfs`.
3. Exit code 0 from `condor_history -l <ClusterId>.<ProcId> | grep ExitCode`, and the
   merged-in destination file present at its final path with a non-zero size.

> ⚠️ **The `.out` is not in chronological order — grep it, don't read it top to bottom.**
> Both lines above are printed by `condor_runner.py`, whose stdout is a file and therefore
> block-buffered by Python, while the C++ app it launches inherits the same descriptor and
> writes unbuffered. So the app's thousands of lines land first and `condor_runner.py`'s own
> output is flushed at process exit, which puts the pre-flight line and the
> `Executing command_args=[...]` line at the **end** of the file, after output from a step
> that logically came later. This is cosmetic — the pre-flight really does run before the
> app, and the `Executing` line really is printed before the app starts — but it makes
> "check, in order" impossible to do by scrolling.
>
> This is deliberate and is **not** to be fixed with `python3 -u` or
> `PYTHONUNBUFFERED=1`: unbuffering costs a write syscall per line on every job, and these
> logs sit on shared storage. Read the log with `grep` instead, which is order-independent:
>
> ```bash
> grep -nE "pre-flight|Executing command_args" output/<id>/*.out
> ```
>
> The one thing you genuinely cannot conclude from the file is *timing* — the buffering
> destroys it. If you need to prove the pre-flight ran in the job's first seconds rather
> than at the end, take it from the wall-clock gap between the job's start in `log/<id>/`
> and the destination file's mtime, or from a deliberately-failing job (step 3b), which
> exits in seconds.

GFAL writes an LFN or dCache destination directly to its remote URL. It does not create a
local sibling `.stage-*` path and then call `os.replace`, so no `.stage-*` file is expected
for the VUB GFAL path. Confirm the final file instead:

```bash
gfal-stat davs://<door>:2880/<destination>
```

The `.<basename>.stage-<32 hex>` temporary name and atomic `os.replace` apply only when
publishing through a filesystem path. For such destinations, a leftover temporary file
after the job exits means the filesystem publication was interrupted or its rename
failed. Sweep for unexpected leftovers when validating that path:

```bash
find <results> -name '.*stage-*'    # expected: no output
```

### 3b. VUB — deliberately break the pre-flight

The point of the pre-flight is that a job with no credential fails in the first seconds
rather than after four hours. Force it:

```bash
cd <analysis>/bin
# in tmp/condor_run_<id>.sh from a --dry submission, replace the proxy probe with:
#   unset X509_USER_PROXY
condor_submit tmp/condor_config_<id>.sub
```

Note `GetEnv = True` in the submit file, so the job inherits the submitting shell's
environment: editing the probe is not enough on its own if `X509_USER_PROXY` is exported
where you submit from. Put a literal `unset X509_USER_PROXY` after the probe block.

Expected in the `.out`: `Stage-out pre-flight failed ... X509_USER_PROXY is not set`, with
text saying that the runner refuses to run. The job exits nonzero before the application
starts, so there must be no `Executing command_args=[...]` line and no output file.

This is also the cheapest way to confirm the pre-flight is early: with no credential the
whole job is over in well under a minute, so it cannot have spent hours before noticing.


## 4. lxplus — regression, since scratch is newly enabled there

Before this change lxplus never used scratch (staging was gated on the facility having a
remote backend, and only `vub` had one). It now stages through `xrdcp`, so one submission
is needed to confirm nothing regressed:

```bash
cd <analysis>/bin
python3 ecp_batch.py hist --group bkg --year 2024 --condor --devel --save_logs
```

Checks:

- The `.out` shows the pre-flight line and scratch paths, as in step 3.
- `should_transfer_files`/`when_to_transfer_output`/`transfer_output_files` still behave:
  the submission goes out with `condor_submit -spool`, and `condor_dummy.out` still comes
  back. A job held on output transfer points at the template, not at the staging code.
- If the destination is **not** under `/eos/user` or `/eos/home-*` (say an AFS work area),
  the log will say the path does not resolve to an EOS URL and the copy is a plain
  filesystem copy into the staging name. That is correct behaviour, not a fallback bug —
  the publish is still atomic.

## 6. naf — newly covered

naf is dCache like VUB and now uses the same `gfal-copy` transport. If the door differs
from VUB's, set it per-site rather than patching tea:

```bash
export TEA_GFAL_DOOR=davs://<naf door>:2880
export TEA_DCACHE_LOCAL_PREFIX=<naf local mount prefix, if any>
```

Run step 3 unchanged. If `_dcache_gfal_url` returns `None` for a naf destination the log
says so explicitly and the job falls back to a filesystem copy — that is the signal that
the prefix override is wrong, not that staging is broken.

---

## Interpreting a stage-out failure

| Symptom                                                                                    | Meaning                                                                                                                                                                                  |
| ------------------------------------------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `pre-flight failed ...` at job start                                                       | For an LFN destination this is fatal and the application does not run. A non-LFN destination can fall back to direct filesystem writing. Fix the reason named in the message.            |
| `stage-out attempt N/5 failed ...; retrying in Xs`                                         | Transient storage error. Each output independently receives five attempts. The wait is 20 s plus an exponential jitter (median ~80 s), so ~1500 concurrent jobs do not retry in lockstep. |
| `Failed to stage ... -> ...` then `Stage-out failed for: ... (outputs that did land: ...)` | Final failure after retries. Deliberately no direct-write fallback: writing to the final path after a failed transport is the corrupt-file bug this exists to prevent. Resubmit the job. |
| A `.stage-*` file left at a filesystem destination                                         | Filesystem publication was interrupted or `os.replace` failed. GFAL writes directly to the remote destination and does not use these temporary names.                                  |
