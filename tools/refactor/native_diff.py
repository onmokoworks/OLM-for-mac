#!/usr/bin/env python3
"""Compare native raw output and refusal tags between two source revisions."""
import argparse
from collections import Counter
import hashlib
import importlib
import json
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import sys
import time
from types import MethodType, SimpleNamespace

ROOT = Path(__file__).resolve().parents[2]
PLUGINS = ('olmdistancegradation', 'olmdirectionalblur', 'radialblur', 'olmblur',
           'olmcolorkey', 'colorkeep', 'olmtoondilate', 'olmsmoother',
           'olmsmoother2', 'olmkirakira')
sys.dont_write_bytecode = True


def adapter_at(root, plugin, main, timeout):
    sys.path.insert(0, str(root / 'tools/fuzz'))
    cls = importlib.import_module('adapters.' + plugin).Adapter
    return cls(SimpleNamespace(main=main, worker=Path('/unused'), max_size=64,
                              size_max_height=64, case_timeout=timeout))


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        while data := f.read(1048576):
            h.update(data)
    return h.hexdigest()


def first_difference(a, b):
    offset = 0
    with a.open('rb') as x, b.open('rb') as y:
        while True:
            left, right = x.read(1048576), y.read(1048576)
            if left != right:
                return offset + next((i for i, (p, q) in enumerate(zip(left, right))
                                      if p != q), min(len(left), len(right)))
            if not left:
                return None
            offset += len(left)


def classify(a, b, first):
    valid = all(r['status'] in ('ok', 'refusal') for r in (a, b))
    different = a != b or first is not None
    status = ('difference' if different else 'exact' if a['status'] == 'ok'
              else 'refusal' if valid else 'execution_error')
    return valid, different, status


def render(adapter, case, directory, arch, timeout):
    from adapters.public import geometry_environment
    from geometry import require_host
    require_host(adapter, case)
    route = 'classic' if adapter.name == 'olmsmoother' else 'smart'
    for name in ('output.raw', 'geometry-output.raw', 'trace'):
        (directory / name).unlink(missing_ok=True)
    argv, data = adapter.candidate_command(case, directory, route)
    env = dict(adapter.env, OLM_PARALLEL_MAX='1', OLM_REFUSAL_TRACE=str(directory/'trace'))
    geometry_environment(case, directory, env)
    (directory/'input.raw').write_bytes(data)
    del data
    timed_out = False
    with (directory/'input.raw').open('rb') as inp, (directory/'stdout').open('wb') as out, (directory/'stderr').open('wb') as err:
        proc = subprocess.Popen(['/usr/bin/arch', '-'+arch, *map(str, argv)],
                                stdin=inp, stdout=out, stderr=err, env=env, start_new_session=True)
        try:
            proc.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            timed_out = True
            os.killpg(proc.pid, signal.SIGKILL)
            proc.wait()
        except BaseException:
            os.killpg(proc.pid, signal.SIGKILL)
            proc.wait()
            raise
    raw = directory/'output.raw'
    raw.write_bytes(b'')
    trace = directory/'trace'
    # Source lines necessarily move during a refactor; guard identity does not.
    tags = [re.sub(r'@\d+$', '', line) for line in trace.read_text().splitlines()] if trace.exists() else []
    if timed_out or proc.returncode:
        return dict(status='timeout' if timed_out else 'process_error', exit=proc.returncode,
                    tags=tags, stderr=(directory/'stderr').read_text(errors='replace')[-2000:])
    metadata = dict(line.split(' ', 1) for line in (directory/'stderr').read_text().splitlines() if ' ' in line)
    if adapter.output_format == 'hex':
        with (directory/'stdout').open('rb') as source, raw.open('wb') as target:
            while prefix := source.read(4):
                if prefix == b'RAW ':
                    while chunk := source.read(1048576):
                        target.write(bytes.fromhex(chunk.decode()))
                    break
                key, value = (prefix + source.readline()).decode().strip().split(' ', 1)
                metadata[key] = value
    else:
        (directory/'stdout').replace(raw)
    error = int(metadata['ERROR'])
    rect = [0, 0, *case['geometry']]
    if error:
        raw.write_bytes(b'')
    elif case.get('geometry_sampler') and route == 'smart':
        rect = list(map(int, metadata['GEOMETRY'].split()))
        (directory/'geometry-output.raw').replace(raw)
    if not error and raw.stat().st_size != (rect[2]-rect[0])*(rect[3]-rect[1])*case['depth']//8*4:
        raise ValueError('output size does not match negotiated rectangle')
    return dict(status='refusal' if error else 'ok', error=error, tags=tags, rect=rect,
                bytes=raw.stat().st_size, sha256=digest(raw))


def worker(config_path):
    def terminate(signum, frame):
        raise SystemExit(128 + signum)

    signal.signal(signal.SIGTERM, terminate)
    cfg = json.loads(Path(config_path).read_text())
    directory, root = Path(cfg['directory']), Path(cfg['root'])
    adapter = adapter_at(root, cfg['plugin'], Path(cfg['main']), cfg['timeout'])
    adapter.reference_build = cfg['build'] == 'reference'
    adapter.env.update(TMPDIR=str(directory), TMP=str(directory), TEMP=str(directory))
    original = getattr(adapter, 'compile', None)

    def compile_arch(self, argv, deadline):
        argv = list(argv)
        if str(argv[0]) == 'clang++':
            if '-arch' in argv:
                argv[argv.index('-arch')+1] = cfg['arch']
            else:
                argv += ['-arch', cfg['arch']]
        elif str(argv[0]) == 'sh' and str(argv[1]).endswith('/ucrtmath/build.sh'):
            argv.append(cfg['arch'])
        return original(argv, deadline)

    if original is not None:
        adapter.compile = MethodType(compile_arch, adapter)
    else:
        # RadialBlur delegates its retained builder to a separate Python process.
        # Adapt that process's compiler/library argv without editing the revision.
        module = importlib.import_module('adapters.' + cfg['plugin'])
        original_command = module.command
        prefix = f"""import subprocess
_native_run = subprocess.run
def _arch_run(argv, *args, **kwargs):
    argv = list(argv)
    if '-arch' in argv:
        argv[argv.index('-arch')+1] = {cfg['arch']!r}
    if len(argv) > 2 and str(argv[1]).endswith('/ucrtmath/build.sh'):
        argv = argv[:3] + [{cfg['arch']!r}]
    return _native_run(argv, *args, **kwargs)
subprocess.run = _arch_run
"""

        def build_command(argv, **kwargs):
            argv = list(argv)
            if len(argv) < 3 or argv[1] != '-c':
                raise ValueError('unexpected delegated builder command')
            argv[2] = prefix + argv[2]
            return original_command(argv, **kwargs)

        module.command = build_command
    adapter.binary, _ = adapter.build(directory, time.monotonic()+300)
    architectures = subprocess.check_output(['lipo', '-archs', str(adapter.binary)], text=True).strip()
    if architectures != cfg['arch']:
        raise RuntimeError('unexpected harness architecture: '+architectures)
    print(json.dumps({'ready': True, 'architecture': architectures, 'binary_sha256': digest(adapter.binary)}), flush=True)
    for line in sys.stdin:
        case = json.loads(Path(line.strip()).read_text())
        case['pixels'] = Path(case.pop('pixel_path')).read_bytes()
        try:
            result = render(adapter, case, directory, cfg['arch'], cfg['timeout'])
        except Exception as exc:
            result = {'status': 'harness_error', 'diagnostic': repr(exc)}
        print(json.dumps(result), flush=True)


def cases(adapter, count, seed):
    from geometry import sample
    # Nine small strata cover all depths for each geometry sampler. Odd/even
    # sizing and S02 independent float colours alternate independently.
    for index in range(count + 3):
        large = index >= count
        desired = (8, 16, 32)[(index-count) if large else index % 3]
        adapter.size_sampler = 'odd-even-v1' if index % 2 else 'default'
        adapter.color_sampler = 'float-v1' if index % 2 else 'default'
        attempt = index
        while True:
            case = adapter.generate(seed, attempt)
            if case['depth'] == desired:
                break
            attempt += count + 3
        case.update(sequence_index=index, size_sampler=adapter.size_sampler)
        if large:
            old = case['geometry']
            case['geometry'] = [3840, 2160]
            n = 3840*2160*desired//8*4
            payload = case['pixels']
            case['pixels'] = (payload*((n+len(payload)-1)//len(payload)))[:n]
            adapter.resize(case, old)
            case['phase'] = '4k'
        else:
            case = sample(case, ('default', 'realistic-v1', 'realistic-v2')[(index//3) % 3])
            case['phase'] = 'small'
        yield case


def snapshot(revision, destination):
    sha = subprocess.check_output(['git', '-C', str(ROOT), 'rev-parse', '--verify', revision+'^{commit}'], text=True).strip()
    destination.mkdir()
    # Archive the native adapter input trees, including RadialBlur declarations.
    # Omit unrelated binary captures/reports; MAIN SDK assets stay in place.
    with subprocess.Popen(['git', '-C', str(ROOT), 'archive', sha, 'mac', 'core', 'cli', 'tools', 'ucrtmath',
                           'reports/radialblur_public_getters_aligned_20261001.json'], stdout=subprocess.PIPE) as archive:
        subprocess.run(['tar', '-xf', '-', '-C', str(destination)], stdin=archive.stdout, check=True)
        archive.stdout.close()
        if archive.wait():
            raise RuntimeError('git archive failed')
    return sha


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--plugin', choices=PLUGINS, required=True)
    p.add_argument('--base', required=True)
    p.add_argument('--head', default='WORKTREE')
    p.add_argument('--cases', type=int, default=3000, help='Small random cases; three full 4K cases are added')
    p.add_argument('--seed', type=int, default=909)
    p.add_argument('--arch', choices=('arm64', 'x86_64', 'both'), default='both')
    p.add_argument('--build', choices=('reference', 'fast', 'both'), default='both')
    p.add_argument('--jobs', type=int, choices=(1,), default=1)
    p.add_argument('--case-timeout', type=float, default=180)
    p.add_argument('--scratch', type=Path, default=ROOT/'orchestra/state/Q00-refactor-native-diff-tool')
    args = p.parse_args()
    if args.cases < 1 or args.case_timeout <= 0:
        p.error('cases and timeout must be positive')
    scratch = args.scratch.resolve()/args.plugin
    if not scratch.is_relative_to(ROOT/'orchestra/state'):
        p.error('scratch must be under this worktree/orchestra/state')
    scratch.mkdir(parents=True, exist_ok=True)
    run_dir = scratch/'run'
    if run_dir.exists():
        p.error('scratch run directory already exists; choose another --scratch or remove the stale run')
    run_dir.mkdir()
    main_root = ROOT.parent.parent if ROOT.parent.name == 'worktrees' else ROOT
    summary = dict(plugin=args.plugin, seed=args.seed, requested_cases=args.cases,
                   counts=Counter(), coverage=Counter(), differences=[], builds={})
    children = []
    logs = []
    try:
        summary['base'] = snapshot(args.base, run_dir/'base-source')
        head_root = ROOT if args.head == 'WORKTREE' else run_dir/'head-source'
        summary['head'] = 'WORKTREE' if args.head == 'WORKTREE' else snapshot(args.head, head_root)
        summary['worktree_diff_sha256'] = hashlib.sha256(subprocess.check_output(['git', '-C', str(ROOT), 'diff', 'HEAD'])).hexdigest()
        generator = adapter_at(ROOT, args.plugin, main_root, args.case_timeout)
        for arch in (('arm64', 'x86_64') if args.arch == 'both' else (args.arch,)):
            for build in (('reference', 'fast') if args.build == 'both' else (args.build,)):
                pair = []
                for side, root in (('base', run_dir/'base-source'), ('head', head_root)):
                    directory = run_dir/f'{arch}-{build}-{side}'
                    directory.mkdir()
                    cfg = dict(root=str(root), directory=str(directory), main=str(main_root),
                               plugin=args.plugin, arch=arch, build=build, timeout=args.case_timeout)
                    config_path = directory/'config.json'
                    config_path.write_text(json.dumps(cfg))
                    log = (scratch/f'{arch}-{build}-{side}.log').open('w')
                    logs.append(log)
                    proc = subprocess.Popen([sys.executable, str(Path(__file__).resolve()), '--worker', str(config_path)],
                                            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=log, text=True)
                    children.append(proc)
                    ready = json.loads(proc.stdout.readline())
                    summary['builds'][directory.name] = ready
                    pair.append((proc, directory))
                with (scratch/f'{arch}-{build}.jsonl').open('w') as records:
                    for case in cases(generator, args.cases, args.seed):
                        pixels = case.pop('pixels')
                        (run_dir/'pixels.raw').write_bytes(pixels)
                        record = dict(case=case, input_sha256=hashlib.sha256(pixels).hexdigest(), arch=arch, build=build)
                        del pixels
                        path = run_dir/'case.json'
                        path.write_text(json.dumps(dict(case, pixel_path=str(run_dir/'pixels.raw'))))
                        results = []
                        for proc, directory in pair:
                            proc.stdin.write(str(path)+'\n'); proc.stdin.flush()
                            results.append(json.loads(proc.stdout.readline()))
                        a, b = results
                        valid = all(r['status'] in ('ok', 'refusal') for r in results)
                        first = first_difference(pair[0][1]/'output.raw', pair[1][1]/'output.raw') if valid else None
                        valid, different, status = classify(a, b, first)
                        summary['counts'][status] += 1
                        summary['counts']['comparisons'] += 1
                        summary['counts']['new_refusals'] += int(a['status'] != 'refusal' and b['status'] == 'refusal')
                        summary['counts']['execution_errors'] += int(not valid)
                        for key in (f"depth:{case['depth']}", case['phase'], 'geometry:'+case.get('geometry_sampler', 'default'), 'size:'+case['size_sampler'], 'colours:'+case.get('color_sampler', 'byte-colours'), 'downsample:'+str(case.get('downsample', [[1, 1], [1, 1]]))):
                            summary['coverage'][key] += 1
                        record.update(base=a, head=b, status=status, first_byte_difference=first)
                        records.write(json.dumps(record)+'\n'); records.flush()
                        if different and len(summary['differences']) < 10:
                            summary['differences'].append(record)
                for proc, directory in pair:
                    proc.stdin.close(); proc.wait(timeout=10)
                    shutil.rmtree(directory)
        return_code = int(bool(summary['counts']['difference'] or summary['counts']['execution_errors']))
    except (Exception, KeyboardInterrupt) as exc:
        summary['fatal_error'] = repr(exc)
        return_code = 2
    finally:
        for proc in children:
            if proc.poll() is None:
                proc.terminate()
                try:
                    proc.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    proc.kill(); proc.wait()
        for log in logs:
            log.close()
        shutil.rmtree(run_dir)
    for key in ('difference', 'exact', 'refusal', 'execution_errors', 'new_refusals', 'comparisons'):
        summary['counts'].setdefault(key, 0)
    (scratch/'summary.json').write_text(json.dumps(summary, indent=2)+'\n')
    print(json.dumps(summary, indent=2))
    return return_code


if __name__ == '__main__':
    if len(sys.argv) == 3 and sys.argv[1] == '--worker':
        worker(sys.argv[2])
    else:
        sys.exit(main())
