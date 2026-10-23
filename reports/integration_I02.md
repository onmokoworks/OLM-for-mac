# I02 integration retry

status: blocked

Checked `c67a52fb388110966df4c8712cc570af69163929` on `orch/I02-integration-finish`. All four requested stages ran sequentially with `OLM_TEST_JOBS=2`; no gates overlapped. **This is not an integration PASS.** Two regressions are bisected. Full release-failure classification remains blocked by missing worktree inputs, stale bindings, and unresolved fixture failures.

## Facts: execution

| Run | Result |
|---|---|
| Release, unmodified gate | Exit 1 after fixture execution; missing worktree Windows return ZIP prevents final report |
| Generic, initial environment | 28 PASS / 25 FAIL / 0 SKIP; missing SDK links caused many failures |
| Fuzz framework, integration enabled | 14 tests PASS, 7.795 s; indexed radial-offset worker |
| All corpus directories, jobs 2 | 708 cases replayed; 686 saved results reproduced; 22 refusal→exact improvements |
| Release diagnostic retry, SDK available | Exit 1; fixture runner: 19 commands PASS, 194 FAIL, plus 3 installed-identity failures; 89 commands skipped in those three lanes |
| Generic retry, SDK available | **48 PASS / 5 FAIL / 0 SKIP**, no timeouts; 344.264 s |

The first release used the original command directly. The retry's `I02-release-with-log.py` observes the gate's existing `subprocess.run` return value and saves captured fixture stdout/stderr without changing commands, return codes, or gate files. The gate still aborts at `windows_boundary_gate()`. No release status/binding was refreshed.

The required return ZIP is absent here but present in MAIN with the expected SHA-256 `e582b0f368deb6dfbb34de2675e382d2222372705da043151d90dc895f7d7a0a`. This is a worktree asset-access failure, not an incorrect MAIN archive. SDK `Headers`, `Util`, and `Resources` were initially absent; ignored absolute symlinks to MAIN's SDK locations were created for read-only compilation. No MAIN files were changed.

## Facts: regressions and other failures

**(a) Generic gate self-test regression: F25 merge `dd7d8fa1f9c457628d2837aed81cce4016399d81`.** The real `test_main_publishes_running_before_execution_then_final_same_run_id`, with its own mocked work execution and the gate-child environment, passes at first parent `fe69053af992fae06864d75de83faadcb18d6cc3`; the merge and checked HEAD raise `SystemExit(2)`. F25 makes `execute_entry()` set `OLM_SELF_SPAWN_CHILD=1`; the self-test intentionally calls `main()` without `--run-test-file`, which the new guard rejects. The gate script has only this modifying first-parent merge between the runner fix and HEAD. This is test integration, not pixel evidence.

**(a) Retained DistanceGradation PF32 fixture regression: F02 merge `f7ce7e67e71e79fe99de37493b903c7f4aaeba57`.** Eight isolated revision probes found first parent `a95eebfc542ae0e5c70fc7850ee7b4092771f42f` good and that merge bad. Baseline `d027fd4db4596cc51cf790ce75557931af12e01d` passes both 2,992-byte fixtures. Merge and HEAD fail the first fixture with **748 differing bytes**. The existing harness only reports a count, so first byte index/value is unavailable. Source snapshots were extracted to scratch, compiled one at a time, and deleted.

Inference: this establishes a retained-test regression caused by the F02 integration boundary. It does not establish whether the historic retained fixture or current uniform-mask rendering agrees with a fresh original-AEX capture. Do not change numerical code to match the fixture without that check.

Final generic FAIL classification:

| Test | Classification and evidence |
|---|---|
| `test_run_olm_generic_beta_gate.py` | (a), F25 boundary above; child guard rejects mocked gate main |
| `test_olmkirakira_mode3_ui_windows_owner_20260821.py` | (b), repository-source identity size/hash drift |
| `test_generic_beta_perf_smoke_runner.py` | (b), invocation executable-prefix mismatch and KiraKira UHD command binding mismatch |
| `test_beta_support_documentation.py` | (b), four stale source hash/predicate/performance-text assertions; standalone 19 tests / 4 failures |
| `test_olmkirakira_mode3_ui_length_beta_20260821.py` | Inference (b), obsolete zero-length negative contract: `MODE3_UI_REJECT length=0 ... ok=0` at all depths; length 301 rejection checks remain `ok=1`. Harness `ok` means rejection contract succeeded, not render admission. F10 explicitly promoted all-rays-disabled tuples including Mode3. Eight tests / three failures. No new raw-output mismatch established by this test. |

For release fixtures, complete command-level triage and extracted evidence are in `integration_I02_evidence.json`; complete stderr is archived. The initial automated triage flags 129 commands with missing inputs, 80 with binding/documentation indicators, three installed-binding failures, and 44 needing interpretation (categories overlap; these are indicators, not a completed causal classification). The 748-byte failure above came from that last group. Other unresolved behavior includes DirectionalBlur adapter `layer3 err=-1 exact=0 visible=0 pad=1`. Those failures must not be silently called stale bindings.

Missing inputs include worktree-local `plugins_2025/*.aex`, `aex/...`, old external AEXCompat build paths, and untracked handoff/decomp data. They cannot honestly be forced into either requested class (a) or (b). No old worker was rebuilt and no assets were copied from MAIN. Installed identity drift prevents all Smoother, Smoother2, and ToonDilate fixture-lane commands from running; installing or rebinding binaries is outside this ticket.

The named known ColorKey documentation and KiraKira workspace-manifest failures recur. KiraKira additionally encounters missing disassembly here. Release documentation is not enumerated by the current fixed-fixture runner; a separate check ran eight tests with three failures. The ticket's before/after equivalence for those three tests remains supplied background, not a new I02 before/after experiment.

## Process explosion: source and observed safety

Historical source: `tools/emulation/test_olmradialblur_pf32_ellipse_32x18_actual_aex_20260811.py`, identified in fix `317e3ae9b79470034bfa0920b604d5e9a56b3dc2`.

`main()` → `compare_effect()` → failed actual capture → `isolated(...)[1]` returns `None` → production invocation omits expected-input filename → argv no longer matches production dispatch → old fallback re-enters campaign `main()` → recursive campaign spawning. Current child guards reject that malformed invocation. Inert dispatch checks show old main called once versus current exit 2 / zero main calls, including both ellipse siblings. Current preflight inventories 302 commands and zero literal pool sizes above two; F26's dedicated pool audit is broader than this literal-only check.

The runtime stderr contains 26 `refusing child invocation` messages. No command crossed the 100-descendant stop threshold. Both full release-stage trees peaked at four descendants (plus the stage root); sampled release retry peak RSS was 355,488 KiB.

Sampling occurred every five seconds using PPID-tree traversal plus `pgrep -g` counts for fixture-runner groups. Cross-PGID traversal is necessary because every fixture command starts a new session. **These are sampled maxima, not guaranteed instantaneous peaks.** Only 17 distinct commands could be identified in samples; fast failures can finish between samples. Two additional process-name keys were not identifiable commands. Unsampled commands have unknown maxima, not zero. Thus this environment-limited run cannot certify fully provisioned numerical campaigns.

Top 10 identified commands, combining both release runs (RSS and Python count include the command itself; descendants exclude it):

| Command | Descendants | Python | RSS KiB |
|---|---:|---:|---:|
| `tools/emulation/test_olmradialblur_type3_host_plumbing_20260811.py` | 2 | 1 | 302944 |
| `tools/emulation/test_olmradialblur_unproven_geometry_fail_closed_20260811.py` | 2 | 1 | 256560 |
| `-m unittest tests.test_olmcolorkey_real_sdk_suite_lifecycle_20260813 tests.test_olmcolorkey_source_bound_atomic_20260813 tests.test_olmcolorkey_public_entries_real_sdk_20260813` | 2 | 1 | 209776 |
| `tools/emulation/test_olmdirectionalblur_smart_cleanup_atomic_20260813.py` | 2 | 1 | 120448 |
| `tools/emulation/test_olmdirectionalblur_mac_smartrender_adapter_20260717.py` | 2 | 1 | 115616 |
| `tools/emulation/test_olmdistancegradation_pf32_effectmain_fixture_20260805.py` | 2 | 1 | 111632 |
| `tools/emulation/test_olmradialblur_zoom_pf32_noise_inner_actual_aex_20260810.py` | 2 | 3 | 109280 |
| `tools/emulation/test_olmradialblur_rotation_pf32_ellipse_actual_aex_20260811.py` | 2 | 3 | 105696 |
| `tools/emulation/test_olmradialblur_zoom_pf32_ellipse_actual_aex_20260811.py` | 2 | 3 | 98864 |
| `tools/emulation/test_olmkirakira_ramp_default_handle_relocation_20260805.py` | 1 | 2 | 42608 |

## Corpus results

Saved-result equality preserves known mismatches/refusals; it is not all-exact conformance.

| Corpus | Matches / saved |
|---|---:|
| colorkeep | 0 / 0 |
| olmblur | 39 / 39 |
| olmcolorkey | 3 / 3 |
| olmdirectionalblur | 56 / 56 |
| olmdistancegradation | 145 / 145 |
| olmkirakira | 8 / 8 |
| olmkirakira_gate_off_T06 | 40 / 62 |
| olmsmoother | 29 / 29 |
| olmsmoother2 | 8 / 8 |
| olmtoondilate | 300 / 300 |
| olmtoondilate_T13 | 23 / 23 |
| radialblur | 35 / 35 |

ColorKeep is empty and returns setup_error/exit 2. All nonempty corpora complete. The inventory wrapper exits 0 when iteration finishes; this is not an aggregate saved-result PASS, and each replay exit code is retained. The 22 changed KiraKira diagnostic cases retain identical oracle objects; Smart changes refusal→exact and every new output hash equals its oracle hash. Classic remains refusal. Current aggregate route states include 150 Classic mismatches and 32 Smart mismatches already present in saved results. The exact count is 131 Classic and 668 Smart; the rest are refusal/no-write states. No corpus was rebaselined.

## Reproduction and retained evidence

From this worktree, create scratch and export:

```sh
export OLM_TEST_JOBS=2 PYTHONDONTWRITEBYTECODE=1
export TMPDIR="$PWD/orchestra/state/I02-integration-finish"
export TMP="$TMPDIR" TEMP="$TMPDIR"
mkdir -p "$TMPDIR"
```

The exact executable/argv, revision, exit and elapsed time for each stage are in `integration_I02_evidence.json` under `runs`. Run each listed command through `python3 -B orchestra/reports/I02-run-monitored.py <stage> <command...>`, strictly one at a time, redirecting monitor output to scratch. Reports use scratch destinations. Before SDK-dependent checks, ensure `Headers`, `Util`, and `Resources` resolve to the absolute MAIN SDK locations; these ignored links are present in this worktree.

For the framework, also export `OLM_AEX_WORKER=/Users/onmk/.cache/olm-emu/radial_offset_reference_20261002/target/release/aex-guest-worker`. Unset this override for corpus replay so each corpus uses its recorded hash-bound worker. The monitor supplies `OLM_FUZZ_INTEGRATION=1` and a ticket-local framework scratch directory. No workers are rebuilt.

Fast focused verification:

```sh
python3 -B orchestra/reports/I02-integration-finish-preflight.py > "$TMPDIR/preflight.json" 2> "$TMPDIR/preflight.log"
python3 -B orchestra/reports/I02-bisect-gate-self.py > "$TMPDIR/gate-self-bisect.log" 2>&1
python3 -B orchestra/reports/I02-bisect-distance.py > "$TMPDIR/distance-bisect.log" 2>&1
python3 -B orchestra/reports/I02-summarize-processes.py > "$TMPDIR/ranking.log"
git diff --check
```

Expected: preflight 302 / zero over-limit sites; self-test probe passes parent and fails merge/HEAD; DistanceGradation first-bad merge F02; ranking matches retained five-second samples; diff clean. Bisection HEAD hashes change after this report commit, while source/test boundaries remain the same.

Complete logs, reports and sample JSONL: `integration_I02_logs.tar.gz`, SHA-256 `fdfc0d4fc31e20f90eb175a780db2f4cfcc72a7c38803999ccdbdc8e74243085`. Extract into ticket scratch with `tar -xzf reports/integration_I02_logs.tar.gz -C "$TMPDIR"` to inspect/rerank original measurements. No build trees are archived.

## Next

1. Fix F25's self-test/child-guard interaction without reopening recursive dispatch.
2. Investigate F02's 748-byte fixture change with a fresh original-AEX witness; retain both old fixture and current output evidence.
3. Provide a read-only worktree-aware asset/worker resolver and current installed identities, then finish release classification and runtime coverage. Do not rebind stale manifests merely to turn the gate green.
4. Reconcile the four generic stale-contract/evidence failures, then rerun the sequential checks.

Only reports and reproducibility helpers changed. No gate, plugin, ledger, corpus, installed binary, MAIN or emulator source was edited; no push/stash/history rewrite. Regenerable scratch directories were removed after execution, and monitored process groups were drained.
