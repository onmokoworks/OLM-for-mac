"""Smoother v1: retained public admission host and original three controls."""
from .public import PublicAdapter, ROOT, replace_once

HOST = ROOT/'tools/emulation/olmsmoother_v1_public_guard_harness_20260812.cpp'
MAIN = ROOT/'tools/fuzz/harnesses/smoother_main.cpp'
SOURCE = ROOT/'mac/OLMSmoother/Mac/OLMSmoother_port.cpp'
SHIM = ROOT/'cli/OLMSmoother/shim'


class Adapter(PublicAdapter):
    name = 'olmsmoother'
    aex_name = 'OLMSmoother'
    output_format = 'raw'
    oracle_route = None  # Original v1 advertises Classic only; use worker auto.
    oracle_path = 'classic'
    oracle_routes = {'classic': 'classic', 'smart': 'classic'}
    original_routes = {'classic': 'render', 'smart': 'absent; Mac Smart wrapper is explicitly compared to original Classic'}

    def build(self, scratch, deadline):
        body = HOST.read_text().split('static unsigned short Widen',1)[0]
        body = replace_once(body,'../../mac/OLMSmoother/Mac/OLMSmoother_port.cpp',str(SOURCE))
        body += '\n'+MAIN.read_text()
        host = scratch/'host.cpp';host.write_text(body);binary = scratch/'mac'
        self.compile(['clang++','-std=c++17','-O2','-fno-fast-math','-ffp-contract=off',
                      '-I',SHIM,host,'-o',binary],deadline)
        return binary,[HOST,MAIN,SOURCE,*sorted(SHIM.glob('*.h'))]

    def scope(self):
        return {'oracle_owner':'original exported PF_Cmd_RENDER, as in the v1 key/tolerance public replay helper; original has no Smart advertisement',
                'mac_host':'existing v1 public guard CLI SDK shim; exactly the three v1 controls',
                'mac_stride':'shared randomly padded input/output stride',
                'depth_limit':'PF32 is probed and retained as refusal/rejection, not promoted to supported'}

    def candidate_command(self, case, directory, route):
        config = directory/'params.txt'
        config.write_text(''.join(f"{p['slot']} {p['kind']} "+(' '.join(map(str,p['value'])) if isinstance(p['value'],list) else str(p['value']))+'\n' for p in case['parameters']))
        return [self.binary,*case['geometry'],case['depth'],route,config,case['input_padding']],case['pixels']
