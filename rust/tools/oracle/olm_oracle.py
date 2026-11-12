#!/usr/bin/env python3
"""Bit-exact, identity-bound AEXCompat CPU differential runner (not native AE)."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
import os
from pathlib import Path
import random
import signal
import subprocess
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from fractions import Fraction

import numpy as np
from PIL import Image

DEFAULT_HARNESS = Path(r"D:\Projects\01_Project\04_Tools\AEXCompat-wt-main\broker\target\release\aexcompat-harness.exe")
ROUTES = {
    "smart8": (8, "--render-experimental-smart-request"),
    "smart16": (16, "--render-experimental-smart-request-16"),
    "smart32": (32, "--render-experimental-smart-request-32-cpu"),
    "classic8": (8, "--render-experimental-request"),
    "classic16": (16, "--render-experimental-request-16"),
    "classic32": (32, "--render-experimental-request-32"),
}
SIZES = [(1, 1), (3, 7), (97, 61), (256, 144)]
CANCELLED = threading.Event()


def sha256(path):
    with open(path, "rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest()


def write_json(path, value):
    path = Path(path)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")
    temporary.replace(path)


class WindowsJob:
    """Own one suspended child and all descendants; no process-name killing."""
    def __init__(self):
        import ctypes as c
        from ctypes import wintypes as w
        self.c = c
        self.k = c.WinDLL("kernel32", use_last_error=True)
        class Basic(c.Structure):
            _fields_ = [("per_process", c.c_int64), ("per_job", c.c_int64),
                        ("flags", w.DWORD), ("min_ws", c.c_size_t), ("max_ws", c.c_size_t),
                        ("active_limit", w.DWORD), ("affinity", c.c_size_t),
                        ("priority", w.DWORD), ("scheduling", w.DWORD)]
        class Extended(c.Structure):
            _fields_ = [("basic", Basic), ("io", c.c_uint64 * 6),
                        ("process_mem", c.c_size_t), ("job_mem", c.c_size_t),
                        ("peak_process", c.c_size_t), ("peak_job", c.c_size_t)]
        self.k.CreateJobObjectW.argtypes = [c.c_void_p, w.LPCWSTR]
        self.k.CreateJobObjectW.restype = w.HANDLE
        for name, args in {
            "SetInformationJobObject": [w.HANDLE, c.c_int, c.c_void_p, w.DWORD],
            "AssignProcessToJobObject": [w.HANDLE, w.HANDLE],
            "TerminateJobObject": [w.HANDLE, w.UINT],
            "QueryInformationJobObject": [w.HANDLE, c.c_int, c.c_void_p, w.DWORD, c.c_void_p],
            "CloseHandle": [w.HANDLE],
        }.items():
            getattr(self.k, name).argtypes = args
        self.handle = self.k.CreateJobObjectW(None, None)
        if not self.handle:
            raise c.WinError(c.get_last_error())
        limits = Extended()
        limits.basic.flags = 0x2000  # JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
        if not self.k.SetInformationJobObject(self.handle, 9, c.byref(limits), c.sizeof(limits)):
            self.k.CloseHandle(self.handle)
            raise c.WinError(c.get_last_error())

    def attach_resume(self, process):
        if not self.k.AssignProcessToJobObject(self.handle, int(process._handle)):
            raise self.c.WinError(self.c.get_last_error())
        nt = self.c.WinDLL("ntdll")
        nt.NtResumeProcess.argtypes = [self.c.c_void_p]
        if nt.NtResumeProcess(int(process._handle)) != 0:
            raise RuntimeError("could not resume owned process")

    def close(self):
        c = self.c
        # Termination is harmless for an empty job and also collects orphaned descendants.
        try:
            if not self.k.TerminateJobObject(self.handle, 124):
                raise c.WinError(c.get_last_error())
            accounting = c.create_string_buffer(48)
            deadline = time.monotonic() + 10
            while True:
                if not self.k.QueryInformationJobObject(self.handle, 1, accounting, 48, None):
                    raise c.WinError(c.get_last_error())
                active = int.from_bytes(accounting.raw[40:44], "little")
                if active == 0:
                    break
                if time.monotonic() >= deadline:
                    raise RuntimeError("owned job descendants did not exit")
                time.sleep(0.01)
        finally:
            self.k.CloseHandle(self.handle)


def run_process(argv, timeout, env_overrides=None, cwd=None):
    if CANCELLED.is_set():
        raise RuntimeError("oracle run cancelled")
    job = WindowsJob() if os.name == "nt" else None
    p = None
    timed_out = False
    cancelled = False
    started = time.monotonic()
    try:
        p = subprocess.Popen([str(x) for x in argv], stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                             cwd=cwd,
                             creationflags=0x4 | 0x08000000 if job else 0,
                             env={**os.environ, **env_overrides} if env_overrides else None,
                             start_new_session=not bool(job))
        if job:
            job.attach_resume(p)
        deadline = time.monotonic() + timeout
        while True:
            try:
                stdout, stderr = p.communicate(timeout=min(.25, max(.001, deadline - time.monotonic())))
                break
            except subprocess.TimeoutExpired:
                cancelled = CANCELLED.is_set()
                if not cancelled and time.monotonic() < deadline:
                    continue
                timed_out = not cancelled
                if job:
                    job.k.TerminateJobObject(job.handle, 130 if cancelled else 124)
                else:
                    os.killpg(p.pid, signal.SIGKILL)
                stdout, stderr = p.communicate(timeout=10)
                break
        return {"argv": [str(x) for x in argv], "pid": p.pid, "returncode": p.returncode,
                "environment_overrides": env_overrides or {},
                "timeout": timed_out, "cancelled": cancelled, "elapsed_seconds": time.monotonic() - started,
                "stdout": stdout.decode("utf-8", "replace"), "stderr": stderr.decode("utf-8", "replace")}
    finally:
        try:
            if job:
                job.close()
            elif p:
                try:
                    os.killpg(p.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
        finally:
            if p:
                if p.poll() is None:
                    p.kill()
                p.wait(timeout=10)


def harness_json(harness, args, timeout):
    result = run_process([harness, "--headless", *args], timeout)
    if result["timeout"] or result["returncode"]:
        raise RuntimeError(json.dumps(result, ensure_ascii=False))
    return json.loads(result["stdout"])


def inspect(harness, plugin, timeout):
    parameters = harness_json(harness, ["--inspect-experimental", plugin], timeout)
    full = harness_json(harness, ["--inspect-experimental-with-deps", plugin, plugin.parent], timeout)
    diag = full["worker_diagnostics"]
    # Deliberate semantic whitelist: never compare elapsed time, module addresses or binary hashes.
    keys = {"advertised_out_flags", "advertised_out_flags2", "smart_render_advertised",
            "audio_effect_only", "image_render_supported", "reported_num_params",
            "parameter_metadata", "plugin_data", "plugin_kind"}
    keys.update(k for k in diag if "pipl" in k.lower())
    host = {k: diag[k] for k in sorted(keys) if k in diag}
    for key in ("advertised_out_flags", "advertised_out_flags2"):
        if key not in host:
            raise ValueError(f"harness does not expose {key}; cannot infer routes")
    return {"parameters": parameters, "host": host, "diagnostics": full}


def differences(a, b, path=""):
    if isinstance(a, dict) and isinstance(b, dict):
        out = []
        for key in sorted(a.keys() | b.keys()):
            p = f"{path}/{key}"
            if key not in a or key not in b:
                out.append({"path": p, "reference": a.get(key), "candidate": b.get(key), "missing": True})
            else:
                out.extend(differences(a[key], b[key], p))
        return out
    if isinstance(a, list) and isinstance(b, list) and len(a) == len(b):
        return [d for i, (x, y) in enumerate(zip(a, b)) for d in differences(x, y, f"{path}/{i}")]
    return [] if a == b else [{"path": path, "reference": a, "candidate": b}]


def inventory_diff(a, b):
    return differences({k: a[k] for k in ("parameters", "host")},
                       {k: b[k] for k in ("parameters", "host")})


def route_support(inventory, route, force_classic=False):
    host = inventory["host"]
    flags, flags2 = host["advertised_out_flags"], host["advertised_out_flags2"]
    depth = ROUTES[route][0]
    if flags & (1 << 31):
        return "audio-only plug-in"
    if route.startswith("smart") and not flags2 & (1 << 10):
        return "SUPPORTS_SMART_RENDER not declared"
    if route.startswith("classic") and flags2 & (1 << 10) and not force_classic:
        return "SmartFX declared: AE does not dispatch PF_Cmd_RENDER (use --force-classic for non-AE debug)"
    if depth == 16 and not flags & (1 << 25):
        return "DEEP_COLOR_AWARE not declared"
    if depth == 32 and (not flags2 & (1 << 12) or route.startswith("classic")):
        return "32 bpc requires FLOAT_COLOR_AWARE and SmartFX (AE contract)"
    return None


def generate_cases(parameters, count, seed, sizes=SIZES, downsample=("1",)):
    """No worker state or scheduling enters generation. First three are default/min/max."""
    rng = random.Random(seed)
    cases = []
    for index in range(count):
        size = sizes[index % len(sizes)]
        assignments, unassigned, untouched_defaults = [], [], []
        numeric_ranges = {}
        for p in parameters:
            kind, slot = p["kind"], p["slot"]
            a = {"slot": slot}
            lo, hi = p["minimum"], p["maximum"]
            if kind in ("integer", "float"):
                numeric_ranges[str(slot)] = {"minimum": lo, "maximum": hi, "kind": kind}
                v = (p["value"], lo, hi)[index] if index < 3 else rng.choice(
                    [lo, hi, p["value"], rng.randint(math.ceil(lo), math.floor(hi))
                     if kind == "integer" else rng.uniform(lo, hi)])
                # Select first, without changing RNG consumption. A declared
                # default is not an edit, even when it lies outside valid_min/max.
                a["value"] = v
            elif kind == "color":
                a["color"] = (p["color"], [0] * 4, [255] * 4)[index] if index < 3 else [rng.randrange(256) for _ in range(4)]
            elif kind in ("point", "point3d", "angle"):
                n = {"point": 2, "point3d": 3, "angle": 1}[kind]
                # Inventory has no component bounds. Use documented transport range,
                # point percentages of layer extent and +/-360 degree angles, not param ranges.
                bounds = [360] if kind == "angle" else [*size, max(size)]
                a["components"] = p["components"][:n] if index == 0 else [
                    (0 if index == 1 else bounds[j] if index == 2 else rng.uniform(-bounds[j], bounds[j])) for j in range(n)]
            elif kind == "layer":
                a["layer"] = f"layer-{slot}.png"
            else:
                unassigned.append({"slot": slot, "kind": kind, "reason": "retained declared default; no generic authored payload"})
                continue
            field = next(key for key in a if key != "slot")
            default = (p["components"][:len(a[field])] if field == "components"
                       else p.get("layer_path") if field == "layer" else p[field])
            if a[field] == default:
                untouched_defaults.append({**a, "kind": kind, "reason": "untouched default"})
                continue
            if field == "value":
                validate_numeric(a["value"], numeric_ranges[str(slot)], slot)
                if kind == "integer":
                    a["value"] = int(a["value"])
            assignments.append(a)
        cases.append({"index": index, "size": list(size), "input_seed": rng.getrandbits(64),
                      "downsample": str(downsample[index % len(downsample)]),
                      "assignments": assignments, "unassigned": unassigned,
                      "untouched_defaults": untouched_defaults, "numeric_ranges": numeric_ranges})
    return cases


def validate_numeric(value, bounds, slot):
    if (not math.isfinite(value) or not bounds["minimum"] <= value <= bounds["maximum"]
            or (bounds["kind"] == "integer" and value != math.trunc(value))):
        raise ValueError(f"parameter slot {slot} chosen value is outside its declared valid range/type")


def generate_sweep_cases(parameters, seed=0, size=(31, 19), downsample="1"):
    """Default baseline, then one typed parameter at a time at min/max/random.

    Returns ordinary generate_cases-compatible plans; unsupported custom/path
    values stay untouched. No harness calls or mutation of the inventory.
    """
    selected = generate_cases(parameters, 4, seed, [size], [downsample])
    baseline = copy.deepcopy(selected[0])
    # Layer defaults are untouched too; a layer probe supplies only that layer.
    baseline["assignments"] = []
    baseline["sweep"] = {"slot": None, "selection": "defaults"}
    result = [baseline]
    seen = set()
    for p in parameters:
        for label, plan in zip(("default", "minimum", "maximum", "random"), selected):
            a = next((a for a in plan["assignments"] if a["slot"] == p["slot"]), None)
            if a is None:
                continue
            key = json.dumps(a, sort_keys=True)
            if key in seen:
                continue
            seen.add(key)
            case = copy.deepcopy(baseline)
            case["index"] = len(result)
            case["assignments"] = [copy.deepcopy(a)]
            case["untouched_defaults"] = [a for a in case["untouched_defaults"] if a["slot"] != p["slot"]]
            case["sweep"] = {"slot": p["slot"], "selection": label}
            result.append(case)
    return result


def input_pixels(width, height, seed):
    rng = np.random.Generator(np.random.PCG64(seed))
    a = rng.integers(0, 256, (height, width, 4), dtype=np.uint8)
    yy, xx = np.indices((height, width))
    a[..., 0] = np.rint(xx * 255 / max(1, width - 1)).astype(np.uint8)
    a[..., 1] = np.where(xx < width // 2, 17, 239)
    a[..., 3] = np.take(np.array([0, 1, 32, 128, 255], dtype=np.uint8), (xx + yy * width) % 5)
    # Nonblack transparent RGB is intentional; Pillow does no ICC transformation.
    a[..., 2] |= 1
    return a


def make_request(case, perturb=(), extent=None, route="smart8"):
    assignments = copy.deepcopy(case["assignments"])
    for slot, delta in perturb:
        a = next((a for a in assignments if a["slot"] == slot and "value" in a), None)
        if a is None:
            default = next((a for a in case.get("untouched_defaults", [])
                            if a["slot"] == slot and "value" in a), None)
            if default is not None:
                a = {"slot": slot, "value": default["value"]}
                assignments.append(a)
        if a is None:
            raise ValueError(f"perturb slot {slot} is not a numeric assignment")
        a["value"] += delta  # An explicit perturbation is an edit; never clamp it.
        bounds = case.get("numeric_ranges", {}).get(str(slot))
        if bounds is not None:
            validate_numeric(a["value"], bounds, slot)
    factor = Fraction(case["downsample"])
    rational = {"numerator": factor.numerator, "denominator": factor.denominator}
    w, h = case["size"]
    context = {"mask_scene": {"masks": []}, "spatial": {
        "downsample_x": rational, "downsample_y": rational,
        "pixel_aspect_ratio": {"numerator": 1, "denominator": 1},
        "full_resolution_width": math.ceil(w / factor), "full_resolution_height": math.ceil(h / factor)}}
    if extent is not None:
        if not route.startswith("smart"):
            raise ValueError("--extent is a SmartFX output request rectangle; classic extent needs fixture v2")
        context["smart_output_request_rect"] = extent
    return {"schema_version": 1, "assignments": assignments, "host_context": context,
            "render_settings": {"premultiplication": "straight", "color_management": {
                "enabled": False, "working_space": None}, "linear_light": False, "renderer": "software"}}


def load_output(path, depth):
    path = Path(path)
    with Image.open(path) as im:
        w, h = im.size
        if depth == 8:
            if im.mode != "RGBA":
                raise ValueError(f"expected RGBA PNG, got {im.mode}")
            return np.asarray(im).copy()
    suffix, dtype = (".rgba16le", "<u2") if depth == 16 else (".rgba32f-le", "<u4")
    # with_extension in the harness replaces .png, it does not append to it.
    raw = path.with_suffix(suffix).read_bytes()
    if len(raw) != w * h * 4 * (depth // 8):
        raise ValueError("raw sidecar length does not match PNG dimensions/depth")
    return np.frombuffer(raw, dtype=dtype).reshape(h, w, 4)


def compare_samples(reference, candidate, depth):
    if reference.shape != candidate.shape:
        return {"exact": False, "shape_mismatch": [list(reference.shape), list(candidate.shape)],
                "mismatching_pixels": None, "max_abs_diff": None, "first_coordinates": []}
    mask = np.any(reference != candidate, axis=2)
    coords = np.argwhere(mask)
    if depth == 32:
        x, y = reference.view("<f4").astype(np.float64), candidate.view("<f4").astype(np.float64)
    else:
        x, y = reference.astype(np.float64), candidate.astype(np.float64)
    with np.errstate(invalid="ignore", over="ignore"):
        delta = np.abs(x - y)
    finite = delta[np.isfinite(delta)]
    maxdiff = float(finite.max()) if finite.size else 0.0
    return {"exact": not bool(coords.size), "mismatching_pixels": int(mask.sum()),
            "mismatching_samples": int(np.count_nonzero(reference != candidate)),
            "max_abs_diff": "Infinity" if np.isinf(delta).any() else maxdiff,
            "nonfinite_difference_samples": int(np.count_nonzero(~np.isfinite(delta) & (reference != candidate))),
            "first_coordinates": [{"x": int(col), "y": int(row)} for row, col in coords[:8]]}


def frame_deadline_environment(timeout):
    # Installed AEXCompat's supported override range is 1000..600000 ms.
    # The outer process timeout still bounds total launch + render time.
    return {"AEXCOMPAT_FRAME_DEADLINE_MS": str(max(1000, min(600000, math.ceil(timeout * 1000))))}


def evaluate_case(directory, manifest, timeout):
    results, outputs = {}, {}
    route = manifest["route"]
    depth, command = ROUTES[route]
    for side in ("reference", "candidate"):
        output = directory / f"{side}.png"
        result = run_process([manifest["harness"]["path"], "--headless", command,
                              manifest[side]["path"], directory / "input.png", output,
                              directory / "requests" / f"{side}.json"], timeout,
                             env_overrides=frame_deadline_environment(timeout))
        diagnostic_text = result["stderr"] + result["stdout"]
        result["harness_frame_timeout"] = ("frame_deadline" in diagnostic_text and "exceeded" in diagnostic_text)
        write_json(directory / f"{side}.process.json", result)
        if not result["timeout"] and result["returncode"] == 0:
            try:
                outputs[side] = load_output(output, depth)
            except (OSError, ValueError) as exc:
                result["artifact_error"] = str(exc)
        results[side] = {k: v for k, v in result.items() if k not in ("stdout", "stderr", "argv")}
        results[side]["ok"] = side in outputs
    row = {"case": manifest["case"]["index"], "route": route,
           "directory": directory.name, "processes": results}
    if "reference" not in outputs:
        row["status"] = "reference_timeout" if (results["reference"]["timeout"] or results["reference"]["harness_frame_timeout"]) else "reference_unrenderable"
    elif "candidate" not in outputs:
        row["status"] = "candidate_failure"
    else:
        row["comparison"] = compare_samples(outputs["reference"], outputs["candidate"], depth)
        row["status"] = "exact" if row["comparison"]["exact"] else "mismatched"
    write_json(directory / "diff.json", row)
    return row


def run_case(out, case, route, identities, perturb, extent, timeout):
    directory, manifest = prepare_case(out, case, route, identities, perturb, extent)
    return evaluate_case(directory, manifest, timeout)


def prepare_case(out, case, route, identities, perturb=(), extent=None):
    """Prepare the existing replayable bundle without choosing a transport."""
    if CANCELLED.is_set():
        raise RuntimeError("oracle run cancelled")
    directory = out / f"case-{case['index']:04d}-{route}"
    directory.mkdir()
    (directory / "requests").mkdir()
    w, h = case["size"]
    Image.fromarray(input_pixels(w, h, case["input_seed"])).save(directory / "input.png")
    for a in case["assignments"]:
        if "layer" in a:
            Image.fromarray(input_pixels(w, h, case["input_seed"] ^ a["slot"])).save(directory / a["layer"])
    for side in ("reference", "candidate"):
        write_json(directory / "requests" / f"{side}.json",
                   make_request(case, perturb if side == "candidate" else (), extent, route))
    manifest = {**identities, "route": route, "case": case}
    manifest["assets"] = {str(p.relative_to(directory)): sha256(p) for p in sorted(directory.rglob("*")) if p.is_file()}
    write_json(directory / "case.json", manifest)
    return directory, manifest


def summarize(rows, applicability, non_ae_debug_routes=()):
    summary = {}
    for route, reason in applicability.items():
        group = [r for r in rows if r["route"] == route]
        item = {"status": "not_applicable" if reason else "tested", "reason": reason, "cases_run": len(group)}
        item["route_scope"] = "non_ae_debug" if route in non_ae_debug_routes else "ae_dispatch_contract"
        for status in ("exact", "mismatched", "reference_unrenderable", "reference_timeout", "candidate_failure", "tool_error"):
            item[status] = sum(r["status"] == status for r in group)
        item["reference_harness_failures"] = sum(not r.get("processes", {}).get("reference", {"ok": True})["ok"] for r in group)
        item["candidate_harness_failures"] = sum(not r.get("processes", {}).get("candidate", {"ok": True})["ok"] for r in group)
        comps = [r["comparison"] for r in group if "comparison" in r]
        diffs = [c["max_abs_diff"] for c in comps if c["max_abs_diff"] is not None]
        item["max_abs_diff"] = "Infinity" if "Infinity" in diffs else max(diffs, default=0)
        item["mismatching_pixels"] = sum(c["mismatching_pixels"] or 0 for c in comps)
        item["first_coordinates"] = [{"case": r["case"], **p} for r in group for p in r.get("comparison", {}).get("first_coordinates", [])][:8]
        summary[route] = item
    return summary


def exit_code(summary):
    if summary.get("inventory_diff") or any(v["mismatched"] or v["candidate_failure"] for v in summary["routes"].values()):
        return 1
    if any(v["reference_unrenderable"] or v.get("reference_timeout", 0) or v["tool_error"] for v in summary["routes"].values()):
        return 2
    return 0


def print_table(summary):
    print("route       run  exact  mismatch  ref_fail  ref_timeout  cand_fail  max_abs_diff")
    for route, v in summary["routes"].items():
        if v["status"] == "not_applicable":
            print(f"{route:10} not_applicable: {v['reason']}")
        else:
            label = " [non-AE debug]" if v.get("route_scope") == "non_ae_debug" else ""
            print(f"{route:10} {v['cases_run']:4} {v['exact']:6} {v['mismatched']:9} {v['reference_unrenderable']:9} {v.get('reference_timeout', 0):12} {v['candidate_harness_failures']:10}  {v['max_abs_diff']}{label}")


def identity(path):
    path = Path(path).resolve(strict=True)
    return {"path": str(path), "sha256": sha256(path)}


def render(args):
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    identities = {name: identity(getattr(args, name)) for name in ("harness", "reference", "candidate")}
    identities["tool"] = identity(__file__)
    if getattr(args, "resident", False):
        import oracle_resident
        identities["resident_tool"] = identity(oracle_resident.__file__)
    try:
        inv = {side: inspect(args.harness, getattr(args, side), args.timeout) for side in ("reference", "candidate")}
    except Exception as exc:
        write_json(out / "summary.json", {"schema_version": 1, **identities, "seed": args.seed,
                   "cases": args.cases, "complete": False, "setup_error": str(exc), "routes": {}, "exit_code": 2})
        raise
    for side in inv:
        write_json(out / f"{side}.inventory.json", inv[side])
    diff = inventory_diff(inv["reference"], inv["candidate"])
    cases = generate_cases(inv["reference"]["parameters"], args.cases, args.seed, args.sizes, args.downsample)
    write_json(out / "cases.json", cases)
    applicability = {r: route_support(inv["reference"], r, args.force_classic) for r in args.routes}
    debug_routes = [r for r in args.routes if args.force_classic and r.startswith("classic")
                    and applicability[r] is None and route_support(inv["reference"], r) is not None]
    identities["non_ae_debug_routes"] = debug_routes
    summary = {"schema_version": 1, **identities, "seed": args.seed, "cases": args.cases,
               "timeout_seconds": args.timeout, "force_classic": args.force_classic,
               "render_environment_overrides": frame_deadline_environment(args.timeout),
               "jobs": args.jobs, "sizes": args.sizes, "downsample": args.downsample,
               "extent": args.extent, "perturb_candidate": args.perturb_candidate,
               "inventory_diff": diff, "same_binary": identities["reference"]["sha256"] == identities["candidate"]["sha256"],
               "results": [], "routes": {}, "complete": False}
    rows = summary["results"]
    if getattr(args, "resident", False):
        from oracle_resident import render_campaign
        return render_campaign(args, cases, identities, applicability, debug_routes, summary,
                               sys.modules[__name__])
    with ThreadPoolExecutor(max_workers=args.jobs) as pool:
        futures = {pool.submit(run_case, out, case, route, identities, args.perturb_candidate,
                               args.extent, args.timeout): (case, route)
                   for case in cases for route, reason in applicability.items() if reason is None}
        try:
            for future in as_completed(futures):
                case, route = futures[future]
                try:
                    rows.append(future.result())
                except Exception as exc:
                    rows.append({"case": case["index"], "route": route, "status": "tool_error", "error": repr(exc)})
                summary["routes"] = summarize(rows, applicability, debug_routes)
                write_json(out / "summary.json", summary)
                if len(rows) % 20 == 0:
                    print(f"completed {len(rows)}/{len(futures)} route-cases", flush=True)
        except KeyboardInterrupt:
            CANCELLED.set()
            for future in futures:
                future.cancel()
            summary["cancelled"] = True
            summary["exit_code"] = 130
            summary["routes"] = summarize(rows, applicability, debug_routes)
            write_json(out / "summary.json", summary)
            raise
    rows.sort(key=lambda r: (r["case"], r["route"]))
    summary["routes"] = summarize(rows, applicability, debug_routes)
    summary["complete"] = True
    summary["exit_code"] = exit_code(summary)
    write_json(out / "summary.json", summary)
    print_table(summary)
    print(f"summary: {out / 'summary.json'}")
    return summary["exit_code"]


def replay(args):
    source = args.case_dir.resolve(strict=True)
    manifest = json.loads((source / "case.json").read_text(encoding="utf-8"))
    for key in ("harness", "reference", "candidate"):
        if sha256(manifest[key]["path"]) != manifest[key]["sha256"]:
            raise ValueError(f"{key} hash changed; replay refused")
    out = args.out.resolve() if args.out else source / ("replay-" + time.strftime("%Y%m%d-%H%M%S"))
    out.mkdir(parents=True, exist_ok=False)
    import shutil
    for relative, digest in manifest["assets"].items():
        src = (source / relative).resolve(strict=True)
        if not src.is_relative_to(source) or sha256(src) != digest:
            raise ValueError(f"invalid/changed replay asset: {relative}")
        dst = out / relative
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, dst)
    manifest["replayed_by_tool"] = identity(__file__)
    if manifest.get("transport") == "resident":
        manifest["replay_source_transport"] = "resident"
        manifest["transport"] = "per_process"
    write_json(out / "case.json", manifest)
    result = evaluate_case(out, manifest, args.timeout)
    summary = {**manifest, "original_tool": manifest["tool"], "tool": identity(__file__),
               "seed": None, "cases": 1, "results": [result], "complete": True,
               "timeout_seconds": args.timeout,
               "render_environment_overrides": frame_deadline_environment(args.timeout),
               "routes": summarize([result], {manifest["route"]: None}, manifest.get("non_ae_debug_routes", []))}
    summary["exit_code"] = exit_code(summary)
    write_json(out / "summary.json", summary)
    print_table(summary)
    return summary["exit_code"]


def main(argv=None):
    CANCELLED.clear()
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    from oracle_workflows import add_commands, dispatch
    add_commands(sub, DEFAULT_HARNESS)
    for command in ("inventory", "render", "replay"):
        p = sub.add_parser(command)
        p.add_argument("--timeout", type=float, default=60 if command == "inventory" else 120)
        p.add_argument("--out", type=Path)
        if command == "replay":
            p.add_argument("case_dir", type=Path)
            continue
        p.add_argument("--harness", type=Path, default=DEFAULT_HARNESS)
        p.add_argument("--reference", type=Path, required=True)
        p.add_argument("--candidate", type=Path, required=True)
        if command == "render":
            p.add_argument("--resident", action="store_true", help="fresh-instance batches; retain per-process reruns of any mismatch/failure")
            p.add_argument("--force-classic", action="store_true", help="non-AE debug: allow classic8/16 for SmartFX effects")
            p.add_argument("--cases", type=int, default=20)
            p.add_argument("--seed", type=int, default=0)
            p.add_argument("--jobs", type=int, default=min(3, max(1, (os.cpu_count() or 2) // 2)))
            p.add_argument("--routes", default=",".join(ROUTES))
            p.add_argument("--sizes", default="1x1,3x7,97x61,256x144")
            p.add_argument("--downsample", default="1", help="comma-separated ratios: 1,1/2,1/4")
            p.add_argument("--extent", help="SmartFX output rectangle: left,top,right,bottom")
            p.add_argument("--perturb-candidate", action="append", default=[], metavar="SLOT=DELTA")
    args = parser.parse_args(argv)
    try:
        if args.command in ("check", "minimize"):
            return dispatch(args, sys.modules[__name__])
        if args.timeout <= 0:
            raise ValueError("timeout must be positive")
        if args.command == "replay":
            return replay(args)
        for key in ("harness", "reference", "candidate"):
            setattr(args, key, getattr(args, key).resolve(strict=True))
        if args.command == "inventory":
            inventories = {side: inspect(args.harness, getattr(args, side), args.timeout) for side in ("reference", "candidate")}
            diff = inventory_diff(inventories["reference"], inventories["candidate"])
            result = {"schema_version": 1, "identical": not diff, "diff": diff, "inventories": inventories,
                      **{key: identity(getattr(args, key)) for key in ("harness", "reference", "candidate")}, "tool": identity(__file__)}
            if args.out:
                args.out.mkdir(parents=True, exist_ok=False)
                write_json(args.out / "summary.json", result)
            print(json.dumps(diff, indent=2, ensure_ascii=False) if diff else "inventory: identical (all exposed parameter and host fields)")
            return int(bool(diff))
        args.routes = list(dict.fromkeys(args.routes.split(",")))
        if any(r not in ROUTES for r in args.routes):
            raise ValueError("unknown route; use " + ",".join(ROUTES))
        args.sizes = [tuple(map(int, s.lower().replace("×", "x").split("x"))) for s in args.sizes.split(",")]
        if any(len(s) != 2 or min(s) <= 0 for s in args.sizes):
            raise ValueError("sizes must be positive WxH")
        args.downsample = [str(Fraction(s)) for s in args.downsample.split(",")]
        if any(not 0 < Fraction(s) <= 1 for s in args.downsample):
            raise ValueError("downsample must be in (0,1]")
        args.perturb_candidate = [(int(s.split("=")[0]), float(s.split("=")[1])) for s in args.perturb_candidate]
        if any(not math.isfinite(delta) for _, delta in args.perturb_candidate):
            raise ValueError("perturbation must be finite")
        if args.extent:
            args.extent = list(map(int, args.extent.split(",")))
            if len(args.extent) != 4 or any(not r.startswith("smart") for r in args.routes):
                raise ValueError("extent needs four integers and only SmartFX routes")
        if args.cases < 1 or not 1 <= args.jobs <= 3:
            raise ValueError("cases must be positive; jobs must be in 1..3")
        args.out = args.out or Path(__file__).parent / "runs" / time.strftime("%Y%m%d-%H%M%S")
        return render(args)
    except KeyboardInterrupt:
        CANCELLED.set()
        print("oracle cancelled; owned processes stopped", file=sys.stderr)
        return 130
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as exc:
        print(f"oracle error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
