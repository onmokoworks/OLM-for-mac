#!/usr/bin/env python3
"""Evidence-first AEX version triage. Uses the adjacent oracle without modifying it."""
from __future__ import annotations

import argparse
import collections
import concurrent.futures
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import signal
import shutil
import struct
import subprocess
import sys
import time

import pefile
from PIL import Image

HERE = Path(__file__).resolve().parent
GHIDRA_SCRIPTS = HERE / "ghidra"
spec = importlib.util.spec_from_file_location("olm_triage_oracle", HERE.parent / "oracle" / "olm_oracle.py")
oracle = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = oracle
spec.loader.exec_module(oracle)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def decode_pipl(raw):
    """Windows PiPL: WORD resource version, DWORD PiPL version/count, LE FourCCs."""
    if len(raw) < 10:
        raise ValueError("truncated PiPL header")
    resource_version, version, count = struct.unpack_from("<HII", raw)
    if count > 4096:
        raise ValueError("unreasonable PiPL property count")
    offset, properties, fields = 10, [], {}
    for _ in range(count):
        if offset + 16 > len(raw):
            raise ValueError("truncated PiPL property header")
        vendor, key, prop_id, length = struct.unpack_from("<4s4sII", raw, offset)
        offset += 16
        if offset + length > len(raw):
            raise ValueError("truncated PiPL property payload")
        value = raw[offset:offset + length]
        offset += (length + 3) & ~3
        key = key[::-1].decode("ascii", "replace")
        item = {"vendor": vendor[::-1].decode("ascii", "replace"), "key": key,
                "id": prop_id, "raw_hex": value.hex()}
        decoded = None
        if key in ("name", "catg", "eMNA"):
            if not value or value[0] > len(value) - 1:
                raise ValueError(f"invalid PiPL Pascal string {key}")
            decoded = value[1:1 + value[0]].decode("utf-8", "replace")
        elif key in ("ePVR", "eSVR") and len(value) == 4:
            major, minor = struct.unpack("<HH", value)
            decoded = {"major": major, "minor": minor}
        elif key in ("eVER", "eGLO", "eGL2", "aeFL", "eINF") and len(value) in (2, 4):
            decoded = int.from_bytes(value, "little")
        elif key in ("8664", "wx86", "mi64", "ma64"):
            decoded = value.rstrip(b"\0").decode("ascii", "replace")
        if decoded is not None:
            item["decoded"] = decoded
            fields[key] = decoded
        properties.append(item)
    flags, flags2 = fields.get("eGLO"), fields.get("eGL2")
    fields["depths"] = ([8] + ([16] if flags & (1 << 25) else []) +
                        ([32] if flags2 & (1 << 12) else [])) if flags is not None and flags2 is not None else None
    fields["smart_render"] = bool(flags2 & (1 << 10)) if flags2 is not None else None
    if "eVER" in fields:
        v = fields["eVER"]
        fields["effect_version"] = {"major": v >> 19, "minor": (v >> 15) & 15,
                                    "bug": (v >> 11) & 15, "stage": (v >> 9) & 3, "build": v & 511}
    return {"resource_version": resource_version, "version": version, "fields": fields,
            "properties": properties, "trailing_hex": raw[offset:].hex()}


def import_family(text):
    s = text.lower()
    if "ipp" in s:
        return "IPP"
    if "opencv" in s or re.search(r"\bcv::", s):
        return "OpenCV"
    if any(x in s for x in ("ucrt", "api-ms-win-crt", "msvcr", "vcruntime")):
        return "UCRT/CRT"
    return "other"


def pe_inventory(path, out):
    result = {"pipl": [], "imports": [], "sdk_suite_strings": []}
    with pefile.PE(str(path)) as pe:
        for root in getattr(pe, "DIRECTORY_ENTRY_RESOURCE", type("R", (), {"entries": []})()).entries:
            if str(root.name).upper() != "PIPL":
                continue
            for resource in root.directory.entries:
                for language in resource.directory.entries:
                    d = language.data.struct
                    raw = pe.get_data(d.OffsetToData, d.Size)
                    filename = f"pipl-{len(result['pipl']):03d}-{language.id}.bin"
                    (out / filename).write_bytes(raw)
                    row = {"id": resource.id if resource.id is not None else str(resource.name), "language": language.id,
                           "size": len(raw), "sha256": digest(raw), "raw_file": filename}
                    try:
                        row.update(decode_pipl(raw))
                    except ValueError as exc:
                        row["decode_error"] = str(exc)
                    result["pipl"].append(row)
        for kind, directory in (("normal", "DIRECTORY_ENTRY_IMPORT"), ("delay", "DIRECTORY_ENTRY_DELAY_IMPORT")):
            for desc in getattr(pe, directory, []):
                dll = desc.dll.decode("ascii", "replace")
                for symbol in desc.imports:
                    name = symbol.name.decode("ascii", "replace") if symbol.name else f"ordinal:{symbol.ordinal}"
                    result["imports"].append({"dll": dll, "name": name, "kind": kind,
                                               "family": import_family(dll + "!" + name)})
        # Suite acquisition is dynamic via the host, not a PE import. Report string evidence separately.
        for section in pe.sections:
            if section.Characteristics & 0x20000000:
                continue
            for raw in re.findall(rb"[\x20-\x7e]{5,160}", section.get_data()):
                text = raw.decode("ascii")
                if "suite" in text.lower() and any(x in text for x in ("AEGP", "PF ", "AE ", "Adobe", "Suite")):
                    result["sdk_suite_strings"].append(text)
    result["sdk_suite_strings"] = sorted(set(result["sdk_suite_strings"]))
    result["imports"].sort(key=lambda r: (r["dll"], r["name"], r["kind"]))
    return result


def match_parameters(old, new):
    """Exact slot/name/kind, then unique name/kind. Renamed same-slot controls stay unmatched."""
    matches, used, unmatched = [], set(), []
    for p in old:
        candidates = [q for q in new if q["slot"] not in used and q["name"] == p["name"] and q["kind"] == p["kind"]]
        exact = [q for q in candidates if q["slot"] == p["slot"]]
        q = exact[0] if exact else candidates[0] if len(candidates) == 1 else None
        if q is None:
            unmatched.append(p)
        else:
            used.add(q["slot"])
            matches.append({"old_slot": p["slot"], "new_slot": q["slot"], "name": p["name"],
                            "kind": p["kind"], "basis": "slot/name" if exact else "unique name"})
    return {"matched": matches, "removed_or_unmatched": unmatched,
            "added_or_unmatched": [q for q in new if q["slot"] not in used]}


def remap_case(case, mapping, new_parameters):
    mapped = copy.deepcopy(case)
    slots = {m["old_slot"]: m["new_slot"] for m in mapping["matched"]}
    by_slot = {p["slot"]: p for p in new_parameters}
    for a in mapped["assignments"]:
        a["slot"] = slots[a["slot"]]
        if "value" in a:
            p = by_slot[a["slot"]]
            oracle.validate_numeric(a["value"], {"minimum": p["minimum"], "maximum": p["maximum"], "kind": p["kind"]}, a["slot"])
    return mapped


def sensitivity_cases(parameters, seed, size):
    # The same input for default and each one-control edit; default assignments are empty.
    base = oracle.generate_cases([], 1, seed, [size])[0]
    base["label"] = "defaults"
    cases, skipped = [base], []
    for p in parameters:
        probes = oracle.generate_cases([p], 6, seed, [size])
        seen = set()
        assignments = []
        for probe in probes:
            for a in probe["assignments"]:
                key = json.dumps(a, sort_keys=True)
                if key not in seen:
                    seen.add(key)
                    assignments.append(a)
        # Endpoints plus one seeded interior probe, at most three edits per parameter.
        for a in assignments[:3]:
            case = copy.deepcopy(base)
            case.update(index=len(cases), assignments=[a], parameter={"slot": p["slot"], "name": p["name"]},
                        label=f"slot-{p['slot']}")
            cases.append(case)
        if not assignments:
            skipped.append({"slot": p["slot"], "name": p["name"], "kind": p["kind"],
                            "reason": "no generic non-default payload or no variable range"})
    return cases, skipped


def render_pair(out, case, route, identities, mapping, new_parameters, timeout):
    directory = out / f"case-{case['index']:04d}-{route}"
    directory.mkdir()
    (directory / "requests").mkdir()
    try:
        new_case = remap_case(case, mapping, new_parameters)
    except (KeyError, ValueError) as exc:
        row = {"case": case["index"], "route": route, "status": "tool_error", "error": str(exc)}
        oracle.write_json(directory / "diff.json", row)
        return row
    w, h = case["size"]
    Image.fromarray(oracle.input_pixels(w, h, case["input_seed"])).save(directory / "input.png")
    for a in case["assignments"]:
        if "layer" in a:
            Image.fromarray(oracle.input_pixels(w, h, case["input_seed"] ^ a["slot"])).save(directory / a["layer"])
    for side, plan in (("reference", case), ("candidate", new_case)):
        oracle.write_json(directory / "requests" / f"{side}.json", oracle.make_request(plan, route=route))
    manifest = {**identities, "route": route, "case": case, "candidate_case": new_case}
    manifest["assets"] = {str(p.relative_to(directory)): oracle.sha256(p) for p in directory.rglob("*") if p.is_file()}
    oracle.write_json(directory / "case.json", manifest)
    row = oracle.evaluate_case(directory, manifest, timeout)
    row["label"] = case.get("label", "random")
    if "parameter" in case:
        row["parameter"] = case["parameter"]
    return row


def campaign(out, cases, identities, mapping, inventories, args):
    out.mkdir()
    oracle.write_json(out / "cases.json", cases)
    applicability = {r: oracle.route_support(inventories[0], r) or oracle.route_support(inventories[1], r)
                     for r in args.routes}
    rows = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.jobs) as pool:
        futures = [pool.submit(render_pair, out, c, r, identities, mapping, inventories[1]["parameters"], args.timeout)
                   for c in cases for r, reason in applicability.items() if not reason]
        for future in concurrent.futures.as_completed(futures):
            rows.append(future.result())
    rows.sort(key=lambda r: (r["case"], r["route"]))
    result = {"routes": oracle.summarize(rows, applicability), "cases": rows}
    oracle.write_json(out / "summary.json", result)
    return result


def sensitivity_summary(campaign_result):
    rows = campaign_result["cases"]
    defaults = {r["route"]: r for r in rows if r.get("label") == "defaults"}
    result = []
    for slot in sorted({r["parameter"]["slot"] for r in rows if "parameter" in r}):
        group = [r for r in rows if r.get("parameter", {}).get("slot") == slot]
        result.append({**group[0]["parameter"], "cases": len(group),
                       "mismatched": sum(r["status"] == "mismatched" for r in group),
                       "exact": sum(r["status"] == "exact" for r in group),
                       "incomplete": sum(r["status"] not in ("exact", "mismatched") for r in group),
                       "change_exposed_from_equal_defaults": any(r["status"] == "mismatched" and
                           defaults.get(r["route"], {}).get("status") == "exact" for r in group)})
    return result


def headless_path(value):
    if value:
        p = Path(value).resolve()
        if p.is_file():
            return p
        candidate = p / "support" / ("analyzeHeadless.bat" if os.name == "nt" else "analyzeHeadless")
        if candidate.is_file():
            return candidate
        raise FileNotFoundError(f"Ghidra headless not found under {p}")
    for root in (Path("C:/ghidra_12"), Path("C:/ghidra_11")):
        for candidate in sorted(root.glob("*/support/analyzeHeadless.bat"), reverse=True):
            return candidate
    raise FileNotFoundError("pass --ghidra PATH to analyzeHeadless or Ghidra installation")


class OwnedWindowsJob(oracle.WindowsJob):
    """Retain handles to this job's processes until their exit is signalled."""
    def close(self):
        c = self.c
        from ctypes import wintypes as w
        self.k.OpenProcess.argtypes = [w.DWORD, w.BOOL, w.DWORD]
        self.k.OpenProcess.restype = w.HANDLE
        self.k.WaitForSingleObject.argtypes = [w.HANDLE, w.DWORD]
        self.k.WaitForSingleObject.restype = w.DWORD
        handles = []
        self.owned_pids = []
        try:
            try:
                capacity = 64
                while True:
                    buf = c.create_string_buffer(8 + capacity * c.sizeof(c.c_size_t))
                    if self.k.QueryInformationJobObject(self.handle, 3, buf, len(buf), None):
                        break
                    if c.get_last_error() != 234:  # ERROR_MORE_DATA
                        raise c.WinError(c.get_last_error())
                    capacity = max(capacity * 2, int.from_bytes(buf.raw[:4], "little"))
                count = int.from_bytes(buf.raw[4:8], "little")
                for i in range(count):
                    start = 8 + i * c.sizeof(c.c_size_t)
                    pid = int.from_bytes(buf.raw[start:start + c.sizeof(c.c_size_t)], "little")
                    handle = self.k.OpenProcess(0x100000, False, pid)  # SYNCHRONIZE only
                    if handle:
                        handles.append(handle)
                        self.owned_pids.append(pid)
                    elif c.get_last_error() != 87:  # already exited
                        raise c.WinError(c.get_last_error())
            finally:
                super().close()
            deadline = time.monotonic() + 10
            for handle in handles:
                remaining = max(0, int((deadline - time.monotonic()) * 1000))
                if self.k.WaitForSingleObject(handle, remaining) != 0:
                    raise RuntimeError("owned process exit was not signalled after job termination")
        finally:
            for handle in handles:
                self.k.CloseHandle(handle)


def run_headless(command, out, timeout):
    """Keep JVM output on disk: timeout cleanup must not wait on inherited pipe handles."""
    job = OwnedWindowsJob() if os.name == "nt" else None
    process = None
    started = time.monotonic()
    result = {"argv": [str(x) for x in command], "timeout": False, "cancelled": False}
    try:
        with (out / "ghidra.stdout.txt").open("wb") as stdout, (out / "ghidra.stderr.txt").open("wb") as stderr:
            process = subprocess.Popen(result["argv"], stdout=stdout, stderr=stderr,
                                       creationflags=0x4 | 0x08000000 if job else 0,
                                       start_new_session=not bool(job))
            result["pid"] = process.pid
            oracle.write_json(out / "ghidra.launch.json", result)
            if job:
                job.attach_resume(process)
            while True:
                if oracle.CANCELLED.is_set():
                    result["cancelled"] = True
                    break
                remaining = timeout - (time.monotonic() - started)
                if remaining <= 0:
                    result["timeout"] = True
                    break
                try:
                    process.wait(timeout=min(.25, remaining))
                    break
                except subprocess.TimeoutExpired:
                    pass
    finally:
        try:
            if job:
                job.close()  # Terminates only this job and verifies its active-process count is zero.
            elif process:
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
        finally:
            if process:
                if process.poll() is None:
                    process.kill()
                process.wait(timeout=10)
    result.update(returncode=process.returncode, elapsed_seconds=time.monotonic() - started,
                  stdout=(out / "ghidra.stdout.txt").read_text(encoding="utf-8", errors="replace"),
                  stderr=(out / "ghidra.stderr.txt").read_text(encoding="utf-8", errors="replace"),
                  owned_process_cleanup_verified=True, owned_pids_at_cleanup=job.owned_pids if job else [process.pid])
    return result


def binary_analysis(path, out, args):
    exporter_hash = digest((oracle.sha256(GHIDRA_SCRIPTS / "TriageExport.java") + oracle.sha256(GHIDRA_SCRIPTS / "TriageConfigure.java")).encode())
    launcher = headless_path(args.ghidra)
    cache_key = digest((oracle.sha256(path) + exporter_hash + str(launcher)).encode())
    cache = args.cache / f"{cache_key}.json" if args.cache else None
    if cache and cache.exists():
        data = json.loads(cache.read_text(encoding="utf-8"))
        if data.get("analysis_complete"):
            oracle.write_json(out / "functions.json", data)
            return data
    project = out / "ghidra-project"
    project.mkdir()
    scripts = out / "ghidra-scripts"
    scripts.mkdir()
    for name in ("TriageExport.java", "TriageConfigure.java"):
        shutil.copy2(GHIDRA_SCRIPTS / name, scripts / name)
    output = out / "functions.json"
    command = [launcher, project, "triage", "-import", path, "-scriptPath", scripts, "-preScript", "TriageConfigure.java",
               "-postScript", "TriageExport.java", output, "-analysisTimeoutPerFile", str(args.analysis_timeout),
               "-max-cpu", "2", "-log", out / "ghidra.log", "-readOnly", "-deleteProject"]
    try:
        process = run_headless(command, out, args.analysis_timeout + 180)
    except subprocess.SubprocessError as exc:
        # The oracle still closes its private job in finally if pipe draining fails.
        process = {"returncode": None, "timeout": isinstance(exc, subprocess.TimeoutExpired),
                   "error": str(exc), "stdout": "", "stderr": "", "argv": [str(x) for x in command]}
    oracle.write_json(out / "ghidra.process.json", process)
    if not output.exists():
        raise RuntimeError(f"Ghidra failed; see {out / 'ghidra.process.json'}")
    data = json.loads(output.read_text(encoding="utf-8"))
    log = process["stdout"] + process["stderr"]
    data.update(binary=oracle.identity(path), exporter_sha256=exporter_hash,
                analysis_complete=(process["returncode"] == 0 and not process["timeout"] and
                                   not bool(re.search(r"analysis[^\n]*(?:timed?[\s-]*out|timeout[^\n]*(?:exceed|occur))", log, re.I))),
                normalization="instruction bytes with address operand/relocation masks, local targets by instruction index, literal data fingerprints")
    oracle.write_json(output, data)
    if cache and data["analysis_complete"]:
        cache.parent.mkdir(parents=True, exist_ok=True)
        oracle.write_json(cache, data)
    return data


def match_functions(old, new):
    left, right = {f["address"]: f for f in old}, {f["address"]: f for f in new}
    pairs = []

    def unique_match(key, basis, eligible=lambda f: True):
        a, b = collections.defaultdict(list), collections.defaultdict(list)
        for f in left.values():
            if eligible(f):
                a[key(f)].append(f)
        for f in right.values():
            if eligible(f):
                b[key(f)].append(f)
        for k in sorted(a.keys() & b.keys()):
            if len(a[k]) == len(b[k]) == 1:
                x, y = a[k][0], b[k][0]
                pairs.append({"old": x, "new": y, "basis": basis, "changed": x["hash"] != y["hash"]})
                del left[x["address"]]
                del right[y["address"]]

    unique_match(lambda f: f["name"], "unique symbol", lambda f: f.get("named", False))
    unique_match(lambda f: f["hash"], "unique normalized hash")
    # Identical duplicates are interchangeable; retain that ambiguity explicitly.
    by_hash = collections.defaultdict(list)
    for y in right.values():
        by_hash[y["hash"]].append(y)
    for x in list(left.values()):
        y = by_hash[x["hash"]].pop() if by_hash[x["hash"]] else None
        if y:
            pairs.append({"old": x, "new": y, "basis": "equivalent duplicate hash; identity ambiguous", "changed": False})
            del left[x["address"]]
            del right[y["address"]]
    unique_match(lambda f: f["shape_hash"], "unique instruction shape (heuristic)", lambda f: f["instructions"] >= 5)
    changed = [p for p in pairs if p["changed"]]
    for p in changed:
        a, b = p["old"], p["new"]
        p["change_kind"] = ("instructions" if a["code_hash"] != b["code_hash"] else "referenced data") if "code_hash" in a and "code_hash" in b else "code or referenced data"
    return {"matched": pairs, "changed": changed, "added": list(right.values()), "removed": list(left.values()),
            "summary": {"matched": len(pairs), "unchanged": len(pairs) - len(changed), "changed": len(changed),
                        "instruction_changes": sum(p["change_kind"] == "instructions" for p in changed),
                        "referenced_data_changes": sum(p["change_kind"] == "referenced data" for p in changed),
                        "changed_old_bytes": sum(p["old"]["size"] for p in changed),
                        "changed_new_bytes": sum(p["new"]["size"] for p in changed),
                        "added": len(right), "added_bytes": sum(f["size"] for f in right.values()),
                        "removed": len(left), "removed_bytes": sum(f["size"] for f in left.values())}}


def profile_side(path, out, args):
    out.mkdir()
    print(f"Inspecting {path.name}", flush=True)
    inventory = oracle.inspect(args.harness, path, args.timeout)
    oracle.write_json(out / "inventory.json", inventory)
    pe = pe_inventory(path, out)
    oracle.write_json(out / "pe.json", pe)
    print(f"Ghidra: {path.name}", flush=True)
    binary = binary_analysis(path, out, args)
    functions = binary["functions"]
    return {"identity": oracle.identity(path), "inventory": inventory, **pe, "binary": binary,
            "routes": {r: oracle.route_support(inventory, r) for r in oracle.ROUTES},
            "function_count": len(functions), "function_bytes": sum(f["size"] for f in functions),
            "largest_functions": sorted(functions, key=lambda f: f["size"], reverse=True)[:20]}


def profile_timing(side, out, args):
    results = []
    out.mkdir()
    case = oracle.generate_cases([], 1, args.seed, [args.size])[0]
    Image.fromarray(oracle.input_pixels(*args.size, case["input_seed"])).save(out / "input.png")
    for route in args.routes:
        if side["routes"][route]:
            continue
        request = out / f"{route}.request.json"
        oracle.write_json(request, oracle.make_request(case, route=route))
        output = out / f"{route}.png"
        process = oracle.run_process([args.harness, "--headless", oracle.ROUTES[route][1], side["identity"]["path"],
                                      out / "input.png", output, request], args.timeout,
                                     oracle.frame_deadline_environment(args.timeout))
        oracle.write_json(out / f"{route}.process.json", process)
        row = {"route": route, "wall_seconds": process["elapsed_seconds"], "returncode": process["returncode"],
               "timeout": process["timeout"], "status": "incomplete"}
        if not process["timeout"] and process["returncode"] == 0:
            try:
                pixels = oracle.load_output(output, oracle.ROUTES[route][0])
                row.update(status="rendered", output_sha256=digest(pixels.tobytes()))
            except (OSError, ValueError) as exc:
                row["artifact_error"] = str(exc)
        results.append(row)
    return {"size": list(args.size), "assignments": [], "note": "Single cold process wall time including host startup; not kernel-only timing.", "routes": results}


def import_delta(old, new):
    key = lambda r: (r["dll"].lower(), r["name"], r["kind"])
    a, b = {key(r): r for r in old}, {key(r): r for r in new}
    return {"added": [b[k] for k in sorted(b.keys() - a.keys())], "removed": [a[k] for k in sorted(a.keys() - b.keys())]}


def markdown(report):
    lines = ["# OLM triage", "", f"Mode: **{report['mode']}**. AEXCompat CPU observations; not native AE qualification.", ""]
    lines += [f"Evidence: **{'incomplete' if report.get('incomplete') else 'complete for the selected scope'}**.", ""]
    if report["mode"] == "profile":
        p = report["profile"]
        lines += [f"Plug-in: `{p['identity']['path']}`", f"SHA-256: `{p['identity']['sha256']}`", "",
                  f"Parameters: {len(p['inventory']['parameters'])}; functions: {p['function_count']}; function bytes: {p['function_bytes']}.", "",
                  "## PiPL", "", "```json", json.dumps([x.get('fields', {}) for x in p['pipl']], indent=2), "```", "",
                  "## Default render timing", "", p["timing"]["note"], "", "| Route | Status | Seconds |", "|---|---|---:|"]
        lines += [f"| {r['route']} | {r['status']} | {r['wall_seconds']:.3f} |" for r in p["timing"]["routes"]]
        lines += ["", "## Largest functions", "", "| Name | RVA | Bytes |", "|---|---:|---:|"]
        lines += [f"| {f['name'].replace('|', '/')} | {f['rva']:x} | {f['size']} |" for f in p["largest_functions"]]
        lines += ["", "## Imports", "", str(dict(collections.Counter(x["family"] for x in p["imports"]))), "",
                  "SDK suite strings (static presence, not observed acquisition): " + ", ".join(p["sdk_suite_strings"])]
    else:
        s = report["binary_diff"]["summary"]
        lines += [f"Inventory differences: {len(report['inventory_diff'])}; PiPL differences: {len(report['pipl_diff'])}.", "",
                  "## Effort hints", "",
                  f"Changed functions: {s['changed']} ({s['changed_old_bytes']} → {s['changed_new_bytes']} bytes). "
                  f"Added: {s['added']} ({s['added_bytes']} bytes); removed: {s['removed']} ({s['removed_bytes']} bytes); unchanged: {s['unchanged']}.",
                  f"Of those, {s['instruction_changes']} have changed normalized instructions and {s['referenced_data_changes']} have only changed referenced-data fingerprints.",
                  f"New PE imports: {len(report['import_diff']['added'])}; new/unmatched parameters: {len(report['parameter_mapping']['added_or_unmatched'])}.", "",
                  "Counts indicate review scope, not engineering hours. Different compilers can prevent matching. Shape matches are hypotheses.", "",
                  "## Behaviour", "", "| Campaign / route | Exact | Different | Incomplete |", "|---|---:|---:|---:|"]
        for name in ("behaviour", "sensitivity"):
            for route, r in report[name]["routes"].items():
                if r["status"] == "tested":
                    incomplete = sum(r[k] for k in ("reference_unrenderable", "reference_timeout", "candidate_failure", "tool_error"))
                    lines.append(f"| {name} / {route} | {r['exact']} | {r['mismatched']} | {incomplete} |")
        lines += ["", "## Parameter sensitivity", "", "| Parameter | Different / tested | Exposes change from equal defaults |", "|---|---:|---|"]
        lines += [f"| {r['slot']}: {r['name']} | {r['mismatched']} / {r['cases']} | {r['change_exposed_from_equal_defaults']} |" for r in report["parameter_sensitivity"]]
        lines += ["", "These are one-control probes, not causal parameter-to-function attribution. Untested interactions can hide changes.", "",
                  "## Changed functions and callers", "", "| Old → new | Bytes | Change / match basis | Callers (old / new addresses) |", "|---|---:|---|---|"]
        for p in report["binary_diff"]["changed"][:100]:
            lines.append(f"| {p['old']['name']} → {p['new']['name']} | {p['old']['size']} → {p['new']['size']} | {p['change_kind']} / {p['basis']} | {', '.join(p['old']['callers'])} / {', '.join(p['new']['callers'])} |")
        lines += ["", "Full function lists, added/removed functions, import names, raw PiPL files, plans, requests and diagnostics are retained in JSON and side directories."]
        lines += ["", "## Compatibility changes", ""]
        for title, rows in (("Inventory", report["inventory_diff"]), ("PiPL", report["pipl_diff"])):
            lines += [f"### {title}", "", "| Field | Old | New |", "|---|---|---|"]
            for r in rows[:30]:
                values = [json.dumps(r.get(k), ensure_ascii=False).replace("|", "\\|")[:180] for k in ("reference", "candidate")]
                lines.append(f"| {r['path']} | {values[0]} | {values[1]} |")
            if not rows:
                lines.append("| All exposed fields | equal | equal |")
        lines += ["", "### Added imports", ""]
        lines += [f"- `{r['dll']}!{r['name']}` ({r['family']}, {r['kind']})" for r in report["import_diff"]["added"][:40]] or ["None."]
        lines += ["", "### New or unmatched parameters", ""]
        lines += [f"- Slot {p['slot']}: {p['name']} ({p['kind']})" for p in report["parameter_mapping"]["added_or_unmatched"]] or ["None."]
    lines += ["", "## Limits", "", *[f"- {x}" for x in report["limits"]], ""]
    return "\n".join(lines)


def main(argv=None):
    def cancel(signum, frame):
        oracle.CANCELLED.set()
        raise KeyboardInterrupt()
    signal.signal(signal.SIGINT, cancel)
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="mode", required=True)
    for mode in ("diff", "profile"):
        p = sub.add_parser(mode)
        if mode == "diff":
            p.add_argument("--old", type=Path, required=True)
            p.add_argument("--new", type=Path, required=True)
            p.add_argument("--cases", type=int, default=12, help="includes defaults/min/max, then seeded random cases")
        else:
            p.add_argument("--aex", type=Path, required=True)
        p.add_argument("--out", type=Path, required=mode == "diff")
        p.add_argument("--harness", type=Path, default=oracle.DEFAULT_HARNESS)
        p.add_argument("--ghidra", help="Ghidra installation or headless launcher")
        p.add_argument("--cache", type=Path, help="optional content-addressed Ghidra export cache")
        p.add_argument("--jobs", type=int, choices=(1, 2, 3), default=2)
        p.add_argument("--timeout", type=float, default=120)
        p.add_argument("--analysis-timeout", type=int, default=300)
        p.add_argument("--seed", type=int, default=20261112)
        p.add_argument("--size", default="31x19")
        p.add_argument("--routes", default=",".join(oracle.ROUTES))
    args = parser.parse_args(argv)
    args.routes = args.routes.split(",")
    if any(r not in oracle.ROUTES for r in args.routes):
        parser.error("unknown route")
    try:
        args.size = tuple(int(x) for x in args.size.split("x"))
        if len(args.size) != 2 or min(args.size) < 1 or max(args.size) > 4096:
            raise ValueError()
    except ValueError:
        parser.error("--size must be WIDTHxHEIGHT with dimensions 1..4096")
    if args.timeout <= 0 or args.analysis_timeout <= 0 or getattr(args, "cases", 1) < 1:
        parser.error("timeouts and cases must be positive")
    args.harness = args.harness.resolve()
    if args.cache:
        args.cache = args.cache.resolve()
    args.out = (args.out or HERE / "runs" / f"profile-{args.aex.stem}-{time.time_ns()}").resolve()
    args.out.mkdir(parents=True, exist_ok=False)
    report = {"schema_version": 1, "mode": args.mode, "harness": oracle.identity(args.harness),
              "tool": oracle.identity(Path(__file__)), "oracle": oracle.identity(Path(oracle.__file__)),
              "settings": {k: str(v) if isinstance(v, Path) else v for k, v in vars(args).items()},
              "limits": ["Static function boundaries and shape matches depend on Ghidra analysis; no semantic equivalence proof.",
                         "Indirect callers, runtime suite acquisition and statically linked library provenance are not established.",
                         "Normalized code hashes ignore function-target identity and pointer addresses; call graph and literal data are separate evidence. Mutable data and untyped pointer tables can cause false changes.",
                         "Bounded PNG-derived CPU renders do not cover HDR, GPU, arbitrary payload edits, temporal sequences, native AE or exhaustive combinations."]}
    if args.mode == "profile":
        p = profile_side(args.aex.resolve(), args.out / "profile", args)
        p["timing"] = profile_timing(p, args.out / "timing", args)
        report["profile"] = p
        report["incomplete"] = (not p["binary"]["analysis_complete"] or not p["pipl"] or
                                any("decode_error" in x for x in p["pipl"]) or
                                not p["timing"]["routes"] or any(r["status"] != "rendered" for r in p["timing"]["routes"]))
    else:
        old = profile_side(args.old.resolve(), args.out / "old", args)
        new = profile_side(args.new.resolve(), args.out / "new", args)
        report.update(old=old, new=new, inventory_diff=oracle.inventory_diff(old["inventory"], new["inventory"]),
                      pipl_diff=oracle.differences(old["pipl"], new["pipl"]),
                      parameter_mapping=match_parameters(old["inventory"]["parameters"], new["inventory"]["parameters"]),
                      binary_diff=match_functions(old["binary"]["functions"], new["binary"]["functions"]),
                      import_diff=import_delta(old["imports"], new["imports"]),
                      sdk_suite_string_diff={"added": sorted(set(new["sdk_suite_strings"]) - set(old["sdk_suite_strings"])),
                                             "removed": sorted(set(old["sdk_suite_strings"]) - set(new["sdk_suite_strings"]))})
        mapping = report["parameter_mapping"]
        common = {m["old_slot"] for m in mapping["matched"]}
        params = [p for p in old["inventory"]["parameters"] if p["slot"] in common]
        identities = {"reference": old["identity"], "candidate": new["identity"], "harness": report["harness"]}
        cases = oracle.generate_cases(params, args.cases, args.seed, [args.size])
        print(f"Rendering {len(cases)} behavioural cases and one-control probes", flush=True)
        report["behaviour"] = campaign(args.out / "behaviour", cases, identities, mapping, [old["inventory"], new["inventory"]], args)
        probes, skipped = sensitivity_cases(params, args.seed, args.size)
        report["sensitivity"] = campaign(args.out / "sensitivity", probes, identities, mapping, [old["inventory"], new["inventory"]], args)
        report["sensitivity"]["skipped_parameters"] = skipped
        report["sensitivity"]["unmatched_parameters_not_probed"] = {
            "old": mapping["removed_or_unmatched"], "new": mapping["added_or_unmatched"]}
        report["parameter_sensitivity"] = sensitivity_summary(report["sensitivity"])
        report["incomplete"] = (any(not p["binary"]["analysis_complete"] or not p["pipl"] or any("decode_error" in x for x in p["pipl"]) for p in (old, new)) or
                                any(not report[k]["cases"] or any(r["status"] not in ("exact", "mismatched") for r in report[k]["cases"]) for k in ("behaviour", "sensitivity")))
    oracle.write_json(args.out / "triage.json", report)
    (args.out / "triage.md").write_text(markdown(report), encoding="utf-8")
    print(args.out / "triage.md", flush=True)
    # A triage diff is expected to find changes; 0 = complete report, 2 = incomplete evidence.
    return 2 if report["incomplete"] else 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        oracle.CANCELLED.set()
        raise SystemExit(130)
    except (OSError, ValueError, RuntimeError) as exc:
        print(f"triage: {exc}", file=sys.stderr)
        raise SystemExit(2)
