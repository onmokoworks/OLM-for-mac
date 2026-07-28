#!/usr/bin/env python3
"""Capture the audited Mac OLMDistanceGradation PF16 boundary witnesses."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import re
import signal
import struct
import subprocess
import sys
import time
import uuid
from pathlib import Path
from typing import Any
from collections.abc import Callable

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REQUEST = ROOT / "handoff/ae_pixel_validation_20260618/requests/ae_pixel_bitdepth16_olmdistancegradation_extended_exact_20260625"
SINGLE_CASE = ROOT / "scripts/run_ae_single_case.py"
VALIDATOR = ROOT / "tools/emulation/validate_olmdistancegradation_pf16_boundary_capture_20260728.py"
SCHEMA_ID = "olmdistancegradation_pf16_boundary_capture_20260728/v1"
CANONICAL_REQUEST_MANIFEST_SHA256 = "7c4761b3b4de904c2a8baa8883c964f234943604414d2cd34bab107ccc43cf29"
CANONICAL_REFERENCE_MANIFEST_SHA256 = "c4378358c8b4db2b2d5d12d0bf0b4142f141963538ca5ec4d86a49eeb8b9e71e"
CASE_COORDINATES = {
    "olmdistancegradation_extended__case_0012": (438, 0),
    "olmdistancegradation_extended__case_0014": (448, 0),
    "olmdistancegradation_extended__case_0024": (232, 328),
    "olmdistancegradation_extended__case_0025": (3, 0),
    "olmdistancegradation_extended__case_0026": (907, 222),
    "olmdistancegradation_extended__case_0027": (1234, 443),
}
LAYER_CASES = set(list(CASE_COORDINATES)[:2])


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_manifests(request_dir: Path) -> tuple[Path, Path]:
    request = request_dir / "request_manifest.json"
    reference = request_dir / "reference_manifest.json"
    if sha256(request) != CANONICAL_REQUEST_MANIFEST_SHA256:
        raise ValueError("request_manifest.json is not the hash-pinned authoritative canonical manifest")
    if sha256(reference) != CANONICAL_REFERENCE_MANIFEST_SHA256:
        raise ValueError("reference_manifest.json is not the hash-pinned authoritative canonical manifest")
    request_data = json.loads(request.read_text(encoding="utf-8"))
    reference_data = json.loads(reference.read_text(encoding="utf-8"))
    request_cases = {item["id"]: item for item in request_data.get("cases", [])}
    reference_cases = {item["id"]: item for item in reference_data.get("cases", [])}
    missing = set(CASE_COORDINATES) - request_cases.keys() | (set(CASE_COORDINATES) - reference_cases.keys())
    if missing:
        raise ValueError(f"canonical manifests are missing cases: {sorted(missing)}")
    bpc = reference_data.get("project", {}).get("bits_per_channel")
    if bpc != 16:
        raise ValueError(f"reference manifest is not the canonical 16bpc request: {bpc!r}")
    for case_id in CASE_COORDINATES:
        request_case = request_cases[case_id]
        reference_case = reference_cases[case_id]
        if request_case.get("frame") != reference_case.get("frame"):
            raise ValueError(f"canonical output frame contract drifted for {case_id}")
        if request_case.get("before_effects_frame") != reference_case.get("before_effects_frame"):
            raise ValueError(f"canonical input frame contract drifted for {case_id}")
        if reference_case.get("bits_per_channel") != 16:
            raise ValueError(f"case depth contract drifted for {case_id}")
        if reference_case.get("project_gpu_accel_type", {}).get("current_name") != "SOFTWARE":
            raise ValueError(f"case renderer contract drifted for {case_id}")
        if reference_case.get("requested_effect", {}).get("match_name") != "OLM Distance Gradation":
            raise ValueError(f"case effect identity drifted for {case_id}")
    return request, reference


def parse_marker(path: Path, case_id: str) -> None:
    text = path.read_text(encoding="utf-8", errors="strict")
    required = (f"case_id={case_id}", "pid_host=AfterFX", "effect_loaded=1", "parameters_applied=1")
    if any(token not in text for token in required):
        raise RuntimeError(f"pause marker identity mismatch: {text!r}")


def wait_for_file(path: Path, timeout: float, process: subprocess.Popen[str]) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if path.is_file():
            return
        if process.poll() is not None:
            raise RuntimeError(f"single-case runner exited before pause marker ({process.returncode})")
        time.sleep(0.05)
    raise TimeoutError(f"timed out waiting for pause marker: {path}")


def run_text(args: list[str], timeout: int) -> str:
    result = subprocess.run(args, text=True, capture_output=True, timeout=timeout)
    if result.returncode != 0:
        raise RuntimeError(f"{args[0]} failed ({result.returncode}): {result.stderr.strip()}")
    return result.stdout


def running_ae_pids() -> list[int]:
    result = subprocess.run(["pgrep", "-x", "After Effects"], text=True, capture_output=True, timeout=10)
    if result.returncode not in (0, 1):
        raise RuntimeError(f"cannot inspect running After Effects processes: {result.stderr.strip()}")
    return [int(value) for value in result.stdout.split() if value.isdigit()]


def process_identity(plugin_binary: Path) -> dict[str, Any]:
    pids = running_ae_pids()
    if len(pids) != 1:
        raise RuntimeError(f"expected exactly one After Effects process at pause marker, found {pids}")
    pid = pids[0]
    start_token = " ".join(run_text(["ps", "-p", str(pid), "-o", "lstart="], 10).split())
    executable = Path(run_text(["ps", "-p", str(pid), "-o", "comm="], 10).strip()).resolve()
    if not start_token or not executable.is_file():
        raise RuntimeError("could not bind After Effects start/executable identity")
    vmmap = run_text(["vmmap", str(pid)], 120)
    plugin_path = str(plugin_binary.resolve())
    if not any(re.search(r"\s" + re.escape(plugin_path) + r"$", line) for line in vmmap.splitlines()):
        raise RuntimeError("exact requested OLMDistanceGradation Mach-O is not mapped in paused AE")
    return {
        "platform": "macos",
        "plugin_path": plugin_path,
        "plugin_sha256": sha256(plugin_binary),
        "process_id": pid,
        "process_start_token": start_token,
        "process_executable": str(executable),
        "process_executable_sha256": sha256(executable),
    }


def verify_process_closed(pid: int, timeout: int = 30) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        state = subprocess.run(["ps", "-p", str(pid), "-o", "pid="], text=True, capture_output=True, timeout=5)
        if state.returncode != 0 or not state.stdout.strip():
            return
        time.sleep(0.1)
    raise RuntimeError(f"final shared-JSX cooperative close was not observed for PID {pid}")


def reverify_exact_owned_process(identity: dict[str, Any]) -> bool:
    if identity.get("platform") != "macos":
        raise RuntimeError("owned process platform identity changed; refusing cleanup action")
    pid = identity["process_id"]
    running = running_ae_pids()
    if not running:
        return False
    if running != [pid]:
        raise RuntimeError(
            f"running AE process set is not exactly the owned PID {[pid]}: {running}; refusing any cleanup action"
        )
    start_token = " ".join(run_text(["ps", "-p", str(pid), "-o", "lstart="], 10).split())
    executable = Path(run_text(["ps", "-p", str(pid), "-o", "comm="], 10).strip()).resolve()
    if (
        start_token != identity["process_start_token"]
        or str(executable) != identity["process_executable"]
        or not executable.is_file()
        or sha256(executable) != identity["process_executable_sha256"]
    ):
        raise RuntimeError("owned AE PID was recycled or its start/executable identity changed; refusing fallback signal")
    plugin = Path(identity["plugin_path"])
    if not plugin.is_file() or sha256(plugin) != identity["plugin_sha256"]:
        raise RuntimeError("owned mapped plug-in file identity changed; refusing fallback signal")
    vmmap = run_text(["vmmap", str(pid)], 120)
    if not any(re.search(r"\s" + re.escape(str(plugin.resolve())) + r"$", line) for line in vmmap.splitlines()):
        raise RuntimeError("owned AE no longer maps the exact capture plug-in; refusing fallback signal")
    return True


def close_exact_owned_process(app_name: str, identity: dict[str, Any]) -> None:
    if not reverify_exact_owned_process(identity):
        return
    # Re-run the complete process-set/start/executable/plugin/vmmap check at
    # the last possible point before signaling, closing the PID-reuse window.
    if not reverify_exact_owned_process(identity):
        return
    os.kill(identity["process_id"], signal.SIGTERM)
    verify_process_closed(identity["process_id"])


def parse_log(path: Path, case_id: str, coordinate: tuple[int, int]) -> dict[str, Any]:
    matches = []
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        if (
            row.get("kind") == "olmdg_pf16_shade_boundary_v1"
            and row.get("case_id") == case_id
            and (row.get("x"), row.get("y")) == coordinate
        ):
            matches.append(row)
    if len(matches) != 1:
        raise RuntimeError(f"expected one PF16 shade record for {case_id} {coordinate}, found {len(matches)}")
    return matches[0]


def png_header(path: Path) -> tuple[int, int, int]:
    data = path.read_bytes()[:33]
    if len(data) < 33 or not data.startswith(b"\x89PNG\r\n\x1a\n") or data[12:16] != b"IHDR":
        raise ValueError(f"not a PNG with an IHDR header: {path}")
    width, height, depth = struct.unpack(">IIB", data[16:25])
    return width, height, depth


def read_true16_pixel(path: Path, coordinate: tuple[int, int]) -> dict[str, int]:
    width, height, depth = png_header(path)
    x, y = coordinate
    if depth != 16:
        raise RuntimeError(f"host output is not true16 PNG (IHDR depth={depth}): {path}")
    if not (0 <= x < width and 0 <= y < height):
        raise ValueError(f"coordinate {coordinate} outside {width}x{height}")
    magick = subprocess.run(
        ["magick", str(path), "-depth", "16", "-endian", "MSB", "rgba:-"],
        capture_output=True,
        timeout=180,
    )
    if magick.returncode != 0:
        raise RuntimeError("ImageMagick is required to extract authoritative true16 output")
    offset = (y * width + x) * 8
    r, g, b, a = struct.unpack(">HHHH", magick.stdout[offset : offset + 8])
    return {"a": a, "r": r, "g": g, "b": b}


def typed(value: dict[str, Any]) -> dict[str, Any]:
    return {"value": value["value"], "bits_hex": value["bits"]}


def make_capture(
    case_id: str,
    identity: dict[str, Any],
    row: dict[str, Any],
    artifact: Path | None,
) -> dict[str, Any]:
    coordinate = {"x": row["x"], "y": row["y"]}
    capture: dict[str, Any] = {
        "case_id": case_id,
        "identity": identity,
        "coordinate": coordinate,
        "source_pf16": {"coordinate": coordinate, "argb": row["source"]},
    }
    if case_id in LAYER_CASES:
        if artifact is None:
            raise RuntimeError(f"{case_id} requires a true16 host artifact")
        capture.update(
            {
                "pre_store": {
                    "coordinate": coordinate,
                    "argb": {channel: typed(row["pre_store"][channel]) for channel in ("a", "r", "g", "b")},
                },
                "stored_pf16": {"coordinate": coordinate, "argb": row["stored"]},
                "exported_true16": {
                    "coordinate": coordinate,
                    "argb": read_true16_pixel(artifact, (row["x"], row["y"])),
                    "artifact_path": str(artifact.resolve()),
                    "artifact_sha256": sha256(artifact),
                    "relation_to_stored_pf16": "unverified_structural_only",
                },
            }
        )
    else:
        capture["field"] = {
            "coordinate": coordinate,
            "float_value": row["field"]["value"],
            "float_bits_hex": row["field"]["bits"],
            "derived_pf16_word": row["field"]["derived_pf16_word"],
            "derivation": row["field"]["derivation"],
            "direct_field_staging_word": row["field"]["direct_field_staging_word"],
        }
    return capture


def run_case(
    args: argparse.Namespace,
    case_id: str,
    output_root: Path,
    expected_identity: dict[str, Any] | None,
    keep_open: bool,
    publish_owned_identity: Callable[[dict[str, Any]], None],
) -> tuple[dict[str, Any], dict[str, Any]]:
    x, y = CASE_COORDINATES[case_id]
    case_dir = output_root / case_id
    case_dir.mkdir(parents=True)
    capture_log = case_dir / "pf16_boundary.jsonl"
    ready = case_dir / "ae_ready.marker"
    resume = case_dir / "ae_continue.marker"
    command = [
        sys.executable,
        str(SINGLE_CASE),
        "--request-dir",
        str(args.request_dir),
        "--case-id",
        case_id,
        "--output-dir",
        str(case_dir),
        "--app-name",
        args.app_name,
        "--timeout",
        str(args.timeout),
        "--ae-env",
        "OLM_AE_FORCE_SOFTWARE=1",
        "--ae-env",
        "OLM_AE_PAUSE_BEFORE_RENDER=1",
        "--ae-env",
        f"OLM_AE_PAUSE_TIMEOUT_SECONDS={args.pause_timeout}",
        "--ae-env",
        f"OLM_AE_READY_MARKER={ready}",
        "--ae-env",
        f"OLM_AE_CONTINUE_MARKER={resume}",
        "--ae-env",
        f"OLM_DG_DEBUG_POINTS={x},{y}",
        "--ae-env",
        f"OLM_DG_PF16_BOUNDARY_CAPTURE_PATH={capture_log}",
        "--ae-env",
        f"OLM_DG_PF16_BOUNDARY_CAPTURE_CASE_ID={case_id}",
    ]
    if keep_open:
        command.append("--keep-open")
    process = subprocess.Popen(command, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    bound: dict[str, Any] | None = None
    try:
        wait_for_file(ready, args.pause_timeout, process)
        paused_pids = running_ae_pids()
        if len(paused_pids) != 1:
            raise RuntimeError(f"expected one freshly capture-owned AE process at pause, found {paused_pids}")
        bound = process_identity(args.plugin_binary)
        if expected_identity is not None and bound != expected_identity:
            raise RuntimeError("AE/plugin process identity changed between boundary cases")
        publish_owned_identity(bound)
        parse_marker(ready, case_id)
        resume.write_text("continue\n", encoding="ascii")
        stdout, stderr = process.communicate(timeout=args.timeout + 30)
        if process.returncode:
            raise RuntimeError(f"single-case runner failed ({process.returncode}): {stderr.strip()} {stdout.strip()}")
        if not keep_open:
            verify_process_closed(bound["process_id"])
    except BaseException:
        if not resume.exists():
            # The shared JSX only recognizes marker existence, so this releases
            # its pause cooperatively.  The orchestrator then waits for that
            # invocation and closes the capture AE process without SIGKILL.
            resume.write_text("abort-close\n", encoding="ascii")
        try:
            process.communicate(timeout=args.timeout + 30)
        except subprocess.TimeoutExpired:
            process.terminate()
            process.communicate(timeout=10)
        raise
    result_path = case_dir / "AE_SINGLE_CASE_RESULT.json"
    result = json.loads(result_path.read_text(encoding="utf-8-sig"))
    artifact = Path(result["output_png"]) if result.get("output_png") else None
    row = parse_log(capture_log, case_id, (x, y))
    assert bound is not None
    return bound, make_capture(case_id, {}, row, artifact)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--request-dir", type=Path, default=DEFAULT_REQUEST)
    parser.add_argument("--plugin-binary", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--app-name", default="Adobe After Effects 2026")
    parser.add_argument("--timeout", type=int, default=1200)
    parser.add_argument("--pause-timeout", type=int, default=300)
    parser.add_argument("--dry-run", action="store_true", help="Validate bindings and print commands without launching AE.")
    args = parser.parse_args(argv)
    owned_identity: dict[str, Any] | None = None
    owned_closed = False

    def publish_owned(identity: dict[str, Any]) -> None:
        nonlocal owned_identity
        if owned_identity is not None and identity != owned_identity:
            raise RuntimeError("capture ownership identity changed")
        owned_identity = identity

    try:
        args.request_dir = args.request_dir.resolve()
        args.plugin_binary = args.plugin_binary.resolve()
        args.output_dir = args.output_dir.resolve()
        request_manifest, reference_manifest = canonical_manifests(args.request_dir)
        if args.plugin_binary.name != "OLMDistanceGradation" or not args.plugin_binary.is_file():
            raise ValueError("--plugin-binary must be the OLMDistanceGradation bundle Mach-O")
        if args.dry_run:
            print(json.dumps({
                "status": "dry_run_no_ae_launched",
                "cases": [{"case_id": case, "coordinate": CASE_COORDINATES[case]} for case in CASE_COORDINATES],
                "request_manifest_sha256": sha256(request_manifest),
                "reference_manifest_sha256": sha256(reference_manifest),
                "plugin_path": str(args.plugin_binary),
                "plugin_sha256": sha256(args.plugin_binary),
            }, indent=2))
            return 0
        preexisting_pids = running_ae_pids()
        if preexisting_pids:
            raise RuntimeError(
                f"refusing capture while user After Effects is already running: {preexisting_pids}; "
                "the one-process cleanup contract requires a fresh capture-owned process"
            )
        args.output_dir.mkdir(parents=True, exist_ok=False)
        run_id = f"olmdg-pf16-{dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%SZ')}-{uuid.uuid4().hex[:12]}"
        stable_process: dict[str, Any] | None = None
        captures = []
        case_ids = list(CASE_COORDINATES)
        for index, case_id in enumerate(case_ids):
            bound, capture = run_case(
                args,
                case_id,
                args.output_dir,
                stable_process,
                keep_open=index < len(case_ids) - 1,
                publish_owned_identity=publish_owned,
            )
            stable_process = stable_process or bound
            captures.append(capture)
            if index == len(case_ids) - 1:
                owned_closed = True
        assert stable_process is not None
        identity = {
            "run_id": run_id,
            "case_manifest_sha256": sha256(request_manifest),
            "reference_manifest_sha256": sha256(reference_manifest),
            **stable_process,
        }
        for capture in captures:
            capture["identity"] = identity
        document = {"schema_id": SCHEMA_ID, "identity": identity, "captures": captures}
        evidence = args.output_dir / "olmdistancegradation_pf16_boundary_capture.json"
        evidence.write_text(json.dumps(document, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        validated = subprocess.run(
            [sys.executable, str(VALIDATOR), str(evidence), "--require-all-cases"],
            text=True,
            capture_output=True,
        )
        if validated.returncode:
            raise RuntimeError(f"capture validator rejected evidence: {validated.stderr.strip()}")
        print(validated.stdout.strip())
        print(f"[OK] {evidence}")
        return 0
    except (OSError, ValueError, RuntimeError, TimeoutError, subprocess.SubprocessError, json.JSONDecodeError) as exc:
        print(f"[FAIL_CLOSED] {exc}", file=sys.stderr)
        return 1
    finally:
        if owned_identity is not None and not owned_closed:
            try:
                close_exact_owned_process(args.app_name, owned_identity)
            except (OSError, RuntimeError, subprocess.SubprocessError) as cleanup_error:
                print(f"[FAIL_CLOSED] exact-owned AE cleanup failed: {cleanup_error}", file=sys.stderr)


if __name__ == "__main__":
    raise SystemExit(main())
