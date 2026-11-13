"""Extend record's owned debugger with bounded, explicitly selected pointer follows.

The extension records evidence; it never substitutes implementations or patches
another process. All breakpoint lifecycle/cleanup remains in record.capture.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'record'))
import record


class ContextCapture(record.Capture):
    def hook_target(self,debug,p,target,name,args,ret,buffers=(),max_calls=2):
        # Resolve only the selected pointer through the debugger's module map.
        owner=None
        for m in reversed(p['loaded']):
            if not m['path'] or target<m['base']: continue
            if 'size' not in m:
                dos=debug.read(p,m['base'],64)
                nt=m['base']+int.from_bytes(dos[60:64],'little')
                m['size']=int.from_bytes(debug.read(p,nt+24+56,4),'little')
            if target<m['base']+m['size']:owner=m;break
        if owner is None:
            # CREATE_PROCESS is not included in record's DLL-only loaded list.
            import ctypes as c
            mbi=c.create_string_buffer(48)
            query=c.WinDLL('kernel32',use_last_error=True).VirtualQueryEx
            query.argtypes=[c.c_void_p,c.c_void_p,c.c_void_p,c.c_size_t]
            query.restype=c.c_size_t
            if not query(p['handle'],target,mbi,48):raise c.WinError(c.get_last_error())
            base=struct.unpack_from('<Q',mbi.raw,8)[0]
            import pefile
            pe=pefile.PE(p['image'],fast_load=True)
            if not base <= target < base+pe.OPTIONAL_HEADER.SizeOfImage:
                raise ValueError('unresolved callback provider')
            owner={'path':p['image'],'base':base}
        path=str(Path(owner['path']).resolve())
        self.identities.setdefault(path,record.sha(path))
        hook={'name':name,'rva':hex(target-owner['base']),'module':path,'args':args,'return':ret,
              'max_calls':max_calls,'buffers':list(buffers),'import':{'name':name,'dll':Path(path).name,'kind':'observed-suite-pointer'}}
        debug.bp(p,target,hook)

    def extra(self,debug,p,rec,name,address,size,link,phase='before'):
        if not address or not 0 < size <= 4*1024*1024:
            raise ValueError(f'invalid followed region {name}: {address:x}/{size}')
        if self.bytes_reserved+size*2 > self.max_bytes:
            raise ValueError('context snapshot budget exhausted')
        self.bytes_reserved+=size*2
        b={'name':name,'address':hex(address),'size':size,'stride':size,'role':'inout',
           'descriptor':{'follow':link}}
        self.blob(debug,p,rec,b,phase)
        rec['buffers'].append(b)
        return debug.read(p,address,size)

    def entry(self,debug,p,tid,ctx,f):
        rec=super().entry(debug,p,tid,ctx,f)
        if rec is None: return None
        ptr=lambda i:int.from_bytes(bytes.fromhex(rec['args'][i]['bits_le']),'little')
        if f['name'].startswith('worker'):
            for i in [2,3]:
                header=debug.read(p,ptr(i),0x80)
                data=struct.unpack_from('<Q',header,0x18)[0]
                stride,w,h=struct.unpack_from('<iii',header,0x20)
                if min(stride,w,h)<=0 or max(w,h)>8192: raise ValueError('unsupported world geometry')
                self.extra(debug,p,rec,f'world{i}_pixels',data,stride*h,{'arg':i,'offset':0x18})
            context=debug.read(p,ptr(0),0x190)
            for off,size,label in [(0xb0,0x48,'util_callbacks'),(0x180,16,'basic_suite')]:
                target=struct.unpack_from('<Q',context,off)[0]
                raw=self.extra(debug,p,rec,label,target,size,{'arg':0,'offset':off})
                rec.setdefault('indirect_targets',[]).extend(
                    {'table':label,'offset':j,'target':hex(struct.unpack_from('<Q',raw,j)[0])}
                    for j in range(0,size,8))
                if f.get('trace_callbacks'):
                    if label=='util_callbacks':
                        self.hook_target(debug,p,struct.unpack_from('<Q',raw,0x40)[0],'observed_world_copy',
                            ['u64','ptr','ptr','u64'],'i32',[{'arg':1,'size':128},{'arg':2,'size':128}])
                    else:
                        self.hook_target(debug,p,struct.unpack_from('<Q',raw)[0],'observed_acquire',
                            ['ptr','i32','ptr'],'i32',[{'arg':0,'size':16},{'arg':2,'size':8}])
        self.save(rec)
        return rec

    def returned(self,debug,p,ctx,rec):
        super().returned(debug,p,ctx,rec)
        if rec['name']=='observed_acquire' and rec['return']['bits_le']=='00000000':
            output=int.from_bytes(bytes.fromhex(rec['args'][2]['bits_le']),'little')
            table=int.from_bytes(debug.read(p,output,8),'little')
            raw=self.extra(debug,p,rec,'returned_handle_suite',table,32,{'arg':2,'indirect':True},phase='after')
            rec['resolved_handle_targets']=[hex(struct.unpack_from('<Q',raw,i)[0]) for i in range(0,32,8)]
            self.hook_target(debug,p,struct.unpack_from('<Q',raw)[0],'observed_new_handle',['u64'],'ptr')
            self.hook_target(debug,p,struct.unpack_from('<Q',raw,8)[0],'observed_lock_handle',['ptr'],'ptr')
            self.save(rec)


def profile(module,trace=False):
    functions=[]
    for name,rva in [('worker8',0x1a6150),('worker16',0x1a5a90),('worker32',0x1a6800)]:
        functions.append({'name':name,'rva':hex(rva),'args':['ptr','u64','ptr','ptr','ptr'],'return':'void','trace_callbacks':trace,
            'max_calls':4,'buffers':[{'arg':i,'size':size} for i,size in [(0,0x190),(2,0x80),(3,0x80),(4,4)]]})
    functions.append({'name':'smart_root','rva':'0x1a5970','args':['ptr']*4,'return':'void','max_calls':4,
        'buffers':[{'arg':i,'size':n} for i,n in [(0,0x90),(1,0x190),(2,0x80),(3,0x20)]]})
    functions.append({'name':'matrix_allocate','rva':'0x1ad7c0','args':['ptr','ptr','i32','i32','i32','i32'],
        'return':'ptr','max_calls':4,'buffers':[{'arg':0,'size':112},{'arg':1,'size':0x190}]})
    return {'schema_version':1,'module_sha256':record.sha(module),'functions':functions}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--route',default='smart8')
    p.add_argument('--width',type=int,default=7)
    p.add_argument('--height',type=int,default=5)
    p.add_argument('--radius',type=float,default=2)
    p.add_argument('--downsample',default='1')
    p.add_argument('--seed',type=int,default=20261112)
    p.add_argument('--trace-callbacks',action='store_true')
    a=p.parse_args(); a.out=a.out.resolve()
    a.module=(HERE.parents[3]/'ghidra_windows_aex/OLMToonDilate.aex').resolve()
    config=a.out.parent/(a.out.name+'-profile.json'); config.parent.mkdir(parents=True,exist_ok=True)
    config.write_text(json.dumps(profile(a.module,a.trace_callbacks),indent=2))
    request=config.with_name(a.out.name+'-request.json')
    request.write_text(json.dumps(record.oracle.make_request({'assignments':[{'slot':1,'value':a.radius}],
        'downsample':a.downsample,'size':[a.width,a.height]})))
    a.profile=config; a.request=request
    a.harness=record.oracle.DEFAULT_HARNESS
    a.timeout=60; a.max_calls=32; a.max_bytes=16*1024*1024
    record.Capture=ContextCapture
    raise SystemExit(record.capture(a))
