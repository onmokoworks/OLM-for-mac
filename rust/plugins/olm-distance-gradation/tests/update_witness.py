"""Replay captured native field/filter inputs through production Rust exports."""
import json
from pathlib import Path
import struct
import sys
import numpy as np
import pefile

CRATE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CRATE.parents[1] / 'tools/witness'))
import witness
capture, module, out = [Path(x).resolve() for x in sys.argv[1:4]]
out.mkdir(exist_ok=False)
pe = pefile.PE(str(module))
exports = {x.name.decode(): x.address for x in pe.DIRECTORY_ENTRY_EXPORT.symbols if x.name}
rows = []
for path in sorted(capture.glob('calls/*/record.json')):
    rec = json.loads(path.read_text())
    if rec['name'] not in ('field', 'smooth', 'distance'): continue
    def plane(b, phase):
        header = bytes.fromhex(b['image']['header'])
        w, h = struct.unpack_from('<ii', header, 40)
        n = b['image']['depth'] // 8
        raw = (capture / b[phase]['file']).read_bytes()
        return w, h, b''.join(raw[y*b['stride']:y*b['stride']+w*n] for y in range(h))
    w, h, source = plane(rec['buffers'][0], 'before')
    _, _, expected = plane(rec['buffers'][1], 'after')
    def arg(i): return int.from_bytes(bytes.fromhex(rec['args'][i]['bits_le']), 'little', signed=True)
    def i32(x): return {'type': 'i32', 'value': x}
    args = [{'type': 'ptr', 'buffer': 'source'}, {'type': 'ptr', 'buffer': 'output'}, i32(w), i32(h)]
    if rec['name'] == 'field':
        args += [i32(arg(5)), i32(arg(6)), i32(arg(3)), i32(arg(7)),
                 {'type':'f32','value':{8:255.,16:32768.,32:1.}[arg(4)]}]
        export = 'olm_update_field_v1'
    elif rec['name'] == 'distance':
        export = 'olm_update_edt_v1'
    else:
        args += [i32(arg(2)), i32(arg(3)), i32(arg(4))]
        export = 'olm_update_filter_v1'
    spec = {'schema_version':1,'module':str(module),'buffers':{
        'source': {'size':len(source),'hex':source.hex()}, 'output':{'size':len(expected)}},
        'calls':[{'rva':hex(exports[export]),'args':args,'return':'i32'}]}
    dest = out / path.parent.name
    result = witness.run(spec, dest, timeout=30)
    result_json = json.loads((dest/'result.json').read_text())
    # The witness dumps every buffer after the completed call.
    actual = next(dest.glob('call-*-output.bin')).read_bytes()
    aa, bb = np.frombuffer(actual,dtype='<u4'), np.frombuffer(expected,dtype='<u4')
    bad = np.flatnonzero(aa != bb)
    rows.append({'name':rec['name'],'call':rec['sequence'],'shape':[w,h],
        'mismatching_words':len(bad),'first':int(bad[0]) if len(bad) else None,
        'first_bits':[hex(int(aa[bad[0]])),hex(int(bb[bad[0]]))] if len(bad) else None,
        'native_record_sha256':witness.sha256(path), 'expected_sha256':__import__('hashlib').sha256(expected).hexdigest()})
(out/'comparison.json').write_text(json.dumps(rows,indent=2))
print(json.dumps(rows,indent=2))
