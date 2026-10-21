#!/usr/bin/env python3
"""F06 scratch-only PF8 fallback dispatch/core admission experiment."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path
import sys
import subprocess
import tempfile
import time

sys.dont_write_bytecode = True
from adapters.olmdirectionalblur import Adapter, SOURCE, ROOT
from adapters.public import replace_once
from core import evaluate, load_corpus, sha

TICKET = 'F06-dblur-pf8-feature-dispatch'
BASE_REF = 'a253fd15011c970469a24ff201e262d8ca875fbc'


def baseline(path):
    return subprocess.check_output(['git','show',f'{BASE_REF}:{path.relative_to(ROOT)}'], cwd=ROOT).decode()


class Probe(Adapter):
    def __init__(self, args, sanitizer=False, unchanged=False):
        super().__init__(args)
        self.sanitizer = sanitizer
        self.unchanged = unchanged
        self.commands = []
        self.env.update(ASAN_OPTIONS='detect_leaks=0:halt_on_error=1',
                        UBSAN_OPTIONS='halt_on_error=1:print_stacktrace=1')

    def compile(self, argv, deadline):
        argv = list(argv)
        if argv[0] == 'clang++':
            host = next(Path(x) for x in argv if str(x).endswith('/host.cpp'))
            source = host.with_name('dispatch.cpp')
            body = baseline(SOURCE)
            if not self.unchanged:
                body = replace_once(body, 'return RenderDirectional8(input, output, info);',
                    'if (IsGenericDeepFeatureShape(info)) return RenderExact8(input, output, noise_layer, info);\n'
                    '\t\treturn RenderDirectional8(input, output, info);')
            body = body.replace('#include "../../core/', f'#include "{ROOT}/core/')
            body = body.replace('#include "OLMDirectionalBlur.h"', f'#include "{SOURCE.with_suffix(".h")}"')
            source.write_text(body)
            host.write_text(replace_once(host.read_text(), str(SOURCE), str(source)))
            original = ROOT/'core/dblur_frontonly.cpp'
            core = host.with_name('core.cpp')
            body = baseline(original)
            if not self.unchanged:
                body = replace_once(body, '(front_strength <= 0 && back_strength <= 0)',
                    '(front_strength <= 0 && back_strength <= 0 && front_alpha_fade <= 0 && back_alpha_fade <= 0)')
            body = '#include <cstdio>\n#include <cstdlib>\n'+body
            body = replace_once(body,
                'output_rgba[destination + 0] = static_cast<std::uint8_t>(',
                'if (const char* path = std::getenv("OLM_F06_FLOATS")) {\n'
                '  if (FILE* file = std::fopen(path, "ab")) {\n'
                '    std::fwrite(buffer_a.data()+source, sizeof(float), 4, file); std::fclose(file);\n'
                '  }\n}\n'
                'output_rgba[destination + 0] = static_cast<std::uint8_t>(')
            core.write_text(body)
            argv = [core if x == original else x for x in argv]
            argv += ['-I', ROOT/'core']
            if self.sanitizer:
                argv += ['-fsanitize=address,undefined', '-fno-sanitize-recover=all', '-fno-omit-frame-pointer', '-g']
        self.commands.append(list(map(str, argv)))
        return super().compile(argv, deadline)


class Sanitized(Adapter):
    def compile(self, argv, deadline):
        argv = list(argv)
        if argv[0] == 'clang++':
            argv += ['-fsanitize=address,undefined','-fno-sanitize-recover=all','-fno-omit-frame-pointer','-g']
        self.env.update(ASAN_OPTIONS='detect_leaks=0:halt_on_error=1', UBSAN_OPTIONS='halt_on_error=1:print_stacktrace=1')
        return super().compile(argv, deadline)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--worker', type=Path, required=True)
    p.add_argument('--report', type=Path, required=True)
    p.add_argument('--main', type=Path, default=ROOT.parent.parent)
    p.add_argument('--campaign', action='store_true')
    p.add_argument('--production', action='store_true')
    args = p.parse_args()
    args.max_size, args.case_timeout = 256, 10
    scratch = ROOT/'orchestra/state'/TICKET
    scratch.mkdir(parents=True, exist_ok=True)
    os.environ.update(TMPDIR=str(scratch), TMP=str(scratch), TEMP=str(scratch))
    tempfile.tempdir = str(scratch)
    deadline = time.monotonic()+1200
    triage = json.loads((ROOT/'reports/fuzz/olmdirectionalblur_triage_20261022.json').read_text())
    targets = {c['corpus']:c['cluster'] for c in triage['clusters'] if c['cluster'] in (4,5,6,7,16,17)}
    paths = list(range(300)) if args.campaign else sorted((ROOT/'tests/fuzz_corpus/olmdirectionalblur').glob('*.json'))
    report = {'schema':'directionalblur.pf8-dispatch-probe/1', 'cases':[], 'builds':[],
              'baseline_ref':BASE_REF, 'production':args.production,
              'baseline_source_sha256':sha(baseline(SOURCE).encode()),
              'baseline_core_sha256':sha(baseline(ROOT/'core/dblur_frontonly.cpp').encode())}
    with tempfile.TemporaryDirectory(prefix='probe_', dir=scratch) as tmp:
        tmp = Path(tmp)
        adapters = [Probe(args, unchanged=True),
                    Adapter(args) if args.production else Probe(args),
                    Sanitized(args) if args.production else Probe(args, True)]
        for i, adapter in enumerate(adapters):
            directory = tmp/str(i); directory.mkdir()
            report['builds'].append(adapter.prepare(directory, deadline))
        def run(path):
            case = adapters[0].generate(1, path) if args.campaign else load_corpus(path, adapters[0])[0]
            results = []
            with tempfile.TemporaryDirectory(prefix='case_', dir=tmp) as directory:
                for adapter in adapters:
                    results.append(evaluate(adapter, case, Path(directory), deadline))
            name = str(path) if args.campaign else str(path.relative_to(ROOT))
            return {'path':name, 'cluster':targets.get(name),
                    'before':results[0], 'gate_off':results[1], 'sanitized':results[2],
                    'sanitizer_same':results[1] == results[2]}
        with ThreadPoolExecutor(max_workers=2) as pool:
            report['cases'] = list(pool.map(run, paths))
        report['commands'] = [getattr(a,'commands',[]) for a in adapters]
    report['script_sha256'] = sha(Path(__file__).read_bytes())
    args.report.write_text(json.dumps(report, sort_keys=True, indent=2)+'\n')
    assert all(r['sanitizer_same'] for r in report['cases'])
    if args.production:
        for route in adapters[0].routes:
            before_count = sum(r['before']['routes'][route]['status']=='exact' for r in report['cases'])
            after_count = sum(r['gate_off']['routes'][route]['status']=='exact' for r in report['cases'])
            assert after_count >= before_count
        for row in report['cases']:
            for route in adapters[0].routes:
                before, after = row['before']['routes'][route], row['gate_off']['routes'][route]
                if before.get('raw_sha256') != after.get('raw_sha256'):
                    assert after['status'] in ('exact','refusal'), row['path']
                if not args.campaign and before != after:
                    assert after['status']=='exact', row['path']
    for row in report['cases']:
        if row['cluster']:
            print(row['cluster'], {k:row[k]['routes']['classic'] for k in ('before','gate_off')}, 'san_same',row['sanitizer_same'])
    print('SANITIZER SAME', sum(r['sanitizer_same'] for r in report['cases']), '/', len(report['cases']))


if __name__ == '__main__':
    main()
