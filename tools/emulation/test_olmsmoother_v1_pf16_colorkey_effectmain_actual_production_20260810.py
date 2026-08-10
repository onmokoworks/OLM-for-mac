#!/usr/bin/env python3
"""Actual exported PF16 Render session versus production EffectMain."""

import ctypes
import hashlib
import json
import struct
import subprocess
import tempfile
from pathlib import Path

from unicorn import UC_PROT_ALL
from unicorn.x86_const import UC_X86_REG_RSP
from aex_loader import AexLoader

ROOT = Path(__file__).resolve().parents[2]
AEX = ROOT / "plugins_2025/OLMSmoother.aex"
AEX_SHA = "6206f601b645dc915b78269ae403e5cbee642ac2812e320d85838ec72135fe82"
ENTRY = 0x18000A2C0
HARNESS = ROOT / "tools/emulation/olmsmoother_v1_pf16_colorkey_production_harness_20260810.cpp"
REPORT = ROOT / "refs/conformance/olmsmoother_v1_pf16_colorkey_effectmain_actual_production_20260810.json"
W, H, ROWBYTES = 5, 3, 48
KEY = (202, 187, 230)

ASM = r"""
.text
.globl iterate16_guest
iterate16_guest:
 pushq %rbx
 pushq %rbp
 pushq %rsi
 pushq %rdi
 pushq %r12
 pushq %r13
 pushq %r14
 pushq %r15
 subq $0x38, %rsp
 movl %edx, %r12d
 movl %r8d, %r13d
 movq %r9, %r14
 movq 0xa8(%rsp), %rsi
 movq 0xb0(%rsp), %r15
 movq 0xb8(%rsp), %rdi
 movq 0x18(%r14), %rbx
 movq 0x18(%rdi), %rbp
 movl 0x20(%r14), %eax
 movl %eax, 0x28(%rsp)
 movl 0x20(%rdi), %eax
 movl %eax, 0x2c(%rsp)
 movl 0x24(%r14), %eax
 movl %eax, 0x30(%rsp)
.Ly:
 cmpl %r13d, %r12d
 jge .Ldone
 movl $0, 0x34(%rsp)
.Lx:
 movl 0x34(%rsp), %eax
 cmpl 0x30(%rsp), %eax
 jge .Lnexty
 movslq %r12d, %rcx
 movslq 0x28(%rsp), %rdx
 imulq %rdx, %rcx
 leaq (%rbx,%rcx), %r9
 movslq 0x34(%rsp), %rax
 leaq (%r9,%rax,8), %r9
 movslq %r12d, %rcx
 movslq 0x2c(%rsp), %rdx
 imulq %rdx, %rcx
 leaq (%rbp,%rcx), %rdx
 leaq (%rdx,%rax,8), %rdx
 movq %rdx, 0x20(%rsp)
 movq %rsi, %rcx
 movl 0x34(%rsp), %edx
 movl %r12d, %r8d
 callq *%r15
 testl %eax, %eax
 jne .Lret
 incl 0x34(%rsp)
 jmp .Lx
.Lnexty:
 incl %r12d
 jmp .Ly
.Ldone:
 xorl %eax, %eax
.Lret:
 addq $0x38, %rsp
 popq %r15
 popq %r14
 popq %r13
 popq %r12
 popq %rdi
 popq %rsi
 popq %rbp
 popq %rbx
 retq
"""


def widen(v): return (v * 0x8000 + 0x80) // 0xFF
def u64(ld, p): return struct.unpack("<Q", ld.read_bytes(p, 8))[0]
def u32(ld, p): return struct.unpack("<I", ld.read_bytes(p, 4))[0]


def guest_code(directory):
    src = directory / "iterate.s"; obj = directory / "iterate.obj"
    src.write_text(ASM)
    subprocess.run(["clang", "-target", "x86_64-pc-windows-msvc", "-c", str(src), "-o", str(obj)], check=True)
    raw = obj.read_bytes()
    _machine, count, _time, sym, nsyms, opt, _flags = struct.unpack_from("<HHIIIHH", raw, 0)
    off = 20 + opt
    for index in range(count):
        sh = off + index * 40
        name = raw[sh:sh + 8].rstrip(b"\0")
        size, ptr = struct.unpack_from("<II", raw, sh + 16)
        if name == b".text": return raw[ptr:ptr + size]
    raise RuntimeError("COFF .text missing")


def make_world(ld, payload, fill, trace, temporary=False):
    data = ld.host_alloc(ROWBYTES * H, align=16)
    ld.write_bytes(data, payload if payload is not None else bytes([fill]) * (ROWBYTES * H))
    world = ld.host_alloc(0x80, align=16)
    ld.write_bytes(world, b"\0" * 0x80)
    ld.write_bytes(world + 0x10, struct.pack("<I", 1))
    ld.write_bytes(world + 0x18, struct.pack("<Qiii", data, ROWBYTES, W, H))
    ld.write_bytes(world + 0x2C, struct.pack("<H", 16))
    # Native PF_Rect order is top,left,bottom,right.
    ld.write_bytes(world + 0x30, struct.pack("<4i", 0, 0, H, W))
    if temporary: trace.append({"event": "new_world", "world": hex(world), "data": hex(data)})
    return world, data


def actual(payload):
    ld = AexLoader(str(AEX), verbose=False, fast=True)
    trace = []
    with tempfile.TemporaryDirectory(prefix="sm1-guest-iterate-") as td:
        code = guest_code(Path(td))
    guest = 0x83000000
    ld.uc.mem_map(guest, 0x1000, UC_PROT_ALL); ld.uc.mem_write(guest, code)
    iterate_suite = ld.host_alloc(8); ld.write_bytes(iterate_suite, struct.pack("<Q", guest))

    def acquire(loader, args):
        loader.write_bytes(args[2], struct.pack("<Q", iterate_suite)); trace.append({"event": "acquire_iterate16"}); return 0
    def release(loader, args): trace.append({"event": "release_suite"}); return 0
    sp = ld.host_alloc(16); ld.write_bytes(sp, struct.pack("<2Q", ld.install_callback("acquire", acquire), ld.install_callback("release", release)))

    temp = {}
    def copy(loader, args):
        src, dst = args[1], args[2]
        for y in range(min(u32(loader, src + 0x28), u32(loader, dst + 0x28))):
            n = min(u32(loader, src + 0x24), u32(loader, dst + 0x24)) * 8
            loader.write_bytes(u64(loader, dst + 0x18) + y * u32(loader, dst + 0x20), loader.read_bytes(u64(loader, src + 0x18) + y * u32(loader, src + 0x20), n))
        trace.append({"event": "copy", "src": hex(src), "dst": hex(dst)}); return 0
    def new_world(loader, args):
        rsp = loader.uc.reg_read(UC_X86_REG_RSP)
        outp = u64(loader, rsp + 0x28)
        world, data = make_world(loader, None, 0xC3, trace, True)
        loader.write_bytes(outp, loader.read_bytes(world, 0x80)); temp.update(world=outp, data=data)
        return 0
    def dispose(loader, args): trace.append({"event": "dispose_world"}); return 0
    utils = ld.host_alloc(0x90); ld.write_bytes(utils, b"\0" * 0x90)
    ld.write_bytes(utils + 0x40, struct.pack("<Q", ld.install_callback("copy", copy)))
    ld.write_bytes(utils + 0x70, struct.pack("<Q", ld.install_callback("new_world", new_world)))
    ld.write_bytes(utils + 0x78, struct.pack("<Q", ld.install_callback("dispose", dispose)))
    indata = ld.host_alloc(0x200); ld.write_bytes(indata, b"\0" * 0x200)
    ld.write_bytes(indata + 0xB0, struct.pack("<QQ", utils, 0x1234)); ld.write_bytes(indata + 0x180, struct.pack("<Q", sp))
    outdata = ld.host_alloc(0x200); ld.write_bytes(outdata, b"\0" * 0x200)
    output, output_data = make_world(ld, None, 0xA5, trace)
    params = []
    for _ in range(4):
        p = ld.host_alloc(0x200); ld.write_bytes(p, b"\0" * 0x200); params.append(p)
    input_world, input_data = make_world(ld, payload, 0, trace)
    ld.write_bytes(params[0] + 0x38, ld.read_bytes(input_world, 0x80))
    ld.write_bytes(params[1] + 0x38, struct.pack("<I", 1))
    ld.write_bytes(params[2] + 0x38, bytes((255, *KEY)))
    ld.write_bytes(params[3] + 0x38, struct.pack("<I", 6))
    parr = ld.host_alloc(32); ld.write_bytes(parr, struct.pack("<4Q", *params))
    for addr, label in ((0x1800096F0, "dispatcher"), (0x1800011E0, "pf16_entry"), (0x180002670, "mask"), (0x180009470, "main")):
        ld.add_code_hook(addr, lambda loader, address, size, label=label: trace.append({"event": label}))
    result = ld.call_function(ENTRY, [11, indata, outdata, parr, output, 0], max_instructions=30_000_000)
    assert result["rax"] == 0
    return ld.read_bytes(output_data, ROWBYTES * H), trace


def production(payload):
    with tempfile.TemporaryDirectory(prefix="sm1-prod-effectmain-") as td:
        dylib = Path(td) / "lib.dylib"
        subprocess.run(["clang++", "-std=c++17", "-O2", "-shared", "-fPIC", "-I" + str(ROOT / "cli/OLMSmoother/shim"), str(HARNESS), "-o", str(dylib)], check=True, capture_output=True)
        lib = ctypes.CDLL(str(dylib)); fn = lib.olmsmoother_v1_effectmain_render16_colorkey
        fn.argtypes = [ctypes.POINTER(ctypes.c_uint16), ctypes.POINTER(ctypes.c_uint16), ctypes.c_int32, ctypes.c_int32, ctypes.c_int32, ctypes.c_int32, ctypes.c_uint8, ctypes.c_uint8, ctypes.c_uint8, ctypes.c_int32]
        words = struct.unpack("<%dH" % (len(payload)//2), payload)
        src = (ctypes.c_uint16 * len(words))(*words); dst = (ctypes.c_uint16 * len(words))(*([0xA5A5] * len(words)))
        assert fn(src, dst, W, H, ROWBYTES, 1, *KEY, 6) == 0
        return struct.pack("<%dH" % len(words), *dst)


def main():
    assert hashlib.sha256(AEX.read_bytes()).hexdigest() == AEX_SHA
    k = tuple(map(widen, KEY)); cases=[]
    for name,pixel in (("exact_key",(0x8000,*k)),("near_key_red_plus_one",(0x8000,k[0]+1,k[1],k[2]))):
        payload=b''.join(struct.pack('<4H',*pixel)*W+bytes([0xD0+y])*8 for y in range(H))
        a,trace=actual(payload); p=production(payload)
        assert a == p, (name,next((i,x,y) for i,(x,y) in enumerate(zip(a,p)) if x!=y))
        counts={event:sum(e['event']==event for e in trace) for event in ('dispatcher','pf16_entry','new_world','copy','mask','main','dispose_world')}
        assert counts['dispatcher']==counts['pf16_entry']==counts['new_world']==counts['dispose_world']==1
        assert counts['mask']==counts['main']==W*H
        cases.append({'name':name,'raw_sha256':hashlib.sha256(a).hexdigest(),'padding_exact':all(a[y*ROWBYTES+W*8:(y+1)*ROWBYTES]==bytes([0xA5])*8 for y in range(H)),'trace_counts':counts,'trace':trace})
    assert cases[0]['raw_sha256'] != cases[1]['raw_sha256']
    report={'schema_version':1,'status':'exact','scope':'OLMSmoother v1 actual exported PF_Cmd_RENDER full PF16 Color Key session vs production EffectMain','actual_aex_sha256':AEX_SHA,'fixture':{'width':W,'height':H,'rowbytes':ROWBYTES,'tolerance':6,'key_rgb8':KEY},'cases':cases,'claims_not_made':['AE export Gamma boundary','PF32','non-uniform main-kernel arithmetic','other geometry or iteration order']}
    REPORT.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n'); print(json.dumps(report,indent=2,sort_keys=True))

if __name__ == '__main__': main()
