"""P04d bundle smoke with an explicitly selected, registered candidate host."""
import hashlib
import json
import os
from pathlib import Path
import sys
import time
from types import SimpleNamespace
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'tools/fuzz'))
from adapters.plugin_bundle import Adapter
from adapters import bundle_geometry
from core import evaluate
from geometry import sample,require_host
from run import main_checkout
S=ROOT/'orchestra/state/P04d-colorkeep-cropped-checkout'
CACHE=Path.home()/'.cache/olm-emu'
host=CACHE/'P04d-colorkeep-host/plugin-host'
bundle=CACHE/'P04d-colorkeep-bundle/ColorKeep.plugin'
# The production adapter remains pinned to the historical F53 host. Override
# only this test's candidate transport; original AEX execution stays untouched.
command=bundle_geometry.command
def selected_command(argv, **kwargs):
    argv=list(argv);argv[0]=host
    return command(argv,**kwargs)
bundle_geometry.command=selected_command
os.environ.update(TMPDIR=str(S),PYTHONDONTWRITEBYTECODE='1',OLM_TEST_JOBS='1')
a=Adapter(SimpleNamespace(plugin='colorkeep',plugin_bundle=bundle,main=main_checkout(),worker=CACHE/'worker-F53-geom/aex-guest-worker',max_size=256,case_timeout=10))
stage=S/'bundle-smoke';stage.mkdir(exist_ok=True)
rows=[]
for mode in ('realistic-v1','realistic-v2'):
    for i in list(range(10))+[29,63,99]:
        c=sample(a.generate(1,i),mode);require_host(a,c)
        if i==0:
            provenance=a.prepare(stage,time.monotonic()+60)
            provenance.update(bundle_host_path=str(host),bundle_host_sha256=hashlib.sha256(host.read_bytes()).hexdigest())
        r=evaluate(a,c,stage,time.monotonic()+60)
        rows.append(dict(mode=mode,index=i,result=r,provenance=provenance))
        print(mode,i,r['routes']['smart']['status'],flush=True)
(S/'bundle-smoke.json').write_text(json.dumps(rows,indent=2)+'\n')
assert all(r['result']['routes']['smart']['status']=='exact' for r in rows)
print(len(rows),'exact')
