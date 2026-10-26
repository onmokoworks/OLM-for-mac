status: done
summary: Removed superseded captured direction-1/2/3 blur paths and their unused tables/helpers.
Retained direction-0/4 paths because the broad OFF experiment changed Smart output.
Legal public ON/OFF/final campaigns each have 330 Smart-exact cases.
Production code shrinks from 2,584 to 2,352 non-comment/nonblank lines (232 removed).
G1 passes all 12,012 comparisons; builds, UI, corpus replay and warning checks pass.

facts:
- Base: `db59044515791af9890d0768c1fa4c7f5ad34034`. Experiment switch commit: `934d1be5`.
- Read `AGENT_GUIDE.md`, the ColorKey ledger decision/forbidden-action row, `tools/emulation/GOTCHAS.md`, the compatibility plan, and both F/Q specifications. No release gates, ledger, other plugin code, or shared core code changed.
- Original AEX SHA-256: `9c6cca226a52d35ce7833fcc4c0f914f6b15b3abe0202e0957ba97ba3bb2cf2c` (from campaign provenance).
- Original AEX oracle: `/Users/onmk/.cache/olm-emu/worker-X01b-parity/aex-guest-worker`; SHA-256 `34ce39821a53815dbd2252046cf375222d27a8045685fa6d946cfad211e40c4b` (registered prebuilt worker, no rebuild).
- The experiment used `OLM_COLORKEY_FIXTURE_PATHS`, default 0. Final code has no experiment switch. Deletion used a scratch Python script to remove guarded declarations/blocks, fold the direction conditions, and remove unreferenced helpers/constants; compiler unused checks then passed without any new warnings.
- No tool call was rejected. An exploratory search of `tools/fuzz/corpus` found no such directory; the actual retained corpus is `tests/fuzz_corpus/olmcolorkey`.

Predicate inventory (fixture versus general):

| Classification | Predicates / branches | Action |
|---|---|---|
| Fixture | `public_owner_lane`: six exact direction/metric/amount triples | Removed; public recovered worker supersedes the captured output branches. |
| Fixture | `use_pf32_positive_thin_outside_caller`, `EdgeBlurPf32Case9CapturedWeight`: PF32 positive Thin/outside and amount-25 shell table | Removed; public legal directions use recovered processing. |
| Fixture | `use_pf32_amount2_native_plane`, `EdgeBlurPf32Amount2Plane`: amount-2 direction-1/2/3 plane and exact shell branches | Removed. |
| Fixture | `EdgeBlurWeight` captured direction-1/2/3 amount 1/1.5/2/2.5/3/3.5/4 branches, including exact distance shells | Removed, retaining the general fallback formulas. |
| Fixture | Post-recovered captured direction-1/2/3 weight/plane overrides, PF32 amount-2 shell correction, and amount-specific unbounded writer selection | Removed. |
| Fixture, retained | `public_owner_geometry_transfer_lane`, its `public_owner_zero_four_lane` / `bounded_public_owner_lane` aliases, `use_pf32_internal_amount4_native_plane`, `EdgeBlurPf32InternalAmount4Plane`, direction-0/4 captured weight/shell/plane/writer branches | Retained with a one-line source explanation because the broad OFF experiment lost a Smart-exact result. |
| General | `IsRecoveredPublicBlur`, `IsGenericEdgeCompositionTuple` | Retained: public direction/range and finite-value checks, not fixture identity. |
| General admission | `IsGenericEdgeBlurTuple` | Retained: despite exact amount lists and its name, this admits inputs and includes the retained 0/4 lane. Removing it would change admission. |
| General | Pixel-local and Thin admission, null/span/stride/overlap/ROI/origin/downsample checks; `w == 1` distance-transform handling | Retained. No fixed 9×7/32×18/16×16 geometry dispatch was found in this plugin. |
| General | Color-space/precision/component/palette dispatch, key comparison/epsilon checks, distance-metric selection, alpha endpoint/replacement handling, recovered direction selection and phase boundaries | Retained; no arithmetic/type/order changes. |

The ticket's “112 literal-equality chains” is a screening count, not 112 proven fixture predicates. For a separately reproducible metric, stripping comments and counting `==\s*-?\d[\w.]*` across this plugin's top-level `.inc/.cpp/.h/.r` files gives **310 → 182 literal equality comparisons**. This includes general checks and is not a count of removable branches.

Removed tables: `kCapturedInsideOutsideAtZero`, `kCapturedAroundAmount2`, `kCapturedAroundAmount1Point5`, `kCapturedAroundAmount2Point5`, `kCapturedAroundAmount3`, `kCapturedAroundAmount3Point5`, `kPublicAroundPlane`, `kPublicOutsidePlane`, and the case-9 `kShellWeightBits`. No new arithmetic constants were introduced.

Oracle campaigns (seed 101, 330 cases each, `--jobs 1`, source candidate, original AEX both routes):

| Campaign | Smart exact | Smart mismatch | Smart refusal/uncompared | Classic exact | Classic mismatch | Classic refusal/uncompared |
|---|---:|---:|---:|---:|---:|---:|
| Legal ON | 330 | 0 | 0 | 0 | 330 | 0 |
| Legal OFF | 330 | 0 | 0 | 0 | 330 | 0 |
| Legal final deletion | 330 | 0 | 0 | 0 | 330 | 0 |
| Exploratory all directions ON | 275 | 27 | 28 | 0 | 302 | 28 |
| Exploratory all directions broad OFF | 274 | 28 | 28 | 0 | 302 | 28 |
| Exploratory all directions final (0/4 retained) | 275 | 27 | 28 | 0 | 302 | 28 |

- The legal campaign parses 37 direction/metric/amount triples from the base literal predicates; directions 1–3 are the declared popup range. Sources use a 50% black matching palette mixture and 85% opaque alpha sampling, all three depths, and 9×7/32×18/16×16/17×11 worlds. Remaining alpha values are independently sampled.
- Out-of-range directions 0/4 are reported separately, not counted as passing legal cases. All 27 exploratory baseline Smart mismatches and 28 refusals belong to directions 0/4. Classic is outside the SmartFX contract (T14).
- First lost exact case in broad OFF: index 98, PF32, 32×18, Keep=0, Blur=4, metric=3, direction=0. First different byte/word 0; expected word hex `1cf6153e`, actual `0000803f`; 1,143 different bytes / 286 different words. Actual output SHA-256 `3863d8c48068affb8a8549aca8dd56432d51e0ae38841ab4db42bfb33d1e1f93`.
- After retaining 0/4, all 330 exploratory Smart raw hashes/statuses and all 330 Classic raw hashes/statuses equal ON: **0 differences**. No acceptance claim is made for the pre-existing out-of-range mismatches.

Gates:

- Initial random OFF check: `native_diff.py --plugin olmcolorkey --base db590445 --head WORKTREE --cases 300 --jobs 1`, both architectures/builds: **1,212 exact comparisons, 0 differences, 0 refusals, 0 new refusals, 0 execution errors** (300 small + 3 4K cases per combination).
- G1: `native_diff.py --plugin olmcolorkey --base db590445 --head WORKTREE --cases 3000 --jobs 1 --scratch orchestra/state/F01-fixtures-olmcolorkey/g1` passed: **12,012 exact comparisons, 0 differences, 0 refusals, 0 new refusals, 0 execution errors**. Each of arm64 reference, arm64 fast, x86_64 reference, and x86_64 fast has **3,003 exact** (3,000 small + three 4K). Seed 909; first mismatch: none.
- G2: every one of the **51** committed ColorKey corpus JSON witnesses was reconstructed with `core.load_corpus` and its recorded max-size/generator/geometry settings. `native_diff` compared Mac-only raw hashes/refusal tags across both architectures/builds. Smart: **204 exact / 0 differences / 0 refusals / 0 errors**. Classic: **188 exact / 16 matching refusals / 0 differences / 0 new refusals / 0 errors**. No oracle output or timing is used in this comparison.
- G4: Xcode Release universal build succeeded (`-jobs 1`, `ARCHS=arm64 x86_64`, `ONLY_ACTIVE_ARCH=NO`, signing disabled). `lipo -archs` reports `x86_64 arm64`. `test_olmcolorkey_parameter_ui_parity_20260806.py` passed its three checks; `test_olmcolorkey_parameter_order_static_20260728.py` passed four tests. `tests/ui_oracle/compare_mac.py`, restricted to ColorKey through its plugin dictionary, passed **36 updates / 72 checks including reload / 0 mismatches**.
- G5: baseline and final universal Xcode builds both emitted **338 warnings**: 328 SDK pragma-pack, 6 existing ALIGN redefinitions, 2 existing shared `OLMSetDisabled` unused-function warnings, and 2 project warnings. Built with `-Wunused-variable -Wunused-but-set-variable -Wunused-function`; **0 new warnings**, no new unused ColorKey symbols.
- `git diff --check` passed. Sampled scratch usage remained below 256 MiB; regenerable build trees and temporary SDK symlinks were deleted. No started background worker remains.

Non-comment/nonblank source lines (C/C++ line and block comments stripped):

| File under `mac/OLMColorKey/` | Before | After |
|---|---:|---:|
| BlurMath.inc | 230 | 100 |
| Kernel.inc | 572 | 470 |
| ColorMath.inc | 126 | 126 |
| Diagnostics.inc | 149 | 149 |
| Distance.inc | 186 | 186 |
| OLMColorKey.cpp | 287 | 287 |
| OLMColorKey.h | 146 | 146 |
| OLMColorKeyPiPL.r | 31 | 31 |
| OLMColorKey_Strings.cpp | 41 | 41 |
| OLMColorKey_Strings.h | 34 | 34 |
| Parameters.inc | 264 | 264 |
| Pixels.inc | 159 | 159 |
| Render.inc | 359 | 359 |
| Total | **2,584** | **2,352** |

Largest source file after deletion: Kernel.inc, 544 physical lines. No new source files or abstraction layers.

Final source SHA-256 `mac/OLMColorKey/BlurMath.inc`: `5b919964ad975d27456966d8d76c958b879948b66d5f51d51de06f3136c7c56d`.

Final source SHA-256 `mac/OLMColorKey/Kernel.inc`: `c6227f7b9ff22b9ef96d52c038010795e59bec6c6dcb2293d13ba8060c5e34a8`.

inference:
- The public recovered direction-1/2/3 lane makes these captured cases redundant for the declared Smart route. The finite campaigns and corpus establish the recorded boundary, not all-input equivalence of legacy direct internal-worker records.
- Direction-0/4 captures cannot be removed wholesale under the no-output-change rule; they need a separate binary-grounded investigation. Retaining them follows the F-series exception rather than replacing their outputs with patches.

changed_files:
- `mac/OLMColorKey/BlurMath.inc`
- `mac/OLMColorKey/Kernel.inc`
- `orchestra/reports/F01-fixtures-olmcolorkey.md`

verify:
Run from this worktree. Fresh output directories are required by native_diff. The following recreates the required G1 check (expected 12,012 comparisons and zero differences/new refusals/errors):

```sh
S="$PWD/orchestra/state/F01-fixtures-olmcolorkey-recheck"
mkdir -p "$S"
export TMPDIR="$S"
python3 tools/refactor/native_diff.py --plugin olmcolorkey --base db59044515791af9890d0768c1fa4c7f5ad34034 --head HEAD --cases 3000 --jobs 1 --scratch "$S/g1" > "$S/g1.log" 2>&1
```

The focused generator is provided below as an inline reproduction command, not a new committed tool. Its `EXPERIMENT_SOURCE` override permits checking the ON/OFF experiment from an isolated source archive while retaining the shared harness. Save it in `$S/campaign.py`:

```sh
cat > "$S/campaign.py" <<'PY'
import os,sys,re,random,struct,runpy,subprocess
from pathlib import Path
ROOT=Path.cwd()
sys.path.insert(0,str(ROOT/'tools/fuzz'))
import adapters.olmcolorkey as ck
if os.environ.get("EXPERIMENT_SOURCE"):
    ck.SOURCE=Path(os.environ["EXPERIMENT_SOURCE"]).resolve()
from core import case_seed
# Parse the pre-change literal tuples, preserving each conjunction.
src=subprocess.check_output(['git','show','db590445:mac/OLMColorKey/Kernel.inc'],text=True)
tuples=sorted(set((int(a),int(b),float(c)) for a,b,c in re.findall(r'edge_blur_direction == (\d+) && info.edge_blur_distance_type == (\d+) && info.edge_blur_amount == ([\d.]+)',src)))
# Additional amount-specific captured worker branches.
blur=subprocess.check_output(['git','show','db590445:mac/OLMColorKey/BlurMath.inc'],text=True)
tuples+=sorted(set((int(d),t,float(a)) for d,a in re.findall(r'direction == (\d+) && amount == ([\d.]+)f',blur) for t in (1,2,3)))
tuples=sorted(t for t in set(tuples) if os.environ.get("ALLOW_INTERNAL") == "1" or 1 <= t[0] <= 3)
print('parsed tuples',tuples,flush=True)
original=ck.Adapter.generate
compile_original=ck.Adapter.compile
def compile(self,argv,deadline):
    if str(argv[0])=='clang++': argv=list(argv)+['-DOLM_COLORKEY_FIXTURE_PATHS='+os.environ.get('FIXTURE_ON','0')]
    return compile_original(self,argv,deadline)
ck.Adapter.compile=compile
def generate(self,seed,index):
    rng=random.Random(case_seed(seed,index)^0xf01)
    case=original(self,seed,index)
    direction,metric,amount=tuples[index%len(tuples)]
    w,h=rng.choice([(9,7),(32,18),(16,16),(17,11)])
    depth=(8,16,32)[index%3]
    params=self.defaults(w,h);p={p['slot']:p for p in params}
    for slot,v in {1:rng.randrange(2),2:0.0,14:0,18:amount,19:metric,20:direction,22:1,24:1,26:[255,0,0,0]}.items():p[slot]['value']=v
    raw=bytearray()
    for _ in range(w*h):
        top=255 if depth==8 else 32768 if depth==16 else 1.
        alpha=top if rng.random()<.85 else rng.random()*top
        rgb=[0,0,0] if rng.random()<.5 else [rng.random()*top for _ in range(3)]
        values=[alpha,*rgb]
        raw+=struct.pack('<4f' if depth==32 else '<4B' if depth==8 else '<4H',*(values if depth==32 else map(int,values)))
    case.update(geometry=[w,h],depth=depth,parameters=params,pixels=bytes(raw),profile='sdr')
    return case
ck.Adapter.generate=generate
sys.argv=[str(ROOT/'tools/fuzz/run.py')]+sys.argv[1:]
runpy.run_path(str(ROOT/'tools/fuzz/run.py'),run_name='__main__')
PY
```

```sh
mkdir -p "$S/experiment"
git archive 934d1be5 mac/OLMColorKey mac/DynamicControls.h core ucrtmath | tar -x -C "$S/experiment"
PYTHON='/Users/onmk/Documents/Projects/Personal/OLM as/tools/emulation/.venv/bin/python3'
for mode in on off final; do
  export FIXTURE_ON=0
  export EXPERIMENT_SOURCE="$S/experiment/mac/OLMColorKey/OLMColorKey.cpp"
  if [ "$mode" = on ]; then export FIXTURE_ON=1; fi
  if [ "$mode" = final ]; then unset EXPERIMENT_SOURCE; fi
  "$PYTHON" "$S/campaign.py" --plugin olmcolorkey --n 330 --seed 101 --jobs 1 --budget-minutes 20 --case-timeout 30 --shrink-attempts 0 --worker /Users/onmk/.cache/olm-emu/worker-X01b-parity/aex-guest-worker --scratch "$S/$mode" --report "$S/$mode.json" --corpus "$S/$mode-corpus" > "$S/$mode.log" 2>&1
done
```

Expected each: Smart 330 exact, zero mismatch/refusal; Classic 330 mismatch. `ALLOW_INTERNAL=1` additionally samples directions 0/4; ON and final then reproduce the exploratory retained row above. The unretained broad-OFF result was the earlier experiment, before restoring the two 0/4 declarations and the 0/4 disjuncts preserved in `934d1be5`.

Corpus reconstruction command, reusing the shared native_diff worker and core loader:

```sh
cat > "$S/replay.py" <<'PY'
import sys,json
from pathlib import Path
sys.path.insert(0,str(Path('tools/refactor').resolve()))
import native_diff as nd
def cases(adapter,count,seed):
 from core import load_corpus
 for i,path in enumerate(sorted(Path('tests/fuzz_corpus/olmcolorkey').rglob('*.json'))):
  data=json.loads(path.read_text())
  if data.get('plugin')!='olmcolorkey':continue
  adapter.max_size=data['max_size']
  case,_=load_corpus(path,adapter)
  case.update(sequence_index=i,phase='corpus',size_sampler=data.get('size_sampler','default'))
  yield case
nd.cases=cases
sys.exit(nd.main())
PY
python3 "$S/replay.py" --plugin olmcolorkey --base db590445 --head HEAD --jobs 1 --scratch "$S/g2" > "$S/g2.log" 2>&1
```

For the Classic corpus replay, insert these lines immediately after `import native_diff as nd` in the scratch wrapper (the actual run used this same shared-render override):

```python
import inspect
nd.__file__=__file__
exec(inspect.getsource(nd.render).replace("route = 'classic' if adapter.name == 'olmsmoother' else 'smart'", "route = 'classic'"),nd.__dict__)
if len(sys.argv)==3 and sys.argv[1]=='--worker':
    nd.worker(sys.argv[2]);sys.exit(0)
```

Use a fresh `--scratch "$S/g2-classic"`; expected Smart and Classic counts are listed above.

UI/build checks:

```sh
python3 tests/test_olmcolorkey_parameter_ui_parity_20260806.py
python3 tests/test_olmcolorkey_parameter_order_static_20260728.py
python3 - "$S/ui" <<'PY'
import sys
from pathlib import Path
sys.path.insert(0,str(Path('tests/ui_oracle').resolve()))
import compare_mac
compare_mac.PLUGINS={'ColorKey':compare_mac.PLUGINS['ColorKey']}
sys.argv=['compare_mac','--scratch',sys.argv[1]]
compare_mac.main()
PY
# In a worktree without SDK links, link Headers, Util and Resources to MAIN;
# never copy the SDK or modify MAIN.
for name in Headers Util Resources; do
  if [ ! -e "$name" ]; then ln -s "/Users/onmk/Documents/Projects/Personal/OLM as/$name" "$name"; fi
done
xcodebuild -project mac/OLMColorKey/Mac/OLMColorKey.xcodeproj -configuration Release -jobs 1 'ARCHS=arm64 x86_64' ONLY_ACTIVE_ARCH=NO CODE_SIGNING_ALLOWED=NO "SYMROOT=$S/products" "OBJROOT=$S/objects" 'WARNING_CFLAGS=-Wunused-variable -Wunused-but-set-variable -Wunused-function' > "$S/xcode.log" 2>&1
```

Expected: UI 72/72, four static ordering tests and three UI-shape checks pass; universal Xcode build succeeds. Baseline warning comparison used a `git archive db590445 mac/OLMColorKey mac/DynamicControls.h core ucrtmath` snapshot under scratch, the same SDK symlinks, and the same Xcode flags.

next:
- Optional follow-up: investigate the retained out-of-range direction-0/4 owner paths against the original binary; preserve the index-98 boundary above. No changes to those general formulas or admission rules were attempted here.
- The orchestrator can run its independent seed and review the retained-fixture exception before merging. No push or release action performed.
