status: blocked
summary:
- Admission checks reuse shared world-safety helpers and compute invariant predicates once.
- PF8/PF32 scanline composition is shared; PF16 keeps its distinct field/store semantics.
- Non-comment source lines: 2,353 -> 2,323; universal Debug warning occurrences: 366 -> 342.
- Test-helper extraction needs two include-only edits outside the explicitly authorized scope; approval requested, pending.
- Full G1: 12,012 comparisons, zero differences/new refusals/execution errors; G2 unchanged; release gate not run.

facts:
- Baseline: `62a470a98bb4dce1c9a371209f0d0261a1840580`.
- Admission commit: `49d581ec`; composition/conversion commit: `deb38a6e`.
- Each structural step ran `tools/refactor/native_diff.py --plugin olmdistancegradation --base 62a470a98bb4dce1c9a371209f0d0261a1840580 --head WORKTREE --cases 500 --arch arm64 --build both --jobs 1` with separate scratch directories. Both results: 1,006 comparisons, 998 exact, 8 unchanged refusals, 0 differences, 0 new refusals, 0 execution errors. First mismatch: none.
- Final G1 ran once: `python3 tools/refactor/native_diff.py --plugin olmdistancegradation --base 62a470a98bb4dce1c9a371209f0d0261a1840580 --head HEAD --cases 3000 --arch both --build both --jobs 1 --scratch "$TMPDIR/G1-final"`, with HEAD `deb38a6ec4048d93c6496ec052d3de659019e2ae`. Exit 0: 12,012 comparisons, 11,912 exact, 100 unchanged refusals, 0 differences, 0 new refusals, 0 execution errors; first mismatch none. Summary SHA256: `7101e219cef8f5a2a47bfb6ac352f566b1873c6ceadaa1f4b06451ac01538520`. Each architecture/build had 2,978 exact and 25 unchanged refusals.
- G2 used the native-only replay recipe from the C01 report against every saved `plugin=olmdistancegradation` corpus item, with recorded flags: 461 cases, Classic and Smart, 922 observations per revision, all successful. `cmp` returned 0. Both JSONL SHA256: `f34dfda386d95f840a1cddafcace6d20956f54bcc35bd7614bbfd9d635aa428c`. First mismatch: none. This compares Mac behavior, not a new AEX execution.
- Baseline and head Xcode Debug builds with `ARCHS='arm64 x86_64'`, `-jobs 1`, deployment target 11.0 both succeeded. Warning breakdown: pragma-pack 328 -> 328, macro-redefined 8 -> 8, implicit narrowing 24 -> 0, unused-function 4 -> 4, build-system 2 -> 2. Compiler-only warnings: 364 -> 340.
- `python3 -B tests/test_olmdistancegradation_update_params_ui_20260810.py`: 2 tests passed.
- `tests/ui_oracle/compare_mac.py`, restricted to its existing DistanceGradation entry: 3 recorded updates, 6 checks including reload, 0 mismatches.
- The only callers of `RenderSmartPF16PreseededField` and `RenderSmartPF8PreseededField` are `tools/emulation/dg_pf16_smart_preseed_production_harness_20260805.cpp` and `tools/emulation/dg_pf8_smart_preseed_production_harness_20260805.cpp`. Neither release dispatch calls them. Moving them without adding explicit harness includes would break those retained harnesses. Their removal/extraction remains unfinished because both callers are outside this ticket's explicit scope.
- Scratch stayed below 121 MiB at observed checks (5 GiB limit); regenerable Xcode build trees and replay snapshots were deleted. G1 removed its own snapshots and workers after exit. Logs and replay records remain under `orchestra/state/C02-cleanup-olmdistancegradation/`.
- The fixture-specific PF32 admission remains live: `pf32_smart_matrix_admitted` affects Power composition and field dispatch. It was not classified as dead test code or removed.

Non-comment, nonblank lines (strip block comments, then line comments; count nonempty lines):

| File under mac/OLMDistanceGradation | Before | After |
| --- | ---: | ---: |
| Admission.inc | 195 | 190 |
| BilateralFilters.inc | 293 | 293 |
| DistanceField.inc | 313 | 313 |
| DistanceFilters.inc | 341 | 341 |
| OLMDistanceGradation.cpp | 665 | 665 |
| OLMDistanceGradation.h | 95 | 95 |
| OLMDistanceGradation_Strings.cpp | 30 | 30 |
| OLMDistanceGradation_Strings.h | 23 | 23 |
| PixelCompose.inc | 398 | 373 |
| Total | 2353 | 2323 |

inference:
- `require_disjoint` already validates both world layouts, so the preceding duplicate validation calls are redundant. `checked_multiply` retains the prior overflow behavior and the plugin retains its vector-capacity bounds and refusal tags.
- The original unblurred predicate on `p` is subsumed by the same predicate on `finite_admission`: the only changed field is valid Power -> Linear, and the original unblurred predicate rejects Power. Therefore `extended_field` can reuse `nonfinite_field` without enlarging the accepted domain.
- PF16's source reconstruction and staging differ materially from PF8/PF32; keeping its specialization avoids changing arithmetic or ownership semantics. The Smart Layer branch's false ternary arm was unreachable because its enclosing condition requires `p.smart_owner`.
- Explicit casts document existing conversions at assignments; operand and arithmetic types are unchanged. No new constants or expected-value patches were introduced.

changed_files:
- mac/OLMDistanceGradation/Admission.inc
- mac/OLMDistanceGradation/OLMDistanceGradation.cpp
- mac/OLMDistanceGradation/PixelCompose.inc
- orchestra/reports/C02-cleanup-olmdistancegradation.md

verify:
Run in this worktree, choosing a fresh scratch directory. The C01 report supplies the retained G2 replay script; the extraction below uses that committed recipe exactly.

```sh
BASE=62a470a98bb4dce1c9a371209f0d0261a1840580
S="$PWD/orchestra/state/C02-cleanup-olmdistancegradation/recheck"
mkdir -p "$S"
export TMPDIR="$S" TMP="$S" TEMP="$S" OLM_TEST_JOBS=1 PYTHONDONTWRITEBYTECODE=1
python3 tools/refactor/native_diff.py --plugin olmdistancegradation --base "$BASE" --head deb38a6e --cases 3000 --arch both --build both --jobs 1 --scratch "$S/G1" > "$S/G1.log" 2>&1
scripts/setup_ae_sdk_links.sh > "$S/sdk.log" 2>&1
python3 -B tests/test_olmdistancegradation_update_params_ui_20260810.py > "$S/ui-source.log" 2>&1
python3 -B - <<'PY' > "$S/ui-oracle.log" 2>&1
import importlib.util,os,sys
from pathlib import Path
p=Path('tests/ui_oracle/compare_mac.py').resolve()
spec=importlib.util.spec_from_file_location('ui',p)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
m.PLUGINS={'DistanceGradation':m.PLUGINS['DistanceGradation']}
sys.argv=[str(p),'--scratch',str(Path(os.environ['TMPDIR'])/'ui')]
m.main()
PY
mkdir -p "$S/base"
git archive "$BASE" mac core cli tools ucrtmath reports/radialblur_public_getters_aligned_20261001.json | tar -xf - -C "$S/base"
for name in Headers Util Resources; do ln -s "$PWD/$name" "$S/base/$name"; done
python3 -B - <<'PY'
from pathlib import Path
import os
r=Path('orchestra/reports/C01-cleanup-shared-math-and-tests.md').read_text()
(Path(os.environ['TMPDIR'])/'replay_native.py').write_text(r.split("<<'PY_NATIVE'\n")[1].split('\nPY_NATIVE')[0]+'\n')
PY
for side in base head; do
  TREE="$PWD"
  if [ "$side" = base ]; then TREE="$S/base"; fi
  python3 -B "$S/replay_native.py" "$TREE" "$PWD/tests/fuzz_corpus" "$S/G2-$side.jsonl" olmdistancegradation > "$S/G2-$side.log" 2>&1
  OUT="$S/xcode-$side"
  xcodebuild -project "$TREE/mac/OLMDistanceGradation/Mac/OLMDistanceGradation.xcodeproj" -configuration Debug -jobs 1 ARCHS='arm64 x86_64' ONLY_ACTIVE_ARCH=NO MACOSX_DEPLOYMENT_TARGET=11.0 OBJROOT="$OUT/objects" SHARED_PRECOMPS_DIR="$OUT/pch" CONFIGURATION_BUILD_DIR="$OUT/products" build > "$S/xcode-$side.log" 2>&1
  rm -rf "$OUT"
done
cmp "$S/G2-base.jsonl" "$S/G2-head.jsonl"
```

Expected: G1 zero differences/new refusals/execution errors; G2 identical 922 observations; two successful universal builds and 366/342 warnings; 2 UI source tests and 6 recorded UI checks pass.

next:
- Authorize the two include-only harness edits, then move the two preseeded helpers into `mac/OLMDistanceGradation/tests/PreseededField.inc`, included explicitly by those harnesses. This completes C01 step 2 for this plugin and removes its remaining unused-function warnings.
- The orchestrator owns the combined release gate; it was not run here.
