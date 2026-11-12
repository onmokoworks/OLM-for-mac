"""Windows AMD64 debugger. No attach API: only DEBUG_PROCESS descendants.

CONTEXT/DEBUG_EVENT offsets are the Windows SDK AMD64 layouts. A breakpoint
is removed for precisely one instruction while every other thread is suspended.
No target-side logging, allocation, callbacks, or trampoline code is injected.
"""
from __future__ import annotations
import ctypes as c
from ctypes import wintypes as w
import struct
import time


class Context:
    def __init__(self):
        self.storage = c.create_string_buffer(1232 + 15)
        self.address = (c.addressof(self.storage) + 15) & ~15
        self.raw = (c.c_ubyte * 1232).from_address(self.address)
        self.put(48, 0x10000b, 4)  # AMD64 CONTROL | INTEGER | FLOATING_POINT

    def get(self, offset, size=8):
        return int.from_bytes(bytes(self.raw[offset:offset+size]), 'little')

    def put(self, offset, value, size=8):
        self.raw[offset:offset+size] = value.to_bytes(size, 'little')

    def bytes(self, offset, size):
        return bytes(self.raw[offset:offset+size])


class Debugger:
    def __init__(self, module, functions, on_entry, on_return, on_module):
        self.k = c.WinDLL('kernel32', use_last_error=True)
        self.nt = c.WinDLL('ntdll')
        self.nt.NtQueryInformationThread.argtypes = [w.HANDLE, c.c_int, c.c_void_p, w.DWORD, c.c_void_p]
        self.nt.NtQueryInformationThread.restype = c.c_long
        signatures = {
            'WaitForDebugEvent': ([c.c_void_p, w.DWORD], w.BOOL),
            'ContinueDebugEvent': ([w.DWORD, w.DWORD, w.DWORD], w.BOOL),
            'GetThreadContext': ([w.HANDLE, c.c_void_p], w.BOOL),
            'SetThreadContext': ([w.HANDLE, c.c_void_p], w.BOOL),
            'ReadProcessMemory': ([w.HANDLE, c.c_void_p, c.c_void_p, c.c_size_t, c.c_void_p], w.BOOL),
            'WriteProcessMemory': ([w.HANDLE, c.c_void_p, c.c_void_p, c.c_size_t, c.c_void_p], w.BOOL),
            'FlushInstructionCache': ([w.HANDLE, c.c_void_p, c.c_size_t], w.BOOL),
            'VirtualProtectEx': ([w.HANDLE, c.c_void_p, c.c_size_t, w.DWORD, c.c_void_p], w.BOOL),
            'SuspendThread': ([w.HANDLE], w.DWORD), 'ResumeThread': ([w.HANDLE], w.DWORD),
            'CloseHandle': ([w.HANDLE], w.BOOL),
            'WaitForSingleObject': ([w.HANDLE, w.DWORD], w.DWORD),
            'GetExitCodeThread': ([w.HANDLE, c.c_void_p], w.BOOL),
            'DuplicateHandle': ([w.HANDLE, w.HANDLE, w.HANDLE, c.c_void_p, w.DWORD, w.BOOL, w.DWORD], w.BOOL),
            'GetFinalPathNameByHandleW': ([w.HANDLE, w.LPWSTR, w.DWORD, w.DWORD], w.DWORD),
        }
        for name, (args, result) in signatures.items():
            getattr(self.k, name).argtypes = args
            getattr(self.k, name).restype = result
        self.module = str(module).lower().replace('\\', '/')
        self.functions = functions
        self.on_entry, self.on_return, self.on_module = on_entry, on_return, on_module
        self.processes, self.exits, self.modules = {}, {}, []
        self.pending = None

    def retain_wait_handle(self, process):
        # ContinueDebugEvent closes CREATE_PROCESS's handle. Popen may own that
        # very handle, so retain a separate one for its wait/poll/destructor.
        duplicate = w.HANDLE()
        self.check(self.k.DuplicateHandle(-1, int(process._handle), -1, c.byref(duplicate), 0, False, 2))
        process._handle.Detach()
        import subprocess
        process._handle = subprocess.Handle(duplicate.value)

    @staticmethod
    def check(ok):
        if not ok:
            raise c.WinError(c.get_last_error())

    def read(self, p, address, size):
        if not size:
            return b''
        buf, done = c.create_string_buffer(size), c.c_size_t()
        self.check(self.k.ReadProcessMemory(p['handle'], address, buf, size, c.byref(done)))
        if done.value != size:
            raise RuntimeError('short remote read')
        return buf.raw

    def write(self, p, address, data):
        old, done = w.DWORD(), c.c_size_t()
        self.check(self.k.VirtualProtectEx(p['handle'], address, len(data), 0x40, c.byref(old)))
        try:
            self.check(self.k.WriteProcessMemory(p['handle'], address, data, len(data), c.byref(done)))
            if done.value != len(data):
                raise RuntimeError('short remote write')
            self.check(self.k.FlushInstructionCache(p['handle'], address, len(data)))
        finally:
            ignored = w.DWORD()
            self.check(self.k.VirtualProtectEx(p['handle'], address, len(data), old, c.byref(ignored)))

    def bp(self, p, address, function=None):
        if address not in p['bps']:
            original = self.read(p, address, 1)
            if original == b'\xcc':
                raise ValueError('target already contains INT3')
            p['bps'][address] = {'original': original, 'function': function, 'returns': []}
            self.write(p, address, b'\xcc')
        elif function is not None:
            if p['bps'][address]['function'] not in (None, function):
                raise ValueError('multiple incompatible signatures at one address')
            p['bps'][address]['function'] = function
        return p['bps'][address]

    def context(self, p, tid):
        ctx = Context()
        self.check(self.k.GetThreadContext(p['threads'][tid], ctx.address))
        return ctx

    def path(self, handle):
        if not handle:
            return ''
        buf = c.create_unicode_buffer(32768)
        n = self.k.GetFinalPathNameByHandleW(handle, buf, len(buf), 0)
        return buf.value.removeprefix('\\\\?\\') if 0 < n < len(buf) else ''

    def poll(self, milliseconds=100, cleanup=False):
        event = c.create_string_buffer(176)
        if not self.k.WaitForDebugEvent(event, milliseconds):
            if c.get_last_error() == 121:
                return False
            raise c.WinError(c.get_last_error())
        code, pid, tid = struct.unpack_from('<III', event)
        q = lambda offset: struct.unpack_from('<Q', event, offset)[0]
        d = lambda offset: struct.unpack_from('<I', event, offset)[0]
        self.pending = (pid, tid)
        status = 0x10002  # DBG_CONTINUE
        try:
            if code == 3:  # CREATE_PROCESS
                self.processes[pid] = {'pid': pid, 'handle': q(24), 'threads': {tid: q(32)},
                    'bps': {}, 'step': None, 'base': None, 'image': self.path(q(16)), 'loaded': []}
                if q(16):
                    self.k.CloseHandle(q(16))
            p = self.processes[pid]
            if code == 2:
                p['threads'][tid] = q(16)
                if p['step']:
                    if self.k.SuspendThread(q(16)) == 0xffffffff:
                        raise c.WinError(c.get_last_error())
                    p['step']['suspended'].append(tid)
            elif code == 4:
                p['threads'].pop(tid, None)  # OS closes debug thread handle at continue
            elif code == 5:
                self.exits[pid] = {'image': p['image'], 'exit_code': d(16)}
                del self.processes[pid]
            elif code == 6:
                path, base = self.path(q(16)), q(24)
                if q(16):
                    self.k.CloseHandle(q(16))
                p['loaded'].append({'path': path, 'base': base})
                if path.lower().replace('\\', '/') == self.module and not cleanup:
                    p['base'] = base
                    self.modules.append({'pid': pid, 'path': path, 'base': hex(base)})
                    self.on_module(self, p)
                    for f in self.functions:
                        self.bp(p, base + int(f['rva'], 0), f)
            elif code == 7 and p['base'] == q(16) and not cleanup:
                if any(b['returns'] for b in p['bps'].values()):
                    raise RuntimeError('module unloaded with calls in flight')
                # The image is already unmapped. Restore only provider breakpoints.
                for address, bp in list(p['bps'].items()):
                    if bp['function'] and 'import' in bp['function']:
                        self.write(p, address, bp['original'])
                p['bps'].clear()
                p['base'] = None
                p['imports_ready'] = False
            elif code == 1:
                exception, address = d(16), q(32)
                if cleanup:
                    status = 0x80010001
                elif exception == 0x80000003 and address in p['bps']:
                    if p['step']:
                        raise RuntimeError('unexpected nested breakpoint while stepping')
                    bp, ctx = p['bps'][address], self.context(p, tid)
                    rsp = ctx.get(152)
                    matches = [r for r in bp['returns'] if r['tid'] == tid and r['rsp'] + 8 == rsp]
                    for ret in matches:
                        self.on_return(self, p, ctx, ret['record'])
                        bp['returns'].remove(ret)
                    if bp['function']:
                        record = self.on_entry(self, p, tid, ctx, bp['function'])
                        if record is not None:
                            caller = int.from_bytes(self.read(p, rsp, 8), 'little')
                            self.bp(p, caller)['returns'].append({'tid': tid, 'rsp': rsp, 'record': record})
                    self.write(p, address, bp['original'])
                    ctx.put(248, address)
                    ctx.put(68, ctx.get(68, 4) | 0x100, 4)
                    self.check(self.k.SetThreadContext(p['threads'][tid], ctx.address))
                    suspended = []
                    for other, handle in p['threads'].items():
                        if other != tid:
                            if self.k.SuspendThread(handle) == 0xffffffff:
                                # Thread termination can precede delivery of its
                                # queued EXIT_THREAD event. It cannot hit a hook.
                                exit_code = w.DWORD()
                                self.check(self.k.GetExitCodeThread(handle, c.byref(exit_code)))
                                if exit_code.value != 259 or self.k.WaitForSingleObject(handle, 0) == 0:
                                    continue
                                # ExitThread can be waiting for its debugger event:
                                # exit status is still STILL_ACTIVE and the handle
                                # is not signaled, but the thread cannot run again.
                                terminated = w.DWORD()
                                status_nt = self.nt.NtQueryInformationThread(handle, 20, c.byref(terminated), 4, None)
                                if status_nt == 0 and terminated.value:
                                    continue
                                raise RuntimeError(f'cannot suspend thread {other}, exit={exit_code.value}, error={c.get_last_error()}')
                            suspended.append(other)
                    p['step'] = {'tid': tid, 'address': address, 'suspended': suspended}
                elif exception == 0x80000004 and p['step'] and p['step']['tid'] == tid:
                    step = p['step']
                    bp = p['bps'][step['address']]
                    if bp['function'] or bp['returns']:
                        self.write(p, step['address'], b'\xcc')
                    else:
                        del p['bps'][step['address']]
                    ctx = self.context(p, tid)
                    ctx.put(68, ctx.get(68, 4) & ~0x100, 4)
                    self.check(self.k.SetThreadContext(p['threads'][tid], ctx.address))
                    for other in step['suspended']:
                        if other in p['threads'] and self.k.ResumeThread(p['threads'][other]) == 0xffffffff:
                            raise c.WinError(c.get_last_error())
                    p['step'] = None
                elif exception == 0x80000003 and not p.get('initial_break'):
                    p['initial_break'] = True
                else:
                    status = 0x80010001  # Let debuggee handle its own exceptions.
                    if not d(168):
                        raise RuntimeError(f'second-chance exception {exception:#x} at {address:#x} pid={pid}')
        finally:
            self.check(self.k.ContinueDebugEvent(pid, tid, status))
            self.pending = None
        return True

    def drain(self, root_pid=None, timeout=10):
        deadline = time.monotonic() + timeout
        while (self.processes or (root_pid and root_pid not in self.exits)) and time.monotonic() < deadline:
            self.poll(cleanup=True)
        if self.processes or (root_pid and root_pid not in self.exits):
            raise RuntimeError('owned debug processes failed to exit')
