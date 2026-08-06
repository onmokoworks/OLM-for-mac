import importlib.util
import json
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "tools/emulation/audit_olmblur_32bpc_red_only_residual_20260718.py"
RUNNER = ROOT / "scripts/run_olmblur_case0001_pf32_current_mac_20260805.py"
WINDOWS = ROOT / "refs/win_references/20260710_190500__ae26_3_32bpc_recap/OLMbit-depthconformancebatch"
MAC = ROOT / "refs/reports/olmblur_case0001_current_host_success_20260805/output"


def load_audit():
    spec = importlib.util.spec_from_file_location("olmblur_red_residual", AUDIT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_current_host_matches_core_and_stale_reference_is_not_a_fix_oracle():
    report = load_audit().build_report(WINDOWS, MAC)
    facts = report["facts"]
    assert facts["full_mac_effect_equals_current_core"] is True
    assert facts["bounded_current_aex_repeat1_equals_current_core"] is True
    assert facts["authoritative_same_aex_case0001_ae_exact"] is True
    assert facts["effect_mismatches_by_channel"] == {"A": 0, "B": 0, "G": 0, "R": 201576}
    assert report["classification"] == "superseded_reference_conflict"
    assert report["plugin_source_change"] is False


def test_runner_excludes_superseded_reference_and_requires_authoritative_artifacts():
    source = RUNNER.read_text(encoding="utf-8")
    assert "20260710_190500__ae26_3_32bpc_recap" not in source
    assert "fd2e2020720513e7590d32fadfbb1acb1a25fa551b11d0c440f6e3391ded38b6" not in source
    with tempfile.TemporaryDirectory(prefix="olmblur_authoritative_gate_") as raw:
        directory = Path(raw)
        preflight = directory / "preflight.json"
        command = [
            sys.executable, str(RUNNER),
            "--support-dir", str(directory / "support"),
            "--output-dir", str(directory / "output"),
            "--result-json", str(directory / "result.json"),
            "--provenance-json", str(directory / "provenance.json"),
            "--preflight-json", str(preflight),
        ]
        result = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, check=False)
        assert result.returncode == 3, result.stdout + result.stderr
        record = json.loads(preflight.read_text(encoding="utf-8"))
        assert record["status"] == "authoritative_recapture_required"
        assert record["checks"]["authoritative_record_exact"] is True
        assert record["checks"]["authoritative_artifacts_complete"] is False
        assert record["render_started"] is False
