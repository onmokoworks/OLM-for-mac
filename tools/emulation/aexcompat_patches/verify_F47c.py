#!/usr/bin/env python3
"""Anchor native Smart output and AEX regression in the same worker."""
import copy
import json
from pathlib import Path
import sys
import time
from types import SimpleNamespace

ROOT=Path(__file__).resolve().parents[3]
STATE=ROOT/'orchestra/state/F47c-native-plugin-smart-render'
sys.path.insert(0,str(ROOT/'tools/fuzz'))
from adapters.plugin_bundle import Adapter
from core import evaluate, sha

def main():
    options=SimpleNamespace(max_size=256,case_timeout=60,
        main=ROOT.parent.parent,worker=STATE/'aex-guest-worker',
        plugin_bundle=STATE/'bundles/xcode/OLMBlur/products/OLMBlur.plugin')
    adapter=Adapter(options)
    directory=STATE/'anchor'
    directory.mkdir(exist_ok=True)
    deadline=time.monotonic()+180
    provenance=adapter.prepare(directory,deadline)
    case=adapter.generate(1,0)
    case.update(geometry=[32,32],depth=8,profile='sdr',parameters=adapter.defaults(32,32),
        pixels=bytes(v for y in range(32) for x in range(32) for v in (255,(x*17+y*3)%256,(x*7+y*23)%256,(x*31+y*5)%256)),input_padding=7,output_padding=0)
    result=evaluate(adapter,case,directory,deadline)
    old=copy.copy(adapter)
    old.worker=Path.home()/'.cache/olm-emu/worker-F47-nativeplugin/aex-guest-worker'
    old_status,old_raw=old.oracle(case,directory,deadline,'smart')
    new_status,new_raw=adapter.oracle(case,directory,deadline,'smart')
    unsupported,_ = old.candidate(case,directory,'smart',deadline)[:2]
    assert unsupported['status']=='harness_error', unsupported
    record=dict(provenance=provenance,case={k:v for k,v in case.items() if k!='pixels'},
        input_sha256=sha(case['pixels']),result=result,
        old_worker_candidate_rejection=unsupported['status'],
        aex_regression={'old':old_status,'new':new_status,'old_sha256':sha(old_raw),'new_sha256':sha(new_raw),'equal':old_raw==new_raw})
    (STATE/'anchor.json').write_text(json.dumps(record,indent=2)+'\n')
    print(json.dumps(record,indent=2))
    assert result['routes']['smart']['status']=='exact',result
    assert old_status['status']==new_status['status']=='ok' and old_raw==new_raw
if __name__=='__main__': main()
