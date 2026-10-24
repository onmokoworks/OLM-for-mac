"""OLMBlur real-SDK public replay with captured fixed Smoothness units."""
from .public import PublicAdapter, ROOT, replace_once

HOST = ROOT/'tools/emulation/probe_olmblur_smart_public_admission_20260813.cpp'
MAIN = ROOT/'tools/fuzz/harnesses/blur_main.cpp'
PARAMETERS = ROOT/'tools/fuzz/harnesses/parameters.hpp'
SOURCE = ROOT/'mac/OLMBlur/OLMBlur.cpp'
CORES = [ROOT/'core'/name for name in ('olmblur_helper.cpp','olmblur_fullworker_helper.cpp',
    'olmblur_worker16_nonlegacy.cpp','olmblur_worker16_legacy.cpp','olmblur_worker32_nonlegacy.cpp',
    'olmblur_worker32_legacy.cpp','olmblur_worker8_legacy.cpp','olmblur_worker_orchestration.cpp')]


class Adapter(PublicAdapter):
    name = 'olmblur'
    geometry_samplers = ('realistic-v1',)
    aex_name = 'OLMBlur'
    output_format = 'raw'
    small_controls = (1,)

    def build(self, scratch, deadline):
        body = HOST.read_text().split('static unsigned char *misaligned_payload',1)[0]
        body = body.replace('../../mac/OLMBlur/OLMBlur.cpp',str(SOURCE))
        body = body.replace('{0, 0, 24, 24}','{0, 0, g_input->width, g_input->height}')
        body = replace_once(body,'result->ref_width = 24; result->ref_height = 24;',
                            'result->ref_width = g_input->width; result->ref_height = g_input->height;')
        body = replace_once(body,'static_cast<size_t>(src->rowbytes));',
                            'static_cast<size_t>(src->width)*(g_depth/8*4));')
        body += '\n#include "'+str(PARAMETERS)+'"\n'+MAIN.read_text()
        return self.compile_sdk(scratch,body,SOURCE,deadline,CORES),[HOST,MAIN,PARAMETERS,SOURCE,SOURCE.with_suffix('.h'),*CORES,ROOT/'core/x86_float.h']

    def scope(self):
        return {'mac_stride':'shared randomly padded input/output stride; host copy callback copies active pixels',
                'units':'Smoothness PF_Fixed uses the retained public helper; no internal worker bypass'}

    def candidate_command(self, case, directory, route):
        config = directory/'params.txt'
        config.write_text(''.join(f"{p['slot']} {p['kind']} {p['value']}\n" for p in case['parameters']))
        return [self.binary,*case['geometry'],case['depth'],route,config,case['input_padding']],case['pixels']

    def candidate(self, case, directory, route, deadline):
        trace = directory/f'olmblur_refusal_{route}.txt'
        try:
            trace.unlink()
        except OSError:
            pass
        env = dict(self.env)
        env['OLM_REFUSAL_TRACE'] = str(trace)
        result, raw = super().candidate(case, directory, route, deadline, env=env)
        guards = []
        try:
            guards = [line.strip() for line in trace.read_text().splitlines() if line.strip()]
        except OSError:
            pass
        finally:
            try:
                trace.unlink()
            except OSError:
                pass
        return result, raw, guards
