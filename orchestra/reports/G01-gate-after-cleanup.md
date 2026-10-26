status: done
summary:
- Resumed G01 with obsolete retained-route checks removed and retained output bytes checked exactly.
- All 45 selected test files pass in the sequential precheck.
- Full release gate v2 passes 7/7, exit 0; no selected-route mismatch or cross-architecture difference.
- Production and release-gate code are unchanged.

facts:

Tested production revision: `c80a48c176a3eb9817c0d998baec681e03b3f471`, with the test-only changes in
this commit. Full gate ran from `2026-10-26T14:38:10.770512+00:00` to
`2026-10-26T15:29:22.123457+00:00` (UTC). Exact invocation:

```sh
TMPDIR="$PWD/orchestra/state/G01-gate-after-cleanup/tmp" OLM_TEST_JOBS=1 \
python3 -B scripts/run_olm_release_gate_v2.py \
  --state orchestra/state/G01-gate-after-cleanup/gate --jobs 1 \
  > orchestra/state/G01-gate-after-cleanup/gate.log 2>&1
```

Exit 0, `local_gate_pass: true`, `release_authorized: false`.

| Stage | Result | Measured result |
| --- | --- | --- |
| Framework | PASS | 50 tests, 3 skipped |
| Universal build | PASS | All ten bundles contain arm64 and x86_64 |
| Corpus | PASS | 2,998 cases: 2,996 PASS, 2 ORACLE-STOP, 0 FAIL |
| Fresh seeds | PASS | 20 campaigns × 300 cases: E=5,692, M=0, R=250, U=58, errors=0 |
| Bundle checks | PASS | F47d: E=941, M=0, R=46, U=13, errors=0; F51: 3,870 equal renders + 128 equal refusals, 0 differences |
| Selected plugin tests | PASS | 45/45 files exit 0 |
| Static | PASS | Ten release configurations/PiPL comparisons plus package layout |

E/R/U mean exact/refused/uncompared on the selected owner route; U is not a
numerical pass. The gate's existing policy permits these oracle stops.
The corpus cases `C46_seed1_case000280.json` and `C49_seed1_case000117.json`
under RadialBlur initially made replay group 54 exit 1. Both Smart reference
emulations stopped in the guest and still stopped on the gate's 120-second
retry. For both, the unmodified `persistent_stop_matches` check returned true:
current native Smart hash equals the saved successful reference hash, and the
Classic route remains unchanged. The gate classified both as ORACLE-STOP.
Raw saved/retried result objects are in `G01-evidence/corpus-oracle-stops.json`;
all corpus verdicts and the seven-stage summary are committed. No behaviour
failure was found; no production, release-gate, ledger, MAIN or cached worker
changes were made. No install, push or reference-worker rebuild occurred.

The test changes (no test files deleted):

| Test | Reason and preserved coverage |
| --- | --- |
| `test_olmblur_generic_beta_lane_20260820.py::test_geometry_representation_and_control_limits_are_explicit` | Replace the inline overflow-division spelling with the current shared checked-multiply call; preserve vector and control limits. |
| `test_olmdistancegradation_pf32_smart_unblurred_beta_20260820.py::test_pixel_count_is_checked_before_frame_allocation` | Replace obsolete division spelling with checked-multiply; preserve allocation ordering. |
| Same file, `test_pf32_smart_world_contract_is_bounded_aligned_disjoint_and_sdr` | Check current checked-multiply and `area` vector bound; preserve alignment, disjointness and SDR assertions. |
| `test_dblur_generic_backonly_beta_20260821.py` | Remove internal retained-route requirements from the ten 16×16 cases and 960×540 anchor. Split combined render failures into error/route/output/input/padding codes. Add exact active-byte comparison for all ten small cases; preserve negative-rowbytes checks and the existing anchor hash. |

The small-case expected bytes were captured from the pre-F01 native retained
implementation at `db59044515791af9890d0768c1fa4c7f5ad34034`, with its original
probe still requiring retained route 1. They are regression evidence, not new
AEX ground truth. The capture extracts historical plugin/core/header sources
into scratch and builds with the existing UCRT compiler wrapper. An initial
capture build failed because the extracted source lacked `ucrtmath/include`;
adding those historical headers resolved the compile failure. No tool rejection.

The committed 28,672-byte fixture SHA-256 is
`8722e9bfd894895b9148dda941ada8bfb08b119a0e3e80ac42e17c8f1d8600c6`.
All ten cases match: PF8 (2), PF16 (3), PF32 (5). First differing byte: none.
The current probe requires PF_Err_NONE, unchanged input, intact padding and exact
active bytes. It prints depth, case, parameters, offset, expected and actual on a
byte mismatch. The 960×540 anchor retains SHA-256
`1a25fefa174c7a69f1004ce42f116e9633967587bccc3278b0d2418d99084695`.
After the small cases passed, the anchor exposed the same obsolete route pin
(code 302); removing that implementation assertion left its output hash passing.

Standalone source tests: 2/2 OLMBlur and 7/7 DistanceGradation pass.
Sequential early `Gate.run` precheck: 45/45 files exit 0; commands and exits are
in `G01-evidence/early-tests-summary.json`. It ran alongside the full gate, with
at most two top-level build/emulator jobs and `OLM_TEST_JOBS=1`.

Production line counts use `G01-evidence/count_code.py`: tracked plugin-local
`.cpp/.c/.h/.hpp/.inc/.r/.mm`, excluding tests directories, comments and blank
lines. Includes LUTs and Rez resources; excludes shared core/ucrtmath and
`mac/DynamicControls.h`. These are source lines, not compiled instructions.

| Plugin | 12622f68 | Current | Delta |
| --- | ---: | ---: | ---: |
| ColorKeep | 714 | 704 | -10 |
| OLMBlur | 2,161 | 976 | -1,185 |
| OLMColorKey | 2,920 | 2,352 | -568 |
| OLMDirectionalBlur | 2,814 | 1,912 | -902 |
| OLMDistanceGradation | 2,384 | 2,354 | -30 |
| OLMKiraKira | 3,590 | 3,481 | -109 |
| OLMRadialBlur | 6,402 | 4,168 | -2,234 |
| OLMSmoother | 18,748 | 18,693 | -55 |
| OLMSmoother2 | 11,993 | 11,870 | -123 |
| OLMToonDilate | 917 | 755 | -162 |
| **Total** | **52,643** | **47,265** | **-5,378** |

Regenerable build trees and capture executables were removed. Gate and precheck
processes exited normally; no owned background worker remains. Logs/reports and
replay witnesses remain in scratch, below 5 GiB. Evidence hashes are in
`G01-evidence/sha256.json`. `git diff --check` and the production/gate diff check
(`git diff --exit-code -- mac core ucrtmath scripts`) both exited 0.

inference:
- The removed route checks pinned implementation choices rather than output
  behaviour. All retained small-case bytes and the anchor hash remain exact.
- Shared checked-multiply replaced the old inline overflow expressions; matching
  the current helper calls retains meaningful allocation and world-safety checks.
- This is the existing local gate's scope, not an expansion to all-input or
  native AE exactness. Its accepted oracle-stop policy is unchanged.

changed_files:
- `tests/test_olmblur_generic_beta_lane_20260820.py`
- `tests/test_olmdistancegradation_pf32_smart_unblurred_beta_20260820.py`
- `tools/emulation/test_dblur_generic_backonly_beta_20260821.py`
- `tools/emulation/fixtures/dblur_backonly_retained.{argb,md}`
- `orchestra/reports/G01-gate-after-cleanup.md`
- `orchestra/reports/G01-evidence/` (capture/count reproduction scripts, counts,
  gate/precheck summaries, oracle-stop evidence, verification logs and hashes)

verify:

Run from this worktree root. Use a new gate state directory (the gate deliberately
refuses an existing directory). The gate selects MAIN's existing Python venv and
prebuilt cached reference workers; no worker rebuild or plugin install is needed.

```sh
scripts/setup_ae_sdk_links.sh
mkdir -p orchestra/state/G01-gate-after-cleanup/recheck-tmp
TMPDIR="$PWD/orchestra/state/G01-gate-after-cleanup/recheck-tmp" OLM_TEST_JOBS=1 \
python3 -B scripts/run_olm_release_gate_v2.py \
  --state orchestra/state/G01-gate-after-cleanup/recheck-gate --jobs 1 \
  > orchestra/state/G01-gate-after-cleanup/recheck-gate.log 2>&1
```

Expected: exit 0, seven PASS stages, `local_gate_pass: true`. Oracle stop/budget
counts may vary; there must be no selected-route mismatch, harness error or
cross-architecture difference. `release_authorized` remains false by design.

Focused test and fixture reproduction:

```sh
TMPDIR="$PWD/orchestra/state/G01-gate-after-cleanup/recheck-tmp" OLM_TEST_JOBS=1 \
python3 -B tools/emulation/test_dblur_generic_backonly_beta_20260821.py \
  > orchestra/state/G01-gate-after-cleanup/recheck-backonly.log 2>&1
python3 -B tests/test_olmblur_generic_beta_lane_20260820.py
python3 -B tests/test_olmdistancegradation_pf32_smart_unblurred_beta_20260820.py
TMPDIR="$PWD/orchestra/state/G01-gate-after-cleanup/recheck-tmp" \
python3 -B orchestra/reports/G01-evidence/capture_retained.py \
  > orchestra/state/G01-gate-after-cleanup/recheck-capture.log 2>&1
cmp tools/emulation/fixtures/dblur_backonly_retained.argb \
  orchestra/state/G01-gate-after-cleanup/capture/retained.argb
python3 -B orchestra/reports/G01-evidence/count_code.py \
  > orchestra/state/G01-gate-after-cleanup/recount.json
git diff --check
```

Expected: all exit 0; retained fixture SHA-256 as above; source test counts 2 and
7; production totals 52,643 before and 47,265 after (while production is unchanged).
The count JSON includes the resolved HEAD, so its revision field changes on commit.

next:
- Orchestrator review and merge; no production fix is proposed.
- Native-host/release authorization remains outside this local-gate ticket.
