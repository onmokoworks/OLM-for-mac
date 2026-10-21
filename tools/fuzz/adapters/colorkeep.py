"""ColorKeep public covering host, with arbitrary legal palettes and geometry."""
import random
import struct
from core import case_seed
from .public import PublicAdapter, ROOT, replace_once

HOST = ROOT/'tools/emulation/test_colorkeep_installed_public_covering_matrix_20260812.py'
MAIN = ROOT/'tools/fuzz/harnesses/colorkeep_main.cpp'
PARAMETERS = ROOT/'tools/fuzz/harnesses/parameters.hpp'
SOURCE = ROOT/'mac/ColorKeep/ColorKeep.cpp'


class Adapter(PublicAdapter):
    name = 'colorkeep'
    aex_name = 'ColorKeep'
    output_format = 'raw'

    def generate(self, seed, index):
        case = super().generate(seed,index)
        rng = random.Random(case_seed(seed,index)^0xc010)
        case['parameters'][0]['value'] = rng.choice([1,4,5,99,100,rng.randint(1,100)])
        palette = [p['value'] for p in case['parameters'][1:]]
        if rng.random()<.7:
            # Mix actual palette members, inactive members and independent colors.
            ps = case['depth']//8*4;data = bytearray(case['pixels'])
            for at in range(0,len(data),ps):
                if rng.random()<.5:
                    pixel = rng.choice(palette)
                    data[at:at+ps] = bytes(pixel) if case['depth']==8 else struct.pack('<4H',*((v*32768+127)//255 for v in pixel)) if case['depth']==16 else struct.pack('<4f',*(v/255 for v in pixel))
            case['pixels'] = bytes(data)
        return case

    def build(self, scratch, deadline):
        text = HOST.read_text()
        header = text.split("    code = r'''",1)[1].split("''' +",1)[0]
        prefix = 'template<class P,class F> static PF_Err iter'
        callbacks = prefix+text.split(prefix,1)[1].split('template<class P>static bool run',1)[0]
        old = 'static PF_Err color(PF_ProgPtr,const PF_ParamDef*p,PF_PixelFloat*out){int n=p->u.cd.value.red;if(n<0||n>=100)return 91;std::memcpy(out,colors+n*16,16);return 0;}'
        callbacks = replace_once(callbacks,old,
            'static PF_Err color(PF_ProgPtr,const PF_ParamDef*p,PF_PixelFloat*out){'
            'out->alpha=p->u.cd.value.alpha/255.0f;out->red=p->u.cd.value.red/255.0f;'
            'out->green=p->u.cd.value.green/255.0f;out->blue=p->u.cd.value.blue/255.0f;return 0;}')
        callbacks = replace_once(callbacks,
            'std::memset(p,0,sizeof(*p));if(checks<101)order[checks]=n;checks++;if(n==1)p->u.sd.value=gcount;else if(n>=2&&n<102)p->u.cd.value.red=n-2;else return 93;return 0;',
            'if(n<1||n>=102)return 93;checks++;*p=fuzz_defs[n];return 0;')
        callbacks = replace_once(callbacks,'o->result_rect={0,0,11,7};',
                                'o->result_rect={0,0,gin->width,gin->height};')
        body = '#include "'+str(SOURCE)+'"\n#include <vector>\n'+header
        body += '\nstatic PF_ParamDef fuzz_defs[102];\n'+callbacks
        body += '\n#include "'+str(PARAMETERS)+'"\n'+MAIN.read_text()
        return self.compile_sdk(scratch,body,SOURCE,deadline),[HOST,MAIN,PARAMETERS,SOURCE,SOURCE.with_suffix('.h')]

    def scope(self):
        return {'palette':'all 100 public colors supplied; counts 1/4/5/99/100 and random 1..100; mixed palette-member pixels',
                'mac_host':'retained real-SDK public covering host callbacks, linked to worktree production EffectMain'}

    def candidate_command(self, case, directory, route):
        config = directory/'params.txt'
        config.write_text(''.join(f"{p['slot']} {p['kind']} "+(' '.join(map(str,p['value'])) if isinstance(p['value'],list) else str(p['value']))+'\n' for p in case['parameters']))
        return [self.binary,*case['geometry'],case['depth'],route,config,
                case['input_padding'],case['output_padding']],case['pixels']
