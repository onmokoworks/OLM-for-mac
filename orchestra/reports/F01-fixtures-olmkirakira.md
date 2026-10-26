status: blocked
summary:
  Removed the redundant 32x18 admission family and its source-text assertion.
  Kept the three Gaussian leaves: unchanged behavioural assertions require their admission.
  Kept the fixed tuple map/5x3 family because prior blanket OFF lost Smart admissions.
  The requested combined removal is incomplete; the validated 32x18 subset is reviewable.

facts:
- Resume base: `daffe2cc` on `orch/F01-fixtures-olmkirakira` (clean at start).
- Read the shared guide, F-series method, refactor gates, compatibility plan,
  emulator gotchas and the KiraKira ledger sections. No release gate, forbidden-action
  list, MAIN source, original binary, or worker was modified. No push or worker rebuild.
- Prior experiment is preserved in `F01-fixtures-olmkirakira-evidence/prior-attempt.md.gz`
  and the `prior-*.json.gz` evidence, copied from commit
  `1de66c96177d4a72d328b000a8fca5cb380e3b49`. Its facts below are inherited evidence,
  not claimed as fresh executions in this resume.
- Prior method steps 2–4 used `OLM_KIRAKIRA_FIXTURE_PATHS`, the broad ON/OFF campaign,
  and a stable selected-OFF 300-case differential. This resume mechanically folded the
  32x18 predicates false with the Python script embedded below, then ran final gates.
- Deleted `IsMode3Closure32x18Tuple`, `IsMode3Closure32x18Layout`, their Classic/Smart
  consumers and the two `kMode3SmartClosure*` constants. Arithmetic is unchanged.
- Deleted only two fixture-presence lines in
  `tests/test_olmkirakira_generic_beta_lane_20260820.py`:
  obtaining `IsMode3Closure32x18Tuple` as source text and asserting it contains
  `info.horizontal_length == 50`. All other assertions remain unchanged.
- The Gaussian blocker is different: `tools/emulation/test_kirakira_mode3_nonwhitelist_geometry.cpp`
  executes `assert(mode3_gaussian_admitted(11,6,3))`, `(13,5,7)`, `(15,6,9)`.
  Deleting these leaves makes each return false. The F-series permission explicitly
  covers source-text assertions; it also explicitly requires behavioural tests to
  pass unchanged. No such assertions or Gaussian production code were changed.

Predicate inventory (source facts; fixture/general classification is inference):
- Fixture-style, retained: the seven conjunctions in `ClassicClosureSourceFamilyForTuple`:
  `mode1_horizontal`, `mode1_highlight`, `mode2_horizontal`, `mode2_highlight`,
  `mode3_horizontal`, `mode4_highlight_gradient`, `mode4_declared_family`;
  their default color/ramp and zero-control preconditions; `IsClassicClosureTuple`;
  `IsClassicClosureLayout` (5x3); `ClassicClosureSourceMatches` (indexed byte patterns,
  PF16 promotion, PF32 bit equality). These also feed general-size admission.
- Fixture-style, deleted: the 32x18 tuple/layout helpers and `mode3_32x18_closure`,
  `pre_is_mode3_32x18`, their operands in `exact_world_layout`, `exact_tuple_is_admitted`
  and `exact_closure`. This is one deleted fixture family.
- Fixture-style, retained by behavioural test contract: the three Gaussian workspace
  exceptions `(11,6,3)`, `(13,5,7)`, `(15,6,9)` (width,height,length).
- General, retained: full-frame dimension/ROI/storage/disjointness guards,
  `KiraSmartGeometryFits`, checked arithmetic, Mode3 memory/work budgets, generic ray
  admission, finite-SDR/source support, zero-ray/alpha-box paths, Smart scalar/color
  box checks, approximation and directional Gaussian selection, enum dispatch,
  zero-length skips, percentage endpoints, float representability, recovered seed/color pipelines.
- Mixed dependencies, retained: `IsGenericBetaMode12Tuple`,
  `IsGenericBetaMode3HorizontalTuple`, `IsGenericBetaMode34TupleForGeometry`,
  `IsGenericBetaTupleForGeometry`; these use the fixed map at arbitrary sizes.
  `ColorIsClosureWhite` and `RampIsClosureDefault` describe controls, not source pixels.
- The brief's 98 is not an independently verified predicate count. Regex
  `\binfo\.\w+\s*==\s*-?[\d.]+` counts Admission 86→81, Filters 20→20, Render 15→15:
  121→116 expressions, not a count of removable predicates.

Oracle campaigns:

| Campaign | Cases | Smart exact | Smart mismatch | Smart uncompared/refusal | Classic exact | Classic mismatch | Classic uncompared/refusal |
|---|---:|---:|---:|---:|---:|---:|---:|
| Prior broad ON | 315 | 259 | 0 | 56 | 0 | 236 | 79 |
| Prior broad blanket OFF | 315 | 90 | 0 | 225 | 0 | 40 | 275 |
| Prior 32x18 + Gaussian OFF | 315 | 259 | 0 | 56 | 0 | 236 | 79 |
| Prior Gaussian supplement ON | 18 | 18 | 0 | 0 | 0 | 0 | 18 |
| Prior Gaussian supplement OFF | 18 | 18 | 0 | 0 | 0 | 0 | 18 |
| Fresh 32x18 ON | 315 | 315 | 0 | 0 | 0 | 315 | 0 |
| Final 32x18 deleted | 315 | 315 | 0 | 0 | 0 | 315 | 0 |

- Fresh seed 1001; 105 cases per depth (8/16/32), all 315 satisfy the deleted
  32x18/Mode3/Merge1/gain0.1/length50/rotation0/default-control family. This exceeds
  the 20-per-deleted-family minimum. Three Gaussian families were not deleted;
  their inherited six cases per leaf are not claimed to meet that deletion minimum.
- Generator parses the baseline map and deleted tuple/layout literals, uses mostly
  opaque random sources and indexed exact-pattern sources every fourth case.
  The final parser version was checked against all 315 recorded input hashes,
  parameters, dimensions, depths and padding: zero changes with recorded max-size 256.
- Every fresh original execution completed successfully: 315 Classic + 315 Smart
  per campaign, intact guards, no framework failures/timeouts. Full observation
  results are identical ON/OFF, not just aggregate counts.
- First retained Classic mismatch, both campaigns: index 0, PF8, byte 0,
  original `00`, Mac `4b`, 2,304 differing bytes. Input SHA-256
  `10dec3fb5e5ed3c0ba773832d4ba0ae2c7544ffc66217a830b6ebe5007d126f6`;
  Mac/Smart oracle output SHA-256
  `77c5825780a940fcb87825807c9d91eda4919e97f72b4c34977e05f7e6d3ac6e`.
  No Smart first mismatch. Classic is outside this plugin's T14 Smart contract.
- Prior blanket OFF first lost admission: case 0, `mode1_horizontal`, 5x3 PF8,
  input `40a68d8a2f5e83c281777829bffdbdb4850838d44a7746e03c94286918d2e3b9`;
  ON exact, OFF error 516. One source comment explains why the tuple map stays.

Gate results:
- G1: exit 0; 12,012 comparisons, 11,712 exact renders, 300 identical refusals,
  0 differences, 0 new refusals, 0 execution errors. Each of arm64/x86_64 ×
  reference/fast: 3,003 comparisons, 2,928 exact, 75 identical refusals.
  Seed 909, 3,000 small cases plus three UHD cases per configuration; 4,004
  comparisons per depth. Source remained unchanged throughout all configurations.
  First differing byte: none. `G1-summary.json` records coverage and all eight
  baseline/head executable hashes. G1 worker/compiler logs contain no warnings.
- G2 native-only replay: all 390 corpus witnesses in seven directories, using each
  saved max-size, size/color/geometry sampler and parameters via `load_corpus`.
  Compared 780 Classic/Smart observations: 0 differences in status, metadata,
  raw SHA-256 or ordered refusal tags (only source-line suffixes normalized).
  Smart 389 renders/1 refusal; Classic 47 renders/343 refusals. No oracle claims
  are made for this native-only replay. Both JSONL files have SHA-256
  `771f0a771d178b0f8b784d86e7648bd9cbf128632f3acc5ea67936ccc241c5d6`.
- G4 Xcode: baseline and head Release builds succeeded for x86_64 and arm64,
  -jobs 1, signing disabled; `lipo -archs` verified both architectures.
- G4 UI: 13 sessions/159 dispatches, zero active-state/ordered-call mismatches;
  existing inactive capacity differences remain under the unchanged comparator policy.
  Persistence: 34 presets byte-identical, zero live handles. Shared UI runner:
  seven plugins/240 checks/zero mismatches. All three runners completed successfully.
- G4 tests: 142 tests at both base and head; same 20 failure + 43 error IDs,
  zero new failures/errors. Full logs and ID comparison are committed. This is
  baseline equality, not a claim that the historical suite is fully green.
  Targeted generic-beta module: 9 tests pass. Original Gaussian C++ test: exit 0.
- G5: compiled with -Wunused-variable -Wunused-but-set-variable -Wunused-function.
  334 warning lines before and after; sorted warning messages identical. No new warning.
- Original AEX SHA-256: `60997c0c52207c15844a46289435231fa6b0a885f63778404e02cea6e03899f7`.
  Cached worker: `/Users/onmk/.cache/olm-emu/worker-F54c/aex-guest-worker`, SHA-256
  `3d5eec0c6792f176a9cfbc38093c53b852f4ea1baae2cfd313345c02f55d6fba`.
- No tool call was rejected. No background processes or regenerable builds are retained
  after final cleanup. Scratch usage: 172 MiB sampled during work, 34 MiB after cleanup (below 5 GiB). Logs and evidence remain.

Code line counts:
Top-level plugin cpp/h/inc plus its core/kirakira*.h; comments and blank lines excluded
by a scanner preserving quoted strings. No arithmetic constants or general code were
renamed; the scope was fixture removal. No file exceeds 1,000 physical lines.

| File | Physical before | Physical after | Code before | Code after |
|---|---:|---:|---:|---:|
| `core/kirakira_gaussian.h` | 182 | 182 | 146 | 146 |
| `core/kirakira_highlight.h` | 126 | 126 | 111 | 111 |
| `core/kirakira_highlight_gaussian.h` | 84 | 84 | 72 | 72 |
| `core/kirakira_merge2.h` | 339 | 339 | 306 | 306 |
| `core/kirakira_mode4.h` | 119 | 119 | 103 | 103 |
| `core/kirakira_sincos.h` | 3 | 3 | 2 | 2 |
| `core/kirakira_sincos_tables.h` | 523 | 523 | 520 | 520 |
| `core/kirakira_warp.h` | 136 | 136 | 124 | 124 |
| `mac/OLMKiraKira/KiraAdmission.inc` | 780 | 748 | 659 | 631 |
| `mac/OLMKiraKira/KiraFilters.inc` | 419 | 419 | 356 | 356 |
| `mac/OLMKiraKira/KiraParameters.inc` | 270 | 270 | 238 | 238 |
| `mac/OLMKiraKira/KiraRampUI.inc` | 291 | 291 | 275 | 275 |
| `mac/OLMKiraKira/KiraRender.inc` | 250 | 250 | 206 | 206 |
| `mac/OLMKiraKira/KiraWorld.inc` | 401 | 401 | 359 | 359 |
| `mac/OLMKiraKira/OLMKiraKira.cpp` | 600 | 591 | 529 | 520 |
| `mac/OLMKiraKira/OLMKiraKira.h` | 189 | 189 | 174 | 174 |
| `mac/OLMKiraKira/OLMKiraKira_Strings.cpp` | 46 | 46 | 43 | 43 |
| `mac/OLMKiraKira/OLMKiraKira_Strings.h` | 37 | 37 | 36 | 36 |
| `mac/OLMKiraKira/RampEditor.h` | 235 | 235 | 225 | 225 |
| `mac/OLMKiraKira/RampPresets.h` | 389 | 389 | 387 | 387 |
| **Total** | **5419** | **5378** | **4871** | **4834** |

inference:
- The measured 32x18 admission is redundant with the general path. No assertion of
  correctness for unmeasured parameters or host implementations follows from this.
- The Gaussian pixel-neutral experiment does not authorize changing its independently
  asserted helper behaviour. This is the remaining blocker, not a Smart pixel mismatch.
- Blanket removal remains incorrect; it removes admissions. Recovering general
  brightness/Mode4 support is a separate task, not an arithmetic change in this ticket.

changed_files:
- `mac/OLMKiraKira/KiraAdmission.inc`: remove two helpers, retain-map explanation.
- `mac/OLMKiraKira/OLMKiraKira.cpp`: fold their callers and remove unused constants.
- `tests/test_olmkirakira_generic_beta_lane_20260820.py`: remove two source-text assertions.
- `orchestra/reports/F01-fixtures-olmkirakira.md` and its evidence directory.

verify:
Run from the ticket checkout. The production base is `daffe2cc`; the older attempt's
`db590445` has identical files in this plugin/core scope (`git diff --stat` is empty).
Extract the Python blocks below, in order, as `focused.py`, `corpus.py`, `delete.py`
under `$S`. The last script documents the mechanical edit; do not run it on already
deleted source. The inherited switch experiment is reproduced by the scripts in
`prior-attempt.md.gz`.

```sh
S="$PWD/orchestra/state/F01-fixtures-olmkirakira/recheck"
mkdir -p "$S"
export TMPDIR="$S" OLM_TEST_JOBS=1 OLM_PARALLEL_MAX=1
MAIN='/Users/onmk/Documents/Projects/Personal/OLM as'
# Prepare a disposable baseline snapshot, with read-only SDK symlinks.
mkdir -p "$S/base"
git archive daffe2cc mac core tools ucrtmath tests | tar -xf - -C "$S/base"
for n in Headers Util Resources; do ln -s "$MAIN/$n" "$S/base/$n"; done
git show daffe2cc:mac/OLMKiraKira/KiraAdmission.inc > "$S/admission-base.inc"
# focused.py reads this baseline text in each working root.
mkdir -p "$S/base/orchestra/state/F01-fixtures-olmkirakira"
cp "$S/admission-base.inc" "$S/base/orchestra/state/F01-fixtures-olmkirakira/admission-base.inc"
cp "$S/admission-base.inc" orchestra/state/F01-fixtures-olmkirakira/admission-base.inc
(
 cd "$S/base"
 python3 "$S/focused.py" --plugin olmkirakira --main "$MAIN" \
  --n 315 --seed 1001 --max-size 256 --jobs 1 --budget-minutes 30 \
  --case-timeout 20 --shrink-attempts 0 \
  --worker /Users/onmk/.cache/olm-emu/worker-F54c/aex-guest-worker \
  --scratch "$S/on" --report "$S/on.json" --corpus "$S/on-corpus"
) > "$S/on.log" 2>&1
python3 "$S/focused.py" --plugin olmkirakira --main "$MAIN" \
 --n 315 --seed 1001 --max-size 256 --jobs 1 --budget-minutes 30 \
 --case-timeout 20 --shrink-attempts 0 \
 --worker /Users/onmk/.cache/olm-emu/worker-F54c/aex-guest-worker \
 --scratch "$S/off" --report "$S/off.json" --corpus "$S/off-corpus" > "$S/off.log" 2>&1
# Expected each: Smart 315 exact/0 mismatch/0 uncompared; Classic 315 mismatch.
python3 tools/refactor/native_diff.py --plugin olmkirakira \
 --base daffe2cc --head HEAD --cases 3000 --seed 909 --arch both --build both \
 --jobs 1 --scratch "$S/G1" > "$S/G1.log" 2>&1
# Expected 12,012 comparisons; 11,712 exact, 300 identical refusals, no differences/errors.
python3 "$S/corpus.py" "$S/base" "$S/base-corpus" > "$S/base-corpus.log" 2>&1
python3 "$S/corpus.py" "$PWD" "$S/head-corpus" > "$S/head-corpus.log" 2>&1
cmp "$S/base-corpus/observations.jsonl" "$S/head-corpus/observations.jsonl"
# Expected identical 780 observations, SHA-256 771f0a77...c5d6 recorded above.
python3 mac/OLMKiraKira/tests/ui_compare.py --scratch "$S/ui" > "$S/ui.log" 2>&1
python3 mac/OLMKiraKira/tests/persistence.py --scratch "$S/persistence" > "$S/persistence.log" 2>&1
python3 tests/ui_oracle/compare_mac.py --scratch "$S/shared-ui" > "$S/shared-ui.log" 2>&1
PYTHONPATH=tests python3 -m unittest test_olmkirakira_generic_beta_lane_20260820
clang++ -std=c++17 tools/emulation/test_kirakira_mode3_nonwhitelist_geometry.cpp -o "$S/gaussian-test"
"$S/gaussian-test"
python3 -m unittest discover -s tests -p 'test_olmkirakira*' > "$S/tests.log" 2>&1
# Expected current environment: 142 tests, same 20 failures + 43 errors as evidence.
xcodebuild -project mac/OLMKiraKira/Mac/OLMKiraKira.xcodeproj \
 -target OLMKiraKira -configuration Release -jobs 1 'ARCHS=arm64 x86_64' \
 ONLY_ACTIVE_ARCH=NO CODE_SIGNING_ALLOWED=NO SYMROOT="$S/xcode/products" \
 OBJROOT="$S/xcode/objects" SHARED_PRECOMPS_DIR="$S/xcode/pch" \
 CLANG_MODULE_CACHE_PATH="$S/xcode/modules" \
 'WARNING_CFLAGS=-Wunused-variable -Wunused-but-set-variable -Wunused-function' \
 build > "$S/xcode.log" 2>&1
# Expected BUILD SUCCEEDED, both architectures, 334 warning lines.
```

The Gaussian blocker can be reproduced without editing production or assertions:
copy `core/kirakira_gaussian.h` into scratch, replace just its three literal OR
leaves with `return false;`, copy the existing C++ test into scratch and redirect
only its include to that header, compile, and execute with core dumps disabled.
Observed: assertion at line 11 (`mode3_gaussian_admitted(11, 6, 3)`), SIGABRT / -6.
The unmodified header/test executable exits 0. Log: `gaussian-off-test.log.gz`.

next:
- Review/merge the validated 32x18 subset independently if desired.
- Explicitly resolve the behavioural-test contract before removing the three Gaussian
  leaves. Their old oracle supplement also needs increasing from 6 to ≥20 per leaf.
- Keep the tuple map and 5x3 closure until missing general admissions are recovered.
- Existing historical test failures, release gate and packaging remain orchestrator work.

Reproduction generator:

```python
import os, collections, random, re, runpy, struct, sys
from pathlib import Path
from types import SimpleNamespace
ROOT = Path.cwd()
sys.path.insert(0, str(ROOT/'tools/fuzz'))
import adapters.olmkirakira as kk
from core import case_seed
SLOT = dict(channel=1, blur_mode=2, merge_mode=3, approximated_input=4, brightness_gain=5,
 strength_multiplier=6, fade_out=7, glow_opacity=8, source_opacity=9, vertical_length=10,
 vertical_use_ramp=13, horizontal_length=16, horizontal_use_ramp=19, diagonal_length=22,
 diagonal_use_ramp=25, diagonal2_length=28, diagonal2_use_ramp=31, highlight_radius=34,
 highlight_use_ramp=37, glow_rotation=40)
src = (ROOT/'orchestra/state/F01-fixtures-olmkirakira/admission-base.inc').read_text()
flags=[]
for name, body in re.findall(r'const bool (mode\w+) =\s*(.*?);',src,re.S):
 eq=collections.defaultdict(set)
 for f,v in re.findall(r'info\.(\w+) == (-?[\d.]+)',body): eq[f].add(float(v))
 expr=re.sub(r'!(?!=)', ' not ', body).replace('&&',' and ').replace('||',' or ')
 flags.append((name,eq,expr))
flags=[f for f in flags if f[0]=='mode3_horizontal']
tuple_body=re.search(r'static bool IsMode3Closure32x18Tuple.*?\n\{(.*?)\n\}',src,re.S)[1]
selected_fields={f:float(v) for f,v in re.findall(r'info\.(\w+) == (-?[\d.]+)',tuple_body)}
layout_body=re.search(r'static bool IsMode3Closure32x18Layout.*?\n\{(.*?)\n\}',src,re.S)[1]
selected_geometry=tuple(int(re.search(r'input->'+f+r' != (\d+)',layout_body)[1]) for f in ('width','height'))
base=kk.Adapter.generate
def generate(self,seed,index):
 rng=random.Random(case_seed(seed,index)^0xf01)
 name,eq,expr=flags[index%len(flags)]
 w,h=[(5,3),(32,18),(9,7)][(index//len(flags))%3]
 fields=dict(channel=1, approximated_input=0, brightness_gain=1, strength_multiplier=1,
 fade_out=0, glow_opacity=1, source_opacity=1, glow_rotation=0,
 **{k:0 for k in SLOT if k.endswith(('_length','_radius','_use_ramp'))})
 for attempt in range(10000):
  for f,vs in eq.items(): fields[f]=rng.choice(sorted(vs))
  for f in re.findall(r'(?<!!)info\.(\w+_use_ramp)',expr): fields[f]=rng.choice([0,1])
  if eval('('+expr+')',{'info':SimpleNamespace(**fields)}): break
 else: raise RuntimeError(name)
 w,h=selected_geometry
 fields.update(selected_fields)
 name='mode3-32x18'
 case=base(self,seed,index);params=self.defaults(w,h)
 for p in params:
  f=next((f for f,s in SLOT.items() if s==p['slot']),None)
  if f:
   v=fields[f]
   if f in ('strength_multiplier','glow_opacity','source_opacity'): v*=100
   if f=='glow_rotation': v/=65536
   p['value']=int(v) if p['kind'] in ('i','u','b') else v
  elif p['kind']=='c': p['value']=[255]*4
 depth=[8,16,32][(index//21)%3]; raw=bytearray()
 exact=index%4==0
 gradient='highlight' in name and 'declared' not in name
 for i in range(w*h):
  vals=[(i*15)%256 if gradient else (64+i*11)%256,
        0 if gradient else (i*15)%256,0 if gradient else (i*11)%256,0 if gradient else (i*7)%256]
  if depth==32:
   vals=[v/255 for v in vals] if exact else [1. if rng.random()<.85 else rng.random(),rng.random(),rng.random(),rng.random()]
   raw+=struct.pack('<4f',*vals)
  else:
   top=255 if depth==8 else 32768
   vals=[int(v*top/255+.5) for v in vals] if exact else [top if rng.random()<.85 else rng.randint(0,top),rng.randint(0,top),rng.randint(0,top),rng.randint(0,top)]
   raw+=struct.pack('<4B' if depth==8 else '<4H',*vals)
 case.update(geometry=[w,h],parameters=params,depth=depth,pixels=bytes(raw),profile='sdr',fixture=name)
 return case
kk.Adapter.generate=generate
sys.argv=[str(ROOT/'tools/fuzz/run.py')]+sys.argv[1:]
runpy.run_path(sys.argv[0],run_name='__main__')
```

```python
import sys,json,time,re,hashlib
from pathlib import Path
from types import SimpleNamespace
root=Path(sys.argv[1]).resolve();out=Path(sys.argv[2]).resolve();out.mkdir(parents=True,exist_ok=True)
sys.path.insert(0,str(root/'tools/fuzz'))
from adapters.olmkirakira import Adapter
from core import load_corpus
from geometry import require_host
main=Path('/Users/onmk/Documents/Projects/Personal/OLM as')
a=Adapter(SimpleNamespace(main=main,worker=Path('/unused'),max_size=256,case_timeout=180))
a.env.update(TMPDIR=str(out),OLM_PARALLEL_MAX='1')
a.binary,_=a.build(out,time.monotonic()+300)
with (out/'observations.jsonl').open('w') as f:
 for p in sorted((Path.cwd()/'tests/fuzz_corpus').rglob('*.json')):
  d=json.loads(p.read_text())
  if d.get('plugin')!='olmkirakira':continue
  a.max_size=d['max_size'];a.timeout=d.get('case_timeout_seconds',180)
  case,_=load_corpus(p,a);require_host(a,case)
  for route in a.routes:
   r,raw,tags=a.candidate(case,out,route,time.monotonic()+180)
   row=dict(path=str(p.relative_to(Path.cwd())),route=route,result=r,sha256=hashlib.sha256(raw).hexdigest(),tags=[re.sub(r'@\d+$','',x) for x in tags])
   f.write(json.dumps(row,sort_keys=True)+'\n');f.flush()
print('complete',flush=True)
```

```python
from pathlib import Path
p=Path('mac/OLMKiraKira/KiraAdmission.inc');s=p.read_text()
for name in ['IsMode3Closure32x18Tuple','IsMode3Closure32x18Layout']:
 start=s.index('static bool '+name+'('); end=s.index('\n}\n',start)+3
 s=s[:start]+s[end+1:]
s=s.replace('\t// These are the fixed public Classic fixtures closed against the current','\t// Retained: blanket OFF loses 169 Smart admissions in the F01 oracle campaign.\n\t// These are the fixed public Classic fixtures closed against the current')
p.write_text(s)
p=Path('mac/OLMKiraKira/OLMKiraKira.cpp');s=p.read_text()
start=s.index('\tconst bool mode3_32x18_closure =');end=s.index('\tconst bool exact_closure =',start)
s=s[:start]+s[end:];s=s.replace('(classic_closure || mode3_32x18_closure)','classic_closure')
for line in ['constexpr A_long kMode3SmartClosureWidth = 32;\n','constexpr A_long kMode3SmartClosureHeight = 18;\n']:s=s.replace(line,'')
start=s.index('\t\tconst bool pre_is_mode3_32x18 =');end=s.index('\t\tconst bool pre_is_generic_beta =',start)
s=s[:start]+s[end:];s=s.replace('(pre_is_classic || pre_is_mode3_32x18)','pre_is_classic')
s=s.replace(' pre_mode3_32=%d','').replace('(int)pre_is_classic, (int)pre_is_mode3_32x18,','(int)pre_is_classic,')
s=s.replace('(pre_is_classic && IsClassicClosureTuple(info)) ||\n\t\t\t\t(pre_is_mode3_32x18 && IsMode3Closure32x18Tuple(info))','pre_is_classic && IsClassicClosureTuple(info)')
p.write_text(s)
p=Path('tests/test_olmkirakira_generic_beta_lane_20260820.py');s=p.read_text();s=s.replace('        closure32 = self.function_body("IsMode3Closure32x18Tuple")\n        self.assertIn("info.horizontal_length == 50", closure32)\n','');p.write_text(s)
```
