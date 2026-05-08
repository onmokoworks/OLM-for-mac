## 解析結果

### 1. 8-bit版と16-bit版の構造差

**エントリポイント (FUN_1800011e0 vs FUN_180001400)**:
- ほぼ同一の構造。差異は以下のみ:
  - `FUN_1800068b0` (16-bit) vs `FUN_1800069a0` (8-bit) — 異なるサブルーチン
  - `FUN_180009470` (16-bit) vs `FUN_1800095b0` (8-bit) — 異なるコールバック/ラベル
  - オフセット値: `param_5+0x20` (16-bit) vs `param_5+0x18` (8-bit) — バッファ格納位置が異なる

**カラーブレンド/アキュムレータ (FUN_180001620 vs FUN_180001a90)**:
- 明確な違い:
  - 16-bit: `(float)*pixel * DAT_18000d250` (乗算)
  - 8-bit: `(float)*pixel / DAT_18000d268` (除算)
  - 16-bit: clamp値 `0x8000` (32768)
  - 8-bit: clamp値 `0xff` (255)
  - 出力キャスト: 16-bit → `(ushort)`, 8-bit → `(byte)`

**カラーコンペア (FUN_1800021f0 vs FUN_180002430)**:
- 比較関数は別物:
  - 16-bit: `* DAT_18000d250`
  - 8-bit: `/ DAT_18000d268`
- 構造は同一だが、スケーリング定数と除数が異なる

**キーとなるcallee (FUN_180002740)**:
- 16-bit版のみ提供。8-bit版は存在しないか未提示。
- この関数は`ushort*`を扱い、`FUN_1800021f0`(16-bit版)を呼ぶ。

### 2. バイト→u16のwidening箇所

明示的なwideningは以下の箇所で行われている:

1. **入力時** (calleeへの引数渡し時): 構造体paddingにより暗黙的に`byte`が`ushort`に格納されている。明示的なキャストは見られない。

2. **FUN_180001620** (16-bit accumulator):
   ```c
   uVar6 = (uint)*param_2;                    // 暗黙的widening
   uVar7 = (uint)param_2[1];
   ```
   8-bit版 (FUN_180001a90) も同じく`uint`にwideningしている。

3. **FUN_1800021f0** (16-bit compare):
   ```c
   uVar3 = (uint)*param_1 - (uint)*param_2;  // ushort→uint widening
   ```
   8-bit版 (FUN_180002430) も同じ
   
4. **スケーリング時のfloat変換**:
   - 16-bit: `(float)*param_1 * DAT_18000d250`
   - 8-bit: `(float)*param_1 / DAT_18000d268`
   
5. **出力書き込み**:
   - 16-bit: clamp to 0x8000 → `ushort` cast
   - 8-bit: clamp to 0xff → `byte` cast

**注意**: decompでは明示的なbyte→ushort wideningは見えない。内部的には常にuintで扱われ、出力時にclampされている。

### 3. 共通化可能性の評価

**共通化可能な部分**:
- エントリポイントの構造 (FUN_1800011e0/FUN_180001400): **可** — テンプレートで`PixelType=ushort|byte`にできる
- カラーコンペア関数 (FUN_1800021f0/FUN_180002430): **可** — スケール定数をテンプレートパラメータ化
- プレンド/アキュムレータ (FUN_180001620/FUN_180001a90): **可** — clamp値とスケール演算をテンプレート化

**共通化が困難な部分**:
- `FUN_180002740` (16-bit) の8-bit版が未確認で、存在するか不明
- 異なるcallee (FUN_1800068b0 vs FUN_1800069a0) の内部構造が未解析
- 異なるコールバックアドレス (FUN_180009470 vs FUN_1800095b0) — これらは独立した関数である可能性が高い

**結論**: 主要なロジックは**template<typename Pixel>で1本にまとめられる**。ただし以下のリスクが残る:
- `FUN_180002740` が8-bit版と16-bit版で異なるデータ構造体に依存していないか要確認
- calleeアドレスの違いが単なるビルド配置の差か、実際に別ロジックなのか

### 4. Literal Port戦略の提案

```cpp
// === 推奨戦略: templateベースの共通化 ===

// Pixel traits: 8-bitと16-bitの差異を吸収
template<typename T>
struct PixelTraits;

template<>
struct PixelTraits<uint8_t> {
    using pixel_t = uint8_t;
    static constexpr int max_chan = 255;
    static constexpr float scale_factor(); // = DAT_18000d268 (逆数?)
    static constexpr float weight();       // 未確定: 要Ghidra定数確認
};

template<>
struct PixelTraits<uint16_t> {
    using pixel_t = uint16_t;
    static constexpr int max_chan = 32768;
    static constexpr float scale_factor(); // = DAT_18000d250
    static constexpr float weight();       // 未確定
};

// テンプレート化されたエントリポイント
template<typename T>
int render_entry_impl(longlong param_1, undefined8 param_2, undefined1* param_3,
                      longlong param_4, char* param_5) {
    // FUN_1800011e0/FUN_180001400 のロジックをそのままtemplate化
    // 差異点:
    // - buffer offset (0x18 vs 0x20) は定数化
    // - calleeアドレスはテンプレート特殊化で切り替え
    // - callbackアドレスもテンプレート特殊化で切り替え
}

// テンプレート化されたcolor compare
template<typename T>
int color_compare(T* a, T* b) {
    // FUN_1800021f0/FUN_180002430 のロジック
    // scale_factorによって演算子を分岐
    static_assert(std::is_same_v<T, uint8_t> || std::is_same_v<T, uint16_t>);
    if constexpr (std::is_same_v<T, uint8_t>) {
        // * DAT_18000d268?  → 要Ghidra確認: 実際は/なのか*なのか
        float f5 = (float)*a / DAT_18000d268;
        float f6 = (float)*b / DAT_18000d268;
    } else {
        float f5 = (float)*a * DAT_18000d250;
        float f6 = (float)*b * DAT_18000d250;
    }
    // ... 共通ロジック ...
}

// テンプレート化されたaccumulator
template<typename T>
void accumulate_colors(longlong param_1, T* output, int param_3) {
    // FUN_180001620/FUN_180001a90 のロジック
    constexpr T max_val = PixelTraits<T>::max_chan;
    // ... 処理 ...
    // clamp時にmax_valを使用
    if (val > max_val) val = max_val;
}
```

**要Ghidra確認事項**:
1. `FUN_180002740` の8-bit版が存在するか。存在すれば、`byte`版の`color_compare`を呼ぶ同一構造か確認
2. `DAT_18000d250` と `DAT_18000d268` の実際の値 (float定数)
3. `FUN_1800069a0` と `FUN_1800068b0` の実体 — 単なる型違いのラッパーか
4. `FUN_1800095b0` と `FUN_180009470` の実体 — 同様に型違いか