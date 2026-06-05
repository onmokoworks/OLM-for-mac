# OLM Tools 移植 — Codex 引き継ぎメモ

最終更新: 2026-06-05 / 作成: Claude Code セッションからの引き継ぎ

## 0. ゴールと環境

- **目的**: OLM Tools の Windows 版 AEX 群を Ghidra 解析＋Windows 参照PNG/manifest
  検証に基づき Apple Silicon/macOS 版へ移植。各プラグインを「AEなしCLIハーネス」で
  検証できる状態にし、最終的に macOS/AppleSilicon の AE プラグインへ反映する。
- **作業ディレクトリ**: `/Users/onmk/Documents/Projects/Personal/OLM as`
- **重要な環境制約**:
  - この環境に **After Effects 実機が無い** → 「最終AEプラグイン検証」はここでは不可。
    AEなしCLIとmacOS `.plugin` ビルド確認までが現環境の到達点。
  - AE SDK はローカルにあり:
    `/Users/onmk/Documents/After Effects SDK/ae25.2_20.64bit.AfterEffectsSDK/AfterEffectsSDK/Examples`
    `scripts/setup_ae_sdk_links.sh` で repo root に ignored symlink
    `Headers` / `Util` / `Resources` を作る。これが無いとXcodeプロジェクトは
    `AEConfig.h`, `AEGP_SuiteHandler.cpp` などを見つけられない。
  - 2026-06-05時点で既存/追加Macプロジェクト
    `ColorKeep`, `OLMBlur`, `OLMColorKey`, `OLMDirectionalBlur`, `OLMRadialBlur`,
    `OLMToonDilate`, `OLMDistanceGradation`, `OLMSmoother`, `OLMSmoother2`
    は `xcodebuild -project mac/<Name>/Mac/<Name>.xcodeproj -configuration Debug`
    でビルド成功確認済み。`scripts/build_all_mac_plugins.sh` で8本まとめて
    SDK symlink作成、Debugビルド、`arm64`/`x86_64` slice確認、`codesign --verify`
    まで再現できる。
  - Ghidra は GUI/MCP を**ライブでは使っていない**。事前エクスポート済みの
    `decomp/*.aex.c.txt`（逆コンパイル）と `disasm/*.aex.asm.txt`（逆アセンブル）を読む。
    新規エクスポートが要るときは `scripts/ghidra_export_one.sh` / GhidraMCP(127.0.0.1:8080)。
  - Python は `python3`（Homebrew 3.14）。`scipy` を `--break-system-packages` で導入済み
    （ToonDilate CLI が距離変換に使用）。numpy / Pillow は既存。
- **停止条件**:
  - 追加のWindows AE差分参照（例: CUDA vs Software、`project_gpu_accel_type` 別PNG）が
    無いと CPU移植バグなのか AE Project Settings 差なのか判定できない地点に来たら、
    そのプラグインの推測実装を深追いせず、作業を停止してユーザーに追加参照取得を依頼する。
  - 追加参照は全プラグイン一括で必須ではない。まず既存参照で移植/CLI化を進め、
    構造的な不一致が出たプラグインだけ依頼する。

## 1. ⚠️ 最重要の注意: `ADBE Force CPU GPU=1` は実行経路判定に使わない

全 manifest のパラメータに **`Compositing Options > GPU Rendering`**
（`match_name = ADBE Force CPU GPU`）が記録され、値は全ケース **`1`**。
ただしこれは AE が各エフェクトに追加する組み込み/隠しプロパティらしく、
通常UI上で見えないことがある。

Windows AE 2025 / OLM 環境で確認した結果:

- AE version: `25.2x131`
- Project Settings が CUDA の時:
  `project_gpu_accel_type.current_name = CUDA`, raw `1813`
- Project Settings が Software Only の時:
  `project_gpu_accel_type.current_name = SOFTWARE`, raw `1816`
- どちらの場合も `Compositing Options > GPU Rendering /
  ADBE Force CPU GPU = 1`
- OLM plugin UIには GPU Rendering ボタンは基本見えない

結論: **`ADBE Force CPU GPU=1` は「GPUで実レンダーされた」という判定には使えない**。
manifestには参考値として残してよいが、実行経路は `project_gpu_accel_type`
などの別フィールドで記録・判断する。

ローカル確認では、mac移植コードに `PF_OutFlag2_SUPPORTS_GPU_RENDER_F32` や
AE GPU selector 実装の痕跡は見当たらない。Windows AEX文字列でも OpenCL/CUDA/OpenCV
痕跡が強いのは主に `DistanceGradation`, `OLMKiraKira`, `OLMToonDilate` で、
`OLMBlur`, `OLMColorKey`, `OLMDirectionalBlur`, `OLMRadialBlur`,
`OLMSmoother`, `OLMSmoother2`, `ColorKeep` では少なくとも文字列レベルの
GPU/OpenCL痕跡は薄い。

したがって、残差は **`ADBE Force CPU GPU=1` を根拠にGPU/CPU差と断定せず**、
以下のいずれかの可能性として扱う:

- AE Project Settings の renderer (`project_gpu_accel_type`) 差
- SmartRender / classic Render 経路差
- OpenCV/OpenCL 使用有無またはライブラリ実装差
- 逆コンパイル移植の未一致
- downsample / 透明RGB / 境界処理差

実測で3プラグインに同じ「境界・分類まわりの残差」傾向を確認:

- OLMColorKey erode … 0.48%（L1距離シェル上）
- OLMSmoother … CPU MLAA が約20倍過剰発火（構造的乖離）
- OLMToonDilate … 半径に比例した境界残差 0.02〜1.6%

**含意**: CPU移植が逆コンパイルに忠実でも、現参照に対して `max=0` が出ない可能性はあるが、
その原因を GPU と断定しない。厳密一致を確認したいなら、Windows AE側で
`project_gpu_accel_type` を manifest に別フィールドとして記録し、CUDA / SOFTWARE などの
Project Settings 差で同一ケースを撮り直して、PNG差分を見るのが最有効。
（このメモのこの節は最優先で頭に入れること）

## 2. 検証ハーネス（共通基盤）

- `refs/scripts/run_reference_test.py <refdir> --command '<cli template>' [--case-id ...]
  [--expected-effect '<name>'] [--max-diff N --mean-diff F --nonzero-px-percent P]`
  - 参照をコピー → `run_algorithm_cases.py` で各ケース実行 → `verify_manifest.py` で差分。
  - `{input}/{params}/{output}` がコマンドテンプレに展開される。
  - **今セッションで許容差ゲート（`--max-diff/--mean-diff/--nonzero-px-percent`）を pass-through 追加**。
    既定は全て 0（＝厳密一致要求）。回帰ガードに使う。
- `verify_manifest.py` の合否は max_diff/mean_diff/nonzero_px_percent **すべて**が閾値以下で `[OK]`。
  近似プラグインを緑にするには **3つとも**ゲートを与える必要がある（mean を忘れがち）。
- 参照: `refs/win_references/20260604_olm/<Plugin>/`（before/after PNG 対 + reference_manifest.json）。
- 追加参照: `refs/win_references/20260605_extra/`。
  - `OLMDistanceGradation`: 30 cases（`case_0030` は selected effect なし）
  - `OLMRadialBlur_img2`: 30 cases（Blur Type 2 / Rotation 系の追加参照）
  - `OLMSmoother2`: 12 cases
- アルゴリズム解説: `refs/ALGORITHM_HARNESS.md`。状態ボード: `notes/PORTING_BOARD.md`（詳細はこちらが一次情報）。

## 3. プラグイン別ステータス

| Plugin | AEなしCLI | 参照一致 | 実体 |
|---|---|---|---|
| OLMBlur | ✅ C++ | 全7ケース smoke OK（max<=1; 1/2/4 exact） | `cli/OLMBlur/main.cpp` |
| OLMColorKey | ✅ Python + C++ + Rust + Mac plugin(新) | C++: 1–4・7 exact / 5・6 erode 0.48%; Edge Blur C++ now matches Python exploratory residual (`case8 mean=1.0396`, `case9 mean=1.2503`); Mac plugin builds universal | `refs/scripts/olmcolorkey_cli.py`, `cli/OLMColorKey/main.cpp`, `rust/olmcolorkey_cli/`, `mac/OLMColorKey/` |
| OLMSmoother | ✅ C++(新) | v1単体CLIは過剰発火だが、OLMSmoother2 `--force-version 1` 互換probeが v1 refs 3ケース green (`mean=0.0055/0.0051/0.0200`)。v1単体の深追いは低優先 | `cli/OLMSmoother/`, `refs/scripts/smoke_olmsmoother2_v1_compat_cli.py` |
| OLMSmoother2 | ✅ C++(新) | 20260605追加参照 cases 1-4 を測定。disasm/objdump-firstで Color Key + Invert active-palette と non-invert scalar-key path を修正。key-path smoke cases2-4 は green。現状: case1 0.1832 / case2 0.0216 / case3 exact / case4 0.0189 after writeback-premul + key-path fixes | `cli/OLMSmoother2/`, `mac/OLMSmoother2/Mac/OLMSmoother2_port.cpp`, `notes/OLMSmoother2_ASM_FACTS.md` |
| OLMToonDilate | ✅ Python + C++ + Mac plugin(新) | C++: case1 mean 0.4762 / case2 0.0022 / case3 3.0676; Mac plugin builds universal | `refs/scripts/olmtoondilate_cli.py`, `cli/OLMToonDilate/main.cpp`, `mac/OLMToonDilate/` |
| OLMDistanceGradation | ✅ Python + Mac plugin | 新規20260605参照の11ケース smoke OK（max<=7 / mean<=0.11）。Threshold=0特別扱いをWindows参照に合わせてMac側も修正。背景色linearはPNG premul補正で緑化、blur/constant系はまだ赤測定対象 | `refs/scripts/olmdistancegradation_cli.py`, `refs/scripts/smoke_olmdistancegradation_cli.py`, `mac/OLMDistanceGradation/` |
| OLMDirectionalBlur | 🔎 実験CLI + Mac plugin(新) | front-only/no-noise は DIFF 計測中。Python/C++ direct probeあり。rotate-back denominator-alpha は neutral/negative。`rotated-aex-exact-rowdriver` は `exact-scatter-helper` と完全同値 (`4.4392/1.1761`) で、row-driver統合だけでは残差説明不能。次はASM引数対応の精査か、非opaque alpha / render-context scaleを識別できる追加Win参照なしに深追いしない。Mac plugin builds universal for 8bpc front-only/no-noise direct slice | `refs/scripts/olmdirectionalblur_cli.py`, `cli/OLMDirectionalBlur/main.cpp`, `mac/OLMDirectionalBlur/` |
| OLMRadialBlur | ✅/🔎 decomp解析 + Python/C++ Zoom/Rotation CLI + Mac plugin(新) | Rotation `0010` Python/C++ mean 0.0104; broad Python `0001` 1.9039 / `0002` 1.3077; broad C++ `0001` 1.9034 / `0002` 1.3071 after offset port; Zoom `0009` Python max=1 mean=0.0058 OK / C++ max=1 mean=0.0046 OK; C++ Zoom `0003..0005` max=8 mean=0.0059 OK with Size Variation ignored; Inner source-scatter/prepass baseline now measures old Inner `0011/0012/0013` at 25.2972 / 10.6222 / 21.2910; Edge Fade `0024/0025/0027` conditional seed edgefade-none improves means to 5.1129 / 3.9755 / 1.9204 but is red diagnostic due coverage regression; Mac plugin builds universal for 8bpc Zoom plus 8bpc outer-only Rotation/noise-off slice, including FFT fast path and Size Variation no-op pass-through | `notes/OLMRadialBlur_RE.md`, `refs/scripts/olmradialblur_cli.py`, `cli/OLMRadialBlur/main.cpp`, `mac/OLMRadialBlur/` |
| OLMKiraKira | 🔎 実験CLI + C++ scaffold + Mac plugin(新) | Python OpenCV two-temp probe added: baseline `0.8379/1.1627/1.7073` -> OpenCV primitive `0.8504/1.1570/1.0514`; explicit ROI/`dst=` alias probe is identical, so simple Mat aliasing is not the residual; C++ `aex-two-temp/no-fastpath` `0.8506/1.1570/1.0563`; Mac plugin now uses the same all-ray two-temp candidate path and builds universal、まだ DIFF | `refs/scripts/olmkirakira_cli.py`, `refs/scripts/smoke_olmkirakira_opencv_two_temp_probe_cli.py`, `refs/scripts/smoke_olmkirakira_opencv_two_temp_alias_probe_cli.py`, `cli/OLMKiraKira/main.cpp`, `mac/OLMKiraKira/` |

OLMSmoother2 最新メモ: 2026-06-06 に `--idx0-mode
none|suppress|half|quarter` 診断を追加し、no-key case_0001を測定。
`none=0.1832`, `suppress=0.2720`, `half=0.2069`, `quarter=0.2349` で全て悪化。
`idx=0x00` four-corner weightが単に強すぎる仮説は否定寄り。次は
class-plane source と `FUN_1800104d0` sample source のplane/timing splitを追う。
同日に `--plane-split-mode
none|sample-pre-setup|class-pre-setup|sample-pre-gamma|class-pre-gamma` も追加。
結果は `none=0.1832`, `sample-pre-setup=0.4606`,
`class-pre-setup=0.2049`, `sample-pre-gamma=0.4606`,
`class-pre-gamma=0.2049` で全て悪化。idx0/plane split の両方が否定寄りなので、
`refs/reference_requests/smoother2_no_key_grid_20260606.json` の追加Win参照で
Smoothness / Smooth Range / class-plane firingを切り分ける。

OLMKiraKira 最新メモ: `OLMKiraKiraLuminance` vtable は `+0x00 FUN_181150600`,
`+0x08 FUN_18114fd90`, `+0x10 FUN_18114ffd0`, `+0x18/+0x20` が1を返す小関数。
`FUN_18114fd90` の最終scale引数は Strength multiplier ではなく Brightness Gain
らしい。2026-06-05 の stack-argument 再確認で、seed exponent は normalized
Strength、final premul aggregation scale は Brightness Gain と見てよさそう。
これを Python/C++/Mac に反映し、`case_0003` は旧 `max=110 mean=6.4745` から
`max=60 mean=1.7073` まで改善。BrightnessGainをseed exponentへ強制するprobeは
`mean=58.2944` に大悪化したので、seed exponentは引き続きStrength側で扱う。
次は exact `Blur Mode=2` kernel/normalization と
rotate/crop border を詰める。
同日merge probeでは、現C++差分はalpha diff 0 / RGBのみ。単純な
`aex-add-rgb` / `aex-screen-rgb` は `case_0001/0002 mean` を約4.6-4.9へ悪化させ、
current premul平均 (`0.8382/1.1630`) より大幅に悪い。次はMerge modeの単純置換ではなく、
`Blur Mode=2` のOpenCV kernel size / anchor / border / normalizationを追う。
同日box-size probeでは、C++に `--box-size-mode length|radius` を追加して
`2*length+1` をray側へ一律適用したが、`radius` は `case_0001 mean=3.0404`,
`case_0002 mean=3.3702` へ悪化。baseline `length` (`0.8382/1.1627`) を維持し、
次は OpenCV warp/boxFilter anchor・border・crop・5バッファ合成の正規化を追う。
同日 `Glow Rotation` の配線漏れを C++ CLI / Python scaffold / Mac plugin に反映。
現参照3ケースはすべて rotation=0 なのでPNG差分は変わらないが、今後のランダム参照で
非ゼロ回転が出た時の互換穴を塞いだ。C++ smoke は `0.8382/1.1630/1.7023` のまま、
Python smoke は `0.8380/1.1630` のまま、Mac KiraKira Debug build は成功。
同日追加で C++ CLI の `--filter-border reflect|mirror` を実装し、Mac scaffoldも
REFLECT_101-style indexingへ寄せた。Python sweepでは `mirror` がcases1/2で
`0.8379/1.1627` とわずかに改善。C++ smokeは `0.8382/1.1627/1.7073`。
case3は `1.7023 -> 1.7073` に少し悪化するため、これはOpenCV境界寄せの小前進として扱う。
2026-06-06 OpenCV 4.5.5 parity confirmed the same two-temp results as 4.13
(`0.8504/1.1570/1.0514`); C++ `aex-two-temp/no-fastpath` is
`0.8506/1.1570/1.0563` and Mac is already ported to that candidate.
Explicit ROI/`dst=` alias probe also produced the same
`0.8504/1.1570/1.0514`, so the remaining target is not simple Mat aliasing;
focus on destination canvas, final composition, or another pre/post ray detail.
OpenCV probes are now available through the optional aggregate profile:
`python3 refs/scripts/smoke_all_algorithm_clis.py --profile opencv`. If the
selected Python lacks `cv2`, this profile reports `SKIP missing optional cv2`;
set `OLM_PROBE_PYTHON` to an OpenCV environment to reproduce the numeric
measurements.
Follow-up C++ `aex-two-temp-direct-back` was strongly negative
(`10.9852/11.6630/50.6637` vs `aex-two-temp` `0.8506/1.1570/1.0563`), so do
not model the final descriptor/dsize evidence as a naive final-size rotate-back
with the rotated temp center.
2026-06-06 追加: C++ `--aggregation-mode fd90-exact` を追加し、
`smoke_olmkirakira_cpp_aggregation_probe_cli.py` へ登録。`FUN_18114fd90` 風に
`ray > epsilon`、`clamp(ray * brightness)`、RGB加算、alpha union、final RGB normalizeを
式レベルで分けたが、`fd90-five/current` と同値 (`0.8381/1.1623/1.7003`)。
最終五枚集約は主残差ではない。次は `FUN_181150790` の中間 forward warp /
boxFilter / rotate-back dump、またはWin側per-ray isolate参照が有効。
同日 C++ `--warp-mode aex-two-temp --axis-fast-path false` は
`0.8506/1.1570/1.0563` でPython OpenCV probeとほぼ一致。手書きsampler差ではなく、
0/90度rayのfast pathをAEXが通すかどうかが主な分岐。新規
`smoke_olmkirakira_cpp_two_temp_no_fastpath_probe_cli.py` をred測定として追加。
サブエージェントASM確認ではAEX側0/90度fast pathの証拠はなく、全rayが
`FUN_181150790` を通る見方が強い。追加の
`--axis-fast-path-mode strength-nonzero` probeは
`0.8531/1.1555/1.0563` でcase3診断には有用だが、ASM根拠はall-ray
two-temp/no-fastpath側。
Mac `OLMKiraKira.cpp` も all-ray two-temp/no-fastpath候補へ更新済み。
`xcodebuild -project mac/OLMKiraKira/Mac/OLMKiraKira.xcodeproj -configuration Debug build`
成功、universal x86_64/arm64 と `codesign --verify` 確認済み。
同日 rotate/crop probe: Python CLIに `--crop-offset-y/x`, `--rotate-order`,
`--rotate-prefilter` を診断用に追加。crop offset `[-1,0,1]` は `(0,0)` が明確に最良で、
1px originズレ説は弱い。`order=3 --rotate-prefilter` はcases1/2を
`0.8234/1.1430` に改善するが、case3を `2.5628` へ悪化させるため、
C++/Mac既定のbilinearには未採用。`smoke_olmkirakira_rotate_probe_cli.py` を
expected-redとしてaggregateへ登録。
登録後の `python3 refs/scripts/smoke_all_algorithm_clis.py` は exit 0。
`OLMKiraKira Rotate probe` も `DIFF-observed`。
2026-06-05 追加: C++/Mac scaffold の rotate reshape を SciPy/OpenCV風の
`int(ptp(bounds) + 0.5)` に修正。半解像度 `case_0001` のC++差分は
`max=27 mean=0.9821` から `max=22 mean=0.8382` へ改善し、Python scaffold
`mean=0.8380` とほぼ一致。`case_0002` は `max=24 mean=1.1630` のまま。
Mac plugin note: `mac/OLMKiraKira/` は `OLM OLM Kira Kira` match name で追加済み。
現時点では C++ CLI の all-ray two-temp/no-fastpath 候補と同じ
OpenCV風 `warpAffine`/`boxFilter`/centered ROI copy レイ近似を AE SDK の
8/16/32bpc render path に接続した scaffold。2026-06-05 に
`xcodebuild -project mac/OLMKiraKira/Mac/OLMKiraKira.xcodeproj -configuration Debug build`
で universal `x86_64/arm64` build と `codesign --verify` を確認済み。
同日 `scripts/build_all_mac_plugins.sh` も KiraKira 追加後に完走し、
`all mac plugin builds verified (Debug)` を確認済み。
2026-06-05 verification refresh: RadialBlur C++ smokeは Zoom Offset
`case_0003..0005 max=8 mean=0.0059`、Zoom `case_0009 max=1 mean=0.0046`、
Tiny Rotation `case_0010 max=255 mean=0.0104` でOK。`scripts/build_all_mac_plugins.sh`
も再実行して全Mac Debug universal bundle確認まで再度成功。`notes/OLMRadialBlur_RE.md`
は current code に合わせ、Mac RadialBlur が Zoom slice と Rotation outer-only slice
を持つこと、Inner/Noise/unsupported Size Variation/16/32bpc はcopy inputであることを明記。
同日 `python3 refs/scripts/smoke_all_algorithm_clis.py` も exit 0 で完走。green gatesは通過し、
registered red-measurement はすべて `DIFF-observed` として観測できた。
Next candidates: OLMDirectionalBlur should pause before further image-only
tuning unless an asm argument mapping or extra nonopaque-alpha/render-context
scale refs are available; OLMKiraKira destination canvas / final composition /
pre-post ray details after simple Mat aliasing went neutral;
OLMRadialBlur Inner + Edge Fade caller-populated +0x10/+0x14 and
0xf250/0xf252 coupling. OLMSmoother stays v2-compat-first.
2026-06-06 subagent parallel review update: DirectionalBlur `FUN_1800013e0`
argument ownership is now mostly confirmed (`A.rgb` source, `alpha_or_valid`
contribution, denom sum, B.a max), so remaining front-only residual likely sits
in populate/edge/render-scale. KiraKira `FUN_181150790` uses in-place
`warpAffine(R14,R14)` then in-place `warpAffine(R12,R12)`, with second dsize
from R12, not final ray Mat. RadialBlur `FUN_180004640` maps `+0x38` polar
RGBA, `+0x40` scatter span/gate, `+0x48` prepass alpha, and `+0x50` factor;
existing param10 alpha probes are negative, so next Radial Inner work is
source-layer/sampler semantics for `+0x40` or prepass/scatter normalization.
Follow-up audit: all current old Inner / Edge Fade refs have `Size Variation=0`,
`Noise Variation=0`, and `Noise Layer=0`; `+0x40` cannot be strongly identified
from them. Added
`refs/reference_requests/radialblur_inner_size_variation_20260606.json`; do not
keep tuning `+0x40` until nonzero Size Variation refs are imported.
Second stop-condition review: KiraKira should wait for
`refs/reference_requests/kirakira_single_ray_20260606.json`; current equal-ray,
rotation-zero refs cannot isolate ray order/scalar/crop. DirectionalBlur should
wait for `refs/reference_requests/directionalblur_context_scale_20260606.json`;
current opaque refs and neutral/negative probes have exhausted useful PNG-only
tuning.
2026-06-05 REFLECT_101更新後にも `python3 refs/scripts/smoke_all_algorithm_clis.py`
を再実行し、exit 0。KiraKira の新baseline
(`Python 0.8379/1.1627`, `C++ 0.8382/1.1627/1.7073`) と
box-size probe (`radius 3.0404/3.3702`) を含め、green gates OK /
registered red-measurement は全て `DIFF-observed`。
2026-06-05 追加: C++ CLI に `--rotate-filter bilinear|bicubic` を診断用追加。
既定は `bilinear` のまま。Catmull-Rom風 `bicubic` は
`case_0001 mean=7.9161`, `case_0002 mean=8.0050`, `case_0003 mean=19.6771`
へ大悪化したため negative evidence。Python の `order=3 --rotate-prefilter`
改善を「任意のcubic採用」と解釈せず、次は OpenCV `warpAffine`/`boxFilter`
引数、anchor/border、または5バッファ合成正規化を追う。
2026-06-05 追加: C++ CLI に `--rotate-border edge|constant` と
`--warp-mode current|opencv-center` を診断用追加し、aggregateにも
`smoke_olmkirakira_cpp_rotate_border_probe_cli.py` と
`smoke_olmkirakira_cpp_warp_mode_probe_cli.py` を登録。OpenCV
`BORDER_CONSTANT`相当の外側tapゼロ化は全ケースで微改善したためC++既定と
Mac実装に採用: C++ baseline は `case_0001 mean=0.8381`,
`case_0002 mean=1.1623`, `case_0003 mean=1.7003`。一方
`opencv-center` は `0.8676/1.1658/1.9845` に悪化したため negative
evidence。中心/crop規約は現行維持、次は exact `boxFilter`/aggregation。
2026-06-05 追加: C++ CLI に `--glow-normalize union|sum` と
`--aggregation-mode current|fd90-five` を診断用追加し、aggregateにも
`smoke_olmkirakira_cpp_glow_normalize_probe_cli.py` と
`smoke_olmkirakira_cpp_aggregation_probe_cli.py` を登録。`sum`正規化は
`2.3386/2.6722/21.7350` に大悪化。`fd90-five` は current と実質同値
(`0.8381/1.1623/1.7003`, case_0001 の nz が1pxだけ差)。よって最終
5バッファ集約は主犯ではなさそうで、次は exact `boxFilter` の
phase/anchor/border、または exact `warpAffine`/crop sampling details。
2026-06-05 追加: C++ CLI に `--box-anchor-mode
opencv|floor-left|origin|end` を診断用追加し、
`smoke_olmkirakira_cpp_box_anchor_probe_cli.py` をaggregateへ登録。
`opencv` は baseline維持 `0.8381/1.1623/1.7003`、`floor-left` は
`0.8381/1.2197/2.5483`、`origin` は `7.6446/8.5897/41.1855`、
`end` は `7.7687/8.6222/41.2080`。anchor/phaseはnegative evidenceなので
既定`opencv`維持。次は boxFilter border/rounding/output-depth か
warpAffine sampling/crop。
2026-06-05 追加: C++ CLI に `--box-normalize true|false` を診断用追加し、
`smoke_olmkirakira_cpp_box_normalize_probe_cli.py` をaggregateへ登録。
`true` は baseline維持 `0.8381/1.1623/1.7003`、`false` は
`151.5376/148.1213/88.8005` に大悪化。OpenCV `boxFilter` は
normalize=true と見る。残差は boxFilter border/rounding/output-depth か
rotate/crop coordinate details。
2026-06-05 追加: C++ CLI に `--box-output-depth float|u8-each|u16-each` を
診断用追加し、`smoke_olmkirakira_cpp_box_output_depth_probe_cli.py` を
aggregateへ登録。`float` は baseline維持 `0.8381/1.1623/1.7003`。
`u8-each` は `0.8565/1.1601/1.9693` でcase_0002以外悪化。
`u16-each` は `0.8381/1.1623/1.7002` でほぼ同値。中間8bit/16bit化は
主犯ではないため既定float維持。
2026-06-05 追加: C++ CLI に `--crop-mode floor|ceil|round` を診断用追加し、
`smoke_olmkirakira_cpp_crop_mode_probe_cli.py` をaggregateへ登録。3モード全て
`0.8381/1.1623/1.7003` で同値。現参照ではfloor-vs-ceil crop originは
露出していない。次は `warpAffine` sampling/output-size math、rotated
intermediateのOpenCV border、または別のpre/post ray detail。
2026-06-05 追加: C++ CLI に `--rotate-size-mode round|floor|ceil` を診断用追加し、
`smoke_olmkirakira_cpp_rotate_size_probe_cli.py` をaggregateへ登録。`round` は
baseline維持 `0.8381/1.1623/1.7003`、`floor` は
`0.9949/1.2704/4.2024`、`ceil` は `0.9823/1.2645/3.9547` に悪化。
rotate output-size roundingは既定round維持。次は `warpAffine` pixel
sampling/interpolation、rotated intermediateのOpenCV border、または別の
pre/post ray detail。
2026-06-05 追加: RadialBlur C++ CLI に `--inner-alpha-mode
max|sum|outer|inner|input` と Edge Fade parse を追加し、
`audit_olmradialblur_manifest.py` も Edge Fade列を表示するよう更新。
現Inner参照 `0011..0013` は Edge Fade が全て0。C++ alpha-mode probeは
`max 63.4207/15.4790/20.0603`, `sum 54.7860/17.6602/19.8535`,
`outer 63.4207/14.4709/20.8267`, `inner 92.1469/14.2504/21.4453`,
`input 92.1469/13.1655/22.2481`。単一alpha accumulatorでは閉じないため、
次は `FUN_1800024c0 -> FUN_180001c90` の per-source validity/scatter order を追う。
Subagent auditでは、Innerは destination row gather ではなく source-cell
scatterで、`FUN_180002780` prepassがsource/baseを作った後、
`FUN_180001c90` tail offset `1..` をouter then innerで撒く形が本命。
次パッチはpolar RGBAとは別にvalidity planeとscatter-alpha/base/max-alpha
bufferを作る方向。
2026-06-05 追加: C++ CLI限定で `--inner-source-scatter-prepass` を追加し、
`smoke_olmradialblur_cpp_inner_source_scatter_prepass_cli.py` とaggregateへ登録。
結果は `case_0011 mean=22.1632`, `case_0012 mean=16.6793`,
`case_0013 mean=19.8113`。default C++ Inner
`63.4207/15.4790/20.0603` と比べ、0011は大改善、0013は微改善、0012は
悪化。source-cell scatter/prepass 仮説は本命寄りだが未完成なので、Macへ
portせず `FUN_180002780` validity/prepass と `FUN_180001c90` span/weightを
詰める。
2026-06-05 追加: RadialBlur C++ CLI に
`--inner-scatter-span-scale-mode one|source-alpha|input-alpha` を診断用追加し、
`smoke_olmradialblur_cpp_inner_span_scale_probe_cli.py` をaggregateへ登録。
`FUN_180001c90` の `iVar10 = int(effective_span * param_10)` を、簡易的に
source/input alphaで代用できるか確認した。current best-ish variantでは
`one 25.2972/10.6222/21.2910`、`source-alpha 29.8855/12.6410/21.2560`、
`input-alpha 29.8855/12.6410/21.2560`。単純alpha scaleは0011/0012で悪化し、
0013だけ微改善なので未採用。次は `param_1+0x10` の exact prepass-alpha
生成/サンプリングを追う。
2026-06-06 追加: サブエージェントASM監査で、RadialBlur Innerは
`FUN_180002780(+0xe,+0x12,+0x14,...,+0xf250,+0xf252)` の後に
`FUN_1800024c0(+0xe,+0x12,+0x10,validity,...,+0xf250,+0xf252)` が走ることを再確認。
prepass factorは`+0x14`、scatter alphaはprepass後`+0x12`、span/gateは別サンプル`+0x10`。
C++ CLIの `--inner-scatter-span-scale-mode source-alpha|input-alpha` を実際の
`effective_span=int(span*param10)` に接続し直し、
`smoke_olmradialblur_cpp_inner_aex_split_probe_cli.py` を再実行。結果は既存赤行列どおりで、
直接alpha span/gateは一部old-innerだけ改善しEdge Fadeを悪化させるため未採用。
`+0x14` が最後の曖昧点になったら、Size Variation / variation-layer factor有効のWin参照が必要。
2026-06-05 追加: RadialBlur C++ CLI に
`--inner-wrap-mode circular|aex-next-row` を診断用追加し、
`smoke_olmradialblur_cpp_inner_wrap_probe_cli.py` をaggregateへ登録。
`FUN_180001c90` inner branch の負方向wrapが `param_5 + 1` 行へ見えるため
検証したが、`circular 25.2972/10.6222/21.2910` に対し
`aex-next-row 26.1534/10.6248/21.2910` で悪化/同等。採用せず、
次は exact `FUN_180002780` prepass-alpha と weight table 生成を見る。
2026-06-05 追加: Win側で追加参照を取りやすくするため、
`refs/reference_requests/README.md` と
`refs/reference_requests/radialblur_inner_20260605.json` を追加。
RadialBlur InnerのSOFTWARE/CUDAペア、Edge Fadeあり、opaque/alpha素材別、
Quality別ケースを指定している。`ADBE Force CPU GPU` は参考値のみ、
実行経路ラベルは `project_gpu_accel_type.current_name/raw` を使う。

### OLMColorKey（cases 1–7 まで実装済み）
- 簡易経路 `render_rgb_binary`（RGB/1色/mean-delta閾値）= cases 1–4 exact。
- 拡張経路 `render_extended`（premultiplied / per-color / per-component / Edge Thin）:
  - キーイング: premult した RGB を per-channel box で比較。global Threshold は 8bit 半歩
    `0.5/255` に正規化 → 実質「完全バイト一致」。キーは黒なので `matched = premult RGB == 0`。
    Color Space=4 は Lab94（黒は全色空間で不変なので今回は無関係）。出力は二値αで premult。
  - Edge Thin（Distance Type 2）= 直交のみ2パスチャンファ = **厳密 L1**。
    - **Dilate（Amount>0）厳密一致**（case_0007 max=0）。`matte |= dist_to_matte <= Amount`。
    - **Erode（Amount<0）残差 9860px(0.48%)**。`matte &= dist_to_nonmatte > |Amount|+1` が最良。
      残差は全て `L1==17` シェル上（AE/CPU経路差または未移植境界条件の可能性）。
  - Edge Blur（case_0008/0009）は部分実装済みで regression guard あり。
    `smoke_olmcolorkey_edgeblur_cli.py` は ok=2（case8 max=79 mean=1.0396 /
    case9 max=255 mean=1.2503）。フレーム端をEdge Blur境界として扱わない修正と、
    Edge Blur feather weight をRGBにも掛けるpremult修正で改善済み。
    C++ CLIにもEdge Blur/Lab76 scaffoldを追加し、
    `smoke_olmcolorkey_cpp_edgeblur_cli.py` は ok=2（case8 mean=1.5386 / case9 mean=1.2503）。
    Rust互換CLIで見つけた1D EDT境界処理をC++へ反映し、case9 はPython探索版と同等まで改善済み。
    Edge Blur内部境界/透明RGBの厳密化と replace color は未完。
- 検証: `python3 refs/scripts/smoke_olmcolorkey_cli.py`（1–4, ok=4）。5–7 は run_reference_test 直叩き。
- C++移植核: `cli/OLMColorKey/main.cpp`。
  `refs/scripts/build_olmcolorkey_cli.sh && python3 refs/scripts/smoke_olmcolorkey_cpp_cli.py`
  で cases 1–7 を検証。RGB 1–4 exact、Edge Thin 7 exact、5/6 はPython版と同じ既知erode残差。
- Mac AEプラグイン: `mac/OLMColorKey/`。
  `ColorKeep` Xcodeプロジェクトを元に追加。`OLM Color Key` match name、2.3.1 develop。
  AE側レンダー核はC++ CLIの cases 1–7 相当（RGB/simple key、premultiplied
  per-component/per-color、Edge Thin L1）を移植。2026-06-05 に Edge Blur の
  RGB/alpha feather scaffold と Lab76 定数経路もMac pluginへ反映済み。
  Edge Blur境界/透明RGBの厳密化と Replace はまだ未確定範囲。
  `xcodebuild -project mac/OLMColorKey/Mac/OLMColorKey.xcodeproj -configuration Debug build`
  後、`file` で `arm64` + `x86_64`、`codesign --verify` OKを確認済み。

### OLMToonDilate（cases 1–3 実装済み）
- 唯一の効くパラメータ = **Search Radius**（13, 27）。8bpc。case1/2 は半解像度(960x540)、
  case3 は全解像度(1920x1080)。
- アルゴリズム（`decomp/OLMToonDilate.aex.c.txt` FUN_1801a6150）:
  - seed = `alpha==255`、`R_eff = ceil(SearchRadius * img_w/comp_w)`、
    `fill = ~seed & (chebyshev_dist_to_seed <= R_eff)`、色 = **最近傍不透明画素のRGBA**（Euclid最近傍で厳密）。
  - **Chebyshev（8近傍チャンファ）が正解の距離**（case3: cheb 32931 vs euclid 134259）。
- Python CLI: `refs/scripts/olmtoondilate_cli.py`（numpy+Pillow+**scipy**）。`--comp-width 1920` を渡す。
- C++ CLI: `cli/OLMToonDilate/main.cpp`（8近傍BFSでChebyshev距離とコピー元座標を伝播）。
  ビルド: `refs/scripts/build_olmtoondilate_cli.sh`。
- Mac AEプラグイン: `mac/OLMToonDilate/`。
  `OLM Toon Dilate` / match name `ADBE OLMToonDilate`。パラメータは `Search Radius`
  のみ。AE側レンダー核は C++ CLI と同じ 8近傍BFS/Chebyshev 伝播で、8/16/32bpc
  SmartRender と classic Render に対応。SmartRender では `PF_CheckoutResult.ref_width`
  を使って `R_eff = ceil(SearchRadius * output_width / comp_width)` の comp幅スケールを
  伝播する。AE実機でのホスト検証はまだ未実施。
- 検証:
  - `python3 refs/scripts/smoke_olmtoondilate_cli.py`（許容差ゲート付き、ok=3）。
  - `refs/scripts/build_olmtoondilate_cli.sh && python3 refs/scripts/smoke_olmtoondilate_cpp_cli.py`
    （C++版もok=3。case2/3はPython版より残差が小さい）。
- 残差は境界差。`project_gpu_accel_type` 別値の参照が取れれば、CPU版が厳密かを確認できる。

### OLMSmoother（cases 1–3, key-off 8bpc）
- これは **MLAA系のエッジAA**（ブラーではない）。"Do Smooth Range"=6 は実は **Tolerance** スライダ。
- **既存 mac 版ポート `mac/OLMSmoother/Mac/OLMSmoother_port.cpp` を AEなしでビルドする CLI を新規作成**:
  - シムヘッダ `cli/OLMSmoother/shim/{OLMSmoother.h, AEFX_SuiteHandlerTemplate.h}`
    （AE SDK の最小スタブ。`AEFX_SuiteScoper` を自前 `PF_Iterate8` ループで裏打ち）。
  - `cli/OLMSmoother/main.cpp` が port.cpp を `#include` して `DispatchRender(...,8)` を直叩き。
    PNG↔ARGB変換。ビルド: `refs/scripts/build_olmsmoother_cli.sh`。
- **結果: 動くが過剰発火**。参照は ~868–2348px しか変えないのに、port は 30k–45k px 変える。
  - トレランス掃引: tol 6/30 は同一(30110px)、tol≥100 で 0px。**どの tol でも参照の868pxを再現できない**
    → 閾値スケールのバグではなく **構造/レンダー経路差**。
- 検証: `refs/scripts/build_olmsmoother_cli.sh && python3 refs/scripts/smoke_olmsmoother_cli.py`
  （意図的に緑化していない＝DIFF表示のまま、正直な状態）。

### 残り3つ（Directional/Radial/KiraKira）— 手続き型
- いずれも `Noise Type / Seed / Thickness / Size Variation / Quality` を持つ **乱数駆動の
  ストリーク/スピン/ズーム効果**。RadialBlur に素朴なズームブラー近似をかけても参照とほぼ
  相関しない（実測: identity比でほぼ改善なし）。
- RNG/ノイズ生成まで一致させないと pixel-exact にならない。現環境では完全一致は重い。
- 着手するなら decomp から RNG/ノイズ生成と幾何カーネルの両方を抽出する重RE。RadialBlur が
  比較的構造的なので着手するならそこから。

### OLMDirectionalBlur（front-only/no-noise 実験CLI）
- `refs/scripts/olmdirectionalblur_cli.py` に `--rgb-normalize` を追加。
  旧 `alpha-sum` 正規化は入力の赤チャンネル総量をほぼ保存していたが、AEX参照は
  `case_0001` で赤総量を明確に減衰させるため、`front-strength` 正規化を標準smokeへ採用。
- `smoke_olmdirectionalblur_cli.py` は
  `--angle-sign -1 --sample-sign -1 --strength-scale auto --rgb-normalize front-strength`。
  cases 1..4 は `mean=4.4483` 付近から `mean=4.0897` 付近へ改善。
  case5 は `mean=1.1838` から `1.1931` へ少し悪化するため、まだ正解ではない。
- C++版 `cli/OLMDirectionalBlur/main.cpp` と
  `refs/scripts/build_olmdirectionalblur_cli.sh` /
  `refs/scripts/smoke_olmdirectionalblur_cpp_cli.py` を追加。
  Python direct probe と同じ差分（cases 1..3 `max=241 mean=4.0897`,
  case4 `mean=4.0900`, case5 `max=247 mean=1.1931`）を出す。
  これは次のREを高速化するためのCLI足場。
- 2026-06-05: C++ CLIに `back_sharp_tail` のパラメータ配線を追加。
  Python scaffold / Mac plugin には既にあった項目。front-only cases 1..5 の
  出力は変わらず、`smoke_olmdirectionalblur_cpp_cli.py` は上記DIFF値のまま。
  Back blur自体はまだ未実装で、cases 6..9 実装前の土台整理。
- 同日 Python/C++ CLIに測定用 `--direction both` /
  `--ignore-noise-variation` / `--rgb-normalize total-strength` を追加し、
  `refs/scripts/smoke_olmdirectionalblur_back_probe_cli.py` と
  `refs/scripts/smoke_olmdirectionalblur_cpp_back_probe_cli.py` をaggregateへ登録。
  Noiseを無視したback probeなので赤のままだが、Python/C++とも
  `case_0006/0007 max=204 mean=0.8383`, `case_0008 max=250 mean=0.7800`,
  `case_0009 max=209 mean=3.3248` で一致して走る。
  Noise Variationと正確なFront/Back合成はまだ未実装。
- Mac AEプラグイン: `mac/OLMDirectionalBlur/` を追加。
  `OLM DirectionalBlur` / match name `OLM Directional Blur`。現在のAEレンダー核は
  C++ direct/front-strength baselineに合わせた 8bpc front-only/no-noise sliceのみ。
  Back Strength、Alpha Fade、Noise Variation、16/32bpc は未確定なので入力コピー。
  `xcodebuild -project mac/OLMDirectionalBlur/Mac/OLMDirectionalBlur.xcodeproj -configuration Debug build`
  後、`file` で `arm64` + `x86_64`、`codesign --verify` OKを確認済み。
- 同じC++ CLIに `--algorithm rotated` も追加。
  `refs/scripts/smoke_olmdirectionalblur_cpp_rotated_cli.py` は
  `case_0001 max=254 mean=4.4483`, `case_0005 max=246 mean=1.2174`。
  direct/front-strengthの方が現DIFFは小さいが、rotatedはAEXの
  rotate-buffer/horizontal-scatter構造に近く、次のcomponent map移植の土台。
- `--algorithm rotated-gather` で `FUN_180001000` 風のpre-scatter alpha gatherも試した。
  `refs/scripts/smoke_olmdirectionalblur_cpp_rotated_gather_cli.py` は
  `case_0001 max=254 mean=4.8362`, `case_0005 max=246 mean=1.2796` と悪化。
  つまり単純なgather追加では足りず、次は `FUN_1800038d0` の `param_11` 係数、
  Size Variation、Front/Back fade、component map center/half-height項を合わせる必要がある。
- `--algorithm rotated-alpha` / `rotated-aex` で `FUN_180001ec0` 風のalpha-weighted bilinear
  rotation（AEX風の内側境界条件込み）も追加済み。`FUN_180001000` のgather長はBlur Strengthではなく
  Front/Back Alpha Fade (`+0x4c`/`+0x54`) と判明したため修正済み。current refs 1..5 は
  Alpha Fade 0 なのでgatherは実質no-op。`rotated-aex` は
  `case_0001 mean=4.7505`, `case_0005 mean=1.3802` で、plain `rotated`
  (`4.4483`, `1.2174`) よりまだ悪い。
- `--algorithm rotated-map` で `FUN_1800028e0` 風のconnected-component mapも追加済み。
  valid alpha maskから component area/minY/centerY/halfHeight を作り、
  `pow(area/maxArea, Size Variation) * SharpTail(row, centerY, halfHeight)` を
  `FUN_1800013e0` の `param_11` と同様に scatter距離/weight indexへ反映する。
  今回のfront-only refsはほぼ単一成分なので `rotated` と同値
  (`case_0001 mean=4.4483`, `case_0005 mean=1.2174`)。
  `rotated-map-aex` はまだ悪化 (`case_0001 mean=4.7505`, `case_0005 mean=1.3802`)。
- `--algorithm rotated-preserve-alpha` を赤観測smokeとして追加済み。回転バッファRGBは
  使いつつ rotate-back 後のalphaを入力alphaに戻す診断分岐で、
  `case_0005 mean=1.1831` と current rotated RGB系では最良寄り。これはalpha実装済みの
  主張ではなく、次に詰めるべき箇所が rotate-back alpha coupling / output compositing
  であることを固定するための測定。`rotated-strict`（AEX風の内側限定bilinear）は
  `case_0001 mean=4.7505`, `case_0005 mean=1.3802` と悪化したため、border clipping
  単独では主因ではない。
- 2026-06-05 追加: `rotated-map-dest-coeff` は `case_0005 mean=1.3063` へ悪化し、
  component係数は現行のscatter-origin/source側が正しそう。
  `rotated-front-strength-preserve-alpha` は `case_0001..0003 mean=4.0897`,
  `case_0004 mean=4.0900`, `case_0005 mean=1.1927` で、direct相当のcase1群を保ったまま
  case5を少し改善。`refs/scripts/smoke_olmdirectionalblur_cpp_rotated_front_strength_preserve_alpha_cli.py`
  を expected-red としてaggregate登録済み。まだMac plugin対応sliceではなく診断用。
- `--algorithm rotated-alpha-sum` は赤観測smokeとして追加済み。scatter alphaをsum/clamp
  するだけでは `case_0001 mean=4.4483` 維持、`case_0005 mean=1.2173` と
  ほぼ無効で、nonzero diff pixelsは増える。単純なalpha sumではない。
- `--algorithm rotated-map-alpha-coeff` も赤観測smokeとして追加済み。component map /
  row-driver係数を出力alpha max寄与に掛ける診断だが、`case_0001 mean=4.4483` 維持、
  `case_0005 mean=1.2276` と悪化。係数は直接alphaを薄めるものではなく、
  scatter距離 / Gaussian index再配置として扱うのが現時点の読み。
- `FUN_180001ec0` rotate-back はalpha-weighted bilinear（4隅alpha和でRGB重みを
  正規化し、alpha和を出力）として読める。ただし `rotated-alpha-out` は現refsの
  `case_0001/0005` では `rotated` と同値で、この参照だけでは主因になっていない。
- `--algorithm rotated-aex-pad` は AEX風の作業バッファ寸法
  `2 - int(diagonal * -0.5)` を使う赤観測。`case_0001 mean=4.4483`,
  `case_0005 mean=1.2174` で通常 `rotated` と同値。pad寸法差は現refsの主因ではない。
- `--algorithm direct-map` は direct sampler に component-map の Size Variation /
  Sharp Tail 係数を掛ける赤観測。`case_0001 mean=4.0897 -> 4.0883` の微改善のみ、
  `case_0005 mean=1.1931` は不変。row-driver係数は一部効くが主残差ではない。
- `--algorithm rotated-aex-init` / `rotated-map-aex-init` で、AEXの
  `memcpy(_Dst,_Src)` → scatter → `param_6[0x1010]` 正規化を「weight-sum初期値0」
  と読む仮説も測定済み。結果は `case_0001 mean=4.7724`,
  `case_0005 mean=1.3862` で、`rotated-aex` より悪化。単純な中心サンプル除外説は
  現refsの missing piece ではない。
- decomp再確認: `FUN_1800038d0` は `+0x8118` component map由来の
  `pow(area/maxArea, SizeVariation)` を `FUN_180001000` の Alpha Fade pre-pass
  にも渡し、その後 `FUN_1800013e0` scatter に渡す。現 cases 1..5 は
  Alpha Fade 0 なのでこの差は主因ではないが、back/noise/fadeケースでは必須。
  `FUN_1800013e0` の `param_11` は距離短縮と Gaussian index 再配置の両方に効く。
- 次の本命は `FUN_1800013e0` / `FUN_1800038d0` の scatter 正規化・Size Variation・Sharp Tail
  マップの再現。単純なAngle向き/Strength scaleでは詰め切れない。

## 4. このセッションで触ったファイル（git 未コミット）

- 追加: `refs/scripts/olmtoondilate_cli.py`, `refs/scripts/smoke_olmtoondilate_cli.py`,
  `refs/scripts/smoke_olmsmoother_cli.py`, `refs/scripts/build_olmsmoother_cli.sh`,
  `cli/OLMSmoother/main.cpp`, `cli/OLMSmoother/shim/OLMSmoother.h`,
  `cli/OLMSmoother/shim/AEFX_SuiteHandlerTemplate.h`, `notes/HANDOFF_CODEX.md`(これ)。
- 変更: `refs/scripts/olmcolorkey_cli.py`（拡張経路追加）, `refs/scripts/run_reference_test.py`
  （許容差ゲート pass-through）, `notes/PORTING_BOARD.md`（全プラグインの所見）, `.gitignore`
  （`cli/*/olm*_cli` を ignore）。
- ⚠️ 既存の変更を勝手に revert しないこと。手動編集はパッチ志向。生成物/一時ファイルは `/tmp` か
  ignore 済みパスへ。`__pycache__` は消す。

## 5. 推奨される次の一手（優先順）

1. **既存参照で移植/CLI化を進める**。`OLMRadialBlur` は Zoom Offset `case_0003..0005`
   のC++核に加えて、大Strength Zoom `case_0009` もC++ FFT畳み込みで通った。
   Mac AEプラグインにも 8bpc Zoom/no-inner/no-noise スライスとして載せており、
   大Strength用FFT高速経路と Size Variation no-op 通過も移植済み。次はAE実機ロード/描画確認。
2. **構造的な不一致で詰まったら停止**。その時点で Windows AE側に
   `project_gpu_accel_type` を manifest に記録した追加参照（CUDA / Software など）を依頼する。
   これは全プラグイン一括の前提作業ではなく、詰まったケースだけの切り分け手段。
3. **AE実機で最終プラグイン検証**（ゴールの第2軸。現環境では不可）。
4. 既存CLIの仕上げ: ColorKey の Edge Blur(8/9)・非黒キーの色空間、ToonScale の comp幅伝播の自動化。

## 6. 全スモーク再現コマンド（回帰確認用）

```sh
cd "/Users/onmk/Documents/Projects/Personal/OLM as"
python3 refs/scripts/smoke_all_algorithm_clis.py --profile quick # green gates only; 2026-06-05 OK (21 checks)
refs/scripts/build_olmblur_cli.sh && refs/scripts/build_olmsmoother_cli.sh && refs/scripts/build_olmtoondilate_cli.sh && refs/scripts/build_olmradialblur_cli.sh
refs/scripts/build_olmkirakira_cli.sh              # OLMKiraKira C++ scaffold
scripts/build_all_mac_plugins.sh                  # Mac plugins: build + universal/codesign verify
python3 refs/scripts/smoke_olmblur_cli.py            # ok=7 (max<=1 gate)
python3 refs/scripts/smoke_olmcolorkey_cli.py      # ok=4 (exact)
python3 refs/scripts/smoke_olmcolorkey_extended_cli.py # ok=3 (gated erode residual)
python3 refs/scripts/smoke_olmcolorkey_edgeblur_cli.py # ok=2 (exploratory edge blur guard)
python3 refs/scripts/smoke_olmtoondilate_cli.py    # ok=3 (gated regression guard)
python3 refs/scripts/smoke_olmtoondilate_cpp_cli.py # ok=3 (C++ BFS port; lower residual on cases 2/3)
python3 refs/scripts/smoke_olmradialblur_cpp_cli.py # ok=3 (C++ Zoom Offset; Size Variation ignored)
python3 refs/scripts/smoke_olmradialblur_cpp_inner_cli.py # DIFF (C++ Inner measurement: 63.4207 / 15.4790 / 20.0603)
python3 refs/scripts/smoke_olmradialblur_cpp_inner_alpha_mode_probe_cli.py # DIFF (alpha-mode probe; best mode differs per case)
python3 refs/scripts/smoke_olmradialblur_cpp_inner_source_scatter_prepass_cli.py # DIFF (source-scatter prepass: 22.1632 / 16.6793 / 19.8113)
python3 refs/scripts/smoke_olmradialblur_cpp_inner_scatter_rgb_probe_cli.py # DIFF (prepass-premul improves case_0012 only: 25.2972 / 10.6222 / 21.2910)
python3 refs/scripts/smoke_olmradialblur_cpp_inner_source_scale_probe_cli.py # DIFF (simple alpha/inv-alpha scale is negative except tiny case_0013 alpha improvement)
python3 refs/scripts/smoke_olmradialblur_cpp_dynamic_offset_probe_cli.py # DIFF (current/aex-row/min-radius all identical on refs)
python3 refs/scripts/smoke_olmradialblur_cpp_inner_prepass_mode_probe_cli.py # DIFF (AEX-alpha/source-seed probes; seed=none negative, best still 25.2972 / 10.6222 / 21.2910)
python3 refs/scripts/smoke_olmradialblur_cpp_inner_final_norm_probe_cli.py # DIFF (final-alpha/denominator alternatives negative; current max/accum still best)
python3 refs/scripts/smoke_olmradialblur_cpp_inner_seed_alpha_probe_cli.py # DIFF (seed-alpha prepass split negative; prepass/straight 57.3704 / 16.6466 / 20.9672)
python3 refs/scripts/smoke_olmsmoother_cli.py      # DIFF (構造差; 緑化していない)
python3 refs/scripts/smoke_olmkirakira_cli.py      # DIFF (case1 mean 0.8379 / case2 mean 1.1627)
python3 refs/scripts/smoke_olmkirakira_cpp_cli.py  # DIFF (native scaffold: case1 mean 0.8382 / case2 mean 1.1627 / case3 mean 1.7073)
python3 refs/scripts/smoke_olmkirakira_brightness_probe_cli.py # DIFF (Brightness/Strength=0 probe, mean 1.7073)
python3 refs/scripts/smoke_olmkirakira_cpp_rotate_filter_probe_cli.py # DIFF (bicubic negative probe: 7.9161 / 8.0050 / 19.6771)
python3 refs/scripts/smoke_all_algorithm_clis.py   # full aggregate; treats known-red scaffolds as DIFF-observed
# OLMColorKey 5-7:
python3 refs/scripts/run_reference_test.py refs/win_references/20260604_olm/OLMColorKey \
  --run-dir /tmp/ck57 --case-id case_0005 --case-id case_0006 --case-id case_0007 \
  --expected-effect 'OLM Color Key' \
  --command 'python3 "refs/scripts/olmcolorkey_cli.py" --input "{input}" --params "{params}" --output "{output}"'
```
