"""Reproducible, bounded resident/process equivalence and campaign timings.

All-ten lifecycle corpus: 60 cases/route, A/B/A/edited-C/B/A blocks, unique
seeded input triplets per block, three preview scales, one bounded numeric edit.
Two Rust candidates: ordinary full-range oracle generation, 60 cases/route.
No post-result exclusion, retry replacement, or modification of original AEXs.
"""
from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
import random
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from types import SimpleNamespace

import olm_oracle as o
import oracle_resident as resident

NAMES = "ColorKeep DistanceGradation OLMBlur OLMColorKey OLMDirectionalBlur OLMKiraKira OLMRadialBlur OLMSmoother OLMSmoother2 OLMToonDilate".split()
DEFAULT_ORIGINALS = Path(r"D:\Projects\01_Project\04_Tools\olm for mac\ghidra_windows_aex")


def lifecycle_cases(parameters, count, seed):
    base = o.generate_cases(parameters, 1, seed, [(97, 61)], ["1"])[0]
    base["assignments"] = []
    editable = next(p for p in parameters if p["kind"] in ("integer", "float") and p["maximum"] > p["minimum"])
    value = min(editable["maximum"], max(editable["minimum"], editable["value"]) + 1)
    if value == editable["value"]:
        value = max(editable["minimum"], value - 1)
    if editable["kind"] == "integer":
        value = int(value)
    rng, result = random.Random(seed), []
    for block in range((count + 5) // 6):
        seeds = [rng.getrandbits(64) for _ in range(3)]
        for source in (0, 1, 0, 2, 1, 0):
            if len(result) == count:
                break
            case = copy.deepcopy(base)
            case.update(index=len(result), input_seed=seeds[source],
                        downsample=("1", "1/2", "1/4")[block % 3],
                        qualification={"kind": "lifecycle", "block": block, "source": source,
                                       "edited_slot": editable["slot"], "edited_value": value})
            if source == 2:
                case["assignments"] = [{"slot": editable["slot"], "value": value}]
                case["untouched_defaults"] = [x for x in case["untouched_defaults"] if x["slot"] != editable["slot"]]
            result.append(case)
    return result


def run_mode(out, plans, identities, inv, mode, jobs, timeout):
    out.mkdir()
    o.write_json(out / "cases.json", plans)
    routes = {r: o.route_support(inv, r) for r in o.ROUTES}
    summary = {"schema_version": 1, **identities, "results": [], "routes": {}, "complete": False,
               "cases": len(plans), "jobs": jobs, "timeout_seconds": timeout, "inventory_diff": [],
               "transport": mode}
    started = time.perf_counter()
    if mode == "resident":
        args = SimpleNamespace(out=out, jobs=jobs, timeout=timeout, perturb_candidate=[], extent=None)
        resident.render_campaign(args, plans, identities, routes, [], summary, o)
    else:
        with ThreadPoolExecutor(max_workers=jobs) as pool:
            futures = {pool.submit(o.run_case, out, case, route, identities, (), None, timeout): (case, route)
                       for case in plans for route, reason in routes.items() if reason is None}
            try:
                for future in as_completed(futures):
                    case, route = futures[future]
                    try:
                        summary["results"].append(future.result())
                    except Exception as exc:
                        summary["results"].append({"case": case["index"], "route": route,
                                                   "status": "tool_error", "error": repr(exc)})
                    if len(summary["results"]) % 30 == 0:
                        print(out.parent.name, mode, len(summary["results"]), "/", len(futures), flush=True)
                    o.write_json(out / "summary.json", summary)
            except KeyboardInterrupt:
                o.CANCELLED.set()
                for future in futures:
                    future.cancel()
                raise
        summary["results"].sort(key=lambda row: (row["case"], row["route"]))
        summary.update(complete=True, routes=o.summarize(summary["results"], routes))
        summary["exit_code"] = o.exit_code(summary)
    summary["campaign_wall_seconds"] = time.perf_counter() - started
    o.write_json(out / "summary.json", summary)
    return summary


def compare_modes(folder, singles, batches):
    left = {(r["case"], r["route"]): r for r in singles["results"]}
    right = {(r["case"], r["route"]): r for r in batches["results"]}
    if left.keys() != right.keys():
        raise ValueError("mode result populations differ")
    records = []
    for key, a in sorted(left.items()):
        b = right[key]
        name = f"case-{key[0]:04d}-{key[1]}"
        record = {"case": key[0], "route": key[1], "per_process": a["status"], "resident": b["status"],
                  "verdict_equal": a["status"] == b["status"], "sides": {}}
        for side in ("reference", "candidate"):
            old = folder / "per_process" / name
            new = folder / "resident" / name
            # Exact requests/assets and native bytes; never compare only preview pixels.
            am = json.loads((old / "case.json").read_text(encoding="utf-8"))
            bm = json.loads((new / "case.json").read_text(encoding="utf-8"))
            if am["assets"] != bm["assets"]:
                raise ValueError("mode input/request asset identities differ")
            depth = o.ROUTES[key[1]][0]
            extensions = [".png"] + ([".rgba16le"] if depth == 16 else [".rgba32f-le"] if depth == 32 else [])
            files = {}
            for extension in extensions:
                p, q = old / (side + extension), new / (side + extension)
                ph, qh = o.sha256(p) if p.exists() else None, o.sha256(q) if q.exists() else None
                files[extension] = {"per_process_sha256": ph, "resident_sha256": qh,
                                    "equal": ph == qh, "both_present": ph is not None and qh is not None}
            record["sides"][side] = {"files": files, "all_equal": all(v["equal"] and v["both_present"] for v in files.values()),
                                     "both_successful": a.get("processes", {}).get(side, {}).get("ok", False)
                                                        and b.get("processes", {}).get(side, {}).get("ok", False)}
        records.append(record)
    return {"route_cases": len(records), "verdicts_equal": sum(r["verdict_equal"] for r in records),
            "side_outputs_equal": sum(s["all_equal"] and s["both_successful"] for r in records for s in r["sides"].values()),
            "all_equivalent": all(r["verdict_equal"] and all(s["all_equal"] and s["both_successful"] for s in r["sides"].values()) for r in records),
            "per_process_wall_seconds": singles["campaign_wall_seconds"],
            "resident_wall_seconds": batches["campaign_wall_seconds"],
            "speedup": singles["campaign_wall_seconds"] / batches["campaign_wall_seconds"], "records": records}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--originals", type=Path, default=DEFAULT_ORIGINALS)
    p.add_argument("--candidates", type=Path, default=Path(__file__).resolve().parents[2] / "local/integration/staged-final")
    p.add_argument("--harness", type=Path, default=o.DEFAULT_HARNESS)
    p.add_argument("--cases", type=int, default=60)
    p.add_argument("--seed", type=int, default=20261112)
    p.add_argument("--jobs", type=int, choices=range(1, 4), default=3)
    p.add_argument("--only", help="one configuration name, e.g. original-OLMBlur or rust-ColorKeep")
    args = p.parse_args()
    if not 6 <= args.cases <= 120:
        p.error("--cases must be 6..120")
    out = args.out.resolve(); out.mkdir(parents=True, exist_ok=False)
    configs = [("original-" + name, args.originals / (name + ".aex"), args.originals / (name + ".aex"), "lifecycle") for name in NAMES]
    configs += [("rust-" + name, args.originals / (name + ".aex"), args.candidates / (name + ".aex"), "full_generator") for name in ("OLMBlur", "ColorKeep")]
    if args.only:
        configs = [c for c in configs if c[0] == args.only]
        if not configs: p.error("unknown --only")
    summary = {"schema_version": 1, "seed": args.seed, "cases_per_route": args.cases, "jobs": args.jobs,
               "tool": o.identity(__file__), "oracle": o.identity(o.__file__), "resident": o.identity(resident.__file__),
               "timing_scope": "wall time: prepare inputs/requests, dispatch, compare, cleanup and report; shared inventory acquisition outside both clocks",
               "rows": [], "complete": False}
    for index, (name, reference, candidate, corpus) in enumerate(configs):
        folder = out / name;folder.mkdir()
        identities = {"harness": o.identity(args.harness), "reference": o.identity(reference),
                      "candidate": o.identity(candidate), "tool": o.identity(o.__file__),
                      "resident_tool": o.identity(resident.__file__)}
        inv = {side: o.inspect(args.harness, path, 120) for side, path in [("reference", reference), ("candidate", candidate)]}
        o.write_json(folder / "inventory.json", inv)
        plans = lifecycle_cases(inv["reference"]["parameters"], args.cases, args.seed) if corpus == "lifecycle" else o.generate_cases(
            inv["reference"]["parameters"], args.cases, args.seed, [(11, 7), (31, 19)], ["1", "1/2", "1/4"])
        o.write_json(folder / "plans.json", plans)
        runs = {}
        order = ["per_process", "resident"] if index % 2 == 0 else ["resident", "per_process"]
        for mode in order:
            print("START", name, corpus, mode, flush=True)
            runs[mode] = run_mode(folder / mode, plans, identities, inv["reference"], mode, args.jobs, 120)
        comparison = compare_modes(folder, runs["per_process"], runs["resident"])
        comparison.update(name=name, corpus=corpus, order=order, identities=identities,
                          inventory_diff=o.inventory_diff(inv["reference"], inv["candidate"]))
        o.write_json(folder / "equivalence.json", comparison)
        summary["rows"].append({k: v for k, v in comparison.items() if k != "records"})
        o.write_json(out / "summary.json", summary)
        print("RESULT", name, comparison["all_equivalent"], comparison["side_outputs_equal"],
              f'{comparison["speedup"]:.2f}x', flush=True)
    summary["complete"] = True
    summary["all_equivalent"] = all(r["all_equivalent"] for r in summary["rows"])
    summary["speedup_ratio_of_summed_times"] = sum(r["per_process_wall_seconds"] for r in summary["rows"]) / sum(r["resident_wall_seconds"] for r in summary["rows"])
    o.write_json(out / "summary.json", summary)
    return 0 if summary["all_equivalent"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
