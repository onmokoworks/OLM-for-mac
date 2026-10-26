status: blocked
summary:
- Extracted test exports and reduced-world compatibility code into plugin-local `tests/`; release builds do not compile them.
- Reused shared world safety and typed staging helpers; removed redundant copy checks and subset predicates without changing core arithmetic.
- Scoped non-comment/nonblank lines 3,477 -> 3,439; Universal Debug warnings 376 -> 344.
- G1: 12,012 exact comparisons, zero differences/refusals/execution errors. G2: 612 unchanged Mac observations; both-architecture builds and focused UI checks pass.
- Blocked per the worker brief’s mandatory tool-rejection rule: forced scratch cleanup was rejected; non-forced cleanup succeeded. An inherited Classic-dispatch text assertion also fails on both revisions. No release gate was run.

facts:
- Automatic command review rejected `rm -rf` of the three generated scratch directories (`xcode-base`, `xcode-head`, `base`): “rm -f style commands are not permitted. Use a safer approach”. The command did not execute. Retrying the same scratch cleanup with `rm -r` succeeded (exit 0). No permission escalation was requested. The worker brief explicitly requires a blocked report after any tool rejection, even though cleanup recovered.
- Base: `62a470a98bb4dce1c9a371209f0d0261a1840580`. Code commits: `50c32976`, `d2dc5b72`.
- G1 intermediate commands used `--cases 500 --arch arm64 --build both --jobs 1`: each completed with 1,006 exact comparisons, 0 differences, 0 new refusals, 0 execution errors.
- The initial extraction run was interrupted after noticing a misplaced extracted preprocessor block. It had 502 exact observations and `KeyboardInterrupt()`; it is not gate evidence. The corrected extraction was rerun completely before the first commit.
- G1 final: `--cases 3000 --arch both --build both --jobs 1 --head d2dc5b72` completed with 12,012 exact comparisons (3,003 per architecture/build), 0 differences, 0 new refusals, 0 refusals, 0 execution errors. Summary SHA256: `ea3562543d8f2d104cb85e98b1a9c6c81c22e523492ffd4b0e601e826b29ea96`. First mismatch: none.
- G2 native-only replay used all plugin corpus JSON files and their recorded max-size, size/color samplers, height limits, geometry, timeout, and both public routes. Base/head each produced 612 observations. `cmp` returned 0; both JSONL SHA256 values are `e639380ba42a7cb2a3a1e8e9eafef8b4b5d1e7ee30d5ec21303b9f943cbb53d8`. Output SHA256, status and refusal tags compare equal after removing source-line suffixes. No oracle worker was changed or rebuilt.
- G4: base and head Xcode Debug builds with `ARCHS='arm64 x86_64'`, `ONLY_ACTIVE_ARCH=NO`, `-jobs 1` both reported `BUILD SUCCEEDED`. Focused `tests/ui_oracle/compare_mac.py` DirectionalBlur run: 3 updates, 6 checks including reload, 0 mismatches. `tests/test_olmdirectionalblur_update_params_ui_20260810.py`: 1 test passed. `tests/test_directionalblur_general_feature_budget_20261001.py`: 1 test passed.
- Source-included test seam passed `clang++ -fsyntax-only` with `OLM_DBLUR_TEST_SEAM=1` and `OLM_DBLUR_TEST_FULL_RENDER_REQUEST=1`. `nm -g` on the Universal production bundle found 0 `OLMDirectionalBlurTest*` symbols.
- The DirectionalBlur portion of `tests/test_directional_radial_classic_render_bitdepth_dispatch_20260716.py` raises the same `AssertionError` on both revisions: it expects literal `default:\n\t\treturn PF_Err_BAD_CALLBACK_PARAM;`, while the existing production path returns `OLM_DIRECTIONAL_REFUSAL("classic-format")`. The test and production refusal tag were not changed to satisfy this stale text expectation. Later assertions in that test were not reached.
- G5 Universal warning occurrences: 376 -> 344 (compiler 374 -> 342, unchanged build-system 2). Removed 16 plugin-header C++17-namespace extension diagnostics, 8 redundant logical-expression diagnostics and 8 unused test-helper diagnostics. Remaining 328 SDK pack, 6 UCRT macro, 4 core `.cpp` narrowing, 2 core `.cpp` unused-function, 2 shared-header namespace, and 2 build-system warnings are outside this scoped cleanup; no warning flags were disabled.

inference:
- FACT: the original `PayloadSpan` checked active-row stride, last-active-byte span and pointer overflow. The shared `olm::world_safety::address_range` performs those checks; signed-world validation remains in the adapter. Its additional tight-size multiplication cannot overflow for a layout whose larger addressable span passed the old checks.
- FACT: after the general four-zero-control copy return, the default-copy branch cannot reach a supported depth. The unsupported-depth `noop-depth` refusal remains; redundant stride checks already performed by `PayloadSpan` were removed.
- FACT: both removed `fade_sharp_cross_exact` predicates were `P && Q`, used only beside `P` in an OR expression. Removing them preserves the admission truth value and removes the parenthesis warnings.
- INFERENCE supported by G1/G2: shared staging and namespace spelling preserve the tested native behavior. PF16/PF32 core calls remain separate because their gain/angle argument order and signatures differ. No floating-point arithmetic type or operation order was changed.
- Test harnesses retain their explicit `OLM_DBLUR_TEST_SEAM` opt-in; guarded includes load the moved test files. This preserves existing source-included harnesses without editing callers outside the authorized scope.
- Finite native comparisons establish refactor equivalence for the recorded cases; they do not establish new Windows/AE conformance cells. Existing source-bound admission contracts remain intact.

changed_files:
Non-comment/nonblank counts strip block comments, line comments and blank lines. The table includes every changed source file; unchanged plugin files and plugin-only `core/dblur*.h` headers are included in the scoped total.

| File | Before | After |
|---|---:|---:|
| `core/dblur_float.h` | 27 | 27 |
| `core/dblur_gaussian.h` | 23 | 23 |
| `core/dblur_generic_budget.h` | 289 | 289 |
| `core/dblur_noise.h` | 173 | 173 |
| `mac/OLMDirectionalBlur/OLMDirectionalBlur.cpp` | 317 | 324 |
| `mac/OLMDirectionalBlur/OLMDirectionalBlur_admission.inc` | 809 | 794 |
| `mac/OLMDirectionalBlur/OLMDirectionalBlur_dispatch.inc` | 695 | 527 |
| `mac/OLMDirectionalBlur/OLMDirectionalBlur_host.inc` | 547 | 477 |
| `mac/OLMDirectionalBlur/tests/HostCompatibility.inc` | 0 | 16 |
| `mac/OLMDirectionalBlur/tests/TestEntry.inc` | 0 | 192 |
| All plugin files, including moved tests | 2,729 | 2,691 |
| All plugin-only core headers | 748 | 748 |
| Scoped total | 3,477 | 3,439 |

Production plugin lines alone: 2,729 -> 2,483. Largest source is the admission include, 865 physical lines. No new numeric constants or abstraction classes were introduced; existing templates are reused. Also changed: `orchestra/reports/C02-cleanup-olmdirectionalblur.md` (this report).

verify:
Run from this worktree with a fresh scratch path. The following uses the reviewed code commit, so the report commit itself does not change the tested source.

```sh
ROOT="$PWD"
BASE=62a470a98bb4dce1c9a371209f0d0261a1840580
S="$ROOT/orchestra/state/C02-cleanup-olmdirectionalblur/recheck"
mkdir -p "$S"
export TMPDIR="$S" TMP="$S" TEMP="$S" OLM_TEST_JOBS=1 PYTHONDONTWRITEBYTECODE=1
python3 tools/refactor/native_diff.py --plugin olmdirectionalblur --base "$BASE" \
  --head d2dc5b72 --cases 3000 --arch both --build both --jobs 1 \
  --scratch "$S/G1" > "$S/G1.log" 2>&1
bash scripts/setup_ae_sdk_links.sh > "$S/sdk-links.log" 2>&1
mkdir -p "$S/base"
git archive "$BASE" mac core cli tools ucrtmath reports/radialblur_public_getters_aligned_20261001.json | tar -xf - -C "$S/base"
for name in Headers Util Resources; do ln -s "$ROOT/$name" "$S/base/$name"; done
python3 - "$S" <<'PY_REPLAY_SETUP'
import sys
from pathlib import Path
text=Path('orchestra/reports/C01-cleanup-shared-math-and-tests.md').read_text()
Path(sys.argv[1], 'replay_native.py').write_text(text.split("<<'PY_NATIVE'\n",1)[1].split('\nPY_NATIVE',1)[0])
PY_REPLAY_SETUP
for side in base head; do
  TREE="$ROOT"
  if [ "$side" = base ]; then TREE="$S/base"; fi
  python3 -B "$S/replay_native.py" "$TREE" "$ROOT/tests/fuzz_corpus" \
    "$S/G2-$side.jsonl" olmdirectionalblur > "$S/G2-$side.log" 2>&1
  OUT="$S/xcode-$side"
  xcodebuild -project "$TREE/mac/OLMDirectionalBlur/Mac/OLMDirectionalBlur.xcodeproj" \
    -configuration Debug -jobs 1 ARCHS='arm64 x86_64' ONLY_ACTIVE_ARCH=NO \
    MACOSX_DEPLOYMENT_TARGET=11.0 OBJROOT="$OUT/objects" \
    SHARED_PRECOMPS_DIR="$OUT/pch" CONFIGURATION_BUILD_DIR="$OUT/products" \
    build > "$S/xcode-$side.log" 2>&1
  rm -r "$OUT"
done
cmp "$S/G2-base.jsonl" "$S/G2-head.jsonl"
python3 -B - "$S" > "$S/ui.log" 2>&1 <<'PY_UI'
import importlib.util,sys
from pathlib import Path
p=Path('tests/ui_oracle/compare_mac.py')
spec=importlib.util.spec_from_file_location('ui',p)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
m.PLUGINS={'DirectionalBlur':m.PLUGINS['DirectionalBlur']}
sys.argv=[str(p),'--scratch',str(Path(sys.argv[1])/'ui')];m.main()
PY_UI
"/Users/onmk/Documents/Projects/Personal/OLM as/tools/emulation/.venv/bin/python" -B \
  tests/test_olmdirectionalblur_update_params_ui_20260810.py > "$S/ui-source.log" 2>&1
python3 -B tests/test_directionalblur_general_feature_budget_20261001.py > "$S/budget.log" 2>&1
clang++ -std=c++17 -fsyntax-only -DOLM_DBLUR_TEST_SEAM=1 \
  -DOLM_DBLUR_TEST_FULL_RENDER_REQUEST=1 -I Headers -I Headers/SP -I Util -I Resources \
  mac/OLMDirectionalBlur/OLMDirectionalBlur.cpp > "$S/test-seam-syntax.log" 2>&1
```

Expected: G1 12,012 comparisons, zero differences/new refusals/execution errors; G2 `cmp` exit 0 with 612 observations and the hash above; two successful Universal builds with 376/344 warnings; UI 6 checks, no mismatch; both unit tests and syntax check exit 0.

To reproduce the inherited scoped text-test failure without testing or modifying RadialBlur:

```sh
python3 -B - "$S" <<'PY_CLASSIC'
import importlib.util,sys
from pathlib import Path
p=Path('tests/test_directional_radial_classic_render_bitdepth_dispatch_20260716.py')
spec=importlib.util.spec_from_file_location('classic',p)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
for side,root in [('base',Path(sys.argv[1])/'base'),('head',Path.cwd())]:
    m.OWNED_SOURCES=(root/'mac/OLMDirectionalBlur/OLMDirectionalBlur.cpp',)
    try:
        m.ClassicRenderBitdepthDispatchTests().test_classic_render_dispatch()
        print(side,'PASS')
    except Exception as error:
        print(side,type(error).__name__,str(error))
PY_CLASSIC
```

Expected: the same `AssertionError` on both revisions. This is not counted as a passing G4 text-test gate.

next:
- The tool-rejection status is retained as required by the worker brief; the rejected cleanup was recovered safely. Cleanup implementation and numeric verification are complete. Assign the inherited Classic-dispatch text-test contract to a separate maintenance ticket before declaring every REFACTOR_SPEC gate green.
- Regenerable Xcode/base trees were removed with non-forced cleanup; the G1 driver removed its own build trees. Logs and replay evidence remain in ticket scratch.
- The orchestrator owns the combined release-gate run. No release gate, MAIN modification, push, or reference-worker rebuild was performed here.
