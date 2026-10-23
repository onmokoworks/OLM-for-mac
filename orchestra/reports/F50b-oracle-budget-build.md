status: blocked

summary:
- Built, installed and registered the unchanged F50 budget candidate using the authorized space-free build directory.
- Synthetic normal return passed; two exhaustion runs stopped at exactly the same 2,000,000,000-instruction boundary.
- Corpus validation found an acceptance regression: RadialBlur C45_seed45102_case000052 Smart returns with F46 but exhausts F50's budget.
- Stopped validation at that blocker: 1,403 byte-identical pairs, 7 uncompared pairs, 0 observed byte mismatches; corpus completion, S01 and seed-1 totals remain unqualified.
- Do not switch defaults to this candidate. No fuzz default, harness timeout, plugin, release-gate or ledger change was applied.

facts:

FACT — build and durable identity:

- `python3 tools/emulation/aexcompat_patches/build_F50.py > orchestra/state/F50b-oracle-budget-build/build-driver.log 2>&1` exited 0. Cargo used `--release --offline --locked -j 1`; CMake jobs=1. Build time: 2m48s. `memory_pressure` immediately before the Rust build reported **57% free**, above the required 30%.
- Physical build directory: `/Users/onmk/.cache/olm-emu/build-F50`. It was removed after successful installation.
- Installed worker: `/Users/onmk/.cache/olm-emu/worker-F50-budget/aex-guest-worker`.
- Worker SHA256: `92be4c0c8d873c6b9b20238b0389afadc64096e97193e2cac09be4441d7069d6`.
- Parent F46 SHA256: `6616943ba74e07d7f1c0209fe8e650bd496f6caa92fc5a1d3a4151063a36a903`.
- Unchanged F50 patch SHA256: `a60866763c08b0e597776cd9a0de2c3027246d2a509524ce726d1f7dc95f32bb`.
- `~/.cache/olm-emu/INDEX.json` contains exactly one matching F50 entry; its durable manifest is `~/.cache/olm-emu/F50-budget-build.json`. The patched source remains at `~/.cache/olm-emu/src-F50-budget/reference-guest`.
- Post-run audit matched all 546 retained source-file hashes to the manifest. Exactly two files differ from the verified F46 source: `crates/aex-guest-worker/src/x64.rs` and `crates/aex-guest-worker/src/x64/engine.rs`.

FACT — production-budget smoke:

- `python3 tools/emulation/aexcompat_patches/smoke_F50_budget.py > orchestra/state/F50b-oracle-budget-build/budget-smoke.log 2>&1` exited 0.
- A generated synthetic PE whose EffectMain executes `xor eax,eax; ret` returned successfully in 0.320935 seconds.
- A separate synthetic PE executes one XOR followed by alternating `inc rax; jmp`. Two executions exhausted the production budget in **709.005955** and **679.583908** seconds. Both snapshots contain **RAX=1,000,000,000, RIP=0x180001005, RVA=0x1005**, exactly the 2-billion-instruction boundary.
- Register assertions were added while the initial smoke process was running; both saved snapshots were independently checked afterward. The committed script includes those assertions, and `--audit` checks the installed hash, normal return and both saved boundaries without rerunning the long loops. Final audit exited 0.
- These are synthetic verification PEs; no original plugin binary was modified.

FACT — the two requested real-AEX smoke cases:

`python3 tools/emulation/aexcompat_patches/verify_F50.py smoke > orchestra/state/F50b-oracle-budget-build/smoke.log 2>&1` exited 0. This recipe records failures; its exit code does **not** imply equality.

| Case, Smart route | F46 | F50 | Output comparison |
| --- | --- | --- | --- |
| C49_seed1_case000117 | Guest stopped, 20.013962 s | Instruction budget, 861.385241 s; RIP 0x1800029b9 | Uncompared |
| C46_seed1_case000280 | Guest stopped, about 20.014 s | Instruction budget, 854.926 s; RIP 0x1800029f1 | Uncompared |

FACT — first acceptance regression and reason for stopping:

- Case: `tests/fuzz_corpus/radialblur/C45_seed45102_case000052.json`, **Smart** route.
- Input SHA256: `2742213296eee1bce7b7e6d8becf6ffe996af9efa2adf907e0a3f4df9dd7eed3`.
- **F46: status ok, 18.088 seconds**, guards/session checks passed. Raw output SHA256: `8dd8931b572b2d93f784d0d8d33da0604ebfb0a81488e6636e5f0ca6bec41133`.
- **F50: status budget, 800.601 seconds, no output**. Diagnostic: `execution stopped before the guest returned (instruction budget 2000000000 per scheduler slice; RIP=0x18000b46e)`.
- The corpus file hash was checked against the recorded pair. Full retained observation: `F50b-evidence/first-regression.json`.
- This is an accepted-input/output-availability regression, not a measured pixel-value mismatch. First differing output byte: **not available**, because F50 did not return an output.
- Validation was stopped because this candidate cannot meet the requested corpus-equivalence condition. The remaining campaigns were **not** silently treated as passing. No budget tuning was attempted; this stop is not a claim that the two-hypothesis/no-new-boundary rule was triggered.

FACT — partial corpus results:

The complete inventory is 769 saved cases, producing 1,509 distinct available-route pairs. ColorKeep has no saved cases; the recipe additionally defines six labeled generated depth/route anchors. At stopping, 1,410 pairs from 720 distinct corpus files were recorded; 99 saved-corpus route pairs and all six ColorKeep anchors remained unexecuted. One of those 720 files had only its Classic pair completed.

| Plugin | Byte-identical | Uncompared | Byte-different | Completion |
| --- | ---: | ---: | ---: | --- |
| OLMBlur | 72 | 6 | 0 | All saved pairs attempted |
| ColorKey | 18 | 0 | 0 | Complete |
| DirectionalBlur | 166 | 0 | 0 | Complete |
| DistanceGradation | 294 | 0 | 0 | Complete |
| KiraKira | 140 | 0 | 0 | Complete |
| Smoother | 29 | 0 | 0 | Complete; duplicate oracle route deduplicated |
| Smoother2 | 16 | 0 | 0 | Complete |
| ToonDilate | 646 | 0 | 0 | Complete, including T13 |
| RadialBlur | 22 | 1 | 0 | 23 of 122 route pairs recorded |
| ColorKeep | 0 | 0 | 0 | No saved corpus; six supplemental pairs unexecuted |
| Total | **1,403** | **7** | **0** | **Partial** |

All seven uncompared rows were inspected (`F50b-evidence/uncompared-review.json`). Six OLMBlur Classic rows have the same PF Handle allocation rejection in both workers. The seventh is the F46-success/F50-budget regression above. Shared rejections are not counted as byte equality.

Performance observations among identical outputs:

- DistanceGradation `seed104_case000207_S01`, Smart: F46 **3.858 s**, F50 **1027.504 s**, identical SHA256 `ce105eef699eaeadc66b5df833664962825b18db9b4991c99b60283db2863ea1`.
- RadialBlur `C45_seed45102_case000020`, Smart: F46 **7.280 s**, F50 **724.908 s**, byte-identical.
- Complete recorded timing aggregates are in `F50b-evidence/summary.json`; these are observations under shared-machine load, not fixed runtime guarantees.

FACT — execution accounting and unexecuted obligations:

- Corpus command: `python3 tools/emulation/aexcompat_patches/verify_F50.py corpus`, output redirected to the task scratch log. It resumes completed rows on rerun.
- A premature first invocation briefly overlapped the last real-AEX smoke, within the two-process limit. It recorded 97 pairs (91 identical, six uncompared), then was stopped to restore the requested serial order. Its in-flight pair was unrecorded. Corpus resumed only after smoke ended.
- The resumed corpus process was killed after the acceptance regression was inspected; shell exit **137**, not a completed validation exit. The next in-flight Smart row was not recorded. Process IDs and reason are retained in `stopped-processes.json`.
- **S01 transitions executed: 0 of 174** (111 RadialBlur, 63 DistanceGradation Smart failures identified from seeds 101–105).
- **DG/Radial seed-1 n300 campaigns executed: 0 of 4** (both workers requested). Exact/mismatch/refusal/uncompared campaign totals are **unmeasured**, not zero outcomes.
- No outer 3600-second watchdog expiry occurred in the recorded completed observations. This does not qualify it for all remaining cases.
- Build, smoke and corpus task processes have exited or were killed; a final PID check found no surviving listed processes. Interrupted regenerable pair/smoke directories were deleted. Scratch was far below 5 GiB; the Rust build tree is absent.
- Four Python scripts passed syntax checks. `smoke_F50_budget.py --audit`, source/INDEX identity checks and `git diff --check` passed. No tool permission rejection, push, stash, history rewrite, subagent, original AEXCompat edit, plugin-source edit, MAIN write, ledger edit or release-gate edit was performed by this ticket.

inference:

- The synthetic loop establishes deterministic exhaustion at this production instruction boundary despite different elapsed times; it does not bound arbitrary host callbacks, all 257 scheduler slices, or total wall time.
- The unchanged 2-billion-per-slice candidate is insufficient even for a case that F46 completed. Raising only the external watchdog cannot fix that failure.
- Recorded identical cases also show substantial execution-cost increases. This candidate is not qualified as a fuzz default on correctness/availability or runtime evidence.

changed_files:

- `tools/emulation/aexcompat_patches/build_F50.py` — authorized physical cache build directory, cleanup, F50b evidence paths.
- `tools/emulation/aexcompat_patches/verify_F50.py` — F50b paths, labeled ColorKeep supplements, generic single-pair replay, corrected resume documentation.
- `tools/emulation/aexcompat_patches/smoke_F50_budget.py` — synthetic production-budget checks and saved-evidence audit.
- `tools/emulation/aexcompat_patches/summarize_F50.py` — outcome/timing summaries without equating failures.
- `orchestra/reports/F50b-evidence/` — build binding/logs, smoke snapshots, partial corpus pairs, first regression, failure review, summaries and hashes.
- This report. Durable cache additions are listed above; no defaults changed.

verify:

From this worktree, quick retained-evidence checks:

```sh
python3 tools/emulation/aexcompat_patches/smoke_F50_budget.py --audit
python3 tools/emulation/aexcompat_patches/summarize_F50.py
git diff --check
```

Expected: audit PASS; the partial per-plugin counts above, seven uncompared rows, empty S01/campaign summaries; diff check exit 0.

Fresh single-case reproduction (long; output redirected as required):

```sh
mkdir -p orchestra/state/F50b-oracle-budget-build
python3 tools/emulation/aexcompat_patches/verify_F50.py pair --case tests/fuzz_corpus/radialblur/C45_seed45102_case000052.json --route smart > orchestra/state/F50b-oracle-budget-build/recheck-regression.log 2>&1
```

Expected: a new `F50b-evidence/recheck.jsonl` observation with F50 instruction exhaustion. The recorded F46 run returned the hash above; F46 still has its load-dependent 20-second timer and may itself time out under a different load. Recipe exit 0 means the observation was recorded, not equality. The generic `pair` CLI was additionally exercised on `tests/fuzz_corpus/olmcolorkey/seed47_case000178_C42.json` Smart: identical outputs, exit 0, recorded separately in `recheck.jsonl` (not added to corpus totals). The same `pair()` implementation produced the recorded regression during corpus execution.

For a fresh synthetic repeat, run `python3 tools/emulation/aexcompat_patches/smoke_F50_budget.py > orchestra/state/F50b-oracle-budget-build/budget-smoke-recheck.log 2>&1`; expected normal return and both exact boundary assertions, with variable durations. Build recipe intentionally refuses to overwrite retained workers.

next:

- Follow-up: determine a sufficient deterministic instruction budget and address the measured counting overhead in a separate worker candidate. Preserve F50 and F46 identities; do not tune plugin numerics. Use the accepted F46 regression above as an admission test.
- After that candidate passes, complete every saved corpus route plus ColorKeep anchors, all 174 S01 transitions, and the four seed-1 n300 campaigns. Retain the same serial/jobs=1 limits. Do not combine another worker's outcomes into these F50 evidence files.
- **Default-switch proposal, not applied:** reject promotion of this F50 candidate; keep the existing F46 default until a successor passes equivalence and the remaining measurements. A future switch must update both `default_worker()` and the timeout policy explicitly.
- **Matching-timeout proposal, not applied:** keep **3600 seconds** as an explicit opt-in watchdog for further F50 diagnostics (measured normal return reached 1027.504 s). It is not a proven bound for arbitrary calls or a remedy for instruction exhaustion. Do not claim that the old 10-second default qualifies F50, or that an unmeasured larger timeout fixes this candidate. Qualify a successor's default timeout from its completed runs before adopting it.
