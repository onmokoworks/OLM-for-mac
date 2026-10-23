#!/usr/bin/env python3
"""Byte-exact comparison of saved bound resident captures and paired Mac planes."""
import argparse
import json
from pathlib import Path
import hashlib


def diff(a,b):
    assert len(a)==len(b), (len(a),len(b))
    first = None
    count = 0
    for i in range(0,len(a),4):
        if a[i:i+4] != b[i:i+4]:
            count += 1
            if first is None:
                first = dict(word=i//4,aex_le=a[i:i+4].hex(),mac_le=b[i:i+4].hex())
    return dict(bytes=len(a),different_words=count,first=first,
                aex_sha256=hashlib.sha256(a).hexdigest(),mac_sha256=hashlib.sha256(b).hexdigest())


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--trace',required=True,type=Path)
    ap.add_argument('--mac',required=True,type=Path)
    ap.add_argument('--output',required=True,type=Path)
    args=ap.parse_args()
    report=[]
    for row in json.loads((args.trace/'report.json').read_text())['cases']:
        assert row['bound']
        trace=json.loads((args.trace/row['trace_file']).read_text()) if 'trace_file' in row else row['trace']
        case_dir=args.mac/f"{row['seed']}-{row['index']}"
        measurements={}
        mapping={'56f0-source':('source','before'),'b150-polar-head':('polar','before'),
                 'a9d0-accum':('prepass','before'),'normalized':('normalized','before'),'4640-source':('source','before'),
                 '2780-polar':('polar','before'),'24c0-accum':('prepass','before'),
                 'rotation-normalized':('normalized','before'), '24c0-max':('maximum','after')}
        expanded = list(trace['memory_witnesses'])
        for w in trace['memory_witnesses']:
            if w['watch_id'] in ('a9d0-accum','24c0-accum'):
                expanded.append(dict(w,watch_id='scatter-accum'))
        mapping.update({'scatter-accum':('accum','after'),'a9d0-max':('maximum','after')})
        for w in expanded:
            if w['watch_id'] not in mapping:continue
            name,phase=mapping[w['watch_id']]
            p=case_dir/(name+'.bin')
            if not p.exists():continue
            snapshot=w[phase]
            assert snapshot['status']=='captured',snapshot['status']
            a=bytes.fromhex(snapshot['hex'])
            measurements[name]=diff(a,p.read_bytes()[:len(a)])
        output=(case_dir/'output.bin').read_bytes()
        report.append(dict(seed=row['seed'],index=row['index'],stages=measurements,
                           final_exact=hashlib.sha256(output).hexdigest()==row['saved_output_sha256']))
    args.output.write_text(json.dumps(report,indent=2)+'\n')
    for r in report:
        print(r['seed'],r['index'],{n:s['different_words'] for n,s in r['stages'].items()},r['final_exact'])

if __name__=='__main__':main()
