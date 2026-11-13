"""Run the real all-ten oracle campaign. All output stays under this directory."""
from pathlib import Path
import argparse
import json
import sys

import olm_oracle as o

NAMES = "ColorKeep DistanceGradation OLMBlur OLMColorKey OLMDirectionalBlur OLMKiraKira OLMRadialBlur OLMSmoother OLMSmoother2 OLMToonDilate".split()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--originals", type=Path, default=Path(r"D:\Projects\01_Project\04_Tools\olm for mac\ghidra_windows_aex"))
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--jobs", type=int, choices=range(1, 4), default=3)
    p.add_argument("--timeout", type=float, default=120)
    args = p.parse_args()
    args.out.mkdir(parents=True, exist_ok=False)
    results = {}
    for name in NAMES:
        print(f"\n=== {name} ===", flush=True)
        plugin = str(args.originals / (name + ".aex"))
        common = ["--reference", plugin, "--candidate", plugin]
        inv = o.main(["inventory", *common, "--out", str(args.out / (name + "-inventory"))])
        if inv == 130:
            return 130
        code = o.main(["render", *common, "--cases", "20", "--seed", "20261112", "--jobs", str(args.jobs),
                       "--timeout", str(args.timeout), "--downsample", "1,1/2,1/4", "--out", str(args.out / name)])
        if code == 130:
            return 130
        results[name] = {"inventory_exit": inv, "render_exit": code}
        o.write_json(args.out / "campaign.json", results)
    plugin = str(args.originals / "OLMBlur.aex")
    code = o.main(["render", "--reference", plugin, "--candidate", plugin, "--cases", "1", "--sizes", "97x61",
                   "--routes", "smart8,smart16,smart32", "--perturb-candidate", "1=0.5",
                   "--jobs", str(args.jobs), "--timeout", str(args.timeout), "--out", str(args.out / "negative-control")])
    results["negative_control"] = {"exit_code": code, "expected": 1}
    o.write_json(args.out / "campaign.json", results)
    print(json.dumps(results, indent=2))
    return 0 if code == 1 and all(v["inventory_exit"] == 0 and v["render_exit"] == 0 for k, v in results.items() if k != "negative_control") else 1


if __name__ == "__main__":
    sys.exit(main())
