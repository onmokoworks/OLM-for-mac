"""Deterministic opaque, nonblack 8bpc priority inputs; no color conversion needed."""
import hashlib
import json
from pathlib import Path
import numpy as np
import tifffile


def prepare(out, high_depth=False):
    out.mkdir(parents=True, exist_ok=True)
    rows = []
    specs = [(1920, 1080, 8), (1279, 719, 8), (3840, 2160, 8)]
    if high_depth:
        specs = [(w, h, depth) for depth in (16, 32)
                 for w, h in ((1920, 1080), (1279, 719))]
    for w, h, depth in specs:
        y, x = np.indices((h, w), dtype=np.uint32)
        rgba = np.empty((h, w, 4), dtype=np.uint8)
        rgba[:, :, 0] = 32 + ((x // 17 + y // 13) % 192)
        rgba[:, :, 1] = 32 + ((x // 31 + y // 7) % 192)
        rgba[:, :, 2] = 32 + ((x // 11 + y // 29) % 192)
        rgba[:, :, 3] = 255
        if depth == 16:
            rgba = ((rgba.astype(np.uint32) * 32768 + 127) // 255).astype('<u2')
        elif depth == 32:
            rgba = (rgba.astype(np.float32) / np.float32(255)).astype('<f4')
        path = out / f'input-{w}x{h}-{depth}.{"exr" if depth == 32 else "tif"}'
        if depth == 32:
            import OpenEXR
            OpenEXR.File({'compression': OpenEXR.NO_COMPRESSION, 'type': OpenEXR.scanlineimage},
                        {k: np.ascontiguousarray(rgba[:, :, i]) for i, k in enumerate('RGBA')}).write(str(path))
        else:
            encoded = (rgba.astype(np.uint64) * 65535 // 32768).astype('<u2') if depth == 16 else rgba
            tifffile.imwrite(path, encoded, photometric='rgb', extrasamples=['unassalpha'], metadata=None)
        raw = out / f'input-{w}x{h}-{depth}.argb'
        raw.write_bytes(rgba[:, :, [3, 0, 1, 2]].tobytes())
        rows.append(dict(depth=depth, width=w, height=h, path=str(path), raw=str(raw),
                         source_sha256=hashlib.sha256(raw.read_bytes()).hexdigest(),
                         file_sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
    (out / 'inputs.json').write_text(json.dumps(rows, indent=2) + '\n')
    return rows
