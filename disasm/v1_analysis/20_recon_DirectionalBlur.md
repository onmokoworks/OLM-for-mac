# OLMDirectionalBlur - High-Level Architecture Recon

## 1. プラグイン名 / メタ情報

- **プラグイン名**: `OLMDirectionalBlur`
- **ファイル名**: `OLMDirectionalBlur.aex`
- **バージョン**: v1.0.0 (string から: 2番目)
- **説明文字列** (FUN_180008720 からの文字列インデックス):
  - 0: プラグイン名
  - 1: バージョン文字列 "v%d.%d.%d"
  - 2: 著作権行
  - 以降: パラメータ名 (Blur Length, Center, Angle, Angle2, Samples, Curvature, Radial Type など)
- **PI ID**: `DAT_18000efa0` (0x88800 を GlobalOutFlagsA に格納)

---

## 2. AE Entry Point (entryPointFunc @ 1800083f0) + CMD Dispatch

### Entry Point アドレス推定
**entryPointFunc** @ `0x1800083f0` が AE のエントリポイント。

### CMD ディスパッチ構造

| CMD | 呼び出し先 | 役割 |
|-----|-----------|------|
| 0 (PF_Cmd_GLOBAL_SETUP) | インライン処理 + FUN_180008740 | バージョン文字列設定 |
| 1 (PF_Cmd_GLOBAL_SETOUT) | インライン処理 + AEGP Utility Suite | プラグイン名登録 `"OLMDirectionalBlur"` |
| 4 (PF_Cmd_PARAMS_SETUP) | **FUN_180007310** | UI パラメータ設定 (21 パラメータ) |
| 0xb (PF_Cmd_SEQUENCE_SETUP) | 空 (何もしない) | |
| 0xe (PF_Cmd_SEQUENCE_RESETUP) | **FUN_180007eb0** | シーケンスリセット + AEGP ストリーム設定 |
| 0x17 (PF_Cmd_USER_CHANGED) | インライン処理 + FUN_180009740 | ユーザー UI 変更時のパラメータ反映 |
| 0x18 (PF_Cmd_RENDER) | **FUN_180007bd0** | メインレンダリング (8/16/32-bit 分岐) |

---

## 3. PARAMS_SETUP (FUN_180007310 @ 180007310) - UI パラメータ一覧

FUN_180008720 から取得する文字列で `strncpy` を使って名前を設定している。パラメータ順:

| # | パラメータID (local_e8[0]) | 型 (local_dc) | パラメータ名 (string index) | 備考 |
|---|---------------------------|---|-----------------------------|------|
| 1 | 1 | 3 (FLOAT_SLIDER) | index 3 | Blur Length (float, 0-1000?) |
| 2 | 2 | 10 (POINT_2D) | index 4 | Center (2D Point) |
| 3 | 3 | 2 (ANGLE) | index 5 | Angle (degrees) |
| 4 | 4 | 0xd (POPUP) | index 6 | Radial Type (popup) |
| 5 | 5 | 1 (SLIDER) | index 9 | Samples (int, 0-4000) |
| 6 | 6 | 1 (SLIDER) | index 8 | Curvature (int, 0-100) |
| 7 | 7 | 2 (ANGLE) | index 10 | Angle 2 (degrees) |
| 8 | 8 | 0xe (CHECKBOX?) | - | Edge Behavior? |
| 9 | 9 | 0xd (POPUP) | index 7 | Sampling Mode? |
| 10 | 10 | 1 (SLIDER) | index 9 | Samples (2) |
| 11 | 0xb | 1 (SLIDER) | index 8 | Curvature (2) |
| 12 | 0xc | 2 (ANGLE) | index 10 | Angle 2 (2) |
| 13 | 0xd | 0xe (CHECKBOX?) | - | |
| 14 | 0xe | 0xd (POPUP) | index 0xc | |
| 15 | 0xf | 2 (ANGLE) | index 0xb | |
| 16 | 0x10 | 7 (COLOR) | index 0xd | Color |
| 17 | 0x11 | 0xd (POPUP) | index 0xf | Composite Mode |
| 18 | 0x12 | 1 (SLIDER) | index 0x10 | Opacity (0-100%) |
| 19 | 0x13 | 3 (FLOAT_SLIDER) | index 0x11 | Intensity |
| 20 | 0x14 | 10 (POINT_2D) | index 0x12 | Center 2? |
| 21 | 0x15 | 0xe (CHECKBOX?) | - | |

**Important**: `param_6 + 0x20` に格納される値でレンダリングモードが判定される:
- `param_6[4] == 2` → 16-bit
- `param_6[4] == 3` → 32-bit (float)
- それ以外 → 8-bit (デフォルト)

---

## 4. RENDER Entry (FUN_180007bd0 @ 180007bd0) + Bit Depth 分岐

**FUN_180007bd0** が Render のエントリ。

### Bit Depth 分岐構造

```
FUN_180007bd0 (render entry)
  |
  +-- 8-bit (sVar1 == 8) → FUN_180004a20 (8-bit render path)
  +-- 16-bit (sVar1 == 0x10) → FUN_180003c90 (16-bit render path)
  +-- 32-bit float (sVar1 == 0x20) → FUN_1800057b0 (32-bit float render path)
```

それぞれの Render パスはほぼ同一構造:
1. パラメータスケーリング (解像度に応じて)
2. 処理領域計算 (padding 付きの拡張矩形)
3. 各色成分ごとに処理 (RGB + Alpha)
4. 重み付き方向性ブラー適用
5. 結果の後処理

---

## 5. Main Render Loop の高レベル構造

### 共通レンダリングパイプライン (各 bit depth)

```
1. 入力パラメータのスケーリング (解像度依存)
2. 処理領域の拡張 (blur margin を考慮)
3. 作業バッファの確保 (float RGBA × 拡張領域)
4. FUN_180001ec0 - 入力画像を角度分回転 (bilinear sampling)
5. FUN_1800018c0 - オプション: 追加の回転 (8-neighbor weighted sampling)
6. memcpy(src, dst, size * 16) - バッファコピー
7. エッジ検出 + 領域分割 (FUN_1800028e0 - 領域成長アルゴリズム)
8. マルチスレッド処理 (OpenMP):
   → 各スレッドで FUN_1800038d0 を呼ぶ
   → 内部で:
     a. 各ピクセルの色成分に対して方向性ブラー
     b. FUN_180001000 で前方方向のブラー
     c. FUN_1800013e0 で後方方向のブラー (alpha 重み付き)
9. 正規化 (alpha で除算)
10. 逆回転 (FUN_180001ec0)
11. 結果の後処理 (FUN_180006610/700/7f0)
12. リソース解放
```

### ピクセルレベル構造

- **Per-pixel**: 各ピクセルに対して方向に沿ったサンプリング
- **Weighted accumulation**: ガウシアン重み (FUN_180001830 で生成) + 距離減衰
- **8-neighbor bilinear**: FUN_1800018c0 で回転時の weighted bilinear sampling
- **Area segmentation**: FUN_1800028e0 で connected component 分析

---

## 6. 重要な Helper 関数 Top-10

| # | アドレス | 関数名推定 | 役割 |
|---|---------|-----------|------|
| 1 | `0x180001830` | `buildGaussianKernel` | ガウシアンカーネル生成 (sigma ベース) |
| 2 | `0x180001ec0` | `rotateImageBilinear` | 画像を角度分回転 (bilinear interpolation) |
| 3 | `0x1800018c0` | `rotateImageWeighted8` | 8-neighbor weighted 回転 (より高品質) |
| 4 | `0x180001000` | `accumulateDirection` | 前方方向の色累積 (weighted blend) |
| 5 | `0x1800013e0` | `accumulateDirectionRev` | 後方方向の色累積 (alpha 考慮) |
| 6 | `0x1800038d0` | `processScanlines` | スキャンライン単位の方向性ブラー適用 |
| 7 | `0x1800028e0` | `segmentRegions` | 領域分割 (connected components) |
| 8 | `0x180002590` | `fastRandom` | メルセンヌ・ツイスタ乱数生成 |
| 9 | `0x1800034e0` | `generateNoiseTexture` | ノイズテクスチャ生成 (perlin?) |
| 10 | `0x180003370` | `sampleBicubic` | バイキュービックサンプリング |

---

## 7. DAT_180_\* 定数の主要なもの

| アドレス | 値 | 用途 |
|---------|----|------|
| `0x18000b1e8` | `1.0f` | 定数 1.0 (正規化など) |
| `0x18000b1ec` | `0.5f` | 定数 0.5 (補間計算) |
| `0x18000b200` | `1.5` (double) | バッファサイズ拡張倍率 |
| `0x18000b208` | `2.328306437080797e-10` (double) | 乱数正規化係数 (1/2^32) |
| `0x18000b210` | `1.0` (double) | 定数 1.0 (double) |
| `0x18000b218` | `3.0f` | powf 指数 (ノイズ生成用) |
| `0x18000b220` | `2.0` (double) | 倍率 (ノイズ分布) |
| `0x18000b340` | `0.0` (double) | 閾値 0.0 |
| `0x18000b348` | `0.114f` (B) | BT.709 輝度係数 (B) |
| `0x18000b350` | `0.587f` (G) | BT.709 輝度係数 (G) |
| `0x18000b358` | `0.299f` (R) | BT.709 輝度係数 (R) |
| `0x18000b360` | `360.0` (double) | 角度変換 (degree→?) |
| `0x18000b370` | `270.0` (double) | オフセット |
| `0x18000b378` | `360.0` (double) | 正規化分母 |
| `0x18000b380` | `100.0f` | Intensity 正規化 |
| `0x18000b384` | `255.0f` | スケール (8-bit max) |
| `0x18000b388` | `255.0f` | (16-bit mode 用?) |
| `0x18000b390` | `0.5f` | fRadius 補正係数 |
| `0x18000b3b0` | `0x80000000` xor mask | 符号反転用 (角度反転) |

---

## 8. OLMSmoother v1/v2 との類似性

**判明した類似点**:

- **8-neighbor weighted sampling** (FUN_1800018c0): OLMSmoother v2 の "8-neighbor classifier" に類似
  - 4隅 + 4辺の重み計算を行い、bilinear weighted interpolation
- **方向性ブラー**: v2 の "方向性ぼかし" と同一コンセプト
  - 前方/後方の加重累積 (FUN_180001000 / FUN_1800013e0)
- **ガウシアンカーネル**: v1 の "ガウシアン畳み込み" と同じ
- **領域分割**: v2 の "cardinal scan + flood fill" に類似 (FUN_1800028e0)
- **OpenMP 並列化**: スキャンライン分割方式

**主な差異**:
- 回転テーブル (`FUN_180001ec0`) は OLMDirectionalBlur 固有の角度回転処理
- 複数の bit depth (8/16/32) をサポート
- より複雑な AEGP Suite インタラクション

**結論**: **高い類似性あり。特に v2 の core smoothing 技術を方向性ブラーに応用したもの。**

---

## 9. 移植難易度 Estimate

**Medium-Hard** (Medium～Hard)

### 理由
- **プラグインマネージャ**: AEGP Suite/PF Suite の多用 (移植時にラッパーが必要)
- **OpenMP**: `omp_get_max_threads()` 呼び出し → macOS では p_thread / GCD に置き換え
- **Mersenne Twister**: 移植は容易 (標準実装あり)
- **SIMD**: 現在の実装はスカラーのみの模様 → macOS では NEON に最適化可能
- **ガウシアン + 方向性ブラー**: 計算量多いが macOS の Accelerate Framework で高速化可能
- **リトルエンディアン**: x64 Windows ↔ ARM macOS でエンディアン問題なし
- **メモリ管理**: PF Handle Suite の代わりに macOS の CFAllocator 等で代替可能

---

## 10. 最初に着手すべき関数 3 つ (Literal Port 開始点)

### 1. `entryPointFunc` @ `0x1800083f0`
**理由**: エントリポイント。CMD ディスパッチの枠組み。全ての関数の呼び出し元。テストの基本。

### 2. `FUN_180001830` (buildGaussianKernel) @ `0x180001830`
**理由**: 最もシンプルな純粋計算関数。移植容易でテスト可能。expf とループのみ。成功体験を得られる。

### 3. `FUN_180001ec0` (rotateImageBilinear) @ `0x180001ec0`
**理由**: コア処理の中核。bilinear sampling + rotation。cosf/sinf の呼び出し。入出力が float* で明確。正確な移植で全体の品質が決まる。

**推奨順序**: 1 → 2 → 3 → テスト → `FUN_180001000` + `FUN_1800013e0` → 残りの pipeline