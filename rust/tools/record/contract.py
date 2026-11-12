"""Portable record schema, bounded size expressions, and witness relocation."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path

KINDS = {f'{s}{n}' for s in 'ui' for n in (8, 16, 32, 64)} | {'f32', 'f64', 'ptr'}


def write_json(path, value):
    Path(path).write_text(json.dumps(value, indent=2, sort_keys=True) + '\n', encoding='utf-8')


def sha(path):
    with open(path, 'rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def width(kind):
    return 0 if kind == 'void' else 8 if kind == 'ptr' else int(kind[1:]) // 8


def size_expr(expr, args):
    if type(expr) is int:
        result = expr
    elif isinstance(expr, dict) and set(expr) == {'arg'}:
        arg = args[expr['arg']]
        if arg['type'][0] not in 'ui':
            raise ValueError('sizes require integer arguments')
        result = int.from_bytes(bytes.fromhex(arg['bits_le']), 'little', signed=arg['type'][0] == 'i')
    elif isinstance(expr, dict) and set(expr) == {'mul'} and 1 <= len(expr['mul']) <= 8:
        result = 1
        for x in expr['mul']:
            result *= size_expr(x, args)
    else:
        raise ValueError('size expression must be an integer, arg, or mul')
    if not 0 <= result <= 256 * 1024 * 1024:
        raise ValueError('size expression outside 0..256 MiB')
    return result


def validate_profile(p):
    if p['schema_version'] != 1 or not p.get('functions'):
        raise ValueError('profile requires schema_version 1 and functions')
    names = set()
    for f in p['functions'] + p.get('imports', []):
        if f['name'] in names:
            raise ValueError('duplicate hook name')
        names.add(f['name'])
        if f['name'] == '__loader_ready':
            raise ValueError('reserved hook name')
        if type(f.get('max_calls', 1)) is not int or not 0 <= f.get('max_calls', 1) <= 100000:
            raise ValueError('invalid per-function call budget')
        if len(f['args']) > 32 or any(t not in KINDS for t in f['args']) or f['return'] not in KINDS | {'void'}:
            raise ValueError('unsupported scalar ABI')
        if 'rva' in f and not 0 <= int(f['rva'], 0) <= 0xffffffff:
            raise ValueError('invalid RVA')
        for b in f.get('buffers', []):
            if ('arg' in b) == bool(b.get('returned')):
                raise ValueError('buffer requires exactly one of arg or returned')
            if 'arg' in b and (type(b['arg']) is not int or not 0 <= b['arg'] < len(f['args'])):
                raise ValueError('buffer argument index out of bounds')
            if 'arg' in b and f['args'][b['arg']] != 'ptr':
                raise ValueError('buffer argument must be a pointer')
            if b.get('returned') and f['return'] != 'ptr':
                raise ValueError('returned buffer needs pointer return')
    return p


def checked_blob(root, item, phase):
    path = (root / item[phase]['file']).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError('snapshot escapes recording')
    raw = path.read_bytes()
    if len(raw) != item['size'] or hashlib.sha256(raw).hexdigest() != item[phase]['sha256']:
        raise ValueError('snapshot identity mismatch')
    return raw


def witness_spec(record, root):
    """Merge overlapping regions so replay preserves pointer aliasing."""
    root = Path(root)
    if record['status'] != 'complete':
        raise ValueError('cannot replay incomplete call')
    regions = sorted((int(b['address'], 0), int(b['address'], 0) + b['size'])
                     for b in record['buffers'] if 'before' in b)
    merged = []
    for start, end in regions:
        if merged and start <= merged[-1][1]:
            merged[-1][1] = max(end, merged[-1][1])
        else:
            merged.append([start, end])
    buffers = {}
    for i, (start, end) in enumerate(merged):
        raw = bytearray(end - start)
        for b in record['buffers']:
            addr = int(b['address'], 0)
            if 'before' in b and start <= addr and addr + b['size'] <= end:
                raw[addr-start:addr-start+b['size']] = checked_blob(root, b, 'before')
        buffers[f'b{i}'] = {'size': end-start, 'hex': raw.hex()}
    args = []
    for arg in record['args']:
        n = int.from_bytes(bytes.fromhex(arg['bits_le']), 'little')
        if arg['type'] == 'ptr' and n:
            match = next((i for i, (s, e) in enumerate(merged) if s <= n <= e), None)
            if match is None:
                raise ValueError('unrelocated pointer; supply complete buffer descriptors')
            args.append({'type': 'ptr', 'buffer': f'b{match}', 'offset': n-merged[match][0]})
        else:
            args.append({'type': arg['type'], 'bits': hex(n)})
    return {'schema_version': 1, 'module': record['module'], 'buffers': buffers,
            'calls': [{'rva': record['rva'], 'args': args, 'return': record['return']['type']}]}, merged


def returned_spec(record, spec, regions, bridge, bridge_rva):
    """Lower a pointer return through a witness-callable shim with a bounded copy."""
    import struct
    snapshots = [b for b in record['buffers'] if b['descriptor'].get('returned')]
    if len(snapshots) > 1:
        raise ValueError('one returned-buffer descriptor is supported')
    size = snapshots[0]['size'] if snapshots else 0
    slots = bytearray(32 * 8)
    relocations = []
    for i, arg in enumerate(spec['calls'][0]['args']):
        if 'buffer' in arg:
            relocations.append({'offset': i*8, 'buffer': arg['buffer'], 'addend': arg.get('offset', 0)})
        else:
            struct.pack_into('<Q', slots, i*8, int(arg['bits'], 0))
    value = int.from_bytes(bytes.fromhex(record['return']['bits_le']), 'little')
    match = next((i for i, (s, e) in enumerate(regions) if s <= value <= e), None)
    mode = 0 if value == 0 else 2 if match is not None else 1
    if mode == 1 and not snapshots:
        raise ValueError('non-null unowned pointer return requires returned-buffer descriptor')
    meta = {'size': 32, 'hex': struct.pack('<QQQQ', 0, 0, 0, mode).hex()}
    if mode == 2:
        meta['pointers'] = [{'offset': 16, 'buffer': f'b{match}', 'addend': value-regions[match][0]}]
    buffers = spec['buffers']
    wide = (record['module']+'\0').encode('utf-16-le')
    buffers.update(_module={'size': len(wide), 'hex': wide.hex()},
                   _slots={'size': 256, 'hex': slots.hex(), 'pointers': relocations},
                   _returned={'size': size}, _meta=meta)
    spec.update(module=str(bridge), calls=[{'rva': hex(bridge_rva), 'return': 'i32', 'args': [
        {'type': 'ptr', 'buffer': '_module'}, {'type': 'u64', 'value': record['rva']},
        {'type': 'ptr', 'buffer': '_slots'}, {'type': 'ptr', 'buffer': '_returned'},
        {'type': 'u64', 'value': size}, {'type': 'ptr', 'buffer': '_meta'}]}])
    return spec, 'null' if mode == 0 else f'b{match}+{value-regions[match][0]}' if mode == 2 else 'nonnull'
