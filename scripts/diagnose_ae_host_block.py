#!/usr/bin/env python3
"""Diagnose local After Effects automation/modal blockers.

This script is intentionally read-only by default: it does not launch or kill
After Effects. It records whether AE is running, whether System Events can see
windows, and whether a process sample looks stuck in a modal dialog.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


MODAL_NEEDLES = {
    "dvaui_message_box": "dvaui::dialogs::UI_MessageBox::RunModal",
    "dvaui_os_dialog": "dvaui::ui::OS_Dialog::ModalLoop",
    "cf_user_notification": "CFUserNotificationDisplayAlert",
    "ns_run_modal": "runModal",
    "modal_session": "ModalSession",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--process-name", default="After Effects", help="Process name passed to pgrep/System Events.")
    parser.add_argument("--output-dir", type=Path, default=None, help="Directory for JSON/Markdown diagnostics.")
    parser.add_argument("--sample-seconds", type=int, default=5, help="Seconds to sample each AE process.")
    parser.add_argument("--no-sample", action="store_true", help="Skip live process sampling.")
    parser.add_argument(
        "--sample-file",
        type=Path,
        default=None,
        help="Analyze an existing sample file instead of running sample(1). Useful for smoke tests.",
    )
    return parser.parse_args()


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def timestamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def run_cmd(cmd: list[str], *, input_text: str | None = None, timeout: int = 10) -> dict[str, Any]:
    try:
        proc = subprocess.run(
            cmd,
            input=input_text,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
        )
        return {
            "cmd": cmd,
            "returncode": proc.returncode,
            "stdout": proc.stdout,
            "stderr": proc.stderr,
            "timed_out": False,
        }
    except subprocess.TimeoutExpired as exc:
        return {
            "cmd": cmd,
            "returncode": None,
            "stdout": exc.stdout or "",
            "stderr": exc.stderr or "",
            "timed_out": True,
        }


def pgrep_process(name: str) -> list[int]:
    proc = run_cmd(["pgrep", "-x", name])
    if proc["returncode"] != 0:
        return []
    pids: list[int] = []
    for line in str(proc["stdout"]).splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            pids.append(int(line))
        except ValueError:
            pass
    return pids


def system_events_snapshot(process_name: str) -> dict[str, Any]:
    script = f'''
tell application "System Events"
  set outText to ""
  if exists process "{process_name}" then
    tell process "{process_name}"
      set outText to outText & "process_exists=true" & linefeed
      set outText to outText & "frontmost=" & (frontmost as text) & linefeed
      set outText to outText & "windows=" & ((count of windows) as text) & linefeed
      repeat with w in windows
        set outText to outText & "window=" & (name of w as text) & linefeed
        try
          set outText to outText & "buttons=" & ((count of buttons of w) as text) & linefeed
        end try
        try
          repeat with b in buttons of w
            set outText to outText & "button=" & (name of b as text) & linefeed
          end repeat
        end try
        try
          repeat with s in static texts of w
            set outText to outText & "static_text=" & (value of s as text) & linefeed
          end repeat
        end try
      end repeat
    end tell
  else
    set outText to "process_exists=false" & linefeed
  end if
end tell
return outText
'''
    result = run_cmd(["osascript"], input_text=script, timeout=10)
    result["parsed"] = parse_key_lines(str(result.get("stdout") or ""))
    stderr = str(result.get("stderr") or "")
    result["accessibility_denied"] = any(
        needle in stderr
        for needle in (
            "補助アクセス",
            "assistive access",
            "not authorized",
            "not permitted",
            "-25211",
        )
    )
    return result


def parse_key_lines(text: str) -> dict[str, list[str]]:
    parsed: dict[str, list[str]] = {}
    for raw_line in text.splitlines():
        if "=" not in raw_line:
            continue
        key, value = raw_line.split("=", 1)
        parsed.setdefault(key.strip(), []).append(value.strip())
    return parsed


def analyze_sample_text(text: str) -> dict[str, Any]:
    flags = {key: needle in text for key, needle in MODAL_NEEDLES.items()}
    modal_hit = any(flags.values())
    if flags["dvaui_message_box"] or flags["dvaui_os_dialog"] or flags["cf_user_notification"]:
        likely_status = "ae-modal-dialog"
    elif modal_hit:
        likely_status = "possibly-modal"
    elif text.strip():
        likely_status = "sample-collected-no-known-modal"
    else:
        likely_status = "no-sample"
    return {
        "likely_status": likely_status,
        "modal_flags": flags,
        "matched_needles": [needle for key, needle in MODAL_NEEDLES.items() if flags[key]],
    }


def sample_process(pid: int, seconds: int, output_path: Path) -> dict[str, Any]:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    result = run_cmd(["sample", str(pid), str(seconds), "-file", str(output_path)], timeout=max(seconds + 20, 30))
    result["output_path"] = str(output_path)
    if output_path.exists():
        result["analysis"] = analyze_sample_text(output_path.read_text(encoding="utf-8", errors="replace"))
    else:
        result["analysis"] = analyze_sample_text("")
    return result


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# AE Host Automation Diagnostic",
        "",
        f"- generated_at: `{report['generated_at']}`",
        f"- process_name: `{report['process_name']}`",
        f"- overall_status: `{report['overall_status']}`",
        f"- pids: `{', '.join(str(pid) for pid in report['pids']) or 'none'}`",
        "",
        "## System Events",
        "",
    ]
    events = report["system_events"]
    lines.extend(
        [
            f"- returncode: `{events.get('returncode')}`",
            f"- timed_out: `{events.get('timed_out')}`",
            f"- accessibility_denied: `{events.get('accessibility_denied')}`",
            f"- parsed: `{json.dumps(events.get('parsed', {}), ensure_ascii=False)}`",
        ]
    )
    if events.get("stderr"):
        lines.append(f"- stderr: `{str(events['stderr']).strip()}`")
    lines.extend(["", "## Samples", ""])
    for row in report["samples"]:
        analysis = row.get("analysis", {})
        lines.extend(
            [
                f"### PID {row.get('pid', 'sample-file')}",
                "",
                f"- sample_path: `{row.get('output_path', row.get('sample_file', ''))}`",
                f"- likely_status: `{analysis.get('likely_status', 'unknown')}`",
                f"- matched_needles: `{', '.join(analysis.get('matched_needles', [])) or 'none'}`",
                "",
            ]
        )
    lines.extend(["## Suggested Next Action", "", f"- {report['suggested_next_action']}"])
    return "\n".join(lines) + "\n"


def classify_report(pids: list[int], system_events: dict[str, Any], samples: list[dict[str, Any]]) -> tuple[str, str]:
    if samples:
        statuses = [str(row.get("analysis", {}).get("likely_status", "")) for row in samples]
        if "ae-modal-dialog" in statuses:
            action = "Bring After Effects to foreground and clear the hidden/modal dialog; rerun this diagnostic before AE validation."
            if system_events.get("accessibility_denied"):
                action += " Also grant Accessibility permission to the app running this script if UI introspection is needed."
            return ("host-blocked-modal-dialog", action)
        if "possibly-modal" in statuses:
            return (
                "host-blocked-possible-modal",
                "Inspect After Effects UI manually, then rerun this diagnostic or try the single-case renderer.",
            )
    if not pids:
        return (
            "ae-not-running",
            "Start After Effects normally, confirm no startup dialog remains, then rerun this diagnostic.",
        )
    parsed = system_events.get("parsed", {})
    if system_events.get("accessibility_denied"):
        return (
            "ae-running-accessibility-denied",
            "Grant Accessibility permission to the app running this script, then rerun the diagnostic before AE validation.",
        )
    windows = parsed.get("windows", [])
    if windows == ["0"]:
        return (
            "ae-running-no-accessible-window",
            "After Effects is running but has no accessible windows; check for splash/login/modal UI or relaunch AE.",
        )
    return (
        "ae-running-no-known-modal",
        "Try the bounded AE validation renderer; if it hangs, rerun this diagnostic with sampling enabled.",
    )


def main() -> int:
    args = parse_args()
    root = repo_root()
    out_dir = args.output_dir or root / "refs" / "reports" / "ae_host_diagnostics" / timestamp()
    out_dir.mkdir(parents=True, exist_ok=True)

    pids = pgrep_process(args.process_name)
    system_events = system_events_snapshot(args.process_name)
    samples: list[dict[str, Any]] = []

    if args.sample_file is not None:
        sample_text = args.sample_file.read_text(encoding="utf-8", errors="replace")
        samples.append(
            {
                "pid": None,
                "sample_file": str(args.sample_file),
                "analysis": analyze_sample_text(sample_text),
            }
        )
    elif not args.no_sample:
        for pid in pids:
            samples.append(sample_process(pid, args.sample_seconds, out_dir / f"sample_{pid}.txt") | {"pid": pid})

    overall_status, suggested_next_action = classify_report(pids, system_events, samples)
    report = {
        "schema": 1,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "process_name": args.process_name,
        "pids": pids,
        "overall_status": overall_status,
        "suggested_next_action": suggested_next_action,
        "system_events": system_events,
        "samples": samples,
    }

    json_path = out_dir / "ae_host_diagnostic.json"
    md_path = out_dir / "ae_host_diagnostic.md"
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    md_path.write_text(render_markdown(report), encoding="utf-8")

    print(f"[OK] AE host diagnostic: {overall_status}")
    print(f"[INFO] JSON: {json_path}")
    print(f"[INFO] Markdown: {md_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
