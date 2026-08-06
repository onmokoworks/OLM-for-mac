# OLMSmoother v1 PF16 cross-host Gamma境界

現在のMac AE effect出力はPF16正規化値と完全一致する。全FLOAT sampleを32768倍した値は整数で、最大deltaは0。残るWindows/Mac差183語は、100×100 fixture範囲内のR channelだけに存在する。各差について、Windows値は`Mac値 ^ 2.4`で最大絶対誤差`9.624730730184439e-07`まで説明できる。

したがって残差はAE host/exportの色変換境界として閉じる。プラグインのPF16補間演算を変更する根拠にはしない。
