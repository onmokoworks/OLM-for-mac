"""Reproducible, crate-local 2026-11-12 qualification; no shared source edits."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
TOOLS = ROOT / "rust/tools"
for name in ("oracle", "scaffold", "triage", "witness", "diverge"):
    sys.path.insert(0, str(TOOLS / name))
import olm_oracle as oracle
import olm_scaffold as scaffold

BASE = ROOT.parent
OLD = BASE / "ghidra_windows_aex/ColorKeep.aex"
NEW = BASE / "upstream_20261112/extracted/OLMColorKeep/OLMColorKeep/Plugins/64"
TARGET = Path("D:/olm-rs-target/Up-colorkeep")
OUT = HERE / "validation/upstream-20261112"
CANDIDATE = OUT / "ColorKeep.aex"


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def run(args, log, timeout=1200):
    result = oracle.run_process(args, timeout, {"CARGO_TARGET_DIR": str(TARGET), "PYTHONDONTWRITEBYTECODE": "1"})
    save(OUT / (log + ".process.json"), result)
    if log.startswith("record-replay-") and result["returncode"] == 0:
        print(log, "exact", flush=True)
    else:
        print(log, result["returncode"], result["stdout"][-1500:], result["stderr"][-1000:], flush=True)
    if result["returncode"] != 0 or result["timeout"]:
        raise RuntimeError(log)


def build():
    # Shared Cargo.lock may need changes belonging to other concurrent jobs.
    # Compile the actual production source/build.rs through a private manifest.
    manifest = HERE / "validation/build/Cargo.toml"
    text = '''[package]
name = "color-keep"
version = "0.1.0"
edition = "2021"
publish = false
build = "../../build.rs"
[workspace]
[lib]
path = "../../src/lib.rs"
crate-type = ["rlib", "cdylib"]
[dependencies]
olm-core = { path = "../../../../crates/olm-core" }
olm-math = { path = "../../../../crates/olm-math" }
olm-ae = { path = "../../../../crates/olm-ae" }
serde_json = "1"
[build-dependencies]
pipl = { git = "https://github.com/virtualritz/after-effects.git", rev = "0e0b197850f28c1bb24e8c82fce2e3d4c120d1e9" }
winres = "0.1"
[profile.release]
debug = 1
[[example]]
name = "callback-witness"
path = "../../witness_adapter.rs"
crate-type = ["cdylib"]
[[example]]
name = "record-adapter"
path = "../../record_adapter.rs"
'''
    manifest.parent.mkdir(parents=True, exist_ok=True)
    manifest.write_text(text, encoding="utf-8")
    for command, extra in [("build", []), ("test", []), ("build", ["--example", "callback-witness"])]:
        run(["cargo", command, "--manifest-path", str(manifest), "--release", "--offline", "-j", "2", *extra], command + ("-adapter" if extra else ""))
    shutil.copyfile(TARGET / "release/color_keep.dll", CANDIDATE)


def supplement():
    from concurrent.futures import ThreadPoolExecutor
    cases = []
    for count in (0, 1, 100, 101, 199, 200):
        for alpha in (0, 255):
            for ds in ("1", "1/2", "1/4"):
                i = len(cases)
                source_seed = 20261112 + i
                source = oracle.input_pixels(11, 7, source_seed)
                rgba = next(p for p in source.reshape(-1, 4) if 0 < p[3] < 255 and any(p[:3]))
                assignments = [{"slot": 1, "value": count}]
                if count:
                    assignments.append({"slot": count + 1, "color": [alpha, *map(int, rgba[:3])]})
                cases.append({"index": i, "size": [11, 7], "input_seed": source_seed,
                              "downsample": ds, "assignments": assignments, "unassigned": [],
                              "untouched_defaults": [], "numeric_ranges": {"1": {"minimum": 0, "maximum": 200, "kind": "integer"}}})
    for label, reference, candidate, plans in [
        ("matched-2025", NEW / "2025/ColorKeep.aex", CANDIDATE, cases),
        ("matched-2026", NEW / "2026/ColorKeep.aex", CANDIDATE, cases),
        ("old-new-matched", OLD, NEW / "2025/ColorKeep.aex", [c for c in cases if c["assignments"][0]["value"] in (1, 100)]),
    ]:
        folder = OUT / label
        folder.mkdir()
        identities = {k: oracle.identity(v) for k,v in {"reference": reference, "candidate": candidate, "harness": oracle.DEFAULT_HARNESS, "tool": Path(oracle.__file__)}.items()}
        jobs = [(c, route) for c in plans for route in ("smart8", "smart16", "smart32")]
        def execute(job):
            return oracle.run_case(folder, job[0], job[1], identities, (), None, 120)
        with ThreadPoolExecutor(max_workers=2) as pool:
            rows = list(pool.map(execute, jobs))
        save(folder / "summary.json", {"identities": identities, "results": rows})
        counts = {s:sum(r["status"] == s for r in rows) for s in sorted({r["status"] for r in rows})}
        print(label, counts, flush=True)
        assert all(r["status"] == ("mismatched" if label == "old-new-matched" else "exact") for r in rows)


def recordings():
    manifest = HERE / "validation/build/Cargo.toml"
    # Add only the test adapter dependency/example to the private build manifest.
    text = manifest.read_text()
    if 'name = "record-adapter"' not in text:
        text = text.replace('[dependencies]', '[dependencies]\nserde_json = "1"')
        text += '\n[[example]]\nname = "record-adapter"\npath = "../../record_adapter.rs"\n'
        manifest.write_text(text)
    run(["cargo", "build", "--manifest-path", str(manifest), "--release", "--offline", "-j", "2", "--example", "record-adapter"], "build-record-adapter")
    for depth, rva in [(8, 0x15c0), (16, 0x1690), (32, 0x1780)]:
        size = depth // 8 * 4
        profile = {"schema_version": 1, "module_sha256": oracle.identity(NEW / "2025/ColorKeep.aex")["sha256"],
                   "functions": [{"name": f"pixel{depth}", "rva": hex(rva), "args": ["ptr", "i32", "i32", "ptr", "ptr"], "return": "i32", "adapter": f"color-keep.{depth}", "max_calls": 6,
                                  "buffers": [{"arg": 0, "size": 3236, "stride": 4, "role": "input"}, {"arg": 3, "size": size, "stride": size, "role": "input"}, {"arg": 4, "size": size, "stride": size, "role": "inout"}]}]}
        profile_path = OUT / f"record-profile-{depth}.json"
        save(profile_path, profile)
        request_path = OUT / "record-request.json"
        save(request_path, {"schema_version": 1, "assignments": [{"slot": 1, "value": 200}, {"slot": 201, "color": [255, 0, 0, 0]}]})
        folder = OUT / f"record-{depth}"
        run([sys.executable, str(TOOLS / "record/record.py"), "capture", "--module", str(NEW / "2025/ColorKeep.aex"), "--profile", str(profile_path), "--request", str(request_path), "--route", f"smart{depth}", "--out", str(folder), "--max-calls", "6"], f"record-{depth}")
        records = sorted((folder / "calls").glob("*/record.json"))
        assert len(records) == 6
        for i, record in enumerate(records):
            run([sys.executable, str(TOOLS / "record/record.py"), "replay", str(record), "--out", str(OUT / f"record-replay-{depth}-{i}"), "--adapter-exe", str(TARGET / "release/examples/record-adapter.exe")], f"record-replay-{depth}-{i}")


def golden():
    manifest = HERE / "validation/build/Cargo.toml"
    text = manifest.read_text()
    if 'name = "golden-color-keep"' not in text:
        text += '\n[[example]]\nname = "golden-color-keep"\npath = "../../golden_probe.rs"\n'
        manifest.write_text(text)
    run(["cargo", "build", "--manifest-path", str(manifest), "--release", "--offline", "-j", "2", "--example", "golden-color-keep"], "build-golden")
    # --only deliberately does not publish shared manifests (tool-owner policy).
    run([sys.executable, str(TOOLS / "golden/regenerate.py"), "--originals", str(NEW / "2025"), "--harness", str(oracle.DEFAULT_HARNESS), "--kira-harness", str(oracle.DEFAULT_HARNESS), "--out", str(OUT / "golden"), "--jobs", "2", "--only", "color-keep", "--bin-dir", str(TARGET / "release/examples")], "golden")


def sensitivity():
    """Activate each of the 200 palette controls against a translucent source."""
    from types import SimpleNamespace
    import oracle_resident
    folder = OUT / "active-sensitivity"
    folder.mkdir()
    cases = []
    for i in range(200):
        seed = 20261112 + i
        source = oracle.input_pixels(11, 7, seed)
        rgba = next(p for p in source.reshape(-1, 4) if 0 < p[3] < 255 and any(p[:3]))
        cases.append({"index": i, "size": [11, 7], "input_seed": seed,
                      "downsample": ["1", "1/2", "1/4"][i % 3],
                      "assignments": [{"slot": 1, "value": 200}, {"slot": i + 2, "color": [255, *map(int, rgba[:3])]}],
                      "unassigned": [], "untouched_defaults": []})
    identities = {k: oracle.identity(v) for k,v in {"reference": NEW / "2025/ColorKeep.aex", "candidate": CANDIDATE, "harness": oracle.DEFAULT_HARNESS, "tool": Path(oracle.__file__), "resident_tool": Path(oracle_resident.__file__)}.items()}
    summary = {"schema_version": 1, **identities, "complete": False, "results": [], "routes": {}, "jobs": 2}
    save(folder / "cases.json", cases)
    args = SimpleNamespace(out=folder, jobs=2, timeout=120, perturb_candidate=[], extent=None)
    assert oracle_resident.render_campaign(args, cases, identities, {r:None for r in ("smart8", "smart16", "smart32")}, [], summary, oracle) == 0


def diagnose_change():
    case = OUT / "old-new-matched/case-0006-smart8"
    run([sys.executable, str(TOOLS / "oracle/olm_oracle.py"), "minimize", str(case), "--out", str(OUT / "old-new-minimized"), "--max-attempts", "16"], "old-new-minimize")
    run([sys.executable, str(TOOLS / "ubdetect/ubdetect.py"), "classify", "--case", str(case), "--out", str(OUT / "old-new-stability"), "--repeats", "3", "--profile", "none"], "old-new-stability")


def report():
    def read(relative):
        return json.loads((OUT / relative).read_text())
    def evidence(relative):
        p = OUT / relative
        return {"path": str(p.relative_to(HERE)), "sha256": hashlib.sha256(p.read_bytes()).hexdigest()}
    metadata = read("metadata-summary.json")
    for identity in metadata["identities"].values():
        assert oracle.identity(Path(identity["path"]))["sha256"] == identity["sha256"]
    campaigns = {}
    for name in ["random-20261112", "random-20261113", "fresh-2025", "fresh-2026", "active-sensitivity"]:
        d = read(name + "/summary.json")
        assert d["complete"] and d["exit_code"] == 0
        campaigns[name] = {**evidence(name + "/summary.json"), "transport": d.get("transport", "per_process"),
                           "routes": {k: {field:v[field] for field in ("cases_run", "exact", "mismatched", "reference_unrenderable", "reference_timeout", "candidate_failure", "tool_error")} for k,v in d["routes"].items()}}
    for name in ["matched-2025", "matched-2026", "old-new-matched"]:
        d = read(name + "/summary.json")
        campaigns[name] = {**evidence(name + "/summary.json"), "transport": "per_process", "routes": {}}
        for route in ("smart8", "smart16", "smart32"):
            rows = [r for r in d["results"] if r["route"] == route]
            campaigns[name]["routes"][route] = {"cases_run": len(rows), **{status:sum(r["status"]==status for r in rows) for status in ("exact", "mismatched", "reference_unrenderable", "reference_timeout", "candidate_failure", "tool_error")}}
    golden = read("golden/verification.json")["plugins"]["ColorKeep"]
    old_golden = json.loads((TOOLS / "golden/golden.json").read_text())
    changed = [r["id"] for r in golden["cases"] if old_golden.get(r["id"]) != r["rust_sha256"]]
    record_rows = []
    for depth in (8, 16, 32):
        for i in range(6):
            path = f"record-replay-{depth}-{i}/comparison.json"
            d = read(path)
            assert d["exact"] and d["original_cleanup"] and d["adapter_cleanup"]
            record_rows.append({"depth":depth, **evidence(path)})
    stop = read("hub/reports/last-stop.json")
    assert stop["exited"] and not stop["remaining"]
    import olm_triage as triage
    resource = scaffold.resources(NEW / "2025/ColorKeep.aex")[0]
    report = {"job": "Up-colorkeep", "release": "2026-11-12", "measured": "2026-11-13",
              "qualification": "AEXCompat Windows x64 CPU, not native AE or macOS acceptance",
              "metadata": metadata, "pipl": {"length":len(resource["bytes"]), "sha256":hashlib.sha256(resource["bytes"]).hexdigest(), "fields":triage.decode_pipl(resource["bytes"])["fields"]},
              "source_sha256": {name:hashlib.sha256((HERE/name).read_bytes()).hexdigest() for name in ("src/lib.rs", "build.rs", "Cargo.toml", "witness_adapter.rs", "record_adapter.rs", "golden_probe.rs", "validate_upstream.py", "upstream_hub.py")},
              "build_equivalence": read("build-equivalence.json"), "unit_tests":4,
              "campaigns": campaigns, "random_cases_per_depth":400, "random_seeds":[20261112,20261113], "downsample":["1","1/2","1/4"],
              "witnesses": read("witness-summary.json"), "record_replays":record_rows,
              "golden": {**evidence("golden/verification.json"), "exact":golden["exact"], "changed_legacy_hashes":changed, "shared_manifests_written":False, "follow_up":"Refresh ColorKeep's 54 entries and upstream identity in shared golden verification when the owner supports per-plugin publishing, or as part of an authorized all-plugin regeneration. Add translucent matches and counts 101/199/200 to the shared corpus."},
              "static": {"reused_triage":evidence("reused-triage.json"), "decompile":evidence("decompile.json"), "old_decompile":evidence("decompile-old.json"), "funcdb":evidence("funcdb.json"), "function_counts":read("funcdb.json")["counts"], "callbacks":{"8":"0x15c0","16":"0x1690","32":"0x1780"}, "conversion_helpers":["0x7080","0x70f0","0x7160"]},
              "old_new_minimize":evidence("old-new-minimized/summary.json"), "old_new_stability":evidence("old-new-stability/verdict.json"),
              "owned_hub_cleanup":stop,
              "limits":["Native AE project load/save and conditional parameter UI unverified; original color visibility handler is not implemented by the existing shared glue.", "macOS arm64/x86_64 builds and packaging unverified on this Windows machine.", "Full-render sources are PNG-promoted SDR. Direct callback witnesses include bounded HDR/nonfinite values but do not qualify arbitrary HDR/nonfinite worlds.", "Resident exact results retain shared module state; fresh-process campaigns are reported separately.", "Cropped-demand/row-padding/temporal behavior not newly qualified; historical old-binary evidence is not promoted.", "Shared Cargo.lock needed an update at initial build; isolated build avoids editing files outside ownership."]}
    save(HERE / "upstream-validation.json", report)
    print("Wrote", HERE / "upstream-validation.json")


def metadata():
    probe = TOOLS / "scaffold/local/all-ten-final/probe/capture.aex"
    caps, resources, identities = {}, {}, {}
    for name, aex in {"old": OLD, "2025": NEW / "2025/ColorKeep.aex", "2026": NEW / "2026/ColorKeep.aex", "candidate": CANDIDATE}.items():
        folder = OUT / "metadata" / name
        folder.mkdir(parents=True, exist_ok=True)
        inv = oracle.inspect(oracle.DEFAULT_HARNESS, aex, 120)
        save(folder / "inventory.json", inv)
        res = scaffold.resources(aex)
        desc = scaffold.descriptor(res)
        env = {"OLM_SCAFFOLD_ORIGINAL": str(aex), "OLM_SCAFFOLD_ENTRY": desc["entry"], "OLM_SCAFFOLD_CAPTURE": str(folder / "declarations.json")}
        process = oracle.run_process([oracle.DEFAULT_HARNESS, "--headless", "--inspect-experimental-with-deps", probe, aex.parent], 120, env)
        save(folder / "capture-process.json", process)
        assert process["returncode"] == 0 and not process["timeout"], process
        cap = json.loads((folder / "declarations.json").read_text())
        scaffold.validate_capture(inv, cap)
        caps[name] = cap
        resources[name] = res
        identities[name] = oracle.identity(aex)
    # Full resource identity and supplemental declarations, not only public UI.
    assert resources["2025"] == resources["candidate"]
    assert caps["2025"] == caps["candidate"], "supplemental declaration difference"
    oldp, newp = caps["old"]["params"], caps["2025"]["params"]
    assert oldp[1:] == newp[1:101]
    save(OUT / "metadata-summary.json", {"identities": identities, "pipl_exact": True, "declarations_exact": True, "old_palette_declarations_preserved": True, "counts": {k:len(v["params"]) for k,v in caps.items()}})


def campaigns():
    for seed in (20261112, 20261113):
        name = f"random-{seed}"
        run([sys.executable, str(TOOLS / "oracle/olm_oracle.py"), "render", "--reference", str(NEW / "2025/ColorKeep.aex"), "--candidate", str(CANDIDATE), "--resident", "--cases", "203", "--seed", str(seed), "--jobs", "2", "--sizes", "1x1,3x7,11x7,31x19,97x61", "--downsample", "1,1/2,1/4", "--routes", "smart8,smart16,smart32", "--out", str(OUT / name)], name)
    for year in (2025, 2026):
        name = f"fresh-{year}"
        run([sys.executable, str(TOOLS / "oracle/olm_oracle.py"), "render", "--reference", str(NEW / f"{year}/ColorKeep.aex"), "--candidate", str(CANDIDATE), "--cases", "12", "--seed", "20261114", "--jobs", "2", "--sizes", "3x7,11x7,31x19", "--downsample", "1,1/2,1/4", "--routes", "smart8,smart16,smart32", "--out", str(OUT / name)], name)


def witnesses():
    import copy
    import random
    import struct
    import numpy as np
    import olm_diverge as diverge
    adapter = TARGET / "release/examples/callback_witness.dll"
    summaries = []
    for depth, rva, fmt in [(8, 0x15c0, "B"), (16, 0x1690, "H"), (32, 0x1780, "f")]:
        rng = random.Random(20261112 + depth)
        contexts, inputs = bytearray(), bytearray()
        calls, stages = [], []
        for i in range(320):
            if depth == 8:
                p = [rng.randrange(256) for _ in range(4)]
                normalized = [float(np.float32(x) * np.float32(1 / 255)) for x in p]
            elif depth == 16:
                p = [rng.randrange(65536) for _ in range(4)]
                normalized = [x / 32768 for x in p]
            else:
                p = [float(np.float32(rng.uniform(-2, 3))) for _ in range(4)]
                if i < 16:
                    special = [0.0, -0.0, float("nan"), float("inf"), -float("inf"), 1e-38, 1.0, 2.0]
                    p[1 + i % 3] = special[i % len(special)]
                normalized = p[:]
            # Includes alpha-independent hits, all RGB channels, both threshold
            # neighbors, unordered values, and active entries beyond old slot 101.
            count = [0, 1, 2, 100, 101, 199, 200][i] if i < 7 else 1
            palette = [[1.0, 8.0, 8.0, 8.0] for _ in range(count)]
            if count:
                c = normalized[:]
                c[0] = float(np.float32(rng.random()))
                threshold = np.float32(0.0001)
                delta = [0.0, -0.0, 0.00005, -0.00005, 0.0002, -0.0002,
                         float(np.nextafter(threshold, np.float32(0))), float(threshold),
                         float(np.nextafter(threshold, np.float32(1)))][i % 9]
                channel = 1 + i % 3
                c[channel] = float(np.float32(c[channel]) + np.float32(delta))
                palette[-1] = c
            offset = len(contexts)
            contexts += bytes(0x20) + struct.pack("<i", count)
            for c in palette:
                contexts += struct.pack("<4f", *c)
            contexts += bytes((-len(contexts)) % 16)
            pixel_offset = len(inputs)
            inputs += struct.pack("<4" + fmt, *p)
            args = [{"type": "ptr", "buffer": "contexts", "offset": offset},
                    {"type": "i32", "value": 0}, {"type": "i32", "value": 0},
                    {"type": "ptr", "buffer": "input", "offset": pixel_offset},
                    {"type": "ptr", "buffer": "output", "offset": pixel_offset}]
            calls.append({"rva": hex(rva), "args": args, "return": "i32"})
            selection = {"call": i, "buffer": "output", "offset": pixel_offset}
            stages.append({"id": f"pixel-{i:03d}", "dtype": "u8", "shape": [depth // 8 * 4],
                           "grounding": f"New callback {rva:#x}: context count +0x20, ARGB palette +0x24, alpha-only store; production pixel adapter",
                           "reference": selection, "candidate": selection})
        buffers = {name: {"size": len(data), "hex": data.hex()} for name, data in
                   [("contexts", contexts), ("input", inputs), ("output", inputs)]}
        native = {"schema_version": 1, "module": str(NEW / "2025/ColorKeep.aex"), "buffers": buffers, "calls": calls}
        rust = copy.deepcopy(native)
        rust["module"] = str(adapter)
        for call in rust["calls"]:
            call.pop("rva")
            call["export"] = f"callback{depth}"
        case = {"schema_version": 1, "scope": f"ColorKeep new CPU {depth}-bpc callback, 320 independent pixels",
                "stages": stages, "stateless": True}
        for side, spec in [("reference", native), ("candidate", rust)]:
            case[side] = {"sha256": oracle.identity(Path(spec["module"]))["sha256"], "witness": spec,
                          "return_bits": {str(i): "00000000" for i in range(len(calls))}}
        report = diverge.run(case, OUT / f"witness-{depth}", timeout=120)
        print("witness", depth, report["classification"], report.get("error"), flush=True)
        assert report["classification"] == "exact", report.get("first_divergent_stage")
        summaries.append({"depth": depth, "cases": len(calls), "exact": len(report["stages"])})
    save(OUT / "witness-summary.json", summaries)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("phase", choices=["build", "metadata", "campaigns", "witnesses", "supplement", "recordings", "golden", "sensitivity", "diagnose_change", "report"])
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    globals()[args.phase]()
