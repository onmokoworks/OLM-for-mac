# OLM RadialBlur Rotation typed Edge Fade 32x18 — 2026-08-11

Status: **exact** (12/12). PF8/PF16/PF32のOuter/Inner Fade 50/100は、polar、source scalar、accum、max alpha、final RGBA、coordinates、outputでbyte一致しました。prepass alphaはactual側で取得済みですが共通production harnessがexportしないため比較対象外です。以前のPF32 Inner残差はwrapperがStrength 4をStrength 0へ上書きしていたactual harness設定不備であり、アルゴリズム差ではありません。
