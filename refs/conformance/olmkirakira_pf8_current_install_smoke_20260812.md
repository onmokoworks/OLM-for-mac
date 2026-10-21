# OLMKiraKira recorded PF8 build install / AE smoke（2026-08-12）

Status: **installed host smoke pass; AE pixel gate fail-closed**

このsmoke時点でPF8 source-decode correctionを含んでいたproduction source
`c05dc15a0f7a12857d70e0387d55ee5d18d95a25c5b76c316a93399703a2091b`と
Highlight core `e98232e4224b6ae4dd372216e10c29f3ba6621f68ab6cb10b56a02b9cc248390`
から構成したUniversal（x86_64 + arm64）binary SHA-256
`5248592a32d3a34bac67c43a1a65af875097aa1c251840d1db4aa8dcd2b39367`を
MediaCoreへ単一installし、ad-hoc署名のdeep/strict検証を通した。直前の
Highlight build `136ca31b2a2f75bd2dc624bbba4f907e29214202af80926c091abcef536f5c92`
は`/tmp/olmkirakira-pf8-install-backup.lcSjG1/OLMKiraKira.plugin`へ回復可能な
形で退避した。旧Highlight install evidenceはhistorical recordとして維持する。

AE 26.3x87 PID 73457はinstalled moduleを単一のexact pathからロードし、
Highlight Radius 5を含む記録済みparameterを適用してPF32 effect-off/effect-on
EXRを生成した。raw reportはbyte-preservedで
`olmkirakira_pf8_current_install_smoke_raw_20260812.json`へ保存し、そのSHA-256は
`0ec121cce5330e532589a752a361ea205dc555c1ea4d9e01b3132ce6a14e21c0`。

このrunの収録rowはPF32であり、PF8修正入りbuildのload/render smokeであって
live-AE PF8 pixel testではない。Windows比較はeffect-off/effect-onの双方が
6,220,800 raw FLOAT32 wordsすべて
不一致で、入力解釈は`preserve_rgb=null`だった。従ってこの証拠が閉じるのは
このsmoke時点で記録したbinaryのload/apply/renderだけで、Mac AE pixel exactは主張しない。
PF8 source-decodeのpixel exact性は別のhash-bound bounded closure
`olmkirakira_pf8_source_decode_closure_20260812.json`に限定される。Mode 4の
fixed 5×3 Highlight-gradient exact性も別のbounded closure
`olmkirakira_mode4_highlight_gradient_closure_20260812.json`へ分離され、この
PF32 AE smokeからpixel exactへ昇格しない。後続のSmart bounded promotionとmutable
workspace sourceはこの記録をsupersedeしており、本書は現在のsource SHA、on-disk
MediaCore identity、またはSmart候補のinstall状態を主張しない。
