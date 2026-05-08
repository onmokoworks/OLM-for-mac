## 解析結果

5つのクラスの data layout と evaluator 関数を抽出しました。

### Byte Layout (32-bit, x86_64)

各クラスは vtable pointer + メンバ変数で構成:

```
LinearOffsetFunction:    [vptr(8)] [offset(4)] [pad4?] [v0(4)] [v1(4)]  → total 24 bytes
LinearOffsetOneValue:    [vptr(8)] [offset(4)] [pad4?] [v0(4)] [v1(4)] [val(4)] → total 28 bytes
LinearOffsetZeroValue:   [vptr(8)] [offset(4)] [pad4?] [v0(4)] [v1(4)] [val(4)] → total 28 bytes
LinearOffsetZeroOneValue:[vptr(8)] [offset(4)] [pad4?] [v0(4)] [v1(4)] [val0(4)] [val1(4)] → total 32 bytes
LinearThreeOffsetFunction:[vptr(8)] [offset(4)] [pad4?] [v0(4)] [v1(4)] [v2(4)] [pad?] [t0(4)] → total 32 bytes
```

Key: `[vptr(8)]` は8バイト、`[offset(4)]` は param_1+1 (8バイト目以降)、`[pad4?]` は param_1+0xc のオフセットを埋めるためのパディング。(longlong)param_1+0xc は vptr の8バイト + offset の4バイト + 次の4バイトの前半 = 0x0c。

実際の data アクセス:
- `*(param_1 + 1)` = offset at +8 (32-bit)
- `*(longlong)param_1 + 0xc` = v0 at +12 (32-bit) - このパディング位置は不明瞭だが、access パターンから +12
- `*(param_1 + 2)` = v1 at +16 (32-bit)
- `*(param_1 + 3)` = v2 at +24 (32-bit) (ZeroOneValue のみ)
- `*(longlong)param_1 + 0x14` = t0 at +20 (32-bit) (ThreeOffset のみ)
- `*(longlong)param_1 + 0x18` = val1 at +24 (32-bit) (ZeroOneValue の特殊値)

DAT_18000d1f4 はメモリ上の float 定数。Ghidra で確認が必要だが、値は 1.0f と推測。

```cpp
// === header ===
#pragma once
#include <cstdint>

struct LinearOffsetFunction {
    // vtable pointer (non-reproduced)
    float offset;   // +8
    float v0;       // +12
    float v1;       // +16 (implicitly from access pattern)
    
    LinearOffsetFunction(float offset, float v0, float v1);
    float operator()(float t) const;
};

struct LinearOffsetOneValue {
    float offset;   // +8
    float v0;       // +12
    float v1;       // +16
    float val;      // +20 (special value at 1.0f case)
    
    LinearOffsetOneValue(float offset, float v0, float v1, float val);
    float operator()(float t) const;
};

struct LinearOffsetZeroValue {
    float offset;   // +8
    float v0;       // +12
    float v1;       // +16
    float val;      // +20 (special value at 0.0f case)
    
    LinearOffsetZeroValue(float offset, float v0, float v1, float val);
    float operator()(float t) const;
};

struct LinearOffsetZeroOneValue {
    float offset;   // +8
    float v0;       // +12
    float v1;       // +16
    float val0;     // +24 (special value at t==0.0f)
    float val1;     // +24? (special value at t==1.0f) -> 要 Ghidra 確認: 実際のオフセットは +24 と +28?
    
    LinearOffsetZeroOneValue(float offset, float v0, float v1, float val0, float val1);
    float operator()(float t) const;
};

struct LinearThreeOffsetFunction {
    float offset;   // +8
    float v0;       // +12
    float v1;       // +16
    float v2;       // +24? (access pattern: param_1+2 = +16, param_1+3 = +24? 要 Ghidra 確認)
    float t0;       // +20 (threshold t0)
    
    LinearThreeOffsetFunction(float offset, float v0, float v1, float v2, float t0);
    float operator()(float t) const;
};

// === impl ===
#include "evaluators.h"

// DAT_18000d1f4 の値は Ghidra で確認する必要あり。ここでは一時的に定数として定義
static constexpr float kDAT_18000d1f4 = 1.0f; // 要 Ghidra 確認

LinearOffsetFunction::LinearOffsetFunction(float offset, float v0, float v1)
    : offset(offset), v0(v0), v1(v1) {}

float LinearOffsetFunction::operator()(float t) const {
    // FUN_1800010c0: simple linear interpolation
    return (v1 - v0) * t + v0;
}

LinearOffsetOneValue::LinearOffsetOneValue(float offset, float v0, float v1, float val)
    : offset(offset), v0(v0), v1(v1), val(val) {}

float LinearOffsetOneValue::operator()(float t) const {
    // FUN_1800010e0: if t == 1.0f, return val
    if (t != kDAT_18000d1f4) {
        return (v1 - v0) * t + v0;
    }
    return val;
}

LinearOffsetZeroValue::LinearOffsetZeroValue(float offset, float v0, float v1, float val)
    : offset(offset), v0(v0), v1(v1), val(val) {}

float LinearOffsetZeroValue::operator()(float t) const {
    // FUN_180001150: if t == 0.0f, return val
    if (t != 0.0f) {
        return (v1 - v0) * t + v0;
    }
    return val;
}

LinearOffsetZeroOneValue::LinearOffsetZeroOneValue(float offset, float v0, float v1, float val0, float val1)
    : offset(offset), v0(v0), v1(v1), val0(val0), val1(val1) {}

float LinearOffsetZeroOneValue::operator()(float t) const {
    // FUN_180001110: 3 cases: t==1.0f, t==0.0f, else
    if (t == kDAT_18000d1f4) {
        // 要 Ghidra 確認: このクラスの val1 の実際のオフセット位置。param_1+0x18 = +24 を参照
        // メンバ val1 が +24 にあると仮定
        return val1;  // 不明: val1 の実体オフセットが疑わしい
    }
    if (t != 0.0f) {
        return (v1 - v0) * t + v0;
    }
    return val0;
}

LinearThreeOffsetFunction::LinearThreeOffsetFunction(float offset, float v0, float v1, float v2, float t0)
    : offset(offset), v0(v0), v1(v1), v2(v2), t0(t0) {}

float LinearThreeOffsetFunction::operator()(float t) const {
    // FUN_180001180: piecewise linear with threshold t0
    if (t <= t0) {
        return ((v1 - v0) / t0) * t + v0;
    }
    // 要 Ghidra 確認: この部分のデータアクセス。param_1+0x14 = t0(+20), param_1+0x10 は？ 
    // 実際のコードでは v2 が +24, DAT_18000d1f4 が 1.0f と仮定
    float slope = (v2 - v1) / (kDAT_18000d1f4 - t0);
    return (slope * t + v2) - slope;
}
```

### 注意事項 (Ghidra 確認必須)

1. **DAT_18000d1f4 の値**: 現時点では 1.0f と仮定。完全に確定するには Ghidra で該当アドレスの float 値を確認してください。

2. **パディングの解釈**: decomp における `*(longlong)param_1 + 0xc` と `*(param_1 + 1)` の書き分けから、offset の直後に4バイトのパディングが入っている可能性。ただし access pattern が不自然なため、実際の layout はもしかすると構造体が8バイトアラインメントされているだけか。要 Ghidra 確認。

3. **LinearOffsetZeroOneValue の val1 オフセット**: decomp では `*(longlong)param_1 + 0x18` でアクセスしているが、このクラスのデータメンバが v0(+12), v1(+16), val0(+24), val1(+28) なのか、あるいは +20 と +24 なのか、実際のメモリレイアウトを Ghidra で確認する必要あり。

4. **LinearThreeOffsetFunction の v2 オフセット**: decomp の `*(param_1 + 2)` は +16 (v1) だが、3つ目の値は `*(param_1 + 3)` で +24 か、あるいは `*(longlong)param_1 + 0x14` の +20 が v2 か要確認。実際のコードでは v2 があいまい。

5. **クラス vtable ポインタ**: 移植では不要だが、データレイアウトを完全に保つために vtable ポインタの分の8バイトはクラスに含める必要がある。上記の layout は vptr を考慮した相対オフセットで記述済み。