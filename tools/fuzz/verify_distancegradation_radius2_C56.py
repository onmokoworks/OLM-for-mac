#!/usr/bin/env python3
"""Recheck radius-two admissions against hash-bound independent public reports."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
sys.dont_write_bytecode = True
from adapters.olmdistancegradation import Adapter, SOURCE
from adapters.public import ROOT
from core import sha
from run import main_checkout, default_worker
from verify_distancegradation_smart_C08 import variant
import probe_distancegradation_C56 as probe


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--before-ref',default='becd26a2')
    p.add_argument('--source',type=Path,default=SOURCE)
    p.add_argument('--reference',type=Path,action='append',required=True)
    p.add_argument('--scratch',type=Path,required=True)
    p.add_argument('--report',type=Path,required=True)
    args=p.parse_args();args.scratch=args.scratch.resolve()
    assert args.scratch.is_relative_to(ROOT/'orchestra/state')
    args.scratch.mkdir(parents=True,exist_ok=True)
    os.environ.update(TMPDIR=str(args.scratch),TMP=str(args.scratch),TEMP=str(args.scratch))
    tempfile.tempdir=str(args.scratch)
    old=subprocess.check_output(['git','show',args.before_ref+':mac/OLMDistanceGradation/OLMDistanceGradation.cpp'],cwd=ROOT).decode()
    source=args.source.read_text();deadline=time.monotonic()+3600
    report=dict(before_ref=args.before_ref,before_sha256=sha(old.encode()),source_sha256=sha(source.encode()),rows=[])
    a=Adapter(argparse.Namespace(max_size=256,case_timeout=180,main=main_checkout(),worker=default_worker()))
    probe.radius_two=True
    try:
      with tempfile.TemporaryDirectory(dir=args.scratch) as td:
        td=Path(td);prod=td/'prod';prod.mkdir();report['provenance']=a.prepare(prod,deadline)
        before=variant(a,td/'before',deadline,old)
        current=variant(a,td/'current',deadline,source)
        san=variant(a,td/'san',deadline,source,sanitized=True)
        wd=td/'case';wd.mkdir()
        for path in args.reference:
            ref=json.loads(path.read_text());assert ref['completed']
            refs={r['label']:r for r in ref['rows']}
            cases=list(probe.matrix(a,'bilateral',ref['extreme']))
            assert len(refs)==len(cases)
            for label,c in cases:
                r=refs[label];assert r['exact'] and r['input_sha256']==sha(c['pixels'])
                assert r['parameters']==c['parameters'] and r['geometry']==c['geometry']
                bs,br,_=before.candidate(c,wd,'smart',deadline)
                ns,nr,_=current.candidate(c,wd,'smart',deadline)
                ss,sr,_=san.candidate(c,wd,'smart',deadline)
                assert bs['status']=='refusal', (label,bs)
                assert ns['status']=='ok' and sha(nr)==r['oracle_sha256'],(label,ns)
                assert ns==ss and nr==sr,(label,ss)
                report['rows'].append(dict(label=label,extreme=ref['extreme'],input_sha256=sha(c['pixels']),before=bs,
                    after=ns,oracle_sha256=r['oracle_sha256'],after_sha256=sha(nr),sanitized_equal=True))
            print(path.name,len(cases),'refusal->exact',flush=True)
        report['completed']=True
    finally:
        args.report.parent.mkdir(parents=True,exist_ok=True)
        args.report.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')

if __name__=='__main__':main()
