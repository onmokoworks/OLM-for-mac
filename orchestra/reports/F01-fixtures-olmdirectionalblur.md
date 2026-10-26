status: done
summary:
- Removed eight fixture helpers, their dead world helper, fixed-tuple dispatch branches, and retained-neutral Smart/test-seam bypasses.
- Preserved source-bound Smart guards and two legacy exceptions; disabling all fixtures changed admission.
- Plugin C/C++/resource code, including its test seam, shrank from 2,722 to 2,119 non-comment/nonblank lines (603 removed).
- Focused final oracle: Smart 275 exact / 25 refusals / 0 uncompared / 0 mismatches, identical to ON.
- G1 passed 12,012 exact comparisons; G2, Universal build, UI and unused-warning checks passed.

facts:
- Base: `db59044515791af9890d0768c1fa4c7f5ad34034`. Switch experiment: `5b0b811e`. Removal: `454780ab`.
- Read `AGENT_GUIDE.md`, `orchestra/FIXTURE_REMOVAL.md`, `orchestra/REFACTOR_SPEC.md`, emulator GOTCHAS, the DirectionalBlur ledger rows, and the compatibility-plan plugin row. No ledger, release gate, other plugin, core arithmetic, or MAIN file was edited. No tool call was rejected.
- Source inventory regex `\b(?:width|height)\s*(?:==|!=)\s*\d+` counted 102 comparisons at base (admission 48, dispatch 54), rather than the ticket's approximate 90. Final count is 36 (34 + 2). This counts occurrences, not distinct predicates.
- Experiment set 19 named helpers and 24 local declarations false with `OLM_DIRECTIONAL_FIXTURE_PATHS=0`. The narrowed experiment restores source-bound guards and legacy exceptions. Final source has no experiment macro.
- Deletion used scratch Python scripts: balanced-brace function/call removal, Boolean constant propagation, then removal of deep legacy tails rendered unreachable by the neutral/feature partition. Removed unused `RetainedNeutralBackWorlds`. No algorithm, floating-point expression, core implementation, reference/fast split, or parallel limit changed.
- Initial random check: `native_diff.py --plugin olmdirectionalblur --base db59044515791af9890d0768c1fa4c7f5ad34034 --head WORKTREE --cases 300 --jobs 1 --scratch orchestra/state/F01-fixtures-olmdirectionalblur/random`: **1,212 exact, 0 differences, 0 refusals, 0 new refusals, 0 execution errors**, both architectures/builds, including 12 added 4K comparisons.
- Final G1: `native_diff.py --plugin olmdirectionalblur --base db59044515791af9890d0768c1fa4c7f5ad34034 --head WORKTREE --cases 3000 --jobs 1 --scratch orchestra/state/F01-fixtures-olmdirectionalblur/G1`: **12,012 exact, 0 differences, 0 refusals, 0 new refusals, 0 execution errors**. Each of arm64/reference, arm64/fast, x86_64/reference and x86_64/fast produced 3,003 exact comparisons. Coverage: 12,000 small and 12 4K; 4,004 comparisons per depth (8/16/32). First native mismatch: none. The first arm64/reference batch was additionally repeated against committed HEAD after whitespace/test-seam cleanup: **3,003 exact, 0 differences/new refusals/execution errors**, head `454780ab18a684d0a55afabb203553da9ac54341`, with an empty worktree diff. The other three original batches compiled the final production source.
- Committed-source G1 recheck command: `python3 tools/refactor/native_diff.py --plugin olmdirectionalblur --base db59044515791af9890d0768c1fa4c7f5ad34034 --head HEAD --cases 3000 --arch arm64 --build reference --jobs 1 --scratch orchestra/state/F01-fixtures-olmdirectionalblur/G1-final-arm64-reference`.
- G2: all 106 committed corpus JSON entries, loaded with recorded size/colour/geometry settings and input-hash validation, replayed through the shared native comparator on both architectures/builds: **424 exact, 0 differences, 0 refusals, 0 new refusals, 0 execution errors**. This compares Mac output hashes, error/status and normalized refusal tags; no oracle diagnostic comparison is claimed.
- G4: `python3 tools/fuzz/build_F47_bundles.py --plugins OLMDirectionalBlur --scratch orchestra/state/F01-fixtures-olmdirectionalblur/xcode` passed; `lipo` reported `x86_64 arm64`.
- Test-seam build: `TMPDIR="$PWD/orchestra/state/F01-fixtures-olmdirectionalblur" clang++ -std=c++17 -fsyntax-only -DOLM_DBLUR_TEST_SEAM=1 -Wno-deprecated-declarations -Wno-pragma-pack -IHeaders -IHeaders/SP -IUtil -IResources mac/OLMDirectionalBlur/OLMDirectionalBlur.cpp` exited 0.
- UI: `tests/ui_oracle/compare_mac.py`, restricted by its `PLUGINS` mapping to DirectionalBlur, passed 3 updates / 6 checks including reload / 0 mismatches. `tests/test_olmdirectionalblur_update_params_ui_20260810.py` passed its 1 test, including actual-AEX cases 0..4 and production-source assertions. Only the harness/report destination was redirected into scratch, avoiding writes to `refs/conformance`; assertions were unchanged.
- Regenerable Xcode products and experiment source snapshots were deleted; shared gate/campaign runners cleaned their build directories. No background worker remains. Scratch logs/reports/corpora total 49 MiB, below the 5 GiB limit.
- G5: syntax-only compilation of base/final with `-Wunused-variable -Wunused-but-set-variable -Wunused-function` on arm64 and x86_64: 0 warnings and exit 0 in all four runs. `git diff --check` passed.
- AEX: `/Users/onmk/Documents/Projects/Personal/OLM as/plugins_2025/OLMDirectionalBlur.aex`, SHA-256 `d3e5e4079a759d521dc7457ebf998487fe43b00f182a1e2f910b187936b6c06e`.
- Oracle worker: `/Users/onmk/.cache/olm-emu/worker-F54c/aex-guest-worker`, SHA-256 `3d5eec0c6792f176a9cfbc38093c53b852f4ea1baae2cfd313345c02f55d6fba`; no worker rebuild.

Predicate inventory (fixture versus general):

| Class | Predicates / disposition |
|---|---|
| Fixture helpers removed | `NoiseCoefficientHigherOrderTuple`, `NoisePublicPairwiseTuple`, `IsRetainedNeutralBackExact8`, `IsRetainedNeutralBackExact16`, `IsRetainedNeutralBackExact32`, `IsRetainedNeutralDualExact16`, `IsRetainedNeutralBackExact`, `IsRetainedNeutralExact` |
| Fixture locals removed | `size_front_combo_exact`, `size_back_combo_exact`; deep `front_only_exact`, `back_family_exact`, `pf16_fade_sharp_family_exact`, `pf16_size_variation_exact`, `pf16_size_fade_cross_exact`, `pf16_size_sharp_cross_exact`, `pf16_size_back_cross_exact`, `pf16_noise_size_exact`, `front_alpha_fade_exact`, `front_fade_size_combination_exact`, `size_noise_type1_combination_exact`, `fade_noise_type1_combination_exact`, `sharp_back_family_exact`, `pf32_noise_size_exact`, `pf32_size_coeff_cross_exact`; dependent `retained_exact`, `noise_public_pairwise_exact`, `noise_coefficient_higher_order_exact`, deep `dual_side_higher_order_exact`, deep `noise_type2_natural64_exact`, `pf16_full_exact`, and both `minimal_exact` tails |
| Fixture helpers retained | `DualSideHigherOrderTuple`, `NoiseType2Natural64Tuple`, `Natural64RowbytesSafe`, `Natural64SourceExact`, `PublicType3Layer16Tuple`, `PublicDualSideType2_32x18Tuple`, `ExactExtent16`, `ExactExtent32x18`, `PublicType3Layer16WorldsExact`, `PublicDualSideType2WorldsExact`, `PublicDualSideExportedSmartExact`, with their geometry/source guard locals and PF8 kernel selection |
| Legacy fixture exceptions retained | `legacy_size_sharp_exact` (960×540, half scale: oracle did not finish consistently); `legacy_mode2_adapter_exact` (connected Layer: no equivalent general PF8 fallback proven) |
| General predicates retained | `PayloadSpan`, `DisjointPayloads`; neutral/feature shapes; `GenericEffectiveStrengths`; `CanUseGenericNeutral8`; `IsGenericNeutralDeepParameters`; `GenericDeepWorldsSafe`; feature estimate/world safety; finite-input and Layer coefficient bounds; `CanUsePF8FeatureFallback`; `GenericDeepLayerWorldSafe`; size/front/back overlap checks; zero-strength/fade copy; invalid-depth default-no-op rejection; host geometry/origin/row-stride/checkout/resource checks |
| General helper deleted as unused | `RetainedNeutralBackWorlds` took arbitrary dimensions, but only the removed retained-fixture helpers called it |

The plugin-only `core/dblur*.h` scan found no corresponding fixed-dimension/Tuple/Fixture/Retained predicates; core headers are unchanged. No new named arithmetic constants were needed.

Oracle campaigns (300 cases each, seed 5101, jobs 1):

| Campaign | Smart exact | Smart refusal | Smart uncompared | Smart mismatch | Classic exact | Classic refusal | Classic uncompared | Classic mismatch |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Initial all-fixture ON | 272 | 22 | 6 | 0 | 0 | 32 | 0 | 268 |
| Initial all-fixture OFF | 285 | 10 | 5 | 0 | 0 | 20 | 0 | 280 |
| Retained-guard ON | 275 | 25 | 0 | 0 | 0 | 25 | 0 | 275 |
| Retained-guard OFF | 275 | 25 | 0 | 0 | 0 | 25 | 0 | 275 |
| Final code OFF | 275 | 25 | 0 | 0 | 0 | 25 | 0 | 275 |
| Reproduction driver ON, switch commit | 275 | 25 | 0 | 0 | 0 | 25 | 0 | 275 |

- Initial ON/OFF had identical input hashes and parameters for all 300 cases. First admission delta: case 8, `PublicDualSideType2_32x18Tuple` parameter family, 16×16 PF32: ON error 516/refusal; OFF error 0/exact, native SHA-256 `53fb43d8a0e896b6cd4f89fb3e69b19315b912c0cf292f5558c6ae8c78f02145`. Thus blanket removal is not a behaviour-preserving refactor.
- Initial uncompared outcomes were oracle budgets. The narrowed campaign retains the unverified 960×540 exception and samples the remaining 29 literal-condition groups at sizes up to 64. It does not claim source-hash fixture or connected-Layer coverage. Conditions are sampled from literal equalities/early-reject inequalities, following the supplied RadialBlur generator; arbitrary combinations may fall outside individual disjunctions. Sources use 80% opaque-alpha probability per pixel. The retained source checks deliberately reject some candidates.
- Narrowed ON versus final OFF has **0 native hash/status changes on Smart and 0 on Classic**. First Smart mismatch: none. First Classic mismatch in both: case 0, 16×16 PF16, byte/word 0, expected word bytes `0000`, actual `7b62`, 2,032 different bytes / 1,024 different words out of 2,048 bytes. Classic remains outside this SmartFX contract.

Code size (strip C/C++ line/block comments, count nonblank lines; `.cpp/.h/.inc/.r`, including test seam):

| File | Physical before → after | Code before → after |
|---|---:|---:|
| `mac/OLMDirectionalBlur/OLMDirectionalBlur_admission.inc` | 865 → 658 | 794 → 589 |
| `mac/OLMDirectionalBlur/OLMDirectionalBlur_dispatch.inc` | 563 → 169 | 527 → 133 |
| `mac/OLMDirectionalBlur/OLMDirectionalBlur_host.inc` | 521 → 519 | 477 → 474 |
| `mac/OLMDirectionalBlur/tests/TestEntry.inc` | 209 → 208 | 192 → 191 |
| All plugin source/resource files | — | **2,722 → 2,119** |

Largest resulting plugin source is the admission include at 658 physical lines. Main `.cpp`, arithmetic kernels, UI, and all core headers are unchanged.

inference:
- The general renderers cover the removed admission families. Once the retained-neutral bypass is false, non-copy deep work partitions exhaustively into neutral or feature shapes, both of which return before the old fixed-tuple tails. This is why those arithmetic call sites could be deleted without rewriting any arithmetic.
- The source-bound predicates are observable admission policy, even where the underlying general renderer can produce exact pixels. Removing them needs a separate behavioural/admission change, not a zero-difference refactor.
- The measured campaigns are bounded evidence, not a claim of new native AE conformance or universal parameter coverage.

changed_files:
- `mac/OLMDirectionalBlur/OLMDirectionalBlur_admission.inc`
- `mac/OLMDirectionalBlur/OLMDirectionalBlur_dispatch.inc`
- `mac/OLMDirectionalBlur/OLMDirectionalBlur_host.inc`
- `mac/OLMDirectionalBlur/tests/TestEntry.inc`
- `orchestra/reports/F01-fixtures-olmdirectionalblur.md`

verify:
Run from this worktree. MAIN is read-only. Extract the two embedded drivers below into ticket scratch (they wrap existing shared tools; no standalone one-off tool is added to the repository).

```sh
STATE="$PWD/orchestra/state/F01-fixtures-olmdirectionalblur/recheck"
MAIN='/Users/onmk/Documents/Projects/Personal/OLM as'
PY="$MAIN/tools/emulation/.venv/bin/python3"
mkdir -p "$STATE"
export TMPDIR="$STATE" OLM_TEST_JOBS=1 PYTHONDONTWRITEBYTECODE=1 F01_STATE="$STATE"
python3 - <<'PY'
import os,re
from pathlib import Path
text=Path('orchestra/reports/F01-fixtures-olmdirectionalblur.md').read_text()
for name,marker in [('campaign.py','F01_ORACLE_DRIVER'),('replay.py','F01_CORPUS_DRIVER')]:
    body=next(b for b in re.findall(r'```python\n(.*?)\n```',text,re.S) if b.startswith('# '+marker))
    (Path(os.environ['F01_STATE'])/name).write_text(body+'\n')
PY
python3 tools/refactor/native_diff.py --plugin olmdirectionalblur --base db59044515791af9890d0768c1fa4c7f5ad34034 --head HEAD --cases 3000 --seed 909 --arch both --build both --jobs 1 --scratch "$STATE/G1" > "$STATE/G1.log" 2>&1
python3 "$STATE/replay.py" --plugin olmdirectionalblur --base db59044515791af9890d0768c1fa4c7f5ad34034 --head HEAD --cases 106 --arch both --build both --jobs 1 --scratch "$STATE/G2" > "$STATE/G2.log" 2>&1
for mode in 1 0; do
  FIXTURE_ON="$mode" F01_SOURCE_REV=5b0b811e "$PY" "$STATE/campaign.py" --plugin olmdirectionalblur --n 300 --seed 5101 --jobs 1 --budget-minutes 30 --case-timeout 30 --shrink-attempts 0 --worker /Users/onmk/.cache/olm-emu/worker-F54c/aex-guest-worker --scratch "$STATE/oracle-$mode" --report "$STATE/oracle-$mode.json" --corpus "$STATE/corpus-$mode" > "$STATE/oracle-$mode.log" 2>&1
done
FIXTURE_ON=0 "$PY" "$STATE/campaign.py" --plugin olmdirectionalblur --n 300 --seed 5101 --jobs 1 --budget-minutes 30 --case-timeout 30 --shrink-attempts 0 --worker /Users/onmk/.cache/olm-emu/worker-F54c/aex-guest-worker --scratch "$STATE/final" --report "$STATE/final.json" --corpus "$STATE/corpus-final" > "$STATE/final.log" 2>&1
python3 tools/fuzz/build_F47_bundles.py --plugins OLMDirectionalBlur --scratch "$STATE/xcode" > "$STATE/xcode.log" 2>&1
python3 - <<'PY' > "$STATE/UI.log" 2>&1
import importlib.util,os,sys
spec=importlib.util.spec_from_file_location('ui','tests/ui_oracle/compare_mac.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
m.PLUGINS={'DirectionalBlur':m.PLUGINS['DirectionalBlur']}
sys.argv=['compare_mac.py','--scratch',os.environ['F01_STATE']+'/UI'];m.main()
PY
```

To repeat the initial blanket-switch diagnostic, add `F01_ALL=1` to the two switch-commit oracle invocations, use distinct scratch/report/corpus paths, and set `--case-timeout 20`. This restores the 960×540 group and switches the retained guards off too; its budget counts can vary.

Expected G1: 12,012 exact comparisons, 0 differences/new refusals/execution errors. Expected G2: 424 exact with the same zero counters. Each oracle campaign: Smart 275 exact / 25 refusals, Classic 275 mismatches / 25 refusals, no uncompared. Build: both architectures. UI: six checks, zero mismatches. Runtime budget outcomes are environmental; do not treat an incomplete campaign as a pass.

```python
# F01_ORACLE_DRIVER
import sys,random,struct,json,runpy,os,re,subprocess
sys.dont_write_bytecode=True
from pathlib import Path
ROOT=Path.cwd(); S=Path(os.environ.get('F01_STATE',str(ROOT/'orchestra/state/F01-fixtures-olmdirectionalblur/recheck')));S.mkdir(parents=True,exist_ok=True)
sys.path.insert(0,str(ROOT/'tools/fuzz'))
import adapters.olmdirectionalblur as db
from core import case_seed
SLOT=dict(angle_deg=1,brightness_gain=2,size_variation=3,front_strength=5,front_alpha_fade=6,front_sharp_tail=7,back_strength=10,back_alpha_fade=11,back_sharp_tail=12,noise_variation=15,noise_type=16,seed=18,noise_offset=19,thickness=20)
flags=[]
for suffix in ('admission','dispatch'):
 source=subprocess.check_output(['git','show','db59044515791af9890d0768c1fa4c7f5ad34034:mac/OLMDirectionalBlur/OLMDirectionalBlur_'+suffix+'.inc'],text=True)
 groups=[]
 for m in re.finditer(r'const bool (\w+) =(.*?);',source,re.S):
  if re.search(r'(?:width|height) == \d+',m[2]) or m[1] in ('front_only_exact','back_family_exact','front_alpha_fade_exact'):groups.append((m[1],m[2]))
 for m in re.finditer(r'static bool (\w+)\([^{}]+\)\n\{',source):
  if not any(k in m[1] for k in ('Tuple','Natural64','ExactExtent','WorldsExact','ExportedSmartExact','IsRetained')):continue
  i=m.end();j=i;level=1
  while level:level+=(source[j]=='{')-(source[j]=='}');j+=1
  groups.append((m[1],source[i:j-1]))
 for name,body in groups:
  eq={}
  for k,v in re.findall(r'info\.(\w+) (?:==|!=) (-?\d+(?:\.\d+)?)',body):eq.setdefault(k,[]).append(float(v))
  sizes=[(int(w),int(h)) for w,h in re.findall(r'(?:width|width\(\)) (?:==|!=) (\d+) && (?:input->)?height (?:==|!=) (\d+)',body)] or [(16,16)]
  if eq and (os.environ.get('F01_ALL') or all(w<=64 for w,h in sizes)):flags.append((name,eq,sizes))
if os.environ.get('F01_DRY'):
 print(json.dumps(flags));raise SystemExit
if rev:=os.environ.get('F01_SOURCE_REV'):
 sys.path.insert(0,str(ROOT/'tools/refactor'));from native_diff import snapshot
 source_root=S/(('source-all-' if os.environ.get('F01_ALL') else 'source-')+rev[:8])
 if not source_root.exists():
  snapshot(rev,source_root)
  if os.environ.get('F01_ALL'):
   for suffix in ('admission','dispatch'):
    p=source_root/'mac/OLMDirectionalBlur'/('OLMDirectionalBlur_'+suffix+'.inc');text=p.read_text()
    if suffix=='admission':
     def guard(m):
      if any(k in m[1] for k in ('Tuple','Natural64','ExactExtent','WorldsExact','ExportedSmartExact','IsRetained')) and not text[m.end():].startswith('\n\tif (!OLM_DIRECTIONAL_FIXTURE_PATHS)'):return m[0]+'\n\tif (!OLM_DIRECTIONAL_FIXTURE_PATHS) return false;'
      return m[0]
     text=re.sub(r'static bool (\w+)\([^{}]+\)\n\{',guard,text)
    def local(m):
     if 'OLM_DIRECTIONAL_FIXTURE_PATHS' not in m[2] and (re.search(r'(?:width|height) == \d+',m[2]) or m[1] in ('front_only_exact','back_family_exact','front_alpha_fade_exact')):return 'const bool '+m[1]+' = OLM_DIRECTIONAL_FIXTURE_PATHS && ('+m[2]+');'
     return m[0]
    text=re.sub(r'const bool (\w+) =(.*?);',local,text,flags=re.S);p.write_text(text)
 db.SOURCE=source_root/'mac/OLMDirectionalBlur/OLMDirectionalBlur.cpp'
old=db.Adapter.generate; compile=db.Adapter.compile
def build(self,argv,deadline):
 if str(argv[0])=='clang++':argv=[*argv,'-DOLM_DIRECTIONAL_FIXTURE_PATHS='+os.environ['FIXTURE_ON']]
 return compile(self,argv,deadline)
def generate(self,seed,index):
 rng=random.Random(case_seed(seed,index)^0x5eed)
 name,eq,sizes=flags[index%len(flags)];w,h=rng.choice(sizes)
 case=old(self,seed,index);params=self.defaults(w,h)
 for f,vals in eq.items():
  if f in SLOT:
   p=next(p for p in params if p['slot']==SLOT[f]);v=rng.choice(sorted(set(vals)));p['value']=int(v) if p['kind'] in ('i','u','b') else v
 raw=bytearray();depth=case['depth']
 for _ in range(w*h):
  if depth==32:raw+=struct.pack('<4f',1.0 if rng.random()<.8 else rng.random(),rng.random(),rng.random(),rng.random())
  else:
   top=255 if depth==8 else 32768
   raw+=struct.pack('<4B' if depth==8 else '<4H',top if rng.random()<.8 else rng.randint(0,top),*[rng.randint(0,top) for _ in range(3)])
 case.update(geometry=[w,h],parameters=params,pixels=bytes(raw),profile='sdr',fixture=name)
 return case
db.Adapter.generate=generate;db.Adapter.compile=build
sys.argv=[str(ROOT/'tools/fuzz/run.py'),*sys.argv[1:]]
runpy.run_path(sys.argv[0],run_name='__main__')
```

```python
# F01_CORPUS_DRIVER
import sys,json,importlib.util
from pathlib import Path
ROOT=Path.cwd();spec=importlib.util.spec_from_file_location('native_diff',ROOT/'tools/refactor/native_diff.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
def cases(adapter,count,seed):
 from core import load_corpus
 for i,p in enumerate(sorted((ROOT/'tests/fuzz_corpus/olmdirectionalblur').rglob('*.json'))):
  data=json.loads(p.read_text());adapter.max_size=data['max_size'];case,_=load_corpus(p,adapter)
  case.update(phase='corpus',sequence_index=i,corpus=str(p.relative_to(ROOT)),size_sampler=data.get('size_sampler','default'))
  yield case
m.cases=cases
sys.exit(m.main())
```

Additional G4 source-unit and G5 warning rechecks (same assertions, scratch-only report destination):

```sh
"$PY" - <<'PYCODE' > "$STATE/UI-unit.log" 2>&1
import importlib.util,os,unittest
from pathlib import Path
state=Path(os.environ['F01_STATE']);root=Path.cwd()
launcher=state/'ui_actual.py'
launcher.write_text("import sys\nfrom pathlib import Path\nsys.path.insert(0,"+repr(str(root/'tools/emulation'))+")\nimport test_olmdirectionalblur_update_params_ui_actual_aex_20260810 as p\np.REPORT=Path("+repr(str(state/'ui-actual.json'))+")\nraise SystemExit(p.main())\n")
spec=importlib.util.spec_from_file_location('unit','tests/test_olmdirectionalblur_update_params_ui_20260810.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
m.HARNESS=launcher;m.REPORT=state/'ui-actual.json'
r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(m))
raise SystemExit(not r.wasSuccessful())
PYCODE
python3 - <<'PYCODE' > "$STATE/warnings.log" 2>&1
import os,subprocess,sys
from pathlib import Path
sys.path.insert(0,'tools/refactor');from native_diff import snapshot
state=Path(os.environ['F01_STATE']);base=state/'warning-base'
if not base.exists():snapshot('db59044515791af9890d0768c1fa4c7f5ad34034',base)
main=Path('/Users/onmk/Documents/Projects/Personal/OLM as')
for arch in ('arm64','x86_64'):
    for label,root in [('base',base),('head',Path.cwd())]:
        command=['clang++','-std=c++17','-arch',arch,'-fsyntax-only','-Wunused-variable','-Wunused-but-set-variable','-Wunused-function','-Wno-deprecated-declarations','-Wno-pragma-pack',*[x for d in ('Headers','Headers/SP','Util','Resources') for x in ('-I',str(main/d))],str(root/'mac/OLMDirectionalBlur/OLMDirectionalBlur.cpp')]
        r=subprocess.run(command,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
        (state/f'warnings-{label}-{arch}.log').write_text(r.stdout)
        print(label,arch,r.returncode,r.stdout.count('warning:'))
        assert r.returncode==0 and r.stdout.count('warning:')==0
PYCODE
```

Expected: one UI unit test passes; all four warning builds exit 0 with 0 warnings.

next:
- Follow-up admission-policy ticket for dual-side / Type-3 Layer / natural64 source restrictions, with explicit source-hash and independent Layer fixtures.
- Obtain a completed half-scale 960×540 legacy oracle witness before considering that exception for removal.
- No new AE-exact claim or release-gate change is requested.
