"""Serial public-path replay of the P03b refusals, using the retained F52c oracle."""
import argparse, importlib, json, os, shutil, sys, time
from pathlib import Path
from types import SimpleNamespace
R = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(R/'tools/fuzz'))
from core import evaluate, load_corpus, sha
from geometry import require_host
from run import main_checkout
S = R/'orchestra/state/P03b-nonfinite-hdr-admission'
S.mkdir(parents=True, exist_ok=True)
os.environ.update(TMPDIR=str(S), PYTHONDONTWRITEBYTECODE='1', OLM_TEST_JOBS='1')
p = argparse.ArgumentParser()
p.add_argument('--label', default='baseline')
p.add_argument('--plugin', nargs='+', default=['olmdirectionalblur','olmkirakira','olmdistancegradation','radialblur'])
args = p.parse_args()
for name in args.plugin:
    d = S/(args.label+'-'+name); d.mkdir(exist_ok=True)
    a = importlib.import_module('adapters.'+name).Adapter(SimpleNamespace(main=main_checkout(),worker=Path.home()/'.cache/olm-emu/worker-F52c-geom/aex-guest-worker',max_size=1080 if name == 'olmkirakira' else 1920,case_timeout=10))
    require_host(a, {'geometry_sampler':'realistic-v1'})
    provenance = a.prepare(d,time.monotonic()+300)
    summary = json.loads((R/'orchestra/reports/T15b-evidence'/f'{name}-summary.json').read_text())
    cases = [(w['path'],load_corpus(R/w['path'],a)[0]) for w in summary['witnesses'] if 'refus' in w['failure_class']]
    if name == 'olmdistancegradation':
        a.max_size = 256
        cases.append(('default-seed909-index16', a.generate(909,16)))
    rows = []
    for label,c in cases:
        attr = {}; result = evaluate(a,c,d,time.monotonic()+40,attr)
        rows.append(dict(witness=label,input_sha256=sha(c['pixels']),result=result,refusals=attr))
        print(name,label,{k:v['status'] for k,v in result['routes'].items()},flush=True)
    (S/f'{args.label}-{name}.json').write_text(json.dumps(dict(provenance=provenance,rows=rows),indent=2))
    shutil.rmtree(d)
    if args.label != 'baseline':
        assert all(r['result']['routes']['smart']['status']=='exact' for r in rows)
