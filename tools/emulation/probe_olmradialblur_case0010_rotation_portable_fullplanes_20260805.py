#!/usr/bin/env python3
"""Compare the current portable Rotation worker with the case_0010 AEX planes."""

from __future__ import annotations

import hashlib
import json
import os
import shlex
import subprocess
import tempfile
import zlib
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[2]
CPP = ROOT / "cli/OLMRadialBlur/main.cpp"
FIXTURE = ROOT / "refs/fixtures/olmradialblur_case0010_rotation_full_planes_20260805"
OUT_JSON = ROOT / "refs/conformance/olmradialblur_case0010_rotation_portable_fullplanes_20260805.json"
OUT_MD = ROOT / "refs/conformance/olmradialblur_case0010_rotation_portable_fullplanes_20260805.md"


def adapter_source() -> str:
    include = str(CPP).replace("\\", "\\\\").replace('"', '\\"')
    return f'''#define main olmradialblur_embedded_main
#include "{include}"
#undef main

static bool read_f32(const char *path, std::vector<float> &value, size_t count) {{
    std::ifstream stream(path, std::ios::binary);
    if (!stream) return false;
    value.resize(count);
    stream.read(reinterpret_cast<char *>(value.data()), static_cast<std::streamsize>(count * sizeof(float)));
    return stream.gcount() == static_cast<std::streamsize>(count * sizeof(float));
}}
static bool read_u8(const char *path, std::vector<uint8_t> &value, size_t count) {{
    std::ifstream stream(path, std::ios::binary);
    if (!stream) return false;
    value.resize(count);
    stream.read(reinterpret_cast<char *>(value.data()), static_cast<std::streamsize>(count));
    return stream.gcount() == static_cast<std::streamsize>(count);
}}
template <typename T> static bool write_vec(const std::string &path, const std::vector<T> &value) {{
    std::ofstream stream(path, std::ios::binary);
    if (!stream) return false;
    stream.write(reinterpret_cast<const char *>(value.data()),
                 static_cast<std::streamsize>(value.size() * sizeof(T)));
    return static_cast<bool>(stream);
}}

int main(int argc, char **argv) {{
    if (argc != 6) return 64;
    constexpr int width = 1800;
    constexpr int height = 1104;
    constexpr size_t cells = static_cast<size_t>(width) * height;
    RotationTypedPolarInput input;
    input.width = width;
    input.height = height;
    input.row_stride = width * 4;
    if (!read_f32(argv[1], input.rgba, cells * 4) ||
        !read_u8(argv[2], input.polar_valid, cells) ||
        !read_f32(argv[3], input.source_scalar, cells) ||
        !read_f32(argv[4], input.size_factor, cells)) return 65;
    FloatImage dummy;
    dummy.width = 1;
    dummy.height = 1;
    dummy.rgba = {{0.0f, 0.0f, 0.0f, 1.0f}};
    RadialBlurParams params;
    params.blur_type = 2;
    params.outer_strength = 4;
    params.outer_offset_mode = 1;
    params.inner_strength = 0;
    params.inner_offset_mode = 1;
    params.repeat_border = true;
    params.quality = 5.0;
    params.outer_source_scatter_prepass = true;
    params.aex_rotation_two_stage_worker = true;
    params.rotation_gaussian_mode = "double";
    g_rotation_gaussian_mode = params.rotation_gaussian_mode;
    RotationTypedPlanes planes;
    render_olmradialblur_rotation_float(dummy, params, &planes, 8, &input);
    const std::string prefix = argv[5];
    if (!write_vec(prefix + "accum.f32rgba", planes.accum.rgba) ||
        !write_vec(prefix + "scatter.f32", planes.scatter_alpha) ||
        !write_vec(prefix + "source.f32", planes.source_alpha) ||
        !write_vec(prefix + "collapsed.f32rgba", planes.collapsed.rgba)) return 66;
    return 0;
}}
'''


def compiler_flags() -> list[str]:
    result = subprocess.run(["pkg-config", "--cflags", "--libs", "libpng"],
                            check=False, capture_output=True, text=True)
    return shlex.split(result.stdout) if result.returncode == 0 else ["-lpng"]


def sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def compare(actual_path: Path, expected: bytes) -> dict:
    actual = actual_path.read_bytes()
    if len(actual) != len(expected):
        return {"size_match": False, "actual_bytes": len(actual), "expected_bytes": len(expected)}
    left = np.frombuffer(actual, dtype="<u4")
    right = np.frombuffer(expected, dtype="<u4")
    different = np.flatnonzero(left != right)
    actual_f32 = np.frombuffer(actual, dtype="<f4")
    expected_f32 = np.frombuffer(expected, dtype="<f4")
    finite = np.isfinite(actual_f32) & np.isfinite(expected_f32)
    max_abs = float(np.max(np.abs(actual_f32[finite] - expected_f32[finite]))) if np.any(finite) else None
    samples = [
        {
            "word": int(index),
            "actual_bits": f"0x{int(left[index]):08x}",
            "expected_bits": f"0x{int(right[index]):08x}",
            "actual_f32": float(actual_f32[index]),
            "expected_f32": float(expected_f32[index]),
        }
        for index in different[:4]
    ]
    return {
        "size_match": True,
        "actual_sha256": sha256(actual),
        "expected_sha256": sha256(expected),
        "different_words": int(different.size),
        "different_words_mod4": {
            str(lane): int(np.count_nonzero((different % 4) == lane)) for lane in range(4)
        },
        "first_different_word": int(different[0]) if different.size else None,
        "first_differences": samples,
        "max_abs_difference": max_abs,
        "bit_exact": different.size == 0,
    }


def main() -> int:
    manifest = json.loads((FIXTURE / "manifest.json").read_text())
    stages = {stage["stage"]: stage for stage in manifest["stages"]}

    def plane(stage: str, name: str) -> bytes:
        metadata = stages[stage]["planes"][name]
        encoded = (FIXTURE / metadata["path"]).read_bytes()
        if sha256(encoded) != metadata["zlib_sha256"]:
            raise RuntimeError(f"fixture identity mismatch: {stage}/{name}")
        raw = zlib.decompress(encoded)
        if sha256(raw) != metadata["raw_sha256"]:
            raise RuntimeError(f"fixture raw identity mismatch: {stage}/{name}")
        return raw

    with tempfile.TemporaryDirectory(prefix="olmradialblur_rotation_fullplane_") as value:
        temp = Path(value)
        source = temp / "adapter.cpp"
        binary = temp / "adapter"
        source.write_text(adapter_source(), encoding="utf-8")
        command = [os.environ.get("CXX", "clang++"), "-std=c++17", "-O2", "-DNDEBUG",
                   str(source), *compiler_flags(), "-o", str(binary)]
        build = subprocess.run(command, check=False, capture_output=True, text=True)
        if build.returncode:
            raise RuntimeError(f"adapter build failed:\n{build.stderr}")
        inputs = {
            "polar": plane("pre_scatter", "normalized_or_polar_rgba"),
            "valid": plane("post_scatter_pre_gather", "eligibility_mask"),
            "source": plane("pre_scatter", "slot_0x10"),
            "size": plane("pre_scatter", "slot_0x14"),
        }
        paths: dict[str, Path] = {}
        for name, raw in inputs.items():
            path = temp / f"{name}.bin"
            path.write_bytes(raw)
            paths[name] = path
        prefix = str(temp / "portable_")
        run = subprocess.run([str(binary), str(paths["polar"]), str(paths["valid"]),
                              str(paths["source"]), str(paths["size"]), prefix],
                             check=False, capture_output=True, text=True)
        if run.returncode:
            raise RuntimeError(f"adapter run failed ({run.returncode}):\n{run.stderr}")
        comparisons = {
            "accum_vs_post_normalize": compare(
                Path(prefix + "accum.f32rgba"), plane("post_normalize", "accum_rgba")),
            "scatter_vs_post_scatter": compare(
                Path(prefix + "scatter.f32"), plane("post_scatter_pre_gather", "max_alpha")),
            "source_vs_pre_scatter": compare(
                Path(prefix + "source.f32"), plane("pre_scatter", "slot_0x10")),
            "collapsed_vs_post_normalize": compare(
                Path(prefix + "collapsed.f32rgba"),
                plane("post_normalize", "normalized_or_polar_rgba")),
        }
    result = {
        "kind": "olmradialblur_case0010_rotation_portable_fullplanes_probe_20260805",
        "status": "bit_exact" if all(item.get("bit_exact") for item in comparisons.values()) else "mismatch",
        "implementation": "cli/OLMRadialBlur/main.cpp::render_olmradialblur_rotation_float",
        "comparisons": comparisons,
        "claim_boundary": "portable worker against retained case_0010 internal planes; no host writeback claim",
    }
    OUT_JSON.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    lines = [
        "# OLMRadialBlur case_0010 portable Rotation full-plane comparison (2026-08-05)",
        "",
        f"- Status: `{result['status']}`",
        "- Implementation: `cli/OLMRadialBlur/main.cpp::render_olmradialblur_rotation_float`",
    ]
    for name, comparison in comparisons.items():
        lines.append(
            f"- `{name}`: `{comparison['different_words']}` differing float32 words; "
            f"SHA-256 `{comparison['actual_sha256']}`"
        )
    lines.extend([
        "- The portable worker consumes the retained AEX polar RGBA, validity, source-scalar, "
        "and size-factor planes; no Windows machine is needed for this regression.",
        "- Claim boundary: " + result["claim_boundary"] + ".",
    ])
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["status"] == "bit_exact" else 1


if __name__ == "__main__":
    raise SystemExit(main())
