#!/usr/bin/env python3
"""Run scripts/ae_render_single_case.jsx through a live After Effects instance."""

from __future__ import annotations

import argparse
import contextlib
import fcntl
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path


VOLATILE_AE_ENV_KEYS = (
    "OLM_AE_DISABLE_EFFECT",
    "OLM_AE_DISABLE_PROJECT_COLOR_MANAGEMENT",
    "OLM_AE_FORCE_NEW_PROJECT",
    "OLM_AE_FORCE_SOFTWARE",
    "OLM_AE_INPUT_ALPHA_MODE",
    "OLM_DBLUR_CAPTURE_PREFIX",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--request-dir", type=Path, required=True)
    parser.add_argument("--case-id", required=True)
    parser.add_argument("--output-dir", type=Path, default=None)
    parser.add_argument("--app-name", default="Adobe After Effects 2026")
    parser.add_argument("--output-mode", choices=("png", "exr_render_queue"), default="png")
    parser.add_argument("--output-template", default="", help="Output Module template required for --output-mode exr_render_queue.")
    parser.add_argument("--keep-open", action="store_true", help="Keep the live AE project/application open after rendering.")
    parser.add_argument("--timeout", type=int, default=1200)
    parser.add_argument(
        "--param-override",
        action="append",
        default=[],
        metavar="NAME=JSON",
        help="Override one AE parameter by display name or match name, e.g. 'Use Background Color=0'.",
    )
    parser.add_argument(
        "--ae-env",
        action="append",
        default=[],
        metavar="NAME=VALUE",
        help="Set an ExtendScript environment variable before running the case.",
    )
    parser.add_argument(
        "--lock-path",
        type=Path,
        default=Path("/tmp/olm_ae_single_case.lock"),
        help="Serialize AE host runs that use shared $.setenv state.",
    )
    parser.add_argument("--dump-js", type=Path, default=None, help="Write the generated ExtendScript wrapper and exit.")
    return parser.parse_args()


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def js_string(value: str) -> str:
    return json.dumps(value)


def js_escape_expr(value: str) -> str:
    return (
        str(value)
        .replace("\\", "\\\\")
        .replace('"', '\\"')
        .replace("\r", "\\r")
        .replace("\n", "\\n")
    )


@contextlib.contextmanager
def ae_lock(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a+") as lock_file:
        fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)


def main() -> int:
    args = parse_args()
    root = repo_root()
    request_dir = args.request_dir.resolve()
    if not request_dir.exists():
        print(f"[FAIL] request dir not found: {request_dir}", file=sys.stderr)
        return 1
    output_dir = (
        args.output_dir.resolve()
        if args.output_dir
        else Path("/tmp") / f"olm_ae_single_case_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    log_path = output_dir / "AE_SINGLE_CASE.log"
    result_json = output_dir / "AE_SINGLE_CASE_RESULT.json"
    jsx_path = root / "scripts" / "ae_render_single_case.jsx"
    overrides: dict[str, object] = {}
    for item in args.param_override:
        if "=" not in item:
            print(f"[FAIL] --param-override must be NAME=JSON: {item}", file=sys.stderr)
            return 1
        key, raw_value = item.split("=", 1)
        try:
            value = json.loads(raw_value)
        except json.JSONDecodeError:
            value = raw_value
        overrides[key] = value
    ae_env: dict[str, str] = {}
    for item in args.ae_env:
        if "=" not in item:
            print(f"[FAIL] --ae-env must be NAME=VALUE: {item}", file=sys.stderr)
            return 1
        key, value = item.split("=", 1)
        if not key:
            print(f"[FAIL] --ae-env key is empty: {item}", file=sys.stderr)
            return 1
        ae_env[key] = value
    if args.output_mode == "exr_render_queue" and not args.output_template:
        print("[FAIL] --output-template is required for --output-mode exr_render_queue", file=sys.stderr)
        return 1
    reset_env_lines = [f"$.setenv({js_string(key)}, '');" for key in VOLATILE_AE_ENV_KEYS]
    extra_env_lines = [f"$.setenv({js_string(key)}, {js_string(value)});" for key, value in sorted(ae_env.items())]
    js = "\n".join(
        [
            "function __olmWriteText(path, text) { var f = new File(path); f.encoding = 'UTF-8'; if (f.open('w')) { f.write(text); f.close(); } }",
            "function __olmEsc(value) { return String(value).replace(/\\\\/g, '\\\\\\\\').replace(/\"/g, '\\\\\"').replace(/\\r/g, '\\\\r').replace(/\\n/g, '\\\\n'); }",
            *reset_env_lines,
            f"$.setenv('OLM_AE_REQUEST_DIR', {js_string(str(request_dir))});",
            f"$.setenv('OLM_AE_CASE_ID', {js_string(args.case_id)});",
            f"$.setenv('OLM_AE_OUTPUT_DIR', {js_string(str(output_dir))});",
            f"$.setenv('OLM_AE_LOG_PATH', {js_string(str(log_path))});",
            f"$.setenv('OLM_AE_RESULT_JSON', {js_string(str(result_json))});",
            f"$.setenv('OLM_AE_PARAM_OVERRIDES_JSON', {js_string(json.dumps(overrides))});",
            f"$.setenv('OLM_AE_OUTPUT_MODE', {js_string(args.output_mode)});",
            f"$.setenv('OLM_AE_OUTPUT_TEMPLATE', {js_string(args.output_template)});",
            f"$.setenv('OLM_AE_KEEP_OPEN', {js_string('1' if args.keep_open else '0')});",
            *extra_env_lines,
            "try {",
            f"  $.evalFile(new File({js_string(str(jsx_path))}));",
            "} catch (__olmError) {",
            f"  __olmWriteText({js_string(str(log_path))}, 'wrapper.error ' + __olmError.toString() + '\\n');",
            (
                f"  __olmWriteText({js_string(str(result_json))}, "
                "'{\\n'"
                f" + '  \"kind\": \"olm_ae_single_case_result\",\\n'"
                f" + '  \"ae_version\": \"' + __olmEsc(app.version) + '\",\\n'"
                f" + '  \"request_dir\": \"{js_escape_expr(str(request_dir))}\",\\n'"
                f" + '  \"case_id\": \"{js_escape_expr(args.case_id)}\",\\n'"
                f" + '  \"output_dir\": \"{js_escape_expr(str(output_dir))}\",\\n'"
                f" + '  \"output_png\": \"\",\\n'"
                f" + '  \"output_exr\": \"\",\\n'"
                f" + '  \"status\": \"error\",\\n'"
                f" + '  \"error\": \"' + __olmEsc(__olmError.toString()) + '\",\\n'"
                f" + '  \"warnings\": []\\n'"
                " + '}\\n');"
            ),
            "}",
        ]
    )
    if args.dump_js:
        args.dump_js.parent.mkdir(parents=True, exist_ok=True)
        args.dump_js.write_text(js, encoding="utf-8")
        print(f"[OK] wrote ExtendScript wrapper: {args.dump_js}")
        return 0
    wrapper_jsx = output_dir / "AE_SINGLE_CASE_WRAPPER.jsx"
    wrapper_jsx.write_text(js, encoding="utf-8")
    apple_script = (
        f"with timeout of {int(args.timeout)} seconds\n"
        f"tell application {js_string(args.app_name)} to DoScriptFile POSIX file {js_string(str(wrapper_jsx))} with override\n"
        "end timeout\n"
    )
    with ae_lock(args.lock_path.resolve()):
        proc = subprocess.run(
            ["osascript"],
            input=apple_script,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=args.timeout + 30,
        )
    if proc.stdout:
        print(proc.stdout, end="" if proc.stdout.endswith("\n") else "\n")
    if proc.stderr:
        print(proc.stderr, end="" if proc.stderr.endswith("\n") else "\n", file=sys.stderr)
    if proc.returncode != 0:
        print(f"[FAIL] osascript exited {proc.returncode}", file=sys.stderr)
        print(f"[INFO] output_dir: {output_dir}")
        return proc.returncode
    if not result_json.exists():
        print(f"[FAIL] AE did not write result JSON: {result_json}", file=sys.stderr)
        print(f"[INFO] output_dir: {output_dir}")
        return 1
    result = json.loads(result_json.read_text(encoding="utf-8-sig"))
    print(f"[OK] AE single case status: {result.get('status')}")
    print(f"[INFO] output_dir: {output_dir}")
    print(f"[INFO] result_json: {result_json}")
    if result.get("output_png"):
        print(f"[INFO] output_png: {result['output_png']}")
    observation = result.get("png_observation") or {}
    if observation:
        print(
            f"[INFO] png_observation: {observation.get('status')} "
            f"waited_ms={observation.get('waited_ms', 0)} "
            f"size_bytes={observation.get('size_bytes', 0)}"
        )
    if result.get("output_exr"):
        print(f"[INFO] output_exr: {result['output_exr']}")
    if result.get("status") != "ok":
        print(f"[FAIL] AE single case error: {result.get('error')}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
