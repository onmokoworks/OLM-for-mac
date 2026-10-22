#!/usr/bin/env python3
"""C11 independent center boundary matrix plus C06's sanitized replay checks."""
import random
import struct
import sys
sys.dont_write_bytecode = True
import verify_radialblur_smart_C06 as verify

ALL_DEPTHS = False
FINITE_INPUTS = False


def cases(adapter, matrix=None):
    if FINITE_INPUTS:
        yield from finite_cases(adapter)
        return
    for w,h in ((1,1),(3,5),(11,7)):
        centers=[[-1/65536,h/2],[w+1/65536,h/2],[w/2,-1/65536],[w/2,h+1/65536],
                 [-3.25,h/2],[w+3.25,h/2],[w/2,-5.75],[w/2,h+5.75],
                 [-w-2,-h-3],[2*w+2,2*h+3],[w//2+.25,h//2+.25],[0,0]]
        for depth in (8,16,32):
            rng=random.Random(11000+w*100+h+depth)
            pixels=b''
            for i in range(w*h):
                values=[rng.choice([0,16384,32768]),*[rng.randrange(32769) for _ in range(3)]]
                pixels+=(struct.pack('<4B',*[v*255//32768 for v in values]) if depth==8 else
                         struct.pack('<4H',*values) if depth==16 else
                         struct.pack('<4f',*[v/32768 for v in values]))
            for family in (1,2):
                if not ALL_DEPTHS and (depth==32 or (depth==16 and family==2)):
                    continue
                for index,center in enumerate(centers):
                    variants=[{4:4},{4:7,10:3,6:2,12:4},{4:4,7:25,13:50},
                              {4:7,10:3,22:25,24:25,25:2,27:89,28:31,29:7}]
                    changes=dict(variants[index%4])
                    changes.update({1:family,2:center,15:index%2,17:1 if index<8 else 2.25,
                                    18:0 if index<8 else -721,20:1})
                    params=adapter.defaults(w,h)
                    for p in params:
                        if p['slot'] in changes:p['value']=changes[p['slot']]
                    yield dict(geometry=[w,h],depth=depth,profile='sdr',parameters=params,
                               pixels=pixels,input_padding=0,output_padding=0)


def finite_cases(adapter):
    """Independent signed/HDR samples, including signed alpha and subnormals."""
    for w, h in ((1, 1), (3, 5), (11, 7)):
        for profile, values in (
                ('signed', [-4., -1., -0., 0., .5, 1., 2., 8.]),
                ('hdr', [0., .5, 1., 2., 8., 128., 32768., 65536.]),
                ('tiny', [-2**-126, -2**-149, -0., 0., 2**-149, 2**-126, .5, 1.])):
            rng = random.Random(11200 + w*100 + h)
            pixels = b''.join(struct.pack('<4f', *[rng.choice(values) for _ in range(4)])
                              for _ in range(w*h))
            for family in (1, 2):
                for index, controls in enumerate((
                        {4: 4}, {4: 7, 10: 3, 6: 2, 12: 4},
                        {4: 4, 7: 25, 13: 50},
                        {4: 7, 10: 3, 22: 25, 24: 25, 25: 2, 27: 89, 28: 31, 29: 7})):
                    changes = dict(controls)
                    changes.update({1: family, 15: index%2, 17: 1 if index<3 else 2.25,
                                    18: 0 if index<3 else -721, 20: 1})
                    params = adapter.defaults(w, h)
                    for p in params:
                        if p['slot'] in changes: p['value'] = changes[p['slot']]
                    yield dict(geometry=[w,h], depth=32, profile=profile, parameters=params,
                               pixels=pixels, input_padding=0, output_padding=0)


if __name__=='__main__':
    # Keep the broad, rejected matrix reproducible as well as the admitted one.
    ALL_DEPTHS='--all-depths' in sys.argv
    if ALL_DEPTHS:sys.argv.remove('--all-depths')
    FINITE_INPUTS='--finite-inputs' in sys.argv
    if FINITE_INPUTS:sys.argv.remove('--finite-inputs')
    verify.independent_cases=cases
    raise SystemExit(verify.main())
