#!/usr/bin/env python3
"""Fail-closed audit for the Smoother2 current-AEX 0012 typed return.

This is an evidence comparator. It never edits production or ledger files and
does not treat the local AEX replay as Windows truth.
"""

from __future__ import annotations

import argparse
import json
import tempfile
import zipfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PACKAGE = ROOT / "refs/runtime_trace_packages/olm_smoother2_current_aex_0012_typed_bind_read_20260710.zip"
LOCAL_TYPED = ROOT / "refs/conformance/olmsmoother2_typed_witness_20260710.json"
LOCAL_REPLAY = ROOT / "refs/conformance/olmsmoother2_fullchain_local_diff_20260711.json"
TARGET_CASE = "legacy_case_0012_gamma5_red_blue_current_aex"
TARGET_XY = [91, 841]
TARGET_IDX = 105
TARGET_DESCRIPTOR = [91, 841, 1, 91, 843, 5]
MISSING = object()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def get(data: Any, *keys: str) -> Any:
    for key in keys:
        if not isinstance(data, dict) or key not in data:
            return MISSING
        data = data[key]
    return data


def present(value: Any) -> bool:
    if value is MISSING or value is None:
        return False
    if isinstance(value, str) and not value.strip():
        return False
    if isinstance(value, (list, dict)) and not value:
        return False
    return True


def load_return(path: Path | None) -> tuple[dict[str, Any] | None, str]:
    if path is None:
        return None, "no return supplied"
    if path.is_dir():
        candidates = list(path.rglob("RETURN.json")) + list(path.rglob("RETURN_RUNTIME_TRACE_RESULT.json"))
        if not candidates:
            return None, f"no return JSON under {path.name}"
        return read_json(candidates[0]), f"{path.name}/{candidates[0].name}"
    if path.suffix.lower() == ".json":
        return read_json(path), path.name
    if path.suffix.lower() == ".zip":
        with zipfile.ZipFile(path) as archive:
            names = [n for n in archive.namelist() if n.endswith(("RETURN.json", "RETURN_RUNTIME_TRACE_RESULT.json"))]
            if not names:
                return None, f"no typed return JSON in {path.name}"
            return json.loads(archive.read(names[0]).decode("utf-8-sig")), f"{path.name}:{names[0]}"
    return None, f"unsupported return path: {path.name}"


def local_evidence() -> dict[str, Any]:
    typed = read_json(LOCAL_TYPED)
    row = next(row for row in typed["cases"] if row["name"] == "legacy_current_aex")
    replay = read_json(LOCAL_REPLAY)
    return {"typed": row, "typed_claim_boundary": typed.get("claim_boundary"), "replay": replay}


def check(report: dict[str, Any], label: str, ok: bool, fact: str, inference: str | None = None) -> None:
    report["checks"].append({"label": label, "status": "PASS" if ok else "BLOCKED", "FACT": fact, "INFERENCE": inference})
    if not ok:
        report["blockers"].append(label)


def audit(package: Path, return_path: Path | None) -> dict[str, Any]:
    local = local_evidence()
    with tempfile.TemporaryDirectory(prefix="smoother2_audit_"):
        with zipfile.ZipFile(package) as archive:
            manifest_name = next((n for n in archive.namelist() if n.endswith("/manifest.json")), None)
            manifest = json.loads(archive.read(manifest_name)) if manifest_name else {}
            contract_name = next((n for n in archive.namelist() if n.endswith("/CONTRACT.md")), None)
            contract = archive.read(contract_name).decode("utf-8") if contract_name else ""
    result, return_source = load_return(return_path)
    report: dict[str, Any] = {
        "schema": "olmsmoother2_0012_typed_bind_read_audit_v1",
        "scope": "Smoother2 current-AEX 0012; no production or ledger edits",
        "package": str(package.relative_to(ROOT)) if package.is_relative_to(ROOT) else str(package),
        "return_source": return_source,
        "verdict": "BLOCKED_MISSING_LIVE_TYPED_BINDING",
        "checks": [],
        "blockers": [],
        "facts": [],
        "inferences": [],
    }

    check(report, "request_manifest_scope", manifest.get("request_id") == "olmsmoother2_current_aex_0012_typed_bind_read_20260710" and manifest.get("pixel") == TARGET_XY and manifest.get("idx") == TARGET_IDX, "The pending package declares the expected request id, witness, and idx.")
    check(report, "request_contract_present", bool(contract) and "same-run" in contract and "exact_bind_failure" in contract, "The package carries its same-run and exact-failure contract.")
    if result is None:
        report["blockers"].append("live_typed_return_present")
        report["facts"].append("FACT: No Windows typed return was supplied; the package is a request package only.")
        report["inferences"].append("INFERENCE: No live binding or stage comparison can be promoted from this package.")
    else:
        run = result.get("run", {})
        bind = result.get("bind", {})
        obs = result.get("observations", {})
        status = result.get("status")
        check(report, "answered_status", status == "answered", f"Return status is {status!r}; only 'answered' is accepted.")
        check(report, "same_run_identity", present(run.get("run_id")) and run.get("case_id") == TARGET_CASE and run.get("pixel") == TARGET_XY, "Run identity, case, and pixel are present and target the requested witness.")
        check(report, "live_module_and_hook", present(run.get("module_base")) and present(run.get("module")) and present(bind.get("hook")), "Live module/base and exact hook are returned from the claimed run.")
        check(report, "fifth_argument_config_binding", any(present(bind.get(k)) for k in ("fifth_argument", "config_pointer", "config_object", "binding_expression")) and present(bind.get("pointer_arithmetic")), "The return provides an explicit live c280 fifth-argument/config binding and pointer arithmetic.", "A non-empty expression alone is not accepted as an identical-memory proof unless pointer context is also present.")
        gamma = get(result, "gamma_key_context")
        if gamma is MISSING:
            gamma = get(obs, "gamma_key_context")
        check(report, "gamma_key_context", present(gamma), "Live gamma/key/config context is present in the typed return.", "The local replay explicitly leaves gamma/key/config binding unresolved.")
        required = {
            "idx": obs.get("idx"), "descriptor": obs.get("descriptor"),
            "center_b0": get(obs, "class_bytes", "center_b0"),
            "prev_b0": get(obs, "class_bytes", "prev_b0"),
            "left_b1": get(obs, "class_bytes", "left_b1"), "e170.c": get(obs, "e170", "c"),
            "f270.append": get(obs, "f270", "append"), "f270.source_xy": get(obs, "f270", "source_xy"), "f270.weight": get(obs, "f270", "weight"),
            "e3a0.append": get(obs, "e3a0", "append"), "e3a0.source_xy": get(obs, "e3a0", "source_xy"), "e3a0.weight": get(obs, "e3a0", "weight"),
            "polygon_count": obs.get("polygon_count"), "cce0.output_rgba_float": get(obs, "cce0", "output_rgba_float"), "cce0.output_rgba_hex": get(obs, "cce0", "output_rgba_hex"), "final_writer": obs.get("final_writer"),
        }
        check(report, "typed_stage_completeness", all(present(v) for v in required.values()), "All mandatory producer/class, polygon, cce0, and writer fields are non-null in one return.")
        check(report, "typed_target_identity", required["idx"] == TARGET_IDX and required["descriptor"] == TARGET_DESCRIPTOR, "Returned idx and descriptor match the requested 0012 witness.")
        if all(present(required[k]) for k in ("center_b0", "prev_b0", "left_b1", "e170.c", "f270.append", "e3a0.append")):
            expected = local["typed"]["producer_bytes"] | {"e170_c": local["typed"]["e170"]["c"], "f270_append": local["typed"]["f270"]["append"], "e3a0_append": local["typed"]["e3a0"]["append"]}
            observed = {"center_b0": required["center_b0"], "prev_b0": required["prev_b0"], "left_b1": required["left_b1"], "e170_c": required["e170.c"], "f270_append": required["f270.append"], "e3a0_append": required["e3a0.append"]}
            check(report, "local_typed_witness_comparison", observed == expected, f"Windows typed tuple={observed}; local AEX tuple={expected}.", "Equality would support, but would not by itself prove, live Windows equivalence.")

    replay_rows = local["replay"].get("facts", [])
    replay_ok = bool(replay_rows) and all(row.get("comparison", {}).get("all_replayed_boundaries_equal") is True for row in replay_rows)
    check(report, "local_c280_cce0_replay", replay_ok, "Existing local c280-to-cce0 replay reports all exercised boundaries equal.", "This supports only the exercised local chain; it does not bind live c280's fifth argument or Windows AE state.")
    report["facts"].extend([
        "FACT: Local typed witness records (0,1,0) -> e170 c=2 -> f270/e3a0 append for (91,841).",
        "FACT: Existing local c280->cce0 replay covers c=2 and c=4 fixture rows with all replayed comparisons true.",
        "FACT: The local evidence claim boundary says it is not Windows truth or AE exact evidence.",
    ])
    report["inferences"].extend([
        "INFERENCE: A complete same-run Windows return matching the local tuple would narrow the first divergence upstream of cce0.",
        "INFERENCE: Without live fifth-argument/config and gamma/key context, no c280/cce0 readiness claim is valid.",
    ])
    if not report["blockers"]:
        report["verdict"] = "READY_FOR_TYPED_COMPARISON_ONLY"
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--package", type=Path, default=DEFAULT_PACKAGE)
    parser.add_argument("--return", dest="return_path", type=Path)
    parser.add_argument("--json-output", type=Path)
    args = parser.parse_args()
    report = audit(args.package.resolve(), args.return_path.resolve() if args.return_path else None)
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.json_output:
        args.json_output.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0 if not report["blockers"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
