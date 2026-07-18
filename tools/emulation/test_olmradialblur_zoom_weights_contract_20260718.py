#!/usr/bin/env python3
"""Exact-contract regression for OLMRadialBlur zoom Gaussian weights."""

from __future__ import annotations

import hashlib
import json
import os
import platform
import shutil
import struct
import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "mac/OLMRadialBlur/OLMRadialBlur.cpp"
EXPECTED_SHA256 = "82d66d41ebba38e15638fd369acdf3a218a9160d39b0ad12a2aad482df8242d8"
EXPECTED_COUNT = 1717
EXPECTED_SINGLE = struct.pack("<f", 1.0)
ARCHES = ("arm64", "x86_64")


class ContractError(RuntimeError):
    """Raised when the requested contract cannot be proven safely."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ContractError(f"FAIL_CLOSED: {message}")


def compiler_path() -> str:
    compiler_name = os.environ.get("CXX", "clang++")
    compiler = shutil.which(compiler_name)
    require(compiler is not None, f"compiler unavailable: {compiler_name}")
    return compiler


def sdk_path() -> str:
    xcrun = shutil.which("xcrun")
    require(xcrun is not None, "xcrun unavailable")
    probe = subprocess.run([xcrun, "--show-sdk-path"], capture_output=True, text=True, check=False)
    require(probe.returncode == 0 and probe.stdout.strip(), f"macOS SDK unavailable: {probe.stderr.strip()}")
    return probe.stdout.strip()


def write_probe(path: Path) -> None:
    escaped_source = str(SOURCE).replace("\\", "\\\\").replace('"', '\\"')
    path.write_text(
        '''#define OLM_RADIALBLUR_TEST_SEAM 1
#include "__SOURCE__"

#include <cstdint>
#include <cstdio>
#include <cstring>
#include <vector>

static bool WriteLittleEndianFloats(const char *path, const std::vector<float> &weights)
{
    FILE *file = std::fopen(path, "wb");
    if (!file) return false;
    for (float value : weights) {
        std::uint32_t bits = 0;
        std::memcpy(&bits, &value, sizeof(bits));
        const unsigned char bytes[4] = {
            static_cast<unsigned char>(bits & 0xffu),
            static_cast<unsigned char>((bits >> 8) & 0xffu),
            static_cast<unsigned char>((bits >> 16) & 0xffu),
            static_cast<unsigned char>((bits >> 24) & 0xffu),
        };
        if (std::fwrite(bytes, 1, sizeof(bytes), file) != sizeof(bytes)) {
            std::fclose(file);
            return false;
        }
    }
    return std::fclose(file) == 0;
}

int main(int argc, char **argv)
{
    if (argc != 3) {
        std::fprintf(stderr, "usage: %s <weights1717.bin> <weights1.bin>\\n", argv[0]);
        return 64;
    }
    const std::vector<float> weights1717 = ZoomGaussianWeights(1717);
    const std::vector<float> weights1 = ZoomGaussianWeights(1);
    if (weights1717.size() != 1717u) return 65;
    if (weights1.size() != 1u) return 66;
    if (!WriteLittleEndianFloats(argv[1], weights1717)) return 67;
    if (!WriteLittleEndianFloats(argv[2], weights1)) return 68;
    std::printf("{\\"count1717\\":%zu,\\"count1\\":%zu}\\n", weights1717.size(), weights1.size());
    return 0;
}
'''.replace("__SOURCE__", escaped_source),
        encoding="utf-8",
    )


def build_probe(directory: Path, arch: str, compiler: str, sdk: str) -> dict[str, object]:
    probe = directory / f"olmradialblur_zoom_weights_probe_{arch}.cpp"
    binary = directory / f"olmradialblur_zoom_weights_probe_{arch}"
    write_probe(probe)
    command = [
        compiler,
        "-std=c++17",
        "-O2",
        "-fno-fast-math",
        "-ffp-contract=off",
        "-Wno-unused-function",
        "-Wno-unused-parameter",
        "-Wno-deprecated-declarations",
        "-isysroot",
        sdk,
        "-I",
        str(ROOT / "Headers"),
        "-I",
        str(ROOT / "Headers/SP"),
        "-I",
        str(ROOT / "Util"),
        "-I",
        str(ROOT / "Resources"),
        "-arch",
        arch,
        str(probe),
        "-Wl,-dead_strip",
        "-framework",
        "Cocoa",
        "-o",
        str(binary),
    ]
    built = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, check=False)
    return {
        "arch": arch,
        "probe": probe,
        "binary": binary,
        "command": command,
        "returncode": built.returncode,
        "stdout": built.stdout,
        "stderr": built.stderr,
        "ok": built.returncode == 0,
    }


def run_attempts(binary: Path, arch: str, out1717: Path, out1: Path) -> tuple[subprocess.CompletedProcess[str] | None, str | None]:
    host_arch = platform.machine()
    arch_tool = shutil.which("arch")
    commands: list[list[str]] = []
    if arch_tool and host_arch == "arm64" and arch == "x86_64":
        commands.append([arch_tool, "-x86_64", str(binary), str(out1717), str(out1)])
    if arch_tool and host_arch == "x86_64" and arch == "arm64":
        commands.append([arch_tool, "-arm64", str(binary), str(out1717), str(out1)])
    commands.append([str(binary), str(out1717), str(out1)])

    last_error: str | None = None
    for command in commands:
        try:
            completed = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, check=False)
            return completed, " ".join(command)
        except OSError as exc:
            last_error = f"{exc.__class__.__name__}: {exc}"
    return None, last_error


def evaluate_binary(binary: Path, arch: str, directory: Path) -> dict[str, object]:
    weights1717 = directory / f"olmradialblur_zoom_weights_{arch}_1717.bin"
    weights1 = directory / f"olmradialblur_zoom_weights_{arch}_1.bin"
    completed, launch = run_attempts(binary, arch, weights1717, weights1)
    if completed is None:
        return {
            "arch": arch,
            "status": "skip",
            "reason": f"not runnable: {launch}",
        }
    if completed.returncode != 0:
        return {
            "arch": arch,
            "status": "skip",
            "reason": f"probe rc={completed.returncode} stderr={completed.stderr.strip() or '<empty>'}",
            "launch": launch,
        }

    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise ContractError(
            f"FAIL_CLOSED: arch={arch}: probe emitted invalid JSON: {exc}: stdout={completed.stdout!r}"
        ) from exc
    require(payload.get("count1717") == EXPECTED_COUNT, f"arch={arch}: probe count1717 changed: {payload!r}")
    require(payload.get("count1") == 1, f"arch={arch}: probe count1 changed: {payload!r}")

    raw1717 = weights1717.read_bytes()
    raw1 = weights1.read_bytes()
    require(len(raw1717) % 4 == 0, f"arch={arch}: weights1717 byte count is not a multiple of 4")
    require(len(raw1) == 4, f"arch={arch}: weights1 byte count changed: {len(raw1)}")
    count1717 = len(raw1717) // 4
    sha256 = hashlib.sha256(raw1717).hexdigest()
    single_bits = struct.unpack("<I", raw1)[0]
    status = "pass"
    failures: list[str] = []
    if count1717 != EXPECTED_COUNT:
        status = "fail"
        failures.append(f"count1717 expected {EXPECTED_COUNT} got {count1717}")
    if sha256 != EXPECTED_SHA256:
        status = "fail"
        failures.append(f"sha256 expected {EXPECTED_SHA256} got {sha256}")
    if raw1 != EXPECTED_SINGLE:
        status = "fail"
        failures.append(
            f"n1 expected {EXPECTED_SINGLE.hex()} got {raw1.hex()} (bits=0x{single_bits:08x})"
        )
    return {
        "arch": arch,
        "status": status,
        "launch": launch,
        "count1717": count1717,
        "sha256": sha256,
        "n1_bits": f"0x{single_bits:08x}",
        "failures": failures,
    }


def native_required_arch() -> str:
    host_arch = platform.machine()
    return host_arch if host_arch in ARCHES else "arm64"


def main() -> int:
    require(SOURCE.is_file(), f"source missing: {SOURCE}")
    compiler = compiler_path()
    sdk = sdk_path()
    required_arch = native_required_arch()
    results: list[dict[str, object]] = []
    fatal = False

    with tempfile.TemporaryDirectory(prefix="olmradialblur_zoom_weights_contract_20260718_") as name:
        tempdir = Path(name)
        for arch in ARCHES:
            build = build_probe(tempdir, arch, compiler, sdk)
            if not build["ok"]:
                result = {
                    "arch": arch,
                    "status": "build_failed",
                    "reason": (build["stderr"] or build["stdout"] or "").strip() or "<empty>",
                }
                results.append(result)
                if arch == required_arch or arch == "arm64":
                    fatal = True
                continue
            try:
                result = evaluate_binary(Path(build["binary"]), arch, tempdir)
            except ContractError:
                raise
            results.append(result)
            if result["status"] == "fail":
                fatal = True
            if arch == required_arch and result["status"] != "pass":
                fatal = True
            if arch == "arm64" and result["status"] != "pass":
                fatal = True

    print(f"source={SOURCE.relative_to(ROOT)} host_arch={platform.machine()} required_arch={required_arch}")
    for result in results:
        arch = result["arch"]
        status = result["status"]
        if status == "pass":
            print(
                f"arch={arch} status=pass count1717={result['count1717']} "
                f"sha256={result['sha256']} n1_bits={result['n1_bits']}"
            )
        elif status == "fail":
            print(
                f"arch={arch} status=fail count1717={result['count1717']} "
                f"sha256={result['sha256']} n1_bits={result['n1_bits']}"
            )
            for failure in result["failures"]:
                print(f"  failure={failure}")
        else:
            print(f"arch={arch} status={status} reason={result['reason']}")

    return 2 if fatal else 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ContractError as exc:
        print(str(exc))
        raise SystemExit(2)
