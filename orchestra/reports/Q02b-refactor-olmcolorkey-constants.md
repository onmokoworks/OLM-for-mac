status: blocked
summary:
- Restored the numerical naming/declaration cleanup from 6eee3860 on the B01-fixed base and extended it to color coefficients, captured blur weights and distance-envelope names.
- Removed unreachable toggle admission checks/helpers; retained helpers directly used by hostless tests.
- Source code count shrank from 2,937 to 2,915 non-comment/nonblank lines; largest file is 653 lines.
- G1 12,012 exact; G2 102 identical Mac route results; Universal build and ColorKey UI checks pass; warnings unchanged.
- Strict G4 completion is blocked by inherited source-test/harness failures, reproduced on base and head.

facts:
- Base: `d9997b4ebcf840be27facdb0bee82fe11d6091c4`, containing B01 merge `e1c59da2`. Final production commit: `8fc86304` (preceded by `e0684ea3`). Branch: `orch/Q02b-refactor-olmcolorkey-constants`.
- Read AGENT_GUIDE, revised REFACTOR_SPEC, GOTCHAS, compatibility plan and targeted ColorKey ledger entries. Applied `git show 6eee3860 --format= -- mac/OLMColorKey` with `git apply`; existing Q02 test-reader changes were already present.
- No new translation unit, algorithm rewrite, type change, reassociation, generated-file edit, emulator rebuild, release-gate edit, MAIN edit or push.
- Constant examples: kLabLinearBreakpoint/kLabPower, kLabLSource/kLabASource/kLabBSource, kYuvY/U/V, kYccY/Chroma, kLabThresholdScale/kLabEpsilonScale/kLabOffsets, kHueDegrees, kRadiansToDegrees, kLab94Weights/kLab94DistanceScale, kCapturedAroundAmount*, kPublicAroundWeight/Plane, kInt32ExclusiveUpper, kDistanceCap/kFirstNonseed, kSquaredDistanceInfinity/kEnvelopeInfinity, kByteToUnit and kPublicBlurDirectionBias. Existing shell bit-pattern array remains byte-for-byte unchanged and is now constexpr. Decimal literals retain their exact spelling and float/double widths.
- Order comments preserve the AEX Lab sum, scalar threshold/epsilon products, NaN comparisons and per-depth writer distinctions. EDT v/z/k/q/s are now envelope_sites/breakpoints/envelope_index/query/intersection, with unchanged expressions and loop order.
- Dead cleanup: three unused is_16bpc methods, redundant includes, redundant ExactColor forward declarations, IsBoundedToggleInfo and IsBoundedToggleSource, and unreachable Lab/toggle tail admission checks. IsBoundedLab76NativeTuple/BoundedLab76Input/Key and ToggleFixturePixel/RGBA remain because retained hostless tests call them directly; their non-template helpers/specializations are inline to avoid unused warnings once production calls disappear. ClassicWorldsMatch likewise remains test-used.

G1:
- `python3 tools/refactor/native_diff.py --plugin olmcolorkey --base d9997b4e --head HEAD --cases 3000 --seed 909 --arch both --build both --jobs 1 --scratch "$STATE/G1-verified" > "$STATE/G1-verified.log" 2>&1` returned 0 at production commit `8fc86304aaa45ed703849ace40747d122ccca4df`.
- **12,012 / 12,012 exact**, 0 differences, 0 refusals, 0 new refusals, 0 execution errors. Each architecture/build pair passed 3,003 comparisons (3,000 small plus 3 UHD). First mismatch: none. All eight native compiler logs contain 0 warnings. Summary SHA256: `eff5e6e67404a30daffe64770f5fbac57f44be30066b22c3dfd1f9509488d933`.
- Two exploratory runs were explicitly interrupted to finish naming and eliminate newly exposed test-helper warnings; neither is claimed as a complete gate. The first completed arm64/reference pair had 3,003 exact comparisons. No observed numerical/refusal difference motivated these interruptions.

G2 (Mac only):
- Shared tools/fuzz adapters build/candidate, core.load_corpus and geometry.require_host replayed all 51 JSON witnesses recursively under tests/fuzz_corpus/olmcolorkey, including all six parent directories.
- Each witness restored saved max_size, size_max_height, size_sampler, color_sampler and case_timeout_seconds; load_corpus restores the saved case/geometry. Each recorded case ran both adapter routes, Classic and Smart, on archived base and final head.
- `python3 "$STATE/replay_mac.py"` (reproducible inline equivalent below) returned 0: **102 equal native route results**, 204 candidate invocations. Compared status/error/metadata, raw length/SHA256 and refusal tags normalized only for source line suffix. First Mac mismatch: none. No oracle process was run; oracle diagnostics and timing are excluded by the revised gate.
- Base/head G2 rows SHA256: `0978ae1e18e46d3f31ad86acc2ce534c77035bccb303a0637429901409387826`.

G4/G5:
- `python3 tools/fuzz/build_F47_bundles.py --plugins OLMColorKey --scratch "$STATE/xcode-verified"` returned 0: x86_64 arm64 Universal Release build, jobs 1. The same baseline command returned 0.
- Compiler warning occurrences: base 342, final 342; warning-message multisets are identical (0 added, 0 removed). Intermediate removal exposed unused fixture warnings (356 then 344); inline declarations resolved those without deleting test coverage.
- `python3 tests/ui_oracle/compare_mac.py --scratch "$STATE/ui-verified"` returned 0. ColorKey: 36 updates, 72 checks including reload, 0 mismatches.
- Direct runpy invocation of the parameter-UI test functions: 3/3 pass on base and final head.
- Unmodified legacy tests remain baseline-red: parameter-order unittest setUpClass fails its ParamsSetup regex (0 tests run); classic-dispatch unittest errors because the unchanged OLMBlur PF32 branch no longer contains its expected return literal (1 test attempted); typed-tinyworld has two source-assertion failures and a compile failure because its hostless OLMColorKeyInfo lacks distance_step_x/y (4 diagnostics). These same first failures occur on base and final head. No assertions were weakened and other plugins were not edited. G4's literal all-tests-green condition is therefore not claimed; these inherited failures need a separate test-maintenance ticket.
- Initial legacy-test invocation inherited macOS temporary storage under /var/folders rather than ticket scratch; TemporaryDirectory removed its outputs. Final baseline/head test runs explicitly set TMPDIR/TMP/TEMP to ticket scratch. No /tmp path was used by this worker.

inference:
- The final differential evidence establishes no observed behavior change over these cases, not universal AEX equivalence.
- The removed tail admission branches cannot succeed after the pixel_local return: both require Thin=Blur=0. This is a control-flow proof, independently checked by G1/G2.
- Captured blur constants retain the pre-existing evidence boundary. Naming them does not generalize the captured curves, endorse new per-case patches, or claim fresh AEX measurements. Comments distinguish recovered AEX constants from retained capture/port policy values where a precise RVA was not established here.

changed_files:
- mac/OLMColorKey/{AdmissionFixtures,BlurMath,ColorMath,Diagnostics,Distance,Kernel,Parameters,Pixels,Render}.inc
- orchestra/reports/Q02b-refactor-olmcolorkey-constants.md

refactor_accounting:
Counts strip C/C++ block/line comments and then count nonblank lines, including the same cpp/h/inc/r files before and after. Total code 2,937 -> 2,915 (22 fewer); no file exceeds 653 physical lines.

| File under mac/OLMColorKey | Physical before / after | Code before / after |
|---|---:|---:|
| AdmissionFixtures.inc | 409 / 356 | 374 / 324 |
| BlurMath.inc | 260 / 275 | 215 / 230 |
| ColorMath.inc | 129 / 152 | 104 / 126 |
| Diagnostics.inc | 169 / 160 | 157 / 149 |
| Distance.inc | 213 / 213 | 188 / 186 |
| Kernel.inc | 647 / 653 | 575 / 581 |
| OLMColorKey.cpp | 333 / 333 | 287 / 287 |
| OLMColorKey.h | 161 / 161 | 146 / 146 |
| OLMColorKeyPiPL.r | 33 / 33 | 31 / 31 |
| OLMColorKey_Strings.cpp | 44 / 44 | 41 / 41 |
| OLMColorKey_Strings.h | 35 / 35 | 34 / 34 |
| Parameters.inc | 234 / 235 | 224 / 225 |
| Pixels.inc | 176 / 175 | 161 / 159 |
| Render.inc | 432 / 429 | 400 / 396 |

verify:
From this worktree, with a fresh scratch directory:

```sh
BASE=d9997b4ebcf840be27facdb0bee82fe11d6091c4
STATE="$PWD/orchestra/state/Q02b-refactor-olmcolorkey-constants/recheck"
mkdir -p "$STATE/base"
export TMPDIR="$STATE" TMP="$STATE" TEMP="$STATE" OLM_TEST_JOBS=1 PYTHONDONTWRITEBYTECODE=1
python3 tools/refactor/native_diff.py --plugin olmcolorkey --base "$BASE" --head 8fc86304 --cases 3000 --seed 909 --arch both --build both --jobs 1 --scratch "$STATE/G1" > "$STATE/G1.log" 2>&1
python3 tools/fuzz/build_F47_bundles.py --plugins OLMColorKey --scratch "$STATE/xcode" > "$STATE/xcode.log" 2>&1
python3 tests/ui_oracle/compare_mac.py --scratch "$STATE/ui" > "$STATE/ui.log" 2>&1
git archive "$BASE" mac core cli tools ucrtmath scripts/setup_ae_sdk_links.sh reports/radialblur_public_getters_aligned_20261001.json | tar -xf - -C "$STATE/base"
python3 "$STATE/base/tools/fuzz/build_F47_bundles.py" --plugins OLMColorKey --scratch "$STATE/xcode-base" > "$STATE/xcode-base.log" 2>&1
```

Expected: G1 12,012 exact, zero differences/new refusals/execution errors; both Universal builds succeed; 342 warnings each; ColorKey UI 72 checks/zero mismatches.
The following executes the already-committed Q07 Mac replay recipe with only the plugin list changed; its base directory is $TMPDIR/base and candidate source is the current worktree. No new renderer or test script is introduced.

```sh
python3 - <<'PY_REPLAY'
from pathlib import Path
text = Path('orchestra/reports/Q07-refactor-olmsmall.md').read_text()
code = text.split("python3 - <<'PY_REPLAY'\n", 1)[1].split('\nPY_REPLAY', 1)[0]
code = code.replace("for plugin in ('olmsmoother2', 'olmsmoother', 'olmtoondilate', 'colorkeep'):", "for plugin in ('olmcolorkey',):")
exec(compile(code, '<Q07 shared Mac replay recipe>', 'exec'))
PY_REPLAY
```

Expected: `olmcolorkey 102 equal native route results` (base/head rows identical).

Legacy test reproduction (same runpy/unittest entrypoints used above; expected baseline failures described under G4/G5):

```sh
python3 - <<'PY_TESTS'
import runpy, unittest
from pathlib import Path
for filename in ('test_olmcolorkey_parameter_ui_parity_20260806.py',
                 'test_olmcolorkey_parameter_order_static_20260728.py',
                 'test_colorkey_toondilate_mac_typed_tinyworld_matrix_20260728.py',
                 'test_olmblur_colorkey_classic_render_bitdepth_dispatch_20260716.py'):
    namespace = runpy.run_path(str(Path('tests') / filename))
    for name, function in namespace.items():
        if name.startswith('test_') and callable(function):
            try:
                function()
                print(filename, name, 'PASS')
            except Exception as error:
                print(filename, name, 'FAIL', type(error).__name__, str(error))
    for cls in namespace.values():
        if isinstance(cls, type) and issubclass(cls, unittest.TestCase):
            unittest.TextTestRunner().run(unittest.defaultTestLoader.loadTestsFromTestCase(cls))
PY_TESTS
```

For the baseline comparison, archive these four `tests/` files at BASE into `$STATE/base`, then execute the same block from that directory with TMPDIR still pointing to ticket scratch. Results should match the failures above, not be interpreted as a passing suite.

next:
- Strict all-gates completion is blocked by the inherited G4 failures. The refactor implementation and numerical gates are complete; do not label the whole test suite green.
- Orchestrator review and fresh-seed G1; release gate/packaging remain orchestrator-owned under the revised spec.
- Separate test-maintenance ticket for the inherited parameter-order/classic-dispatch regexes and typed-tinyworld stale struct/assertions; no numerical tolerance changes.
- All started processes finished or were explicitly interrupted and reaped. Deleted archived source/build trees, Universal bundles, UI executables/generated source, and task-created SDK symlinks. Retained logs/results occupy 200,549,928 bytes, below 5 GiB. No durable reference worker was created.
