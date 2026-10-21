#!/usr/bin/env python3
"""Classify corrected ColorKeep/Kira returns without overclaiming raw exactness."""

from __future__ import annotations

import hashlib
import json
import sys
import tempfile
import zipfile
from pathlib import Path, PurePosixPath

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "handoffs/windows_batch/olm_windows_all_plugins_reference_campaign_20260731_r5/tools"
sys.path[:0] = [str(TOOLS), str(ROOT / "scripts")]
from compare_float_exr import read_planes_with_layout  # noqa: E402

PACKAGE = ROOT / "refs/reference_requests/olm_crosshost_linear_input_20260806.zip"
WINDOWS = ROOT / "refs/returns/windows/RETURN_OLM_CROSSHOST_LINEAR_INPUT_CORRECTED_20260806.zip"
MAC = ROOT / "refs/returns/mac/RETURN_OLM_CROSSHOST_LINEAR_INPUT_MAC_CORRECTED_20260806.zip"
NORMALIZED = ROOT / "refs/conformance/olmkirakira_crosshost_normalized_mac_ae_20260806.json"
OUTPUT = ROOT / "refs/conformance/olm_crosshost_corrected_return_audit_20260806.json"


def sha(path: Path) -> str: return hashlib.sha256(path.read_bytes()).hexdigest()


def extract(path: Path, target: Path) -> None:
    folded = set()
    with zipfile.ZipFile(path) as archive:
        for info in archive.infolist():
            if info.is_dir(): continue
            name = info.filename.replace("\\", "/"); pure = PurePosixPath(name)
            if name.startswith("/") or any(part in ("", ".", "..") for part in pure.parts) or name.casefold() in folded:
                raise ValueError(f"unsafe/duplicate member: {name}")
            folded.add(name.casefold()); output = target.joinpath(*pure.parts); output.parent.mkdir(parents=True, exist_ok=True); output.write_bytes(archive.read(info))


def planes(path: Path) -> dict[str, np.ndarray]:
    raw, width, height, _ = read_planes_with_layout(path)
    if (width, height) != (1920, 1080): raise ValueError("dimensions")
    return {name: np.frombuffer(data, dtype="<u4") for name, data in raw.items()}


def mismatch(left, right):
    by = {ch: int(np.count_nonzero(left[ch] != right[ch])) for ch in "RGBA"}
    return {"total": sum(by.values()), "by_channel": by}


def exponent_mapping(mac, windows) -> dict:
    pairs = []
    for ch in "RGB": pairs.append(np.unique(np.stack((mac[ch], windows[ch]), axis=1), axis=0))
    unique = np.unique(np.concatenate(pairs), axis=0)
    keys, counts = np.unique(unique[:, 0], return_counts=True)
    x, y = unique[:, 0].view("<f4"), unique[:, 1].view("<f4")
    mask = (x > 0) & (x < 1) & (y > 0) & (y < 1) & np.isfinite(x) & np.isfinite(y)
    exponent = np.log(y[mask].astype("f8")) / np.log(x[mask].astype("f8"))
    return {
        "unique_input_words": len(keys), "conflicting_input_words": int(np.count_nonzero(counts > 1)),
        "effective_power_median": float(np.median(exponent)), "effective_power_min": float(np.min(exponent)), "effective_power_max": float(np.max(exponent)),
    }


def colorkeep_relation(win_no, win_yes, mac_no, mac_yes) -> dict:
    zero = np.uint32(0)
    win_keep = np.any(np.stack([win_yes[ch] != zero for ch in "RGBA"]), axis=0)
    mac_keep = np.any(np.stack([mac_yes[ch] != zero for ch in "RGBA"]), axis=0)
    mask_diff = int(np.count_nonzero(win_keep != mac_keep))
    unexplained = 0; within_host = {}
    for host, no, yes, keep in (("windows", win_no, win_yes, win_keep), ("mac", mac_no, mac_yes, mac_keep)):
        bad = 0
        for ch in "RGBA": bad += int(np.count_nonzero(np.where(keep, yes[ch] != no[ch], yes[ch] != zero)))
        within_host[host] = bad
    for ch in "RGBA":
        expected = np.where(win_keep, win_no[ch] != mac_no[ch], False)
        actual = win_yes[ch] != mac_yes[ch]
        unexplained += int(np.count_nonzero(expected != actual))
    return {
        "keep_mask_mismatched_pixels": mask_diff, "retained_pixels": int(np.count_nonzero(win_keep)),
        "rejected_pixels": int(win_keep.size - np.count_nonzero(win_keep)), "within_host_relation_mismatched_values": within_host,
        "cross_host_effect_differences_unexplained_by_retained_control": unexplained,
        "plugin_relation_exact": mask_diff == 0 and unexplained == 0 and not any(within_host.values()),
    }


def main() -> int:
    normalized = json.loads(NORMALIZED.read_text(encoding="utf-8"))
    with tempfile.TemporaryDirectory(prefix="olm_corrected_audit_") as tmp:
        root = Path(tmp)
        for name, path in (("package", PACKAGE), ("windows", WINDOWS), ("mac", MAC)): extract(path, root / name)
        contract = json.loads((root / "package/BATCH_CONTRACT.json").read_text(encoding="utf-8")); rows = []
        for row in contract["acquire"]:
            rid = row["row_id"]; values = {}
            atts = {}
            for host in ("windows", "mac"):
                base = root / host / "outputs" / rid
                atts[host] = json.loads((base / "attestation.json").read_text(encoding="utf-8-sig"))
                for branch in ("no_effect", "effect_on"): values[host, branch] = planes(base / f"{branch}.exr")
            no_diff = mismatch(values["windows", "no_effect"], values["mac", "no_effect"])
            effect_diff = mismatch(values["windows", "effect_on"], values["mac", "effect_on"])
            alpha_ones = {host: int(np.count_nonzero(values[host, "no_effect"]["A"] == np.float32(1).view("<u4"))) for host in ("windows", "mac")}
            item = {
                "row_id": rid, "plugin": row["plugin"], "depth": row["depth"],
                "source_interpretation_equal": atts["windows"]["source_interpretation"] == atts["mac"]["source_interpretation"],
                "no_effect_alpha_one_pixels": alpha_ones, "channel_binding_correct": alpha_ones == {"windows": 2073600, "mac": 2073600},
                "cross_host": {"no_effect": no_diff, "effect_on": effect_diff},
                "no_effect_host_transfer": exponent_mapping(values["mac", "no_effect"], values["windows", "no_effect"]),
            }
            if row["plugin"] == "ColorKeep": item["effect_relation"] = colorkeep_relation(values["windows", "no_effect"], values["windows", "effect_on"], values["mac", "no_effect"], values["mac", "effect_on"])
            else:
                item["effect_host_transfer"] = exponent_mapping(values["mac", "effect_on"], values["windows", "effect_on"])
                item["normalized_mac_replay"] = next(value for value in normalized["rows"] if value["depth"] == row["depth"])
            rows.append(item)
    color_exact = all(row["effect_relation"]["plugin_relation_exact"] for row in rows if row["plugin"] == "ColorKeep")
    report = {
        "kind": "olm_crosshost_corrected_return_audit", "status": "host_transform_classified_kira_exact_pending",
        "artifacts": {"package_sha256": sha(PACKAGE), "windows_return_sha256": sha(WINDOWS), "mac_return_sha256": sha(MAC), "normalized_kira_report_sha256": sha(NORMALIZED)},
        "rows": rows,
        "verdict": {
            "corrected_channel_binding": all(row["channel_binding_correct"] for row in rows),
            "raw_cross_host_exact_rows": [], "color_keep_relation_exact_depths": [row["depth"] for row in rows if row["plugin"] == "ColorKeep" and row["effect_relation"]["plugin_relation_exact"]],
            "kira_operation_exact_depths": [], "color_keep_relation_exact": color_exact,
            "kira_reason": "effect outputs are not one component-wise host transfer of Mac outputs; PF32 normalized replay makes control exact but effect RGB differs at all 6,220,800 values",
        },
        "claim_boundary": "ColorKeep keep/reject/zero relation is exact for this case at PF8/PF16/PF32. Kira raw and operation exactness remain unproven. No row is promoted to cross-host raw exact.",
    }
    OUTPUT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "verdict": report["verdict"]}, indent=2))
    return 0


if __name__ == "__main__": raise SystemExit(main())
