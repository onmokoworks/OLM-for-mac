#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path


def load_manifest(path: Path) -> dict:
    return json.loads(path.read_text())


def load_manifests(path: Path) -> list[dict]:
    if path.is_dir():
        manifests = sorted(path.glob("**/reference_manifest.json"))
        return [load_manifest(item) for item in manifests]
    return [load_manifest(path)]


def case_plugin_name(case: dict) -> str:
    effects = case.get("effects") or []
    if effects:
        effect = effects[0]
        return effect.get("match_name") or effect.get("name") or "UNKNOWN"
    return "NO_EFFECT"


def summarize(manifests: list[dict]) -> dict:
    by_plugin: dict[str, list[dict]] = defaultdict(list)
    inputs = set()
    request_ids = set()
    gpu_modes = set()
    total_cases = 0
    for manifest in manifests:
        for case in manifest.get("cases", []):
            total_cases += 1
            by_plugin[case_plugin_name(case)].append(case)
            if case.get("input_id"):
                inputs.add(case["input_id"])
            if case.get("request_id"):
                request_ids.add(case["request_id"])
            gpu_name = ((case.get("project_gpu_accel_type") or {}).get("current_name"))
            if gpu_name:
                gpu_modes.add(gpu_name)

    plugins = []
    for plugin_name in sorted(by_plugin):
        cases = by_plugin[plugin_name]
        first = cases[0]
        plugins.append(
            {
                "plugin_name": plugin_name,
                "case_count": len(cases),
                "request_ids": sorted({c.get("request_id") for c in cases if c.get("request_id")}),
                "input_ids": sorted({c.get("input_id") for c in cases if c.get("input_id")}),
                "sample_case_ids": [c.get("id") for c in cases[:3]],
                "render_sets": sorted({c.get("render_set_id") for c in cases if c.get("render_set_id")}),
                "frame_rates": sorted({((c.get("comp") or {}).get("frame_rate")) for c in cases if (c.get("comp") or {}).get("frame_rate") is not None}),
                "effect_param_count": len(((first.get("effects") or [{}])[0].get("params") or [])),
            }
        )

    return {
        "case_count": total_cases,
        "plugin_count": len(plugins),
        "plugins": plugins,
        "request_ids": sorted(request_ids),
        "input_ids": sorted(inputs),
        "gpu_modes": sorted(gpu_modes),
    }


def write_markdown(summary: dict, out: Path) -> None:
    lines = [
        "# Combined Reference Summary",
        "",
        f"- total_cases: {summary['case_count']}",
        f"- plugin_count: {summary['plugin_count']}",
        f"- input_ids: {', '.join(summary['input_ids'])}",
        f"- gpu_modes: {', '.join(summary['gpu_modes'])}",
        "",
        "| Plug-in | Cases | Params | Request ID | Input | Sample cases |",
        "| --- | ---: | ---: | --- | --- | --- |",
    ]
    for row in summary["plugins"]:
        lines.append(
            "| {plugin} | {cases} | {params} | {req} | {inp} | {samples} |".format(
                plugin=row["plugin_name"],
                cases=row["case_count"],
                params=row["effect_param_count"],
                req=", ".join(row["request_ids"]),
                inp=", ".join(row["input_ids"]),
                samples=", ".join(x or "-" for x in row["sample_case_ids"]),
            )
        )
    out.write_text("\n".join(lines) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--output-json", type=Path)
    parser.add_argument("--output-md", type=Path)
    args = parser.parse_args()

    summary = summarize(load_manifests(args.manifest))
    if args.output_json:
        args.output_json.write_text(json.dumps(summary, indent=2) + "\n")
    if args.output_md:
        write_markdown(summary, args.output_md)
    else:
        print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
