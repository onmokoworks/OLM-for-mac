"""DirectionalBlur: reuse the existing real-SDK public feature replay host."""
import copy

from .public import PublicAdapter, ROOT, replace_once

HARNESS = ROOT/'tools/emulation/directionalblur_general_features_effectmain_harness_20261001.cpp'
SOURCE = ROOT/'mac/OLMDirectionalBlur/OLMDirectionalBlur.cpp'
CORES = [ROOT/'core'/n for n in ('dblur_frontonly.cpp','dblur_rotate.cpp','dblur_rowdriver.cpp','dblur_field.cpp')]


class Adapter(PublicAdapter):
    name = 'olmdirectionalblur'
    # T15 qualifies transport; numerical ROI failures remain recorded separately.
    geometry_samplers = ('realistic-v1',)
    aex_name = 'OLMDirectionalBlur'
    small_controls = (5,10)
    output_format = 'hex'

    def build(self, scratch, deadline):
        body = HARNESS.read_text().replace('../../mac/OLMDirectionalBlur/OLMDirectionalBlur.cpp',str(SOURCE))
        for old,new in [('argc!=6','argc!=8'),('w>64||h>64','w>4096||h>4096'),
            ('(depth!=16&&depth!=32)','(depth!=8&&depth!=16&&depth!=32)'),
            ('ps=depth==16?8:16','ps=depth==8?4:depth==16?8:16'),
            ('irb=active+5,orb=active+11','irb=active+atoi(argv[6]),orb=active+atoi(argv[7])'),
            ('state.format=depth==16?','state.format=depth==8?PF_PixelFormat_ARGB32:depth==16?'),
            ('in.current_time = 7','in.current_time = 0')]:
            body = replace_once(body,old,new)
        body = self.geometry_host(body)
        path = scratch/'host.cpp';path.write_text(body)
        sdk = self.compile(['xcrun','--show-sdk-path'],deadline).decode().strip()
        binary = scratch/'mac'
        self.compile(['clang++','-std=c++17','-arch','arm64','-O2','-fno-fast-math','-ffp-contract=off',
            '-Wno-deprecated-declarations','-Wno-pragma-pack','-ffunction-sections','-fdata-sections',
            '-isysroot',sdk,*[x for p in ('Headers','Headers/SP','Util','Resources') for x in ('-I',self.main/p)],
            path,SOURCE.with_name('OLMDirectionalBlur_Strings.cpp'),self.main/'Util/AEGP_SuiteHandler.cpp',
            self.main/'Util/MissingSuiteError.cpp',*CORES,'-Wl,-dead_strip','-framework','Cocoa','-o',binary],deadline)
        return binary,[HARNESS,SOURCE,SOURCE.with_suffix('.h'),*CORES]

    def candidate_command(self, case, directory, route):
        parameters = ','.join(f"{p['slot']}={p['value']}" for p in case['parameters'])
        return [self.binary,*case['geometry'],case['depth'],parameters,route,
                case['input_padding'],case['output_padding']],case['pixels']

    def candidate(self, case, directory, route, deadline):
        trace = directory/f'refusal_trace_{route}.txt'
        trace.unlink(missing_ok=True)
        # Per-call environment: the shared adapter is used by concurrent jobs.
        traced = copy.copy(self)
        traced.env = dict(self.env, OLM_REFUSAL_TRACE=str(trace))
        try:
            result, raw = PublicAdapter.candidate(traced, case, directory, route, deadline)
            try:
                guards = [line.strip() for line in trace.read_text().splitlines() if line.strip()]
            except OSError:
                guards = []
            return result, raw, guards
        finally:
            trace.unlink(missing_ok=True)
