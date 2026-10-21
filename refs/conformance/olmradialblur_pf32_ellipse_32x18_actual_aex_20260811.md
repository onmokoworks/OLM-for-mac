# OLM RadialBlur PF32 ellipse 32×18 — 2026-08-11

Status: **exact**

ZoomとRotationのRatio 2/5 × Angle 0/30/90を、center `(16,9)`、rowbytes 528の32×18 worldで比較し、全plane byte-exactを確認しました。9×7で確定した各モード固有のfloat演算順を、centered same-shape PF32 geometryへ一般化します。
