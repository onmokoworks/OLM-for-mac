以下が、提示された Ghidra 逆アセンブル結果 (x86_64→疑似C decomp) を基にした **render entry chain 完全 trace** と、**literal C++ への移植** です。不明点は明記します。

---

## 1. 全体 call graph 整理

```
FUN_1800096f0 (トップレベル: 色比較モード分岐)
  ├── [if 通常ビット] → FUN_180001400 (16bit色パス)
  └── [else / 特殊ビット] → FUN_1800011e0 (8bit色パス)

FUN_180001400 (16bit色 render entry)
  ├── FUN_1800069a0 (内部で color compare / blend を呼ぶ)
  │   ├── FUN_1800021f0 (16bit色比較: 輝度＋色差)
  │   ├── FUN_180001620 (16bit accumulator blend)
  │   ├── FUN_180001ed0 (16bit alpha blend, premul対応)
  │   └── FUN_180002740 (色選定と内挿決定)
  └── 最終出力: FUN_1800095b0 (仮定)

FUN_1800011e0 (8bit色 render entry)
  ├── FUN_1800068b0 (内部で color compare / blend を呼ぶ)
  │   ├── FUN_180002430 (8bit色比較: 輝度＋色差)
  │   ├── FUN_180001a90 (8bit accumulator blend)
  │   ├── FUN_180002060 (8bit alpha blend, premul対応)
  │   └── FUN_180002740 (色選定と内挿決定)
  └── 最終出力: FUN_180009470 (仮定)
```

---

## 2. 各関数の役割と C++ port

### 2.1 Color compare: `FUN_1800021f0` / `FUN_180002430`
- **役割**: 2つの色 (16bit or 8bit) の「距離」を計算。輝度差 + 色差 (重み付き) を組み合わせ、符号付き整数で返す。0 = 完全一致、非0 = 差の大きさ。符号は輝度の大小に基づく。
- **共通ロジック**:
  1. 輝度差 (絶対値)
  2. 色差 (RGB各チャンネルに重み `_DAT_18000d258` etc. を乗算) → 輝度で正規化 → 重み付き和
  3. 距離 = (輝度差 + Σ色差絶対値) >> 2  (平均的距離)
  4. 輝度差に基づく符号を付加
- **不明定数**:
  - `DAT_18000d250`: 1.0 / 32768.0f (16bit scale)
  - `DAT_18000d268`: 255.0f (8bit scale)
  - `_DAT_18000d258`: R重み (0.299?)
  - `_DAT_18000d25c`: G重み (0.587?)
  - `_DAT_18000d254`: B重み (0.114?)
  - `DAT_18000d270`: 0x7FFF (16bit) / 0xFF (8bit) のマスク定数

```cpp
// FUN_1800021f0 equivalent
int compareColor16(const uint16_t* c1, const uint16_t* c2) {
    if (!c1 || !c2) return 0;
    if (c1[1] == c2[1] && c1[2] == c2[2] && c1[3] == c2[3] && c1[0] == c2[0]) return 0;

    int lumadiff = (int)c1[0] - (int)c2[0];
    float sr = (float)c1[0] * (1.0f / 32768.0f);
    float dr = (float)c2[0] * (1.0f / 32768.0f);

    // weighted color difference (luminance-normalized)
    float X = ((float)c1[1] * sr * wR + (float)c1[2] * sr * wG + (float)c1[3] * sr * wB)
            - ((float)c2[1] * dr * wR + (float)c2[2] * dr * wG + (float)c2[3] * dr * wB);

    int abslumadiff = (lumadiff ^ (lumadiff >> 31)) - (lumadiff >> 31);
    int absRd = (int)((float)((int)((float)c1[1] * sr - (float)c2[1] * dr) & 0x7FFF));
    int absGd = (int)((float)((int)((float)c1[2] * sr - (float)c2[2] * dr) & 0x7FFF));
    int absBd = (int)((float)((int)((float)c1[3] * sr - (float)c2[3] * dr) & 0x7FFF));

    int dist = (int)((float)abslumadiff + (float)(absRd) + (float)(absGd) + (float)(absBd));
    dist = ((dist >> 31) & 3) + dist >> 2; // divide by 4 with rounding toward zero
    if (dist == 0) dist = 1;

    float Xabs = (X <= 0.0f) ? floorf(X) : ceilf(X);
    int Xint = (int)Xabs;
    int Xabsint = (Xint ^ (Xint >> 31)) - (Xint >> 31);
    if (dist < Xabsint) dist = Xabsint;
    if (Xint < 1) dist = -dist;
    return dist;
}
```

```cpp
// FUN_180002430 equivalent (8bit)
int compareColor8(const uint8_t* c1, const uint8_t* c2) {
    // 同様; 定数 1.0f/255.0f とマスク 0xFF を使用
}
```

### 2.2 Accumulator blend: `FUN_180001620` / `FUN_180001a90`
- **役割**: 複数の色サンプル（最大9個？）を重み付き平均し、最終的な色を計算。サンプルは`param_1`のオフセット-2, -1, 0 (ポインタ配列) から取得。
- **ループ**: 0..6 を3個ずつ処理 (i=0,3,6)。各グループで3つのサンプル (null可) を加算。
- **重み**: カウント (`DAT_18000d1f4` = 1.0f?) と輝度比例の重み (`fVar16 = 輝度 * scale`)。
- **平均**: 総和 / 総重み。色成分は輝度で正規化。
- **クランプ**: 16bit 0x8000 / 8bit 0xFF。
- **不明点**: `DAT_18000d1f4` は 1.0f と仮定。`DAT_18000d250` は 1/32768, `DAT_18000d268` は 1/255。

```cpp
// FUN_180001620 (16bit)
void blendAccumulator16(uint16_t* dst, const SomeContext* ctx, int param3) {
    // ctx->samples: uint16_t*[9] at offsets -2, -1, 0, pos+3 ...
    const uint16_t** samples = (const uint16_t**)((uintptr_t)ctx + 0x10); // array of pointers
    const uint16_t* base = *(const uint16_t**)((uintptr_t)ctx + 0x20); // reference sample

    float sumWeight = 0.0f;
    float sumA = 0.0f;
    float sumR = 0.0f, sumG = 0.0f, sumB = 0.0f;

    int idx[9] = {-2, -1, 0, 1, 2, 3, 4, 5, 6}; // Ghidraではループ内で-2,-1,0を参照
    for (int i = 0; i < 9; i += 3) {
        // start compute...
    }
    // ... (同上のループ)
    // 結果をdstに書き込み、輝度で色を正規化、0x8000クランプ
}
```

### 2.3 Alpha blend: `FUN_180001ed0` / `FUN_180002060`
- **役割**: 前景色と背景色を alpha blending。premultiplied alpha を前提。
- **式**:
  - `out_A = src_A * f_src + dst_A * f_dst` (clamp 0..1)
  - `out_R = (src_R * f_src * src_A + dst_R * f_dst * dst_A) / out_A`
  - 同様に G, B
- **プリマルチ**: 入力は premultiplied と仮定 (rgb * a)。出力も premultiplied。

```cpp
void blendAlpha16(const uint16_t* src, float f_src,
                  const uint16_t* dst, float f_dst,
                  uint16_t* out) {
    float sa = src[0] / 32768.0f;
    float da = dst[0] / 32768.0f;
    float a = sa * f_src + da * f_dst;
    a = clamp(a, 0.0f, 1.0f);
    out[0] = (uint16_t)(a * 32768.0f);

    float sr = clamp((src[1] * f_src * sa + dst[1] * f_dst * da) / a, 0.0f, 1.0f);
    // ... G, B
    out[1] = (uint16_t)(sr * 32768.0f);
    // ...
}
```

### 2.4 Color selection: `FUN_180002740`
- **役割**: 複数の基準色 (puVar1,3,13,14) と現在色 (puVar2) を比較し、最も適切な内挿方向を決定。出力: 内挿先 (x,y) とフラグ。
- **ロジック**:
  - `param_14` (モード) が 0 なら完全一致判定、非0なら閾値 (`iVar18 = param_14 << 7`) 距離判定。
  - 比較関数 `compareColor16` で距離が iVar18 未満なら「類似」とみなす。
  - 各基準色に対して `FUN_180009960` (おそらく最近傍サンプリング) で補間点を計算し、最適なものを選択。
- **C++シグネチャ**:
```cpp
void selectBlendColor(
    void* context,
    longlong param2,
    uint param3, uint param4, uint param5,
    uint32_t* pOut,       // param6: 結果フラグ (0=no change,1=interpolate,2=direct,3=exact)
    uint8_t* outFlag1,    // param7
    uint8_t* outFlag2,    // param8
    uint32_t* x1, uint32_t* y1, // 内挿開始
    uint32_t* x2, uint32_t* y2, // 内挿終了
    uint32_t* x3, uint32_t* y3  // 第3点 (未使用?)
);
// 不明な点: 多くのポインタの正確な構造は要 Ghidra 確認
```

---

## 3. FUN_1800096f0 の制御フロー

```
Entry (top-level render)
if (param_4->flags & 1) == 0:  // 通常パス
    setup local variables (color source, bias)
    call FUN_180001400 (16bit)
else:  // 特殊パス (例えば輝度変換)
    setup local variables (色変換)
    call FUN_1800011e0 (8bit)
```

---

## 4. 補足説明

- **16bit vs 8bit**: すべての関数にペアが存在。内部定数 (スケール、マスク) のみ異なる。
- **`DAT_18000d250` / `DAT_18000d268`**: `1.0 / 32768.0` (16bit) と `1.0 / 255.0` (8bit) の逆数。
- **`FUN_180009960`**: 不明な補助関数。座標変換かサンプリング。実装未確認。
- **`FUN_1800069a0` / `FUN_1800068b0`**: 内部で compare / blend を呼ぶループ関数。正確な構造は decomp が不十分なので要 Ghidra 確認。
- **`FUN_180002740` の戻り値**: `*param_6` が `0,1,2,3` で動作を選択。

---

## 5. 未確定事項 (要 Ghidra 確認)

1. `FUN_1800069a0` / `FUN_1800068b0` の完全なロジック (ループ回数、サンプル選択)
2. `FUN_180009960` の動作 (最近傍探索? バイリニア?)
3. 定数 `_DAT_18000d258`, `_DAT_18000d25c`, `_DAT_18000d254` の正確な値 (RGB輝度重み)
4. `DAT_18000d1f4` は `1.0f` と仮定するが、確認必要
5. 8bit版の `compareColor8` のマスク値 (`DAT_18000d270`) は `0xFF` か?

以上が、decomp に基づく厳密な trace と C++ 移植案です。