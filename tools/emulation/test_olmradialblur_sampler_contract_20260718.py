#!/usr/bin/env python3
"""Local exact-contract regression for OLMRadialBlur's AEX alpha sampler."""

from __future__ import annotations

import json
import os
import platform
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "mac/OLMRadialBlur/OLMRadialBlur.cpp"
ORACLE = ROOT / "refs/conformance/olmradialblur_border_sampler_semantics_actual_aex_20260716.json"
EXPECTED_FIXTURE = {
    "width": 2,
    "height": 2,
    "row_stride_floats": 8,
    "plane_rgba_f32": [
        0.1, 0.2, 0.3, 0.8,
        0.4, 0.5, 0.6, 0.4,
        0.7, 0.8, 0.9, 0.2,
        1.0, 0.9, 0.8, 0.6,
    ],
}
EXPECTED_RECORDS = (
    "left_loose_window",
    "top_loose_window",
    "interior_control",
)


class ContractError(RuntimeError):
    """Raised when the regression cannot safely prove the requested contract."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ContractError(f"FAIL_CLOSED: {message}")


def load_oracle() -> dict[str, object]:
    require(SOURCE.is_file(), f"source missing: {SOURCE}")
    require(ORACLE.is_file(), f"oracle missing: {ORACLE}")
    try:
        report = json.loads(ORACLE.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ContractError(f"FAIL_CLOSED: oracle is not valid JSON: {exc}") from exc
    fixture = report.get("fixture")
    require(isinstance(fixture, dict), "oracle fixture missing")
    require(fixture == EXPECTED_FIXTURE, "oracle fixture does not match documented 2x2 RGBA float fixture")
    records = report.get("records")
    require(isinstance(records, list) and records, "oracle records missing")
    names = [record.get("name") for record in records if isinstance(record, dict)]
    require(names == list(EXPECTED_RECORDS), f"oracle record set/order changed: {names!r}")
    for record in records:
        require(isinstance(record, dict), "oracle record is not an object")
        for mode in ("non_repeat", "repeat_border"):
            branch = record.get(mode)
            require(isinstance(branch, dict), f"{record.get('name')}: oracle branch {mode} missing")
            words = branch.get("rgba_f32_words")
            require(
                isinstance(words, list) and len(words) == 4 and all(isinstance(word, str) for word in words),
                f"{record.get('name')}:{mode}: oracle RGBA words missing",
            )
            require(isinstance(branch.get("return_rax"), int), f"{record.get('name')}:{mode}: oracle return missing")
    return report


def build_probe(directory: Path) -> Path:
    compiler_name = os.environ.get("CXX", "clang++")
    compiler = shutil.which(compiler_name)
    require(compiler is not None, f"compiler unavailable: {compiler_name}")
    xcrun = shutil.which("xcrun")
    require(xcrun is not None, "xcrun unavailable")
    sdk = subprocess.run([xcrun, "--show-sdk-path"], capture_output=True, text=True, check=False)
    require(sdk.returncode == 0 and sdk.stdout.strip(), f"macOS SDK unavailable: {sdk.stderr.strip()}")

    source_text = str(SOURCE).replace("\\", "\\\\").replace('"', '\\"')
    probe = directory / "olmradialblur_sampler_contract_probe.cpp"
    binary = directory / "olmradialblur_sampler_contract_probe"
    probe.write_text(
        '''#define OLM_RADIALBLUR_TEST_SEAM 1
#include "__SOURCE__"

#include <cstdint>
#include <cstdio>
#include <cstring>

static std::uint32_t probe_bits(float value) {
    std::uint32_t bits = 0;
    std::memcpy(&bits, &value, sizeof(bits));
    return bits;
}

int main() {
    FloatImage image;
    image.width = 2;
    image.height = 2;
    image.rgba = {
        0.1f, 0.2f, 0.3f, 0.8f,
        0.4f, 0.5f, 0.6f, 0.4f,
        0.7f, 0.8f, 0.9f, 0.2f,
        1.0f, 0.9f, 0.8f, 0.6f
    };
    struct SampleCase {
        const char *name;
        float x;
        float y;
        bool repeat;
    };
    const SampleCase cases[] = {
        {"left_loose_window", -1.25f, 0.5f, false},
        {"left_loose_window", -1.25f, 0.5f, true},
        {"top_loose_window", 0.25f, -1.25f, false},
        {"top_loose_window", 0.25f, -1.25f, true},
        {"interior_control", 0.25f, 0.5f, false},
        {"interior_control", 0.25f, 0.5f, true}
    };
    std::puts("{\\"results\\":[");
    for (int i = 0; i < 6; ++i) {
        const AEXPolarSample sample = SampleRGBAAEXAlpha(image, cases[i].x, cases[i].y, cases[i].repeat);
        std::printf(
            "{\\"name\\":\\"%s\\",\\"mode\\":\\"%s\\",\\"eligible\\":%u,"
            "\\"rgba_f32_words\\":[\\"0x%08x\\",\\"0x%08x\\",\\"0x%08x\\",\\"0x%08x\\"]}%s\\n",
            cases[i].name,
            cases[i].repeat ? "repeat_border" : "non_repeat",
            static_cast<unsigned>(sample.eligible),
            probe_bits(sample.rgba[0]),
            probe_bits(sample.rgba[1]),
            probe_bits(sample.rgba[2]),
            probe_bits(sample.rgba[3]),
            i == 5 ? "" : ",");
    }
    std::puts("]}");
    return 0;
}
'''.replace("__SOURCE__", source_text),
        encoding="utf-8",
    )

    command = [
        compiler,
        "-std=c++17",
        "-O2",
        "-fno-fast-math",
        "-ffp-contract=off",
        "-Wno-unused-function",
        "-Wno-unused-parameter",
        "-ffunction-sections",
        "-fdata-sections",
        "-isysroot",
        sdk.stdout.strip(),
        "-I",
        str(ROOT / "Headers"),
        "-I",
        str(ROOT / "Headers/SP"),
        "-I",
        str(ROOT / "Util"),
        "-I",
        str(ROOT / "Resources"),
    ]
    arch = platform.machine()
    if arch in {"arm64", "x86_64"}:
        command.extend(["-arch", arch])
    command.extend(
        [
            str(probe),
            "-Wl,-dead_strip",
            "-framework",
            "Cocoa",
            "-o",
            str(binary),
        ]
    )
    build = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, check=False)
    require(
        build.returncode == 0,
        "temporary source-included sampler probe did not compile:\n" + build.stderr.strip(),
    )
    return binary


def run_probe(binary: Path) -> dict[str, object]:
    run = subprocess.run([str(binary)], cwd=ROOT, capture_output=True, text=True, check=False)
    require(run.returncode == 0, f"temporary probe failed: rc={run.returncode}\n{run.stderr.strip()}")
    try:
        payload = json.loads(run.stdout)
    except json.JSONDecodeError as exc:
        raise ContractError(f"FAIL_CLOSED: probe did not emit valid JSON: {exc}\nstdout={run.stdout!r}") from exc
    require(isinstance(payload, dict), "probe payload is not an object")
    results = payload.get("results")
    require(isinstance(results, list) and len(results) == 6, "probe results missing or incomplete")
    return payload


def compare(oracle: dict[str, object], payload: dict[str, object]) -> list[str]:
    actual_map: dict[tuple[str, str], dict[str, object]] = {}
    for entry in payload["results"]:
        require(isinstance(entry, dict), "probe result entry is not an object")
        name = entry.get("name")
        mode = entry.get("mode")
        require(isinstance(name, str) and isinstance(mode, str), "probe result missing name/mode")
        actual_map[(name, mode)] = entry

    failures: list[str] = []
    for record in oracle["records"]:
        name = record["name"]
        for mode in ("non_repeat", "repeat_border"):
            expected = record[mode]
            actual = actual_map.get((name, mode))
            if actual is None:
                failures.append(f"{name}:{mode}:missing_probe_result")
                continue
            expected_eligible = int(expected["return_rax"])
            actual_eligible = int(actual.get("eligible", -1))
            if actual_eligible != expected_eligible:
                failures.append(
                    f"{name}:{mode}:eligible expected {expected_eligible} got {actual_eligible}"
                )
            actual_words = actual.get("rgba_f32_words")
            if actual_words != expected["rgba_f32_words"]:
                failures.append(
                    f"{name}:{mode}:rgba words expected {expected['rgba_f32_words']} got {actual_words}"
                )
    extra = sorted(set(actual_map) - {(record["name"], mode) for record in oracle["records"] for mode in ("non_repeat", "repeat_border")})
    if extra:
        failures.append(f"unexpected_probe_results:{extra!r}")
    return failures


def main() -> int:
    oracle = load_oracle()
    with tempfile.TemporaryDirectory(prefix="olmradialblur_sampler_contract_20260718_") as name:
        binary = build_probe(Path(name))
        payload = run_probe(binary)
    failures = compare(oracle, payload)
    status = "pass" if not failures else "fail"
    print(f"status={status} oracle={ORACLE.relative_to(ROOT)} source={SOURCE.relative_to(ROOT)}")
    for record in oracle["records"]:
        name = record["name"]
        for mode in ("non_repeat", "repeat_border"):
            entry = next(item for item in payload["results"] if item["name"] == name and item["mode"] == mode)
            print(
                f"{name}:{mode} eligible={entry['eligible']} words={','.join(entry['rgba_f32_words'])}"
            )
    if failures:
        print("failures:")
        for failure in failures:
            print(f"  - {failure}")
        return 2
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ContractError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(2) from exc
