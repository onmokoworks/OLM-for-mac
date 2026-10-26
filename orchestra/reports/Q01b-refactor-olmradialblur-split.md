status: blocked
summary:
- Split the remaining main file into same-translation-unit includes: main 5,923 -> 955 lines; no source file exceeds 955 lines.
- Named 28 constants with provenance, retained exact trig bits and arithmetic order, and removed four uncalled helpers plus unused epsilon/flag plumbing.
- Non-comment/nonblank plugin source decreased 6,380 -> 6,342; structural G1 passed 4,012/4,012.
- G2 native corpus equality and both Universal Xcode builds pass; warnings decreased 386 -> 374.
- Final G1 passed 12,012/12,012. G4 remains blocked by three existing regression failures and unfinished historical kernel-text reader compatibility.

facts:

Baseline: `5b66d1a74a92e0d0967b47be0ef92cb950503682`. Branch:
`orch/Q01b-refactor-olmradialblur-split`. Structural commit: `b7a38470`.
Constant/dead-code commit: `2a6e4b3e`. No push, MAIN edits, new translation units,
release-gate changes, generated-file edits, or reference-worker rebuilds.

Structure and size (physical / non-comment, nonblank; C/C++ comments stripped):

| File under mac/OLMRadialBlur | Before | After |
| --- | ---: | ---: |
| OLMRadialBlur.cpp | 5923 / 5508 | 955 / 847 |
| OLMRadialBlur.h | 149 / 137 | 149 / 137 |
| OLMRadialBlurPiPL.r | 33 / 31 | 33 / 31 |
| OLMRadialBlur_Strings.cpp | 47 / 44 | 47 / 44 |
| OLMRadialBlur_Strings.h | 38 / 37 | 38 / 37 |
| RadialAdmission.inc | 0 / 0 | 361 / 318 |
| RadialDiagnostics.inc | 230 / 223 | 230 / 223 |
| RadialLayerAdmission.inc | 0 / 0 | 94 / 86 |
| RadialLayerCompose.inc | 0 / 0 | 150 / 127 |
| RadialMath.inc | 350 / 302 | 368 / 320 |
| RadialPixelTraits.inc | 0 / 0 | 289 / 254 |
| RadialRotation.inc | 0 / 0 | 786 / 738 |
| RadialRotationAdmission.inc | 0 / 0 | 820 / 818 |
| RadialRotationRows.h | 32 / 26 | 32 / 26 |
| RadialSampling.inc | 0 / 0 | 376 / 332 |
| RadialScatterSIMD.h | 84 / 72 | 84 / 72 |
| RadialTestEntry.inc | 0 / 0 | 305 / 291 |
| RadialTestWorkers.inc | 0 / 0 | 287 / 272 |
| RadialWorldStorage.inc | 0 / 0 | 117 / 107 |
| RadialZoom.inc | 0 / 0 | 571 / 522 |
| RadialZoomAdmission.inc | 0 / 0 | 489 / 483 |
| RadialZoomKernels.inc | 0 / 0 | 277 / 257 |
| **Total** | **6886 / 6380** | **6858 / 6342** |

`RadialZoomAdmission.inc` and `RadialRotationAdmission.inc` are included inside
existing function scopes. They preserve the original declarations, control flow,
and order without introducing helper calls or changing floating-point widths.
ParamsSetup, UpdateParamsUI, Classic/Smart lifecycle, and public dispatch remain
in the main cpp for current text readers. Kernel, sampling, traits, storage,
layer admission/composition, and test-only responsibilities have separate includes.
The reference/fast split and parallel-limit behavior were not edited.

Constants and dead code:

- Trig bits were checked with MAIN's `tools/emulation/.venv/bin/python`, `pefile`
  and `capstone` against the original `aex/OLMRadialBlur/Plugins/64/2025/OLMRadialBlur.aex`.
  The AEX identity used by the replay adapters is
  `ffbb1d0109671e3ea9b1a12cd1126f2c72f965197577a57cc602fb096414ccdb`.
- Named trig words: `kTrigInvPiBits` (RVA 31880), `kTrigRoundShiftBits` (318c0),
  `kTrigPi0Bits..kTrigPi3Bits` (315c0/31600/31640/31680),
  `kTrigSinC3Bits..kTrigSinC9Bits` (31780/317c0/31800/31840), and
  `kTrigTinyBits`, `kTrigHalfBits`, `kTrigOneBits`, `kTrigHalfPiBits`
  (256a0/25690/25680/256b0). `RadialF32FromBits` remains in use.
- Also named Gaussian variance/bias, exp range-reduction and table-index constants,
  FLOAT32 masks, CVTTSS2SI boundary, worker span cap and size activation threshold.
  Reused the existing exact degree-conversion coefficient in rendering.
  Comments identify AEX functions/data or instruction semantics; the sine polynomial
  explicitly forbids reassociation. Existing per-depth/NaN/rounding comments remain.
- `rg` over plugin, tests and tools found no callers of `UnionLRect`, `CopyWorld`,
  `MatchesType3SmallSourceFixture`, or `MatchesType3SmallLayerFixture`.
  Removed these definitions. Removed the unused `alpha_quantize_epsilon` and
  ignored `apply_case0010_aex_ulp` parameter, including its two argument sites.
  Active hash-bound admission, FFT/convolver fallbacks and test seams remain.
- The first split expands byte-for-byte to the baseline cpp. Final expanded source
  also matches after reversing the 28 constant substitutions, existing coefficient
  reuse and the documented deletions, ignoring comments/whitespace. The initial
  reconstruction checker omitted an additional coefficient reuse in Rotation's
  inverse angle scale; correcting that checker made it pass, without a source edit.
  `git diff --check` passes.

Gates:

- G1 after structural commit: `native_diff.py --plugin radialblur --base 5b66d1a74a92e0d0967b47be0ef92cb950503682 --cases 1000 --arch both --build both --jobs 1`.
  Exit 0: 4,012 comparisons, 4,012 exact, 0 differences, 0 refusals,
  0 new refusals, 0 execution errors. First differing byte: none.
- G1 final: `native_diff.py --plugin radialblur --base 5b66d1a74a92e0d0967b47be0ef92cb950503682 --head 2a6e4b3e --cases 3000 --arch both --build both --jobs 1`.
  Exit 0: 12,012 comparisons, 12,012 exact, 0 differences, 0 refusals,
  0 new refusals, 0 execution errors. First differing byte: none. All eight
  harness builds reported the requested architecture. Coverage: 4,004 comparisons
  per depth, 4,020 default / 3,996 realistic-v1 / 3,996 realistic-v2 geometry,
  and 12 full 4K comparisons. As in Q01, RadialBlur does not read Q00's
  `color_sampler` attribute; the adapter itself supplies independent FLOAT32
  HDR/signed/nonfinite profiles. No separate float-v1 coverage claim.
- G2: all 243 corpus files replayed on base/head (61 default, 180 realistic-v1,
  2 realistic-v2), with recorded hash-bound workers/timeouts. Four C49 files were
  separately replayed with `OLM_RADIAL_CANDIDATE_SANITIZE=1` on both sides.
  Every replay completed. Across 486 routes, native hashes, errors, rectangles,
  metadata and sanitizer fields have 0 differences.
  Full oracle-bearing results differ for `C45_seed45102_case000052`,
  `C46_seed1_case000280`, and `C49_seed1_case000117`. The first two change
  oracle-dependent Smart labels (uncompared -> exact and exact -> uncompared);
  native output is unchanged. The third differs in oracle diagnostics.
  These are excluded by revised G2, not claimed as full-result equality.
- G2 refusal attribution: the shared replay runner discards the optional attribution
  returned by `Adapter.candidate`. An additional native-only replay using the same
  adapter, `load_corpus`, `require_host`, recorded sanitizer flags and per-case timeouts
  compares all native fields plus tags (only `@line` suffixes normalized, as in G1).
  486/486 identical: Smart 243 successes; Classic 146 successes and 97 refusals.
  All 97 refusal observations carry identical tags. No native execution errors.
- G4 Xcode: base/head Debug builds with `ARCHS='arm64 x86_64'`, `-jobs 1`,
  deployment target 11.0 both succeeded. No bundles were installed.
- G4 UI oracle: RadialBlur 54 updates / 108 checks including reload, 0 mismatches.
  Both Smart rectangle/lifecycle tests, the generic memory/work budget test,
  and the Type-3 sanitizer test pass on the refactored source.
- G4 known-red tests, reproduced on both base and head:
  `test_olmradialblur_parameter_ui_parity_20260806.py` has 2 passing tests and one
  failure: it expects Thickness UI flags `0`, whereas production has `0x40`.
  `test_directional_radial_classic_render_bitdepth_dispatch_20260716.py` expects
  `AEFX_SuiteScoper<PF_WorldSuite2>`; production uses explicit acquire/release.
  `test_olmradialblur_generic_baseline_20260820.py` builds but its probe exits 38.
  No production behavior or assertion was changed to satisfy stale expectations.
  Python environments lacked pytest; test functions were invoked with `runpy`
  and unittest methods directly, preserving their assertions.
- G4 limitation: historical `tools/emulation/test_olmradialblur_*source_guard*`
  and other kernel-text probes were not all rerun or made include-aware. Some read
  moved text with `SOURCE.read_text()`; updating their hash-bound historical test
  machinery is unfinished. This is not a claim of full text-test compatibility.
- G5: warning lines 386 -> 374; no new warning kind or increased warning count.
  Removed eight C++17-extension warnings from the dead fixture templates, two
  unused epsilon warnings and two unused UnionLRect warnings. Two unchanged
  build-system warnings are included in each total; compiler warnings are 384 -> 372.
- Regenerable Xcode trees, native-replay temporary builds, UI executable/source,
  baseline snapshot and native_diff run trees were removed; logs/results remain.
  Scratch remained below 5 GiB. No background process or durable oracle artifact
  was left by this ticket.
- G3, ref_vs_fast, packaging and release gates were not run, as specified by the
  revised ticket gates. No new oracle campaign or Windows/native-AE claim.

inference:

The decisive native comparisons and corpus equality support preservation within
measured coverage; they do not establish new AEX conformance. Oracle-only variation
is consistent with the previously observed diagnostic/time-budget instability.
The three current regression failures predate this ticket. Nevertheless the literal
G4 requirement is not met, and historical kernel-text readers remain unfinished;
this ticket is reported blocked rather than fully done.

changed_files:
- mac/OLMRadialBlur/OLMRadialBlur.cpp
- mac/OLMRadialBlur/RadialAdmission.inc
- mac/OLMRadialBlur/RadialLayerAdmission.inc
- mac/OLMRadialBlur/RadialLayerCompose.inc
- mac/OLMRadialBlur/RadialMath.inc
- mac/OLMRadialBlur/RadialPixelTraits.inc
- mac/OLMRadialBlur/RadialRotation.inc
- mac/OLMRadialBlur/RadialRotationAdmission.inc
- mac/OLMRadialBlur/RadialSampling.inc
- mac/OLMRadialBlur/RadialTestEntry.inc
- mac/OLMRadialBlur/RadialTestWorkers.inc
- mac/OLMRadialBlur/RadialWorldStorage.inc
- mac/OLMRadialBlur/RadialZoom.inc
- mac/OLMRadialBlur/RadialZoomAdmission.inc
- mac/OLMRadialBlur/RadialZoomKernels.inc
- orchestra/reports/Q01b-refactor-olmradialblur-split.md

verify:

Run from this worktree; choose a fresh scratch suffix because native_diff refuses
an existing run directory. Expected G1: 4,012 and 12,012 exact comparisons,
respectively, with no differences/refusals/execution errors.

```sh
ROOT="$PWD"
MAIN='/Users/onmk/Documents/Projects/Personal/OLM as'
BASE=5b66d1a74a92e0d0967b47be0ef92cb950503682
S="$ROOT/orchestra/state/Q01b-refactor-olmradialblur-split/verify"
mkdir -p "$S"
export TMPDIR="$S" OLM_TEST_JOBS=1 PYTHONDONTWRITEBYTECODE=1
scripts/setup_ae_sdk_links.sh > "$S/sdk.log" 2>&1
python3 tools/refactor/native_diff.py --plugin radialblur --base "$BASE" \
  --head b7a38470 --cases 1000 --seed 909 --arch both --build both --jobs 1 \
  --scratch "$S/g1-split" > "$S/g1-split.log" 2>&1
python3 tools/refactor/native_diff.py --plugin radialblur --base "$BASE" \
  --head 2a6e4b3e --cases 3000 --seed 909 --arch both --build both --jobs 1 \
  --scratch "$S/g1-final" > "$S/g1-final.log" 2>&1
```

G2/G4/G5 (both Xcode builds should succeed; corpus commands can exit 1 for
oracle-only differences from saved results). Keep reports inside each snapshot's
root, as required by run.py. Compare Mac route fields, not whole oracle dictionaries.

```sh
mkdir -p "$S/base"
git archive "$BASE" mac core cli tools ucrtmath \
  reports/radialblur_public_getters_aligned_20261001.json | tar -xf - -C "$S/base"
for name in Headers Util Resources; do ln -s "$MAIN/$name" "$S/base/$name"; done
for side in base head; do
  T="$ROOT"; [ "$side" != base ] || T="$S/base"
  V="$T/orchestra/state/Q01b-refactor-olmradialblur-split/verify"
  mkdir -p "$V"
  for corpus in radialblur radialblur_realistic_P02d radialblur_N02-nightly-20261025; do
    python3 "$T/tools/fuzz/run.py" --plugin radialblur --jobs 1 --main "$MAIN" \
      --replay "$ROOT/tests/fuzz_corpus/$corpus" --scratch "$V/$corpus" \
      --report "$V/$corpus.json" > "$V/$corpus.log" 2>&1
  done
  for case in C49_seed1_case000117 C49_seed105_case000150 C49_seed1_case000148 C49_seed105_case000071; do
    OLM_RADIAL_CANDIDATE_SANITIZE=1 python3 "$T/tools/fuzz/run.py" \
      --plugin radialblur --jobs 1 --main "$MAIN" \
      --replay "$ROOT/tests/fuzz_corpus/radialblur/$case.json" \
      --scratch "$V/$case-sanitized" --report "$V/$case-sanitized.json" \
      > "$V/$case-sanitized.log" 2>&1
  done
  xcodebuild -project "$T/mac/OLMRadialBlur/Mac/OLMRadialBlur.xcodeproj" \
    -configuration Debug -jobs 1 ARCHS='arm64 x86_64' ONLY_ACTIVE_ARCH=NO \
    MACOSX_DEPLOYMENT_TARGET=11.0 OBJROOT="$V/xcode/objects" \
    SHARED_PRECOMPS_DIR="$V/xcode/pch" CONFIGURATION_BUILD_DIR="$V/xcode/products" \
    build > "$V/xcode.log" 2>&1
 done
```

The additional refusal-tag comparison uses the shared adapter directly, avoiding
oracle diagnostics. This is the exact native replay recipe; it creates no new
committed tool. Run the following block once with `T="$S/base"; SIDE=base` and
once with `T="$ROOT"; SIDE=head`; compare the two resulting JSON arrays. Expected:
486 observations each, exactly equal, including 97 nonempty tag lists.

```sh
python3 - "$T" "$ROOT/tests/fuzz_corpus" "$S/native-$SIDE.json" \
  > "$S/native-$SIDE.log" 2>&1 <<'PY_NATIVE'
import json,os,re,sys,tempfile,time
from pathlib import Path
from types import SimpleNamespace
root,corpus_root,output=map(Path,sys.argv[1:])
sys.path.insert(0,str(root/'tools/fuzz'))
from adapters.radialblur import Adapter
from core import load_corpus,sha
from geometry import require_host
paths=sorted(corpus_root.glob('radialblur*/*.json'));rows=[]
for sanitized in [False,True]:
 os.environ['OLM_RADIAL_CANDIDATE_SANITIZE']=str(int(sanitized))
 with tempfile.TemporaryDirectory(dir=output.parent,prefix='native-corpus-') as tmp:
  directory=Path(tmp)
  adapter=Adapter(SimpleNamespace(main=Path('/Users/onmk/Documents/Projects/Personal/OLM as'),worker=Path('/unused'),max_size=256,case_timeout=180))
  adapter.build(directory,time.monotonic()+300)
  for path in paths:
   saved=json.loads(path.read_text());provenance=saved.get('provenance',{})
   if bool(provenance.get('candidate_sanitize',False))!=sanitized:continue
   assert not provenance.get('candidate_bypass') and not provenance.get('reference_build')
   adapter.max_size=saved['max_size'];adapter.timeout=provenance.get('case_timeout_seconds',10)
   case,_=load_corpus(path,adapter);require_host(adapter,case)
   for route in adapter.routes:
    with tempfile.TemporaryDirectory(dir=directory) as run:
     result,raw,tags=adapter.candidate(case,Path(run),route,time.monotonic()+adapter.timeout+5)
    rows.append(dict(case=str(path.relative_to(corpus_root)),route=route,result=result,sha256=sha(raw),tags=[re.sub(r'@\d+$','',t) for t in tags]))
output.write_text(json.dumps(rows,indent=2)+'\n')
print('native observations',len(rows))
PY_NATIVE
```

For the current RadialBlur-only UI oracle (108 checks / zero mismatches):

```sh
python3 - "$S/ui" > "$S/ui.log" 2>&1 <<'PY_UI'
import runpy, sys
ns = runpy.run_path('tests/ui_oracle/compare_mac.py')
ns['main'].__globals__['PLUGINS'] = {'RadialBlur': ns['PLUGINS']['RadialBlur']}
sys.argv = ['compare_mac.py', '--scratch', sys.argv[1]]
ns['main']()
PY_UI
```

Native regression assertions can be invoked without pytest as follows. This
records each assertion failure and continues; expected final-source failures
are the Thickness flag and generic-baseline exit 38 described above. The Classic
source test is checked separately with unittest, restricted to RadialBlur.

```sh
python3 - > "$S/regressions.log" 2>&1 <<'PY_TESTS'
import runpy
for script in ['test_olmradialblur_parameter_ui_parity_20260806.py',
               'test_olmradialblur_global_polar_smart_contract_20260820.py',
               'test_olmradialblur_generic_budget_20260821.py',
               'test_olmradialblur_generic_baseline_20260820.py',
               'test_olmradialblur_generic_type3_sanitizers_20260820.py']:
    ns = runpy.run_path('tests/' + script)
    for name, fn in ns.items():
        if name.startswith('test_'):
            try:
                fn(); print('PASS', name)
            except Exception as exc:
                print('FAIL', name, repr(exc))
ns = runpy.run_path('tests/test_directional_radial_classic_render_bitdepth_dispatch_20260716.py')
method = ns['ClassicRenderBitdepthDispatchTests']().test_classic_render_dispatch
method.__globals__['OWNED_SOURCES'] = (ns['ROOT']/'mac/OLMRadialBlur/OLMRadialBlur.cpp',)
try:
    method(); print('PASS Classic dispatch text test')
except AssertionError as exc:
    print('FAIL Classic dispatch text test', repr(exc))
PY_TESTS
```

To repeat the baseline checks, use the same functions with their `ROOT`, `SOURCE`,
`_UCRT_CXX` and `OWNED_SOURCES` globals pointing into `$S/base`; for the UI module,
`SOURCE` is the cpp text, not a Path. The untouched UI strings are identical.
Remove scratch Xcode build trees after checking; retain logs and JSON reports.


next:
- Suggested follow-up: Q01c RadialBlur test-reader and regression-contract maintenance.
- Reconcile the three existing regression expectations with the current production contract; do not change rendering to satisfy them.
- Make historical RadialBlur kernel-text probes include-aware without weakening assertions or rewriting historical evidence hashes.
- Orchestrator reviews this diff and runs its independent seed after merge; no release-ready claim from this ticket.
