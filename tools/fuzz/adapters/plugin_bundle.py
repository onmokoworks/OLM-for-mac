"""Opt-in native bundles over the same Rust ClassicHost session arena.

The AEX supplies parameter schemas/arena construction. Its render selectors are
replaced only for the candidate. This is deliberately not a standalone AE host.
"""
import copy
import importlib
import json
from core import sha

SUPPORTED = ('olmblur', 'colorkeep', 'olmcolorkey', 'olmdirectionalblur',
             'olmdistancegradation', 'olmkirakira', 'olmsmoother2', 'olmtoondilate',
             'radialblur', 'olmsmoother')


def Adapter(options):
    options = copy.copy(options)
    options.plugin = getattr(options, 'plugin', 'olmblur')
    if options.plugin not in SUPPORTED:
        raise ValueError('unsupported bundle plugin: '+options.plugin)
    base = importlib.import_module('adapters.'+options.plugin).Adapter
    return type('BundleAdapter', (BundleMixin, base), {})(options)


Adapter.generator_version = 1


class BundleMixin:
    # Source-host qualification must never leak into the independent bundle host.
    geometry_samplers = ()
    routes = ('smart',)
    oracle_routes = {'smart':'smart'}
    original_routes = {'smart':'render'}

    def __init__(self, options):
        super().__init__(options)
        if options.plugin in ('colorkeep','olmdistancegradation','olmkirakira','radialblur','olmtoondilate','olmsmoother2','olmsmoother','olmblur','olmdirectionalblur','olmcolorkey'):
            self.geometry_samplers=('realistic-v1','realistic-v2')
        self.env.pop('OLM_NATIVE_BUNDLE_EXECUTABLE', None)
        self.env.pop('OLM_NATIVE_PARAMETER_PROFILE', None)
        self.bundle = options.plugin_bundle.resolve()
        name = {'radialblur':'OLMRadialBlur', 'olmdistancegradation':'OLMDistanceGradation'}.get(options.plugin, getattr(self, 'aex_name', None))
        self.executable = self.bundle/'Contents/MacOS'/name
        if options.plugin == 'olmsmoother':
            self.routes = ('classic',)
            self.oracle_routes = {'classic':'classic'}
            self.original_routes = {'classic':'render'}
        if options.plugin == 'radialblur':
            from .radialblur import DECLARATIONS
            self.declaration_path = DECLARATIONS
            self.binding = {'aex_sha256': sha(self.aex.read_bytes())}
        if self.bundle.name != name+'.plugin' or not self.executable.is_file():
            raise ValueError('expected built '+name+'.plugin bundle')

    def prepare(self, scratch, deadline):
        if sha(self.aex.read_bytes()) != self.binding['aex_sha256']:
            raise ValueError('AEX declaration binding changed')
        self.env.update(TMPDIR=str(scratch), TMP=str(scratch), TEMP=str(scratch))
        self.binary = self.executable
        from .bundle_geometry import HOST
        geometry=getattr(self,'geometry_active',False)
        if getattr(self,'geometry_version',None)=='realistic-v2':
            from pathlib import Path
            HOST=Path.home()/'.cache/olm-emu/worker-F53-bundle/plugin-host'
        return {'host':('F52c standalone Universal bundle host; negotiated geometry' if geometry else 'F47d shared Rust ClassicHost arena; AEX setup, native candidate setup and selected render route'),
                **({'bundle_host_path':str(HOST),'bundle_host_sha256':sha(HOST.read_bytes())} if geometry else {}),
                'worker_path':str(self.worker), 'worker_sha256':sha(self.worker.read_bytes()),
                'aex_path':str(self.aex), 'aex_sha256':sha(self.aex.read_bytes()),
                'candidate_path':str(self.bundle), 'candidate_sha256':sha(self.executable.read_bytes()),
                'declarations_sha256':sha(self.declaration_path.read_bytes()),
                'world':('realistic-v1: byte padding, extent, aspect, downsample, request and negotiated output rect/origin' if geometry else 'same ARGB worlds: input padding rounded up to pixel alignment, 0xA5 fill; output packed in both runs; generated output_padding unused'),
                'parameter_profile':'kirakira-default-ramps; raw ANGLE to native slider' if self.name == 'olmkirakira' else 'shared declarations',
                'oracle_routes':self.oracle_routes, 'original_routes':self.original_routes}

    def first_stage(self, *args):
        return None

    def session_arguments(self, case, directory):
        if case.get('geometry_sampler'):return []
        w,h = case['geometry']
        pixel = case['depth']//8*4
        padding = ((case['input_padding']+pixel-1)//pixel)*pixel
        manifest = directory/'layers.json'
        manifest.write_text(json.dumps({'v':2, 'primary':{
            'rowbytes':w*pixel+padding, 'padding_byte':165,
            'origin_x':0, 'origin_y':0, 'extent':[0,0,w,h]}, 'layers':[]}))
        return ['--fixture-layers-v1', manifest]

    def candidate(self, case, directory, route, deadline):
        if case.get('geometry_sampler'):
            from .bundle_geometry import candidate
            return candidate(self,case,directory,route,deadline)
        candidate = copy.copy(self)
        candidate.env = dict(self.env, OLM_NATIVE_BUNDLE_EXECUTABLE=str(self.executable),
                             OLM_REFUSAL_TRACE=str(directory/'native-refusal.txt'))
        if self.name == 'olmkirakira':
            candidate.env['OLM_NATIVE_PARAMETER_PROFILE'] = 'kirakira-default-ramps'
        captured = []
        candidate.session_observed = lambda out, err: captured.append(err.decode(errors='replace'))
        result, raw = candidate.oracle(case, directory, deadline, route)
        trace = ''.join(captured)
        # Prove this was a bundle render; never accept an old worker's AEX output
        # as a native result merely because it ignored the environment switch.
        if result['status']=='ok' and (f'F47c selector {24 if route == "smart" else 11} error=0' not in trace or 'F47c counters' not in trace):
            return {'status':'harness_error','diagnostic':'worker did not execute native selectors'}, b''
        result['native_trace'] = trace
        path=directory/'native-refusal.txt'
        guards=path.read_text().splitlines() if path.exists() else []
        return result,raw,guards
