"""Replay exported Windows Thin witnesses through both real-SDK Mac entries."""
import importlib.util
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools/emulation"))
import probe_olmcolorkey_thin_public_owner_20261001 as owner


def test_legal_thin_public_owner_exact() -> None:
    report = json.loads((ROOT / "reports/colorkey_thin_public_owner_production_20261001.json").read_text())
    assert report["production"] and report["case_count"] == len(report["cases"]) == 216
    assert report["summary"] == {"classic": 216, "smart": 216}
    assert report["aex_sha256"] == owner.general.base.retained.actual_probe.AEX_SHA256
    identities = set()
    with tempfile.TemporaryDirectory(prefix="olmck_thin_replay_") as raw:
        executable = owner.compile_public(Path(raw) / "mac", owner.general.SOURCE.read_text())
        for case in report["cases"]:
            fixture = case["fixture"]
            source, _ = owner.general.fixture(fixture, case["depth"])
            assert owner.general.base.sha(source) == case["input_sha256"]
            values = {p["slot"]: p.get("value") for p in case["parameter_values"]}
            assert (values[1], values[14], values[15]) == (int(case["keep"]), case["thin"], case["type"])
            assert case["guards_intact"]
            identity = (fixture["id"], case["depth"], case["keep"], case["thin"], case["type"])
            assert identity not in identities
            identities.add(identity)
            for route in (0, 1):
                output = subprocess.check_output([str(executable), str(fixture["width"]),
                    str(fixture["height"]), case["depth"][2:], str(case["thin"]),
                    str(case["type"]), str(int(case["keep"])), str(route)], input=source)
                assert len(output) == fixture["width"] * fixture["height"] * owner.general.DEPTHS[case["depth"]]
                assert owner.general.base.sha(output) == case["actual_sha256"], (identity, route)


if __name__ == "__main__":
    test_legal_thin_public_owner_exact()
