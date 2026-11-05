#!/usr/bin/env python3
"""Real bundles + existing fuzz bundle host + original AEX; no AE required."""
import importlib,json,os,shutil,sys,time
from pathlib import Path
from targets import T23, TICKET, PLUGINS
from types import SimpleNamespace
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/fuzz'))
from core import load_corpus
from adapters.plugin_bundle import Adapter
from replay_aex import replay
S=ROOT/'orchestra/state'/TICKET/'self-test'
S.mkdir(parents=True,exist_ok=True)
worker=Path.home()/'.cache/olm-emu/worker-F53-geom/aex-guest-worker'
main=ROOT.parent.parent if ROOT.parent.name=='worktrees' else ROOT
results=[]
cases = [
    ('olmdistancegradation','OLMDistanceGradation','seed104_case000207_S01.json'),
    ('olmkirakira','OLMKiraKira','refusal_seed1_case000000.json')]
if T23:
    cases = [('radialblur','OLMRadialBlur','C45_seed45101_case000273.json'),
             ('olmdirectionalblur','OLMDirectionalBlur','C45_seed1_case000246.json'),
             ('olmblur','OLMBlur','seed1_case000004_adfc483da30a.json')]
for plugin,name,casefile in cases:
    corpus=ROOT/'tests/fuzz_corpus'/plugin/casefile
    saved=json.loads(corpus.read_text())
    d=S/plugin;d.mkdir(exist_ok=True);captures=d/'captures';captures.mkdir(exist_ok=True)
    options=SimpleNamespace(plugin=plugin,max_size=saved['max_size'],case_timeout=600,main=main,worker=worker,
        plugin_bundle=ROOT/'orchestra/state'/TICKET/'build'/(name+'.plugin'))
    a=Adapter(options);case,_=load_corpus(corpus,a)
    w,h=case['geometry']
    # The same saved active input/parameters, with one common legal padded stride.
    case.update(geometry_sampler='realistic-v1',full_geometry=[w,h],downsample=[[1,1],[1,1]],
        rowbytes_padding=3,input_padding=3,output_padding=3,extent_hint=[0,0,w,h],request_rect=[0,0,w,h],pixel_aspect=[1,1])
    a.geometry_active=True;a.geometry_version='realistic-v1'
    a.prepare(d,time.monotonic()+600)
    before=set(captures.iterdir());a.env['OLM_LIVE_CAPTURE_DIR']=str(captures)
    result,raw,*_=a.candidate(case,d,'smart',time.monotonic()+600)
    if result['status']!='ok':raise RuntimeError(result)
    made=set(captures.iterdir())-before
    if len(made)!=1:raise RuntimeError(f'expected one capture, got {made}')
    capture=made.pop()
    # Failure to open a capture directory must preserve the actual render.
    bad_root=d/'not-a-directory';bad_root.write_text('intentional capture I/O failure')
    a.env['OLM_LIVE_CAPTURE_DIR']=str(bad_root)
    failed,failed_raw,*_=a.candidate(case,d,'smart',time.monotonic()+600)
    assert failed['status']=='ok' and failed_raw==raw,failed
    a.env.pop('OLM_LIVE_CAPTURE_DIR')
    disabled,disabled_raw,*_=a.candidate(case,d,'smart',time.monotonic()+600)
    assert disabled['status']=='ok' and disabled_raw==raw,disabled
    exact=replay(capture,d/'replay',worker,main)
    if exact['status']!='exact':raise RuntimeError(exact)
    altered=d/'altered'
    if altered.exists():shutil.rmtree(altered)
    shutil.copytree(capture,altered)
    with (altered/'output.raw').open('r+b') as f:
        b=f.read(1);f.seek(0);f.write(bytes([b[0]^1]))
    negative=replay(altered,d/'negative',worker,main)
    assert negative['status']=='mismatch' and negative['different_words']==1 and negative['max_diff']==1,negative
    results.append({'plugin':plugin,'corpus':str(corpus),'capture':str(capture),'exact':exact,'altered':negative,'capture_disabled_same':True,'capture_io_failure_same':True})
    (S/'results.json').write_text(json.dumps(results,indent=2))
    print(plugin,'exact; altered output: 1 word, max 1',flush=True)

if T23 and '--with-layer' in sys.argv:
    # Exercise the retained worker's existing layer-manifest transport in both
    # native-bundle and original-AEX routes. No worker implementation is changed.
    plugin='radialblur';name='OLMRadialBlur'
    corpus=ROOT/'tests/fuzz_corpus/radialblur/C45_seed45101_case000273.json'
    saved=json.loads(corpus.read_text())
    d=S/'radial-distinct-layer';d.mkdir(exist_ok=True)
    captures=d/'captures';captures.mkdir(exist_ok=True)
    options=SimpleNamespace(plugin=plugin,max_size=saved['max_size'],case_timeout=600,main=main,worker=worker,
        plugin_bundle=ROOT/'orchestra/state'/TICKET/'build'/(name+'.plugin'))
    a=Adapter(options);case,_=load_corpus(corpus,a)
    # Bounded Layer-mode derivative of the corpus input; keep it nontrivial.
    overrides={1:1,4:4,5:1,6:0,7:0,10:0,11:1,12:0,13:0,15:1,17:1.0,18:0.0,20:5.0,21:1.0,22:0.0,24:25.0,25:3,28:0.0,29:7.0}
    for p in case['parameters']:
        if p['slot'] in overrides:p['value']=overrides[p['slot']]
    case['input_padding']=0;case['output_padding']=0
    width,height=case['geometry']
    noise=bytes(255-b for b in case['pixels'])
    assert noise!=case['pixels']
    from build_layer_host import build
    from adapters import bundle_geometry
    bundle_geometry.HOST=build()
    case.update(geometry_sampler='realistic-v1',full_geometry=[width,height],downsample=[[1,1],[1,1]],
        rowbytes_padding=0,input_padding=0,output_padding=0,extent_hint=[0,0,width,height],request_rect=[0,0,width,height],pixel_aspect=[1,1])
    a.geometry_active=True;a.geometry_version='realistic-v1'
    noise_file=d/'noise.raw';noise_file.write_bytes(noise)
    a.env.update(OLM_TEST_NOISE_FILE=str(noise_file),OLM_TEST_NOISE_SLOT='26')
    a.prepare(d,time.monotonic()+600)
    a.env['OLM_LIVE_CAPTURE_DIR']=str(captures)
    before=set(captures.iterdir())
    result,raw,*_=a.candidate(case,d,'smart',time.monotonic()+600)
    if result['status']!='ok':raise RuntimeError(result)
    made=set(captures.iterdir())-before
    assert len(made)==1,made
    capture=made.pop()
    assert (capture/'noise_layer.raw').read_bytes()==noise
    try:
        exact=replay(capture,d/'replay',worker,main)
    except Exception as error:
        results.append({'plugin':plugin,'variant':'distinct Noise Layer','capture':str(capture),
                        'status':'unsupported_or_error','error':str(error),'overrides':overrides})
        (S/'results.json').write_text(json.dumps(results,indent=2))
        raise
    assert exact['status']=='exact',exact
    results.append({'plugin':plugin,'variant':'distinct Noise Layer','corpus':str(corpus),
                    'overrides':overrides,'capture':str(capture),'exact':exact})
    (S/'results.json').write_text(json.dumps(results,indent=2))
    print('radialblur distinct Noise Layer: exact',flush=True)
