# OLM パラメーターUI互換性ノート — 2026-08-06

## 結論

Windows 2025 AEX の公開 `PF_Cmd_GLOBAL_SETUP`／`PF_Cmd_PARAMS_SETUP` を
AEXCompat／Unicornで直接実行し、Mac production entryが登録するパラメーター面を
10プラグインすべてで比較した。

この検証が証明するのは、比較対象に含めたパラメーターの順序、disk ID、型、名前、
初期値、有効範囲、表示範囲、popup文字列、flags、UI flags、group構造、および
float-slider metadataである。レンダー結果の一致とは別のゲートであり、AEが最終的に
描画するパネルの見た目、ローカライズ、custom controlの操作性まで一律に証明する
ものではない。

## プラグイン別の状態

| プラグイン | 登録面の結果 | 主な修正 | 証拠境界 |
| --- | --- | --- | --- |
| ColorKeep | 101行とGLOBAL payloadがexact | slider／100色のdisk ID、型、flags、範囲、既定値、raw colorを固定 | actual AEXのDLL／CRT初期化を通さないfixtureでは101行のname領域がzero。埋込ASCII literalはexactだが、行への動的名前結合とAE layoutは未証明 |
| OLMBlur | 5行とGLOBAL payloadがexact | Blur Amount precision、Smoothness percent表示、Legacyのcurrent／defaultと旧project flag | 特定AE版のvisual layout／localizationは未証明 |
| OLMColorKey | 223 owned行がexact、mismatch 0 | Number of Colors、Edge Thin／Blur表示範囲、折り畳み／supervise flags、Use Color 1初期値、group end ID | Universal build／install／AE再起動は確認済み。accessibility経由のslider最小値visual readoutは未取得 |
| OLMToonDilate | 1行とGLOBAL／PiPL capabilityがexact | capability flags、Search Radiusのzero curve tolerance | native AE control layoutは未証明 |
| OLMDistanceGradation | 12行とGLOBAL payloadがexact | In/Out初期値、threshold／Blur Size表示範囲、末尾空白を含む名前、Power／Blur flags、popup choice count | install／署名は確認済み。変更後binaryのAE lazy-load確認は別のhost gate |
| OLMDirectionalBlur | 21行とGLOBAL payloadがexact | ANGLE／fixed slider型、topic構造、range／precision／percent表示、popup count、layer初期値 | imported `strncpy`をfixtureが再現しない名前は、decompiled string-table indexで結合。native layout／localizationは未証明 |
| OLMRadialBlur | 30行のpublic parameter surfaceがexact | topic構造へ変更し、「サポートされていないプレビュー制御」を解消。Center、Edge Fade、Angle、Noise Offset、range／precision／popup／layer初期値を修正 | actual AEXのsupervised custom UI/global bitsは記録済みだが、MacにEVENT／USER_CHANGED／UPDATE handlerがないため未広告。custom UI lifecycleは未移植 |
| OLMSmoother2 | 15行とGLOBAL payloadがexact | Smooth Range最大値、Gamma controlsのsupervise、Gamma Value curve tolerance | native AE layout／render parityはこの証拠に含めない |
| OLMKiraKira | 40 owned行、5 Ramp、GLOBAL payloadがexact | Ramp名、310×170 custom control、flags／UI flags、popup／merge文字列とchoice count | AEXが宣言するchoice countと区切り文字列の項目数が一致しない箇所も、補正せずraw contractどおり保持。展開後RampのDrawbot描画／操作はnative AEで未証明 |
| OLMSmoother v1 | 3個の完全な0xb0 recordとGLOBAL write footprintがexact | disk ID、型、flags／UI flags、defaults／ranges／colorを固定 | 英語3文字列のみ証明。localization、native AE layout、render、PF16／PF32はこの登録面証拠の対象外 |

## 重要な読み方

### 「raw exact」と「AE画面exact」は別

`PARAMS_SETUP`のraw一致は、MacがWindows AEXと同じhost契約を登録することを示す。
ただしAEは、その後にlocalization、control layout、custom UI event、Drawbot描画を行う。
したがってnative AEで未観測の項目を「画面まで完全一致」と一般化しない。

### AEXの不自然な値も互換契約

OLMKiraKiraやOLMDistanceGradationには、宣言choice countと区切り文字列の項目数が
一致しないpopupがある。これはMac側で見栄えよく補正せず、actual AEXのraw登録値を
保持する。saved project ABIとhost解釈を変えないためである。

### レンダー完全一致の範囲は拡張しない

この作業で修正したのはhostへの登録面であり、既存のpixel／内部数値exact証拠を
未検証の入力、geometry、bit-depth、パラメーターへ広げるものではない。レンダーの
完成範囲は `olm_release_completion_matrix_20260806.md` を正とする。

## 再現コマンド

```sh
python3 tools/emulation/test_colorkeep_params_setup_actual_aex_20260805.py
python3 tools/emulation/test_colorkeep_global_setup_actual_aex_20260805.py
python3 tools/emulation/test_olmblur_params_setup_actual_aex_20260806.py
python3 tools/emulation/test_olmcolorkey_params_setup_actual_aex_20260806.py
python3 tools/emulation/test_olmtoondilate_ui_setup_actual_aex_20260806.py
python3 tools/emulation/test_olmdistancegradation_ui_setup_actual_aex_20260806.py
python3 tools/emulation/test_olmdirectionalblur_ui_setup_actual_aex_20260806.py
python3 tools/emulation/test_olmradialblur_ui_setup_actual_aex_20260806.py
python3 tools/emulation/test_olmsmoother2_ui_setup_actual_aex_20260806.py
python3 tools/emulation/test_olmkirakira_ui_setup_actual_aex_20260806.py
python3 tools/emulation/test_olmsmoother_v1_setup_raw_actual_production_20260806.py
```

2026-08-06の再実行では、上記11コマンドがすべてPASSした。ColorKeyは223行、
KiraKiraは40行／5 Ramp、RadialBlurは30行のpublic surfaceを含む。

## 関連証拠

- `colorkeep_parameter_ui_closure_20260806.md`
- `olmblur_ui_registration_parity_20260806.md`
- `olmcolorkey_parameter_ui_parity_20260806.md`
- `olmtoondilate_ui_setup_actual_aex_20260806.md`
- `olmdistancegradation_ui_setup_actual_aex_20260806.md`
- `olmdirectionalblur_ui_setup_actual_aex_20260806.md`
- `olmradialblur_ui_setup_actual_aex_20260806.md`
- `olmsmoother2_ui_setup_actual_aex_20260806.md`
- `olmkirakira_ui_setup_actual_aex_20260806.json`
- `olmsmoother_v1_setup_raw_actual_production_20260806.md`
