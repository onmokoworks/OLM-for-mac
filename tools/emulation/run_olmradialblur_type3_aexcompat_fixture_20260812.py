#!/usr/bin/env python3
"""Run the bounded PF32 Type-3 actual-AEX fixture and fail-close admission gate."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import struct
import subprocess
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from prepare_olmradialblur_type3_windows_witness_20260811 import png_rgba

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "mac/OLMRadialBlur/OLMRadialBlur.cpp"
BOUNDARY = ROOT / "refs/conformance/olmradialblur_type3_pf32_aexcompat_fixture_boundary_20260812.json"
AEX_SHA256 = "ffbb1d0109671e3ea9b1a12cd1126f2c72f965197577a57cc602fb096414ccdb"
CASES = (
    ("pf32_zoom_nv25_pattern", 1, "pattern"),
    ("pf32_zoom_nv25_inverse", 1, "inverse"),
    ("pf32_rotation_nv25_pattern", 2, "pattern"),
    ("pf32_rotation_nv25_inverse", 2, "inverse"),
)
REPEATS = (1, 2)
KIND = {
    0: "layer", 1: "integer", 2: "float", 3: "angle", 4: "integer",
    5: "color", 6: "point", 7: "integer", 8: "custom", 9: "no_data",
    10: "float", 11: "arbitrary_data", 12: "path", 13: "group_start",
    14: "group_end", 15: "button", 18: "point3d",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(command: list[str], *, cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=cwd, capture_output=True, text=True)


def setup_parameters(guest_worker: Path, aex: Path, cwd: Path) -> list[dict]:
    completed = run([str(guest_worker), "setup", str(aex)], cwd=cwd)
    if completed.returncode:
        raise RuntimeError(f"guest setup failed: {completed.stderr.strip()}")
    report = json.loads(completed.stdout)
    if report.get("params_setup_error") != 0 or len(report.get("parameters", [])) != 30:
        raise RuntimeError("OLMRadialBlur ParamsSetup did not return the pinned 30 slots")
    result = []
    for row in report["parameters"]:
        param_type = int(row["param_type"])
        count = 1 if param_type == 3 else 2 if param_type == 6 else 3 if param_type == 18 else 0
        result.append({
            "slot": int(row["slot"]), "name": row.get("name", "Parameter"),
            "kind": KIND.get(param_type, "custom"),
            "minimum": row.get("valid_min") if row.get("valid_min") is not None else -32768,
            "maximum": row.get("valid_max") if row.get("valid_max") is not None else 32768,
            "value": row.get("default_value") if row.get("default_value") is not None else 0,
            "choices": [], "color": [255, 0, 0, 0], "components": [0, 0, 0],
            "component_count": count, "layer_path": None, "enabled": True,
            "visible": True, "supervised": False, "debug_summary": None,
            "custom_ui_events": 0, "control_size": [0, 0],
        })
    if [row["slot"] for row in result] != list(range(1, 31)):
        raise RuntimeError("OLMRadialBlur parameter slots are not the pinned contiguous 1..30 map")
    return result


def case_parameters(base: list[dict], blur_type: int) -> list[dict]:
    values = {1: blur_type, 4: 4, 5: 1, 6: 0, 10: 0, 15: 1, 17: 1,
              20: 5, 21: 1, 22: 0, 24: 25, 25: 3, 27: 1, 29: 3}
    result = json.loads(json.dumps(base))
    for parameter in result:
        slot = parameter["slot"]
        if slot in values:
            parameter["value"] = values[slot]
        if slot == 2:
            parameter["components"] = [4, 3, 0]
        elif slot in (18, 28):
            parameter["components"] = [0, 0, 0]
        elif slot == 26:
            parameter["layer_path"] = "noise.png"
    return result


def write_fixtures(root: Path, base: list[dict], render_path: str) -> None:
    for case_id, blur_type, layer_name in CASES:
        directory = root / "fixtures" / case_id
        directory.mkdir(parents=True)
        (directory / "primary.png").write_bytes(png_rgba("source"))
        (directory / "noise.png").write_bytes(png_rgba(layer_name))
        fixture = {
            "schema": "aexcompat.render_fixture", "schema_version": 1,
            "primary_layer": "primary.png", "parameters": case_parameters(base, blur_type),
            "pixel_format": "argb32f", "render_path": render_path,
            "premultiplication": "straight",
            "timing": {"current_time": 0, "time_step": 1, "total_time": 1, "time_scale": 1},
            "final_artifact": "exr",
            "checkpoints": [
                {"id": "input_world", "stage": f"{render_path}-input"},
                {"id": "output_world", "stage": f"{render_path}-output"},
                {"id": "noise_layer", "stage": f"{render_path}-layer-slot26"},
            ],
        }
        (directory / "fixture.json").write_text(json.dumps(fixture, indent=2) + "\n")


def render_one(harness: Path, aex: Path, work: Path, case_id: str, repeat: int) -> dict:
    output = work / "results" / f"{case_id}.r{repeat}"
    completed = run([str(harness), "--headless", "--render-fixture", str(aex),
                     str(work / "fixtures" / case_id / "fixture.json"), str(output)],
                    cwd=harness.parent)
    log = work / "logs" / f"{case_id}.r{repeat}"
    log.parent.mkdir(parents=True, exist_ok=True)
    (log.with_suffix(".stdout")).write_text(completed.stdout)
    (log.with_suffix(".stderr")).write_text(completed.stderr)
    row = {"case_id": case_id, "repeat": repeat, "returncode": completed.returncode,
           "stderr": completed.stderr.strip(), "published": output.is_dir()}
    if completed.returncode == 0 and output.is_dir():
        row["hashes"] = {
            "input_world": sha256(output / "checkpoints/input_world/output.bin"),
            "noise_layer": sha256(output / "checkpoints/noise_layer/output.bin"),
            "output_world": sha256(output / "checkpoints/output_world/output.bin"),
            "exr": sha256(output / "final/output.exr"),
        }
        raw = (output / "checkpoints/output_world/output.bin").read_bytes()
        row["output_nonzero"] = any(raw)
    return row


def compile_production_probe(directory: Path) -> Path:
    source_path = str(SOURCE).replace("\\", "\\\\").replace('"', '\\"')
    cpp = directory / "production_probe.cpp"
    exe = directory / "production_probe"
    cpp.write_text(f'''#define OLM_RADIALBLUR_TEST_SEAM 1
#include "{source_path}"
#include <fstream>
#include <vector>
int main(int argc,char**argv){{if(argc!=5)return 1;constexpr int W=9,H=7;
std::vector<PF_PixelFloat> input(W*H),layer(W*H),output(W*H);
std::ifstream(argv[1],std::ios::binary).read((char*)input.data(),input.size()*sizeof(PF_PixelFloat));
std::ifstream(argv[2],std::ios::binary).read((char*)layer.data(),layer.size()*sizeof(PF_PixelFloat));
PF_EffectWorld iw{{}},lw{{}},ow{{}};iw.data=(PF_PixelPtr)input.data();lw.data=(PF_PixelPtr)layer.data();ow.data=(PF_PixelPtr)output.data();
iw.width=lw.width=ow.width=W;iw.height=lw.height=ow.height=H;iw.rowbytes=lw.rowbytes=ow.rowbytes=W*sizeof(PF_PixelFloat);
OLMRadialBlurInfo i{{}};i.blur_type=std::atoi(argv[3]);i.center_x=4;i.center_y=3;i.outer_strength=4;i.outer_offset_mode=1;
i.inner_offset_mode=1;i.repeat_border=TRUE;i.ratio=1;i.quality=5;i.brightness_gain=1;i.noise_variation=25;i.noise_type=3;
i.noise_layer=1;i.seed=1;i.thickness=3;i.comp_width=W;i.comp_height=H;
if(OLMRadialBlurTestRenderWorldWithNoiseLayer(&iw,&ow,&lw,&i,32)!=PF_Err_NONE)return 3;
std::ofstream(argv[4],std::ios::binary).write((char*)output.data(),output.size()*sizeof(PF_PixelFloat));return 0;}}''')
    command = ["xcrun", "clang++", "-std=c++17", "-O2", "-fno-fast-math",
               "-ffp-contract=off", "-D__MACH__", "-Wno-pragma-pack", "-I.", "-IHeaders",
               "-IHeaders/SP", "-IUtil", "-IResources", str(cpp),
               "mac/OLMRadialBlur/OLMRadialBlur_Strings.cpp", "Util/AEGP_SuiteHandler.cpp",
               "Util/MissingSuiteError.cpp", "-framework", "Cocoa", "-o", str(exe)]
    completed = run(command, cwd=ROOT)
    if completed.returncode:
        raise RuntimeError(f"production probe build failed: {completed.stderr}")
    return exe


def production_rows(exe: Path, work: Path, rows: list[dict]) -> list[dict]:
    result = []
    modes = {case_id: blur_type for case_id, blur_type, _ in CASES}
    for row in rows:
        item = {"case_id": row["case_id"], "repeat": row["repeat"], "returncode": None,
                "exact": False}
        if not row.get("published"):
            item["reason"] = "actual output was not published"
            result.append(item)
            continue
        actual = work / "results" / f'{row["case_id"]}.r{row["repeat"]}'
        output = work / "production" / f'{row["case_id"]}.r{row["repeat"]}.bin'
        output.parent.mkdir(parents=True, exist_ok=True)
        completed = run([str(exe), str(actual / "checkpoints/input_world/output.bin"),
                         str(actual / "checkpoints/noise_layer/output.bin"),
                         str(modes[row["case_id"]]), str(output)], cwd=ROOT)
        item["returncode"] = completed.returncode
        if completed.returncode == 0 and output.is_file():
            actual_output = actual / "checkpoints/output_world/output.bin"
            item["production_sha256"] = sha256(output)
            item["actual_sha256"] = sha256(actual_output)
            item["exact"] = output.read_bytes() == actual_output.read_bytes()
        else:
            item["reason"] = "production Type 3 remained fail-closed"
        result.append(item)
    return result


def same(rows: list[dict], case_id: str, field: str) -> bool:
    values = [row.get("hashes", {}).get(field) for row in rows if row["case_id"] == case_id]
    return len(values) == 2 and None not in values and len(set(values)) == 1


def evaluate(rows: list[dict], production: list[dict], expected: dict) -> dict:
    published = len(rows) == 8 and all(row.get("published") for row in rows)
    input_exact = published and len({row["hashes"]["input_world"] for row in rows}) == 1
    repeat_exact = published and all(same(rows, case_id, field) for case_id, _, _ in CASES
                                     for field in ("input_world", "noise_layer", "output_world", "exr"))
    layer_hashes = {name: {row.get("hashes", {}).get("noise_layer") for row in rows
                           if row["case_id"].endswith(name)} for name in ("pattern", "inverse")}
    layer_exact = published and all(len(values) == 1 and None not in values for values in layer_hashes.values()) \
        and layer_hashes["pattern"] != layer_hashes["inverse"]
    outputs_nonzero = published and all(row.get("output_nonzero") for row in rows)
    output_distinct = published and all(
        next(row["hashes"]["output_world"] for row in rows if row["case_id"] == f"pf32_{mode}_nv25_pattern") !=
        next(row["hashes"]["output_world"] for row in rows if row["case_id"] == f"pf32_{mode}_nv25_inverse")
        for mode in ("zoom", "rotation"))
    output_gate = published and repeat_exact and outputs_nonzero and output_distinct
    production_exact = len(production) == 8 and all(row["returncode"] == 0 and row["exact"] for row in production)
    admission = input_exact and layer_exact and output_gate and production_exact
    observed = {
        "world_io_checkpoint_gate": "pass" if input_exact and layer_exact else "fail",
        "repeat_determinism_gate": "pass" if repeat_exact else "fail",
        "actual_aex_output_gate": "pass" if output_gate else "fail",
        "production_admission": admission,
    }
    pinned = expected["decision"]
    expected_view = {key: pinned[key] for key in observed}
    return {"status": "exact" if admission else "fail_closed", "observed": observed,
            "expected_boundary": expected_view, "matches_expected_boundary": observed == expected_view,
            "published_renders": sum(bool(row.get("published")) for row in rows),
            "checks": {"primary_exact": input_exact, "secondary_layer_exact": layer_exact,
                       "repeat_exact": repeat_exact, "outputs_nonzero": outputs_nonzero,
                       "pattern_inverse_output_distinct": output_distinct,
                       "production_exact": production_exact}}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--aexcompat-repo", type=Path, required=True)
    parser.add_argument("--harness", type=Path)
    parser.add_argument("--guest-worker", type=Path)
    parser.add_argument("--aex", type=Path, required=True)
    parser.add_argument("--render-path", choices=("classic", "smart"), default="classic")
    parser.add_argument("--work-dir", type=Path)
    parser.add_argument("--report", type=Path)
    parser.add_argument("--expect-boundary", type=Path, default=BOUNDARY)
    parser.add_argument("--allow-status-change", action="store_true")
    args = parser.parse_args()
    repo = args.aexcompat_repo.resolve()
    harness = (args.harness or repo / "broker/target/release/aexcompat-harness").resolve()
    guest = (args.guest_worker or repo / "guest/target/release/aex-guest-worker").resolve()
    aex = args.aex.resolve()
    for path in (repo, harness, guest, aex, args.expect_boundary):
        if not path.exists():
            parser.error(f"required path does not exist: {path}")
    if sha256(aex) != AEX_SHA256:
        parser.error("AEX identity differs from the pinned OLMRadialBlur 2025 binary")
    temporary = None
    if args.work_dir:
        work = args.work_dir.resolve()
        if work.exists():
            parser.error("--work-dir must not already exist")
        work.mkdir(parents=True)
    else:
        temporary = tempfile.TemporaryDirectory(prefix="olmradial-type3-aexcompat-")
        work = Path(temporary.name)
    base = setup_parameters(guest, aex, repo)
    write_fixtures(work, base, args.render_path)
    jobs = [(case_id, repeat) for case_id, _, _ in CASES for repeat in REPEATS]
    with ThreadPoolExecutor(max_workers=8) as pool:
        rows = list(pool.map(lambda job: render_one(harness, aex, work, *job), jobs))
    probe = compile_production_probe(work)
    production = production_rows(probe, work, rows)
    expected = json.loads(args.expect_boundary.read_text())
    verdict = evaluate(rows, production, expected)
    report = {"schema": "olmradialblur-type3-aexcompat-pilot/1", "aex_sha256": AEX_SHA256,
              "aexcompat_repo": str(repo), "render_path": args.render_path,
              "work_dir": str(work) if args.work_dir else None, "renders": rows,
              "production": production, "verdict": verdict}
    encoded = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.report:
        args.report.write_text(encoded)
    print(encoded, end="")
    ok = verdict["matches_expected_boundary"] or args.allow_status_change
    if temporary:
        temporary.cleanup()
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
