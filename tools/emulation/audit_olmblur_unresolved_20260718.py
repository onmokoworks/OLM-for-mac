#!/usr/bin/env python3
"""Read-only audit of the remaining OLMBlur exactness boundary."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "mac/OLMBlur/OLMBlur.cpp"
EVIDENCE = {
    "ae_exact_16bpc": ROOT / "refs/conformance/olmblur_16bpc_fixed_worker_mac_ae_exact_20260717.json",
    "fixture_32bpc": ROOT / "refs/conformance/olmblur_32bpc_source_aex_adapter_20260717.md",
    "missing_32bpc_provenance": ROOT / "refs/conformance/olmblur_32bpc_missing_windows_loaded_aex_artifact_20260717.md",
    "readiness_0003_0004": ROOT / "refs/conformance/olmblur_case0003_0004_readiness_audit_20260717.md",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    source = SOURCE.read_text()
    evidence = {name: path.exists() for name, path in EVIDENCE.items()}
    required_dispatch = {
        "pf8_legacy": "render_8bpc_legacy_adapter" in source,
        "pf16_nonlegacy": "render_16bpc_nonlegacy_adapter" in source,
        "pf16_legacy": "render_16bpc_legacy_adapter" in source,
        "pf32_nonlegacy": "render_32bpc_nonlegacy_adapter" in source,
        "pf32_legacy": "render_32bpc_legacy_adapter" in source,
    }
    alpha_preservation = bool(re.search(r"pixel\.alpha\s*=\s*source_row\[x\]\.alpha", source))
    source_hash = sha256(SOURCE)
    ae16 = json.loads(EVIDENCE["ae_exact_16bpc"].read_text()) if EVIDENCE["ae_exact_16bpc"].exists() else {}
    summary16 = ae16.get("summary", {})
    result = {
        "audit": "olmblur_unresolved_exactness_20260718",
        "scope": "Mac-only read-only audit; no source, ledger, AE, or Windows mutation",
        "source": {"path": str(SOURCE.relative_to(ROOT)), "sha256": source_hash},
        "evidence_files_present": evidence,
        "production_dispatch_symbols_present": required_dispatch,
        "alpha_preservation_assignment_present": alpha_preservation,
        "retained_16bpc_ae_exact_slice": summary16,
        "retained_32bpc_fixture_claim": {
            "source_vs_actual_aex_fixtures": "12/12 byte-exact",
            "cross_host_ae_exact": False,
            "reason": "Windows loaded AEX hash/module binding is missing",
        },
        "open_local_boundaries": [
            "32bpc Windows loaded-module provenance is absent; do not promote AE exact",
            "case_0003/case_0004 worker/helper pre-store remains unexecuted at the retained boundary",
        ],
        "highest_value_mac_only_action": {
            "action": "re-run the bounded source-vs-AEX 32bpc adapter and case_0003/0004 readiness audits, then freeze the source pending provenance",
            "why": "It confirms the Mac production dispatch has no untested local path while avoiding an unjustified algorithm change",
            "commands": [
                "python3 tools/emulation/test_olmblur_32bpc_source_aex_adapter_20260717.py",
                "python3 tools/emulation/test_olmblur_case0003_0004_readiness_audit_20260717.py",
            ],
            "not_done_by_this_audit": "Windows loaded-AEX/AE exact comparison",
        },
        "pass": all(required_dispatch.values()) and alpha_preservation and all(evidence.values()),
    }
    out = ROOT / "refs/conformance/olmblur_unresolved_exactness_20260718.json"
    out.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
