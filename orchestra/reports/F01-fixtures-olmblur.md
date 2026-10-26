status: blocked

summary:
- Removed all 27 fixed-tuple Smart admissions and their source-pattern/padding-copy fallback.
- ON Smart: 421 exact / 146 padding-canary errors; OFF and final: 567 exact / zero mismatches.
- G1: 12,012 exact, zero differences/refusals/new refusals/execution errors; 3,003 comparisons per architecture/build (arm64/x86_64, reference/fast), including three 4K cases each. First mismatch: none. Final source tested with --head WORKTREE before committing, identical to the committed source.
- Corpus replay: 139/139 identical Mac results; Universal Xcode and UI/sanitizer checks pass.
- Strict G4 is blocked by unchanged historical source/evidence test failures; deletion and numerical validation are complete.

facts:
- Pre-change base: `5978493bbf14d1b2ca0a5e68af9b330b4745714f`; branch `orch/F01-fixtures-olmblur`. Production sources at the previous investigation's `db59044515791af9890d0768c1fa4c7f5ad34034` and this base are byte-identical in OLMBlur and its core files (`git diff` empty).
- Read AGENT_GUIDE, FIXTURE_REMOVAL, REFACTOR_SPEC, GOTCHAS, compatibility plan, OLMBlur ledger matches, previous F01 and Q06 reports. No MAIN, emulator source, release gate, ledger or other-plugin edits; no push/stash/worker rebuild.
- Step 2 used `OLM_BLUR_FIXTURE_PATHS` (default 0) to gate all 27 `public*` predicates. Step 3: `native_diff.py --plugin olmblur --base HEAD --head WORKTREE --cases 300 --jobs 1` gave 1,212 exact, zero differences/refusals/new refusals/execution errors, both architectures/builds.
- Step 4 reran the previous report's focused generator with `--n 567 --seed 20261026 --jobs 1 --budget-minutes 45 --case-timeout 30 --shrink-attempts 0`, once ON and once OFF. Each family has 21 cases: seven original source-pattern/stride cases and fourteen random-colour cases with 90% opaque-alpha probability. All 567 input hashes, geometries, parameters and strides are identical across ON, OFF and final OFF. The generator parses literal predicates, enumerates satisfying tuples, and uses the original source-pattern definitions only to write test inputs; it does not generate expected outputs.
- Step 5 used a small Python substring/regex deletion script: fold all fixture predicates false, remove their selection/source enum, fold `exact_fixture_owner` false, keep the existing generic lane and refusal priority, delete the now-unreachable render/copy tail, and remove unused ExactPublicWorld/PublicWorldsDisjoint and OLMBlur_Fixtures.inc. No arithmetic changed. The final source has no experimental switch.
- The approved padding decision is observable: old fallback copied input 0xA5 row padding into output; the generic path preserves output padding. Full fixture matches now also use the existing generic staging/checkin lifecycle instead of the fallback's PF_COPY callback. No claim of complete AE-host lifecycle equivalence is made.

| Campaign | Smart exact | Smart refusal/uncompared | Smart error | Smart pixel mismatch | Classic exact | Classic refusal | Classic error/mismatch |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| ON | 421 | 0 | 146 | 0 measured | 0 | 567 | 0 |
| OFF (switch) | 567 | 0 | 0 | 0 | 0 | 567 | 0 |
| OFF (final deletion) | 567 | 0 | 0 | 0 | 0 | 567 | 0 |

- Original AEX in each campaign: Smart 567 ok; Classic 428 ok / 139 reject. ON errors are uncompared executions, not exact results or pixel mismatches. Every error is exit 68 (padding canary). No active-pixel equality claim for these 146 aborted ON renders.
- First boundary remains case 0, public24, PF16 24x24, amount 5, Smoothness 100, repeat 1, bias 1, Legacy 1, padding 23. Input SHA256 `bb4130a96cab14e0e5a6c186f81803ffc744608ac4dfd8d10ea9e97aaae7ce88`; final OFF/AEX output `c22524ff901f905cc2d9354a0a6a47ed5aecd1dcc0d46fc79439d5ee069593fc`; ON exits 68 before output.
- AEX SHA256 `f0611785e7b14ac4fcfc75f23b8862beb4539eee52d25d472556849535e96e5b`; retained `/Users/onmk/.cache/olm-emu/worker-F46-pow/aex-guest-worker` SHA256 `6616943ba74e07d7f1c0209fe8e650bd496f6caa92fc5a1d3a4151063a36a903`.
- Candidate hashes (path-dependent): ON `2958b85f262100b8e698d3d5d4b50d6337df8b7245e67bc40e103f568747989d`; switched OFF `e88f719602e2716d464242ec698a97638008b99be70154ebce2eed43c9413e75`; final `2f93ec6ce01a309f2dd629b5fb513ed7943c3bc575e9e9a0576dc077b573f39e`.

Predicates — fixture (all deleted; per-family counts):

| Predicate | Cases per campaign | ON Smart exact | ON error | Final OFF Smart exact |
| --- | ---: | ---: | ---: | ---: |
| `public24` | 21 | 16 | 5 | 21 |
| `public7x5` | 21 | 14 | 7 | 21 |
| `public12x12` | 21 | 14 | 7 | 21 |
| `public18x18` | 21 | 14 | 7 | 21 |
| `public18x12` | 21 | 14 | 7 | 21 |
| `public8NonLegacy12` | 21 | 14 | 7 | 21 |
| `public8NonLegacy24` | 21 | 14 | 7 | 21 |
| `public8NonLegacy18` | 21 | 14 | 7 | 21 |
| `public8NonLegacy24Repeat2` | 21 | 14 | 7 | 21 |
| `public8Legacy12` | 21 | 14 | 7 | 21 |
| `public8Legacy18` | 21 | 14 | 7 | 21 |
| `public8Legacy18x12` | 21 | 14 | 7 | 21 |
| `public8Legacy6` | 21 | 14 | 7 | 21 |
| `public8LegacyBoundary12` | 21 | 14 | 7 | 21 |
| `public8Legacy16` | 21 | 14 | 7 | 21 |
| `public8Legacy10x8` | 21 | 14 | 7 | 21 |
| `public8LegacySmooth` | 21 | 14 | 7 | 21 |
| `public16LegacySmooth` | 21 | 14 | 7 | 21 |
| `public32NonLegacyRetained` | 21 | 20 | 1 | 21 |
| `public32Legacy12` | 21 | 21 | 0 | 21 |
| `public32Legacy18` | 21 | 21 | 0 | 21 |
| `public32Legacy18x12` | 21 | 14 | 7 | 21 |
| `public32Legacy7x5` | 21 | 14 | 7 | 21 |
| `public32Legacy9x7` | 21 | 14 | 7 | 21 |
| `public32Legacy24Repeat1` | 21 | 21 | 0 | 21 |
| `public32Legacy24Repeat10` | 21 | 21 | 0 | 21 |
| `public32LegacySmooth` | 21 | 21 | 0 | 21 |

- Also deleted: `exact_fixture_owner`, `PublicBlurSourceKind`, `ExactPublicSource` and its fixed-size/palette/coordinate identity comparisons. `ExactPublicWorld`, `PublicWorldsDisjoint`, and `full_resolution` were general geometry/storage checks used exclusively by the deleted fallback and became unused.

Predicates — general / retained:
- `GenericBetaTupleRefusal`: finite/legal controls, supported depths, positive dimensions, checked multiplication and vector representability. The historical `generic-small-fixture` refusal identifies unsupported depth, not an input identity.
- `GenericBetaWorld`, `ClassicCopyGeometry`, format/stride/origin validation, staging and downsample behavior are general host/storage conditions.
- `SmallDefaultPF32Source` and the <=24 guard are a value-domain admission; they do not compare an image against literal pixels.
- Classic default-control copy-only tuple has no fixed image size/source; preserved unchanged. Per-depth/Legacy/alpha/boundary/parallel/reference arithmetic and dispatch are unchanged. No fixture input predicates in OLMBlur-only core headers.
- Retained case0006 observation gates (`OLMBLUR_OBSERVE_CASE0006_PIXEL`, case-id check, kObservedX/Y) are opt-in diagnostics, not an alternate pixel calculation or admission fallback. They and their capture validation are unchanged; this ticket does not remove diagnostic instrumentation.

Gates:
- G1: 12,012 exact, zero differences/refusals/new refusals/execution errors; 3,003 comparisons per architecture/build (arm64/x86_64, reference/fast), including three 4K cases each. First mismatch: none. Final source tested with --head WORKTREE before committing, identical to the committed source.
- G2: native-only replay through existing `load_corpus`, `require_host`, and production `Adapter.candidate`, base and final. 139/139 records identical including raw hashes, metadata/callback counts, refusal tags (source-line suffix normalized), and saved-result pass/fail. Smart 139 exact; Classic 17 exact / 122 existing refusals. Corpus counts: default 39; downsample_P01a 43; realistic_P02h 36; P05c-parallel-boundary 18; T15b-odd-even-realistic 3. Each recorded max-size, sampler, height and timeout is restored. All 139 match saved results on both revisions. Oracle re-execution is deliberately excluded from this Mac-side G2 comparison.
- G4 build: base and final `xcodebuild -configuration Debug -jobs 1 ARCHS="arm64 x86_64" ONLY_ACTIVE_ARCH=NO MACOSX_DEPLOYMENT_TARGET=11.0` both exit 0. SDK directories were temporary symlinks to MAIN; build products stayed in scratch.
- G4 behavior/UI: all five ROI functions pass; unchanged generic production ASan/UBSan probe passes (six odd-geometry rows); `tests/ui_oracle/compare_mac.py` restricted in memory to Blur gives 2 updates / 4 checks including reload / zero mismatches.
- G4 historical tests: unittest loading of all 34 `test_olmblur*.py` files yielded 83 loaded tests / 14 failures / 11 errors plus 9 import failures before, 81 loaded tests / 13 failures / 11 errors plus the same 9 import failures after. Remaining failure/error test IDs are identical. Missing historical manifests/handoffs and pre-existing source/hash pins remain. In particular, generic geometry test still expects obsolete `usize_width > ((size_t)-1) / usize_height` instead of the existing checked_multiply call. These unrelated assertions were not rewritten; G4's entire historical suite is NOT green.
- G5: both Universal Xcode builds explicitly enabled `-Wunused-variable -Wunused-but-set-variable -Wunused-function`. Both have 336 compiler warnings (328 pragma-pack, 6 ALIGN and 2 ABS macro redefinitions) plus 2 existing project warnings = 338 each; zero new/increased warning categories and zero unused warnings.
- Original-source unittest results were rechecked after G1 (temporarily restore the five changed base files, run, and restore final bytes in a finally block): identical to the switched baseline, confirming the listed failures predate this deletion.
- `git diff --check` passes. No tool approval rejection. A scratch diagnostic glob had no matches; no task action was blocked.
- Initial explicit ROI function run exposed two assertions pinning the deleted ExactPublicWorld extent checks. Removed those authorized source-text assertions and reran all five successfully. Behavior checks remain unchanged.

Deleted source-contract assertions (no behavior-test deletion):
- `tests/test_olmblur_generic_beta_lane_20260820.py`: removed `test_lane_precedes_exact_fixture_admission` and `test_exact_small_fixtures_remain_owned_by_exact_lane`.
- `tests/test_olmblur_16bpc_typed_exact_contract_20260805.py`: removed only the `ExactPublicSource(input_world,bpc)` and fallback `staged_input.rowbytes=(A_long)active` assertions.
- `tests/test_olmblur_roi_halo_contract_20260820.py`: removed only two `world->extent_hint.right/bottom != width/height` assertions for the deleted fallback helper; origin/general checks remain.
- No 0xA5 probe/assertion file was deleted; the old source-pattern host is still a test input generator, not production code.

Code lines (remove C/C++ comments, then blank lines; .cpp/.h/.inc/.r):

| File in mac/OLMBlur | Physical before / after | Code before / after |
| --- | ---: | ---: |
| `OLMBlur.cpp` | 832 / 622 | 738 / 538 |
| `OLMBlur.h` | 75 / 75 | 63 / 63 |
| `OLMBlurPiPL.r` | 33 / 33 | 31 / 31 |
| `OLMBlur_Fixtures.inc` | 252 / 0 | 220 / 0 |
| `OLMBlur_Strings.cpp` | 23 / 23 | 20 / 20 |
| `OLMBlur_Strings.h` | 14 / 14 | 13 / 13 |
| `OLMBlur_Workers.inc` | 360 / 360 | 311 / 311 |

Mac total non-comment/nonblank code: **1396 -> 976 (-420)**. Physical lines: 1589 -> 1127 (-462). Largest remaining file: 622 lines. Core headers unchanged. No new abstraction or source file.

inference:
- All tested fixture families can use the existing general Smart path; ON-only padding writes are unnecessary under the explicit F01 contract decision. This is bounded CPU oracle evidence, not a claim of universal input/AE-host equivalence.
- Historical test failures are base defects or stale evidence dependencies, not regressions introduced by deleting these admissions. The release owner must decide their separate cleanup; this report does not hide them as passes.

changed_files:
- `mac/OLMBlur/OLMBlur.cpp`
- `mac/OLMBlur/OLMBlur_Fixtures.inc` (deleted)
- The three source-test files listed above.
- `orchestra/reports/F01-fixtures-olmblur.md`

verify:
Run from this worktree. Use fresh scratch subdirectories on repeats; never use /tmp.

```sh
BASE=5978493bbf14d1b2ca0a5e68af9b330b4745714f
MAIN='/Users/onmk/Documents/Projects/Personal/OLM as'
STATE="$PWD/orchestra/state/F01-fixtures-olmblur"
mkdir -p "$STATE"
export TMPDIR="$STATE" TMP="$STATE" TEMP="$STATE" OLM_TEST_JOBS=1
python3 tools/refactor/native_diff.py --plugin olmblur --base "$BASE" --head HEAD --cases 3000 --jobs 1 --scratch "$STATE/recheck-g1" > "$STATE/recheck-g1.log" 2>&1
```
Expected G1: 12,012 exact; all difference/refusal/new-refusal/execution-error counts zero.

Extract the reproducible focused generator from the previous committed investigation (same input definitions, unchanged plugin base):

```sh
python3 - <<'PY_EXTRACT'
from pathlib import Path
import subprocess
r=subprocess.check_output(['git','show','03192244d4bfe5942abf4d9bae3f775e4eddd2c4:orchestra/reports/F01-fixtures-olmblur.md'],text=True)
Path('orchestra/state/F01-fixtures-olmblur/focused.py').write_text(r.split('```python\n')[1].split('```')[0])
PY_EXTRACT
FIXTURE_PATHS=0 "$MAIN/tools/emulation/.venv/bin/python3" "$STATE/focused.py" --plugin olmblur --n 567 --seed 20261026 --jobs 1 --budget-minutes 45 --case-timeout 30 --shrink-attempts 0 --worker /Users/onmk/.cache/olm-emu/worker-F46-pow/aex-guest-worker --scratch "$STATE/recheck-final" --report "$STATE/recheck-final.json" --corpus "$STATE/recheck-corpus" > "$STATE/recheck-final.log" 2>&1
```
Expected final: 567 Smart exact, Classic 567 refusals, zero pixel mismatches/errors. For ON and switched OFF reproduction, use the previous report's switch/extraction commands in a disposable base checkout, with `--n 567` instead of 324; expected ON 421 exact / 146 errors, OFF 567 exact. No acceptance condition is relaxed.

G2 exact native-only command used:

```sh
python3 "$STATE/replay-native.py" "$STATE/base-source" base > "$STATE/replay-base.log" 2>&1
python3 "$STATE/replay-native.py" "$PWD" head > "$STATE/replay-head.log" 2>&1
```
Create base-source with `tools/refactor/native_diff.py`'s `snapshot(BASE, destination)` helper. Save the following block as `$STATE/replay-native.py` (embedded rather than committed as a one-off tool). Expected JSON arrays identical; each command prints `completed 139 saved_matches 139`.

```python
import hashlib,json,pathlib,re,sys,time
from types import SimpleNamespace
root=pathlib.Path(sys.argv[1]).resolve(); workspace=pathlib.Path.cwd(); state=workspace/'orchestra/state/F01-fixtures-olmblur'; side=sys.argv[2]
sys.path.insert(0,str(root/'tools/fuzz'))
from adapters.olmblur import Adapter
from core import load_corpus
from geometry import require_host
out=state/('replay-'+side);out.mkdir(exist_ok=True)
a=Adapter(SimpleNamespace(main=workspace.parent.parent,worker=pathlib.Path('/unused'),max_size=256,case_timeout=30))
a.binary,_=a.build(out,time.monotonic()+600)
rows=[]
for p in sorted((workspace/'tests/fuzz_corpus').glob('*olmblur*/**/*.json')):
    saved=json.loads(p.read_text());a.max_size=saved['max_size'];a.size_sampler=saved.get('size_sampler','default');a.size_max_height=saved.get('size_max_height');a.timeout=saved.get('provenance',{}).get('case_timeout_seconds',10)
    case,_=load_corpus(p,a);require_host(a,case);routes={}
    for route in a.routes:
        result,raw,tags=a.candidate(case,out,route,time.monotonic()+a.timeout+5)
        if result['status']=='ok': result['raw_sha256']=hashlib.sha256(raw).hexdigest()
        expected=saved['result']['routes'][route]
        match=(result['status']=='ok' and expected['status']=='exact' and result['raw_sha256']==expected['raw_sha256']) or (result['status']==expected['status']=='refusal' and result['error']==expected['error'])
        routes[route]=dict(result=result,tags=[re.sub(r'@\d+$','',t) for t in tags],matches_saved=match)
    rows.append(dict(path=str(p.relative_to(workspace)),routes=routes))
    (state/('replay-'+side+'.json')).write_text(json.dumps(rows,indent=2))
print('completed',len(rows),'saved_matches',sum(all(r['matches_saved'] for r in row['routes'].values()) for row in rows))
```

Build/UI/function-test commands were run via the following scratch drivers; they are embedded for exact reproduction. Save as `$STATE/build.py` and `$STATE/behavior.py` respectively, then run `python3 "$STATE/build.py" > "$STATE/build.log" 2>&1` and `python3 "$STATE/behavior.py" > "$STATE/behavior.log" 2>&1`. Expected builds exit 0, six PASS function lines and Blur UI zero mismatches. The base archive must exist as above. Both drivers remove their SDK symlinks afterward.

```python
import pathlib,subprocess,os,json
root=pathlib.Path.cwd();state=root/'orchestra/state/F01-fixtures-olmblur';main=root.parent.parent;results=[]
for name,source in [('base',state/'base-source'),('head',root)]:
 links=[]
 try:
  for item in ['Headers','Util','Resources']:
   link=source/item
   if not link.exists():link.symlink_to(main/item,target_is_directory=True);links.append(link)
  dest=state/('xcode-'+name)
  cmd=['xcodebuild','-project',str(source/'mac/OLMBlur/Mac/OLMBlur.xcodeproj'),'-configuration','Debug','-jobs','1','ARCHS=arm64 x86_64','ONLY_ACTIVE_ARCH=NO','MACOSX_DEPLOYMENT_TARGET=11.0','OTHER_CPLUSPLUSFLAGS=$(inherited) -Wunused-variable -Wunused-but-set-variable -Wunused-function',f'OBJROOT={dest}/obj',f'SYMROOT={dest}/products',f'SHARED_PRECOMPS_DIR={dest}/pch','build']
  with (state/('xcode-'+name+'.log')).open('w') as log:r=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT)
  results.append(dict(side=name,command=cmd,exit=r.returncode));print(name,r.returncode,flush=True)
 finally:
  for link in links:link.unlink()
(state/'xcode.json').write_text(json.dumps(results,indent=2))
```

```python
import importlib.util,pathlib,runpy,sys
root=pathlib.Path.cwd();state=root/'orchestra/state/F01-fixtures-olmblur';links=[]
try:
 for name in ['Headers','Util','Resources']:
  p=root/name
  if not p.exists():p.symlink_to(root.parent.parent/name,target_is_directory=True);links.append(p)
 for file in ['test_olmblur_roi_halo_contract_20260820.py','test_olmblur_generic_beta_sanitizers_20260820.py']:
  for name,fn in runpy.run_path(str(root/'tests'/file)).items():
   if name.startswith('test_'):fn();print('PASS',name,flush=True)
 p=root/'tests/ui_oracle/compare_mac.py';spec=importlib.util.spec_from_file_location('ui',p);ui=importlib.util.module_from_spec(spec);spec.loader.exec_module(ui);ui.PLUGINS={'Blur':ui.PLUGINS['Blur']};sys.argv=[str(p),'--scratch',str(state/'ui')];ui.main()
finally:
 for p in links:p.unlink()
```

`python3 -m unittest discover -s tests -p 'test_olmblur*.py'` reproduces the historical suite failures described above (not a passing gate). It also discovers the nine import errors. `git diff --check` should exit 0.

next:
- Orchestrator review/merge. Separate follow-up: repair stale OLMBlur source/hash assertions and missing historical evidence dependencies if the complete historical unittest suite is required as a release gate.
- Cleanup complete: all started commands exited; scratch build/archive/replay binaries and temporary SDK symlinks removed. Final scratch scan found zero Mach-O files. Logs, JSON measurements and scratch drivers remain; no durable reference worker was created. Largest sampled scratch usage was 674 MiB, below 5 GiB.
