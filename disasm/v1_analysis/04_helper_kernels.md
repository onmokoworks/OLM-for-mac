## 3 Helper Kernel 比較解析

### 1. 各 Kernel の役割の推定

**FUN_180004b80 (param_6 == 0/1/2/3):**
- **param_6 == 0**: 初期スキャン？中心から外側への放射状スキャン？
- **param_6 == 1**: エッジ検出・境界スキャン？
- **param_6 == 2**: コーナー処理・特殊ケース？ (bVar3 フラグで分岐)
- **param_6 == 3**: 単一ピクセル書き込み？ (FUN_180001620 を呼び出すのみ)

**FUN_180006a90:**
- 8近傍の ushort[4] (RGBA?) の一致/類似度チェック
- 戻り値: 0=完全一致, 1=多少異なる, 2=部分一致, 3=より強く一致, 4=不一致
- あるピクセルが周囲のどのピクセルと似ているかを判定
- **役割**: 周辺ピクセルとの類似度に基づく補間ウェイト計算？

**FUN_180008060:**
- FUN_180006a90 とほぼ同じロジック
- 違い: byte[4] を比較 (8bit/ch 版)
- 戻り値の意味も同じ
- **役割**: 8bit/ch 版の周辺ピクセル類似度判定

### 2. direction param の使われ方

`local_158[0] = (longlong)param_5;` で direction param (0-7) を保持。その後:

- `*(int *)(&DAT_18000f000 + local_158[0] * 4)` → 隣接方向へのオフセットインデックス
- `*(int *)(&DAT_18000f0c8 + local_158[0] * 4)` → X方向スキャンステップ (0, ±1)
- `*(int *)(&DAT_18000f0f0 + local_158[0] * 4)` → Y方向スキャンステップ (0, ±1)

**パターン**: これらのテーブルアクセスにより、direction 値がスキャン方向と隣接ピクセル選択に変換される。8方向 (0-7) に対応している。

### 3. 3 Kernel の関係

- **FUN_180004b80**: ushort[4] 版メインカーネル。大規模な座標計算 + 重み付け補間
- **FUN_180006a90 / FUN_180008060**: 周辺ピクセル類似度判定のみ。テンプレート化可能
  
- **FUN_180005570**: FUN_180004b80 の byte[4] 版

これらは **同一テンプレートの異なるインスタンス** ではない。役割が異なる：
  - 前者: 補間実行
  - 後者2つ: 類似度判定 (16bit vs 8bit)

### 4. 共通 subroutine の呼び出しパターン

**FUN_1800021f0** (ushort比較): `iVar9 = FUN_1800021f0(puVar15, puVar1);`
- FUN_180004b80: param_6 == 0/1 で呼び出し
- FUN_180006a90: 広範囲で呼び出し (類似度判定)

**FUN_180002430** (byte比較): FUN_180005570 / FUN_180008060 で上記と同パターン

**FUN_180001ed0** (ushort blend): FUN_180005f60 内で呼び出し
**FUN_180002060** (byte blend): FUN_180006270 内で呼び出し

**FUN_180001000/001020/001040/001070/001090**: 重みテーブル計算群
- FUN_180004b80 でのみ使用
- param_6 の値に応じて異なる組み合わせ

### 5. 関数シグネチャ案

```cpp
// === ushort 版メインカーネル (FUN_180004b80) ===
void kernel_ushort_main(
    void* renderer,          // param_1
    void* pixel_buffer,      // param_2
    int x0, int y0,          // param_3, param_4
    int direction,           // param_5 (0-7)
    int scan_type,           // param_6 (0-3)
    char flag_a,             // param_7
    char flag_b,             // param_8
    int bounds_left,         // param_9
    int bounds_top,          // param_10
    int bounds_right,        // param_11
    int bounds_bottom,       // param_12
    int scan_start_x,        // param_13
    int scan_start_y         // param_14
);

// === byte 版メインカーネル (FUN_180005570) ===
void kernel_byte_main(
    void* renderer,
    void* pixel_buffer,
    int x0, int y0,
    int direction,
    int scan_type,
    char flag_a,
    char flag_b,
    int bounds_left,
    int bounds_top,
    int bounds_right,
    int bounds_bottom,
    int scan_start_x,
    int scan_start_y
);

// === ushort 版類似度判定 (FUN_180006a90) ===
// Returns: 0=match, 1=partial, 2=half, 3=strong, 4=mismatch
int kernel_ushort_similarity(
    void* renderer,          // param_1
    // param_2, param_3: unused
    uint16_t* neighbors[9],  // param_4 (9 近傍配列へのポインタ)
    int target_idx           // param_5 (0-8, 中心ピクセルインデックス)
);

// === byte 版類似度判定 (FUN_180008060) ===
int kernel_byte_similarity(
    void* renderer,
    uint8_t* neighbors[9],
    int target_idx
);

// === ushort 補間実行 (FUN_180005f60) ===
void kernel_interpolate_ushort(
    void* renderer,          // param_1
    int direction,           // param_2
    int x, int y,            // param_3, param_4
    uint16_t* src_a,         // param_5 (4要素)
    int base_x, int base_y,  // param_6, param_7
    uint16_t* src_b,         // param_8 (4要素)
    float* weight_fn,        // param_9 (関数ポインタ)
    char use_src_a,          // param_10
    int max_steps            // param_11
);

// === byte 補間実行 (FUN_180006270) ===
void kernel_interpolate_byte(
    void* renderer,
    int direction,
    int x, int y,
    uint8_t* src_a,
    int base_x, int base_y,
    uint8_t* src_b,
    float* weight_fn,
    char use_src_a,
    int max_steps
);
```

**補足**: DAT_18000f0XX テーブル群の構造は Ghidra での確認が必要。8方向×4テーブルの構造と推測される。