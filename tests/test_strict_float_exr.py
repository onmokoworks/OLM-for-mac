#!/usr/bin/env python3
"""Adversarial tests for the deliberately small exact-FLOAT EXR contract."""

from __future__ import annotations

import gzip
import struct
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from compare_float_exr import compare, read_planes_with_layout  # noqa: E402
from compare_pf32_entry_to_exr import compare_pf32_entry, read_raw  # noqa: E402
from verify_32bpc_float_return import VerificationError  # noqa: E402


def attr(name: str, typ: str, value: bytes) -> bytes:
    return name.encode() + b"\0" + typ.encode() + b"\0" + struct.pack("<I", len(value)) + value


def chlist(
    names: tuple[str, ...] = ("R", "G", "B", "A"),
    sample_type: int = 2,
    p_linear: int = 0,
    sampling: tuple[int, int] = (1, 1),
    suffix: bytes = b"",
) -> bytes:
    body = b"".join(
        name.encode() + b"\0" + struct.pack("<iB3xii", sample_type, p_linear, *sampling)
        for name in names
    )
    return body + b"\0" + suffix


def make_exr(
    *,
    version_field: int = 2,
    channels: bytes | None = None,
    data_window: tuple[int, int, int, int] = (0, 0, 0, 0),
    display_window: tuple[int, int, int, int] = (0, 0, 0, 0),
    data_type: str = "box2i",
    data_raw: bytes | None = None,
    display_type: str = "box2i",
    display_raw: bytes | None = None,
    compression_type: str = "compression",
    compression: bytes = b"\0",
    line_type: str = "lineOrder",
    line_order: bytes = b"\0",
    duplicate: bytes = b"",
    gap: bytes = b"",
    trailing: bytes = b"",
    rows: tuple[int, ...] | None = None,
    overlap_offsets: bool = False,
) -> bytes:
    channels = chlist() if channels is None else channels
    data_value = struct.pack("<4i", *data_window) if data_raw is None else data_raw
    display_value = struct.pack("<4i", *display_window) if display_raw is None else display_raw
    header = b"".join(
        (
            attr("channels", "chlist", channels),
            attr("dataWindow", data_type, data_value),
            attr("displayWindow", display_type, display_value),
            attr("compression", compression_type, compression),
            attr("lineOrder", line_type, line_order),
            duplicate,
            b"\0",
        )
    )
    height = data_window[3] - data_window[1] + 1
    ys = rows if rows is not None else tuple(range(data_window[1], data_window[3] + 1))
    prefix = struct.pack("<II", 20000630, version_field) + header
    table_end = len(prefix) + height * 8
    payload_size = (data_window[2] - data_window[0] + 1) * 16
    chunks = [struct.pack("<iI", y, payload_size) + bytes(payload_size) for y in ys]
    offsets = []
    cursor = table_end + len(gap)
    for chunk in chunks:
        offsets.append(cursor)
        cursor += len(chunk)
    if overlap_offsets and len(offsets) > 1:
        offsets[1] = offsets[0]
    return prefix + b"".join(struct.pack("<Q", x) for x in offsets) + gap + b"".join(chunks) + trailing


class StrictFloatExrTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def write(self, name: str, data: bytes) -> Path:
        path = self.root / name
        path.write_bytes(data)
        return path

    def rejected(self, data: bytes) -> None:
        with self.assertRaises(VerificationError):
            read_planes_with_layout(self.write("bad.exr", data))

    def test_valid_minimal_file_and_bitwise_nonfinite_words(self) -> None:
        path = self.write("ok.exr", make_exr())
        planes, width, height, layout = read_planes_with_layout(path)
        self.assertEqual((width, height), (1, 1))
        self.assertEqual(layout["data_window"], [0, 0, 0, 0])
        self.assertEqual(set(planes), {"R", "G", "B", "A"})

    def test_rejects_version_flags_and_duplicate_attributes(self) -> None:
        self.rejected(make_exr(version_field=1))
        self.rejected(make_exr(version_field=2 | (1 << 8)))
        self.rejected(make_exr(duplicate=attr("compression", "compression", b"\0")))

    def test_rejects_chlist_terminator_suffix_and_channel_mutations(self) -> None:
        self.rejected(make_exr(channels=chlist(suffix=b"x")))
        self.rejected(make_exr(channels=chlist()[:-1]))
        self.rejected(make_exr(channels=chlist(("R", "G", "B", "B"))))
        self.rejected(make_exr(channels=chlist(sample_type=1)))
        self.rejected(make_exr(channels=chlist(p_linear=2)))
        self.rejected(make_exr(channels=chlist(sampling=(2, 1))))

    def test_rejects_strict_attribute_type_and_length_mutations(self) -> None:
        self.rejected(make_exr(data_type="string"))
        self.rejected(make_exr(data_raw=bytes(15)))
        self.rejected(make_exr(display_type="string"))
        self.rejected(make_exr(display_raw=bytes(15)))
        self.rejected(make_exr(compression_type="uchar"))
        self.rejected(make_exr(compression=b"\0\0"))
        self.rejected(make_exr(line_type="uchar"))
        self.rejected(make_exr(line_order=b"\0\0"))
        self.rejected(make_exr(line_order=b"\3"))

    def test_rejects_duplicate_rows_offsets_gaps_overlap_and_trailing_bytes(self) -> None:
        two_rows = dict(data_window=(0, 0, 0, 1), display_window=(0, 0, 0, 1))
        self.rejected(make_exr(**two_rows, rows=(0, 0)))
        self.rejected(make_exr(**two_rows, overlap_offsets=True))
        self.rejected(make_exr(**two_rows, gap=b"x"))
        self.rejected(make_exr(**two_rows, trailing=b"x"))

    def test_compare_requires_identical_windows_and_line_order(self) -> None:
        reference = self.write("ref.exr", make_exr())
        shifted = self.write(
            "shifted.exr",
            make_exr(data_window=(1, 0, 1, 0), display_window=(1, 0, 1, 0)),
        )
        with self.assertRaisesRegex(VerificationError, "data_window"):
            compare(reference, shifted)
        different_display = self.write(
            "display.exr", make_exr(display_window=(0, 0, 1, 0))
        )
        with self.assertRaisesRegex(VerificationError, "display_window"):
            compare(reference, different_display)
        different_order = self.write("order.exr", make_exr(line_order=b"\1"))
        with self.assertRaisesRegex(VerificationError, "line_order"):
            compare(reference, different_order)

    def test_pf32_requires_zero_origin_and_full_windows(self) -> None:
        raw = self.write("frame.raw", bytes(16))
        shifted = self.write(
            "shifted.exr",
            make_exr(data_window=(1, 0, 1, 0), display_window=(1, 0, 1, 0)),
        )
        with self.assertRaisesRegex(ValueError, "origin 0"):
            compare_pf32_entry(raw, shifted)
        cropped = self.write("cropped.exr", make_exr(display_window=(0, 0, 1, 0)))
        with self.assertRaisesRegex(ValueError, "display/data"):
            compare_pf32_entry(raw, cropped)

    def test_gzip_read_is_bounded_and_rejects_excess(self) -> None:
        path = self.root / "oversize.raw.gz"
        with gzip.open(path, "wb") as stream:
            stream.write(bytes(17))
        with self.assertRaisesRegex(ValueError, "17 != expected 16"):
            read_raw(path, 16)


if __name__ == "__main__":
    unittest.main()
