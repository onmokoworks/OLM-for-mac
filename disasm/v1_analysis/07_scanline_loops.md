## 逆解析による scanline loop 構造の解析

### 1. ループ構造の特定

**発見：FUN_1800069a0 (8-bit) と FUN_1800068b0 (16-bit) は scanline loop を含んでいない**

これらの関数は **PF Iterator Suite のラッパー関数** です：
- 8-bit → `"PF Iterate8 Suite"` 
- 16-bit → `"PF iterate16 Suite"`

実際のループ処理は After Effects の SDK 関数 `(＊suite->iterate)(...)` によって実行され、スイートが内部で x/y 走査を行います。

### 2. callback ポインタ呼び出しパターン

- param_7 (8bit) / param_7 (16bit) は **イテレート関数のコールバックとして直接渡される**
- 呼び出しはスイート内部で行われ、このラッパーからは直接見えない
- スイートは通常 `refcon` (param_8) をコールバックの最後の引数として渡す

### 3. 早期 return / break 条件

- スイート取得失敗時 → `FUN_18000b5c0()` 呼び出し後、スイートポインタを設定
- 戻り値はスイートの iterate 関数の結果をそのまま返す（`uVar2`）

### 4. 8/16-bit 差異

- **型のみの違い**：
  - 8-bit: 内部処理で `param_1 + 0x180` からデータを取得
  - 16-bit: 同じオフセット `param_1 + 0x180`
- ロジックは同一
- 違いはスイート名文字列と、スイートが扱うピクセル型だけ

### 5. Literal C++ Port 疑似コード

```cpp
// PF_IterateSuite を使ったラッパー関数 (8-bit版)
// 注: 実際のループはAfter Effects SDK内で実装
int32_t PF_Iterate8_Wrapper(PF_EffectWorld* self,      // param_1
                            int32_t param2,             // param_2 (x?)
                            int32_t param3,             // param_3 (y?)
                            int64_t param4,             // param_4
                            int64_t param5,             // param_5
                            int64_t param6,             // param_6
                            int64_t callback_func,      // param_7: callback function pointer
                            int64_t refcon)             // param_8: user data
{
    // スタック上のサイズ不明なバッファ
    // Ghidra: local_4a8[87] → 実サイズは要確認
    uint8_t buffer[87 * 8]; // 推定サイズ
    
    // スイート取得 (実際の関数ポインタは事前解決済み)
    PF_Err err = AcquireSuite(kPFIterate8Suite, 1, &suite);
    
    if (!suite) {
        // エラーハンドリング (FUN_18000b5c0)
        HandleSuiteError();
        suite = fallback_suite;
    }
    
    // イテレート関数を呼び出し ← ここでループ内部が実行される
    int32_t result = suite->iterate(self, param2, param3, param4, param5, param6,
                                    callback_func, refcon);
    
    // スイート解放
    ReleaseSuite(buffer);
    
    return result;
}

// 16-bit版 (機能は同じ、型のみ異なる)
int32_t PF_Iterate16_Wrapper(PF_EffectWorld* self,
                             int32_t param2,
                             int32_t param3,
                             int64_t param4,
                             int64_t param5,
                             int64_t param6,
                             int64_t callback_func,
                             int64_t refcon)
{
    uint8_t buffer[88 * 8]; // 16bit版は配列サイズが1つ多い
    
    PF_Err err = AcquireSuite(kPFIterate16Suite, 1, &suite);
    
    if (!suite) {
        HandleSuiteError();
        suite = fallback_suite;
    }
    
    int32_t result = suite->iterate(self, param2, param3, param4, param5, param6,
                                    callback_func, refcon);
    
    ReleaseSuite(buffer);
    
    return result;
}
```

### 注意事項（要 Ghidra 確認）

1. **`buffer` の実サイズ**：スタック配列の正確なサイズは Ghidra の local 変数サイズからは不明。`local_4a8[87]` は `undefined8 *` の配列だが、実際の確保サイズは `FUN_18000a5e0` の内部実装に依存する。

2. **AcquireSuite / ReleaseSuite の関数シグネチャ**：`FUN_18000a5e0` と `FUN_18000a620` の正確なプロトタイプは未確認。

3. **エラーハンドリング**：`FUN_18000b5c0()` の動作（例外送出かエラーコード設定か）は未確認。

4. **callback の呼び出し規約**：After Effects SDK の `iterate` 関数がどのように callback を呼び出すかはプラットフォーム依存の可能性あり。