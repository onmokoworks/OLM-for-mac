"""Record ColorKeep's parameter parent and first pixel calls on real renders."""
import argparse,json,struct
from pathlib import Path
from capture_context import ContextCapture,record,HERE

class ColorCapture(ContextCapture):
    def entry(self,debug,p,tid,ctx,f):
        rec=record.CaptureBase.entry(self,debug,p,tid,ctx,f)
        if rec is None:return None
        ptr=lambda i:int.from_bytes(bytes.fromhex(rec['args'][i]['bits_le']),'little')
        if f['name']=='parameter_snapshot':
            raw=debug.read(p,ptr(1),400)
            self.hook_target(debug,p,struct.unpack_from('<Q',raw)[0],'checkout',
                ['u64','i32','i32','i32','u32','ptr'],'i32',[{'arg':5,'size':176}],max_calls=101)
            basic=struct.unpack_from('<Q',raw,0x180)[0]
            target=struct.unpack('<Q',debug.read(p,basic,8))[0]
            self.hook_target(debug,p,target,'color_acquire',['ptr','i32','ptr'],'i32',[{'arg':0,'size':18},{'arg':2,'size':8}])
        if f['name'].startswith('pixel'):
            raw=debug.read(p,ptr(0),1640)
            for off,label in [(8,'source'),(16,'destination')]:
                address=struct.unpack_from('<Q',raw,off)[0]
                header=self.extra(debug,p,rec,label,address,128,{'arg':0,'offset':off})
                data=struct.unpack_from('<Q',header,24)[0]
                stride,w,h=struct.unpack_from('<iii',header,32)
                self.extra(debug,p,rec,label+'_pixels',data,stride*h,{'buffer':label,'offset':24})
        self.save(rec)
        return rec

    def returned(self,debug,p,ctx,rec):
        record.CaptureBase.returned(self,debug,p,ctx,rec)
        if rec['name']=='color_acquire' and rec['return']['bits_le']=='00000000':
            address=int.from_bytes(bytes.fromhex(rec['args'][2]['bits_le']),'little')
            table=struct.unpack('<Q',debug.read(p,address,8))[0]
            target=struct.unpack('<Q',debug.read(p,table,8))[0]
            rec['resolved_target']=hex(target);self.save(rec)
            self.hook_target(debug,p,target,'color_float',['u64','ptr','ptr'],'i32',
                [{'arg':1,'size':176},{'arg':2,'size':16}],max_calls=100)

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--out',type=Path,required=True);p.add_argument('--route',default='smart8')
    a=p.parse_args();a.out=a.out.resolve();a.out.parent.mkdir(parents=True,exist_ok=True)
    a.module=(HERE.parents[3]/'ghidra_windows_aex/ColorKeep.aex').resolve()
    funcs=[{'name':'parameter_snapshot','rva':'0x1a90','args':['u64','ptr','u64','u64','ptr','ptr'],
        'return':'i32','max_calls':2,'buffers':[{'arg':1,'size':400},{'arg':4,'size':128},{'arg':5,'size':1640}]}]
    for d,rva,n in [(8,'0x1580',4),(16,'0x1280',8),(32,'0x1850',16)]:
        funcs.append({'name':f'pixel{d}','rva':rva,'args':['ptr','u64','u64','ptr','ptr'],'return':'u64',
          'max_calls':2,'buffers':[{'arg':0,'size':1640},{'arg':3,'size':n},{'arg':4,'size':n}]})
    a.profile=a.out.with_name(a.out.name+'-profile.json')
    a.profile.write_text(json.dumps({'schema_version':1,'module_sha256':record.sha(a.module),'functions':funcs}))
    a.request=a.out.with_name(a.out.name+'-request.json')
    a.request.write_text(json.dumps(record.oracle.make_request({'size':[7,5],'downsample':'1','assignments':[{'slot':1,'value':2}]})))
    a.width=7;a.height=5;a.seed=20261112;a.timeout=60;a.max_calls=256;a.max_bytes=16*1024*1024
    a.harness=record.oracle.DEFAULT_HARNESS
    record.CaptureBase=record.Capture;record.Capture=ColorCapture
    return record.capture(a)

if __name__=='__main__':raise SystemExit(main())
