#!/usr/bin/env python3
"""Bind real AE outputs/readbacks to original F53 and the installed bundle.

Reduced-resolution controls supply the host-resampled input. This is a measured
output input proxy, not a plugin checkout trace. Geometry assumptions are explicit.
"""
import argparse
import json
import os
from pathlib import Path
import sys
import struct
import time
from types import SimpleNamespace
import numpy as np
import tifffile
from compare import compare

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools/fuzz'))
from core import sha, command
from run import main_checkout
from adapters.plugin_bundle import Adapter
from geometry import require_host


def full_frame_bundle(adapter, case, directory, route, timeout):
    """F51 is a full-frame 1:1 host; never use it for downsample or ROI."""
    if case['downsample'] != [[1,1],[1,1]] or case['geometry'] != case['full_geometry']:
        raise ValueError('F51 fallback requires full-frame 1:1 geometry')
    declarations = getattr(adapter,'declarations',None) or adapter.binding['parameters']
    types = [0]*(max(d['slot'] for d in declarations)+1)
    for d in declarations: types[d['slot']] = d['param_type']
    schema, params = directory/'f51-schema.txt', directory/'f51-params.txt'
    schema.write_text(str(len(types))+'\n'+'\n'.join(map(str,types))+'\n')
    params.write_text(''.join(str(p['slot'])+' '+p['kind']+' '+(' '.join(map(str,p['value'])) if isinstance(p['value'],list) else str(p['value']))+'\n' for p in case['parameters']))
    # V01 retains the F51/F47d full-frame transport with ordinary iterate support.
    host = Path.home()/'.cache/olm-emu/worker-V01-universal/full'
    env = dict(adapter.env, OLM_REFUSAL_TRACE=str(directory/'f51-refusals.txt'))
    if adapter.name == 'olmkirakira': env['OLM_NATIVE_PARAMETER_PROFILE']='kirakira-default-ramps'
    status, raw, err = command([host,adapter.executable,*case['geometry'],case['depth'],0,int(route=='smart'),schema,params],
        data=case['pixels'],timeout=timeout,deadline=time.monotonic()+timeout,env=env)
    status.update(host_path=str(host),host_sha256=sha(host.read_bytes()),native_trace=err.decode(errors='replace'))
    if status['status']=='ok':
        if len(raw)!=len(case['pixels'])+4:
            status.update(status='harness_error',diagnostic='F51 output length')
        elif struct.unpack('<i',raw[:4])[0]:
            status.update(status='refusal',error=struct.unpack('<i',raw[:4])[0])
        elif 'F47c counters' not in status['native_trace']:
            status.update(status='harness_error',diagnostic='F51 selector evidence missing')
        else:
            return status,raw[4:]
    return status,b''


def load_rgba(path, depth):
    if path.suffix == '.exr':
        import OpenEXR
        channels = OpenEXR.File(str(path), separate_channels=True).channels()
        if any(channels[c].pixels.dtype != np.float32 for c in 'RGBA'):
            raise ValueError('FLOAT EXR required')
        rgba = np.stack([channels[c].pixels for c in 'RGBA'], axis=-1)
        if depth == 16:
            scaled = rgba * np.float32(32768)
            if not np.all(np.isfinite(scaled)) or np.any(scaled < 0) or np.any(scaled > 65535) or not np.all(scaled == np.rint(scaled)):
                raise ValueError('16 bpc FLOAT export is not exact integer/32768')
            rgba = scaled.astype('<u2')
        return rgba
    if path.suffix == '.png':
        from PIL import Image
        with Image.open(path) as image:
            if depth != 8 or image.mode != 'RGBA':
                raise ValueError('8 bpc RGBA PNG required')
            return np.array(image)
    rgba = tifffile.imread(path)
    if depth != 8 or rgba.dtype != np.uint8:
        raise ValueError('Only 8 bpc TIFF accepted; use FLOAT EXR for deeper projects')
    return rgba


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
    prior = {r['outputPrefix']:r for r in results}
    completed = {r['outputPrefix'] for r in results if r.get('comparison',{}).get('exact') is not None or 'io' in r}
    for row in rendered:
        if row['status'] == 'error':
            continue
        prefix = row['outputPrefix']
        if prefix in completed:
            continue
        depth = row['depth']
        extension = row.get('outputExtension', 'exr' if depth == 32 else 'tif')
        path = next(state.glob(prefix + '_*.' + extension))
        rgba = load_rgba(path, depth)
        h, w = rgba.shape[:2]
        case_dir = out / prefix
        case_dir.mkdir(exist_ok=True)
        ae = case_dir / 'ae.argb'
        ae.write_bytes(rgba[:, :, [3, 0, 1, 2]].tobytes())
        result = dict(outputPrefix=prefix, plugin=row['plugin'], geometry=[w,h],
                      full_geometry=[row['width'],row['height']], divisor=row['divisor'], depth=depth,
                      resolution_readback=row['renderSettings']['Resolution'],
                      assumptions='input=matching no-effect control; checkout origin=0; full-frame extent; downsample=queue rational; no live InData trace')
        if row['plugin'] == 'control':
            if row['divisor'] == 1:
                project = next(p for p in json.loads((state/'build.json').read_text())['projects']
                               if any(i['outputPrefix']==prefix for i in p['items']))
                source = Path(project['input']['raw']) if 'input' in project else Path(project['path']).parent / 'inputs' / f"input-{row['width']}x{row['height']}-{depth}.argb"
                result['io'] = compare(ae, source, w, h, depth)
            else:
                result['io'] = {'exact': None, 'note': 'resampling is not an identity I/O test'}
        else:
            control_prefix = prefix.replace(row['plugin'], 'control', 1)
            full_control = control_prefix.rsplit('-d',1)[0]+'-d1'
            calibration = next((r.get('io',{}) for r in results if r['outputPrefix']==full_control),{})
            if calibration.get('exact') is not True:
                result['comparison'] = {'exact':None,'reason':'full-resolution I/O control is not exact',
                                        'classification':'I/O conversion'}
                ae.unlink()
                results = [r for r in results if r['outputPrefix']!=prefix]+[result]
                result_path.write_text(json.dumps(results,indent=2)+'\n')
                print(prefix,result['comparison'],flush=True)
                continue
            name = 'radialblur' if row['plugin'] == 'OLMRadialBlur' else row['plugin'].lower()
            options = SimpleNamespace(plugin=name, plugin_bundle=Path('/Applications/Adobe After Effects 2026/Plug-ins/OLM-smoke')/(row['plugin']+'.plugin'),
                main=main_checkout(), worker=Path.home()/'.cache/olm-emu/worker-F53-geom/aex-guest-worker',max_size=4096,case_timeout=args.timeout)
            adapter = Adapter(options)
            require_host(adapter, {'geometry_sampler':'realistic-v2'})
            result['provenance'] = adapter.prepare(case_dir, time.monotonic()+args.timeout)
            control_prefix = prefix.replace(row['plugin'], 'control', 1)
            control = load_rgba(next(state.glob(control_prefix + '_*.' + extension)), depth)
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
            case = dict(geometry=[w,h],full_geometry=[row['width'],row['height']],depth=depth,
                downsample=[[1,row['divisor']],[1,row['divisor']]],geometry_sampler='realistic-v2',
                checkout_rect=[0,0,w,h],request_rect=[0,0,w,h],extent_hint=[0,0,w,h],pixel_aspect=[1,1],
                rowbytes_padding=0,input_padding=0,output_padding=0,pixels=pixels,parameters=params)
            result.update(input_sha256=sha(pixels),parameters=params)
            if row.get('corpus'):
                project = next(p for p in json.loads((state/'build.json').read_text())['projects']
                               if any(i['outputPrefix'] == prefix for i in p['items']))
                requested = project['input']['parameters']
                observed = {p['slot']: p for p in params}
                differences = [dict(requested=p, observed=observed.get(p['slot']))
                               for p in requested if observed.get(p['slot']) != p]
                result['corpus_binding'] = dict(path=row['corpus'], sha256=row['corpus_sha256'],
                    parameter_differences=differences, parameters_exact=not differences,
                    input_exact=sha(pixels) == project['input']['source_sha256'])
            route = 'classic' if name=='olmsmoother' else 'smart'
            if w <= 1920 and h <= 1080:
                status, raw = adapter.oracle(case,case_dir,time.monotonic()+args.timeout,route)
                result['original'] = status
            else:
                status, raw = {'status':'not-run','reason':'4K uses bundle fallback'},b''
                result['original'] = status
            if status['status'] != 'ok':
                if row['divisor']==1 and (w>1920 or h>1080):
                    status, raw = full_frame_bundle(adapter,case,case_dir,route,args.timeout)
                    result['bundle'] = status
                    if prefix in prior:
                        result['previous_reference_attempt'] = prior[prefix].get('bundle')
                else:
                    status, raw, guards = adapter.candidate(case,case_dir,route,time.monotonic()+args.timeout)
                    result['bundle'] = dict(status,refusals=guards)
            if status['status'] == 'ok' and len(raw)==ae.stat().st_size:
                reference = case_dir / 'reference.argb'
                reference.write_bytes(raw)
                result['comparison'] = compare(ae,reference,w,h,depth)
                original = np.frombuffer(raw,dtype={8:np.uint8,16:np.dtype('<u2'),32:np.dtype('<f4')}[depth]).reshape(h,w,4)
                actual = rgba[:, :, [3,0,1,2]]
                differs = original.view(np.uint32) != actual.view(np.uint32) if depth == 32 else original != actual
                transparent_rgb = (original[:,:,0] == 0) & (actual[:,:,0] == 0)
                only_hidden = not np.any(differs[:,:,0]) and not np.any(differs[:,:,1:] & ~transparent_rgb[:,:,None])
                result['comparison']['classification'] = ('I/O conversion: hidden RGB at zero alpha lost in premultiplied export'
                    if not result['comparison']['exact'] and only_hidden else
                    None if result['comparison']['exact'] else 'unresolved: host geometry/color management/plugin')
                reference.unlink()
            else:
                result['comparison'] = {'exact':None,'reason':'reference unavailable or negotiated output differs'}
        ae.unlink()
        results = [r for r in results if r['outputPrefix'] != prefix]
        results.append(result)
        (state/'comparisons.json').write_text(json.dumps(results,indent=2)+'\n')
        print(prefix, result.get('comparison',result.get('io')),flush=True)

if __name__=='__main__':
    main()
