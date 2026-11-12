#!/usr/bin/env python3
"""Palette-hit/edge regression corpus using F-oracle's renderer and comparator.

Unlike uniform independent palettes, these cases deliberately select colors from
the generated partial-alpha source, so successful matches are observable.
"""
from pathlib import Path
import argparse
import concurrent.futures
import copy
import importlib.util
import json
import random
import time

ROOT = Path(__file__).resolve().parents[3]
spec = importlib.util.spec_from_file_location("olm_oracle", ROOT / "rust/tools/oracle/olm_oracle.py")
oracle = importlib.util.module_from_spec(spec)
spec.loader.exec_module(oracle)


def write_summary(path, value):
    # Windows readers may temporarily deny the atomic rename of a live summary.
    for attempt in range(50):
        try:
            oracle.write_json(path, value)
            return
        except PermissionError:
            if attempt == 49: raise
            time.sleep(.02)


def recover(out):
    summary = json.loads((out / "summary.json").read_text())
    cases = json.loads((out / "cases.json").read_text())
    manifests = sorted(out.glob("case-*/case.json"))
    assert len(manifests) == len(cases)*3, "incomplete corpus"
    rows = []
    for path in manifests:
        manifest = json.loads(path.read_text())
        for side in ("reference", "candidate", "harness"):
            assert oracle.sha256(manifest[side]["path"]) == manifest[side]["sha256"]
        for name, digest in manifest["assets"].items():
            assert oracle.sha256(path.parent / name) == digest
        row = json.loads((path.parent / "diff.json").read_text())
        for side in ("reference", "candidate"):
            process = json.loads((path.parent / f"{side}.process.json").read_text())
            assert process["returncode"] == 0 and not process["timeout"]
        depth = oracle.ROUTES[manifest["route"]][0]
        comparison = oracle.compare_samples(oracle.load_output(path.parent / "reference.png", depth),
                                            oracle.load_output(path.parent / "candidate.png", depth), depth)
        assert comparison == row["comparison"], "saved comparison differs from raw artifacts"
        rows.append(row)
    summary["results"] = rows
    summary["routes"] = oracle.summarize(rows, {r: None for r in ("smart8", "smart16", "smart32")})
    summary["complete"] = True
    summary["recovery"] = {"reason": "Windows denied atomic summary rename during progress observation; all worker tasks completed",
                           "method": "rechecked every manifest, binary/input hash, process result and raw output comparison; no rerender",
                           "script": oracle.identity(__file__)}
    summary["exit_code"] = oracle.exit_code(summary)
    write_summary(out / "summary.json", summary)
    oracle.print_table(summary)
    return summary["exit_code"]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plugin", choices=["ColorKeep", "OLMColorKey"], required=True)
    parser.add_argument("--reference", type=Path, required=True)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--cases", type=int, default=48)
    parser.add_argument("--jobs", type=int, default=2)
    parser.add_argument("--extent", help="optional left,top,right,bottom output demand")
    parser.add_argument("--recover", action="store_true", help="verify completed raw artifacts after a summary-write interruption")
    args = parser.parse_args()
    out = args.out.resolve()
    if args.recover: return recover(out)
    out.mkdir(parents=True, exist_ok=False)
    identities = {"harness": oracle.identity(oracle.DEFAULT_HARNESS),
                  "reference": oracle.identity(args.reference), "candidate": oracle.identity(args.candidate),
                  "tool": oracle.identity(oracle.__file__), "corpus": oracle.identity(__file__)}
    inv = {side: oracle.inspect(oracle.DEFAULT_HARNESS, Path(identities[side]["path"]), 60)
           for side in ("reference", "candidate")}
    defaults = oracle.generate_cases(inv["reference"]["parameters"], 1, 1)[0]["assignments"]
    rng = random.Random(0xF001C0DE)
    sizes = [(1, 9), (17, 1), (11, 7), (31, 19)] if not args.extent else [(11, 7)]
    cases = []
    for index in range(args.cases):
        w, h = sizes[index % len(sizes)]; seed = rng.getrandbits(64)
        source = oracle.input_pixels(w, h, seed).reshape(-1, 4)
        assignments = {p["slot"]: copy.deepcopy(p) for p in defaults}
        def value(slot, number): assignments[slot] = {"slot": slot, "value": number}
        def color(slot, rgba):
            r, g, b, a = map(int, rgba)
            assignments[slot] = {"slot": slot, "color": [a, r, g, b]}
        if args.plugin == "ColorKeep":
            count = [1, 3, 9, 100][index % 4]; value(1, count)
            for j in range(count): color(2+j, source[(3+j*7) % len(source)])
        else:
            value(1, index % 2); value(2, rng.choice([0, .002, .02, .1]))
            value(4, int(index % 7 == 0)); value(5, 1+index % 6); value(6, 1+index % 3)
            value(7, int(index % 5 == 0)); value(8, int(index % 3 == 0))
            for slot in [9, 10, 11]: value(slot, rng.choice([0, .02, .1]))
            value(14, rng.choice([-3, -1, 0, 0, 1, 2])); value(15, 1+index % 3)
            value(18, rng.choice([0, .5, 1, 1.5, 2, 4])); value(19, 1+(index//3) % 3)
            value(20, 1+(index//6) % 3); value(22, 3); value(23, int(index % 4 != 0))
            for j in range(3):
                s = 24+j*8; value(s, 1); value(s+1, int(j != 1))
                color(s+2, source[(3+j*7) % len(source)])
                color(s+3, [rng.randrange(256), rng.randrange(256), rng.randrange(256), 255])
                for k in range(4, 8): value(s+k, rng.choice([0, .02, .1]))
        cases.append({"index": index, "size": [w,h], "input_seed": seed,
                      "downsample": ["1", "1/2", "1/4"][index % 3],
                      "assignments": list(assignments.values()), "unassigned": []})
    oracle.write_json(out / "cases.json", cases)
    routes = ["smart8", "smart16", "smart32"]
    extent = list(map(int, args.extent.split(','))) if args.extent else None
    summary = {**identities, "cases": args.cases, "seed": 0xF001C0DE, "extent": extent,
               "inventory_diff": oracle.inventory_diff(inv["reference"], inv["candidate"]),
               "results": [], "complete": False}
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.jobs) as pool:
        futures = [pool.submit(oracle.run_case, out, case, route, identities, (), extent, 60)
                   for case in cases for route in routes]
        for future in concurrent.futures.as_completed(futures):
            summary["results"].append(future.result())
            summary["routes"] = oracle.summarize(summary["results"], {r: None for r in routes})
            write_summary(out / "summary.json", summary)
            if len(summary["results"]) % 12 == 0: print(f"completed {len(summary['results'])}/{len(futures)}", flush=True)
    summary["complete"] = True; summary["exit_code"] = oracle.exit_code(summary)
    write_summary(out / "summary.json", summary); oracle.print_table(summary)
    return summary["exit_code"]


if __name__ == "__main__":
    raise SystemExit(main())
