from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).parent))
from probe_olmcolorkey_boundary_to_distance_type3_actual_aex_20260716 import run  # noqa: E402


def test_type3_euclidean_handle_suite_contract() -> None:
    report = run(ROOT / "aex/OLMColorKey/Plugins/64/2025/OLMColorKey.aex")
    assert report["status"] == "pass", report
    assert report["aex"]["sha256_match"]
    assert report["loader_import_log"] == []
    assert report["normal_return"]
    assert report["seed"]["boundary_rax"] == "0x0"
    assert report["target"]["va"] == "0x180007ec0"
    assert report["shim"]["required_allocation_count"] == 1
    assert report["shim"]["required_allocations"][0]["size"] == report["shim"]["expected_allocation_bytes"]
    assert report["shim"]["lifecycle_order_valid"]
    callbacks = report["shim"]["callbacks_seen"]
    assert callbacks[0] == "PF_HandleSuite.acquire"
    assert callbacks[-1] == "PF_HandleSuite.release_suite"
    assert callbacks.count("PF_HandleSuite.acquire") == callbacks.count("PF_HandleSuite.release_suite")
    assert callbacks.count("PF_HandleSuite.new_handle") == callbacks.count("PF_HandleSuite.lock_handle")
    assert callbacks.count("PF_HandleSuite.new_handle") == callbacks.count("PF_HandleSuite.unlock_handle")
    assert callbacks.count("PF_HandleSuite.new_handle") == callbacks.count("PF_HandleSuite.dispose_handle")
    assert report["cleanup_observed"]
    assert report["acceptance_gates"] == {
        "normal_return": True,
        "exactly_one_required_allocation": True,
        "lifecycle_complete": True,
        "cleanup_observed": True,
        "no_unresolved_imports": True,
        "float32_model_match": True,
    }
    pixels = report["output"]
    assert all(len(channel) == 4 for row in pixels for channel in row)
    assert all(value >= 0.0 for row in pixels for channel in row for value in channel)
    model = report["independent_model"]["first_channel"]
    assert all(
        abs(pixels[y][x][channel] - model[y][x]) < 1e-4
        for y in range(3) for x in range(5) for channel in range(4)
    )


if __name__ == "__main__":
    test_type3_euclidean_handle_suite_contract()
    print("PASS type3 Euclidean HandleSuite contract")
