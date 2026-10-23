#!/usr/bin/env python3
"""Exercise the installed worker's production call budget with synthetic PE code.

No original plugin is modified. The loop increments RAX on every second guest
instruction, so its stopped register/PC expose the exact instruction boundary.
"""
import hashlib
import json
import os
from pathlib import Path
import struct
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[3]
S = ROOT/'orchestra/state/F50b-oracle-budget-build'
E = ROOT/'orchestra/reports/F50b-evidence'
WORKER = Path.home()/'.cache/olm-emu/worker-F50-budget/aex-guest-worker'

def fixture(code):
    b = bytearray(0x400)
    def u16(o, v): struct.pack_into('<H', b, o, v)
    def u32(o, v): struct.pack_into('<I', b, o, v)
    b[:2] = b'MZ'
    u32(60, 0x80)
    b[0x80:0x84] = b'PE\0\0'
    for o,v in [(0x84,0x8664),(0x86,1),(0x94,240),(0x96,0x2022),(0x98,0x20b)]: u16(o,v)
    struct.pack_into('<Q',b,0x98+24,0x180000000)
    for o,v in [(32,0x1000),(36,0x200),(56,0x2000),(60,0x200),(108,16),(112,0x1100),(116,0x80)]: u32(0x98+o,v)
    sec=0x98+240
    b[sec:sec+5]=b'.text'
    for o,v in [(8,0x200),(12,0x1000),(16,0x200),(20,0x200),(36,0x60000020)]: u32(sec+o,v)
    b[0x200:0x200+len(code)] = code
    for o,v in [(12,0x1180),(16,1),(20,1),(24,1),(28,0x1128),(32,0x112c),(36,0x1130),(40,0x1000),(44,0x1160)]: u32(0x300+o,v)
    b[0x360:0x36b]=b'EffectMain\0'
    b[0x380:0x386]=b'probe\0'
    return b

def audit():
    manifest = json.loads((E/'build-manifest.json').read_text())
    assert hashlib.sha256(WORKER.read_bytes()).hexdigest() == manifest['worker_sha256']
    rows = json.loads((E/'budget-smoke.json').read_text())
    assert [r['name'] for r in rows] == ['return', 'exhaustion1', 'exhaustion2']
    normal = json.loads((E/'return.stdout.json').read_text())
    assert rows[0]['returncode'] == 0
    assert normal['global_setup_error'] == normal['params_setup_error'] == 0
    for row in rows[1:]:
        diagnostic = (E/(row['name']+'.stderr.log')).read_text()
        assert row['returncode'] == 1
        assert 'instruction budget 2000000000 per scheduler slice' in diagnostic
        snapshot = json.loads(diagnostic.split('crash_snapshot=', 1)[1])
        assert snapshot['registers']['rax'] == row['rax'] == 1_000_000_000
        assert snapshot['registers']['rip'] == row['rip'] == 0x180001005
        assert snapshot['instruction_rva'] == row['instruction_rva'] == 0x1005
    print('PASS: installed identity, normal return, both exact exhaustion boundaries.')


def main():
    if sys.argv[1:] == ['--audit']:
        audit()
        return
    assert not sys.argv[1:], 'Only --audit or no arguments are supported'
    S.mkdir(parents=True,exist_ok=True)
    E.mkdir(parents=True,exist_ok=True)
    env=dict(os.environ,TMPDIR=str(S),TMP=str(S),TEMP=str(S))
    rows=[]
    for name,code in [('return',b'\x31\xc0\xc3'),('exhaustion1',b'\x31\xc0\x48\xff\xc0\xeb\xfb'),('exhaustion2',b'\x31\xc0\x48\xff\xc0\xeb\xfb')]:
        pe=S/(name+'.aex')
        pe.write_bytes(fixture(code))
        start=time.monotonic()
        with (E/(name+'.stdout.json')).open('w') as out, (E/(name+'.stderr.log')).open('w') as err:
            p=subprocess.run([WORKER,'setup',pe],stdout=out,stderr=err,env=env,timeout=3600)
        rows.append(dict(name=name,returncode=p.returncode,elapsed_seconds=time.monotonic()-start))
        (E/'budget-smoke.json').write_text(json.dumps(rows,indent=2)+'\n')
        print(rows[-1],flush=True)
        if name=='return':
            assert p.returncode==0
        else:
            assert p.returncode!=0
            diagnostic = (E/(name+'.stderr.log')).read_text()
            assert 'instruction budget 2000000000 per scheduler slice' in diagnostic
            snapshot = json.loads(diagnostic.split('crash_snapshot=', 1)[1])
            registers = snapshot['registers']
            assert registers['rax'] == 1_000_000_000, registers
            assert registers['rip'] == 0x180001005, registers
            rows[-1].update(rax=registers['rax'], rip=registers['rip'],
                            instruction_rva=snapshot['instruction_rva'])
            (E/'budget-smoke.json').write_text(json.dumps(rows,indent=2)+'\n')
    print('PASS: both runs exhausted at RAX=1000000000, RIP=0x180001005.',flush=True)

if __name__=='__main__': main()
