#!/usr/bin/env python3
"""Check that the comparator rejects corruption/truncation/count errors.
Run pow_check.py first to build. Also checks native file input truncation.
"""
import json, os, struct, subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
STATE=ROOT/'orchestra/state/F43c-ucrtmath-ms-pow'
BUILD=STATE/'build'
DLL=Path.home()/'.cache/olm-emu/ucrt/10.0.28000.2705/ucrtbase.dll'
row=struct.pack('<QQQQ',0,0,0x3ff0000000000000,0x3ff0000000000000)
checks=[]
for name,payload,count,expected in [
 ('correct',row,1,0),('truncated',row[:-1],1,2),
 ('count',row,2,2),('empty',b'',1,2),
 ('both_results_corrupt',struct.pack('<QQQQ',0,0,0,0),1,1),
 ('second_mode_corrupt',struct.pack('<QQQQ',0,0,0x3ff0000000000000,0),1,1)]:
 p=subprocess.run([str(BUILD/'compare'),str(DLL),'pow',str(count)],input=payload,capture_output=True)
 assert p.returncode==expected,(name,p.returncode,p.stderr)
 result=json.loads(p.stdout) if p.stdout else None
 if result:
  assert [m['mismatches'] for m in result['modes']]==({'correct':[0,0],'both_results_corrupt':[1,1],'second_mode_corrupt':[0,1]}[name])
 checks.append(dict(test=name,exit=p.returncode,result=result,error=p.stderr.decode().strip()))
p=subprocess.run([str(BUILD/'native'),'file','1'],input=b'',capture_output=True)
assert p.returncode==2
checks.append(dict(test='producer_missing_input',exit=p.returncode))
(STATE/'harness.json').write_text(json.dumps(checks,indent=2)+'\n')
print(f'{len(checks)} stream integrity checks passed')
