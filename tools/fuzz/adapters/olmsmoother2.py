"""Smoother2: extend the retained public key/gamma replay host to Classic."""
import copy

from .public import PublicAdapter, ROOT, replace_once, geometry_shim

SOURCE = ROOT/'mac/OLMSmoother2/Mac/OLMSmoother2_port.cpp'
HARNESS = ROOT/'tools/emulation/olmsmoother2_public_key_gamma_harness_20261001.cpp'
SHIM = ROOT/'cli/OLMSmoother2/shim'


class Adapter(PublicAdapter):
    original_routes = {'classic': 'no-write', 'smart': 'render'}
    no_write_fill = 0xee
    name = 'olmsmoother2'
    geometry_samplers = ('realistic-v1',)
    aex_name = 'OLMSmoother2'
    output_format = 'hex'

    def build(self, scratch, deadline):
        (scratch/'production_under_test.cpp').write_text(SOURCE.read_text())
        shim=geometry_shim(SHIM,scratch/'geometry-shim')
        body = HARNESS.read_text().replace('#include "production_under_test.cpp"','#include "production_under_test.cpp"\n#include "'+str(ROOT/'tools/fuzz/harnesses/geometry.hpp')+'"')
        body=body.replace('PF_RenderRequest *request, A_long, A_long, A_long,','const PF_RenderRequest *request, A_long, A_long, A_u_long,')
        body = replace_once(body,'static PF_EffectWorld *source_world, *destination_world;',
                            'static bool fuzz_classic; static size_t fuzz_pad;\nstatic PF_EffectWorld *source_world, *destination_world;')
        body = replace_once(body,'const size_t pad = sizeof(Pixel) == 4 ? 5 : (sizeof(Pixel) == 8 ? 7 : 13);',
                            'const size_t pad = fuzz_pad;')
        body = replace_once(body,'    PF_PreRenderInput pre_input{};', '''    int error;
    if (fuzz_classic) {
        definitions[0].u.ld=iw;
        PF_ParamDef *params[SM_NUM_PARAMS];
        for(int i=0;i<SM_NUM_PARAMS;++i) params[i]=definitions+i;
        error=EffectMain(PF_Cmd_RENDER,&in,&out,params,&ow,nullptr);
    } else {
    PF_PreRenderInput pre_input{};''')
        body = replace_once(body,'    int error = pre_error ? pre_error : EffectMain(PF_Cmd_SMART_RENDER, &in, &out, nullptr, nullptr, &smart);',
                            '    error = pre_error ? pre_error : EffectMain(PF_Cmd_SMART_RENDER, &in, &out, nullptr, nullptr, &smart);\n    }')
        for old,new in [('argc != 5','argc != 7'),('w > 32 || h > 32','w > 4096 || h > 4096'),
            ('int w = atoi(argv[1]), h = atoi(argv[2]);',
             'int w = atoi(argv[1]), h = atoi(argv[2]); fuzz_classic=!strcmp(argv[5],"classic"); fuzz_pad=atoi(argv[6]);')]:
            body = replace_once(body,old,new)
        host = scratch/'host.cpp';host.write_text(body);binary = scratch/'mac'
        self.compile(['clang++','-std=c++17','-O2','-fno-fast-math','-ffp-contract=off',
            '-Wno-deprecated-declarations','-I',scratch,'-I',shim,'-I',SOURCE.parent,host,'-o',binary],deadline)
        return binary,[HARNESS,SOURCE,*sorted(SHIM.glob('*.h')),
                       SOURCE.parent/'OLMSmoother2_decode_lut_10000.h',SOURCE.parent/'OLMSmoother2_encode_lut_10000.h']

    def scope(self):
        return {'mac_host':'existing public key/gamma CLI SDK shim, production EffectMain; Classic added using same params/worlds',
                'mac_stride':'shared randomly padded input/output stride plus 32-byte guards'}

    def candidate_command(self, case, directory, route):
        config = directory/'params.txt'
        config.write_text(''.join(f"{p['slot']} c "+' '.join(map(str,p['value']))+'\n' if p['kind']=='c'
                                  else f"{p['slot']} s {p['value']}\n" for p in case['parameters']))
        return [self.binary,*case['geometry'],f"PF{case['depth']}",config,route,case['input_padding']],case['pixels']

    def candidate(self, case, directory, route, deadline):
        # Keep attribution outside the compared result, as in RadialBlur.
        # The trace only exists when the candidate appends a named guard; the
        # returned status and bytes are identical with or without tracing.
        trace = directory/f'refusal_trace_{route}.txt'
        trace.unlink(missing_ok=True)
        local = copy.copy(self)
        local.env = dict(self.env, OLM_REFUSAL_TRACE=str(trace))
        try:
            result, raw = PublicAdapter.candidate(local, case, directory, route, deadline)
            guards = [line.strip() for line in trace.read_text().splitlines() if line.strip()] if trace.is_file() else []
            return result, raw, guards
        finally:
            trace.unlink(missing_ok=True)
