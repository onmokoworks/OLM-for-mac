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

# Smoother2 P00b corpus03 (all depths) and corpus05 (PF8/4K)
# contain identical parameter lists; corpus03 represents both heavy presets.
HEAVY = dict(olmdirectionalblur=9, radialblur=5, olmblur=5, olmcolorkey=5, olmsmoother=0, olmsmoother2=3, olmkirakira=5)

PLUGINS = ('olmdirectionalblur', 'radialblur', 'olmblur', 'olmcolorkey', 'olmsmoother', 'olmkirakira', 'olmsmoother2')


def build(kind, options, directory, deadline):
    base = importlib.import_module('adapters.' + options.plugin).Adapter
    adapter = base(options)
    adapter.reference_build = kind == 'reference'
    adapter.env.update(TMPDIR=str(directory), TMP=str(directory), TEMP=str(directory))
    directory.mkdir(parents=True, exist_ok=True)
    adapter.binary, dependencies = adapter.build(directory, deadline)
    sources = set(dependencies) | set((ROOT/'core').glob('*.h'))
    sources.update(header for source in dependencies for header in source.parent.glob('*.h'))
    adapter.build_sources = {str(path.relative_to(ROOT)): digest(path) for path in sorted(sources)}
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
    if args.large_corpus and args.hd+args.uhd and not corpus:
        raise RuntimeError('No retained exact P00b corpus samples')
    for index in range(args.small + args.hd + args.uhd):
        adapter.size_sampler = 'odd-even-v1' if index % 4 == 3 else 'default'
        adapter.max_size = args.max_size if index % 4 == 3 else 64
        adapter.size_max_height = args.max_height
        phase = 'small' if index < args.small else '1080p' if index < args.small + args.hd else '4k'
        case = adapter.generate(args.seed, index)
        if phase != 'small' and args.cycle_depth:
            phase_index = index-args.small-(args.hd if phase=='4k' else 0)
            desired = (8,16,32)[phase_index % 3]
            attempt = 0
            while case['depth'] != desired:
                attempt += 1
                case = adapter.generate(args.seed, index+attempt*100000)
        case['sequence_index'] = index
        if phase != 'small':
            # Include all ten P00b corpus parameter sets, including corpus09.
            old = case['geometry']
            if corpus and args.large_corpus:
                phase_count = args.hd if phase == '1080p' else args.uhd
                phase_index = index-args.small-(args.hd if phase=='4k' else 0)
                corpus_index = HEAVY[adapter.name] if phase_index >= max(0, phase_count-3) else (index-args.small) % len(corpus)
                if args.corpus_index is not None:
                    corpus_index = args.corpus_index
                _, saved = corpus[corpus_index]
                old = saved['case']['geometry']
                case['parameters'] = copy.deepcopy(saved['case']['parameters'])
                case['parameter_source'] = str(corpus[corpus_index][0].relative_to(ROOT))
            case['geometry'] = [1920,1080] if phase == '1080p' else [3840,2160]
            n = case['geometry'][0]*case['geometry'][1]*case['depth']//8*4
            payload = case['pixels']
            case['pixels'] = (payload * ((n+len(payload)-1)//len(payload)))[:n]
            # P00b presets are literal parameter values, including points.
            # Only procedural fuzz parameters follow the generated frame resize.
            if not (corpus and args.large_corpus):
                adapter.resize(case, old)
        if phase != 'small' and args.default_params:
            case['parameters'] = adapter.defaults(*case['geometry'])
            case['parameter_source'] = 'PARAMS_SETUP defaults'
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
    p.add_argument('--jobs', type=int, choices=(1,), default=1, help='Native builds and renders are serialized')
    p.add_argument('--cycle-depth', action=argparse.BooleanOptionalAction, default=True, help='Guarantee every depth in each fixed-size phase')
    p.add_argument('--max-size', type=int, default=64)
    p.add_argument('--large-corpus', action=argparse.BooleanOptionalAction, default=True, help='Use P00b corpus parameters for fixed-size frames (default: enabled)')
    p.add_argument('--default-params', action='store_true', help='Use Smoother2 declared defaults for fixed-size frames (requires --no-large-corpus)')
    p.add_argument('--corpus-index', type=int, choices=range(10), help='Choose one P00b corpus parameter set (requires --large-corpus)')
    p.add_argument('--max-height', type=int, default=64)
    p.add_argument('--case-timeout', type=float, default=180)
    p.add_argument('--parallel', type=int, nargs='+', help='Override thread caps (default: 1/2/8 for threaded plugins, 1 otherwise)')
    p.add_argument('--scratch', type=Path, default=ROOT/'orchestra/state/R10-reference-fast-split')
    args = p.parse_args()
    if min(args.small,args.hd,args.uhd) < 0 or not (1 <= args.max_size <= 4096 and 1 <= args.max_height <= 4096) or args.case_timeout <= 0:
        p.error('counts must be nonnegative, sizes 1..4096, and timeout positive')
    if args.default_params and (args.plugin != 'olmsmoother2' or args.large_corpus):
        p.error('--default-params requires --plugin olmsmoother2 --no-large-corpus')
    if args.corpus_index is not None and not args.large_corpus:
        p.error('--corpus-index requires --large-corpus')
    if args.parallel is not None and any(n < 1 for n in args.parallel):
        p.error('thread caps must be positive')
    if args.parallel is None:
        args.parallel = [1,2,8] if args.plugin in ('olmdirectionalblur','olmblur','olmkirakira','radialblur','olmsmoother2') else [1]
    args.scratch = args.scratch.resolve() / args.plugin
    if not args.scratch.is_relative_to(ROOT/'orchestra/state'):
        p.error('scratch must be inside this worktree/orchestra/state')
    args.scratch.mkdir(parents=True, exist_ok=True)
    for stale in ('summary.json','failure.json','builds.json','current-case.json'):
        (args.scratch/stale).unlink(missing_ok=True)
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
        (args.scratch/'builds.json').write_text(json.dumps({kind: {'binary_sha256': digest(adapter.binary), 'reference_definition': kind=='reference', 'sources': adapter.build_sources} for kind, adapter in adapters.items()}, indent=2)+'\n')
        counts = {'exact':0, 'refusal':0, 'mismatch':0}
        with (args.scratch/'results.jsonl').open('w') as report:
            for phase, case in cases(adapters['fast'], args):
                # A timeout must not leave a previous case's output beside the
                # current input and metadata. Preserve only this case's streams.
                for kind in adapters:
                    for name in ('input.raw','output.raw','stdout','stderr','geometry-input.raw','geometry-output.raw'):
                        (args.scratch/kind/name).unlink(missing_ok=True)
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
                    if status == 'mismatch':
                        break  # Keep this failing output; never overwrite it with the next cap.
                report.write(json.dumps(record)+'\n'); report.flush()
                print(phase, case['index'], case['depth'], counts, flush=True)
                if counts['mismatch']:
                    # Retain the exact input and both outputs at the first failure.
                    return 1
        (args.scratch/'summary.json').write_text(json.dumps(dict(counts=counts, seconds=time.monotonic()-started, requested=vars(args)), default=str, indent=2)+'\n')
        for kind in adapters:
            for name in ('input.raw','output.raw','stdout','stderr','geometry-input.raw','geometry-output.raw'):
                (args.scratch/kind/name).unlink(missing_ok=True)
        return 0
    except Exception as exc:
        (args.scratch/'failure.json').write_text(json.dumps({'error':str(exc), 'seconds':time.monotonic()-started}, indent=2)+'\n')
        raise
    finally:
        for kind in adapters:
            shutil.rmtree(args.scratch/kind/'ucrtmath', ignore_errors=True)


if __name__ == '__main__':
    sys.exit(main())
