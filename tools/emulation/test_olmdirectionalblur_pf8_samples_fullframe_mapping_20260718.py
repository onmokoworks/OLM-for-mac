#!/usr/bin/env python3
"""Join the seven actual-AEX PF8 samples to the Mac world/adapter contracts.

This is a bounded provenance proof.  It does not render AE, compare PNGs, or
promote the Mac implementation to AE exactness.
"""

from __future__ import annotations

import hashlib
import json
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
AEX = ROOT / "plugins_2025/OLMDirectionalBlur.aex"
CONTRACT = ROOT / "refs/conformance/olmdirectionalblur_final_pf_output_contract_20260718.json"
NATURAL = ROOT / "refs/conformance/olmdirectionalblur_natural_writer_owner_20260717.json"
WORLD = ROOT / "tools/emulation/test_dblur_world_row_mapping_20260716.py"
ADAPTER = ROOT / "tools/emulation/test_dblur_mac_host_adapter_20260716.py"
REPORT = ROOT / "refs/conformance/olmdirectionalblur_pf8_samples_fullframe_mapping_20260718.json"
NOTE = ROOT / "refs/conformance/olmdirectionalblur_pf8_samples_fullframe_mapping_20260718.md"

WIDTH = HEIGHT = 16
PF8_PIXEL_BYTES = 4
ROW_PADDING = 12
PF_FLOAT_BYTES = 16
WRITER = "0x180006b30"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def run_json(script: Path) -> tuple[dict, str, str, int]:
    proc = subprocess.run(
        [sys.executable, str(script)], cwd=ROOT, capture_output=True, text=True
    )
    parsed = None
    for line in reversed(proc.stdout.splitlines()):
        try:
            parsed = json.loads(line)
            break
        except json.JSONDecodeError:
            continue
    return parsed or {}, proc.stdout[-4000:], proc.stderr[-4000:], proc.returncode


def main() -> int:
    if platform.system() != "Darwin":
        raise SystemExit("BLOCKED_FAIL_CLOSED: this proof is Mac-only")

    contract = load(CONTRACT)
    natural = load(NATURAL)
    world, world_stdout, world_stderr, world_rc = run_json(WORLD)
    adapter, adapter_stdout, adapter_stderr, adapter_rc = run_json(ADAPTER)

    samples = contract.get("observed", {}).get("writer_entry_samples", [])
    sample_checks = []
    for sample in samples:
        x, y = sample["xy"]
        row0 = sample["row0"]
        col0 = sample["col0"]
        stride = sample["stride_floats"]
        float_cell = ((row0 + y) * stride) + col0 + x
        sample_checks.append({
            "xy": [x, y],
            "float_cell_index": sample["float_cell_index"],
            "expected_float_cell_index": float_cell,
            "float_byte_offset": sample["float_byte_offset"],
            "expected_float_byte_offset": float_cell * PF_FLOAT_BYTES,
            "fullframe_pf8_byte_offset": (y * WIDTH + x) * PF8_PIXEL_BYTES,
            "argb8": sample["writer_entry_argb8"],
            "cell_mapping_matches": sample["float_cell_index"] == float_cell,
            "byte_mapping_matches": sample["float_byte_offset"] == float_cell * PF_FLOAT_BYTES,
        })

    natural_area = natural.get("natural_path", {}).get("iterate_area")
    world_area = world.get("iterate_areas")
    world_pass = (
        world.get("status") == "pass"
        and world.get("actual_output_sha256") == world.get("detoured_output_sha256")
        and world_area == [[2, 1, 14, 15], [2, 1, 14, 15]]
    )
    adapter_cases = adapter.get("cases", [])
    adapter_pass = (
        adapter.get("status") == "ok"
        and len(adapter_cases) == 4
        and all(case.get("used_exact") == 1 for case in adapter_cases)
        and all(case.get("pixels_match") is True for case in adapter_cases)
    )
    checks = {
        "contract_pass": contract.get("status") == "pass",
        "actual_aex_writer": contract.get("observed", {}).get("output_callback") == WRITER,
        "seven_samples": len(samples) == 7,
        "natural_fullframe_iterate": natural_area == [0, 0, WIDTH, HEIGHT],
        "sample_cells_map": bool(sample_checks) and all(item["cell_mapping_matches"] for item in sample_checks),
        "sample_bytes_map": bool(sample_checks) and all(item["byte_mapping_matches"] for item in sample_checks),
        "sample_row_contiguous": [item["xy"] for item in sample_checks] == [[x, 0] for x in range(7)],
        "actual_aex_padded_world": world_pass and world_rc == 0,
        "mac_writer_adapter": adapter_pass and adapter_rc == 0,
        "fail_closed": contract.get("fail_closed", {}).get("ae_exact_claim") is False,
    }
    status = "pass" if all(checks.values()) else "blocked"
    report = {
        "schema": 1,
        "kind": "olmdirectionalblur_pf8_samples_fullframe_mapping_20260718",
        "status": status,
        "created_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "scope": "Mac-only actual-AEX PF8 writer samples joined to full-frame Iterate8 coordinates, padded PF world mapping, and the current Mac writer adapter",
        "claim_scope": "The seven actual-AEX PF8 samples have consistent full-frame output coordinates and float-cell provenance; the current Mac adapter preserves the bounded PF8 layout. No AE exact claim.",
        "provenance": {
            "aex": str(AEX.relative_to(ROOT)),
            "aex_sha256": sha256(AEX),
            "contract": str(CONTRACT.relative_to(ROOT)),
            "contract_sha256": sha256(CONTRACT),
            "natural_writer_report": str(NATURAL.relative_to(ROOT)),
            "natural_writer_report_sha256": sha256(NATURAL),
            "world_probe": str(WORLD.relative_to(ROOT)),
            "adapter_probe": str(ADAPTER.relative_to(ROOT)),
        },
        "checks": checks,
        "fullframe": {
            "dimensions": [WIDTH, HEIGHT],
            "iterate_area": natural_area,
            "pf8_rowbytes": WIDTH * PF8_PIXEL_BYTES + ROW_PADDING,
            "pf8_pixel_layout": "A/R/G/B",
            "writer": WRITER,
            "writer_store_order": "A/R/G/B",
        },
        "samples": sample_checks,
        "actual_aex_world_probe": {
            "status": world.get("status"),
            "returncode": world_rc,
            "iterate_areas": world_area,
            "actual_output_sha256": world.get("actual_output_sha256"),
            "detoured_output_sha256": world.get("detoured_output_sha256"),
            "stdout_tail": world_stdout,
            "stderr_tail": world_stderr,
        },
        "mac_adapter_probe": {
            "status": adapter.get("status"),
            "returncode": adapter_rc,
            "full_cases": [case for case in adapter_cases if case.get("roi") == "full"],
            "partial_cases": [case for case in adapter_cases if case.get("roi") == "partial"],
            "stdout_tail": adapter_stdout,
            "stderr_tail": adapter_stderr,
        },
        "boundary": {
            "full_frame_equivalence": False,
            "ae_exact": False,
            "png_tuning": False,
            "next_missing_proof": "same-run Mac host render capture of the complete output frame",
        },
    }
    def portable(value):
        if isinstance(value, dict):
            return {key: portable(item) for key, item in value.items()}
        if isinstance(value, list):
            return [portable(item) for item in value]
        if isinstance(value, str):
            return value.replace(str(ROOT), "<repo>")
        return value

    report = portable(report)
    REPORT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    NOTE.write_text(render_md(report), encoding="utf-8")
    print(json.dumps({"status": status, "report": str(REPORT.relative_to(ROOT)), "checks": checks}))
    return 0 if status == "pass" else 1


def render_md(report: dict) -> str:
    lines = [
        "# OLMDirectionalBlur PF8 Samples to Full-Frame Mapping 20260718",
        "",
        f"- Status: `{report['status']}`.",
        "- Scope: Mac-only actual-AEX bounded proof; no AE exact claim and no PNG tuning.",
        "- Production source changed: `False`.",
        "",
        "## FACT",
        "",
        "- The seven samples from the dated PF8 output contract belong to the natural full `[0,0,16,16]` Iterate8.",
        "- Their coordinates are `(0,0)` through `(6,0)` and map to float cells `(5,5)` through `(5,11)` with `stride_floats=26`.",
        "- Their float byte offsets are computed as `(((row0+y)*stride)+col0+x)*16`; their PF8 destination offsets are `(y*16+x)*4`.",
        "- The actual-AEX padded-world differential passes with `rowbytes=76` and the nonzero `[2,1,14,15]` area; actual and detoured output digests match.",
        "- The source-included Mac adapter probe passes full and partial extent cases with `used_exact=1` and matching PF8 A/R/G/B pixels.",
        "",
        "## Evidence",
        "",
        "| Check | Result |",
        "| --- | --- |",
    ]
    for key, value in report["checks"].items():
        lines.append(f"| `{key}` | `{value}` |")
    lines += [
        "",
        "## Boundary",
        "",
        "- This connects the seven actual-AEX writer samples to coordinate and row/stride contracts. It is not a same-run complete-frame capture.",
        "- `AE exact` remains `False`; broad full-frame comparison and PNG tuning remain out of scope.",
        "",
        "## Reproduction",
        "",
        "`python3 tools/emulation/test_olmdirectionalblur_pf8_samples_fullframe_mapping_20260718.py`",
        "",
    ]
    return "\n".join(lines)


if __name__ == "__main__":
    raise SystemExit(main())
