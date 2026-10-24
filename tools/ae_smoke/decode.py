"""Decode straight RGBA exports to packed AE ARGB; validate using controls first."""
from pathlib import Path
import json
import numpy as np
import tifffile
import OpenEXR
from compare import compare


def decode(path, depth, width, height):
    if depth == 32:
        channels = OpenEXR.File(str(path), separate_channels=True).channels()
        if not all(c in channels for c in 'ARGB'):
            raise ValueError(f'{path}: missing ARGB EXR channels')
        if any(channels[c].pixels.dtype != np.float32 for c in 'ARGB'):
            raise ValueError(f'{path}: output must preserve FLOAT channels, not HALF')
        argb = np.stack([channels[c].pixels for c in 'ARGB'], axis=-1).astype('<f4')
    else:
        rgba = tifffile.imread(path)
        if rgba.shape != (height, width, 4):
            raise ValueError(f'{path}: unexpected TIFF shape {rgba.shape}')
        if depth == 8:
            if rgba.dtype != np.uint8:
                raise ValueError(f'{path}: expected 8-bit TIFF')
            argb = rgba[:, :, [3, 0, 1, 2]]
        else:
            if rgba.dtype != np.uint16:
                raise ValueError(f'{path}: expected 16-bit TIFF')
            # Nearest integer inverse of AE's full-range 0..65535 export.
            argb = ((rgba[:, :, [3, 0, 1, 2]].astype(np.uint64) * 32768 + 32767)
                    // 65535).astype('<u2')
    if argb.shape != (height, width, 4):
        raise ValueError(f'{path}: unexpected shape {argb.shape}')
    return argb.tobytes()


def check_controls(state):
    results = []
    for spec in json.loads((state / 'inputs/inputs.json').read_text()):
        depth = spec['depth']
        paths = sorted(state.glob(f'control-{depth}_*.{"exr" if depth == 32 else "tif"}'))
        if len(paths) != 1:
            raise ValueError(f'depth {depth}: expected exactly one rendered control, got {paths}')
        normalized = state / f'control-{depth}.argb'
        normalized.write_bytes(decode(paths[0], depth, spec['width'], spec['height']))
        row = compare(normalized, Path(spec['raw']), spec['width'], spec['height'], depth)
        row.update(depth=depth, classification=None if row['exact'] else 'I/O conversion')
        results.append(row)
    return results
