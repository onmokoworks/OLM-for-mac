#!/usr/bin/env python3
"""Record the inherited warmed selector-entry checkpoint boundary, not a pass."""
import json,time
from pathlib import Path
from types import SimpleNamespace
import verify_F54c as v

def main():
    d=v.S/'entry-boundary';d.mkdir(parents=True,exist_ok=True)
    rows=[]
    for name in ('worker-F54b','worker-F54c'):
        worker=Path.home()/'.cache/olm-emu'/name/'aex-guest-worker'
        a=v.Adapter(SimpleNamespace(main=v.MAIN,worker=worker,max_size=4096,case_timeout=180))
        for key in list(a.env):
            if key.startswith('AEXCOMPAT_RESIDENT_') or key.startswith('AEXCOMPAT_SMART_TRACE'):del a.env[key]
        case=dict(geometry=[3840,2160],depth=8,pixels=bytes([255,71,29,103])*(3840*2160),parameters=a.defaults(3840,2160),input_padding=0,output_padding=0)
        tp=d/(name+'.json');a.env.update(AEXCOMPAT_SMART_TRACE=str(tp),AEXCOMPAT_SMART_TRACE_WATCH='10540,128,first')
        status,raw=a.oracle(case,d,time.monotonic()+190)
        assert status['status']=='ok' and raw==case['pixels'],status
        trace=json.loads(tp.read_text())
        rows.append(dict(worker=name,worker_sha256=v.sha(worker.read_bytes()),output_sha256=v.sha(raw),status=status,entry_rva=trace['entry_rva'],witnesses=len(trace['memory_witnesses']),unhookable=trace['trace_configuration']['unhookable_watches']))
    (v.S/'entry-boundary-summary.json').write_text(json.dumps(rows,indent=2)+'\n');print(json.dumps(rows))
if __name__=='__main__':main()
