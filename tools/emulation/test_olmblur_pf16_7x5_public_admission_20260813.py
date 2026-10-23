#!/usr/bin/env python3
"""Real-SDK source-included closure for the bounded PF16 7x5 public cell."""
from __future__ import annotations

from pathlib import Path as _HarnessPath
_UCRT_CXX = str(_HarnessPath(__file__).resolve().parents[2] / "tools/ucrt_cxx.py")

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tools.emulation.olm_assets import resolve_asset
import argparse,hashlib,json,subprocess,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
SOURCE=ROOT/'mac/OLMBlur/OLMBlur.cpp';WORKER=ROOT/'core/olmblur_worker16_nonlegacy.cpp'
PROBE=ROOT/'tools/emulation/probe_olmblur_pf16_7x5_public_admission_20260813.cpp'
OWNER=ROOT/'refs/conformance/olmblur_pf16_7x5_exported_public_owner_20260813.json'
REPORT=ROOT/'refs/conformance/olmblur_pf16_7x5_public_admission_20260813.json'
DOC=ROOT/'refs/conformance/olmblur_pf16_7x5_public_admission_20260813.md'
EXPECTED={'source':'22eb712a2485e080d811d2c064fe78bd521ee25434ece9a290a2d9b7b6e1fdd7','worker':'e0cec4230006c518514e4c730fa940fb935074a48e401d8e7f586b46b7b4266e','probe':'796a656e14838dac783611cf534c31c722068e2a17ebc663e0c3c078fb5ee1be','owner':'7d0374fc07cdeeee509a2db0d77ad96ad0d924a0d68fbeb464ad2cb769e4c4a6'}
SOURCE_SHA='5faee8f036157e787ab66a48553da63cc3d4b3bacd678c53ac12a9fe6ef0117b';OUTPUT_SHA='d644ed25b46352400797efce2abaa29c7a50c20ad44a7eac4a3618f774ed424a'
CLAIM='For the exact PF16 7x5 source, rowbytes 69, Amount 4, Smoothness 100, Repeat 1, Bias 1 and NonLegacy tuple only, current Mac public SmartRender is raw exact to the same-source Windows exported owner and preserves input, output headers, padding and guards. Enumerated one-away and lifecycle failures commit no output. No other source, tuple, geometry, depth, native AE or installed-binary behavior is promoted.'
def sha(p:Path)->str:return hashlib.sha256(p.read_bytes()).hexdigest()
def run()->str:
 if {k:sha(p) for k,p in [('source',SOURCE),('worker',WORKER),('probe',PROBE),('owner',OWNER)]}!=EXPECTED:raise RuntimeError('identity drift')
 with tempfile.TemporaryDirectory(prefix='olmblur-pf16-7x5-') as td:
  exe=Path(td)/'probe';sources=[PROBE,ROOT/'mac/OLMBlur/OLMBlur_Strings.cpp',*[ROOT/'core'/n for n in ('olmblur_helper.cpp','olmblur_fullworker_helper.cpp','olmblur_worker16_nonlegacy.cpp','olmblur_worker16_legacy.cpp','olmblur_worker32_nonlegacy.cpp','olmblur_worker32_legacy.cpp','olmblur_worker8_legacy.cpp','olmblur_worker_orchestration.cpp')],resolve_asset(ROOT/'Util/AEGP_SuiteHandler.cpp'),resolve_asset(ROOT/'Util/MissingSuiteError.cpp')]
  cmd=[_UCRT_CXX,'-std=c++17','-arch','arm64','-O2','-fno-fast-math','-ffp-contract=off','-DOLMBLUR_HOSTLESS_RENDER_HARNESS=1','-Wno-pragma-pack','-Wno-deprecated-declarations',*[x for d in ('Headers','Headers/SP','Util','Resources','core','mac/OLMBlur') for x in ('-I',str(ROOT/d))],*[str(x) for x in sources],'-framework','Cocoa','-o',str(exe)]
  subprocess.run(cmd,cwd=ROOT,check=True,capture_output=True);r=subprocess.run([str(exe)],cwd=ROOT,capture_output=True,text=True)
  if r.returncode or r.stderr:raise RuntimeError(f'probe rc={r.returncode} stderr={r.stderr!r}')
  return r.stdout
def build(stdout:str)->dict:
 lines=stdout.splitlines();positive=[x for x in lines if x.startswith('SMALL positive')];negative=[x for x in lines if x.startswith('SMALL ') and not x.startswith('SMALL positive')]
 if len(positive)!=2 or len(negative)!=62 or lines[-1]!='small_all_exact=1 positive=2 negative=62' or any('exact=0' in x for x in lines):raise RuntimeError('run contract')
 return {'schema':'olmblur.pf16-7x5-public-admission/1','status':'PASS_PF16_7X5_PUBLIC_RAW_EXACT_AND_62_FAIL_CLOSED',
  'identities':{'source':{'path':str(SOURCE.relative_to(ROOT)),'sha256':EXPECTED['source']},'worker':{'path':str(WORKER.relative_to(ROOT)),'sha256':EXPECTED['worker']},'probe':{'path':str(PROBE.relative_to(ROOT)),'sha256':EXPECTED['probe']},'windows_exported_owner':{'path':str(OWNER.relative_to(ROOT)),'sha256':EXPECTED['owner']}},
  'contract':{'geometry':[7,5],'depth':'PF16','rowbytes':69,'padding_per_row':13,'parameters':{'amount_f64':4.0,'smoothness_fixed':6553600,'repeat':1,'bias':1,'legacy':0},'active_source_sha256':SOURCE_SHA,'active_output_sha256':OUTPUT_SHA},
  'summary':{'positive_controls':2,'negative_controls':62,'all_exact':True},'run_sha256':hashlib.sha256(stdout.encode()).hexdigest(),'run_lines':lines,
  'gates':['real AE_Effect.h source-included SmartRender','optional pixel checkin present/null and never called','same-source Windows exported public owner','active output raw exact','13 input padding bytes copied only on success','input full storage and world header immutable','output world header and guards immutable','failure output full storage untouched','source first/middle/last mutation','parameter and world/layout one-aways','bidirectional partial overlap','five checkout and five checkin failure ordinals','suite/format/copy/allocation failures'],
  'claim_boundary':CLAIM,'claims_not_made':['PF8 or PF32 for this geometry','another PF16 source/tuple/layout','native Windows AE','native Mac AE','current installed binary','release gate']}
def validate(d:dict)->None:
 if set(d)!={'schema','status','identities','contract','summary','run_sha256','run_lines','gates','claim_boundary','claims_not_made'}:raise ValueError('top')
 if d['schema']!='olmblur.pf16-7x5-public-admission/1' or d['status']!='PASS_PF16_7X5_PUBLIC_RAW_EXACT_AND_62_FAIL_CLOSED' or d['claim_boundary']!=CLAIM:raise ValueError('authority')
 if d['summary']!={'positive_controls':2,'negative_controls':62,'all_exact':True}:raise ValueError('summary')
 if len(d['run_lines'])!=65 or sum(x.startswith('SMALL positive') for x in d['run_lines'])!=2 or sum(x.startswith('SMALL ') and not x.startswith('SMALL positive') for x in d['run_lines'])!=62:raise ValueError('rows')
 if hashlib.sha256(('\n'.join(d['run_lines'])+'\n').encode()).hexdigest()!=d['run_sha256']:raise ValueError('run digest')
 if d['contract']!={'geometry':[7,5],'depth':'PF16','rowbytes':69,'padding_per_row':13,'parameters':{'amount_f64':4.0,'smoothness_fixed':6553600,'repeat':1,'bias':1,'legacy':0},'active_source_sha256':SOURCE_SHA,'active_output_sha256':OUTPUT_SHA}:raise ValueError('contract')
 for key in EXPECTED:
  name={'owner':'windows_exported_owner'}.get(key,key)
  if d['identities'][name]['sha256']!=EXPECTED[key]:raise ValueError('identity')
 if d!=build('\n'.join(d['run_lines'])+'\n'):raise ValueError('recanonicalization')
def md(d:dict)->str:return f"# OLMBlur PF16 7x5 public admission\n\nStatus: **{d['status']}**\n\n- Positive controls: 2\n- Fail-closed controls: 62\n- Source: `{SOURCE_SHA}`\n- Output: `{OUTPUT_SHA}`\n\n{CLAIM}\n"
def main()->int:
 ap=argparse.ArgumentParser();ap.add_argument('--write',action='store_true');ap.add_argument('--validate-only',action='store_true');a=ap.parse_args();stdout=run();fresh=build(stdout);validate(fresh)
 if a.write:REPORT.write_text(json.dumps(fresh,indent=2,sort_keys=True)+'\n');DOC.write_text(md(fresh));print(fresh['status']);return 0
 saved=json.loads(REPORT.read_text());validate(saved)
 if saved!=fresh or DOC.read_text()!=md(saved):raise RuntimeError('saved drift')
 print(saved['status']);return 0
if __name__=='__main__':raise SystemExit(main())
