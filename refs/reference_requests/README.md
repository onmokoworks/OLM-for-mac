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
2. `directionalblur_context_scale_20260606.json`
   - OLMDirectionalBlurの `ctx+0x11c / ctx+0x120` render-context scale と
     非不透明alpha挙動を切るためのセット。
3. 既存Mac移植扱いのプラグイン確認
   - `OLMDistanceGradation`
   - `OLMSmoother2`
   - その他READMEで port complete 扱いのもの。
4. OLMSmoother alternate reference
   - 現参照は過剰発火原因の切り分けが弱いので、単純な高コントラスト素材で追加確認する。

Mac側への取り込み:

```sh
python3 refs/scripts/import_win_reference.py path/to/packed_reference.zip
python3 refs/scripts/audit_olmradialblur_manifest.py
python3 refs/scripts/smoke_olmradialblur_cpp_inner_cli.py
```
