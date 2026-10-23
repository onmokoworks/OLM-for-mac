#!/usr/bin/env python3
"""Direct PE64 UCRT execution. Unresolved imports fail closed, never use host math."""
import argparse, ctypes, hashlib, json, pathlib, struct
import pefile, unicorn
from unicorn import x86_const as x
from capstone import Cs, CS_ARCH_X86, CS_MODE_64
DEFAULT_DLL = pathlib.Path.home()/'.cache/olm-emu/ucrt/10.0.28000.2705/ucrtbase.dll'
FUNCTIONS = ('expf','atan2f','sinf','cosf','powf')
PINNED_SHA256 = '385a6d73a50063a4c760bdb2ee59e575de7ff350a2e3b214ea491d08358484f3'
class Probe:
    def __init__(self, path=DEFAULT_DLL, cpu=None):
        if hashlib.sha256(path.read_bytes()).hexdigest() != PINNED_SHA256:
            raise ValueError('Unknown DLL: dispatch RVAs are pinned to the recorded SHA256')
        self.pe = pefile.PE(str(path)); self.base = self.pe.OPTIONAL_HEADER.ImageBase
        self.uc = unicorn.Uc(unicorn.UC_ARCH_X86, unicorn.UC_MODE_64)
        if cpu is not None: self.uc.ctl_set_cpu_model(cpu)
        self.uc.mem_map(self.base, (self.pe.OPTIONAL_HEADER.SizeOfImage+4095)&~4095)
        self.uc.mem_write(self.base, self.pe.get_memory_mapped_image())
        self.exports = {s.name.decode(): self.base+s.address for s in self.pe.DIRECTORY_ENTRY_EXPORT.symbols if s.name}
        self.stack = 0x70000000; self.stop = 0x71000000
        self.uc.mem_map(self.stack, 0x100000); self.uc.mem_map(self.stop, 0x1000)
        self.uc.reg_write(x.UC_X86_REG_MXCSR,0x1f80)
        self.imports = {}
        for desc in self.pe.DIRECTORY_ENTRY_IMPORT:
            for imp in desc.imports:
                self.imports[imp.address] = desc.dll.decode()+'!'+str(imp.name)
        self.md = Cs(CS_ARCH_X86, CS_MODE_64)
    def disasm(self, addr, size=128):
        return [f'{i.address-self.base:#x}: {i.mnemonic} {i.op_str}' for i in self.md.disasm(bytes(self.uc.mem_read(addr,size)),addr)]
    def call(self, name, bits=(), integer=None):
        sp = self.stack+0xfff08
        self.uc.mem_write(sp, struct.pack('<Q',self.stop))
        self.uc.reg_write(x.UC_X86_REG_RSP,sp)
        for i,b in enumerate(bits): self.uc.reg_write(x.UC_X86_REG_XMM0+i,b)
        if integer is not None: self.uc.reg_write(x.UC_X86_REG_RCX,integer)
        try:
            self.uc.emu_start(self.exports[name],self.stop,count=100000)
            if self.uc.reg_read(x.UC_X86_REG_RIP)!=self.stop: raise RuntimeError('instruction limit')
        except (unicorn.UcError,RuntimeError) as e:
            rip = self.uc.reg_read(x.UC_X86_REG_RIP)
            raise RuntimeError(json.dumps(dict(error=str(e),rip=hex(rip),rva=hex(rip-self.base),instruction=self.disasm(rip,20)))) from e
        return self.uc.reg_read(x.UC_X86_REG_XMM0)&0xffffffff
    def identity(self,path):
        v=self.pe.VS_FIXEDFILEINFO[0]
        return dict(sha256=hashlib.sha256(path.read_bytes()).hexdigest(),file_version='.'.join(str(a) for a in (v.FileVersionMS>>16,v.FileVersionMS&65535,v.FileVersionLS>>16,v.FileVersionLS&65535)),unicorn=unicorn.__version__,exports={n:hex(self.exports[n]-self.base) for n in (*FUNCTIONS,'_set_FMA3_enable')})
    def set_mode(self, mode):
        # DLL startup is deliberately not executed. Seed the capability mask
        # read by the actual setter; 3 also selects atan2f's accelerated entry.
        self.uc.mem_write(self.base+0x13bdf4, struct.pack('<I', 3))
        self.call('_set_FMA3_enable', integer=mode)
        value = struct.unpack('<I', self.uc.mem_read(self.base+0x13bdf0,4))[0]
        assert value == (3 if mode else 0), value
        return value
def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--dll',type=pathlib.Path,default=DEFAULT_DLL)
    ap.add_argument('--check',type=pathlib.Path,help='Require exact equality with a recorded smoke summary')
    args=ap.parse_args()
    p=Probe(args.dll); out=p.identity(args.dll)
    out['status']='blocked'
    out['scope']='Smoke only; no random or exhaustive sweep; AMD not built or compared.'
    out['dispatch']={'capability_rva':'0x13bdf4','active_mask_rva':'0x13bdf0','startup_executed':False,'forced_capability_mask':3}
    out['dispatch_disassembly']=p.disasm(p.exports['_set_FMA3_enable'],64)
    out['entry_disassembly']={n:p.disasm(p.exports[n],64) for n in FUNCTIONS}
    out['smoke']=[]
    libm=ctypes.CDLL('/usr/lib/libSystem.B.dylib')
    for cpu_name,cpu in [('default',None),('haswell',x.UC_CPU_X86_HASWELL),('skylake_client',x.UC_CPU_X86_SKYLAKE_CLIENT)]:
        for mode in (0,1):
            for name in FUNCTIONS:
                # Each observation starts with a fresh machine, including after faults.
                p=Probe(args.dll,cpu)
                mask=p.set_mode(mode)
                binary=name in ('atan2f','powf')
                inputs=(0x3f800000,0x40000000) if binary else (0x3f800000,)
                fn=getattr(libm,name);fn.argtypes=[ctypes.c_float]*len(inputs);fn.restype=ctypes.c_float
                apple=struct.unpack('<I',struct.pack('<f',fn(*([1.0,2.0] if binary else [1.0]))))[0]
                try:
                    value=p.call(name,inputs)
                    result={'output':hex(value),'matches_apple':value==apple}
                except RuntimeError as e: result={'failure':json.loads(str(e))}
                out['smoke'].append(dict(cpu=cpu_name,mode=mode,active_mask=mask,function=name,inputs=[hex(b) for b in inputs],apple=hex(apple),**result))
    if args.check:
        assert out==json.loads(args.check.read_text()), 'Smoke results changed'
        print('PASS: 30 smoke observations reproduce; status remains blocked')
        return
    print(json.dumps(out,indent=2))
if __name__=='__main__': main()
