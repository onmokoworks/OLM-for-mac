#!/usr/bin/env python3
"""Hash-bound real AEX comparisons against the existing Rust source translations."""
import argparse
import hashlib
import json
from pathlib import Path
import random
import struct
import subprocess
import time
import witness


def corpus(seed=20261112):
    rng = random.Random(seed)
    counts = sorted(set([0, 1, 2, 3, 96, 240, 511, 512, 513, 1023, 1024, 4095, 4096]
                        + list(range(1, 257)) + [rng.randrange(1, 4097) for _ in range(256)]))
    degrees = [float(i) for i in range(-720, 721)] + [0., -0., 1.e-30, -1.e-30]
    degrees += [rng.uniform(-100000, 100000) for _ in range(2048)]
    degrees += [(-1 if rng.randrange(2) else 1) * 2. ** rng.randrange(-120, 121) * rng.uniform(1, 2) for _ in range(2048)]
    factor = struct.unpack("<d", struct.pack("<Q", 0x3f91df46a2529d39))[0]
    for radians in [2.**-13, 10000., 10000.-struct.unpack("<f", bytes.fromhex("db0fc93f"))[0]]:
        word = struct.unpack("<I", struct.pack("<f", radians))[0]
        for delta in range(-8, 9):
            x = struct.unpack("<f", struct.pack("<I", word+delta))[0]
            degrees.extend([x/factor, -x/factor])
    return {"counts": counts, "degrees": degrees}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--originals", required=True, type=Path)
    p.add_argument("--out", required=True, type=Path)
    p.add_argument("--seed", type=int, default=20261112)
    args = p.parse_args()
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    inputs = corpus(args.seed)
    raw = json.dumps(inputs).encode()
    (out / "inputs.json").write_bytes(raw)
    reference = witness.HERE / "target/release/translation-reference.exe"
    expected_raw = subprocess.run([str(reference)], input=raw, stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, check=True, timeout=60).stdout
    (out / "translation.json").write_bytes(expected_raw)
    expected = json.loads(expected_raw)
    gaussian = {"schema_version": 1, "module": str((args.originals / "OLMDirectionalBlur.aex").resolve()),
        "buffers": {"table": {"size": max(inputs["counts"]) * 4, "fill": 165}},
        "trace": {"math": True, "budget": 64},
        "calls": [{"label": f"length={n}", "rva": "0x1830", "args": [
            {"type": "ptr", "buffer": "table"}, {"type": "i32", "value": n}], "return": "void"} for n in inputs["counts"]]}
    trig = {"schema_version": 1, "module": str((args.originals / "OLMKiraKira.aex").resolve()),
        "calls": [{"label": f"degrees={d!r}", "rva": "0x132b2e0", "args": [
            {"type": "f32", "bits": r["input_bits"]}], "return": "f64"} for d, r in zip(inputs["degrees"], expected["trig"])]}
    summary = {"seed": args.seed, "reference_sha256": witness.sha256(reference),
        "inputs_sha256": hashlib.sha256(raw).hexdigest(), "translation_sha256": hashlib.sha256(expected_raw).hexdigest(),
        "source_sha256": {p.resolve().relative_to(witness.HERE.parents[1]).as_posix(): witness.sha256(p) for p in [
            witness.HERE / "../../plugins/olm-directional-blur/src/algorithm.rs",
            witness.HERE / "../../plugins/olm-kirakira/src/trig.rs",
            witness.HERE / "../../plugins/olm-kirakira/src/trig_tables.rs"]}}
    for name, spec in [("gaussian", gaussian), ("sincos", trig)]:
        started = time.monotonic()
        manifest = witness.run(spec, out / name, timeout=60)
        record = {"classification": manifest["classification"], "module_sha256": manifest["module_sha256"],
                  "process": manifest["process"], "host_sha256": manifest["host_sha256"]}
        summary[name] = record
        if manifest["classification"] != "success":
            (out / "summary.json").write_text(json.dumps(summary, indent=2))
            raise RuntimeError(f"{name}: {manifest['classification']}; inspect {out / name}")
        result = json.loads((out / name / "result.json").read_text())
        actual, wanted, mismatches = bytearray(), bytearray(), []
        if name == "gaussian":
            # The production translation explicitly uses FMA. Do not compare a
            # different native lane and then tune values to hide the discrepancy.
            if result["fma"]["effective"] != 1:
                raise RuntimeError("production Gaussian comparison requires native UCRT FMA=1")
            for i, (n, want) in enumerate(zip(inputs["counts"], expected["gaussian"])):
                a = (out / name / result["calls"][i]["buffers"]["table"]).read_bytes()[:n*4]
                w = bytes.fromhex(want)
                actual.extend(a); wanted.extend(w)
                if a != w:
                    mismatches.append({"index": i, "length": n, "different_words": sum(a[j:j+4] != w[j:j+4] for j in range(0, len(w), 4))})
            record["float_words"] = sum(inputs["counts"])
            record["trace"] = result["trace"]
            record["patched_imports"] = result["imports_patched"]
            if any(p["provider_fma"] != 1 for p in result["imports_patched"] if p["name"] == "expf"):
                raise RuntimeError("expf provider did not confirm FMA=1")
        else:
            for i, (a, w) in enumerate(zip(result["calls"], expected["trig"])):
                a = bytes.fromhex(a["return"]["bits_le"]); w = bytes.fromhex(w["bits_le"])
                actual.extend(a); wanted.extend(w)
                if a != w:
                    mismatches.append({"index": i, "degrees": inputs["degrees"][i], "native": a.hex(), "rust": w.hex()})
        record.update(cases=len(result["calls"]), mismatches=len(mismatches), first_mismatches=mismatches[:16],
            native_sha256=hashlib.sha256(actual).hexdigest(), rust_sha256=hashlib.sha256(wanted).hexdigest(),
            fma=result["fma"], elapsed_total_seconds=time.monotonic()-started)
        print(f"{name}: {record['cases']} cases, {len(mismatches)} mismatches, "
              f"child {manifest['process']['elapsed_seconds']:.3f}s, cleanup={manifest['process']['cleanup_verified']}", flush=True)
        (out / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return 0 if all(summary[n]["mismatches"] == 0 for n in ["gaussian", "sincos"]) else 1


if __name__ == "__main__":
    raise SystemExit(main())
