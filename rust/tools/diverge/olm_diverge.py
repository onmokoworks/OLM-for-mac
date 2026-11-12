#!/usr/bin/env python3
"""Bit-exact first-divergence localization using hash-bound native stage maps."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
from pathlib import Path
import struct
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "witness"))
import witness  # public run/normalize/sha256 APIs; no native load in Python

TYPES = {"u8": "B", "i8": "b", "u16": "H", "i16": "h", "u32": "I",
         "i32": "i", "u64": "Q", "i64": "q", "f32": "f", "f64": "d"}


def write_json(path, value):
    Path(path).write_text(json.dumps(value, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def digest(data):
    return hashlib.sha256(data).hexdigest()


def export_rva(module, name):
    # Reading the PE export table does not load or execute the DLL.
    import pefile
    with pefile.PE(str(module), fast_load=True) as pe:
        pe.parse_data_directories(directories=[pefile.DIRECTORY_ENTRY["IMAGE_DIRECTORY_ENTRY_EXPORT"]])
        found = [s for s in getattr(pe, "DIRECTORY_ENTRY_EXPORT", ()).symbols
                 if s.name == name.encode("ascii")] if hasattr(pe, "DIRECTORY_ENTRY_EXPORT") else []
        if len(found) != 1 or found[0].forwarder:
            raise ValueError(f"missing/nonlocal diagnostic export {name} in {module}; enable stage-dump")
        return found[0].address


def word_value(raw, dtype):
    v = struct.unpack("<" + TYPES[dtype], raw)[0]
    return repr(v) if isinstance(v, float) and not math.isfinite(v) else v


def compare_bytes(reference, candidate, dtype, shape):
    if dtype not in TYPES or not shape or any(type(x) is not int or x < 1 for x in shape):
        raise ValueError("invalid element type or positive shape")
    width = struct.calcsize(TYPES[dtype])
    count = math.prod(shape)
    if len(reference) != count * width or len(candidate) != count * width:
        raise ValueError("missing/truncated/oversized stage output")
    different = 0
    first = None
    for i in range(count):
        a, b = reference[i * width:(i + 1) * width], candidate[i * width:(i + 1) * width]
        if a == b:
            continue
        different += 1
        if first is None:
            coordinate, remaining = [], i
            for dimension in reversed(shape):
                coordinate.insert(0, remaining % dimension)
                remaining //= dimension
            first = {"element": i, "coordinate": coordinate, "byte_offset": i * width,
                     "reference": {"bits": f"0x{int.from_bytes(a, 'little'):0{width*2}x}",
                                   "value": word_value(a, dtype)},
                     "candidate": {"bits": f"0x{int.from_bytes(b, 'little'):0{width*2}x}",
                                   "value": word_value(b, dtype)}}
    return {"status": "different" if different else "exact", "elements": count,
            "different_elements": different, "first_difference": first,
            "reference_sha256": digest(reference), "candidate_sha256": digest(candidate)}


def prepare(case, base):
    case = copy.deepcopy(case)
    if case.get("schema_version") != 1 or not case.get("scope") or not case.get("stages"):
        raise ValueError("requires schema_version=1, explicit scope, ordered stages")
    ids = [s["id"] for s in case["stages"]]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate stage ids")
    for side in ("reference", "candidate"):
        binding = case[side]
        spec = binding["witness"]
        module = Path(spec["module"])
        if not module.is_absolute():
            module = base / module
        module = module.resolve(strict=True)
        if witness.sha256(module) != binding["sha256"]:
            raise ValueError(f"{side} binary identity changed: {module}")
        spec["module"] = str(module)
        for call in spec["calls"]:
            if "export" in call:
                if "rva" in call:
                    raise ValueError("call must use export or rva, not both")
                call["rva"] = hex(export_rva(module, call.pop("export")))
        binding["witness"] = witness.normalize(spec, base)
    previous = {"reference": -1, "candidate": -1}
    for stage in case["stages"]:
        if not stage.get("grounding"):
            raise ValueError("stage needs source/signature grounding")
        if stage["dtype"] not in TYPES or not stage["shape"] or any(
                type(n) is not int or n <= 0 for n in stage["shape"]):
            raise ValueError("invalid stage type/shape")
        length = math.prod(stage["shape"]) * struct.calcsize(TYPES[stage["dtype"]])
        for side in ("reference", "candidate"):
            selection = stage[side]
            spec = case[side]["witness"]
            index = selection["call"]
            if type(index) is not int or not 0 <= index < len(spec["calls"]):
                raise ValueError("stage selects nonexistent call")
            if index < previous[side]:
                raise ValueError("stage order runs backwards through witness calls")
            previous[side] = index
            offset = selection.get("offset", 0)
            size = spec["buffers"][selection["buffer"]]["size"]
            if type(offset) is not int or offset < 0 or offset + length > size:
                raise ValueError("stage selection outside buffer")
    return case


def select_bytes(stage, side, result, directory):
    selection = stage[side]
    name = result["calls"][selection["call"]]["buffers"][selection["buffer"]]
    path = (directory / name).resolve()
    if path.parent != directory.resolve():
        raise ValueError("worker output path escapes run directory")
    raw = path.read_bytes()
    length = math.prod(stage["shape"]) * struct.calcsize(TYPES[stage["dtype"]])
    start = selection.get("offset", 0)
    if len(raw) < start + length:
        raise ValueError("truncated worker output")
    return raw[start:start + length]


def one_call_spec(spec, call_index, result, directory):
    """Freeze pre-call state, retain only the argument/relocation buffer closure.

    Worker addresses in struct snapshots are overwritten by retained relocations.
    Only maps declaring stateless calls are eligible: module globals/heap objects
    cannot be reconstructed from a buffer dump.
    """
    spec = copy.deepcopy(spec)
    call = spec["calls"][call_index]
    wanted = {a["buffer"] for a in call["args"] if "buffer" in a}
    pending = list(wanted)
    while pending:
        for pointer in spec["buffers"][pending.pop()].get("pointers", []):
            name = pointer["buffer"]
            if name not in wanted:
                wanted.add(name)
                pending.append(name)
    spec["buffers"] = {name: value for name, value in spec["buffers"].items() if name in wanted}
    for name, buf in spec["buffers"].items():
        if call_index:
            raw = (directory / result["calls"][call_index - 1]["buffers"][name]).read_bytes()
        elif "file" in buf:
            raw = Path(buf["file"]).read_bytes()
        else:
            raw = bytes.fromhex(buf.get("hex", ""))
        raw += bytes([buf.get("fill", 0)]) * (buf["size"] - len(raw))
        raw = bytearray(raw)
        for pointer in buf.get("pointers", []):
            raw[pointer["offset"]:pointer["offset"] + 8] = b"\0" * 8
        buf.pop("file", None)
        buf["hex"] = raw.hex()
    spec["calls"] = [call]
    return spec


def make_reproducer(case, stage, results, out):
    if not case.get("stateless_calls", False):
        return None
    repro = {"schema_version": 1, "scope": "single native stage call: " + stage["id"],
             "stateless_calls": True, "stages": [copy.deepcopy(stage)],
             "minimality": "one call per side; transitive argument/relocation buffer closure; not pixel-minimal"}
    for side in ("reference", "candidate"):
        repro[side] = {"sha256": case[side]["sha256"], "witness": one_call_spec(
            case[side]["witness"], stage[side]["call"], results[side], out / side)}
        repro["stages"][0][side]["call"] = 0
        if "expected_fma" in case[side]:
            repro[side]["expected_fma"] = case[side]["expected_fma"]
        status = case[side].get("return_bits", {}).get(str(stage[side]["call"]))
        if status is not None:
            repro[side]["return_bits"] = {"0": status}
    write_json(out / "reproducer.json", repro)
    return "reproducer.json"


def run(case, out, *, base=None, host=None, timeout=30, reproduce=True):
    base = Path(base or Path.cwd()).resolve()
    case = prepare(case, base)
    out = Path(out).resolve()
    out.mkdir(parents=True, exist_ok=False)
    write_json(out / "case.json", case)
    report = {"schema_version": 1, "scope": case["scope"],
              "classification": "incomplete", "first_divergent_stage": None, "stages": [],
              "case_sha256": witness.sha256(out / "case.json"), "processes": {},
              "claim": "earliest difference among ordered mapped stages only"}
    results = {}
    try:
        for side in ("reference", "candidate"):
            manifest = witness.run(case[side]["witness"], out / side, host=host, timeout=timeout)
            report["processes"][side] = manifest
            if manifest["classification"] != "success" or not manifest["process"]["cleanup_verified"]:
                report["error"] = f"{side}: {manifest['classification']}"
                return report
            result = load_json(out / side / "result.json")
            results[side] = result
            calls = case[side]["witness"]["calls"]
            if len(result["calls"]) != len(calls):
                raise ValueError("missing call result")
            expected_fma = case[side].get("expected_fma")
            if expected_fma is not None and result["fma"]["effective"] != expected_fma:
                raise ValueError(f"{side} FMA profile mismatch")
            for index, expected in case[side].get("return_bits", {}).items():
                if result["calls"][int(index)]["return"]["bits_le"] != expected:
                    raise ValueError(f"{side} call {index} diagnostic returned an error")
        report["controls"] = []
        for control in case.get("controls", []):
            side, index = control["side"], control["call"]
            files = results[side]["calls"][index]["buffers"]
            left = (out / side / files[control["left"]]).read_bytes()
            right = (out / side / files[control["right"]]).read_bytes()
            report["controls"].append({**control, "exact": left == right,
                                       "left_sha256": digest(left), "right_sha256": digest(right)})
            if left != right:
                raise ValueError("native decomposed/full-pipeline control failed; map is not equivalent")
        for stage in case["stages"]:
            comparison = compare_bytes(*(select_bytes(stage, side, results[side], out / side)
                                         for side in ("reference", "candidate")), stage["dtype"], stage["shape"])
            comparison.update(id=stage["id"], grounding=stage["grounding"])
            report["stages"].append(comparison)
            if comparison["status"] == "different" and report["first_divergent_stage"] is None:
                report["first_divergent_stage"] = stage["id"]
                if reproduce:
                    report["reproducer"] = make_reproducer(case, stage, results, out)
        report["classification"] = "divergent" if report["first_divergent_stage"] else "exact"
        # A reproducer is evidence only after it independently reproduces the same bits.
        if reproduce and report.get("reproducer"):
            replay = run(load_json(out / report["reproducer"]), out / "reproducer-check",
                         host=host, timeout=timeout, reproduce=False)
            first = next(s for s in report["stages"] if s["id"] == report["first_divergent_stage"])
            verified = (replay["classification"] == "divergent" and
                        replay["stages"][0]["reference_sha256"] == first["reference_sha256"] and
                        replay["stages"][0]["candidate_sha256"] == first["candidate_sha256"])
            report["reproducer_verified"] = verified
            if not verified:
                report["classification"] = "incomplete"
                report["error"] = "single-call replay did not reproduce; stateful or unstable map"
        return report
    except Exception as error:
        report["classification"] = "incomplete"
        report["error"] = f"{type(error).__name__}: {error}"
        return report
    finally:
        write_json(out / "report.json", report)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("case", type=Path, help="stage map or emitted reproducer.json")
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--host", type=Path)
    parser.add_argument("--timeout", type=float, default=30)
    args = parser.parse_args()
    try:
        report = run(load_json(args.case), args.out, base=args.case.resolve().parent,
                     host=args.host, timeout=args.timeout)
    except (OSError, ValueError, KeyError) as error:
        parser.exit(2, f"incomplete: {error}\n")
    print(f"{report['classification']}: {report['first_divergent_stage'] or report.get('error', 'all mapped stages exact')}")
    for stage in report["stages"]:
        if stage["first_difference"]:
            print(json.dumps({"stage": stage["id"], **stage["first_difference"]}))
    return {"exact": 0, "divergent": 1, "incomplete": 2}[report["classification"]]


if __name__ == "__main__":
    raise SystemExit(main())
