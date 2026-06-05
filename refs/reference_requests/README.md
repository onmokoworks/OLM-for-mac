# Windows Reference Render Requests

このフォルダは、Windows AE実機で追加レンダーしてほしい参照ケースの仕様を置く場所です。

目的:

- Mac側のAEなしCLIで、移植アルゴリズムを追加PNGとmanifestに照合する。
- `ADBE Force CPU GPU` ではなく、`project_gpu_accel_type.current_name` と raw値で実行設定を記録する。
- CUDA/Software Only差が必要な地点で、推測実装を深追いせず差分参照を取得できるようにする。

共通レンダー条件:

- AE version, project path, comp width/height/bpc, selected layer/effect paramsをmanifestへ記録する。
- 各caseで `before_effects_frame` と effect適用後PNGを保存する。
- 可能なら同一caseを2セット出す。
  - `project_gpu_accel_type.current_name = CUDA`
  - `project_gpu_accel_type.current_name = SOFTWARE`
- `Compositing Options > GPU Rendering / ADBE Force CPU GPU` は参考値として残すが、GPU/CPU判定には使わない。

優先度:

1. `radialblur_inner_20260605.json`
   - OLMRadialBlur Innerの未解決箇所を切るための最優先セット。
2. `radialblur_inner_size_variation_20260606.json`
   - RadialBlur Inner `FUN_180004640` の `+0x40` scatter span/gate planeを、
     Size Variation非ゼロ参照で切り分けるためのセット。
3. `directionalblur_context_scale_20260606.json`
   - OLMDirectionalBlurの `ctx+0x11c / ctx+0x120` render-context scale と
     非不透明alpha挙動を切るためのセット。
4. `kirakira_single_ray_20260606.json`
   - OLMKiraKiraのray order / angle table / helper戻り値scalarを分離するための
     単独rayセット。
5. `smoother2_no_key_grid_20260606.json`
   - OLMSmoother2 no-key v2 の残差を、Smoothness / Smooth Range gridで
     class-plane firing・sample plane・color-space/writebackに切り分けるためのセット。
6. `olmcolorkey_replace_colorspace_20260606.json`
   - OLMColorKey の Enable Replace、非黒キー、複数キー、Lab76/Lab94/YUV/YCrCbを
     既存9ケースから分離して確認するためのセット。
7. 既存Mac移植扱いのプラグイン確認
   - `OLMDistanceGradation`
   - `OLMSmoother2`
   - その他READMEで port complete 扱いのもの。
8. OLMSmoother alternate reference
   - 現参照は過剰発火原因の切り分けが弱いので、単純な高コントラスト素材で追加確認する。

Mac側への取り込み:

```sh
python3 refs/scripts/import_win_reference.py path/to/packed_reference.zip --allow-missing-optional-render-sets
python3 refs/scripts/smoke_reference_requests_after_import.py
python3 refs/scripts/check_reference_request_status.py
python3 refs/scripts/audit_olmradialblur_manifest.py
python3 refs/scripts/smoke_olmradialblur_cpp_inner_cli.py
```

`import_win_reference.py` は zip/folder 内の `reference_manifest.json` を再帰的に探し、
`refs/win_references/<zip名>/<effect名>/` にPNGごとコピーします。対応する
`refs/reference_requests/*.json` が一意に見つかった場合は、その場で
`verify_reference_request_result.py` も実行します。

再開時の基本順序:

1. `check_reference_request_status.py` で対象requestが `covered` になったか確認する。
2. `smoke_reference_requests_after_import.py` でcovered manifestの検証と登録済みrequest smokeを走らせる。
3. 結果を `notes/*_ASM_FACTS.md` または `notes/PORTING_BOARD.md` に戻す。
4. green化または新しい停止条件を確認してから `smoke_all_algorithm_clis.py --profile quick` を走らせる。

代表的な再開コマンド:

```sh
python3 refs/scripts/smoke_olmdirectionalblur_cpp_rotated_aex_full_choreo_cli.py
python3 refs/scripts/smoke_olmradialblur_cpp_inner_source_scatter_prepass_cli.py
python3 refs/scripts/smoke_olmkirakira_cpp_two_temp_no_fastpath_probe_cli.py
python3 refs/scripts/smoke_olmsmoother2_cli.py
python3 refs/scripts/audit_olmcolorkey_manifest.py path/to/imported/OLMColorKey/reference_manifest.json
```

Win側へ渡すリクエストzip作成:

```sh
python3 refs/scripts/check_reference_request_status.py
python3 refs/scripts/package_reference_requests.py --pending
python3 refs/scripts/package_reference_requests.py --only kirakira_single_ray_20260606
```

生成zipにはこのREADME、選択されたrequest JSON、Win側Codexへそのまま渡すための
`WIN_CODEX_HANDOFF.md` が入ります。
