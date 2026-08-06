#!/usr/bin/env python3
"""Generate the color-management-free OLM cross-host FLOAT32 input fixture."""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import struct
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE_PACKAGE = ROOT / "refs/reference_requests/olm_windows_ae_release_boundary_minimal_20260806.zip"
SOURCE_MEMBER = "inputs/opaque_cells_rgba8.png"
DEFAULT_OUTPUT = ROOT / "refs/fixtures/olm_crosshost_linear/opaque_cells_linear_float32.exr"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def generate(output: Path) -> dict:
    try:
        from PIL import Image
    except ImportError as exc:
        raise SystemExit("Pillow is required") from exc

    with zipfile.ZipFile(SOURCE_PACKAGE) as archive:
        png = archive.read(SOURCE_MEMBER)
    image = Image.open(io.BytesIO(png)).convert("RGBA")
    width, height = image.size
    pixels = list(image.getdata())
    planes: dict[str, bytearray] = {}
    for index, name in enumerate("RGBA"):
        # Converting the integer code value directly to binary32 deliberately
        # avoids PNG profile/gamma interpretation in either AE host.
        plane = bytearray(width * height * 4)
        for pixel_index, value in enumerate(pixels):
            struct.pack_into("<f", plane, pixel_index * 4, value[index] / 255.0)
        planes[name] = plane

    def attr(name: str, kind: str, value: bytes) -> bytes:
        return name.encode() + b"\0" + kind.encode() + b"\0" + struct.pack("<I", len(value)) + value

    # OpenEXR channel lists and scanline payloads are canonicalized in
    # lexicographic physical order.  AE's Windows and macOS readers disagree
    # on a non-canonical R,G,B,A list (the first plane can become alpha).
    physical_order = "ABGR"
    channels = b"".join(
        name.encode() + b"\0" + struct.pack("<iB3xii", 2, 0, 1, 1)
        for name in physical_order
    ) + b"\0"
    window = struct.pack("<4i", 0, 0, width - 1, height - 1)
    header = b"".join((
        attr("channels", "chlist", channels),
        attr("dataWindow", "box2i", window),
        attr("displayWindow", "box2i", window),
        attr("compression", "compression", b"\0"),
        attr("lineOrder", "lineOrder", b"\0"),
        attr("pixelAspectRatio", "float", struct.pack("<f", 1.0)),
        attr("screenWindowCenter", "v2f", struct.pack("<2f", 0.0, 0.0)),
        attr("screenWindowWidth", "float", struct.pack("<f", 1.0)),
        b"\0",
    ))
    prefix = struct.pack("<II", 20000630, 2) + header
    row_payload_bytes = width * 4 * 4
    table_end = len(prefix) + height * 8
    chunk_bytes = 8 + row_payload_bytes
    offsets = b"".join(struct.pack("<Q", table_end + y * chunk_bytes) for y in range(height))
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("wb") as stream:
        stream.write(prefix)
        stream.write(offsets)
        for y in range(height):
            stream.write(struct.pack("<iI", y, row_payload_bytes))
            start, end = y * width * 4, (y + 1) * width * 4
            for name in physical_order:
                stream.write(planes[name][start:end])
    payload = output.read_bytes()
    return {
        "kind": "olm_crosshost_linear_float32_fixture",
        "source_package_sha256": sha256(SOURCE_PACKAGE.read_bytes()),
        "source_member": SOURCE_MEMBER,
        "source_png_sha256": sha256(png),
        "output": str(output.relative_to(ROOT)),
        "output_sha256": sha256(payload),
        "width": width,
        "height": height,
        "channels": ["R", "G", "B", "A"],
        "physical_channel_order": ["A", "B", "G", "R"],
        "sample_type": "FLOAT32",
        "compression": "none",
        "conversion": "rgba8 code value / 255.0 rounded once to IEEE-754 binary32",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--manifest", type=Path)
    args = parser.parse_args()
    report = generate(args.output.resolve())
    if args.manifest:
        args.manifest.parent.mkdir(parents=True, exist_ok=True)
        args.manifest.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
