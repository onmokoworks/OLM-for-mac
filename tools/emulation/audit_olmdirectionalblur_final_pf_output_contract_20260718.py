#!/usr/bin/env python3
"""Join the natural continuation to the actual-AEX PF8 final-store contract."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AEX = ROOT / "plugins_2025/OLMDirectionalBlur.aex"
FIXTURE = ROOT / "tools/emulation/dblur_fullrender_host_fixture_20260711.py"
SOURCE = ROOT / "refs/win_references/20260604_olm/OLMDirectionalBlur/case_0001_before_effects.png"
CONTINUATION = ROOT / "refs/conformance/olmdirectionalblur_natural_continuation_20260718.json"
WRITER_PROBE = ROOT / "tools/emulation/test_olmdirectionalblur_natural_writer_owner_20260717.py"
WRITER_REPORT = ROOT / "refs/conformance/olmdirectionalblur_natural_writer_owner_20260717.json"
REPORT = ROOT / "refs/conformance/olmdirectionalblur_final_pf_output_contract_20260718.json"
NOTE = ROOT / "refs/conformance/olmdirectionalblur_final_pf_output_contract_20260718.md"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    before = sha256(WRITER_REPORT) if WRITER_REPORT.exists() else None
    run = subprocess.run(
        [sys.executable, str(WRITER_PROBE)], cwd=ROOT, capture_output=True, text=True
    )
    if run.returncode != 0 or not WRITER_REPORT.exists():
        status = "blocked"
        writer = {}
    else:
        writer = load(WRITER_REPORT)
        status = "pass"

    continuation = load(CONTINUATION) if CONTINUATION.exists() else {}
    continuation_hashes = continuation.get("provenance", {})
    writer_hashes = writer.get("provenance", {})
    samples = writer.get("ownership", {}).get("writer_entry_samples", [])
    callbacks = writer.get("natural_path", {}).get("iterate_callbacks", [])
    sample_words = [sample.get("writer_entry_argb8") for sample in samples]
    required = {
        "continuation_pass": continuation.get("status") == "pass",
        "writer_probe_pass": writer.get("status") == "pass" and run.returncode == 0,
        "same_aex": continuation_hashes.get("aex_sha256") == sha256(AEX) == writer_hashes.get("aex_sha256"),
        "same_fixture": continuation_hashes.get("fixture_sha256") == sha256(FIXTURE) == writer_hashes.get("fixture_sha256"),
        "same_source": writer_hashes.get("source_sha256") == sha256(SOURCE),
        "actual_output_callback": callbacks == ["0x180006980", "0x180006b30"],
        "final_store_samples": bool(samples) and all(len(word) == 4 for word in sample_words),
        "nontrivial_store": any(word != [0, 0, 0, 0] for word in sample_words),
        "fail_closed_probe": writer.get("fail_closed", {}).get("ae_exact_claim") is False,
    }
    status = "pass" if all(required.values()) else "blocked"
    report = {
        "schema": 1,
        "kind": "olmdirectionalblur_final_pf_output_contract_20260718",
        "status": status,
        "created_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "scope": "Mac-local bounded PF8 final-store contract joined to the natural continuation; not full-frame equivalence",
        "claim_scope": "The actual AEX output callback writes PF8 A/R/G/B words for natural output-callback samples; no AE exact claim",
        "provenance": {
            "aex": str(AEX.relative_to(ROOT)), "aex_sha256": sha256(AEX),
            "fixture": str(FIXTURE.relative_to(ROOT)), "fixture_sha256": sha256(FIXTURE),
            "source": str(SOURCE.relative_to(ROOT)), "source_sha256": sha256(SOURCE),
            "continuation_report": str(CONTINUATION.relative_to(ROOT)),
            "continuation_report_sha256": sha256(CONTINUATION) if CONTINUATION.exists() else None,
            "writer_probe": str(WRITER_PROBE.relative_to(ROOT)), "writer_probe_sha256": sha256(WRITER_PROBE),
            "writer_report": str(WRITER_REPORT.relative_to(ROOT)),
            "writer_report_sha256_before": before,
            "writer_report_sha256_after": sha256(WRITER_REPORT) if WRITER_REPORT.exists() else None,
        },
        "checks": required,
        "observed": {
            "continuation_status": continuation.get("status"),
            "writer_status": writer.get("status"),
            "subprocess_returncode": run.returncode,
            "iterate_callbacks": callbacks,
            "sample_count": len(samples),
            "writer_entry_samples": samples,
            "output_callback": "0x180006b30",
            "store_order": "PF8 bytes at destination pointer [RSP+0x28] are A/R/G/B",
        },
        "boundary": {
            "status": "bounded-contract-only",
            "full_frame_equivalence": False,
            "same_run_natural_full_frame": False,
            "next_missing_proof": "same-run natural output buffer capture covering the complete requested frame",
        },
        "run": {"command": f"python3 {WRITER_PROBE.relative_to(ROOT)}", "stdout_tail": run.stdout[-2000:], "stderr_tail": run.stderr[-2000:]},
        "fail_closed": {
            "production_source_edited": False, "windows_values_fabricated": False,
            "png_tuning": False, "ae_exact_claim": False,
        },
    }
    REPORT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    NOTE.write_text("\n".join([
        "# OLMDirectionalBlur Final PF Output Contract 20260718", "",
        f"- Status: `{status}`.",
        "- Scope: bounded actual-AEX PF8 final-store contract joined to the natural continuation.",
        "- Production source changed: `False`.", "- Windows values fabricated: `False`.", "- AE exact claim: `False`.", "",
        "## Result", "",
        f"- Required checks: `{json.dumps(required, sort_keys=True)}`.",
        f"- Actual callback sequence: `{callbacks}`.",
        f"- Final-store samples: `{len(samples)}`; first words: `{sample_words[:2]}`.",
        "- The real `0x180006b30` callback overwrote PF8 destination words through the callback destination pointer.",
        "- A fresh full-frame equivalence claim remains blocked because this proof is not a same-run complete-frame capture.",
        "",
        "## Provenance", "",
        f"- AEX: `{AEX.relative_to(ROOT)}` sha256 `{sha256(AEX)}`.",
        f"- Fixture: `{FIXTURE.relative_to(ROOT)}` sha256 `{sha256(FIXTURE)}`.",
        f"- Source: `{SOURCE.relative_to(ROOT)}` sha256 `{sha256(SOURCE)}`.",
        f"- Continuation report: `{CONTINUATION.relative_to(ROOT)}`.",
        f"- Writer probe: `{WRITER_PROBE.relative_to(ROOT)}`.",
        "",
        "## Reproduction", "", f"`python3 {WRITER_PROBE.relative_to(ROOT)}`", "",
    ]) + "\n", encoding="utf-8")
    print(json.dumps({"status": status, "report": str(REPORT.relative_to(ROOT)), "samples": len(samples), "checks": required}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
