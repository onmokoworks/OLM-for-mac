status: partial
summary:
- Moved Radial test workers/entry points to tools/fuzz/harnesses/radialblur; release preprocessing excludes them.
- Reused existing shared checked multiplication/address-range validation; removed redundant outer size/noise admission alternatives.
- Consolidated capture-free per-depth Zoom dispatch; moved the test-only RenderWorld overload and removed unused Zoom trig locals.
- Product non-comment lines: 6,207 -> 5,621; including relocated tests: 6,207 -> 6,189. Universal warning occurrences: 372 -> 366.
- Partial solely for the inherited G4 UI text assertion (Thickness flag 0 expected, existing 0x40); no test was weakened.

facts:
- Baseline: `ac9415d364d17d35b8a5f5834d6985325cdd6d6e`. Structural commit: `c8026c75`.
- Intermediate G1: 500 small + 3 UHD, arm64 reference/fast: 1,006 exact comparisons, 0 differences, 0 new refusals, 0 execution errors; first mismatch none.
- Final G1: seed 909, 3,000 small + 3 UHD cases per architecture/build, arm64 and x86_64, reference and fast: **12,012 exact comparisons, 0 differences, 0 new refusals, 0 execution errors; first mismatch none.** Summary SHA256 `42e5b8f1d989835d3e038426b2bfb5592d2cf09f18a6d744fc5585d75cff950b`. Final native_diff exit 0; full gate run once.
- G2: 506 observations each, all recorded Radial corpora, both Classic/Smart, recorded size/colour/geometry/timeout and candidate sanitizer flags. `cmp` exit 0. Identical SHA256: `1b4e8a0aca561c9985399656af9de6faa59f06914c5f4dbb202dc76672a4494f`. Native only; no oracle was rerun.
- G4: baseline/head Universal Debug Xcode builds both exit 0. Shared UI oracle exit 0, Radial 54 updates / 108 checks / 0 mismatches. Test-seam arm64 C++17 syntax check exits 0. `nm -g` finds no OLMRadialBlurTest symbol in the Universal product.
- The three Radial parameter UI text tests were invoked directly on each revision: 2 pass, 1 identical inherited failure per revision (`test_windows_control_types_and_ui_ranges_are_preserved`, Thickness flag assertion at line 21). UI declarations were not changed.
- Selected test modules: 6/6 tests pass across baseline sanitizers, Type-3 sanitizers, generic budgets, size/noise EffectMain, and global-polar Smart contract. The first pytest invocation failed because the MAIN venv has no pytest; the unchanged module-level test functions were then invoked directly with Python, exit 0.
- G5: total warning occurrences 372 -> 366; compiler warnings 370 -> 364 (two unchanged build-system warnings). The removed unused-function/variable warnings account for all six occurrences across both architectures. Remaining SDK, C++17-extension and shared-header warnings were not suppressed.
- Cleanup: completed Xcode trees, temporary native builds, G1 snapshots, and UI binaries removed; SDK symlinks created for this worktree removed. Logs and JSONL evidence remain in ticket scratch. No owned background verification process remains.
- No release gate was run. No original AEX, emulator, release gate, forbidden-action list, or other plugin source was modified.

inference:
- The historical size/noise control profile is a subset of baseline admission: its fixed strength/offset/ratio/quality/seed/thickness values and bounded size/noise values all satisfy the broader baseline predicate. Neutralizing size/noise in its world check changes none of the layout/center predicates. Removing only the outer OR alternatives preserves admission.
- Internal size/noise dispatch is retained: it can enter the noise builder at zero noise amount. Subset admission alone does not prove that removing those internal flags preserves floating-point behavior. No new conformance claim is made.
- Shared address-range validation is equivalent here: positive signed extents/stride are checked before conversion, active row bytes must fit stride, and total span must fit size_t and uintptr_t. Its tight-byte overflow check cannot reject an otherwise valid positive-stride span. Refusal tags/call sites remain unchanged.
- Existing per-depth arithmetic kernels were already templates. Only their duplicated capture-free dispatch was merged; pixel trait conversion differences and all arithmetic types/order remain intact.
- Test harnesses explicitly opt in with OLM_RADIALBLUR_TEST_SEAM. Guarded includes preserve retained harness callers while keeping test definitions outside the product tree; the unused four-argument render overload now belongs to the test entry include.
- Removed unused base_angle/cos_a/sin_a did not feed pixel computations; fixed-radian float sin/cos used by the Zoom renderer remain unchanged.

changed_files:
| File | Before | After |
|---|---:|---:|
| `mac/OLMRadialBlur/OLMRadialBlur.cpp` | 847 | 844 |
| `mac/OLMRadialBlur/RadialAdmission.inc` | 318 | 314 |
| `mac/OLMRadialBlur/RadialTestEntry.inc` | 291 | 0 |
| `mac/OLMRadialBlur/RadialTestWorkers.inc` | 272 | 0 |
| `mac/OLMRadialBlur/RadialWorldStorage.inc` | 111 | 106 |
| `mac/OLMRadialBlur/RadialZoom.inc` | 522 | 511 |
| `tools/fuzz/harnesses/radialblur/RadialTestEntry.inc` | 0 | 296 |
| `tools/fuzz/harnesses/radialblur/RadialTestWorkers.inc` | 0 | 272 |
- `orchestra/reports/C02-cleanup-olmradialblur.md` (this report).
- Counts remove comments and blank lines from tracked plugin `.cpp/.h/.inc`; new test files are included separately in the combined total. No new numeric constants or arithmetic types. No source file was enlarged beyond the refactor size limit.

verify:
```sh
BASE=ac9415d364d17d35b8a5f5834d6985325cdd6d6e
S="$PWD/orchestra/state/C02-cleanup-olmradialblur/recheck"
mkdir -p "$S"
export TMPDIR="$S" OLM_TEST_JOBS=1 OLM_PARALLEL_MAX=1
python3 tools/refactor/native_diff.py --plugin radialblur --base "$BASE" --head HEAD --cases 3000 --arch both --build both --jobs 1 --scratch "$S/G1" > "$S/G1.log" 2>&1
```
Expected: 12,012 comparisons, 0 differences/new refusals/execution errors.

Use the exact native-only G2 replay script embedded in `orchestra/reports/C01-cleanup-shared-math-and-tests.md` (unchanged), with this ticket's BASE and radialblur only:
```sh
mkdir -p "$S/base"
git archive "$BASE" mac core cli tools ucrtmath reports/radialblur_public_getters_aligned_20261001.json | tar -xf - -C "$S/base"
for name in Headers Util Resources; do ln -s "$PWD/$name" "$S/base/$name"; done
python3 - "$S" <<'PY_REPLAY'
import sys
from pathlib import Path
text=Path('orchestra/reports/C01-cleanup-shared-math-and-tests.md').read_text()
script=text.split("<<'PY_NATIVE'\n")[1].split('\nPY_NATIVE')[0]
(Path(sys.argv[1])/'replay_native.py').write_text(script)
PY_REPLAY
python3 -B "$S/replay_native.py" "$S/base" "$PWD/tests/fuzz_corpus" "$S/G2-base.jsonl" radialblur > "$S/G2-base.log" 2>&1
python3 -B "$S/replay_native.py" "$PWD" "$PWD/tests/fuzz_corpus" "$S/G2-head.jsonl" radialblur > "$S/G2-head.log" 2>&1
cmp "$S/G2-base.jsonl" "$S/G2-head.jsonl"
```
Expected: cmp 0, 506 observations and the hash above for each side. Set up SDK links first using `bash scripts/setup_ae_sdk_links.sh` if absent.

```sh
for side in base head; do
  TREE="$PWD"
  if [ "$side" = base ]; then TREE="$S/base"; fi
  OUT="$S/xcode-$side"
  xcodebuild -project "$TREE/mac/OLMRadialBlur/Mac/OLMRadialBlur.xcodeproj" -configuration Debug -jobs 1 ARCHS='arm64 x86_64' ONLY_ACTIVE_ARCH=NO MACOSX_DEPLOYMENT_TARGET=11.0 OBJROOT="$OUT/objects" SHARED_PRECOMPS_DIR="$OUT/pch" CONFIGURATION_BUILD_DIR="$OUT/products" build > "$S/xcode-$side.log" 2>&1
done
python3 -B tests/ui_oracle/compare_mac.py --scratch "$S/ui-oracle" > "$S/ui-oracle.log" 2>&1
clang++ -std=c++17 -arch arm64 -DOLM_RADIALBLUR_TEST_SEAM -IHeaders -IHeaders/SP -IUtil -IResources -fsyntax-only mac/OLMRadialBlur/OLMRadialBlur.cpp > "$S/test-seam.log" 2>&1
```
Expected: all exit 0; UI Radial checks 108, mismatches 0; Xcode warning counts above.

```sh
python3 -B - <<'PY_TESTS' > "$S/selected-tests.log" 2>&1
import runpy
from pathlib import Path
for suffix in ('generic_baseline_sanitizers_20260820','generic_type3_sanitizers_20260820','generic_budget_20260821','size_noise_effectmain_20260821','global_polar_smart_contract_20260820'):
    path=Path('tests/test_olmradialblur_'+suffix+'.py')
    for name,fn in runpy.run_path(str(path)).items():
        if name.startswith('test_') and callable(fn):
            fn()
            print('PASS',name,flush=True)
PY_TESTS
```
Expected: 6 PASS, exit 0. The separate parameter-UI text module still has its inherited Thickness assertion failure; do not weaken it to make this refactor green.

next:
- Resolve the inherited Thickness UI text-test contract in a separately authorized maintenance ticket. Existing production behavior and assertion are unchanged here.
- The orchestrator runs the release gate after all C02 merges. This report does not claim that gate was rerun.
