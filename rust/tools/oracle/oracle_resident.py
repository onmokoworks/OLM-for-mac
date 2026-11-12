"""Opt-in finite fresh-instance batches. Per-process reruns never erase evidence."""
from __future__ import annotations

import copy
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from PIL import Image

SCHEMA = "aexcompat.independent_case_batch"
MAX_CASES = 128
MAX_MANIFEST_BYTES = 1024 * 1024


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
                      allow_nan=False)


def static_key(directory, manifest, side, request):
    """Conservative refinement of AEXCompat's key for existing oracle requests.

    Whole host context/settings/dependency documents are retained, so equivalent
    alternate encodings may split unnecessarily but incompatible ones never merge.
    Secondary images are keyed by decoded RGBA content, dimensions and slot.
    """
    context = copy.deepcopy(request)
    assignments = context.pop("assignments", [])
    timing = context.get("timing", {})
    timing.pop("frame", None)  # typed-request schema uses frame/fps/duration_frames
    timing.pop("current_time", None)
    if context.get("diagnostics", {}).get("memory_fill") is not None:
        raise ValueError("--resident does not support diagnostics.memory_fill")
    layers = []
    for assignment in assignments:
        if "layer" not in assignment:
            continue
        path = Path(assignment["layer"])
        if not path.is_absolute():
            path = directory / path  # requests/<side>.json -> bundle root, existing oracle contract
        with Image.open(path) as image:
            rgba = image.convert("RGBA")
            layers.append({"slot": assignment["slot"], "size": list(rgba.size),
                           "sha256": hashlib.sha256(rgba.tobytes()).hexdigest(),
                           "attributes": {k: v for k, v in assignment.items() if k != "layer"}})
    with Image.open(directory / "input.png") as image:
        size = image.size
    return canonical({"side": side, "plugin": manifest[side], "route": manifest["route"],
                      "size": size, "request_static": context,
                      "layers": sorted(layers, key=lambda item: item["slot"])})


def batch_manifest(entries, timeout):
    first = entries[0]
    return {"schema": SCHEMA, "schema_version": 1,
            "plugin": first["manifest"][first["side"]]["path"],
            "route": first["manifest"]["route"], "isolation": "fresh_sequence",
            "frame_deadline_ms": max(1, min(600000, math.ceil(timeout * 1000))),
            "cases": [{"id": item["id"], "input": str(item["directory"] / "input.png"),
                       "request": str(item["directory"] / "requests" / (item["side"] + ".json")),
                       "output": str(item["directory"] / (item["side"] + ".png"))}
                      for item in entries]}


def manifest_bytes(entries, timeout):
    # Match write_json, including text-mode newline translation on Windows.
    text = json.dumps(batch_manifest(entries, timeout), indent=2,
                      ensure_ascii=False, allow_nan=False) + "\n"
    return len(text.replace("\n", os.linesep).encode("utf-8"))


def partition(entries, timeout):
    """Stable group order, stable case order; split at both protocol limits."""
    groups = {}
    for item in entries:
        key = static_key(item["directory"], item["manifest"], item["side"], item["request"])
        groups.setdefault(key, []).append(item)
    batches = []
    for group in groups.values():
        chunk = []
        for item in group:
            proposed = chunk + [item]
            if len(proposed) > MAX_CASES or manifest_bytes(proposed, timeout) > MAX_MANIFEST_BYTES:
                if not chunk:
                    raise ValueError("single case exceeds batch manifest size limit")
                batches.append(chunk)
                chunk = [item]
            else:
                chunk = proposed
            if manifest_bytes(chunk, timeout) > MAX_MANIFEST_BYTES:
                raise ValueError("single case exceeds batch manifest size limit")
        if chunk:
            batches.append(chunk)
    return batches


def map_report(report, entries):
    """Validate the complete envelope before accepting any per-case evidence."""
    first = entries[0]
    if not isinstance(report, dict) or report.get("schema") != SCHEMA or report.get("schema_version") != 1:
        raise ValueError("missing/unknown batch report schema")
    if report.get("route") != first["manifest"]["route"] or report.get("isolation") != "fresh_sequence":
        raise ValueError("batch report route/isolation differs")
    rows = report.get("cases")
    if not isinstance(rows, list) or len(rows) != len(entries):
        raise ValueError("missing or extra case results")
    by_id = {}
    for row in rows:
        if not isinstance(row, dict) or not isinstance(row.get("id"), str) or row["id"] in by_id:
            raise ValueError("malformed or duplicate case result ID")
        by_id[row["id"]] = row
    if set(by_id) != {e["id"] for e in entries}:
        raise ValueError("batch result IDs differ from submitted cases")
    clean = report.get("complete") is True and report.get("session_close", {}).get("independent_cases_clean") is True
    for index, entry in enumerate(entries):
        row = by_id[entry["id"]]
        if row.get("case_index") != index:
            raise ValueError("batch case index does not match its ID")
        if row.get("passed") is True:
            if (not clean or row.get("evidence_valid") is not True
                    or row.get("evidence_provisional") is not False or row.get("case_cleanup") is not True):
                raise ValueError("provisional or unclean batch success")
            expected = entry["manifest"][entry["side"]]["sha256"]
            if report.get("plugin_sha256") != expected or row.get("plugin_sha256") != expected:
                raise ValueError("loaded plug-in identity differs from case evidence")
            if row.get("requested_route") != entry["manifest"]["route"]:
                raise ValueError("case route differs")
    return by_id


def execute_batch(index, entries, root, timeout, o):
    directory = root / f"batch-{index:05d}"
    directory.mkdir()
    path = directory / "manifest.json"
    o.write_json(path, batch_manifest(entries, timeout))
    # Per-case watchdog remains timeout; the process budget includes all cases
    # plus one startup/discovery/close allowance. It is never just one case's cap.
    process = o.run_process([entries[0]["manifest"]["harness"]["path"], "--headless",
                             "--render-request-batch", path], timeout * (len(entries) + 1),
                            env_overrides=o.frame_deadline_environment(timeout))
    o.write_json(directory / "batch.process.json", process)
    error = None
    report = {}
    try:
        if process["timeout"] or process["cancelled"] or process["returncode"] not in (0, 1):
            raise ValueError("batch did not finish normally")
        report = json.loads(process["stdout"])
        by_id = map_report(report, entries)
        if process["returncode"] == 0 and report.get("passed") is not True:
            raise ValueError("successful batch exit contradicts report")
    except (ValueError, TypeError) as exc:
        error = str(exc)
        by_id = {}
    mapped = {}
    for entry in entries:
        row = by_id.get(entry["id"], {})
        ok = error is None and row.get("passed") is True and row.get("evidence_valid") is True
        diagnostic = canonical(row)
        result = {"argv": process["argv"], "pid": process["pid"], "returncode": 0 if ok else 1,
                  "batch_returncode": process["returncode"], "timeout": process["timeout"],
                  "cancelled": process["cancelled"], "environment_overrides": process["environment_overrides"],
                  "elapsed_seconds": row.get("wall_ms", 0) / 1000,
                  "batch_elapsed_seconds": process["elapsed_seconds"],
                  "harness_frame_timeout": "frame_deadline" in diagnostic or "frame deadline" in diagnostic,
                  "stdout": json.dumps(row, ensure_ascii=False), "stderr": process["stderr"],
                  "transport": "resident", "batch": str(directory), "batch_case_id": entry["id"],
                  "worker_pid": row.get("worker_pid"), "worker_sha256": row.get("worker_sha256"),
                  "outcome": row.get("outcome", "batch_error"), "ok": ok}
        if error:
            result["batch_error"] = error
        o.write_json(entry["directory"] / (entry["side"] + ".process.json"), result)
        mapped[entry["id"]] = result
    return mapped, {"directory": str(directory), "cases": len(entries),
                    "side": entries[0]["side"], "elapsed_seconds": process["elapsed_seconds"],
                    "returncode": process["returncode"], "error": error}


def compare_case(directory, manifest, processes, o):
    depth = o.ROUTES[manifest["route"]][0]
    outputs, results = {}, {}
    for side in ("reference", "candidate"):
        result = copy.deepcopy(processes[f"{directory.name}/{side}"])
        if result["ok"]:
            try:
                outputs[side] = o.load_output(directory / (side + ".png"), depth)
            except (OSError, ValueError) as exc:
                result["artifact_error"] = str(exc)
                result["ok"] = False
        results[side] = {k: v for k, v in result.items() if k not in ("argv", "stdout", "stderr")}
    row = {"case": manifest["case"]["index"], "route": manifest["route"],
           "directory": directory.name, "processes": results, "transport": "resident"}
    if "reference" not in outputs:
        row["status"] = "reference_timeout" if results["reference"]["timeout"] or results["reference"]["harness_frame_timeout"] else "reference_unrenderable"
    elif "candidate" not in outputs:
        row["status"] = "candidate_failure"
    else:
        row["comparison"] = o.compare_samples(outputs["reference"], outputs["candidate"], depth)
        row["status"] = "exact" if row["comparison"]["exact"] else "mismatched"
    return row


def rerun_authority(directory, manifest, timeout, o):
    target = directory / "per-process-authority"
    target.mkdir()
    for relative, digest in manifest["assets"].items():
        source = (directory / relative).resolve(strict=True)
        if not source.is_relative_to(directory) or o.sha256(source) != digest:
            raise ValueError("authority rerun input/request changed")
        destination = target / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)
    replay_manifest = {**manifest, "transport": "per_process", "resident_source": str(directory)}
    o.write_json(target / "case.json", replay_manifest)
    return o.evaluate_case(target, replay_manifest, timeout)


def render_campaign(args, cases, identities, applicability, debug_routes, summary, o):
    start = time.monotonic()
    out = args.out.resolve()
    root = out / "batches"
    root.mkdir()
    summary.update(transport="resident", batches=[], per_process_reruns=[],
                   isolation="fresh_sequence_with_shared_globals")
    prepared, entries, processes = [], [], {}
    rows = summary["results"]
    o.write_json(out / "summary.json", summary)
    try:
        if debug_routes:
            raise ValueError("--resident does not support forced Classic on SmartFX effects")
        for case in cases:
            for route, reason in applicability.items():
                if reason is not None:
                    continue
                directory, manifest = o.prepare_case(out, case, route, identities, args.perturb_candidate, args.extent)
                manifest["transport"] = "resident"
                o.write_json(directory / "case.json", manifest)
                prepared.append((directory, manifest))
                for side in ("reference", "candidate"):
                    request = json.loads((directory / "requests" / (side + ".json")).read_text(encoding="utf-8"))
                    entries.append({"id": f"{directory.name}/{side}", "directory": directory,
                                    "manifest": manifest, "side": side, "request": request})
        batches = partition(entries, args.timeout)
        with ThreadPoolExecutor(max_workers=args.jobs) as pool:
            futures = {pool.submit(execute_batch, i, batch, root, args.timeout, o): batch
                       for i, batch in enumerate(batches)}
            try:
                for future in as_completed(futures):
                    batch = futures[future]
                    try:
                        mapped, record = future.result()
                        processes.update(mapped)
                        summary["batches"].append(record)
                    except Exception as exc:
                        # Preserve infrastructure failures as failed resident observations.
                        for entry in batch:
                            result = {"ok": False, "timeout": False, "harness_frame_timeout": False,
                                      "returncode": 1, "transport": "resident", "batch_error": repr(exc),
                                      "pid": None, "argv": [], "elapsed_seconds": 0,
                                      "stdout": "", "stderr": repr(exc), "cancelled": False,
                                      "environment_overrides": {}}
                            processes[entry["id"]] = result
                            o.write_json(entry["directory"] / (entry["side"] + ".process.json"), result)
                        summary["batches"].append({"cases": len(batch), "error": repr(exc)})
                    o.write_json(out / "summary.json", summary)
            except KeyboardInterrupt:
                o.CANCELLED.set()
                for future in futures:
                    future.cancel()
                raise
        # All resident workers have exited before authority reruns. This also
        # makes the global --jobs cap apply to reference, candidate and retries.
        for directory, manifest in prepared:
            row = compare_case(directory, manifest, processes, o)
            if row["status"] != "exact":
                try:
                    authority = rerun_authority(directory, manifest, args.timeout, o)
                except Exception as exc:
                    authority = {"case": row["case"], "route": row["route"],
                                 "status": "tool_error", "error": repr(exc)}
                row["per_process_authority"] = authority
                summary["per_process_reruns"].append(authority)
                print(f"resident {directory.name}: {row['status']}; per-process: {authority['status']}", flush=True)
            rows.append(row)
            o.write_json(directory / "diff.json", row)
            summary["routes"] = o.summarize(rows, applicability, debug_routes)
            o.write_json(out / "summary.json", summary)
        summary["complete"] = True
    except KeyboardInterrupt:
        summary.update(cancelled=True, exit_code=130)
        raise
    except Exception as exc:
        summary.update(setup_error=repr(exc), exit_code=2)
        raise
    finally:
        summary["elapsed_render_seconds"] = time.monotonic() - start
        rows.sort(key=lambda r: (r["case"], r["route"]))
        summary["routes"] = o.summarize(rows, applicability, debug_routes)
        summary["per_process_rerun_routes"] = o.summarize(summary["per_process_reruns"], applicability, debug_routes)
        if summary["complete"]:
            resident_code = o.exit_code(summary)
            authority_code = o.exit_code({"routes": summary["per_process_rerun_routes"]})
            summary["exit_code"] = 1 if 1 in (resident_code, authority_code) else max(resident_code, authority_code)
        o.write_json(out / "summary.json", summary)
    o.print_table(summary)
    print(f"summary: {out / 'summary.json'}")
    return summary["exit_code"]
