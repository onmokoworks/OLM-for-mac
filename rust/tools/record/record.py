#!/usr/bin/env python3
"""Capture native calls during an owned real AEXCompat render; replay with witness."""
from __future__ import annotations
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import struct
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'witness'))
sys.path.insert(0, str(HERE.parent / 'oracle'))
import witness
import olm_oracle as oracle
from contract import checked_blob, returned_spec, sha, size_expr, validate_profile, width, witness_spec, write_json


def pe_info(path):
    import pefile
    pe = pefile.PE(str(path))
    try:
        if pe.FILE_HEADER.Machine != 0x8664:
            raise ValueError('only AMD64 PE supported')
        imports = []
        for desc in getattr(pe, 'DIRECTORY_ENTRY_IMPORT', []):
            for item in desc.imports:
                imports.append({'dll': desc.dll.decode(),
                    'name': item.name.decode() if item.name else f'#{item.ordinal}',
                    'iat_rva': item.address-pe.OPTIONAL_HEADER.ImageBase})
        return {'size': pe.OPTIONAL_HEADER.SizeOfImage, 'entry': pe.OPTIONAL_HEADER.AddressOfEntryPoint,
                'imports': imports}
    finally:
        pe.close()


class Capture:
    def __init__(self, module, profile, out, max_calls, max_bytes):
        self.module, self.profile, self.out = module, profile, out
        self.max_calls, self.max_bytes = max_calls, max_bytes
        self.module_hash = sha(module)
        if profile.get('module_sha256') != self.module_hash:
            raise ValueError('profile must bind the exact module SHA-256')
        self.info = pe_info(module)
        self.records, self.counts, self.closed, self.imports = [], {}, {}, []
        self.bytes_reserved = 0
        self.identities = {str(module): self.module_hash}
        self.event_sequence = 0
        # Missing explicit imports are configuration errors, never silent coverage.
        for f in profile.get('imports', []):
            if not any(x['name'] == f['name'] and ('dll' not in f or x['dll'].lower() == f['dll'].lower())
                       for x in self.info['imports']):
                raise ValueError(f"requested import absent: {f['name']}")

    def tick(self):
        n = self.event_sequence
        self.event_sequence += 1
        return n

    def loaded(self, debug, p):
        # The loader entry executes after the normal IAT is bound, before plugin code.
        debug.bp(p, p['base'] + self.info['entry'],
                 {'name': '__loader_ready', 'args': [], 'return': 'void'})

    def install_imports(self, debug, p):
        if p.get('imports_ready'):
            return
        p['imports_ready'] = True
        for f in self.profile.get('imports', []):
            for imp in self.info['imports']:
                if imp['name'] != f['name'] or ('dll' in f and imp['dll'].lower() != f['dll'].lower()):
                    continue
                target = int.from_bytes(debug.read(p, p['base'] + imp['iat_rva'], 8), 'little')
                provider = None
                for m in reversed(p['loaded']):
                    if not m['path'] or target < m['base']:
                        continue
                    if 'size' not in m:
                        dos = debug.read(p, m['base'], 64)
                        nt = m['base'] + int.from_bytes(dos[60:64], 'little')
                        m['size'] = int.from_bytes(debug.read(p, nt + 24 + 56, 4), 'little')
                    if target < m['base'] + m['size']:
                        provider = m
                        break
                if provider is None:
                    raise ValueError(f'IAT target has no loaded provider: {imp}')
                path = str(Path(provider['path']).resolve())
                self.identities.setdefault(path, sha(path))
                hook = {**f, 'import': imp, 'module': path, 'rva': hex(target-provider['base'])}
                debug.bp(p, target, hook)
                self.imports.append({'pid': p['pid'], **imp, 'target': hex(target),
                    'provider': path, 'provider_sha256': self.identities[path], 'provider_rva': hook['rva']})

    def blob(self, debug, p, rec, b, phase):
        raw = debug.read(p, int(b['address'], 0), b['size'])
        name = f"calls/{rec['sequence']:06d}/{b['name']}.{phase}.bin"
        (self.out / name).parent.mkdir(parents=True, exist_ok=True)
        (self.out / name).write_bytes(raw)
        b[phase] = {'file': name, 'sha256': hashlib.sha256(raw).hexdigest()}

    def entry(self, debug, p, tid, ctx, f):
        self.install_imports(debug, p)
        if f['name'] == '__loader_ready':
            p['bps'][ctx.get(248)-1]['function'] = None
            return None
        rsp = ctx.get(152)
        caller = int.from_bytes(debug.read(p, rsp, 8), 'little')
        if 'import' in f and not p['base'] <= caller < p['base'] + self.info['size']:
            return None  # Provider hooks may also be hit by the host itself.
        name = f['name']
        if len(self.records) >= self.max_calls or self.counts.get(name, 0) >= f.get('max_calls', self.max_calls):
            self.closed[name] = 'call_budget'
            p['bps'][ctx.get(248)-1]['function'] = None
            return None
        args = []
        for i, kind in enumerate(f['args']):
            if i < 4:
                offset = 416 + 16*i if kind.startswith('f') else [128, 136, 184, 192][i]
                bits = ctx.bytes(offset, width(kind))
            else:
                bits = debug.read(p, rsp + 40 + 8*(i-4), width(kind))
            args.append({'type': kind, 'bits_le': bits.hex()})
        buffers, reserve = [], 0
        for i, desc in enumerate(f.get('buffers', [])):
            n = size_expr(desc['size'], args)
            reserve += n if desc.get('returned') else n * 2
            b = {'name': f'buffer{i}', 'size': n, 'stride': size_expr(desc.get('stride', n), args),
                 'role': desc.get('role', 'inout'), 'descriptor': desc}
            if not desc.get('returned'):
                b['address'] = hex(int.from_bytes(bytes.fromhex(args[desc['arg']]['bits_le']), 'little'))
            buffers.append(b)
        if self.bytes_reserved + reserve > self.max_bytes:
            self.closed[name] = 'byte_budget'
            p['bps'][ctx.get(248)-1]['function'] = None
            return None
        self.bytes_reserved += reserve
        self.counts[name] = self.counts.get(name, 0) + 1
        module = f.get('module', str(self.module))
        rec = {'schema_version': 1, 'sequence': len(self.records), 'entry_order': self.tick(),
            'pid': p['pid'], 'tid': tid, 'name': name, 'rva': f['rva'],
            'module': module, 'module_sha256': self.identities[module], 'args': args,
            'return': {'type': f['return']}, 'buffers': buffers, 'status': 'entered',
            'caller': hex(caller), 'caller_plugin_rva': hex(caller-p['base']) if p['base'] <= caller < p['base']+self.info['size'] else None,
            'mxcsr_entry': hex(ctx.get(52, 4)), 'adapter': f.get('adapter'),
            'origin': 'import' if 'import' in f else 'internal'}
        if 'import' in f:
            rec['import'] = f['import']
        self.records.append(rec)
        for b in buffers:
            if 'address' in b:
                self.blob(debug, p, rec, b, 'before')
        self.save(rec)
        return rec

    def save(self, rec):
        folder = self.out / 'calls' / f"{rec['sequence']:06d}"
        folder.mkdir(parents=True, exist_ok=True)
        write_json(folder / 'record.json', rec)

    def returned(self, debug, p, ctx, rec):
        kind = rec['return']['type']
        rec['return']['bits_le'] = ctx.bytes(416 if kind.startswith('f') else 120, width(kind)).hex()
        rec['return']['rax'] = hex(ctx.get(120))
        rec['return']['xmm0'] = ctx.bytes(416, 16).hex()
        rec['mxcsr_return'] = hex(ctx.get(52, 4))
        for b in rec['buffers']:
            if b['descriptor'].get('returned'):
                b['address'] = hex(ctx.get(120))
            self.blob(debug, p, rec, b, 'after')
        rec.update(status='complete', return_order=self.tick())
        self.save(rec)


def capture(args):
    from win_debug import Debugger
    if os.name != 'nt' or struct.calcsize('P') != 8:
        raise OSError('requires 64-bit Windows Python')
    if not math.isfinite(args.timeout) or args.timeout <= 0 or not 0 <= args.max_calls <= 100000 or not 0 <= args.max_bytes <= 256*1024*1024:
        raise ValueError('invalid capture budgets')
    module, profile_path, harness = args.module.resolve(strict=True), args.profile.resolve(strict=True), args.harness.resolve(strict=True)
    profile = validate_profile(json.loads(profile_path.read_text(encoding='utf-8-sig')))
    if not 1 <= args.width <= 8192 or not 1 <= args.height <= 8192 or args.width*args.height > 16*1024*1024:
        raise ValueError('input dimensions exceed the bounded image budget')
    out = args.out.resolve()
    # Validate before starting any process.
    cap = Capture(module, profile, out, args.max_calls, args.max_bytes)
    out.mkdir(parents=True, exist_ok=False)
    write_json(out / 'profile.json', profile)
    from PIL import Image
    Image.fromarray(oracle.input_pixels(args.width, args.height, args.seed), 'RGBA').save(out / 'input.png')
    request = json.loads(args.request.read_text(encoding='utf-8-sig')) if args.request else oracle.make_request(
        {'assignments': [], 'downsample': '1', 'size': [args.width, args.height]})
    write_json(out / 'request.json', request)
    command = [str(harness), '--headless', oracle.ROUTES[args.route][1], str(module),
               str(out / 'input.png'), str(out / 'output.png'), str(out / 'request.json')]
    debug = Debugger(module, profile['functions'], cap.entry, cap.returned, cap.loaded)
    job, process, cleanup = witness.WindowsJob(), None, False
    started, failure = time.monotonic(), None
    manifest = {'schema_version': 1, 'mechanism': 'Windows DEBUG_PROCESS + INT3', 'command': command,
        'module': str(module), 'module_sha256': cap.module_hash, 'harness_sha256': sha(harness),
        'profile_sha256': sha(out / 'profile.json'), 'request_sha256': sha(out / 'request.json'),
        'input_sha256': sha(out / 'input.png'), 'route': args.route, 'seed': args.seed,
        'platform': platform.platform(), 'max_calls': args.max_calls, 'max_bytes': args.max_bytes,
        'imports_inventory': cap.info['imports'], 'timeout': args.timeout}
    try:
        with (out / 'stdout.txt').open('wb') as stdout, (out / 'stderr.txt').open('wb') as stderr:
            process = subprocess.Popen(command, stdout=stdout, stderr=stderr, stdin=subprocess.DEVNULL,
                creationflags=0x1 | 0x4 | 0x08000000,
                env={**os.environ, **oracle.frame_deadline_environment(args.timeout)})
            debug.retain_wait_handle(process)
            manifest['pid'] = process.pid
            write_json(out / 'manifest.json', manifest)
            job.attach_resume(process)
            while True:
                if time.monotonic() - started > args.timeout:
                    raise TimeoutError('capture wall-clock budget exhausted')
                debug.poll()
                if process.pid in debug.exits:
                    break
    except BaseException as e:
        failure = repr(e)
        import traceback
        (out / 'error.txt').write_text(traceback.format_exc(), encoding='utf-8')
    finally:
        try:
            # Debug events must be drained before waiting for terminated processes.
            try:
                job.terminate()
                if process and process.pid not in debug.exits:
                    process.kill()  # also covers failed job assignment, exact owned PID
                debug.drain(process.pid if process else None)
            finally:
                cleanup = job.close()
        finally:
            if process:
                if process.poll() is None:
                    process.kill()
                process.wait(timeout=10)
            manifest.update(classification='error' if failure else 'complete', error=failure,
                cleanup_verified=cleanup, elapsed_seconds=time.monotonic()-started,
                exit_code=debug.exits.get(process.pid, {}).get('exit_code', process.returncode) if process else None, processes=debug.exits,
                modules=debug.modules, imports_installed=cap.imports, calls=len(cap.records),
                completed=sum(r['status'] == 'complete' for r in cap.records), counts=cap.counts,
                budget_closed=cap.closed, snapshot_bytes_reserved=cap.bytes_reserved,
                unobserved=[f['name'] for f in profile['functions'] + profile.get('imports', []) if not cap.counts.get(f['name'])],
                source_sha256={name: sha(HERE / name) for name in ('record.py', 'contract.py', 'win_debug.py')},
                module_sha256_after=sha(module))
            if not failure and (not process or manifest['exit_code'] or not (out / 'output.png').exists()
                    or not cap.records or any(r['status'] != 'complete' for r in cap.records)
                    or cap.module_hash != manifest['module_sha256_after']):
                manifest['classification'] = 'incomplete'
            if (out / 'output.png').exists():
                manifest['output_sha256'] = sha(out / 'output.png')
            try:
                host = json.loads((out / 'stdout.txt').read_text(encoding='utf-8'))
                manifest['render_evidence'] = {k: host.get(k) for k in (
                    'render_path', 'worker_classification', 'pre_render_error', 'smart_render_error',
                    'smart_render_selector_dispatched', 'smart_render_selector_error', 'gpu_render_dispatched')}
                manifest['render_evidence']['stage_events'] = host.get('worker_diagnostics', {}).get('stage_events')
            except (ValueError, OSError):
                manifest['render_evidence'] = None
            manifest['artifacts'] = {p.relative_to(out).as_posix(): sha(p) for p in sorted(out.iterdir())
                if p.is_file() and p.name != 'manifest.json'}
            (out / 'calls.jsonl').write_text(''.join(json.dumps(r, sort_keys=True)+'\n' for r in cap.records), encoding='utf-8')
            write_json(out / 'manifest.json', manifest)
    print(json.dumps({k: manifest[k] for k in ('classification', 'error', 'calls', 'counts', 'cleanup_verified')}))
    return 0 if manifest['classification'] == 'complete' else 2


def replay(args):
    record_path = args.record.resolve(strict=True)
    root = record_path.parents[2]
    rec = json.loads(record_path.read_text(encoding='utf-8'))
    if sha(rec['module']) != rec['module_sha256']:
        raise ValueError('original/provider identity changed')
    spec, regions = witness_spec(rec, root)
    pointer_semantic = None
    if rec['return']['type'] == 'ptr':
        import pefile
        bridge = HERE / 'adapter/target/release/record_return_bridge.dll'
        with pefile.PE(str(bridge)) as pe:
            bridge_rva = next(x.address for x in pe.DIRECTORY_ENTRY_EXPORT.symbols if x.name == b'record_returned')
        spec, pointer_semantic = returned_spec(rec, spec, regions, bridge, bridge_rva)
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    manifest = witness.run(spec, out / 'original', timeout=args.timeout)
    if manifest['classification'] != 'success':
        raise RuntimeError(f"witness failed: {manifest['classification']}")
    native = json.loads((out / 'original/result.json').read_text())['calls'][0]
    adapter = args.adapter or rec.get('adapter')
    if not adapter:
        raise ValueError('record has no Rust adapter; select --adapter')
    adapter_exe = args.adapter_exe.resolve(strict=True)
    adapter_input = {'name': adapter, 'args': rec['args'], 'buffers': [
        {**b, 'before_hex': checked_blob(root, b, 'before').hex() if 'before' in b else None}
        for b in rec['buffers']]}
    write_json(out / 'adapter-input.json', adapter_input)
    proc = witness.run_owned([adapter_exe, out / 'adapter-input.json', out / 'rust.json'], args.timeout, out)
    if proc['returncode'] or proc['timeout']:
        raise RuntimeError('Rust adapter failed; inspect stderr.txt')
    rust = json.loads((out / 'rust.json').read_text())
    comparisons = []

    def compare(label, a, b):
        comparisons.append({'item': label, 'exact': a == b, 'bytes': len(a),
            'expected_sha256': hashlib.sha256(a).hexdigest(), 'actual_sha256': hashlib.sha256(b).hexdigest(),
            'first_difference': next((i for i, (x, y) in enumerate(zip(a, b)) if x != y),
                                     min(len(a), len(b)) if len(a) != len(b) else None)})

    if pointer_semantic is not None:
        compare('original:bridge_status', bytes(4), bytes.fromhex(native['return']['bits_le']))
        meta = (out / 'original' / native['buffers']['_meta']).read_bytes()
        compare('record/original:pointer_relation', (1).to_bytes(8, 'little'), meta[8:16])
        compare('record/rust:pointer_relation', pointer_semantic.encode(), rust['return_pointer'].encode())
    else:
        expected_return = bytes.fromhex(rec['return']['bits_le'])
        compare('record/original:return', expected_return, bytes.fromhex(native['return']['bits_le']))
        compare('record/rust:return', expected_return, bytes.fromhex(rust['return_hex']))
    if len(rust['buffers']) != len(rec['buffers']):
        raise ValueError('adapter buffer count mismatch')
    for i, b in enumerate(rec['buffers']):
        if b['descriptor'].get('returned'):
            raw = (out / 'original' / native['buffers']['_returned']).read_bytes()
            expected = checked_blob(root, b, 'after')
            compare(f'record/original:{b["name"]}', expected, raw)
            compare(f'record/rust:{b["name"]}', expected, bytes.fromhex(rust['buffers'][i]))
            continue
        start = int(b['address'], 0)
        region = next((j for j, (s, e) in enumerate(regions) if s <= start and start+b['size'] <= e), None)
        if region is None:
            raise ValueError('returned allocation has no replay ownership adapter')
        raw = (out / 'original' / native['buffers'][f'b{region}']).read_bytes()
        offset = start - regions[region][0]
        expected = checked_blob(root, b, 'after')
        compare(f'record/original:{b["name"]}', expected, raw[offset:offset+b['size']])
        compare(f'record/rust:{b["name"]}', expected, bytes.fromhex(rust['buffers'][i]))
    result = {'exact': all(x['exact'] for x in comparisons), 'adapter': adapter,
        'record_sha256': sha(record_path), 'adapter_sha256': sha(adapter_exe),
        'original_module_sha256': rec['module_sha256'], 'witness_manifest_sha256': sha(out / 'original/manifest.json'),
        'original_cleanup': manifest['process']['cleanup_verified'], 'adapter_cleanup': proc['cleanup_verified'],
        'comparisons': comparisons}
    write_json(out / 'comparison.json', result)
    print(json.dumps(result))
    return 0 if result['exact'] else 1


def main():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest='command', required=True)
    cap = sub.add_parser('capture')
    cap.add_argument('--module', required=True, type=Path)
    cap.add_argument('--profile', required=True, type=Path)
    cap.add_argument('--harness', type=Path, default=oracle.DEFAULT_HARNESS)
    cap.add_argument('--out', type=Path, required=True)
    cap.add_argument('--request', type=Path)
    cap.add_argument('--route', choices=oracle.ROUTES, default='smart8')
    cap.add_argument('--width', type=int, default=11)
    cap.add_argument('--height', type=int, default=7)
    cap.add_argument('--seed', type=int, default=20261112)
    cap.add_argument('--max-calls', type=int, default=128)
    cap.add_argument('--max-bytes', type=int, default=16*1024*1024)
    cap.add_argument('--timeout', type=float, default=120)
    rep = sub.add_parser('replay')
    rep.add_argument('record', type=Path)
    rep.add_argument('--out', required=True, type=Path)
    rep.add_argument('--adapter')
    rep.add_argument('--adapter-exe', type=Path, default=HERE / 'adapter/target/release/record-adapter.exe')
    rep.add_argument('--timeout', type=float, default=30)
    args = p.parse_args()
    return capture(args) if args.command == 'capture' else replay(args)


if __name__ == '__main__':
    raise SystemExit(main())
