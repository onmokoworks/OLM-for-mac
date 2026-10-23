#!/usr/bin/env python3
"""Five-engine raw-bit survey, at most two math worker processes."""
import pathlib,subprocess,sys,time,json
root=pathlib.Path(__file__).resolve().parents[2]
state=root/'orchestra/state/F28-ucrtmath-lib-amd';build=state/'survey-build'
dll='/Users/onmk/.cache/olm-emu/ucrt/10.0.28000.2705/ucrtbase.dll'
for fn in sys.argv[1:] or ['sin','cos','exp','pow','log2f']:
 for dataset,count in ([('full',2**32)] if fn=='log2f' else [('random',100_000_000),('ranges',1048576)]):
  stamp=time.monotonic()
  with (state/f'survey-{fn}-{dataset}.json').open('w') as out,(state/f'survey-{fn}-{dataset}.log').open('w') as err:
   p=subprocess.Popen([str(build/'survey_native'),fn,str(count)]+(['ranges'] if dataset=='ranges' else []),stdout=subprocess.PIPE,stderr=err)
   try:
    q=subprocess.run([str(build/'survey_compare'),dll,fn,str(build/'amd-off.dylib'),str(build/'amd-fma.dylib'),str(count)],stdin=p.stdout,stdout=out,stderr=err)
    p.stdout.close();rc=p.wait()
   finally:
    if p.poll() is None:p.kill();p.wait()
  if rc or q.returncode:sys.exit(f'{fn}/{dataset}: producer={rc}, comparator={q.returncode}')
  print(fn,dataset,count,'completed',round(time.monotonic()-stamp,3),'seconds',flush=True)
