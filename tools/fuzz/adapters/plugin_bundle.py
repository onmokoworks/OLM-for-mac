"""Opt-in OLMBlur native bundle over the same Rust ClassicHost session arena.

The AEX supplies parameter schemas/arena construction. Its Smart selectors are
replaced only for the candidate. This is deliberately not a standalone AE host.
"""
import copy
import json
from pathlib import Path
from .olmblur import Adapter as BlurAdapter
from .public import ROOT
from core import sha

class Adapter(BlurAdapter):
    routes = ('smart',)
    oracle_routes = {'smart':'smart'}
    original_routes = {'smart':'render'}

    def __init__(self, options):
        super().__init__(options)
        self.bundle = options.plugin_bundle.resolve()
        self.executable = self.bundle/'Contents/MacOS/OLMBlur'
        if self.bundle.name != 'OLMBlur.plugin' or not self.executable.is_file():
            raise ValueError('expected built OLMBlur.plugin bundle')

    def prepare(self, scratch, deadline):
        if sha(self.aex.read_bytes()) != self.binding['aex_sha256']:
            raise ValueError('AEX declaration binding changed')
        self.env.update(TMPDIR=str(scratch), TMP=str(scratch), TEMP=str(scratch))
        self.binary = self.executable
        return {'host':'F47c shared Rust ClassicHost arena; AEX setup, native candidate setup and Smart selectors',
                'worker_path':str(self.worker), 'worker_sha256':sha(self.worker.read_bytes()),
                'aex_path':str(self.aex), 'aex_sha256':sha(self.aex.read_bytes()),
                'candidate_path':str(self.bundle), 'candidate_sha256':sha(self.executable.read_bytes()),
                'declarations_sha256':sha(self.declaration_path.read_bytes()),
                'world':'same ARGB worlds: input padding rounded up to pixel alignment, 0xA5 fill; output packed in both runs; generated output_padding unused',
                'oracle_routes':self.oracle_routes, 'original_routes':self.original_routes}

    def session_arguments(self, case, directory):
        w,h = case['geometry']
        pixel = case['depth']//8*4
        padding = ((case['input_padding']+pixel-1)//pixel)*pixel
        manifest = directory/'layers.json'
        manifest.write_text(json.dumps({'v':2, 'primary':{
            'rowbytes':w*pixel+padding, 'padding_byte':165,
            'origin_x':0, 'origin_y':0, 'extent':[0,0,w,h]}, 'layers':[]}))
        return ['--fixture-layers-v1', manifest]

    def candidate(self, case, directory, route, deadline):
        candidate = copy.copy(self)
        candidate.env = dict(self.env, OLM_NATIVE_BUNDLE_EXECUTABLE=str(self.executable),
                             OLM_REFUSAL_TRACE=str(directory/'native-refusal.txt'))
        captured = []
        candidate.session_observed = lambda out, err: captured.append(err.decode(errors='replace'))
        result, raw = candidate.oracle(case, directory, deadline, 'smart')
        trace = ''.join(captured)
        # Prove this was a bundle render; never accept an old worker's AEX output
        # as a native result merely because it ignored the environment switch.
        if result['status']=='ok' and ('F47c selector 24 error=0' not in trace or 'F47c counters' not in trace):
            return {'status':'harness_error','diagnostic':'worker did not execute native Smart selectors'}, b''
        result['native_trace'] = trace[-4000:]
        path=directory/'native-refusal.txt'
        guards=path.read_text().splitlines() if path.exists() else []
        return result,raw,guards
