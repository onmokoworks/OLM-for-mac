from __future__ import annotations

import hashlib
import json
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from aex_loader import AexLoader

ROOT = Path(__file__).resolve().parents[2]
AEX = ROOT / "plugins_2025" / "OLMDirectionalBlur.aex"
OUT = ROOT / "replay" / "fixtures" / "dblur_rowdriver"

ROWDRIVER = 0x1800038D0
PREPASS = 0x180001000
SCATTER = 0x1800013E0


def f32(x: float) -> bytes:
    return struct.pack("<f", x)


def floats(values):
    return struct.pack("<%df" % len(values), *values)


def alloc_floats(ld, values, align=16):
    addr = ld.bump_alloc(len(values) * 4, align=align)
    ld.write_bytes(addr, floats(values))
    return addr


def alloc_rgba(ld, values):
    assert len(values) % 4 == 0
    return alloc_floats(ld, values, align=16)


def dump(ld, path: Path, addr: int, size: int):
    path.write_bytes(ld.read_bytes(addr, size))


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def make_leaf_fixture(ld):
    # One row with a nonzero center and asymmetric RGB/alpha values. Padding
    # keeps both helpers' signed neighbor accesses in mapped storage.
    n = 9
    source_values = []
    for i in range(n):
        source_values += [0.07 + i * 0.11, 0.19 + i * 0.07,
                          0.31 + i * 0.05, 0.20 + i * 0.06]
    source = alloc_rgba(ld, source_values)
    prepass = alloc_rgba(ld, [0.0] * (n * 4))
    denom = alloc_floats(ld, [0.0] * n)
    av = alloc_floats(ld, [0.0] * n)
    front_weights = alloc_floats(ld, [1.0, 0.82, 0.57, 0.31, 0.13, 0.0, 0.0, 0.0])
    back_weights = alloc_floats(ld, [1.0, 0.71, 0.44, 0.22, 0.08, 0.0, 0.0, 0.0])
    scatter_out = alloc_rgba(ld, [0.013, 0.017, 0.023, 0.029] * n)
    scatter_denom = alloc_floats(ld, [0.11 + i * 0.03 for i in range(n)])
    scatter_av = alloc_floats(ld, [0.09 + i * 0.02 for i in range(n)])
    return locals()


def run_leaf_fixtures(ld, case_dir: Path):
    q = make_leaf_fixture(ld)
    n = q["n"]
    for name, addr, size in (
        ("leaf_source.bin", q["source"], n * 16),
        ("leaf_front_weights.bin", q["front_weights"], 8 * 4),
        ("leaf_back_weights.bin", q["back_weights"], 8 * 4),
        ("leaf_initial_prepass.bin", q["prepass"], n * 16),
        ("leaf_initial_denom.bin", q["denom"], n * 4),
        ("leaf_initial_av.bin", q["av"], n * 4),
        ("leaf_initial_scatter_output.bin", q["scatter_out"], n * 16),
        ("leaf_initial_scatter_denom.bin", q["scatter_denom"], n * 4),
        ("leaf_initial_scatter_av.bin", q["scatter_av"], n * 4),
    ):
        dump(ld, case_dir / name, addr, size)
    pre_args = [2, 3, q["source"], q["prepass"], q["denom"], q["av"],
                q["front_weights"], 4, q["back_weights"], 3, n,
                struct.unpack("<I", f32(1.25))[0]]
    ld.call_function(PREPASS, int_args=pre_args, max_instructions=2000000)
    pre_raw = ld.read_bytes(q["prepass"], n * 16)
    dump(ld, case_dir / "prepass_output.bin", q["prepass"], n * 16)
    dump(ld, case_dir / "prepass_denom.bin", q["denom"], n * 4)
    dump(ld, case_dir / "prepass_av.bin", q["av"], n * 4)

    scatter_args = [3, 3, 1, q["source"], q["scatter_out"], q["scatter_denom"],
                    q["scatter_av"], q["front_weights"], 4, n,
                    struct.unpack("<I", f32(0.75))[0]]
    ld.call_function(SCATTER, int_args=scatter_args, max_instructions=2000000)
    dump(ld, case_dir / "scatter_output.bin", q["scatter_out"], n * 16)
    dump(ld, case_dir / "scatter_denom.bin", q["scatter_denom"], n * 4)
    dump(ld, case_dir / "scatter_av.bin", q["scatter_av"], n * 4)
    return {"width": n, "source_sha256": sha(case_dir / "leaf_source.bin"),
            "prepass_output_sha256": sha(case_dir / "prepass_output.bin"),
            "scatter_output_sha256": sha(case_dir / "scatter_output.bin"),
            "prepass_raw_len": len(pre_raw)}


def run_rowdriver(ld, case_dir: Path):
    width = 5
    source = alloc_rgba(ld, [0.11, 0.21, 0.37, 0.25,
                             0.23, 0.31, 0.43, 0.50,
                             0.41, 0.17, 0.59, 0.75,
                             0.67, 0.29, 0.13, 0.90,
                             0.83, 0.47, 0.71, 0.35])
    output = alloc_rgba(ld, [0.0] * (width * 4))
    source_slot = ld.host_alloc(8)
    output_slot = ld.host_alloc(8)
    ld.write_bytes(source_slot, struct.pack("<Q", source))
    ld.write_bytes(output_slot, struct.pack("<Q", output))

    params = ld.host_alloc(0x8200)
    ld.write_bytes(params, b"\x00" * 0x8200)
    front_table = alloc_floats(ld, [1.0, 0.8, 0.5, 0.25, 0.1, 0.0, 0.0, 0.0])
    back_table = alloc_floats(ld, [1.0, 0.7, 0.45, 0.2, 0.05, 0.0, 0.0, 0.0])
    pre_front = alloc_floats(ld, [1.0, 0.9, 0.6, 0.3, 0.1, 0.0, 0.0, 0.0])
    pre_back = alloc_floats(ld, [1.0, 0.85, 0.55, 0.2, 0.05, 0.0, 0.0, 0.0])
    comp_map = alloc_floats(ld, [1.0, 0.0, 0.0, 2.0] * width)
    prepass_out = alloc_rgba(ld, [0.0] * (width * 4))
    denom = alloc_floats(ld, [0.0] * width)
    av = alloc_floats(ld, [0.0] * width)
    for off, value in ((0x20, 0), (0x30, 1), (0x38, 2), (0x40, 0),
                       (0x44, 0), (0x48, 3), (0x4c, 3), (0x50, 3), (0x54, 3)):
        ld.write_bytes(params + off, struct.pack("<I", value))
    for off, value in ((0x58, front_table), (0x4068, back_table),
                       (0x3ed8, pre_front), (0x7ee8, pre_back),
                       (0x8080, denom), (0x8088, av), (0x8118, comp_map),
                       (0x8090, prepass_out)):
        ld.write_bytes(params + off, struct.pack("<Q", value))
    ld.write_bytes(params + 0x38, f32(2.0))
    dump(ld, case_dir / "rowdriver_source.bin", source, width * 16)
    dump(ld, case_dir / "rowdriver_params_input.bin", params, 0x8200)

    result = ld.call_function(ROWDRIVER,
                              int_args=[0, 1, source_slot, output_slot, width,
                                        0, params], max_instructions=10000000)
    dump(ld, case_dir / "rowdriver_output.bin", output, width * 16)
    dump(ld, case_dir / "rowdriver_denom.bin", denom, width * 4)
    dump(ld, case_dir / "rowdriver_av.bin", av, width * 4)
    return {"width": width, "rows": [0, 1], "instructions": result["instructions"],
            "output_sha256": sha(case_dir / "rowdriver_output.bin"),
            "denom_sha256": sha(case_dir / "rowdriver_denom.bin"),
            "av_sha256": sha(case_dir / "rowdriver_av.bin")}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    case_dir = OUT / "case_0001"
    case_dir.mkdir(exist_ok=True)
    ld = AexLoader(str(AEX), verbose=False)
    ld.register_libm_impls(max_threads=1)
    leaf = run_leaf_fixtures(ld, case_dir)
    row = run_rowdriver(ld, case_dir)
    manifest = {"schema": 1, "kind": "dblur_rowdriver_exact_microfixture",
                "aex": str(AEX.relative_to(ROOT)),
                "aex_sha256": sha(AEX), "fixture": "case_0001",
                "leaf": leaf, "rowdriver": row,
                "files": {p.name: sha(p) for p in sorted(case_dir.glob("*.bin"))},
                "exact_policy": "byte equality only; no tolerance"}
    (case_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
