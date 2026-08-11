# OLM for Mac — Public Beta

Windows版OLM ToolsのAfter Effectsプラグイン（AEX）を、macOS／Apple Silicon向けの
Universalプラグインとして互換移植するプロジェクトです。

本プロジェクトはOLM DigitalのオリジナルOLMプラグインを基にした非公式の互換移植で、
OLM Digitalによる提携・承認を示すものではありません。オリジナルのプラグイン、
製品名、商標および原著作物に関する権利は、それぞれの権利者に帰属します。
リポジトリの[LICENSE](LICENSE)は収録コードの利用条件であり、本家の名称、商標、
バイナリ、素材などに別途の権利を付与するものではありません。

見た目が近いだけの再実装ではありません。対象として明記したAfter Effects、
Softwareレンダー、bit-depth、入力、geometry、パラメーターについて、Windows AEX／
Windows AEとピクセルおよび必要な内部値が完全一致することを合格条件にしています。

## Public Betaについて

このリポジトリは現在、公開ベータとしての配布準備中です。主要な処理経路は
Windows AEXを直接実行した結果やWindows／Mac AEの保存済み結果と照合していますが、
Windows版の全入力・全geometry・全パラメーター直積との完全互換を保証する正式版では
ありません。重要なプロジェクトでは複製を作り、出力を確認してから使用してください。

不具合報告には、プラグイン名、After Effectsのバージョン、プロジェクト色深度、
フレームサイズ、設定値、再現素材または最小プロジェクトを添えてください。

詳しい導入方法は[インストールガイド](docs/INSTALL_JA.md)、既知の制限は
[KNOWN_LIMITATIONS.md](KNOWN_LIMITATIONS.md)を参照してください。

## 現在の状態

2026-08-11時点のMacリリース候補（Public Beta）は、次の統合ゲートを通過しています。

- 全10プラグインの固定fixture回帰：PASS
- 現行Mac AEでのロード／代表レンダー：10/10
- 最新の最小host smoke：10/10 loaded／applied／render succeeded（64×64 PNG）
- インストール済みUniversal bundle、SHA-256、署名：10/10
- 対象ホスト：After Effects `26.3x87`、macOS 15.7.2 arm64、Softwareレンダー
- 最終Mac統合ゲート：`release_gate_pass`

Windows AEで取得する7行として固定した同一条件校正は、受領・検証済みです。
ただしWindows／MacのAE hostが
素材import、premultiply、色管理、書き出しで異なる場合があるため、最終EXR全体の
包括的なcross-host一致は主張しません。
最新の10-plugin smokeはロード、適用、64×64 PNG保存のhost動作確認です。
Windowsとのpixel exactや主要パラメーター一致を追加で証明するものではありません。

直近のpublic-entry／installed-binary検証では、ColorKeep 6セル、OLMSmoother2 6セル、
OLMToonDilate 12セル、OLMDirectionalBlur 6セル、OLMColorKey 18セルを記録済み条件で
raw exact確認しています。一方、OLMKiraKira Mode 1のpublic 3-depth経路はraw不一致で
fail-closeです。個別セルの成功を任意入力やWindows／Mac AE pixel一致へ一般化しません。

詳しい対応範囲と制限は、次の文書を正とします。

- [日本語リリースノート](refs/conformance/OLM_MAC_RELEASE_NOTES_20260806.md)
- [プラグイン別の完成対象・証拠境界](refs/conformance/olm_release_completion_matrix_20260806.md)
- [機械判定された最終ゲート結果](refs/conformance/olm_release_gate_status_20260806.json)

## 対象プラグイン

| プラグイン | 主な対象 | native depth／扱い |
| --- | --- | --- |
| OLMBlur | Legacy／NonLegacy、repeat、bias、記録済みSmart chain | PF8／PF16／PF32 |
| ColorKeep | 有効／無効、tolerance、1〜100色、installed public covering | PF8／PF16／PF32 |
| OLMColorKey | core、Edge Thin、Edge Blur、replace／color space、記録済み半透明51-cell matrix | PF8／PF16／PF32（限定範囲） |
| OLMToonDilate | copy／dilate、radius、frontier／tie／corner、installed covering | PF8／PF16／PF32 |
| OLMDistanceGradation | Inside／Outside／Both、補間、invert、background、記録済みblur／bilateral matrix | PF8／PF16／PF32（限定範囲） |
| OLMDirectionalBlur | 基本方向ブラー、Noise Type 1／2／3、記録済みfront＋back複合経路 | PF8／PF16／PF32（限定範囲） |
| OLMRadialBlur | Zoom／Rotation／Inner、記録済みtransform／Size×Edge×Noise複合経路 | PF8／PF16／PF32（bounded guard付き） |
| OLMSmoother2 | v1／v2 classifier、key／invert、Gamma、range、palette交差 | PF8／PF16／PF32（限定範囲） |
| OLMKiraKira | Mode 1／2／3／4、ramp、compose、warp／blur、記録済みnatural Mode 4 | PF8／PF16／PF32（限定範囲） |
| OLMSmoother v1 | no-key／Color Key、smoothing range | native PF8／PF16。32bpcはAE host conversion |

この表は「全パラメーターの直積が完全一致」という意味ではありません。記録済みの
geometry、入力、値、分岐境界だけが証明対象です。範囲外はリリースノートに明記し、
実装側でも可能な箇所はfail-closeにしています。

現在の主な残課題は、OLMKiraKira Mode 1のbox primitive、OLMDistanceGradation
PF32 Mode 5の未解決6セル（matrix 58／64 exact）、OLMSmoother v1の32bpc
AE host conversion境界、Layer Noise Type 3の汎用world対応です。Type 3の効率的な
検証にはAEXCompat issue #1162のmacOS declarative fixture runnerが関係します。

## インストールとビルド

全プラグインをビルドします。

```sh
scripts/build_all_mac_plugins.sh
```

MediaCoreへインストールします。

```sh
scripts/install_mac_plugins_to_mediacore.sh
```

配布用ZIPを作成します。

```sh
scripts/package_mac_plugins.sh
```

同名pluginのバックアップをAdobeの検索パス内へ残すと、重複モーダルが出ます。
バックアップはMediaCoreの外へ移してください。

## 検証

通常の全10プラグイン固定fixture回帰：

```sh
python3 scripts/run_olm_mac_fixed_fixture_regression_20260805.py
```

Macリリース統合ゲート（固定fixture、Universal／署名／identity、Mac AE証拠）：

```sh
python3 scripts/run_olm_release_gate_20260806.py
```

文書とWindowsパッケージの整合性：

```sh
python3 -m unittest \
  tests.test_olm_release_documentation_20260806 \
  tests.test_windows_ae_release_boundary_minimal_20260806
```

`Exact`は、その証拠レコード内でのbyte一致、またはraw FLOAT32 word一致です。
PNGやEXRファイル全体のSHAはmetadataで変わるため、必要に応じて生sampleを比較します。

## Windows AE境界の記録

実行対象は次のhash固定パッケージだけです。

`refs/reference_requests/olm_windows_ae_release_boundary_minimal_20260806.zip`

SHA-256：

```text
6a060641dc867cbb5cb858136f6fd294fb49d274fa252cec71459bc9b20a4652
```

ColorKeep PF8／PF16／PF32、OLMKiraKira Mode 4 PF8／PF16／PF32、
OLMSmoother v1 PF16の計7行を取得・受領済みです。返却物は次で再検証できます。

```sh
python3 scripts/verify_windows_ae_release_boundary_minimal_20260806.py \
  RETURN_OLM_WINDOWS_AE_RELEASE_BOUNDARY_MINIMAL_20260806.zip
```

過去の大量のrequestは解析履歴です。現在のリリース作業では再送しません。

## WindowsとMacでAE出力が異なる場合

最終ファイルの差だけでは、プラグイン演算の差と判断しません。次の境界を分けます。

1. 同一の生ピクセルをAEXとMac実装へ渡した演算比較
2. AE管理world上でのプラグイン入口から出力までの比較
3. 素材import、premultiply、color management、codecを含む最終書き出し比較

実際に、AEのimportやpremultiply／unpremultiplyで差が生じるケースを確認しています。
同一入力worldでの演算が完全一致している場合、その差はhost境界として記録します。

## ディレクトリ

| パス | 内容 |
| --- | --- |
| `mac/` | Mac After Effectsプラグイン本体 |
| `core/` | AEX命令列に合わせた共有kernel／worker |
| `cli/` | AEなしの局所検証CLI |
| `tools/emulation/` | AEXCompat、Unicorn、Windows AEX直接再生 |
| `refs/conformance/` | 完全一致の証拠、完成表、リリースノート |
| `refs/reference_requests/` | Windows AEへ渡すhash固定パッケージ |
| `scripts/` | ビルド、Mac AE検証、Windows往復、統合ゲート |
| `notes/` | 逆解析・調査履歴。現在状態は最新リリース文書を優先 |

## 開発上の原則

- 未検証範囲へ完全一致を一般化しない
- 見た目合わせ、許容差、off-by-1を完成扱いしない
- Windows実機はAE固有境界の最小観測だけに使う
- 通常開発はMacのfixture、AEXCompat、Unicorn、Mac AEで完結させる
- AEXCompatの解析基盤更新は別リポジトリ・別commitとして管理し、OLMのExact証拠とは分ける
- 既に閉じた分岐の近接値を無制限に追加しない
- 主要モード、bit-depth、分岐境界、実用geometryへ完成作業を集中する

低レベルの開発規約は[AGENT_GUIDE.md](AGENT_GUIDE.md)、AEX直接再生は
[tools/emulation/README.md](tools/emulation/README.md)、公開対象とローカル解析資料の境界は
[docs/REPOSITORY_POLICY_JA.md](docs/REPOSITORY_POLICY_JA.md)を参照してください。

## English summary

This repository ports the Windows OLM After Effects plug-ins to Universal
macOS/Apple Silicon plug-ins. The Public Beta candidate passes all ten fixed
fixture lanes, ten current-Mac-AE representative renders, and all installed
Universal/signature/identity checks. Exactness claims remain limited to the
declared host, depths, fixtures, geometries and parameter boundaries. Seven
same-contract Windows AE calibration rows are accepted. This is a bounded
compatibility claim, not a guarantee over every input, geometry, parameter
combination, custom UI path, or host color pipeline.

This is an unofficial compatibility port based on the original OLM plug-ins
from OLM Digital; it does not imply endorsement or affiliation. Rights in the
original plug-ins, product names, trademarks, and original works remain with
their respective owners. The repository license covers the code distributed
here and does not grant additional rights to upstream assets.
