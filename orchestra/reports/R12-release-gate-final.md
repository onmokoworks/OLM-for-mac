status: blocked
summary:
- Bisect identifies 20c4024277b215fe7bf7a673bfe53c7e06cc3d67 (P02a) as the first ColorKeep generic/ROI failure after R09.
- No unbalanced checkout: co/cc/ci/li count parameter checkout/color conversion/parameter checkin/layer-pixel checkin, respectively.
- Repaired stale ROI host expectations; production ColorKeep is unchanged. All 141 mutation cells are now asserted rather than counting only refusals.
- Release gate accepts worktree-local state and --jobs 1 (default remains 2); its seven stages and decision assertions are unchanged.
- Full gate: 4/7 stages PASS; release remains blocked by corpus configuration, pinned native-host callback rejection, and three other-plugin test failures.

facts:

## Root cause and measured boundary

`git bisect start 853db347 fa1af7d2` followed by `git bisect run orchestra/state/R12-release-gate-final/bisect.sh` found first bad **20c40242**. Its parent **5bb59841** passed (exit 0), and the commit failed (exit 1). Full bisect commands and each measurement are retained in `R12-evidence/bisect.log` and `bisect-results.json.gz`. `git bisect reset` restored `orch/R12-release-gate-final`; no history was rewritten.

The reproduced Smart PF8/PF16/PF32 error was `rc=0 life=1 phase=1 pads=1 unchanged=1 req=1 ih=1 co=101 cc=100 ci=101 li=1`. The failing condition was the probe's iteration phase/range assertion, not a pixel mismatch or lifecycle imbalance. The lifecycle has 101 parameter checkouts (count + 100 colors), 100 floating-color conversions, 101 parameter checkins, and one layer-pixel checkin for one layer-pixel checkout. Output checkout is a separate callback (`oh`), not `co`.

P02a changed only `mac/ColorKeep/ColorKeep.cpp` among the production/test/harness paths at the bisected boundary (Git blob identities retained in `history-blobs.json`). It replaced Smart manual layer-origin mapping with ordinary host iterate using `output->extent_hint` and `bottom - top`, matching the original AEX contract documented and independently exercised in `orchestra/reports/P02a-colorkeep-geometry.md`. The old synthetic probe fixed its loop and expected progress range to 4x3/three rows even when its output was 3x2 with a one-row extent, and required zero Smart iterate calls. That expectation became stale with the production geometry correction.

The new synthetic host verifies the actual range and rectangle supplied to iterate, stays within the negotiated input/output dimensions, and checks route-specific bytes against the retained AEX typed oracle. It does not claim that its synthetic local-coordinate mock is a native AE ROI oracle. Classic mapping and Smart host delegation are checked separately. The mutation matrix retains every old mutation and now asserts all **141** cells: expected error, iteration count, cleanup counts and phase, no-write on failure, source/header/request invariance, output canaries, and retained exact active pixels for unchanged-source layouts. The old aggregate expected only 49 successful predicates from a larger loop; valid mutations were otherwise unexamined. Format-bit mutation 26 retains exact-byte checks.

Both standalone entry points completed with exit 0:
- `scripts/run_olm_generic_beta_gate.py --run-test-file tests/test_colorkeep_generic_beta_20260820.py`
- `scripts/run_olm_generic_beta_gate.py --run-test-file tests/test_colorkeep_roi_tile_beta_20260820.py`

The runner first prints `Ran 0 tests / NO TESTS RAN` for its unittest discovery, then runs the module's standalone test functions; exit 0 records those functions passing. `python3 -B tests/test_release_gate_v2.py`: five decision tests PASS. SDK links were initially absent; the initial build failed before test execution, then the standard read-only SDK links were prepared. The ColorKeep candidate builder now respects TMPDIR and OLM_TEST_JOBS, avoiding historical handoff-directory build products and unconstrained Xcode jobs.

No production source was edited, so the ticket's conditional G1 native_diff requirement for a production fix does not apply. The fresh ColorKeep oracle and bundle results are recorded below as part of the unchanged release stages.

## Complete release gate

Command (exit **1**):

```sh
python3 -B scripts/run_olm_release_gate_v2.py \
  --state orchestra/state/R12-release-gate-final/complete --jobs 1 \
  > orchestra/state/R12-release-gate-final/complete.log 2>&1
```

Every stage ran to completion. `local_gate_pass=false`, `release_authorized=false`.

| Stage | Result | Actual result |
| --- | --- | --- |
| Framework | PASS | 50 tests run, 3 skipped |
| Universal build | PASS | 10 bundles, all arm64 + x86_64 |
| Corpus replay | **FAIL** | 2,864 PASS / 134 FAIL / 0 ORACLE-STOP, 2,998 total |
| Fresh seeds | PASS | 6,000 complete; E=5,695 / M=0 / R=250 / U=55 / errors=0 |
| Bundle checks | **FAIL** | F47d: E=841 / M=0 / R=146 / U=13 / errors=0. F51: 3,349 equal renders + 128 equal refusals + 521 differences = 3,998 pairs |
| Selected plugin tests | **FAIL** | 42/45 files PASS, 3 FAIL; both ColorKeep files PASS |
| Static | PASS | All 10 Release settings and PiPL comparisons satisfy the existing predicates |

All **134 final corpus failures** are missing-`--max-size` setup failures from **15 replay groups**; no final replay pixel mismatch was observed. The first failing group is `tests/fuzz_corpus/colorkeep/T15b-odd-even-realistic` (3 cases). `corpus-inventory.json` records the saved sizes, including two mixed-size directories. One initial RadialBlur oracle stop (`C49_seed1_case000117.json`) passed on the prescribed 120-second retry; it was not excused as ORACLE-STOP.

All **521 F51 differences** are ColorKeep rows with `host_error` on **both** architectures, not measured byte differences. Both logs report `F47c unsupported/invalid callback: iterate`. First row: `seed1/0`, PF8, 21x19, input SHA-256 `e99780567c9ce233fe369420cc46337c417a13979476627be276756b8371b886`. F47d similarly classifies all 100 ColorKeep bundle cases as refusals/rejects; that satisfies its existing refusal-tolerant predicate but does **not** establish bundle pixel equality. These hosts remain pinned, and no gate assertion or refusal policy was changed.

A separate bounded diagnostic tried the already-cached F52c geometry worker with the same ColorKeep bundle, seed 1, n=100, jobs=1. It produced **100 harness errors**, each `worker did not execute native selectors`: the adapter correctly refused to accept output without native-selector evidence. This is not a successful alternative bundle validation. Exact command, full report and log are retained under `R12-evidence/ck-geometry-*`; no worker was rebuilt or modified.

The three selected-file failures are:
- `tests/test_olmcolorkey_generic_roi_tile.py`: compilation fails with four errors because its probe's `OLMColorKeyInfo` lacks `distance_step_x` / `distance_step_y` used by `Kernel.inc`.
- `tests/test_olmkirakira_generic_beta_sanitizers_20260820.py`: render-success assertion fails, first `m1_h7_r0`, PF8, 17x11, `ok=0`, `callbacks=1/1/1/0`, parameters 25/25, `lifecycle=1`; stderr is empty, not a sanitizer diagnostic.
- `tests/test_olmkirakira_native_smoke_tuple_20260820.py`: render-success assertion fails for `m2_highlight_r3`, PF8, 1920x1080, `ok=0`, `callbacks=1/1/1/0`, parameters 25/25, `lifecycle=1`.

No root cause is claimed for the Kira failures, and neither other-plugin code nor tests were edited.

ColorKeep source-host fresh campaigns are **600/600 Smart-owner exact**, with zero Smart mismatch/refusal/uncompared cases. Its non-owner Classic diagnostics remain 146 exact / 235 mismatch / 219 refusal and are not promoted or repaired here. The release gate's owner selection remains Smart except Smoother v1 Classic.

The run began at `6a66b436`. The cleanup-phase assertion was strengthened in `20862f0d` **before** the plugin-test stage executed; subsequent commits add evidence/recipes only. `run-head-binding.json` proves no production files changed since the run began, the gate script SHA matches, and all 45 test SHA-256s recorded by the stage match the final files. This is disclosed rather than replacing the recorded start commit. Complete command exits, timing, test hashes, bundle hashes, and per-case F51 rows are retained in `gate-results.json` and `gate-evidence.tar.gz`.


The R11 recipe, with only R12 scratch/cache paths and scratch-contained product links, completed with exit **0**:

```sh
bash orchestra/reports/R12-evidence/build.sh > orchestra/state/R12-release-gate-final/package-build.log 2>&1
python3 orchestra/reports/R12-evidence/verify.py /Users/onmk/.cache/olm-emu/release-R12/OLM_Mac_Plugins_Release_20261026.zip orchestra/state/R12-release-gate-final/package-audit > orchestra/state/R12-release-gate-final/package-audit.log 2>&1
```

Audit exit **0**. ZIP: `/Users/onmk/.cache/olm-emu/release-R12/OLM_Mac_Plugins_Release_20261026.zip`

SHA-256: **`3bf6c2f8d8755e598b97faad5a6bc8b368d2d25e2f5c1eeeed31252657c2c9b2`**

Package source commit: `42dcc2f02e87195cc5f38700b764b2fea2725cea`, `git_dirty=false`. It contains **132 ZIP entries**, ten Universal ad-hoc signed bundles, both architectures with minimum macOS 11.0. The audit checked **76 text files** and **6 nested ZIPs**, found no local paths, verified docs/relative links, verified signatures, and matched executable hashes to the package manifest. Exact audit results and listing are committed. This audit does not replace the failed release gate or native AE validation.

Registered as `release-R12` in `/Users/onmk/.cache/olm-emu/INDEX.json`; the retained entry is `R12-evidence/cache-registration.json`. It explicitly records `published=false`, `local_gate_pass=false`, and `release_authorized=false`. Nothing was published, pushed, installed, or written into MAIN.

Regenerable build products and scratch binaries were removed after evidence retention. The gate archive preserves 232 reports/logs including every F51 case row. The durable ZIP remains in the cache. All started commands finished; no background worker remains.

inference:
- The reported 101/100/101 counters were mistaken for unmatched checkout/checkin counts; the actual failure is stale host-test geometry after an AEX-grounded production correction.
- Corpus setup failures found in the full gate are separate from ColorKeep's repaired phase expectation. A corpus launcher repair must group by saved configuration, including mixed-size directories, while retaining all current comparison predicates.

changed_files:
- `scripts/run_olm_release_gate_v2.py`
- `tests/test_colorkeep_roi_tile_beta_20260820.py`
- `tools/emulation/test_colorkeep_nine_color_public_closure_20260813.py`
- `orchestra/reports/R12-release-gate-final.md`
- `orchestra/reports/R12-evidence/*`

verify:
From this worktree, prepare the read-only SDK links and scratch:

```sh
scripts/setup_ae_sdk_links.sh
export TMPDIR="$PWD/orchestra/state/R12-release-gate-final/recheck-tmp"
mkdir -p "$TMPDIR"
export OLM_TEST_JOBS=1
olm_verify_python="$(dirname "$(git rev-parse --path-format=absolute --git-common-dir)")/tools/emulation/.venv/bin/python3"
"$olm_verify_python" -B scripts/run_olm_generic_beta_gate.py --run-test-file tests/test_colorkeep_generic_beta_20260820.py
"$olm_verify_python" -B scripts/run_olm_generic_beta_gate.py --run-test-file tests/test_colorkeep_roi_tile_beta_20260820.py
python3 -B tests/test_release_gate_v2.py
python3 -B scripts/run_olm_release_gate_v2.py --state orchestra/state/R12-release-gate-final/recheck --jobs 1 > "$TMPDIR/gate.log" 2>&1
```

Expected: both ColorKeep entry points exit 0; five decision tests pass. The full gate exits 1 with the documented three failing stages until follow-up repairs are made. `recheck` must be a fresh state directory. Guest timeout/uncompared counts may vary with machine load; none is an exact pass.

Audit the retained ZIP:

```sh
python3 orchestra/reports/R12-evidence/verify.py "$HOME/.cache/olm-emu/release-R12/OLM_Mac_Plugins_Release_20261026.zip" "$TMPDIR/package-audit"
```

Expected: audit exit 0, ten Universal ad-hoc bundles, both slices minos 11.0, no local paths in scanned text, docs/links present, manifest hashes equal executable hashes, and the SHA-256 recorded above.

The exact R11-derived rebuild is `bash orchestra/reports/R12-evidence/build.sh > "$TMPDIR/package-build.log" 2>&1`; expected exit 0. It writes the named R12 cache ZIP, so preserve the original archive if independently rebuilding. Package timestamps/source metadata mean rebuilt ZIP bytes need not match the retained hash. No publication/install step is present.

`git diff --exit-code d450c9dc -- mac/ColorKeep` exits 0 (production unchanged). `git diff --check` exits 0.

next:
- Repair release replay launch configuration by grouping on saved `max_size` (including mixed directories), without dropping corpus records or relaxing saved-result comparison.
- Provide/rebind a compatible native bundle host for ColorKeep's AEX-grounded iterate contract; repeat F47d and both-architecture F51. Replacing it with the tested F52c AEX worker did not meet native-selector proof requirements.
- Assign separate ColorKey ROI harness and Kira sanitizer/native-smoke investigations. Do not infer that Kira's assertion failures are numerical mismatches or memory errors from these logs alone.
- Re-run the complete release gate after those repairs. Native AE/Windows-host obligations remain unchanged; nothing was published or installed.
