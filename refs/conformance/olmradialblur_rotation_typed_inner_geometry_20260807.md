# OLMRadialBlur Rotation Inner typed geometry 境界（2026-08-07）

PF16／PF32 の非ゼロ Inner は、従来の 9×7 固定fixture専用guardから、同じ
actual-AEXアルゴリズムを使う寸法非依存のproduction経路へ移した。

## 完全一致を主張する範囲

- Blur Type: Rotation
- pixel format: native PF16 / PF32
- 入出力: 同じ正の寸法、各rowbytesはvisible byte数以上（padding可）
- Center: 各軸の整数除算による中央、Comp Width/Height: 入出力寸法と同一
- Outer Strength / Offset / Edge Fade: 0 / mode 1 / 0 / 0
- Inner Strength: 整数 1〜64、Offset mode 1、Offset 0、Edge Fade 0
- Repeat Border: on、Ratio: 1、Angle: 0、Quality: 5、Brightness: 1
- Size / Noise Variation: 0、Noise Type: 1、Layer: 0、Seed: 1、Offset: 0、Thickness: 10

64×36のpadded fixtureで、PF16／PF32それぞれStrength 3・33・64をactual
Windows AEXそのものへUnicorn/AEXCompatで入力し、polar、source scalar、accum、
max alpha、final RGBA、逆変換座標、typed outputをMac productionと
byte単位で比較する。出力row paddingも入力したsentinelを保持しなければならない。

さらに実用geometry代表としてPF16 640×360／padded rowbytes 5136／Strength 3を
同じ方法で実行し、全7境界とpaddingがbyte exactになった。追加証拠は
`olmradialblur_rotation_pf16_inner_640x360_20260807.json`。PF32 640×360はこの
証拠から一般化せず、64×36までを直接観測済み境界とする。

証拠JSONは
`refs/conformance/olmradialblur_rotation_typed_inner_geometry_20260807.json`、
再生成器は
`tools/emulation/test_olmradialblur_rotation_typed_inner_geometry_20260807.py`。

## fail-closeを維持する範囲

off-center、Comp寸法不一致、入出力寸法不一致、visible byte未満のrowbytes、
Inner 1〜64外、非ゼロOuter、offset／edge fade、repeat off、ratio／angle／quality、
brightness、noise／variationの未証明tupleはこの拡張に含めない。
runtime guard testはcenterずれ、Comp不一致、短rowbytes、出力寸法不一致を明示的に
`PF_Err_BAD_CALLBACK_PARAM`へ落とす。

これはoffline actual-AEX ownerとの完全一致であり、Windows AEまたはMac AE hostの
任意geometry一致を直接主張するものではない。

今回の検証はAEプロジェクトやoutput moduleを作成・変更していないため、別経路で
表示された「プロジェクト設定と出力色深度が異なる」警告とは無関係である。
Universal build、ad-hoc署名、MediaCoreへの単一bundle install、source/installed
binary hash一致は`olmradialblur_typed_inner_universal_install_20260807.json`に記録した。
