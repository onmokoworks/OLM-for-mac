status: partial
summary:
- Centralized retained embedded AEX math in `core/olm_exact_math.h`; existing UCRT implementations remain in `ucrtmath` behind that shared include.
- Switched all existing UCRT consumers; preserved the distinct Radial/KiraKira trig variants and explicit probe helper names.
- Changed source non-comment/nonblank lines: 6,127 -> 6,113 (-14); plugin-local lines fall by 109.
- All 20 Universal Debug builds passed; warnings 3,608 -> 3,598. G2: all ten plugins, 5,770 observations unchanged.
- Full G1 passes all ten plugins (120,120 comparisons, zero differences); release-v2 passes 7/7. Status is partial solely because the inherited G4 UI text assertion still fails on both revisions.

facts:
- Base: `61e55835ed4ec3bbb0c345d3a699be12f914657c`. Shared-piece commit: `5e39d8a5`.
- Final G1: seed 909; 3,000 small + 3 UHD cases per architecture/build/plugin; both arm64 and x86_64, both reference and fast; **120,120 comparisons**, 113,920 exact renders and 6,200 matched refusals. **0 differences, 0 new refusals, 0 execution errors; first mismatch: none.** Final source was frozen at `5e39d8a5`; the first three plugins used that identical WORKTREE content, subsequent runs used the commit explicitly.
- SHA256 of the ten final summary files concatenated in the per-plugin G1 table order: `041262dcd4ecbeb5f21582206461212bf42b9d29c6bc9c6ecb2745e241a3a30e`. This records this run's reports, whose paths/build hashes can differ on a rerun.
- Scheduling only: the outer serial queue was retired after Blur's native_diff completed; remaining plugins continued in one serial queue, with a second serial queue starting only after release-v2 freed the second process slot. No final native_diff run was cancelled or duplicated.
- Intermediate G1, RadialBlur, seed 909, 500 small + 3 UHD cases, arm64/reference+fast: 1,006 exact, 0 differences, 0 new refusals, 0 execution errors. This preceded retention of the probe helper aliases.
- An exploratory full run was interrupted while finalizing those aliases: 1,631 exact comparisons, no differences/refusals/errors; excluded from final gate totals.
- G2 used recorded max size, size/color samplers, height limit, geometry and timeout, with the four recorded Radial sanitizer witnesses built separately. Both native routes were replayed where supported. No oracle was run or changed. Complete result dictionaries, raw SHA256 and refusal tags (excluding source line suffixes) compare equal.
- Release-v2 at code commit `5e39d8a5`: **7/7 PASS**, `local_gate_pass=true`, `release_authorized=false`. Framework: 50 tests / 3 skipped; 10 Universal bundles; 2,998/2,998 corpus PASS (0 FAIL, 0 ORACLE-STOP); fresh seeds E=5,693, M=0, R=250, U=57, errors=0; F47d E=941, M=0, R=46, U=13, errors=0; F51 3,870 equal renders + 128 equal refusals; 45/45 selected test files PASS; static PASS. U counts are retained oracle limitations, not exact-output claims.
- Two initial Radial corpus guest stops (`C46_seed1_case000280`, `C49_seed1_case000117`) passed the gate's built-in retries. No gate/expected-value change was made.
- Release summary SHA256: `a9b661df6f1fa76cacbe16c3ca9d45662f7a0b53e0ddd18379d3d42d94f9fe16`.
- All ten baseline and head Xcode Debug builds succeeded with `ARCHS='arm64 x86_64'`, `-jobs 1`. Warning totals include two unchanged build-system warnings per plugin; compiler totals are 3,588 -> 3,578.
- The initial head Xcode attempt lacked SDK links and failed with `AEConfig.h` missing. Adding SDK references resolved it. The first release-v2 build then rejected the nonstandard link spelling; standard `scripts/setup_ae_sdk_links.sh` links resolved that setup issue. The interrupted gate is not a pass.
- Shared UI oracle: 240 checks, 0 mismatches. KiraKira UI oracle: 159 dispatches, 0 mismatches (the existing comparator deliberately reports raw dispatch differences separately).
- The two parameter-UI text modules each replayed on base/head: 6 assertions, 5 pass and the same pre-existing assertion `test_windows_control_types_and_ui_ranges_are_preserved` at `tests/test_olmradialblur_parameter_ui_parity_20260806.py:21` fails: it expects the Thickness flag `0`, while both source revisions use `0x40` at the unchanged parameter declaration. No test was weakened. `unittest discover` initially found no tests (exit 5); actual module-level test functions were then invoked directly.

- Cleanup: all verification queues exited; generated build trees, remaining 22 compiled artifacts and the SDK links created for this worktree were removed. Logs/reports remain. Final `du -sh orchestra/state/C01-cleanup-shared-math-and-tests` returned `502M`; owned-orphan-process audit returned an empty list.

Per-plugin non-comment/nonblank source lines (`.cpp`, `.h`, `.inc`, including unchanged generated sources) and Universal Debug warning occurrences:

| Plugin | Lines before | Lines after | Warnings before | Warnings after |
|---|---:|---:|---:|---:|
| ColorKeep | 719 | 719 | 332 | 332 |
| OLMBlur | 1456 | 1456 | 352 | 352 |
| OLMColorKey | 2884 | 2884 | 342 | 340 |
| OLMDirectionalBlur | 2729 | 2729 | 382 | 376 |
| OLMDistanceGradation | 2353 | 2353 | 366 | 366 |
| OLMKiraKira | 3640 | 3639 | 354 | 354 |
| OLMRadialBlur | 6315 | 6207 | 374 | 372 |
| OLMSmoother | 18725 | 18725 | 410 | 410 |
| OLMSmoother2 | 11947 | 11947 | 346 | 346 |
| OLMToonDilate | 886 | 886 | 350 | 350 |

Final G1 counts (all difference/new-refusal/execution-error columns are zero):

| Plugin | Comparisons | Exact renders | Matched refusals |
|---|---:|---:|---:|
| radialblur | 12012 | 12012 | 0 |
| olmkirakira | 12012 | 11712 | 300 |
| olmblur | 12012 | 12012 | 0 |
| olmcolorkey | 12012 | 12012 | 0 |
| olmdistancegradation | 12012 | 11912 | 100 |
| olmdirectionalblur | 12012 | 12012 | 0 |
| olmsmoother2 | 12012 | 10216 | 1796 |
| colorkeep | 12012 | 12012 | 0 |
| olmtoondilate | 12012 | 12012 | 0 |
| olmsmoother | 12012 | 8008 | 4004 |

G2 per-plugin observations and identical base/head JSONL SHA256:

| Plugin | Observations | SHA256 |
|---|---:|---|
| radialblur | 506 | `1b4e8a0aca561c9985399656af9de6faa59f06914c5f4dbb202dc76672a4494f` |
| olmkirakira | 780 | `3c325fc956a8fefafa5a32d5df51a6f90e9ad3750373a540a5795dfe9c21ed4d` |
| olmblur | 278 | `2d09cf9d211fb697a56125cfedf3f670f4751d039b04b0b2cc206347faa7c5ac` |
| olmcolorkey | 102 | `d388f3bcf3d980d830d22b8e22a486972acfe9221398d4af06ceea139f05be41` |
| olmdistancegradation | 922 | `f34dfda386d95f840a1cddafcace6d20956f54bcc35bd7614bbfd9d635aa428c` |
| olmdirectionalblur | 612 | `e639380ba42a7cb2a3a1e8e9eafef8b4b5d1e7ee30d5ec21303b9f943cbb53d8` |
| olmsmoother2 | 224 | `ffd106d234488d1331529c2f692f280d1c52ed1705ed5572df1db4e0c9353f20` |
| colorkeep | 842 | `05b85b184df2a94c362f3920e676731ec37f44a98a9c5a7a20c734c003dd0e6c` |
| olmtoondilate | 1124 | `005579222d14788108216ce86f451373838fe8aef7f656b6ea6c94f0fbebf3b8` |
| olmsmoother | 380 | `b32df87a2076100f81456c7e29955390e12242ae835a8c4241a10ba0e04caa9f` |

inference:
- Moving inline definitions and retaining the existing operation widths/order should preserve behavior; the gates establish equality only for their measured cases, not general AE exactness.
- UCRT sin/cos/exp/pow/atan2 implementations were already shared. Duplicating or moving their C implementation into a header would not remove plugin copies. The new core header imports that existing API and owns the remaining embedded variants.
- Radial uses explicit SSE NaN selection at each hot-path operation. KiraKira additionally performs large-angle table reduction and has distinct NaN handling; the header documents why these implementations remain separate.
- ColorKeep, ToonDilate and Smoother have no UCRT/embedded-trig consumers to switch. Their product sources are unchanged but they remain in the all-ten validation.
- Fourteen redundant bit-word locals were removed while retaining named float constants, exact hex bits and AEX RVA comments (for example `inv_pi`, `shift`, `pi0..pi3`, `c3..c9`). Radial's bit extraction now reuses `x86_float::bits`. The old KiraKira header remains a compatibility include for retained leaf harnesses.
- Nested namespace spelling in `x86_float.h` was made C++11-compatible; no arithmetic type, expression, build flag or rejection tag changed. Steps 2-5 are untouched.

changed_files:
The following table is also the complete changed-source list. Counts remove block/line comments and blank lines. New shared header: 298 physical lines, below the size limit.

| File | Before | After |
|---|---:|---:|
| `core/dblur_gaussian.h` | 23 | 23 |
| `core/dblur_noise.h` | 173 | 173 |
| `core/dblur_rotate.cpp` | 180 | 180 |
| `core/dblur_rowdriver.cpp` | 476 | 476 |
| `core/kirakira_sincos.h` | 160 | 2 |
| `core/kirakira_warp.h` | 124 | 124 |
| `core/olmblur_worker16_legacy.cpp` | 116 | 116 |
| `core/olmblur_worker16_nonlegacy.cpp` | 136 | 136 |
| `core/olmblur_worker32_legacy.cpp` | 102 | 102 |
| `core/olmblur_worker32_nonlegacy.cpp` | 94 | 94 |
| `core/olmblur_worker8_legacy.cpp` | 117 | 117 |
| `core/olmblur_worker_orchestration.cpp` | 102 | 102 |
| `core/x86_float.h` | 38 | 38 |
| `mac/OLMBlur/OLMBlur.cpp` | 746 | 746 |
| `mac/OLMColorKey/OLMColorKey.cpp` | 287 | 287 |
| `mac/OLMDistanceGradation/OLMDistanceGradation.cpp` | 665 | 665 |
| `mac/OLMKiraKira/OLMKiraKira.cpp` | 540 | 539 |
| `mac/OLMRadialBlur/OLMRadialBlur.cpp` | 847 | 847 |
| `mac/OLMRadialBlur/RadialMath.inc` | 320 | 212 |
| `mac/OLMSmoother2/Mac/OLMSmoother2_port.cpp` | 607 | 607 |
| `mac/OLMSmoother2/OLMSmoother2.cpp` | 274 | 274 |
| `core/olm_exact_math.h` | 0 | 253 |

- `orchestra/reports/C01-cleanup-shared-math-and-tests.md` (this report).

verify:
Run from this worktree. Use a fresh `S` (native_diff refuses an existing run directory).

```sh
ROOT="$PWD"
BASE=61e55835ed4ec3bbb0c345d3a699be12f914657c
S="$ROOT/orchestra/state/C01-cleanup-shared-math-and-tests/recheck"
mkdir -p "$S"
export TMPDIR="$S" TMP="$S" TEMP="$S" OLM_TEST_JOBS=1 PYTHONDONTWRITEBYTECODE=1
for plugin in radialblur olmkirakira olmblur olmcolorkey olmdistancegradation olmdirectionalblur olmsmoother2 colorkeep olmtoondilate olmsmoother; do
  python3 tools/refactor/native_diff.py --plugin "$plugin" --base "$BASE" \
    --head 5e39d8a5 --cases 3000 --arch both --build both --jobs 1 \
    --scratch "$S/G1" > "$S/G1-$plugin.log" 2>&1 || break
done
scripts/setup_ae_sdk_links.sh > "$S/sdk-links.log" 2>&1
python3 -B tests/ui_oracle/compare_mac.py --scratch "$S/ui" > "$S/ui.log" 2>&1
python3 -B mac/OLMKiraKira/tests/ui_compare.py --scratch "$S/kira-ui" > "$S/kira-ui.log" 2>&1
python3 -B scripts/run_olm_release_gate_v2.py --jobs 1 --state "$S/release" > "$S/release.log" 2>&1
```

Expected UI: 240 checks and 159 KiraKira dispatches, zero semantic mismatches.
Expected G1: 12,012 comparisons per plugin, zero differences/new refusals/execution errors.
Release-v2 must be 7/7 before claiming its pass. This does not authorize installation or release.

For native-only G2 and warning counts, prepare the baseline (SDK assets remain symlinks, never copies):

```sh
mkdir -p "$S/base"
git archive "$BASE" mac core cli tools ucrtmath reports/radialblur_public_getters_aligned_20261001.json | tar -xf - -C "$S/base"
for name in Headers Util Resources; do ln -s "$ROOT/$name" "$S/base/$name"; done
cat > "$S/replay_native.py" <<'PY_NATIVE'
import importlib,json,os,re,sys,tempfile,time
from pathlib import Path
from types import SimpleNamespace
sys.dont_write_bytecode=True
root,corpus,output=map(Path,sys.argv[1:4]);plugin=sys.argv[4]
sys.path.insert(0,str(root/'tools/fuzz'))
Adapter=importlib.import_module('adapters.'+plugin).Adapter
from core import load_corpus,sha
from geometry import require_host
paths=[]
for path in sorted(corpus.rglob('*.json')):
    saved=json.loads(path.read_text())
    if saved.get('plugin')==plugin:paths.append((path,saved))
with output.open('w') as records:
    for sanitized in sorted({bool(d.get('provenance',{}).get('candidate_sanitize')) for _,d in paths}):
        os.environ['OLM_RADIAL_CANDIDATE_SANITIZE']=str(int(sanitized))
        os.environ['OLM_RADIAL_CANDIDATE_BYPASS']=''
        for name in ('BYPASS','SANITIZE','HOST_FLAGS','NO_TRACE'):
            os.environ['OLM_COLOR_TRIAGE_'+name]='0'
        with tempfile.TemporaryDirectory(dir=output.parent,prefix='native-build-') as tmp:
            directory=Path(tmp)
            adapter=Adapter(SimpleNamespace(main=Path('/Users/onmk/Documents/Projects/Personal/OLM as'),worker=Path('/unused'),max_size=256,case_timeout=180))
            adapter.env.update(OLM_PARALLEL_MAX='1',TMPDIR=str(directory),TMP=str(directory),TEMP=str(directory))
            adapter.binary,_=adapter.build(directory,time.monotonic()+300)
            for path,saved in paths:
                prov=saved.get('provenance',{})
                if bool(prov.get('candidate_sanitize'))!=sanitized:continue
                assert not prov.get('candidate_bypass') and not prov.get('reference_build')
                triage=prov.get('triage',{})
                assert not any(triage.get(k) for k in ('bypass','sanitizers','host_flags_control'))
                adapter.max_size=saved['max_size'];adapter.timeout=prov.get('case_timeout_seconds',10)
                for key in ('size_sampler','color_sampler','size_max_height'):
                    setattr(adapter,key,saved.get(key,None if key=='size_max_height' else 'default'))
                case,_=load_corpus(path,adapter);require_host(adapter,case)
                for route in adapter.routes:
                    with tempfile.TemporaryDirectory(dir=directory) as run:
                        result=adapter.candidate(case,Path(run),route,time.monotonic()+adapter.timeout+5)
                    status,raw=result[:2];tags=result[2] if len(result)==3 else []
                    row=dict(case=str(path.relative_to(corpus)),route=route,result=status,sha256=sha(raw),tags=[re.sub(r'@\d+$','',t) for t in tags])
                    records.write(json.dumps(row,sort_keys=True)+'\n');records.flush()
PY_NATIVE
for plugin in radialblur olmkirakira olmblur olmcolorkey olmdistancegradation olmdirectionalblur olmsmoother2 colorkeep olmtoondilate olmsmoother; do
  for side in base head; do
    TREE="$ROOT"
    if [ "$side" = base ]; then TREE="$S/base"; fi
    python3 -B "$S/replay_native.py" "$TREE" "$ROOT/tests/fuzz_corpus" "$S/G2-$plugin-$side.jsonl" "$plugin" > "$S/G2-$plugin-$side.log" 2>&1
  done
  cmp "$S/G2-$plugin-base.jsonl" "$S/G2-$plugin-head.jsonl" || break
done
for plugin in OLMRadialBlur OLMKiraKira OLMBlur OLMColorKey OLMDistanceGradation OLMDirectionalBlur OLMSmoother2 ColorKeep OLMToonDilate OLMSmoother; do
  for side in base head; do
    TREE="$ROOT"
    if [ "$side" = base ]; then TREE="$S/base"; fi
    OUT="$S/xcode/$plugin/$side"
    mkdir -p "$OUT"
    xcodebuild -project "$TREE/mac/$plugin/Mac/$plugin.xcodeproj" \
      -configuration Debug -jobs 1 ARCHS='arm64 x86_64' ONLY_ACTIVE_ARCH=NO \
      MACOSX_DEPLOYMENT_TARGET=11.0 OBJROOT="$OUT/objects" \
      SHARED_PRECOMPS_DIR="$OUT/pch" CONFIGURATION_BUILD_DIR="$OUT/products" \
      build > "$S/xcode-$plugin-$side.log" 2>&1
    rm -rf "$OUT"
  done
done
```

Expected G2: all ten `cmp` calls return 0, 5,770 observations per side, hashes above.
Expected Xcode: 20 successful builds and warning occurrences in the per-plugin table.
For non-comment line counts, use the same tracked `.cpp/.h/.inc` files at BASE and HEAD,
remove `/\*.*?\*/` with DOTALL, then `//[^\n]*`, and count nonempty stripped lines.



The inherited UI-source assertion is reproducible without pytest (run after the baseline snapshot above):

```sh
python3 -B - "$ROOT" "$S/base" <<'PY_UI_TEXT'
import sys
from pathlib import Path
root,base=map(Path,sys.argv[1:])
for side,tree in [('base',base),('head',root)]:
    for name in ['test_olmradialblur_parameter_ui_parity_20260806.py',
                 'test_olmcolorkey_parameter_ui_parity_20260806.py']:
        ns={'__file__':str(tree/'tests'/name)}
        exec(compile((root/'tests'/name).read_text(),ns['__file__'],'exec'),ns)
        for key,fn in list(ns.items()):
            if key.startswith('test_') and callable(fn):
                try: fn(); print(side,key,'PASS')
                except Exception as error: print(side,key,type(error).__name__)
PY_UI_TEXT
```

Expected: five PASS and the same named AssertionError on each revision. This is not counted as a green text-test gate.

next:
- Scoped math work and G1/G2/release-v2 verification are complete. Before calling every REFACTOR_SPEC gate green, assign the inherited Radial UI-source assertion mismatch (expected flag 0 versus existing 0x40) to a separate test-contract maintenance task. It is not caused by this math change; C01 does not alter that UI contract or weaken the assertion.
- C02 per-plugin tickets own test-entry extraction, admission cleanup, depth templates and further warning cleanup.
