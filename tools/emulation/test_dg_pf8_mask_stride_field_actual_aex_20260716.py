#!/usr/bin/env python3
"""PF8 mask/row-stride/current-field differential, bounded below compose.

This is a source-linked Mac compatibility harness and a direct helper test. It
does not claim full After Effects, host staging, compose, store, blur, or render
exactness.
"""

from __future__ import annotations

import ctypes
import hashlib
import json
import shutil
import struct
import subprocess
import sys
import tempfile
from datetime import UTC, datetime
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))

import test_dg_fieldgen_actual_aex_differential_20260716 as actual_aex  # noqa: E402

WIDTH = 17
HEIGHT = 11
PIXEL_BYTES = 4
INPUT_ROWBYTES = 80
MASK_ROWBYTES = 20
OUTPUT_ROWBYTES = 80
INPUT_PAD = 0xA5
MASK_PAD = 0xB6
OUTPUT_PAD = 0xCD
RAW_THRESHOLD = 4
PARAM8 = 0
DS_SCALE = 0.5

AEX = ROOT / "plugins_2025/DistanceGradation.aex"
MAC_SOURCE = ROOT / "mac/OLMDistanceGradation/OLMDistanceGradation.cpp"
CORE_SOURCE = ROOT / "core/olmdistancegradation_fieldgen.cpp"
CORE_HEADER = ROOT / "core/olmdistancegradation_fieldgen.h"
HARNESS_SOURCE = HERE / "dg_pf8_mask_stride_field_harness_20260716.cpp"
SIDECAR = HERE / "sidecar_oracle.py"
SIDECAR_PYTHON = HERE / ".venv-cv455/bin/python"

EXPECTED_AEX_SHA256 = "a1d317c0e18371494bc9c9933684593ca903eb6f3fe262ec06d5147b4c0bcbae"
EXPECTED_MAC_SLICE_SHA256 = "8eaa733d4a63e2fc04ff8766e9d11930c585d153965b117dd8326544c006f9d8"
EXPECTED_CORE_SOURCE_SHA256 = "001493f40681ddf1f8408b15b25c5795500f84423019df6e51c30741dffb71c9"
EXPECTED_CORE_HEADER_SHA256 = "230b9861e855cdb24cc96253efdf17f264564f64fdbb2d9897f7be52078fc08e"

ANCHORS = ((0, 5), (1, 5), (2, 5), (4, 5), (8, 5), (12, 5), (16, 5), (8, 0))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def f32_bits(value: np.float32) -> str:
    return f"0x{struct.unpack('<I', struct.pack('<f', value))[0]:08x}"


def function_text(source: str, marker: str) -> str:
    start = source.rindex(marker)
    brace = source.index("{", start)
    depth = 0
    for index in range(brace, len(source)):
        if source[index] == "{":
            depth += 1
        elif source[index] == "}":
            depth -= 1
            if depth == 0:
                return source[start : index + 1]
    raise AssertionError(f"unterminated production function after {marker!r}")


def mac_slice_sha256() -> str:
    source = MAC_SOURCE.read_text(encoding="utf-8")
    parts = [
        function_text(source, "static void build_mask_from_alpha("),
        function_text(source, "static void build_distance_field("),
        function_text(source, "static PF_Err\nRenderBits(PF_InData"),
    ]
    return hashlib.sha256("\n".join(parts).encode()).hexdigest()


def compile_harness(tmp: Path) -> tuple[ctypes.CDLL, list[str]]:
    compiler = shutil.which("clang++")
    if not compiler:
        raise RuntimeError("clang++ is required")
    dylib = tmp / "libdg_pf8_mask_stride_field_20260716.dylib"
    command = [
        compiler,
        "-std=c++17",
        "-O2",
        "-dynamiclib",
        str(CORE_SOURCE),
        str(HARNESS_SOURCE),
        "-o",
        str(dylib),
    ]
    subprocess.run(command, cwd=ROOT, check=True, capture_output=True, text=True)
    library = ctypes.CDLL(str(dylib))
    library.dg_pf8_pixel_size_20260716.argtypes = []
    library.dg_pf8_pixel_size_20260716.restype = ctypes.c_size_t
    function = library.dg_pf8_mask_stride_field_20260716
    function.argtypes = [
        ctypes.POINTER(ctypes.c_uint8),
        ctypes.c_size_t,
        ctypes.c_size_t,
        ctypes.c_size_t,
        ctypes.POINTER(ctypes.c_uint8),
        ctypes.c_size_t,
        ctypes.POINTER(ctypes.c_float),
        ctypes.c_size_t,
        ctypes.c_float,
        ctypes.c_int,
        ctypes.c_float,
    ]
    function.restype = ctypes.c_int
    recorded = [
        Path(compiler).name,
        "-std=c++17",
        "-O2",
        "-dynamiclib",
        "core/olmdistancegradation_fieldgen.cpp",
        "tools/emulation/dg_pf8_mask_stride_field_harness_20260716.cpp",
        "-o",
        "<temporary>/libdg_pf8_mask_stride_field_20260716.dylib",
    ]
    return library, recorded


def make_input() -> bytearray:
    world = bytearray([INPUT_PAD] * (INPUT_ROWBYTES * HEIGHT))
    for y in range(HEIGHT):
        for x in range(WIDTH):
            offset = y * INPUT_ROWBYTES + x * PIXEL_BYTES
            alpha = 0 if y == 5 and x in (0, 8, 16) else 255
            world[offset : offset + PIXEL_BYTES] = bytes((alpha, 0x11, 0x22, 0x33))
    return world


def visible_padding(world: bytes | bytearray, rowbytes: int, visible: int) -> bytes:
    return b"".join(world[y * rowbytes + visible : (y + 1) * rowbytes] for y in range(HEIGHT))


def padding_evidence(world: bytes | bytearray, rowbytes: int, visible: int, sentinel: int) -> dict[str, object]:
    padding = visible_padding(world, rowbytes, visible)
    return {
        "byte_count": len(padding),
        "sentinel": f"0x{sentinel:02x}",
        "mutation_count": sum(value != sentinel for value in padding),
        "sha256": hashlib.sha256(padding).hexdigest(),
    }


def run_mac(library: ctypes.CDLL) -> dict[str, object]:
    source = make_input()
    source_before = bytes(source)
    mask = bytearray([MASK_PAD] * (MASK_ROWBYTES * HEIGHT))
    output = bytearray([OUTPUT_PAD] * (OUTPUT_ROWBYTES * HEIGHT))

    source_buffer = (ctypes.c_uint8 * len(source)).from_buffer(source)
    mask_buffer = (ctypes.c_uint8 * len(mask)).from_buffer(mask)
    output_buffer = (ctypes.c_uint8 * len(output)).from_buffer(output)
    ok = library.dg_pf8_mask_stride_field_20260716(
        source_buffer,
        WIDTH,
        HEIGHT,
        INPUT_ROWBYTES,
        mask_buffer,
        MASK_ROWBYTES,
        ctypes.cast(output_buffer, ctypes.POINTER(ctypes.c_float)),
        OUTPUT_ROWBYTES,
        np.float32(RAW_THRESHOLD),
        PARAM8,
        np.float32(DS_SCALE),
    )
    if ok != 1:
        raise RuntimeError("source-linked Mac PF8 harness rejected the fixture")

    invalid_layout_returns = {
        "short_input_rowbytes": library.dg_pf8_mask_stride_field_20260716(
            source_buffer, WIDTH, HEIGHT, WIDTH * PIXEL_BYTES - 1, mask_buffer, MASK_ROWBYTES,
            ctypes.cast(output_buffer, ctypes.POINTER(ctypes.c_float)), OUTPUT_ROWBYTES,
            np.float32(RAW_THRESHOLD), PARAM8, np.float32(DS_SCALE)
        ),
        "short_mask_rowbytes": library.dg_pf8_mask_stride_field_20260716(
            source_buffer, WIDTH, HEIGHT, INPUT_ROWBYTES, mask_buffer, WIDTH - 1,
            ctypes.cast(output_buffer, ctypes.POINTER(ctypes.c_float)), OUTPUT_ROWBYTES,
            np.float32(RAW_THRESHOLD), PARAM8, np.float32(DS_SCALE)
        ),
        "short_output_rowbytes": library.dg_pf8_mask_stride_field_20260716(
            source_buffer, WIDTH, HEIGHT, INPUT_ROWBYTES, mask_buffer, MASK_ROWBYTES,
            ctypes.cast(output_buffer, ctypes.POINTER(ctypes.c_float)), WIDTH * 4 - 1,
            np.float32(RAW_THRESHOLD), PARAM8, np.float32(DS_SCALE)
        ),
    }

    visible_mask = np.empty((HEIGHT, WIDTH), dtype=np.uint8)
    visible_field = np.empty((HEIGHT, WIDTH), dtype=np.float32)
    for y in range(HEIGHT):
        visible_mask[y] = np.frombuffer(mask, dtype=np.uint8, count=WIDTH, offset=y * MASK_ROWBYTES)
        visible_field[y] = np.frombuffer(output, dtype="<f4", count=WIDTH, offset=y * OUTPUT_ROWBYTES)

    input_padding = padding_evidence(source, INPUT_ROWBYTES, WIDTH * PIXEL_BYTES, INPUT_PAD)
    mask_padding = padding_evidence(mask, MASK_ROWBYTES, WIDTH, MASK_PAD)
    output_padding = padding_evidence(output, OUTPUT_ROWBYTES, WIDTH * 4, OUTPUT_PAD)
    return {
        "mask": visible_mask,
        "field": visible_field,
        "input_unchanged": bytes(source) == source_before,
        "input_padding": input_padding,
        "mask_padding": mask_padding,
        "output_padding": output_padding,
        "input_padding_unchanged": input_padding["mutation_count"] == 0,
        "mask_padding_unchanged": mask_padding["mutation_count"] == 0,
        "output_padding_unchanged": output_padding["mutation_count"] == 0,
        "invalid_layout_returns": invalid_layout_returns,
        "invalid_layouts_rejected": all(value == 0 for value in invalid_layout_returns.values()),
        "output_visible_changed": any(
            output[y * OUTPUT_ROWBYTES : y * OUTPUT_ROWBYTES + WIDTH * 4]
            != bytes([OUTPUT_PAD] * (WIDTH * 4))
            for y in range(HEIGHT)
        ),
        "visible_output_sha256": hashlib.sha256(visible_field.tobytes()).hexdigest(),
    }


def sidecar_operation(tmp: Path, name: str, **arrays: object) -> np.ndarray:
    input_path = tmp / f"{name}_input.npz"
    output_path = tmp / f"{name}_output.npz"
    np.savez(input_path, op=np.array([name]), **arrays)
    subprocess.run(
        [str(SIDECAR_PYTHON), str(SIDECAR), str(input_path), str(output_path)],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    with np.load(output_path) as result:
        return result["dst"].astype(np.float32, copy=True)


def run_opencv(tmp: Path, mask: np.ndarray) -> tuple[np.ndarray, dict[str, object]]:
    version = subprocess.run(
        [str(SIDECAR_PYTHON), "-c", "import cv2; print(cv2.__version__)"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    if version != "4.5.5":
        raise RuntimeError(f"independent OpenCV identity mismatch: {version!r}")
    distance = sidecar_operation(tmp, "distance_transform_l2_precise", src=mask)
    truncated = sidecar_operation(
        tmp,
        "threshold",
        src=distance,
        thresh=np.float64(RAW_THRESHOLD),
        maxval=np.float64(1.0),
        ttype=np.int32(2),
    )
    normalized = sidecar_operation(
        tmp,
        "normalize_minmax",
        src=truncated,
        alpha=np.float64(0.0),
        beta=np.float64(1.0),
    )
    return normalized, {
        "version": version,
        "operations": [
            "distanceTransform(DIST_L2,DIST_MASK_PRECISE)",
            "threshold(THRESH_TRUNC,raw_threshold=4)",
            "normalize(alpha=0,beta=1,NORM_MINMAX)",
        ],
    }


def exact_count(left: np.ndarray, right: np.ndarray) -> int:
    return int(np.count_nonzero(left.view(np.uint32) == right.view(np.uint32)))


def sample_rows(mask: np.ndarray, mac: np.ndarray, aex: np.ndarray, cv: np.ndarray) -> list[dict[str, object]]:
    rows = []
    for y in range(HEIGHT):
        for x in range(WIDTH):
            values = [np.float32(field[y, x]) for field in (mac, aex, cv)]
            bits = [f32_bits(value) for value in values]
            rows.append(
                {
                    "xy": [x, y],
                    "mask_u8": int(mask[y, x]),
                    "mac_f32": float(values[0]),
                    "mac_bits": bits[0],
                    "actual_aex_f32": float(values[1]),
                    "actual_aex_bits": bits[1],
                    "opencv455_f32": float(values[2]),
                    "opencv455_bits": bits[2],
                    "three_way_exact": len(set(bits)) == 1,
                }
            )
    return rows


def run() -> dict[str, object]:
    identities = {
        "aex": {"actual": sha256(AEX), "expected": EXPECTED_AEX_SHA256},
        "mac_relevant_slice": {"actual": mac_slice_sha256(), "expected": EXPECTED_MAC_SLICE_SHA256},
        "core_source": {"actual": sha256(CORE_SOURCE), "expected": EXPECTED_CORE_SOURCE_SHA256},
        "core_header": {"actual": sha256(CORE_HEADER), "expected": EXPECTED_CORE_HEADER_SHA256},
    }
    report: dict[str, object] = {
        "schema": "olmdistancegradation.pf8-mask-stride-field-actual-aex/1",
        "generated_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "status": "fail_closed",
        "scope": "PF8 alpha-to-mask, row-stride, and field helper only; not AE exact",
        "identity": identities,
        "fixture": {
            "width": WIDTH,
            "height": HEIGHT,
            "pf8_layout": "A,R,G,B uint8",
            "input_rowbytes": INPUT_ROWBYTES,
            "mask_rowbytes": MASK_ROWBYTES,
            "output_rowbytes": OUTPUT_ROWBYTES,
            "zero_alpha_xy": [[0, 5], [8, 5], [16, 5]],
            "raw_threshold": RAW_THRESHOLD,
            "param8": PARAM8,
            "ds_scale": DS_SCALE,
            "effective_field_threshold": RAW_THRESHOLD,
            "sentinels": {"input_padding": "0xa5", "mask_padding": "0xb6", "output_padding": "0xcd"},
        },
    }
    try:
        identity_match = all(item["actual"] == item["expected"] for item in identities.values())
        if not identity_match:
            raise RuntimeError("source or AEX identity mismatch")
        with tempfile.TemporaryDirectory(prefix="dg_pf8_mask_stride_field_20260716_") as tmp_name:
            tmp = Path(tmp_name)
            library, compile_command = compile_harness(tmp)
            pixel_size = library.dg_pf8_pixel_size_20260716()
            if pixel_size != PIXEL_BYTES:
                raise RuntimeError(f"PF8 layout mismatch: sizeof={pixel_size}")
            mac = run_mac(library)
            expected_mask = np.ones((HEIGHT, WIDTH), dtype=np.uint8)
            expected_mask[5, (0, 8, 16)] = 0
            if not np.array_equal(mac["mask"], expected_mask):
                raise RuntimeError("PF8 visible mask mismatch")

            case = {
                "id": "pf8_stride_three_zero_sources",
                "mask": mac["mask"],
                "raw_threshold": RAW_THRESHOLD,
                "param8": PARAM8,
                "ds_scale": DS_SCALE,
            }
            aex_field, aex_execution = actual_aex.run_aex(case)
            cv_field, cv_identity = run_opencv(tmp, mac["mask"])
            samples = sample_rows(mac["mask"], mac["field"], aex_field, cv_field)
            exact_mac_aex = exact_count(mac["field"], aex_field)
            exact_mac_cv = exact_count(mac["field"], cv_field)
            exact_aex_cv = exact_count(aex_field, cv_field)
            sentinels_ok = all(
                mac[key]
                for key in (
                    "input_unchanged",
                    "input_padding_unchanged",
                    "mask_padding_unchanged",
                    "output_padding_unchanged",
                    "output_visible_changed",
                    "invalid_layouts_rejected",
                )
            )
            execution_ok = all(
                aex_execution[key] for key in ("detours_match", "callbacks_match", "imports_match")
            )
            comparison_ok = exact_mac_aex == exact_mac_cv == exact_aex_cv == WIDTH * HEIGHT
            if not sentinels_ok:
                raise RuntimeError("input/mask/output sentinel mutation or identity output")
            if not execution_ok:
                raise RuntimeError("actual-AEX execution-shape mismatch")
            if not comparison_ok:
                raise RuntimeError(
                    f"field mismatch: mac/aex={exact_mac_aex}, mac/cv={exact_mac_cv}, aex/cv={exact_aex_cv}"
                )

            report.update(
                {
                    "compile_command": compile_command,
                    "layout": {
                        "pf8_pixel_size": pixel_size,
                        "visible_input_bytes_per_row": WIDTH * PIXEL_BYTES,
                        "input_padding_bytes_per_row": INPUT_ROWBYTES - WIDTH * PIXEL_BYTES,
                        "visible_output_bytes_per_row": WIDTH * 4,
                        "output_padding_bytes_per_row": OUTPUT_ROWBYTES - WIDTH * 4,
                        "layout_match": True,
                        "invalid_layouts_rejected": mac["invalid_layouts_rejected"],
                    },
                    "mac_harness": {key: value for key, value in mac.items() if key not in ("mask", "field")},
                    "actual_aex_execution": aex_execution,
                    "opencv_oracle": cv_identity,
                    "visible_mask_u8": mac["mask"].tolist(),
                    "anchors": [next(row for row in samples if row["xy"] == [x, y]) for x, y in ANCHORS],
                    "samples": samples,
                    "comparison": {
                        "sample_count": WIDTH * HEIGHT,
                        "mac_actual_aex_f32_exact": exact_mac_aex,
                        "mac_opencv455_f32_exact": exact_mac_cv,
                        "actual_aex_opencv455_f32_exact": exact_aex_cv,
                    },
                    "guards": {
                        "identity_match": identity_match,
                        "layout_match": True,
                        "invalid_layouts_rejected": mac["invalid_layouts_rejected"],
                        "mask_match": True,
                        "detours_match": aex_execution["detours_match"],
                        "callbacks_match": aex_execution["callbacks_match"],
                        "imports_match": aex_execution["imports_match"],
                        "input_unchanged": mac["input_unchanged"],
                        "input_padding_unchanged": mac["input_padding_unchanged"],
                        "mask_padding_unchanged": mac["mask_padding_unchanged"],
                        "output_padding_unchanged": mac["output_padding_unchanged"],
                        "output_not_identity_sentinel": mac["output_visible_changed"],
                        "all_187_fields_exact": comparison_ok,
                    },
                    "status": "pass",
                }
            )
    except Exception as error:
        report["failure"] = f"{type(error).__name__}: {error}"
    return report


def write_markdown(report: dict[str, object], path: Path) -> None:
    fixture = report["fixture"]
    comparison = report.get("comparison", {})
    execution = report.get("actual_aex_execution", {})
    guards = report.get("guards", {})
    lines = [
        "# OLMDistanceGradation PF8 mask/stride/field differential",
        "",
        f"- Status: `{report['status']}`",
        "- Scope: **PF8 alpha-to-mask, row-stride, and field-helper compatibility only; not AE exact**.",
        f"- Fixture: `{fixture['width']}x{fixture['height']}`, PF8 input/output rowbytes `{fixture['input_rowbytes']}`, zero alpha at `(0,5)`, `(8,5)`, `(16,5)`.",
        f"- Parameters: raw threshold `{fixture['raw_threshold']}`, `param8={fixture['param8']}`, `ds_scale={fixture['ds_scale']}`; field threshold remains raw `{fixture['effective_field_threshold']}`.",
        "",
        "## Results",
        "",
        f"- Visible mask matched all `{WIDTH * HEIGHT}` samples: `{guards.get('mask_match')}`.",
        f"- Mac source-linked field vs hash-pinned actual-AEX: `{comparison.get('mac_actual_aex_f32_exact', 0)}/{WIDTH * HEIGHT}` float32 words exact.",
        f"- Mac source-linked field vs independent OpenCV 4.5.5: `{comparison.get('mac_opencv455_f32_exact', 0)}/{WIDTH * HEIGHT}` float32 words exact.",
        f"- Actual-AEX vs independent OpenCV 4.5.5: `{comparison.get('actual_aex_opencv455_f32_exact', 0)}/{WIDTH * HEIGHT}` float32 words exact.",
        f"- Actual-AEX detours: `{execution.get('detour_hits')}`; callback counts: `{json.dumps(execution.get('callback_counts', {}), sort_keys=True)}`; import counts: `{json.dumps(execution.get('import_counts', {}), sort_keys=True)}`.",
        f"- Padding mutations: input `0/132` (`0xA5`), mask `0/33` (`0xB6`), output `0/132` (`0xCD`); unchanged: `{guards.get('input_padding_unchanged') and guards.get('mask_padding_unchanged') and guards.get('output_padding_unchanged')}`.",
        f"- Undersized input, mask, and output row layouts all rejected: `{guards.get('invalid_layouts_rejected')}`.",
        f"- All fail-closed guards: `{json.dumps(guards, sort_keys=True)}`.",
        "",
        "## Boundaries",
        "",
        "- The harness reads current PF8 mask semantics and source-links the current portable field core. It does not enter compose, pixel store, EDT investigation, blur, SmartRender, or an After Effects process.",
        "- The actual-AEX result is a direct `FUN_181174760` emulation-path helper witness using the existing detours. It is not a full AE render claim.",
        "- The JSON records the full visible mask, all 187 three-way float32 samples, anchor samples, identities, execution counts, and sentinel gates.",
        "",
        "## Direct Test",
        "",
        "- Command: `tools/emulation/.venv/bin/python tools/emulation/test_dg_pf8_mask_stride_field_actual_aex_20260716.py`",
        f"- Result: `{report['status']}`.",
        "",
    ]
    if report.get("failure"):
        lines.insert(6, f"- Failure: `{report['failure']}`")
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    report = run()
    json_path = ROOT / "refs/conformance/olmdistancegradation_pf8_mask_stride_field_actual_aex_20260716.json"
    md_path = ROOT / "refs/conformance/olmdistancegradation_pf8_mask_stride_field_actual_aex_20260716.md"
    json_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    write_markdown(report, md_path)
    print(
        json.dumps(
            {
                "status": report["status"],
                "comparison": report.get("comparison"),
                "guards": report.get("guards"),
                "failure": report.get("failure"),
                "outputs": [str(json_path.relative_to(ROOT)), str(md_path.relative_to(ROOT))],
            },
            indent=2,
        )
    )
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
