## FUN_180009960 解析結果

### 1. シグネチャ分析

```cpp
// Decomp からのリテラルシグネチャ
ushort* FUN_180009960(
    longlong param_1,    // 多分 base class / context pointer (poly?)
    int param_2,         // x 座標 (開始点)
    int param_3,         // y 座標 (開始点)
    int param_4,         // direction key / index (0-7 の方向)
    uint param_5,        // もう一つの direction key (param_4 の補完?)
    int *param_6,        // 出力 x (走査中の位置)
    int *param_7,        // 出力 y (走査中の位置)
    int param_8          // threshold (0=exact match, >0=tolerance)
)
```

**param_1**: `param_1 + 0x18` → `poly` の画像データ部分と推測。
**param_4/param_5**: direction key。`DAT_18000f0c8` + param_4*4 で x offset、`DAT_18000f0f0` + param_4*4 で y offset を読んでいる。
**param_8**: 0→exact equality check、非0→abs diff <= (param_8 << 7) で近似判定。

### 2. weight計算
→ この関数内に **weight 計算は存在しない。** 
weight 計算や curve eval は呼び出し元 (FUN_180004450, 1800047f0) で別途行われる。
この関数の役割は **画像上を指定方向に走査し、色が一致(または許容範囲内)する連続ピクセルを辿る**だけ。

### 3. 出力形式
戻り値は `ushort*` だが、実体は return value が走査終了理由を示す:
- `(ushort*)param_5` → ループ途中で param_5 側がアウトオブバウンズ (bVar15=false)
- `(ushort*)0x1` → param_6側の走査がアウトオブバウンズ (bVar16=false)
- `(ushort*)0x2` → 両方とも失敗 (bVar15=false && bVar16=false)

param_6, param_7 は走査後の座標 (最後に正常だった位置 or 最終位置) で更新される。
**alpha blend や premul は行わない。**

### 4. 周辺 scanner の役割

```cpp
// 関数シグネチャと役割

// FUN_180003ff0: ushort* (16bit/pixel) 用 3x3 近傍取得
// param_1=x, param_2=y, param_3=context, param_4=出力配列[9]
// 周囲9ピクセルのアドレスを param_4[0..8] に格納
void FUN_180003ff0(int param_1,int param_2,longlong param_3,longlong *param_4);

// FUN_180004220: byte* (8bit/pixel) 用 3x3 近傍取得 (ushort版と同一ロジック)
void FUN_180004220(int param_1,int param_2,longlong param_3,longlong *param_4);

// FUN_180004450: ushort* 用エッジ検出/走査後処理 (DL smoother 用?)
// param_6=3 → 元座標から走査, param_6=2 → direction offset 適用後から走査
// 内部で FUN_180009960 と FUN_180003ff0 を使う
void FUN_180004450(longlong param_1,longlong param_2,int param_3,int param_4,uint param_5,int param_6);

// FUN_1800047f0: byte* 用エッジ検出/走査後処理 (ushort版 = 180004450 と同一ロジック)
void FUN_1800047f0(longlong param_1,longlong param_2,int param_3,int param_4,uint param_5,int param_6);
```

### 5. literal C++ port

```cpp
// === リテラル C++ port ===

// data tables (from .rdata at 0x18000f0c8 and 0x18000f0f0)
// 8 direction offsets: {x_off, y_off}
//  index: 0=E, 1=NE, 2=N, 3=NW, 4=W, 5=SW, 6=S, 7=SE
static const int kXOffsets[8] = {1, 1, 0, -1, -1, -1, 0, 1};
static const int kYOffsets[8] = {0, -1, -1, -1, 0, 1, 1, 1};

// additional tables used in decomp (role unclear without more context)
// static const int kTable_f028[8];  // ??
// static const int kTable_f000[8];  // ??
// static const int kTable_f0a0[8];  // ??
// static const int kTable_f050[8];  // ??
// static const int kTable_f078[8];  // ??

struct Context {
    void* field_0x10;    // byte* data context
    void* field_0x18;    // ushort* data context (larger bit depth)
    int   field_0x08;    // threshold for byte version
    int   field_0x0c;    // threshold for ushort version
};

struct ImageInfo {
    void* data;          // offset 0x18 from context
    int   rowStride;     // bytes per row
    int   width;         // offset 0x24
    int   height;        // offset 0x28
};

// === FUN_180009960 ===
// ushort* (16bit/pixel) scanner: scan along direction param_4 until color mismatch or OOB
// returns: 0x0 = direction param_5 side fail, 0x1 = starting side fail, 0x2 = both fail
ushort* ScanUshort(Context* ctx, int startX, int startY, int dirKey, int altDirKey,
                   int* outX, int* outY, int tolerance) {
    int dx = kXOffsets[dirKey];
    int dy = kYOffsets[dirKey];
    
    int x0 = kXOffsets[altDirKey] + startX;  // alternate direction start
    int y0 = kYOffsets[altDirKey] + startY;
    
    *outX = startX;
    *outY = startY;
    
    ImageInfo* img = (ImageInfo*)ctx->field_0x18;
    
    // get pixel pointers for starting and alternate positions
    ushort* pStart = GetPixelUshort(img, startX, startY);
    ushort* pAlt   = GetPixelUshort(img, x0, y0);
    
    int stepDx = kXOffsets[dirKey];
    int stepDy = kYOffsets[dirKey];
    int altStepDx = kXOffsets[altDirKey];
    int altStepDy = kYOffsets[altDirKey];
    
    bool validStart = (pStart != nullptr);
    bool validAlt   = (pAlt != nullptr);
    
    // initial match check (exact or tolerance)
    bool matched;
    if (tolerance == 0) {
        matched = validStart && validAlt &&
                  pStart[0] == pAlt[0] && pStart[1] == pAlt[1] &&
                  pStart[2] == pAlt[2] && pStart[3] == pAlt[3];
    } else {
        int thresh = tolerance << 7;
        matched = validStart && validAlt &&
                  abs((int)pStart[0] - (int)pAlt[0]) <= thresh &&
                  abs((int)pStart[1] - (int)pAlt[1]) <= thresh &&
                  abs((int)pStart[2] - (int)pAlt[2]) <= thresh &&
                  abs((int)pStart[3] - (int)pAlt[3]) <= thresh;
    }
    
    // main scan loop
    while (validStart) {
        if (!validAlt || matched) break;
        
        *outX += altStepDx;
        y0 += stepDx;
        *outY += stepDy;
        x0 += altStepDy;
        
        ushort* pNext = GetPixelUshort(img, *outX, *outY);
        ushort* pAltNext = GetPixelUshort(img, x0, y0);
        
        if (tolerance == 0) {
            validStart = pStart && pNext &&
                         pStart[0] == pNext[0] && pStart[1] == pNext[1] &&
                         pStart[2] == pNext[2] && pStart[3] == pNext[3];
            validAlt = pAlt && pAltNext &&
                       pAlt[0] == pAltNext[0] && pAlt[1] == pAltNext[1] &&
                       pAlt[2] == pAltNext[2] && pAlt[3] == pAltNext[3];
            matched = pNext && pAltNext &&
                      pNext[0] == pAltNext[0] && pNext[1] == pAltNext[1] &&
                      pNext[2] == pAltNext[2] && pNext[3] == pAltNext[3];
        } else {
            int t = tolerance << 7;
            validStart = pStart && pNext &&
                         abs((int)pStart[0] - (int)pNext[0]) <= t &&
                         abs((int)pStart[1] - (int)pNext[1]) <= t &&
                         abs((int)pStart[2] - (int)pNext[2]) <= t &&
                         abs((int)pStart[3] - (int)pNext[3]) <= t;
            validAlt = pAlt && pAltNext &&
                       abs((int)pAlt[0] - (int)pAltNext[0]) <= t &&
                       abs((int)pAlt[1] - (int)pAltNext[1]) <= t &&
                       abs((int)pAlt[2] - (int)pAltNext[2]) <= t &&
                       abs((int)pAlt[3] - (int)pAltNext[3]) <= t;
            matched = pNext && pAltNext &&
                      abs((int)pNext[0] - (int)pAltNext[0]) <= t &&
                      abs((int)pNext[1] - (int)pAltNext[1]) <= t &&
                      abs((int)pNext[2] - (int)pAltNext[2]) <= t &&
                      abs((int)pNext[3] - (int)pAltNext[3]) <= t;
        }
        
        pStart = pNext;
        pAlt = pAltNext;
    }
    
    // determine return value
    ushort* result;
    if (!validStart)
        result = (ushort*)(uintptr_t)altDirKey;
    else if (!validAlt)
        result = (ushort*)0x1;
    else
        result = (ushort*)0x2;
    
    // restore original step offsets
    // (decomp shows decrement of step values before return)
    *outX -= altStepDx;
    *outY -= stepDy;
    
    return result;
}

// helper (要 Ghidra 確認で正確な構造体オフセット)
static ushort* GetPixelUshort(ImageInfo* img, int x, int y) {
    if (x < 0 || x >= img->width || y < 0 || y >= img->height)
        return nullptr;
    return (ushort*)((uint8_t*)img->data + y * img->rowStride + x * 8);
}

static byte* GetPixelByte(ImageInfo* img, int x, int y) {
    if (x < 0 || x >= img->width || y < 0 || y >= img->height)
        return nullptr;
    return (byte*)((uint8_t*)img->data + y * img->rowStride + x * 4);
}

// === FUN_180009e30 ===
// byte* (8bit/pixel) scanner (ushort 版と同一ロジック、画素サイズが 4bytes=RGBA)
byte* ScanByte(Context* ctx, int startX, int startY, int dirKey, int altDirKey,
               int* outX, int* outY, int tolerance) {
    // ... impl same as ScanUshort but with byte* and pixel stride 4
    // コードはほぼ同一なので省略。tolerance は byte* 版では << 7 なしで直接比較
}

// FUN_180003ff0: ushort* 3x3 neighborhood getter
void GetNeighborhoodUshort(int x, int y, Context* ctx, ushort* neighbors[9]) {
    ImageInfo* img = (ImageInfo*)ctx->field_0x18;
    neighbors[0] = GetPixelUshort(img, x-1, y-1);  // TL
    neighbors[1] = GetPixelUshort(img, x,   y-1);  // T
    neighbors[2] = GetPixelUshort(img, x+1, y-1);  // TR
    neighbors[3] = GetPixelUshort(img, x-1, y);    // L
    neighbors[4] = GetPixelUshort(img, x,   y);    // C
    neighbors[5] = GetPixelUshort(img, x+1, y);    // R
    neighbors[6] = GetPixelUshort(img, x-1, y+1);  // BL
    neighbors[7] = GetPixelUshort(img, x,   y+1);  // B
    neighbors[8] = GetPixelUshort(img, x+1, y+1);  // BR
}

// FUN_180004220: byte* 3x3 neighborhood getter
void GetNeighborhoodByte(int x, int y, Context* ctx, byte* neighbors[9]) {
    ImageInfo* img = (ImageInfo*)ctx->field_0x10;
    // same logic as ushort version with stride adjusted for 4-byte pixels
}
```

**未確定部分:**
- `DAT_18000f028`, `DAT_18000f000`, `DAT_18000f0a0` の役割 → 要 Ghidra 確認
- Context 構造体の正確なレイアウト (offset 0x10, 0x18, 0x08, 0x0c 以外のフィールド)
- `FUN_180001620`, `FUN_180001a90` (color blend utility) の正確な impl