#!/usr/bin/env python3
"""Run the Output Module template probe through an already-running AE GUI."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path, help="Probe JSON output path.")
    parser.add_argument("--app-name", default="Adobe After Effects 2026")
    parser.add_argument("--timeout", type=int, default=120)
    parser.add_argument("--dump-js", type=Path, help="Write the wrapper JSX without contacting AE.")
    return parser.parse_args()


def wrapper_script(probe: Path, output: Path) -> str:
    # The probe owns the JSON response. This wrapper only injects its output path
    # into the live ExtendScript engine, avoiding AE's cold `-r` launch path.
    return "\n".join(
        [
            f"$.setenv('OLM_AE_OUTPUT_MODULE_PROBE', {json.dumps(str(output))});",
            "try {",
            f"  $.evalFile(new File({json.dumps(str(probe))}));",
            "} catch (error) {",
            "  throw error;",
            "}",
            "",
        ]
    )


def main() -> int:
    args = parse_args()
    output = args.output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    probe = ROOT / "scripts" / "ae_probe_output_module_templates.jsx"
    wrapper = output.parent / "AE_OUTPUT_MODULE_PROBE_WRAPPER.jsx"
    script = wrapper_script(probe, output)
    if args.dump_js:
        args.dump_js.parent.mkdir(parents=True, exist_ok=True)
        args.dump_js.write_text(script, encoding="utf-8")
        print(f"[OK] wrote ExtendScript wrapper: {args.dump_js}")
        return 0
    if output.exists():
        output.unlink()
    wrapper.write_text(script, encoding="utf-8")
    apple_script = (
        f"with timeout of {int(args.timeout)} seconds\n"
        f"tell application {json.dumps(args.app_name)} to DoScriptFile POSIX file {json.dumps(str(wrapper))} with override\n"
        "end timeout\n"
    )
    proc = subprocess.run(
        ["osascript"], input=apple_script, text=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=args.timeout + 30,
    )
    if proc.stdout:
        print(proc.stdout, end="" if proc.stdout.endswith("\n") else "\n")
    if proc.stderr:
        print(proc.stderr, end="" if proc.stderr.endswith("\n") else "\n", file=sys.stderr)
    if proc.returncode:
        print(f"[FAIL] osascript exited {proc.returncode}", file=sys.stderr)
        return proc.returncode
    if not output.is_file():
        print(f"[FAIL] AE did not write template probe: {output}", file=sys.stderr)
        return 1
    try:
        result = json.loads(output.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as exc:
        print(f"[FAIL] invalid probe JSON: {exc}", file=sys.stderr)
        return 1
    if result.get("error"):
        print(f"[FAIL] AE template probe: {result['error']}", file=sys.stderr)
        return 1
    templates = result.get("templates")
    if not isinstance(templates, list):
        print("[FAIL] template probe did not return a templates array", file=sys.stderr)
        return 1
    print(f"[OK] AE {result.get('ae_version', '?')}: {len(templates)} output module template(s)")
    print(f"[INFO] probe: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
