# OLM RadialBlur Size Variation × Edge Fade × Noise — 2026-08-11

Status: **24/24 consumed planes and typed output exact**

Rotation SV25のdiagnostic source-scalarには1 ULP差が残るため、その内部数値自体はexact範囲へ一般化しません。消費されるprepass・accum・max・final・typed outputはbyte exactです。
