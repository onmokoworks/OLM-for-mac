"""Optional diagnostics shared only by the two T12 color adapters."""
import os
import re

from core import command


class ColorTriage:
    def compile_sdk(self, scratch, body, source, deadline, cores=()):
        if os.environ.get('OLM_COLOR_TRIAGE_BYPASS') == '1':
            macro = 'COLORKEEP' if self.name == 'colorkeep' else 'COLORKEY'
            body = f'#define OLM_{macro}_EXPERIMENT_BYPASS 1\n' + body
        # Independent host-side control for the suspected float-world flag bug.
        if self.name == 'colorkeep' and os.environ.get('OLM_COLOR_TRIAGE_HOST_FLAGS') == '1':
            old = 'iw.world_flags=depth==8?0:PF_WorldFlag_DEEP;'
            if body.count(old) != 1:
                raise ValueError('ColorKeep host flag anchor drift')
            body = body.replace(old, 'iw.world_flags=depth==16?PF_WorldFlag_DEEP:0;')
        return super().compile_sdk(scratch, body, source, deadline, cores)

    def compile(self, argv, deadline):
        if str(argv[0]) == 'clang++' and os.environ.get('OLM_COLOR_TRIAGE_SANITIZE') == '1':
            argv = [a for a in argv if a != '-O2'] + [
                '-O1', '-g', '-fsanitize=address,undefined', '-fno-omit-frame-pointer']
        return super().compile(argv, deadline)

    def scope(self):
        return dict(super().scope(), triage={
            'trace': os.environ.get('OLM_COLOR_TRIAGE_NO_TRACE') != '1',
            'bypass': os.environ.get('OLM_COLOR_TRIAGE_BYPASS') == '1',
            'sanitizers': os.environ.get('OLM_COLOR_TRIAGE_SANITIZE') == '1',
            'host_flags_control': os.environ.get('OLM_COLOR_TRIAGE_HOST_FLAGS') == '1'})

    def candidate(self, case, directory, route, deadline):
        argv, data = self.candidate_command(case, directory, route)
        trace = directory / f'refusal_{route}.txt'
        trace.unlink(missing_ok=True)
        env = dict(self.env)
        if os.environ.get('OLM_COLOR_TRIAGE_NO_TRACE') != '1':
            env['OLM_REFUSAL_TRACE'] = str(trace)
        status, out, err = command(argv, data=data, timeout=self.timeout, deadline=deadline, env=env)
        guards = trace.read_text().splitlines() if trace.exists() else []
        trace.unlink(missing_ok=True)
        stderr = err.decode(errors='replace')
        diagnostics = [line for line in stderr.splitlines()
                       if 'runtime error:' in line or 'ERROR: AddressSanitizer' in line
                       or 'SUMMARY:' in line]
        if status['status'] != 'ok':
            result, raw = dict(status, diagnostic=stderr[-1600:]), b''
        else:
            try:
                metadata = dict(line.split(' ', 1) for line in stderr.splitlines()
                                if re.fullmatch(r'[A-Z_]+ .+', line))
                error = int(metadata['ERROR'])
                if error:
                    result, raw = {'status': 'refusal', 'error': error, 'metadata': metadata}, b''
                elif len(out) != len(case['pixels']):
                    result, raw = {'status': 'harness_error', 'diagnostic': 'output size'}, b''
                else:
                    result, raw = {'status': 'ok', 'error': 0, 'metadata': metadata}, out
            except (ValueError, KeyError) as exc:
                result, raw = {'status': 'harness_error', 'diagnostic': repr(exc)}, b''
        if diagnostics:
            result['sanitizer'] = diagnostics
        return result, raw, guards
