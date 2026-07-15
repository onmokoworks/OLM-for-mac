#!/usr/bin/env python3
"""Validate the DirectionalBlur Mac FLOAT EXR request remains fail-closed."""

from pathlib import Path
import json
import hashlib
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
REQUEST = ROOT / "refs/mac_validation_requests/olmdirectionalblur_32bpc_mac_validation_20260715.json"


def main() -> int:
    request = json.loads(REQUEST.read_text(encoding="utf-8"))
    assert request["status"] == "request_only_no_ae_exact_claim"
    assert request["ae_contract"]["bits_per_channel"] == 32
    assert request["ae_contract"]["renderer"] == "SOFTWARE"
    assert request["ae_contract"]["sample_type"] == "FLOAT"
    assert request["ae_contract"]["compression"] == "none"
    assert request["ae_contract"]["outputs"] == ["no_effect", "effect_on"]
    assert request["case"]["input"]["sha256"] != "REQUIRED_CAPTURE_AND_MATCH"
    assert len(request["case"]["input"]["sha256"]) == 64
    assert request["plugin_identity"]["sha256_required"] is True
    acceptance = request["acceptance"]
    assert acceptance["ae_exact_claim"] is False
    assert "any nonzero raw FLOAT32 word delta" in acceptance["fail_closed"]
    assert "control_gate" in acceptance
    runner = ROOT / "scripts/run_olmdirectionalblur_32bpc_mac_validation_20260715.py"
    reporter = ROOT / "scripts/report_olmdirectionalblur_32bpc_mac_validation_20260715.py"
    with tempfile.TemporaryDirectory(prefix="olmdirectionalblur_mac_smoke_") as raw:
        temp = Path(raw); plugin = temp / "OLMDirectionalBlur.plugin"; plugin.write_bytes(b"smoke plugin")
        dump = temp / "wrapper.jsx"
        bad = subprocess.run([sys.executable, str(runner), "--plugin-path", str(temp / "wrong.plugin"), "--dump-js", str(dump)], cwd=ROOT, text=True, capture_output=True)
        assert bad.returncode == 2 and not dump.exists()
        good = subprocess.run([sys.executable, str(runner), "--plugin-path", str(plugin), "--support-dir", str(temp / "support"), "--dump-js", str(dump)], cwd=ROOT, text=True, capture_output=True)
        assert good.returncode == 0, good.stdout + good.stderr
        jsx = (temp / "support" / "run_mac_olmdirectionalblur_32bpc_validation.jsx").read_text()
        for token in ("GpuAccelType.SOFTWARE", "bitsPerChannel", "OLM_AE_MAC_PLUGIN_PATH", "OLM EXR 32 Float", "getSettings(GetSettingsFormat.STRING)", "no_effect", "effect_on", "loadedHash", "FAIL_CLOSED"):
            assert token in jsx, token
        malformed = temp / "malformed.json"
        malformed.write_text(json.dumps({"ae_exact_claim": True}), encoding="utf-8")
        missing = subprocess.run([sys.executable, str(reporter), str(malformed)], cwd=ROOT, text=True, capture_output=True)
        assert missing.returncode != 0
    print("[OK] OLMDirectionalBlur 32bpc Mac validation contract smoke")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
