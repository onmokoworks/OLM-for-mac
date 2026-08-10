# OLM RadialBlur PF32 Rotation ellipse — 2026-08-11

Status: **exact**

Ratio 2/5 × Angle 0/30/90 の6セルについて、forward polarからRotation worker、inverse coordinates、padded PF32 outputまでactual AEXとbyte-exactです。Angle setupはZoomと共通ですが、Rotationのellipseは `(radius * ratio) * sin(theta)` のfloat順です。
