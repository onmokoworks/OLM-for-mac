#!/usr/bin/env python3
"""Read-only live closure for the bounded OLMBlur Smart public owner."""
from __future__ import annotations
import argparse, hashlib, json, subprocess, tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
SOURCE=ROOT/'mac/OLMBlur/OLMBlur.cpp'
PROBE=ROOT/'tools/emulation/probe_olmblur_smart_public_admission_20260813.cpp'
FIXTURE=ROOT/'tools/emulation/fixtures/olmblur_amount_repeat_legacy_matrix_20260810'
MANIFEST=FIXTURE/'manifest.json'
ACTUAL=ROOT/'refs/conformance/olmblur_exported_effectmain_chain_actual_aex_20260811.json'
REPORT=ROOT/'refs/conformance/olmblur_smart_public_admission_20260813.json'
DOC=ROOT/'refs/conformance/olmblur_smart_public_admission_20260813.md'
EXPECTED={'source':'22eb712a2485e080d811d2c064fe78bd521ee25434ece9a290a2d9b7b6e1fdd7','probe':'1023569bb8ca7e685b2a104d5c22e9b549138bd56d908c2e6bb853f29dd785c5','fixture':'01a5c8bc8d4269ae31ed918c6d1f3db6fcc26014800a6a06bba3c00dba012d5c','actual':'6cb3d704de6b99f0c30434969afa954b0f3d790b6b1b254302c55efa4e7a021f','run':'9bd82d62d1e41e28132565b7ce70136dface31c89a1bafd328d5a00b7b44b7b8'}
CLAIM=('For exactly six 24x24 active-byte fixtures (PF8/PF16/PF32 crossed with Legacy 0/1), '
       'the current Mac source-included public EffectMain is raw-exact to the retained Windows exported-owner '
       'oracles and fail-closes the enumerated Smart/SmartPre safety controls. Windows world headers and lifecycle '
       'remain probe-local synthetic evidence; no native AE, installed-binary, arbitrary-input, install, or release claim is made.')
TOP={'schema','status','identities','matrix','summary','run_sha256','run_lines','gates','claim_boundary','claims_not_made'}

def sha(p:Path)->str:return hashlib.sha256(p.read_bytes()).hexdigest()
def compile_run()->str:
  if {k:sha(p) for k,p in [('source',SOURCE),('probe',PROBE),('fixture',MANIFEST),('actual',ACTUAL)]}!={k:EXPECTED[k] for k in ('source','probe','fixture','actual')}:raise RuntimeError('identity drift')
  with tempfile.TemporaryDirectory(prefix='olmblur-smart-public-') as td:
    exe=Path(td)/'probe'
    sources=[PROBE,ROOT/'mac/OLMBlur/OLMBlur_Strings.cpp',*[ROOT/'core'/n for n in ('olmblur_helper.cpp','olmblur_fullworker_helper.cpp','olmblur_worker16_nonlegacy.cpp','olmblur_worker16_legacy.cpp','olmblur_worker32_nonlegacy.cpp','olmblur_worker32_legacy.cpp','olmblur_worker8_legacy.cpp','olmblur_worker_orchestration.cpp')],ROOT/'Util/AEGP_SuiteHandler.cpp',ROOT/'Util/MissingSuiteError.cpp']
    cmd=['clang++','-std=c++17','-arch','arm64','-O2','-fno-fast-math','-ffp-contract=off','-DOLMBLUR_HOSTLESS_RENDER_HARNESS=1','-Wno-pragma-pack','-Wno-deprecated-declarations',*[x for d in ('Headers','Headers/SP','Util','Resources','core','mac/OLMBlur') for x in ('-I',str(ROOT/d))],*[str(x) for x in sources],'-framework','Cocoa','-o',str(exe)]
    subprocess.run(cmd,cwd=ROOT,check=True,capture_output=True)
    run=subprocess.run([str(exe),str(FIXTURE)],cwd=ROOT,check=False,capture_output=True,text=True)
    if run.returncode or run.stderr:raise RuntimeError(f'probe failed rc={run.returncode} stderr={run.stderr!r}')
    return run.stdout

def build(stdout:str)->dict:
  lines=stdout.splitlines();pos=[x for x in lines if x.startswith('PF')];neg=[x for x in lines if x.startswith('NEG ')];prepos=[x for x in lines if x.startswith('PREPOS ')];preneg=[x for x in lines if x.startswith('PRENEG ')]
  if len(pos)!=12 or len(neg)!=91 or len(prepos)!=1 or len(preneg)!=9 or lines[-1]!='all_exact=1 positive_rows=12 negative_rows=91 pre_positive_rows=1 pre_negative_rows=9' or any('exact=0' in x or 'pass=0' in x for x in lines):raise RuntimeError('probe output contract failed')
  return {'schema':'olmblur.smart-public-admission/1','status':'PASS_HOSTLESS_BOUNDED_PUBLIC6_AND_SAFETY100','identities':{'source':{'path':str(SOURCE.relative_to(ROOT)),'sha256':EXPECTED['source']},'probe':{'path':str(PROBE.relative_to(ROOT)),'sha256':EXPECTED['probe']},'fixture_manifest':{'path':str(MANIFEST.relative_to(ROOT)),'sha256':EXPECTED['fixture']},'windows_exported_report':{'path':str(ACTUAL.relative_to(ROOT)),'sha256':EXPECTED['actual'],'role':'active numerical oracle; probe-local world/lifecycle only'}},'matrix':{'geometry':[24,24],'depths':[8,16,32],'legacy':[0,1],'rowbytes':{'PF8':113,'PF16':215,'PF32':416},'parameters':{'amount_f64':5.0,'smoothness_fixed':6553600,'repeat':1,'bias':1},'active_source_sha256':{'PF8':'572932cfa1c2c26b9bb6a6feaa4b9f3966ef0855e013ce3a86b139434a737adf','PF16':'bb4130a96cab14e0e5a6c186f81803ffc744608ac4dfd8d10ea9e97aaae7ce88','PF32':'9322e0b08c8623a892b4e75005c863a639bf604fe5882f4a6f12f46da18ce8ae'}},'summary':{'positive_controls':12,'numerical_cells':6,'smart_render_negatives':91,'smart_pre_positive':1,'smart_pre_negatives':9,'all_exact':True},'run_sha256':hashlib.sha256(stdout.encode()).hexdigest(),'run_lines':lines,'gates':['real AE_Effect.h ABI','optional pixel checkin present/null and never called','WorldSuite Acquire/Get2/Release','odd/misaligned host rows to aligned tight staging','PF_COPY exactly once on success','active output raw exact','input full storage/header/guards immutable','success input padding copied to output','failure output full storage/header/padding/guards untouched','parameter first-error checkout/checkin ownership','suite/callback PF_Err bad_alloc other exception mapping','SmartPre request exact and failure output byte-unchanged'],'claim_boundary':CLAIM,'claims_not_made':['native Windows AE lifecycle or world headers','native Mac AE','installed binary','arbitrary source or tuple','install','formal release gate']}

def validate(d:dict)->None:
  if set(d)!=TOP:raise ValueError('top schema')
  if d['schema']!='olmblur.smart-public-admission/1' or d['status']!='PASS_HOSTLESS_BOUNDED_PUBLIC6_AND_SAFETY100' or d['claim_boundary']!=CLAIM:raise ValueError('authority')
  if d['run_sha256']!=EXPECTED['run'] or hashlib.sha256(('\n'.join(d['run_lines'])+'\n').encode()).hexdigest()!=EXPECTED['run']:raise ValueError('run digest')
  if d['summary']!={'positive_controls':12,'numerical_cells':6,'smart_render_negatives':91,'smart_pre_positive':1,'smart_pre_negatives':9,'all_exact':True}:raise ValueError('summary')
  for key in ('source','probe','fixture_manifest','windows_exported_report'):
    expected=EXPECTED[{'fixture_manifest':'fixture','windows_exported_report':'actual'}.get(key,key)]
    if d['identities'][key]['sha256']!=expected:raise ValueError('identity')
  if len(d['run_lines'])!=114 or sum(x.startswith('PF') for x in d['run_lines'])!=12 or sum(x.startswith('NEG ') for x in d['run_lines'])!=91 or sum(x.startswith('PRENEG ') for x in d['run_lines'])!=9:raise ValueError('rows')
  if d!=build('\n'.join(d['run_lines'])+'\n'):raise ValueError('recanonicalized drift')

def md(d:dict)->str:return '# OLMBlur Smart public admission — hostless closure\n\n- Status: **'+d['status']+'**\n- Positive controls: 12 (6 numerical cells)\n- SmartRender negatives: 91\n- SmartPre controls: 1 positive + 9 negative\n- Production source: `'+d['identities']['source']['sha256']+'`\n\n'+d['claim_boundary']+'\n'
def main()->int:
  ap=argparse.ArgumentParser();ap.add_argument('--write',action='store_true');ap.add_argument('--validate-only',action='store_true');a=ap.parse_args()
  stdout=compile_run();fresh=build(stdout);validate(fresh)
  if a.write:
    REPORT.write_text(json.dumps(fresh,sort_keys=True,indent=2)+'\n');DOC.write_text(md(fresh));print('PASS wrote canonical closure');return 0
  saved=json.loads(REPORT.read_text());validate(saved)
  if fresh!=saved or DOC.read_text()!=md(saved):raise RuntimeError('saved drift')
  print('PASS read-only exact closure');return 0
if __name__=='__main__':raise SystemExit(main())
