"""Compare native c110 at every pixel with the actual Rust class-plane builder."""
import copy,json,struct
from verify_upstream_leaves import WORK,ORIGINAL,CANDIDATE,ptr,scalar,save,d

def f32(x):return struct.unpack('<f',struct.pack('<f',x))[0]
def main():
    w,h=7,5
    pixels=b''.join(struct.pack('<4f',.02*(x%3),.03*(y%3),.04*((x+y)%3),[0.,.5,1.][(x+y)%3]) for y in range(h) for x in range(w))
    buffers=dict(input=dict(size=len(pixels),hex=pixels.hex()),output=dict(size=4),plane=dict(size=24,hex=struct.pack('<Qiii4x',0,w,h,w*16).hex(),pointers=[dict(offset=0,buffer='input')]))
    ref=dict(schema_version=1,module=str(ORIGINAL),fma='fma',buffers=copy.deepcopy(buffers),calls=[])
    cand=dict(schema_version=1,module=str(CANDIDATE),fma='fma',buffers=copy.deepcopy(buffers),calls=[])
    stages=[]
    for version in (1,2,3):
        for value in (0.,.1,1.7,2.,2.9,49.9,100.):
            name=f'p{version}_{value}'.replace('.','_')
            config=bytearray(160);struct.pack_into('<i',config,4,version-1);struct.pack_into('<f',config,0x20,f32(f32(value)*f32(.01)));struct.pack_into('<f',config,0x90,value)
            for spec in (ref,cand):spec['buffers'][name]=dict(size=len(config),hex=config.hex())
            for y in range(h):
                for x in range(w):
                    idx=len(ref['calls']);args=[ptr('output'),ptr('plane'),scalar('i32',x),scalar('i32',y),ptr(name)]
                    ref['calls'].append(dict(rva='0xc110',args=args,**{'return':'void'}))
                    cand['calls'].append(dict(export='classify',args=copy.deepcopy(args),**{'return':'void'}))
                    stages.append(dict(id=f'{name}-{x}-{y}',dtype='u8',shape=[4],grounding='new c110 ABI: out[4], {data,width,height,rowbytes}, x,y, config; distance dispatch at +4, threshold at +0x20, extra disabled at +0x80',reference=dict(call=idx,buffer='output'),candidate=dict(call=idx,buffer='output')))
    case=dict(schema_version=1,stateless_calls=True,scope='All 35 pixels of a 7x5 class plane, 3 versions x 7 integer/fractional ranges, actual Rust whole-plane build',reference=dict(sha256=d.witness.sha256(ORIGINAL),expected_fma=1,witness=ref),candidate=dict(sha256=d.witness.sha256(CANDIDATE),expected_fma=1,witness=cand),stages=stages)
    save(WORK/'classes-map.json',case);print('Prepared',len(stages),'class comparisons')

if __name__=='__main__':main()
