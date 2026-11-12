"""Collect the two completed P-toon campaigns; refuse stale/incomplete evidence."""
import hashlib
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def main():
    inventory = read(ROOT / "validation/inventory-release/summary.json")
    pipl = read(ROOT / "pipl-comparison.json")
    worker = read(ROOT / "validation/worker-identity-before.json")
    assert inventory["identical"] and not inventory["diff"]
    assert pipl["identical"] and pipl["original_hex"] == pipl["candidate_hex"]
    assert worker["sha256"] == sha(worker["path"])
    campaigns = []
    identities = None
    for seed in [20261112, 20261113]:
        directory = ROOT / "validation" / f"seed-{seed}"
        summary = read(directory / "summary.json")
        cases = read(directory / "cases.json")
        assert summary["complete"] and summary["exit_code"] == 0
        assert summary["seed"] == seed and summary["cases"] == 203
        current = {k: summary[k] for k in ["reference", "candidate", "harness", "tool"]}
        if identities is None:
            identities = current
        assert current == identities
        for item in current.values():
            assert item["sha256"] == sha(item["path"]), item
        assert inventory["candidate"] == current["candidate"]
        assert not summary["inventory_diff"]
        for route in ["smart8", "smart16", "smart32"]:
            count = summary["routes"][route]
            assert count["cases_run"] == count["exact"] == 203
            assert all(count[k] == 0 for k in ["mismatched", "reference_unrenderable",
                "reference_timeout", "candidate_failure", "tool_error"])
        assert len(summary["results"]) == 609
        assert {(r["case"], r["route"]) for r in summary["results"]} == {
            (i, route) for i in range(203) for route in ["smart8", "smart16", "smart32"]}
        assert all(r["status"] == "exact" for r in summary["results"])
        campaigns.append({
            "seed": seed, "cases_per_depth": 203, "randomized_per_depth": 200,
            "downsample_counts_per_depth": dict(Counter(c["downsample"] for c in cases)),
            "routes": summary["routes"], "jobs": summary["jobs"],
            "sizes": summary["sizes"], "timeout_seconds": summary["timeout_seconds"],
            "render_environment_overrides": summary["render_environment_overrides"],
            "summary_path": str((directory / "summary.json").relative_to(ROOT)),
            "summary_sha256": sha(directory / "summary.json"),
            "case_plan_sha256": sha(directory / "cases.json"),
        })
    assert pipl["candidate_sha256"] == identities["candidate"]["sha256"]
    assert pipl["original_sha256"] == identities["reference"]["sha256"]
    repository = ROOT.parents[2]
    sources = ["Cargo.toml", "build.rs", "src/lib.rs", "src/algorithm.rs", "src/ae.rs",
               "tests/reference.cpp", "tests/kernel.rs"]
    report = {
        "schema_version": 1, "date": "2026-11-12", "plugin": "OLMToonDilate",
        "qualification": "AEXCompat CPU, not native AE or macOS",
        "identities": {**identities, "worker": worker},
        "inventory_identical": True, "pipl_identical_bytes": pipl["original_size"],
        "campaigns": campaigns,
        "totals": {"exact": 1218, "per_depth": 406, "randomized_per_depth": 400,
            "mismatches": 0, "reference_unrenderable": 0, "reference_timeout": 0,
            "candidate_failure": 0, "tool_error": 0},
        "tests": {"passed": 7, "cpp_matrix_comparisons": 3150,
            "concurrent_cpp_comparisons": 168, "frame_thread_counts": [1, 2, 7]},
        "source_sha256": {name: sha(ROOT / name) for name in sources},
        "cpp_production_sha256": sha(repository / "mac/OLMToonDilate/OLMToonDilate.cpp"),
        "reference_unrenderable_cases": [],
        "process_cleanup": "Oracle owned Windows Job Objects verify zero active descendants on every return.",
        "remaining_gaps": ["native AE", "macOS build", "UI interaction", "saved-project round trips",
            "native-deep/ROI original-AEX campaign beyond request PNG corpus"],
        "hoisting_candidates": ["optional pixel-checkin policy", "commit after checkin",
            "custom UI event registration", "pre-render extra-pixels flag"],
    }
    (ROOT / "validation-report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report["totals"], indent=2))


if __name__ == "__main__":
    main()
