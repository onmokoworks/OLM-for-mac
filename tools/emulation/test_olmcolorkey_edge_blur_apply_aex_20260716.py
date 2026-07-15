from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).parent))
from probe_olmcolorkey_edge_blur_apply_aex_20260716 import run  # noqa: E402


def test_direction_one_handle_suite_apply_contract() -> None:
    report = run(ROOT / "aex/OLMColorKey/Plugins/64/2025/OLMColorKey.aex", direction=1)
    assert report["target"]["va"] == "0x1800085b0"
    assert report["independent_weight"]["va"] == "0x1800049a0"
    assert report["classification"].endswith("not AE-exact")
    assert "PF_HandleSuite.acquire" in report["shim"]["callbacks_seen"]
    assert report["status"] in {"pass", "blocked"}
    if report["status"] == "pass":
        assert report["rax"] == "0x0"
        assert report["cleanup_observed"]
        assert report["destination_bytes"] != report["worlds"]["destination"]["initial_bytes"]
    else:
        assert report.get("deepest_rip") or report.get("error")
        assert report.get("fault_registers")
