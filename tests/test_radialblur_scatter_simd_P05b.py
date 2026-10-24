"""Bitwise scalar/SIMD scatter arithmetic, including payloads and signed zero."""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
ROOT = Path(__file__).resolve().parents[1]

class ScatterSIMD(unittest.TestCase):
    def test_bits(self):
        source = r'''
#include "mac/OLMRadialBlur/RadialScatterSIMD.h"
#include "core/x86_float.h"
#include <cstdio>
#include <cstdlib>
static float from(unsigned b) { float f; std::memcpy(&f,&b,4); return f; }
int main() {
    const unsigned edges[] = {0,0x80000000,1,0x80000001,0x007fffff,0x00800000,
        0x3f800000,0xbf800000,0x7f7fffff,0xff7fffff,0x7f800000,0xff800000,
        0x7fc00000,0xffc00000,0x7f800001,0xff800001,0x7fc01234,0xffc05678};
    unsigned state=0x505b1234, count=0;
    auto random=[&]() {state^=state<<13;state^=state>>17;state^=state<<5;return state;};
    auto check=[&](float c,float s,float a) {
        float src[4]={s,from(random()),from(random()),from(random())};
        float acc[4]={a,from(random()),from(random()),a}, expected[4];
        for(int i=0;i<3;++i) expected[i]=olm::x86_float::sse_add(
            olm::x86_float::sse_mul(c,src[i]),acc[i]);
        expected[3]=olm::x86_float::sse_add(c,acc[3]);
        olm::radial::scatter_accumulate(acc,src,c);
        for(int i=0;i<4;++i) if(olm::x86_float::bits(acc[i])!=olm::x86_float::bits(expected[i])) {
            std::printf("mismatch case %u lane %d: %08x != %08x\n",count,i,
                olm::x86_float::bits(acc[i]),olm::x86_float::bits(expected[i])); std::exit(1);
        }
        ++count;
    };
    for(auto c:edges) for(auto s:edges) for(auto a:edges) check(from(c),from(s),from(a));
    for(int i=0;i<100000;++i) check(from(random()),from(random()),from(random()));
    std::printf("%u scatter tuples exact\n",count);
}
'''
        base=ROOT/'orchestra/state/P05b-radialblur-rotation-performance'
        base.mkdir(parents=True,exist_ok=True)
        with tempfile.TemporaryDirectory(dir=base) as d:
            d=Path(d);(d/'check.cpp').write_text(source)
            env=dict(os.environ,TMPDIR=str(d),TMP=str(d),TEMP=str(d))
            subprocess.run(['clang++','-std=c++17','-O2','-fno-fast-math','-ffp-contract=off',
                            '-I'+str(ROOT),str(d/'check.cpp'),'-o',str(d/'check')],check=True,env=env)
            result=subprocess.check_output([str(d/'check')],text=True,env=env)
            self.assertEqual(result.strip(),'105832 scatter tuples exact')

if __name__=='__main__':unittest.main()
