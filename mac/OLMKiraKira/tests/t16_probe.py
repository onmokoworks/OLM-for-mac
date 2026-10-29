#!/usr/bin/env python3
"""T16 read-only fixture audit and serial original-AEX/public-Mac comparison.

Run with MAIN's emulation venv (numpy/Pillow). The source PNG stays in the
external fixture. This deliberately does not claim to recreate AE's color
management, footage interpretation, layer opacity, or final composition.
"""
import argparse
import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[3]
MAIN = Path('/Users/onmk/Documents/Projects/Personal/OLM as')
FIXTURE = Path.home()/'.cache/olm-emu/fixtures/T18-mac-open-test'
TICKET = 'T16-kirakira-multidirection-gain-mismatch'
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT/'tools/fuzz'))
from adapters.olmkirakira import Adapter
from core import sha


class UIAdapter(Adapter):
    """Materialize UI degrees according to the actual production PARAMS_SETUP."""
    def candidate_command(self, case, directory, route):
        mapped = copy.deepcopy(case)
        rotation = next(p for p in mapped['parameters'] if p['slot'] == 40)
        degrees = rotation['value']
        # Bypass the historical adapter's integer rounding of raw fixed words:
        # this host starts with actual (possibly fractional) UI degrees.
        rotation['value'] = 0
        command, data = super().candidate_command(mapped, directory, route)
        config = directory/'params.txt'
        config.write_text(''.join(f'40 s {degrees}\n' if line.startswith('40 ')
                                  else line for line in config.read_text().splitlines(True)))
        return command, data

    def compile_sdk(self, scratch, body, source, deadline, cores=()):
        callbacks = r'''
static PF_ParamType t16_rotation_type = PF_Param_RESERVED;
static PF_Err t16_add(PF_ProgPtr, A_long, PF_ParamDef *p) {
    if (p->uu.id == GLOW_ROTATION_DISK_ID) t16_rotation_type = p->param_type;
    if (p->param_type == PF_Param_ARBITRARY_DATA && p->u.arb_d.value)
        host_dispose_handle((PF_Handle)p->u.arb_d.value);
    return PF_Err_NONE;
}
static PF_Err t16_register(PF_ProgPtr, PF_CustomUIInfo *) { return PF_Err_NONE; }
'''
        body = body.replace('int main(int argc,char **argv) {', callbacks+'\nint main(int argc,char **argv) {')
        before = '    init_params(kTuples[0]);'
        setup = r'''
    PF_InData setup_in{}; PF_OutData setup_out{};
    setup_in.pica_basicP=&g_basic;
    setup_in.inter.add_param=t16_add; setup_in.inter.register_ui=t16_register;
    if (EffectMain(PF_Cmd_PARAMS_SETUP,&setup_in,&setup_out,nullptr,nullptr,nullptr)) return 71;
    if (t16_rotation_type!=PF_Param_ANGLE && t16_rotation_type!=PF_Param_FLOAT_SLIDER) return 72;
    fprintf(stderr,"ROTATION_TYPE %d\n",int(t16_rotation_type));
'''
        assert body.count(before)==1
        body = body.replace(before,setup+before)
        before = '    PF_EffectWorld iw{},ow{};'
        decode = r'''
    const double degrees=g_defs[OLMKIRAKIRA_GLOW_ROTATION].u.fs_d.value;
    g_defs[OLMKIRAKIRA_GLOW_ROTATION].param_type=t16_rotation_type;
    if (t16_rotation_type==PF_Param_ANGLE)
        g_defs[OLMKIRAKIRA_GLOW_ROTATION].u.ad.value=(PF_Fixed)llround(degrees*65536.0);
'''
        assert body.count(before)==1
        body=body.replace(before,decode+before)
        return super().compile_sdk(scratch,body,source,deadline,cores)


def audit():
    requested = FIXTURE/'evidence/requested.json'
    data = json.loads(requested.read_text(encoding='utf-8-sig'))
    effect = next(e for e in data['effects'] if e['matchName'] == 'OLM OLM Kira Kira')
    return dict(requested_path=str(requested), requested_sha256=sha(requested.read_bytes()),
                effect=effect, source_path=str(FIXTURE/'footage/source_rgba16.png'),
                source_sha256=sha((FIXTURE/'footage/source_rgba16.png').read_bytes()))


def pixels(width, height):
    import numpy as np
    from PIL import Image
    # Explicit comparable soft-alpha input, not an inferred AE input world.
    im = Image.open(FIXTURE/'footage/source_rgba16.png').convert('RGBA')
    if im.size != (width, height):
        im = im.resize((width, height), Image.Resampling.BILINEAR)
    rgba = np.array(im, dtype=np.uint8)
    rgba[..., :3] = np.rint(rgba[..., :3].astype(np.float64)*rgba[..., 3:4]/255).astype(np.uint8)
    return rgba[..., [3, 0, 1, 2]].tobytes()


def case(adapter, args, evidence):
    c = dict(seed=16, index=0, geometry=[args.width,args.height], depth=8,
             profile='T18-Pillow8-premultiplied', parameters=adapter.defaults(args.width,args.height),
             input_padding=0, output_padding=0, pixels=pixels(args.width,args.height))
    p = {v['slot']:v for v in c['parameters']}
    if args.parameters == 'fixture':
        for value in evidence['effect']['params']:
            slot, v = value['index'], value['value']
            if isinstance(v, list):
                # Public adapter's captured PF8 color suite contract.
                v = [round(v[3]*255), *[round(x*255) for x in v[:3]]]
            p[slot]['value'] = v
    else:
        for slot,v in {1:4,2:3,3:3,5:18,6:80,8:65,9:75,10:12,16:16,22:10,28:8,34:3,40:17}.items():
            p[slot]['value'] = v
    for override in args.set:
        slot,value = override.split('=',1)
        p[int(slot)]['value'] = float(value)
    # Historical test transport sends raw fixed integers to the Windows owner.
    # UI mode instead materializes the type declared by PARAMS_SETUP.
    if args.rotation == 'raw-fixed':
        p[40]['value'] /= 65536
    if args.rays != 'all':
        enabled = set(args.rays.split(','))
        for slot,name in zip((10,16,22,28,34),('v','h','d','d2','highlight')):
            if name not in enabled:
                p[slot]['value'] = 0
    return c


def diff(ref, actual, width):
    import numpy as np
    a = np.frombuffer(ref,dtype=np.uint8).reshape(-1,4)
    b = np.frombuffer(actual,dtype=np.uint8).reshape(-1,4)
    delta = np.abs(a.astype(np.int16)-b)
    where = np.argwhere(delta != 0)
    first = None
    if len(where):
        pixel,channel = map(int,where[0])
        first = dict(x=pixel%width,y=pixel//width,channel_argb=channel,
                     expected=int(a[pixel,channel]),actual=int(b[pixel,channel]))
    return dict(different_pixels=int(np.count_nonzero(np.any(delta,axis=1))),
                different_samples=int(np.count_nonzero(delta)),max_abs=int(delta.max()),first=first)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--label',required=True)
    parser.add_argument('--width',type=int,default=192)
    parser.add_argument('--height',type=int,default=108)
    parser.add_argument('--parameters',choices=('fixture','brief'),default='fixture')
    parser.add_argument('--rotation',choices=('raw-fixed','ui'),default='raw-fixed')
    parser.add_argument('--set',action='append',default=[])
    parser.add_argument('--rays',default='all')
    parser.add_argument('--timeout',type=int,default=180)
    parser.add_argument('--worker',type=Path,default=Path.home()/'.cache/olm-emu/worker-F46-pow/aex-guest-worker')
    parser.add_argument('--rebuild',action='store_true')
    parser.add_argument('--compare-binary',type=Path,
                        help='Pre-fix public host with the original FLOAT_SLIDER rotation field')
    parser.add_argument('--audit-only',action='store_true')
    args=parser.parse_args()
    s=ROOT/'orchestra/state'/TICKET/args.label
    s.mkdir(parents=True,exist_ok=True)
    os.environ.update(TMPDIR=str(s),TMP=str(s),TEMP=str(s),PYTHONDONTWRITEBYTECODE='1')
    evidence=audit()
    (s/'fixture-audit.json').write_text(json.dumps(evidence,indent=2)+'\n')
    if args.audit_only:
        print(json.dumps(evidence,indent=2));return
    pressure=subprocess.check_output(['memory_pressure'],text=True)
    (s/'memory-pressure.txt').write_text(pressure)
    free=int(pressure.rsplit('System-wide memory free percentage: ',1)[1].split('%')[0])
    if free < 30:
        raise RuntimeError(f'memory free {free}% below required 30%')
    adapter=UIAdapter if args.rotation=='ui' else Adapter
    a=adapter(SimpleNamespace(main=MAIN,worker=args.worker,max_size=4096,case_timeout=args.timeout))
    c=case(a,args,evidence)
    deadline=time.monotonic()+args.timeout+300
    build=ROOT/'orchestra/state'/TICKET/('build-ui' if args.rotation=='ui' else 'build')
    build.mkdir(exist_ok=True)
    if (build/'mac').exists() and not args.rebuild:
        a.binary=build/'mac'; a.env.update(TMPDIR=str(s),TMP=str(s),TEMP=str(s))
    else:
        prov=a.prepare(build,deadline)
        (build/'provenance.json').write_text(json.dumps(prov,indent=2)+'\n')
    record=dict(options={k:str(v) if isinstance(v,Path) else v for k,v in vars(args).items()},
                case={k:v for k,v in c.items() if k!='pixels'},input_sha256=sha(c['pixels']),
                worker_sha256=sha(a.worker.read_bytes()),aex_sha256=sha(a.aex.read_bytes()),
                candidate_sha256=sha(a.binary.read_bytes()),routes={})
    (s/'input.argb8').write_bytes(c['pixels'])
    for route in ('smart','classic'):
        result,raw,guards=a.candidate(c,s,route,deadline)
        record['routes'][route]=dict(result=result,guards=guards,sha256=sha(raw))
        if raw:(s/f'mac-{route}.argb8').write_bytes(raw)
    if args.compare_binary:
        baseline=copy.copy(a)
        baseline.binary=args.compare_binary.resolve()
        result,raw,guards=baseline.candidate(c,s,'smart',deadline)
        record['before']=dict(result=result,guards=guards,sha256=sha(raw),
                              candidate_sha256=sha(baseline.binary.read_bytes()))
        if raw:(s/'before-smart.argb8').write_bytes(raw)
    start=time.monotonic()
    oracle,ref=a.oracle(c,s,deadline,'smart')
    record.update(oracle=oracle,oracle_seconds=time.monotonic()-start,oracle_sha256=sha(ref))
    if ref:
        (s/'aex-smart.argb8').write_bytes(ref)
        for route,entry in record['routes'].items():
            if entry['result']['status']=='ok':
                entry['diff_against_aex_smart']=diff(ref,(s/f'mac-{route}.argb8').read_bytes(),args.width)
        if args.compare_binary and record['before']['result']['status']=='ok':
            record['before']['diff_against_aex_smart']=diff(ref,(s/'before-smart.argb8').read_bytes(),args.width)
    (s/'result.json').write_text(json.dumps(record,indent=2)+'\n')
    print(json.dumps({k:record[k] for k in ('oracle','oracle_seconds','routes','before') if k in record},indent=2))


if __name__=='__main__':
    main()
