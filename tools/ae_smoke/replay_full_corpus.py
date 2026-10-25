#!/usr/bin/env python3
"""Replay a full 1:1 corpus through F53 and the installed bundle's F51 host.

This diagnostic uses tightly packed native worlds; it is not an AE render or
proof of the corpus's optional padding geometry. No source/worker build occurs.
"""
import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import time
from types import SimpleNamespace
import zlib
from compare_downsample import Adapter, full_frame_bundle, main_checkout, require_host
from compare import compare
from run_ae_smoke import PLUGINS


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('corpus', type=Path)
    ap.add_argument('state', type=Path)
    a = ap.parse_args()
    a.state = a.state.resolve(); a.state.mkdir(parents=True, exist_ok=False)
    os.environ.update(TMPDIR=str(a.state), TMP=str(a.state), TEMP=str(a.state))
    data = json.loads(a.corpus.read_text()); case = dict(data['case'])
    w,h = case['geometry']
    if case.get('full_geometry',[w,h]) != [w,h] or case.get('downsample',[[1,1],[1,1]]) != [[1,1],[1,1]]:
        raise ValueError('Full 1:1 corpus required')
    pixels = zlib.decompress(base64.b64decode(data['pixels_zlib_base64']))
    assert hashlib.sha256(pixels).hexdigest() == data['input_sha256']
    name = data['plugin']
    plugin = next(p for p in PLUGINS if p.lower() == name or (name=='radialblur' and p=='OLMRadialBlur'))
    adapter = Adapter(SimpleNamespace(plugin=name, main=main_checkout(),
        plugin_bundle=Path('/Applications/Adobe After Effects 2026/Plug-ins/OLM-smoke')/(plugin+'.plugin'),
        worker=Path.home()/'.cache/olm-emu/worker-F53-geom/aex-guest-worker', max_size=4096, case_timeout=15))
    case.update(pixels=pixels, full_geometry=[w,h], downsample=[[1,1],[1,1]],
                geometry_sampler='realistic-v2', checkout_rect=[0,0,w,h],
                request_rect=[0,0,w,h], extent_hint=[0,0,w,h], pixel_aspect=[1,1],
                input_padding=0, output_padding=0, rowbytes_padding=0)
    require_host(adapter,case)
    result = dict(corpus=str(a.corpus), input_sha256=data['input_sha256'],
                  layout='Full 1:1, tightly packed diagnostic worlds',
                  provenance=adapter.prepare(a.state,time.monotonic()+15))
    route = 'classic' if name=='olmsmoother' else 'smart'
    original, reference = adapter.oracle(case,a.state,time.monotonic()+15,route)
    native, actual = full_frame_bundle(adapter,case,a.state,route,15)
    result.update(original=original,bundle=native)
    if original['status']=='ok' and native['status']=='ok':
        left,right=a.state/'native.argb',a.state/'original.argb'
        left.write_bytes(actual);right.write_bytes(reference)
        result['comparison']=compare(left,right,w,h,case['depth'])
    (a.state/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:result[k] for k in ('original','bundle','comparison') if k in result}))
    return 0 if result.get('comparison',{}).get('exact') is True else 1


if __name__=='__main__': raise SystemExit(main())
