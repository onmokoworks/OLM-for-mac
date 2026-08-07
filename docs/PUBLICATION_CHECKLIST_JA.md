# 公開前チェックリスト

## 配布ZIP

- [ ] 10個の`.plugin`だけが期待したbundle名で入っている
- [ ] 各実行ファイルがarm64／x86_64のUniversal binary
- [ ] `codesign --verify`が10本すべて成功
- [ ] `INSTALL_JA.md`、`KNOWN_LIMITATIONS.md`、リリースノートを同梱
- [ ] manifest／INSTALL文書にビルド端末の絶対パスがない
- [ ] ZIPのSHA-256をリリースページへ記載
- [ ] Developer ID署名／notarizationを行うか、未実施であることを明記

## GitHubリポジトリ

現在のprivate開発リポジトリは、そのままvisibilityをPublicへ変更しないでください。
公開用にはクリーンな履歴または別リポジトリを作成し、少なくとも次を除外します。

- 元Windows版`.aex`を含むrequest ZIP
- Windows実機のreturn ZIP、dump、trace、AEP、EXRなどの解析資料
- `refs/share_staging/`、`refs/windows_returns/`などの受け渡し履歴
- ローカルの絶対パス、ユーザー名、ホスト名を含む生成済み証拠
- Adobe SDKや第三者ライブラリの再配布が許可されていないファイル
- 一時ファイル、バックアップ、クラッシュログ、巨大fixture

現在確認済みの重大な公開ブロッカー：

- `refs/reference_requests/olm_crosshost_linear_input_20260806.zip`にWindows `.aex`を含む
- `refs/reference_requests/olm_windows_ae_release_boundary_minimal_20260806.zip`にWindows `.aex`を含む
- リポジトリにLICENSEがない。ソース公開時の利用条件を所有者が決める必要がある
- 過去のcommitにも対象ファイルが存在するため、最新commitから削除するだけでは不十分

## 公開表現

- [ ] `Public Beta`または`Technology Preview`と明記
- [ ] Windows版との全入力・全設定の完全互換を保証しない
- [ ] 対応AEバージョン、CPU Software基準、色深度境界を明記
- [ ] 重要なプロジェクトは複製して試すよう案内
- [ ] 問題報告テンプレートを有効化

## 公開直前

- [ ] private開発リポジトリとは別の公開候補を新規cloneして内容を再監査
- [ ] 公開候補の全tracked fileに対してsecret scanと絶対パス検索を再実行
- [ ] 配布ZIPを新規ユーザー環境で展開・インストール確認
- [ ] リリースページを下書きし、visibility変更や公開ボタンは所有者が最終確認する
