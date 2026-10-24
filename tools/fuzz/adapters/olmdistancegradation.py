"""DistanceGradation public owner contract host; no field/helper bypass."""
import copy
import shutil

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
    geometry_samplers = ('realistic-v1','realistic-v2')
    aex_name = 'DistanceGradation'
    output_format = 'raw'
    small_controls = (3,4,12)

    def build(self, scratch, deadline):
        shim=scratch/'geometry-shim.h'
        text=SHIM.read_text().replace('A_long origin_x, origin_y;','A_long origin_x, origin_y;\n    struct { A_long num,den; } pix_aspect_ratio;')
        text=text.replace('struct PF_InData {','struct PF_InData {\n    PF_LRect extent_hint;\n    struct { A_long num,den; } pixel_aspect_ratio;')
        text=text.replace('struct PF_CheckoutResult {','typedef A_long PF_ParamIndex;\nstruct PF_CheckoutResult { struct { A_long num,den; } par;')
        text=text.replace('PF_RenderRequest *, A_long, A_long, A_long,','const PF_RenderRequest *, A_long, A_long, A_u_long,')
        text=text.replace('struct PF_SmartRenderInput { short bitdepth; void *pre_render_data;','struct PF_SmartRenderInput { short bitdepth; void *pre_render_data; PF_RenderRequest output_request;')
        shim.write_text(text)
        shimdir=scratch/'geometry-shim';shimdir.mkdir(exist_ok=True)
        for p in SHIM_DIR.glob('*.h'):
            (shimdir/p.name).write_text(p.read_text().replace('../dg_renderbits_real_harness_20260716_sdk_shim.h',str(shim)))
        body = HOST.read_text().split('void set_params(',1)[0]
        body = replace_once(body,'"dg_renderbits_real_harness_20260716_sdk_shim.h"','"'+str(shim)+'"')
        body = replace_once(body,'../../mac/OLMDistanceGradation/OLMDistanceGradation.cpp',str(SOURCE))
        body = replace_once(body,'constexpr int W = 17, H = 11, PAD = 16;','int W,H;')
        body = replace_once(body,'result->max_result_rect = {0, 0, W, H};',
                            'result->max_result_rect = {0, 0, W, H};\n\tresult->ref_width = W; result->ref_height = H;')
        body += '\n} // namespace\n#include "'+str(PARAMETERS)+'"\n'+MAIN.read_text()
        body=body.replace('PF_RenderRequest *,\n\tA_long, A_long, A_long,','const PF_RenderRequest *,\n\tA_long, A_long, A_u_long,')
        body=self.geometry_host(body)
        host = scratch/'host.cpp';host.write_text(body);binary = scratch/'mac'
        self.compile(['clang++','-std=c++17','-O2','-fno-fast-math','-ffp-contract=off',
                      '-I',shimdir,host,FIELDGEN,'-o',binary],deadline)
        return binary,[HOST,SHIM,*sorted(SHIM_DIR.glob('*.h')),MAIN,PARAMETERS,SOURCE,SOURCE.with_suffix('.h'),FIELDGEN,FIELDGEN.with_suffix('.h')]

    def real_defaults(self, w, h):
        """Captured PARAMS_SETUP values, including the In/Out=0 builder state.

        Explicit P04a corpus cases serialize these parameters and input bytes;
        ordinary historical seeded generation remains unchanged.
        """
        params = self.defaults(w, h)
        for p, declaration in zip(params, self.controls):
            if p["kind"] not in ("a", "p", "c"):
                value = declaration["default_value"]
                p["value"] = int(value) if p["kind"] in ("i", "u", "b") else value
        return params

    def scope(self):
        return {'mac_host':'existing public owner contract SDK shim; O2 strict floating-point production EffectMain',
                'host_checkout_reference':'fuzz scratch host fills checkout ref_width/ref_height from the layer geometry',
                'builder_anomalies':'In/Out builder default 0 lies outside 1..3; sampling/shrinking default is legal 1; real_defaults preserves captured values for explicit P04a corpus'}

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
