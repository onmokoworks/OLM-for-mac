"""DistanceGradation public owner contract host; no field/helper bypass."""
import copy

from .public import PublicAdapter, ROOT, replace_once

HOST = ROOT/'tools/emulation/dg_public_smart_owner_contract_harness_20260812.cpp'
SHIM = ROOT/'tools/emulation/dg_renderbits_real_harness_20260716_sdk_shim.h'
SHIM_DIR = ROOT/'tools/emulation/dg_renderbits_real_harness_20260716'
MAIN = ROOT/'tools/fuzz/harnesses/distancegradation_main.cpp'
PARAMETERS = ROOT/'tools/fuzz/harnesses/scalar_color_parameters.hpp'
SOURCE = ROOT/'mac/OLMDistanceGradation/OLMDistanceGradation.cpp'
FIELDGEN = ROOT/'core/olmdistancegradation_fieldgen.cpp'


class Adapter(PublicAdapter):
    name = 'olmdistancegradation'
    aex_name = 'DistanceGradation'
    output_format = 'raw'
    small_controls = (3,4,12)

    def build(self, scratch, deadline):
        body = HOST.read_text().split('void set_params(',1)[0]
        body = replace_once(body,'"dg_renderbits_real_harness_20260716_sdk_shim.h"','"'+str(SHIM)+'"')
        body = replace_once(body,'../../mac/OLMDistanceGradation/OLMDistanceGradation.cpp',str(SOURCE))
        body = replace_once(body,'constexpr int W = 17, H = 11, PAD = 16;','int W,H;')
        body += '\n} // namespace\n#include "'+str(PARAMETERS)+'"\n'+MAIN.read_text()
        host = scratch/'host.cpp';host.write_text(body);binary = scratch/'mac'
        self.compile(['clang++','-std=c++17','-O2','-fno-fast-math','-ffp-contract=off',
                      '-I',SHIM_DIR,host,FIELDGEN,'-o',binary],deadline)
        return binary,[HOST,SHIM,*sorted(SHIM_DIR.glob('*.h')),MAIN,PARAMETERS,SOURCE,SOURCE.with_suffix('.h'),FIELDGEN,FIELDGEN.with_suffix('.h')]

    def scope(self):
        return {'mac_host':'existing public owner contract SDK shim; O2 strict floating-point production EffectMain',
                'builder_anomalies':'In/Out builder default 0 lies outside 1..3; sampling/shrinking default is legal 1'}

    def candidate_command(self, case, directory, route):
        config = directory/'params.txt'
        config.write_text(''.join(f"{p['slot']} {p['kind']} "+(' '.join(map(str,p['value'])) if isinstance(p['value'],list) else str(p['value']))+'\n' for p in case['parameters']))
        return [self.binary,*case['geometry'],case['depth'],route,config,
                case['input_padding'],case['output_padding']],case['pixels']

    def candidate(self, case, directory, route, deadline):
        # Keep attribution outside the compared result, as in RadialBlur.
        trace = directory/f'refusal_trace_{route}.txt'
        trace.unlink(missing_ok=True)
        local = copy.copy(self)
        local.env = dict(self.env, OLM_REFUSAL_TRACE=str(trace))
        try:
            result, raw = PublicAdapter.candidate(local, case, directory, route, deadline)
            guards = trace.read_text().splitlines() if trace.is_file() else []
            return result, raw, guards
        finally:
            trace.unlink(missing_ok=True)
