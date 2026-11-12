"""Pack hash-bound native field recordings into the small checked-in regression fixture."""
import hashlib
import json
from pathlib import Path
import struct

crate = Path(__file__).resolve().parents[1]
data = bytearray()
rows = []
for name in ('record-stages-case2', 'record-case38'):
    cap = crate / 'validation/upstream' / name
    for path in sorted(cap.glob('calls/*/record.json')):
        r = json.loads(path.read_text())
        if r['name'] != 'field': continue
        def arg(i): return int.from_bytes(bytes.fromhex(r['args'][i]['bits_le']), 'little')
        def plane(b, phase):
            w, h = struct.unpack_from('<ii', bytes.fromhex(b['image']['header']), 40)
            raw = (cap / b[phase]['file']).read_bytes()
            step = w * b['image']['depth'] // 8
            return w, h, b''.join(raw[y*b['stride']:y*b['stride']+step] for y in range(h))
        w, h, source = plane(r['buffers'][0], 'before')
        _, _, expected = plane(r['buffers'][1], 'after')
        maximum = {8:255., 16:32768., 32:1.}[arg(4)]
        data += struct.pack('<6If', w,h,arg(5),arg(6),arg(3),arg(7),maximum)
        data += source + expected
        rows.append(dict(record=str(path.relative_to(crate)),
            record_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
            shape=[w,h], reconstructed_shape=[arg(5),arg(6)],
            threshold=arg(3), interpolation=arg(7),
            output_sha256=hashlib.sha256(expected).hexdigest()))
(crate/'tests/upstream-field.bin').write_bytes(data)
(crate/'tests/upstream-field-provenance.json').write_text(json.dumps(dict(
    original_sha256='fd151598c015baf7068ce7ef59eead7430657cab083d9000c2a35e9b84da5e63',
    field_rva='0x11750f0', fixture_sha256=hashlib.sha256(data).hexdigest(), cases=rows),indent=2))
print(len(rows), 'recorded fields,', len(data), 'bytes')
