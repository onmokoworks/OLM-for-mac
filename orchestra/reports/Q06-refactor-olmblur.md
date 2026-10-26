status: blocked

summary:
- Readability-only OLMBlur refactor: structural commit `64bd41b8`, final source `5a7bf8e7`.
- Removed unreachable fallback; split typed adapters and retained-source validation into single-TU includes; named worker constants.
- Non-comment/non-blank source lines: 3,271 -> 2,618; largest source: 850 lines.
- G1-G4/G6 and OLMBlur build/UI/bundle checks pass; full G5 exits 1 on gate/corpus/other-plugin test failures.

facts:
- Branch `orch/Q06-refactor-olmblur` was clean at start. Base SHA: `e55bc78a463786e79261b8c251c41e361b218c6c`, from `git merge-base HEAD codex/public-beta-roi` before edits. MAIN's integration branch is `codex/public-beta-roi`; the old branch named `main` is not the current integration checkout.
- Read REFACTOR_SPEC, AGENT_GUIDE, OLMBlur ledger rows, GOTCHAS and the compatibility plan. No MAIN, emulator, release-gate file, forbidden-action list, generated source or other-plugin source changed. No worker rebuild or push.
- Main retains UI, Classic/Smart entry, geometry checks and typed dispatch. Workers.inc holds typed-world adapters and live PF16 observation; Fixtures.inc holds existing input admission. Both remain in the original translation unit; no build entry point needs another translation unit.
- Removed dead fallback after all six supported depth/Legacy branches return, its four 1-D kernels, three load_input specializations, old stores and fallback-only debug/parser helpers. Smart validates supported pixel formats before calling BlurRender; Classic never calls it. Live case0006 observation remains. The removed float/double-exp experimental path could not execute through shipped/reference public entry.
- Kept intentional per-depth and Legacy/Non-Legacy variants, with comments on byte/word conversion, float storage, alpha and carry differences. OLM_REFERENCE_BUILD, partition boundaries and OLM_PARALLEL_MAX behavior remain unchanged.
- Named constants (sample): kPassParts, kLastPassPart, kSigmaDivisor, kSmoothnessPercent, kRadiusPadding, kRoundingHalf, kInt32LowerBound/UpperBound, kLegacyCarrySentinel, kParallelMinDimension, kGlobalFlags/Flags2, kFloatExponentMask, kFiniteColourLimit, kObservedX/Y, retained PF16 source coefficients and constexpr palettes. Comments distinguish AEX arithmetic, native scheduling policy and retained-source data. Source-asserted UI/control/geometry expressions remain in main. No bit-pattern literal converted to decimal.
- Names clarified: Legacy helper a -> accumulator; fixture p -> expected_argb and at -> actual_pixel; byte/word/float palettes. Comments mark sigma doubling and helper tap/operand/NaN order. Explicit x86 operations remain unchanged.
- ROI source test now reads all six live workers instead of removed fallback strings. All five function tests explicitly invoked and passed. The generic gate unittest wrapper reports zero tests for this function-style file; that invocation is not counted as coverage.

| Gate | Real result |
| --- | --- |
| G1 structure | PASS: 12,012 exact, 0 differences/refusals/new refusals/execution errors. |
| G1 final | PASS: 12,012 exact, 0 differences/refusals/new refusals/execution errors, both architectures and builds. |
| G2 | PASS base/head: 139/139 saved records: 39 default + 43 downsample_P01a + 36 realistic_P02h + 18 P05c-parallel-boundary + 3 T15b-odd-even-realistic. Smart 139 exact; Classic 17 exact / 122 existing refusals. Replay retains recorded workers, timeouts and geometry flags. |
| G3 | PASS seed 909, realistic, 100 cases, default oracle. Base/head input hashes and result dictionaries equal for 100/100. Smart 100 exact; Classic 7 exact / 93 refusals; 0 pixel-mismatch cases. |
| G4 | PASS: 200 small + 20 HD + 5 UHD, caps 1/2/8: 675 exact, 0 refusals/mismatches. |
| G5 Xcode/package/UI | Universal Debug Xcode PASS; all 10 Universal bundles built and package ZIP verified. UI Blur: 2 updates / 4 checks including reload, 0 mismatches; all compared plugins have 0 mismatches. |
| G5 release-v2 | BLOCKED: exit 1. Framework/build/fresh-seeds/static PASS; corpus/bundle-checks/plugin-tests FAIL. All seven stages ran. |
| G6 | PASS: same Universal Debug Xcode command against archived base/head, 350 compiler warnings (4 message types) plus 2 Xcode project warnings in each build, 352 total / 6 unique messages, no new/increased message. |

- G1 full-run coverage: 4,004 comparisons per depth; 4,020 default / 3,996 realistic-v1 / 3,996 realistic-v2; 6,004 odd-even-v1; 12 full 3840x2160 comparisons. Downsample: 1/1, 1/2, 1/3, 1/4, 1/8 and anisotropic 1/2 x 1/3. First mismatch: none in either complete G1 run.
- Release-v2 framework: 50 tests, 3 skipped; build: 10 Universal bundles; static: all 10 Release configs and PiPL comparisons pass.
- Release-v2 corpus: 2,998 records, 2,862 PASS / 135 FAIL / 1 ORACLE-STOP. Its OLMBlur failures are the 21 nested records requiring --max-size 1920 / --size-max-height 1080 / odd-even-v1 / realistic; the correctly flagged independent G2 passes all 139. The same missing-max-size setup error was reproduced using archived base tools on olmdistancegradation_P04a (exit 2).
- First release corpus failure: `tests/fuzz_corpus/colorkeep/P04d-cropped-checkout/seed20261025-case096.json`, SHA256 `81836638a1adda2239c39db2b94b2f654589fd40be333dbc6d5ddf77584d2808`, current Classic/Smart refusal results do not match the saved record. This ColorKeep source is unchanged; its case was not individually rerun against base.
- Release-v2 fresh seeds: 6,000 total, E=5,692 / M=0 / R=250 / U=58 / errors=0; OLMBlur seeds 2026/2027 each have 300 Smart exact, zero pixel-mismatch cases.
- Bundle F47d: E=841 / M=0 / R=146 / U=13 / errors=0, all plugin verdicts PASS; OLMBlur 100 exact. F51: 3,349 equal_render / 128 equal_refuse / 521 difference; OLMBlur 239 equal_render. All 521 differences are ColorKeep host_error on both architectures (`unsupported/invalid callback: iterate`, selector 24 error 516), not measured pixel mismatches. First such record: 21x19 PF8, input SHA256 `e99780567c9ce233fe369420cc46337c417a13979476627be276756b8371b886`.
- Selected tests: 40 PASS / 5 FAIL. Failures: test_colorkeep_generic_beta_20260820.py, test_colorkeep_roi_tile_beta_20260820.py, test_olmcolorkey_generic_roi_tile.py, test_olmkirakira_generic_beta_sanitizers_20260820.py, test_olmkirakira_native_smoke_tuple_20260820.py. All four selected OLMBlur entries exit 0; the function-style ROI coverage is separately established by the explicit five-function invocation.
- Package SHA256: `5eecb19beccffcc175535047cec16bcbc22a7f5f1e71ac4cce799d458b915ac5`. Regenerable candidate, not an installed oracle.
- Initial package command built all plugins, then exited 1 for missing untracked reference_manifest.json. Retry used existing OLM_REFERENCE_ROOT pointing to MAIN plus --skip-build and passed, without copying MAIN assets.
- Archived-base G3 initially rejected scratch outside its archived root; corrected nested scratch and completed. Release-v2 initially rejected its R09-specific scratch guard; retry adjusted only in-memory TICKET and test concurrency to Q06 / 1. No gate acceptance check changed.
- The inherited compiler warnings include 14 logical-op-parentheses warnings in retained fixture predicates; their existing grouping/precedence was not changed.
- Four additional historical source tests fail in both revisions: typed-PF16 contract (missing old manifests; stale ERR(PF_COPY...) assertion), classic-current-install smoke (missing old handoff captures), classic-public-entry closure (missing plugins_2025; obsolete equal-rowbytes assertion), classic-bitdepth dispatch (raw error text predates refusal macros). Left unchanged. Current generic source unittest files pass in both revisions (4 + 3 tests).

Source line counts (`.cpp/.h/.inc/.r`, including unchanged sources):

| File | Before lines | After lines | Before code | After code |
| --- | ---: | ---: | ---: | ---: |
| `mac/OLMBlur/OLMBlur.cpp` | 2204 | 850 | 2034 | 746 |
| `mac/OLMBlur/OLMBlur.h` | 75 | 75 | 63 | 63 |
| `mac/OLMBlur/OLMBlurPiPL.r` | 33 | 33 | 31 | 31 |
| `mac/OLMBlur/OLMBlur_Fixtures.inc` | 0 | 252 | 0 | 220 |
| `mac/OLMBlur/OLMBlur_Strings.cpp` | 23 | 23 | 20 | 20 |
| `mac/OLMBlur/OLMBlur_Strings.h` | 14 | 14 | 13 | 13 |
| `mac/OLMBlur/OLMBlur_Workers.inc` | 0 | 438 | 0 | 394 |
| `core/olmblur_constants.h` | 0 | 24 | 0 | 13 |
| `core/olmblur_fullworker_helper.cpp` | 162 | 164 | 153 | 154 |
| `core/olmblur_fullworker_helper.h` | 30 | 30 | 22 | 22 |
| `core/olmblur_helper.cpp` | 136 | 136 | 123 | 123 |
| `core/olmblur_helper.h` | 32 | 32 | 22 | 22 |
| `core/olmblur_parallel_parts.h` | 32 | 33 | 24 | 25 |
| `core/olmblur_worker16_legacy.cpp` | 138 | 141 | 115 | 116 |
| `core/olmblur_worker16_legacy.h` | 24 | 24 | 17 | 17 |
| `core/olmblur_worker16_nonlegacy.cpp` | 157 | 160 | 135 | 136 |
| `core/olmblur_worker16_nonlegacy.h` | 32 | 32 | 24 | 24 |
| `core/olmblur_worker32_legacy.cpp` | 117 | 120 | 101 | 102 |
| `core/olmblur_worker32_legacy.h` | 23 | 23 | 16 | 16 |
| `core/olmblur_worker32_nonlegacy.cpp` | 110 | 113 | 93 | 94 |
| `core/olmblur_worker32_nonlegacy.h` | 22 | 22 | 15 | 15 |
| `core/olmblur_worker8_legacy.cpp` | 135 | 138 | 116 | 117 |
| `core/olmblur_worker8_legacy.h` | 25 | 25 | 17 | 17 |
| `core/olmblur_worker_orchestration.cpp` | 114 | 117 | 101 | 102 |
| `core/olmblur_worker_orchestration.h` | 24 | 24 | 16 | 16 |


inference:
- Gates establish bounded byte/refusal preservation, not new Windows AE/GPU conformance. Fallback removal follows supported-depth dispatch and admission, not a lack of fuzz hits.
- Possible latent host-contract issues left unchanged: BlurRender divides by downsample_x.den without a local zero guard; Smart output-checkout failure returns after input checkout without checkin. Whether AE supplies these states is unconfirmed; investigate in a separate lifecycle/invalid-host-input ticket.
- Fuzz adapter build_sources lists main/core sources but not the new transitive .inc/constant header explicitly. Compilation and native snapshots include them; use the complete recorded git revision and binary hashes for source identity. Updating shared provenance tooling is outside this ticket.
- Legacy coordinate-zero exclusion, carried RGB and inactive-alpha horizontal/vertical asymmetry are documented AEX behavior, not refactor bugs.

changed_files:
- mac/OLMBlur/OLMBlur.cpp, OLMBlur_Workers.inc, OLMBlur_Fixtures.inc.
- core/olmblur_constants.h, olmblur_parallel_parts.h, olmblur_fullworker_helper.cpp and six per-depth worker/orchestration .cpp files.
- tests/test_olmblur_roi_halo_contract_20260820.py (inspect live workers).
- This report and Q06-refactor-olmblur-evidence.json.

verify:
```sh
BASE=e55bc78a463786e79261b8c251c41e361b218c6c
MAIN='/Users/onmk/Documents/Projects/Personal/OLM as'
PY="$MAIN/tools/emulation/.venv/bin/python3"
STATE="$PWD/orchestra/state/Q06-refactor-olmblur/recheck"
mkdir -p "$STATE"
export TMPDIR="$STATE" TMP="$STATE" TEMP="$STATE" OLM_TEST_JOBS=1
python3 tools/refactor/native_diff.py --plugin olmblur --base "$BASE" --head HEAD --cases 3000 --seed 909 --arch both --build both --jobs 1 --scratch "$STATE/g1"
for corpus in tests/fuzz_corpus/*olmblur*; do
  "$PY" tools/fuzz/run.py --plugin olmblur --replay "$corpus" --jobs 1 --scratch "$STATE/replay" --report "$STATE/$(basename "$corpus").json"
done
for corpus in tests/fuzz_corpus/olmblur/P05c-parallel-boundary tests/fuzz_corpus/olmblur/T15b-odd-even-realistic; do
  "$PY" tools/fuzz/run.py --plugin olmblur --replay "$corpus" --jobs 1 --max-size 1920 --size-max-height 1080 --size-sampler odd-even-v1 --geometry realistic --scratch "$STATE/replay-nested" --report "$STATE/$(basename "$corpus").json"
done
"$PY" tools/fuzz/run.py --plugin olmblur --n 100 --seed 909 --geometry realistic --jobs 1 --scratch "$STATE/fuzz" --corpus "$STATE/corpus" --report "$STATE/g3.json"
"$PY" tools/perf/ref_vs_fast.py --plugin olmblur --jobs 1 --scratch "$STATE/g4"
python3 tests/ui_oracle/compare_mac.py --scratch "$STATE/ui"
python3 tests/test_olmblur_generic_beta_lane_20260820.py
python3 tests/test_olmblur_generic_classic_beta_20260822.py
python3 - <<'PY'
import runpy
for name, function in runpy.run_path('tests/test_olmblur_roi_halo_contract_20260820.py').items():
    if name.startswith('test_'):
        function()
        print('PASS', name)
PY
git diff --check
```
Expected counts are in the gate table, including existing Classic refusals. Release-v2 is expected to exit 1 until the reported blockers are repaired; oracle-stop/budget counts can depend on run conditions. For base G3/G6, archive BASE's mac/core/tools/cli/ucrtmath into ticket scratch, pass --main MAIN, and keep that runner's scratch/report/corpus under its own orchestra/state. Xcode commands are in the evidence JSON.

Package recheck in a fresh worktree (route build products to scratch and cap Xcode jobs):
```sh
python3 - <<'PY'
import os
from pathlib import Path
state = Path(os.environ['TMPDIR'])
bin_dir = state / 'bin'
bin_dir.mkdir(parents=True, exist_ok=True)
shim = bin_dir / 'xcodebuild'
shim.write_text('#!/bin/sh\nfor arg do\n  if [ "$arg" = "-jobs" ]; then exec /usr/bin/xcodebuild "$@"; fi\ndone\nexec /usr/bin/xcodebuild -jobs 1 "$@"\n')
shim.chmod(0o755)
for name in ('ColorKeep','OLMBlur','OLMColorKey','OLMDirectionalBlur','OLMRadialBlur',
             'OLMKiraKira','OLMToonDilate','OLMDistanceGradation','OLMSmoother','OLMSmoother2'):
    destination = state / 'package-builds' / name
    destination.mkdir(parents=True, exist_ok=True)
    link = Path('mac') / name / 'Mac/build'
    assert not link.exists(), link
    link.symlink_to(destination, target_is_directory=True)
PY
PATH="$STATE/bin:$PATH" OLM_REFERENCE_ROOT="$MAIN" bash scripts/package_mac_plugins.sh --configuration Debug --output "$STATE/plugins.zip"
```
Expected: all 10 Universal builds and package verification succeed. Remove those temporary build symlinks and regenerable build directories after checking.

Release-v2 (all seven stages; only scratch routing and concurrency adjusted in memory):
```sh
"$PY" -B - <<'PY'
import importlib.util, sys
from pathlib import Path
path = Path('scripts/run_olm_release_gate_v2.py')
spec = importlib.util.spec_from_file_location('release_gate', path)
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)
gate.TICKET = 'Q06-refactor-olmblur'
original = gate.Gate.__init__
def initialize(self, *args, **kwargs):
    original(self, *args, **kwargs)
    self.env['OLM_TEST_JOBS'] = '1'
    self.summary['OLM_TEST_JOBS'] = 1
gate.Gate.__init__ = initialize
sys.argv = [str(path), '--state', str(Path('orchestra/state/Q06-refactor-olmblur/recheck-release').resolve())]
sys.exit(gate.main())
PY
```
Package used TMPDIR under Q06 and a PATH shim adding `-jobs 1` only where absent. Conventional mac/<plugin>/Mac/build directories were temporary symlinks into Q06 scratch. Re-run `OLM_REFERENCE_ROOT="$MAIN" bash scripts/package_mac_plugins.sh --configuration Debug --output "$STATE/plugins.zip"` with the same job cap and scratch routing. No installed bundle or reference worker changed.

next:
- Separate gate/tool ticket: propagate recorded replay options, qualify the F51 iterate callback, and investigate the five out-of-scope selected-test failures; then rerun G5. Do not treat this report as an all-gates-pass merge authorization.
- Orchestrator review of the two source commits; no OLMBlur behavior fix is proposed. Consider the noted host-lifecycle concerns separately.

Cleanup: all started command exits were collected. Completed build trees, archived source trees, package ZIP and temporary package build symlinks were removed; shared cache workers and MAIN were not modified. A final scratch scan found zero Mach-O/object/archive files. Logs and JSON measurements remain under ticket scratch.
