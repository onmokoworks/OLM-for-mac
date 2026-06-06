#!/usr/bin/env python3
"""Validate and package Windows AE reference render requests.

The output zip is meant to be handed to the Windows machine/Codex session that
renders additional AE references. It contains the request README plus selected
JSON request specs, preserving paths under refs/reference_requests/.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
import zipfile
from pathlib import Path

from check_reference_request_status import load_status_rows


HANDOFF_NAME = "refs/reference_requests/WIN_CODEX_HANDOFF.md"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--only",
        action="append",
        default=[],
        metavar="REQUEST_JSON",
        help="Package only this request JSON basename or path. May be repeated.",
    )
    parser.add_argument(
        "--pending",
        action="store_true",
        help="Package only requests not currently covered by refs/win_references.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Output zip path. Defaults to /tmp/olm_reference_requests_YYYYMMDD.zip.",
    )
    return parser.parse_args()


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def resolve_requests(request_dir: Path, only: list[str]) -> list[Path]:
    all_requests = sorted(request_dir.glob("*.json"))
    if not only:
        return all_requests

    selected: list[Path] = []
    by_name = {path.name: path for path in all_requests}
    by_stem = {path.stem: path for path in all_requests}
    for item in only:
        candidate = Path(item)
        if candidate.exists():
            selected.append(candidate.resolve())
        elif item in by_name:
            selected.append(by_name[item])
        elif item in by_stem:
            selected.append(by_stem[item])
        else:
            known = ", ".join(path.name for path in all_requests)
            raise SystemExit(f"unknown request {item!r}; known: {known}")

    return sorted(dict.fromkeys(selected))


def resolve_pending_requests(root: Path, request_dir: Path) -> list[Path]:
    rows = load_status_rows(request_dir, root / "refs" / "win_references")
    pending_ids = {row["request_id"] for row in rows if row["status"] != "covered"}
    requests = [
        path
        for path in sorted(request_dir.glob("*.json"))
        if validate_request(path)["request_id"] in pending_ids
    ]
    return requests


def validate_request(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError("top-level JSON must be an object")
    request_id = data.get("request_id")
    if not isinstance(request_id, str) or not request_id:
        raise ValueError("missing non-empty request_id")
    if not isinstance(data.get("cases"), list) or not data["cases"]:
        raise ValueError("missing non-empty cases list")
    if not isinstance(data.get("manifest_requirements"), list):
        raise ValueError("missing manifest_requirements list")
    return data


def request_summary(data: dict) -> str:
    effect = data.get("effect", {})
    effect_name = effect.get("name", "unknown effect")
    match_name = effect.get("match_name", "")
    render_sets = data.get("render_sets", [])
    required_sets = [
        item.get("project_gpu_accel_type.current_name", item.get("id", "unknown"))
        for item in render_sets
        if item.get("required")
    ]
    optional_sets = [
        item.get("project_gpu_accel_type.current_name", item.get("id", "unknown"))
        for item in render_sets
        if not item.get("required")
    ]
    lines = [
        f"### {data['request_id']}",
        "",
        f"- Effect: `{effect_name}`" + (f" / `{match_name}`" if match_name else ""),
        f"- Cases: {len(data['cases'])}",
    ]
    if required_sets:
        lines.append(f"- Required render set(s): {', '.join(required_sets)}")
    if optional_sets:
        lines.append(f"- Optional render set(s): {', '.join(optional_sets)}")

    why = data.get("why", [])
    if why:
        lines.append("- Why: " + str(why[0]))

    cases = data.get("cases", [])
    if cases:
        sample_ids = ", ".join(str(case.get("id", "unnamed")) for case in cases[:4])
        if len(cases) > 4:
            sample_ids += ", ..."
        lines.append(f"- Case ids: {sample_ids}")

    followup = data.get("mac_follow_up", data.get("mac_side_followup", []))
    if followup:
        first_followup = str(followup[0])
        if "import_win_reference.py" in first_followup:
            first_followup = "Import with scripts/intake_olm_return.py path/to/returned_reference.zip --quick."
        lines.append("- Mac follow-up: " + first_followup)

    return "\n".join(lines)


def build_handoff(validated: list[tuple[Path, dict]]) -> str:
    total_cases = sum(len(data["cases"]) for _path, data in validated)
    lines = [
        "# Windows Codex Handoff: OLM Reference Requests",
        "",
        "You are running on the Windows AE machine. Render the selected OLM Tools",
        "reference requests in this package and return a packed result zip to the",
        "Mac porting workspace.",
        "",
        "Hard requirements:",
        "",
        "- Prefer `project_gpu_accel_type.current_name = SOFTWARE` first.",
        "- CUDA renders are useful but optional unless a request marks them required.",
        "- Record `project_gpu_accel_type.current_name` and raw value in the manifest.",
        "- Keep `ADBE Force CPU GPU` / hidden GPU Rendering as reference-only metadata.",
        "- Save `before_effects_frame` and the effect output PNG for every case.",
        "- Record all selected effect property names, match_names, indices, values,",
        "  and enabled/active state.",
        "- If a request asks for instrumentation that AE scripting cannot access,",
        "  record that limitation explicitly rather than inventing a value.",
        "",
        f"Selected requests: {len(validated)}",
        f"Total requested cases before render-set multiplication: {total_cases}",
        "",
        "## Request Summaries",
        "",
    ]
    for _path, data in validated:
        lines.append(request_summary(data))
        lines.append("")

    lines.extend(
        [
            "## Return Shape",
            "",
            "Return one zip containing:",
            "",
            "- Rendered PNG outputs.",
            "- Matching `before_effects_frame` PNGs.",
            "- A manifest JSON with render-set metadata and all effect parameters.",
            "- Any AE script/log output or error screenshots if a case fails.",
            "",
            "The Mac side will import the result with:",
            "",
            "```sh",
            "python3 scripts/intake_olm_return.py path/to/returned_reference.zip --quick",
            "```",
            "",
            "That command auto-detects Windows reference returns, imports the manifest,",
            "runs post-import request checks, prints the prioritized next action, and",
            "runs the quick AE-free aggregate smoke.",
            "",
            "If manual low-level validation is needed, use:",
            "",
            "```sh",
            "python3 refs/scripts/import_and_check_win_reference.py path/to/returned_reference.zip --quick",
            "python3 refs/scripts/verify_reference_request_result.py refs/reference_requests/<request>.json path/to/imported/reference_manifest.json",
            "```",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    root = repo_root()
    request_dir = root / "refs" / "reference_requests"
    if args.pending and args.only:
        print("--pending cannot be combined with --only", file=sys.stderr)
        return 2
    requests = resolve_pending_requests(root, request_dir) if args.pending else resolve_requests(request_dir, args.only)
    if not requests:
        print(f"no request JSON files found in {request_dir}", file=sys.stderr)
        return 1

    output = args.output
    if output is None:
        stamp = dt.datetime.now().strftime("%Y%m%d")
        output = Path("/tmp") / f"olm_reference_requests_{stamp}.zip"
    output = output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)

    validated: list[tuple[Path, dict]] = []
    for request in requests:
        try:
            validated.append((request, validate_request(request)))
        except Exception as exc:  # noqa: BLE001 - show path-specific validation error.
            print(f"invalid request {request}: {exc}", file=sys.stderr)
            return 1

    readme = request_dir / "README.md"
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        if readme.exists():
            zf.write(readme, readme.relative_to(root))
        zf.writestr(HANDOFF_NAME, build_handoff(validated))
        for request, _data in validated:
            zf.write(request, request.relative_to(root))

    print(f"wrote {output}")
    for request, data in validated:
        print(f"- {request.name}: {data['request_id']} ({len(data['cases'])} cases)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
