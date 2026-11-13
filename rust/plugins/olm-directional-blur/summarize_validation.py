"""Summarize saved final campaigns without changing their verdicts."""
import collections
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parents[1] / "tools/oracle"))
import olm_oracle as oracle


def read(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def main():
    diagnoses = read(ROOT / "validation/final-mismatch-diagnosis/summary.json")
    by_source = {str(Path(d["source"]).resolve()): d for d in diagnoses}
    campaigns = []
    totals = collections.defaultdict(collections.Counter)
    witnesses = []
    for seed in (20261112, 20261113):
        directory = ROOT / f"validation/final-seed-{seed}"
        summary = read(directory / "summary.json")
        if not summary["complete"]:
            # Preserve the interrupted tool summary. Recover only from complete,
            # independently saved case verdicts; never rerender or relabel them.
            rows = [read(p) for p in sorted(directory.glob("case-*/diff.json"))]
            assert {(r["case"], r["route"]) for r in rows} == {
                (i, route) for i in range(128) for route in ("smart8", "smart16", "smart32")
            }
            assert len(rows) == 384
            for row in rows:
                manifest = read(directory / row["directory"] / "case.json")
                assert manifest["case"] == read(directory / "cases.json")[row["case"]]
                assert all(manifest[k] == summary[k] for k in ("reference", "candidate", "harness", "tool"))
            summary["results"] = rows
            summary["routes"] = oracle.summarize(rows, {r: None for r in ("smart8", "smart16", "smart32")})
            summary["complete"] = True
            summary["recovery"] = {"reason": "Oracle summary.json.tmp rename failed with WinError 5; renderer futures still completed", "original_summary_preserved": True, "all_384_saved_case_verdicts_present": True, "render_process_exit_success": all(p["ok"] for r in rows for p in r["processes"].values()), "oracle_process_exit_code": 1}
            (directory / "summary-recovered.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
        assert summary["complete"]
        counts = collections.defaultdict(collections.Counter)
        scales = collections.defaultdict(lambda: collections.defaultdict(collections.Counter))
        for row in summary["results"]:
            route = row["route"]
            counts[route][row["status"]] += 1
            counts[route]["total"] += 1
            if row["case"] >= 3:
                counts[route]["random_total"] += 1
                counts[route]["random_" + row["status"]] += 1
            case_dir = directory / row["directory"]
            case = read(case_dir / "case.json")["case"]
            scales[route][case["downsample"]][row["status"]] += 1
            if row["status"] != "exact":
                d = by_source[str(case_dir.resolve())]
                witnesses.append({
                    "seed": seed, "case": row["case"], "route": route,
                    "baseline_status": row["status"], "offset": d["offset"],
                    "distinct_reference_outputs": d["distinct_reference_outputs"],
                    "reference_nondeterminism_proven": d["reference_nondeterminism_proven"],
                    "zero_offset_control_status": d["zero_offset_control"]["status"],
                    "reference_pixel_hashes": d["reference_pixel_hashes"],
                    "diagnostic_statuses": [r["status"] for r in d["repeats"]],
                    "evidence": str(case_dir.relative_to(ROOT)),
                })
        for route, counter in counts.items():
            totals[route].update(counter)
        campaigns.append({"seed": seed, "complete": True, "per_depth": counts,
                          "summary_recovery": summary.get("recovery"),
                          "per_depth_downsample": scales,
                          "failure_counts": {r: {k: v for k, v in d.items() if "failure" in k or "timeout" in k or k in ("tool_error", "reference_unrenderable")} for r, d in summary["routes"].items()},
                          "identities": {k: summary[k] for k in ("reference", "candidate", "harness", "tool")}})
    identities = read(ROOT / "source-identities.json")
    repo = ROOT.parents[2]
    drift = [p for p, h in identities.items() if hashlib.sha256((repo / p).read_bytes()).hexdigest() != h]
    candidate = Path(campaigns[0]["identities"]["candidate"]["path"])
    assert hashlib.sha256(candidate.read_bytes()).hexdigest() == campaigns[0]["identities"]["candidate"]["sha256"]
    assert not drift
    report = {
        "status": "qualified_with_original_nondeterminism_limit; universal exact definition of done is not met",
        "campaigns": campaigns, "totals_per_depth": totals,
        "baseline_mismatches": witnesses,
        "baseline_mismatch_count": len(witnesses),
        "all_mismatches_have_observed_reference_nondeterminism": all(w["reference_nondeterminism_proven"] for w in witnesses),
        "all_zero_offset_controls_exact": all(w["zero_offset_control_status"] == "exact" for w in witnesses),
        "source_hash_drift": drift,
        "inventory_identical": read(ROOT / "inventory-comparison.json")["identical"],
        "pipl": read(ROOT / "pipl-comparison.json"),
        "tests": {"passed": 6, "random_cpp_images": 360, "thread_counts": [1, 4], "layer_hdr_nonfinite_cpp_images": 24, "gaussian_words": 5498},
        "excluded_from_main_counts": ["smoke", "superseded preliminary campaign", "reference self-repeats", "zero-offset controls"],
        "limitations": ["AEXCompat only; native AE and macOS not tested", "Original negative-offset table underread: nondeterminism observed, memory cause inferred from grounded C++", "Noise Type 3 original defect; Layer arithmetic tested against C++ only", "Native HDR/negative alpha and Classic/ROI layouts not qualified against original", "Harness reports source_newer_than_worker; worker loaded-module identity not observed"],
    }
    (ROOT / "validation-report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"totals": totals, "mismatches": len(witnesses), "all_nondeterministic": report["all_mismatches_have_observed_reference_nondeterminism"], "controls_exact": report["all_zero_offset_controls_exact"]}, indent=2))


if __name__ == "__main__":
    main()
