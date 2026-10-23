#!/usr/bin/env python3
"""Freeze the PF32 Strength-290 exported-owner host-math boundary.

This is deliberately a non-promotion closure.  The exported AEX was run through
an AE-free AEXCompat worker after adding f32 atan2f/log2f imports.  Its result is
not native Windows UCRT evidence.  The pinned internal owner and the current Mac
typed owner agree, while the exported host-substituted path differs.
"""
from __future__ import annotations

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tools.emulation.olm_assets import resolve_asset

import argparse
import base64
import hashlib
import json
from pathlib import Path
import struct
import zlib


ROOT = Path(__file__).resolve().parents[2]
REPORT = ROOT / "refs/conformance/olmradialblur_strength290_exported_math_boundary_20260814.json"
MARKDOWN = REPORT.with_suffix(".md")
SOURCE = ROOT / "mac/OLMRadialBlur/OLMRadialBlur.cpp"
AEX = resolve_asset(ROOT / "aex/OLMRadialBlur/Plugins/64/2025/OLMRadialBlur.aex")
PATCH = ROOT / "tools/emulation/aexcompat_olmradialblur_float_math_imports_20260814.patch"
TRACE_PATCH = ROOT / "tools/emulation/aexcompat_olmradialblur_float_math_trace_20260814.patch"
TYPE1_REPORT = ROOT / "refs/conformance/olmradialblur_rotation_type1_inverse_cell_closure_20260812.json"
TYPE1_TOOL = ROOT / "tools/emulation/test_olmradialblur_rotation_type1_inverse_cell_closure_20260812.py"

EXPECTED = {
    "source": "b74b3d2c7ea6724593b28f82d36615e071e18d813e5b99cc948e26a447fdb0d1",
    "aex": "ffbb1d0109671e3ea9b1a12cd1126f2c72f965197577a57cc602fb096414ccdb",
    "patch": "04147344b71c3f08a5e7e796d9d50f65845def15e924a2836a9e89ae249f81e3",
    "trace_patch": "a1dc5e91cb2a9c9c2e332c7ce2361c97eee6134e9b89f3bf0e9bd890b8038684",
    "type1_report": "d0dd7b20615e18a0e9dc3cf501c4fe858f88e5ef7344ab9f691a2a41f2a9921b",
    "type1_tool": "4e50de24a7f1eeda37c1a24d60a6cfb58c0f94d0bc14970f6e3ade0c73b22a5e",
}

SOURCE_B85 = "c-rmPu}cDB7zXgilMutjLUCz{79j%ZXtMWp6NG{Y?vH5l4{&fRP;hD!oP}nm!$E=qk(>_48yap1z2S%(i~Cw#9E9}wZO{5VeDHn%5z#trMffQ2p9OJNll=K6u!jP#Zt_=J@#G3>qbmE_!TqC-pfwW|^Jed0Dwz9%=+@-rf#NI@;O3fr?cn}#Ptdg#cIofEe+aH}iX+G5Fr)Abispd(6A=*+(f04vNk!qV1pRkOvU~UYKTRplPnG@b!Tzt8ikD->!ZZ7i?-kC8qEY7lL_|dNKku91TX1oxupW5N5E0QvegMx0KHU"
EXPORTED_B85 = "c-rlkZBUd|7>3_>!QBnYB?Mhya9AcXzGM)pfql<&134);Qv!u%L_+#w3lp+T9TmkaDxwJ1!A1lfu^9(}BouS`7?m*{VIp85#bm-10tES3Cq&<N1M6SYuL9;=|L!^ep6h<joFfSTOz?6wX^v!3oOdCud)yInK^1x2G?HP*F}j+w0QM<PINw@I+t1X|DMcX0XqXcHyXl>KE%fwQ3ndorp_=#!3fJ_JIx~fm8&9&gf|S^87BO&kFI$;Zs5fX-_@%-D&pKqYU6Ivc!jKB`byo;!MNHuQuY@e>rNsIy3iK(WpJE)5m$3|o!;g@%rjAx#^MPZ~EBN|KGdZqmp`aKATH19;7cF%Da1Uj{NZUfQDZyQdJ^6Mhx}3*4@9vi}om7bV@KJO~`<U0-ws6tvThYaRPY2eetfv((d_pdzCn?`=E_UV<HiYNW+qv~r9PbMEk_<?8Wprtzg9^;v_^x6r$_IX>jp}|XUTh&>lRwrd=b$Uc9yiuDvNXdSTJWk8$(1VfZ9B+rR8Ht^`z>01%Nx1x=|*bh@9frrY*H1O>9t5_bm<bXG%A;NpT12|ZdwS!E_D88qSYn$$y65#)5N=YNgSo0Z>!*%TTSnkk5H6#-=qB<5!+kKJU8`AiYecGzo$RR+G|X{`#A~O3dkW^#6GqLUV0;Kc*YL2%oE++TX7=d0+pE^AY6D3Wdl2LPqfGQaTkp1g6Lx0T+)7|gompODxU0QRZRhsZQlj%e@3$TWv{>bAcSh+lJo@|@;ybgMU7(%2|k&5%t<>=2BS0Ha4V&O)I-w4`(5O|IsY-Mb(h1$v%wHdgCrdIp7=y&H{zKbedf(z1X<r5?FTPXX0a^2?iGSfxI^U=jg;i<CYArF$NSA=RG2f!`!LJcV%#BReYOOjb}6jJo9K{GO(la%aP`V4#eLIAm-eSpebov?J&>t2dp@>rHt7|nScq97!~k#b3C?U9{61#x86g<Gqd~!7E7|@h#*|PDj@TpTMBAS^J~|Ey10R9K>k00AmXV$(v#-vDApPh(ENU~;>4rqqt0fFO&qv=67E0AbA#LbItg7-r`*j@}+8UW$6Av-L6N(sL-iH~^@VN*kTm1{A^B{DXNqJmFVbRZ{cc~i!A~mpl;Kzj8N#7#(&Earn5KVj6OJa|O#KjH}6>p;d%Q$As!c^uHn%zvKe9IJ5{spV=v9fr`w=DD^a5CSoYzVhyTOVYR_hHukZ*>vUL%%lP&2*I6vK%<++fe%y6MFtW=M&>_IRBPE0DvNz#s"
INTERNAL_B85 = "c-rlkYfzL`7{}jt!QE{sAuhV$C6<X)E;3wl2KGJAAJEC5nGy)BL<cvW2?l~jW7J6?$RY<Rf-S8OHSvRkfD($a0;4c$BTR(5l9ys+Qc-Slvk-mT&2akE^r?V3zi<CJ-~PYnJadj9{4;?ss>$hKKE-;K(uSuUAn&fF`8SM|vi&e!DVz&?gA<xBR?vI(jdVick5L+;MBi@Oe7}R9AMK#T(mbk<o1jp~JEYDv(E8TnEG<BZJd22d(>vIzb*1{Z996hpt-&%)0n3S~3l#=c5W3tTWRx+1^S=_jsD~1p^2y)3jDCuCKuPvW><>Fg%2SQB>Y6tk0$xY?<#y7n?x28Z1v)P2kS>l<^MPBG4<l_0DWG@{C2~saP<o-5UA?zQ%5_p9`okyDDSghKNiv5itiDC=drGjuu#uu(-bpSM$Enz7HnK_xX<<e5c2N`Ui*tiVc{U`wN;)^(NxLmx_^x^@s``GVbagKsSUN_FO}<#8oQ1AJdvqtYvW(<eG<S^>h8h*_Y}?DO*G%X|t8azXx5#}@IZ|tWXE(ntAXS-#)<!s^OP7EZkwx_W$$pA-*Fq3-aOJj%63QQtsWAkmiOqOb9HF24Rd6e+qj#%@X}R^jNBcS;wx@y3-_$Ej-fuab`=08o*Ir}ty-!FeP(TjWBIc<#;HfuK+A=%P$_41|-il-4XQ|SnfpB&?D*Li<U$n>g5m$`s0_c3~Y|?(D#5^}w9DVL8t8Md>1is&=Et&D2kLN)M(ZY4zr)+S^38F1(99~H9&Mjt6+Hp!YI^#|E3hGPU|JXO*@0|ad)w&CziqnA*Oaml;b&hx=GaIqKP@i`r5JA>=N9W%2l)F!sl01X433sV_qLtP<yGvC+>XF$#N~MJZd>&>PTa4SK{9QrV*`=@=Z=*7yj=mWPLg(cXiaFX!-|tDK=GvDK`A{Zv!5m~|n)G(27>M~IL_aU^2B$amJ|8oW>|l)Cb;K6~7s>WNDKUhgf7l+oj+y_=@lml@=>G(M^L&>3o?*OGEVD1qSoi%Q7c4Sc=wwSGn$!}8oadnDhcQZZj6}xZD|oGT9?ZY!&|+?7@~Jo|5*9!ay@b!hG-v2cIFqgZg$fruyksHe5fz0-y@1;*+~F7Dh_MfRn9%UZx5#~SIGkxj+m4Nrcx#Nrr5cEe6!d-;%WPTrEAxhCHWP+#nPBxT`)eSJDHyGcgM9N*7Oegs)U<@zvTYu0=e)5Q_P^DIOOt+WzT4>#oAht<o!qdP{r#Lb#^G@OEq?&+h@P("


def sha_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def sha_file(path: Path) -> str:
    return sha_bytes(path.read_bytes())


def unpack(encoded: str) -> bytes:
    raw = zlib.decompress(base64.b85decode(encoded))
    if len(raw) != 32 * 18 * 16:
        raise RuntimeError("embedded PF32 payload size drift")
    return raw


def reconstruct_source() -> bytes:
    width, height = 32, 18
    raw = bytearray(width * height * 16)
    points = (
        {(x, y) for y in range(2, 5) for x in range(2, 5)}
        | {(x, y) for y in range(9, 11) for x in range(13, 15)}
        | {(27, 14)}
    )
    for y in range(height):
        for x in range(width):
            if (x, y) in points:
                struct.pack_into(
                    "<4f", raw, (y * width + x) * 16, 1.0,
                    ((x * 4093 + y * 257) % 32769) / 32768.0,
                    ((x * 1237 + y * 3559) % 32769) / 32768.0,
                    ((x * 7919 + y * 911) % 32769) / 32768.0,
                )
    return bytes(raw)


def diff_rows(left: bytes, right: bytes) -> list[dict[str, object]]:
    rows = []
    for word, ((a,), (b,)) in enumerate(zip(struct.iter_unpack("<I", left), struct.iter_unpack("<I", right))):
        if a != b:
            rows.append({"word": word, "exported_bits": f"0x{a:08x}", "internal_bits": f"0x{b:08x}", "ulp": abs(a - b)})
    return rows


def live_identities() -> dict[str, str]:
    actual = {
        "production_source_sha256": sha_file(SOURCE),
        "aex_sha256": sha_file(AEX),
        "aexcompat_float_math_patch_sha256": sha_file(PATCH),
        "aexcompat_float_math_trace_patch_sha256": sha_file(TRACE_PATCH),
        "type1_closure_report_sha256": sha_file(TYPE1_REPORT),
        "type1_closure_generator_sha256": sha_file(TYPE1_TOOL),
    }
    mapped = {
        "production_source_sha256": EXPECTED["source"],
        "aex_sha256": EXPECTED["aex"],
        "aexcompat_float_math_patch_sha256": EXPECTED["patch"],
        "aexcompat_float_math_trace_patch_sha256": EXPECTED["trace_patch"],
        "type1_closure_report_sha256": EXPECTED["type1_report"],
        "type1_closure_generator_sha256": EXPECTED["type1_tool"],
    }
    if actual != mapped:
        raise RuntimeError(f"live identity drift: {actual!r}")
    return actual


def build() -> dict[str, object]:
    source = unpack(SOURCE_B85)
    exported = unpack(EXPORTED_B85)
    internal = unpack(INTERNAL_B85)
    if source != reconstruct_source():
        raise RuntimeError("embedded source no longer matches exact reconstruction")
    rows = diff_rows(exported, internal)
    histogram: dict[str, int] = {}
    for row in rows:
        key = str(row["ulp"])
        histogram[key] = histogram.get(key, 0) + 1
    type1 = json.loads(TYPE1_REPORT.read_text(encoding="utf-8"))
    if type1.get("controls", {}).get("strength290") != "excluded; diagnostic direct-owner counterexample only, never a public admission or closure row":
        raise RuntimeError("Strength-290 fail-closed authority drift")
    if "outer_strength == 290" in SOURCE.read_text(encoding="utf-8"):
        raise RuntimeError("Strength-290 appeared in production admission")
    atan2_left = [
        "00000000", "3f800000", "40000000", "40400000", "40800000", "40a00000",
        "40c00000", "40e00000", "41000000", "bf800000", "c0000000", "c0400000",
        "c0800000", "c0a00000", "c0c00000", "c0e00000", "c1000000", "c1100000",
    ]
    atan2_right = [
        "00000000", "3f800000", "40000000", "40400000", "40800000", "40a00000",
        "40c00000", "40e00000", "41000000", "41100000", "41200000", "41300000",
        "41400000", "41500000", "41600000", "41700000", "bf800000", "c0000000",
        "c0400000", "c0800000", "c0a00000", "c0c00000", "c0e00000", "c1000000",
        "c1100000", "c1200000", "c1300000", "c1400000", "c1500000", "c1600000",
        "c1700000", "c1800000",
    ]
    atan2_keys = sorted(f"{left},{right}" for left in atan2_left for right in atan2_right)
    if len(atan2_keys) != 576:
        raise RuntimeError("atan2f Cartesian key census drift")
    return {
        "schema": "olmradialblur.strength290-exported-math-boundary/1",
        "status": "PASS_LOCALIZED_HOST_MATH_BOUNDARY_STRENGTH290_REMAINS_FAIL_CLOSED",
        "identities": live_identities(),
        "fixture": {
            "pixel_format": "PF32_ARGB_FLOAT_LE",
            "width": 32,
            "height": 18,
            "rowbytes": 512,
            "bytes": len(source),
            "active_source_sha256": sha_bytes(source),
            "source_family": "opaque disconnected 3x3, 2x2, and 1x1 components on transparent black",
        },
        "parameters": {
            "blur_type": "Rotation_Type_2",
            "center": [16.0, 9.0],
            "outer_strength": 290,
            "outer_offset_mode": 1,
            "outer_offset": 0,
            "outer_edge_fade": 0,
            "inner_strength": 0,
            "inner_offset_mode": 1,
            "inner_offset": 0,
            "inner_edge_fade": 0,
            "repeat_border": 1,
            "ratio": 1.0,
            "angle_degrees": 0.0,
            "quality": 5.0,
            "brightness": 1.0,
            "size_variation": 25.0,
            "noise_variation": 100.0,
            "noise_type": 1,
            "seed": 1,
            "noise_offset": 0.0,
            "thickness": 10.0,
        },
        "owners": {
            "exported_smart_aexcompat_f32_math": {
                "worker_sha256": "fa0541ff62babf170fd8c53b6de21d6747b27c4e55eeec8270f68051dd4bf80d",
                "output_sha256": sha_bytes(exported),
                "bytes": len(exported),
                "returncode": 0,
                "render_error": 0,
                "guards_intact": True,
            },
            "aex_internal_owner": {"output_sha256": sha_bytes(internal), "bytes": len(internal)},
            "mac_typed_owner": {"output_sha256": sha_bytes(internal), "bytes": len(internal)},
            "exported_f64_to_f32_counterfactual": {
                "output_sha256": "5c70fe269db5c2923c1ce1a63645f83075975ab6b13eb34e09c240b999351f28",
                "bytes": 9216,
            },
        },
        "comparison": {
            "internal_equals_mac_typed": True,
            "exported_equals_internal": False,
            "different_words": len(rows),
            "ulp_histogram": histogram,
            "max_ulp": max(row["ulp"] for row in rows),
            "canonical_diff_sha256": sha_bytes(json.dumps(rows, sort_keys=True, separators=(",", ":")).encode()),
        },
        "actual_exported_call_census": {
            "trace_worker_sha256": "c77ec9d203b2ffd1124525e92f28aaa5ca5553166aaa2a0afe5f82488fca96fd",
            "raw_trace_sha256": "8544b8ea35e7055a136f27f93bdcf19a4071e4ba31d16edc6ad00a93e7058eec",
            "total_calls": 725,
            "log2f": {
                "calls": 149,
                "unique_inputs": 1,
                "input_bits": ["0x4f800000"],
                "host_substitute_result_bits": ["0x42000000"],
            },
            "atan2f": {
                "calls": 576,
                "unique_pairs": 576,
                "left_bits": ["0x" + value for value in atan2_left],
                "right_bits": ["0x" + value for value in atan2_right],
                "cartesian_product": True,
                "canonical_pair_digest": sha_bytes(json.dumps(atan2_keys, separators=(",", ":")).encode()),
            },
            "native_request_vectors": 577,
        },
        "boundary": {
            "aexcompat_head": "28d535469f84f67236ef3425afe4291ea2fb0991",
            "float_imports": ["atan2f", "log2f"],
            "host_substituted_float_math_is_not_native_windows_ucrt": True,
            "python_double_math_is_not_native_windows_ucrt": True,
            "native_windows_ucrt_capture_received": False,
            "native_after_effects_used": False,
            "network_state_changed": False,
            "production_admission_added": False,
            "installed_bundle_changed": False,
            "strength290_public_result": "PF_Err_BAD_CALLBACK_PARAM_before_iteration",
        },
    }


def markdown(value: dict[str, object]) -> str:
    comparison = value["comparison"]
    return (
        "# OLMRadialBlur Strength 290 exported math boundary\n\n"
        f"Status: `{value['status']}`.\n\n"
        "The exact PF32 32x18 fixture gives byte-identical output from the pinned AEX internal owner "
        "and the current Mac typed owner (`940c1e7e…`). The exported Smart route through an AE-free "
        "AEXCompat worker using Rust f32 `atan2f`/`log2f` produces `f8be3360…` instead: "
        f"{comparison['different_words']} float words differ, with ULP histogram "
        f"`{json.dumps(comparison['ulp_histogram'], sort_keys=True, separators=(',', ':'))}`. "
        "A double-to-float counterfactual produces a third hash, so "
        "neither host substitute is promoted as a Windows oracle. The exported call census is 149 "
        "`log2f` calls over one input plus 576 `atan2f` calls over a complete 18×32 argument grid "
        "(577 unique native request vectors). Native Windows UCRT output has not "
        "been captured. Strength 290 therefore remains fail-closed before iteration; production, the "
        "installed bundle, network state, and After Effects were unchanged.\n"
    )


def validate_persisted() -> None:
    expected = build()
    actual = json.loads(REPORT.read_text(encoding="utf-8"))
    if actual != expected:
        raise RuntimeError("persisted Strength-290 boundary drift")
    if MARKDOWN.read_text(encoding="utf-8") != markdown(actual):
        raise RuntimeError("persisted Strength-290 markdown drift")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()
    value = build()
    if args.write:
        REPORT.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        MARKDOWN.write_text(markdown(value), encoding="utf-8")
    validate_persisted()
    print(value["status"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
