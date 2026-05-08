# OLMSmoother2 Mac port — gap analysis vs Win disassembly

生成: 2026-04-20 セッション
対象: `Mac/OLMSmoother2_port.cpp` (918 行) と Win aex の Ghidra デコンパイル

## 1. DAT 定数テーブル (`.rdata` @ 0x180022dc0..)

| RVA | float32 | 用途 |
|---|---|---|
| 0x22dc0 | 3.0 | |
| 0x22dc4 | 6.0 | |
| 0x22dc8 | 10.0 | |
| 0x22dcc | 15.0 | |
| 0x22dd0 | **100.0** | slider 除数 (smoothness, extra_smooth とも) |
| 0x22dd4 | **0.125** | polygon helper の基本ステップ |
| 0x22dd8 | **0.2**   | helper 内 sub-step (例: FUN_180013570) |
| 0x22ddc | 0.25 | |
| 0x22de0 | 1.5 | |
| 0x22de4 | 2.0 | |
| 0x22de8 | **0.4**   | helper 内コーナー重み (例: FUN_1800134c0) |
| 0x22dec | 0.0 | |

**port の齟齬**: 現行 `build_polygon` は 0.125 を使わず独自の 0.5 + 0.25*extra を採用。これが「Win と AA 形状が一致しない」主要因の一つ。

## 2. FUN_18000c280 (polygon builder) の分類ロジック

Ghidra より:

```
switch_val = (iVar3 + uVar9 + ((!bVar16 + uVar7*2) * 4)) * 0x10
           + iVar4 + (local_1b7==0) + iVar11 + iVar10
```

- 下位 4 bit: 「現在のピクセル2×2ブロック」の 4 バイトアルファ (0 なら透明フラグ立てる)
  - bit3=local_1b5, bit1=local_1b6, bit0=local_1b7, bit2=local_1b8
- 上位 4 bit: 周辺1ピクセルのコンテキスト (東隣, 南東隣, 南南東隣, 南西隣)

⇒ **現行 port の 8-近傍エミッタ (N/S/E/W/NE/NW/SE/SW の全部走査) はトポロジーが違う**。
Win は 2×2 セル単位での Marching Squares で、判定軸は 4+4=8 ビット index (0..0xFF, 256 ケース) になる。

実使用ケースは 222 個 (`disasm/OLMSmoother2_case_map.txt` にマップを保存済)。
残り 34 ケースは `goto switchD_18000c530_caseD_2` に落ちる (= 不要/対称で既処理)。

## 3. 21 個のヘルパ関数

| helper | Ghidra 行数 | 想定形状 |
|---|---|---|
| FUN_18000cc70 | 22 | 正規化 (各頂点 w を count で割る) |
| FUN_1800105f0 | 31 | |
| FUN_1800106b0 | 32 | |
| FUN_180010760 | 31 | |
| FUN_180010820 | 31 | |
| FUN_180011030 | 121 | |
| FUN_180011300 | 116 | |
| FUN_1800115a0 | 194 | 大型 (複合形状) |
| FUN_1800119a0 | 178 | 大型 |
| FUN_180011d80 | 123 | |
| FUN_180012040 | 114 | |
| FUN_1800122e0 | 136 | |
| FUN_1800125c0 | 112 | |
| FUN_180012c20 | 30 | 単純 (軸沿い頂点追加) |
| FUN_180012ce0 | 30 | 単純 |
| FUN_180012da0 | 66 | |
| FUN_180012f60 | 70 | |
| FUN_180013140 | 65 | |
| FUN_1800132f0 | 69 | |
| FUN_1800134c0 | 29 | コーナー 3 点追加 (0.4 と 0.2) |
| FUN_180013570 | 29 | 対称コーナー 3 点追加 |

合計 ~1629 行。ロジック自体は座標オフセット + weight の定数で出来ていて、
ベースは `FUN_1800104d0(poly, &grid_ij, weight)` — 既存頂点バッファにグリッド座標と
coverage を push するアペンダ。

**polygon 構造** (FUN_1800104d0 で判明。`undefined8 local_148[30]` = 240 B):

| offset | field | 出所 |
|---|---|---|
| +0x00 | `float* plane_base` | param_1[0] = source_plane base |
| +0x08 | — | param_1[1] (未解析) |
| +0x10 | `longlong row_stride_bytes` | param_1[2] |
| +0x18..0x1F | — | |
| +0x20 | `int bound_x` | (image width − 1) 相当 : FUN_180012ce0 `param_1[4]+-1` 比較用 |
| +0x24 | `int bound_y` | (image height − 1) 相当 : FUN_180012c20 `+0x24+-1` |
| +0x28..0x2F | — | |
| +0x30 | `int cur_x` | 現在の出力ピクセル X (integer grid) |
| +0x34 | `int cur_y` | 現在の出力ピクセル Y |
| +0x38 | `float base_weight` | slider * magnitude — helper 呼出時の前倒し係数 |
| +0x40 | `vertex[0]` (20 B: R, G, B, A, w) | FUN_1800104d0 が書き込み |
| … | vertex[1..11] | |
| +0x130 | `longlong count` | poly[0x26] |

**FUN_1800104d0(poly, int grid_ij[2], float w)** の挙動:
```
ptr = poly->plane_base + grid_ij[1]*row_stride + grid_ij[0]*16  // 16B/px float RGBA
vertex[count++] = { ptr[0], ptr[1], ptr[2], ptr[3], w }           // nearest-neighbor サンプル
```
⇒ bilinear ではなく **整数グリッド nearest-neighbor** サンプリング。

## 3.1 コーナー helper 4 個 (最小サイズグループ) 完全解析

| helper | 想定コーナー | guard | 追加 3 頂点 (Δ) / 重み倍率 |
|---|---|---|---|
| FUN_1800134c0 | 左上 (NW) | cur_x>0 && cur_y>0 | (−1, 0), (−1, −1), (0, −1) / 0.4, 0.2, 0.4 |
| FUN_180013570 | 右上 (NE) | cur_x<bound_x−1 && cur_y>0 | (0, −1), (+1, −1), (+1, 0) / 0.4, 0.2, 0.4 |
| FUN_180012c20 | 左下 (SW) | cur_x>0 && cur_y<bound_y−1 | (−1, 0), (−1, +1), (0, +1) / 0.4, 0.2, 0.4 |
| FUN_180012ce0 | 右下 (SE) | cur_x<bound_x−1 && cur_y<bound_y−1 | (0, +1), (+1, +1), (+1, 0) / 0.4, 0.2, 0.4 |

共通: `w = passed_f * base_weight * {0.4 or 0.2}`, passed_f は呼出時に `DAT_180022dd4 = 0.125` を渡す。
⇒ 例えば case 0x00 の4連鎖 `FUN_1800134c0 → FUN_180013570 → FUN_180012ce0 → FUN_180012c20` は
4コーナー全てに L 字 3頂点を配置する「全周スムーズ」パターン。

## 3.2 cc70 = 正規化

```c
void FUN_18000cc70(poly) {
    n = poly->count
    for i in 0..n-1:
        poly->vertex[i].w /= n
}
```
⇒ **dispatch の末尾 or 途中に挟まれる正規化ステップ**。case 0x0c..0x0f や 0x22..等で出現。

## 3.3 classification plane の読み取り (FUN_18000c280 先頭)

`param_3` は **u8 RGBA 4-byte/pixel** プレーン (stride 4B)。
`local_1b5..8` = 現ピクセルの R/G/B/A 4 バイト → 各バイトを `== 0` 判定して 4 ビットの下位 nibble を作る。
⇒ key_test ステージが float 経路とは別に **u8 4-channel 分類プレーンを書き出している**
   (どの stage が書くかは未特定 — FUN_180002930 は float 経路のみ)。
   8bpc 描画ルート (line 1391 caller, `uVar8*4` 出力) ではこのプレーンが直接使える。

## 4. その他の未達

- **`win_FUN_180002930_key_test`**: 1b5..1b8 は 4 *バイト* を独立アルファ判定に使っている。
  Win の key_test は **RGBA 4 バイト中に 4 つの独立した分類フラグ** を書き込んでいる可能性。
  → 現 port の「アルファだけ」書き込みでは下位 4 bit の分類が機能しない恐れ。要再確認。
- **FUN_180004c30 (user gamma LUT)**: port は stub (未使用)。gamma_mode!=0 かつ runtime LUT がある場合のみ呼ばれるので AE 側の入力次第。
- **4 種 attenuation 曲線**: 未特定。orchestrator 内の係数計算と照合して列挙予定。

## 5. 次セッションの手順 (優先順)

1. `key_test` (FUN_180002930) の出力 4 バイトの意味を disasm から特定 → port 側で同じ 4 分類を書き込む
2. `SmootherPolygon` を Win レイアウト (grid_x, grid_y, base_w, count, verts) に拡張
3. 小型 helper 5 個 (cc70, 134c0, 13570, 12c20, 12ce0) を忠実移植 — 再現テストの土台
4. 222-case dispatch を (case_map から) 自動生成して switch 置換
5. 中型/大型 helper (~170 行超) は個別精査
