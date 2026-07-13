#!/usr/bin/env python3
"""Classify the live Windows Mode 3 kernel without image-level inference."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CV455_PYTHON = ROOT / "tools/emulation/.venv-cv455/bin/python"
REQUEST_ID = "olmkirakira_mode3_live_gaussian_20260713"
SCHEMA = "olmkirakira-mode3-live-gaussian-return-v1"
CASE_ID = "final_random10_olm_kira_kira_03"
AEX_SHA256 = "60997c0c52207c15844a46289435231fa6b0a885f63778404e02cea6e03899f7"
AEX_SIZE = 25_781_248
EXPECTED_RVAS = {
    "wrapper": 0x1272EC0,
    "create": 0x1266730,
    "getKernel": 0x12754A0,
    "getKernelReturn": 0x126685C,
}
REQUIRED_TRACE_MARKERS = (
    "KK_RUN_START",
    "KK_MODULE",
    "KK_BREAKPOINTS_READY",
    "KK_WRAPPER",
    "KK_CREATE",
    "KK_KERNEL_ENTRY",
    "KK_KERNEL_RETURN",
)
UNIFORM_WORD = 0x3D430C31


def load_return(path: Path) -> dict:
    if path.suffix.lower() != ".zip":
        return json.loads(path.read_text(encoding="utf-8-sig"))
    with zipfile.ZipFile(path) as archive:
        result_names = {
            "RETURN_RUNTIME_TRACE.json",
            "AE_RUNTIME_TRACE_RESULT.json",
        }
        names = [
            name for name in archive.namelist()
            if name.replace("\\", "/").rsplit("/", 1)[-1] in result_names
        ]
        if len(names) != 1:
            raise ValueError(f"expected one runtime trace result JSON, found {len(names)}")
        return json.loads(archive.read(names[0]).decode("utf-8-sig"))


def opencv_words() -> list[int]:
    code = (
        "import cv2,json,numpy as np;"
        "assert cv2.__version__=='4.5.5';"
        "k=cv2.getGaussianKernel(21,2.5,cv2.CV_32F).reshape(-1);"
        "print(json.dumps([int(x) for x in k.view(np.uint32)]))"
    )
    output = subprocess.check_output([str(CV455_PYTHON), "-c", code], text=True)
    return json.loads(output)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def parse_address(value: object, field: str) -> int:
    require(isinstance(value, str) and bool(value), f"{field} is missing")
    try:
        parsed = int(value, 0)
    except (TypeError, ValueError) as error:
        raise ValueError(f"{field} is not a hexadecimal address: {value!r}") from error
    require(parsed > 0, f"{field} must be nonzero")
    return parsed


def parse_raw_words(raw: object) -> list[int]:
    require(isinstance(raw, list) and len(raw) == 21, "expected exactly 21 raw words")
    words: list[int] = []
    for index, word in enumerate(raw):
        require(isinstance(word, str) and bool(re.fullmatch(r"(?:0x)?[0-9a-fA-F]{8}", word)),
                f"raw word {index} is not one uint32 hex word")
        words.append(int(word.removeprefix("0x").removeprefix("0X"), 16))
    return words


def validate_payload(payload: dict) -> list[int]:
    """Validate the live-process proof contract before classifying coefficients."""
    require(payload.get("schema") == SCHEMA, "return schema mismatch")
    require(payload.get("request_id") == REQUEST_ID, "request_id mismatch")
    require(payload.get("status") == "answered", f"return is not answered: {payload.get('status')}")

    run_id = payload.get("run_id")
    require(isinstance(run_id, str) and bool(run_id.strip()), "top-level run_id is missing")

    preflight = payload.get("preflight") or {}
    require(preflight.get("status") == "ready", "AE JSX preflight was not ready")
    require(isinstance(preflight.get("ae_pid"), int) and preflight["ae_pid"] > 0,
            "AE preflight PID is missing")
    require("AE_JSX_PREFLIGHT_READY" in str(preflight.get("marker", "")),
            "AE JSX preflight marker is missing")

    run = payload.get("run") or {}
    require(run.get("run_id") == run_id, "nested run_id mismatch")
    require(run.get("case_id") == CASE_ID, "case_id mismatch")
    require(run.get("module") == "OLMKiraKira.aex", "module identity mismatch")
    require(str(run.get("aex_sha256", "")).lower() == AEX_SHA256, "AEX SHA256 mismatch")
    require(run.get("aex_size") == AEX_SIZE, "AEX size mismatch")
    module_base = parse_address(run.get("module_base"), "run.module_base")

    binding = payload.get("binding") or {}
    for name, rva in EXPECTED_RVAS.items():
        require(parse_address(binding.get(f"{name}_rva"), f"binding.{name}_rva") == rva,
                f"{name} RVA mismatch")
        require(parse_address(binding.get(name), f"binding.{name}") == module_base + rva,
                f"{name} absolute address does not equal module_base + RVA")

    case = payload.get("case") or {}
    require(case.get("blur_mode_manifest") == 3, "Blur Mode 3 was not bound")
    overrides = case.get("overrides_match_name") or {}
    require(overrides.get("OLM OLM Kira Kira-0003") == 5, "Vertical Length override mismatch")
    for key in ("OLM OLM Kira Kira-0004", "OLM OLM Kira Kira-0005", "OLM OLM Kira Kira-0026"):
        require(overrides.get(key) == 0, f"zero-ray override mismatch: {key}")

    observation = payload.get("observation") or {}
    require(observation.get("raw_bytes") == 84, "raw byte count mismatch")
    first = observation.get("first_getKernel") or {}
    require(first.get("ecx") == 21, "getKernel ecx mismatch")
    require(first.get("r8") == 5, "getKernel r8 type mismatch")
    require(first.get("xmm1") == 2.5, "getKernel sigma mismatch")
    parse_address(first.get("output_mat"), "observation.first_getKernel.output_mat")
    parse_address(observation.get("return_data"), "observation.return_data")

    module_marker = str(observation.get("module_marker", ""))
    require("KK_MODULE" in module_marker and f"run_id={run_id}" in module_marker,
            "hash-pinned module marker is missing or from another run")
    require(f"sha256={AEX_SHA256}" in module_marker.lower(), "module marker SHA256 mismatch")
    require(f"size={AEX_SIZE}" in module_marker, "module marker size mismatch")

    trace = payload.get("trace")
    require(isinstance(trace, str) and bool(trace), "CDB trace is missing")
    trace_run_ids = set(re.findall(r"^KK_\S+.*?\brun_id=([^\s]+)", trace, flags=re.MULTILINE))
    require(trace_run_ids == {run_id}, f"trace does not prove one run identity: {sorted(trace_run_ids)}")
    for marker in REQUIRED_TRACE_MARKERS:
        require(bool(re.search(rf"^{marker}\b", trace, flags=re.MULTILINE)), f"trace marker missing: {marker}")

    return parse_raw_words(observation.get("raw_words_u32"))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("return_path", type=Path)
    parser.add_argument("--output-json", type=Path)
    args = parser.parse_args()
    payload = load_return(args.return_path)
    words = validate_payload(payload)
    gaussian = opencv_words()
    uniform = [UNIFORM_WORD] * 21
    gaussian_mismatches = sum(a != b for a, b in zip(words, gaussian))
    uniform_mismatches = sum(a != b for a, b in zip(words, uniform))
    if gaussian_mismatches == 0:
        classification = "opencv_4_5_5_gaussian_exact"
    elif uniform_mismatches == 0:
        classification = "uniform_21tap_exact"
    else:
        classification = "neither_known_model"
    result = {
        "request_id": REQUEST_ID,
        "evidence_gate": "same-run-hash-pinned-live-module-absolute-rva",
        "run_id": payload["run_id"],
        "classification": classification,
        "word_count": 21,
        "opencv_4_5_5_gaussian_mismatches": gaussian_mismatches,
        "uniform_21tap_mismatches": uniform_mismatches,
        "raw_words_u32": [f"0x{word:08x}" for word in words],
        "opencv_words_u32": [f"0x{word:08x}" for word in gaussian],
    }
    rendered = json.dumps(result, indent=2) + "\n"
    if args.output_json:
        args.output_json.parent.mkdir(parents=True, exist_ok=True)
        args.output_json.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0 if classification != "neither_known_model" else 2


if __name__ == "__main__":
    raise SystemExit(main())
