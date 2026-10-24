#!/usr/bin/env python3
"""Native reference/fast raw-byte differential; no AEX worker is invoked."""
import argparse
import copy
import re
import hashlib
import importlib
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import time
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[2]
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT / 'tools/fuzz'))
from adapters.public import geometry_environment
from geometry import sample, require_host

PLUGINS = ('olmdirectionalblur', 'radialblur', 'olmblur', 'olmcolorkey', 'olmsmoother', 'olmkirakira')


def build(kind, options, directory, deadline):
    base = importlib.import_module('adapters.' + options.plugin).Adapter
    class Native(base):
        def compile(self, argv, end):
            if str(argv[0]) == 'clang++' and kind == 'reference':
                argv = [*argv, '-DOLM_REFERENCE_BUILD=1']
            return super().compile(argv, end)
    adapter = Native(options)
    adapter.env.update(TMPDIR=str(directory), TMP=str(directory), TEMP=str(directory))
    directory.mkdir(parents=True, exist_ok=True)
    adapter.binary, _ = adapter.build(directory, deadline)
    return adapter


def digest(path):
    with path.open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def run(adapter, case, directory, parallel, timeout):
    require_host(adapter, case)
    argv, data = adapter.candidate_command(case, directory, 'classic' if adapter.name == 'olmsmoother' else 'smart')
    env = dict(adapter.env, OLM_PARALLEL_MAX=str(parallel))
    geometry_environment(case, directory, env)
    inp, out, err = [directory / n for n in ('input.raw', 'stdout', 'stderr')]
    inp.write_bytes(data)
    del data
    with inp.open('rb') as i, out.open('wb') as o, err.open('wb') as e:
        proc = subprocess.Popen(list(map(str, argv)), stdin=i, stdout=o, stderr=e,
                                env=env, start_new_session=True)
        try:
            proc.wait(timeout=timeout)
        except BaseException:
            os.killpg(proc.pid, signal.SIGKILL)
            proc.wait()
            raise
    if proc.returncode:
        raise RuntimeError(f'host exit {proc.returncode}: {err.read_text()[-2000:]}')
    metadata = dict(line.split(' ', 1) for line in err.read_text().splitlines() if ' ' in line)
    raw = directory / 'output.raw'
    if adapter.output_format == 'hex':
        with out.open('rb') as source, raw.open('wb') as target:
            while True:
                prefix = source.read(4)
                if not prefix:
                    break
                if prefix == b'RAW ':
                    while chunk := source.read(1024 * 1024):
                        target.write(bytes.fromhex(chunk.decode()))
                    break
                line = prefix + source.readline()
                key, value = line.decode().strip().split(' ', 1)
                metadata[key] = value
    else:
        out.replace(raw)
    error = int(metadata['ERROR'])
    rect = [0, 0, *case['geometry']]
    if case.get('geometry_sampler') and adapter.name != 'olmsmoother' and not error:
        rect = list(map(int, metadata['GEOMETRY'].split()))
        (directory / 'geometry-output.raw').replace(raw)
    if error:
        raw.write_bytes(b'')
    elif raw.stat().st_size != (rect[2]-rect[0])*(rect[3]-rect[1])*case['depth']//8*4:
        raise RuntimeError('raw output size differs from output rect')
    return {'error': error, 'rect': rect, 'sha256': digest(raw), 'bytes': raw.stat().st_size}, raw


def difference(a, b):
    offset = 0
    with a.open('rb') as x, b.open('rb') as y:
        while True:
            left, right = x.read(1048576), y.read(1048576)
            if left != right:
                return offset + next((i for i, (p, q) in enumerate(zip(left, right)) if p != q), min(len(left), len(right)))
            if not left:
                return None
            offset += len(left)


def cases(adapter, args):
    # Every sampler retains its own deterministic fuzz RNG stream. Large fixed
    # frames tile the generated payload to avoid millions of Python RNG calls;
    # parameters and exceptional float words remain from the original generator.
    from ae_realism_audit import samples
    corpus, _ = samples(adapter.name)
    for index in range(args.small + args.hd + args.uhd):
        adapter.size_sampler = 'odd-even-v1' if index % 4 == 3 else 'default'
        adapter.max_size = args.max_size if index % 4 == 3 else 64
        adapter.size_max_height = args.max_height
        case = adapter.generate(args.seed, index)
        phase = 'small' if index < args.small else '1080p' if index < args.small + args.hd else '4k'
        if phase != 'small':
            # Include all ten P00b corpus parameter sets, including corpus09.
            if corpus and args.large_corpus:
                _, saved = corpus[(index-args.small) % len(corpus)]
                case['parameters'] = copy.deepcopy(saved['case']['parameters'])
                case['parameter_source'] = str(corpus[(index-args.small) % len(corpus)][0].relative_to(ROOT))
            old = case['geometry']
            case['geometry'] = [1920,1080] if phase == '1080p' else [3840,2160]
            n = case['geometry'][0]*case['geometry'][1]*case['depth']//8*4
            payload = case['pixels']
            case['pixels'] = (payload * ((n+len(payload)-1)//len(payload)))[:n]
            adapter.resize(case, old)
        # Downsample/ROI are independently exercised by the small cases. Fixed
        # large cases must really render their requested full frame dimensions.
        if phase == 'small':
            case = sample(case, ('default','realistic-v1','realistic-v2','default')[index % 4])
        yield phase, case


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--plugin', choices=PLUGINS, required=True)
    p.add_argument('--small', type=int, default=200)
    p.add_argument('--hd', type=int, default=20)
    p.add_argument('--uhd', type=int, default=5)
    p.add_argument('--seed', type=int, default=1)
    p.add_argument('--max-size', type=int, default=64)
    p.add_argument('--large-corpus', action='store_true', help='Use P00b corpus parameters for fixed-size frames')
    p.add_argument('--max-height', type=int, default=2160)
    p.add_argument('--case-timeout', type=float, default=180)
    p.add_argument('--parallel', type=int, nargs='+', default=[1,2,8])
    p.add_argument('--scratch', type=Path, default=ROOT/'orchestra/state/R10-reference-fast-split')
    args = p.parse_args()
    args.scratch = args.scratch.resolve() / args.plugin
    if not args.scratch.is_relative_to(ROOT/'orchestra/state'):
        p.error('scratch must be inside this worktree/orchestra/state')
    args.scratch.mkdir(parents=True, exist_ok=True)
    options = SimpleNamespace(**vars(args), main=ROOT.parent.parent if ROOT.parent.name=='worktrees' else ROOT,
                              worker=Path('/unused'), size_sampler='default', size_max_height=args.max_height)
    free = re.search(r'System-wide memory free percentage: (\d+)%', subprocess.check_output(['memory_pressure'], text=True))
    if not free or int(free[1]) < 30:
        raise RuntimeError('memory_pressure must report at least 30% free')
    started = time.monotonic()
    adapters = {}
    try:
        for kind in ('fast','reference'):
            adapters[kind] = build(kind, options, args.scratch/kind, time.monotonic()+300)
            print('built', kind, flush=True)
        (args.scratch/'builds.json').write_text(json.dumps({kind: {'binary_sha256': digest(adapter.binary), 'reference_definition': kind=='reference'} for kind, adapter in adapters.items()}, indent=2)+'\n')
        counts = {'exact':0, 'refusal':0, 'mismatch':0}
        with (args.scratch/'results.jsonl').open('w') as report:
            for phase, case in cases(adapters['fast'], args):
                record = {'phase':phase, 'case':{k:v for k,v in case.items() if k!='pixels'}, 'input_sha256':hashlib.sha256(case['pixels']).hexdigest()}
                (args.scratch/'current-case.json').write_text(json.dumps(record, indent=2)+'\n')
                ref, reference = run(adapters['reference'],case,args.scratch/'reference',8,args.case_timeout)
                record['reference'] = ref
                record['fast'] = {}
                for parallel in args.parallel:
                    fast, actual = run(adapters['fast'],case,args.scratch/'fast',parallel,args.case_timeout)
                    first = difference(reference, actual)
                    status = 'mismatch' if ref != fast or first is not None else 'refusal' if ref['error'] else 'exact'
                    counts[status] += 1
                    record['fast'][parallel] = dict(fast, status=status, first_mismatch=first)
                report.write(json.dumps(record)+'\n'); report.flush()
                print(phase, case['index'], case['depth'], counts, flush=True)
                if counts['mismatch']:
                    # Retain the exact input and both outputs at the first failure.
                    return 1
        (args.scratch/'summary.json').write_text(json.dumps(dict(counts=counts, seconds=time.monotonic()-started, requested=vars(args)), default=str, indent=2)+'\n')
        return 0
    except Exception as exc:
        (args.scratch/'failure.json').write_text(json.dumps({'error':str(exc), 'seconds':time.monotonic()-started}, indent=2)+'\n')
        raise
    finally:
        for kind in adapters:
            shutil.rmtree(args.scratch/kind/'ucrtmath', ignore_errors=True)


if __name__ == '__main__':
    sys.exit(main())
