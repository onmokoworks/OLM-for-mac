"""ColorKey: original typed-control serializer and real-SDK public replay host."""
import copy
import random
import struct
from core import case_seed
from .public import PublicAdapter, ROOT, replace_once
from .color_triage import ColorTriage

HOST = ROOT/'tools/emulation/colorkey_thin_public_host_20261001.hpp'
HARNESS = ROOT/'tools/emulation/colorkey_typed_controls_harness_20261001.cpp'
SOURCE = ROOT/'mac/OLMColorKey/OLMColorKey.cpp'


class Adapter(ColorTriage, PublicAdapter):
    name = 'olmcolorkey'
    aex_name = 'OLMColorKey'
    output_format = 'raw'
    small_controls = (18,)

    def generate(self, seed, index):
        case = super().generate(seed,index)
        rng = random.Random(case_seed(seed,index)^0xc0102)
        params = {p['slot']:p for p in case['parameters']}
        # Sparse sampling among 217 controls otherwise almost never exercises
        # the global classifier. Mix full-range global controls with palettes.
        count = rng.choice([0,1,1,2,4,5,24,25])
        params[22]['value'] = count
        for slot in rng.sample([1,2,4,5,6,7,8,9,10,11,14,15,18,19,20,23],rng.randint(1,5)):
            p = params[slot];d = next(d for d in self.controls if d['slot']==slot)
            lo,hi = d['valid_min'],d['valid_max']
            p['value'] = rng.randint(int(lo),int(hi)) if p['kind'] in ('i','u','b') else rng.choice([lo,hi,rng.uniform(lo,hi)])
        for i in range(count):
            params[24+8*i]['value'] = rng.randrange(2)
            params[25+8*i]['value'] = rng.randrange(2)
            if rng.random()<.7:
                params[26+8*i]['value'] = [rng.choice([0,128,255]),*[rng.randrange(256) for _ in range(3)]]
        # Independent matching and nonmatching pixels, including alpha endpoints.
        if count and rng.random()<.5:
            data = bytearray(case['pixels']); ps = case['depth']//8*4
            palette = [params[26+8*i]['value'] for i in range(count)]
            for at in range(0,len(data),ps):
                if rng.random()<.4:
                    pixel = rng.choice(palette)
                    raw = bytes(pixel) if case['depth']==8 else struct.pack('<4H',*((v*32768+127)//255 for v in pixel)) if case['depth']==16 else struct.pack('<4f',*(v/255 for v in pixel))
                    data[at:at+ps] = raw
            case['pixels'] = bytes(data)
        return case

    def build(self, scratch, deadline):
        header = HOST.read_text().replace('../../mac/OLMColorKey/OLMColorKey.cpp',str(SOURCE))
        body = HARNESS.read_text()
        for old,new in [('argc != 6','argc != 7'),('rb = w * ps + 8','rb = w * ps + atoi(argv[6])'),
            ('count < 1','count < 0')]:
            body = replace_once(body,old,new)
        body = replace_once(body,
            'if (input != before || state.acquire != 2 || state.release != 2 || state.world_calls != 2 || state.color_calls != 2 * count) return 102;',
            'if (input != before || state.acquire != state.release || state.param_checkout != state.param_checkin || '
            '(!err && (state.acquire != 2 || state.world_calls != 2 || state.color_calls != 2 * count))) return 102;')
        # Early public refusals need balanced callbacks, not successful-call counts.
        # Existing helper requires one shared padded stride; record that limit.
        header = replace_once(header,'in_data.inter.checkout_param = CheckoutParam;',
            'in_data.width=state->input->width; in_data.height=state->input->height;\n'
            '    in_data.current_time=0; in_data.time_step=1; in_data.time_scale=24;\n'
            '    in_data.inter.checkout_param = CheckoutParam;')
        return self.compile_sdk(scratch,header+body,SOURCE,deadline),[HOST,HARNESS,SOURCE,SOURCE.with_suffix('.h'),ROOT/'core/x86_float.h']

    def scope(self):
        return dict(super().scope(), **{'mac_stride':'shared randomly padded input/output stride from existing ColorKey helper',
                'palette':'all 25 declarations supplied; counts include 0/1/2/4/5/24/25; mixed matching pixels'})

    def candidate(self, case, directory, route, deadline):
        # ColorTriage owns candidate execution, so the shared PublicAdapter
        # geometry environment setup is not reached through this MRO.
        if 'downsample' not in case:
            return super().candidate(case, directory, route, deadline)
        invocation = copy.copy(self)
        invocation.env = dict(self.env)
        values = [*case['full_geometry'], *case['downsample'][0], *case['downsample'][1]]
        invocation.env['OLM_F52_DOWNSAMPLE'] = ','.join(map(str, values))
        return ColorTriage.candidate(invocation, case, directory, route, deadline)

    def candidate_command(self, case, directory, route):
        # Same configuration format as typed_controls.config_text.
        config = directory/'params.txt'
        config.write_text(''.join(f"{p['slot']} c "+' '.join(map(str,p['value']))+'\n' if p['kind']=='c'
                                  else f"{p['slot']} s {p['value']}\n" for p in case['parameters']))
        pad = case['input_padding'];w,h = case['geometry'];active = w*case['depth']//8*4
        data = b''.join(case['pixels'][y*active:(y+1)*active]+bytes([0xa5])*pad for y in range(h))
        return [self.binary,w,h,case['depth'],int(route=='smart'),config,pad],data
