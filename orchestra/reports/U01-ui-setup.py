"""Run original GLOBAL_SETUP/PARAMS_SETUP with the pinned cached Unicorn worker."""
import json,subprocess,sys,hashlib,os
from pathlib import Path
root=Path('/Users/onmk/Documents/Projects/Personal/OLM as')
worker=Path('/Users/onmk/.cache/olm-emu/radial_frozen_reference_bd878da/target/release/aex-guest-worker')
out=Path(sys.argv[1]);out.mkdir(parents=True,exist_ok=True)
rows=[]
for p in sorted((root/'plugins_2025').glob('*.aex')):
 with (out/(p.stem+'.json')).open('w') as f,(out/(p.stem+'.log')).open('w') as e:
  r=subprocess.run([str(worker),'setup',str(p)],stdout=f,stderr=e,timeout=90,env={**os.environ,'TMPDIR':str(out.resolve())})
 d=json.loads((out/(p.stem+'.json')).read_text()) if r.returncode==0 else {}
 rows.append(dict(plugin=p.stem,returncode=r.returncode,report=d))
 print(p.stem,r.returncode,len(d.get('params',d.get('parameters',[]))),flush=True)
(out/'summary.json').write_text(json.dumps(dict(worker=str(worker),worker_sha256=hashlib.sha256(worker.read_bytes()).hexdigest(),plugins=rows),indent=2)+'\n')
