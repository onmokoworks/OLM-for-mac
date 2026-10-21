"""Smoother v1: retained public admission host and original three controls."""
from core import command
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

    def candidate(self, case, directory, route, deadline):
        argv, data = self.candidate_command(case, directory, route)
        trace = directory/f'refusal_trace_{route}.txt'
        trace.unlink(missing_ok=True)
        env = dict(self.env, OLM_REFUSAL_TRACE=str(trace))
        status, raw, err = command(argv, data=data, timeout=self.timeout,
                                   deadline=deadline, env=env)
        # Optional attribution: the candidate binary appends "function:tag@line"
        # only when an admission guard refuses. The guards are returned outside
        # the compared result; status and bytes are unchanged without a trace.
        guards = []
        try:
            if trace.is_file():
                guards = [line.strip() for line in trace.read_text().splitlines() if line.strip()]
        except OSError:
            guards = []
        finally:
            trace.unlink(missing_ok=True)
        if status['status'] != 'ok':
            return dict(status, diagnostic=err.decode(errors='replace')[-1600:]), b'', guards
        try:
            metadata = dict(line.split(' ', 1) for line in err.decode().splitlines())
            error = int(metadata['ERROR'])
            if error:
                return {'status':'refusal', 'error':error, 'metadata':metadata}, b'', guards
            if len(raw) != len(case['pixels']):
                return {'status':'harness_error','diagnostic':'output size'}, b'', guards
            return {'status':'ok','error':0,'metadata':metadata}, raw, guards
        except (ValueError, KeyError) as exc:
            return {'status':'harness_error','diagnostic':repr(exc)}, b'', guards
