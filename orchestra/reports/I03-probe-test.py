#!/usr/bin/env python3
"""Observe compiler exits while running an unchanged historical-source test harness."""
import atexit, json, os, runpy, subprocess, sys
from pathlib import Path
EVENTS=[]
output=Path(os.environ['I03_COMPILE_EVENTS'])
def compiler(argv):
    return isinstance(argv,(list,tuple)) and Path(str(argv[0])).name in ('clang++','clang','c++','g++','cc')
def wrap(original):
    def call(argv,*args,**kwargs):
        try: result=original(argv,*args,**kwargs)
        except subprocess.CalledProcessError as exc:
            if compiler(argv): EVENTS.append(dict(command=list(map(str,argv)),exit=exc.returncode))
            raise
        if compiler(argv): EVENTS.append(dict(command=list(map(str,argv)),exit=result.returncode if hasattr(result,'returncode') else result))
        return result
    return call
subprocess.run=wrap(subprocess.run)
subprocess.check_call=wrap(subprocess.check_call)
atexit.register(lambda:output.write_text(json.dumps(EVENTS,indent=2)+'\n'))
root=Path(sys.argv[1]);test=sys.argv[2]
if test.startswith('@edge'):
    # Use retained geometry only to generate the existing C++ harness; never run
    # it or fabricate an expected pixel plane. Stop immediately after linking.
    import importlib, struct
    sys.path.insert(0,str(root/'tools/emulation'))
    suffix='edge_fade_intersections' if test=='@edge-intersection' else 'edge_fade'
    module=importlib.import_module('test_olmradialblur_rotation_pf32_'+suffix+'_actual_aex_20260811')
    module.configure('outer','noise25' if test=='@edge-intersection' else 50)
    geometry=json.loads((root/'refs/conformance/olmradialblur_rotation_pf32_small_actual_aex_20260805.json').read_text())['geometry']
    class Linked(BaseException): pass
    observed_run=subprocess.run
    def compile_only(argv,*args,**kwargs):
        result=observed_run(argv,*args,**kwargs)
        if compiler(argv) and '-c' not in argv and result.returncode==0: raise Linked()
        return result
    subprocess.run=compile_only
    try: module.pf32.mac_production({'geometry':struct.pack('<II',geometry['angular_count'],geometry['radius_count'])})
    except Linked: raise SystemExit(0)
    raise SystemExit('compile-only sentinel was not reached')
if test.startswith('tools/') or test.startswith('refs/'):
    sys.argv=[str(root/test)]
else:
    sys.argv=[str(root/'scripts/run_olm_generic_beta_gate.py'),'--run-test-file',str(root/test)]
runpy.run_path(sys.argv[0],run_name='__main__')
