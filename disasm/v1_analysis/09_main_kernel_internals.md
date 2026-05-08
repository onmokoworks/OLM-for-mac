## メイン補間 kernel 内部詳細解析

### 1. param_6 (scan_type) 各分岐の役割

**param_6 = 0**: 標準的なバイリニア補間
- 線形オフセット計算に `LinearOffsetFunction` (FUN_180001000) と `LinearOffsetZeroValue` (FUN_180001070) を使用
- param_7 (invert?) が非0の場合、LinearOffsetFunction を優先

**param_6 = 1**: 3点オフセット補間
- `LinearThreeOffsetFunction` (FUN_180001090) を使用
- 特殊ケース: iVar8 == 1 の場合、直接ポインタ書き込み（単一ピクセル）

**param_6 = 2**: 特殊2パス補間
- 2つのサブケース: bVar3 (特殊条件) と通常
- `LinearOffsetZeroOneValue` (FUN_180001040), `LinearOffsetFunction`, `LinearOffsetZeroValue` を使用
- param_8 で条件分岐あり

**param_6 = 3**: 最終処理/エッジケース
- 9近傍スキャナー (FUN_180003ff0/FUN_180004220) を呼び出し
- 単一ピクセル書き込み (FUN_180001620/FUN_180001a90)

### 2. LinearOffset* クラスの構築

各クラスは 8バイトのvtable + 浮動小数点パラメータで構成:

```c
struct LinearOffsetFunction {
    void* vftable;        // offset 0
    float param1;         // offset 8
    float param2;         // offset 12
};

struct LinearOffsetZeroValue {
    void* vftable;        // offset 0
    float param1;         // offset 8
    float param2;         // offset 12
    float param3;         // offset 16
};

struct LinearOffsetOneValue {
    void* vftable;        // offset 0
    float param1;         // offset 8
    float param2;         // offset 12
    float param3;         // offset 16
};

struct LinearOffsetZeroOneValue {
    void* vftable;        // offset 0
    float param1;         // offset 8
    float param2;         // offset 12
    float param3;         // offset 16
    float param4;         // offset 20
};

struct LinearThreeOffsetFunction {
    void* vftable;        // offset 0
    float param1;         // offset 8
    float param2;         // offset 12
    float param3;         // offset 16
    float param4;         // offset 20
};
```

### 3. FUN_180009960 (scanner) の呼び出し

**この関数は decomp 内で直接呼び出されていません。**

代わりに:
- param_6 == 3 で FUN_180003ff0 (FUN_180004b80) / FUN_180004220 (FUN_180005570) を呼び出し
- これらが内部で scanner を呼び出している可能性が高い

確認すべき場所:
- 関数 FUN_180003ff0 の内部
- 関数 FUN_180004220 の内部

### 4. FUN_180003ff0/180004220 (9近傍) の呼び出し

**FUN_180004b80**:
```c
FUN_180003ff0(iVar6, iVar17, param_1, local_f8);  // param_6 == 3
```

**FUN_180005570**:
```c
FUN_180004220(iVar6, iVar17, param_1, local_f8);  // param_6 == 3
```

引数: (x, y, コンテキスト, 出力配列[10])

### 5. FUN_180001ed0/180002060/180001a90 (alpha blend) の呼び出し

**FUN_180004b80** (16bit画像):
```c
FUN_180001620(local_128, pbVar15, 1);   // param_6 == 1, iVar8 == 1
FUN_180001620((longlong)local_f8, pbVar15, 4); // param_6 == 3
```

**FUN_180005570** (8bit画像):
```c
FUN_180001a90(local_128, pbVar15, 1);   // param_6 == 1, iVar8 == 1
FUN_180001a90((longlong)local_f8, pbVar15, 4); // param_6 == 3
```

第三引数がモード: 1=単一ピクセル, 4=4x4ブロック（要確認）

### 6. 最終出力

関数は常に `void` を返します。

出力は以下のいずれか:
- **param_6 0-2**: FUN_180005f60 (16bit) / FUN_180006270 (8bit) によるポリゴン書き出し
- **param_6 3**: FUN_180001620 / FUN_180001a90 による直接ピクセル書き込み

### 7. literal C++ 擬似コード

```cpp
// 16bit版 (FUN_180004b80)
// 8bit版 (FUN_180005570) は型と関数名が異なるのみ

void InterpolationKernel_16(
    long long context,      // param_1
    long long imageData,    // param_2
    int x,                  // param_3
    int y,                  // param_4
    int planeIndex,         // param_5
    int scanType,           // param_6 = 0,1,2,3
    char invertFlag,        // param_7
    char unknownFlag,       // param_8
    int srcX,               // param_9
    int srcY,               // param_10
    int dstX1,              // param_11
    int dstY1,              // param_12
    int dstX2,              // param_13
    int dstY2)              // param_14
{
    // ---- 領域計算 ----
    ushort* planeData = *(ushort**)(imageData + 0x20);
    ushort* srcData = *(ushort**)(imageData + planeIndex * 8);
    ushort* refData = *(ushort**)(imageData + *(int*)(DAT_18000f000 + planeIndex * 4) * 8);
    
    int cx = srcX - (srcX - x) / 2;
    int cy = srcY - (srcY - y) / 2;
    
    // 領域サイズ計算 (decomp の複雑な abs/min/max 処理)
    uint sizeW = abs(dstX2 - dstX1);
    uint sizeH = abs(dstY2 - dstY1);
    uint maxWH = max(sizeW, sizeH) + 1;
    
    uint range1 = abs(srcX - dstX2);
    uint range2 = abs(srcY - dstY2);
    uint rangeMax1 = max(range1, range2);
    
    uint range3 = abs(dstX1 - srcX);
    uint range4 = abs(dstY1 - srcY);
    uint rangeMax2 = max(range3, range4) + 1;
    
    // ---- scanType 分岐 ----
    switch (scanType) {
    case 0: {
        // パラメータ比較 (FUN_1800021f0)
        int cmp1 = ComparePlanes(planeData, refData);
        if (cmp1 < 0) {
            int cmp2 = ComparePlanes(planeData, refData);
            if (cmp2 < 0) {
                if (ComparePlanes(refData, srcData) < 0)
                    srcData = refData;
                if (ComparePlanes(refData, srcData) < 0)
                    srcData = refData;
            }
        }
        
        float stepSize = 1.0f / (float)(iVar8 * 2);
        LinearOffsetFunction linear(stepSize, 1.0f - stepSize);
        
        float denom = (float)(iVar8 * 2) - 1.0f;
        LinearOffsetZeroValue zeroValue(1.0f / denom, 1.0f - 1.0f / denom,
                                       1.0f / (denom * DAT_18000d260 - DAT_18000d1f0));
        
        void* offsetObj = invertFlag ? (void*)&linear : (void*)&zeroValue;
        
        FUN_180005f60(context, planeIndex,
                      local_170 + dstX1, local_174 + dstY1,
                      planeData, cx, cy,
                      srcData, offsetObj, '\x01', iVar8);
        break;
    }
    case 1: {
        // パラメータ比較 (同上)
        int cmp1 = ComparePlanes(planeData, refData);
        if (cmp1 < 0) {
            int cmp2 = ComparePlanes(planeData, refData);
            if (cmp2 < 0) {
                if (ComparePlanes(refData, srcData) < 0)
                    srcData = refData;
                if (ComparePlanes(refData, srcData) < 0)
                    srcData = refData;
            }
        }
        
        LinearThreeOffsetFunction threeOffset(
            1.0f / (float)(iVar8 * 4),
            (float)local_148 * DAT_18000d1f0 / (float)iVar8,
            (float)local_148 / (float)iVar8,
            1.0f - 1.0f / (float)(iVar8 * 2));
        
        if (iVar8 == 1) {
            // 単一ピクセル書き込み
            ushort* dstPixel = nullptr;
            long long layer = *(long long*)(context + 0x20);
            if (local_144 >= 0 && local_144 < *(int*)(layer + 0x24) &&
                y >= 0 && y < *(int*)(layer + 0x28)) {
                dstPixel = (ushort*)((long long)(y * *(int*)(layer + 0x20)) + (long long)local_144 * 8 + *(long long*)(layer + 0x18));
            }
            AlphaBlendSingle(imageData, dstPixel, 1);
        } else {
            FUN_180005f60(context, planeIndex,
                          local_170 + dstX1, local_174 + dstY1,
                          planeData, cx, cy,
                          srcData, &threeOffset, '\x01', iVar8);
        }
        break;
    }
    case 2: {
        if (bVar3) {
            // 特殊ケース (uVar16 == uVar11+1 && scanType==2)
            float f22 = (float)local_140 / ((float)(int)uVar16 - DAT_18000d1f0);
            float f19;
            if ((local_13c & 1) == 0)
                f19 = ((float)local_138 * 2.0f) - 1.0f;
            else
                f19 = (float)(iVar8 * 2 - 1) * DAT_18000d264;
            
            LinearOffsetZeroOneValue zeroOneVal(
                DAT_18000d1f0 - f22, f22 + DAT_18000d1f0,
                1.0f / f19, 1.0f - 1.0f / f19);
            
            FUN_180005f60(context, planeIndex,
                          local_170 + dstX1, local_174 + dstY1,
                          planeData, cx, cy,
                          srcData, &zeroOneVal, '\x01', iVar9);
        } else {
            // 標準ケース (2パス)
            if ((int)uVar16 > 0) {
                float f21 = (float)(int)uVar16;
                float f24 = 1.0f / (f21 * DAT_18000d264);
                float f20 = 1.0f / (f21 * 2.0f);
                float f21b = DAT_18000d1f0 - f20;
                
                LinearOffsetFunction linear1(f20, f21b);
                if (f21b <= f24) f21b = f24;
                LinearOffsetZeroValue zeroVal1(0.0f, f21b, f24);
                
                void* useOffset = &linear1;
                if ((uVar16 & 1) == 1) useOffset = &zeroVal1;
                
                if (param_8 == 0) {
                    FUN_180005f60(context, planeIndex,
                                  local_170 + dstX1, local_174 + dstY1,
                                  planeData, iVar7, iVar18,
                                  srcData, useOffset, '\x01', iVar9);
                }
            }
            if ((int)uVar11 > 0) {
                float f20 = (float)(int)uVar11;
                float f21 = fVar19 / (f20 * 2.0f);
                float f22b = f21 + fVar22;
                
                LinearOffsetFunction linear2(f22b, fVar19 - f21);
                float f23b = fVar19 - fVar19 / (f20 * fVar23);
                if (f23b <= f22b) f22b = f23b;
                LinearOffsetOneValue oneVal2(f22b, fVar19, f23b);
                
                void* useOffset = &linear2;
                if ((uVar11 & 1) == 1) useOffset = &oneVal2;
                
                FUN_180005f60(context, planeIndex,
                              local_130, local_134,
                              planeData, cx, cy,
                              srcData, useOffset, '\x01', -1);
            }
        }
        break;
    }
    case 3: {
        ushort* dstPixel = nullptr;
        long long layer = *(long long*)(context + 0x18);
        int px = *(int*)(&DAT_18000f0c8 + planeIndex * 4) + x;
        int py = *(int*)(&DAT_18000f0f0 + planeIndex * 4) + y;
        
        if (px >= 0 && px < *(int*)(layer + 0x24) &&
            py >= 0 && py < *(int*)(layer + 0x28)) {
            dstPixel = (ushort*)((long long)(py * *(int*)(layer + 0x20)) + (long long)px * 8 + *(long long*)(layer + 0x18));
        }
        
        long long neighborhood[10];
        FUN_180003ff0(px, py, context, neighborhood);
        AlphaBlendBlock(neighborhood, dstPixel, 4);
        break;
    }
    }
}
```

### 未確定部分

1. 関数 `FUN_180009960` (scanner) の直接呼び出しは decomp 内に確認できず。FUN_180003ff0/FUN_180004220 内部で呼ばれている可能性が高い。

2. グローバル定数 `DAT_18000d1f0`, `DAT_18000d1f4`, `DAT_18000d260`, `DAT_18000d264` の値は不明。`DAT_18000d1f4` は 1.0f と推定される。

3. `local_170`, `local_174`, `local_140`, その他計算変数の意味は不完全: デコード時の座標変換に関連する一時的な位置情報。

4. `bVar3` の条件: `uVar16 == uVar11 + 1 && param_6 == 2` の正確な幾何学的意味は不明。サイズが1異なる特殊ケース？