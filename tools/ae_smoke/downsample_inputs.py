"""Deterministic opaque, nonblack 8bpc priority inputs; no color conversion needed."""
import hashlib
import json
from pathlib import Path
import numpy as np
import tifffile


def prepare(out):
    out.mkdir(parents=True, exist_ok=True)
    rows = []
    for w, h in ((1920, 1080), (1279, 719), (3840, 2160)):
        y, x = np.indices((h, w), dtype=np.uint32)
        rgba = np.empty((h, w, 4), dtype=np.uint8)
        rgba[:, :, 0] = 32 + ((x // 17 + y // 13) % 192)
        rgba[:, :, 1] = 32 + ((x // 31 + y // 7) % 192)
        rgba[:, :, 2] = 32 + ((x // 11 + y // 29) % 192)
        rgba[:, :, 3] = 255
        path = out / f'input-{w}x{h}-8.tif'
        tifffile.imwrite(path, rgba, photometric='rgb', extrasamples=['unassalpha'], metadata=None)
        raw = out / f'input-{w}x{h}-8.argb'
        raw.write_bytes(rgba[:, :, [3, 0, 1, 2]].tobytes())
        rows.append(dict(depth=8, width=w, height=h, path=str(path), raw=str(raw),
                         source_sha256=hashlib.sha256(raw.read_bytes()).hexdigest(),
                         file_sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
    (out / 'inputs.json').write_text(json.dumps(rows, indent=2) + '\n')
    return rows
