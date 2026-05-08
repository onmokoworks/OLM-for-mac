以下、Ghidra Decompiler の出力に基づく解析結果と C++ ポートを示します。

## 1. Render Callback 関数群 (FUN_1800095b0 / FUN_180009470)

### シグネチャとロジック

両関数はほぼ同一の構造を持ち、以下の処理を行います：

1. **初期化**: `FUN_180004220` (または `FUN_180003ff0`) でパラメータから `local_78` 配列を初期化
2. **4つのチャンネル（5, 3, 1, 7）に対して反復処理**:
   - `FUN_180008060` (または `FUN_180006a90`) で何らかの値を計算
   - `FUN_180006710` (または `FUN_180006570`) でチャンネルデータの処理を実行

**注意**: チャンネル番号 5, 3, 1, 7 は不連続で、バイナリ表現（0101, 0011, 0001, 0111）から RGBA チャンネルの特定の組み合わせを指す可能性があります。

```cpp
// Ported signature (literal from decomp)
uint64_t RenderCallback_1800095b0(void* param_1, uint32_t param_2, uint32_t param_3);
uint64_t RenderCallback_180009470(void* param_1, uint32_t param_2, uint32_t param_3);
```

### 呼ばれるタイミング

- `entryPointFunc` (18000a2c0) の case 0xB から呼ばれる `FUN_1800096f0` 内部で使用される可能性
- 現在の decomp からは直接の caller は不明。`render callback` という名前から per-frame/tile 単位での呼び出しが推測される

**要確認**: per-pixel か per-edge かは decomp からは判断できない。`FUN_1800096f0` 内部構造の解析が必要。

## 2. Main Kernel と Render Callback の関係

**Decomp からは、render callback 内で直接 main kernel (FUN_180004b80 / FUN_180005570) を呼ぶ形跡は見られない。**

代わりに、以下の中間関数を介して処理：
- `FUN_180008060` / `FUN_180006a90`: 何らかの値の計算（おそらく重みやしきい値）
- `FUN_180006710` / `FUN_180006570`: 実際のピクセル処理（これらが kernel を内部で呼ぶ可能性あり）

**要 Ghidra 確認**: 
- `FUN_180006710` と `FUN_180006570` の内部で main kernel が呼ばれているか
- render callback とは別のパスで直接 main kernel を呼ぶエントリポイントが存在するか

## 3. Interpolate Executor (FUN_180005f60 / FUN_180006270)

### 呼び出し元

現在の decomp からは直接の caller は不明。以下の可能性が考えられる：

- render callback 内（FUN_180006710/FUN_180006570）から呼ばれる
- 別の high-level なループから呼ばれる補間処理関数

### ロジック概要

**FUN_180005f60 (16-bit版)**:
```
入力: param_5 (current color), param_8 (target color), param_9 (weight function pointer)
処理:
1. 2色を8バイトの一時変数に保存
2. 開始位置(param_3, param_4)から終了位置(param_6, param_7)までの距離を計算
3. 距離を基にループ回数を決定
4. 各反復:
   - weight function から重みを取得
   - 重みを[0, 1]にクランプ
   - 2つのピクセル(src0, src1)を読み取り
   - 色が異なる場合のみ補間を実行
5. 16-bit色の補間には FUN_180001ed0 を使用
```

**FUN_180006270 (8-bit版)**:
- 上記とほぼ同じロジック
- データ構造が 8-bit x 4チャンネル（4バイト/ピクセル）
- 補間関数は FUN_180002060 を使用

```cpp
// Ported signatures
void InterpolateExecutor16(void* param_1, int param_2, int param_3, int param_4, 
                           uint16_t* param_5, int param_6, int param_7, 
                           uint16_t* param_8, void* param_9, bool param_10, int param_11);

void InterpolateExecutor8(void* param_1, int param_2, int param_3, int param_4, 
                          uint8_t* param_5, int param_6, int param_7, 
                          uint8_t* param_8, void* param_9, bool param_10, int param_11);
```

## 4. Weight Curve Evaluator との連携

`param_9` は関数ポインタの配列を指し、以下のように使用：
```c
float weight = (float)(**(code **)*param_9)(param_9);
```

**構造**: 
- `param_9[0]` の最初の要素が関数ポインタ
- この関数ポインタが指す関数を `param_9` 自身を引数として呼び出し、float の重みを返す

これは `LinearOffset*` 型のオブジェクトで、`operatror()` として重みを計算する典型的な C++ ファンクタパターン。

**要 Ghidra 確認**:
- `FUN_180003ed0` 周辺の weight curve 実装を解析し、具体的な評価ロジック（線形/スプライン等）を特定する必要がある

## 5. 補助関数 (FUN_180009960 / FUN_180009e30)

Two-point edge walker (pixel searching):

**FUN_180009960 (16-bit版)**:
```
入力: param_1 (コンテキスト), param_2, param_3 (開始座標), 
      param_4 (方向ID), param_5 (方向ID), param_8 (許容誤差)
戻り値: ushort* (エッジタイプのエンコード)
- 0: 両方のエッジが異なる色
- 1: 片方のエッジのみ
- 2: 両方なし
- param_5: 特別なケース
```

**FUN_180009e30 (8-bit版)**:
- 同様のロジックで 8-bit/channel データを処理

```cpp
uint16_t* EdgeWalker16(void* param_1, int x1, int y1, int dir1, uint32_t dir2, 
                       int* out_x, int* out_y, int tolerance);
uint8_t* EdgeWalker8(void* param_1, int x1, int y1, int dir1, uint32_t dir2, 
                     int* out_x, int* out_y, int tolerance);
```

## 6. エントリポイント (entryPointFunc @ 18000a2c0)

**case 0**: 初期化 - コールバック関数の登録とバージョン表示  
**case 1**: パラメータ設定 (0x90800, ピクセルフォーマット等)  
**case 4**: レイヤー/マスクの設定 (PiPL リソース風)  
**case 0xB**: 実際の描画処理 (`FUN_1800096f0` を呼び出し)

### 全体の呼び出し構造（推定）

```
entryPointFunc (case 0xB)
  └── FUN_1800096f0
        ├── RenderCallback_1800095b0 / FUN_180009470
        │     ├── チャンネル初期化 (FUN_180004220/3ff0)
        │     └── 4チャンネル処理ループ
        │           ├── FUN_180008060/6a90 (重み計算?)
        │           └── FUN_180006710/6570
        │                 └── InterpolateExecutor (複数種類)
        │                       ├── EdgeWalker (エッジ検出)
        │                       └── FUN_180001ed0/2060 (色補間)
        └── (その他のパス)
```

**注意**: この call graph は一部推測を含み、特に `FUN_180006710`→`InterpolateExecutor` の関係は未確認です。