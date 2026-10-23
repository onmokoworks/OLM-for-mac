#!/usr/bin/env python3
"""Independent inner-Override / zero-span work admission boundary matrix."""
import random
import struct
import sys
sys.dont_write_bytecode=True
import verify_radialblur_type3_C46 as verify


def cases(adapter,matrix=None):
    for family in ('inner-override','zero-span-outer-override'):
        w,h=(1,65) if family=='inner-override' else (48,1)
        for depth in (8,16,32):
            rng=random.Random(46200+depth)
            values=[[rng.choice([0,16384,32768]),*[rng.randrange(32769) for _ in range(3)]] for _ in range(w*h)]
            pixels=b''.join(struct.pack('<4B',*[v*255//32768 for v in row]) if depth==8 else struct.pack('<4H',*row) if depth==16 else struct.pack('<4f',*[v/32768 for v in row]) for row in values)
            for repeat in (0,1):
                for size in (0.,50.):
                    params=adapter.defaults(w,h)
                    changes={1:2,2:[w*1.25,-h*.25],4:18,5:1,6:18,7:9,10:665,11:3,12:24,13:7,15:repeat,20:50.,22:size,24:0.,25:1}
                    if family=='zero-span-outer-override':changes.update({4:1693,5:3,6:16,10:11,11:2,12:28,25:3})
                    for p in params:
                        if p['slot'] in changes:p['value']=changes[p['slot']]
                    yield dict(seed=46200,index=0,family=family,geometry=[w,h],depth=depth,profile='sdr',parameters=params,pixels=pixels,input_padding=0,output_padding=0)


if __name__=='__main__':
    verify.cases=cases
    raise SystemExit(verify.main())
