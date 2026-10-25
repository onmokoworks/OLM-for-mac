"""Shared typed session transport for existing per-plugin public replay hosts.

Wire types follow probe_olmcolorkey_typed_controls_20261001.native_render and
probe_directionalblur_general_features_20261001.native_render. No numerical
emulator or production algorithm is implemented here.
"""
from __future__ import annotations
import copy
import json
import math
import os
from pathlib import Path
import random
import re
import struct
import tempfile
import time
from core import case_seed, command, sha

ROOT = Path(__file__).resolve().parents[3]
KINDS = {1:'i', 2:'f', 3:'a', 4:'b', 5:'c', 6:'p', 7:'u', 10:'s'}


def replace_once(body, old, new):
    if body.count(old) != 1:
        raise ValueError(f'Public helper drift: {old!r}')
    return body.replace(old, new)


def messages(raw):
    result, pos = [], 0
    while pos < len(raw):
        n = struct.unpack_from('<I', raw, pos)[0]
        pos += 4
        result.append(json.loads(raw[pos:pos+n]))
        pos += n
    return result


class PublicAdapter:
    generator_version = 1
    routes = ('classic', 'smart')
    aex_name = None
    oracle_route = 'smart'
    oracle_path = 'smartfx'
    oracle_routes = {'classic': 'classic', 'smart': 'smart'}
    original_routes = {'classic': 'render', 'smart': 'render'}
    no_write_fill = None
    # Override only sampling weights/subsets, never the builder's legal bounds.
    small_controls = ()

    def __init__(self, options):
        self.reference_build = getattr(options, "reference_build", False)
        self.max_size = options.max_size
        self.size_max_height = getattr(options, "size_max_height", None)
        self.size_sampler = getattr(options, "size_sampler", "default")
        self.timeout = options.case_timeout
        self.main = options.main.resolve()
        self.worker = options.worker.resolve()
        self.aex = self.main/'plugins_2025'/f'{self.aex_name}.aex'
        self.declaration_path = ROOT/f'tools/fuzz/declarations/{self.name}.json'
        self.binding = json.loads(self.declaration_path.read_text())
        self.controls = [d for d in self.binding['parameters'] if d['param_type'] in KINDS]
        self.env = dict(os.environ)
        for key in list(self.env):
            if key.startswith(('OLM', 'DBLUR', 'COLORKEEP')):
                del self.env[key]
        self.binary = None

    def defaults(self, w, h):
        result = []
        for d in self.controls:
            kind = KINDS[d['param_type']]
            value = d['default_value']
            if kind == 'a':
                value = d['default_components'][0]
            elif kind == 'p':
                value = [round(v*extent/100*65536)/65536 for v,extent in zip(d['default_components'], (w,h))]
            elif kind == 'c':
                value = list(d['default_color'])
            elif kind in ('i','u','b'):
                value = int(value)
            # Some original builders declare an out-of-range default (Kira gain,
            # DistanceGradation In/Out). Keep the snapshot, sample legal bounds.
            if kind not in ('a','p','c'):
                value = max(d['valid_min'], min(d['valid_max'], value))
                if kind in ('i','u','b'):
                    value = int(value)
            result.append({'slot':d['slot'], 'kind':kind, 'value':value})
        return result

    def generate(self, seed, index):
        rng = random.Random(case_seed(seed, index))
        mode = rng.random()
        if mode < .08:
            w,h = 1,1
        elif mode < .24:
            n = rng.randint(1,self.max_size)
            w,h = (1,n) if rng.getrandbits(1) else (n,1)
        else:
            limit = min(self.max_size,24 if mode<.8 else 64 if mode<.95 else self.max_size)
            w,h = rng.randint(1,limit),rng.randint(1,limit)
        from sizes import selected
        w, h = selected(self, seed, index, (w, h))
        depth = rng.choice([8,16,32])
        params = self.defaults(w,h)
        count = rng.randint(1,min(6,len(params))) if rng.random()<.9 else len(params)
        for i in rng.sample(range(len(params)),count):
            p,d = params[i],self.controls[i]
            kind = p['kind']
            if kind == 'p':
                p['value'] = [rng.randint(-n*65536,2*n*65536)/65536 for n in (w,h)]
            elif kind == 'a':
                p['value'] = rng.randint(-720*65536,720*65536)/65536
            elif kind == 'c':
                p['value'] = [rng.choice([0,128,255]), *[rng.randrange(256) for _ in range(3)]]
            else:
                lo,hi = d['valid_min'],d['valid_max']
                if p['slot'] in self.small_controls and rng.random()<.75:
                    hi = min(hi,max(lo,30))
                if kind in ('i','u','b'):
                    p['value'] = rng.randint(math.ceil(lo),math.floor(hi))
                elif kind == 'f':
                    p['value'] = rng.randint(math.ceil(lo*65536),math.floor(hi*65536))/65536
                else:
                    p['value'] = rng.choice([lo,hi,rng.uniform(lo,hi),rng.uniform(lo,hi)])
        profile = rng.choices(['sdr','hdr','signed','nonfinite'],[65,15,15,5])[0] if depth==32 else 'sdr'
        pixels = bytearray()
        for _ in range(w*h):
            if depth in (8,16):
                top = 255 if depth==8 else 32768
                values = [rng.choice([0,top,rng.randint(1,top-1)]),*[rng.randint(0,top) for _ in range(3)]]
                pixels.extend(struct.pack('<4B' if depth==8 else '<4H',*values))
            else:
                lo,hi = (-4,4) if profile=='signed' else (0,8) if profile=='hdr' else (0,1)
                for v in [rng.choice([0.,1.,.5,rng.uniform(lo,hi)]),*[rng.uniform(lo,hi) for _ in range(3)]]:
                    pixels.extend(struct.pack('<I',rng.choice([0x7f800000,0xff800000,0x7fc12345,0xff812346,0x80000000]))
                                  if profile=='nonfinite' and rng.random()<.25 else struct.pack('<f',v))
        return dict(seed=seed,index=index,geometry=[w,h],depth=depth,profile=profile,
                    parameters=params,pixels=bytes(pixels),input_padding=rng.choice([0,1,3,7,16]),
                    output_padding=rng.choice([0,1,5,11,32]))

    def resize(self, case, old_geometry):
        for p in case['parameters']:
            if p['kind']=='p':
                p['value'] = [round(v*n/o*65536)/65536 for v,n,o in zip(p['value'],case['geometry'],old_geometry)]
        return case

    def simple_pixels(self, case):
        fmt,cut,top = {8:('B',128,255),16:('H',16384,32768),32:('f',.5,1.)}[case['depth']]
        return b''.join(struct.pack('<'+fmt,top if math.isfinite(v) and v>=cut else 0)
                        for (v,) in struct.iter_unpack('<'+fmt,case['pixels']))

    def prepare(self, scratch, deadline):
        if sha(self.aex.read_bytes()) != self.binding['aex_sha256']:
            raise ValueError('Original AEX hash differs from captured PARAMS_SETUP')
        self.env.update(TMPDIR=str(scratch),TMP=str(scratch),TEMP=str(scratch))
        self.binary, dependencies = self.build(scratch,deadline)
        dependencies = [*dependencies, *sorted({header for source in dependencies for header in source.parent.glob('*.h')}), ROOT/'tools/fuzz/harnesses/geometry.hpp', *sorted((ROOT/'ucrtmath/src').glob('*')), ROOT/'ucrtmath/include/ucrtmath.h', ROOT/'ucrtmath/build.sh']
        return {'reference_build':self.reference_build, 'aex_path':str(self.aex),'aex_sha256':sha(self.aex.read_bytes()),
                'worker_path':str(self.worker),'worker_sha256':sha(self.worker.read_bytes()),
                'candidate_sha256':sha(self.binary.read_bytes()),
                'dependencies_sha256':{str(p.relative_to(ROOT)):sha(p.read_bytes()) for p in dependencies},
                'declarations_sha256':sha(self.declaration_path.read_bytes()),
                'out_of_range_builder_defaults':[{'slot':d['slot'],'builder_default':d['default_value'],
                    'sampled_default':p['value']} for d,p in zip(self.controls,self.defaults(1,1))
                    if p['kind'] not in ('a','p','c') and p['value']!=d['default_value']],
                'host':'Original AEX Unicorn CPU per-route; production Mac EffectMain Classic + Smart fake host',
                'oracle_routes':self.oracle_routes, 'original_routes':self.original_routes,
                'oracle_render_path':self.oracle_path,
                'time':{'value':0,'scale':24,'step':1,'total':1},
                'world':('realistic-v1: sampled input, byte padding, extent, request, aspect; PreRender output rectangle/origin; packed ARGB' if getattr(self,'geometry_active',False) else 'full frame, origin 0, downsample 1:1, raw ARGB, no conversion'),
                'layer':'None; independent layer worlds outside this adapter',
                'stage_support':'existing public replay helpers expose final raw output only',
                'reference_limit':'Retained host imports are not native Windows UCRT or AE proof',
                **self.scope()}

    def scope(self):
        return {}

    def compile(self, argv, deadline):
        if str(argv[0]) == "clang++" and self.reference_build:
            argv = [*argv, "-DOLM_REFERENCE_BUILD=1"]
        # Link the independent C implementation into every public harness.
        if str(argv[0]) == 'clang++' and '-o' in argv and '-c' not in argv:
            out = Path(argv[argv.index('-o') + 1]).parent / 'ucrtmath'
            self.compile(['sh', ROOT/'ucrtmath/build.sh', out], deadline)
            argv = [*argv, out/'libucrtmath.a']
        status,out,err = command(argv,timeout=max(0,deadline-time.monotonic()),deadline=deadline,env=self.env)
        if status['status']!='ok':
            raise RuntimeError('Public harness build failed: '+repr(status)+' '+err.decode(errors='replace')[-4000:])
        return out

    def geometry_host(self, body):
        # The macro wraps only host calls; production source is included first.
        pattern = r'(#include (?:"[^"\n]+/mac/[^"\n]+\.cpp"|KIRA_SOURCE)[^\n]*\n)'
        body, count = re.subn(pattern, lambda m: m[0]+'#include "'+str(ROOT/'tools/fuzz/harnesses/geometry.hpp')+'"\n', body)
        if count != 1:
            raise ValueError('F52 geometry host requires one production source include')
        return body

    def compile_sdk(self, scratch, body, source, deadline, cores=()):
        body = self.geometry_host(body)
        host = scratch/'host.cpp';host.write_text(body)
        binary = scratch/'mac'
        sdk = self.compile(['xcrun','--show-sdk-path'],deadline).decode().strip()
        self.compile(['clang++','-std=c++17','-arch','arm64','-O2','-fno-fast-math','-ffp-contract=off',
            '-Wno-deprecated-declarations','-Wno-pragma-pack','-ffunction-sections','-fdata-sections',
            '-isysroot',sdk,*[x for p in ('Headers','Headers/SP','Util','Resources') for x in ('-I',self.main/p)],
            '-I',ROOT/'core',host,source.with_name(source.stem+'_Strings.cpp'),*cores,
            self.main/'Util/AEGP_SuiteHandler.cpp',self.main/'Util/MissingSuiteError.cpp',
            '-Wl,-dead_strip','-framework','Cocoa','-o',binary],deadline)
        return binary

    def oracle(self, case, directory, deadline, route=None):
        with tempfile.TemporaryDirectory(prefix='native_',dir=directory) as td:
            return self._oracle(case,Path(td),deadline,route)

    def _oracle(self, case, directory, deadline, route=None):
        selected = self.oracle_route if route is None else route
        expected_path = self.oracle_path if route is None else {"classic":"classic", "smart":"smartfx"}[route]
        ip,op = directory/'input.raw',directory/'output.raw'
        ip.write_bytes(case['pixels'])
        encoded = []
        for p in case['parameters']:
            kind = {'a':'angle','p':'point','c':'argb8'}.get(p['kind'],'f64')
            value = p['value']
            if p['kind']=='p':
                value = [v*100/n for v,n in zip(value,case['geometry'])]
            value = ','.join(map(str,value)) if isinstance(value,list) else str(value)
            encoded.append(f"param_{p['slot']}@{p['slot']}:{kind}={value}")
        request = json.dumps({'v':4,'type':'render_frame','frame_index':0,
            'current_time':{'value':0,'scale':24,'step':1,'total':1},'parameters':'v4|'+';'.join(encoded)}).encode()
        env = self.env
        float_colors = {str(p['slot']): p['float_value'] for p in case['parameters'] if 'float_value' in p}
        if float_colors:
            if hasattr(self, 'bundle'):
                raise ValueError('S02 float colour fixtures are not yet supported by the bundle bridge')
            metadata = self.worker.parent/'build.json'
            if not metadata.exists() or json.loads(metadata.read_text()).get('capability') != 'S02-float-colors-v1':
                raise ValueError('Independent float colours require a registered S02 F53/F54 worker')
            env = dict(env, OLM_FLOAT_COLOR_VALUES=json.dumps(float_colors, allow_nan=False))
        status,out,err = command([self.worker,'session',self.aex,ip,op,*case.get('full_geometry',case['geometry']),'24',
            *[v for axis,ratio in zip(('x','y'),case.get('downsample',[])) for v in ('--downsample-'+axis, '/'.join(map(str,ratio)))],
            *geometry_arguments(case,selected),
            '--pixel-format',{8:'argb8',16:'argb16',32:'argb32f'}[case['depth']],
            *(['--fixture-render-path',selected] if selected else []),
            *getattr(self, 'session_arguments', lambda case, directory: [])(case, directory)],data=struct.pack('<I',len(request))+request,
            timeout=self.timeout,deadline=deadline,env=env)
        observer = getattr(self, 'session_observed', None)
        if observer is not None:
            observer(out, err)
        if status['status']!='ok':
            reason = err.decode(errors='replace')
            if status['status']!='budget':
                status['status'] = 'budget' if any(x in reason.lower() for x in ('timeout','budget','instruction limit','deadline')) else 'reject'
            return dict(status,diagnostic=reason[:800]+reason[-800:] if len(reason)>1600 else reason),b''
        try:
            decoded = messages(out)
            setup = next(m['setup'] for m in decoded if m['type']=='session_ready')
            frame = next(m for m in decoded if m['type']=='frame_done')
            close = next(m['close'] for m in decoded if m['type']=='session_closed')
            keys = ('slot','param_type','valid_min','valid_max','default_value','default_components','default_color')
            actual = [{k:d.get(k) for k in keys} for d in setup['parameters']]
            expected = [{k:d.get(k) for k in keys} for d in self.binding['parameters']]
            if actual!=expected:
                return {'status':'harness_error','diagnostic':'live builder declaration drift'},b''
            if setup['global_setup_error'] or setup['params_setup_error'] or frame['status']!='ok' or frame['render_error']:
                return {'status':'reject','diagnostic':json.dumps(frame)[-1600:]},b''
            raw = op.read_bytes()
            if not (frame['output']['guards_intact'] and frame['output']['checksum']==sha(raw)
                    and len(raw)==(frame['output']['width']*frame['output']['height']*case['depth']//8*4 if case.get('geometry_sampler') else len(case['pixels'])) and frame['output']['render_path']==expected_path
                    and close['session_clean'] and not close['unsupported_suite_calls']
                    and not close['dropped_unsupported_suite_calls']):
                return {'status':'harness_error','diagnostic':'guard/checksum/size/route/session invariant'},b''
            return {'status':'ok','guards_intact':True,'session_clean':True,**({'output_rect':frame['output']['rect']} if case.get('geometry_sampler') else {})},raw
        except (KeyError,ValueError,StopIteration,OSError,struct.error) as exc:
            return {'status':'harness_error','diagnostic':repr(exc)},b''

    def candidate(self, case, directory, route, deadline, env=None):
        argv,data = self.candidate_command(case,directory,route)
        environment = dict(env or self.env)
        if 'downsample' in case:
            values = [*case['full_geometry'], *case['downsample'][0], *case['downsample'][1]]
            environment['OLM_F52_DOWNSAMPLE'] = ','.join(map(str,values))
        geometry_environment(case,directory,environment)
        status,out,err = command(argv,data=data,timeout=self.timeout,deadline=deadline,env=environment)
        if status['status']!='ok':
            return dict(status,diagnostic=err.decode(errors='replace')[-1600:]),b''
        try:
            if self.output_format=='hex':
                metadata = dict(line.split(' ',1) for line in out.decode().splitlines())
                raw = bytes.fromhex(metadata.pop('RAW'))
                for line in err.decode().splitlines():
                    if line.startswith('GEOMETRY'):
                        key,value=line.split(' ',1);metadata[key]=value
            else:
                metadata = dict(line.split(' ',1) for line in err.decode().splitlines())
                raw = out
            error = int(metadata['ERROR'])
            if error:
                return {'status':'refusal','error':error,'metadata':metadata},b''
            if case.get('geometry_sampler') and route=='smart':
                raw=(directory/'geometry-output.raw').read_bytes()
                rect=list(map(int,metadata['GEOMETRY'].split()))
                expected=(rect[2]-rect[0])*(rect[3]-rect[1])*case['depth']//8*4
            else:
                rect=[0,0,*case['geometry']];expected=len(case['pixels'])
            if len(raw)!=expected:
                return {'status':'harness_error','diagnostic':'output size'},b''
            return {'status':'ok','error':0,'metadata':metadata,**({'output_rect':rect} if case.get('geometry_sampler') else {})},raw
        except (ValueError,KeyError,OSError) as exc:
            return {'status':'harness_error','diagnostic':repr(exc)},b''

    def first_stage(self, *args):
        return None


def geometry_arguments(case,route=None):
    if not case.get('geometry_sampler'): return []
    return (['--checkout-rect',','.join(map(str,case['checkout_rect'])) if 'checkout_rect' in case else 'auto'] if case.get('geometry_sampler')=='realistic-v2' else []) + ['--negotiate-output','1','--rowbytes-pad',str(case['rowbytes_padding']),
            '--extent-hint',','.join(map(str,case['extent_hint'])),
            *(['--request-rect',','.join(map(str,case['request_rect']))] if route!='classic' else []),
            '--pixel-aspect','/'.join(map(str,case['pixel_aspect']))]


def geometry_environment(case,directory,env):
    if not case.get('geometry_sampler'): return
    if case.get('geometry_sampler')=='realistic-v2':
        env['OLM_F53_CHECKOUT']=','.join(map(str,case['checkout_rect'])) if 'checkout_rect' in case else 'auto'
    else:
        env.pop('OLM_F53_CHECKOUT',None)
    values=[*case['full_geometry'],*case['downsample'][0],*case['downsample'][1]]
    env['OLM_F52_DOWNSAMPLE']=','.join(map(str,values))
    env.update(OLM_F52_GEOMETRY_OUTPUT=str(directory/'geometry-output.raw'),
               OLM_F52_EXTENT=','.join(map(str,case['extent_hint'])),
               OLM_F52_REQUEST=','.join(map(str,case['request_rect'])),
               OLM_F52_ASPECT=','.join(map(str,case['pixel_aspect'])),
               OLM_F52_PADDING=str(case['rowbytes_padding']))
    (directory/'geometry-output.raw').unlink(missing_ok=True)


def geometry_shim(source, destination, classic=False):
    """Extend only a scratch copy of the legacy CLI ABI; production stays untouched."""
    import shutil
    shutil.copytree(source,destination,dirs_exist_ok=True)
    name='OLMSmoother.h' if classic else 'OLMSmoother2.h'
    path=destination/name;body=path.read_text()
    body=body.replace('struct PF_EffectWorld {','struct PF_EffectWorld {\n    struct { A_long num, den; } pix_aspect_ratio;')
    if classic:
        body=body.replace('struct PF_EffectWorld {','struct PF_EffectWorld {\n    A_long origin_x, origin_y;')
        body=body.replace('struct PF_InData {','struct PF_InData {\n    A_long width,height;\n    struct { A_long num,den; } downsample_x,downsample_y;')
    body=body.replace('struct PF_InData {','struct PF_InData {\n    A_long output_origin_x,output_origin_y;\n    PF_LRect extent_hint;\n    struct { A_long num,den; } pixel_aspect_ratio;')
    if not classic:
        body=body.replace('struct PF_CheckoutResult {','typedef A_long PF_ParamIndex;\nstruct PF_CheckoutResult {\n    struct { A_long num,den; } par;')
        body=body.replace('A_long, A_long, PF_RenderRequest *,','A_long, A_long, const PF_RenderRequest *,')
        body=body.replace('A_long, A_long, A_long, PF_CheckoutResult *);','A_long, A_long, A_u_long, PF_CheckoutResult *);')
    path.write_text(body)
    return destination
