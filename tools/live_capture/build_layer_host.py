#!/usr/bin/env python3
"""Build a separate diagnostic bundle host with one explicit Noise Layer.
Reuse the checked-in F52 host; never modify its source or retained binaries.
"""
import json,os,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
STATE=ROOT/'orchestra/state/T23-live-world-capture-radial-dblur-blur/layer-host'
SDK=Path.home()/'Documents/After Effects SDK/ae25.2_20.64bit.AfterEffectsSDK/AfterEffectsSDK/Examples'

def build():
    STATE.mkdir(parents=True,exist_ok=True)
    base=ROOT/'tools/emulation/aexcompat_patches'
    bridge='#include <fstream>\n'+(base/'F47d-native-bridge.cpp').read_text()
    def replace(old,new):
        nonlocal bridge
        assert bridge.count(old)==1,old
        bridge=bridge.replace(old,new)
    replace('if(i>0 && i<s->count && s->params[i].param_type==PF_Param_LAYER) { *out={}; return PF_Err_BAD_CALLBACK_PARAM; }', '''if(i>0 && i<s->count && s->params[i].param_type==PF_Param_LAYER) {
  if(!out || !r || id!=i || !s->params[i].u.ld.data) return fail("noise pre");
  const auto &w=s->params[i].u.ld; *out={}; out->result_rect=out->max_result_rect=w.extent_hint;
  out->ref_width=w.width; out->ref_height=w.height; return 0;
 }''')
    replace('if(id>0 && id<s->count && s->params[id].param_type==PF_Param_LAYER && w) { *w=nullptr; return PF_Err_BAD_CALLBACK_PARAM; }', 'if(id>0 && id<s->count && s->params[id].param_type==PF_Param_LAYER && w) { *w=&s->params[id].u.ld; return (*w)->data?0:fail("noise pixels"); }')
    replace('return id?fail("checkin_layer_pixels"):0;', 'return id && !(id>0 && id<s->count && s->params[id].param_type==PF_Param_LAYER)?fail("checkin_layer_pixels"):0;')
    replace('if(!f || (w!=s->src && w!=s->dst && w!=&s->params[0].u.ld)) return fail("GetPixelFormat");', '''bool layer=false;
 for(int i=1;i<s->count;++i) if(s->params[i].param_type==PF_Param_LAYER && w==&s->params[i].u.ld) layer=true;
 if(!f || (!layer && w!=s->src && w!=s->dst && w!=&s->params[0].u.ld)) return fail("GetPixelFormat");''')
    replace('State state{&src,&dst,params.data(),depth,count}; s=&state;', '''std::vector<unsigned char> noise;
 if(const char *noise_path=std::getenv("OLM_TEST_NOISE_FILE")) {
  const char *slot_text=std::getenv("OLM_TEST_NOISE_SLOT");
  const int slot=slot_text?std::atoi(slot_text):0;
  if(slot<=0 || slot>=count || params[slot].param_type!=PF_Param_LAYER) return 516;
  const size_t packed=size_t(src.width)*4*(depth/8);
  noise.resize(packed*src.height);
  std::ifstream file(noise_path,std::ios::binary);
  if(!file.read(reinterpret_cast<char*>(noise.data()),noise.size()) || file.peek()!=EOF) return 516;
  params[slot].u.ld=src; params[slot].u.ld.rowbytes=packed;
  params[slot].u.ld.data=reinterpret_cast<PF_Pixel*>(noise.data());
 }
 State state{&src,&dst,params.data(),depth,count}; s=&state;''')
    bridge=bridge.replace('"../../fuzz/harnesses/geometry.hpp"',json.dumps(str(ROOT/'tools/fuzz/harnesses/geometry.hpp')))
    (STATE/'bridge.cpp').write_text(bridge)
    host=(base/'F52c-plugin-host.cpp').read_text().replace('"F47d-native-bridge.cpp"','"bridge.cpp"').replace('"../../fuzz/harnesses/parameters.hpp"',json.dumps(str(ROOT/'tools/fuzz/harnesses/parameters.hpp')))
    (STATE/'host.cpp').write_text(host)
    binary=STATE/'plugin-host'
    cmd=['clang++','-std=c++17','-O2','-fno-fast-math','-ffp-contract=off','-arch','arm64','-arch','x86_64','-Wno-pragma-pack',
         '-I'+str(SDK/'Headers'),'-I'+str(SDK/'Headers/SP'),str(STATE/'host.cpp'),'-o',str(binary)]
    (STATE/'command.json').write_text(json.dumps(cmd,indent=2))
    with (STATE/'build.log').open('w') as log:
        subprocess.run(cmd,env=dict(os.environ,TMPDIR=str(STATE)),stdout=log,stderr=subprocess.STDOUT,check=True)
    return binary
if __name__=='__main__':print(build())
