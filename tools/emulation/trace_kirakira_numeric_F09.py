#!/usr/bin/env python3
"""Paired raw stage census for the retained T06 numeric witnesses.

Uses the original AEX full caller, its original source reader and outer writer.
The existing Python probe supplies Windows allocation/TLS/import scaffolding;
no numerical AEX function is replaced. Each result is bound independently to
the resident public worker's final raw output before interpreting its stages.
Mac instrumentation and admission bypass exist only in a scratch translation
unit. This is a diagnostic, not a production admission change.
"""
import argparse
import json
import os
from pathlib import Path
import struct
import sys
import time
from types import SimpleNamespace

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'tools/fuzz'))
from adapters import olmkirakira
from core import load_corpus, sha, raw_diff
from run import default_worker, main_checkout


def original_trace(case, aex, *, aex_percent_materialization=False, host_powf=False, ucrt_math=None):
    import probe_olmkirakira_mode3_actual_aex as base
    from unicorn.x86_const import (UC_X86_REG_RBP, UC_X86_REG_RDX, UC_X86_REG_RCX,
        UC_X86_REG_RSP, UC_X86_REG_R8, UC_X86_REG_R9, UC_X86_REG_XMM0, UC_X86_REG_XMM1, UC_X86_REG_XMM2, UC_X86_REG_XMM3)
    p = {v['slot']: v['value'] for v in case['parameters']}
    fw, fh = case['geometry']; fn = fw*fh
    w, h = (fw//2, fh//2) if p[4] else (fw, fh)
    n = w*h
    stages = {}; geometry = []; row_filters = {}; column_filters = []; resize_writers = []
    original = base.AexLoader

    class Loader(original):
        def register_libm_impls(self, max_threads=1):
            super().register_libm_impls(max_threads)
            if host_powf:
                # Legacy host-powf diagnostic, not the F46 UCRT import.
                # Require final public-output binding before stage claims.
                import ctypes
                powf = ctypes.CDLL(None).powf
                powf.argtypes = (ctypes.c_float, ctypes.c_float)
                powf.restype = ctypes.c_float
                def imported_powf(uc, args):
                    self.write_xmm_f32(0, powf(self.read_xmm_f32(0), self.read_xmm_f32(1)))
                    return 0
                self.import_impls['powf'] = imported_powf
            if ucrt_math is not None:
                # Bind all F46 imported math to the independent UCRT library.
                import ctypes
                library = ctypes.CDLL(str(ucrt_math))
                for name, count, wide in (('expf', 1, False), ('powf', 2, False),
                        ('atan2f', 2, False), ('sinf', 1, False), ('cosf', 1, False),
                        ('log2f', 1, False), ('sin', 1, True), ('cos', 1, True),
                        ('exp', 1, True), ('pow', 2, True)):
                    function = getattr(library, 'ucrt_' + name)
                    scalar = ctypes.c_double if wide else ctypes.c_float
                    function.argtypes = [scalar] * count + [ctypes.c_int]
                    function.restype = scalar
                    def imported(uc, args, function=function, count=count, wide=wide):
                        read = self.read_xmm_f64 if wide else self.read_xmm_f32
                        write = self.write_xmm_f64 if wide else self.write_xmm_f32
                        write(0, function(*(read(i) for i in range(count)), 1))
                        return 0
                    self.import_impls[name] = imported



        def add_code_hook(self, address, callback):
            # The base probe normally stops at Gaussian entry. Here execute
            # the actual Gaussian body, after the original CRT initializers.
            if address != base.FUN_GAUSSIAN:
                return super().add_code_hook(address, callback)

        def call_function(self, address, *args, **kwargs):
            if address != base.FUN_HELPER:
                return super().call_function(address, *args, **kwargs)
            def alloc(data):
                ptr = self.host_alloc(max(8, len(data)), align=64)
                self.write_bytes(ptr, data)
                return ptr
            def words(ptr, count):
                return self.read_bytes(ptr, count*4).hex()
            # Import-free known answer also validates the fifth Win64 stack
            # argument before any full-caller observation is trusted.
            probe_input = alloc(bytes([255,255,0,0])); probe_rgba = alloc(bytes(16))
            super().call_function(0x181230a80,
                int_args=[probe_rgba,probe_rgba+4,probe_rgba+8,probe_rgba+12,probe_input],max_instructions=1000)
            assert self.read_bytes(probe_rgba,16) == struct.pack('<4f',1,0,0,1)
            raw = alloc(case['pixels']); pixels = alloc(bytes(fn*16))
            reader = {8:0x181230a80,16:0x181230af0,32:0x181230b60}[case['depth']]
            for i in range(fn):
                q = pixels+i*16
                super().call_function(reader, int_args=[q,q+4,q+8,q+12,raw+i*case['depth']//2], max_instructions=1000)
            full_pixels = pixels
            stages['source_full'] = words(pixels, fn*4)
            def resize(data, sw, sh, dw, dh):
                from unicorn import UC_HOOK_MEM_WRITE, UC_HOOK_CODE
                from unicorn.x86_const import UC_X86_REG_RIP
                output = alloc(bytes(dw*dh*16))
                mats = []
                for ptr, width, height in ((data, sw, sh), (output, dw, dh)):
                    mat = alloc(bytes(96))
                    super(Loader,self).call_function(0x181157770,
                        int_args=[mat,height,width,29,ptr,width*16], max_instructions=100000)
                    mats.append(mat)
                a = alloc(struct.pack('<IIQQ', 0x1010000,0,mats[0],0))
                b = alloc(struct.pack('<IIQQ', 0x2010000,0,mats[1],0))
                writers = {}
                interpolation_rows = []
                horizontal_coefficients = []
                def horizontal_row(ld, _addr, _size):
                    count = ld.uc.reg_read(UC_X86_REG_RDX) & 0xffffffff
                    value = dict(count=count, indices_hex=ld.read_bytes(ld.uc.reg_read(UC_X86_REG_R8),count*4).hex(),
                        weights_hex=ld.read_bytes(ld.uc.reg_read(UC_X86_REG_R9),count*4).hex())
                    if value not in horizontal_coefficients: horizontal_coefficients.append(value)
                horizontal_hook = self.uc.hook_add(UC_HOOK_CODE, lambda uc,addr,size,user: horizontal_row(self,addr,size), begin=0x1806e7d20, end=0x1806e7d20)
                def vertical_row(ld, _addr, _size):
                    count = ld.uc.reg_read(UC_X86_REG_RDX) & 0xffffffff
                    stack = ld.uc.reg_read(UC_X86_REG_RSP)
                    second = struct.unpack("<Q", ld.read_bytes(stack+0x28,8))[0]
                    interpolation_rows.append(dict(
                        destination_word=(ld.uc.reg_read(UC_X86_REG_RCX)-output)//4,
                        count=count,
                        weight_hex=(ld.uc.reg_read(UC_X86_REG_XMM2)&0xffffffff).to_bytes(4,"little").hex(),
                        a_hex=ld.read_bytes(ld.uc.reg_read(UC_X86_REG_R9),count*4).hex(),
                        b_hex=ld.read_bytes(second,count*4).hex()))
                row_hook = self.uc.hook_add(UC_HOOK_CODE, lambda uc,addr,size,user: vertical_row(self,addr,size), begin=0x1806e6e80, end=0x1806e6e80)
                def wrote(uc, access, address, size, value, user):
                    pc = hex(uc.reg_read(UC_X86_REG_RIP))
                    writers[pc] = writers.get(pc, 0) + 1
                hook = self.uc.hook_add(UC_HOOK_MEM_WRITE, wrote,
                    begin=output, end=output+dw*dh*16-1)
                try:
                    super(Loader,self).call_function(0x1812639f0,
                        int_args=[a,b,dw+(dh<<32),0,0,1], float_args={3:0.0},max_instructions=200000000)
                finally:
                    self.uc.hook_del(hook)
                    self.uc.hook_del(row_hook)
                    self.uc.hook_del(horizontal_hook)
                resize_writers.append(dict(source=[sw,sh], destination=[dw,dh], interpolation=1, writers=writers, vertical_rows=interpolation_rows, horizontal_coefficients=horizontal_coefficients))
                return output
            if p[4]: pixels = resize(pixels,fw,fh,w,h)
            stages['source'] = words(pixels,n*4)
            def sincos_entry(ld, _addr, _size):
                geometry.append(dict(radians_f32_hex=struct.pack('<I',ld.uc.reg_read(UC_X86_REG_XMM0)&0xffffffff).hex()))
            def sincos_return(ld, _addr, _size):
                geometry[-1]['sine_cosine_f32_hex'] = (ld.uc.reg_read(UC_X86_REG_XMM0)&((1<<64)-1)).to_bytes(8,'little').hex()
            super().add_code_hook(0x18114f78b,sincos_entry)
            super().add_code_hook(0x18114f790,sincos_return)
            def row_filter_entry(ld, _addr, _size):
                obj = ld.uc.reg_read(UC_X86_REG_RCX)
                kernel = struct.unpack('<i', ld.read_bytes(obj + 8, 4))[0]
                width = ld.uc.reg_read(UC_X86_REG_R9) & 0xffffffff
                channels = struct.unpack('<I', ld.read_bytes(ld.uc.reg_read(UC_X86_REG_RSP) + 0x28, 4))[0]
                key = f'{_addr:x}/{kernel}/{width}/{channels}'
                row_filters[key] = row_filters.get(key, 0) + 1
            for row_entry in (0x18127f3c0, 0x1812d6690, 0x1812adaa0, 0x1812f9a70, 0x1813183d0):
                super().add_code_hook(row_entry, row_filter_entry)
            def column_filter_entry(ld, address, _size):
                obj = ld.uc.reg_read(UC_X86_REG_RCX)
                stack = ld.uc.reg_read(UC_X86_REG_RSP)
                column_filters.append(dict(address=hex(address),
                    kernel=struct.unpack('<i', ld.read_bytes(obj + 8, 4))[0],
                    sum_count=struct.unpack('<i', ld.read_bytes(obj + 0x18, 4))[0],
                    rows=struct.unpack('<i', ld.read_bytes(stack + 0x28, 4))[0],
                    width=struct.unpack('<i', ld.read_bytes(stack + 0x30, 4))[0]))
            super().add_code_hook(0x1812d1d70, column_filter_entry)
            ray_number = [-1]
            op_number = [0]
            def helper_entry(ld, _addr, _size):
                ray_number[0] += 1; op_number[0] = 0
            super().add_code_hook(base.FUN_HELPER, helper_entry)
            def op_entry(ld, addr, _size):
                num = op_number[0]; op_number[0] += 1
                name = f'helper{ray_number[0]}_op{num}'
                def read_wrapper(wrapper):
                    matptr = struct.unpack('<Q',ld.read_bytes(wrapper+8,8))[0]
                    mat = base.read_mat(ld,matptr)
                    assert mat
                    data = b''.join(ld.read_bytes(int(mat['data'],16)+y*mat['step_bytes'],mat['cols']*mat['channels']*4) for y in range(mat['rows']))
                    return data.hex(), [mat['cols'],mat['rows'],mat['channels']]
                source_wrapper = ld.uc.reg_read(UC_X86_REG_RCX)
                dest_wrapper = ld.uc.reg_read(UC_X86_REG_RDX)
                stages[name+'_in'], stages[name+'_shape'] = read_wrapper(source_wrapper)
                ret = struct.unpack('<Q',ld.read_bytes(ld.uc.reg_read(UC_X86_REG_RSP),8))[0]
                active = [True]
                def returned(ld, _addr, _size):
                    if active[0]:
                        active[0] = False
                        stages[name+'_out'],_ = read_wrapper(dest_wrapper)
                super(Loader,self).add_code_hook(ret, returned)
            for addr in (0x181297ac0,0x181280bc0,0x181272ec0):
                super().add_code_hook(addr, op_entry)
            def seed(ld, _addr, _size):
                mat = base.read_mat(ld, ld.uc.reg_read(UC_X86_REG_RBP))
                assert mat and mat['rows'] == h and mat['cols'] == w
                stages['seed_channels'] = mat['channels']
                stages['seed'] = b''.join(ld.read_bytes(int(mat['data'],16)+y*mat['step_bytes'], w*mat['channels']*4) for y in range(h)).hex()
            super().add_code_hook(0x18114f589, seed)
            def aggregate(ld, _addr, _size):
                norms = struct.unpack('<Q',ld.read_bytes(ld.uc.reg_read(UC_X86_REG_RSP)+0x30,8))[0]
                stages['normalizers'] = words(norms,5)
                ptrs = struct.unpack('<5Q',ld.read_bytes(ld.uc.reg_read(UC_X86_REG_RDX),40))
                for i, ptr in enumerate(ptrs):
                    stages[f'ray{i}'] = words(ptr,n*stages['seed_channels'])
            for addr in (0x18114fd90,0x18114f020):
                super().add_code_hook(addr, aggregate)
            handles = {}
            def new_handle(ld, args):
                ptr = alloc(bytes(max(8,int(args[0])))); handles[ptr] = 1
                return ptr
            no_op = lambda ld,args: 0
            suite = alloc(struct.pack('<4Q', self.install_callback('F09 new',new_handle),
                self.install_callback('F09 lock',lambda ld,args: args[0]),
                self.install_callback('F09 unlock',no_op), self.install_callback('F09 dispose',no_op)))
            def acquire(ld,args):
                ld.write_bytes(args[2],struct.pack('<Q',suite)); return 0
            basic = alloc(struct.pack('<2Q',self.install_callback('F09 acquire',acquire),self.install_callback('F09 release',no_op)))
            host = alloc(bytes(0x188)); self.write_bytes(host+0x180,struct.pack('<Q',basic))
            obj = alloc(bytes(8))
            ctor = {1:0x18114edb0,2:0x1811505c0,4:0x18114ec20}.get(p[1],0x18114eed0)
            super().call_function(ctor,int_args=[obj],max_instructions=1000)
            angles = alloc(struct.pack('<5i',*[a+round(p[40]*65536) for a in (90,0,45,135)],0))
            lengths = alloc(struct.pack('<5i',*[p[s]//2 if p[4] else p[s] for s in (10,16,22,28,34)]))
            colors = alloc(struct.pack('<20f',*[v/255 for s in (11,17,23,29,35) for v in p[s]]))
            # Drive the original default-handle producer using the grounded
            # ABI from the default-handle/relocation probes. Custom handles
            # are not modeled; public final-output binding is still required.
            handler = alloc(struct.pack('<2Q', 0x18148d818, 0))
            output_handle = alloc(bytes(8))
            super().call_function(0x18123abf0,
                int_args=[handler,host,output_handle],max_instructions=500000)
            handle = struct.unpack('<Q',self.read_bytes(output_handle,8))[0]
            payload = self.read_bytes(handle+16,0x144)
            ramps = alloc(payload * 5)
            flags = alloc(bytes(int(bool(p[s])) for s in (13,19,25,31,37)))
            glow = alloc(bytes(n*16))
            bits = lambda f: struct.unpack('<I',struct.pack('<f',f))[0]
            def percent(value):
                if not aex_percent_materialization:
                    return value / 100
                # FUN_18114e860: CVTDQ2PS followed by MULSS with the
                # original binary constant. Keep legacy F09 traces reproducible.
                f32 = lambda x: struct.unpack('<f', struct.pack('<f', x))[0]
                scale = struct.unpack('<f', self.read_bytes(0x181486c10, 4))[0]
                assert struct.pack('<f', scale).hex() == '0ad7233c'
                return f32(f32(value) * scale)
            # FUN_18114e860 materializes the slider as FLOAT32 then MULSS
            # with DAT_181486c18, not a double product narrowed afterwards.
            f32 = lambda x: struct.unpack('<f', struct.pack('<f', x))[0]
            fade_scale = struct.unpack('<f', self.read_bytes(0x181486c18,4))[0]
            result = super().call_function(0x18114f4a0,
                int_args=[obj,host,pixels,glow,angles,lengths,colors,flags,ramps,p[2],w,h,bits(percent(p[6])),bits(f32(p[7])*fade_scale),1,bits(p[5])],
                max_instructions=200_000_000)
            stages['glow'] = words(glow,n*4)
            if p[4]: glow = resize(glow,w,h,fw,fh)
            stages['glow_full'] = words(glow,fn*4)
            owner = alloc(bytes(0x200))
            for off,data in ((0x38,struct.pack('<f',percent(p[8]))),(0x3c,struct.pack('<f',percent(p[9]))),
                (0x44,struct.pack('<i',p[3])),(0x58,struct.pack('<i',fn)),
                (0x128,struct.pack('<Q',full_pixels)),(0x190,struct.pack('<Q',glow))):
                self.write_bytes(owner+off,data)
            output = alloc(bytes(len(case['pixels'])))
            compose = {8:0x18114e110,16:0x18114ddc0,32:0x18114e460}[case['depth']]
            composed = bytearray()
            def before_writer(ld, _addr, _size):
                composed.extend(struct.pack('<4I',*[ld.uc.reg_read(r)&0xffffffff for r in
                    (UC_X86_REG_XMM0,UC_X86_REG_XMM1,UC_X86_REG_XMM2,UC_X86_REG_XMM3)]))
            super().add_code_hook({8:0x181230b90,16:0x181230bd0,32:0x181230c20}[case['depth']],before_writer)
            world = alloc(bytes(0x40))
            self.write_bytes(world+0x18,struct.pack('<Qiii',output,len(case['pixels']),fn,1))
            super().call_function(compose,int_args=[owner,world],max_instructions=max(200_000,fn*1000))
            stages['output'] = self.read_bytes(output,len(case['pixels'])).hex()
            stages['composed'] = composed.hex()
            return result

    base.AexLoader = Loader
    try:
        result = base.run(SimpleNamespace(aex_path=aex,width=w,height=h,length=50,sigma=0,max_instructions=200_000_000))
    finally:
        base.AexLoader = original
    return dict(stages=stages,geometry=geometry,row_filters=row_filters,column_filters=column_filters,resize_writers=resize_writers,status=result['status'],error=result.get('error'),
                crt=result.get('manual_crt_initializers_diagnostic'))


def traced_source(source_path, gate_off=True):
    source = source_path.read_text()
    source = source.replace('#include "OLMKiraKira.h"', '#include "'+str(olmkirakira.SOURCE.with_suffix('.h'))+'"')
    source = source.replace('#include "../../core/', '#include "'+str(ROOT/'core')+'/')
    source = source.replace('#include "../../ucrtmath/', '#include "'+str(ROOT/'ucrtmath')+'/')
    assert source.count('if (!exact_closure && !generic_beta) {') == 2
    if gate_off:
        source = source.replace('if (!exact_closure && !generic_beta) {','if (false) {')
    helper = r'''
static void F09Dump(const char *name, const void *data, size_t size) {
    const char *dir = std::getenv("F09_TRACE"); if (!dir) return;
    std::string path = std::string(dir) + "/" + name + ".raw";
    FILE *f = std::fopen(path.c_str(), "wb"); if (!f) std::abort();
    if (std::fwrite(data, 1, size, f) != size) std::abort(); std::fclose(f);
}
'''
    source = source.replace('static std::vector<float> DirectionBoxBlur(', helper+'\nstatic int F09Ray = -1;\nstatic std::vector<float> DirectionBoxBlur(')
    def insert(marker, text):
        nonlocal source
        assert source.count(marker) == 1, marker
        source = source.replace(marker,text+'\n'+marker)
    insert('\tconst A_long passes = BlurModePasses(info.blur_mode);',
           '\tF09Dump("source_full", source_pixels.data(), source_pixels.size()*sizeof(FloatRGBA));\n\tF09Dump("source", working_pixels.data(), working_pixels.size()*sizeof(FloatRGBA));\n\tF09Dump("seed", seed.data(), seed.size()*4);')
    insert('\tfloat scale = (float)info.brightness_gain;', '\n'.join(f'\tF09Dump("ray{i}", {name}.data(), {name}.size()*4);' for i,name in enumerate(('vertical','horizontal','diagonal','diagonal2','highlight'))))
    insert('\tstd::vector<FloatRGBA> composed((size_t)work_width * work_height);','\tF09Dump("glow", glow.data(), glow.size()*sizeof(FloatRGBA));')
    insert('\tfor (A_long y = 0; y < h; ++y) {\n\t\tfor (A_long x = 0; x < w; ++x) {\n\t\t\tconst size_t idx = (size_t)y * w + x;',
           '\tF09Dump("glow_full", glow_full.data(), glow_full.size()*sizeof(FloatRGBA));\n\tF09Dump("composed", output_pixels.data(), output_pixels.size()*sizeof(FloatRGBA));')
    insert('\ttemp_a = WarpGetRotDirect(temp_a, rw, rh, rw, rh, temp_cx, temp_cy, angle_deg);',
        '\t++F09Ray; F09Dump(("helper"+std::to_string(F09Ray)+"_op0_in").c_str(),temp_a.data(),temp_a.size()*4);')
    insert('\tstd::vector<float> temp_b((size_t)rw * rh);',
        '\tF09Dump(("helper"+std::to_string(F09Ray)+"_op0_out").c_str(),temp_a.data(),temp_a.size()*4);')
    insert('\t\tsrc.swap(dst);',
        '\t\tF09Dump(("helper"+std::to_string(F09Ray)+"_op"+std::to_string(pass+1)+"_out").c_str(),dst.data(),dst.size()*4);')
    insert('\ttemp_b = WarpGetRotDirect(temp_b, rw, rh, rw, rh, temp_cx, temp_cy, -angle_deg);',
        '\tif (blur_mode == 3) F09Dump(("helper"+std::to_string(F09Ray)+"_op1_out").c_str(),temp_b.data(),temp_b.size()*4);')
    return source


def build_mac(source, scratch, options, deadline, gate_off=True):
    class Adapter(olmkirakira.Adapter):
        def compile(self, argv, deadline):
            if argv[0] == 'clang++':
                host = next(Path(x) for x in argv if str(x).endswith('/host.cpp'))
                src = host.parent/'trace.cpp'; src.write_text(traced_source(source,gate_off))
                host.write_text(host.read_text().replace(str(olmkirakira.SOURCE),str(src)))
            return super().compile(argv,deadline)
    scratch.mkdir(parents=True,exist_ok=True)
    adapter = Adapter(options)
    adapter.binary,_ = adapter.build(scratch,deadline)
    return adapter


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--scratch',type=Path,required=True)
    parser.add_argument('--report',type=Path,required=True)
    parser.add_argument('--source',type=Path,default=olmkirakira.SOURCE,
                        help='Read an alternate revision; includes still resolve in this worktree')
    parser.add_argument('--indices',type=int,nargs='+',default=[148,116,78,157,19,210,23,232,3])
    args = parser.parse_args()
    args.scratch = args.scratch.resolve()
    assert args.scratch.is_relative_to(ROOT/'orchestra/state')
    args.scratch.mkdir(parents=True,exist_ok=True)
    os.environ.update(TMPDIR=str(args.scratch),TMP=str(args.scratch),TEMP=str(args.scratch),
                      OLM_KK_PROCESS_ATTACH_DIAGNOSTIC='1',OLM_KK_MANUAL_CRT_INITIALIZERS_DIAGNOSTIC='1')
    deadline = time.monotonic()+3600
    adapter = build_mac(args.source,args.scratch,
        SimpleNamespace(max_size=256,case_timeout=180,main=main_checkout(),worker=default_worker()),deadline)
    report = dict(schema='olm-kira-F09-stage-trace/1',aex_sha256=sha(adapter.aex.read_bytes()),
        worker_sha256=sha(adapter.worker.read_bytes()),source_sha256=sha(args.source.read_bytes()),
        source_path=str(args.source),
        contracts=dict(aex='CPU original full caller + source reader + typed outer writer',
            host='probe-local TLS, allocation, CRT initializers; Python libm imports; no numerical detours',
            mac='Classic EffectMain, scratch tuple bypass, arm64 O2 ffp-contract=off',
            limitation='Full-caller stages are usable only when final bytes bind to the public resident worker; neither is native AE/UCRT proof'),
        rows=[])
    for index in args.indices:
        path = next((ROOT/'tests/fuzz_corpus/olmkirakira_gate_off_T06').glob(f'seed1_case{index:06}_*.json'))
        case,_ = load_corpus(path,adapter)
        directory = args.scratch/str(index); directory.mkdir(exist_ok=True)
        adapter.env['F09_TRACE'] = str(directory)
        status,public = adapter.oracle(case,directory,deadline)
        candidate,mac,*_ = adapter.candidate(case,directory,'classic',deadline)
        trace = original_trace(case,adapter.aex)
        stages = trace['stages']; paired = {}
        for name in [*(k for k in stages if k not in ('output','seed_channels') and not k.endswith('_shape'))]:
            file = directory/(name+'.raw')
            if name in stages and file.exists():
                expected,actual = bytes.fromhex(stages[name]),file.read_bytes()
                paired[name] = dict(exact=expected==actual,aex_sha256=sha(expected),mac_sha256=sha(actual),
                    aex_hex=expected.hex(),mac_hex=actual.hex(),diff=None if expected==actual else raw_diff(expected,actual,32))
        bound = 'output' in stages and bytes.fromhex(stages['output']) == public and status['status']=='ok'
        # Keep captured plane data compact while retaining complete word-exact
        # first differences, hashes, shape and public final-output binding.
        for values in paired.values():
            for key in ('aex_hex','mac_hex'):
                if len(values[key]) > 512:
                    del values[key]
        row = dict(index=index,case_path=str(path.relative_to(ROOT)),input_sha256=sha(case['pixels']),
            geometry=case['geometry'],depth=case['depth'],oracle=status,candidate=candidate,
            public_sha256=sha(public),mac_sha256=sha(mac),trace_public_exact=bound,
            trace_output_sha256=sha(bytes.fromhex(stages.get('output',''))),trace_status=trace['status'],trace_error=trace['error'],
            aex_geometry=trace['geometry'],abi_leaf_exact='source' in stages,
            aex_shapes={k:v for k,v in stages.items() if k.endswith('_shape')},
            final_diff=raw_diff(public,mac,case['depth']) if public!=mac else None,
            first_divergent_stage=next((k for k,v in paired.items() if not v['exact']),None),paired=paired)
        report['rows'].append(row)
        args.report.parent.mkdir(parents=True,exist_ok=True)
        args.report.write_text(json.dumps(report,indent=2)+'\n')
        print(index,'bound',bound,'first',row['first_divergent_stage'],'error',trace['error'],flush=True)
    assert all(r['trace_public_exact'] for r in report['rows']), 'unbound AEX trace; do not infer a public first stage'


if __name__ == '__main__':
    main()
