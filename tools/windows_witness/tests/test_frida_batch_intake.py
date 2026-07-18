from __future__ import annotations

import hashlib
import io
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
PACKAGE_SCRIPT = ROOT / "scripts" / "package_windows_frida_entrypoint_batch_20260718.py"
INTAKE_SCRIPT = ROOT / "scripts" / "intake_windows_frida_entrypoint_batch_20260718.py"


def _load_intake() -> Any:
    spec = importlib.util.spec_from_file_location("olm_frida_batch_intake", INTAKE_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load Frida batch intake module")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


INTAKE = _load_intake()


def _zip_write(path: Path, files: dict[str, bytes]) -> None:
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name in sorted(files):
            info = zipfile.ZipInfo(name)
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            archive.writestr(info, files[name], compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)


def _json(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=True, sort_keys=True, indent=2) + "\n").encode("utf-8")


def _package_batch(root: Path) -> Path:
    request_zip = root / "request.zip"
    subprocess.run(
        [sys.executable, str(PACKAGE_SCRIPT), "--output-dir", str(root / "request_dir"), "--zip", str(request_zip)],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return request_zip


def _synthesize_return(request_zip: Path, root: Path, *, tamper_manifest: bool = False,
                       mixed_identity: bool = False, missing_pf_cmd: bool = False) -> Path:
    request = INTAKE.request_batch(request_zip)
    request_files: dict[str, bytes]
    with zipfile.ZipFile(request_zip) as archive:
        request_files = {info.filename: archive.read(info) for info in archive.infolist() if not info.is_dir()}

    output: dict[str, bytes] = {"batch-manifest.json": request["manifest_bytes"]}
    rows: list[dict[str, Any]] = []
    for index, expected in enumerate(request["packages"], 1):
        package = expected["package"]
        package_bytes = request_files[f"packages/{package}"]
        package_files: dict[str, bytes]
        with zipfile.ZipFile(io.BytesIO(package_bytes)) as archive:
            package_files = {info.filename: archive.read(info) for info in archive.infolist() if not info.is_dir()}
        contract = json.loads(package_files["witness-contract.json"])
        plugin = contract["plugin"]
        project = contract["project"]
        case = contract["cases"][0]
        case_id = case["id"]
        module = plugin["module_filename"]
        aex_sha = plugin["aex_sha256"]
        renderer = project["renderer"]
        bpc = project["bits_per_channel"]
        run_id = f"fixture-frida-{index:02d}"
        pid = 4100 + index
        module_base = f"0x{0x180000000 + index * 0x10000:x}"
        entry = contract["transport"]["agent_config"]["exports"][0]
        entry_name = entry.get("name") or entry["export"]

        identity = {
            "run_id": run_id,
            "ae_pid": pid,
            "module_base": module_base,
            "aex_sha256": aex_sha,
            "renderer": renderer,
            "project_bpc": bpc,
            "case_id": case_id,
        }
        events = [
            {"sequence": 1, "event": "module_loaded", **identity},
            {
                "sequence": 2,
                "event": entry_name,
                "hook": entry_name,
                "rva": int(entry["rva"], 0) if isinstance(entry.get("rva"), str) else entry.get("rva", 0),
                "reads": {} if missing_pf_cmd else {"pf_cmd": {"type": "i32", "value": 3}},
                **identity,
            },
        ]
        if mixed_identity and index == 1:
            events[1]["case_id"] = "stale-case-from-another-run"

        run_root = f"runs/{Path(package).stem}"
        for name, data in package_files.items():
            output[f"{run_root}/{name}"] = data
        armed = {
            "run_id": run_id,
            "case_id": case_id,
            "ae_pid": pid,
            "module": module,
            "module_base": module_base,
            "aex_sha256": aex_sha,
            "renderer": renderer,
            "project_bpc": bpc,
        }
        result = {
            "status": "answered",
            "run_id": run_id,
            "module": module,
            "module_base": module_base,
            "aex_sha256": aex_sha,
            "identity": {
                "run_id": run_id,
                "ae_pid": pid,
                "module_base": module_base,
                "renderer": renderer,
                "project_bpc": bpc,
            },
        }
        output[f"{run_root}/armed.json"] = _json(armed)
        output[f"{run_root}/result-manifest.json"] = _json(result)
        output[f"{run_root}/events.jsonl"] = b"\n".join(
            json.dumps(event, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode("utf-8")
            for event in events
        ) + b"\n"
        output[f"{run_root}/ae_{case_id}.log"] = b"gpuAccelType=SOFTWARE\n"
        rows.append({"package": package, "package_sha256": hashlib.sha256(package_bytes).hexdigest(),
                     "status": "answered", "run_dir": Path(package).stem})

    status = {
        "schema_version": 1,
        "kind": "olm_frida_entrypoint_batch_return",
        "request_manifest_sha256": hashlib.sha256(request["manifest_bytes"]).hexdigest(),
        "status": "failed" if missing_pf_cmd else ("partial" if mixed_identity else "answered"),
        "packages": rows,
    }
    if tamper_manifest:
        status["request_manifest_sha256"] = "0" * 64
    output["batch_status.json"] = _json(status)
    return_zip = root / "return.zip"
    _zip_write(return_zip, output)
    return return_zip


class FridaBatchIntakeTests(unittest.TestCase):
    def test_six_lane_return_preserves_packages_and_is_accepted(self) -> None:
        with tempfile.TemporaryDirectory(prefix="olm_frida_batch_test_") as temp:
            root = Path(temp)
            request_zip = _package_batch(root)
            return_zip = _synthesize_return(request_zip, root)
            report = INTAKE.validate_return(return_zip, INTAKE.request_batch(request_zip))
            self.assertEqual(report["classification"], "accepted_all_answered")
            self.assertEqual(report["answered_count"], 6)
            self.assertEqual(report["failed_count"], 0)
            cli_report = root / "cli-report.json"
            completed = subprocess.run(
                [sys.executable, str(INTAKE_SCRIPT), str(return_zip), "--request-batch", str(request_zip),
                 "--output-json", str(cli_report)],
                cwd=ROOT,
                check=True,
                capture_output=True,
                text=True,
            )
            self.assertIn('"answered_count": 6', completed.stdout)
            self.assertEqual(json.loads(cli_report.read_text(encoding="utf-8"))["status"], "answered")

    def test_tampered_request_manifest_sha_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory(prefix="olm_frida_batch_test_") as temp:
            root = Path(temp)
            request_zip = _package_batch(root)
            return_zip = _synthesize_return(request_zip, root, tamper_manifest=True)
            with self.assertRaises(INTAKE.IntakeError):
                INTAKE.validate_return(return_zip, INTAKE.request_batch(request_zip))

    def test_mixed_event_identity_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory(prefix="olm_frida_batch_test_") as temp:
            root = Path(temp)
            request_zip = _package_batch(root)
            return_zip = _synthesize_return(request_zip, root, mixed_identity=True)
            report = INTAKE.validate_return(return_zip, INTAKE.request_batch(request_zip))
            self.assertEqual(report["answered_count"], 5)
            self.assertEqual(report["failed_count"], 1)

    def test_missing_typed_pf_cmd_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory(prefix="olm_frida_batch_test_") as temp:
            root = Path(temp)
            request_zip = _package_batch(root)
            return_zip = _synthesize_return(request_zip, root, missing_pf_cmd=True)
            report = INTAKE.validate_return(return_zip, INTAKE.request_batch(request_zip))
            self.assertEqual(report["answered_count"], 0)
            self.assertEqual(report["failed_count"], 6)


if __name__ == "__main__":
    unittest.main()
