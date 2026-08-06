#!/usr/bin/env python3
"""Smoke and adversarial mutation tests for the OLMSmoother v1 boundary audit."""

from __future__ import annotations

import hashlib
import shutil
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from audit_olmsmoother_v1_32bpc_host_conversion_boundary_20260730 import (  # noqa: E402
    DISASM,
    MAC,
    MANIFEST,
    PIPL,
    REQUEST,
    WIN,
    build_report,
)


def copied_root(*, include_exrs: bool = False) -> tuple[tempfile.TemporaryDirectory[str], Path]:
    holder = tempfile.TemporaryDirectory(prefix="olm_smoother_v1_host_boundary_")
    root = Path(holder.name)
    for relative in (REQUEST, DISASM, MAC, PIPL):
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / relative, target)
    win_target = root / WIN
    win_target.mkdir(parents=True, exist_ok=True)
    for source in (ROOT / WIN).iterdir():
        target = win_target / source.name
        if source.suffix == ".exr":
            if include_exrs:
                shutil.copy2(source, target)
        else:
            shutil.copy2(source, target)
    return holder, root


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def authoritative_hashes() -> dict[str, str]:
    paths = [ROOT / MANIFEST, ROOT / REQUEST, ROOT / DISASM, ROOT / MAC, ROOT / PIPL]
    paths.extend(sorted((ROOT / WIN).glob("*.exr")))
    return {str(path.relative_to(ROOT)): sha256(path) for path in paths}


def reject_mutation(relative: Path, old: str, new: str) -> None:
    holder, root = copied_root()
    try:
        path = root / relative
        text = path.read_text(encoding="utf-8")
        assert old in text, f"mutation anchor absent: {old}"
        path.write_text(text.replace(old, new, 1), encoding="utf-8")
        try:
            build_report(root)
        except (AssertionError, KeyError, ValueError):
            return
        raise AssertionError(f"adversarial mutation accepted: {relative} {old!r}")
    finally:
        holder.cleanup()


def run_smoke() -> None:
    report = build_report(ROOT)
    assert report["windows"]["effect_changing_count"] == 8
    assert report["windows"]["exact_pass_through_cases"] == [
        "final_random10_olm_smoother_05",
        "final_random10_olm_smoother_07",
    ]
    assert report["binary"]["native_pf32_branch"] is False
    assert report["mac"]["smart_render_bit10"] is False
    assert report["mac"]["float_color_aware_bit12"] is False

    reject_mutation(MANIFEST, '"bits_per_channel": 32', '"bits_per_channel": 16')
    reject_mutation(REQUEST, '"match_name": "OLM Smoother"', '"match_name": "OLM Smoother v2"')
    reject_mutation(DISASM, "FUN_1800011e0(param_1", "FUN_180001400(param_1")
    reject_mutation(
        DISASM,
        "FUN_1800011e0(param_1,param_2",
        "FUN_1800011e0(param_1,param_2);\n    FUN_18000ffff(param_1,param_2",
    )
    reject_mutation(DISASM, "// program: OLMSmoother.aex", "// unrelated drift\n// program: OLMSmoother.aex")
    reject_mutation(MAC, "out_data->out_flags2 = 0x08000000;", "out_data->out_flags2 = 0x08001000;")
    reject_mutation(PIPL, "AE_Effect_Global_OutFlags_2 { 0x08000000 }", "AE_Effect_Global_OutFlags_2 { 0x08000400 }")
    reject_mutation(
        MANIFEST,
        '"match_name": "OLM Smoother-0001",',
        '"match_name": "OLM Smoother-0001",\n              "duplicate_probe": true,',
    )

    holder, root = copied_root(include_exrs=True)
    try:
        effect = next((root / WIN).glob("*final_random10_olm_smoother_05.exr"))
        raw = bytearray(effect.read_bytes())
        raw[-1] ^= 1
        effect.write_bytes(raw)
        try:
            build_report(root)
        except (AssertionError, ValueError):
            pass
        else:
            raise AssertionError("mutated EXR payload was accepted")
    finally:
        holder.cleanup()


def main() -> int:
    before = authoritative_hashes()
    try:
        run_smoke()
    finally:
        after = authoritative_hashes()
        if after != before:
            changed = sorted(set(before) | set(after))
            changed = [path for path in changed if before.get(path) != after.get(path)]
            raise AssertionError(f"smoke modified authoritative repository files: {changed}")
    print("[OK] OLMSmoother v1 host-conversion audit and adversarial mutations")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
