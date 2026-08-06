#!/usr/bin/env python3
"""Fail-closed verifier for paired Windows/Mac cross-host linear-input returns."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
import tempfile
import zipfile
from pathlib import Path, PurePosixPath


def safe(path: Path) -> dict[str, bytes]:
    result, folded = {}, set()
    with zipfile.ZipFile(path) as archive:
        for info in archive.infolist():
            if info.is_dir():
                continue
            name = info.filename.replace("\\", "/")
            parts = PurePosixPath(name).parts
            if name.startswith("/") or any(part in ("", ".", "..") for part in parts) or name.casefold() in folded:
                raise ValueError(f"unsafe or duplicate member: {name}")
            folded.add(name.casefold())
            result[name] = archive.read(info)
    return result


def locate(files: dict[str, bytes], suffix: str) -> bytes:
    values = [value for name, value in files.items() if name == suffix or name.endswith("/" + suffix)]
    if len(values) != 1:
        raise ValueError(f"expected one {suffix}, got {len(values)}")
    return values[0]


def comparator(package: Path):
    tools = Path(__file__).resolve().parents[1] / "handoffs/windows_batch/olm_windows_all_plugins_reference_campaign_20260731_r5/tools"
    if tools.is_dir():
        sys.path.insert(0, str(tools))
    source = Path(__file__).resolve().parents[1] / "scripts/compare_float_exr.py"
    if not source.is_file():
        source = package.parent / "scripts/compare_float_exr.py"
    spec = importlib.util.spec_from_file_location("olm_linear_compare", source)
    if spec is None or spec.loader is None:
        raise ValueError("FLOAT32 comparator missing")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def verify(windows_zip: Path, mac_zip: Path, package_zip: Path) -> dict:
    package, windows, mac = safe(package_zip), safe(windows_zip), safe(mac_zip)
    contract = json.loads(locate(package, "BATCH_CONTRACT.json"))
    if contract.get("package_id") != "olm_crosshost_linear_input_20260806" or len(contract.get("acquire", [])) != 6:
        raise ValueError("contract identity or row count")
    compare = comparator(package_zip)
    rows = []
    with tempfile.TemporaryDirectory(prefix="olm_linear_verify_") as tmp:
        root = Path(tmp)
        for row in contract["acquire"]:
            row_id = row["row_id"]
            branches = {}
            for branch in ("no_effect", "effect_on"):
                suffix = f"outputs/{row_id}/{branch}.exr"
                left, right = locate(windows, suffix), locate(mac, suffix)
                lp, rp = root / f"{row_id}_{branch}_win.exr", root / f"{row_id}_{branch}_mac.exr"
                lp.write_bytes(left); rp.write_bytes(right)
                result = compare.compare(lp, rp)
                if result.get("equal") is not True or result.get("nonzero_count") != 0:
                    raise ValueError(f"{row_id}/{branch}: raw FLOAT32 mismatch")
                branches[branch] = {"exact": True, "sha256_windows": hashlib.sha256(left).hexdigest(), "sha256_mac": hashlib.sha256(right).hexdigest()}
            interpretations = []
            for host, files in (("windows", windows), ("mac", mac)):
                att = json.loads(locate(files, f"outputs/{row_id}/attestation.json").decode("utf-8-sig"))
                interpretation = att.get("source_interpretation", {})
                available = interpretation.get("preserve_rgb_api_available")
                if not isinstance(available, bool):
                    raise ValueError(f"{row_id}/{host}: Preserve RGB API availability not attested")
                if available and interpretation.get("preserve_rgb") is not True:
                    raise ValueError(f"{row_id}/{host}: available Preserve RGB API is not true")
                if interpretation.get("source_extension") != ".exr" or not isinstance(interpretation.get("color_profile_name"), str):
                    raise ValueError(f"{row_id}/{host}: EXR/profile readback incomplete")
                if att.get("source_sha256") != row["source_sha256"] or att.get("execution_row_sha256") != row["execution_row_sha256"]:
                    raise ValueError(f"{row_id}/{host}: source/row identity")
                interpretations.append(interpretation)
            for field in ("alpha_mode", "color_profile_name", "source_extension"):
                if interpretations[0].get(field) != interpretations[1].get(field):
                    raise ValueError(f"{row_id}: source interpretation {field} differs cross-host")
            rows.append({"row_id": row_id, "status": "exact", "branches": branches})
    return {"kind": "olm_crosshost_linear_input_verification", "status": "exact", "rows": rows, "claim_boundary": contract["claim_boundary"]}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("windows_return", type=Path)
    parser.add_argument("mac_return", type=Path)
    parser.add_argument("package", type=Path)
    args = parser.parse_args()
    try:
        print(json.dumps(verify(args.windows_return, args.mac_return, args.package), indent=2))
    except (OSError, ValueError, KeyError, json.JSONDecodeError, zipfile.BadZipFile) as exc:
        print(f"[FAIL] {exc}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
