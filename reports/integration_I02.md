# I02 integration check — blocked at safety preflight

Checked revision: `fe69053af992fae06864d75de83faadcb18d6cc3`, branch
`orch/I02-integration-finish`. No release/generic gate or emulator campaign was
launched. This is **not an integration PASS**.

## Facts: why the release gate was not launched

The worker brief says “never more than 2 parallel emulator/build processes.”
The unmodified fixed-fixture runner enumerates 302 commands. A read-only AST
preflight found **18 literal pool declarations above two workers in 10 directly
enumerated scripts**. The runner has no `--jobs` option; setting `TMPDIR` or running
only one gate does not constrain these pools. See the complete source paths,
line numbers, pool sizes and hashes in `integration_I02_preflight.json`.

For example,
`tools/emulation/test_olmradialblur_rotation_pf32_size_noise_combo_actual_aex_20260810.py:99`
uses four workers mapping `isolated_actual()`, which launches one Python capture
subprocess per task at line 76. The production pool at line 103 similarly
launches subprocesses. The 32×18 ellipse script uses three workers; the separate
Rotation and Zoom ellipse scripts each use six workers.

More seriously, the two separate ellipse scripts still accept the malformed
production-child argument list by falling through to campaign `main()`:

- `tools/emulation/test_olmradialblur_rotation_pf32_ellipse_actual_aex_20260811.py`
- `tools/emulation/test_olmradialblur_zoom_pf32_ellipse_actual_aex_20260811.py`

Both are directly enumerated by the fixed-fixture gate. An isolated dispatch
experiment on **current source** reached a sentinel replacing `main()` once for
each script. No capture, compiler, subprocess, or recursive campaign was executed
by the experiment. The sentinel returns 99; **99 is an experiment marker, not a
real gate failure code**.

These are concrete safety blockers. I did not edit gate files, plugin code, or
silently monkey-patch test scheduling. Further work should first make these
scripts obey the machine limit and reject malformed child dispatch.

## Process explosion: source and causal path

Fact: commit `317e3ae9b79470034bfa0920b604d5e9a56b3dc2` names
`tools/emulation/test_olmradialblur_pf32_ellipse_32x18_actual_aex_20260811.py`
as the I01 fork-bomb source. The source first appears in
`25ee328e10d07618717837947d5d18c85145404f` (source history inspection, not a
runtime merge bisection).

The source establishes this path:

1. `main()` calls `compare_effect()` (lines 80–82).
2. `compare_effect()` captures reference results through `isolated()` and keeps
   the returned payload, discarding the capture return code (line 64).
3. If the capture produces no output, `isolated()` returns `None` as payload
   (line 55). The production call receives `expected=None` (line 66).
4. `isolated()` only adds the expected-input filename when `expected is not None`
   (lines 47–50). The resulting production child has five argv entries, while
   production dispatch requires six (line 109).
5. Before the fix, this unmatched invocation reached `main()` again. The child
   could repeat the capture/production campaign recursively.
6. The fix adds `OLM_SELF_SPAWN_CHILD=1`, a 1800-second subprocess timeout, and
   a dispatch guard before `main()`.

Fact: executing only the old and current `__main__` blocks with inert `main()`
sentinels reproduced the boundary for both `--zoom-production` and
`--rotation-production`: old dispatch reached the sentinel once; current dispatch
reached it zero times and exited **2**, printing `refusing child invocation`.

Inference: this validates the described recursive-dispatch mechanism and the
specific fix, without reproducing a process explosion. It does not independently
establish which capture originally failed or prove that every self-spawning test
is safe. The two unprotected sibling scripts demonstrate a remaining equivalent
dispatch hazard on this revision. Propagate this evidence to the queued F25 audit.

## Execution and measurement inventory

| Requested step | Result |
|---|---|
| Release gate | NOT RUN: safety preflight blocked launch |
| Generic beta gate | NOT RUN: preserve required execution order |
| Fuzz framework integration | NOT RUN: preserve required execution order |
| All corpus replays, jobs 2 | NOT RUN: preserve required execution order |
| Five-second descendant/Python/RSS sampling | NOT RUN: no runner launched |
| Top 10 commands by observed descendants | Unavailable; no runtime samples |
| Any command observed above 100 descendants | No observation; not a claim of safety |
| Gate failure classification / merge bisection | No new gate results to classify |

The three known stale-evidence failures named in the ticket remain **provided
background, not independently reverified I02 results**:
`tests.test_olm_release_documentation_20260806`,
`test_olmcolorkey_public_source_bound_docs_20260813`, and
`test_olmkirakira_smart_workspace_dependency_manifest_20260812`.
Do not classify the safety preflight as either a numerical regression or stale
evidence. No pixel comparison or first pixel mismatch was obtained.

The runner starts every command in a new session. Therefore a future monitor must
walk PPID descendants and account for their separate PGIDs: sampling only
`pgrep -g <runner-pgid>` would undercount. The release gate also captures regression
stdout/stderr internally, so its outer log does not stream live lane output.
These are source observations, not measured process counts.

An exploratory search also found hard-coded `/tmp` writes in other emulation
scripts, for example `test_olmradialblur_noise_type2_block_actual_aex_20260811.py:123`.
That script is not directly enumerated in this gate. Its reachability was not
established; this is **not** used as the decisive blocker. `TMPDIR` alone cannot
relocate a literal absolute path.

## Reproduce the safe checks

From this worktree:

```sh
mkdir -p orchestra/state/I02-integration-finish
python3 -B orchestra/reports/I02-integration-finish-preflight.py > orchestra/state/I02-integration-finish/preflight.json 2> orchestra/state/I02-integration-finish/preflight.log
```

Expected exit 0: 302 enumerated commands, 18 over-limit pool sites in 10 files;
two old dispatches call the sentinel and two fixed dispatches exit 2 without
calling it; both current sibling dispatches call the sentinel. The JSON `head`
will change after this report commit. Findings and source hashes should not.
No imports of emulator test modules occur. This narrowly scoped check does not
prove full runtime behavior or replace the pending gates.

Recorded SHA-256:

- Fixed-fixture runner: `2644d8710434ef8b74a29fcb387cc381307a2127fc4ec2fcfed76e53b6b79b74`
- Fixed 32×18 ellipse test: `1250f03e1e6740f51231d0373dd13e5c924d4a613aae018116fc0b33f3a261b9`

No background processes or build trees were created. Scratch contains only small
preflight JSON/log files (8 KiB allocated when checked). MAIN was not modified;
no pushes, stashes, history rewrites, or external messages were made.

## Follow-up

Finish F25's malformed-child audit, constrain each gate-listed subprocess pool to
two, and audit scratch-path behavior before resuming I02. Then run the four stages
strictly sequentially with logs, the cross-PGID five-second monitor and the
100-descendant stop, using indexed workers and `--jobs 2` for corpus replay.
Classify actual gate failures with evidence and bisect genuine regressions.
