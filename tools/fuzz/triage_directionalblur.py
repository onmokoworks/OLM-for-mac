#!/usr/bin/env python3
"""T10 reproducible census analysis and scratch-only gate experiments (two jobs).

Production source only supplies refusal diagnostics. All gate/dispatch probes
below are applied to a disposable source copy, never to a release build.
"""
from __future__ import annotations
import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
import copy
import json
import math
import os
from pathlib import Path
import struct
import sys
import tempfile
import time

sys.dont_write_bytecode = True
from adapters.olmdirectionalblur import Adapter, SOURCE, ROOT
from adapters.public import PublicAdapter, replace_once
from core import load_corpus, raw_diff, sha

TICKET = 'T10-triage-directionalblur'
WORKER = Path.home()/'.cache/olm-emu/radial_windows_reference_v2_20261001/target/release/aex-guest-worker'


def scratch_source():
    body = SOURCE.read_text()
    for tag in ('pf16-unadmitted-profile', 'pf32-unadmitted-profile'):
        original = f'return OLM_DIRECTIONAL_REFUSAL("{tag}");'
        body = replace_once(body, original,
            '#if !defined(OLM_DBLUR_TRIAGE_GATE_OFF)\n'+original+'\n#endif')
    original = 'if (!GenericPF32FiniteInput(input)) return OLM_DIRECTIONAL_REFUSAL("pf32-nonfinite-input");'
    body = replace_once(body, original,
        '#if !defined(OLM_DBLUR_TRIAGE_NONFINITE_OFF)\n'+original+'\n#endif')
    # Observe actual selected routes; these diagnostic calls return zero and
    # never alter dispatch. No numerical stage or output is synthesized.
    signatures = [
        ('const auto info = DirectionalDeepLayerInfo(requested_info, input, noise_layer, bitdepth);', 'world'),
        ('if (info.noise_variation != 0.0 || info.back_strength != 0 ||', 'legacy-pf8'),
        ('const A_long width = output->width;\n\tconst A_long height = output->height;', 'exact-pf8'),
        ('std::vector<std::uint16_t> source, destination;\n\tStageDirectionalWorld<PF_Pixel16>(input, &source);', 'neutral-pf16'),
        ('std::vector<float> source, destination;\n\tStageDirectionalWorld<PF_PixelFloat>(input, &source);', 'neutral-pf32'),
        ('const bool use_layer = info.noise_variation > 0.0 && info.noise_type == 3;', 'deep-features'),
    ]
    for anchor, tag in signatures:
        body = replace_once(body, anchor,
            f'(void)DirectionalRefusal(__func__, "dispatch-{tag}", __LINE__, PF_Err_NONE);\n\t'+anchor)
    anchor = '\t\tCopyWorld<PF_Pixel8>(input, output);\n\t\treturn PF_Err_NONE;'
    # Exactly two early identity branches in the legacy renderer.
    assert body.count(anchor) == 2
    body = body.replace(anchor,
        '\t\t(void)DirectionalRefusal(__func__, "legacy-copy", __LINE__, PF_Err_NONE);\n'+anchor)
    body = body.replace('#include "../../core/', f'#include "{ROOT}/core/')
    body = body.replace('#include "OLMDirectionalBlur.h"', f'#include "{SOURCE.with_suffix(".h")}"')
    return body


class ProbeAdapter(Adapter):
    def __init__(self, options, mode, sanitizer=False):
        super().__init__(options)
        self.mode, self.sanitizer = mode, sanitizer
        self.commands = []
        self.env.update(ASAN_OPTIONS='detect_leaks=0:halt_on_error=1',
                        UBSAN_OPTIONS='halt_on_error=1:print_stacktrace=1')

    def compile(self, argv, deadline):
        argv = list(argv)
        if argv[0] == 'clang++':
            host = next(Path(x) for x in argv if str(x).endswith('/host.cpp'))
            patched = host.with_name('directionalblur-probe.cpp')
            patched.write_text(scratch_source())
            host.write_text(replace_once(host.read_text(), str(SOURCE), str(patched)))
            if self.mode == 'terminal':
                argv += ['-DOLM_DBLUR_TRIAGE_GATE_OFF=1']
            elif self.mode == 'nonfinite':
                argv += ['-DOLM_DBLUR_TRIAGE_NONFINITE_OFF=1']
            if self.sanitizer:
                argv += ['-fsanitize=address,undefined', '-fno-sanitize-recover=all', '-fno-omit-frame-pointer', '-g']
        self.commands.append(list(map(str, argv)))
        return super().compile(argv, deadline)


def outcome(adapter, case, directory, route, deadline):
    result, raw, guards = adapter.candidate(case, directory, route, deadline)
    return dict(result, guards=guards, raw_sha256=sha(raw)), raw


def diff_stats(expected, actual, case):
    result = raw_diff(expected, actual, case['depth'])
    unit = case['depth']//8
    fmt = {8:'B', 16:'H', 32:'f'}[case['depth']]
    words = [i//unit for i in range(0, len(expected), unit) if expected[i:i+unit] != actual[i:i+unit]]
    pixels = sorted(set(i//4 for i in words))
    w,h = case['geometry']
    finite_diffs, nonfinite = [], 0
    for i in words:
        a,b = (struct.unpack_from('<'+fmt, raw, i*unit)[0] for raw in (expected,actual))
        if math.isfinite(a) and math.isfinite(b):
            finite_diffs.append(abs(a-b))
        else:
            nonfinite += 1
    result.update(max_abs_byte_diff=max((abs(a-b) for a,b in zip(expected,actual)), default=0),
        max_abs_finite_sample_diff=max(finite_diffs, default=0), nonfinite_different_words=nonfinite,
        channels=dict(Counter('ARGB'[i%4] for i in words)), different_pixels=len(pixels),
        bbox_xyxy=[min(p%w for p in pixels),min(p//w for p in pixels),
                   max(p%w for p in pixels),max(p//w for p in pixels)] if pixels else None,
        pixels_per_row=dict(sorted(Counter(p//w for p in pixels).items())),
        first_pixel_xy=[words[0]//4%w, words[0]//4//w] if words else None,
        first_channel='ARGB'[words[0]%4] if words else None,
        spatial_pattern='all pixels' if len(pixels)==w*h else 'subset of pixels',
        equals_input=actual==case['pixels'])
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--jobs', type=int, choices=[2], required=True)
    p.add_argument('--worker', type=Path, default=WORKER)
    p.add_argument('--main', type=Path, default=ROOT.parent.parent)
    p.add_argument('--scratch', type=Path, default=ROOT/'orchestra/state'/TICKET)
    p.add_argument('--census', type=Path, required=True)
    p.add_argument('--baseline', type=Path, default=ROOT/'reports/fuzz/olmdirectionalblur_20261021.json')
    p.add_argument('--report', type=Path, required=True)
    args=p.parse_args()
    args.max_size, args.case_timeout = 256, 10
    args.scratch=args.scratch.resolve()
    assert args.scratch.is_relative_to(ROOT/'orchestra/state'/TICKET)
    args.scratch.mkdir(parents=True,exist_ok=True)
    assert sum(x.stat().st_size for x in args.scratch.rglob('*') if x.is_file()) < 4*1024**3
    os.environ.update(TMPDIR=str(args.scratch),TMP=str(args.scratch),TEMP=str(args.scratch))
    tempfile.tempdir=str(args.scratch)
    deadline=time.monotonic()+1200
    census=json.loads(args.census.read_text()); baseline=json.loads(args.baseline.read_text())
    report={'schema':'olm-directionalblur-triage/1', 'jobs':args.jobs,
            'census_sha256':sha(args.census.read_bytes()), 'baseline_sha256':sha(args.baseline.read_bytes()),
            'probe_source_sha256':sha(scratch_source().encode()),
            'script_sha256':sha(Path(__file__).read_bytes()),
            'core_sha256':{str(p.relative_to(ROOT)):sha(p.read_bytes()) for p in sorted((ROOT/'core').glob('dblur*')) if p.is_file()},
            'census_summary':census['summary'], 'guards':[], 'clusters':[], 'gate_runs':[]}
    guards={}
    for row in census['cases']:
        for route, result in row['result']['routes'].items():
            if result['status']!='refusal': continue
            names=row.get('refusal_guards',{}).get(route,['UNATTRIBUTED'])
            for name in names:
                name=name.split('@')[0]
                g=guards.setdefault(name, {'guard':name,'routes':Counter(),'indices':set(),'aex_ok_indices':set(),'errors':Counter()})
                g['routes'][route]+=1;g['indices'].add(row['index']);g['errors'][result['error']]+=1
                if row['result']['oracle']['status']=='ok':g['aex_ok_indices'].add(row['index'])
    for g in sorted(guards.values(),key=lambda g:-sum(g['routes'].values())):
        g['indices']=sorted(g['indices']);g['aex_ok_indices']=sorted(g['aex_ok_indices'])
        report['guards'].append(g)
    with tempfile.TemporaryDirectory(prefix='triage_',dir=args.scratch) as td:
        scratch=Path(td)
        builds={}
        for mode,san in [('production',False),('baseline',False),('terminal',False),('terminal',True),('nonfinite',False),('nonfinite',True)]:
            key=mode+('-san' if san else '')
            directory=scratch/key;directory.mkdir()
            adapter=Adapter(args) if mode=='production' else ProbeAdapter(args,mode,san)
            provenance=adapter.prepare(directory,deadline)
            builds[key]=adapter
            report.setdefault('builds',{})[key]={'provenance':provenance,'commands':getattr(adapter,'commands',[])}
            print('BUILT',key,flush=True)
        base=builds['baseline']
        neutral=builds['production']
        # All 300 original samples: tracing disabled/enabled preserves metadata,
        # error statuses and output bytes. Also bind each regenerated input.
        def neutrality(row):
            case=neutral.generate(census['seed'],row['index'])
            assert sha(case['pixels'])==row['input_sha256']
            with tempfile.TemporaryDirectory(dir=scratch) as td:
                d=Path(td); values={}
                for route in base.routes:
                    traced,raw,_=neutral.candidate(case,d,route,deadline)
                    plain,plain_raw=PublicAdapter.candidate(neutral,case,d,route,deadline)
                    values[route]=traced==plain and raw==plain_raw
                return {'index':row['index'],'routes':values}
        with ThreadPoolExecutor(max_workers=args.jobs) as pool:
            report['trace_neutrality']=list(pool.map(neutrality,census['cases']))
        assert all(all(x['routes'].values()) for x in report['trace_neutrality'])
        print('NEUTRALITY',len(report['trace_neutrality']),flush=True)
        report['unwritable_trace_neutrality']=[]
        broken=copy.copy(neutral)
        broken.env=dict(neutral.env, OLM_REFUSAL_TRACE=str(scratch/'missing-parent'/'trace'))
        for index in (3,4,109):
            case=neutral.generate(census['seed'],index)
            with tempfile.TemporaryDirectory(dir=scratch) as td:
                for route in neutral.routes:
                    plain,raw=PublicAdapter.candidate(neutral,case,Path(td),route,deadline)
                    failed,failed_raw=PublicAdapter.candidate(broken,case,Path(td),route,deadline)
                    same=plain==failed and raw==failed_raw
                    assert same
                    report['unwritable_trace_neutrality'].append({'index':index,'route':route,'same':same})
        # Use the baseline's 18 original signature clusters and smallest saved
        # shrink by active input bytes, then changed-control count, then path.
        for number,(signature,cluster) in enumerate(baseline['clusters'].items(),1):
            candidates=[(load_corpus(ROOT/path,base)[0],path) for path in cluster['corpus']]
            def size(item):
                case,path=item
                defaults=base.defaults(*case['geometry'])
                return (len(case['pixels']),sum(p['value']!=d['value'] for p,d in zip(case['parameters'],defaults)),path)
            case,path=min(candidates,key=size)
            with tempfile.TemporaryDirectory(dir=scratch) as td:
                d=Path(td);oracle,reference=base.oracle(case,d,deadline)
                assert oracle['status']=='ok',oracle
                row={'cluster':number,'signature':signature,'population':cluster['count'],'corpus':path,
                     'case':{k:v for k,v in case.items() if k!='pixels'},'input_sha256':sha(case['pixels']),
                     'oracle':dict(oracle,raw_sha256=sha(reference)),'routes':{},
                     'first_differing_stage':None,'stage_reason':'No paired intermediate trace for this public session; dispatch labels are not numerical stages.'}
                for route in base.routes:
                    status,raw=outcome(base,case,d,route,deadline)
                    assert status['status']=='ok',status
                    assert raw!=reference, 'Saved mismatch no longer reproduces'
                    packed=copy.deepcopy(case);packed['input_padding']=packed['output_padding']=0
                    packed_status,packed_raw=outcome(base,packed,d,route,deadline)
                    # Terminal switch does not affect these successful paths;
                    # use its sanitizer build for the same input.
                    san_status,san_raw=outcome(builds['terminal-san'],case,d,route,deadline)
                    row['routes'][route]={'status':status,'diff':diff_stats(reference,raw,case),
                        'packed_same':packed_status['status']=='ok' and packed_raw==raw,
                        'sanitizer':san_status,'sanitizer_same':san_status['status']=='ok' and san_raw==raw}
                dispatch=row['routes']['classic']['status']['guards']
                row['classification']='port bug' if any('legacy-' in tag for tag in dispatch) else 'unexplained'
                row['classification_basis']='Observed legacy PF8 fallback, with identity/approximate implementation in source' if row['classification']=='port bug' else 'Final-byte residual in shared exact/generic core; no paired stage identifies arithmetic or Windows dependency'
                report['clusters'].append(row)
            print('CLUSTER',number,case['index'],row['classification'],flush=True)
        selected=[r for r in census['cases'] if any(
            any(t in name for t in ('pf16-unadmitted-profile','pf32-unadmitted-profile','pf32-nonfinite-input'))
            for names in r.get('refusal_guards',{}).values() for name in names)]
        def gate_run(row):
            case=base.generate(census['seed'],row['index'])
            nonfinite=any('pf32-nonfinite-input' in name for names in row['refusal_guards'].values() for name in names)
            mode='nonfinite' if nonfinite else 'terminal'
            result={'index':row['index'],'mode':mode,'original_guards':row['refusal_guards'],'routes':{}}
            with tempfile.TemporaryDirectory(dir=scratch) as td:
                d=Path(td)
                oracle,reference=base.oracle(case,d,deadline) if nonfinite else (row['result']['oracle'],b'')
                result['oracle']=oracle
                for route in base.routes:
                    result['routes'][route]={}
                    for key in (mode,mode+'-san'):
                        status,raw=outcome(builds[key],case,d,route,deadline)
                        if status['status']=='ok':
                            if not nonfinite:
                                oracle,reference=base.oracle(case,d,deadline)
                                result['oracle']=oracle
                            label=('exact' if raw==reference else 'mismatch') if oracle['status']=='ok' else 'uncompared'
                            if label=='mismatch':status['diff']=diff_stats(reference,raw,case)
                        elif any(s in status.get('diagnostic','') for s in ('AddressSanitizer','runtime error:','UndefinedBehaviorSanitizer')):
                            label='sanitizer_error'
                        elif status.get('returncode',0)<0:
                            label='crash'
                        else:label=status['status']
                        result['routes'][route][key]=dict(status,classification=label)
            return result
        with ThreadPoolExecutor(max_workers=args.jobs) as pool:
            report['gate_runs']=list(pool.map(gate_run,selected))
        report['gate_summary']={}
        for row in report['gate_runs']:
            for route,builds_out in row['routes'].items():
                for build,out in builds_out.items():
                    key=build+'/'+route
                    counts=report['gate_summary'].setdefault(key,Counter())
                    counts[out['classification']]+=1
        print('GATES',report['gate_summary'],flush=True)
    args.report.parent.mkdir(parents=True,exist_ok=True)
    args.report.write_text(json.dumps(report,sort_keys=True,indent=2)+'\n')
    print('REPORT',args.report,flush=True)


if __name__=='__main__':
    main()
