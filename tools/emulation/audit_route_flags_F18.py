#!/usr/bin/env python3
"""Read original PE/Mac PiPL resources and execute all ten GLOBAL_SETUPs.

Writes only the requested report and worktree ticket scratch. No AE launch,
installation, reference-worker rebuild, source-included Mac substitute, or render.
"""
from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import asdict
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import struct
import subprocess

import pefile
from unicorn.x86_const import UC_X86_REG_RIP, UC_X86_REG_RSP
from aex_loader import AexLoader, RETURN_TRAMPOLINE
from aex_witness import leaf_check

ROOT = Path(__file__).resolve().parents[2]
MAIN = Path('/Users/onmk/Documents/Projects/Personal/OLM as')
PLUGINS = ('ColorKeep', 'OLMBlur', 'OLMColorKey', 'OLMDirectionalBlur',
           'OLMDistanceGradation', 'OLMKiraKira', 'OLMRadialBlur',
           'OLMSmoother', 'OLMSmoother2', 'OLMToonDilate')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def import_summary(calls):
    # Smoother2's setup alone calls pow 19,561 times. Preserve identity/counts,
    # not a multi-megabyte per-call argument transcript in the committed report.
    return {'count': len(calls),
            'counts_by_import': dict(sorted(Counter(f'{c["dll"]}!{c["name"]}' for c in calls).items())),
            'transcript_sha256': hashlib.sha256(json.dumps(calls, sort_keys=True).encode()).hexdigest()}


def abi_control(main):
    """Existing import-free transparent prepass exercises Win64 stack args 5/6."""
    path = main/'plugins_2025/OLMDirectionalBlur.aex'
    loader = AexLoader(str(path), verbose=False, fast=True)
    source, destination, denominator, valid = [loader.host_alloc(16) for _ in range(4)]
    loader.write_bytes(source, bytes(16))
    for ptr in (destination, denominator, valid):
        loader.write_bytes(ptr, b'\xa5'*16)
    leaf_check(loader, 0x180001000,
               [0, 0, source, destination, denominator, valid, 0, 0, 0, 0, 1, 0])
    assert loader.uc.reg_read(UC_X86_REG_RIP) == RETURN_TRAMPOLINE
    assert not loader.import_log
    assert loader.read_bytes(destination, 16) == bytes(16)
    for ptr in (denominator, valid):
        assert loader.read_bytes(ptr, 16) == bytes(4)+b'\xa5'*12
    return {'aex_sha256': sha(path), 'entry': '0x180001000', 'passed': True,
            'destination_bytes_checked': 16, 'stack_argument_buffers_checked': 2}


def pipl(blob, windows):
    """Parse property boundaries, not byte-search for apparent flag constants."""
    order, pos = ('<', 2) if windows else ('>', 0)
    if windows:
        assert blob[:2] == b'\x01\x00', 'PE PiPL resource wrapper'
    version, count = struct.unpack_from(order + 'II', blob, pos)
    assert version == 0 and 0 < count < 100
    pos += 8
    props = []
    for _ in range(count):
        vendor, key = blob[pos:pos+4], blob[pos+4:pos+8]
        if windows:
            vendor, key = vendor[::-1], key[::-1]
        ident, size = struct.unpack_from(order + 'II', blob, pos+8)
        assert vendor == b'8BIM' and ident == 0
        start = pos+16
        value = blob[start:start+size]
        assert len(value) == size
        props.append({'key': key.decode('ascii'), 'offset': start, 'hex': value.hex()})
        pos = start + ((size+3)//4)*4
    assert pos == len(blob), (pos, len(blob))
    flags = {}
    for key, field in [('eGLO', 'out_flags'), ('eGL2', 'out_flags2')]:
        values = [x for x in props if x['key'] == key]
        assert len(values) == 1
        raw = bytes.fromhex(values[0]['hex'])
        assert len(raw) == 4
        flags[field] = struct.unpack(order+'I', raw)[0]
    return {'sha256': hashlib.sha256(blob).hexdigest(), 'raw_hex': blob.hex(),
            'properties': props, **flags}


def pe_pipls(pe):
    result = []
    for typ in pe.DIRECTORY_ENTRY_RESOURCE.entries:
        if str(typ.name).upper() != 'PIPL':
            continue
        for ident in typ.directory.entries:
            for lang in ident.directory.entries:
                data = lang.data.struct
                result.append({'id': ident.id, 'language': lang.id,
                               **pipl(pe.get_data(data.OffsetToData, data.Size), True)})
    assert result
    return result


def mac_pipls(path):
    """Read classic resource-file data/map/type/reference tables from .rsrc."""
    blob = path.read_bytes()
    data, resource_map, _, _ = struct.unpack_from('>4I', blob)
    type_list = resource_map + struct.unpack_from('>H', blob, resource_map+24)[0]
    count = struct.unpack_from('>H', blob, type_list)[0]+1
    result = []
    for i in range(count):
        offset = type_list+2+i*8
        typ, n, refs = struct.unpack_from('>4sHH', blob, offset)
        if typ != b'PiPL':
            continue
        for j in range(n+1):
            ref = type_list+refs+j*12
            ident = struct.unpack_from('>h', blob, ref)[0]
            start = data+int.from_bytes(blob[ref+5:ref+8], 'big')
            size = struct.unpack_from('>I', blob, start)[0]
            result.append({'id': ident, **pipl(blob[start+4:start+4+size], False)})
    assert result
    return result


def original_setup(path, entry, fill):
    loader = AexLoader(str(path), verbose=False, fast=True)
    loader.register_libm_impls()
    import_errors = []
    for name, implementation in list(loader.import_impls.items()):
        def checked(uc, args, name=name, implementation=implementation):
            try:
                return implementation(uc, args)
            except Exception as error:
                import_errors.append(f'{name}: {error}')
                raise
        loader.import_impls[name] = checked
    acquired, released, registrations, allocations, memories = [], [], [], {}, {}
    def q(addr, val):
        loader.write_bytes(addr, struct.pack('<Q', val))
    def cb(name, fn):
        return loader.install_callback(name, fn)
    def cstr(addr):
        return loader.read_bytes(addr, 128).split(b'\0', 1)[0].decode('ascii')
    def register(current, args):
        registrations.append(cstr(args[1]))
        current.write_bytes(args[2], struct.pack('<i', 42))
        return 0
    def new(current, args):
        size = max(1, args[0])
        ptr = current.host_alloc(size)
        current.write_bytes(ptr, bytes(size))
        allocations[ptr] = size
        return ptr
    zero = lambda _l, _a: 0
    handles = loader.host_alloc(48)
    loader.write_bytes(handles, struct.pack('<6Q', cb('new', new),
        cb('lock', lambda _l, a: a[0]), cb('unlock', zero), cb('dispose', zero),
        cb('size', lambda _l, a: allocations[a[0]]), cb('resize', zero)))
    utility = loader.host_alloc(0x60)
    loader.write_bytes(utility, bytes(0x60))
    # Frozen utility v3/version7 uses slot7; later versions use slot9.
    q(utility+0x38, cb('register_v3', register))
    q(utility+0x48, cb('register_later', register))
    def new_memory(current, args):
        # AEGP_NewMemHandle's fifth Win64 argument follows return + shadow space.
        out_pointer = struct.unpack('<Q', current.read_bytes(
            current.uc.reg_read(UC_X86_REG_RSP)+0x28, 8))[0]
        ptr = current.host_alloc(args[2])
        current.write_bytes(ptr, bytes(args[2]))
        handle = current.host_alloc(8)
        q(handle, ptr)
        memories[handle] = ptr
        q(out_pointer, handle)
        return 0
    def lock_memory(_current, args):
        q(args[1], memories[args[0]])
        return 0
    memory_suite = loader.host_alloc(32)
    loader.write_bytes(memory_suite, struct.pack('<4Q', cb('new_memory', new_memory),
        cb('free_memory', zero), cb('lock_memory', lock_memory), cb('unlock_memory', zero)))
    def acquire(current, args):
        name, version = cstr(args[0]), args[1]
        acquired.append([name, version])
        suites = {('AEGP Utility Suite', 7): utility, ('AEGP Utility Suite', 13): utility,
                  ('PF Handle Suite', 2): handles, ('AEGP Memory Suite', 1): memory_suite}
        assert (name, version) in suites, (name, version)
        q(args[2], suites[name, version])
        return 0
    def release(_current, args):
        released.append([cstr(args[0]), args[1]])
        return 0
    basic = loader.host_alloc(16)
    q(basic, cb('acquire', acquire))
    q(basic+8, cb('release', release))
    inp, out = loader.host_alloc(0x220), loader.host_alloc(0x300)
    loader.write_bytes(inp, bytes(0x220))
    loader.write_bytes(out, bytes([fill])*0x300)
    q(inp+0x180, basic)
    q(inp+0xb8, 0x1234)
    result = loader.call_function(entry, [1, inp, out, 0, 0, 0], max_instructions=3_000_000)
    assert loader.uc.reg_read(UC_X86_REG_RIP) == RETURN_TRAMPOLINE, 'instruction budget exhausted'
    assert result['rax'] == 0
    assert not import_errors, import_errors
    assert all(call.name in loader.import_impls for call in loader.import_log), 'unimplemented import'
    values = [struct.unpack('<I', loader.read_bytes(out+off, 4))[0] for off in (0, 0x60, 0x190)]
    return {'return_code': result['rax'], 'my_version': values[0], 'out_flags': values[1],
            'out_flags2': values[2], 'initial_fill': fill, 'suite_acquisitions': acquired,
            'suite_releases': released, 'registrations': registrations,
            'import_policy': 'registered loader memory/libm callbacks; no unimplemented imports or callback errors',
            'imports': import_summary([asdict(call) for call in loader.import_log])}


def run(command, log, env):
    with log.open('w') as stream:
        result = subprocess.run(list(map(str, command)), cwd=ROOT, env=env,
                                stdout=stream, stderr=subprocess.STDOUT)
    if result.returncode:
        raise RuntimeError(f'command failed ({result.returncode}); see {log}')


def flags(row):
    return [row['out_flags'], row['out_flags2']]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--main', type=Path, default=MAIN)
    parser.add_argument('--scratch', type=Path, default=ROOT/'orchestra/state/F18-route-target-per-plugin')
    parser.add_argument('--report', type=Path, required=True)
    parser.add_argument('--keep-builds', action='store_true')
    parser.add_argument('--require-agreement', action='store_true',
                        help='Exit nonzero unless all original/Mac resource/runtime flags agree')
    args = parser.parse_args()
    scratch = args.scratch.resolve()
    assert scratch.is_relative_to(ROOT/'orchestra/state/F18-route-target-per-plugin')
    scratch.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ, TMPDIR=str(scratch), TMP=str(scratch), TEMP=str(scratch),
               PYTHONDONTWRITEBYTECODE='1')
    os.environ.update({k: env[k] for k in ('TMPDIR', 'TMP', 'TEMP')})
    run(['bash', 'scripts/setup_ae_sdk_links.sh'], scratch/'sdk.log', env)
    header = ROOT/'Headers/AE_Effect.h'
    definitions = {name: 1 << int(bit) for name, bit in re.findall(
        r'(PF_OutFlag2?_\w+)\s*=\s*1L\s*<<\s*(\d+)', header.read_text())}
    host = scratch/'route_flags_mac'
    host_source = ROOT/'tools/emulation/route_flags_mac_F18.cpp'
    run(['xcrun', 'clang++', '-std=c++17', '-arch', 'arm64', '-arch', 'x86_64',
         '-D__MACH__', '-IHeaders', '-IHeaders/SP', host_source, '-o', host], scratch/'host-build.log', env)
    report = {'schema': 'olm.route-flags.F18/1', 'native_ae_trace': False,
              'abi_control': abi_control(args.main),
              'source_revision': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
              'sdk_header_sha256': sha(header), 'loader_sha256': sha(ROOT/'tools/emulation/aex_loader.py'),
              'harness_sha256': sha(host_source), 'flag_definitions': definitions, 'plugins': []}
    for plugin in PLUGINS:
        aex_name = 'DistanceGradation' if plugin == 'OLMDistanceGradation' else plugin
        aex = args.main/'plugins_2025'/f'{aex_name}.aex'
        pe = pefile.PE(str(aex))
        resources = pe_pipls(pe)
        names = {bytes.fromhex(prop['hex']).split(b'\0', 1)[0]
                 for resource in resources for prop in resource['properties'] if prop['key'] == '8664'}
        assert len(names) == 1, names
        entries = [x for x in pe.DIRECTORY_ENTRY_EXPORT.symbols if x.name in names]
        assert len(entries) == 1
        entry = pe.OPTIONAL_HEADER.ImageBase+entries[0].address
        original = [original_setup(aex, entry, fill) for fill in (0, 0xa5)]
        build = scratch/'build'/plugin
        command = ['xcodebuild', '-project', f'mac/{plugin}/Mac/{plugin}.xcodeproj',
                   '-configuration', 'Debug', 'ARCHS=arm64 x86_64', 'ONLY_ACTIVE_ARCH=NO',
                   'GCC_OPTIMIZATION_LEVEL=2', f'OBJROOT={build}/obj', f'SYMROOT={build}/sym',
                   f'SHARED_PRECOMPS_DIR={build}/precomp', f'CONFIGURATION_BUILD_DIR={build}/products', 'build']
        run(command, scratch/f'build-{plugin}.log', env)
        bundle = build/f'products/{plugin}.plugin/Contents'
        binary = bundle/f'MacOS/{plugin}'
        rsrc = bundle/f'Resources/{plugin}.rsrc'
        mac_resources = mac_pipls(rsrc)
        mac = {}
        for arch in ('arm64', 'x86_64'):
            rows = []
            for fill in (0, 0xa5):
                result = subprocess.run(['arch', '-'+arch, str(host), str(binary), str(fill)],
                                        env=env, capture_output=True, text=True, check=True)
                rows.append({**json.loads(result.stdout), 'initial_fill': fill,
                             'suite_log': result.stderr.splitlines()})
            mac[arch] = rows
        observations = resources + original + mac_resources + [x for rows in mac.values() for x in rows]
        agree = all(flags(x) == flags(original[0]) for x in observations)
        decoded = [name for name, bit in definitions.items()
                   if original[0]['out_flags2' if name.startswith('PF_OutFlag2_') else 'out_flags'] & bit]
        smart = bool(original[0]['out_flags2'] & definitions['PF_OutFlag2_SUPPORTS_SMART_RENDER'])
        row = {'plugin': plugin, 'aex_path': str(aex), 'aex_sha256': sha(aex), 'entry': hex(entry),
               'original_pipl': resources, 'original_global_setup': original,
               'mac_source_sha256': sha(ROOT/(f'mac/{plugin}/Mac/{plugin}_port.cpp'
                                             if plugin == 'OLMSmoother' else f'mac/{plugin}/{plugin}.cpp')),
               'mac_pipl_source_sha256': sha(ROOT/f'mac/{plugin}/{plugin}PiPL.r'),
               'mac_binary_sha256': sha(binary), 'mac_rsrc_sha256': sha(rsrc),
               'mac_pipl': mac_resources, 'mac_global_setup': mac,
               'build_command': list(map(str, command)), 'all_flags_agree': agree,
               'decoded_original_flags': decoded, 'original_smart': smart,
               'original_classic_used_by_ae': not smart, 'target_route': 'smart' if smart else 'classic'}
        report['plugins'].append(row)
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, indent=2, sort_keys=True)+'\n')
        print(f'{plugin}: {original[0]["out_flags"]:#010x}/{original[0]["out_flags2"]:#010x} '
              f'flags_agree={agree} target={row["target_route"]}', flush=True)
        if not args.keep_builds:
            shutil.rmtree(build)
    report['summary'] = {'plugin_count': len(report['plugins']),
                         'flags_agree': sum(x['all_flags_agree'] for x in report['plugins']),
                         'smart': sum(x['original_smart'] for x in report['plugins'])}
    args.report.write_text(json.dumps(report, indent=2, sort_keys=True)+'\n')
    print(json.dumps(report['summary']), flush=True)
    if args.require_agreement:
        assert report['summary']['flags_agree'] == len(PLUGINS), 'capability disagreement'


if __name__ == '__main__':
    main()
