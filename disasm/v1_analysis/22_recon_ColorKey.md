# OLMColorKey Plugin Architecture Recon Report

## 1. Plugin Name / Meta Information

**Plugin Name:** `OLM Color Key` (found via string "OLM Color Key" at FUN_18000b340)

**File:** `OLMColorKey.aex`

**String references found:**
- `"Color Keep"` (param ID 1)
- `"Threshold"` (param ID 2)
- `"Threshold Parameters"` (param ID 3)
- `"Premultiplied Color"` (param ID 4)
- `"Color Space"` (param ID 5) → options: `"RGB"`, `"HSV"`, `"Lab76"`, `"Lab94"`, `"YUV"`, `"YCrCb"`
- `"Force Lower Precision"` (param ID 0x20a) → options: `"Full 16bit"`, `"8bit"`
- `"Per Color"` (param ID 6)
- `"Per Component"` (param ID 7)
- `"Threshold R/H/L/Y/Y_"` (param ID 8)
- `"Threshold G/S/a/U/Cr_"` (param ID 9)
- `"Threshold B/V/b/V/Cb_"` (param ID 10)
- `"Edge Thin"` (param ID 0xc)
- `"Amount"` (param ID 0xd)
- `"Distance Type"` (param ID 0xe) → options: `"Box"`, `"Approximate"`, `"Euclidean"`
- `"Edge Blur"` (param ID 0x10)
- `"Direction"` (param ID 0x13) → options: `"Inside"`, `"Around"`, `"Outside"`
- `"Number of Colors"` (param ID 0x15) — up to 25 colors
- `"Enable Replace"` (param ID 0x20b)
- Per-color parameters: `"Color N"`, `"Threshold N"`, `"Use Color N"`, `"Replace Color N"`, `"Use Replace Color N"`

---

## 2. AE Entry Point Function + Cmd Dispatch

**Entry Point Function:** `FUN_180001000` (address `0x180001000`)

This function calls various `FUN_18000c*` helpers to register UI parameters (PARAMS_SETUP).

**Render dispatching** is done in `FUN_1800018e0` (address `0x1800018e0`):
- Reads `sVar1 = *(short*)(*param_4 + 0x2c)` → this is the **pixel depth** (8, 16, or 32)
- Calls `FUN_18000a3d0` for parameter setup
- Then dispatches based on pixel depth:
  - `sVar1 == 8` → `FUN_1800094b0` (8-bit render)
  - `sVar1 == 0x10` → `FUN_180009000` (16-bit render)
  - `sVar1 == 0x20` → `FUN_180009960` (32-bit float render)

**Cmd dispatch structure:**
- FUN_180001000 registers all UI params with IDs 1-0x20b
- FUN_180001a50 appears to be the **dynamic param update** handler (recalculates UI state based on checkboxes)
- The plugin handles standard AE commands: PARAMS_SETUP, RENDER, dynamic stream updates

---

## 3. UI Parameter List (from PARAMS_SETUP)

| ID | Name | Type | Flags/Notes |
|----|------|------|-------------|
| 1 | Color Keep | checkbox | default OFF |
| 2 | Threshold | float slider | 0.0, precision 4, 0x20 |
| 3 | Threshold Parameters | button group | |
| 4 | Premultiplied Color | checkbox | default OFF |
| 5 | Color Space | popup | 6 choices: RGB, HSV, Lab76, Lab94, YUV, YCrCb |
| 0x20a | Force Lower Precision | popup | 3 choices: Full, 16bit, 8bit |
| 6 | Per Color | checkbox | |
| 7 | Per Component | checkbox | |
| 8 | Threshold R/H/L/Y/Y_ | float | |
| 9 | Threshold G/S/a/U/Cr_ | float | |
| 10 | Threshold B/V/b/V/Cb_ | float | |
| 0xb | (separator) | separator | |
| 0xc | Edge Thin | button group | |
| 0xd | Amount (Edge Thin) | float | min/max: -100.0 to 100.0, precision 0.1 |
| 0xe | Distance Type (Edge Thin) | popup | 3 choices: Box, Approximate, Euclidean |
| 0x14 | (separator) | separator | |
| 0x10 | Edge Blur | button group | |
| 0x11 | Amount (Edge Blur) | float | 0.0 to 1.0 |
| 0x12 | Distance Type (Edge Blur) | popup | 3 choices |
| 0x13 | Direction | popup | 3 choices: Inside, Around, Outside |
| 0x15 | Number of Colors | integer | 1-25, step 64 |
| 0x20b | Enable Replace | checkbox | |
| **Per-color (up to 25):** | | | |
| 0x16 + k*5 | Color N | color picker | 0x20 flags |
| 0x17 + k*5 | Threshold N | float | 0.0-1.0 |
| 0x18 + k*5 | Threshold R/H N | float | 0.0-1.0 |
| 0x19 + k*5 | Threshold G/S N | float | 0.0-1.0 |
| 0x1a + k*5 | Threshold B/V N | float | 0.0-1.0 |
| 0x20c + k*3 | Use Color N | checkbox | |
| 0x20d + k*3 | Use Replace Color N | checkbox | |
| 0x20e + k*3 | Replace Color N | color picker | 0x20 flags |

---

## 4. RENDER Entry + 8/16/32-bit Branch

**Render entry:** `FUN_1800018e0` (address `0x1800018e0`)

```c
sVar1 = *(short *)(*param_4 + 0x2c); // pixel depth
FUN_18000a3d0(param_2, param_3, param_4, local_5a0, local_5a8, local_598, param_1);
if (sVar1 == 8) {
    FUN_1800094b0(...);  // 8-bit processing
} else if (sVar1 == 0x10) {
    FUN_180009000(...);  // 16-bit processing  
} else if (sVar1 == 0x20) {
    FUN_180009960(...);  // 32-bit float processing
}
```

Three separate render paths exist for each bit depth, all following the same architectural pattern.

---

## 5. Main Render Loop Structure (per-pixel / per-scanline / per-block)

The render loop is **per-pixel** with a **per-color iteration** pattern. The structure in each of FUN_1800094b0/9000/9960:

1. **Input setup:** Allocate temp buffers via PF Handle Suite
2. **Per-pixel color space conversion:** Call `FUN_180011450` (8-bit) / `FUN_1800114c0` (16-bit) / `FUN_180011530` (32-bit) to convert source pixel to HSV/Lab/YUV space
3. **Color matching loop:** For each of N colors (up to 25), check if pixel falls within threshold
4. **Distance calculation:** Uses per-color thresholds and selected distance type
5. **Edge processing (if enabled):**
   - Thin: 5x5 neighborhood check for edge pixels
   - Blur: sin-based distance field along inside/around/outside
6. **Replace color blending:** If replace enabled, blend with replace color based on alpha
7. **Write output pixel**

---

## 6. Important Helper Functions (Top 10)

| Address | Function Name (estimated) | Role |
|---------|--------------------------|------|
| `0x18000a3d0` | `readAllParams()` | Reads all UI parameters into a param block structure |
| `0x180001e00` | `processPixel_8bit()` | Core pixel processing for 8-bit input (per-pixel color match + threshold) |
| `0x1800029d0` | `processPixel_16bit()` | Core pixel processing for 16-bit input |
| `0x1800035d0` | `processPixel_32bit()` | Core pixel processing for 32-bit float input |
| `0x180009e10` | `RGBtoHSV()` | RGB → HSV conversion |
| `0x180009f50` | `RGBtoLab76()` | RGB → CIE Lab76 conversion (with nonlinear pow) |
| `0x18000a190` | `RGBtoYUV()` | RGB → YUV conversion |
| `0x18000a250` | `allocateHandle()` | AE handle allocation wrapper |
| `0x18000a980` | `distanceTransform()` | 2-pass Euclidean distance transform (for edge blur/thin) |
| `0x1800058a0` | `distanceField_short()` | Distance field computation for edge blur (16-bit variant) |

---

## 7. Key DAT_180* Constants

| Address | Name (estimated) | Value/Use |
|---------|------------------|-----------|
| `0x18001f698` | | Lab76 matrix coefficient |
| `0x18001f670` | | Lab76 matrix coefficient |
| `0x18001f650` | | Lab76 matrix coefficient |
| `0x18001f688` | `sqrt3/const` | Used in Lab76/HLS conversions |
| `0x18001f6a4` | `ONE` | 1.0f constant |
| `0x18001f6d0` | `PI_OVER_2` | π/2 for sin interpolation |
| `0x18001f6c0` | `ONE` | 1.0 for sin normalization |
| `0x18001f6e0` | `PI_TIMES_2` | 2π for edge blur frequency |
| `0x18001f6b0` | `PI` | π for edge blur |
| `0x18001f760` | `WRAP_MASK` | Bit mask for hue wrapping |
| `0x18001f770` | `NEG_ZERO` | Negative zero for float bit manipulation |

---

## 8. Similarity to OLMSmoother Techniques

This plugin shows **significant architectural similarity** to OLMSmoother's processing approach:

- **Color space conversions** (RGB→HSV, RGB→Lab76, RGB→YUV) — same helper functions as OLMSmoother
- **8-neighbor classification** — used in Edge Thin processing (checks 8-connected neighbors)
- **Cardinal scan / distance transform** — `FUN_18000a980` implements a two-pass Euclidean distance transform (DT), identical to OLMSmoother's DT approach
- **Sin-based curve evaluation** — Edge Blur uses `sin()` interpolation for smooth falloff (similar to OLMSmoother's curve evaluation)
- **Per-pixel color matching loop** with threshold comparison — same pattern
- **Hierarchical processing** (8-bit/16-bit/32-bit branches) — same architecture

**Key differences:** OLMColorKey focuses on color keying with multiple reference colors, while OLMSmoother focuses on temporal/spatial smoothing.

---

## 9. Porting Difficulty Estimate

**Difficulty: Medium**

**Reasons:**
- **Medium difficulty** because:
  - Heavy use of AE SDK suites (PF Handle, PF Param Utils, AEGP Dynamic Stream, AEGP Compute Cache) — needs proper suite acquisition on macOS
  - Complex UI parameter setup with dynamic per-color controls (25 colors × multiple params each)
  - Multiple color space conversions (HSV, Lab76, YUV, YCrCb) with non-linear math
  - Distance transform and edge processing have complex memory management
  - The 32-bit float path has slightly different logic than 8/16-bit

- **Not harder** because:
  - No x86 SIMD intrinsics detected
  - No inline assembly
  - Math is standard C++ (sinf, powf, sqrt, fmodf)
  - Clear function boundaries
  - Well-structured parameter reading

---

## 10. First Functions to Port (Starting Points)

### 1. `FUN_180001000` — **PARAMS_SETUP** (address `0x180001000`)
- Porting this first gives immediate UI feedback
- Identifies all parameter IDs and types
- Establishes the plugin parameter structure

### 2. `FUN_18000a3d0` — **Parameter Reader** (address `0x18000a3d0`)
- Central function that reads all UI parameters into the render structure
- Must be correct for rendering to work
- Defines the memory layout used by all render functions

### 3. `FUN_180009e10` — **RGB→HSV Converter** (address `0x180009e10`)
- Core color math used by all pixel processing
- No AE SDK dependencies — pure math
- Porting this establishes the color space conversion infrastructure