"""KiraKira public owner; keep the recovered raw-fixed Rotation mapping."""
import random
from core import case_seed
from .public import PublicAdapter, ROOT, replace_once

HOST = ROOT/'tools/emulation/olmkirakira_public_smart_bounded_closure_harness_20260812.cpp'
MAIN = ROOT/'tools/fuzz/harnesses/kirakira_main.cpp'
PARAMETERS = ROOT/'tools/fuzz/harnesses/parameters.hpp'
SOURCE = ROOT/'mac/OLMKiraKira/OLMKiraKira.cpp'


class Adapter(PublicAdapter):
    name = 'olmkirakira'
    aex_name = 'OLMKiraKira'
    output_format = 'raw'
    small_controls = (10,16,22,28,34)

    def generate(self, seed, index):
        case = super().generate(seed,index)
        rng = random.Random(case_seed(seed,index)^0x4141)
        if rng.random()<.85:
            for p in case['parameters']:
                if p['slot'] in self.small_controls:
                    p['value'] = rng.randint(1,15) if rng.random()<.25 else 0
                if p['slot']==40:
                    # Existing exported-owner helper: native raw fixed integer
                    # is consumed as degrees, Mac stores the resulting degrees.
                    p['value'] = rng.choice([0,1,22,90,180,359])/65536
        return case

    def build(self, scratch, deadline):
        body = HOST.read_text().split('template <class Pixel> static void set_pixel',1)[0]
        body = '#define KIRA_SOURCE "'+str(SOURCE)+'"\n'+body
        body = replace_once(body,'#include KIRA_STRINGS_SOURCE','')
        body = body.replace('request->rect.right == 5 && request->rect.bottom == 3',
                            'request->rect.right == state->input->width && request->rect.bottom == state->input->height')
        body = body.replace('{0, 0, 5, 3}','{0, 0, state->input->width, state->input->height}')
        body = body.replace('result->ref_width = 5;','result->ref_width = state->input->width;')
        body = body.replace('result->ref_height = 3;','result->ref_height = state->input->height;')
        body += '\n#include "'+str(PARAMETERS)+'"\n'+MAIN.read_text()
        return self.compile_sdk(scratch,body,SOURCE,deadline),[HOST,MAIN,PARAMETERS,SOURCE,SOURCE.with_suffix('.h')]

    def scope(self):
        return {'rotation':'Original ANGLE raw fixed integer consumed as degrees; Mac float degree value follows retained exported-owner helper',
                'ramps':'Existing default three-stop handles only; custom arbitrary ramps outside this adapter',
                'builder_anomalies':'Brightness Gain default 0.10000000149011612 is below declared min 1; sampling/shrinking default clamped to legal 1. Blur Mode samples declared 1..3 only.'}

    def candidate_command(self, case, directory, route):
        config = directory/'params.txt';lines = []
        for p in case['parameters']:
            kind,value = p['kind'],p['value']
            if p['slot']==40:
                kind,value = 's',round(value*65536)
            lines.append(f"{p['slot']} {kind} "+(' '.join(map(str,value)) if isinstance(value,list) else str(value))+'\n')
        config.write_text(''.join(lines))
        return [self.binary,*case['geometry'],case['depth'],route,config,
                case['input_padding'],case['output_padding']],case['pixels']
