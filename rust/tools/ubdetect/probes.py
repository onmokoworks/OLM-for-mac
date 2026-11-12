"""Bounded memory differentials using record's owned Windows debugger.

Profiles are reviewed memory-layout contracts, not automatic UB proofs. Module
hash and instruction bytes must match. A changed legitimate input is not UB.
"""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import struct
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
for sibling in ('oracle', 'record', 'witness'):
    sys.path.insert(0, str(HERE.parent / sibling))
import olm_oracle as oracle
import witness
from win_debug import Debugger

REGS = dict(zip(('rax','rcx','rdx','rbx','rsp','rbp','rsi','rdi',
                 'r8','r9','r10','r11','r12','r13','r14','r15'), range(120,248,8)))
MAX_BYTES = 16 * 1024 * 1024


def integer(x):
    return int(x, 0) if isinstance(x, str) else int(x)


def address(debug, p, ctx, expr):
    value = ctx.get(REGS[expr['reg']])
    for offset in expr.get('deref', []):
        value = int.from_bytes(debug.read(p, value + integer(offset), 8), 'little')
    return value + integer(expr.get('offset', 0))


def size_value(debug, p, ctx, expr):
    if isinstance(expr, int):
        value = expr
    elif 'mul' in expr:
        value = 1
        for part in expr['mul']:
            value *= size_value(debug,p,ctx,part)
    else:
        value = int.from_bytes(debug.read(p,address(debug,p,ctx,expr),4),'little',signed=True)
    if not 0 <= value <= MAX_BYTES:
        raise ValueError('invalid/oversized span length')
    return value


def validate(profile, module, route):
    if profile['schema_version'] != 1 or oracle.sha256(module) != profile['module_sha256']:
        raise ValueError('profile schema/module hash mismatch')
    if route not in profile['routes']:
        raise ValueError('profile does not cover this route')
    import pefile
    pe = pefile.PE(str(module))
    try:
        for h in profile['hooks']:
            expected = bytes.fromhex(h['instruction'])
            if not expected or pe.get_data(integer(h['rva']), len(expected)) != expected:
                raise ValueError('profile instruction mismatch: ' + h['name'])
            if h['kind'] not in ('span', 'oob_read', 'allocation', 'world_padding'):
                raise ValueError('unknown hook kind')
            if not h.get('basis'):
                raise ValueError('a memory ownership/undefinedness basis is required')
    finally:
        pe.close()


class RestoringDebugger(Debugger):
    """Restore the operand before record reinserts INT3 and resumes siblings.

    This deliberately uses record's rearm point, NOT a breakpoint at the next
    instruction (which would leave a race with other threads). No register,
    instruction operand or valid table element is replaced.
    """
    def write(self, p, addr, data):
        pending = p.get('ub_restore')
        if pending and addr == pending['site'] and data == b'\xcc' and p.get('step'):
            super().write(p, pending['address'], pending['before'])
            pending['event']['restored'] = True
            del p['ub_restore']
        super().write(p, addr, data)


class Probe:
    def __init__(self, profile, pattern, max_events=10000):
        self.profile, self.pattern = profile, pattern
        self.events, self.counts = [], {}
        self.max_events, self.bytes_written = max_events, 0

    def loaded(self, debug, p):
        pass

    def fill(self, debug, p, addr, size, event, transient=False):
        if not 0 <= size <= MAX_BYTES or self.bytes_written + size > MAX_BYTES:
            raise ValueError('poison byte budget exceeded')
        before = debug.read(p, addr, size)
        event.update(address=hex(addr), size=size,
                     before_sha256=hashlib.sha256(before).hexdigest(),
                     before_prefix=before[:32].hex(), mutated=self.pattern is not None)
        if self.pattern is not None and size:
            payload = (self.pattern * ((size + len(self.pattern)-1)//len(self.pattern)))[:size]
            debug.write(p, addr, payload)
            self.bytes_written += size
            event['after_sha256'] = hashlib.sha256(payload).hexdigest()
            if transient:
                if p.get('ub_restore'):
                    raise RuntimeError('overlapping transient poison')
                p['ub_restore'] = dict(site=p['base']+integer(event['rva']), address=addr,
                                       before=before, event=event)
                event['restored'] = False

    def entry(self, debug, p, tid, ctx, h):
        self.counts[h['name']] = self.counts.get(h['name'], 0) + 1
        if len(self.events) >= self.max_events:
            raise ValueError('probe event budget exceeded; evidence incomplete')
        ev = dict(name=h['name'], kind=h['kind'], rva=h['rva'], instruction=h['instruction'],
                  pid=p['pid'], tid=tid, basis=h['basis'])
        if h['kind'] == 'oob_read':
            base = address(debug, p, ctx, h['table'])
            raw = ctx.get(REGS[h['index_reg']])
            index = raw - (1 << 64) if raw & (1 << 63) else raw
            index += h.get('index_add', 0)
            count = h['count']
            ev.update(table_base=hex(base), index=index, count=count,
                      invalid=not 0 <= index < count, effective_address=hex(base + index*4))
            if ev['invalid']:
                self.fill(debug, p, base + index*4, 4, ev, transient=True)
        elif h['kind'] == 'span':
            self.fill(debug, p, address(debug, p, ctx, h['address']), size_value(debug,p,ctx,h['size']), ev)
        elif h['kind'] == 'world_padding':
            world = address(debug, p, ctx, h['address'])
            # Explicit ABI offsets; no guessed world layout.
            layout = h['layout']
            def field(key, n=4):
                return int.from_bytes(debug.read(p, world+integer(layout[key]), n), 'little', signed=n==4)
            data, stride, width, height = field('data',8), field('rowbytes'), field('width'), field('height')
            active = width*h['pixel_bytes']
            if not (0 <= width <= 8192 and 0 <= height <= 8192 and active <= stride <= MAX_BYTES):
                raise ValueError('world layout outside budget')
            ev.update(rows=[], width=width, height=height, rowbytes=stride)
            for y in range(height):
                row = {'y': y}
                self.fill(debug,p,data+y*stride+active,stride-active,row)
                ev['rows'].append(row)
        elif h['kind'] == 'allocation':
            # Hook a proven allocator entry, then poison only the returned fresh
            # allocation. Realloc/calloc are intentionally not inferred.
            size = ctx.get(REGS[h['size_reg']]) * h.get('size_scale', 1)
            if not 0 <= size <= MAX_BYTES:
                raise ValueError('allocation exceeds budget')
            ev.update(size=size, status='pending')
            self.events.append(ev)
            return ev
        self.events.append(ev)
        return None

    def returned(self, debug, p, ctx, ev):
        ptr = ctx.get(REGS['rax'])
        if ptr:
            self.fill(debug,p,ptr,ev['size'],ev)
        ev.update(status='complete', null=not bool(ptr))


def run(command, module, profile, out, timeout, pattern=None):
    """One real render; never attaches to an existing process."""
    out.mkdir(parents=True, exist_ok=False)
    probe = Probe(profile, pattern)
    debug = RestoringDebugger(module, profile['hooks'], probe.entry, probe.returned, probe.loaded)
    job, process, cleanup = witness.WindowsJob(), None, False
    started, error = time.monotonic(), None
    result = {'command': [str(x) for x in command], 'pattern': pattern.hex() if pattern else None,
              'environment': oracle.frame_deadline_environment(timeout)}
    try:
        with (out/'stdout.txt').open('wb') as stdout, (out/'stderr.txt').open('wb') as stderr:
            process = subprocess.Popen([str(x) for x in command], stdout=stdout, stderr=stderr,
                stdin=subprocess.DEVNULL, creationflags=0x1|0x4|0x08000000,
                env={**os.environ, **result['environment']})
            result['pid'] = process.pid
            oracle.write_json(out/'process.json', result)
            debug.retain_wait_handle(process)
            job.attach_resume(process)
            while process.pid not in debug.exits:
                if time.monotonic()-started > timeout:
                    raise TimeoutError('debug render deadline')
                debug.poll()
    except BaseException as exc:
        error = repr(exc)
        if isinstance(exc, KeyboardInterrupt):
            result['cancelled'] = True
    finally:
        try:
            try:
                job.terminate()
                if process and process.pid not in debug.exits:
                    process.kill()
                debug.drain(process.pid if process else None)
            finally:
                cleanup = job.close()
        finally:
            if process:
                if process.poll() is None:
                    process.kill()
                process.wait(timeout=10)
            result.update(error=error, cleanup_verified=cleanup, processes=debug.exits,
                modules=debug.modules, events=probe.events, counts=probe.counts,
                elapsed_seconds=time.monotonic()-started,
                returncode=process.returncode if process else None)
            result['ok'] = (not error and result['returncode']==0 and cleanup and
                all(e.get('restored', True) and e.get('status')!='pending' for e in probe.events))
            oracle.write_json(out/'process.json',result)
    if result.get('cancelled'):
        raise KeyboardInterrupt
    return result
