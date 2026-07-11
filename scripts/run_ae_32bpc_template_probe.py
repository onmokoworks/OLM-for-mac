#!/usr/bin/env python3
"""Run a 32bpc Render Queue EXR template probe through a live AE GUI."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--template", default="OLM EXR 32 Float")
    parser.add_argument("--app-name", default="Adobe After Effects 2026")
    parser.add_argument("--timeout", type=int, default=180)
    args = parser.parse_args()
    output = args.output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    result = output.parent / "AE_32BPC_TEMPLATE_PROBE_RESULT.json"
    wrapper = output.parent / "AE_32BPC_TEMPLATE_PROBE_WRAPPER.jsx"
    jsx = ROOT / "scripts" / "ae_render_32bpc_template_probe.jsx"
    for path in (output, result):
        if path.exists(): path.unlink()
    wrapper.write_text("\n".join([
        f"$.setenv('OLM_AE_EXR_PROBE_OUTPUT', {json.dumps(str(output))});",
        f"$.setenv('OLM_AE_EXR_PROBE_RESULT', {json.dumps(str(result))});",
        f"$.setenv('OLM_AE_EXR_TEMPLATE', {json.dumps(args.template)});",
        f"$.evalFile(new File({json.dumps(str(jsx))}));",
        "",
    ]), encoding="utf-8")
    apple = (f"with timeout of {args.timeout} seconds\n"
             f"tell application {json.dumps(args.app_name)} to DoScriptFile POSIX file {json.dumps(str(wrapper))} with override\n"
             "end timeout\n")
    proc = subprocess.run(["osascript"], input=apple, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=args.timeout + 30)
    if proc.stdout: print(proc.stdout, end="")
    if proc.stderr: print(proc.stderr, end="", file=sys.stderr)
    if proc.returncode: return proc.returncode
    if not result.is_file():
        print(f"[FAIL] AE did not write result: {result}", file=sys.stderr); return 1
    payload = json.loads(result.read_text(encoding="utf-8-sig"))
    actual = Path(payload.get("output", ""))
    if payload.get("status") != "ok" or not actual.is_file():
        print(f"[FAIL] template probe: {payload.get('error')}", file=sys.stderr); return 1
    if actual != output:
        actual.replace(output)
    print(f"[OK] 32bpc template rendered: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
