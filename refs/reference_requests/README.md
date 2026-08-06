# Windows AE 参照リクエスト

このディレクトリには、Windows AEでしか確認できないhost境界を取得するための
requestとhash固定ZIPを保存します。

## 現在実行するパッケージ

現在のMacリリース候補に必要なのは、次の1ファイルだけです。

`olm_windows_ae_release_boundary_minimal_20260806.zip`

SHA-256：

```text
6a060641dc867cbb5cb858136f6fd294fb49d274fa252cec71459bc9b20a4652
```

取得対象は次の7行です。

- ColorKeep：PF8／PF16／PF32
- OLMKiraKira controlled Mode 4：PF8／PF16／PF32
- OLMSmoother v1 canonical `case_0001`：PF16

パッケージ内の`README_WINDOWS.md`と`BATCH_CONTRACT.json`を正としてください。
各行はAE `26.3x87`、Softwareレンダー、固定AEX／入力／パラメーター、
disabled／effect-onのuncompressed scanline FLOAT32 OpenEXR、process／module
attestationを要求します。PNG previewだけの返却は受理しません。

## パッケージを検査する

Mac側：

```sh
python3 -m unittest tests.test_windows_ae_release_boundary_minimal_20260806
shasum -a 256 refs/reference_requests/olm_windows_ae_release_boundary_minimal_20260806.zip
```

返却後：

```sh
python3 scripts/verify_windows_ae_release_boundary_minimal_20260806.py \
  RETURN_OLM_WINDOWS_AE_RELEASE_BOUNDARY_MINIMAL_20260806.zip
```

verifierはZIP path safety、process／module attestation、binary／input／setting／
parameter readback、no-op、FLOAT32 scanline EXR、寸法をfail-closedで検査します。

## 過去のrequestについて

このフォルダに残る多数のJSON、ZIP、handoff文書は逆解析・bit-depth拡張・
障害切り分けの履歴です。現在の7行と重複するもの、すでにAEXCompat／Unicorn／Mac AEで
閉じたものを再送しないでください。

新しいWindows requestを増やすのは、Mac fixtureとAEX直接再生で解決できず、
完成対象内のAE固有挙動が不足すると確認された場合だけです。

最新の対応範囲は次を参照してください。

- [`../conformance/OLM_MAC_RELEASE_NOTES_20260806.md`](../conformance/OLM_MAC_RELEASE_NOTES_20260806.md)
- [`../conformance/olm_release_completion_matrix_20260806.md`](../conformance/olm_release_completion_matrix_20260806.md)
