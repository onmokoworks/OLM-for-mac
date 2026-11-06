#!/usr/bin/env python3
"""Compile production leaf functions without the AE SDK; never launch AE/AEX.

This checks the deterministic read contract and equality to the previous Mac
zero-guard implementation. It does not validate full macOS plug-in rendering.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

sys.dont_write_bytecode = True
from core import load_corpus

ROOT = Path(__file__).resolve().parents[2]
BASE = 'ac0e314c08827b96a4738ab47d83db7c577d14a4'


def extract(text, start):
    begin = text.index(start)
    brace = text.index('{', begin)
    level = 1
    end = brace + 1
    while level:
        level += (text[end] == '{') - (text[end] == '}')
        end += 1
    return text[begin:end] + '\n'


def functions(read, prefix=''):
    sampling = read('mac/OLMRadialBlur/RadialSampling.inc')
    traits = read('mac/OLMRadialBlur/RadialPixelTraits.inc')
    body = extract(traits, 'static bool RadialSizeVariationEnabled(')
    body += extract(traits, 'template <typename PixelT>\nstatic bool BuildRadialSizeFactorPlaneAEX(')
    body += extract(sampling, 'static float SampleScalarAEXRepeat(')
    for name in ('RadialSizeVariationEnabled', 'BuildRadialSizeFactorPlaneAEX', 'SampleScalarAEXRepeat'):
        body = body.replace(name, prefix + name)
    return body


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--scratch', type=Path, required=True)
    ap.add_argument('--compiler', default='clang++')
    ap.add_argument('--sanitize', action='store_true')
    args = ap.parse_args()
    scratch = args.scratch.resolve()
    scratch.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ, TMP=str(scratch), TEMP=str(scratch), TMPDIR=str(scratch))
    baseline = lambda path: subprocess.check_output(
        ['git', 'show', BASE + ':' + path], cwd=ROOT).decode('utf-8').replace('\r\n', '\n')
    body = functions(baseline, 'Before') + functions(lambda p: (ROOT/p).read_text(encoding='utf-8'))
    (scratch/'production_functions.inc').write_text(body, encoding='utf-8')
    binary = scratch/('tail-reads.exe' if os.name == 'nt' else 'tail-reads')
    command = [args.compiler, '-std=c++17', '-O2', '-ffp-contract=off',
               '-I'+str(scratch), str(Path(__file__).with_name('test_radial_tail_reads_T32.cpp')),
               '-o', str(binary)]
    if args.sanitize:
        command += ['-fsanitize=address,undefined', '-fno-omit-frame-pointer']
        env.update(ASAN_OPTIONS='halt_on_error=1', UBSAN_OPTIONS='halt_on_error=1')
        if os.name == 'nt':
            resource = Path(subprocess.check_output(
                [args.compiler, '-print-resource-dir'], env=env, text=True).strip())
            # LLVM's Windows distribution keeps its ASan DLL here, outside
            # the compiler's bin directory. Do not copy or install the DLL.
            env['PATH'] = str(resource/'lib/windows') + os.pathsep + env.get('PATH', '')
    with (scratch/'build.log').open('w', encoding='utf-8') as log:
        subprocess.run(command, env=env, stdout=log, stderr=subprocess.STDOUT, check=True)
    runs = []
    adapter = SimpleNamespace(name='radialblur', generator_version=1, max_size=256)
    for path in sorted((ROOT/'tests/fuzz_witnesses/radialblur').glob('T32_*.json')):
        case, saved = load_corpus(path, adapter)
        w, h = case['geometry']
        assert len(case['pixels']) == w*h*(8 if case['depth'] == 16 else 16)
        assert saved['provenance']['t15_tag1_sha256'] == saved['input_sha256']
        raw = scratch/(path.stem+'.raw')
        raw.write_bytes(case['pixels'])
        sv = next(p['value'] for p in case['parameters'] if p['slot'] == 22)
        result = subprocess.run([str(binary), str(raw), str(w), str(h), str(case['depth']), str(sv)],
                                env=env, capture_output=True, text=True)
        (scratch/(path.stem+'.log')).write_text(result.stdout+result.stderr, encoding='utf-8')
        result.check_returncode()
        runs.append(dict(witness=path.relative_to(ROOT).as_posix(), input_sha256=saved['input_sha256'],
                         result=result.stdout.strip()))
    assert len(runs) == 2, 'Both captured T15 witnesses are required'
    summary = dict(baseline=BASE, sanitizer=args.sanitize, build_command=command,
                   extracted_functions_sha256=hashlib.sha256(body.encode()).hexdigest(), runs=runs,
                   scope='SDK-free production leaves; full macOS render and AE exact NOT tested')
    (scratch/'summary.json').write_text(json.dumps(summary, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
