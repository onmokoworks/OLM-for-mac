#!/usr/bin/env python3
"""Fail-closed verifier for the minimal Windows AE release-boundary return."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import re
import sys
import tempfile
import zipfile
from pathlib import Path, PurePosixPath


SHA = re.compile(r"^[0-9a-f]{64}$")
PACKAGE_ID = "olm_windows_ae_release_boundary_minimal_20260806"


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def fail(message: str) -> None:
    raise ValueError(message)


def read_safe(path: Path) -> dict[str, bytes]:
    files = {}
    folded = set()
    with zipfile.ZipFile(path) as archive:
        for info in archive.infolist():
            if info.is_dir():
                continue
            name = info.filename.replace("\\", "/")
            pure = PurePosixPath(name)
            if name.startswith("/") or any(p in ("", ".", "..") for p in pure.parts):
                fail(f"unsafe member: {name}")
            if name.casefold() in folded:
                fail(f"duplicate Windows member: {name}")
            folded.add(name.casefold())
            files[name] = archive.read(info)
    return files


def locate(files: dict[str, bytes], suffix: str) -> tuple[str, bytes]:
    matches = [(n, b) for n, b in files.items() if n == suffix or n.endswith("/" + suffix)]
    if len(matches) != 1:
        fail(f"expected exactly one {suffix}; got {len(matches)}")
    return matches[0]


def load_exr_verifier():
    candidates = [
        Path(__file__).with_name("tools") / "verify_32bpc_float_return.py",
        Path(__file__).resolve().parents[1] / "handoffs/windows_batch/olm_windows_all_plugins_reference_campaign_20260731_r5/tools/verify_32bpc_float_return.py",
    ]
    source = next((p for p in candidates if p.is_file()), None)
    if source is None:
        fail("missing bundled FLOAT32 EXR verifier")
    spec = importlib.util.spec_from_file_location("olm_minimal_exr_verify", source)
    if spec is None or spec.loader is None:
        fail("cannot load bundled FLOAT32 EXR verifier")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def verify(return_zip: Path, contract_zip: Path | None = None) -> dict:
    returned = read_safe(return_zip)
    exr_verifier = load_exr_verifier()
    if contract_zip is None:
        local = Path(__file__).with_name("BATCH_CONTRACT.json")
        if not local.is_file():
            fail("pass package zip as second argument when verifier is outside the package")
        contract = json.loads(local.read_text(encoding="utf-8"))
    else:
        packaged = read_safe(contract_zip)
        contract = json.loads(locate(packaged, "BATCH_CONTRACT.json")[1])
    if contract.get("package_id") != PACKAGE_ID:
        fail("package_id mismatch")

    required_fields = set(contract["required_return"]["attestation_fields"])
    results = []
    for row in contract["acquire"]:
        row_id = row["row_id"]
        base = f"outputs/{row_id}"
        _, no_effect = locate(returned, f"{base}/no_effect.exr")
        _, effect_on = locate(returned, f"{base}/effect_on.exr")
        _, attestation_bytes = locate(returned, f"{base}/attestation.json")
        att = json.loads(attestation_bytes.decode("utf-8-sig"))
        missing = required_fields - set(att)
        if missing:
            fail(f"{row_id}: missing attestation fields: {sorted(missing)}")
        expected = {
            "row_id": row_id,
            "execution_row_sha256": row["execution_row_sha256"],
            "ae_version": "26.3x87",
            "renderer_raw": 1816,
            "bits_per_channel": row["depth"],
            "linear_blending": False,
            "aex_sha256": row["aex_sha256"],
            "source_sha256": row["source_sha256"],
            "no_effect_sha256": digest(no_effect),
            "effect_on_sha256": digest(effect_on),
        }
        for field, value in expected.items():
            if att.get(field) != value:
                fail(f"{row_id}: {field} mismatch")
        if att.get("working_space_raw") not in (None, ""):
            fail(f"{row_id}: working_space_raw is not None")
        for field in ("ae_executable_sha256", "aex_sha256", "no_effect_sha256", "effect_on_sha256"):
            if not isinstance(att.get(field), str) or not SHA.fullmatch(att[field]):
                fail(f"{row_id}: invalid {field}")
        if not isinstance(att.get("ae_pid"), int) or isinstance(att.get("ae_pid"), bool):
            fail(f"{row_id}: invalid ae_pid")
        if not att.get("module_base") or not att.get("ae_process_start_utc"):
            fail(f"{row_id}: incomplete process/module attestation")
        if att.get("parameters_before") != att.get("parameters_after"):
            fail(f"{row_id}: parameter readback drift")
        if no_effect == effect_on and not row.get("intentional_noop"):
            fail(f"{row_id}: enabled output unexpectedly equals disabled control")
        with tempfile.TemporaryDirectory(prefix="olm_minimal_exr_") as tmp:
            for name, payload in (("no_effect.exr", no_effect), ("effect_on.exr", effect_on)):
                path = Path(tmp) / name
                path.write_bytes(payload)
                try:
                    exr_verifier.inspect_float_rgba_exr(path, (row["comp"]["width"], row["comp"]["height"]))
                except exr_verifier.VerificationError as exc:
                    fail(f"{row_id}: invalid {name}: {exc}")
        results.append({"row_id": row_id, "status": "accepted", **{k: expected[k] for k in ("no_effect_sha256", "effect_on_sha256")}})
    return {"kind": "olm_windows_ae_release_boundary_minimal_intake", "status": "accepted", "rows": results}


def main() -> int:
    if len(sys.argv) not in (2, 3):
        print(f"usage: {Path(sys.argv[0]).name} RETURN.zip [PACKAGE.zip]", file=sys.stderr)
        return 2
    try:
        report = verify(Path(sys.argv[1]), Path(sys.argv[2]) if len(sys.argv) == 3 else None)
    except (OSError, ValueError, zipfile.BadZipFile, json.JSONDecodeError) as exc:
        print(f"[FAIL] {exc}", file=sys.stderr)
        return 1
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
