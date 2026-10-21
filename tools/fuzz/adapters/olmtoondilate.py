"""ToonDilate: the existing same-source public Classic/Smart SDK callbacks."""
from .public import PublicAdapter, ROOT, replace_once

HOST = ROOT/'tools/emulation/probe_olmtoondilate_same_source_mac_public_20260813.cpp'
MAIN = ROOT/'tools/fuzz/harnesses/toondilate_main.cpp'
PARAMETERS = ROOT/'tools/fuzz/harnesses/parameters.hpp'
SOURCE = ROOT/'mac/OLMToonDilate/OLMToonDilate.cpp'


class Adapter(PublicAdapter):
    name = 'olmtoondilate'
    aex_name = 'OLMToonDilate'
    output_format = 'raw'
    small_controls = (1,)

    def build(self, scratch, deadline):
        body = HOST.read_text().split('static std::string sha256',1)[0]
        body = '#include "'+str(SOURCE)+'"\n'+body
        body = replace_once(body,'r->result_rect = {17, 23, 20, 25}; r->max_result_rect = {11, 13, 29, 31};',
                            'r->result_rect = {0,0,g_input->width,g_input->height}; r->max_result_rect = r->result_rect;')
        body += '\n#include "'+str(PARAMETERS)+'"\n'+MAIN.read_text()
        return self.compile_sdk(scratch,body,SOURCE,deadline),[HOST,MAIN,PARAMETERS,SOURCE,SOURCE.with_suffix('.h')]

    def scope(self):
        return {'classic_owner':'Production PF_Cmd_RENDER is an intentional successful no-op. '
                'Its untouched destination differs from the AEX Smart reference; these are cross-route differences, not kernel residuals.',
                'classic_owner_evidence':'tools/emulation/probe_olmtoondilate_actual_aex_sequence_smartpre_20260805.py: legacy_render_public_noop; original owner FUN_1801a7840 constant-zero stub'}

    def candidate_command(self, case, directory, route):
        config = directory/'params.txt'
        config.write_text(''.join(f"{p['slot']} {p['kind']} {p['value']}\n" for p in case['parameters']))
        return [self.binary,*case['geometry'],case['depth'],route,config,
                case['input_padding'],case['output_padding']],case['pixels']
