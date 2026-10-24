#!/usr/bin/env python3
"""Serial P02g Classic geometry/default/corpus evidence (no oracle rebuild)."""
import argparse
from collections import Counter
import json
import os
import struct
from pathlib import Path
import time
from types import SimpleNamespace
from adapters.olmsmoother import Adapter
from core import evaluate, load_corpus, save_corpus, sha
from geometry import sample, require_host
from run import main_checkout

ROOT = Path(__file__).resolve().parents[2]
S = ROOT / 'orchestra/state/P02g-smoother-geometry'

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--label', required=True)
    ap.add_argument('--jobs', type=int, choices=[1], default=1)
    ap.add_argument('--geometry', choices=['realistic'], default='realistic')
    ap.add_argument('--retain', action='store_true')
    ap.add_argument('--expect-fixed', action='store_true')
    args = ap.parse_args()
    s = S / args.label
    s.mkdir(parents=True, exist_ok=True)
    os.environ.update(TMPDIR=str(s), TMP=str(s), TEMP=str(s), OLM_TEST_JOBS='1')
    a = Adapter(SimpleNamespace(main=main_checkout(), worker=Path.home()/'.cache/olm-emu/worker-F52c-geom/aex-guest-worker', max_size=256, case_timeout=10))
    a.routes = ('classic',)
    deadline = time.monotonic() + 7200
    provenance = a.prepare(s, deadline)
    (s/'provenance.json').write_text(json.dumps(provenance, indent=2)+'\n')
    counts = {}
    with (s/'results.jsonl').open('w') as f:
        def check(group, case, saved=None):
            require_host(a, case)
            attr = {}
            r = evaluate(a, case, s, deadline, attr)
            status = r['routes']['classic']['status'] if r['oracle']['status']=='ok' else 'unavailable'
            counts.setdefault(group, Counter())[status] += 1
            row = dict(group=group, case={k:v for k,v in case.items() if k!='pixels'}, input_sha256=sha(case['pixels']), result=r, refusals=attr)
            if saved:
                row['saved_status'] = saved['result']['routes']['classic']['status']
                row['saved_candidate_sha256'] = saved['result']['routes']['classic'].get('raw_sha256')
            f.write(json.dumps(row)+'\n'); f.flush()
            if args.retain and group in ('boundaries', 'realistic-seed1', 'realistic-seed20261024'):
                corpus = ROOT/'tests/fuzz_corpus/olmsmoother_P02g_realistic'
                corpus.mkdir(exist_ok=True)
                save_corpus(corpus/f"{group}_seed{case['seed']}_case{case['index']:06}.json", a, case, case, r, {'accepted':[], 'attempts':0, 'minimality_claimed':False}, provenance)
        # Patterned sources exercise the key-mask outside/inside ROI and contour
        # reads beyond callback centers. All expected bytes come from the AEX.
        index = 1000
        for depth in (8,16):
            for keyed in (0,1):
                for rect in ([0,0,9,7], [2,1,7,6], [0,0,1,1], [8,6,9,7], [4,0,5,7], [0,0,0,0]):
                    c = a.generate(20261024,index)
                    pixels = bytearray()
                    for y in range(7):
                        for x in range(9):
                            v = 31 if (x+y//2)%4<2 else 221
                            channels = (255,v,v,v)
                            if depth==16: channels = tuple((v*32768+128)//255 for v in channels)
                            pixels.extend(struct.pack('<4B' if depth==8 else '<4H', *channels))
                    c.update(geometry_sampler='realistic-v1', geometry=[9,7], full_geometry=[36,28],
                             downsample=[[1,4],[1,4]], pixel_aspect=[10,11], extent_hint=list(rect),
                             request_rect=[1,1,8,6], input_padding=3, output_padding=3, rowbytes_padding=3,
                             depth=depth, pixels=bytes(pixels), parameters=[
                                 {'slot':1,'kind':'b','value':keyed},
                                 {'slot':2,'kind':'c','value':[255,31,31,31]},
                                 {'slot':3,'kind':'i','value':6}])
                    check('boundaries',c)
                    index += 1
        print(dict(counts), flush=True)
        for seed in (1, 20261024):
            for i in range(100):
                check(f'realistic-seed{seed}', sample(a.generate(seed,i), args.geometry))
            print(dict(counts), flush=True)
        for i in range(300):
            check('default-seed1', a.generate(1,i))
        print(dict(counts), flush=True)
        for path in sorted((ROOT/'tests/fuzz_corpus').glob('*/*.json')):
            if path.parent.name=='olmsmoother_P02g_realistic': continue
            data = json.loads(path.read_text())
            if data.get('plugin')!='olmsmoother': continue
            a.max_size = data['max_size']
            case, saved = load_corpus(path,a)
            check('corpus',case,saved)
        print(dict(counts), flush=True)
    (s/'summary.json').write_text(json.dumps(counts, indent=2)+'\n')
    if args.expect_fixed:
        assert all(status in ('exact','unavailable') for group in counts.values() for status in group), counts

if __name__ == '__main__': main()
