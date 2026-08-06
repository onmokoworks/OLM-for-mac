#!/usr/bin/env python3
from __future__ import annotations
import importlib.util
import hashlib
import struct
import subprocess
import tempfile
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
WRITERS = ROOT / "tools/emulation/test_olmkirakira_typed_writers_actual_aex_20260716.py"
INSTALLED = Path.home() / "Library/Application Support/Adobe/Common/Plug-ins/7.0/MediaCore/OLMKiraKira.plugin"
EXPECTED_INSTALLED_SHA256 = "cd97c6f328bf6a4adbe001662f35c12af405f89a2374046f185f68673df96719"
def main() -> int:
    with tempfile.TemporaryDirectory(prefix="olmkira-mode4-tail-") as tmp:
        binary = Path(tmp) / "tail"
        subprocess.run(["c++", "-std=c++20", "-O2", "-ffp-contract=off",
                        str(ROOT / "tools/emulation/test_kirakira_mode4_cropped_typed.cpp"),
                        "-o", str(binary)], check=True)
        lines = dict(line.split("=", 1) for line in subprocess.check_output([str(binary)], text=True).splitlines())
    rgba = tuple(struct.unpack("<f", int(bits, 16).to_bytes(4, "little"))[0]
                 for bits in lines["RGBA_BITS"].split(","))
    spec = importlib.util.spec_from_file_location("kira_writers", WRITERS)
    assert spec and spec.loader
    writers = importlib.util.module_from_spec(spec); spec.loader.exec_module(writers)
    for depth in ("PF8", "PF16", "PF32"):
        actual = writers.run_writer(depth, rgba)["raw_hex"]
        production = lines[depth]
        if depth == "PF16":
            production = b"".join(int(production[i:i+4], 16).to_bytes(2, "little") for i in range(0, 16, 4)).hex()
        elif depth == "PF32":
            production = b"".join(int(production[i:i+8], 16).to_bytes(4, "little") for i in range(0, 32, 8)).hex()
        assert actual == production, (depth, actual, production)
    source = (ROOT / "mac/OLMKiraKira/OLMKiraKira.cpp").read_text(encoding="utf-8")
    assert "centered_crop_scalar(" in source and "WriteAexTruncate" in source
    assert INSTALLED.exists()
    subprocess.run(["codesign", "--verify", "--deep", "--strict", str(INSTALLED)], check=True)
    installed_binary = INSTALLED / "Contents/MacOS/OLMKiraKira"
    assert hashlib.sha256(installed_binary.read_bytes()).hexdigest() == EXPECTED_INSTALLED_SHA256
    assert set(subprocess.check_output(["lipo", "-archs", str(installed_binary)], text=True).split()) == {"arm64", "x86_64"}
    print("PASS_OLMKIRAKIRA_MODE4_CROP_TYPED_INSTALLED_20260805 " + " ".join(f"{k}={lines[k]}" for k in ("PF8","PF16","PF32")))
    return 0
if __name__ == "__main__": raise SystemExit(main())
