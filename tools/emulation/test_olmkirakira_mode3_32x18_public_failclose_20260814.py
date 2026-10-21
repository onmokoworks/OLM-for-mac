#!/usr/bin/env python3
"""Prove a non-admitted Kira Mode3 32x18 source fails closed at all depths."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "mac/OLMKiraKira/OLMKiraKira.cpp"
STRINGS = ROOT / "mac/OLMKiraKira/OLMKiraKira_Strings.cpp"
BASE = ROOT / "tools/emulation/test_olmkirakira_mode1_exported_effectmain_all_depths_20260812.py"
REPORT = ROOT / "refs/conformance/olmkirakira_mode3_32x18_public_failclose_20260814.json"
DOC = REPORT.with_suffix(".md")
WIDTH, HEIGHT, PADDING = 32, 18, 12
DEPTHS = ("PF8", "PF16", "PF32")


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def build_probe() -> str:
    spec = importlib.util.spec_from_file_location("kira_exported_base", BASE)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(mod)
    rgba = tuple(
        ((i * 15) & 255, (i * 11) & 255, (i * 7) & 255, 64 + ((i * 11) % 192))
        for i in range(WIDTH * HEIGHT)
    )
    rgba_text = ",".join("{" + ",".join(map(str, pixel)) + "}" for pixel in rgba)
    code = (mod.CPP.replace("__SOURCE__", str(SOURCE))
            .replace("__STRINGS__", str(STRINGS))
            .replace("__RGBA__", rgba_text))
    code = code.replace("const int W=5,H=3,PAD=12",
                        f"const int W={WIDTH},H={HEIGHT},PAD={PADDING}")
    code = code.replace("int raw[15][4]", f"int raw[{WIDTH * HEIGHT}][4]")
    code = code.replace(
        "u.sd.value=7;defs[OLMKIRAKIRA_DIAGONAL_LENGTH]",
        "u.sd.value=50;defs[OLMKIRAKIRA_DIAGONAL_LENGTH]",
    )
    code = code.replace(
        "OLMKIRAKIRA_BLUR_MODE].u.pd.value=1",
        "OLMKIRAKIRA_BLUR_MODE].u.pd.value=3",
    )
    success_fragment = (
        "if(e||ib!=before)return 10;for(int y=0;y<H;y++){"
        "std::fwrite(ob.data()+y*RB,1,W*sizeof(P),stdout);"
        "for(int x=W*sizeof(P);x<RB;x++)if(ob[y*RB+x]!=0xD3)return 20;}return 0;"
    )
    failclose_fragment = (
        "if(e!=PF_Err_BAD_CALLBACK_PARAM||ib!=before)return 10;"
        "for(unsigned char v:ob)if(v!=0xD3)return 20;return 0;"
    )
    assert success_fragment in code
    code = code.replace(success_fragment, failclose_fragment)
    old_main = (
        "int main(){if(run<PF_Pixel8>(PF_PixelFormat_ARGB32)||"
        "run<PF_Pixel16>(PF_PixelFormat_ARGB64)||"
        "run<PF_PixelFloat>(PF_PixelFormat_ARGB128))return 2;}"
    )
    new_main = (
        "int main(){int a=run<PF_Pixel8>(PF_PixelFormat_ARGB32);"
        "int b=run<PF_Pixel16>(PF_PixelFormat_ARGB64);"
        "int c=run<PF_PixelFloat>(PF_PixelFormat_ARGB128);"
        "std::printf(\"PF8=%d PF16=%d PF32=%d\\n\",a,b,c);return a||b||c;}"
    )
    assert old_main in code
    return code.replace(old_main, new_main)


def execute() -> tuple[str, str]:
    code = build_probe()
    with tempfile.TemporaryDirectory(prefix="kira_mode3_32x18_failclosed_") as raw:
        directory = Path(raw)
        source = directory / "probe.cpp"
        executable = directory / "probe"
        source.write_text(code, encoding="utf-8")
        sdk = subprocess.check_output(["xcrun", "--show-sdk-path"], text=True).strip()
        command = [
            "clang++", "-std=c++20", "-O2", "-fno-fast-math", "-ffp-contract=off",
            "-isysroot", sdk, "-I", str(ROOT / "Headers"),
            "-I", str(ROOT / "Headers/SP"), "-I", str(ROOT / "Util"),
            "-I", str(ROOT / "Resources"), str(source),
            str(ROOT / "Util/AEGP_SuiteHandler.cpp"),
            str(ROOT / "Util/MissingSuiteError.cpp"),
            "-framework", "Cocoa", "-o", str(executable),
        ]
        built = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
        if built.returncode:
            raise RuntimeError(built.stderr)
        result = subprocess.run([str(executable)], cwd=ROOT, capture_output=True, text=True)
        if result.returncode or result.stdout.strip() != "PF8=0 PF16=0 PF32=0":
            raise AssertionError((result.returncode, result.stdout, result.stderr))
    return sha(code.encode()), result.stdout.strip()


def generate() -> dict:
    probe_sha, stdout = execute()
    return {
        "schema": "olmkirakira_mode3_32x18_public_failclose_v2",
        "date": "2026-08-14",
        "status": "exact_fail_closed_unlisted_source",
        "production_source_sha256": sha(SOURCE.read_bytes()),
        "probe_sha256": probe_sha,
        "fixture": {
            "dimensions": [WIDTH, HEIGHT], "padding": PADDING,
            "blur_mode": 3, "merge_mode": 1,
            "horizontal_length": 50, "source_pattern": "unlisted_modulo192_alpha_v1",
        },
        "depths": list(DEPTHS),
        "result": {
            "return": "PF_Err_BAD_CALLBACK_PARAM",
            "input_full_storage_unchanged": True,
            "output_full_storage_untouched": True,
            "probe_stdout": stdout,
        },
        "boundary": (
            "The current public Mac EffectMain admits only the separately proven wrapped-linear "
            "32x18 source for this tuple. This modulo-192-alpha source is not admitted and fails "
            "closed before output mutation. No numerical equality is claimed for this source."
        ),
        "ae_launched": False,
        "installed_or_production_modified": False,
    }


def validate(saved: dict) -> None:
    assert saved == generate()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    current = generate()
    if args.write:
        REPORT.write_text(json.dumps(current, indent=2) + "\n", encoding="utf-8")
        DOC.write_text(
            "# OLMKiraKira Mode3 32x18 public fail-close（2026-08-14）\n\n"
            "Status: **exact_fail_closed_unlisted_source**\n\n"
            "現行Mac public `EffectMain`へMode3 / Horizontal Length 50 / 32x18を"
            "PF8・PF16・PF32で入力した。全深度が `PF_Err_BAD_CALLBACK_PARAM` を返し、"
            "入力全領域は不変、出力全領域は未変更だった。別途raw exactで証明した"
            "wrapped-linear sourceだけを32x18へadmitし、このmodulo-192-alpha sourceには"
            "数値一致やWindows owner一致を主張しない。\n",
            encoding="utf-8",
        )
    else:
        validate(json.loads(REPORT.read_text(encoding="utf-8")))
    print(json.dumps({"status": current["status"], "depths": current["depths"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
