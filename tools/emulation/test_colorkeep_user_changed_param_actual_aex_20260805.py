#!/usr/bin/env python3
"""USER_CHANGED_PARAM changed-index/extra boundary: actual AEX vs production."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import test_colorkeep_update_params_ui_actual_aex_20260805 as ui

ROOT = Path(__file__).resolve().parents[2]
REPORT = ROOT / "refs/conformance/colorkeep_user_changed_param_actual_aex_20260805.json"
CHANGED_INDICES = (1, 2, 38, 101)


def main() -> int:
    cases = {}
    payload_parts = []
    for count, changed_index in zip(ui.COUNTS, CHANGED_INDICES):
        case = ui.actual(count, command=13, changed_index=changed_index)
        assert case["extra_reads"] == []
        cases[f"count_{count}_changed_{changed_index}"] = case
        payload_parts.append(bytes(disabled for _, disabled in case["updates"]))
    actual_payload = b"".join(payload_parts)
    production_payload = ui.production("PF_Cmd_USER_CHANGED_PARAM")
    assert production_payload == actual_payload
    digest = hashlib.sha256(actual_payload).hexdigest()
    report = {
        "status": "exact",
        "public_entrypoint": "PF_Cmd_USER_CHANGED_PARAM",
        "actual_aex_sha256": ui.AEX_SHA256,
        "actual_exported_entry": f"0x{ui.ENTRY:x}",
        "actual_dispatch_evidence": "PE jump table maps command 13 to 0x180002ada, which calls the shared actual UI callback at 0x180002210.",
        "actual_execution_boundary": "The exported command-13 entry, suite-based enabled-count read, and 100-item UI loop execute under Unicorn. Only nested host UpdateParamUI helper 0x180001ff0 is detoured to record observable calls.",
        "host_extra_boundary": {
            "layout": "PF_UserChangedParamExtra contains PF_ParamIndex param_index at offset 0.",
            "changed_indices": list(CHANGED_INDICES),
            "actual_extra_memory_reads": 0,
            "result": "The actual command-13 path does not read changed-index or any byte of the supplied 16-byte extra fixture; the complete color UI surface is recomputed from enabled count.",
        },
        "production_path": "EffectMain(PF_Cmd_USER_CHANGED_PARAM)->SetColorsEnabled",
        "counts": list(ui.COUNTS),
        "observable_contract": "For every changed index, exactly color parameters 2..101 are updated in order and disabled iff color ordinal >= enabledCount.",
        "cases": cases,
        "payload_format": "400 disabled bytes for paired (count,changed-index) cases (0,1),(1,2),(37,38),(100,101)",
        "actual_payload_sha256": digest,
        "production_payload_sha256": hashlib.sha256(production_payload).hexdigest(),
        "remaining_gaps": [
            "native After Effects visible control redraw",
            "host error propagation from UpdateParamUI failures",
            "malformed enabled-count values outside the public slider range",
        ],
    }
    REPORT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
