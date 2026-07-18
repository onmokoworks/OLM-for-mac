#!/usr/bin/env python3
"""Run a bounded, replay-resumable DirectionalBlur natural continuation.

The 20260717 probe already contains the delicate host callback plumbing.  This
runner treats that probe as the execution kernel and adds an explicit,
fail-closed continuation ledger around it:

* the accepted populate witness is validated before a run;
* each run is bounded by the kernel's fixed instruction budget;
* a JSON token records the last proven checkpoint and the exact replay command;
* --resume validates the token and replays the same natural path.

This is deliberately replay-resumable, not a fabricated CPU-memory restore.
The 20260717 kernel's private continuation is process-local, so the next
process must rebuild the same callback topology before continuing.  That
limitation is recorded in the report instead of being hidden.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
KERNEL = ROOT / "tools/emulation/test_olmdirectionalblur_iterate8_natural_prerender_followup_20260717.py"
FIXTURE = ROOT / "tools/emulation/dblur_fullrender_host_fixture_20260711.py"
AEX = ROOT / "plugins_2025/OLMDirectionalBlur.aex"
POPULATE_EVIDENCE = ROOT / "refs/conformance/olmdirectionalblur_actual_populate_checkpoint_20260717.json"
KERNEL_REPORT = ROOT / "refs/conformance/olmdirectionalblur_iterate8_natural_prerender_followup_20260717.json"
DEFAULT_PROGRESS = ROOT / "refs/conformance/olmdirectionalblur_natural_continuation_20260718.json"
DEFAULT_MD = ROOT / "refs/conformance/olmdirectionalblur_natural_continuation_20260718.md"

EXPECTED_KERNEL_SHA = ""
EXPECTED_CHECKPOINTS = (
    "real_populate_return_0x180006980",
    "rotate_sample_0x180002064",
    "rotateback_call_0x180005628",
    "rotateback_return_0x18000562d",
    "output_iterate_call_0x180005665",
    "real_output_callback_0x180006b30",
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def validate_input() -> dict:
    populate = load_json(POPULATE_EVIDENCE)
    if populate.get("status") != "pass":
        raise RuntimeError("accepted populate evidence is not status=pass")
    if populate.get("actual_callback", {}).get("captured", {}).get("plane", {}).get("width") != 26:
        raise RuntimeError("accepted populate evidence is not the natural 26-wide fixture")
    if populate.get("fail_closed", {}).get("windows_values_fabricated") is not False:
        raise RuntimeError("populate evidence is not fail-closed")
    return {
        "path": str(POPULATE_EVIDENCE.relative_to(ROOT)),
        "sha256": sha256(POPULATE_EVIDENCE),
        "status": populate["status"],
        "callback": populate["actual_callback"]["entry"],
        "natural_width": populate["actual_callback"]["captured"]["plane"]["width"],
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--progress", type=Path, default=DEFAULT_PROGRESS)
    parser.add_argument("--report-md", type=Path, default=DEFAULT_MD)
    parser.add_argument("--resume", action="store_true",
                        help="validate the previous replay token before rerunning")
    parser.add_argument("--dry-run", action="store_true",
                        help="validate inputs and print the replay command without running")
    return parser.parse_args()


def kernel_command() -> list[str]:
    return [sys.executable, str(KERNEL)]


def display_kernel_command() -> str:
    return f"python3 {KERNEL.relative_to(ROOT)}"


def run_kernel() -> tuple[int, dict, str, str]:
    previous_report = KERNEL_REPORT.read_bytes() if KERNEL_REPORT.exists() else None
    KERNEL_REPORT.unlink(missing_ok=True)
    process = subprocess.run(kernel_command(), cwd=ROOT, capture_output=True, text=True)
    generated = KERNEL_REPORT.exists()
    kernel_report = load_json(KERNEL_REPORT) if generated else {}
    if process.returncode != 0 or not generated:
        KERNEL_REPORT.unlink(missing_ok=True)
        if previous_report is not None:
            KERNEL_REPORT.write_bytes(previous_report)
    return process.returncode, kernel_report, process.stdout, process.stderr


def checkpoint_summary(kernel_report: dict) -> dict:
    target = kernel_report.get("target", {})
    observed = target.get("natural_continuation_checkpoints", {})
    # The accepted populate witness is stored as target.real_populate by the
    # 20260717 kernel; later checkpoints are stored in its checkpoint map.
    observed_names = set(observed)
    if target.get("real_populate"):
        observed_names.add("real_populate_return_0x180006980")
    ordered = [name for name in EXPECTED_CHECKPOINTS if name in observed_names]
    first_missing = next((name for name in EXPECTED_CHECKPOINTS if name not in observed_names), None)
    continuation = kernel_report.get("natural_prerender_owner", {}).get("continuation_boundary", {})
    return {
        "observed": ordered,
        "first_missing": first_missing,
        "last_observed": ordered[-1] if ordered else None,
        "initial_fixture_status_before_explicit_continuation": kernel_report.get("natural_prerender_owner", {}).get("fixture_status"),
        "initial_fixture_blocker_before_explicit_continuation": continuation.get("raw_fixture_reason"),
        "initial_fixture_last_rip": continuation.get("last_rip"),
        "downstream_write": target.get("first_distinct_write_0x8078_to_0x8090"),
        "output_callback": "real_output_callback_0x180006b30" in observed_names,
        "final_blocker": None if first_missing is None and target.get("first_distinct_write_0x8078_to_0x8090") and "real_output_callback_0x180006b30" in observed_names else (first_missing or "natural-continuation"),
    }


def render_md(report: dict) -> str:
    run = report["run"]
    checkpoints = report["checkpoint_state"]
    lines = [
        "# OLMDirectionalBlur Natural Continuation 20260718",
        "",
        f"- Status: `{report['status']}`.",
        "- Scope: natural 8bpc AEX path, accepted actual populate callback through downstream continuation.",
        "- Production source changed: `False`.",
        "- Windows values fabricated: `False`.",
        "- AE exact claim: `False`.",
        "",
        "## Checkpoint State",
        "",
        f"- Accepted populate evidence: `{report['input']['path']}` (sha256 `{report['input']['sha256']}`).",
        f"- Observed in this bounded replay: `{', '.join(checkpoints['observed']) or 'none'}`.",
        f"- First missing checkpoint: `{checkpoints['first_missing']}`.",
        f"- Last observed checkpoint: `{checkpoints['last_observed']}`.",
        f"- Downstream target-cell write: `{bool(checkpoints['downstream_write'])}`.",
        f"- Real output callback: `{checkpoints['output_callback']}`.",
        f"- Initial fixture blocker before explicit continuation: `{checkpoints['initial_fixture_blocker_before_explicit_continuation']}` at `{checkpoints['initial_fixture_last_rip']}`.",
        f"- Final blocker: `{checkpoints['final_blocker']}`.",
        "",
        "## FACT",
        "",
        "- The accepted populate witness is a real AEX callback at `0x180006980` in the natural 26-wide fixture.",
        "- The kernel preserves the outer Iterate8 frame while invoking the callback through a private return sentinel.",
        f"- This run returned kernel status `{run['kernel_status']}` with subprocess return code `{run['returncode']}`.",
        "- A downstream write is counted only when a real AEX memory write overlaps the natural `params+0x8090` target cell after populate.",
        "",
        "## INFERENCE",
        "",
        "- A `pass` here is a bounded natural-path continuation witness, not Mac AE exactness.",
        "- A `blocked` result identifies the first missing callback/state and is the only safe conclusion when the natural path stops early.",
        "- `--resume` replays the same bounded kernel after validating the saved token; it does not restore serialized AEX CPU memory.",
        "",
        "## Reproduction",
        "",
        f"`python3 {Path(__file__).relative_to(ROOT)}`",
        f"`python3 {Path(__file__).relative_to(ROOT)} --resume`",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    input_evidence = validate_input()
    previous = load_json(args.progress) if args.progress.exists() else None
    if args.resume:
        if not previous or previous.get("schema") != 1:
            raise RuntimeError("--resume requires a schema=1 progress report")
        if previous.get("provenance", {}).get("aex_sha256") != sha256(AEX):
            raise RuntimeError("--resume refused: AEX identity changed")
        if previous.get("provenance", {}).get("kernel_sha256") != sha256(KERNEL):
            raise RuntimeError("--resume refused: kernel identity changed")
        if previous.get("input", {}).get("sha256") != input_evidence["sha256"]:
            raise RuntimeError("--resume refused: accepted populate evidence changed")

    command = display_kernel_command()
    if args.dry_run:
        print(json.dumps({"status": "ready", "resume": args.resume, "command": command}, indent=2))
        return 0

    returncode, kernel_report, stdout, stderr = run_kernel()
    state = checkpoint_summary(kernel_report)
    complete = (
        returncode == 0
        and kernel_report.get("status") == "pass"
        and state["first_missing"] is None
        and bool(state["downstream_write"])
        and state["output_callback"]
    )
    status = "pass" if complete else "blocked"
    report = {
        "schema": 1,
        "kind": "olmdirectionalblur_natural_continuation_20260718",
        "status": status,
        "created_at_utc": now_utc(),
        "input": input_evidence,
        "provenance": {
            "aex": str(AEX.relative_to(ROOT)),
            "aex_sha256": sha256(AEX),
            "kernel": str(KERNEL.relative_to(ROOT)),
            "kernel_sha256": sha256(KERNEL),
            "fixture": str(FIXTURE.relative_to(ROOT)),
            "fixture_sha256": sha256(FIXTURE),
        },
        "run": {
            "mode": "replay-resume" if args.resume else "fresh-bounded",
            "returncode": returncode,
            "kernel_status": kernel_report.get("status"),
            "command": command,
            "stdout_tail": stdout[-4000:],
            "stderr_tail": stderr[-4000:],
        },
        "checkpoint_state": state,
        "resume_token": {
            "kind": "replay-resume",
            "next_action": ("none; bounded natural chain reached writer and output callback"
                             if status == "pass" else "replay bounded kernel after host/state blocker is addressed"),
            "replay_command": command,
            "last_observed_checkpoint": state["last_observed"],
            "first_missing_checkpoint": state["first_missing"],
        },
        "fact_inference": {
            "facts": [
                "Accepted actual populate evidence was validated before execution.",
                "No production source, Windows value, or PNG tuning was used.",
                "Downstream write requires a real AEX memory-write event overlapping the natural writer cell.",
            ],
            "inferences": [
                "Replay-resume is the safe continuation mechanism because the 20260717 private AEX state is process-local.",
                "A blocked result is a missing host callback/state, not evidence that the algorithm is wrong.",
            ],
        },
        "fail_closed": {
            "production_source_edited": False,
            "windows_values_fabricated": False,
            "png_tuning": False,
            "ae_exact_claim": False,
        },
    }
    args.progress.parent.mkdir(parents=True, exist_ok=True)
    args.progress.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    args.report_md.parent.mkdir(parents=True, exist_ok=True)
    args.report_md.write_text(render_md(report), encoding="utf-8")
    print(json.dumps({"status": status, "report": str(args.progress), "report_md": str(args.report_md),
                      "first_missing": state["first_missing"], "last_observed": state["last_observed"],
                      "downstream_write": bool(state["downstream_write"]),
                      "output_callback": state["output_callback"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
