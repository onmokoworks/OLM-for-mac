status: blocked
summary:
- Removed the redundant 3x2, 5x5 and 17x11 admissions: 13 depth/parameter families, 101 non-comment code lines.
- All 13 families have 24 ON/OFF original-AEX comparisons each, including an exact source-hash anchor per family; Smart 312/312 exact both ways.
- Full-HD fixtures remain: deleting them changes four real-SDK Smart refusals into successful renders.
- G2, Universal build, UI and 16 focused tests pass; the additional SDK lifecycle test fails identically before/after, so the strict all-gates-pass requirement is not met.
- This is a verified partial removal candidate, not completion of removal of all fixture paths.

facts:

Base: `a3c84860472bc593565d369b1cb889eddbf2c5e0`. No MAIN, other-plugin production, shared core, release gate or forbidden-action edits. No rejected tool calls. Read AGENT_GUIDE, fixture-removal/refactor specifications, GOTCHAS, compatibility plan and Smoother2 ledger rows.

Predicate inventory (source facts):

- **Fixture, removed:** PF32 3x2; Gamma 1.8 and 2.4 5x5 each at PF8/PF16/PF32; six 17x11 depth/parameter branches. The predicates combine literal size, stride, key, smoothing, version, gamma, palette and active-source SHA. Removed their now-unused `GammaPaletteRedKey`, `GammaTailZero` helpers and `pad` local by a script. No numerical arithmetic changed.
- **Fixture, retained:** `V2LegacyPF8Tuple` / `V2LegacyPF8ParamsIs` (12 full-HD tuples), PF16/PF32 full-HD case07, `V2Case07WorldContract`, and SmartRender's retained-fixture precedence. Their support helpers `ColorIs`, `SmoothingIs`, `V2SourceIs` and SHA include remain used. A one-line comment records the measured behavioral reason for retention.
- **General, retained:** `WorldDepth`, `CoreParamsPresent`, `ValidatePublicWorlds`, `V2GenericBetaAdmission`, `gamma_mode_and_count`, legal depths/parameter ranges, finite gamma and float-backed UI maximum, positive dimensions, stride/overflow/overlap checks, ROI and cleanup. Gamma lookup tables are numerical data, not fixture predicates. No exclusive core header needed changing.

The initial switch gated the V2SmartAdmission call. Preliminary `native_diff --base HEAD --head WORKTREE --cases 300 --jobs 1` produced 1,212 comparisons: 1,024 exact, 188 matching refusals, zero differences/new refusals/execution errors. After identifying the full-HD boundary, the switch was narrowed to the small-image branches. ON/OFF campaigns each produced Smart 312 exact / 0 mismatch / 0 uncompared and Classic 312 refusals. Scripted deletion repeated those counts. The source-hash anchor generator was then corrected for 17x11 typed rounding/premultiplication and both campaigns repeated; these final campaigns are the evidence below (all 13 anchors match their intended source SHA).

| Final campaign | Smart exact | Smart mismatch | Smart uncompared | Classic exact | Classic mismatch | Classic refusal |
|---|---:|---:|---:|---:|---:|---:|
| ON (baseline admission) | 312 | 0 | 0 | 0 | 0 | 312 |
| OFF (final deletion) | 312 | 0 | 0 | 0 | 0 | 312 |

Both original-AEX routes returned OK in all 312 cases per campaign. Mac Classic error 25 is a refusal, not pixel exactness. No first mismatch. The ordered input-hash-list digest (newline joined without final newline) is `3e68df52b081bb78dea69b6d7c8e47bfa39e49c7375d4b77a0523be4cddb1c92` both ways. First Smart output SHA: `b93f6cc6395f870bf7b241e2da62ad640e660602bfcb8fec525fe94b23cffa5c`.
AEX SHA: `7d42c00fe382304ea8a2b9d72af4f3a55f18b6fc03f6174786c97d7618b744c7`.
Worker: `/Users/onmk/.cache/olm-emu/worker-X01b-parity/aex-guest-worker`, SHA `34ce39821a53815dbd2252046cf375222d27a8045685fa6d946cfad211e40c4b`.

Per-family counts, **each of ON and OFF** (each row includes one pinned-source anchor and 23 independently generated opaque RGB sources):

| Family | Cases | Smart exact | Classic refusal |
|---|---:|---:|---:|
| 3x2 PF32 | 24 | 24 | 24 |
| 5x5 gamma1.8 PF8 | 24 | 24 | 24 |
| 5x5 gamma1.8 PF16 | 24 | 24 | 24 |
| 5x5 gamma1.8 PF32 | 24 | 24 | 24 |
| 5x5 gamma2.4 PF8 | 24 | 24 | 24 |
| 5x5 gamma2.4 PF16 | 24 | 24 | 24 |
| 5x5 gamma2.4 PF32 | 24 | 24 | 24 |
| 17x11 PF8 v1 no-key | 24 | 24 | 24 |
| 17x11 PF8 v2 inverted-key | 24 | 24 | 24 |
| 17x11 PF16 v2 no-key gamma-all | 24 | 24 | 24 |
| 17x11 PF16 v2 key gamma1.0 | 24 | 24 | 24 |
| 17x11 PF32 v1 no-key | 24 | 24 | 24 |
| 17x11 PF32 v2 key gamma2.4 | 24 | 24 | 24 |

Full-HD boundary (real SDK, original hash-pinned PF32 entry input): compiling `tools/emulation/olmsmoother2_case07_public_smart_harness_20260814.cpp` with the sole admission call enabled/disabled changes `input_flags_one`, `output_flags_one`, `origin_one`, `downsample_one` from error 516, no writes, to error 0, rendered output. First changed row: `input_flags_one`. Baseline's historical harness has 14/24 passing assertions; all-disabled has 10/24. Final code reproduces baseline's entire 24-row transcript byte for byte, including its pre-existing historical assertion failures. A preliminary 27-case oracle probe also covered each of the 12 full-HD PF8 literal tuples and both full-HD case07 depths once (flat opaque random sources): Smart 27 exact, Classic 27 refusals, no mismatch. This is not a 20-per-family deletion campaign; these full-HD families are deliberately retained.

G1: 12,012 comparisons (3,003 per arm64/reference, arm64/fast, x86_64/reference, x86_64/fast; 3,000 small cases + three 4K cases each), 10,216 exact outputs, 1,796 matching refusals, 0 differences, 0 new refusals, 0 execution errors. Each configuration: 2,554 exact and 449 matching refusals. No first mismatch or fatal error. Seed 909, pre-change base versus final production.

G2: all 112 recorded JSON cases in `tests/fuzz_corpus/olmsmoother2` (15) and `tests/fuzz_corpus/olmsmoother2_realistic_P02f` (97), loaded with the shared `load_corpus` verifier, original saved parameters/pixels/geometry/flags, Smart and Classic, arm64/x86_64, reference/fast. 896 comparisons, 448 exact Smart outputs, 448 identical Classic refusals, 0 differences, 0 new refusals, 0 execution errors. Native raw output hashes and refusal metadata/tags compared against the pre-change base; no oracle rerender used.

G4: Xcode Release Universal build succeeded (`ARCHS="arm64 x86_64"`, jobs 1). `tests/ui_oracle/compare_mac.py` restricted to its existing Smoother2 entry: 18 update witnesses, 36 checks including reload, 0 mismatches. Four focused unittest modules: 16 tests passed. Adding `tests.test_olmsmoother_real_sdk_suite_lifecycle_20260813` gives 18 tests, one error: `test_v2_world_and_color_suites` exits 3. Baseline and final lifecycle harnesses have identical stdout: all six WORLD rows pass, COLOR modes 0/4/5 fail because `calls=0` (OK expects 6; CALLBACK_ERROR expects 1; RELEASE_ERROR expects 6), `SUITE_LIFECYCLE_EXACT=0`. No behavior test was changed.

G5: arm64 real-SDK lifecycle harness compiled at O2 with `-Wunused-variable -Wunused-but-set-variable -Wunused-function`: baseline 8 warnings, final 8, identical warning classes/functions (polygon_scan `cx`; four histogram helpers; unpremul; writer-frame probe; composite). No fixture helper or local became unused. No warning fix outside this ticket was made.

Deleted source-contract assertions, explicitly permitted by FIXTURE_REMOVAL.md:
- `SourceContract.test_v2_every_fixed_source_is_pinned`
- `SourceContract.test_v2_tuple_to_digest_placement_is_exact`
- Their now-unused `V2_HASHES` and `V2_SOURCE_ORDER` tables.
Fixture digest generation, invalid-hash exclusion, all behavior tests and full-HD precedence assertions remain unchanged.

Non-comment/non-blank code lines (strip C/C++ comments, then count nonblank lines):

| File/group | Before | After |
|---|---:|---:|
| mac/OLMSmoother2/Mac/OLMSmoother2_admission.inc | 369 | 268 |
| mac/OLMSmoother2/Mac/OLMSmoother2_port.cpp | 600 | 600 |
| Other 16 existing plugin code files, including unchanged lookup tables | 10,971 | 10,971 |
| Total | 11,940 | 11,839 |

No added source file or numerical constant. Existing large LUT headers were not split or modified. Scratch stayed under 5 GiB; regenerable binaries/build trees removed after verification.

inference:

Small-image fixture admissions are redundant for the measured corpus and focused campaigns, including actual pinned-source anchors. Full-HD admissions are observably nonredundant as refusal guards, even though valid-source arithmetic uses the general renderer. Removing them would require a separately authorized behavioral change, not merely deleting source-text assertions. The lifecycle failure is pre-existing and does not result from admission deletion; strict G4 nevertheless cannot be reported green.

changed_files:

- `mac/OLMSmoother2/Mac/OLMSmoother2_admission.inc`
- `tests/test_olmsmoother_source_contract_20260813.py`
- `orchestra/reports/F01-fixtures-olmsmoother2.md`

verify:

Environment (all scratch under this worktree; MAIN assets are read-only):

```sh
export PY='/Users/onmk/Documents/Projects/Personal/OLM as/tools/emulation/.venv/bin/python3'
export S="$PWD/orchestra/state/F01-fixtures-olmsmoother2"
mkdir -p "$S"
export TMPDIR="$S" TMP="$S" TEMP="$S" PYTHONDONTWRITEBYTECODE=1
```

```sh
"$PY" tools/refactor/native_diff.py --plugin olmsmoother2 --base a3c84860472bc593565d369b1cb889eddbf2c5e0 --head WORKTREE --cases 3000 --jobs 1 --scratch "$S/g1" > "$S/g1.log" 2>&1
"$PY" -m unittest tests.test_olmsmoother_source_contract_20260813 tests.test_olmsmoother2_default_beta_lane_20260820 tests.test_olmsmoother2_roi_fullframe_contract_20260820 tests.test_olmsmoother2_gamma_colors_beta_20260820 > "$S/tests-focused.log" 2>&1
```
Expected: G1 zero differences/new refusals/execution errors; focused tests 16 passed. SDK-consuming commands require the read-only MAIN `Headers`, `Util`, `Resources` directories available under those relative names (temporary worktree symlinks were used, then removed).

The optional extra lifecycle unittest still fails; it must not be described as passing. Reproduce with `"$PY" -m unittest tests.test_olmsmoother_real_sdk_suite_lifecycle_20260813.RealSdkSuiteLifecycle.test_v2_world_and_color_suites`; expected one error / harness exit 3 on both base and final.

next:

Orchestrator may review the safe small-family deletion independently. Follow-up: resolve the pre-existing real-SDK color-suite lifecycle expectation without weakening behavior tests; separately decide whether full-HD source-dependent world-contract refusals must remain or should change. No all-fixtures-removed or AE-exact promotion is claimed.

Reproduction snippets follow (embedded instead of committing one-off tools).

Save as `$S/campaign.py`, then run the commands below. `FIXTURES=1` supplies the baseline admission include to the existing shared fuzz adapter at compile time; `FIXTURES=0` uses final production. This reproduces the final reinforced ON/OFF campaign without mutating production.

```python
import sys,re,random,struct,runpy,os,subprocess,hashlib
from pathlib import Path
ROOT=Path.cwd(); sys.path.insert(0,str(ROOT/'tools/fuzz'))
import adapters.olmsmoother2 as sm
from core import case_seed
src=subprocess.check_output(['git','show','a3c84860472bc593565d369b1cb889eddbf2c5e0:mac/OLMSmoother2/Mac/OLMSmoother2_admission.inc'],text=True)
constants={'GAMMA_NONE':1,'GAMMA_COLORS_ONLY':2,'GAMMA_ALL_COLORS':3,'SMOOTHER_V1':1,'SMOOTHER_V2':2}
slots={'enable_key':1,'invert_key':3,'version':7,'gamma_mode':8,'gamma_value':9}
colors={'SM_KEY_COLOR':2,**{'SM_GAMMA_COLOR_'+str(i):11+i for i in range(5)}}
def number(v): return constants[v] if v in constants else float(v) if '.' in v else int(v)
# Every terminal branch, with PF8 legacy tuples expanded separately.
families=[]
tuples=src.split('tuples[] = {')[1].split('};')[0]
for i,row in enumerate(re.findall(r'\{([^{}]+)\}',tuples)):
    ek,ik,ss,sr,es,ver,gm,gc,gv,pk=map(lambda x:number(x.strip()),row.split(','))
    values={1:ek,2:[255]*4,3:ik,4:ss,6:sr,5:es,7:ver,8:gm,9:gv,10:gc}
    values.update({11+j:[255,255 if pk==2 and j==0 else 0,0,255 if pk and j==4 else 0] for j in range(5)})
    families.append((f'hd-legacy-{i+1:02}',1920,1080,8,0,values))
body=src.split('// Case 07:')[1].split('// Public-beta lane')[0]
branches=body.split('return true;')[:-1]
for i,block in enumerate(branches):
    # Start at the terminal predicate (skip surrounding dimension-only blocks).
    block=block[block.rfind('\n\t\tif ('):] if '\n\t\tif (' in block else block[block.index('\n\tif ('):]
    values={1:0,2:[0]*4,3:0,4:100,5:0,6:1,7:2,8:1,9:2.4,10:0,**{11+j:[0]*4 for j in range(5)}}
    for field,slot in slots.items():
        m=re.search(r'\b'+field+r' == ([\w.]+)',block)
        if m: values[slot]=number(m[1])
    for param,args in re.findall(r'ColorIs\(params\[(\w+)\], ([\d, ]+)\)',block): values[colors[param]]=list(map(int,args.split(',')))
    ss,sr,es=map(int,re.search(r'SmoothingIs\(params, ([\d, ]+)\)',block)[1].split(','));values.update({4:ss,6:sr,5:es})
    m=re.search(r'SM_NUM_GAMMA_COLORS\]->u.sd.value == (\d+)',block)
    if m:values[10]=int(m[1])
    m=re.search(r'GammaPaletteRedKey\(params, ([\d, ]+)\)',block)
    if m:values.update({10:2,11:[255,255,0,0],12:[255,*map(int,m[1].split(','))]})
    depths=(16,32) if i==0 else (32,) if i==1 else (8,16,32) if i<4 else (int(re.search(r'depth == (\d+)',block)[1]),)
    for depth in depths:
        w,h=(1920,1080) if i==0 else (3,2) if i==1 else (5,5) if i<4 else (17,11)
        name=f'case07-pf{depth}' if i==0 else '3x2' if i==1 else f'5x5-gamma{values[9]}-pf{depth}' if i<4 else f'17x11-{i-4}-pf{depth}'
        families.append((name,w,h,depth,0 if i==0 else 12 if i==1 else {8:5,16:7,32:13}[depth],values.copy()))
families=[f for f in families if f[1]!=1920]
# 13 small families, 24 cases each. Family order supports quick one-per-family probes.
probe=(ROOT/'tools/emulation/probe_olmsmoother_source_contract_20260813.cpp').read_text()
rgb=[list(map(int,x.split(','))) for x in re.findall(r'\{([\d,]+)\}',probe.split('gamma18[25][3] = {')[1].split('};')[0])]
base=sm.Adapter.generate
print('FAMILIES',[(f[0],f[1:5]) for f in families],flush=True)
def generate(self,seed,index):
    name,w,h,depth,pad,v=families[index%len(families)]; repeat=index//len(families)
    rng=random.Random(case_seed(seed,index)); case=base(self,seed,index);values=v.copy()
    if w==5:
        values[7]=1+repeat%2; values[3]=(repeat//2)%2 if values[9]==1.8 else values[7]-1
    params=self.defaults(w,h)
    for p in params:p['value']=values[p['slot']]
    if w==1920:
        # Opaque flat images keep full-HD campaigns bounded; all literal controls preserved.
        vals=[255,*[rng.randrange(256) for _ in range(3)]]
        pack=lambda q:struct.pack('<4B',*q) if depth==8 else struct.pack('<4H',*((x*32768+128)//255 for x in q)) if depth==16 else struct.pack('<4f',*(x/255 for x in q))
        raw=pack(vals)*(w*h)
    else:
        raw=bytearray()
        for y in range(h):
            for x in range(w):
                i=y*w+x;q=[255,*[rng.randrange(256) for _ in range(3)]]
                if repeat==0 and w==5:q=[255,*(values[2][1:] if i==0 else rgb[i])]
                if repeat==0 and w==17:
                    u=(((x+1)*0x9e3779b9)^((y+3)*0x85ebca6b))&0xffffffff
                    u^=u>>16;u=(u*0x7feb352d)&0xffffffff;u^=u>>15
                    q=[(0,1,64,128,192,255)[(x+3*y)%6],u&255,(u>>8)&255,(u>>16)&255]
                    if i==0:q=[128,1,1,1]
                    if i==1:q=[192,255,0,0]
                if repeat==0 and w==3:
                    raw+=struct.pack('<4f',*( ((1,0,0,0),(1,0,1,1),(1,1,0,1),(1,1,1,0),(1,.25,.25,.25),(1,.75,.75,.75))[i] ));continue
                if repeat==0 and w==17:
                    premul=name in ('17x11-1-pf8','17x11-3-pf16','17x11-4-pf32')
                    if depth==8:
                        a=q[0]; raw+=struct.pack('<4B',a,*[((z*a+127)//255 if premul else z) for z in q[1:]])
                    elif depth==16:
                        a=(q[0]*32768+127)//255
                        cs=[(z*32768+127)//255 for z in q[1:]]
                        raw+=struct.pack('<4H',a,*[((z*a+16384)//32768 if premul else z) for z in cs])
                    else:
                        f32=lambda z:struct.unpack('<f',struct.pack('<f',z))[0]
                        a=f32(q[0]/255);cs=[f32(z/255) for z in q[1:]]
                        raw+=struct.pack('<4f',a,*[(f32(z*a) if premul else z) for z in cs])
                    continue
                raw+=struct.pack('<4B',*q) if depth==8 else struct.pack('<4H',*((z*32768+128)//255 for z in q)) if depth==16 else struct.pack('<4f',*(z/255 for z in q))
    case.update(depth=depth,geometry=[w,h],parameters=params,pixels=bytes(raw),profile='sdr',input_padding=pad,output_padding=pad,fixture=name)
    print('CASE',index,name,'source_pinned',hashlib.sha256(raw).hexdigest() in src,flush=True)
    return case
sm.Adapter.generate=generate
orig=sm.Adapter.compile
def compile(self,argv,deadline):
    if str(argv[0])=='clang++':
        if os.environ['FIXTURES']=='1':
            host=next(Path(str(x)) for x in argv if str(x).endswith('/host.cpp'))
            (host.parent/'OLMSmoother2_admission.inc').write_text(src)
        argv=[*argv,'-DOLM_SM2_FIXTURE_PATHS='+os.environ['FIXTURES']]
    return orig(self,argv,deadline)
sm.Adapter.compile=compile
sys.argv=[str(ROOT/'tools/fuzz/run.py'),*sys.argv[1:]];runpy.run_path(sys.argv[0],run_name='__main__')
```

```sh
for MODE in 1 0; do
FIXTURES="$MODE" "$PY" "$S/campaign.py" --plugin olmsmoother2 --n 312 --seed 101 --jobs 1 --budget-minutes 20 --case-timeout 30 --shrink-attempts 0 --worker /Users/onmk/.cache/olm-emu/worker-X01b-parity/aex-guest-worker --scratch "$S/anchors-$MODE" --report "$S/anchors-$MODE.json" --corpus "$S/anchors-$MODE-corpus" > "$S/anchors-$MODE.log" 2>&1
done
```

Save as `$S/corpus.py`:

```python
import sys,json,copy
from pathlib import Path
ROOT=Path.cwd();sys.path.insert(0,str(ROOT/'tools/refactor'))
import native_diff as nd
nd.__file__=__file__
def cases(adapter,count,seed):
    from core import load_corpus
    paths=sorted((ROOT/'tests/fuzz_corpus/olmsmoother2').rglob('*.json'))+sorted((ROOT/'tests/fuzz_corpus/olmsmoother2_realistic_P02f').rglob('*.json'))
    for index,path in enumerate(paths):
        saved=json.loads(path.read_text());adapter.max_size=saved['max_size']
        case,_=load_corpus(path,adapter)
        case.update(sequence_index=index,phase='corpus',size_sampler=saved.get('size_sampler','default'),corpus=str(path.relative_to(ROOT)))
        for route in ('smart','classic'):
            yield dict(case,corpus_route=route)
nd.cases=cases
original=nd.render
def render(adapter,case,directory,arch,timeout):
    old=adapter.candidate_command
    adapter.candidate_command=lambda c,d,r:old(c,d,case['corpus_route'])
    try:return original(adapter,case,directory,arch,timeout)
    finally:adapter.candidate_command=old
nd.render=render
if len(sys.argv)==3 and sys.argv[1]=='--worker':nd.worker(sys.argv[2])
else:sys.exit(nd.main())
```

```sh
"$PY" "$S/corpus.py" --plugin olmsmoother2 --base a3c84860472bc593565d369b1cb889eddbf2c5e0 --head WORKTREE --cases 112 --jobs 1 --scratch "$S/g2" > "$S/g2.log" 2>&1
xcodebuild -project mac/OLMSmoother2/Mac/OLMSmoother2.xcodeproj -configuration Release -jobs 1 ARCHS='arm64 x86_64' ONLY_ACTIVE_ARCH=NO CODE_SIGNING_ALLOWED=NO SYMROOT="$S/xcode-products" OBJROOT="$S/xcode-objects" DSTROOT="$S/xcode-dst" build > "$S/xcode.log" 2>&1
```

UI verification (the shared comparator has no plugin CLI filter):

```python
import sys
from pathlib import Path
sys.path.insert(0,str(Path.cwd()/'tests/ui_oracle'))
import compare_mac
compare_mac.PLUGINS={'Smoother2':compare_mac.PLUGINS['Smoother2']}
sys.argv=['compare_mac.py','--scratch','orchestra/state/F01-fixtures-olmsmoother2/ui']
compare_mac.main()
```

Full-HD boundary / warning reproduction in isolated scratch (no source mutation):

```python
from pathlib import Path
import subprocess
root=Path.cwd(); s=root/'orchestra/state/F01-fixtures-olmsmoother2'
base='a3c84860472bc593565d369b1cb889eddbf2c5e0'
for name in ('OLMSmoother2_port.cpp','OLMSmoother2_admission.inc'):
    (s/name).write_text(subprocess.check_output(['git','show',base+':mac/OLMSmoother2/Mac/'+name],text=True))
(s/'port-off.cpp').write_text((s/'OLMSmoother2_port.cpp').read_text().replace(
    'const bool retained_fixture = !err && V2SmartAdmission(',
    'const bool retained_fixture = false && !err && V2SmartAdmission('))
world=(root/'tools/emulation/olmsmoother2_case07_public_smart_harness_20260814.cpp').read_text()
for label,port in [('base',s/'OLMSmoother2_port.cpp'),('off',s/'port-off.cpp'),
                   ('final',root/'mac/OLMSmoother2/Mac/OLMSmoother2_port.cpp')]:
    (s/f'world-{label}.cpp').write_text(world.replace('../../mac/OLMSmoother2/Mac/OLMSmoother2_port.cpp',str(port)))
life=(root/'tools/emulation/probe_olmsmoother_real_sdk_suite_lifecycle_20260813.cpp').read_text()
(s/'lifecycle-base.cpp').write_text(life.replace('../../mac/OLMSmoother2/Mac/OLMSmoother2_port.cpp',str(s/'OLMSmoother2_port.cpp')))
```

```sh
for LABEL in base off final; do
"$PY" tools/ucrt_cxx.py -std=c++17 -arch arm64 -O2 -Wno-pragma-pack -Wno-deprecated-declarations -IHeaders -IHeaders/SP -IUtil -IResources -Imac/OLMSmoother2 -Imac/OLMSmoother2/Mac "$S/world-$LABEL.cpp" mac/OLMSmoother2/OLMSmoother2_Strings.cpp Util/AEGP_SuiteHandler.cpp Util/MissingSuiteError.cpp -lz -framework Cocoa -o "$S/world-$LABEL" > "$S/world-build-$LABEL.log" 2>&1
"$S/world-$LABEL" '/Users/onmk/Documents/Projects/Personal/OLM as/refs/conformance/fixtures/olmsmoother2_case07_pf32_entry_20260727/pf32_input_entry_argb.bin.gz' > "$S/world-$LABEL.log" 2>&1
done
diff -u "$S/world-base.log" "$S/world-final.log"
diff -u "$S/world-base.log" "$S/world-off.log"
```

Expected first diff empty, second diff exactly the four named rows plus summary 14/24 → 10/24; historical harness exit 4 in all three states. These are unchanged historical behavior assertions, not passing gate claims.

For warning and lifecycle comparison, compile `$S/lifecycle-base.cpp` and `tools/emulation/probe_olmsmoother_real_sdk_suite_lifecycle_20260813.cpp` separately with this same command, substituting `INPUT_CPP` and `OUTPUT_EXE`:

```sh
"$PY" tools/ucrt_cxx.py -std=c++17 -arch arm64 -O2 -Wno-pragma-pack -Wno-deprecated-declarations -Wunused-variable -Wunused-but-set-variable -Wunused-function -IHeaders -IHeaders/SP -IUtil -IResources -Imac/OLMSmoother2 -Imac/OLMSmoother2/Mac -DTEST_SMOOTHER_V2=1 "$INPUT_CPP" mac/OLMSmoother2/OLMSmoother2_Strings.cpp Util/AEGP_SuiteHandler.cpp Util/MissingSuiteError.cpp -framework Cocoa -o "$OUTPUT_EXE"
"$OUTPUT_EXE"
```

Expected 8 warnings and identical 13-line stdout ending `SUITE_LIFECYCLE_EXACT=0`, exit 3, in each build.
