# OLMKiraKira Mode 2 Rotation 22° PF32 seam（2026-08-12）

Status: **fail_closed_pf32_seam**

5×3半透明source、Horizontal Length 7、Ramp ON、Merge2、Brightness Gain 0.73、Rotation 22°をactual exported ownerで追跡した。PF8/PF16はexact。PF32ではwarp前後を含むray 15 wordsがmax ULP 0で、最初の差はRamp aggregate glowの3 words（各1 ULP）、writer後はpixel 3 blueの1 wordだけ残る。

float/double、FMA、reciprocal、加算順の一般則は未回収のためproductionは変更せず、期待word補正も行わない。このtupleのPF32だけをfail-closeする。
