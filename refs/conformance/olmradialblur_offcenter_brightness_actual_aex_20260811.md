# OLM RadialBlur off-center × Brightness — 2026-08-11

Status: **exact** (36/36)

中心を基準から幅・高さの±1/4ずらした3象限とBrightness 0.5/1/2をpairwise化し、Zoom/Rotation、PF8/PF16/PF32、9×7/32×18でactual ownerの内部planeとtyped outputを比較しました。Brightnessは正規化RGBへ乗算後、RGBのみ1.0へ上限clampし、alphaには適用しません。PF32 Zoom gain 2の未clamp first witnessは `(x=4,y=0,B)` のactual `1.0` 対production `1.230492115` でした。第四象限、画面外中心、その他の値は証拠範囲外です。
