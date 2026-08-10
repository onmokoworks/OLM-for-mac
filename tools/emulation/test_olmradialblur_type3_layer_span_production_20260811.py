#!/usr/bin/env python3
"""Compare the internal Type-3 composer with all six actual-AEX span rows."""
from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "mac/OLMRadialBlur/OLMRadialBlur.cpp"
EVIDENCE = ROOT / "refs/conformance/olmradialblur_type3_layer_span_actual_aex_20260811.json"


def run() -> dict:
    evidence = json.loads(EVIDENCE.read_text())
    production_source = SOURCE.read_text()
    assert "noise_variation_normalized" in production_source
    assert "info.noise_variation * 0.01f" in production_source
    assert "not admitted until" in production_source
    assert "PF32 special values" not in evidence.get("scope", "")
    expected = {(r["depth"], r["noise_variation"]): r["span_words"] for r in evidence["rows"]}
    arrays = "\n".join(
        f"static const unsigned E{d}_{nv}[6]={{{','.join(str(v)+'u' for v in words)}}};"
        for (d, nv), words in sorted(expected.items()))
    source = str(SOURCE).replace("\\", "\\\\").replace('"', '\\"')
    cpp = f'''#define OLM_RADIALBLUR_TEST_SEAM 1
#include "{source}"
#include <cstdint>
#include <cstring>
#include <vector>
{arrays}
template<class P> static void set(P& p,float a,float r,float g,float b){{
 if constexpr(std::is_same<P,PF_Pixel8>::value){{p.alpha=(A_u_char)(a*255+.5f);p.red=(A_u_char)(r*255+.5f);p.green=(A_u_char)(g*255+.5f);p.blue=(A_u_char)(b*255+.5f);}}
 else if constexpr(std::is_same<P,PF_Pixel16>::value){{p.alpha=(A_u_short)(a*32768+.5f);p.red=(A_u_short)(r*32768+.5f);p.green=(A_u_short)(g*32768+.5f);p.blue=(A_u_short)(b*32768+.5f);}}
 else {{p.alpha=a;p.red=r;p.green=g;p.blue=b;}}
}}
template<class P> static int one(short depth,int nv,const unsigned* expected){{
 constexpr int W=3,H=2,PAD=19; const int rb=W*sizeof(P)+PAD;
 std::vector<unsigned char> backing((size_t)rb*H,0xD7); P vals[6];
 set(vals[0],.5f,.75f,.25f,1.f);set(vals[1],1.f,.125f,.5f,.875f);set(vals[2],.25f,1.f,.5f,0.f);
 set(vals[3],.75f,.25f,1.f,.5f);set(vals[4],1.f,.9f,.1f,.4f);set(vals[5],0.f,1.f,1.f,1.f);
 for(int y=0;y<H;y++)std::memcpy(backing.data()+(size_t)y*rb,vals+y*W,W*sizeof(P));
 PF_EffectWorld input{{}},layer{{}};input.width=layer.width=W;input.height=layer.height=H;
 input.extent_hint.left=10;input.extent_hint.top=20;layer.extent_hint.left=11;layer.extent_hint.top=21;
 layer.data=(PF_PixelPtr)backing.data();layer.rowbytes=rb;
 float sizes[6]={{.25f,.5f,.75f,1.f,.625f,.375f}},a[6],b[6];
 if(OLMRadialBlurTestComposeType3LayerSpan(&input,&layer,depth,nv/100.f,1,0.f,3.f,sizes,a,6))return 10+depth;
 if(OLMRadialBlurTestComposeType3LayerSpan(&input,&layer,depth,nv/100.f,(A_long)0xdeadbeef,-17.25f,99.f,sizes,b,6))return 20+depth;
 if(std::memcmp(a,b,sizeof(a))||std::memcmp(a,expected,sizeof(a)))return 30+depth+nv;
 for(int y=0;y<H;y++)for(int i=W*sizeof(P);i<rb;i++)if(backing[(size_t)y*rb+i]!=0xD7)return 90;
 return 0;
}}
int main(){{int e=0;
 e|=one<PF_Pixel8>(8,25,E8_25);e|=one<PF_Pixel8>(8,100,E8_100);
 e|=one<PF_Pixel16>(16,25,E16_25);e|=one<PF_Pixel16>(16,100,E16_100);
 e|=one<PF_PixelFloat>(32,25,E32_25);e|=one<PF_PixelFloat>(32,100,E32_100);
 return e;
}}
'''
    with tempfile.TemporaryDirectory(prefix="radial-type3-production-") as raw:
        td = Path(raw); src = td / "probe.cpp"; exe = td / "probe"; src.write_text(cpp)
        command = ["xcrun", "clang++", "-std=c++17", "-O2", "-fno-fast-math", "-ffp-contract=off",
                   "-D__MACH__", "-Wno-pragma-pack", "-I.", "-IHeaders", "-IHeaders/SP", "-IUtil",
                   "-IResources", str(src), "mac/OLMRadialBlur/OLMRadialBlur_Strings.cpp",
                   "Util/AEGP_SuiteHandler.cpp", "Util/MissingSuiteError.cpp", "-framework", "Cocoa",
                   "-o", str(exe)]
        built = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
        assert built.returncode == 0, built.stderr
        executed = subprocess.run([str(exe)], cwd=ROOT, capture_output=True, text=True)
        assert executed.returncode == 0, (executed.returncode, executed.stderr)
    return {"status": "exact", "rows": 6, "depths": [8, 16, 32],
            "noise_variation": [25, 100], "padding_bytes_per_row": 19,
            "controls_invariant": ["seed", "noise_offset", "thickness"],
            "noise_variation_input": "normalized 0.25/1.0, not UI 25/100",
            "special_values_admitted": False,
            "renderworld_type3_admitted": False}


def main() -> int:
    result = run()
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
