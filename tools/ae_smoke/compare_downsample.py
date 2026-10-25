#!/usr/bin/env python3
"""Bind real AE outputs/readbacks to original F53 and the installed bundle.

Reduced-resolution controls supply the host-resampled input. This is a measured
output input proxy, not a plugin checkout trace. Geometry assumptions are explicit.
"""
import argparse
import importlib
import json
import os
from pathlib import Path
import sys
import time
from types import SimpleNamespace
import numpy as np
import tifffile
from compare import compare

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools/fuzz'))
from core import sha
from run import main_checkout
from adapters.plugin_bundle import Adapter
from geometry import require_host


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('state', type=Path)
    ap.add_argument('--timeout', type=int, default=30)
    args = ap.parse_args()
    state = args.state.resolve()
    out = state / 'comparison'
    out.mkdir(exist_ok=True)
    os.environ.update(TMPDIR=str(out), TMP=str(out), TEMP=str(out))
    rendered = json.loads((state / 'render-results.json').read_text())
    result_path = state/'comparisons.json'
    results = json.loads(result_path.read_text()) if result_path.exists() else []
    completed = {r['outputPrefix'] for r in results}
    for row in rendered:
        if row['status'] == 'error':
            continue
        prefix = row['outputPrefix']
        if prefix in completed:
            continue
        if row['depth'] != 8:
            raise ValueError('Only calibrated 8 bpc TIFF is supported')
        path = next(state.glob(prefix + '_*.tif'))
        rgba = tifffile.imread(path)
        h, w = rgba.shape[:2]
        case_dir = out / prefix
        case_dir.mkdir(exist_ok=True)
        ae = case_dir / 'ae.argb'
        ae.write_bytes(rgba[:, :, [3, 0, 1, 2]].tobytes())
        result = dict(outputPrefix=prefix, plugin=row['plugin'], geometry=[w,h],
                      full_geometry=[row['width'],row['height']], divisor=row['divisor'],
                      resolution_readback=row['renderSettings']['Resolution'],
                      assumptions='input=matching no-effect control; checkout origin=0; full-frame extent; downsample=queue rational; no live InData trace')
        if row['plugin'] == 'control':
            if row['divisor'] == 1:
                project = next(p for p in json.loads((state/'build.json').read_text())['projects']
                               if p['items'][0]['width'] == row['width'])
                source = Path(project['path']).parent / 'inputs' / f"input-{row['width']}x{row['height']}-8.argb"
                result['io'] = compare(ae, source, w, h, 8)
            else:
                result['io'] = {'exact': None, 'note': 'resampling is not an identity I/O test'}
        else:
            name = 'radialblur' if row['plugin'] == 'OLMRadialBlur' else row['plugin'].lower()
            options = SimpleNamespace(plugin=name, plugin_bundle=Path('/Applications/Adobe After Effects 2026/Plug-ins/OLM-smoke')/(row['plugin']+'.plugin'),
                main=main_checkout(), worker=Path.home()/'.cache/olm-emu/worker-F53-geom/aex-guest-worker',max_size=4096,case_timeout=args.timeout)
            adapter = Adapter(options)
            require_host(adapter, {'geometry_sampler':'realistic-v2'})
            result['provenance'] = adapter.prepare(case_dir, time.monotonic()+args.timeout)
            control_prefix = prefix.replace(row['plugin'], 'control', 1)
            control = tifffile.imread(next(state.glob(control_prefix + '_*.tif')))
            pixels = control[:, :, [3,0,1,2]].tobytes()
            params = adapter.defaults(row['width'],row['height'])
            properties = {p['index']:p for p in row['properties']}
            for p in params:
                value = properties[p['slot']]['value']
                if value is None:
                    raise ValueError('Missing AE readback for slot '+str(p['slot']))
                if p['kind']=='c':
                    value = [round(value[i]*255) for i in (3,0,1,2)]
                if p['kind']=='p':
                    # Public transport encodes point percentages using sampled dimensions.
                    value = [v*n/f for v,n,f in zip(value,(w,h),(row['width'],row['height']))]
                p['value'] = value
            case = dict(geometry=[w,h],full_geometry=[row['width'],row['height']],depth=8,
                downsample=[[1,row['divisor']],[1,row['divisor']]],geometry_sampler='realistic-v2',
                checkout_rect=[0,0,w,h],request_rect=[0,0,w,h],extent_hint=[0,0,w,h],pixel_aspect=[1,1],
                rowbytes_padding=0,input_padding=0,output_padding=0,pixels=pixels,parameters=params)
            result.update(input_sha256=sha(pixels),parameters=params)
            route = 'classic' if name=='olmsmoother' else 'smart'
            if row['width'] <= 1920 and row['height'] <= 1080:
                status, raw = adapter.oracle(case,case_dir,time.monotonic()+args.timeout,route)
                result['original'] = status
            else:
                status, raw = {'status':'not-run','reason':'4K uses bundle fallback'},b''
                result['original'] = status
            if status['status'] != 'ok':
                status, raw, guards = adapter.candidate(case,case_dir,route,time.monotonic()+args.timeout)
                result['bundle'] = dict(status,refusals=guards)
            if status['status'] == 'ok' and len(raw)==ae.stat().st_size:
                reference = case_dir / 'reference.argb'
                reference.write_bytes(raw)
                result['comparison'] = compare(ae,reference,w,h,8)
                original = np.frombuffer(raw,dtype=np.uint8).reshape(h,w,4)
                actual = rgba[:, :, [3,0,1,2]]
                differs = original != actual
                transparent_rgb = (original[:,:,0] == 0) & (actual[:,:,0] == 0)
                only_hidden = not np.any(differs[:,:,0]) and not np.any(differs[:,:,1:] & ~transparent_rgb[:,:,None])
                result['comparison']['classification'] = ('I/O conversion: hidden RGB at zero alpha lost in premultiplied export'
                    if not result['comparison']['exact'] and only_hidden else
                    None if result['comparison']['exact'] else 'unresolved: host geometry/color management/plugin')
                reference.unlink()
            else:
                result['comparison'] = {'exact':None,'reason':'reference unavailable or negotiated output differs'}
        ae.unlink()
        results.append(result)
        (state/'comparisons.json').write_text(json.dumps(results,indent=2)+'\n')
        print(prefix, result.get('comparison',result.get('io')),flush=True)

if __name__=='__main__':
    main()
