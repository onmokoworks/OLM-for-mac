#!/usr/bin/env python3
"""Rebuild and replay the first DistanceGradation AEX CPU fixture."""

from __future__ import annotations

import hashlib
import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
COMMITTED_FIELDGEN = ROOT / "tools/emulation/fixtures/distancegradation_fieldgen_synthetic_17x11"
COMMITTED_COMPOSE = ROOT / "tools/emulation/fixtures/distancegradation_compose_case0023_triplet"


def run(command: list[str]) -> None:
    subprocess.run(command, cwd=ROOT, check=True)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def assert_fixture_matches(committed: Path, generated: Path) -> None:
    expected_names = sorted(path.name for path in committed.iterdir() if path.is_file())
    generated_names = sorted(path.name for path in generated.iterdir() if path.is_file())
    if generated_names != expected_names:
        raise AssertionError(f"fixture file set changed: committed={expected_names} generated={generated_names}")
    for name in expected_names:
        if digest(committed / name) != digest(generated / name):
            raise AssertionError(f"fixture is not deterministic: {committed.name}/{name}")


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="olm_dg_cpu_fixture_") as temp_value:
        temp = Path(temp_value)
        generated_fieldgen = temp / "fieldgen_fixture"
        generated_compose = temp / "compose_fixture"
        replay_fieldgen = temp / "replay_dg_fieldgen_fixture"
        replay_compose = temp / "replay_dg_compose_fixture"
        distance_stage_test = temp / "test_dg_core_distance_stage"
        run([
            str(ROOT / "tools/emulation/.venv/bin/python"),
            "tools/emulation/export_dg_fieldgen_fixture.py",
            "--output", str(generated_fieldgen),
        ])
        run([
            str(ROOT / "tools/emulation/.venv/bin/python"),
            "tools/emulation/export_dg_compose_fixture.py",
            "--output", str(generated_compose),
        ])
        run([
            str(ROOT / "tools/emulation/.venv/bin/python"),
            "tools/emulation/fixture_contract/verifier.py",
            str(generated_fieldgen),
        ])
        run([
            str(ROOT / "tools/emulation/.venv/bin/python"),
            "tools/emulation/fixture_contract/verifier.py",
            str(generated_compose),
        ])

        assert_fixture_matches(COMMITTED_FIELDGEN, generated_fieldgen)
        assert_fixture_matches(COMMITTED_COMPOSE, generated_compose)

        run([
            "clang++", "-std=c++17", "-O2", "-Wall", "-Wextra", "-Werror",
            "core/olmdistancegradation_fieldgen.cpp",
            "tools/emulation/replay_dg_fieldgen_fixture.cpp",
            "-o", str(replay_fieldgen),
        ])
        run([
            str(replay_fieldgen),
            str(generated_fieldgen / "input_mask_u8.bin"),
            str(generated_fieldgen / "call_params_le_i32.bin"),
            str(generated_fieldgen / "field_f32.bin"),
        ])
        run([
            "clang++", "-std=c++17", "-O2", "-Wall", "-Wextra", "-Werror",
            "core/olmdistancegradation_fieldgen.cpp",
            "tools/emulation/replay_dg_compose_fixture.cpp",
            "-o", str(replay_compose),
        ])
        run([
            str(replay_compose),
            str(generated_compose / "field_agrb16.bin"),
            str(generated_compose / "refcon.bin"),
            str(generated_compose / "output_triplet_agrb16.bin"),
        ])
        run([
            "clang++", "-std=c++17", "-O2", "-Wall", "-Wextra", "-Werror",
            "core/olmdistancegradation_fieldgen.cpp",
            "tools/emulation/test_dg_core_distance_stage.cpp",
            "-o", str(distance_stage_test),
        ])
        run([str(distance_stage_test)])
    print("[OK] DG AEX CPU fieldgen/compose fixture export, verification, determinism, and portable replay passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
