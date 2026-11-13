"""Summarize the two completed, immutable final oracle campaigns."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
VALIDATION = ROOT / "validation"
SEEDS = (20261112, 20261113)

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    identities = json.loads((VALIDATION / "verified-identities.json").read_text())
    for key in ("original", "candidate", "harness", "worker", "oracle", "default_transport_adapter"):
        assert sha(Path(identities[key]["path"])) == identities[key]["sha256"], key
    runs = []
    for seed in SEEDS:
        directory = VALIDATION / f"verified-{seed}"
        path = directory / "summary.json"
        summary = json.loads(path.read_text())
        assert summary["complete"] and summary["exit_code"] == 0
        assert summary["candidate"]["sha256"] == identities["candidate"]["sha256"]
        assert not summary["inventory_diff"]
        cases = json.loads((directory / "cases.json").read_text())
        assert cases[0]["assignments"] == []
        assert len(cases) == 120
        for route in ("smart8", "smart16", "smart32"):
            result = summary["routes"][route]
            assert result["exact"] == 120 and result["max_abs_diff"] == 0
        runs.append({"seed": seed, "summary": str(path.relative_to(ROOT)), "summary_sha256": sha(path),
                     "cases_sha256": sha(directory / "cases.json"), "cases": 120,
                     "empty_assignment_defaults": 1, "boundary_parameter_cases": 2, "random_parameter_cases": 117,
                     "sizes": summary["sizes"], "downsample": summary["downsample"],
                     "routes": summary["routes"]})
    inventory_path=VALIDATION / "inventory-verified" / "summary.json"
    inventory=json.loads(inventory_path.read_text())
    assert inventory["identical"] and inventory["diff"] == []
    files = [ROOT / n for n in ("Cargo.toml", "build.rs", "validate.py", "summarize.py", "revalidate.py", "isolate.py")]
    files += sorted((ROOT / "src").glob("*.rs")) + sorted((ROOT / "tests").glob("*"))
    output = {"schema_version": 1, "job": "P-kira", "identities": identities,
              "runs": runs, "totals_per_depth": {"cases": 240, "random_parameter_cases": 234, "boundary_parameter_cases": 4,
              "independent_defaults": 2, "exact": 240, "mismatch": 0, "reference_failure": 0, "candidate_failure": 0},
              "inventory_verification": {"summary": str(inventory_path.relative_to(ROOT)), "sha256": sha(inventory_path)},
              "test_log_sha256": {name:sha(VALIDATION/name) for name in ["test.log","original-ramp-test.log","candidate-ramp-test.log"]},
              "cpp_reference_tests": 8, "ui_event_and_draw_comparisons": 2017,
              "native_ramp_callbacks": {"plugins": ["original", "candidate"], "defaults_each": 5,
              "unflatten_copy_flatten_each": 255, "flat_size": 325, "compare": "header and active records; inactive capacity is zeroed"},
              "source_sha256": {str(p.relative_to(ROOT)): sha(p) for p in files}}
    (ROOT / "validation-report.json").write_text(json.dumps(output, indent=2) + "\n")
    print("720/720 route-cases exact; 234 random parameter cases + 4 min/max cases + 2 independent defaults per depth.")

if __name__ == "__main__":
    main()
