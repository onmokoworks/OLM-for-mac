#!/usr/bin/env python3
"""Recheck F28's stream rejection contract using the F42 unary dispatch."""
import pathlib,subprocess
root=pathlib.Path(__file__).resolve().parents[2]
b=root/'orchestra/state/F42-ucrtmath-ms-float/build'
dll=pathlib.Path.home()/'.cache/olm-emu/ucrt/10.0.28000.2705/ucrtbase.dll'
for fn in ['sinf','cosf','log2f']:
 raw=subprocess.check_output([str(b/'native'),fn,'sweep','1'])
 for label,data,count,expected in [('valid',raw,1,0),('short',raw,2,2),('truncated',raw[:-1],1,2),('empty',b'',1,2)]:
  p=subprocess.run([str(b/'compare'),str(dll),fn,str(count)],input=data,capture_output=True)
  assert p.returncode==expected,(fn,label,p.returncode,p.stderr.decode())
  print(fn,label,'PASS',p.returncode)
# Preserve behavior of the three existing F28 dispatches after adding unary APIs.
state=b.parent
subprocess.run(['python3',str(root/'ucrtmath/tests/targeted.py'),str(state/'regression-targets')],check=True)
for fn,count in [('expf',8128),('atan2f',13779),('powf',79201)]:
 with (state/'regression-targets'/f'{fn}.txt').open('rb') as src,(state/'regression.bin').open('wb') as dst:
  subprocess.run([str(b/'native'),fn,'file','0'],stdin=src,stdout=dst,check=True)
 with (state/'regression.bin').open('rb') as src,(state/f'regression-{fn}.json').open('w') as dst:
  subprocess.run([str(b/'compare'),str(dll),fn,str(count)],stdin=src,stdout=dst,check=True)
 print(fn,'regression PASS',count)
(state/'regression.bin').unlink()
