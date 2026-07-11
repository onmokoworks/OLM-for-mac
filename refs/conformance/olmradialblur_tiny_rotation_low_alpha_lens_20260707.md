# OLMRadialBlur tiny Rotation Low-Alpha Lens - 2026-07-07

Scope: analysis only. Case `case_0010`, witness `(1614,6)`.

## FACT: source alpha around output bright lobe

Command:

```sh
python3 - <<'PY'
from PIL import Image
import numpy as np
from pathlib import Path
base=Path('refs/win_references/20260604_olm/OLMRadialBlur')
src=np.array(Image.open(base/'case_0010_before_effects.png').convert('RGBA'))
ref=np.array(Image.open(base/'case_0010.png').convert('RGBA'))
wx,wy=1614,6
xs=range(wx-12, wx+13); ys=range(wy-12, wy+13)
bright=[]
low=[]
for y in ys:
  for x in xs:
    if 0<=x<src.shape[1] and 0<=y<src.shape[0]:
      if ref[y,x,0]>=200: bright.append((x,y,int(ref[y,x,0]),int(ref[y,x,3]),int(src[y,x,3]),src[y,x,:3].tolist()))
      if src[y,x,3] in (1,2): low.append((x,y,int(src[y,x,3]),ref[y,x].tolist(),src[y,x,:3].tolist()))
print('src_shape', src.shape)
print('witness_src_rgba', src[wy,wx].tolist())
print('witness_ref_rgba', ref[wy,wx].tolist())
print('25x25 valid pixels', sum(1 for y in ys for x in xs if 0<=x<src.shape[1] and 0<=y<src.shape[0]))
print('25x25 ref_bright_R_ge_200_count', len(bright))
print('25x25 src_alpha_counts', {a:int((src[max(0,wy-12):wy+13, max(0,wx-12):wx+13,3]==a).sum()) for a in [0,1,2,3,255]})
print('bright_pixels_x_y_refR_refA_srcA_srcRGB')
for row in bright: print(row)
print('low_alpha_src_pixels_alpha_1_or_2_in_25x25 count', len(low))
for row in low[:200]: print(row)
PY
```

Output:

```text
src_shape (1080, 1920, 4)
witness_src_rgba [0, 0, 0, 255]
witness_ref_rgba [255, 255, 255, 255]
25x25 valid pixels 475
25x25 ref_bright_R_ge_200_count 17
25x25 src_alpha_counts {0: 0, 1: 0, 2: 0, 3: 0, 255: 475}
bright_pixels_x_y_refR_refA_srcA_srcRGB
(1608, 0, 246, 255, 255, [0, 0, 0])
(1611, 0, 238, 255, 255, [0, 0, 0])
(1609, 1, 244, 255, 255, [223, 223, 223])
(1610, 1, 202, 255, 255, [0, 0, 0])
(1612, 1, 254, 255, 255, [0, 0, 0])
(1610, 2, 247, 255, 255, [0, 0, 0])
(1611, 2, 220, 255, 255, [0, 0, 0])
(1612, 2, 227, 255, 255, [0, 0, 0])
(1611, 3, 247, 255, 255, [0, 0, 0])
(1612, 3, 233, 255, 255, [0, 0, 0])
(1613, 3, 245, 255, 255, [0, 0, 0])
(1612, 4, 251, 255, 255, [0, 0, 0])
(1613, 4, 247, 255, 255, [0, 0, 0])
(1614, 4, 253, 255, 255, [0, 0, 0])
(1613, 5, 253, 255, 255, [0, 0, 0])
(1614, 5, 251, 255, 255, [0, 0, 0])
(1614, 6, 255, 255, 255, [0, 0, 0])
low_alpha_src_pixels_alpha_1_or_2_in_25x25 count 0
```

FACT: in the output-coordinate 25x25 window around `(1614,6)`, every valid input pixel has `src alpha=255`; there are no `alpha=1` or `alpha=2` pixels. The 17 reference bright pixels therefore do not spatially coincide with 1-code/2-code source alpha in that direct window.

## FACT: baseline polar source probe

Command:

```sh
refs/scripts/build_olmradialblur_cli.sh && python3 refs/scripts/run_reference_test.py refs/win_references/20260604_olm/OLMRadialBlur --run-dir /tmp/olmradialblur_low_alpha_baseline --case-id case_0010 --expected-effect "OLM RadialBlur" --command '"cli/OLMRadialBlur/olmradialblur_cli" --input "{input}" --params "{params}" --output "{output}" --witness-dump /tmp/olmradialblur_low_alpha_baseline/witness.json --witness-x 1614 --witness-y 6' --max-diff 255 --mean-diff 0.02 --nonzero-px-percent 1.7
```

Output:

```text
[OK]      case_0010            max=255 mean=0.0103
run_dir=/private/tmp/olmradialblur_low_alpha_baseline
```

Command:

```sh
python3 - <<'PY'
import json
from pathlib import Path
from PIL import Image
import numpy as np
run=Path('/tmp/olmradialblur_low_alpha_baseline')
w=json.loads((run/'witness.json').read_text())
cand=np.array(Image.open('/private/tmp/olmradialblur_low_alpha_baseline/candidate/case_0010.png').convert('RGBA'))
ref=np.array(Image.open('refs/win_references/20260604_olm/OLMRadialBlur/case_0010.png').convert('RGBA'))
wx,wy=1614,6
patch=cand[max(0,wy-12):wy+13, max(0,wx-12):wx+13]
refpatch=ref[max(0,wy-12):wy+13, max(0,wx-12):wx+13]
print('baseline_witness_sample_u8', w.get('sample_u8'))
print('baseline_witness_sample_rgba', w.get('sample_rgba'))
print('baseline_witness_alpha', w.get('alpha'))
print('baseline_witness_validity_alpha', w.get('validity_alpha'))
print('baseline_source_probe_origin', w.get('source_probe_origin'), 'size', w.get('source_probe_size'))
probe=w.get('source_probe', [])
counts={}
low=[]
for p in probe:
    a=p['rgba'][3]
    key=round(a*255)
    counts[key]=counts.get(key,0)+1
    if 0 < a <= 2/255 + 1e-6:
        low.append(p)
print('baseline_source_probe_alpha_u8_counts', dict(sorted(counts.items())))
print('baseline_source_probe_low_alpha_0_lt_a_le_2codes_count', len(low))
print('baseline_candidate_witness_rgba', cand[wy,wx].tolist())
print('baseline_candidate_25x25_R_ge_200_count', int((patch[:,:,0]>=200).sum()))
print('baseline_reference_25x25_R_ge_200_count', int((refpatch[:,:,0]>=200).sum()))
PY
```

Output:

```text
baseline_witness_sample_u8 [0, 0, 0, 255]
baseline_witness_sample_rgba [-0.00408606, -0.00408606, -0.00408606, 1]
baseline_witness_alpha 1
baseline_witness_validity_alpha 1
baseline_source_probe_origin [1598, 838] size [11, 13]
baseline_source_probe_alpha_u8_counts {255: 143}
baseline_source_probe_low_alpha_0_lt_a_le_2codes_count 0
baseline_candidate_witness_rgba [0, 0, 0, 255]
baseline_candidate_25x25_R_ge_200_count 0
baseline_reference_25x25_R_ge_200_count 17
```

FACT: the CLI witness's polar `source_probe` covers 143 cells at origin `[1598,838]`, and all have alpha rounded to 255. No `0 < alpha <= 2/255` polar source cell was present in that probe.

## FACT: Mac and decomp branch sites

Mac source audit command:

```sh
rg -n "SampleRGBAAEXAlpha\\(src|polar_valid\\[|const double alpha = polar\\.rgba|weighted_alpha > 1\\.0e-8|ComputeRadialBlurOuterSampleState|state\\.alpha > 1\\.0e-8|out->red =|out->alpha =" mac/OLMRadialBlur/OLMRadialBlur.cpp
```

Output:

```text
82:static RadialBlurOuterSampleState ComputeRadialBlurOuterSampleState(
108:	if (state.alpha > 1.0e-8) {
938:			SampleRGBAAEXAlpha(src, sx, sy, info.repeat_border != FALSE, sampled);
940:			polar_valid[(size_t)ri * angular_count + ai] = PolarValidSample(sx, sy, w, h, info.repeat_border != FALSE) ? 1.0f : 0.0f;
960:				const double alpha = polar.rgba[src_idx + 3];
967:			if (weighted_alpha > 1.0e-8) {
1005:					const double alpha = polar.rgba[src_idx + 3];
1013:				if (weighted_alpha > 1.0e-8) {
1035:					const double alpha = polar.rgba[src_idx + 3];
1043:				if (weighted_alpha > 1.0e-8) {
1075:				return polar_valid[(size_t)py * angular_count + px];
1077:			const RadialBlurOuterSampleState outer_state = ComputeRadialBlurOuterSampleState(
1080:			out->red = (A_u_char)ClampFloat((float)std::floor(outer_state.final_rgb[0] * 255.0), 0.0f, 255.0f);
1083:			out->alpha = (A_u_char)ClampFloat((float)std::floor(outer_state.alpha * 255.0 + alpha_quantize_epsilon), 0.0f, 255.0f);
```

FACT: `RenderRotation8` copies input alpha into `src`, samples it into `polar` via `SampleRGBAAEXAlpha`, and the rotation scatter paths treat any positive `polar.rgba[...,3]` as contributing alpha. The only visible gates are epsilon checks on accumulated alpha (`> 1.0e-8`), not a 1-code ownership threshold. A source-alpha threshold could technically be inserted before polar population or at the per-cell `const double alpha = polar.rgba[src_idx + 3]` contribution sites, but the measured case did not expose low-alpha cells there.

Decomp audit command:

```sh
rg -n "fVar5 = \\*\\(float \\*\\)\\(lVar28 \\+ \\*\\(longlong \\*\\)\\(param_1 \\+ 0xf252\\)\\)|if \\(fVar5 == 0\\.0\\)|FUN_180001000\\(\\*\\(longlong \\*\\)\\(param_1 \\+ 0xe\\)" decomp/OLMRadialBlur.aex.c.txt
```

Output:

```text
2158:          fVar5 = *(float *)(lVar28 + *(longlong *)(param_1 + 0xf252));
2159:          if (fVar5 == 0.0) {
2200:            FUN_180001000(*(longlong *)(param_1 + 0xe),pfVar25,iVar22,iVar22 * 4,fVar5,
```

FACT: the decomp `RenderRotation8` body reads the preserved side-channel at `param_1 + 0xf252`, branches on exact zero (`fVar5 == 0.0`), then calls the final inverse sampler on `param_1 + 0xe`. In this excerpt there is no observed comparison equivalent to `alpha > 1.5/255`; the observed branch is zero vs nonzero.

## FACT: temporary threshold trial

Temporary edit shape:

```cpp
for (size_t i = 3; i < src.rgba.size(); i += 4) {
    if (src.rgba[i] <= 1.5f / 255.0f) src.rgba[i] = 0.0f;
}
```

The edit was placed only in `render_olmradialblur_rotation`, immediately after input RGBA conversion, then removed after measurement.

Command:

```sh
refs/scripts/build_olmradialblur_cli.sh && python3 refs/scripts/run_reference_test.py refs/win_references/20260604_olm/OLMRadialBlur --run-dir /tmp/olmradialblur_low_alpha_threshold_rotation --case-id case_0010 --expected-effect "OLM RadialBlur" --command '"cli/OLMRadialBlur/olmradialblur_cli" --input "{input}" --params "{params}" --output "{output}" --witness-dump /tmp/olmradialblur_low_alpha_threshold_rotation/witness.json --witness-x 1614 --witness-y 6' --max-diff 255 --mean-diff 0.02 --nonzero-px-percent 1.7
```

Output:

```text
[OK]      case_0010            max=255 mean=0.0103
run_dir=/private/tmp/olmradialblur_low_alpha_threshold_rotation
```

Command:

```sh
python3 - <<'PY'
import json
from pathlib import Path
from PIL import Image
import numpy as np
run=Path('/tmp/olmradialblur_low_alpha_threshold_rotation')
w=json.loads((run/'witness.json').read_text())
cand=np.array(Image.open('/private/tmp/olmradialblur_low_alpha_threshold_rotation/candidate/case_0010.png').convert('RGBA'))
ref=np.array(Image.open('refs/win_references/20260604_olm/OLMRadialBlur/case_0010.png').convert('RGBA'))
wx,wy=1614,6
patch=cand[max(0,wy-12):wy+13, max(0,wx-12):wx+13]
refpatch=ref[max(0,wy-12):wy+13, max(0,wx-12):wx+13]
print('threshold_rotation_witness_sample_u8', w.get('sample_u8'))
print('threshold_rotation_witness_sample_rgba', w.get('sample_rgba'))
print('threshold_rotation_witness_alpha', w.get('alpha'))
print('threshold_rotation_witness_validity_alpha', w.get('validity_alpha'))
print('threshold_rotation_candidate_witness_rgba', cand[wy,wx].tolist())
print('threshold_rotation_candidate_25x25_R_ge_200_count', int((patch[:,:,0]>=200).sum()))
print('threshold_rotation_reference_25x25_R_ge_200_count', int((refpatch[:,:,0]>=200).sum()))
probe=w.get('source_probe', [])
counts={}
low=[]
for p in probe:
    a=p['rgba'][3]
    key=round(a*255)
    counts[key]=counts.get(key,0)+1
    if 0 < a <= 2/255 + 1e-6: low.append(p)
print('threshold_rotation_source_probe_alpha_u8_counts', dict(sorted(counts.items())))
print('threshold_rotation_source_probe_low_alpha_0_lt_a_le_2codes_count', len(low))
PY
```

Output:

```text
threshold_rotation_witness_sample_u8 [0, 0, 0, 255]
threshold_rotation_witness_sample_rgba [-0.00408606, -0.00408606, -0.00408606, 1]
threshold_rotation_witness_alpha 1
threshold_rotation_witness_validity_alpha 1
threshold_rotation_candidate_witness_rgba [0, 0, 0, 255]
threshold_rotation_candidate_25x25_R_ge_200_count 0
threshold_rotation_reference_25x25_R_ge_200_count 17
threshold_rotation_source_probe_alpha_u8_counts {255: 143}
threshold_rotation_source_probe_low_alpha_0_lt_a_le_2codes_count 0
```

FACT: applying a DG-style `alpha <= 1.5/255 -> 0` threshold to the Rotation CLI source alpha changed neither the witness nor the local bright-count: witness stayed `[0,0,0,255]`; candidate 25x25 `R>=200` count stayed `0`; reference bright-count stayed `17`.

## INFERENCE

The low-alpha / 1-code fringe ownership-threshold hypothesis is not supported for this `case_0010` witness. The decisive local source regions measured here are fully alpha-opaque (`255`), the polar source probe feeding the witness has no low-alpha cells, and the temporary threshold build is output-identical at the requested witness metrics. The hypothesis should be treated as rejected for this lane unless a different, binary-grounded Windows trace identifies a low-alpha source region outside the measured direct and polar windows.

## Restoration check

Command:

```sh
rg -n "1\\.5f / 255\\.0f|low_alpha|alpha threshold" cli/OLMRadialBlur/main.cpp mac/OLMRadialBlur/OLMRadialBlur.cpp
```

Output: no matches, command exit status `1`.

Command:

```sh
git diff --name-only -- cli/OLMRadialBlur/main.cpp mac/OLMRadialBlur/OLMRadialBlur.cpp notes/CONFORMANCE_LEDGER.md refs/conformance/olmradialblur_tiny_rotation_low_alpha_lens_20260707.md
```

Output before adding this report:

```text
cli/OLMRadialBlur/main.cpp
mac/OLMRadialBlur/OLMRadialBlur.cpp
notes/CONFORMANCE_LEDGER.md
```

FACT: the repository already had modified `cli/OLMRadialBlur/main.cpp`, `mac/OLMRadialBlur/OLMRadialBlur.cpp`, and `notes/CONFORMANCE_LEDGER.md` before this task. The temporary threshold hunk was removed; this report is the only intended new artifact from this analysis.
