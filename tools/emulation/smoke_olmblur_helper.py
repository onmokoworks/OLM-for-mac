"""Export and replay every OLMBlur helper fixture with the portable C++ core."""
from __future__ import annotations
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "tools/emulation"
FIXTURES = HERE / "fixtures/olmblur_helper"
BIN = Path("/tmp/olmblur_helper_replay")

subprocess.run(["python3", str(HERE / "export_olmblur_helper_fixtures.py")], cwd=ROOT, check=True)
subprocess.run(["c++", "-std=c++17", "-O2", "-ffp-contract=off", "-Icore",
                "core/olmblur_helper.cpp", str(HERE / "replay_olmblur_helper_fixture.cpp"), "-o", str(BIN)],
               cwd=ROOT, check=True)
manifest = json.loads((FIXTURES / "manifest.json").read_text())
for case in manifest["cases"]:
    files = case["files"]
    args = [str(BIN), case["direction"]] + [str(FIXTURES / files[key]["path"]) for key in ("flags", "src", "weights", "expected")] + [
        str(case["width"]), str(case["height"]), str(case["passes"]), str(case["offset"]), str(case["radius"])]
    subprocess.run(args, cwd=ROOT, check=True)
print(f"[OK] OLMBlur helper smoke passed: {len(manifest['cases'])} fixtures")
