#!/usr/bin/env python3
# Generate a 1920x1080 RGBA test image for OLMSmoother v1 byte-perfect verification.
# Pattern: cell-anim style - 1px black outlines + flat color fills + alpha edges + palette patches.

from PIL import Image, ImageDraw
import os

W, H = 1920, 1080
img = Image.new("RGBA", (W, H), (200, 200, 200, 255))
d = ImageDraw.Draw(img)

# Solid color patches (top-left 4x2 grid, 240x270 each)
palette = [
    (255, 0,   0,   255),
    (0,   255, 0,   255),
    (0,   0,   255, 255),
    (255, 255, 0,   255),
    (255, 0,   255, 255),
    (0,   255, 255, 255),
    (255, 255, 255, 255),
    (0,   0,   0,   255),
]
for i, c in enumerate(palette):
    x = (i % 4) * 240
    y = (i // 4) * 270
    d.rectangle([x, y, x + 240, y + 270], fill=c)

# 1px diagonal lines, 8 directions, lower-left quadrant
cx, cy = 480, 810
for ang_idx in range(8):
    dx = [-1, 0, 1, -1, 1, -1, 0, 1][ang_idx]
    dy = [-1, -1, -1, 0, 0, 1, 1, 1][ang_idx]
    for step in range(0, 200):
        px = cx + dx * step
        py = cy + dy * step
        if 0 <= px < W and 0 <= py < H:
            d.point([px, py], fill=(0, 0, 0, 255))

# Filled circle with anti-aliased edge (right side)
import math
ccx, ccy, cr = 1440, 540, 200
for y in range(ccy - cr - 2, ccy + cr + 2):
    for x in range(ccx - cr - 2, ccx + cr + 2):
        if 0 <= x < W and 0 <= y < H:
            r2 = (x - ccx) ** 2 + (y - ccy) ** 2
            if r2 <= cr * cr:
                d.point([x, y], fill=(255, 128, 0, 255))

# Alpha edge rectangle (bottom-right)
for y in range(800, 1080):
    for x in range(1200, 1920):
        a = max(0, min(255, (x - 1200) * 255 // 720))
        d.point([x, y], fill=(50, 100, 200, a))

# Step gradient (top-right strip)
for x in range(960, 1920):
    g = (x - 960) * 255 // (1920 - 960)
    d.line([(x, 0), (x, 80)], fill=(g, g, g, 255))

out = os.path.join(os.path.dirname(__file__), "..", "fixtures", "test_cellanim.png")
out = os.path.abspath(out)
img.save(out)
print(f"wrote: {out} ({W}x{H} RGBA)")
