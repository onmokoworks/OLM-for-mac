"""Original AEX session protocol and production EffectMain SDK host adapter."""
from __future__ import annotations

import copy
import json
import math
import os
from pathlib import Path
import random
import struct
import sys
import tempfile
import time

from core import case_seed, command, sha
from .public import geometry_arguments, geometry_environment, ROOT as FUZZ_ROOT

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT/'tools/emulation'))
import probe_radialblur_public_aligned_20261001 as public

DECLARATIONS = ROOT/'reports/radialblur_public_getters_aligned_20261001.json'
KINDS = {1: 'i', 3: 'a', 4: 'b', 6: 'p', 7: 'u', 10: 's'}


class Adapter:
    name = 'radialblur'
    output_format = 'raw'
    geometry_samplers = ('realistic-v1','realistic-v2')
    generator_version = 1
    routes = ('classic', 'smart')
    oracle_routes = {'classic': 'classic', 'smart': 'smart'}
    original_routes = {'classic': 'render', 'smart': 'render'}

    def __init__(self, options):
        self.reference_build = getattr(options, "reference_build", False)
        self.max_size = options.max_size
        self.size_max_height = getattr(options, "size_max_height", None)
        self.size_sampler = getattr(options, "size_sampler", "default")
        self.timeout = options.case_timeout
        self.main = options.main.resolve()
        self.worker = options.worker.resolve()
        self.aex = self.main/'aex/OLMRadialBlur/Plugins/64/2025/OLMRadialBlur.aex'
        self.declarations = json.loads(DECLARATIONS.read_text())['native_parameter_declarations']
        self.controls = [p for p in self.declarations if p['param_type'] in KINDS]
        self.binary = None
        self.env = dict(os.environ)
        # Avoid diagnostic dump env vars inherited from other probe campaigns.
        for key in list(self.env):
            if (key.startswith(('OLMRADIALBLUR_', 'OLM_RADIALBLUR_', 'OLM_F52_'))
                    or key.endswith(('_PROBE_DIRECTORY', '_PLANES_DIRECTORY'))):
                del self.env[key]

    def defaults(self, w, h):
        params = []
        for declaration in self.controls:
            kind = KINDS[declaration['param_type']]
            value = declaration['default_value']
            if kind == 'p':
                x, y = declaration['default_components']
                value = [round(x*w/100*65536)/65536, round(y*h/100*65536)/65536]
            elif kind == 'a':
                value = declaration['default_components'][0]
            elif kind in ('i', 'b', 'u'):
                value = int(value)
            params.append({'slot': declaration['slot'], 'kind': kind, 'value': value})
        return params

    def generate(self, seed, index):
        rng = random.Random(case_seed(seed, index))
        mode = rng.random()
        if mode < .08:
            w, h = 1, 1
        elif mode < .24:
            n = rng.randint(1, self.max_size)
            w, h = (1, n) if rng.getrandbits(1) else (n, 1)
        else:
            limit = min(self.max_size, 24 if mode < .80 else 64 if mode < .95 else self.max_size)
            w, h = rng.randint(1, limit), rng.randint(1, limit)
        from sizes import selected
        w, h = selected(self, seed, index, (w, h))
        depth = rng.choice([8, 16, 32])
        params = self.defaults(w, h)
        # Sparse and dense mixtures include the entire declared domain without
        # making every test an expensive maximum-strength composition.
        indices = rng.sample(range(len(params)), rng.randint(1, 6) if rng.random() < .9 else len(params))
        for i in indices:
            p, declaration = params[i], self.controls[i]
            kind = p['kind']
            if kind == 'p':
                # Legal representable PF_Fixed coordinates, sampled around frame.
                p['value'] = [rng.randint(-extent*65536, 2*extent*65536)/65536 for extent in (w, h)]
            elif kind == 'a':
                # AD is signed 16.16 degrees, no slider min/max. Sample +/-720.
                p['value'] = rng.randint(-720*65536, 720*65536)/65536
            else:
                lo, hi = declaration['valid_min'], declaration['valid_max']
                if kind in ('i', 'u', 'b'):
                    if p['slot'] in (4, 6, 10, 12) and rng.random() < .7:
                        hi = min(hi, 30)
                    p['value'] = rng.randint(int(lo), int(hi))
                else:
                    p['value'] = rng.choice([lo, hi, rng.uniform(lo, hi), rng.uniform(lo, hi)])
        # Include actual blur frequently; preserve a random no-op population.
        if rng.random() < .8 and all(p['value'] == 0 for p in params if p['slot'] in (4,6,7,10,12,13)):
            slot = rng.choice([4,10])
            next(p for p in params if p['slot'] == slot)['value'] = rng.randint(1, 30)
        profile = rng.choices(['sdr', 'hdr', 'signed', 'nonfinite'], [65, 15, 15, 5])[0] if depth == 32 else 'sdr'
        values = bytearray()
        for _ in range(w*h):
            if depth in (8, 16):
                top = 255 if depth == 8 else 32768
                channels = [rng.choice([0, top, rng.randint(1, top-1)]), *[rng.randint(0, top) for _ in range(3)]]
                values.extend(struct.pack('<4B' if depth == 8 else '<4H', *channels))
            else:
                low, high = (-4, 4) if profile == 'signed' else (0, 8) if profile == 'hdr' else (0, 1)
                channels = [rng.choice([0., 1., .5, rng.uniform(low, high)]), *[rng.uniform(low, high) for _ in range(3)]]
                for value in channels:
                    if profile == 'nonfinite' and rng.random() < .25:
                        values.extend(struct.pack('<I', rng.choice([0x7f800000,0xff800000,0x7fc12345,0xff812346,0x80000000])))
                    else:
                        values.extend(struct.pack('<f', value))
        return {'seed': seed, 'index': index, 'depth': depth, 'geometry': [w,h],
                'profile': profile, 'parameters': params,
                'input_padding': rng.choice([0,1,3,7,16]), 'output_padding': rng.choice([0,1,5,11,32]),
                'pixels': bytes(values)}

    def resize(self, case, old_geometry):
        # Keep the center's relative location when reducing the input extent.
        for p in case['parameters']:
            if p['kind'] == 'p':
                p['value'] = [round(v*new/old*65536)/65536
                              for v,new,old in zip(p['value'],case['geometry'],old_geometry)]
        return case

    def simple_pixels(self, case):
        if case['depth'] == 8:
            return bytes(255 if value >= 128 else 0 for value in case['pixels'])
        fmt, cutoff, top = ('H', 16384, 32768) if case['depth'] == 16 else ('f', .5, 1.)
        return b''.join(struct.pack('<'+fmt, top if math.isfinite(value) and value >= cutoff else 0)
                        for (value,) in struct.iter_unpack('<'+fmt, case['pixels']))

    def build(self, scratch, deadline):
        self.env.update(TMPDIR=str(scratch), TMP=str(scratch), TEMP=str(scratch))
        body = public.initial.HARNESS.read_text()
        replacements = [('argc!=6', 'argc!=8'), ('w>64||h>64', 'w>4096||h>4096'),
                        ('irb=active+3*ps,orb=active+5*ps', 'irb=active+atoi(argv[6]),orb=active+atoi(argv[7])')]
        for old, new in replacements:
            if body.count(old) != 1:
                raise ValueError(f'Harness changed: {old}')
            body = body.replace(old, new)
        body = body.replace('#include "production_under_test.cpp"', '#include "production_under_test.cpp"\n#include "'+str(FUZZ_ROOT/'tools/fuzz/harnesses/geometry.hpp')+'"')
        harness = scratch/'fuzz_harness.cpp'
        harness.write_text(body)
        # Optional measurement switches, both off by default. Bypass names
        # admission-guard tags compiled into the candidate source; sanitize
        # selects the existing probe build's ASan/UBSan flags.
        bypass = os.environ.get('OLM_RADIAL_CANDIDATE_BYPASS', '').strip()
        sanitize = os.environ.get('OLM_RADIAL_CANDIDATE_SANITIZE', '').strip() not in ('', '0')
        source = public.SOURCE.read_text()
        if self.reference_build:
            source = "#define OLM_REFERENCE_BUILD 1\n" + source
        if bypass:
            source = f'#define OLM_RADIAL_EXPERIMENT_BYPASS "{bypass}"\n' + source
        candidate_source = scratch/'candidate_source.cpp'
        candidate_source.write_text(source)
        if bypass:
            self.env['OLM_RADIAL_CANDIDATE_BYPASS'] = bypass
        code = ("import sys; from pathlib import Path; "
                "sys.path.insert(0, sys.argv[1]); "
                "import probe_radialblur_topology_20261001 as p; "
                "p.HARNESS=Path(sys.argv[2]); p.ROOT=Path(sys.argv[4]); p.SOURCE=Path(sys.argv[7]); "
                "p.build(Path(sys.argv[3]), Path(sys.argv[5]).read_text(), sanitize=(sys.argv[6]=='1'))")
        status, out, err = command([sys.executable, '-c', code, ROOT/'tools/emulation',
                                    harness, scratch/'build', self.main, candidate_source,
                                    '1' if sanitize else '0', public.SOURCE], timeout=max(0, deadline-time.monotonic()),
                                   deadline=deadline, env=self.env)
        if status['status'] != 'ok':
            raise RuntimeError('Candidate build failed: '+repr(status)+' '+err.decode(errors='replace')[-2000:])
        self.binary = scratch/'build/mac'
        self._build_info = source, body, bypass, sanitize
        return self.binary, [public.SOURCE, public.initial.HARNESS]

    def prepare(self, scratch, deadline):
        if sha(self.aex.read_bytes()) != public.initial.AEX_SHA:
            raise ValueError('Original AEX hash differs from the public probe binding')
        self.build(scratch, deadline)
        source, body, bypass, sanitize = self._build_info
        provenance = {
            'aex_path': str(self.aex), 'aex_sha256': sha(self.aex.read_bytes()),
            'worker_path': str(self.worker), 'worker_sha256': sha(self.worker.read_bytes()),
            'candidate_sha256': sha(self.binary.read_bytes()),
            'source_sha256': sha(public.SOURCE.read_bytes()),
            'ucrtmath_sha256': {str(p.relative_to(Path(__file__).resolve().parents[3])):sha(p.read_bytes()) for p in sorted((Path(__file__).resolve().parents[3]/'ucrtmath').glob('src/*'))},
            'candidate_source_sha256': sha(source.encode()),
            'candidate_bypass': bypass,
            'candidate_sanitize': sanitize,
            'header_sha256': sha(public.SOURCE.with_suffix('.h').read_bytes()),
            'core_sha256': sha((ROOT/'core/dblur_noise.h').read_bytes()),
            'declarations_sha256': sha(DECLARATIONS.read_bytes()),
            'harness_sha256': sha(body.encode()),
            'compiler': 'clang++ arm64 -O2 -fno-fast-math -ffp-contract=off (existing public.build)',
            'host': 'AEXCompat Unicorn CPU per-route; SDK fake Mac Classic/Smart EffectMain',
            'oracle_routes':self.oracle_routes, 'original_routes':self.original_routes,
            'coordinates': 'Mac pixel PF_Fixed; AEX percent via public.native_case',
            'time': {'value': 0, 'scale': 24, 'step': 1, 'total': 1},
            'world': 'full frame, origin 0, downsample 1:1, raw ARGB; no color conversion',
            'aex_stride': 'packed session input/output; random odd byte padding on Mac worlds only',
            'noise_layer': 'None (slot 26 omitted); popup Layer is sampled, independent layer checkout is outside this adapter',
            'stage_support': 'session protocol + public EffectMain harness expose final raw only',
            'reference_limit': 'Host math imports are not a native Windows UCRT/AE oracle. Calibration is finite, not general equivalence.'}
        # Retained public samples validate transport + known reference math boundaries.
        retained = json.loads(DECLARATIONS.read_text())['cases']
        selected = [next(c for c in retained if c['depth']==d and c['family']==f and c['state']=='neutral')
                    for f in (1,2) for d in (8,16,32)]
        calibrations = []
        for i, archived in enumerate(selected):
            case = dict(archived, pixels=public.fixture(archived), input_padding=3, output_padding=5)
            directory = scratch/f'calibration_{i}'
            directory.mkdir()
            status, raw = self.oracle(case, directory, deadline)
            calibrations.append({'depth': case['depth'], 'family': case['family'], 'oracle': status,
                                 'expected_sha256': archived['native_raw_sha256'],
                                 'actual_sha256': sha(raw) if status['status']=='ok' else None,
                                 'matches_retained': status['status']=='ok' and sha(raw)==archived['native_raw_sha256']})
            for p in directory.iterdir():
                p.unlink()
            directory.rmdir()
        provenance['calibration'] = calibrations
        if not any(c['oracle']['status']=='ok' for c in calibrations):
            raise RuntimeError('AEX worker did not render any calibration: '+json.dumps(calibrations))
        return provenance

    def oracle(self, case, directory, deadline, route='smart'):
        # Like public.native_render: the worker creates exclusive sidecar dumps.
        # Every replay/reduction needs a fresh directory, including on rejection.
        with tempfile.TemporaryDirectory(prefix='native_', dir=directory) as name:
            return self._oracle(case, Path(name), deadline, route)

    def _oracle(self, case, directory, deadline, route='smart'):
        ip, op = directory/'input.raw', directory/'output.raw'
        ip.write_bytes(case['pixels'])
        op.unlink(missing_ok=True)
        converted = public.native_case(case)
        encoded = []
        for p in converted['parameters']:
            kind = 'point' if p['kind']=='p' else 'angle' if p['kind']=='a' else 'f64'
            value = ','.join(map(str,p['value'])) if isinstance(p['value'],list) else str(p['value'])
            encoded.append(f"param_{p['slot']}@{p['slot']}:{kind}={value}")
        request = json.dumps({'v':4, 'type':'render_frame', 'frame_index':0,
                              'current_time':{'value':0,'scale':24,'step':1,'total':1},
                              'parameters':'v4|'+';'.join(encoded)}).encode()
        status, out, err = command([self.worker,'session',self.aex,ip,op,*case.get('full_geometry',case['geometry']),'24',
                                   *[v for axis,ratio in zip(('x','y'),case.get('downsample',[])) for v in ('--downsample-'+axis,'/'.join(map(str,ratio)))],
                                   *geometry_arguments(case,route),
                                   '--pixel-format',{8:'argb8',16:'argb16',32:'argb32f'}[case['depth']],
                                   '--fixture-render-path',route,
                                   *getattr(self, 'session_arguments', lambda case, directory: [])(case, directory)],
                                  data=struct.pack('<I',len(request))+request,
                                  timeout=self.timeout, deadline=deadline, env=self.env)
        observer = getattr(self, 'session_observed', None)
        if observer is not None:
            observer(out, err)
        if status['status'] != 'ok':
            diagnostic = err.decode(errors='replace')
            reason = diagnostic if len(diagnostic) <= 1600 else diagnostic[:800]+' ... '+diagnostic[-800:]
            if status['status'] != 'budget':
                status['status'] = 'budget' if any(s in reason.lower() for s in ('timeout','budget','instruction limit','deadline')) else 'reject'
            return dict(status, diagnostic=reason), b''
        try:
            messages, pos = [], 0
            while pos < len(out):
                n = struct.unpack_from('<I',out,pos)[0]
                pos += 4
                messages.append(json.loads(out[pos:pos+n]))
                pos += n
            ready = next(m for m in messages if m['type']=='session_ready')['setup']
            frame = next(m for m in messages if m['type']=='frame_done')
            close = next(m for m in messages if m['type']=='session_closed')['close']
            if ready['global_setup_error'] or ready['params_setup_error'] or frame['status'] != 'ok' or frame['render_error']:
                return {'status':'reject', 'diagnostic':json.dumps(frame)[-1600:]}, b''
            raw = op.read_bytes()
            if not (frame['output']['guards_intact'] and frame['output']['checksum']==sha(raw)
                    and len(raw)==(frame['output']['width']*frame['output']['height']*case['depth']//8*4 if case.get('geometry_sampler') else len(case['pixels'])) and frame['output']['render_path']=={'classic':'classic','smart':'smartfx'}[route]
                    and close['session_clean'] and not close['unsupported_suite_calls']
                    and not close['dropped_unsupported_suite_calls']):
                return {'status':'harness_error', 'diagnostic':'guard/checksum/size/route/session invariant'}, b''
            expected = [(p['slot'],p['param_type'],p['valid_min'],p['valid_max'],p['default_value']) for p in self.controls]
            actual = [(p['slot'],p['param_type'],p['valid_min'],p['valid_max'],p['default_value'])
                      for p in ready['parameters'] if p['param_type'] in KINDS]
            if actual != expected:
                return {'status':'harness_error', 'diagnostic':'live declarations differ from retained ranges'}, b''
            return {'status':'ok', 'guards_intact':True, 'session_clean':True,**({'output_rect':frame['output']['rect']} if case.get('geometry_sampler') else {})}, raw
        except (KeyError, ValueError, StopIteration, OSError, struct.error) as exc:
            return {'status':'harness_error', 'diagnostic':repr(exc), 'stderr':err.decode(errors='replace')[-1000:]}, b''
        finally:
            ip.unlink(missing_ok=True)
            op.unlink(missing_ok=True)

    def candidate_command(self, case, directory, route):
        config = directory/'parameters.txt'
        config.write_text(public.initial.config_text(case))
        return [self.binary, *case['geometry'], case['depth'], route, config,
                case['input_padding'], case['output_padding']], case['pixels']

    def candidate(self, case, directory, route, deadline):
        config = directory/'parameters.txt'
        config.write_text(public.initial.config_text(case))
        trace = directory/f'refusal_trace_{route}.txt'
        trace.unlink(missing_ok=True)
        env = dict(self.env, OLM_REFUSAL_TRACE=str(trace))
        geometry_environment(case,directory,env)
        status, raw, err = command([self.binary,*case['geometry'],case['depth'],route,config,
                                   case['input_padding'],case['output_padding']],
                                  data=case['pixels'], timeout=self.timeout, deadline=deadline, env=env)
        # Optional attribution: the candidate binary appends "function:tag" to the
        # trace only when an admission guard refuses. With tracing unavailable the
        # list stays empty and every status/byte below is unchanged.
        guards = []
        try:
            if trace.is_file():
                guards = [line.strip() for line in trace.read_text().splitlines() if line.strip()]
        except OSError:
            guards = []
        finally:
            trace.unlink(missing_ok=True)
        stderr = err.decode(errors='replace')
        # Sanitizer builds prepend reports and stack traces (including blank
        # lines) to the harness metadata; keep those reports as evidence and
        # parse only the "KEY value" metadata lines.
        sanitizer = [line for line in stderr.splitlines()
                     if ('AddressSanitizer' in line or 'UndefinedBehaviorSanitizer' in line
                         or 'LeakSanitizer' in line or 'runtime error:' in line)]
        if status['status'] != 'ok':
            return dict(status, diagnostic=stderr[-1600:], sanitizer=sanitizer), b'', guards
        try:
            metadata = {}
            for line in stderr.splitlines():
                if ' ' in line:
                    key, value = line.split(' ', 1)
                    metadata[key] = value
            error = int(metadata['ERROR'])
            if error:
                result = {'status':'refusal', 'error':error, 'metadata':metadata}
                if sanitizer:
                    result['sanitizer'] = sanitizer
                return result, b'', guards
            if case.get('geometry_sampler') and route=='smart':
                raw=(directory/'geometry-output.raw').read_bytes()
                rect=list(map(int,metadata['GEOMETRY'].split()))
                expected=(rect[2]-rect[0])*(rect[3]-rect[1])*case['depth']//8*4
            else:
                rect=[0,0,*case['geometry']];expected=len(case['pixels'])
            if len(raw) != expected:
                return {'status':'harness_error','diagnostic':'output length'}, b'', guards
            result = {'status':'ok','error':0,'metadata':metadata,**({'output_rect':rect} if case.get('geometry_sampler') else {})}
            if sanitizer:
                result['sanitizer'] = sanitizer
            return result, raw, guards
        except (ValueError,KeyError,OSError) as exc:
            return {'status':'harness_error','diagnostic':repr(exc),
                    'stderr':stderr[-1000:], 'sanitizer':sanitizer}, b'', guards

    def first_stage(self, case, directory, results, deadline):
        return None
