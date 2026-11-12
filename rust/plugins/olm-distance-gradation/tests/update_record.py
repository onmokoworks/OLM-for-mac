"""Job-local record extension for bounded IplImage planes in the new drivers."""
from pathlib import Path
import json
import struct
import sys

CRATE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CRATE.parents[1] / 'tools/record'))
import record

class ImageCapture(record.Capture):
    def entry(self, debug, p, tid, ctx, f):
        rec = super().entry(debug, p, tid, ctx, f)
        if rec is None:
            return rec
        if rec['name'] == 'sqrt': return rec
        indices = [1, 2] if rec['name'] == 'field' else [0, 1]
        for index in indices:
            pointer = int.from_bytes(bytes.fromhex(rec['args'][index]['bits_le']), 'little')
            header = debug.read(p, pointer, 144)
            size = struct.unpack_from('<i', header, 80)[0]
            addr = struct.unpack_from('<Q', header, 88)[0]
            stride = struct.unpack_from('<i', header, 96)[0]
            w, h = struct.unpack_from('<ii', header, 40)
            depth = struct.unpack_from('<i', header, 16)[0]
            if struct.unpack_from('<i', header)[0] != 144 or not 0 < size <= 8*1024*1024:
                raise ValueError('not a bounded IplImage')
            if self.bytes_reserved + 2*size > self.max_bytes:
                raise ValueError('image capture budget exceeded')
            self.bytes_reserved += 2*size
            b = dict(name=f'image{index}', size=size, stride=stride, role='inout',
                     address=hex(addr), descriptor={'arg': index},
                     image={'width': w, 'height': h, 'depth': depth, 'header': header.hex()})
            rec['buffers'].append(b)
            self.blob(debug, p, rec, b, 'before')
        self.save(rec)
        return rec

record.Capture = ImageCapture
case = Path(sys.argv[1]).resolve()
out = Path(sys.argv[2]).resolve()
m = json.loads((case / 'case.json').read_text())
profile = {'schema_version': 1, 'module_sha256': m['reference']['sha256'], 'functions': [
    {'name': 'field', 'rva': '0x11750f0', 'args': ['ptr','ptr','ptr','i32','i32','i32','i32','i32'], 'return': 'void', 'max_calls': 2},
    {'name': 'smooth', 'rva': '0x1286e20', 'args': ['ptr','ptr','i32','i32','i32','f64','f64'], 'return': 'void', 'max_calls': 1},
    {'name': 'distance', 'rva': '0x12b1ef0', 'args': ['ptr','ptr','i32','i32','ptr','ptr','i32'], 'return': 'void', 'max_calls': 2},
    {'name': 'resize', 'rva': '0x12af8c0', 'args': ['ptr','ptr','i32'], 'return': 'void', 'max_calls': 4},
    {'name': 'normalize', 'rva': '0x117d2f0', 'args': ['ptr','ptr','f64','f64','i32','ptr'], 'return': 'void', 'max_calls': 2},
    {'name': 'sqrt', 'rva': '0x2f1e20', 'args': ['ptr','ptr','i32'], 'return': 'i32', 'max_calls': 2,
     'buffers': [{'arg':0,'size':{'mul':[{'arg':2},4]}}, {'arg':1,'size':{'mul':[{'arg':2},4]}}]},
]}
profile_path = out.with_suffix('.profile.json')
profile_path.write_text(json.dumps(profile, indent=2))
from types import SimpleNamespace
args = SimpleNamespace(module=Path(m['reference']['path']), profile=profile_path,
    harness=Path(m['harness']['path']), width=m['case']['size'][0], height=m['case']['size'][1],
    seed=m['case']['input_seed'], request=case/'requests/reference.json', route=m['route'],
    out=out, timeout=60., max_calls=13, max_bytes=64*1024*1024)
raise SystemExit(record.capture(args))
