#!/usr/bin/env python3
"""Bounded two-process raw-bit campaigns; check both exits and exact row count."""
import pathlib, subprocess, sys, json, hashlib, time
root=pathlib.Path(__file__).resolve().parents[2]
state=root/'orchestra/state/F28-ucrtmath-lib-amd'
build=state/'build'
dll='/Users/onmk/.cache/olm-emu/ucrt/10.0.28000.2705/ucrtbase.dll'
for fn in sys.argv[1:] or ['atan2f','powf','expf']:
 stamp=time.monotonic()
 count=2**32 if fn=='expf' else 100_000_000
 with (state/f'full-{fn}.json').open('w') as out, (state/f'full-{fn}.log').open('w') as err:
  p=subprocess.Popen([str(build/'native'),fn,'sweep',str(count)],stdout=subprocess.PIPE,stderr=err)
  try:
   q=subprocess.run([str(build/'compare'),dll,fn,str(count)],stdin=p.stdout,stdout=out,stderr=err)
   p.stdout.close()
   rc=p.wait()
  finally:
   if p.poll() is None:p.kill();p.wait()
 if rc or q.returncode:sys.exit(f'{fn}: producer={rc}, comparator={q.returncode}')
 print(fn,count,'PASS',round(time.monotonic()-stamp,3),'seconds',flush=True)
