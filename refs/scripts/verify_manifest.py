#!/usr/bin/env python3
"""Compare reference and candidate PNGs using any manifest with cases[].frame."""

import argparse
import csv
import json
import shutil
import struct
import subprocess
import sys
import zlib
from pathlib import Path

import numpy as np
from PIL import Image

FLOAT_PRIORITY_EXTS = [".exr", ".tiff", ".tif", ".hdr"]


def normalized_relpath(value):
    return value.replace("\\", "/")


def png_header(path):
    data = Path(path).read_bytes()
    if not data.startswith(b"\x89PNG\r\n\x1a\n"):
        return None
    pos = 8
    while pos + 8 <= len(data):
        length = struct.unpack(">I", data[pos : pos + 4])[0]
        chunk_type = data[pos + 4 : pos + 8]
        chunk_data = data[pos + 8 : pos + 8 + length]
        pos += 12 + length
        if chunk_type == b"IHDR":
            width, height, bit_depth, color_type, compression, filter_method, interlace = struct.unpack(
                ">IIBBBBB", chunk_data
            )
            return {
                "width": width,
                "height": height,
                "bit_depth": bit_depth,
                "color_type": color_type,
                "compression": compression,
                "filter_method": filter_method,
                "interlace": interlace,
            }
    return None


def magick_rgba16_array(path, header):
    magick = shutil.which("magick")
    if not magick:
        return None
    raw = subprocess.check_output([magick, str(path), "-depth", "16", "-endian", "MSB", "rgba:-"])
    expected = header["width"] * header["height"] * 4 * 2
    if len(raw) != expected:
        raise ValueError(f"unexpected ImageMagick RGBA payload size in {path}: {len(raw)} != {expected}")
    return np.frombuffer(raw, dtype=">u2").reshape((header["height"], header["width"], 4))


def magick_image_size(path):
    magick = shutil.which("magick")
    if not magick:
        return None
    output = subprocess.check_output(
        [magick, "identify", "-format", "%w %h", str(path)],
        text=True,
    ).strip()
    if not output:
        return None
    width_text, height_text = output.split()
    return int(width_text), int(height_text)


def magick_rgba_float32_array(path):
    magick = shutil.which("magick")
    if not magick:
        return None
    size = magick_image_size(path)
    if not size:
        return None
    width, height = size
    raw = subprocess.check_output(
        [
            magick,
            str(path),
            "-alpha",
            "set",
            "-define",
            "quantum:format=floating-point",
            "-depth",
            "32",
            "-endian",
            "LSB",
            "rgba:-",
        ]
    )
    expected = width * height * 4 * 4
    if len(raw) != expected:
        raise ValueError(f"unexpected ImageMagick float RGBA payload size in {path}: {len(raw)} != {expected}")
    return np.frombuffer(raw, dtype="<f4").reshape((height, width, 4))


def png_rgba_array(path):
    header = png_header(path)
    if header is None:
        raise ValueError(f"not a PNG file: {path}")
    if header["color_type"] != 6 or header["bit_depth"] != 16:
        return None
    magick_array = magick_rgba16_array(path, header)
    if magick_array is not None:
        return magick_array

    data = Path(path).read_bytes()

    pos = 8
    width = height = bit_depth = color_type = None
    idat = []
    while pos + 8 <= len(data):
        length = struct.unpack(">I", data[pos : pos + 4])[0]
        chunk_type = data[pos + 4 : pos + 8]
        chunk_data = data[pos + 8 : pos + 8 + length]
        pos += 12 + length
        if chunk_type == b"IHDR":
            width, height, bit_depth, color_type, compression, filter_method, interlace = struct.unpack(
                ">IIBBBBB", chunk_data
            )
            if compression != 0 or filter_method != 0 or interlace != 0:
                raise ValueError(f"unsupported PNG encoding in {path}")
        elif chunk_type == b"IDAT":
            idat.append(chunk_data)
        elif chunk_type == b"IEND":
            break

    if width is None or height is None or bit_depth is None or color_type is None:
        raise ValueError(f"missing PNG IHDR in {path}")
    if color_type != 6 or bit_depth != 16:
        return None

    channels = 4
    bytes_per_sample = bit_depth // 8
    bytes_per_pixel = channels * bytes_per_sample
    row_bytes = width * bytes_per_pixel
    raw = zlib.decompress(b"".join(idat))
    expected = height * (1 + row_bytes)
    if len(raw) != expected:
        raise ValueError(f"unexpected PNG payload size in {path}: {len(raw)} != {expected}")

    rows = np.empty((height, row_bytes), dtype=np.uint8)
    prev = np.zeros(row_bytes, dtype=np.uint8)
    offset = 0
    for y in range(height):
        filter_type = raw[offset]
        offset += 1
        current = np.frombuffer(raw, dtype=np.uint8, count=row_bytes, offset=offset).copy()
        offset += row_bytes
        recon = np.empty(row_bytes, dtype=np.uint8)
        for x in range(row_bytes):
            left = int(recon[x - bytes_per_pixel]) if x >= bytes_per_pixel else 0
            up = int(prev[x])
            up_left = int(prev[x - bytes_per_pixel]) if x >= bytes_per_pixel else 0
            value = int(current[x])
            if filter_type == 0:
                recon[x] = value
            elif filter_type == 1:
                recon[x] = (value + left) & 0xFF
            elif filter_type == 2:
                recon[x] = (value + up) & 0xFF
            elif filter_type == 3:
                recon[x] = (value + ((left + up) // 2)) & 0xFF
            elif filter_type == 4:
                p = left + up - up_left
                pa = abs(p - left)
                pb = abs(p - up)
                pc = abs(p - up_left)
                predictor = left if pa <= pb and pa <= pc else (up if pb <= pc else up_left)
                recon[x] = (value + predictor) & 0xFF
            else:
                raise ValueError(f"unsupported PNG filter {filter_type} in {path}")
        rows[y] = recon
        prev = recon

    if bit_depth == 8:
        return rows.reshape((height, width, channels))
    return rows.reshape((height, width, channels, 2)).view(">u2").reshape((height, width, channels))


def load_rgba(path):
    suffix = Path(path).suffix.lower()
    if suffix in FLOAT_PRIORITY_EXTS:
        rgba = magick_rgba_float32_array(path)
        if rgba is not None:
            return rgba
    rgba = png_rgba_array(path)
    if rgba is not None:
        return rgba
    return np.asarray(Image.open(path).convert("RGBA"))


def companion_path(path, suffix):
    candidate = path.with_suffix(suffix)
    return candidate if candidate.exists() else None


def resolve_compare_paths(reference_path, candidate_path):
    for suffix in FLOAT_PRIORITY_EXTS:
        ref_alt = companion_path(reference_path, suffix)
        cand_alt = companion_path(candidate_path, suffix)
        if ref_alt and cand_alt:
            return ref_alt, cand_alt
    return reference_path, candidate_path


def compare(reference_path, candidate_path, diff_path):
    reference = load_rgba(reference_path)
    candidate = load_rgba(candidate_path)
    if reference.shape != candidate.shape:
        return {
            "status": "shape_mismatch",
            "reference_shape": list(reference.shape),
            "candidate_shape": list(candidate.shape),
        }

    delta = np.abs(reference.astype(np.int64) - candidate.astype(np.int64))
    mask = delta.any(axis=-1)
    nonzero_px = int(mask.sum())
    total_px = int(reference.shape[0] * reference.shape[1])
    max_diff = int(delta.max())
    mean_diff = float(delta.mean())

    samples = []
    if nonzero_px:
        ys, xs = np.where(mask)
        for i in range(min(10, len(xs))):
            x = int(xs[i])
            y = int(ys[i])
            samples.append(
                {
                    "x": x,
                    "y": y,
                    "reference": [float(v) if np.issubdtype(reference.dtype, np.floating) else int(v) for v in reference[y, x]],
                    "candidate": [float(v) if np.issubdtype(candidate.dtype, np.floating) else int(v) for v in candidate[y, x]],
                    "delta": [float(v) if np.issubdtype(delta.dtype, np.floating) else int(v) for v in delta[y, x]],
                }
            )

        diff_path.parent.mkdir(parents=True, exist_ok=True)
        scale = 32 if delta.max() <= 255 else 255.0 / float(delta.max())
        amplified = np.minimum(delta * scale, 255).astype(np.uint8)
        amplified[..., 3] = 255
        Image.fromarray(amplified, "RGBA").save(diff_path)

    return {
        "status": "compared",
        "max_diff": max_diff,
        "mean_diff": mean_diff,
        "nonzero_px": nonzero_px,
        "total_px": total_px,
        "nonzero_px_percent": 100.0 * nonzero_px / total_px,
        "samples": samples,
    }


def passes(metrics, max_diff, mean_diff, nonzero_px_percent):
    if metrics["status"] != "compared":
        return False
    return (
        metrics["max_diff"] <= max_diff
        and metrics["mean_diff"] <= mean_diff
        and metrics["nonzero_px_percent"] <= nonzero_px_percent
    )


def write_reports(report_dir, report_name, rows, summary):
    report_dir.mkdir(parents=True, exist_ok=True)
    json_path = report_dir / f"{report_name}.json"
    csv_path = report_dir / f"{report_name}.csv"

    with json_path.open("w", encoding="utf-8") as handle:
        json.dump({"summary": summary, "cases": rows}, handle, indent=2, sort_keys=True)

    fields = [
        "id",
        "frame",
        "pass",
        "status",
        "max_diff",
        "mean_diff",
        "nonzero_px",
        "total_px",
        "nonzero_px_percent",
    ]
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})

    return json_path, csv_path


def case_has_effect(case, expected_effect):
    if not expected_effect:
        return True
    for effect in case.get("effects", []):
        if effect.get("name") == expected_effect or effect.get("match_name") == expected_effect:
            return True
    return False


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest")
    parser.add_argument("--reference-dir", required=True)
    parser.add_argument("--candidate-dir", required=True)
    parser.add_argument("--diff-dir", default="refs/diff")
    parser.add_argument("--report-dir", default="refs/reports")
    parser.add_argument("--report-name", default="manifest_diff")
    parser.add_argument("--case-id", action="append", default=None, help="verify only this case id; may be repeated")
    parser.add_argument("--expected-effect", default=None, help="skip cases that do not contain this effect name/matchName")
    parser.add_argument("--max-diff", type=float, default=0.0)
    parser.add_argument("--mean-diff", type=float, default=0.0)
    parser.add_argument("--nonzero-px-percent", type=float, default=0.0)
    args = parser.parse_args()

    manifest_path = Path(args.manifest).resolve()
    reference_dir = Path(args.reference_dir).resolve()
    candidate_dir = Path(args.candidate_dir).resolve()
    diff_dir = Path(args.diff_dir).resolve()
    report_dir = Path(args.report_dir).resolve()

    with manifest_path.open(encoding="utf-8-sig") as handle:
        manifest = json.load(handle)

    ok = fail = missing = 0
    rows = []
    allow_cases = set(args.case_id or [])
    print(f"=== verify {manifest_path.name} ===")
    for index, case in enumerate(manifest.get("cases", []), start=1):
        case_id = case.get("id") or f"case_{index:04d}"
        if allow_cases and case_id not in allow_cases:
            continue
        if not case_has_effect(case, args.expected_effect):
            print(f"[SKIP] {case_id:20s} missing effect {args.expected_effect}")
            continue
        frame = case.get("frame") or f"{case_id}.png"
        normalized_frame = normalized_relpath(frame)
        reference_path = reference_dir / normalized_frame
        candidate_path = candidate_dir / normalized_frame
        reference_path, candidate_path = resolve_compare_paths(reference_path, candidate_path)
        diff_path = diff_dir / f"{Path(normalized_frame).stem}_{case_id}_diff.png"
        row = {
            "id": case_id,
            "frame": frame,
            "normalized_frame": normalized_frame,
            "resolved_reference": str(reference_path.name),
            "resolved_candidate": str(candidate_path.name),
        }

        if not reference_path.exists() or not candidate_path.exists():
            row.update(
                {
                    "pass": False,
                    "status": "missing",
                    "missing_reference": not reference_path.exists(),
                    "missing_candidate": not candidate_path.exists(),
                }
            )
            missing += 1
            print(f"[MISSING] {case_id:20s} {frame}")
            rows.append(row)
            continue

        metrics = compare(reference_path, candidate_path, diff_path)
        row.update(metrics)
        row["pass"] = passes(metrics, args.max_diff, args.mean_diff, args.nonzero_px_percent)
        rows.append(row)
        if row["pass"]:
            ok += 1
            print(f"[OK]      {case_id:20s} max={metrics['max_diff']} mean={metrics['mean_diff']:.4f}")
        else:
            fail += 1
            if metrics["status"] == "compared":
                print(
                    f"[DIFF]    {case_id:20s} "
                    f"max={metrics['max_diff']} mean={metrics['mean_diff']:.4f} "
                    f"nz={metrics['nonzero_px']}/{metrics['total_px']}"
                )
            else:
                print(f"[DIFF]    {case_id:20s} {metrics['status']}")

    summary = {"ok": ok, "fail": fail, "missing": missing, "total": len(rows)}
    json_path, csv_path = write_reports(report_dir, args.report_name, rows, summary)
    print("---")
    print(f"ok={ok} fail={fail} missing={missing} total={len(rows)}")
    print(f"report_json={json_path}")
    print(f"report_csv={csv_path}")
    return 0 if fail == 0 and missing == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
