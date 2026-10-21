#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, subprocess, tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "mac/OLMRadialBlur/OLMRadialBlur.cpp"
PROBE = ROOT / "tools/emulation/probe_olmradialblur_type1_any_size_edge_noise_source_guard_20260813.cpp"
REPORT = ROOT / "refs/conformance/olmradialblur_type1_any_size_edge_noise_source_guard_20260813.json"
DOC = REPORT.with_suffix(".md")
SOURCE_SHA = "b74b3d2c7ea6724593b28f82d36615e071e18d813e5b99cc948e26a447fdb0d1"
RUN_SHA = "14c23bfd6ac405e213fe9f5c0aacdf987a0dd72a54fe4a99533717a76bdcf957"
ACTIVE = {
    "PF8": "11dcefe50c65d40f9a695b183f9c95de7cdd51d4c85448e87641dccf04468444",
    "PF16": "1d745a0b5399ed3040b85175c700f8ae403fccede8d115fb1deb99c4d2ac6356",
    "PF32": "187a7caf98537700d3644aed245150467f284b87ef73df56e46dd331ba40cf1f",
}
BOUNDARY = {
    "proven": "12 fixed Rotation Type1 size/edge/noise component-source cells retain pre-guard output and nine route-specific source mutations reject on each architecture",
    "not_proven": ["Type2 numerical equality", "arbitrary source", "native AE", "installed candidate", "remaining Type1 families"],
}

def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def run(arch: str) -> list[str]:
    with tempfile.TemporaryDirectory(prefix=f"radial-any-size-edge-{arch}.") as raw:
        exe = Path(raw) / "probe"
        sdk = subprocess.check_output(["xcrun", "--show-sdk-path"], text=True).strip()
        cmd = ["clang++", "-std=c++17", "-arch", arch, "-O2", "-fno-fast-math",
               "-ffp-contract=off", "-isysroot", sdk, "-Wno-pragma-pack",
               "-Wno-deprecated-declarations", "-I", str(ROOT / "Headers"),
               "-I", str(ROOT / "Headers/SP"), "-I", str(ROOT / "Util"),
               "-I", str(ROOT / "Resources"), "-I", str(ROOT / "core"),
               "-I", str(ROOT / "mac/OLMRadialBlur"), str(PROBE),
               str(ROOT / "mac/OLMRadialBlur/OLMRadialBlur_Strings.cpp"),
               str(ROOT / "Util/AEGP_SuiteHandler.cpp"), str(ROOT / "Util/MissingSuiteError.cpp"),
               "-framework", "Cocoa", "-o", str(exe)]
        built = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
        if built.returncode:
            raise RuntimeError(built.stdout + built.stderr)
        result = subprocess.run([str(exe)], cwd=ROOT, capture_output=True, text=True)
        if result.returncode:
            raise RuntimeError(result.stdout + result.stderr)
    if hashlib.sha256(result.stdout.encode()).hexdigest() != RUN_SHA:
        raise RuntimeError("transcript drift")
    lines = result.stdout.splitlines()
    if len(lines) != 21 or sum(x.startswith("POS ") for x in lines) != 12 or sum(x.startswith("NEG ") for x in lines) != 9:
        raise RuntimeError("row drift")
    return lines

def generate() -> dict:
    if sha(SOURCE) != SOURCE_SHA:
        raise RuntimeError("source drift")
    text = SOURCE.read_text()
    marker = "MatchesRadial32x18PlainOrComponentFixture<PixelT>(input, true);"
    if marker not in text or text.count(marker) != 2:
        raise RuntimeError("guard missing or ambiguous")
    return {
        "schema": "olmradialblur.type1-any-size-edge-noise-source-guard/1",
        "status": "pass_hostless",
        "authorities": {"production_sha256": sha(SOURCE), "probe_sha256": sha(PROBE)},
        "active_source_sha256": ACTIVE,
        "runs": [{"arch": arch, "lines": run(arch), "transcript_sha256": RUN_SHA}
                 for arch in ("arm64", "x86_64")],
        "positive_cells_per_arch": 12,
        "mutation_rejects_per_arch": 9,
        "claim_boundary": BOUNDARY,
        "promotion_state": "hostless_closed_universal_rebuild_and_install_pending",
    }

def validate(value: dict) -> None:
    keys = {"schema", "status", "authorities", "active_source_sha256", "runs",
            "positive_cells_per_arch", "mutation_rejects_per_arch", "claim_boundary", "promotion_state"}
    if set(value) != keys:
        raise RuntimeError("schema")
    if value["schema"] != "olmradialblur.type1-any-size-edge-noise-source-guard/1" or value["status"] != "pass_hostless":
        raise RuntimeError("status")
    if value["authorities"] != {"production_sha256": sha(SOURCE), "probe_sha256": sha(PROBE)}:
        raise RuntimeError("identity")
    if value["active_source_sha256"] != ACTIVE or value["claim_boundary"] != BOUNDARY:
        raise RuntimeError("boundary")
    if value["positive_cells_per_arch"] != 12 or value["mutation_rejects_per_arch"] != 9:
        raise RuntimeError("count")
    if value["promotion_state"] != "hostless_closed_universal_rebuild_and_install_pending":
        raise RuntimeError("promotion")
    if [row.get("arch") for row in value["runs"]] != ["arm64", "x86_64"]:
        raise RuntimeError("arch")
    for row in value["runs"]:
        if set(row) != {"arch", "lines", "transcript_sha256"} or row["transcript_sha256"] != RUN_SHA:
            raise RuntimeError("run schema")
        if hashlib.sha256(("\n".join(row["lines"]) + "\n").encode()).hexdigest() != RUN_SHA:
            raise RuntimeError("run digest")

def doc(_: dict) -> str:
    return ("# RadialBlur Type1 size/edge/noise source guard\n\n"
            "Twelve fixed PF8/PF16/PF32 component-source rows retain their pre-guard output on both architectures; "
            "nine route-specific source mutations per slice fail closed. Install and AE remain pending.\n")

def main() -> None:
    parser = argparse.ArgumentParser(); parser.add_argument("--write", action="store_true"); args = parser.parse_args()
    fresh = generate()
    if args.write:
        REPORT.write_text(json.dumps(fresh, indent=2, sort_keys=True) + "\n"); DOC.write_text(doc(fresh))
    else:
        saved = json.loads(REPORT.read_text()); validate(saved)
        if saved != fresh or DOC.read_text() != doc(saved):
            raise RuntimeError("persisted drift")
    print("PASS_OLMRADIALBLUR_TYPE1_ANY_SIZE_EDGE_NOISE_SOURCE_GUARD")

if __name__ == "__main__":
    main()
