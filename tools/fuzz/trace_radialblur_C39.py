#!/usr/bin/env python3
"""C39 bounded Rotation tracer invocation (known capture failure retained).

Run reproduce_C39.py --plugin radialblur first. Both angle controls are zero;
the legacy trace CLI omits them. No parameter or image quantization is used.
"""
import sys,json,zlib,base64
from pathlib import Path
R=Path.cwd();S=R/'orchestra/state/C39-seed45-residual-mismatches'
sys.path[:0]=[str(R/'tools/fuzz'),str(R/'tools/emulation')]
import trace_radialblur_rotation_C11 as t
from run import default_worker
v=json.loads((S/'radialblur/witness.json').read_text())
f=S/'radial-fixture.json';f.write_text(json.dumps(dict(case=v['case'],input_hex=zlib.decompress(base64.b64decode(v['pixels_zlib_base64'])).hex())))
original_assignments=t.zoom.assignments
t.zoom.assignments=lambda c:[v for v in original_assignments(c) if ':angle=' not in v]
assert all(q['value']==0 for q in v['case']['parameters'] if q['kind']=='a')
t.WORKER=default_worker();sys.argv=['trace','--output',str(S/'radial-trace2'),'--fixture',str(f)]
t.main()
