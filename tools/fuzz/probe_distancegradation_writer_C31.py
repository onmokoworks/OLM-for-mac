#!/usr/bin/env python3
"""Original PF16 CVTTSS2SI/word-store candidate and independent HDR matrix."""
import struct
from adapters.public import replace_once


def writer_source(source, census=True):
    source=replace_once(source,'static inline PF_Pixel16 compose_pf16_pixel(','''// Original Smart PF16 callback 1811707f4..181170828 multiplies by
// 32768, converts to signed int32 with CVTTSS2SI, then stores AX. The
// integer-indefinite result for invalid conversion has a zero low word.
static inline u_short smart_store_pf16(float value)
{
\tconst float scaled = value * 32768.0f;
\tif (!(scaled >= -2147483648.0f && scaled < 2147483648.0f)) return 0;
\treturn static_cast<u_short>(static_cast<int32_t>(scaled));
}

static inline PF_Pixel16 compose_pf16_pixel(''')
    for field,arg in [('alpha','oa'),('red','orv'),('green','og'),('blue','ob')]:
        old=f'out.{field}'+(' '*(6-len(field)))+f'= clamp16({arg});'
        new=old.replace(f'clamp16({arg})',f'p.smart_owner ? smart_store_pf16({arg}) : clamp16({arg})')
        source=replace_once(source,old,new)
    if census:
        source=replace_once(source,
            '(bounded_alpha || (smart_owner && sizeof(P) == sizeof(PF_PixelFloat)))',
            '(bounded_alpha || smart_owner)')
    return source


def matrix(a):
    for profile in ('mixed-hdr','rgb-hdr','uniform-hdr'):
      for w,h in ((7,1),(7,3)):
       for owner in (1,2,3):
        for mode in (1,2):
         for bg in (0,1):
          for interp in (1,2,3,4):
           for blur,size in ((1,0),(2,2),(3,1)):
            alphas=(0,191,192,193,32768,65535,32769,1,0,65534,32767)
            colors=(0,1,32767,32768,32769,65534,65535)
            pixels=[]
            for y in range(h):
              for x in range(w):
                al=alphas[(x+3*y)%len(alphas)]
                if profile=='rgb-hdr':al=min(al,32768)
                if profile=='uniform-hdr':al=65535
                pixels.append(struct.pack('<4H',al,*[colors[(x+2*y+ch)%len(colors)] for ch in (0,2,4)]))
            c=dict(geometry=[w,h],depth=16,profile=profile,pixels=b''.join(pixels),parameters=a.defaults(w,h),input_padding=3,output_padding=5)
            values={1:(owner+bg)%2,2:owner,3:4,4:3,5:mode,6:bg,7:[255,28,53,238],8:[255,16,160,48],9:interp,10:2.25,11:blur,12:size}
            for q in c['parameters']:
                if q['slot'] in values:q['value']=values[q['slot']]
            yield f'{profile}/{w}x{h}/owner{owner}/mode{mode}/bg{bg}/interp{interp}/blur{blur}',c
