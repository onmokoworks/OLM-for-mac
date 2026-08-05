#!/usr/bin/env python3
"""Bounded actual-AEX -> production audit for Edge Blur direction 4."""
import hashlib, json, subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ADAPTER = ROOT / "tools/emulation/test_olmcolorkey_mac_smartrender_adapter_20260717.py"
OUT = ROOT / "refs/conformance/olmcolorkey_edge_blur_direction_4_all_depths_20260805.json"

def main() -> int:
    expected = {
        "PF8": ([1.0] + [0.0] * 11, [0] + [255] * 11),
        "PF16": ([1.0] + [0.0] * 11, [0] + [32768] * 11),
        "PF32": ([1.0, .4999999701976776, 0.0, 0.0, .4999999701976776] + [0.0] * 7,
                 [0.0, .5, 1.0, 1.0, .5] + [1.0] * 7),
    }
    run = subprocess.run(["python3", str(ADAPTER)], cwd=ROOT, capture_output=True, text=True)
    production = json.loads(run.stdout) if run.returncode == 0 else {}
    rows, passed = [], run.returncode == 0
    for fmt, (plane, alpha) in expected.items():
        path = ROOT / f"refs/conformance/olmcolorkey_{fmt.lower()}_full_worker_actual_aex_20260805.json"
        actual = next(case for case in json.loads(path.read_text())["cases"]
                      if case["case"] == "enabled_black_key_edge_blur_2_single_direction_4")
        prod = next((r for r in production.get("cases", []) if r["case"] == f"enabled_black_key_edge_blur_2_single_direction_4_{fmt.lower()}"), {})
        events = [e for e in actual["execution"]["events"] if "output_alpha" in e]
        contract = prod.get("numerical_contract", {})
        prod_alpha = contract.get("alpha8", contract.get("alpha16", contract.get("alpha32")))
        gates = {
            "actual_direction_is_4": actual["parameter_record"]["edge_blur_direction"] == 4,
            "actual_amount_is_2": actual["parameter_record"]["edge_blur_amount"] == 2.0,
            "actual_direction_plane_exact": actual["execution"]["temporary_handles"][0]["f32"] == plane,
            "actual_final_alpha_exact": events[-1]["output_alpha"] == alpha,
            "production_direction_plane_exact": prod.get("direction_plane") == plane,
            "production_final_alpha_exact": prod_alpha == alpha,
            "production_padding_preserved": prod.get("input_padding_preserved") is True and prod.get("output_padding_preserved") is True,
        }
        passed &= all(gates.values())
        rows.append({"pixel_format": fmt, "actual_aex_sha256": actual["aex"]["sha256"], "gates": gates})
    source = ROOT / "mac/OLMColorKey/OLMColorKey.cpp"
    report = {"status": "pass" if passed else "fail", "scope": "4x3 single black key, Edge Blur amount 2.0, direction 4, PF8/PF16/PF32", "claim_boundary": "Bounded direction-4 actual full-worker to production source-adapter proof only; no direction-3 equivalence, other direction, amount, shape, or AE-host claim.", "production_source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(), "cases": rows}
    OUT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"status": report["status"], "json": str(OUT)}))
    return 0 if passed else 1

if __name__ == "__main__": raise SystemExit(main())
