#!/usr/bin/env python3
"""F05: zero-strength public differentials, sanitizer replay and paired stages.

Uses the cached original-AEX worker; the optional intermediate observation is
inserted only in a scratch copy of the Mac core. No numerical detours.
"""
from __future__ import annotations

import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import time
from types import SimpleNamespace

sys.dont_write_bytecode = True
from adapters.olmdirectionalblur import Adapter, ROOT, SOURCE
from core import evaluate, load_corpus, sha

TICKET = 'F05-dblur-zero-strength-deep'
WORKER = Path.home()/'.cache/olm-emu/radial_windows_reference_v2_20261001/target/release/aex-guest-worker'


class BaselineAdapter(Adapter):
    """Compile the ticket's starting revision without mutating the checkout."""
    def __init__(self, options, revision):
        super().__init__(options)
        self.revision = revision

    def prepare(self, scratch, deadline):
        provenance = super().prepare(scratch, deadline)
        provenance['baseline_revision'] = self.revision
        # These are the files actually compiled from git, not their current
        # working-tree contents reported by the ordinary adapter.
        for path in ('mac/OLMDirectionalBlur/OLMDirectionalBlur.cpp',
                     'core/dblur_frontonly.cpp', 'core/dblur_generic_budget.h'):
            raw = subprocess.check_output(['git','show',f'{self.revision}:{path}'],cwd=ROOT)
            provenance['dependencies_sha256'][path] = sha(raw)
        return provenance

    def compile(self, argv, deadline):
        argv = list(argv)
        if argv[0] == 'clang++':
            directory = Path(argv[argv.index('-o')+1]).parent
            def retained(path, name):
                body=subprocess.check_output(['git','show',f'{self.revision}:{path}'],cwd=ROOT).decode()
                out=directory/name;out.write_text(body);return out
            source=retained('mac/OLMDirectionalBlur/OLMDirectionalBlur.cpp','baseline.cpp')
            core=retained('core/dblur_frontonly.cpp','baseline-core.cpp')
            budget=retained('core/dblur_generic_budget.h','baseline-budget.h')
            body=source.read_text().replace('../../core/dblur_generic_budget.h',str(budget))
            body=body.replace('../../core/',str(ROOT/'core')+'/')
            body=body.replace('"OLMDirectionalBlur.h"',f'"{SOURCE.with_suffix(".h")}"')
            source.write_text(body)
            host=directory/'host.cpp';host.write_text(host.read_text().replace(str(SOURCE),str(source)))
            argv=[core if x==ROOT/'core/dblur_frontonly.cpp' else x for x in argv]
            argv+=['-I',ROOT/'core']
        return super().compile(argv,deadline)


class ProbeAdapter(Adapter):
    def __init__(self, options, sanitize=False, capture=False):
        super().__init__(options)
        self.sanitize, self.capture = sanitize, capture
        self.env.update(ASAN_OPTIONS='detect_leaks=0:halt_on_error=1',
                        UBSAN_OPTIONS='halt_on_error=1:print_stacktrace=1')

    def compile(self, argv, deadline):
        argv = list(argv)
        if argv[0] == 'clang++':
            if self.sanitize:
                argv += ['-fsanitize=address,undefined', '-fno-sanitize-recover=all',
                         '-fno-omit-frame-pointer', '-g']
            if self.capture:
                original = ROOT/'core/dblur_frontonly.cpp'
                body = original.read_text()
                body = '#include <cstdio>\n' + body
                marker = 'namespace {\n'
                dump = '''namespace {
static void capture_stage(const char* name, const std::vector<float>& data) {
    std::printf("%s ", name);
    const auto* bytes = reinterpret_cast<const unsigned char*>(data.data());
    for (std::size_t i = 0; i < data.size()*sizeof(float); ++i) std::printf("%02x", bytes[i]);
    std::printf("\\n");
}
'''
                body = body.replace(marker, dump, 1)
                # Both typed renderers, immediately after the last rowdriver.
                for anchor in ('        for (std::size_t pixel = 0; pixel < work_pixels; ++pixel) {\n            if (denominator[pixel]',
                               '        for (std::size_t p = 0; p < wp; ++p) if (den[p]'):
                    assert body.count(anchor) == 1
                    body = body.replace(anchor, '        capture_stage("STAGE_PRE", b);\n'+anchor)
                anchor = '        std::fill(a.begin(), a.end(), 0.0f);'
                assert body.count(anchor) == 2
                body = body.replace(anchor, '        capture_stage("STAGE_NORMALIZED", b);\n'+anchor)
                binary = Path(argv[argv.index('-o')+1])
                path = binary.with_name('captured-core.cpp')
                path.write_text(body)
                argv = [path if x == original else x for x in argv]
                argv += ['-I', ROOT/'core']
        return super().compile(argv, deadline)


def parameters(case):
    return {p['slot']: p['value'] for p in case['parameters']}


def target(case):
    p = parameters(case)
    return case['depth'] in (16, 32) and p[5] == p[10] == 0


def small_cases(adapter):
    """Independent 1x1/1x2/3x2 boundary inputs; no saved expected pixels."""
    for depth in (16, 32):
        for w, h in ((1, 1), (1, 2), (3, 2)):
            for name, controls in (
                ('copy', {2: 0, 3: 100, 7: 100, 12: 100, 15: 100, 19: -720}),
                ('front', {6: 3}), ('back', {11: 3}),
                ('both', {6: 3, 11: 5}),
                ('features', {1: -17.25, 2: 2.5, 3: 50, 6: 3, 11: 5, 7: 50, 12: 100, 15: 50, 16: 2})):
                c = dict(seed=0, index=0, geometry=[w,h], depth=depth, profile='sdr',
                         parameters=adapter.defaults(w,h), input_padding=3, output_padding=11)
                controls.update({5: 0, 10: 0})
                for p in c['parameters']:
                    if p['slot'] in controls:
                        p['value'] = controls[p['slot']]
                values = [(1., .25, .5, .75), (.5, .75, .25, .5), (0., 1., .5, .25)]
                c['pixels'] = b''.join(struct.pack('<4H', *(int(v*32768) for v in values[i%3]))
                                      if depth == 16 else struct.pack('<4f', *values[i%3])
                                      for i in range(w*h))
                yield f'{depth}-{w}x{h}-{name}', c


def paired_trace(adapter, directory, deadline):
    from PIL import Image
    pixels = [(64,128,192,255), (192,64,128,128)]
    ip = directory/'input.png'
    image = Image.new('RGBA', (1,2)); image.putdata(pixels); image.save(ip)
    rows = []
    # Work geometry for 1x2 is 7x6; six single-row calls exhaust the rowdriver.
    plane_bytes = 7*6*16
    for depth in (16, 32):
        for fade in (0, 3):
            case = dict(seed=0,index=0,geometry=[1,2],depth=depth,profile='sdr',
                        parameters=adapter.defaults(1,2),input_padding=3,output_padding=11)
            for p in case['parameters']:
                if p['slot'] in (5,10): p['value'] = 0
                if p['slot'] == 11: p['value'] = fade
            case['pixels'] = b''.join(struct.pack('<4H', *((v*32768+127)//255 for v in (a,r,g,b)))
                                     if depth == 16 else struct.pack('<4f', *(v/255 for v in (a,r,g,b)))
                                     for r,g,b,a in pixels)
            owner = '0x3c90' if depth == 16 else '0x57b0'
            watches = [f'function={owner},arg=stack6,offset=72,size=16',
                       f'function=0x38d0,arg=r9,deref=0,size={plane_bytes},occurrence=6',
                       f'function=0x1ec0,arg=rcx,size={plane_bytes},occurrence=2']
            assignments = [f"param_{p['slot']}@{p['slot']}"+(':angle' if p['kind']=='a' else '')+f"={p['value']}"
                           for p in case['parameters']]
            cmd = [str(adapter.worker), 'render-trace-png', str(adapter.aex), str(ip),
                   str(directory/'trace.png'), '--pixel-format', 'argb16' if depth==16 else 'argb32f',
                   *[v for watch in watches for v in ('--watch',watch)], *assignments]
            run = subprocess.run(cmd, capture_output=True, check=True, env=adapter.env, timeout=60)
            report = json.loads(run.stdout)
            trace = next(t for t in report['execution_traces'] if t['selector']=='SMART_RENDER')
            assert report['render_error']==0 and report['guards_intact']
            assert not report['unsupported_suite_calls'] and not trace['truncated']
            assert not trace['dropped_memory_witnesses'] and not trace['trace_configuration']['unhookable_watches']
            witnesses = {w['watch_id']:w for w in trace['memory_witnesses']}
            result, raw, _ = adapter.candidate(case, directory, 'classic', deadline)
            assert result['status']=='ok' and sha(raw)==report['raw_pixel_sha256']
            context = witnesses['watch-1']['before']['hex']
            assert struct.unpack('<4i',bytes.fromhex(context)) == (0,0,0,fade)
            row = dict(depth=depth, back_fade=fade, context_four_words_hex=context,
                       final_sha256=sha(raw), trace_sha256=sha(run.stdout), stage_pairs=[])
            if fade:
                for key, watch, side in [('STAGE_PRE','watch-2','after'),
                                         ('STAGE_NORMALIZED','watch-3','before')]:
                    expected = witnesses[watch][side]['hex']
                    actual = result['metadata'][key]
                    assert actual == expected, (depth,key)
                    row['stage_pairs'].append(dict(stage=key, bytes=plane_bytes, sha256=sha(bytes.fromhex(actual)), exact=True))
            else:
                assert set(witnesses)=={'watch-1'} and raw==case['pixels']
            rows.append(row)
    return rows


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--before', type=Path, required=True)
    ap.add_argument('--after', type=Path, required=True)
    ap.add_argument('--output', type=Path, required=True)
    ap.add_argument('--replay', type=Path, required=True)
    ap.add_argument('--baseline', required=True, help='Ticket starting git revision for the before corpus replay')
    args = ap.parse_args()
    scratch = ROOT/'orchestra/state'/TICKET; scratch.mkdir(parents=True, exist_ok=True)
    os.environ.update(TMPDIR=str(scratch), TMP=str(scratch), TEMP=str(scratch))
    tempfile.tempdir = str(scratch)
    options = SimpleNamespace(max_size=256, case_timeout=120, main=ROOT.parent.parent, worker=WORKER)
    before, after = (json.loads(p.read_text()) for p in (args.before,args.after))
    deadline = time.monotonic()+1200
    result = {'schema':'directionalblur.zero-strength/1', 'before_summary':before['summary'],
              'after_summary':after['summary'], 'provenance':after['provenance']}
    result['before_after'] = []
    for old, new in zip(before['cases'],after['cases']):
        assert old['index']==new['index'] and old['input_sha256']==new['input_sha256']
        for route in ('classic','smart'):
            a,b=old['result']['routes'][route],new['result']['routes'][route]
            if a['status']=='exact':
                assert b['status']=='exact' and a['raw_sha256']==b['raw_sha256']
            if a['status']=='mismatch':
                assert a==b
        result['before_after'].append(dict(index=old['index'],depth=old['depth'],
            input_sha256=old['input_sha256'],before=old['result'],after=new['result']))
    replay=json.loads(args.replay.read_text())
    assert len(replay['replays'])==56 and replay['replay_matches_saved']
    result['evidence_source_sha256'] = {str(p.relative_to(ROOT)):sha(p.read_bytes())
        for p in (ROOT/'mac/OLMDirectionalBlur/OLMDirectionalBlur.cpp',
                  ROOT/'core/dblur_frontonly.cpp',ROOT/'core/dblur_generic_budget.h',Path(__file__))}
    with tempfile.TemporaryDirectory(dir=scratch, prefix='verify_') as td:
        directory = Path(td)
        baseline_dir=directory/'baseline';baseline_dir.mkdir()
        baseline=BaselineAdapter(options,args.baseline);baseline.prepare(baseline_dir,deadline)
        result['baseline_revision']=args.baseline
        result['corpus_before_after']=[]
        for row in replay['replays']:
            case,saved=load_corpus(Path(row['path']),baseline)
            with tempfile.TemporaryDirectory(dir=directory) as path:
                observed=evaluate(baseline,case,Path(path),deadline)
            assert observed==saved['result']==row['result']
            result['corpus_before_after'].append(dict(path=Path(row['path']).name,
                before=observed,after=row['result'],matches_saved=True))
        adapters = []
        for sanitize in (False, True):
            build = directory/('san' if sanitize else 'o2'); build.mkdir()
            adapter = ProbeAdapter(options, sanitize=sanitize)
            adapter.prepare(build, deadline); adapters.append(adapter)
        targets = [x for x,y in zip(after['cases'],before['cases']) if target(x)
                   and y['result']['routes']['classic']['status']=='refusal']
        def check(row):
            c = adapters[0].generate(1,row['index'])
            assert sha(c['pixels']) == row['input_sha256']
            out = dict(index=row['index'],depth=c['depth'],geometry=c['geometry'],routes={})
            with tempfile.TemporaryDirectory(dir=directory) as path:
                for route in adapters[0].routes:
                    a, raw, _ = adapters[0].candidate(c, Path(path), route, deadline)
                    b, san_raw, _ = adapters[1].candidate(c, Path(path), route, deadline)
                    assert a==b and raw==san_raw, (row['index'],route)
                    expected = row['result']['oracle']
                    exact = expected['status']=='ok' and a['status']=='ok' and sha(raw)==expected['raw_sha256']
                    out['routes'][route] = dict(status=a['status'], exact=exact, sanitizer_same=True, sha256=sha(raw))
            return out
        with ThreadPoolExecutor(max_workers=2) as pool:
            result['targets'] = list(pool.map(check,targets))
        result['reduced_targets'] = []
        for row in targets:
            case=adapters[0].generate(1,row['index'])
            w,h=case['geometry']; pixel_size=case['depth']//2
            # Keep the first pixel of each of the first two rows. This is a
            # reproducible geometry reduction, not a global-minimum claim.
            case['pixels']=b''.join(case['pixels'][y*w*pixel_size:y*w*pixel_size+pixel_size]
                                    for y in range(min(h,2)))
            case['geometry']=[1,min(h,2)]
            with tempfile.TemporaryDirectory(dir=directory) as path:
                observed=evaluate(adapters[0],case,Path(path),deadline)
                old={}
                for route in adapters[0].routes:
                    old[route]=baseline.candidate(case,Path(path),route,deadline)[0]
                    san,raw,_=adapters[1].candidate(case,Path(path),route,deadline)
                    measured=observed['routes'][route]
                    assert san['status'] in ('ok','refusal')
                    assert san.get('error')==measured.get('error')
                    if san['status']=='ok': assert sha(raw)==measured['raw_sha256']
                result['reduced_targets'].append(dict(index=row['index'],geometry=case['geometry'],
                    input_sha256=sha(case['pixels']),before=old,after=observed,sanitizer_same=True))
        result['small'] = []
        for name,case in small_cases(adapters[0]):
            with tempfile.TemporaryDirectory(dir=directory) as path:
                observed = evaluate(adapters[0],case,Path(path),deadline)
                assert all(r['status']=='exact' for r in observed['routes'].values()), (name,observed)
                for route in adapters[0].routes:
                    san, raw, _ = adapters[1].candidate(case,Path(path),route,deadline)
                    assert san['status']=='ok' and sha(raw)==observed['oracle']['raw_sha256']
                result['small'].append(dict(name=name,result=observed,sanitizer_exact=True))
        # The census time budget is not a numerical verdict. Recheck its target
        # timeout once with a larger explicit per-case budget.
        result['budget_recheck'] = []
        for row in targets:
            if row['result']['oracle']['status']=='budget':
                c=adapters[0].generate(1,row['index'])
                with tempfile.TemporaryDirectory(dir=directory) as path:
                    observed=evaluate(adapters[0],c,Path(path),deadline)
                    result['budget_recheck'].append(dict(index=row['index'],result=observed))
        capture_dir=directory/'capture';capture_dir.mkdir()
        captured=ProbeAdapter(options,capture=True);captured.prepare(capture_dir,deadline)
        result['paired_stages']=paired_trace(captured,capture_dir,deadline)
    args.output.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print('TARGETS',len(result['targets']), 'SMALL',len(result['small']),
          'PAIRED',sum(len(x['stage_pairs']) for x in result['paired_stages']))
    print('TARGET STATUS',dict(Counter(x['routes']['classic']['status'] for x in result['targets'])))


if __name__ == '__main__':
    main()
