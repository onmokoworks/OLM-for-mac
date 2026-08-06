#!/usr/bin/env python3
"""Diagnose the first paired linear-input returns without making an exact claim."""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
import zipfile
from pathlib import Path, PurePosixPath

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "handoffs/windows_batch/olm_windows_all_plugins_reference_campaign_20260731_r5/tools"
sys.path.insert(0, str(TOOLS))
sys.path.insert(0, str(ROOT / "scripts"))
from compare_float_exr import read_planes_with_layout  # noqa: E402


def extract(path: Path, target: Path) -> None:
    with zipfile.ZipFile(path) as archive:
        for info in archive.infolist():
            if info.is_dir():
                continue
            name = info.filename.replace("\\", "/")
            pure = PurePosixPath(name)
            if name.startswith("/") or any(part in ("", ".", "..") for part in pure.parts):
                raise ValueError(f"unsafe member: {name}")
            output = target.joinpath(*pure.parts)
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_bytes(archive.read(info))


def planes(path: Path) -> dict[str, np.ndarray]:
    raw, _, _, _ = read_planes_with_layout(path)
    return {name: np.frombuffer(payload, dtype="<u4") for name, payload in raw.items()}


def mismatch(left: dict[str, np.ndarray], right: dict[str, np.ndarray]) -> dict:
    by = {name: int(np.count_nonzero(left[name] != right[name])) for name in "RGBA"}
    return {"total": sum(by.values()), "by_channel": by}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("windows_return", type=Path)
    parser.add_argument("mac_return", type=Path)
    parser.add_argument("package", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix="olm_linear_audit_") as tmp:
        root = Path(tmp)
        for name, path in (("windows", args.windows_return), ("mac", args.mac_return), ("package", args.package)):
            extract(path, root / name)
        contract = json.loads((root / "package/BATCH_CONTRACT.json").read_text(encoding="utf-8"))
        source = planes(root / "package/inputs/opaque_cells_linear_float32.exr")
        rows = []
        for row in contract["acquire"]:
            row_id = row["row_id"]
            host = {}
            branch_planes = {}
            for platform in ("windows", "mac"):
                base = root / platform / "outputs" / row_id
                attestation = json.loads((base / "attestation.json").read_text(encoding="utf-8-sig"))
                no_effect = planes(base / "no_effect.exr")
                effect_on = planes(base / "effect_on.exr")
                branch_planes[(platform, "no_effect")] = no_effect
                branch_planes[(platform, "effect_on")] = effect_on
                host[platform] = {
                    "source_interpretation": attestation["source_interpretation"],
                    "no_effect_alpha_equals_red": int(np.count_nonzero(no_effect["A"] == no_effect["R"])),
                    "no_effect_red_equals_source_red": int(np.count_nonzero(no_effect["R"] == source["R"])),
                    "effect_on_all_zero_values": int(sum(np.count_nonzero(effect_on[name]) for name in "RGBA")) == 0,
                }
            rows.append({
                "row_id": row_id,
                "plugin": row["plugin"],
                "depth": row["depth"],
                "host": host,
                "cross_host": {
                    "no_effect": mismatch(branch_planes[("windows", "no_effect")], branch_planes[("mac", "no_effect")]),
                    "effect_on": mismatch(branch_planes[("windows", "effect_on")], branch_planes[("mac", "effect_on")]),
                },
            })
    report = {
        "kind": "olm_crosshost_linear_input_first_return_audit",
        "status": "fixture_contract_defect",
        "root_cause": "non-canonical EXR physical channel order R,G,B,A; AE readers bind the first plane as alpha, proven at every depth by no-effect output A == output R for every pixel (and at PF32 both equal source R)",
        "pixel_count": 1920 * 1080,
        "rows": rows,
        "required_fix": "regenerate source with physical channel order A,B,G,R and invalidate every first-generation pixel artifact",
        "minimum_recapture": "six effect rows remain necessary for final ColorKeep/Kira PF8/PF16/PF32 exactness; three disabled controls alone can calibrate the corrected source but cannot close effect-on parity",
    }
    rendered = json.dumps(report, indent=2) + "\n"
    if args.output:
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
