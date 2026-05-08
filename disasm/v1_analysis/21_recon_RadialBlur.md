# OLMRadialBlur Recon Report

## 1. プラグイン名 / メタ情報

- **プラグイン名**: `OLM RadialBlur` (FUN_18000b8e0 から特定)
- **AEGP ID**: `0x98000` (param[0])
- **フラグ**: `0x6008040` (param[0x18])
- **OutFlags**: `0x8001408` (param[100])
- **FloatSuite**: `0x62` が多用されている
- **UI パラメータ数**: `0x1f` = 31 個 (FUN_1800034c0 最終代入より)

## 2. AE Entry Point / Cmd Dispatch

### entryPointFunc 推定アドレス
- **FUN_18000bf00** - 大きな switch 文 (0〜10) を含み、パラメータ param_4[0] で分岐。これが entryPointFunc と推定。
- cmd 0: PLUGIN_SETUP? → `FUN_18000b9d0` (`(**(code**)(*plVar1+0x18))`)
- cmd 1: PLUGIN_ABOUT? → `(**(code**)(*plVar1+8))`
- cmd 2: PARAMS_SETUP? → `(**(code**)(*plVar1+0x20))`
- cmd 3: SEQUENCE_SETUP? → `(**(code**)(*plVar1+0x38))`
- cmd 4: SEQUENCE_RESETUP? → `(**(code**)(*plVar1+0x28))`
- cmd 5: RENDER? → `(**(code**)(*plVar1+0x30))`
- cmd 6/7: その他
- cmd 8: フラグ取得 (`(**(code**)(*plVar1+0x50))`)
- cmd 9: 何か設定 (`(**(code**)(*plVar1+0x58))`)
- cmd 10: 何か設定 (`(**(code**)(*plVar1+0x60))`)

### EffectBase vtable (FUN_18000b7c0)
- `EffectBase::vftable` をセット
- データハンドラ: `RampDataHandler`, `CurveDataHandler`, `StringDataHandler`

## 3. PARAMS_SETUP で作る UI Parameter 一覧

FUN_1800034c0 から抽出:

| # | Name | Type | Flag |
|---|------|------|------|
| 1 | Blur Type | POPUP (2 items: Zoom / Rotation) | 0x62 |
| 2 | Center | POINT (2D) | 0x60 |
| 3 | (Outer Blur) | FLOAT_SLIDER | 0x20 |
| 4 | Strength | FLOAT_SLIDER (0〜0x7d0) | 0x40 |
| 0x1c | Offset Mode | POPUP (3 items: Add/Max/Override) | 0x62 |
| 0x1d | Offset | FLOAT_SLIDER (-0x1f4〜0x1f4) | 0x40 |
| 5 | Edge Fade | FLOAT_SLIDER (0〜0x640) | 0x40 |
| 6 | (separator) | - | - |
| 7 | Inner Blur | FLOAT_SLIDER | 0x20 |
| 8 | Strength | FLOAT_SLIDER | 0x40 |
| 0x1e | Offset Mode | POPUP | 0x62 |
| 0x1f | Offset | FLOAT_SLIDER | 0x40 |
| 9 | Edge Fade | FLOAT_SLIDER | 0x40 |
| 10 | (separator) | - | - |
| 0x1a | Repeat Border | CHECKBOX | 0x62 |
| 0xb | Ellipse | FLOAT_SLIDER | 0x20 |
| 0xc | Ratio | FLOAT_SLIDER (0.0〜1.0) | 0x40 |
| 0xd | Angle | ANGLE | 0x60 |
| 0xe | (separator) | - | - |
| 0xf | Quality | FLOAT_SLIDER (0.0〜1.0) | 0x40 |
| 0x10 | Brightness/Gain | FLOAT_SLIDER | 0x40 |
| 0x11 | Size Variation | FLOAT_SLIDER (0.0〜1.0) | 0x40 |
| 0x12 | Noise Parameters | FLOAT_SLIDER | 0x20 |
| 0x13 | Noise Variation | FLOAT_SLIDER (0.0〜1.0) | 0x40 |
| 0x14 | Noise Type | POPUP (3 items: Smooth/Block/Layer) | 0x62 |
| 0x15 | Noise Layer | LAYER | 0x62 |
| 0x16 | (scale) | FLOAT_SLIDER (1〜100) | 0x40 |
| 0x17 | Offset | ANGLE | 0x60 |
| 0x18 | Thickness | FLOAT_SLIDER (0.0〜1.0) | 0x40 |
| 0x19 | (separator) | - | - |

## 4. RENDER Entry + 8-bit/16-bit 分岐

### Render Entry: FUN_1800040f0
- フレームバッファから `local_148` / `local_140` 取得
- `sVar1` (= depth) で分岐:
  - 8-bit (0x8) → **FUN_180007520**
  - 16-bit (0x10) → **FUN_180006d10**
  - 32-bit (0x20) → **FUN_180007d30**
- いずれも事前に `FUN_180008690` (パラメータ読み取り) + `FUN_180009360` を呼び出す

### 各 depth の render 内部構造 (関数内でさらに分岐)
パラメータ `param_5[4]` でアルゴリズム分岐:
- **1**: FUN_18000a7e0/a810 → FUN_1800056f0 (v2 系)
- **2**: FUN_180001a90/ac0 → FUN_180004640 (v1 系)

最終出力: FUN_180009d80 (8-bit/16-bit 共通 bilinear 書き出し)

## 5. Main Render Loop の高レベル構造

### 5-a) 事前計算フェーズ (FUN_180004640 / FUN_1800056f0 前半)
1. Gauss kernel の生成 → `FUN_18000b680`
2. カーネルサイズ計算 (品質に応じて)
3. ランダムオフセット生成 (`__drand__` → FUN_18001d060)
4. 各サンプル位置を polar 座標に変換 → FUN_180001b10 / FUN_18000a850

### 5-b) サンプリングフェーズ
- **FUN_180002780** (v1) / **FUN_18000b150** (v2): 各サンプル点を画像上に投影し、weighted accumulation
- **FUN_1800024c0** (v1) / **FUN_18000a9d0** (v2): Max-blend モード用の別 path
- 内部で bilinear サンプル (FUN_180001000/270/520/800/950 系) または 16-bit 版 (FUN_180009fc0/a270/a550/a6a0)

### 5-c) 正規化 + 書き出し
- Accumulation buffer を weight で除算
- Output dst にピクセル単位でコピー

**ループ構造**: スキャンライン単位 + スレッド分散 (`omp_get_max_threads` → ファンシーバンド)

## 6. 重要な Helper Functions (Top 10)

| # | Address | Name (推定) | 役割 |
|---|---------|-------------|------|
| 1 | `180001000` | bilinear_fetch | RGBA bilinear interpolation (4 tap) |
| 2 | `180001270` | bilinear_fetch_clamp | clamp付き bilinear |
| 3 | `180001520` | bilinear_fetch_wrap | wrap付き bilinear |
| 4 | `180001b10` | polar_to_pixel | 中心からの角度/半径計算 |
| 5 | `180001c90` | accum_line | 1本のサンプル線分を accumulation buffer に描画 |
| 6 | `180002780` | process_scan_v1 | v1 のメインスキャンフィルタ |
| 7 | `1800024c0` | process_max_v1 | v1 の Max-blend |
| 8 | `180002d30` | build_run | ランレングス圧縮データ構築 |
| 9 | `1800032a0` | mt19937_rand | Mersenne Twister 乱数 |
| 10 | `18000b680` | gauss_kernel | Gauss カーネル生成 |

## 7. 主要定数 (DAT_18002*)

| Symbol | Value | 用途 |
|--------|-------|------|
| `DAT_1800212d4` | 1.0f | 1.0 |
| `DAT_1800212d0` | 0.0f | 0.0 |
| `DAT_1800212d8` | 0.01745329252 | deg_to_rad (π/180) |
| `DAT_1800212e0` | 360.0 | deg |
| `DAT_1800212f0` | 0x80000000 | sign bit mask (abs用) |
| `DAT_1800215f8` | 3.0或0.005 | brightness scale |
| `DAT_180021600` | 1.0或0.0 | threshold |
| `DAT_180021608` | 32000.0 | サンプルレート変換定数 |
| `DAT_180021614` | 1.0f | default ratio |
| `DAT_180021624` | 5760.0 | カーネルサイズ基底 |
| `DAT_1800216cc` | 0.5f | 0.5 (catmull補間用) |
| `DAT_180021370/8` | 1.0/0xffffffff | 乱数スケール |

## 8. OLMSmoother v1/v2 との類似性

**類似点 (高い):**
- Polar 座標系でのカーディナルスキャンパターン
- Weighted accumulation + normalization の2pass構成
- 同一の bilinear fetch 関数群 (FUN_180001000, 270, 520)
- Mersenne Twister によるサンプルオフセット
- Gauss kernel 生成式 (FUN_18000b680)

**未確認:**
- 8-neighbor classifier は使われていない (bilinear一択)
- Curve eval class / string data handler はあるが smooth 用とは別

総合: **高類似度。v2 拡張方式が共通**

## 9. 移植難易度 Estimate

### **Medium〜Hard**

理由:
1. **関数数**: 100+ 関数、大規模コードベース
2. **深いコール階層**: entry → param read → render setup → accum → normalize
3. **AE SDK 依存**: PF_HandleSuite, PF_ParamUtilsSuite, AEGP Layer/Effect Suite に大きく依存
4. **Mersenne Twister**: 再実装 or 移植が必要
5. **SSE/AVX 的可能性**: movmskps 命令が出現 → SIMD 最適化が混入
6. **OpenMP**: `omp_get_max_threads()` → macOS では dispatch_apply 等に変換
7. **16-bit パス**: 別関数に分かれているが移植は素直
8. **3つの depth**: 8/16/32 すべて別関数 → テスト量増加

易しい点:
- アルゴリズム構造が明確
- 算術は float 主体で endian 問題少
- EXC_BAD_ACCESS の可能性は低い (clamp 多用)

## 10. 最初に着手すべき関数 3 つ

### ① `FUN_180004640` (v1 main render @ 180004640)
- **理由**: 最も大きなアルゴリズムコア。ここを動かせば全体の60%は完成。
- **内容**: サンプル生成、accumulation、normalization、書き出しの全行程

### ② `FUN_1800032a0` (Mersenne Twister @ 1800032a0) + `FUN_180003090/0f0` (init)
- **理由**: render で使用する random offset の唯一のソース。移植後は全出力が一致する。
- **移植方法**: 標準 C++ `<random>` の `std::mt19937` または Apple 標準 libc++ 実装に置き換え (ほぼ同一)

### ③ `FUN_180001000` (bilinear fetch @ 180001000) とその周辺 (270, 520, 800, 950)
- **理由**: 全 depth / 全アルゴリズムが呼ぶ最重要プリミティブ。
- **移植方法**: 4 float 入出力のシンプルな関数。単体テストで全パターン確認推奨。

### 推奨着手順
1. MT 乱数 (3f → 3f → 2a)
2. bilinear fetch 群 (000, 270, 520, 800, 950)
3. gauss kernel (b680)
4. v1 main (4640) → テスト
5. param read (8690) + param setup (4c0)
6. v2 main (56f0) → テスト
7. depth 分岐 (0f0 → d10/520/7d30)
8. 残りのユーティリティ