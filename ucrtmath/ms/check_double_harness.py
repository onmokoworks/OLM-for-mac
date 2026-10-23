#!/usr/bin/env python3
"""Exercise acceptance, mismatch, and rejection paths of the double stream."""
import json
import pathlib
import struct
import subprocess
ROOT=pathlib.Path(__file__).resolve().parents[2]
STATE=ROOT/'orchestra/state/F43b-ucrtmath-ms-double-trig-exp'
BUILD=STATE/'build'
DLL=pathlib.Path.home()/'.cache/olm-emu/ucrt/10.0.28000.2705/ucrtbase.dll'
results=[]
for fn in ['sin','cos','exp']:
    raw=subprocess.check_output([str(BUILD/'double_native'),fn,'random','1'])
    assert len(raw)==24
    words=list(struct.unpack('<3Q',raw));words[1]^=1
    broken=struct.pack('<3Q',*words)
    for label,data,count,expected in [('valid',raw,1,0),('mismatch',broken,1,1),
                                      ('short',raw,2,2),('truncated',raw[:-1],1,2),('empty',b'',1,2)]:
        p=subprocess.run([str(BUILD/'double_compare'),str(DLL),fn,str(count)],input=data,capture_output=True)
        assert p.returncode==expected,(fn,label,p.returncode,p.stderr.decode())
        if label=='mismatch':
            r=json.loads(p.stdout)
            assert [m['mismatches'] for m in r['modes']]==[1,0],r
        results.append(dict(function=fn,case=label,exit=p.returncode))
        print(fn,label,'PASS',p.returncode)
(STATE/'harness.json').write_text(json.dumps(results,indent=2)+'\n')
# The common library build gained an object; recheck all existing float exports.
import os
import random
env=dict(os.environ,TMPDIR=str(STATE),PYTHONDONTWRITEBYTECODE='1')
with (STATE/'float-build.log').open('w') as log:
    subprocess.run(['sh',str(ROOT/'ucrtmath/tests/build.sh'),str(BUILD)],env=env,stdout=log,stderr=log,check=True)
    subprocess.run(['python3',str(ROOT/'ucrtmath/tests/targeted.py'),str(STATE/'float-targets')],env=env,stdout=log,stderr=log,check=True)
rng=random.Random(42)
words={rng.getrandbits(32) for _ in range(100000)}
for edge in [0,0x800000,0x39000000,0x3c000000,0x3f330000,0x3f490fdb,0x3f800000,0x48f42400,0x4b742400,0x4b800456,0x4f490fdb,0x7f800000]:
    for delta in range(-128,129):
        for sign in [0,0x80000000]:words.add(((edge+delta)&0x7fffffff)|sign)
with (STATE/'float-targets/unary.txt').open('w') as dst:
    for word in sorted(words):dst.write(f'{word:08x} 0\n')
for fn,count in [('sinf',106167),('cosf',106167),('log2f',106167),('expf',8128),('atan2f',13779),('powf',79201)]:
    target='unary' if fn in ['sinf','cosf','log2f'] else fn
    with (STATE/f'float-targets/{target}.txt').open('rb') as src,(STATE/f'float-{fn}.stderr').open('w') as err:
        producer=subprocess.Popen([str(BUILD/'native'),fn,'file',str(count)],stdin=src,stdout=subprocess.PIPE,stderr=err,env=env)
        try:
            comp=subprocess.run([str(BUILD/'compare'),str(DLL),fn,str(count)],stdin=producer.stdout,capture_output=True,env=env)
            producer.stdout.close();rc=producer.wait()
        finally:
            if producer.poll() is None:producer.kill();producer.wait()
        assert rc==comp.returncode==0,(fn,rc,comp.returncode,comp.stderr)
        (STATE/f'float-{fn}.json').write_bytes(comp.stdout)
        print(fn,'regression PASS',count)
