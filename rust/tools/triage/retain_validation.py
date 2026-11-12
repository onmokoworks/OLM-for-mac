"""Retain compact, hash-bound facts from completed local validation reports."""
import argparse
import collections
import json
from pathlib import Path
import olm_triage as t
from profile_originals import NAMES


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def compact_diff(path):
    d = read(path)
    return {"report": t.oracle.identity(path), "tool": d["tool"], "oracle": d["oracle"], "harness": d["harness"],
            "old": d["old"]["identity"], "new": d["new"]["identity"], "settings": d["settings"],
            "exporter_sha256": d["old"]["binary"]["exporter_sha256"], "incomplete": d["incomplete"],
            "inventory_differences": len(d["inventory_diff"]), "pipl_differences": len(d["pipl_diff"]),
            "binary_summary": d["binary_diff"]["summary"], "parameter_sensitivity": d["parameter_sensitivity"],
            "behaviour": d["behaviour"]["routes"], "sensitivity": d["sensitivity"]["routes"],
            "changed_named_functions": [p for p in d["binary_diff"]["changed"] if p["new"].get("named")]}


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--profiles", type=Path, nargs="+", required=True, help="profile roots; later roots override earlier runs")
    p.add_argument("--blur", type=Path, required=True)
    p.add_argument("--synthetic", type=Path, required=True)
    p.add_argument("--relocation", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    a = p.parse_args()
    a.out.mkdir(parents=True, exist_ok=False)
    profiles = []
    table = ["| Original | Params | Depths | Functions | Function bytes | Largest function | Default seconds (8 / 16 / 32) |",
             "|---|---:|---|---:|---:|---:|---|"]
    for name in NAMES:
        candidates = [root / name / "triage.json" for root in a.profiles if (root / name / "triage.json").exists()]
        if not candidates:
            raise FileNotFoundError(f"no completed profile report for {name}")
        path = candidates[-1]
        report = read(path)
        d = report["profile"]
        row = {"name": name, "report": t.oracle.identity(path), "tool": report["tool"], "harness": report["harness"],
               "identity": d["identity"], "parameter_count": len(d["inventory"]["parameters"]),
               "function_count": d["function_count"], "function_bytes": d["function_bytes"],
               "largest_function": d["largest_functions"][0], "timing": d["timing"], "pipl": d["pipl"],
               "import_count": len(d["imports"]), "import_families": dict(collections.Counter(x["family"] for x in d["imports"])),
               "suite_strings": d["sdk_suite_strings"], "incomplete": report["incomplete"],
               "ghidra_version": d["binary"]["ghidra_version"], "analysis_complete": d["binary"]["analysis_complete"],
               "exporter_sha256": d["binary"]["exporter_sha256"]}
        profiles.append(row)
        depths = d["pipl"][0]["fields"]["depths"]
        times = {t.oracle.ROUTES[r["route"]][0]: r for r in d["timing"]["routes"]}
        timing = " / ".join(f"{times[x]['wall_seconds']:.3f}" if x in times and times[x]["status"] == "rendered" else "-" for x in (8, 16, 32))
        table.append(f"| {name} | {row['parameter_count']} | {'/'.join(map(str,depths))} | {row['function_count']:,} | {row['function_bytes']:,} | {row['largest_function']['size']:,} | {timing} |")
    evidence = {"date": "2026-11-12", "profiles": profiles, "original_vs_rust": compact_diff(a.blur),
                "synthetic": compact_diff(a.synthetic), "relocation": read(a.relocation)}
    assert all(not r["incomplete"] for r in profiles), "profile campaign incomplete"
    assert not evidence["original_vs_rust"]["incomplete"] and not evidence["synthetic"]["incomplete"]
    t.oracle.write_json(a.out / "validation.json", evidence)
    (a.out / "profile-table.md").write_text("\n".join(table) + "\n", encoding="utf-8")
    print("\n".join(table))
