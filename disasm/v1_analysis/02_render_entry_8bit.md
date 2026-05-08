## FUN_180001400 構造解析

### 1. Outer Loop 構造

この関数には**明示的な outer loop (x/y walk) は存在しない**。代わりに以下の call chain で処理が進行：

```
FUN_1800069a0 → (内部で FUN_180002740 等を呼び座標計算)
```

`FUN_1800069a0` が scanline / xy walk の実体を持つと推定される（要 Ghidra 確認）。

### 2. Plane Setup

```
local_c8[128]          → 一時バッファ（128バイト）
local_568[148]         → class plane (FUN_18000a5e0 で初期化)
param_5                → 出力バッファ構造体
  param_5+0x18 = local_c8  (一時バッファへのポインタ)
  param_5+0x10 = local_c8  (別のポインタとしても設定)
```

### 3. Helper 呼び出しパターン

| 順序 | 関数 | 引数パターン | 役割 |
|------|------|-------------|------|
| 1 | `FUN_18000a5e0(local_568, *(param_1+0x180))` | class plane 初期化 | plane setup |
| 2 | `FUN_1800069a0(param_1, 0, iVar3, param_3, param_4+0x2c, param_5, FUN_1800095b0, param_4)` | 第1パス | ループ処理 |
| 3 | `FUN_1800069a0(param_1, 0, iVar3, param_3, param_4+0x2c, param_5, &LAB_1800026e0, local_c8)` | 第2パス (条件: *param_5 != 0) | ループ処理 |

`FUN_1800095b0` と `&LAB_1800026e0` は**コールバック関数ポインタ**。

### 4. Direction Key (1,3,5,7) の推定

`FUN_180002740` 内で参照される `DAT_18000f000[]` テーブルのインデックスが `param_5` (direction) に対応：

| 値 | テーブル | 推定される意味 |
|----|---------|---------------|
| 1 | offset 0x04 | 水平方向（右） |
| 3 | offset 0x0c | 垂直方向（下） |
| 5 | offset 0x14 | 水平方向（左） |
| 7 | offset 0x1c | 垂直方向（上） |

**要確認**：`DAT_18000f000` の内容を Ghidra で確認する必要あり。

### 5. 高レベル擬似コード

```cpp
// FUN_180001400 - 8-bit ARGB render entry
int render_8bit_argb(
    void* ae_plugin_ctx,        // param_1
    undefined8 param2,          // 未使用？
    uint8_t* input_buffer,      // param_3 (initial)
    LayerInfo* layer_info,      // param_4
    OutputBuffer* output        // param_5
) {
    // Step 1: Initialize class plane
    ClassPlane plane;
    plane.init(*(void**)(ae_plugin_ctx + 0x180));
    
    int height = layer_info->bottom - layer_info->top;  // 0x38 - 0x30
    
    // Step 2: Validate input buffer
    int status = ae_plugin_ctx->validate_buffer(input_buffer, layer_info, 0);
    if (status != 0) goto cleanup;
    
    // Step 3: Check flag and possibly allocate temp buffer
    int useTempBuffer = (layer_info->flags & 1) != 0;
    int sampleMode = useTempBuffer ? 2 : 0;
    
    status = ae_plugin_ctx->check_dimensions(
        input_buffer[0x24],  // width
        input_buffer[0x28],  // height
        sampleMode
    );
    if (status != 0) goto cleanup;
    
    uint8_t temp_buffer[128];  // local_c8
    
    // Step 4: If output has extra data, set up temp buffer
    if (output->has_extra_data) {
        output->temp_buffer = temp_buffer;
        
        status = ae_plugin_ctx->validate_buffer(input_buffer, temp_buffer, 0);
        if (status != 0) goto cleanup;
        
        // First pass with callback at LAB_1800026e0
        status = process_scanline(
            ae_plugin_ctx, 0, height,
            input_buffer,
            layer_info + 0x2c,  // some offset
            output,
            &callback_lab_1800026e0,  // callback function
            temp_buffer
        );
        if (status != 0) goto cleanup;
        
        output->extra_data = temp_buffer;
        output->layer_info = layer_info;
        input_buffer = temp_buffer;  // switch to temp buffer
    }
    
    // Step 5: Second pass (main processing)
    status = ae_plugin_ctx->validate_buffer(input_buffer, layer_info, 0);
    if (status != 0) goto cleanup;
    
    status = process_scanline(
        ae_plugin_ctx, 0, height,
        input_buffer,
        layer_info + 0x2c,
        output,
        &FUN_1800095b0,  // callback function
        layer_info
    );
    if (status != 0) goto cleanup;
    
    // Step 6: Cleanup temp buffer
    ae_plugin_ctx->release_buffer(temp_buffer);
    
cleanup:
    plane.destroy();
    return status;
}
```

### 6. 不明箇所の列挙

追加で Ghidra 解析が必要なサブルーチン：

1. **`FUN_1800095b0`** - メインのレンダリングコールバック（最も重要）
2. **`FUN_1800026e0`** - 第1パスのコールバック
3. **`FUN_1800069a0`** - scanline ループの実体
4. **`FUN_180009960`** - FUN_180002740 内で呼ばれる座標計算
5. **`FUN_180002740`** - direction / boundary 決定ロジック（要確認）
6. **`DAT_18000f000` テーブル** - direction key 1/3/5/7 の実際の値
7. **`DAT_18000f0c8` 等のテーブル** - direction 毎のオフセット値
8. **`FUN_1800021f0`** - 16-bit 色比較関数（float 変換あり）

**特記事項**：
- `FUN_180001620` / `FUN_180001a90` は 16-bit / 8-bit のカラー平均化（weighted sum）関数で、render 本体から直接呼ばれる形跡はない。
- `FUN_180001ed0` / `FUN_180002060` は alpha blend 関数（16-bit / 8-bit 版）。
- 関数は直列的な2パス構造で、1パス目は temp buffer への準備処理、2パス目が本処理と推測される。