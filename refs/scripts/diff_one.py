#!/usr/bin/env python3
# Pixel-level diff between Win reference and Mac port output.
# Usage: diff_one.py <win.png> <mac.png> [diff.png]
# Exit: 0 if max diff == 0 (byte-perfect), 1 otherwise.

import sys
from PIL import Image
import numpy as np

if len(sys.argv) < 3:
    print("usage: diff_one.py <win.png> <mac.png> [diff_out.png]", file=sys.stderr)
    sys.exit(2)

win_path, mac_path = sys.argv[1], sys.argv[2]
diff_out = sys.argv[3] if len(sys.argv) > 3 else None

a = np.asarray(Image.open(win_path).convert("RGBA"))
b = np.asarray(Image.open(mac_path).convert("RGBA"))
if a.shape != b.shape:
    print(f"shape mismatch: win={a.shape} mac={b.shape}", file=sys.stderr)
    sys.exit(2)

d = np.abs(a.astype(np.int32) - b.astype(np.int32))
mx = int(d.max())
nz = int((d > 0).any(axis=-1).sum())
mean = float(d.mean())
total_px = a.shape[0] * a.shape[1]

print(f"{win_path} vs {mac_path}")
print(f"  shape={a.shape} max_diff={mx} mean_diff={mean:.4f} nonzero_px={nz}/{total_px} ({100*nz/total_px:.4f}%)")

if mx > 0:
    ys, xs = np.where(d.any(axis=-1))
    for k in range(min(5, len(xs))):
        x, y = int(xs[k]), int(ys[k])
        print(f"  diff @ ({x},{y}): win={tuple(int(v) for v in a[y,x])} mac={tuple(int(v) for v in b[y,x])} delta={tuple(int(v) for v in d[y,x])}")

    if diff_out:
        amp = np.minimum(d.astype(np.int32) * 32, 255).astype(np.uint8)
        amp[..., 3] = 255
        Image.fromarray(amp, "RGBA").save(diff_out)
        print(f"  diff image (32x amplified): {diff_out}")
    sys.exit(1)

print("  BYTE-PERFECT")
sys.exit(0)
