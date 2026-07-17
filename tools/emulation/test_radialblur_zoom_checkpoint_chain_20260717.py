#!/usr/bin/env python3
"""Regression gate for chained RadialBlur natural-render checkpoints."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
RUNNER = ROOT / "tools/emulation/test_zoom_case0009.py"
MATERIALIZER = ROOT / "tools/emulation/materialize_radialblur_checkpoint_journey_20260717.py"
AEX = ROOT / "aex/OLMRadialBlur/Plugins/64/2025/OLMRadialBlur.aex"
DEFAULT_JSON = ROOT / "refs/conformance/olmradialblur_zoom_checkpoint_chain_20260717.json"
DEFAULT_MD = ROOT / "refs/conformance/olmradialblur_zoom_checkpoint_chain_20260717.md"


def run(*args: str) -> str:
    process = subprocess.run(
        [sys.executable, str(RUNNER), *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if process.returncode != 0:
        raise AssertionError(
            f"runner failed with {process.returncode}\nstdout:\n{process.stdout}\nstderr:\n{process.stderr}"
        )
    return process.stdout


def run_materializer(*args: str) -> str:
    process = subprocess.run(
        [sys.executable, str(MATERIALIZER), *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if process.returncode != 0:
        raise AssertionError(
            f"materializer failed with {process.returncode}\nstdout:\n{process.stdout}\nstderr:\n{process.stderr}"
        )
    return process.stdout


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def output_rip(stdout: str, label: str) -> str:
    return stdout.split(f"{label}=", 1)[1].splitlines()[0]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-json", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--output-md", type=Path, default=DEFAULT_MD)
    args = parser.parse_args()

    with tempfile.TemporaryDirectory(prefix="olm_radial_checkpoint_chain_") as tmp:
        work = Path(tmp)
        staging = work / "staging.aexcp"
        progress1 = work / "progress1.aexcp"
        progress2 = work / "progress2.aexcp"

        first = run(
            "--save-checkpoint-at-rip", str(staging), "0x180007811",
            "--max-instructions", "1000000",
            "--output-json", str(work / "first.json"),
            "--output-md", str(work / "first.md"),
        )
        assert "checkpoint_rip=0x180007811" in first
        assert staging.is_file()

        second = run(
            "--resume-checkpoint", str(staging),
            "--save-progress-checkpoint", str(progress1),
            "--max-instructions", "100000",
            "--output-json", str(work / "second.json"),
            "--output-md", str(work / "second.md"),
        )
        assert "progress_checkpoint_saved=" in second
        assert progress1.is_file()

        third = run(
            "--resume-checkpoint", str(progress1),
            "--save-progress-checkpoint", str(progress2),
            "--max-instructions", "100000",
            "--output-json", str(work / "third.json"),
            "--output-md", str(work / "third.md"),
        )
        assert "progress_checkpoint_saved=" in third
        assert progress2.is_file()
        first_progress_rip = output_rip(second, "progress_checkpoint_rip")
        second_progress_rip = output_rip(third, "progress_checkpoint_rip")
        assert first_progress_rip != second_progress_rip

        journey_json = work / "journey.json"
        journey_md = work / "journey.md"
        materialized = run_materializer(
            "--checkpoint", f"staging={staging}",
            "--checkpoint", f"progress1={progress1}",
            "--checkpoint", f"progress2={progress2}",
            "--output-json", str(journey_json),
            "--output-md", str(journey_md),
        )
        assert "PASS checkpoint journey: 3 stages" in materialized
        journey = json.loads(journey_json.read_text(encoding="utf-8"))
        assert journey["checks"]["causal_parent_chain"] is True
        assert journey["checks"]["no_direct_zoom_core"] is True

        report = {
            "kind": "olmradialblur_zoom_checkpoint_chain_20260717",
            "status": "pass_local_transport_only",
            "aex": {
                "path": str(AEX.relative_to(ROOT)),
                "sha256": sha256(AEX),
            },
            "entry_checkpoint": {
                "rip": "0x180007811",
                "sha256": sha256(staging),
                "size": staging.stat().st_size,
            },
            "progress_hops": [
                {
                    "instruction_budget": 100000,
                    "rip": first_progress_rip,
                    "sha256": sha256(progress1),
                    "size": progress1.stat().st_size,
                },
                {
                    "instruction_budget": 100000,
                    "rip": second_progress_rip,
                    "sha256": sha256(progress2),
                    "size": progress2.stat().st_size,
                },
            ],
            "checks": {
                "fresh_process_resume_twice": True,
                "rip_advanced_between_hops": True,
                "complete_sha_ancestry_verified": journey["checks"]["causal_parent_chain"],
                "no_direct_zoom_core": journey["checks"]["no_direct_zoom_core"],
                "checkpoint_files_nonempty": all(path.stat().st_size > 0 for path in (staging, progress1, progress2)),
            },
            "claims_not_made": [
                "No full-frame core, sampler, writer, Windows, or AE-exact claim",
                "No synthetic prefill or worker detour",
            ],
        }

    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_md.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    args.output_md.write_text(
        "\n".join(
            [
                "# OLMRadialBlur natural-render checkpoint chain",
                "",
                f"- Status: `{report['status']}`",
                f"- AEX SHA-256: `{report['aex']['sha256']}`",
                "- Entry checkpoint: `0x180007811`",
                f"- Progress RIPs: `{first_progress_rip}` -> `{second_progress_rip}`",
                "- Two fresh-process resumes completed and produced distinct live RIPs.",
                "- Scope: checkpoint transport only; no full-frame output, Windows, or AE-exact claim.",
                "",
            ]
        ),
        encoding="utf-8",
    )

    print("PASS RadialBlur natural-render checkpoint chain: entry + 2 progress hops")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
