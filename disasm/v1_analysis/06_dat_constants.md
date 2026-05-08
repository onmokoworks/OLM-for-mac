以下が、提供された DECOMP 全体から抽出した `DAT_180_*` シンボルの完全な audit 表です。

| address | usage 推定 (multiplier/threshold/scale/divisor等) | 出現箇所 (関数名) | 文脈ヒント |
|---|---|---|---|
| DAT_18000d1f0 | blend factor / threshold (値は 1.0f か 0.0f 近辺の定数) | FUN_180001ed0, FUN_180002060, FUN_180004450, FUN_1800047f0, FUN_180004b80, FUN_180005570, FUN_180005f60, FUN_180006270 | FUN_180001ed0/func_180002060: 色ブレンドの重みとして `param_2`/`param_4` と共に使用。FUN_180004b80/func_180005570: `DAT_18000d1f0` を 1.0f として除算・減算に使用。カラー lerp の end weight。 |
| DAT_18000d1f4 | accumulator / counter / iteration increment (値は 1.0f か 0.0f 近辺) | FUN_1800010e0, FUN_180001110, FUN_180001620, FUN_180001a90, FUN_180004b80, FUN_180005570, FUN_180005f60, FUN_180006270 | FUN_1800010e0/func_180001110: `param_2 == DAT_18000d1f4` で分岐。FUN_180001620/func_180001a90: ループ内で `fVar18 = fVar18 + DAT_18000d1f4` として重み和のカウンタ。FUN_180004b80/func_180005570: `fVar19 = DAT_18000d1f4 / fVar23` 等、1.0f として除算に使用。 |
| DAT_18000d250 | scale factor for ushort pixel (値は 1/65535.0f か 1/32768.0f 近辺) | FUN_180001620, FUN_1800021f0 | FUN_180001620: `(float)*puVar4 * DAT_18000d250` として ushort ピクセル値を正規化。FUN_1800021f0: `(float)*param_1 * DAT_18000d250` として ushort 値を正規化 (16bit→float normalization)。 |
| DAT_18000d254 | Luma coefficient for B (blue) | FUN_1800021f0 | `_DAT_18000d254` として `(float)param_1[3] * fVar5 * _DAT_18000d254` で使用。輝度計算用。 |
| DAT_18000d258 | Luma coefficient for R (red) | FUN_1800021f0 | `_DAT_18000d258` として `(float)param_1[1] * fVar5 * _DAT_18000d258` で使用。輝度計算用。 |
| DAT_18000d25c | Luma coefficient for G (green) | FUN_1800021f0 | `_DAT_18000d25c` として `(float)param_1[3] * fVar5 * _DAT_18000d25c` で使用。輝度計算用。 |
| DAT_18000d260 | divisor for smoothness falloff (値は 2.0f か 3.0f 近辺) | FUN_180004b80, FUN_180005570 | `fVar22 / (fVar23 * _DAT_18000d260 - DAT_18000d1f0)` として使用。falloff カーブの調整。 |
| DAT_18000d264 | multiplier for step size / iteration count (値は 0.5f か 1.0f 近辺) | FUN_180004b80, FUN_180005570 | `fVar23 = DAT_18000d264` と代入し、`fVar24 = DAT_18000d1f4 / (fVar21 * DAT_18000d264)` 等で使用。 |
| DAT_18000d268 | scale factor for byte pixel (値は 255.0f) | FUN_180001a90, FUN_180002060, FUN_180002430 | FUN_180001a90: `(float)*pbVar5 / DAT_18000d268` として byte ピクセル値を正規化。FUN_180002060/func_180002430: `(float)*param_3 * fVar6 / DAT_18000d268` として byte 値を正規化。 |
| DAT_18000d26c | max clamp for ushort blend (値は 32768.0f か 65535.0f 近辺) | FUN_180001ed0 | `fVar5 = DAT_18000d26c` と代入し、`if (DAT_18000d26c < fVar3) fVar5 = DAT_18000d26c` として ushort 値の上限クランプ。 |
| DAT_18000d270 | bitmask for diff (0xffff か 0xff 近辺) | FUN_1800021f0, FUN_180002430 | `(uint)((float)param_1[1] * fVar5 - (float)param_2[1] * fVar6) & DAT_18000d270` として差分をマスク。絶対値計算の一部。 |
| DAT_18000d268 | (再掲) scale factor for byte pixel (255.0f) | FUN_180001a90, FUN_180002060, FUN_180002430 | 上記参照。byte チャンネルの正規化に使用。 |

**備考:**
- 値が不明な定数については、Ghidra のデータ型解析（`Set Data Type` → `float`）で実際の数値を確認してください。
- `DAT_18000d254`, `_DAT_18000d258`, `_DAT_18000d25c` は、USHORT 版 `FUN_1800021f0` でのみ使用される輝度係数と思われます（BT.601 か BT.709 近辺）。
- `DAT_18000d270` は 16bit/8bit 符号なし絶対値計算のためのビットマスクです（例: `0xFFFF` か `0xFF`）。
- `DAT_18000d260` は smoothness falloff カーブの分母補正に使われます。