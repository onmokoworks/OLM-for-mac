#!/usr/bin/env python3
"""Same-source Windows exported Smart owner for the bounded PF16 7x5 cell."""
from __future__ import annotations

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tools.emulation.olm_assets import resolve_asset, asset_relative
import argparse, hashlib, json, sys, tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/emulation'))
import test_olmblur_exported_effectmain_chain_actual_aex_20260811 as public  # noqa:E402
from test_olmblur_case0006_border_order_writer_differential_20260716 import source_bytes,run_actual  # noqa:E402

REPORT=ROOT/'refs/conformance/olmblur_pf16_7x5_exported_public_owner_20260813.json'
DOC=ROOT/'refs/conformance/olmblur_pf16_7x5_exported_public_owner_20260813.md'
AEX=resolve_asset(ROOT/'plugins_2025/OLMBlur.aex')
SOURCE_GENERATOR=ROOT/'tools/emulation/test_olmblur_case0006_border_order_writer_differential_20260716.py'
PUBLIC_RUNNER=ROOT/'tools/emulation/test_olmblur_exported_effectmain_chain_actual_aex_20260811.py'
AEX_SHA='f0611785e7b14ac4fcfc75f23b8862beb4539eee52d25d472556849535e96e5b'
SOURCE_SHA='5faee8f036157e787ab66a48553da63cc3d4b3bacd678c53ac12a9fe6ef0117b'
OUTPUT_SHA='d644ed25b46352400797efce2abaa29c7a50c20ad44a7eac4a3618f774ed424a'

def sha(p:Path)->str:return hashlib.sha256(p.read_bytes()).hexdigest()

def live()->dict:
  if sha(AEX)!=AEX_SHA:raise RuntimeError('AEX drift')
  case={'kind':'border','width':7,'height':5,'blur_amount':4.0,'repeat':1,'bias_direction':1}
  source=source_bytes(7,5,'border');expected,worker_instructions=run_actual(case,source)
  if hashlib.sha256(source).hexdigest()!=SOURCE_SHA or hashlib.sha256(expected).hexdigest()!=OUTPUT_SHA:raise RuntimeError('fixture drift')
  with tempfile.TemporaryDirectory(prefix='olmblur-public7x5-') as td:
    root=Path(td);(root/'source.bin').write_bytes(source);(root/'expected.bin').write_bytes(expected)
    old=(public.WIDTH,public.HEIGHT,public.PADDING[16],public.FIXTURE)
    try:
      public.WIDTH=7;public.HEIGHT=5;public.PADDING[16]=13;public.FIXTURE=root
      row=public.run_row({'id':'pf16_7x5_amount4_repeat1_legacy0','depth':16,'legacy':0,
        'amount':4.0,'source':'source.bin','expected':'expected.bin','expected_sha256':OUTPUT_SHA})
    finally:public.WIDTH,public.HEIGHT,public.PADDING[16],public.FIXTURE=old
  return {'schema':'olmblur.pf16-7x5-exported-public-owner/1','status':'PASS_ACTUAL_EXPORTED_SMART_OWNER_PF16_7X5_RAW_EXACT',
    'identities':{'aex':{'path':str(asset_relative(AEX, ROOT)),'sha256':AEX_SHA},
      'source_generator':{'path':str(SOURCE_GENERATOR.relative_to(ROOT)),'sha256':sha(SOURCE_GENERATOR)},
      'public_runner':{'path':str(PUBLIC_RUNNER.relative_to(ROOT)),'sha256':sha(PUBLIC_RUNNER)}},
    'contract':{'geometry':[7,5],'depth':'PF16','rowbytes':69,'padding_per_row':13,
      'parameters':{'amount_f64':4.0,'smoothness_fixed':6553600,'repeat':1,'bias':1,'legacy':0},
      'active_source_sha256':SOURCE_SHA,'active_output_sha256':OUTPUT_SHA},
    'public_result':row,'worker_instructions':worker_instructions,
    'gates':{'commands':[23,24],'returns_zero':row['return_codes']==[0,0],
      'parameter_checkout_order':[1,2,3,4,5],'active_raw_exact':row['mismatched_bytes']==0,
      'padding_untouched':row['padding_mismatches']==0},
    'claim_boundary':'Actual Windows 2025 AEX exported SmartPreRender/SmartRender under the repository AexLoader/Unicorn, using the exact 7x5 PF16 source also admitted by Mac production. This is hostless public-owner numerical evidence, not native AE or arbitrary-source evidence.',
    'claims_not_made':['native Windows AE','native Mac AE','installed Mac binary','other source/tuple/geometry/depth','Windows world-header equivalence']}

def validate(d:dict)->None:
  if set(d)!={'schema','status','identities','contract','public_result','worker_instructions','gates','claim_boundary','claims_not_made'}:raise ValueError('top schema')
  if d['schema']!='olmblur.pf16-7x5-exported-public-owner/1' or d['status']!='PASS_ACTUAL_EXPORTED_SMART_OWNER_PF16_7X5_RAW_EXACT':raise ValueError('authority')
  if set(d['identities'])!={'aex','source_generator','public_runner'} or any(set(v)!={'path','sha256'} for v in d['identities'].values()):raise ValueError('identity schema')
  if d['identities']['aex']!={'path':'plugins_2025/OLMBlur.aex','sha256':AEX_SHA}:raise ValueError('aex')
  if d['identities']['source_generator']['sha256']!=sha(SOURCE_GENERATOR) or d['identities']['public_runner']['sha256']!=sha(PUBLIC_RUNNER):raise ValueError('runner identity')
  if d['contract']!={'geometry':[7,5],'depth':'PF16','rowbytes':69,'padding_per_row':13,
    'parameters':{'amount_f64':4.0,'smoothness_fixed':6553600,'repeat':1,'bias':1,'legacy':0},
    'active_source_sha256':SOURCE_SHA,'active_output_sha256':OUTPUT_SHA}:raise ValueError('contract')
  row=d['public_result']
  if row['active_sha256']!=OUTPUT_SHA or row['oracle_sha256']!=OUTPUT_SHA or row['mismatched_bytes'] or row['padding_mismatches'] or row['return_codes']!=[0,0] or row['parameter_checkout_order']!=[1,2,3,4,5]:raise ValueError('public result')
  if d['gates']!={'commands':[23,24],'returns_zero':True,'parameter_checkout_order':[1,2,3,4,5],'active_raw_exact':True,'padding_untouched':True}:raise ValueError('gates')
  if d!=live():raise ValueError('live recanonicalization drift')

def md(d:dict)->str:return f"""# OLMBlur PF16 7x5 exported public owner

Status: **{d['status']}**

The exact 7x5 PF16 source (`{SOURCE_SHA}`), Amount 4, Smoothness 100, Repeat 1,
Bias 1, NonLegacy tuple traverses the Windows exported SmartPreRender and
SmartRender entry points and produces `{OUTPUT_SHA}` with all active bytes exact
and 13 padding bytes per row untouched.

{d['claim_boundary']}
"""

def main()->int:
  ap=argparse.ArgumentParser();ap.add_argument('--write',action='store_true');ap.add_argument('--validate-only',action='store_true');a=ap.parse_args()
  fresh=live()
  if a.write:REPORT.write_text(json.dumps(fresh,indent=2,sort_keys=True)+'\n');DOC.write_text(md(fresh));print(fresh['status']);return 0
  saved=json.loads(REPORT.read_text());validate(saved)
  if saved!=fresh or DOC.read_text()!=md(saved):raise RuntimeError('saved drift')
  print(saved['status']);return 0
if __name__=='__main__':raise SystemExit(main())
