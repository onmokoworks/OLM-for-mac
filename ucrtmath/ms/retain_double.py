#!/usr/bin/env python3
"""Retain or recheck the nine required F43b campaigns and build identities."""
import argparse
import hashlib
import importlib.util
import json
import pathlib
import subprocess
ROOT=pathlib.Path(__file__).resolve().parents[2]
STATE=ROOT/'orchestra/state/F43b-ucrtmath-ms-double-trig-exp'
DEST=ROOT/'ucrtmath/ms/results-double'
p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');a=p.parse_args()
spec=importlib.util.spec_from_file_location('corpus',ROOT/'ucrtmath/ms/check_double.py')
corpus=importlib.util.module_from_spec(spec);spec.loader.exec_module(corpus)
source_paths=['ucrtmath/build.sh','ucrtmath/include/ucrtmath.h','ucrtmath/ms/double.c',
              'ucrtmath/ms/double_tables.h','ucrtmath/ms/double_native.c','ucrtmath/ms/double_compare.c',
              'ucrtmath/ms/check_double.py','ucrtmath/ms/check_double_harness.py',
              'ucrtmath/ms/inspect_double.py','ucrtmath/ms/retain_double.py',
              'tools/ucrt_math_probe/rosetta/oracle.c']
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def numerical(d):return {k:d[k] for k in ['function','kind','count','modes','producer_exit','comparator_exit']}
if not a.check:DEST.mkdir(exist_ok=True)
for fn in ['sin','cos','exp']:
    for kind,count in [('boundary',sum(1 for _ in corpus.boundaries(fn))),('random',10**9),('range',10**8)]:
        name=f'{fn}-{kind}-{count}.json'
        d=json.loads((STATE/name).read_text())
        assert d['function']==fn and d['count']==count and d['kind']==kind
        assert d['producer_exit']==d['comparator_exit']==0
        assert [m['mode'] for m in d['modes']]==[0,1]
        assert all(m['mismatches']==0 for m in d['modes'])
        for src in ['ucrtmath/ms/double.c','ucrtmath/ms/double_tables.h']:
            assert d['sha256'][src]==sha(ROOT/src),(name,src)
        if a.check:assert numerical(d)==numerical(json.loads((DEST/name).read_text())),name
        else:(DEST/name).write_text(json.dumps(d,indent=2)+'\n')
        print(name,'PASS')
harness=json.loads((STATE/'harness.json').read_text())
assert len(harness)==15
for row in harness:assert row['exit']=={'valid':0,'mismatch':1,'short':2,'truncated':2,'empty':2}[row['case']]
for fn,count in [('sinf',106167),('cosf',106167),('log2f',106167),('expf',8128),('atan2f',13779),('powf',79201)]:
    name=f'float-{fn}.json';d=json.loads((STATE/name).read_text())
    assert d['function']==fn and d['count']==count
    assert [m['mismatches'] for m in d['modes']]==[0,0]
    if a.check:assert d==json.loads((DEST/name).read_text())
    else:(DEST/name).write_text(json.dumps(d,indent=2)+'\n')
manifest=dict(sources={path:sha(ROOT/path) for path in source_paths})
if a.check:
    assert manifest['sources']==json.loads((DEST/'manifest.json').read_text())['sources']
    assert harness==json.loads((DEST/'harness.json').read_text())
else:
    manifest['builds']={name:sha(STATE/'build'/name) for name in ['double_native','double_compare','libucrtmath.a']}
    manifest['compiler']=subprocess.check_output(['clang','--version'],text=True)
    (DEST/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    (DEST/'harness.json').write_text(json.dumps(harness,indent=2)+'\n')
print('9 campaigns, 15 stream cases, 6 float regressions, source identities PASS')
