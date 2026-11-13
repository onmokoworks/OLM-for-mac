"""Retain the native end-to-end fractional-padding/Both regression in ARGB8."""
import hashlib
import json
from pathlib import Path
import struct
from PIL import Image
import numpy as np
crate=Path(__file__).resolve().parents[1]
case=crate/'validation/upstream/recheck-v8/case-0076-smart8'
source=np.asarray(Image.open(case/'input.png').convert('RGBA'))
expected=np.asarray(Image.open(case/'reference.png').convert('RGBA'))
data=struct.pack('<4I',source.shape[1],source.shape[0],expected.shape[1],expected.shape[0])
data+=source[:,:,[3,0,1,2]].tobytes()+expected[:,:,[3,0,1,2]].tobytes()
(crate/'tests/upstream-masked-copy.bin').write_bytes(data)
(crate/'tests/upstream-masked-copy-provenance.json').write_text(json.dumps(dict(
    case=str(case.relative_to(crate)),
    original_sha256=json.loads((case/'case.json').read_text())['reference']['sha256'],
    manifest_sha256=hashlib.sha256((case/'case.json').read_bytes()).hexdigest(),
    fixture_sha256=hashlib.sha256(data).hexdigest(),
    packing='four little-endian dimensions; input then expected output packed ARGB8'),indent=2))
