#!/usr/bin/env python3
"""One-shot fresh AE smoke for the installed four-plugin batch checkpoint."""

from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
import sys
import tempfile
from pathlib import Path
from typing import Any


ROOT=Path(__file__).resolve().parents[1]
THIS=Path(__file__).resolve()
BASE=ROOT/'scripts/run_olm_all10_post_toondilate_ded9_corrected_v2_20260813.py'
PAYLOAD=ROOT/'scripts/ae_host_all10_post_toondilate_ded9_corrected_v2_20260813.jsx'
CONTRACT_REPORT=ROOT/'refs/conformance/olm_all10_post_batch4_fresh_ae_smoke_contract_20260813.json'
RAW=ROOT/'refs/conformance/olm_all10_post_batch4_fresh_ae_smoke_raw_20260813.json'
SUMMARY=ROOT/'refs/conformance/olm_all10_post_batch4_fresh_ae_smoke_20260813.json'
ARTIFACT_DIR=ROOT/'handoffs/olm_all10_post_batch4_fresh_ae_smoke_20260813'
RECEIPT=ROOT/'handoffs/olm_all10_post_batch4_fresh_ae_smoke_20260813.invocation-receipt.json'
FAILURE=ROOT/'handoffs/olm_all10_post_batch4_fresh_ae_smoke_failure_20260813/failure_metadata.json'
FAILURE_SHA='c80ffbe1cf0e9d692fa2416c660bcd2c03119659afc89d1547185eba014b3ff1'
POST_INSTALL=ROOT/'refs/conformance/olm_hostless_batch4_incremental_install_20260813.json'
POST_INSTALL_SHA='415e1b26b77097248173da13239b85ae70d0b6a446fa6eb31bc13a0bdc6895af'
IDENTITY=ROOT/'refs/conformance/olm_installed_identity_manifest_20260806.json'
IDENTITY_SHA='426dce713a9595157fe4c9fa3731c464e4ef10afd5db269335a12fa4b38beccc'
TRANSACTION=ROOT/'handoffs/olm_hostless_batch4_install_20260813/install_transaction.json'
TRANSACTION_SHA='984a2c2766b76d9a729a71cbb9ce2bfa5662b6cfa1d4c682f5c40399bf168304'
LIVE_STATUS='FAILURE_PRESERVED_NO_RETRY_RELEASE_GATE_BLOCKED'

def sha(path:Path)->str:return hashlib.sha256(path.read_bytes()).hexdigest()
def load(path:Path,name:str):
 spec=importlib.util.spec_from_file_location(name,path);assert spec and spec.loader
 module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module

V=load(BASE,'batch4_v2_smoke')
V.THIS=THIS;V.PAYLOAD=PAYLOAD;V.CONTRACT_REPORT=CONTRACT_REPORT;V.RAW=RAW;V.SUMMARY=SUMMARY
V.ARTIFACT_DIR=ARTIFACT_DIR;V.RECEIPT=RECEIPT;V.LOCK=Path(tempfile.gettempdir())/'olm-all10-post-batch4-fresh-ae-smoke.lock'
V.LIVE_EXECUTION_ENABLED=False
V.C.THIS=THIS;V.C.PAYLOAD=PAYLOAD;V.C.RAW=RAW;V.C.SUMMARY=SUMMARY;V.C.ARTIFACT_DIR=ARTIFACT_DIR;V.C.RECEIPT=RECEIPT
V.C.IDENTITY_SHA256=IDENTITY_SHA
V.B.RUNNER=THIS;V.B.PAYLOAD=PAYLOAD
_base_contract=V.contract

def batch_authority()->dict[str,Any]:
 return {'post_install':{'path':str(POST_INSTALL.relative_to(ROOT)),'sha256':POST_INSTALL_SHA},
         'accepted_identity':{'path':str(IDENTITY.relative_to(ROOT)),'sha256':IDENTITY_SHA},
         'transaction':{'path':str(TRANSACTION.relative_to(ROOT)),'sha256':TRANSACTION_SHA},
         'preserved_failed_attempt':{'path':str(FAILURE.relative_to(ROOT)),'sha256':FAILURE_SHA},
         'batch_plugins':['OLMBlur','OLMColorKey','OLMSmoother','OLMSmoother2'],
         'enabled_generic_frame_plugins':['OLMBlur','OLMDirectionalBlur'],
         'numerical_assessment':'not_assessed_by_ae_smoke'}

def contract()->dict[str,Any]:
 value=copy.deepcopy(_base_contract());value['status']=LIVE_STATUS;value['batch4_post_install_authority']=batch_authority();return value

def validate_contract(value:Any)->bool:
 try:
  if (value!=contract() or sha(POST_INSTALL)!=POST_INSTALL_SHA or sha(IDENTITY)!=IDENTITY_SHA
      or sha(TRANSACTION)!=TRANSACTION_SHA or sha(FAILURE)!=FAILURE_SHA):return False
  base=copy.deepcopy(value);base.pop('batch4_post_install_authority');base['status']='AE_FORBIDDEN_DEFERRED_BATCH_CHECKPOINT'
  return (base==_base_contract() and sha(V.V1_RUNNER)==V.V1_RUNNER_SHA256 and sha(V.V1_PAYLOAD)==V.V1_PAYLOAD_SHA256
          and V.C.validate_contract(base['dependencies']['v1_contract']) and V.validate_failures(base['failure_authorities']))
 except (OSError,KeyError,TypeError,ValueError):return False

V.contract=contract;V.validate_contract=validate_contract

def outputs_absent()->bool:return not any(path.exists() for path in (RAW,SUMMARY,ARTIFACT_DIR,RECEIPT))

def main()->int:
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--write-contract',action='store_true');p.add_argument('--run',action='store_true');p.add_argument('--timeout',type=int,default=900);a=p.parse_args()
 if a.timeout<=0:raise SystemExit('--timeout must be positive')
 value=contract()
 if not validate_contract(value):raise SystemExit('batch4 smoke contract invalid')
 if a.write_contract:
  CONTRACT_REPORT.write_text(json.dumps(value,indent=2,sort_keys=True)+'\n');print('PASS_BATCH4_SMOKE_CONTRACT_WRITE');return 0
 try:saved=json.loads(CONTRACT_REPORT.read_text())
 except (OSError,json.JSONDecodeError) as error:raise SystemExit('batch4 smoke contract missing') from error
 if saved!=value:raise SystemExit('batch4 smoke contract drift')
 if not a.run:
  print(json.dumps({'status':'attempt_failed_no_retry','outputs_absent':outputs_absent(),'contract':value},indent=2,sort_keys=True));return 0
 raise SystemExit('refusing retry after preserved one-shot readiness failure')

if __name__=='__main__':raise SystemExit(main())
