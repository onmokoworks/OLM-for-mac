# OLM RadialBlur PF16 ellipse — 2026-08-11

Status: **exact**

Zoom/Rotationともに9×7/32×18の全6 tupleが全plane/output exactです。actual owner final planeのHDR値は保持され、PF16 typed writerがRGBのみ1.0上限へ飽和してからtruncateします。
