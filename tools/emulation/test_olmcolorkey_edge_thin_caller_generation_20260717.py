from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).parent))
from probe_olmcolorkey_edge_thin_caller_generation_20260717 import run  # noqa: E402


def test_edge_thin_caller_generation_fixture() -> None:
    report = run(ROOT / "aex/OLMColorKey/Plugins/64/2025/OLMColorKey.aex")
    assert report["status"] == "pass_static_abi_connected_stage_probe"
    assert report["schema"] == 2
    static = report["static_caller_contract"]
    assert static["status"] == "pass"
    assert static["caller_8"]["calls_FUN_180008320"] is False
    assert static["caller_16"]["role"] == "immediate caller of FUN_180008320"
    provenance = report["provenance"]
    assert provenance["constant_0x18001f754_bytes_hex"] == "00007a45"
    assert provenance["constant_0x18001f754_float32"] == 4000.0
    assert provenance["audit_assertion_matches_pinned_aex"] is False
    stage_8 = report["independent_8bit_stage_probe"]
    assert stage_8["xmm3"] == 4000.0
    assert stage_8["boundary_rax"] == stage_8["distance_rax"] == "0x0"
    pipeline = report["connected_16bit_pipeline"]
    assert pipeline["xmm3_distance_scale"] == 4000.0
    assert pipeline["returns"]["boundary_rax"] == "0x0"
    assert pipeline["returns"]["distance_rax"] == "0x0"
    assert pipeline["returns"]["leaf_rax"] == "0x0"
    evidence = pipeline["connected_evidence"]
    assert evidence["distance_identity_preserved"]
    assert evidence["distance_before_leaf_sha256"] == evidence["distance_after_leaf_sha256"]
    assert evidence["actual_equals_oracle"]
    assert evidence["destination_actual_sha256"] == evidence["portable_oracle_sha256"]
    half = report["connected_half_scale_diagnostic"]
    assert half["xmm3_distance_scale"] == 0.5
    assert half["returns"]["leaf_rax"] == "0x0"
    assert half["connected_evidence"]["distance_identity_preserved"]
    assert half["connected_evidence"]["actual_equals_oracle"]


if __name__ == "__main__":
    test_edge_thin_caller_generation_fixture()
    print("[OK] OLMColorKey static caller ABI + connected Edge Thin stage probe")
