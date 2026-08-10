# OLM RadialBlur Inner Offset pairwise — 2026-08-11

Status: **exact** (48/48)

Zoom/Rotation、PF8/PF16/PF32、9×7/32×18で、Inner Strength 4、Offset Mode 2/3、UI Offset 2/4をactual AEX内部planeとtyped outputで比較しました。Zoomは列挙範囲でStrength 4 worker結果を維持します。RotationはUI offsetを1減算後に半径依存でscaleし、Mode 2は固定spanとのmax、Mode 3は動的spanを直接使用します。列挙外はfail-closeです。
