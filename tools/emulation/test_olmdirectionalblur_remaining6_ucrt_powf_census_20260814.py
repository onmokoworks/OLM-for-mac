#!/usr/bin/env python3
"""Freeze the actual exported-Smart DirectionalBlur powf call-key census."""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
from pathlib import Path
import struct
import zlib


ROOT = Path(__file__).resolve().parents[2]
REPORT = ROOT / "refs/conformance/olmdirectionalblur_remaining6_ucrt_powf_census_20260814.json"
MARKDOWN = REPORT.with_suffix(".md")
AEX = ROOT / "plugins_2025/OLMDirectionalBlur.aex"
SOURCE_PNG = ROOT / "refs/win_references/20260604_olm/OLMDirectionalBlur/case_0001_before_effects.png"
CEIL_PATCH = ROOT / "tools/emulation/aexcompat_olmdirectionalblur_double_ceil_import_20260814.patch"
RAW_PATCH = ROOT / "tools/emulation/aexcompat_raw_output_dump_20260814.patch"
TABLE_PATCH = ROOT / "tools/emulation/aexcompat_native_ucrt_table_replay_20260814.patch"
TRACE_PATCH = ROOT / "tools/emulation/aexcompat_ucrt_call_trace_20260814.patch"
CENSUS = ROOT / "tools/emulation/test_olmdirectionalblur_exported_smart_remaining6_census_20260814.py"

# zlib-compressed little-endian (input_u32, exponent_u32) pairs, sorted by key.
PAIR_DATA_B85 = (
    "c-mFjd01Cf9>?*MB0=Pi<WlxSTyPz7-?=KeQ0h<I_n+ptD`;9KjGh{EMa9%cDGPhdESN$cMW=MSYA&OWJDO{VT9_N5GR725bKjr&WBBLwe7@)0bMHO(+;e}=gE9a27i&y>``>kpDcix*RzP26G;L%l9uDg0Ss04G3K*z{*|qUxL$$}Ce}dYlqB|QiQqWnBsVkJzaLWf6^C`anna24N^S;)3_F>w7?0G=>2qqoXaVK>CTpgc}n+mYf6P-MdmBH#kxFi%mtL*8ts7AgTiCdyP-5hM1S(m!g1#b?)0vSFOmnPw^`MBmyJhuYV-@)uPSi08J*4{ww`2nVG#73LZFAKNfFEV6@r@w5D&M&if;=JAX(8Zv=*nFR-Z#bHJa{7LJaFFY2aEx5@q{fw{r!`MkG4CcGyoJF<nDP+oKE~vr&OFC*_=|i$*wbAVN{$ZmwB;&dkII-+h4$-JJ)Qdz<hP!|{j$!po`q3pX3BQ887B+P=g(sqAC8sJMB*Z8>*~7d;ja34p#g4)#+Hq7Q&a5MOyj?x>ymHC5pD629N8Y{qO+hQc|d1eBdf%sUq(A<y5X`oJR=|X;J$bDBnNttXQC;@j7IU~E`6}LFP6#}Kj!wsrxUPme{3*-akmd5Ck)0)!|>&i*jp|fg(0JHvYarUai&isADoPrr+DUFo2L7o&bs+Xh9y$ZlwFhboM$lJ(3!fQS-Q{Hu$N4I-7|aE9P&}wHCfj!e@xN*&eQXlujhkK70dbF!$2W^bLB0q-vzX{f7`Q?AD!W7K9%<{?;nfFHI{H(9GWb-U3OW9hvb1&j99MsKz_LbJEdU?+8XbWTjQNa%0H~ux?SVx>#|n!A~Vpw`Y!je^)Gr)(Dq!1pP&g{kKd!cg~4y9Q@<pidJik&)xd|IXV+xtcv-v=pZ`efXcOaJM^k?@hJ8YPDLNarkdLD2{weiZnR@TghGu!DHO$g_{VVl6G|fKe{ptFJ=0pA+-CX6C*?Qm67r9mI9c}D3t*7nUALWo8j8ku?#z(tH-c`N)SM=MCHfXoj8Jcmj`X22+xbCJ)zcPFE++;q^>bOtuiCic%W&VEL_zmumRSq!j0yHfS;wbqV+8fHV50R76oJ99G%xG|!`cMo>I70g(G{?}If0Fy4?I#oDXD4vsDb3qy##xFc2d%4oO!>6>-BUg2jP}Dbx(}I^tM3uo66L7#`0aT;pKr+}7|6P)^>rCvN4pL4id5frMeoN|jVt57<N5}n9ggN2I@R*XiRdOP$6urW?tF6F8}#3NL-Qe@ys7y|>;Im92|tj>pz~FMr@z82?Y~$M_9J<cbZ*ms0-9QPwLjcryxRA*56Y}UeMf)Ny8cP?B(vm%BJOW~k=9?4)+Gi?l@lM(&phNh%0ATl{0JKt^Pc{Q=ET4FK7>Ekdnp&m0<;@{CU5>(>#l@6L++3V(Y^L>-FK<JLo)F<+C%^Q+uk^1Q_y{cdF7t)wAttemm$}b1JIp|8H37FpAh6}wwCie9u@2vh(q&G20zJh<It=@y8)eC)$>)qDOZMY-rH!3(Wx9t_F?q}%3)98OXz=y8Kvk(hB59%bh<rFeF$FOTweV#DZT>ZjYij1URaUi)6n=UalR>NAE0}^GP!&etcPwiI!(|w0nKk}uUeIygf>n2Z{eO1!PUsE(D@SWF<Geg><GpyLQ}gsw#Ieo%6nz5OsK(egV2tUsj8==*;y0sqC2S;u7B3Epw)A<4?$~X=i1a0(ftt9N^pRAo^>frS=k)z9A#Hdjbxle8B&LN4aLWe(Md!*SNYG%>*cRej90EM#>qD^(5@c23p#scvFu%+aRxTvI;{Kz%?Y#@RG$^?St%85rmWJC{!P%1$HiF~c%b%Y8*$zQ8P%Bn9nf8-yjGq<r%n@|Pc#M`wCB)VNB4p1Ax)_dl+)2J#7dWy^W`(mFkUW0b4uP<y`-7u=?~<yXsX9xq>Pa*U%;{Gj#JJ+8{VAz>V-Bzu0nI8h2D#n%)@>(hcNIn`odaKk45W8=Y8cHYL9MBZYtYLznqPES?HWVa|;9g+fbj^4%5+;Z;!QPcbS4|%h7jA^@tASNHl%WPEvkdE|*`(J?Kv9NdIXa^?cEptNJGSWG8IXN#6l<(=cXOEbYTFX_<1mynv>y!}z@%y-!_e?~jLby6QaLn7>hImt$J7a-%qoUxe<tIIV*hJ=@Mh_kUi;KruR1yW?@Rcd@|f!MNMeUQ&+eiFf3ES+5u4x9O$#PsYhc@tijn?O=3{pnDX}W%(=K3V(_Iu`={!?1;{2<&|jCdo$h^blUaNK8A&Jl((ScqOSyPoxU2kua5I;Uqj!ae)M}ffm}I3-!pW^qq*Imes^%<#{+23L3>>0;$i<lzMt37ZXLvYZAa%InlXdP;X}w#Lvb;>@1iYIJ!qJIe@KfNuMGDrNky|>el3rpZ8-uRG%w24=xjpwlFUb6&5`tb4)Z!-{wTCF)P8pqt{hE$HM(czccZo5WO9J>ZXBcaJC=Gl+8Q!Owo>~nxfb1Za=-e`dxi0ip(&KB#(5^3AE)R2N9|v-+IYrkgm&9_?Q_bfFmO$|;Y9ksIZ^x2M6J_F<e`%_e^ba)rs(&_RNRS4Z%m`T0Nu9JY448a6$~URFHw7%a;-$q^9g7sCTibK!UZ#^ubZLoB4*c^$@!Yk)bo?YXe+$R{Y;ys--+lBo2`8o?Phsa-jelS(>^RSG0<a<es7@r%^W?~H?&Wq`55g<jOaX<+ynEzQVvPxxJ*2`N4aJS=WB{~G)}*V&VA|riQkVm&^DN-?<Lw~%sZm`33(CSE6O?Z@sTt(mVZHb#{LHkQ44("
)

CELLS = [
    {"depth": 8, "tuple_index": 2, "expf_calls": 166, "expf_unique": 107, "powf_calls": 7919, "powf_unique": 785, "raw_sha256": "636e649414ff0ad3968aabb97733dbb67f92900898829361b3f44c58758cfdb3"},
    {"depth": 16, "tuple_index": 2, "expf_calls": 166, "expf_unique": 107, "powf_calls": 7919, "powf_unique": 785, "raw_sha256": "4846a56aea99d2db6be3e56930a8ef1143394e89ca97e316d84a8ec165b4179d"},
    {"depth": 32, "tuple_index": 0, "expf_calls": 166, "expf_unique": 107, "powf_calls": 7919, "powf_unique": 785, "raw_sha256": "05989b2976a2056c738a2c41cf6c9ac39a3fcf8caa35eba4ca1d828fecb9fe19"},
    {"depth": 32, "tuple_index": 1, "expf_calls": 116, "expf_unique": 57, "powf_calls": 7919, "powf_unique": 785, "raw_sha256": "814ae4ec073d6e6ad4c83dea25227de5362d0ae6b8346d155c6aafe086149ac7"},
    {"depth": 32, "tuple_index": 2, "expf_calls": 166, "expf_unique": 107, "powf_calls": 7919, "powf_unique": 785, "raw_sha256": "453bbdf19955a3c6b91f2ca9b756e0d0aa9f2949b5855050636170a117039fc1"},
    {"depth": 32, "tuple_index": 3, "expf_calls": 216, "expf_unique": 107, "powf_calls": 7919, "powf_unique": 785, "raw_sha256": "3424989500b9b05791c1ce9e33e99fb810b5e3c63ad6b4e8c3897c6a2d832c09"},
]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def pairs() -> list[dict[str, str]]:
    data = zlib.decompress(base64.b85decode(PAIR_DATA_B85))
    if len(data) != 787 * 8 or hashlib.sha256(data).hexdigest() != "40e09eb7bedf2652389554fc2703d8327a90f86783ccbe804d6ddfff7040c425":
        raise RuntimeError("powf pair payload drift")
    rows = [
        {"input_bits": f"0x{left:08x}", "exponent_bits": f"0x{right:08x}"}
        for left, right in struct.iter_unpack("<II", data)
    ]
    if rows != sorted(rows, key=lambda row: (row["input_bits"], row["exponent_bits"])):
        raise RuntimeError("powf pair order drift")
    if len(set((row["input_bits"], row["exponent_bits"]) for row in rows)) != 787:
        raise RuntimeError("powf pair uniqueness drift")
    return rows


def identities() -> dict[str, str]:
    return {
        "aex_sha256": sha256(AEX),
        "source_png_sha256": sha256(SOURCE_PNG),
        "ceil_patch_sha256": sha256(CEIL_PATCH),
        "raw_output_patch_sha256": sha256(RAW_PATCH),
        "native_table_patch_sha256": sha256(TABLE_PATCH),
        "trace_patch_sha256": sha256(TRACE_PATCH),
        "remaining6_census_sha256": sha256(CENSUS),
    }


def build() -> dict[str, object]:
    rows = pairs()
    return {
        "schema": "olmdirectionalblur.remaining6-ucrt-powf-call-census/1",
        "status": "PASS_ACTUAL_EXPORTED_SMART_SIX_POWF_KEYS_CENSUSED_AE_FREE",
        "identities": identities(),
        "trace_worker": {
            "aexcompat_head": "28d535469f84f67236ef3425afe4291ea2fb0991",
            "combined_release_worker_sha256": "e0ac80cac6f94179cd5f42794cd042771d719bba7c299d212775c7b254e83382",
            "patch_order": ["ceil", "raw_output", "native_table", "ucrt_call_trace"],
        },
        "cells": CELLS,
        "calls": {
            "expf_occurrences": 996,
            "expf_unique_arguments": 107,
            "powf_occurrences": 47514,
            "powf_unique_pairs": 787,
            "powf_exponent_distribution": {"0x00000000": 2, "0x3f000000": 2, "0x40000000": 783},
            "all_six_exported_raw_exact": True,
        },
        "powf_pairs": rows,
        "powf_pairs_sha256": hashlib.sha256(json.dumps(rows, sort_keys=True, separators=(",", ":")).encode()).hexdigest(),
        "boundary": {
            "host_substituted_results_are_not_native_windows_ucrt": True,
            "keys_only_are_authoritative_for_native_request": True,
            "native_windows_return_received": False,
            "after_effects_launched": False,
            "network_changed": False,
            "original_557_row_batch_is_incomplete": True,
        },
    }


def validate(value: object, *, live: bool = True) -> bool:
    if not isinstance(value, dict) or set(value) != {"schema", "status", "identities", "trace_worker", "cells", "calls", "powf_pairs", "powf_pairs_sha256", "boundary"}:
        return False
    expected = build()
    if not live:
        expected["identities"] = value.get("identities")
    return value == expected


def note(value: dict[str, object]) -> str:
    return (
        "# DirectionalBlur remaining-six UCRT powf call census\n\n"
        f"Status: `{value['status']}`.\n\n"
        "The six pinned exported-Smart cells make 47,514 `powf` calls spanning 787 exact "
        "float32 input/exponent keys in addition to their Gaussian `expf` calls. All six host-substituted "
        "control outputs retain their pinned raw hashes, but those result words are not native Windows "
        "UCRT evidence. Only the call keys are promoted into the AE-free native request. Therefore the "
        "earlier 557-row batch is incomplete and must not be sent. AE and network state were unchanged.\n"
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    value = build()
    if not validate(value):
        raise RuntimeError("generated powf census invalid")
    if args.write:
        REPORT.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        MARKDOWN.write_text(note(value), encoding="utf-8")
    persisted = json.loads(REPORT.read_text(encoding="utf-8"))
    if not validate(persisted) or MARKDOWN.read_text(encoding="utf-8") != note(persisted):
        raise RuntimeError("persisted powf census drift")
    print(value["status"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
