#!/usr/bin/env python3
"""Validate compressed C53b evidence and all ten paired full-stage boundaries."""
import gzip
import hashlib
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
E=ROOT/'orchestra/reports/C53b-evidence'


def read(name):
    with gzip.open(E/name,'rb') as f:return f.read()


def main():
    manifest=json.loads((E/'manifest.json').read_text())
    for name,entry in manifest.items():
        digest=hashlib.sha256();size=0
        opener=gzip.open if name.endswith('.gz') else open
        with opener(E/name,'rb') as f:
            for block in iter(lambda:f.read(1024*1024),b''):
                digest.update(block);size+=len(block)
        assert digest.hexdigest()==entry['uncompressed_sha256'] and size==entry['uncompressed_bytes'],name
    rows=json.loads(read('trace-full-report.json.gz'))['cases']
    count=0
    for row in rows:
        seed,index=row['seed'],row['index'];rotation=seed==105 and index==148
        run='trace-rotation' if rotation else 'trace-full'
        trace=json.loads(read(f'{run}-{seed}-{index}.json.gz'))
        assert row['bound'] and not trace['truncated'] and not trace['dropped_memory_witnesses']
        assert not trace['trace_configuration']['unhookable_watches']
        mapping=[('4640-source' if rotation else '56f0-source','before','source'),
                 ('2780-polar' if rotation else 'b150-polar-head','before','polar'),
                 ('24c0-accum' if rotation else 'a9d0-accum','before','prepass'),
                 ('24c0-accum' if rotation else 'a9d0-accum','after','accum'),
                 ('24c0-max' if rotation else 'a9d0-max','after','maximum'),
                 ('rotation-normalized' if rotation else 'normalized','before','normalized')]
        for watch,phase,plane in mapping:
            snap=next(w for w in trace['memory_witnesses'] if w['watch_id']==watch)[phase]
            assert snap['status']=='captured'
            raw=bytes.fromhex(snap['hex'])
            assert hashlib.sha256(raw).hexdigest()==snap['sha256']
            assert raw==read(f'mac-{seed}-{index}-{plane}.bin.gz'),(seed,index,plane)
            count+=1
        assert hashlib.sha256(read(f'mac-{seed}-{index}-output.bin.gz')).hexdigest()==row['saved_output_sha256']
    witness=json.loads(read('final-witnesses-report.json.gz'))
    assert len(witness['cases'])==20 and all(r['exact'] and not r['result'].get('sanitizer') for r in witness['cases'])
    actual=hashlib.sha256((ROOT/'mac/OLMRadialBlur/OLMRadialBlur.cpp').read_bytes()).hexdigest()
    assert all(b['source_sha256']==actual for b in witness['builds'])
    print(json.dumps(dict(verified_files=len(manifest),exact_full_planes=count,exact_original_outputs=len(rows),final_o2_sanitized=20)))

if __name__=='__main__':main()
